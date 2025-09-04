# reco/indexer.py
"""
Cálculo de similaridade por conteúdo usando TF-IDF + cosseno (scikit-learn).

Responsabilidade:
- Receber o texto de consulta já montado (ex.: user_question [+ pistas/sinônimos]).
- Vetorizar candidatos (combined_text) e a consulta.
- Retornar um score de similaridade em [0, 1] para cada candidato.

Novidades:
- Vetorização acento-insensível (strip_accents via config).
- Normalização segura: se houver 1 candidato ou todos os valores forem iguais, não normaliza.

Observações:
- Não filtra por status aqui; isso deve ser feito antes (Published).
- Não aplica boosts/regras de negócio; isso é papel do ranker.
- Sem uso de pandas; apenas listas/dicts + scikit-learn.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from reco.config import RecoConfig
from schemas.trail_candidate import TrailCandidate


def _build_vectorizer(cfg: RecoConfig) -> TfidfVectorizer:
    """Cria o vetorizador TF-IDF de acordo com as configs (inclui strip_accents)."""
    return TfidfVectorizer(
        ngram_range=cfg.VECTOR_NGRAM_RANGE,
        min_df=cfg.VECTOR_MIN_DF,
        max_features=cfg.VECTOR_MAX_FEATURES,
        sublinear_tf=cfg.VECTOR_SUBLINEAR_TF,
        use_idf=cfg.VECTOR_USE_IDF,
        lowercase=cfg.VECTOR_LOWERCASE,
        stop_words=cfg.VECTOR_STOP_WORDS,
        strip_accents=cfg.VECTOR_STRIP_ACCENTS,
    )


def _prepare_corpus(candidates: List[TrailCandidate]) -> List[str]:
    """
    Extrai o 'combined_text' de cada candidato para formar o corpus.
    Garante string vazia quando não houver texto.
    """
    corpus: List[str] = []
    for c in candidates:
        text = (c.combined_text or "").strip()
        corpus.append(text)
    return corpus


def _normalize_scores(scores: np.ndarray, min_val: float = 0.0, max_val: float = 1.0) -> np.ndarray:
    """
    Normaliza vetor de scores para [min_val, max_val].

    Regras:
    - Se vetor estiver vazio: retorna como está.
    - Se houver apenas 1 valor único (ex.: só 1 candidato ou todos iguais): NÃO normaliza;
      retorna os scores originais (cosine TF-IDF já está em [0,1]).
    - Caso contrário: aplica min-max scaling.
    """
    if scores.size == 0:
        return scores

    unique_vals = np.unique(scores)
    if unique_vals.size <= 1:
        return scores

    s_min, s_max = float(scores.min()), float(scores.max())
    if s_max <= s_min:
        return scores

    scaled = (scores - s_min) / (s_max - min_val if (s_max - s_min) == 0 else (s_max - s_min))
    return scaled * (max_val - min_val) + min_val


def score(
    query_text: str,
    candidates: List[TrailCandidate],
    cfg: RecoConfig,
) -> List[Tuple[TrailCandidate, float]]:
    """
    Calcula a similaridade da consulta em relação a cada candidato.

    Parâmetros:
      - query_text: string final de consulta (ex.: pergunta do jovem [+ pistas]).
      - candidates: lista de TrailCandidate (já filtrados por Published).
      - cfg: RecoConfig com parâmetros do TF-IDF.

    Retorno:
      - Lista de tuplas (candidate, content_score) na mesma ordem dos candidatos de entrada.
    """
    if not candidates:
        return []

    q = (query_text or "").strip()
    if q == "":
        return [(c, 0.0) for c in candidates]

    corpus = _prepare_corpus(candidates)

    vectorizer = _build_vectorizer(cfg)
    try:
        X = vectorizer.fit_transform(corpus)  # shape: (n_docs, n_terms)
    except ValueError:
        return [(c, 0.0) for c in candidates]

    q_vec = vectorizer.transform([q])  # shape: (1, n_terms)

    sims = cosine_similarity(q_vec, X).ravel()  # shape: (n_docs,)

    sims = _normalize_scores(sims, min_val=cfg.NORMALIZE_MIN, max_val=cfg.NORMALIZE_MAX)

    return [(candidates[i], float(sims[i])) for i in range(len(candidates))]
