# reco/index/vector_index.py
"""
VectorIndex — V4 / P1 Híbrido (BM25 + MPNet)

Responsável por:
- Armazenar vetores (embeddings) e metadados por item (ex.: trilhas, vagas).
- Buscar Top-K por similaridade (coseno) com filtros por metadados.
- Abstrair diferentes backends (NumPy puro, FAISS, etc).

Backends disponíveis:
- "numpy" (padrão): rápido o suficiente para catálogos pequenos/médios no piloto.
- "faiss" (opcional): requer 'faiss-cpu' ou 'faiss-gpu'.

Operações:
- upsert(items): insere/atualiza vetores e metadados
- delete(ids): remove itens
- search(query_vec, k, filters): retorna Top-K [(id, score, metadata)]
- size(): número de itens

Observações:
- Usa similaridade por cosseno. Embeddings devem vir normalizados L2 (ver EmbeddingProvider).
- Valida dim do vetor contra config.EMBED_DIM.
- Filtros suportam igualdade simples e listas (in).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Literal, Optional, Sequence, Tuple

import numpy as np

try:
    import faiss  # type: ignore
    _FAISS_AVAILABLE = True
except Exception:
    _FAISS_AVAILABLE = False


VectorIndexBackend = Literal["numpy", "faiss"]


@dataclass
class VectorItem:
    id: str
    vector: np.ndarray          # shape: (dim,), preferencialmente L2-normalizado (float32)
    metadata: Dict[str, Any]    # ex.: {"status": "Published", "nivel": "Beginner"}


class VectorIndex:
    """
    Abstração de índice vetorial com dois backends: NumPy (default) e FAISS (opcional).

    Uso típico:
        idx = VectorIndex.from_config(cfg, backend="numpy", index_name=cfg.INDEX_TRILHAS)
        idx.upsert(items)
        results = idx.search(query_vec, k=50, filters={"status": "Published"})

    Retorno de search:
        List[Tuple[str, float, Dict[str, Any]]]  # (id, score_coseno, metadata)
    """

    def __init__(
        self,
        dim: int,
        index_name: str,
        backend: VectorIndexBackend = "numpy",
        model_version: str = "unspecified",
        ann_random_seed: int = 42,
    ) -> None:
        self._dim = int(dim)
        self._name = index_name
        self._backend = backend
        self._version = model_version
        self._rng = np.random.default_rng(ann_random_seed)

        # Armazenamento de metadados sempre em dicionário
        self._meta: Dict[str, Dict[str, Any]] = {}

        if backend == "faiss":
            if not _FAISS_AVAILABLE:
                raise RuntimeError("Backend 'faiss' selecionado, mas o pacote 'faiss' não está instalado.")
            # Índice de produto escalar (para coseno com vetores L2-normalizados).
            self._faiss_index = faiss.IndexFlatIP(self._dim)
            self._faiss_ids: List[str] = []
            self._faiss_matrix: Optional[np.ndarray] = None  # espelho opcional (para reindexações)
        else:
            # Backend NumPy: mantemos matriz (N, dim) e lista de ids.
            self._faiss_index = None
            self._faiss_ids = []
            self._faiss_matrix = None
            self._np_matrix: Optional[np.ndarray] = None
            self._np_ids: List[str] = []

    # ---------- Fábrica ----------
    @classmethod
    def from_config(cls, cfg, backend: VectorIndexBackend = "numpy", index_name: Optional[str] = None) -> "VectorIndex":
        return cls(
            dim=getattr(cfg, "EMBED_DIM", 768),
            index_name=index_name or getattr(cfg, "INDEX_TRILHAS", "trilhas_mpnet_v1"),
            backend=backend,
            model_version=getattr(cfg, "MODEL_VERSION", "unspecified"),
            ann_random_seed=getattr(cfg, "ANN_RANDOM_SEED", 42),
        )

    # ---------- Operações principais ----------
    def upsert(self, items: Sequence[VectorItem]) -> int:
        """Insere/atualiza itens. Retorna total de itens no índice após operação."""
        if not items:
            return self.size()

        # Validação de dimensão e dtype
        for it in items:
            if it.vector.ndim != 1 or it.vector.shape[0] != self._dim:
                raise ValueError(f"Vetor com dimensão incorreta para id={it.id}: {it.vector.shape} (esperado {(self._dim,)})")
            if it.vector.dtype != np.float32:
                it.vector = it.vector.astype(np.float32, copy=False)

        if self._backend == "faiss":
            return self._upsert_faiss(items)
        return self._upsert_numpy(items)

    def delete(self, ids: Sequence[str]) -> int:
        """Remove itens pelos IDs. Retorna total de itens após a operação."""
        if not ids:
            return self.size()

        if self._backend == "faiss":
            return self._delete_faiss(ids)
        return self._delete_numpy(ids)

    def search(
        self,
        query_vec: np.ndarray,
        k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Busca Top-K por similaridade de coseno. Retorna lista de (id, score, metadata)."""
        if query_vec.ndim != 1 or query_vec.shape[0] != self._dim:
            raise ValueError(f"Dimensão do vetor de consulta inválida: {query_vec.shape} (esperado {(self._dim,)})")
        if query_vec.dtype != np.float32:
            query_vec = query_vec.astype(np.float32, copy=False)

        if self._backend == "faiss":
            return self._search_faiss(query_vec, k, filters)
        return self._search_numpy(query_vec, k, filters)

    def size(self) -> int:
        if self._backend == "faiss":
            return len(self._faiss_ids)
        return len(self._np_ids)

    # ---------- Backend: NumPy ----------
    def _upsert_numpy(self, items: Sequence[VectorItem]) -> int:
        id_to_pos = {id_: pos for pos, id_ in enumerate(self._np_ids)}
        vectors, ids = [], []

        # atualiza ou acumula novos
        for it in items:
            self._meta[it.id] = it.metadata or {}
            if it.id in id_to_pos:
                pos = id_to_pos[it.id]
                self._np_matrix[pos] = it.vector  # type: ignore
            else:
                vectors.append(it.vector)
                ids.append(it.id)

        if vectors:
            new_block = np.vstack(vectors).astype(np.float32)
            if self._np_matrix is None:
                self._np_matrix = new_block
                self._np_ids = list(ids)
            else:
                self._np_matrix = np.vstack([self._np_matrix, new_block])
                self._np_ids.extend(ids)

        return len(self._np_ids)

    def _delete_numpy(self, ids: Sequence[str]) -> int:
        if not ids or not self._np_ids:
            return len(self._np_ids)

        keep_mask = [i for i, id_ in enumerate(self._np_ids) if id_ not in ids]
        if not keep_mask:
            self._np_matrix = None
            self._np_ids = []
            # limpa metadados
            for rem in ids:
                self._meta.pop(rem, None)
            return 0

        self._np_matrix = self._np_matrix[keep_mask, :]  # type: ignore
        self._np_ids = [self._np_ids[i] for i in keep_mask]
        for rem in ids:
            self._meta.pop(rem, None)
        return len(self._np_ids)

    def _search_numpy(
        self, query_vec: np.ndarray, k: int, filters: Optional[Dict[str, Any]]
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        if self._np_matrix is None or not self._np_ids:
            return []

        # Similaridade por produto escalar (coseno, pois vetores são L2-normalizados).
        scores = (self._np_matrix @ query_vec).ravel()  # shape: (N,)
        k = int(min(k, scores.shape[0]))

        # Pré-filtragem por metadados (se houver)
        if filters:
            mask = np.array([self._match_filters(self._meta[id_], filters) for id_ in self._np_ids], dtype=bool)
            idxs = np.where(mask)[0]
            if idxs.size == 0:
                return []
            scores = scores[idxs]
            ids_subset = [self._np_ids[i] for i in idxs]
        else:
            ids_subset = self._np_ids

        # Top-K
        if scores.size == 0:
            return []
        topk_idx = np.argpartition(-scores, kth=min(k - 1, scores.size - 1))[:k]
        topk_sorted = topk_idx[np.argsort(-scores[topk_idx])]
        results: List[Tuple[str, float, Dict[str, Any]]] = []
        for idx in topk_sorted:
            id_ = ids_subset[idx]
            results.append((id_, float(scores[idx]), self._meta.get(id_, {})))
        return results

    # ---------- Backend: FAISS ----------
    def _upsert_faiss(self, items: Sequence[VectorItem]) -> int:
        # Estratégia simples: para manter IDs alinhados, reconstruímos quando há updates.
        # Para catálogos médios no piloto, isso é aceitável. Em produção, usar índices IDMap.
        id_set = set(self._faiss_ids)
        updated = any(it.id in id_set for it in items)

        if updated:
            # Reconstruir a partir dos metadados + novos vetores
            all_ids = []
            all_vecs = []
            # aplica updates no dicionário meta e guarda
            for it in items:
                self._meta[it.id] = it.metadata or {}
            # rebuild completo
            for id_, meta in self._meta.items():
                # procura vetor atualizado nos items, senão mantém o antigo (se existir)
                v = next((it.vector for it in items if it.id == id_), None)
                if v is None:
                    # buscamos vetor antigo do espelho
                    # (para simplificar, assumimos que _faiss_matrix está sempre coerente)
                    if self._faiss_matrix is None:
                        continue
                    pos = self._faiss_ids.index(id_)
                    v = self._faiss_matrix[pos]
                all_ids.append(id_)
                all_vecs.append(v)
            mat = np.vstack(all_vecs).astype(np.float32) if all_vecs else np.empty((0, self._dim), np.float32)
            self._faiss_index.reset()
            if mat.size:
                self._faiss_index.add(mat)
            self._faiss_matrix = mat
            self._faiss_ids = all_ids
            return len(self._faiss_ids)

        # apenas inserts novos
        new_ids = [it.id for it in items if it.id not in id_set]
        if new_ids:
            new_vecs = np.vstack([it.vector for it in items if it.id in new_ids]).astype(np.float32)
            self._faiss_index.add(new_vecs)
            self._faiss_ids.extend(new_ids)
            # espelho (para reconstruções futuras)
            self._faiss_matrix = new_vecs if self._faiss_matrix is None else np.vstack([self._faiss_matrix, new_vecs])
            for it in items:
                self._meta[it.id] = it.metadata or {}

        return len(self._faiss_ids)

    def _delete_faiss(self, ids: Sequence[str]) -> int:
        if not ids or not self._faiss_ids:
            return len(self._faiss_ids)

        keep = [(i, id_) for i, id_ in enumerate(self._faiss_ids) if id_ not in ids]
        if not keep:
            self._faiss_ids = []
            self._faiss_matrix = None
            self._faiss_index.reset()
            for rem in ids:
                self._meta.pop(rem, None)
            return 0

        keep_idx = [i for i, _ in keep]
        self._faiss_ids = [self._faiss_ids[i] for i in keep_idx]
        if self._faiss_matrix is not None:
            self._faiss_matrix = self._faiss_matrix[keep_idx, :]
        self._faiss_index.reset()
        if self._faiss_matrix is not None and self._faiss_matrix.size:
            self._faiss_index.add(self._faiss_matrix)
        for rem in ids:
            self._meta.pop(rem, None)
        return len(self._faiss_ids)

    def _search_faiss(
        self, query_vec: np.ndarray, k: int, filters: Optional[Dict[str, Any]]
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        if not self._faiss_ids:
            return []

        # Pré-filtragem por metadados (se houver)
        if filters:
            mask_ids = [id_ for id_ in self._faiss_ids if self._match_filters(self._meta.get(id_, {}), filters)]
            if not mask_ids:
                return []
            # Para simplificar, buscamos no índice completo e filtramos no pós-processamento.
            D, I = self._faiss_index.search(query_vec[None, :], min(k * 4, len(self._faiss_ids)))
            # pós-filtro mantendo a ordem por score
            candidates = []
            for score, idx in zip(D[0], I[0]):
                if idx < 0:
                    continue
                id_ = self._faiss_ids[idx]
                if id_ in mask_ids:
                    candidates.append((id_, float(score), self._meta.get(id_, {})))
                if len(candidates) >= k:
                    break
            return candidates

        # Busca direta
        D, I = self._faiss_index.search(query_vec[None, :], min(k, len(self._faiss_ids)))
        results: List[Tuple[str, float, Dict[str, Any]]] = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0:
                continue
            id_ = self._faiss_ids[idx]
            results.append((id_, float(score), self._meta.get(id_, {})))
        return results

    # ---------- Utilidades ----------
    @staticmethod
    def _match_filters(meta: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Suporta igualdade e listas (operador 'in')."""
        for key, expected in filters.items():
            val = meta.get(key)
            if isinstance(expected, (list, tuple, set)):
                if val not in expected:
                    return False
            else:
                if val != expected:
                    return False
        return True
