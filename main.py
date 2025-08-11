import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env ANTES de qualquer importação
load_dotenv()

from crew_config import crew
from schemas.user_inputs import UserInput
from pydantic import ValidationError
import agentops

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

        print("\nResultado final:\n")
        print(result)

    # Captura e exibe erros de validação do input do usuário
    except ValidationError as e:
        print("\nErro nos dados fornecidos:")
        for error in e.errors():
            print(f"- {error['loc'][0]}: {error['msg']}")

    # Captura outros erros inesperados (como problemas com LLMs ou dependências)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        print("Verifique se todas as dependências estão instaladas e as chaves de API configuradas.")
