# validators/output_checks.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

from pydantic import ValidationError
from schemas.advisor_output import OutputAdvisor, Modality, Option, Source

# Para checagem HTTP opcional (pode desabilitar em ambiente offline)
try:
    import requests  # type: ignore
    REQUESTS_AVAILABLE = True
except Exception:  # pragma: no cover
    REQUESTS_AVAILABLE = False


@dataclass
class ValidationResult:
    """Resultado consolidado das checagens."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    normalized: Optional[OutputAdvisor] = None
    url_status: Optional[Dict[str, int]] = None


# ---------------------------
# Normalização e parsing
# ---------------------------

def parse_and_normalize(raw_json: dict) -> Tuple[Optional[OutputAdvisor], List[str]]:
    """
    Faz o parse do JSON no schema OutputContract e aplica normalizações leves.
    Retorna o objeto normalizado e uma lista de erros de schema (se houver).
    """
    errors: List[str] = []
    try:
        contract = OutputAdvisor.model_validate(raw_json)
    except ValidationError as ve:
        errors.append(f"Schema inválido: {ve}")
        return None, errors

    # Normalizações leves (semântica de apresentação)
    # 1) Aparar espaços em summary e general_next_steps
    contract.summary = contract.summary.strip()
    contract.general_next_steps = [s.strip() for s in contract.general_next_steps]

    # 2) Em options: aparar espaços e manter modality como enum
    normalized_options: List[Option] = []
    for opt in contract.options:
        normalized_options.append(
            Option(
                rank=opt.rank,
                type=opt.type,
                title=opt.title.strip(),
                institution=opt.institution.strip() if opt.institution else None,
                modality=opt.modality,  # já é Enum; não normalizamos aqui
                duration=opt.duration.strip() if opt.duration else None,
                prerequisites=opt.prerequisites.strip(),
                cost_info=opt.cost_info.strip(),
                scholarships_info=opt.scholarships_info.strip(),
                official_url=opt.official_url,
                why_recommended=opt.why_recommended.strip(),
                next_steps=[s.strip() for s in opt.next_steps],
                compatibility_score=opt.compatibility_score,
            )
        )
    contract.options = normalized_options

    # 3) Em sources: aparar title
    normalized_sources: List[Source] = []
    for s in contract.sources:
        normalized_sources.append(
            Source(
                title=s.title.strip(),
                url=str(s.url),
                accessed_at=s.accessed_at,
            )
        )
    contract.sources = normalized_sources

    return contract, errors


# ---------------------------
# Regras de negócio
# ---------------------------

def check_unique_ranks(contract: OutputAdvisor) -> List[str]:
    """Garante que não há ranks duplicados em options."""
    ranks = [o.rank for o in contract.options]
    dups = {r for r in ranks if ranks.count(r) > 1}
    return [f"Ranks duplicados: {sorted(dups)}"] if dups else []


def check_summary_quality(contract: OutputAdvisor) -> List[str]:
    """
    Heurística simples para '2–3 linhas':
    - Contar quebras de linha e número de frases.
    """
    errors: List[str] = []
    text = contract.summary
    line_count = len([ln for ln in text.splitlines() if ln.strip()])
    # Contagem de frases simples por ponto final
    sentence_count = max(1, text.count("."))
    if line_count == 0:
        errors.append("Resumo vazio após normalização.")
    if sentence_count < 1:
        errors.append("Resumo parece não conter frases completas.")
    if len(text) > 400:
        errors.append("Resumo excede 400 caracteres.")
    return errors


def check_next_steps_quality(contract: OutputAdvisor) -> List[str]:
    """Valida quantidade e tamanho de cada passo."""
    errors: List[str] = []
    if not (2 <= len(contract.general_next_steps) <= 5):
        errors.append("general_next_steps deve conter entre 2 e 5 itens.")
    for i, step in enumerate(contract.general_next_steps, start=1):
        if not (5 <= len(step) <= 140):
            errors.append(f"general_next_steps[{i}] fora do tamanho esperado (5–140 chars).")
    return errors


def check_modality_against_preference(contract: OutputAdvisor, preferencia: Optional[str]) -> List[str]:
    """
    Coerência mínima entre 'preferencia' do usuário e as opções retornadas.
    - Se preferencia mencionar EAD/presencial/híbrido, pelo menos uma opção deve atender.
    """
    if not preferencia:
        return []

    pref = preferencia.lower()
    wants_ead = "ead" in pref or "EAD" in pref
    wants_presencial = "presencial" in pref or "Presencial" in pref
    wants_hibrido = "híbrido" in pref or "Híbrido" in pref or "hibrido" in pref or "Hibrido" in pref

    if not any([wants_ead, wants_presencial, wants_hibrido]):
        return []  # Nada a checar sobre modalidade

    matches = 0
    for o in contract.options:
        if wants_ead and o.modality == Modality.ead:
            matches += 1
        if wants_presencial and o.modality == Modality.presencial:
            matches += 1
        if wants_hibrido and o.modality == Modality.hibrido:
            matches += 1

    return [] if matches >= 1 else [
        "Nenhuma opção atende à modalidade preferida (EAD/presencial/híbrido)."
    ]


def check_sources_basic(contract: OutputAdvisor) -> List[str]:
    """Validações básicas de fontes: datas e quantidade."""
    errors: List[str] = []
    today = date.today()
    if len(contract.sources) < 1:
        errors.append("É obrigatório informar pelo menos 1 fonte.")
    for i, s in enumerate(contract.sources, start=1):
        if s.accessed_at > today:
            errors.append(f"Fonte {i} com accessed_at no futuro.")
        if s.accessed_at.year < 2023:
            errors.append(f"Fonte {i} com accessed_at muito antigo (antes de 2023).")
    return errors


def guess_institution_domain(name: str) -> Optional[str]:
    """
    Heurística simples: se o nome contiver 'USP', 'PUC-SP', etc., não dá para inferir domínio com segurança.
    Aqui apenas retornamos None. A verificação de domínio será apenas 'mesmo domínio do official_url'.
    Evolução futura: manter um mapa instituto->domínio.
    """
    _ = name
    return None


def check_official_urls(contract: OutputAdvisor, http_check: bool = False, timeout: float = 4.0) -> Tuple[List[str], Dict[str, int]]:
    """
    Checa se official_url e sources URLs são potencialmente válidas.
    - Validação de formato já ocorre pelo Pydantic.
    - Aqui opcionalmente tenta um HEAD/GET rápido para status HTTP.
    - Retorna (errors, status_map)
    """
    errors: List[str] = []
    status_map: Dict[str, int] = {}

    if http_check and not REQUESTS_AVAILABLE:
        return ["Checagem HTTP ativada, mas 'requests' não está disponível."], status_map

    urls: List[str] = []
    urls.extend([o.official_url for o in contract.options])
    urls.extend([str(s.url) for s in contract.sources])

    if http_check and REQUESTS_AVAILABLE:
        for url in urls:
            try:
                # HEAD primeiro; se não suportar, tenta GET com stream
                resp = requests.head(url, allow_redirects=True, timeout=timeout)
                if resp.status_code >= 400 or resp.status_code == 405:
                    resp = requests.get(url, allow_redirects=True, timeout=timeout, stream=True)
                status_map[url] = resp.status_code
                if resp.status_code >= 400:
                    errors.append(f"URL com status não OK ({resp.status_code}): {url}")
            except Exception as ex:  # pragma: no cover
                errors.append(f"Falha ao acessar URL: {url} ({ex})")

    return errors, status_map


def check_rank_coverage(contract: OutputAdvisor) -> List[str]:
    """
    Se houver mais de 1 opção, recomenda-se que os ranks sejam 1..N sem repetição.
    Não é obrigatório ser contínuo, mas avisamos se há gaps notáveis.
    """
    warnings: List[str] = []
    ranks = sorted(o.rank for o in contract.options)
    # Se 2+ opções e gap grande, emitir aviso
    if len(ranks) >= 2 and (max(ranks) - min(ranks) + 1) > len(ranks):
        warnings.append(f"Ranks apresentam lacunas: {ranks}")
    return warnings


def check_required_fields_presence(contract: OutputAdvisor) -> List[str]:
    """
    Confirma presença de campos textuais essenciais em cada opção.
    O schema já valida tipos/tamanhos básicos, aqui apenas garantimos semântica mínima.
    """
    errors: List[str] = []
    for i, o in enumerate(contract.options, start=1):
        if not o.title:
            errors.append(f"options[{i}].title vazio.")
        if not o.why_recommended:
            errors.append(f"options[{i}].why_recommended vazio.")
        if not o.next_steps:
            errors.append(f"options[{i}].next_steps vazio.")
    return errors


def check_profile_compatibility(contract: OutputAdvisor, snapshot_file: Optional[str]) -> List[str]:
    """
    Valida se as recomendações são compatíveis com o perfil do jovem.
    """
    errors: List[str] = []
    
    if not snapshot_file:
        return errors
    
    # Aqui você poderia implementar lógica específica para validar compatibilidade
    # Por exemplo, verificar se cursos caros são recomendados para perfis de baixa renda
    # ou se cursos presenciais são recomendados para perfis com barreiras geográficas
    
    return errors


def check_recommendation_diversity(contract: OutputAdvisor) -> List[str]:
    """
    Verifica se há diversidade nos tipos de recomendação.
    """
    warnings: List[str] = []
    
    if len(contract.options) < 2:
        return warnings
    
    types = [o.type for o in contract.options]
    unique_types = set(types)
    
    if len(unique_types) == 1:
        warnings.append("Todas as recomendações são do mesmo tipo. Considere diversificar.")
    
    return warnings


def check_compatibility_scores(contract: OutputAdvisor) -> List[str]:
    """
    Valida se os scores de compatibilidade são realistas.
    """
    warnings: List[str] = []
    
    for i, o in enumerate(contract.options, start=1):
        if o.compatibility_score < 3:
            warnings.append(f"Opção {i} tem score de compatibilidade muito baixo ({o.compatibility_score}/10).")
        if o.compatibility_score > 9:
            warnings.append(f"Opção {i} tem score de compatibilidade muito alto ({o.compatibility_score}/10).")
    
    return warnings


def check_focus_alignment(contract: OutputAdvisor, foco_especifico: Optional[str]) -> List[str]:
    """
    Verifica se as recomendações estão alinhadas com o foco específico.
    """
    warnings: List[str] = []
    
    if not foco_especifico:
        return warnings
    
    foco = foco_especifico.lower()
    
    # Mapear foco para tipos de recomendação esperados
    focus_mapping = {
        "primeiro emprego": ["curso_tecnico", "curso_livre", "certificacao", "trabalho_manual"],
        "mudança de carreira": ["curso_graduacao", "especializacao", "certificacao"],
        "sobrevivência básica": ["trabalho_manual", "orientacao_basica", "apoio_psicologico"],
        "empreendedorismo": ["empreendedorismo", "curso_livre", "certificacao"],
        "carreira artística": ["carreira_artistica", "curso_livre", "empreendedorismo"]
    }
    
    expected_types = focus_mapping.get(foco, [])
    if not expected_types:
        return warnings
    
    actual_types = [o.type for o in contract.options]
    matches = sum(1 for t in actual_types if t in expected_types)
    
    if matches == 0:
        warnings.append(f"Nenhuma recomendação alinhada com o foco '{foco_especifico}'.")
    elif matches < len(contract.options) // 2:
        warnings.append(f"Poucas recomendações alinhadas com o foco '{foco_especifico}'.")
    
    return warnings


# ---------------------------
# Função principal de validação
# ---------------------------

def validate_output_contract(
    raw_json: dict,
    preferencia: Optional[str] = None,
    snapshot_file: Optional[str] = None,
    foco_especifico: Optional[str] = None,
    http_check: bool = False,
) -> ValidationResult:
    """
    Valida a saída do Agent 0 conforme regras de negócio.
    - raw_json: JSON retornado pelo LLM (já convertido para dict).
    - preferencia: texto original da preferência do usuário (usado para checar modalidade).
    - http_check: se True, tenta verificar status HTTP dos links (requer 'requests').

    Retorna ValidationResult com:
      - valid: bool geral (sem erros críticos)
      - errors: lista de problemas
      - warnings: avisos não bloqueantes
      - normalized: OutputContract normalizado
      - url_status: mapa URL->status HTTP (se http_check=True)
    """
    errors: List[str] = []
    warnings: List[str] = []

    contract, schema_errors = parse_and_normalize(raw_json)
    if schema_errors:
        return ValidationResult(valid=False, errors=schema_errors, warnings=[], normalized=None)

    # Regras de negócio
    errors.extend(check_unique_ranks(contract))
    errors.extend(check_summary_quality(contract))
    errors.extend(check_next_steps_quality(contract))
    errors.extend(check_sources_basic(contract))
    errors.extend(check_required_fields_presence(contract))
    errors.extend(check_modality_against_preference(contract, preferencia))
    errors.extend(check_profile_compatibility(contract, snapshot_file))

    warnings.extend(check_rank_coverage(contract))
    warnings.extend(check_recommendation_diversity(contract))
    warnings.extend(check_compatibility_scores(contract))
    warnings.extend(check_focus_alignment(contract, foco_especifico))

    url_errors: List[str] = []
    status_map: Dict[str, int] = {}
    if http_check:
        url_errors, status_map = check_official_urls(contract, http_check=True)
        errors.extend(url_errors)

    return ValidationResult(
        valid=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        normalized=contract,
        url_status=status_map if http_check else None,
    )
