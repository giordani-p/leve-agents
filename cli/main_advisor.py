"""
CLI do Orientador Educacional - Leve Agents

Fornece orientação educacional personalizada baseada em interesses e preferências.
Executa validação completa dos resultados e suporta saída em JSON.

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

from dotenv import load_dotenv
from pydantic import ValidationError

# Configuração de path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from crew_config import advisor_crew
from schemas.advisor_inputs import AdvisorInput
from schemas.advisor_output import OutputAdvisor
from validators.advisor_output_checks import validate_output_contract
from helpers.json_extractor import try_extract_json

# Inicialização do AgentOps para monitoramento de custos
import agentops
if os.getenv("AGENTOPS_API_KEY"):
    agentops.init()


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="advisor-cli",
        description="Planejador de Carreira Estratégico — Leve",
    )
    parser.add_argument(
        "--snapshot",
        help="Caminho para o arquivo de snapshot do jovem (ex: files/snapshots/pablo_001.json)",
    )
    parser.add_argument(
        "-i", "--interesse",
        help="O que você gostaria de aprender ou fazer no futuro? (opcional se snapshot fornecido)",
    )
    parser.add_argument(
        "-p", "--preferencia",
        help="Qual formato ou região você prefere (ex: online, presencial, SP, exterior)? (opcional se snapshot fornecido)",
    )
    parser.add_argument(
        "--foco",
        help="Foco específico do planejamento (ex: 'primeiro emprego', 'mudança de carreira', 'sobrevivência básica')",
    )
    parser.add_argument(
        "--urgencia",
        choices=["baixa", "moderada", "alta", "critica"],
        default="moderada",
        help="Nível de urgência do planejamento (padrão: moderada)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o objeto OutputAdvisor completo em JSON.",
    )
    return parser.parse_args(argv)


def _print_pretty(output: OutputAdvisor) -> None:
    """Imprime o resultado de forma amigável."""
    print("\n🎯 Planejamento Estratégico de Carreira")
    print("=" * 60)
    
    # Resumo
    print(f"\n📋 Resumo:")
    print(f"   {output.summary}")
    
    # Análise do perfil
    if hasattr(output, 'profile_analysis') and output.profile_analysis:
        print(f"\n🔍 Análise do Perfil:")
        print(f"   Perfil Principal: {output.profile_analysis.perfil_principal}")
        print(f"   Nível de Prioridade: {output.profile_analysis.nivel_prioridade}/5")
        
        if output.profile_analysis.pontos_fortes:
            print(f"   Pontos Fortes: {', '.join(output.profile_analysis.pontos_fortes)}")
        
        if output.profile_analysis.areas_desenvolvimento:
            print(f"   Áreas de Desenvolvimento: {', '.join(output.profile_analysis.areas_desenvolvimento)}")
        
        if output.profile_analysis.barreiras_principais:
            print(f"   Barreiras Principais: {', '.join(output.profile_analysis.barreiras_principais)}")
    
    # Recomendações
    if hasattr(output, 'options') and output.options:
        print(f"\n🎯 Recomendações ({len(output.options)} opções):")
        for option in output.options:
            print(f"\n   {option.rank}. {option.title}")
            print(f"      Tipo: {option.type.replace('_', ' ').title()}")
            if option.institution:
                print(f"      Instituição: {option.institution}")
            if option.modality:
                print(f"      Modalidade: {option.modality}")
            if option.duration:
                print(f"      Duração: {option.duration}")
            print(f"      Compatibilidade: {option.compatibility_score}/10")
            print(f"      Por que recomendado: {option.why_recommended}")
            if option.next_steps:
                print(f"      Próximos passos: {'; '.join(option.next_steps)}")
    
    # Próximos passos gerais
    if hasattr(output, 'general_next_steps') and output.general_next_steps:
        print(f"\n📝 Próximos Passos Gerais:")
        for i, step in enumerate(output.general_next_steps, 1):
            print(f"   {i}. {step}")
    
    # Conselho personalizado
    if hasattr(output, 'personalized_advice') and output.personalized_advice:
        print(f"\n💡 Conselho Personalizado:")
        print(f"   {output.personalized_advice}")
    
    # Oportunidades
    if hasattr(output, 'opportunities') and output.opportunities:
        print(f"\n🌟 Oportunidades Identificadas:")
        for opp in output.opportunities:
            print(f"   • {opp}")
    
    # Fatores de risco
    if hasattr(output, 'risk_factors') and output.risk_factors:
        print(f"\n⚠️  Fatores de Risco:")
        for risk in output.risk_factors:
            print(f"   • {risk}")
    
    print("\n" + "=" * 60)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    # Validação básica
    if not args.snapshot and not args.interesse:
        print("[ERRO] Pelo menos '--snapshot' ou '--interesse' deve ser fornecido", file=sys.stderr)
        return 2

    # Valida os dados usando o schema Pydantic
    try:
        user_input = AdvisorInput(
            snapshot_file=args.snapshot,
            interesse=args.interesse,
            preferencia=args.preferencia,
            foco_especifico=args.foco,
            prioridade_urgencia=args.urgencia
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
            "snapshot_file": user_input.snapshot_file,
            "interesse": user_input.interesse,
            "preferencia": user_input.preferencia,
            "foco_especifico": user_input.foco_especifico,
            "prioridade_urgencia": user_input.prioridade_urgencia
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
            snapshot_file=user_input.snapshot_file,
            foco_especifico=user_input.foco_especifico,
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
