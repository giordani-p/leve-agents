# cli/main_advisor.py
"""
CLI do Orientador Educacional
- Lê o interesse e preferência do usuário
- Executa o crew de orientação educacional e imprime o resultado validado no terminal
- Por padrão imprime de forma "amigável"; use --json para ver o objeto completo

Exemplos:
  python -m cli.main_advisor -i "programação" -p "online"
  python -m cli.main_advisor -i "medicina" -p "presencial, SP" --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

import agentops
from dotenv import load_dotenv
from pydantic import ValidationError

# Adiciona o diretório raiz ao path para permitir importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from crew_config import advisor_crew
from schemas.advisor_inputs import UserInput
from schemas.advisor_output import OutputAdvisor
from validators.advisor_output_checks import validate_output_contract
from helpers.json_extractor import try_extract_json

agentops.init()


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="advisor-cli",
        description="Orientador Educacional — Leve",
    )
    parser.add_argument(
        "-i", "--interesse",
        required=True,
        help="O que você gostaria de aprender ou fazer no futuro?",
    )
    parser.add_argument(
        "-p", "--preferencia",
        required=True,
        help="Qual formato ou região você prefere (ex: online, presencial, SP, exterior)?",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o objeto OutputAdvisor completo em JSON.",
    )
    return parser.parse_args(argv)


def _print_pretty(output: OutputAdvisor) -> None:
    """Imprime o resultado de forma amigável."""
    print("\n🎓 Orientação Educacional")
    print("=" * 50)
    
    if hasattr(output, 'courses') and output.courses:
        print(f"\n📚 Cursos Recomendados:")
        for i, course in enumerate(output.courses, 1):
            print(f"   {i}. {course.get('name', 'N/A')}")
            if course.get('description'):
                print(f"      {course['description']}")
    
    if hasattr(output, 'institutions') and output.institutions:
        print(f"\n🏫 Instituições Sugeridas:")
        for inst in output.institutions:
            print(f"   • {inst.get('name', 'N/A')}")
    
    if hasattr(output, 'advice') and output.advice:
        print(f"\n💡 Conselhos:")
        print(f"   {output.advice}")
    
    print("\n" + "=" * 50)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    # Valida os dados usando o schema Pydantic
    try:
        user_input = UserInput(
            interesse=args.interesse,
            preferencia=args.preferencia
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
        result = advisor_crew.kickoff(inputs={
            "interesse": user_input.interesse,
            "preferencia": user_input.preferencia
        })

        raw_text = result if isinstance(result, str) else str(result)

        json_dict = try_extract_json(raw_text)

        if json_dict is None:
            print("[ERRO] A resposta do modelo não veio em JSON puro conforme o expected_output.", file=sys.stderr)
            print("Conteúdo bruto recebido (parcial para diagnóstico):", file=sys.stderr)
            print(raw_text[:1000], file=sys.stderr)
            return 1

        # validação de esquema (estrutura/tipos/limites)
        try:
            output_obj = OutputAdvisor.model_validate(json_dict)
        except ValidationError as ve:
            print(f"[ERRO] Erro de validação do esquema de saída: {ve}", file=sys.stderr)
            print("\nJSON extraído (para revisão):", file=sys.stderr)
            print(json.dumps(json_dict, ensure_ascii=False, indent=2), file=sys.stderr)
            return 1

        # validações de negócio (ranks, fontes, modalidade vs preferência, etc.)
        validation = validate_output_contract(
            raw_json=json_dict,
            preferencia=user_input.preferencia,
            http_check=False  # False para testes rápidos via CLI
        )

        if not validation.valid:
            print("[ERRO] Resultado inválido segundo as regras de negócio.", file=sys.stderr)
            print("\nErros:", file=sys.stderr)
            for err in validation.errors:
                print(f"- {err}", file=sys.stderr)

            if validation.warnings:
                print("\nAvisos:", file=sys.stderr)
                for warn in validation.warnings:
                    print(f"- {warn}", file=sys.stderr)

            if validation.normalized:
                print("\nSaída normalizada (para diagnóstico):", file=sys.stderr)
                print(json.dumps(validation.normalized.model_dump(mode="json"), ensure_ascii=False, indent=2), file=sys.stderr)
            else:
                print("\nJSON recebido (para diagnóstico):", file=sys.stderr)
                print(json.dumps(json_dict, ensure_ascii=False, indent=2), file=sys.stderr)

            return 1

        # Impressão
        if args.json:
            print(validation.normalized.model_dump_json(indent=2))
        else:
            _print_pretty(validation.normalized)

        if validation.warnings:
            print("\nAvisos (não bloqueantes):")
            for warn in validation.warnings:
                print(f"- {warn}")

        return 0

    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}", file=sys.stderr)
        print("Verifique se todas as dependências estão instaladas e as chaves de API configuradas.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
