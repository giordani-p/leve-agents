from typing import List, Tuple
from schemas.career_output import CareerOutput


FORBIDDEN_PHRASES = [
    "garantia de emprego",
    "emprego garantido",
    "100% de chance",
]


def run_all_checks(output: CareerOutput) -> Tuple[bool, List[str]]:
    """
    Executa todas as validações de negócio no CareerOutput.
    Retorna (ok, errors).
    """
    errors: List[str] = []

    # 1. Status válido
    if output.status not in ("ok", "fora_do_escopo"):
        errors.append(f"status inválido: {output.status}")

    # 2. Short answer não vazio e <= 240 chars
    if not output.short_answer.strip():
        errors.append("short_answer está vazio")
    if len(output.short_answer) > 240:
        errors.append("short_answer excede 240 caracteres")

    # 3. Detailed answer não vazio
    if not output.detailed_answer.strip():
        errors.append("detailed_answer está vazio")

    # 4. Verificar recursos
    if output.resources:
        if len(output.resources) > 5:
            errors.append("resources excede o limite de 5 itens")
        for i, r in enumerate(output.resources):
            if not r.title.strip():
                errors.append(f"resource[{i}] sem título")
            if r.type not in ("template", "article", "video", "checklist"):
                errors.append(f"resource[{i}] type inválido: {r.type}")

    # 5. Frases proibidas
    lower_text = f"{output.short_answer} {output.detailed_answer}".lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower_text:
            errors.append(f"frase proibida detectada: '{phrase}'")

    ok = len(errors) == 0
    return ok, errors
