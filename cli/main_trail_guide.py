# from __future__ import annotations

# import os
# import json
# import agentops
# from dotenv import load_dotenv
# from pydantic import ValidationError

# from crew_config import trail_guide_crew

# # Schemas de entrada/saída
# from schemas.trail_input import TrailInput
# from schemas.trail_output import TrailOutput  # contrato JSON de saída

# # Regras de negócio e utilitário para extrair JSON
# from validators.trail_output_checks import validate_output_contract  # validações de negócio
# from helpers.json_extractor import try_extract_json

# load_dotenv()
# agentops.init()


# if __name__ == "__main__":
#     print("Bem-vindo ao Orientador de Trilhas!\n")

#     # ---- Coleta de entradas do usuário (interativo) ----
#     user_question = input("Qual é a sua dúvida/objetivo? (ex.: Quero aprender programação do zero)\n").strip()
#     user_id_str = input("Se tiver, informe seu UUID (opcional). Deixe em branco se não souber.\n").strip()
#     contexto_extra = input("Quer acrescentar algum contexto? (opcional, ex.: área/nível/objetivo)\n").strip()

#     # Normaliza opcionais vazios para None
#     user_id = user_id_str or None
#     contexto_extra = contexto_extra or None

#     try:
#         # ---- Validação de entrada (Pydantic) ----
#         user_input = TrailInput(
#             user_question=user_question,
#             user_id=user_id,            # Pydantic converte/valida UUID se não for None
#             contexto_extra=contexto_extra,
#         )

#         print("\nProcessando sua solicitação...")

#         # ---- Execução da Crew com inputs tipados ----
#         result = trail_guide_crew.kickoff(inputs={
#             "user_question": user_input.user_question,
#             "user_id": str(user_input.user_id) if user_input.user_id else None,
#             "contexto_extra": user_input.contexto_extra
#         })

#         raw_text = result if isinstance(result, str) else str(result)

#         # ---- Extração de JSON da saída do modelo ----
#         json_dict = try_extract_json(raw_text)
#         if json_dict is None:
#             print("\nErro: a resposta do modelo não veio em JSON puro conforme o expected_output.")
#             print("Conteúdo bruto recebido (parcial para diagnóstico):")
#             print(raw_text[:1200])
#             raise SystemExit(1)

#         # ---- Validação de esquema de saída (Pydantic) ----
#         try:
#             _ = TrailOutput.model_validate(json_dict)
#         except ValidationError as ve:
#             print("\nErro de validação do contrato de saída (TrailOutput):")
#             print(ve)
#             print("\nJSON extraído (para revisão):")
#             print(json.dumps(json_dict, ensure_ascii=False, indent=2))
#             raise SystemExit(1)

#         # ---- Validações de negócio (regras do projeto) ----
#         validation = validate_output_contract(
#             raw_json=json_dict,
#             http_check=False 
#         )

#         if not validation.valid:
#             print("\nResultado inválido segundo as regras de negócio.")
#             print("\nErros:")
#             for err in validation.errors:
#                 print("-", err)

#             if validation.warnings:
#                 print("\nAvisos:")
#                 for warn in validation.warnings:
#                     print("-", warn)

#             if validation.normalized:
#                 print("\nSaída normalizada (para diagnóstico):")
#                 print(json.dumps(validation.normalized.model_dump(mode="json"), ensure_ascii=False, indent=2))
#             else:
#                 print("\nJSON recebido (para diagnóstico):")
#                 print(json.dumps(json_dict, ensure_ascii=False, indent=2))

#             raise SystemExit(1)

#         # ---- Caso válido: imprime saída normalizada + avisos (se houver) ----
#         print("\nResultado final (JSON validado e normalizado):\n")
#         print(json.dumps(validation.normalized.model_dump(mode="json"), ensure_ascii=False, indent=2))

#         if validation.warnings:
#             print("\nAvisos (não bloqueantes):")
#             for warn in validation.warnings:
#                 print("-", warn)

#     # ---- Erros de validação da entrada ----
#     except ValidationError as e:
#         print("\nErro nos dados fornecidos:")
#         for error in e.errors():
#             loc = ".".join(str(x) for x in error.get("loc", []))
#             print(f"- {loc}: {error.get('msg')}")

#     # ---- Erros inesperados ----
#     except Exception as e:
#         print(f"\nErro inesperado: {e}")
#         print("Verifique dependências e as chaves de API necessárias (ex.: SERPER_API_KEY).")
