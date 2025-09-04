# reco/pipeline.py
"""
Pipeline ponta a ponta do Sistema de Recomendação (CLI).

Fluxo:
1) Carrega snapshot (sempre via arquivo) e catálogo (via API ou arquivos, conforme config.SOURCE).
2) Normaliza trilhas em TrailCandidate, deduplica e filtra por status permitido (Published).
3) Monta a consulta a partir da user_question (+ pistas opcionais do snapshot/contexto).
4) Calcula similaridade por conteúdo (TF-IDF + cosseno).
5) Aplica regras de ranking (boosts, threshold, ordenação, dedupe e top-N).
6) Gera 'why_match' em tom jovem para os itens do top-K.
7) Constrói TrailOutput já com why_match preenchido e aplica validações de negócio.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from reco.config import RecoConfig
from reco.data_loader import load_snapshot, load_trails as load_trails_file
from reco.data_loader_api import fetch_trails as fetch_trails_api
from reco.normalizer import to_candidates, dedupe_by_public_id, filter_by_status
from reco.query_builder import build as build_query
from reco.indexer import score as index_scores
from reco.ranker import rank as rank_candidates, ScoredCandidate
from reco.explainer import make_reason
from reco.output_builder import build_output

from schemas.trail_input import TrailInput
from schemas.trail_output import TrailOutput

from validators.trail_output_checks import apply_business_rules


def _map_reasons(
    ranked: List[ScoredCandidate],
    query_text: str,
    limit: int,
) -> Dict[str, str]:
    """
    Gera e retorna um dicionário de razões (why_match) indexado por publicId (str).
    Considera apenas os 'limit' primeiros itens.
    """
    reasons: Dict[str, str] = {}
    topk = ranked[: max(1, min(limit, len(ranked)))]
    for sc in topk:
        pid = str(sc.candidate.publicId)
        reasons[pid] = make_reason(sc, query_text)
    return reasons


def run(
    user_input: TrailInput,
    snapshot_path: str,
    trails_path: str,
    cfg: Optional[RecoConfig] = None,
) -> TrailOutput:
    """
    Executa o pipeline completo e retorna um TrailOutput validado.

    Parâmetros:
      - user_input: TrailInput (user_question obrigatório; max_results ≤ 3).
      - snapshot_path: caminho para o JSON de snapshot (ex.: files/snapshots/carlos_001.json).
      - trails_path: caminho para o JSON de trilhas (ex.: files/trails/trails_examples.json).
        *Observação*: quando SOURCE='api', este parâmetro é ignorado.
      - cfg: RecoConfig (opcional; usa padrão se não fornecido).
    """
    cfg = cfg or RecoConfig()

    # 1) Carregar dados
    snapshot = load_snapshot(snapshot_path)

    if cfg.SOURCE == "api":
        # Catálogo via API (httpx, timeout/retry definidos em config)
        raw_trails = fetch_trails_api(cfg)
    else:
        # Catálogo via arquivos (mock local)
        raw_trails = load_trails_file(trails_path)

    # 2) Normalizar, deduplicar e filtrar Published
    candidates_all = to_candidates(raw_trails)
    candidates_all = dedupe_by_public_id(candidates_all)
    candidates = filter_by_status(candidates_all, cfg.ALLOWED_STATUS)

    # Se nada publicado, retorna estado vazio controlado
    if not candidates:
        empty = build_output(
            ranked=[],
            query_text=user_input.user_question,
            max_results=user_input.max_results,
            reasons_by_id={},  # sem razões porque não há itens
        )
        return apply_business_rules(empty)

    # 3) Montar consulta (user_question + pistas opcionais do snapshot + contexto_extra)
    query_text = build_query(
        user_question=user_input.user_question,
        snapshot=snapshot,
        cfg=cfg,
        contexto_extra=user_input.contexto_extra,
    )

    # 4) Similaridade por conteúdo (TF-IDF)
    scored = index_scores(query_text=query_text, candidates=candidates, cfg=cfg)

    # 5) Ranking com regras de negócio (boosts, threshold, dedupe, top-N)
    ranked = rank_candidates(
        scored_candidates=scored,
        query_text=query_text,
        cfg=cfg,
        max_results=user_input.max_results,
    )

    # 6) Gerar razões (why_match) para o top-K
    reasons_by_id = _map_reasons(ranked, query_text, limit=user_input.max_results)

    # 7) Construir saída (status ok/fora_do_escopo) já com why_match preenchido
    output = build_output(
        ranked=ranked,
        query_text=query_text,
        max_results=user_input.max_results,
        reasons_by_id=reasons_by_id,
    )

    # 8) Aplicar regras de negócio/validação final
    final_output = apply_business_rules(output)
    return final_output
