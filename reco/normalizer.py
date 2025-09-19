# reco/normalizer.py
"""
Normalizador de Dados - Leve Agents

Responsável pela normalização e limpeza de dados do catálogo de trilhas educacionais.
Converte dados brutos em formatos padronizados e aplica filtros de qualidade.

Funcionalidades:
- Conversão de dados brutos para TrailCandidate (schema padronizado)
- Preenchimento automático de campos ausentes (combined_text)
- Filtragem por status permitido (case-insensitive)
- Deduplicação por publicId mantendo maior completude
- Ordem estável para evitar flutuações no pipeline
- Validação de dados obrigatórios
- Logging de operações para observabilidade
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Optional
from uuid import UUID
import logging

from schemas.trail_candidate import TrailCandidate
from reco.config import RecoConfig

logger = logging.getLogger(__name__)


# -----------------------------
# Conversão básica
# -----------------------------
def to_candidates(raw_items: List[Dict]) -> List[TrailCandidate]:
    """
    Converte a lista bruta do catálogo em TrailCandidate.
    Ignora entradas inválidas (loga aviso); lança erro apenas se nada restar.
    """
    candidates: List[TrailCandidate] = []
    for i, item in enumerate(raw_items or []):
        try:
            cand = TrailCandidate.from_source(item)  # validações no schema
            # Higienização leve (não altera semântica)
            cand = _sanitize_candidate(cand)
            candidates.append(cand)
        except Exception as e:
            logger.warning("Normalizer: ignorando item inválido na posição %s (%s)", i, e)
            continue

    if not candidates:
        raise ValueError("Nenhuma trilha válida encontrada após normalização.")
    return candidates


def _sanitize_candidate(c: TrailCandidate) -> TrailCandidate:
    """Limpa espaços e normaliza alguns campos para consistência no pipeline."""
    try:
        title = (c.title or "").strip()
        slug = (c.slug or "").strip()
        description = (c.description or "").strip()
        subtitle = (getattr(c, "subtitle", None) or "").strip()
        difficulty = (c.difficulty or "").strip()
        status = (c.status or "").strip()

        # Não altera tags/topicos além de garantir listas
        tags = list(c.tags or []) if isinstance(c.tags, list) else []
        topics = list(c.topics or []) if isinstance(c.topics, list) else []

        # combined_text deixamos como está; podemos preencher depois se vier vazio
        combined_text = c.combined_text

        return c.model_copy(
            update={
                "title": title,
                "slug": slug,
                "subtitle": subtitle or None,
                "description": description or None,
                "difficulty": difficulty.lower() or None,
                "status": status or None,
                "tags": tags,
                "topics": topics,
                "combined_text": combined_text,
            }
        )
    except Exception:
        # Se o schema não for Pydantic v2, cair para um update tolerante
        try:
            c.title = (c.title or "").strip()
            c.slug = (c.slug or "").strip()
            c.description = (c.description or "").strip()
            if hasattr(c, "subtitle"):
                c.subtitle = (getattr(c, "subtitle", "") or "").strip() or None
            if c.difficulty:
                c.difficulty = (c.difficulty or "").strip().lower() or None
            if c.status:
                c.status = (c.status or "").strip() or None
            if not isinstance(c.tags, list):
                c.tags = list(c.tags or [])
            if not isinstance(c.topics, list):
                c.topics = list(c.topics or [])
            return c
        except Exception:
            return c


# -----------------------------
# Status
# -----------------------------
def _norm_status(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    return s.strip().casefold()


def filter_by_status(candidates: List[TrailCandidate], allowed_status: Tuple[str, ...]) -> List[TrailCandidate]:
    """
    Retém apenas candidatos cujo status está em allowed_status (case-insensitive).
    Se o candidato não tiver status definido, ele é descartado por segurança.
    """
    allowed_norm = {(_norm_status(s) or "") for s in (allowed_status or ())}
    out: List[TrailCandidate] = []
    for c in candidates:
        st = _norm_status(getattr(c, "status", None))
        if st and st in allowed_norm:
            out.append(c)
    if not out:
        logger.warning("Normalizer: nenhum candidato restante após filtro de status (%s).", allowed_status)
    return out


# -----------------------------
# Completeness & dedupe
# -----------------------------
def _completeness_score(c: TrailCandidate) -> int:
    """
    Heurística simples de 'completude':
      +1 slug
      +1 title
      +1 difficulty
      +1 description
      +1 se houver >=1 tag
      +1 se houver combined_text
    """
    score = 0
    if getattr(c, "slug", None):
        score += 1
    if getattr(c, "title", None):
        score += 1
    if getattr(c, "difficulty", None):
        score += 1
    if getattr(c, "description", None):
        score += 1
    tags = getattr(c, "tags", None) or []
    if isinstance(tags, list) and len(tags) > 0:
        score += 1
    if getattr(c, "combined_text", None):
        score += 1
    return score


def _public_id_as_uuid(pid) -> Optional[UUID]:
    """
    Tenta padronizar publicId para UUID quando possível (sem quebrar se já for UUID).
    Retorna None se não for possível parsear.
    """
    if isinstance(pid, UUID):
        return pid
    try:
        return UUID(str(pid))
    except Exception:
        return None


def dedupe_by_public_id(candidates: List[TrailCandidate]) -> List[TrailCandidate]:
    """
    Remove duplicatas por publicId, mantendo o candidato de maior 'completude'.
    Em caso de empate, mantém o primeiro visto (estável).
    Retorna lista ordenada estavelmente por (title, slug, publicId-string).
    """
    best_by_id: Dict[str, TrailCandidate] = {}
    for c in candidates:
        pid_raw = getattr(c, "publicId", None)
        if pid_raw is None:
            logger.warning(
                "Normalizer: candidato sem publicId descartado (slug=%s, title=%s)",
                getattr(c, "slug", None),
                getattr(c, "title", None),
            )
            continue

        pid_uuid = _public_id_as_uuid(pid_raw)
        key = str(pid_uuid) if pid_uuid is not None else str(pid_raw)

        prev = best_by_id.get(key)
        if prev is None:
            best_by_id[key] = c
        else:
            if _completeness_score(c) > _completeness_score(prev):
                best_by_id[key] = c

    deduped = list(best_by_id.values())

    def _sort_key(x: TrailCandidate):
        title = (getattr(x, "title", "") or "").casefold()
        slug = (getattr(x, "slug", "") or "").casefold()
        pid_raw = getattr(x, "publicId", None)
        pid_uuid = _public_id_as_uuid(pid_raw)
        pid_str = str(pid_uuid) if pid_uuid is not None else str(pid_raw or "")
        return (title, slug, pid_str)

    deduped.sort(key=_sort_key)
    return deduped


# -----------------------------
# Combined text (opcional)
# -----------------------------
def build_combined_text(c: TrailCandidate) -> str:
    """
    Constrói um combined_text consistente com o pipeline denso/BM25 quando o campo vier vazio.
    """
    parts = [
        c.title or "",
        getattr(c, "subtitle", None) or "",
        c.description or "",
        " ".join(c.topics or []),
        " ".join(c.tags or []),
        c.combined_text or "",
    ]
    return " | ".join(p for p in parts if p)


def fill_missing_combined_text(candidates: List[TrailCandidate]) -> List[TrailCandidate]:
    """
    Retorna nova lista em que itens sem combined_text recebem um texto canônico.
    Útil para catálogos legados em que o backend ainda não preenche esse campo.
    """
    out: List[TrailCandidate] = []
    changed = 0
    for c in candidates:
        if (c.combined_text or "").strip():
            out.append(c)
            continue
        new_ct = build_combined_text(c)
        try:
            out.append(c.model_copy(update={"combined_text": new_ct}))
        except Exception:
            c.combined_text = new_ct  # fallback p/ modelos não-imutáveis
            out.append(c)
        changed += 1
    if changed:
        logger.info("Normalizer: preenchido combined_text em %d item(ns).", changed)
    return out
