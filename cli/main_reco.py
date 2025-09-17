# cli/main_reco.py
"""
CLI do Sistema de Recomendação — Versão Oficial (P1 híbrida)
- Mantém compatibilidade com sua CLI atual (V1).
- Acrescenta controles da P1: modo (hybrid/bm25/dense), blending, normalização e thresholds por coleção.

Fontes de dados:
  --source api   → lê catálogo via endpoint /api/trails do backend da Leve
  --source files → lê catálogo via arquivo local em files/trails/trails_examples.json

Exemplos:
  python -m cli.main_reco -q "Quero aprender programação do zero"
  python -m cli.main_reco -q "trilhas para iniciantes" --json
  python -m cli.main_reco -q "Como organizar meus estudos?" --source api --api-base http://localhost:3000
  python -m cli.main_reco -q "Quais áreas combinam com meu perfil?" --source files --snapshot-path files/snapshots/ana_001.json

Termos:
- blending (mistura de escores): combina BM25 (esparso) e Embeddings (denso).
- normalização: coloca escores numa mesma escala antes do blending.
- threshold (limiar): valor mínimo de score para aceitar uma recomendação.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace, is_dataclass, asdict
from typing import Optional

from reco.config import RecoConfig
from reco.pipeline import run as run_pipeline
from schemas.trail_input import TrailInput


# --------- Argumentos --------- #
def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="reco-cli",
        description="Sistema de Recomendação (CLI) — Leve (P1 híbrida).",
    )

    # Entrada do usuário
    parser.add_argument(
        "-q", "--user-question",
        required=True,
        help="Pergunta/dúvida do jovem (texto livre).",
    )
    parser.add_argument(
        "--snapshot-path",
        default="files/snapshots/pablo_agro_001.json",
        help="Caminho do JSON de snapshot (default: files/snapshots/pablo_agro_001.json).",
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

    # Fontes de dados
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

    # Controles da P1 (retrieval/ranking)
    parser.add_argument(
        "--collection",
        choices=["trilhas", "vagas"],
        default="trilhas",
        help="Coleção alvo da recomendação (default: trilhas).",
    )
    parser.add_argument(
        "--mode",
        choices=["hybrid", "bm25", "dense"],
        default="hybrid",
        help="Modo de indexação/ranking: híbrido, apenas BM25, ou apenas denso (default: hybrid).",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.60,
        help="Peso do componente denso no blending (0..1). Ex.: 0.60 = 60%% denso, 40%% BM25 (default: 0.60).",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Ativa normalização dos escores antes do blending (recomendado para hybrid).",
    )
    parser.add_argument(
        "--threshold-trails",
        type=float,
        default=0.55,
        help="Threshold (limiar) de aceitação para TRILHAS (default: 0.55).",
    )
    parser.add_argument(
        "--threshold-jobs",
        type=float,
        default=0.65,
        help="Threshold (limiar) de aceitação para VAGAS (default: 0.65).",
    )

    # Saída
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o objeto TrailOutput completo em JSON.",
    )

    return parser.parse_args(argv)


# --------- Saída “amigável” --------- #
def _print_pretty(output) -> None:
    from textwrap import indent

    if getattr(output, "status", None) == "ok" and getattr(output, "suggested_trails", None):
        print("\n✨ Sugestões para você")
        for i, s in enumerate(output.suggested_trails, start=1):
            title = getattr(s, "title", None) or getattr(s, "nome", None) or getattr(s, "slug", None) or f"Trilha #{i}"
            why = getattr(s, "why_match", "") or getattr(s, "motivo", "") or ""
            match_score = getattr(s, "match_score", None)
            print(f"\n#{i} — {title}")
            if why:
                print(indent(f"por que indicar: {why}", "  "))
            if isinstance(match_score, (int, float)):
                print(indent(f"match_score: {match_score:.2f}", "  "))
        short = getattr(output, "short_answer", "") or ""
        cta = getattr(output, "cta", "") or ""
        if short:
            print("\n" + short)
        if cta:
            print(f"👉 {cta}\n")
    else:
        # fora_do_escopo ou erro controlado
        msg = getattr(output, "mensagem_padrao", None) or "Não foi possível recomendar trilhas agora."
        short = getattr(output, "short_answer", None) or "Tente reformular sua pergunta com uma palavra-chave."
        cta = getattr(output, "cta", "") or ""
        print("\nℹ️  " + msg)
        print("\n" + short)
        if cta:
            print(f"👉 {cta}\n")


# --------- Auxiliares de configuração --------- #
def _safe_replace_cfg(cfg: RecoConfig, **kwargs) -> RecoConfig:
    """
    Tenta aplicar campos adicionais em RecoConfig sem quebrar quando o campo não existe.
    - Se for dataclass, usa replace() quando possível; senão, faz setattr com guarda.
    - Isso permite evoluir a config aos poucos sem acoplar a CLI.
    """
    if is_dataclass(cfg):
        # Tenta apenas para chaves existentes
        cfg_fields = set(asdict(cfg).keys())
        replace_kwargs = {k: v for k, v in kwargs.items() if k in cfg_fields}
        if replace_kwargs:
            try:
                cfg = replace(cfg, **replace_kwargs)
            except TypeError:
                # Fallback: setattr
                for k, v in replace_kwargs.items():
                    try:
                        setattr(cfg, k, v)
                    except Exception:
                        pass
        # Para chaves inexistentes, ignora silenciosamente
    else:
        # Não é dataclass? Faz setattr best-effort
        for k, v in kwargs.items():
            try:
                setattr(cfg, k, v)
            except Exception:
                pass
    return cfg


# --------- Main --------- #
def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    # Monta a entrada validada
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

    # Configuração base
    cfg = RecoConfig(SOURCE=args.source)
    if args.api_base:
        cfg = _safe_replace_cfg(cfg, TRAILS_API_BASE=args.api_base)

    # Parâmetros P1 — aplicados de forma resiliente (apenas se existirem na RecoConfig)
    # Campos sugeridos na config:
    #   MODE (str: 'hybrid'|'bm25'|'dense')
    #   ALPHA (float: peso do denso no blending)
    #   NORMALIZE (bool)
    #   THRESHOLDS (dict: {'trilhas': float, 'vagas': float})
    #   COLLECTION (str: 'trilhas'|'vagas')
    cfg = _safe_replace_cfg(
        cfg,
        MODE=args.mode,
        ALPHA=args.alpha,
        NORMALIZE=args.normalize,
        THRESHOLDS={"trilhas": args.threshold_trails, "vagas": args.threshold_jobs},
        COLLECTION=args.collection,
    )

    # Execução
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
    if getattr(args, "json", False):
        # Pydantic v2
        if hasattr(output, "model_dump_json"):
            print(output.model_dump_json(indent=2))
        # Pydantic v1 (compat)
        elif hasattr(output, "json"):
            print(output.json(indent=2, ensure_ascii=False))
        else:
            # Melhor esforço
            import json
            try:
                print(json.dumps(output, ensure_ascii=False, indent=2))
            except TypeError:
                print(str(output))
    else:
        _print_pretty(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
