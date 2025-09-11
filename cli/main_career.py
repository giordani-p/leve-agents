# cli/main_career.py
"""
CLI do Especialista de Carreira (primeiro emprego)
- Lê a pergunta do usuário e opcionalmente um snapshot de perfil
- Executa o crew de carreira e imprime o resultado validado no terminal
- Por padrão imprime de forma "amigável"; use --json para ver o objeto completo

Exemplos:
  python -m cli.main_career -q "Como montar um currículo sem experiência?"
  python -m cli.main_career -q "Quais áreas posso trabalhar?" --snapshot-path files/snapshots/ana_001.json
  python -m cli.main_career -q "Como me preparar para entrevistas?" --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

import agentops
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


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="career-cli",
        description="Especialista de Carreira (primeiro emprego) — Leve",
    )
    parser.add_argument(
        "-q", "--question",
        required=True,
        help="Dúvida de carreira do usuário (ex.: 'Como montar um currículo sem experiência?').",
    )
    parser.add_argument(
        "--snapshot-path",
        default=None,
        help="Caminho do JSON de snapshot (opcional).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o objeto CareerOutput completo em JSON.",
    )
    return parser.parse_args(argv)


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


def _load_snapshot_from_file(snapshot_path: str) -> Optional[dict]:
    """Carrega snapshot de um arquivo JSON."""
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"[ERRO] Falha ao carregar snapshot '{snapshot_path}': {e}", file=sys.stderr)
        return None


def _print_pretty(output: CareerOutput) -> None:
    """Imprime o resultado de forma amigável."""
    print("\n🎯 Resposta do Especialista de Carreira")
    print("=" * 50)
    
    if hasattr(output, 'advice') and output.advice:
        print(f"\n💡 Conselho Principal:")
        print(f"   {output.advice}")
    
    if hasattr(output, 'steps') and output.steps:
        print(f"\n📋 Passos Recomendados:")
        for i, step in enumerate(output.steps, 1):
            print(f"   {i}. {step}")
    
    if hasattr(output, 'resources') and output.resources:
        print(f"\n📚 Recursos Úteis:")
        for resource in output.resources:
            print(f"   • {resource}")
    
    print("\n" + "=" * 50)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    
    # Carrega snapshot se fornecido
    profile_snapshot = None
    if args.snapshot_path:
        profile_snapshot = _load_snapshot_from_file(args.snapshot_path)
        if profile_snapshot is None:
            return 1
    else:
        # Se não foi fornecido snapshot via argumento, permite seleção interativa
        profile_snapshot, snapshot_label = _select_profile_snapshot()
        print(f"\nSnapshot selecionado: {snapshot_label}")

    # Valida o input do usuário
    try:
        user_input = CareerInput(
            question=args.question,
            profile_snapshot=profile_snapshot
        )
    except ValidationError as e:
        print(f"[ERRO] Entrada inválida: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[ERRO] Erro inesperado ao processar o input: {e}", file=sys.stderr)
        return 2

    print("\nProcessando sua solicitação...")

    try:
        # Executa o Crew com os inputs validados
        kickoff_inputs = {
            "question": user_input.question
        }
        if user_input.profile_snapshot is not None:
            kickoff_inputs["profile_snapshot"] = user_input.profile_snapshot

        result = career_coach_crew.kickoff(inputs=kickoff_inputs)
        raw_text = result if isinstance(result, str) else str(result)

        # Extrai o JSON da resposta
        json_dict = try_extract_json(raw_text)
        if json_dict is None:
            print("[ERRO] A resposta do modelo não veio em JSON puro conforme o expected_output.", file=sys.stderr)
            print("Conteúdo bruto recebido (parcial para diagnóstico):", file=sys.stderr)
            print(raw_text[:1000], file=sys.stderr)
            return 1

        # Validação de esquema
        try:
            output_obj = CareerOutput.model_validate(json_dict)
        except ValidationError as ve:
            print(f"[ERRO] Erro de validação do esquema de saída: {ve}", file=sys.stderr)
            print("\nJSON extraído (para revisão):", file=sys.stderr)
            print(json.dumps(json_dict, ensure_ascii=False, indent=2), file=sys.stderr)
            return 1

        # Validações de negócio
        ok, errors = run_all_checks(output_obj)
        if not ok:
            print("[ERRO] Resultado inválido segundo as regras de negócio.", file=sys.stderr)
            print("\nErros:", file=sys.stderr)
            for err in errors:
                print(f"- {err}", file=sys.stderr)
            print("\nJSON recebido (para diagnóstico):", file=sys.stderr)
            print(json.dumps(output_obj.model_dump(mode="json"), ensure_ascii=False, indent=2), file=sys.stderr)
            return 1

        # Impressão
        if args.json:
            print(output_obj.model_dump_json(indent=2))
        else:
            _print_pretty(output_obj)

        return 0

    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}", file=sys.stderr)
        print("Verifique se todas as dependências estão instaladas e as chaves de API configuradas.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
