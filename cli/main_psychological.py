"""
CLI do Perfilador Psicológico - Leve Agents

Analisa perfis psicológicos e educacionais baseados em dados fornecidos.
Suporta entrada via texto livre ou arquivo JSON e validação completa dos resultados.

Exemplos:
  python -m cli.main_psychological -d "Escolaridade: Ensino médio completo..."
  python -m cli.main_psychological --data-file files/snapshots/carlos_001.json --json
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

from crew_config import psychological_profiler_crew
from schemas.psychological_output import PsychologicalOutput
from validators.psychological_output_checks import validate_psychological_output
from helpers.json_extractor import try_extract_json
from helpers.snapshot_selector import select_profile_snapshot, load_snapshot_from_file

# Inicialização do AgentOps para monitoramento de custos
import agentops
if os.getenv("AGENTOPS_API_KEY"):
    agentops.init()


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
        "--snapshot",
        help="Caminho para o arquivo de snapshot do jovem (ex: files/snapshots/pablo_001.json)",
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


def _format_snapshot_as_text(snapshot_data: dict) -> str:
    """Converte dados de snapshot JSON em texto formatado para o perfilador."""
    text_parts = []
    
    # Dados pessoais
    if 'dados_pessoais' in snapshot_data:
        dados_pessoais = snapshot_data['dados_pessoais']
        text_parts.append("=== DADOS PESSOAIS ===")
        text_parts.append(f"Nome: {dados_pessoais.get('nome_preferido', 'N/A')}")
        text_parts.append(f"Idade: {dados_pessoais.get('idade', 'N/A')}")
        text_parts.append(f"Localização: {dados_pessoais.get('localizacao', 'N/A')}")
        text_parts.append(f"Disponibilidade de tempo: {dados_pessoais.get('disponibilidade_tempo', 'N/A')}")
        text_parts.append("")
    
    # Situação acadêmica
    if 'situacao_academica' in snapshot_data:
        situacao = snapshot_data['situacao_academica']
        text_parts.append("=== SITUAÇÃO ACADÊMICA ===")
        text_parts.append(f"Estágio escolar: {situacao.get('estagio_escolar', 'N/A')}")
        text_parts.append(f"Curso atual: {situacao.get('curso_atual', 'N/A')}")
        text_parts.append(f"Instituição: {situacao.get('instituicao', 'N/A')}")
        text_parts.append(f"Nota média: {situacao.get('nota_media', 'N/A')}")
        
        if situacao.get('materias_favoritas'):
            text_parts.append(f"Matérias favoritas: {', '.join(situacao['materias_favoritas'])}")
        if situacao.get('materias_dificuldade'):
            text_parts.append(f"Matérias com dificuldade: {', '.join(situacao['materias_dificuldade'])}")
        text_parts.append("")
    
    # Objetivos de carreira
    if 'objetivos_carreira' in snapshot_data:
        objetivos = snapshot_data['objetivos_carreira']
        text_parts.append("=== OBJETIVOS DE CARREIRA ===")
        text_parts.append(f"Objetivo principal: {objetivos.get('objetivo_principal', 'N/A')}")
        
        if objetivos.get('objetivos_especificos'):
            text_parts.append("Objetivos específicos:")
            for obj in objetivos['objetivos_especificos']:
                text_parts.append(f"- {obj}")
        
        if objetivos.get('metas_temporais'):
            metas = objetivos['metas_temporais']
            if metas.get('curto_prazo'):
                text_parts.append("Metas de curto prazo:")
                for meta in metas['curto_prazo']:
                    text_parts.append(f"- {meta}")
            if metas.get('medio_prazo'):
                text_parts.append("Metas de médio prazo:")
                for meta in metas['medio_prazo']:
                    text_parts.append(f"- {meta}")
            if metas.get('longo_prazo'):
                text_parts.append("Metas de longo prazo:")
                for meta in metas['longo_prazo']:
                    text_parts.append(f"- {meta}")
        text_parts.append("")
    
    # Experiência profissional
    if 'experiencia_profissional' in snapshot_data:
        exp = snapshot_data['experiencia_profissional']
        text_parts.append("=== EXPERIÊNCIA PROFISSIONAL ===")
        text_parts.append(f"Tem experiência: {exp.get('tem_experiencia', 'N/A')}")
        if exp.get('experiencias'):
            text_parts.append("Experiências:")
            for exp_item in exp['experiencias']:
                text_parts.append(f"- {exp_item}")
        text_parts.append("")
    
    # Habilidades e competências
    if 'habilidades_competencias' in snapshot_data:
        hab = snapshot_data['habilidades_competencias']
        text_parts.append("=== HABILIDADES E COMPETÊNCIAS ===")
        if hab.get('habilidades_tecnicas'):
            text_parts.append(f"Habilidades técnicas: {', '.join(hab['habilidades_tecnicas'])}")
        if hab.get('habilidades_interpessoais'):
            text_parts.append(f"Habilidades interpessoais: {', '.join(hab['habilidades_interpessoais'])}")
        if hab.get('idiomas'):
            text_parts.append(f"Idiomas: {', '.join(hab['idiomas'])}")
        text_parts.append("")
    
    # Preferências e interesses
    if 'preferencias_interesses' in snapshot_data:
        pref = snapshot_data['preferencias_interesses']
        text_parts.append("=== PREFERÊNCIAS E INTERESSES ===")
        if pref.get('areas_interesse'):
            text_parts.append(f"Áreas de interesse: {', '.join(pref['areas_interesse'])}")
        if pref.get('tipo_trabalho_preferido'):
            text_parts.append(f"Tipo de trabalho preferido: {pref['tipo_trabalho_preferido']}")
        if pref.get('ambiente_trabalho_ideal'):
            text_parts.append(f"Ambiente de trabalho ideal: {pref['ambiente_trabalho_ideal']}")
        text_parts.append("")
    
    return "\n".join(text_parts)


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
    dados = None
    
    if args.snapshot:
        # Carrega snapshot se fornecido
        snapshot_data = load_snapshot_from_file(args.snapshot)
        if snapshot_data is None:
            return 1
        # Converte snapshot para formato de texto para o perfilador
        dados = _format_snapshot_as_text(snapshot_data)
    elif args.data_file:
        dados = _load_data_from_file(args.data_file)
        if dados is None:
            return 1
    elif args.data:
        dados = args.data
    else:
        # Se não foi fornecido nenhum input, permite seleção interativa de snapshot
        snapshot_data, snapshot_label = select_profile_snapshot()
        print(f"\nSnapshot selecionado: {snapshot_label}")
        if snapshot_data:
            dados = _format_snapshot_as_text(snapshot_data)
        else:
            print("[ERRO] É necessário fornecer dados via --data, --data-file ou --snapshot", file=sys.stderr)
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