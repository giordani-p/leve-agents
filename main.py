import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env ANTES de qualquer importação
load_dotenv()

from crew_config import crew
from schemas.user_inputs import UserInput
from pydantic import ValidationError
import agentops

# >>> ADICIONADO: imports para validação de saída e utilidades
import json  # usado para pretty print do JSON validado
import re    # usado no helper de extração de JSON
from typing import Any, Dict, Optional
from schemas.output_contract import OutputContract  # schema da saída (contrato JSON)
from validators.output_checks import validate_output_contract  # regras de negócio


# >>> ADICIONADO: helper simples para extrair apenas o JSON da resposta do LLM
def try_extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Tenta extrair um JSON válido de um texto.
    Estratégias:
      1) Procurar bloco cercado por ```json ... ```
      2) Procurar do primeiro '{' ao último '}' e fazer json.loads
    Retorna dict ou None.
    """
    if not text or not isinstance(text, str):
        return None

    # 1) Bloco cercado por ```json ... ```
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        snippet = fenced.group(1)
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass

    # 2) Primeiro '{' até o último '}'
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            # limpeza leve e nova tentativa
            cleaned = snippet.replace("\u00A0", " ").replace("\u200b", "")
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return None

    return None


# Inicializa o AgentOps (opcional, usado para rastreamento de execução se habilitado)
agentops.init()

if __name__ == "__main__":
    print("Bem-vindo ao Orientador Educacional!\n")

    # Captura os dados fornecidos pelo usuário
    interesse = input("O que você gostaria de aprender ou fazer no futuro?\n")
    preferencia = input("Qual formato ou região você prefere (ex: online, presencial, SP, exterior)?\n")

    try:
        # Valida os dados usando o schema Pydantic
        user_input = UserInput(
            interesse=interesse,
            preferencia=preferencia
        )

        print("\nProcessando sua solicitação...")

        # Executa o Crew com os inputs validados
        result = crew.kickoff(inputs={
            "interesse": user_input.interesse,
            "preferencia": user_input.preferencia
        })

        # >>> ADICIONADO: garantir que a resposta esteja em string
        raw_text = result if isinstance(result, str) else str(result)

        # >>> ADICIONADO: extrair somente o JSON da resposta
        json_dict = try_extract_json(raw_text)
        if json_dict is None:
            print("\nErro: a resposta do modelo não veio em JSON puro conforme o expected_output.")
            print("Conteúdo bruto recebido (parcial para diagnóstico):")
            print(raw_text[:1000])  # evita despejar textos muito longos
            raise SystemExit(1)

        # >>> ADICIONADO: validação de esquema (estrutura/tipos/limites)
        try:
            _ = OutputContract.model_validate(json_dict)
        except ValidationError as ve:
            print("\nErro de validação do esquema de saída (OutputContract):")
            print(ve)
            print("\nJSON extraído (para revisão):")
            print(json.dumps(json_dict, ensure_ascii=False, indent=2))
            raise SystemExit(1)

        # >>> ADICIONADO: validações de negócio (ranks, fontes, modalidade vs preferência, etc.)
        validation = validate_output_contract(
            raw_json=json_dict,
            preferencia=user_input.preferencia,
            http_check=False  # deixar False para testes rápidos via CLI
        )

        if not validation.valid:
            print("\nResultado inválido segundo as regras de negócio.")
            print("\nErros:")
            for err in validation.errors:
                print("-", err)

            if validation.warnings:
                print("\nAvisos:")
                for warn in validation.warnings:
                    print("-", warn)

            if validation.normalized:
                print("\nSaída normalizada (para diagnóstico):")
                print(json.dumps(validation.normalized.model_dump(mode="json"), ensure_ascii=False, indent=2))
            else:
                print("\nJSON recebido (para diagnóstico):")
                print(json.dumps(json_dict, ensure_ascii=False, indent=2))

            raise SystemExit(1)

        # >>> ADICIONADO: caso válido — imprime saída normalizada e avisos (se houver)
        print("\nResultado final (JSON validado e normalizado):\n")
        print(json.dumps(validation.normalized.model_dump(mode="json"), ensure_ascii=False, indent=2))

        if validation.warnings:
            print("\nAvisos (não bloqueantes):")
            for warn in validation.warnings:
                print("-", warn)

        # >>> ALTERADO: removida a impressão direta do 'result' bruto
        # Motivo: agora garantimos JSON conforme contrato e mostramos formatado.

    # Captura e exibe erros de validação do input do usuário
    except ValidationError as e:
        print("\nErro nos dados fornecidos:")
        for error in e.errors():
            print(f"- {error['loc'][0]}: {error['msg']}")

    # Captura outros erros inesperados (como problemas com LLMs ou dependências)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        print("Verifique se todas as dependências estão instaladas e as chaves de API configuradas.")
