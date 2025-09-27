"""
CLI do Especialista de Carreira - Leve Agents

Fornece orientação profissional para primeiro emprego baseada em perguntas específicas.
Suporta análise de perfil via snapshot e validação completa dos resultados.

Exemplos:
  python -m cli.main_career -q "Como montar um currículo sem experiência?"
  python -m cli.main_career -q "Quais áreas posso trabalhar?" --snapshot-path files/snapshots/ana_001.json
  python -m cli.main_career -q "Como me preparar para entrevistas?" --json
  python -m cli.main_career -q "Como montar um currículo?" --no-snapshot
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv
from pydantic import ValidationError

# Configuração de path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from crew_config import career_coach_crew
from schemas.career_input import CareerInput
from schemas.career_output import CareerOutput
from validators.career_output_checks import run_all_checks
from helpers.json_extractor import try_extract_json
from helpers.snapshot_selector import select_profile_snapshot, load_snapshot_from_file

# Inicialização do AgentOps para monitoramento de custos
import agentops
if os.getenv("AGENTOPS_API_KEY"):
    agentops.init()


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="career-cli",
        description="Especialista em Primeiro Emprego — Leve",
    )
    parser.add_argument(
        "-q", "--question",
        required=True,
        help="Dúvida sobre execução prática para primeiro emprego (ex.: 'Como montar um currículo sem experiência?').",
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
    parser.add_argument(
        "--no-snapshot",
        action="store_true",
        help="Pula a seleção de snapshot e executa sem perfil.",
    )
    return parser.parse_args(argv)




def _print_pretty(output: CareerOutput) -> None:
    """Imprime o resultado de forma amigável."""
    print("\n🎯 Resposta do Especialista em Primeiro Emprego")
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
        profile_snapshot = load_snapshot_from_file(args.snapshot_path)
        if profile_snapshot is None:
            return 1
    elif args.no_snapshot:
        # Usuário explicitamente escolheu pular o snapshot
        print("Executando sem snapshot de perfil...")
        profile_snapshot = None
    else:
        # Se não foi fornecido snapshot via argumento, permite seleção interativa
        # Mas permite pular sem erro
        try:
            profile_snapshot, snapshot_label = select_profile_snapshot()
            print(f"\nSnapshot selecionado: {snapshot_label}")
        except KeyboardInterrupt:
            print("\nOperação cancelada pelo usuário.")
            return 1
        except Exception as e:
            print(f"Erro ao selecionar snapshot: {e}")
            print("Continuando sem snapshot...")
            profile_snapshot = None

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
            "question": user_input.question,
            "profile_snapshot": user_input.profile_snapshot
        }

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
