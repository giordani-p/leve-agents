import os
import agentops
import json
from dotenv import load_dotenv

load_dotenv()

from crew_config import advisor_crew

from schemas.advisor_inputs import UserInput
from pydantic import ValidationError

from schemas.advisor_output import OutputAdvisor  # schema da saída (contrato JSON)
from validators.advisor_output_checks import validate_output_contract  # regras de negócio
from helpers.json_extractor import try_extract_json

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
        result = advisor_crew.kickoff(inputs={
            "interesse": user_input.interesse,
            "preferencia": user_input.preferencia
        })

        raw_text = result if isinstance(result, str) else str(result)

        json_dict = try_extract_json(raw_text)

        if json_dict is None:
            print("\nErro: a resposta do modelo não veio em JSON puro conforme o expected_output.")
            print("Conteúdo bruto recebido (parcial para diagnóstico):")
            print(raw_text[:1000]) 
            raise SystemExit(1)

        # validação de esquema (estrutura/tipos/limites)
        try:
            _ = OutputAdvisor.model_validate(json_dict)
        except ValidationError as ve:
            print("\nErro de validação do esquema de saída (OutputContract):")
            print(ve)
            print("\nJSON extraído (para revisão):")
            print(json.dumps(json_dict, ensure_ascii=False, indent=2))
            raise SystemExit(1)

        # validações de negócio (ranks, fontes, modalidade vs preferência, etc.)
        validation = validate_output_contract(
            raw_json=json_dict,
            preferencia=user_input.preferencia,
            http_check=False  # False para testes rápidos via CLI
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

        # caso válido — imprime saída normalizada e avisos (se houver)
        print("\nResultado final (JSON validado e normalizado):\n")
        print(json.dumps(validation.normalized.model_dump(mode="json"), ensure_ascii=False, indent=2))

        if validation.warnings:
            print("\nAvisos (não bloqueantes):")
            for warn in validation.warnings:
                print("-", warn)

    # Captura e exibe erros de validação do input do usuário
    except ValidationError as e:
        print("\nErro nos dados fornecidos:")
        for error in e.errors():
            print(f"- {error['loc'][0]}: {error['msg']}")

    # Captura outros erros inesperados (como problemas com LLMs ou dependências)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        print("Verifique se todas as dependências estão instaladas e as chaves de API configuradas.")
