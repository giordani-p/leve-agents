# reco/ranker.py
"""
Regras de negócio do ranking:
- Recebe candidatos com content_score (0..1) vindos do indexer.
- Aplica boosts explicáveis (título/descrição, tags/tema, difficulty=Beginner).
- Faz cap do score em SCORE_CAP, aplica threshold, ordena desc.
- Deduplica por publicId e corta em até MAX_SUGGESTIONS.
- Regra de dominância: se ninguém passar do threshold, aceita top-1 se score >= DOMINANCE_MIN_ACCEPT.

Novidades:
- Tokenização e matching acento-insensíveis (casefold + strip de acentos).

Sem pandas; operações em listas/sets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple, Dict
import re
import unicodedata as _ud

from reco.config import RecoConfig
from schemas.trail_candidate import TrailCandidate


# Regex de palavra; após strip de acentos, cobre letras/dígitos em ASCII e Unicode.
_WORD_RE = re.compile(r"[a-zA-ZÀ-ÖØ-öø-ÿ0-9]+")


def _strip_accents(text: str) -> str:
    """
    Remove acentos de forma estável (NFKD), preservando apenas caracteres base.
    """
    if not text:
        return ""
    return "".join(ch for ch in _ud.normalize("NFKD", text) if not _ud.combining(ch))


def _tokenize(text: str) -> List[str]:
    """
    Tokenização simples, acento-insensível e case-insensível.
    """
    if not text:
        return []
    norm = _strip_accents(text).casefold()
    return [m.group(0) for m in _WORD_RE.finditer(norm)]


@dataclass
class ScoredCandidate:
    candidate: TrailCandidate
    match_score: float
    applied_boosts: List[str] = field(default_factory=list)


def _has_title_desc_keyword(cand: TrailCandidate, query_tokens: Iterable[str]) -> bool:
    """
    Verifica se alguma palavra-chave da consulta aparece no título/descrição/combined_text,
    de forma acento-insensível. Ignora tokens muito curtos (<=2 chars).
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
    Regras de boost:
      - TITLE_DESC_BOOST: se alguma keyword da consulta aparecer em título/descrição/conteúdo.
      - TAG_BOOST: se qualquer token de tag aparecer na consulta.
      - BEGINNER_BOOST: se difficulty == Beginner.
    """
    boosts_applied: List[str] = []
    score = float(base_score)

    # 0) Boost por título/descrição (palavra-chave da pergunta)
    if _has_title_desc_keyword(cand, query_tokens):
        score += cfg.TITLE_DESC_BOOST
        boosts_applied.append("title_desc_match")

    # 1) Boost por tags/tema (interseção entre tokens de tags e tokens da query)
    tag_tokens: List[str] = []
    for t in cand.tags or []:
        tag_tokens.extend(_tokenize(str(t)))
    qset = set(query_tokens)
    if tag_tokens and qset.intersection(tag_tokens):
        score += cfg.TAG_BOOST
        boosts_applied.append("tag_match")

    # 2) Boost leve para iniciantes (fase de descoberta)
    if (cand.difficulty or "").lower() == "beginner".lower():
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


def rank(
    scored_candidates: List[Tuple[TrailCandidate, float]],
    query_text: str,
    cfg: RecoConfig,
    max_results: Optional[int] = None,
) -> List[ScoredCandidate]:
    """
    Aplica boosts, threshold, ordenação, dedupe e top-N.
    Inclui fallback de dominância quando ninguém passa do threshold.
    """
    if not scored_candidates:
        return []

    max_n = max_results if isinstance(max_results, int) and max_results > 0 else cfg.MAX_SUGGESTIONS
    q_tokens = _tokenize(query_text)

    enriched: List[ScoredCandidate] = []
    for cand, content_score in scored_candidates:
        final_score, boosts = _apply_boosts(content_score, cand, q_tokens, cfg)
        enriched.append(ScoredCandidate(candidate=cand, match_score=final_score, applied_boosts=boosts))

    # Threshold primário
    filtered = [sc for sc in enriched if sc.match_score >= cfg.MATCH_THRESHOLD]

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
        # Fallback de dominância (catálogo pequeno): aceita top-1 se score >= DOMINANCE_MIN_ACCEPT
        dedup_all = _dedup(enriched)
        if dedup_all and dedup_all[0].match_score >= cfg.DOMINANCE_MIN_ACCEPT:
            return dedup_all[:1]
        return []

    deduped = _dedup(filtered)
    return deduped[:max_n]
