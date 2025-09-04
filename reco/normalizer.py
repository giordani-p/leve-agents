# reco/normalizer.py
"""
Normalização do catálogo de trilhas:
- Converte cada item bruto (dict) em TrailCandidate.
- Opcionalmente filtra por status permitido (ex.: Published).
- Deduplica por publicId, mantendo o candidato de maior completude (heurística simples).

Observações:
- publicId é obrigatório em TrailCandidate (validação no from_source).
- O filtro por status pode ser aplicado aqui ou no pipeline; expomos utilitários para ambos os casos.
"""

from __future__ import annotations

from typing import Dict, List, Tuple
from uuid import UUID

from schemas.trail_candidate import TrailCandidate
from reco.config import RecoConfig


def to_candidates(raw_items: List[Dict]) -> List[TrailCandidate]:
    """
    Converte a lista bruta do catálogo em TrailCandidate.
    Ignora entradas inválidas, levantando erro somente quando não houver nenhum válido.
    """
    candidates: List[TrailCandidate] = []
    for i, item in enumerate(raw_items):
        try:
            cand = TrailCandidate.from_source(item)
            candidates.append(cand)
        except Exception as e:
            # Entrada inválida é ignorada com fallback silencioso;
            # em um ambiente produtivo poderíamos logar um warning.
            continue

    if not candidates:
        raise ValueError("Nenhuma trilha válida encontrada após normalização.")
    return candidates


def filter_by_status(candidates: List[TrailCandidate], allowed_status: Tuple[str, ...]) -> List[TrailCandidate]:
    """
    Retém apenas candidatos cujo status está em allowed_status.
    Se o candidato não tiver status definido, ele é descartado por segurança.
    """
    allowed = set(allowed_status or ())
    return [c for c in candidates if (c.status in allowed)]


def _completeness_score(c: TrailCandidate) -> int:
    """
    Heurística simples para escolher entre duplicatas:
    mais pontos para quem tem slug, difficulty e descrição preenchidos.
    """
    score = 0
    if c.slug:
        score += 1
    if c.difficulty:
        score += 1
    if c.description:
        score += 1
    return score


def dedupe_by_public_id(candidates: List[TrailCandidate]) -> List[TrailCandidate]:
    """
    Remove duplicatas por publicId, mantendo o candidato de maior 'completude'.
    """
    best_by_id: Dict[UUID, TrailCandidate] = {}
    for c in candidates:
        pid = c.publicId
        prev = best_by_id.get(pid)
        if prev is None:
            best_by_id[pid] = c
        else:
            if _completeness_score(c) > _completeness_score(prev):
                best_by_id[pid] = c
    return list(best_by_id.values())
