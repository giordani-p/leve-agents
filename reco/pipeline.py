# reco/pipeline.py
"""
Pipeline de Recomendação - Leve Agents

Pipeline completo de recomendação de trilhas educacionais que processa
perfis de usuários e retorna recomendações personalizadas.

Fluxo de processamento:
1. Carregamento: Snapshot do usuário + catálogo de trilhas (API/files)
2. Normalização: Conversão para TrailCandidate com deduplicação e filtros
3. Construção de consulta: Pergunta + pistas do perfil + contexto adicional
4. Indexação: Criação de índices vetoriais (MPNet) e BM25 em memória
5. Retrieval: Busca híbrida combinando semântica e textual
6. Ranking: Aplicação de regras de negócio e boosts personalizados
7. Output: Geração de explicações e validação final

Arquitetura:
- Índices construídos on-the-fly (piloto) - produção usa índices persistentes
- Suporte a múltiplas fontes de dados com fallback automático
- Sistema de logging completo para observabilidade
- Validação rigorosa com schemas Pydantic
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from reco.config import RecoConfig
from reco.data_loader import load_snapshot, load_trails as load_trails_file
from reco.data_loader_api import fetch_trails as fetch_trails_api
from reco.normalizer import to_candidates, dedupe_by_public_id, filter_by_status
from reco.query_builder import build as build_query

# BM25 legado
from reco.indexer import Indexer as BM25Indexer  # ajuste o nome se o seu arquivo expõe outro símbolo

# Denso / Híbrido
from reco.embeddings.embedding_provider import EmbeddingProvider
from reco.index.vector_index import VectorIndex, VectorItem
from reco.retriever.dense_retriever import DenseRetriever, DenseResult
from reco.retriever.hybrid_retriever import HybridRetriever, HybridResult

from reco.ranker import rank as rank_candidates, ScoredCandidate
from reco.explainer import make_reason
from reco.output_builder import build_output

from schemas.trail_input import TrailInput
from schemas.trail_output import TrailOutput
from schemas.trail_candidate import TrailCandidate

from validators.trail_output_checks import apply_business_rules


# -----------------------------
# Helpers internos
# -----------------------------
def _item_vector_text(cand: TrailCandidate) -> str:
    """
    Texto base para embeddings do item (trilha). Mantém coerência com query_builder.
    """
    parts = [
        cand.title or "",
        cand.subtitle or "",
        cand.description or "",
        " ".join(cand.topics or []),
        " ".join(cand.tags or []),
        cand.combined_text or "",
    ]
    return " | ".join(p for p in parts if p)


def _build_vector_index_for_trilhas(
    candidates: List[TrailCandidate],
    cfg: RecoConfig,
    *,
    backend: str = "numpy",
) -> Tuple[VectorIndex, EmbeddingProvider]:
    """
    Constrói um índice vetorial em memória (backend NumPy) para o catálogo atual.
    Retorna (index, provider). Os vetores são L2-normalizados pelo provider.
    """
    provider = EmbeddingProvider.from_config(cfg)
    index = VectorIndex.from_config(cfg, backend=backend, index_name=cfg.INDEX_TRILHAS)

    # Gera embeddings em batch
    texts = [_item_vector_text(c) for c in candidates]
    embs = provider.embed_texts(texts, normalize=True, batch_size=cfg.EMBEDDING_BATCH_SIZE)

    items = []
    for cand, vec in zip(candidates, embs):
        meta = {
            "status": cand.status or "",
            "difficulty": (cand.difficulty or "").lower(),
            "area": cand.area or "",
        }
        items.append(VectorItem(id=str(cand.publicId), vector=vec.astype(np.float32, copy=False), metadata=meta))

    index.upsert(items)
    return index, provider


def _bm25_callable_for_trilhas(
    candidates: List[TrailCandidate],
    cfg: RecoConfig,
) -> tuple:
    """
    Prepara o BM25 indexer legado e retorna um callable:
      bm25_search_topk(query_text, k) -> List[(id, score_bm25, meta)]
    """
    bm25 = BM25Indexer(cfg)  # seu indexer deve aceitar cfg; ajuste se necessário
    bm25.fit_items(candidates)

    def _searcher(query_text: str, k: int) -> List[tuple]:
        # Espera-se que seu indexer retorne [(TrailCandidate, score)] ou [(id, score, meta)].
        # Adaptamos para o formato do HybridRetriever.
        raw = bm25.search_topk(query_text, k)
        out: List[tuple] = []
        if raw and isinstance(raw[0], tuple) and len(raw[0]) == 2 and isinstance(raw[0][0], TrailCandidate):
            # Formato [(TrailCandidate, score)]
            for cand, score in raw:
                meta = {"status": cand.status or "", "difficulty": (cand.difficulty or "").lower(), "area": cand.area or ""}
                out.append((str(cand.publicId), float(score), meta))
        else:
            # Caso seu indexer já devolva (id, score, meta)
            out = [(str(r[0]), float(r[1]), r[2] if len(r) > 2 else {}) for r in raw]
        return out

    return bm25, _searcher


def _map_reasons(
    ranked: List[ScoredCandidate],
    query_text: str,
    limit: int,
) -> Dict[str, str]:
    """
    Gera dicionário de razões (why_match) por publicId (str), considerando os 'limit' primeiros itens.
    """
    reasons: Dict[str, str] = {}
    topk = ranked[: max(1, min(limit, len(ranked)))]
    for sc in topk:
        pid = str(sc.candidate.publicId)
        reasons[pid] = make_reason(sc, query_text)
    return reasons


# -----------------------------
# Pipeline
# -----------------------------
def run(
    user_input: TrailInput,
    snapshot_path: str,
    trails_path: str,
    cfg: Optional[RecoConfig] = None,
) -> TrailOutput:
    """
    Executa o pipeline completo e retorna um TrailOutput validado.
    """
    cfg = cfg or RecoConfig()

    # 1) Carregar dados
    snapshot = load_snapshot(snapshot_path)
    if cfg.SOURCE == "api":
        raw_trails = fetch_trails_api(cfg)
    else:
        raw_trails = load_trails_file(trails_path)

    # 2) Normalizar, deduplicar e filtrar Published
    candidates_all = to_candidates(raw_trails)
    candidates_all = dedupe_by_public_id(candidates_all)
    candidates = filter_by_status(candidates_all, cfg.ALLOWED_STATUS)

    if not candidates:
        empty = build_output(
            ranked=[],
            query_text=user_input.user_question,
            max_results=user_input.max_results,
            reasons_by_id={},
        )
        return apply_business_rules(empty)

    # 3) Montar consulta (user_question + pistas do snapshot + contexto_extra)
    query_text = build_query(
        user_question=user_input.user_question,
        snapshot=snapshot,
        cfg=cfg,
        contexto_extra=user_input.contexto_extra,
    )

    # 4) Construir índice vetorial (piloto: em memória / NumPy)
    vindex, prov = _build_vector_index_for_trilhas(candidates, cfg, backend="numpy")

    # 5) Retrieval (denso ou híbrido)
    dense = DenseRetriever.from_config(cfg, vector_index=vindex, embedding_provider=prov)

    if cfg.USE_HYBRID:
        # Prepara BM25 legado para o catálogo atual
        bm25, bm25_search_topk = _bm25_callable_for_trilhas(candidates, cfg)

        # Híbrido: une BM25 + Denso com normalização e blending
        hybrid = HybridRetriever.from_config(cfg, dense_retriever=dense, bm25_search_topk=bm25_search_topk)
        hybrid_res: List[HybridResult] = hybrid.search(
            query_text=query_text,
            k=cfg.TOP_K_DEFAULT,
            filters={"status": "Published"} if cfg.ENFORCE_PUBLISHED else None,
        )

        # Adapta para entrada do ranker (híbrido)
        scored_candidates = [
            {
                "candidate": next(c for c in candidates if str(c.publicId) == hr.id),
                "score_combined": hr.score_combined,
                "score_semantic": hr.score_semantic,
                "score_bm25": hr.score_bm25,
            }
            for hr in hybrid_res
        ]
    else:
        # Denso puro (P0/P1 com flag desligada)
        dense_res: List[DenseResult] = dense.search(
            query_text=query_text,
            k=cfg.TOP_K_DEFAULT,
            filters={"status": "Published"} if cfg.ENFORCE_PUBLISHED else None,
        )
        # Adapta para entrada do ranker (legado-like com score semântico)
        # Aqui podemos passar como [(TrailCandidate, score)] que o ranker entende
        id2cand = {str(c.publicId): c for c in candidates}
        scored_candidates = [(id2cand[dr.id], dr.score_semantic) for dr in dense_res if dr.id in id2cand]

    # 6) Ranking com regras de negócio (threshold por coleção: trilhas)
    ranked = rank_candidates(
        scored_candidates=scored_candidates,
        query_text=query_text,
        cfg=cfg,
        collection="trilhas",
        max_results=user_input.max_results,
    )

    # 7) Gerar razões (why_match) para o top-K
    reasons_by_id = _map_reasons(ranked, query_text, limit=user_input.max_results)

    # 8) Construir saída (status ok/fora_do_escopo) já com why_match preenchido
    output = build_output(
        ranked=ranked,
        query_text=query_text,
        max_results=user_input.max_results,
        reasons_by_id=reasons_by_id,
    )

    # 9) Aplicar regras de negócio/validação final
    final_output = apply_business_rules(output)
    return final_output
