# reco/ranker.py
"""
Ranking de negócio — V4 / P1 Híbrido (BM25 + MPNet)

O que faz:
- Recebe candidatos já pontuados (legado: content_score do BM25; novo: scores do híbrido).
- Usa o score "base" para ranking:
    - Se houver score_combined (híbrido), usa ele.
    - Senão, usa o content_score legado.
- Aplica boosts explicáveis (título/descrição, tags/tema, difficulty=Beginner).
- Faz cap/clamp do score (0..1) e aplica threshold por coleção (Trilhas P1).
- Dedup por publicId, ordena desc e corta em MAX_SUGGESTIONS.
- Fallback de dominância: se ninguém passa do threshold, aceita top-1 se >= DOMINANCE_MIN_ACCEPT.

Notas:
- Tokenização acento-insensível (normalização NFKD + casefold).
- Mantém compatibilidade com o formato antigo de entrada.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union
import re
import unicodedata as _ud

from reco.config import RecoConfig
from schemas.trail_candidate import TrailCandidate


# Regex de palavra; após strip de acentos, cobre letras/dígitos em ASCII e Unicode.
_WORD_RE = re.compile(r"[a-zA-ZÀ-ÖØ-öø-ÿ0-9]+")


def _strip_accents(text: str) -> str:
    """Remove acentos (NFKD) preservando apenas caracteres base."""
    if not text:
        return ""
    return "".join(ch for ch in _ud.normalize("NFKD", text) if not _ud.combining(ch))


def _tokenize(text: str) -> List[str]:
    """Tokenização simples, acento-insensível e case-insensível."""
    if not text:
        return []
    norm = _strip_accents(text).casefold()
    return [m.group(0) for m in _WORD_RE.finditer(norm)]


@dataclass
class ScoredCandidate:
    candidate: TrailCandidate
    match_score: float
    applied_boosts: List[str] = field(default_factory=list)
    # Campos extras (debug/observabilidade)
    base_score: Optional[float] = None
    score_semantic: Optional[float] = None
    score_bm25: Optional[float] = None
    score_combined: Optional[float] = None


# -----------------------------
# Boosts de negócio
# -----------------------------
def _has_title_desc_keyword(cand: TrailCandidate, query_tokens: Iterable[str]) -> bool:
    """
    True se alguma palavra-chave da consulta aparece em título/descrição/combined_text.
    Ignora tokens muito curtos (<=2).
    """
    q = {t for t in query_tokens if len(t) > 2}
    if not q:
        return False
    hay = f"{cand.title or ''} | {cand.description or ''} | {cand.combined_text or ''}"
    hay_norm = _strip_accents(hay).casefold()
    return any(tok in hay_norm for tok in q)


def _apply_boosts(
    base_score: float,
    cand: TrailCandidate,
    query_tokens: Iterable[str],
    cfg: RecoConfig,
) -> Tuple[float, List[str]]:
    """
    Regras:
      - TITLE_DESC_BOOST: se keyword da pergunta aparece no título/descrição/conteúdo.
      - TAG_BOOST: se tokens de tags aparecem na pergunta.
      - BEGINNER_BOOST: se difficulty == Beginner (ajuda fase de descoberta).
    """
    boosts_applied: List[str] = []
    score = float(base_score)

    # 0) Boost por título/descrição
    if _has_title_desc_keyword(cand, query_tokens):
        score += cfg.TITLE_DESC_BOOST
        boosts_applied.append("title_desc_match")

    # 1) Boost por tags/tema
    tag_tokens: List[str] = []
    for t in cand.tags or []:
        tag_tokens.extend(_tokenize(str(t)))
    qset = set(query_tokens)
    if tag_tokens and qset.intersection(tag_tokens):
        score += cfg.TAG_BOOST
        boosts_applied.append("tag_match")

    # 2) Boost leve para iniciantes
    if (cand.difficulty or "").lower() == "beginner":
        score += cfg.BEGINNER_BOOST
        boosts_applied.append("beginner_boost")

    # Cap e clamp
    if score > cfg.SCORE_CAP:
        score = cfg.SCORE_CAP
    if score < 0.0:
        score = 0.0
    elif score > 1.0:
        score = 1.0

    return score, boosts_applied


# -----------------------------
# Entrada flexível (legado x híbrido)
# -----------------------------
# Formato legado: List[Tuple[TrailCandidate, float]]
LegacyInput = List[Tuple[TrailCandidate, float]]

# Formato híbrido: List[Dict[str, Any]] ou estrutura com chaves:
# {
#   "candidate": TrailCandidate,
#   "score_combined": float,   # opcional
#   "score_semantic": float,   # opcional
#   "score_bm25": float,       # opcional
# }
HybridInputItem = Dict[str, Any]
HybridInput = List[HybridInputItem]

RankInput = Union[LegacyInput, HybridInput]


def _coerce_inputs(
    items: RankInput,
) -> List[Tuple[TrailCandidate, Optional[float], Optional[float], Optional[float]]]:
    """
    Converte entrada (legado ou híbrido) para uma lista homogênea de tuplas:
      (candidate, score_combined, score_semantic, score_bm25)
    """
    out: List[Tuple[TrailCandidate, Optional[float], Optional[float], Optional[float]]] = []
    if not items:
        return out

    # Caso 1: legado
    if isinstance(items, list) and items and isinstance(items[0], tuple):
        for cand, content_score in items:  # type: ignore
            out.append((cand, None, None, float(content_score)))
        return out

    # Caso 2: híbrido (dicts com chaves conhecidas)
    for it in items:  # type: ignore
        cand = it.get("candidate") or it.get("item") or it.get("trail")  # tolerante a nomes
        if not isinstance(cand, TrailCandidate):
            continue
        out.append(
            (
                cand,
                _safe_float(it.get("score_combined")),
                _safe_float(it.get("score_semantic")),
                _safe_float(it.get("score_bm25")),
            )
        )
    return out


def _safe_float(x: Any) -> Optional[float]:
    try:
        return float(x) if x is not None else None
    except Exception:
        return None


# -----------------------------
# Núcleo do rank
# -----------------------------
def rank(
    scored_candidates: RankInput,
    query_text: str,
    cfg: RecoConfig,
    *,
    collection: str = "trilhas",
    max_results: Optional[int] = None,
) -> List[ScoredCandidate]:
    """
    Aplica boosts, threshold, ordenação, dedupe e top-N.
    - scored_candidates: pode ser legado ([(TrailCandidate, score)]) ou híbrido (lista de dicts com scores).
    - collection: "trilhas" (P1) ou "vagas" (futuro P2) — define threshold.
    """
    coerced = _coerce_inputs(scored_candidates)
    if not coerced:
        return []

    # Threshold por coleção
    if collection == "vagas":
        threshold = cfg.MATCH_THRESHOLD_VAGAS
    else:
        threshold = cfg.MATCH_THRESHOLD_TRILHAS

    max_n = max_results if isinstance(max_results, int) and max_results > 0 else cfg.MAX_SUGGESTIONS
    q_tokens = _tokenize(query_text)

    enriched: List[ScoredCandidate] = []
    for cand, score_combined, score_sem, score_bm25 in coerced:
        # Score base: híbrido > legado
        base_score = score_combined
        if base_score is None:
            # Se veio do legado, o content_score estava no slot "bm25" na coerção
            base_score = score_bm25 if score_bm25 is not None else 0.0

        final_score, boosts = _apply_boosts(base_score, cand, q_tokens, cfg)
        enriched.append(
            ScoredCandidate(
                candidate=cand,
                match_score=final_score,
                applied_boosts=boosts,
                base_score=base_score,
                score_semantic=score_sem,
                score_bm25=score_bm25,
                score_combined=score_combined,
            )
        )

    # Threshold primário
    filtered = [sc for sc in enriched if sc.match_score >= threshold]

    # Dedup por publicId (mantém maior score)
    def _dedup(items: List[ScoredCandidate]) -> List[ScoredCandidate]:
        best_by_id: Dict[str, ScoredCandidate] = {}
        for sc in items:
            pid = str(sc.candidate.publicId)
            prev = best_by_id.get(pid)
            if (prev is None) or (sc.match_score > prev.match_score):
                best_by_id[pid] = sc
        out = list(best_by_id.values())
        out.sort(key=lambda x: (-(x.match_score), (x.candidate.title or "").casefold(), str(x.candidate.publicId)))
        return out

    if not filtered:
        # Fallback de dominância (aceita top-1 “muito bom” mesmo sem bater threshold)
        dedup_all = _dedup(enriched)
        if dedup_all and dedup_all[0].match_score >= cfg.DOMINANCE_MIN_ACCEPT:
            return dedup_all[:1]
        return []

    deduped = _dedup(filtered)
    return deduped[:max_n]
