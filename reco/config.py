# reco/config.py
"""
Parâmetros centrais do Sistema de Recomendação (CLI).

Novidades desta revisão:
- Similaridade acento-insensível: adiciona strip_accents para o TF-IDF.
- Peso do boost por título/descrição elevado (TITLE_DESC_BOOST=0.25).
- Parâmetros explícitos para fallback de dominância (DOMINANCE_MIN_ACCEPT).
- Mini dicionário de sinônimos para expandir a consulta (opcional).

Observações:
- Filtro rígido por status 'Published' (ver ALLOWED_STATUS).
- Pontuações são normalizadas no intervalo [0.0, 1.0] e limitadas por SCORE_CAP.
- Similaridade V1: TF-IDF + cosseno (scikit-learn), com n-grams (1,2).
- Sem pandas no core. Dependências principais: scikit-learn (numpy/scipy).
"""

from dataclasses import dataclass
from typing import Dict, Tuple, List


@dataclass(frozen=True)
class RecoConfig:
    # -----------------------------
    # Regras de negócio / ranking
    # -----------------------------
    MATCH_THRESHOLD: float = 0.74          # limiar mínimo para entrar no top-N
    MAX_SUGGESTIONS: int = 3               # cortar a lista final em até 3 itens
    TAG_BOOST: float = 0.10                # bônus quando há match claro de tags/tema
    BEGINNER_BOOST: float = 0.05           # bônus leve para trilhas Beginner (fase de descoberta)
    TITLE_DESC_BOOST: float = 0.15         # bônus quando keyword aparece no título/descrição/conteúdo
    SCORE_CAP: float = 0.96                 # teto para evitar score > 1.0 após boosts
    DOMINANCE_MIN_ACCEPT: float = 0.55     # fallback: aceita top-1 se ninguém passar do threshold, mas top ≥ este valor

    # Filtro de status (apenas Published nesta fase)
    ALLOWED_STATUS: Tuple[str, ...] = ("Published",)

    # Uso de pistas do snapshot (hints) na query
    USE_SNAPSHOT_HINTS: bool = True
    SNAPSHOT_MAX_HINTS: int = 3            # até 3 pistas do snapshot podem ser usadas

    # -----------------------------
    # Vetorização / similaridade (TF-IDF)
    # -----------------------------
    VECTOR_NGRAM_RANGE: Tuple[int, int] = (1, 2)   # unigrams + bigrams
    VECTOR_MIN_DF: int = 1                         # considerar termos raros (catálogo pequeno)
    VECTOR_MAX_FEATURES: int | None = None         # sem limite por ora
    VECTOR_SUBLINEAR_TF: bool = True               # tf = 1 + log(tf)
    VECTOR_USE_IDF: bool = True                    # usar IDF
    VECTOR_LOWERCASE: bool = True                  # normalizar para minúsculas
    VECTOR_STRIP_ACCENTS: str | None = "unicode"   # remove acentos na vetorização ("unicode" recomendado)
    VECTOR_STOP_WORDS: str | None = None           # sem stopwords (pt-BR não nativo no sklearn)

    # -----------------------------
    # Expansão leve de consulta (sinônimos)
    # -----------------------------
    USE_QUERY_SYNONYMS: bool = True
    QUERY_SYNONYMS: Dict[str, List[str]] = None  # definido abaixo via __post_init__ fake

    # -----------------------------
    # Outras configurações
    # -----------------------------
    NORMALIZE_MIN: float = 0.0
    NORMALIZE_MAX: float = 1.0
    RANDOM_SEED: int = 42                         # reprodutibilidade em empates/ordenação estável

    # Hack simples para permitir default mutável de QUERY_SYNONYMS em dataclass frozen
    def __post_init__(self):
        if object.__getattribute__(self, "QUERY_SYNONYMS") is None:
            # Chaves devem estar em caixa baixa e sem acento; o código que usa fará a mesma normalização
            base = {
                "programacao": ["programar", "programador", "coding", "coder", "desenvolver", "dev"],
                "logica": ["algoritmo", "algoritmos", "raciocinio"],
                "javascript": ["js", "java script"],
                "iniciante": ["beginner", "basico", "do zero"],
                "automatizar": ["automacao", "script", "scripts", "macro", "automatizado"],
                "trabalho": ["empresa", "servico", "expediente"],
                "dados": ["data", "csv", "planilha", "planilhas", "analise"],
                "excel": ["planilha", "planilhas", "spreadsheet", "xls", "xlsx"],
                "python": ["py", "python", "pythonico", "pythonista"],
                "ia": ["inteligencia artificial", "inteligencia artificialia", "inteligencia artificialia"],
                "ux": ["user experience", "user experience design", "user experience designer", "user experience designe", "user experience designer"],
                "ui": ["user interface", "user interface design", "user interface designer", "user interface designe", "user interface designer"],
                "direito": ["juridico", "juridica", "juridico", "juridica"],
                "saude": ["saude", "saude mental", "saude mental", "saude mental"],
                "nutricao": ["nutricao", "nutricao", "nutricao", "nutricao"],
            }
            object.__setattr__(self, "QUERY_SYNONYMS", base)
