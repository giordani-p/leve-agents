# reco/query_builder.py
"""
Construção do texto de consulta (query_text) usado pelo indexer.

Princípios:
- A base da consulta é SEMPRE a 'user_question'.
- Opcionalmente adicionamos até 2 pistas do snapshot (ex.: objetivos/dificuldades).
- Opcionalmente adicionamos uma expansão leve por sinônimos da pergunta (configurável).
- Mantemos a consulta simples e legível, separando blocos com ' || '.

Novidades:
- Normalização acento-insensível para análise de tokens.
- Expansão leve de termos por sinônimos vindos da config (sem exagero).

Observações:
- A escolha de pistas do snapshot é heurística e não intrusiva: evita termos genéricos
  e respeita o limite configurado (SNAPSHOT_MAX_HINTS).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Iterable
import re
import unicodedata as _ud

from reco.config import RecoConfig


GENERIC_MARKERS = {
    "não informado",
    "nao informado",
    "n/a",
    "nenhum",
    "none",
}

_WORD_RE = re.compile(r"[a-zA-ZÀ-ÖØ-öø-ÿ0-9]+")


def _strip_accents(text: str) -> str:
    if not text:
        return ""
    return "".join(ch for ch in _ud.normalize("NFKD", text) if not _ud.combining(ch))


def _clean(s: str) -> str:
    return " ".join((s or "").strip().split())


def _tokenize_norm(text: str) -> List[str]:
    """
    Tokenização acento-insensível e case-insensível.
    """
    if not text:
        return []
    norm = _strip_accents(text).casefold()
    return [m.group(0) for m in _WORD_RE.finditer(norm)]


def _valid_hint(text: str) -> bool:
    if not text:
        return False
    t = _clean(text).casefold()
    if len(t) < 3:
        return False
    return t not in GENERIC_MARKERS


def _extract_snapshot_hints(snapshot: Dict, max_hints: int) -> List[str]:
    """
    Extrai até 'max_hints' frases curtas do snapshot, priorizando objetivos e dificuldades.
    """
    hints: List[str] = []

    # 1) Objetivos detectados
    for item in (snapshot.get("objetivos_detectados") or []):
        if isinstance(item, str) and _valid_hint(item):
            hints.append(_clean(item))
            if len(hints) >= max_hints:
                return hints

    # 2) Dificuldades detectadas
    for item in (snapshot.get("dificuldades_detectadas") or []):
        if isinstance(item, str) and _valid_hint(item):
            hints.append(_clean(item))
            if len(hints) >= max_hints:
                return hints

    # 3) Características-chave
    for item in (snapshot.get("caracteristicas_chave") or []):
        if isinstance(item, str) and _valid_hint(item):
            hints.append(_clean(item))
            if len(hints) >= max_hints:
                return hints

    # 4) Macroperfil (último recurso)
    mp = snapshot.get("macroperfil")
    if isinstance(mp, str) and _valid_hint(mp) and len(hints) < max_hints:
        hints.append(_clean(mp))

    return hints[:max_hints]        

def _expand_synonyms(
    user_question: str,
    cfg: RecoConfig,
    max_synonyms: int = 6,
) -> List[str]:
    """
    Expande levemente a pergunta com sinônimos/variações da config.
    - Apenas tokens com len > 3.
    - Usa dict de sinônimos já normalizado (lower/acento-removido) em RecoConfig.
    - Evita duplicatas e limita a 'max_synonyms' termos para não poluir a consulta.
    """
    if not (cfg.USE_QUERY_SYNONYMS and cfg.QUERY_SYNONYMS):
        return []

    toks = _tokenize_norm(user_question)
    keys = set(t for t in toks if len(t) > 3)

    collected: List[str] = []
    seen = set()

    for key in keys:
        syns = cfg.QUERY_SYNONYMS.get(key)
        if not syns:
            continue
        for s in syns:
            s_norm = _strip_accents(s).casefold().strip()
            if not s_norm or s_norm in seen:
                continue
            seen.add(s_norm)
            collected.append(s)  # preserva forma original definida na config
            if len(collected) >= max_synonyms:
                return collected

    return collected


def build(
    user_question: str,
    snapshot: Optional[Dict],
    cfg: RecoConfig,
    contexto_extra: Optional[str] = None,
) -> str:
    """
    Monta o texto final de consulta.

    Retorno:
      - String de consulta no formato: "user_question || hint1; hint2 || contexto_extra || syn1; syn2; ..."
        (blocos opcionais só aparecem quando têm conteúdo válido).
    """
    blocks: List[str] = []

    # Base: pergunta do jovem
    uq = _clean(user_question)
    if uq:
        blocks.append(uq)

    # Pistas do snapshot (se habilitadas)
    if cfg.USE_SNAPSHOT_HINTS and snapshot:
        snap_hints = _extract_snapshot_hints(snapshot, max_hints=cfg.SNAPSHOT_MAX_HINTS)
        if snap_hints:
            blocks.append("; ".join(snap_hints))

    # Contexto extra (se vier)
    cx = _clean(contexto_extra or "")
    if cx:
        blocks.append(cx)

    # Expansão por sinônimos (leve, controlada por config)
    syns: List[str] = _expand_synonyms(user_question, cfg)
    if syns:
        # Mantém em um bloco próprio; termos separados por '; ' para legibilidade
        blocks.append("; ".join(syns))

    # Garante que sempre haja ao menos a user_question
    if not blocks:
        blocks.append("")

    return " || ".join(blocks)
