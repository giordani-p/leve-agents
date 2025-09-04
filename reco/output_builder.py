# reco/output_builder.py
"""
Constrói o objeto TrailOutput a partir dos candidatos ranqueados.
- Quando houver 1..N sugestões (N ≤ max_results): status="ok", suggested_trails preenchido.
- Quando não houver: status="fora_do_escopo", mensagem padrão e nenhuma sugestão.

Atualização (Opção B):
- Recebe 'reasons_by_id' (dict {publicId -> why_match}) e já cria cada SuggestedTrail
  com 'why_match' preenchido (sem placeholder), evitando erro de validação.

Observações:
- 'short_answer' é sempre obrigatório (inclusive em fora_do_escopo).
- 'cta' é curto e direto ("Começar trilha" no caso OK; "Tentar de novo" se vazio).
- 'web_fallback' não é utilizado nesta fase (mantém None).
"""

from __future__ import annotations

from typing import Dict, List, Optional
import re

from schemas.trail_output import (
    TrailOutput,
    SuggestedTrail,
    QueryUnderstanding,
)
from reco.ranker import ScoredCandidate


_WORD_RE = re.compile(r"[a-zA-ZÀ-ÖØ-öø-ÿ0-9]+")

DEFAULT_EMPTY_MESSAGE = (
    "No momento não encontrei trilhas publicadas que combinem com a sua dúvida. "
    "Você pode tentar reformular com uma palavra-chave (ex.: 'programação', 'carreira')."
)


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [m.group(0).casefold() for m in _WORD_RE.finditer(text)]


def _infer_theme(query_text: str) -> str:
    """
    Heurística simples para tema principal: pega a palavra 'significativa' mais longa.
    Fica legível para logs/telemetria (QueryUnderstanding.tema).
    """
    tokens = _tokenize(query_text)
    if not tokens:
        return "não informado"
    tokens_sorted = sorted(tokens, key=len, reverse=True)
    for t in tokens_sorted:
        if len(t) >= 4:
            return t
    return tokens_sorted[0]


def _keywords(query_text: str, limit: int = 5) -> List[str]:
    """
    Extrai até 'limit' palavras-chave distintas da consulta, em ordem de ocorrência.
    """
    seen = set()
    out: List[str] = []
    for tok in _tokenize(query_text):
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
        if len(out) >= limit:
            break
    return out


def build_output(
    ranked: List[ScoredCandidate],
    query_text: str,
    max_results: int = 3,
    reasons_by_id: Optional[Dict[str, str]] = None,
) -> TrailOutput:
    """
    Cria o TrailOutput final (sem aplicar o validator de regras — isso é feito fora).

    Parâmetros:
      - ranked: lista ranqueada de ScoredCandidate (já com match_score final).
      - query_text: pergunta do jovem (+ pistas), usada para entendimento/telemetria.
      - max_results: limite superior de itens a exibir (1..3).
      - reasons_by_id: dicionário {publicId(str) -> why_match(str)} para preencher cada sugestão.
    """
    reasons_by_id = reasons_by_id or {}
    theme = _infer_theme(query_text)
    kws = _keywords(query_text, limit=5)

    # Se não houver sugestões após ranking/threshold, retorna fora_do_escopo
    if not ranked:
        return TrailOutput(
            status="fora_do_escopo",
            mensagem_padrao=DEFAULT_EMPTY_MESSAGE,
            short_answer="Ainda não encontrei trilhas publicadas que combinem com a sua dúvida.",
            suggested_trails=None,
            web_fallback=None,
            cta="Tentar de novo",
            query_understanding=QueryUnderstanding(tema=theme, palavras_chave=kws),
        )

    # Monta até 'max_results' sugestões com why_match e match_score
    topk = ranked[: max(1, min(max_results, len(ranked)))]

    suggestions: List[SuggestedTrail] = []
    for sc in topk:
        cand = sc.candidate
        pid_str = str(cand.publicId) if cand.publicId is not None else None
        reason = reasons_by_id.get(pid_str) if pid_str else None
        if not reason or len(reason.strip()) < 5:
            # Fallback de segurança (não deve ocorrer se reasons_by_id foi gerado do 'ranked')
            reason = "Combina com o que você buscou."

        suggestions.append(
            SuggestedTrail(
                publicId=cand.publicId,
                slug=cand.slug,
                title=cand.title,
                why_match=reason.strip(),
                match_score=float(sc.match_score),
            )
        )

    # Short answer amigável e direta (2–3 linhas curtas)
    short_answer = (
        "Boa! Encontrei algumas trilhas que combinam com o que você buscou. "
        "Dá pra começar pelo básico e ir testando o ritmo."
    )

    return TrailOutput(
        status="ok",
        mensagem_padrao=None,
        short_answer=short_answer,
        suggested_trails=suggestions,
        web_fallback=None,
        cta="Começar trilha",
        query_understanding=QueryUnderstanding(tema=theme, palavras_chave=kws),
    )
