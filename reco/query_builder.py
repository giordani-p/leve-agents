# reco/query_builder.py
"""
Construção do texto de consulta (query_text) — V4 / P1 Híbrido

Princípios:
- Base SEMPRE é 'user_question'.
- Adiciona até SNAPSHOT_MAX_HINTS pistas curtas do snapshot (novo modelo).
- (Opcional) Expansão leve por sinônimos da pergunta — apenas se USE_QUERY_SYNONYMS_DENSE=True.
  * Na P1, sinônimos para BM25 são tratados no indexer (USE_QUERY_SYNONYMS_BM25).
- Blocos separados por ' || ' para legibilidade.

Observações:
- Heurística não intrusiva (evita genéricos), prioriza objetivos e dificuldades.
- O mesmo 'query_text' é usado por denso e BM25; o BM25 faz expansão por conta própria.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Iterable, Any
import re
import unicodedata as _ud

from reco.config import RecoConfig

GENERIC_MARKERS = {
    "não informado",
    "nao informado",
    "n/a",
    "nenhum",
    "none",
    "desconhecido",
    "indefinido",
}

_WORD_RE = re.compile(r"[a-zA-ZÀ-ÖØ-öø-ÿ0-9]+")


# ----------------------------
# Helpers básicos
# ----------------------------
def _strip_accents(text: str) -> str:
    if not text:
        return ""
    return "".join(ch for ch in _ud.normalize("NFKD", text) if not _ud.combining(ch))


def _clean(s: str) -> str:
    return " ".join((s or "").strip().split())


def _tokenize_norm(text: str) -> List[str]:
    """Tokenização acento-insensível e case-insensível."""
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


def _apply_length_cap(text: str, cfg: RecoConfig) -> str:
    """Limita tamanho da query se QUERY_MAX_CHARS existir na config."""
    max_chars = int(getattr(cfg, "QUERY_MAX_CHARS", 0) or 0)
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip()


# ----------------------------
# Acesso seguro ao snapshot (novo modelo)
# ----------------------------
def _get(d: Dict[str, Any], path: str, default=None):
    """Acesso seguro via 'a.b.c'."""
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def _as_list(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, str):
        return [val]
    if isinstance(val, (list, tuple)):
        return [str(x) for x in val if isinstance(x, (str, int, float))]
    return []


def _collect_hints(snapshot: Dict[str, Any], max_hints: int) -> List[str]:
    """
    Extrai até 'max_hints' frases curtas do snapshot (novo modelo), priorizando:
      1) Objetivos (principal, específicos, curto prazo)
      2) Dificuldades/Barreiras
      3) Preferências de aprendizado
      4) Interesses & direção
      5) Perfil & talentos (curtos)
      6) Aspirações
      7) Contexto (apenas se sobrar espaço)
    """
    hints: List[str] = []

    def _add(items: Iterable[str]):
        nonlocal hints
        for it in items:
            if len(hints) >= max_hints:
                return
            if isinstance(it, str) and _valid_hint(it):
                hints.append(_clean(it))

    # 1) Objetivos
    _add(_as_list(_get(snapshot, "objetivos_carreira.objetivo_principal")))
    _add(_as_list(_get(snapshot, "objetivos_carreira.objetivos_especificos")))
    _add(_as_list(_get(snapshot, "objetivos_carreira.metas_temporais.curto_prazo")))

    if len(hints) >= max_hints:
        return hints

    # 2) Dificuldades / Barreiras
    _add(_as_list(_get(snapshot, "preferencias_aprendizado.dificuldades_aprendizado")))
    _add(_as_list(_get(snapshot, "situacao_academica.materias_dificuldade")))
    _add(_as_list(_get(snapshot, "barreiras_desafios.tecnicas")))
    _add(_as_list(_get(snapshot, "barreiras_desafios.sociais")))
    _add(_as_list(_get(snapshot, "barreiras_desafios.financeiras")))
    _add(_as_list(_get(snapshot, "barreiras_desafios.geograficas")))

    if len(hints) >= max_hints:
        return hints

    # 3) Preferências de aprendizado (compacta para frases curtas)
    modalidade = _get(snapshot, "preferencias_aprendizado.modalidade_preferida")
    ritmo = _get(snapshot, "preferencias_aprendizado.ritmo_aprendizado")
    horario = _get(snapshot, "preferencias_aprendizado.horario_estudo")
    recursos = _as_list(_get(snapshot, "preferencias_aprendizado.recursos_preferidos"))
    pref_parts = []
    if _valid_hint(str(modalidade or "")):
        pref_parts.append(f"Preferência: {modalidade}")
    if _valid_hint(str(ritmo or "")):
        pref_parts.append(f"Ritmo: {ritmo}")
    if _valid_hint(str(horario or "")):
        pref_parts.append(f"Horário: {horario}")
    if recursos:
        pref_parts.append("Recursos: " + ", ".join([_clean(r) for r in recursos[:3]]))
    if pref_parts and len(hints) < max_hints:
        _add(["; ".join(pref_parts)])

    if len(hints) >= max_hints:
        return hints

    # 4) Interesses & direção
    _add(_as_list(_get(snapshot, "interesses_pessoais.areas_curiosidade")))
    _add(_as_list(_get(snapshot, "interesses_pessoais.atividades_extracurriculares")))
    _add(_as_list(_get(snapshot, "interesses_pessoais.consumo_midia")))
    _add(_as_list(_get(snapshot, "situacao_academica.materias_favoritas")))

    if len(hints) >= max_hints:
        return hints

    # 5) Perfil & talentos (curtos)
    _add(_as_list(_get(snapshot, "perfil_disc.caracteristicas_chave")))
    _add(_as_list(_get(snapshot, "perfil_disc.areas_compatibilidade")))
    _add(_as_list(_get(snapshot, "perfil_disc.pontos_atencao")))
    _add(_as_list(_get(snapshot, "talentos_cliftonstrengths.talentos_dominantes")))
    if len(hints) < max_hints:
        _add(_as_list(_get(snapshot, "talentos_cliftonstrengths.talentos_secundarios")))

    if len(hints) >= max_hints:
        return hints

    # 6) Aspirações (campos curtos)
    _add(_as_list(_get(snapshot, "aspiracoes_profissionais.tipo_empresa")))
    _add(_as_list(_get(snapshot, "aspiracoes_profissionais.tamanho_equipe")))
    _add(_as_list(_get(snapshot, "aspiracoes_profissionais.disponibilidade_tempo")))
    _add(_as_list(_get(snapshot, "aspiracoes_profissionais.impacto_desejado")))

    if len(hints) >= max_hints:
        return hints

    # 7) Contexto (apenas se sobrar espaço)
    _add(_as_list(_get(snapshot, "dados_pessoais.localizacao")))
    _add(_as_list(_get(snapshot, "contexto_socioeconomico.origem")))

    return hints[:max_hints]


def _expand_synonyms_dense(
    user_question: str,
    cfg: RecoConfig,
    max_synonyms: int = 6,
) -> List[str]:
    """
    Expansão leve apenas para o caminho DENSO (se habilitada em config).
    *Na P1, essa flag deve ficar False; BM25 expande por conta própria.
    """
    if not (getattr(cfg, "USE_QUERY_SYNONYMS_DENSE", False) and getattr(cfg, "QUERY_SYNONYMS", None)):
        return []

    toks = _tokenize_norm(user_question)
    keys = set(t for t in toks if len(t) > 3)

    collected: List[str] = []
    seen = set()

    synonyms_map = getattr(cfg, "QUERY_SYNONYMS", {}) or {}
    for key in keys:
        syns = synonyms_map.get(key)
        if not syns:
            continue
        for s in syns:
            s_norm = _strip_accents(s).casefold().strip()
            if not s_norm or s_norm in seen:
                continue
            seen.add(s_norm)
            collected.append(_clean(s))
            if len(collected) >= max_synonyms:
                return collected
    return collected


# ----------------------------
# API principal
# ----------------------------
def build(
    user_question: str,
    snapshot: Optional[Dict],
    cfg: RecoConfig,
    contexto_extra: Optional[str] = None,
) -> str:
    """
    Monta o texto final de consulta único (usado por denso e BM25).
    BM25 fará sua própria expansão de sinônimos internamente.
    """
    blocks: List[str] = []

    # 1) Base: pergunta do jovem
    uq = _clean(user_question)
    if uq:
        blocks.append(uq)

    # 2) Pistas do snapshot
    if getattr(cfg, "USE_SNAPSHOT_HINTS", True) and isinstance(snapshot, dict):
        max_hints = int(getattr(cfg, "SNAPSHOT_MAX_HINTS", 2) or 2)
        snap_hints = _collect_hints(snapshot, max_hints=max_hints)
        if snap_hints:
            blocks.append("; ".join(snap_hints))

    # 3) Contexto extra
    cx = _clean(contexto_extra or "")
    if cx:
        blocks.append(cx)

    # 4) Expansão de sinônimos (somente se habilitada para DENSO — por padrão, False na P1)
    syns: List[str] = _expand_synonyms_dense(user_question, cfg)
    if syns:
        blocks.append("; ".join(syns))

    # Montagem final
    blocks = [b for b in (blocks or []) if b]
    if not blocks:
        blocks = [""]

    query_text = " || ".join(blocks)
    query_text = _apply_length_cap(query_text, cfg)
    return query_text


# Alias compatível
def build_query(
    user_question: str,
    snapshot: Optional[Dict],
    cfg: RecoConfig,
    contexto_extra: Optional[str] = None,
) -> str:
    return build(user_question=user_question, snapshot=snapshot, cfg=cfg, contexto_extra=contexto_extra)
