# validators/psychological_output_checks.py
from schemas.psychological_output import PsychologicalOutput
from typing import List
from pydantic import BaseModel

# Define o resultado da validação de negócio
class ProfileValidationResult(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    normalized: PsychologicalOutput = None

# Validador principal de negócio para o Agent 01
def validate_psychological_output(raw_json: dict) -> ProfileValidationResult:
    errors = []
    warnings = []

    try:
        # Valida estrutura com o schema Pydantic
        parsed = PsychologicalOutput.model_validate(raw_json)
    except Exception as e:
        return ProfileValidationResult(
            valid=False,
            errors=[f"Erro de estrutura: {str(e)}"]
        )

    # Verifica se todos os campos de lista têm pelo menos 1 item ou 'não informado'
    list_fields = [
        "motivacoes_principais",
        "valores_core",
        "gatilhos_estresse",
        "areas_desenvolvimento",
        "pontos_fortes",
        "desafios_comportamentais",
        "perfis_carreira_compativel",
        "estrategias_personalizacao",
        "alertas_importantes"
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
        "motivacoes_principais": 3,
        "valores_core": 3,
        "gatilhos_estresse": 3,
        "areas_desenvolvimento": 3,
        "pontos_fortes": 3,
        "desafios_comportamentais": 3,
        "perfis_carreira_compativel": 3,
        "estrategias_personalizacao": 3,
        "alertas_importantes": 3
    }

    for field, max_len in max_len_fields.items():
        value = getattr(parsed, field)
        if isinstance(value, list) and len(value) > max_len:
            warnings.append(f"O campo '{field}' tem mais de {max_len} itens (recebido: {len(value)}).")

    # Verificação leve de PII (nome, email, telefone, endereço, CPF, etc.)
    texto_completo = parsed.model_dump_json()

    termos_pii = ["@gmail", "@hotmail", "@yahoo", "telefone", "cpf", " endereço", " bairro", " cidade"]
    for termo in termos_pii:
        if termo.lower() in texto_completo.lower():
            errors.append(f"Possível PII detectado: '{termo}'.")

    return ProfileValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        normalized=parsed
    )
