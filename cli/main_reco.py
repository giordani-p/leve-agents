# cli/main_reco.py
"""
CLI do Sistema de Recomendação (V1)
- Lê a pergunta do jovem e os caminhos dos JSONs de snapshot e trilhas.
- Executa o pipeline e imprime o resultado validado no terminal.
- Por padrão imprime de forma "amigável"; use --json para ver o objeto completo.

Fontes de dados:
  --source api   → lê catálogo via endpoint /api/trails do backend da Leve
  --source files → lê catálogo via arquivo local em files/trails/trails_examples.json

Exemplos:
  python -m cli.main_reco -q "Quero aprender programação do zero"
  python -m cli.main_reco -q "Como organizar meus estudos?" --json
  python -m cli.main_reco -q "trilhas para iniciantes" --source api --api-base http://localhost:3000
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from typing import Optional

from reco.config import RecoConfig
from reco.pipeline import run as run_pipeline
from schemas.trail_input import TrailInput


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="reco-cli",
        description="Sistema de Recomendação (CLI) — Leve",
    )
    parser.add_argument(
        "-q", "--user-question",
        required=True,
        help="Pergunta/dúvida do jovem (texto livre).",
    )
    parser.add_argument(
        "--snapshot-path",
        default="files/snapshots/carlos_001.json",
        help="Caminho do JSON de snapshot (default: files/snapshots/carlos_001.json).",
    )
    parser.add_argument(
        "--trails-path",
        default="files/trails/trails_examples.json",
        help="Caminho do JSON de trilhas (default: files/trails/trails_examples.json). Ignorado quando --source=api.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=3,
        choices=[1, 2, 3],
        help="Número máximo de trilhas sugeridas (1..3, default: 3).",
    )
    parser.add_argument(
        "--user-id",
        default=None,
        help="UUID do usuário (opcional, para personalização futura).",
    )
    parser.add_argument(
        "--contexto-extra",
        default=None,
        help="Contexto adicional livre (ex.: 'iniciante; JavaScript').",
    )
    parser.add_argument(
        "--source",
        choices=["api", "files"],
        default="api",
        help="Fonte do catálogo de trilhas: 'api' (padrão) ou 'files'.",
    )
    parser.add_argument(
        "--api-base",
        default=None,
        help="Override da base URL do backend (ex.: http://localhost:3000). Útil com --source=api.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o objeto TrailOutput completo em JSON.",
    )
    return parser.parse_args(argv)


def _print_pretty(output) -> None:
    from textwrap import indent

    if output.status == "ok" and output.suggested_trails:
        print("\n✨ Sugestões para você")
        for i, s in enumerate(output.suggested_trails, start=1):
            print(f"\n#{i} — {s.title}")
            print(indent(f"por que indicar: {s.why_match}", "  "))
            print(indent(f"match_score: {s.match_score:.2f}", "  "))
        print("\n" + output.short_answer)
        print(f"👉 {output.cta}\n")
    else:
        # fora_do_escopo
        print("\nℹ️  " + (output.mensagem_padrao or "Não foi possível recomendar trilhas agora."))
        print("\n" + (output.short_answer or "Tente reformular sua pergunta com uma palavra-chave."))
        print(f"👉 {output.cta}\n")


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    # Monta a entrada validada (TrailInput cuida dos limites básicos)
    try:
        user_input = TrailInput(
            user_question=args.user_question,
            user_id=args.user_id,
            contexto_extra=args.contexto_extra,
            max_results=args.max_results,
        )
    except Exception as e:
        print(f"[ERRO] Entrada inválida: {e}", file=sys.stderr)
        return 2

    # Configuração com seleção de fonte e override opcional da base da API
    cfg = RecoConfig(SOURCE=args.source)
    if args.api_base:
        cfg = replace(cfg, TRAILS_API_BASE=args.api_base)

    try:
        output = run_pipeline(
            user_input=user_input,
            snapshot_path=args.snapshot_path,
            trails_path=args.trails_path,  # ignorado quando SOURCE='api'
            cfg=cfg,
        )
    except Exception as e:
        print(f"[ERRO] Falha ao executar o recomendador: {e}", file=sys.stderr)
        return 1

    # Impressão
    if args.json:
        print(output.model_dump_json(indent=2))
    else:
        _print_pretty(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
