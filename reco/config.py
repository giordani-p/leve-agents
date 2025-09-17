# reco/config.py
"""
Parâmetros centrais do Sistema de Recomendação — V4 / P1 Híbrido (BM25 + MPNet)

Mudanças nesta revisão (P1):
- Suporte a modo HÍBRIDO (BM25 + Denso) com blending/normalização configuráveis.
- Thresholds separados por coleção (trilhas vs vagas).
- Versão de modelo e nomes de índices vetoriais (facilitam shadow test/rollback).
- Observabilidade (logs do retrieval e do explainer).
- Sinônimos ativados apenas para o caminho BM25 (no denso ficam desligados).
- Ajustes finos: SCORE_CAP=0.99, DOMINANCE_MIN_ACCEPT=0.60, HTTP_TIMEOUT_READ=10.0.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, List, Literal, Optional


# -----------------------------
# Fonte de dados
# -----------------------------
DataSource = Literal["api", "files"]


@dataclass(frozen=True)
class RecoConfig:
    # -----------------------------
    # Regras de negócio / ranking
    # -----------------------------
    MAX_SUGGESTIONS: int = 3
    TAG_BOOST: float = 0.10
    BEGINNER_BOOST: float = 0.05
    TITLE_DESC_BOOST: float = 0.15
    SCORE_CAP: float = 0.99
    DOMINANCE_MIN_ACCEPT: float = 0.60

    # Thresholds por coleção
    MATCH_THRESHOLD_TRILHAS: float = 0.72
    MATCH_THRESHOLD_VAGAS: float = 0.78  # (usado no P2)

    # Filtro de status (apenas Published nesta fase)
    ALLOWED_STATUS: Tuple[str, ...] = ("Published",)

    # Uso de pistas do snapshot (hints) na query
    USE_SNAPSHOT_HINTS: bool = True
    SNAPSHOT_MAX_HINTS: int = 3

    # (Opcional) limite de tamanho da query construída
    QUERY_MAX_CHARS: int = 0  # 0 = sem limite

    # -----------------------------
    # Embeddings / Dense Retrieval (MPNet)
    # -----------------------------
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    EMBED_DIM: int = 768
    EMBEDDING_DEVICE: Optional[str] = None  # "cpu" | "cuda" | None (auto)
    EMBEDDING_BATCH_SIZE: int = 64
    TOP_K_DEFAULT: int = 50  # top-K bruto retornado pelo denso

    # -----------------------------
    # Híbrido BM25 + Denso
    # -----------------------------
    USE_HYBRID: bool = False
    FUSION_METHOD: Literal["weighted", "rrf"] = "weighted"
    WEIGHTS: Optional[Dict[str, float]] = None  # definido em __post_init__  {"semantic": 0.65, "bm25": 0.35}
    NORMALIZATION: Literal["minmax", "zscore"] = "minmax"
    NORMALIZATION_EPS: float = 1e-6

    # -----------------------------
    # Expansão leve de consulta (sinônimos)
    # - Aplicar apenas no BM25; no denso manter desligado
    # -----------------------------
    USE_QUERY_SYNONYMS_BM25: bool = True
    USE_QUERY_SYNONYMS_DENSE: bool = False
    QUERY_SYNONYMS: Optional[Dict[str, List[str]]] = None  # definido em __post_init__

    # -----------------------------
    # Outras configurações
    # -----------------------------
    RANDOM_SEED: int = 42

    # -----------------------------
    # Integração via API (httpx)
    # -----------------------------
    SOURCE: DataSource = "api"                   # "api" | "files"
    TRAILS_API_BASE: str = "http://localhost:3000"
    API_FILTER_PUBLISHED: bool = True
    FALLBACK_TO_FILES: bool = True

    # Timeouts (segundos). httpx permite granularidade: connect/read/write/pool.
    HTTP_TIMEOUT_CONNECT: float = 3.0
    HTTP_TIMEOUT_READ: float = 10.0
    HTTP_TIMEOUT_WRITE: float = 3.0
    HTTP_TIMEOUT_POOL: float = 3.0

    # Retries com backoff simples (exponencial): attempts = 1 + HTTP_RETRIES
    HTTP_RETRIES: int = 2
    HTTP_BACKOFF_BASE: float = 0.4

    # Limites de paginação (se o endpoint paginar no futuro)
    API_MAX_PAGES: int = 10
    API_PAGE_SIZE_HINT: Optional[int] = None

    # -----------------------------
    # Versionamento / índices vetoriais
    # -----------------------------
    MODEL_VERSION: str = "mpnet_v1"
    INDEX_TRILHAS: str = "trilhas_mpnet_v1"
    INDEX_VAGAS: str = "vagas_mpnet_v1"  # (usado no P2)

    # -----------------------------
    # Guardrails / Filtros duros (parametrizados)
    # -----------------------------
    ENFORCE_PUBLISHED: bool = True
    ENFORCE_LOCATION: bool = True     # (vagas, P2)
    ENFORCE_SENIORITY: bool = True    # (vagas, P2)
    ENFORCE_REGIME: bool = True       # (vagas, P2)

    # -----------------------------
    # Observabilidade
    # -----------------------------
    LOG_RETRIEVAL_DEBUG: bool = True
    LOG_EXPLAIN_MATCH: bool = True
    ANN_RANDOM_SEED: int = 42
    API_KEY: Optional[str] = None  # opcional; usado por data_loader_api

    # -----------------------------
    # LEGADO (TF-IDF) — compatibilidade
    # -----------------------------
    VECTOR_NGRAM_RANGE: Tuple[int, int] = (1, 2)
    VECTOR_MIN_DF: int = 1
    VECTOR_MAX_FEATURES: Optional[int] = None
    VECTOR_SUBLINEAR_TF: bool = True
    VECTOR_USE_IDF: bool = True
    VECTOR_LOWERCASE: bool = True
    VECTOR_STRIP_ACCENTS: Optional[str] = "unicode"
    VECTOR_STOP_WORDS: Optional[str] = None

    # -----------------------------
    # Defaults derivados / Pós-init
    # -----------------------------
    def __post_init__(self):
        # Pesos padrão para blending do modo híbrido
        if object.__getattribute__(self, "WEIGHTS") is None:
            object.__setattr__(self, "WEIGHTS", {"semantic": 0.65, "bm25": 0.35})

        # Sinônimos: chaves em caixa-baixa e sem acento; o código normaliza antes de consultar
        if object.__getattribute__(self, "QUERY_SYNONYMS") is None:
            base = {
                "programacao": ["programar", "programador", "coding", "coder", "desenvolver", "dev"],
                "logica": ["algoritmo", "algoritmos", "raciocinio"],
                "javascript": ["js", "java script"],
                "iniciante": ["beginner", "basico", "do zero"],
                "automatizar": ["automacao", "script", "scripts", "macro", "automatizado"],
                "trabalho": ["empresa", "servico", "expediente"],
                "dados": ["data", "csv", "planilha", "planilhas", "analise"],
                "excel": ["planilha", "planilhas", "spreadsheet", "xls", "xlsx"],
                "python": ["py", "pythonico", "pythonista"],
                "ia": ["inteligencia artificial", "ai"],
                "ux": ["user experience", "ux design"],
                "ui": ["user interface", "ui design"],
                "direito": ["juridico", "juridica"],
                "saude": ["saude mental"],
                "nutricao": ["nutricional"],
            }
            object.__setattr__(self, "QUERY_SYNONYMS", base)
