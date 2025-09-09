import os
import sys
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para permitir importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega variáveis de ambiente
load_dotenv()

from crew_config import insight_profiler_crew
from schemas.profile_output import ProfileOutput
from validators.profile_output_checks import validate_profile_output
from pydantic import ValidationError
from helpers.json_extractor import try_extract_json 


import json

if __name__ == "__main__":
    print("\nExecutando Perfilador Educacional...\n")

    # Nome do arquivo de snapshot (presente em files/snapshots/)
    filename = "carlos_001.txt"
    snapshot_raw = """
        Escolaridade: Ensino médio completo

        Experiência profissional:
        - Ajudante de pedreiro (freelancer)
        - Entregador de aplicativo (frequente nos últimos 6 meses)

        Objetivos de carreira:
        - Ter um emprego fixo
        - Ajudar financeiramente a família

        Sonhos e metas:
        - Dar uma vida melhor para a mãe
        - Ter estabilidade financeira
        - Fazer um curso técnico

        Habilidades:
        - Conserta objetos em casa com facilidade
        - Aprende na prática
        - Gosta de entender como as coisas funcionam

        Pontos fortes percebidos:
        - Persistente
        - Responsável
        - Calmo sob pressão

        DISC: Perfil C
        Gallup (top 3): Realizador, Empatia, Restaurador
        """
    result = insight_profiler_crew.kickoff(inputs={"dados": snapshot_raw})

    raw_text = result if isinstance(result, str) else str(result)
    json_dict = try_extract_json(raw_text)
 
     # Validação de esquema (estrutura/tipos/limites)
    if json_dict is None:
        print("\nErro: resposta não veio em JSON válido.")
        print("Conteúdo bruto recebido (parcial):")
        print(raw_text[:1000])
        exit(1)

    try:
        output = ProfileOutput.model_validate(json_dict)
    except ValidationError as ve:
        print("\nErro de validação do JSON de saída:")
        print(ve)
        print("\nJSON extraído (para revisão):")
        print(json.dumps(json_dict, indent=2, ensure_ascii=False))
        exit(1)

     # Validação de negócio (regras de negócio)
    validation = validate_profile_output(json_dict)

    if not validation.valid:
        print("\nResultado inválido segundo as regras de negócio:")
        for err in validation.errors:
            print("-", err)

        print("\nJSON recebido (para diagnóstico):")
        print(json.dumps(json_dict, indent=2, ensure_ascii=False))
        exit(1)

    if validation.warnings:
        print("\nAvisos (não bloqueantes):")
        for warn in validation.warnings:
            print("-", warn)

    print("\nJSON validado com sucesso. Resultado final:\n")
    print(json.dumps(validation.normalized.model_dump(mode="json"), indent=2, ensure_ascii=False))