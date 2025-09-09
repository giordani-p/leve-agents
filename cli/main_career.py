#! /usr/bin/env python3
import os
import sys
import json
from pathlib import Path
import agentops
from typing import Optional, Tuple
from dotenv import load_dotenv
from pydantic import ValidationError

# Adiciona o diretório raiz ao path para permitir importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
# agentops.init()

from crew_config import career_coach_crew
from schemas.career_input import CareerInput
from schemas.career_output import CareerOutput
from validators.career_output_checks import run_all_checks
from helpers.json_extractor import try_extract_json


def _select_profile_snapshot() -> Tuple[Optional[dict], str]:
    """
    Lista arquivos .json em files/snapshots/ e permite seleção.
    Opções:
      - Enter: pular (sem snapshot)
      - Número: carrega o arquivo correspondente
      - 'm': colar JSON manualmente
    Retorna (snapshot_dict | None, label_str)
    """
    # Localiza a pasta files/snapshots a partir da raiz do projeto
    root_dir = Path(__file__).resolve().parents[1]
    snapshots_dir = root_dir / "files" / "snapshots"

    print("\n=== Profile Snapshot (opcional) ===")

    files: list[Path] = []
    try:
        if snapshots_dir.exists() and snapshots_dir.is_dir():
            files = sorted([p for p in snapshots_dir.glob("*.json") if p.is_file()], key=lambda p: p.name.lower())
    except Exception:
        files = []

    if files:
        print("Snapshots disponíveis em files/snapshots/:")
        for idx, p in enumerate(files, start=1):
            print(f"[{idx}] {p.name}")
        print("[m] Colar JSON manualmente")
        print("[Enter] Pular (sem snapshot)")
    else:
        print("Nenhum arquivo .json encontrado em files/snapshots/.")
        print("[m] Colar JSON manualmente")
        print("[Enter] Pular (sem snapshot)")

    while True:
        choice = input("Selecione uma opção (número, 'm' ou Enter): ").strip().lower()

        if choice == "":
            return None, "nenhum"

        if choice == "m":
            profile_raw = input("Cole o JSON do snapshot e pressione Enter:\n")
            if not profile_raw.strip():
                print("Entrada vazia. Voltando ao menu de snapshot.")
                continue
            try:
                return json.loads(profile_raw), "[manual]"
            except json.JSONDecodeError as e:
                print(f"JSON inválido: {e}. Tente novamente.")
                continue

        if choice.isdigit() and files:
            idx = int(choice)
            if 1 <= idx <= len(files):
                selected = files[idx - 1]
                try:
                    text = selected.read_text(encoding="utf-8")
                    return json.loads(text), selected.name
                except (OSError, json.JSONDecodeError) as e:
                    print(f"Falha ao carregar '{selected.name}': {e}. Selecione outra opção.")
                    continue
            else:
                print("Número fora do intervalo. Tente novamente.")
                continue

        print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    print("Bem-vindo ao Especialista de Carreira (primeiro emprego)!\n")

    # Captura a dúvida do usuário
    question = input("Qual é a sua dúvida de carreira? (ex.: 'Como montar um currículo sem experiência?')\n")

    # Permite seleção/entrada de profile_snapshot de forma opcional
    profile_snapshot, snapshot_label = _select_profile_snapshot()
    print(f"\nSnapshot selecionado: {snapshot_label}")

    # Valida o input do usuário (schema de entrada)
    try:
        user_input = CareerInput(
            question=question,
            profile_snapshot=profile_snapshot
        )
    except ValidationError as e:
        print("\nErro nos dados fornecidos (validação de entrada):")
        print(e)
        raise SystemExit(1)
    except Exception as e:
        print(f"\nErro inesperado ao processar o input: {e}")
        raise SystemExit(1)

    print("\nProcessando sua solicitação...")

    try:
        # Executa o Crew com os inputs validados
        kickoff_inputs = {
            "question": user_input.question
        }
        if user_input.profile_snapshot is not None:
            # Inclui o snapshot nos inputs do agente, quando fornecido
            kickoff_inputs["profile_snapshot"] = user_input.profile_snapshot

        print("\n=== Dados de Entrada para o Crew ===")
        print("Pergunta:", user_input.question)
        print("Profile Snapshot:", user_input.profile_snapshot)
        print("Kickoff Inputs:", kickoff_inputs)
        print("===================================\n")

        result = career_coach_crew.kickoff(inputs=kickoff_inputs)

        raw_text = result if isinstance(result, str) else str(result)

        # Extrai o JSON da resposta
        json_dict = try_extract_json(raw_text)
        if json_dict is None:
            print("\nErro: a resposta do modelo não veio em JSON puro conforme o expected_output.")
            print("Conteúdo bruto recebido (parcial para diagnóstico):")
            print(raw_text[:1000])
            raise SystemExit(1)

        # Validação de esquema (estrutura/tipos/limites)
        try:
            output_obj = CareerOutput.model_validate(json_dict)
        except ValidationError as ve:
            print("\nErro de validação do esquema de saída (CareerCoachOutput):")
            print(ve)
            print("\nJSON extraído (para revisão):")
            print(json.dumps(json_dict, ensure_ascii=False, indent=2))
            raise SystemExit(1)

        # Validações de negócio
        ok, errors = run_all_checks(output_obj)
        if not ok:
            print("\nResultado inválido segundo as regras de negócio.")
            print("\nErros:")
            for err in errors:
                print("-", err)
            print("\nJSON recebido (para diagnóstico):")
            print(json.dumps(output_obj.model_dump(mode="json"), ensure_ascii=False, indent=2))
            raise SystemExit(1)

        # Caso válido — imprime saída validada
        print("\nResultado final (JSON validado):\n")
        print(json.dumps(output_obj.model_dump(mode="json"), ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"\nErro inesperado: {e}")
        print("Verifique se todas as dependências estão instaladas e as chaves de API configuradas.")
        raise SystemExit(1)
