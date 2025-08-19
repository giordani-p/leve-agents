# validators/profile_output_checks.py
from schemas.profile_output import ProfileOutput
from typing import List
from pydantic import BaseModel

# Define o resultado da validação de negócio
class ProfileValidationResult(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    normalized: ProfileOutput = None

# Validador principal de negócio para o Agent 01
def validate_profile_output(raw_json: dict) -> ProfileValidationResult:
    errors = []
    warnings = []

    try:
        # Valida estrutura com o schema Pydantic
        parsed = ProfileOutput.model_validate(raw_json)
    except Exception as e:
        return ProfileValidationResult(
            valid=False,
            errors=[f"Erro de estrutura: {str(e)}"]
        )

    # Verifica se todos os campos de lista têm pelo menos 1 item ou 'não informado'
    list_fields = [
        "caracteristicas_chave",
        "objetivos_detectados",
        "dificuldades_detectadas",
        "hipoteses_a_validar",
        "recomendacoes",
        "next_questions",
        "alerts_politicas"
    ]

    for field in list_fields:
        value = getattr(parsed, field)

        # Converte para lista, se por algum erro vier como string
        if isinstance(value, str):
            warnings.append(f"O campo '{field}' veio como string. Esperado: lista.")

        # Verifica se a lista está vazia
        if isinstance(value, list) and len(value) == 0:
            errors.append(f"O campo '{field}' não pode estar vazio. Use 'não informado' se necessário.")

        # Verifica se todos os itens da lista são strings
        if isinstance(value, list) and any(not isinstance(item, str) for item in value):
            errors.append(f"Todos os itens do campo '{field}' devem ser strings.")

        # Verifica se o campo tem apenas 'não informado' como valor
        if isinstance(value, list) and value == ["não informado"]:
            continue  # aceitável

    # Valida tamanho máximo das listas (quando aplicável)
    max_len_fields = {
        "caracteristicas_chave": 5,
        "next_questions": 3
    }

    for field, max_len in max_len_fields.items():
        value = getattr(parsed, field)
        if isinstance(value, list) and len(value) > max_len:
            warnings.append(f"O campo '{field}' tem mais de {max_len} itens (recebido: {len(value)}).")

    # Verificação leve de PII (nome, email, telefone, endereço, CPF, etc.)
    texto_completo = parsed.model_dump_json()

    termos_pii = ["@gmail", "@hotmail", "@yahoo", "telefone", "cpf", "rg", "endereço", "bairro", "cidade"]
    for termo in termos_pii:
        if termo.lower() in texto_completo.lower():
            errors.append(f"Possível PII detectado: '{termo}'.")

    return ProfileValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        normalized=parsed
    )
