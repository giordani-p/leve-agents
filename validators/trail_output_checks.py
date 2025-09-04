# validators/trail_output_checks.py
"""
Regras de negócio do Sistema de Recomendação (CLI).
Aplica threshold de match, garante coerência de status/textos e normaliza o output.

Uso esperado no fluxo:
1) Validar com schemas.TrailOutput
2) Chamar apply_business_rules(output) antes de retornar ao CLI
"""

from __future__ import annotations

from typing import Optional, List, Dict
from copy import deepcopy

from pydantic import ValidationError

# Imports dos schemas
from schemas.trail_output import TrailOutput, SuggestedTrail, WebFallback  # WebFallback mantido por compatibilidade

# ---------------------------------------------------------------------
# Parâmetros de negócio (ajustáveis)
# ---------------------------------------------------------------------
MATCH_THRESHOLD: float = 0.75
MAX_SUGGESTIONS: int = 3
DEFAULT_FALLBACK_MESSAGE: str = (
    "No momento não encontrei trilhas publicadas que combinem com a sua dúvida. "
    "Você pode tentar reformular com uma palavra-chave (ex.: 'programação', 'carreira')."
)
DEFAULT_SHORT_ANSWER_EMPTY: str = (
    "Ainda não encontrei trilhas publicadas que combinem com a sua dúvida."
)
DEFAULT_CTA_EMPTY: str = "Tentar de novo"
DEFAULT_WHY_MATCH: str = "Combina com o que você buscou."


# ---------------------------------------------------------------------
# Utilitários internos
# ---------------------------------------------------------------------
def _strip_text(s: Optional[str]) -> Optional[str]:
    return s.strip() if isinstance(s, str) else s


def _strip_text_fields(o: TrailOutput) -> None:
    """Higieniza campos de texto (trim simples)."""
    o.short_answer = _strip_text(o.short_answer)
    o.cta = _strip_text(o.cta)
    if o.mensagem_padrao is not None:
        o.mensagem_padrao = _strip_text(o.mensagem_padrao)

    # Higieniza why_match das sugestões (se houver)
    if getattr(o, "suggested_trails", None):
        for s in o.suggested_trails or []:
            s.why_match = _strip_text(s.why_match) or ""


def _dedupe_keep_best(items: List[SuggestedTrail]) -> List[SuggestedTrail]:
    """
    Deduplica por publicId (preferencial) e, em ausência, por slug.
    Mantém o item de maior match_score.
    """
    best_by_key: Dict[str, SuggestedTrail] = {}
    for s in items:
        key = None
        if s.publicId is not None:
            key = f"pid:{s.publicId}"
        elif s.slug:
            key = f"slug:{s.slug.lower()}"
        else:
            # Sem identificador útil: cria uma chave efêmera por título para não perder totalmente
            key = f"title:{(s.title or '').lower()}"
        prev = best_by_key.get(key)
        if (prev is None) or (float(s.match_score) > float(prev.match_score)):
            best_by_key[key] = s
    out = list(best_by_key.values())
    # Ordenação determinística: score desc, depois título/UUID
    out.sort(key=lambda x: (-(float(x.match_score)), (x.title or "").casefold(), str(x.publicId)))
    return out


def _enforce_threshold(items: List[SuggestedTrail], threshold: float) -> List[SuggestedTrail]:
    return [s for s in items if float(s.match_score) >= threshold]


def _cap_suggestions(items: List[SuggestedTrail], max_n: int) -> List[SuggestedTrail]:
    max_n = max(1, min(int(max_n), MAX_SUGGESTIONS))
    return items[:max_n]


def _ensure_suggestions_list(o: TrailOutput) -> List[SuggestedTrail]:
    """
    Normaliza acesso às sugestões como lista (compat com contratos anteriores que tinham 'suggested_trail').
    """
    suggestions = getattr(o, "suggested_trails", None)
    if suggestions is None and hasattr(o, "suggested_trail"):
        one = getattr(o, "suggested_trail")
        suggestions = [one] if one is not None else []
    return suggestions or []


def _write_suggestions_list(o: TrailOutput, items: Optional[List[SuggestedTrail]]) -> None:
    """Escreve de volta a lista de sugestões de forma compatível."""
    if hasattr(o, "suggested_trails"):
        o.suggested_trails = items if items else None
    if hasattr(o, "suggested_trail"):
        # Em contrato antigo, zera item único
        o.suggested_trail = None


def _fill_missing_why_match(items: List[SuggestedTrail]) -> None:
    """Garante why_match com >= 5 chars para cada sugestão."""
    for s in items:
        wm = (s.why_match or "").strip()
        if len(wm) < 5:
            s.why_match = DEFAULT_WHY_MATCH


def _ensure_status_coherence(o: TrailOutput) -> None:
    """
    Regras de coerência entre status e payload:
    - status="ok": precisa ter pelo menos 1 sugestão (lista não-vazia).
    - status="fora_do_escopo": não pode ter sugestões; exige mensagem_padrao; ajusta textos.
    """
    suggestions = _ensure_suggestions_list(o)
    has_trails = bool(suggestions)
    has_fallback = bool(getattr(o, "web_fallback", None))  # não usamos nesta fase, mas mantemos compatibilidade

    if o.status == "ok":
        if not has_trails and not has_fallback:
            # Sem orientação útil: força fora_do_escopo + mensagens coerentes
            o.status = "fora_do_escopo"
            o.mensagem_padrao = o.mensagem_padrao or DEFAULT_FALLBACK_MESSAGE
            _write_suggestions_list(o, None)
            o.web_fallback = None
            o.short_answer = DEFAULT_SHORT_ANSWER_EMPTY
            o.cta = DEFAULT_CTA_EMPTY

    elif o.status == "fora_do_escopo":
        # Em fora_do_escopo não retornamos recomendações
        _write_suggestions_list(o, None)
        o.web_fallback = None
        o.mensagem_padrao = o.mensagem_padrao or DEFAULT_FALLBACK_MESSAGE
        # garante coerência textual
        o.short_answer = DEFAULT_SHORT_ANSWER_EMPTY
        o.cta = DEFAULT_CTA_EMPTY


# ---------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------
def apply_business_rules(output: TrailOutput) -> TrailOutput:
    """
    Aplica as regras de negócio sobre um TrailOutput já validado pelo schema:
    - Limpeza/higienização de textos.
    - Threshold de similaridade (≥ MATCH_THRESHOLD) para cada sugestão.
    - Deduplicação por publicId/slug; ordenação e corte top-N (até MAX_SUGGESTIONS).
    - Preenchimento de why_match quando vier curto/vazio.
    - Coerência entre status e payload (inclui textos de fora_do_escopo).
    - Revalidação final com Pydantic.
    """
    o = deepcopy(output)

    # 1) Limpeza/higienização simples
    _strip_text_fields(o)

    # 2) Normalizações de sugestões (quando existirem)
    suggestions = _ensure_suggestions_list(o)
    if suggestions:
        # 2.1) Aplica threshold por item
        suggestions = _enforce_threshold(suggestions, MATCH_THRESHOLD)

        # 2.2) Dedup + ordenação determinística
        suggestions = _dedupe_keep_best(suggestions)

        # 2.3) Garante no máximo MAX_SUGGESTIONS
        suggestions = _cap_suggestions(suggestions, MAX_SUGGESTIONS)

        # 2.4) Why_match mínimo
        _fill_missing_why_match(suggestions)

        # Escreve de volta (ou zera se ficou vazio)
        _write_suggestions_list(o, suggestions if suggestions else None)

    # 3) Coerência de status vs payload (ajusta textos quando vira fora_do_escopo)
    _ensure_status_coherence(o)

    # 4) Revalida contra o schema (garante consistência final)
    try:
        o = TrailOutput.model_validate(o.model_dump())
    except ValidationError as ve:
        # Propaga com mensagem clara
        raise ve

    return o
