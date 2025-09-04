# reco/explainer.py
"""
Geração do texto de 'por que indicar' (why_match) para cada sugestão.

Princípios:
- Tom cordial e jovem.
- Frase curta (1 a 2 ideias principais).
- Baseada em sinais explicáveis: match de tema/tags, nível (Beginner) e pistas do conteúdo.

Novidades:
- Tokenização e matching acento-insensíveis (casefold + strip de acentos).
"""

from __future__ import annotations

from typing import Iterable, List, Optional
import re
import unicodedata as _ud

from reco.ranker import ScoredCandidate
from schemas.trail_candidate import TrailCandidate


_WORD_RE = re.compile(r"[a-zA-ZÀ-ÖØ-öø-ÿ0-9]+")


def _strip_accents(text: str) -> str:
    if not text:
        return ""
    return "".join(ch for ch in _ud.normalize("NFKD", text) if not _ud.combining(ch))


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    norm = _strip_accents(text).casefold()
    return [m.group(0) for m in _WORD_RE.finditer(norm)]


def _best_tag_match(cand: TrailCandidate, query_tokens: Iterable[str]) -> Optional[str]:
    """
    Retorna uma tag representativa do candidato que apareceu na consulta (se houver).
    A comparação é acento-insensível, mas o retorno preserva a grafia original.
    """
    qset = set(query_tokens)
    for t in (cand.tags or []):
        toks = _tokenize(str(t))
        if set(toks) & qset:
            return str(t)  # preserva forma original para exibição
    return None


def _content_cues(cand: TrailCandidate) -> List[str]:
    """
    Infere 'cues' (pistas de formato/estilo) a partir da descrição/combined_text.
    Exemplos: aulas curtas, conteúdos práticos, tem vídeos, tem quizzes.
    Matching acento-insensível.
    """
    text_raw = f"{cand.description or ''} | {cand.combined_text or ''}"
    text = _strip_accents(text_raw).casefold()

    cues: List[str] = []

    # Aulas curtas
    if "curt" in text:  # cobre 'curto', 'curtas'
        cues.append("aulas curtas")

    # Conteúdo prático / exercícios
    if "exerc" in text or "pratic" in text:  # cobre 'prática', 'praticos'
        cues.append("conteúdos práticos")

    # Vídeos
    if "video" in text:
        cues.append("tem vídeos")

    # Quizzes
    if "quiz" in text:
        cues.append("tem quizzes")

    # Evita repetição e limita a no máximo 2 cues
    seen = set()
    deduped = []
    for c in cues:
        if c not in seen:
            seen.add(c)
            deduped.append(c)
        if len(deduped) >= 2:
            break

    return deduped


def make_reason(scored: ScoredCandidate, query_text: str) -> str:
    """
    Monta a frase final de why_match com no máx. ~180 caracteres.
    Ex.: "Conecta com JavaScript e é nível iniciante — aulas curtas."
    """
    cand = scored.candidate
    q_tokens = _tokenize(query_text)

    parts: List[str] = []

    # Tema/tag principal (mostra com grafia original)
    tag = _best_tag_match(cand, q_tokens)
    beginner = (cand.difficulty or "").lower() == "beginner".lower()

    if tag and beginner:
        parts.append(f"Conecta com {tag} e é nível iniciante")
    elif tag:
        parts.append(f"Conecta com {tag}")
    elif beginner:
        parts.append("Boa porta de entrada (nível iniciante)")
    else:
        parts.append("Combina com o que você buscou")

    # Cues de formato/estilo
    cues = _content_cues(cand)
    if cues:
        parts.append(" — " + ", ".join(cues))

    reason = ". ".join([p for p in parts if p])
    reason = reason.replace(".  —", " —").replace(". —", " —")

    if len(reason) > 180:
        reason = reason[:177].rstrip() + "..."

    return reason
