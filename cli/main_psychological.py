# cli/main_psychological_profiler.py
"""
CLI do Perfilador Educacional
- Lê dados de perfil do usuário (texto livre ou arquivo)
- Executa o crew de perfilagem e imprime o resultado validado no terminal
- Por padrão imprime de forma "amigável"; use --json para ver o objeto completo

Exemplos:
  python -m cli.main_profiler -d "Escolaridade: Ensino médio completo..."
  python -m cli.main_profiler --data-file files/snapshots/carlos_001.json --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from pydantic import ValidationError

# Adiciona o diretório raiz ao path para permitir importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega variáveis de ambiente
load_dotenv()

from crew_config import psychological_profiler_crew
from schemas.psychological_output import PsychologicalOutput
from validators.psychological_output_checks import validate_psychological_output
from helpers.json_extractor import try_extract_json


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="profiler-cli",
        description="Perfilador Educacional — Leve",
    )
    parser.add_argument(
        "-d", "--data",
        help="Dados de perfil do usuário (texto livre).",
    )
    parser.add_argument(
        "--data-file",
        help="Arquivo com dados de perfil do usuário.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o objeto ProfileOutput completo em JSON.",
    )
    return parser.parse_args(argv)


def _load_data_from_file(file_path: str) -> Optional[str]:
    """Carrega dados de perfil de um arquivo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except OSError as e:
        print(f"[ERRO] Falha ao carregar arquivo '{file_path}': {e}", file=sys.stderr)
        return None


def _print_pretty(output: PsychologicalOutput) -> None:
    """Imprime o resultado de forma amigável e concisa."""
    print("\n🧠 Análise Psicológica e Comportamental")
    print("=" * 50)
    
    # Perfil principal
    if hasattr(output, 'perfil_psicologico') and output.perfil_psicologico:
        print(f"\n📋 Perfil Psicológico:")
        print(f"   {output.perfil_psicologico}")
    
    # Motivações e valores essenciais
    if hasattr(output, 'motivacoes_principais') and output.motivacoes_principais:
        print(f"\n🎯 Motivações Principais:")
        for motivacao in output.motivacoes_principais:
            print(f"   • {motivacao}")
    
    if hasattr(output, 'valores_core') and output.valores_core:
        print(f"\n💎 Valores Fundamentais:")
        for valor in output.valores_core:
            print(f"   • {valor}")
    
    # Estilos comportamentais
    if hasattr(output, 'estilo_aprendizado') and output.estilo_aprendizado:
        print(f"\n📚 Estilo de Aprendizado: {output.estilo_aprendizado}")
    
    if hasattr(output, 'estilo_comunicacao') and output.estilo_comunicacao:
        print(f"💬 Estilo de Comunicação: {output.estilo_comunicacao}")
    
    if hasattr(output, 'estilo_lideranca') and output.estilo_lideranca:
        print(f"👑 Estilo de Liderança: {output.estilo_lideranca}")
    
    # Preferências de trabalho
    if hasattr(output, 'ambiente_ideal') and output.ambiente_ideal:
        print(f"\n🏢 Ambiente Ideal:")
        ambiente = output.ambiente_ideal
        if isinstance(ambiente, dict):
            for key, value in ambiente.items():
                if value:
                    print(f"   • {key.capitalize()}")
    
    if hasattr(output, 'modalidade_trabalho') and output.modalidade_trabalho:
        print(f"💻 Modalidade: {output.modalidade_trabalho}")
    
    if hasattr(output, 'tipo_atividade') and output.tipo_atividade:
        print(f"🎯 Atividade: {output.tipo_atividade}")
    
    # Pontos fortes e desafios
    if hasattr(output, 'pontos_fortes') and output.pontos_fortes:
        print(f"\n💪 Pontos Fortes:")
        for ponto in output.pontos_fortes:
            print(f"   • {ponto}")
    
    if hasattr(output, 'areas_desenvolvimento') and output.areas_desenvolvimento:
        print(f"\n🎯 Áreas para Desenvolvimento:")
        for area in output.areas_desenvolvimento:
            print(f"   • {area}")
    
    # Compatibilidade
    if hasattr(output, 'perfis_carreira_compativel') and output.perfis_carreira_compativel:
        print(f"\n🚀 Perfis de Carreira Compatíveis:")
        for perfil in output.perfis_carreira_compativel:
            print(f"   • {perfil}")
    
    # Alertas importantes
    if hasattr(output, 'alertas_importantes') and output.alertas_importantes:
        print(f"\n⚠️ Alertas Importantes:")
        for alerta in output.alertas_importantes:
            print(f"   • {alerta}")
    
    # Análise de talentos
    if hasattr(output, 'interpretacao_talentos') and output.interpretacao_talentos:
        print(f"\n💎 Interpretação dos Talentos:")
        print(f"   {output.interpretacao_talentos}")
    
    if hasattr(output, 'integracao_metodologias') and output.integracao_metodologias:
        print(f"\n🔄 Integração de Metodologias:")
        print(f"   {output.integracao_metodologias}")
    
    print("\n" + "=" * 50)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    
    # Carrega dados de perfil
    if args.data_file:
        dados = _load_data_from_file(args.data_file)
        if dados is None:
            return 1
    elif args.data:
        dados = args.data
    else:
        print("[ERRO] É necessário fornecer dados via --data ou --data-file", file=sys.stderr)
        return 2

    print("\nExecutando Perfilador Educacional...\n")

    try:
        result = psychological_profiler_crew.kickoff(inputs={"dados": dados})
        raw_text = result if isinstance(result, str) else str(result)
        json_dict = try_extract_json(raw_text)

        # Validação de esquema (estrutura/tipos/limites)
        if json_dict is None:
            print("[ERRO] Resposta não veio em JSON válido.", file=sys.stderr)
            print("Conteúdo bruto recebido (parcial):", file=sys.stderr)
            print(raw_text[:1000], file=sys.stderr)
            return 1

        try:
            output = PsychologicalOutput.model_validate(json_dict)
        except ValidationError as ve:
            print(f"[ERRO] Erro de validação do JSON de saída: {ve}", file=sys.stderr)
            print("\nJSON extraído (para revisão):", file=sys.stderr)
            print(json.dumps(json_dict, indent=2, ensure_ascii=False), file=sys.stderr)
            return 1

        # Validação de negócio (regras de negócio)
        validation = validate_psychological_output(json_dict)

        if not validation.valid:
            print("[ERRO] Resultado inválido segundo as regras de negócio:", file=sys.stderr)
            for err in validation.errors:
                print(f"- {err}", file=sys.stderr)

            print("\nJSON recebido (para diagnóstico):", file=sys.stderr)
            print(json.dumps(json_dict, indent=2, ensure_ascii=False), file=sys.stderr)
            return 1

        if validation.warnings:
            print("\nAvisos (não bloqueantes):")
            for warn in validation.warnings:
                print(f"- {warn}")

        # Impressão
        if args.json:
            print(validation.normalized.model_dump_json(indent=2))
        else:
            _print_pretty(validation.normalized)

        return 0

    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}", file=sys.stderr)
        print("Verifique se todas as dependências estão instaladas e as chaves de API configuradas.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())