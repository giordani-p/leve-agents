# reco/data_loader_api.py
"""
Cliente HTTP para leitura do catálogo de trilhas a partir do backend da Leve.

Responsabilidades:
- Buscar trilhas publicadas via /api/trails (com suporte a ?status=Published).
- (Opcional) Buscar detalhe de uma trilha via /api/trails/{publicId}.
- Implementar timeouts granulares, retry com backoff e tratamento de erros.
- Retornar dados *brutos* (list[dict] / dict), deixando a normalização para TrailCandidate.from_source().

Dependências:
- httpx (cliente HTTP moderno com timeouts granulares e HTTP/2).
- Este módulo NÃO normaliza; apenas coleta os dados da API.

Observações:
- Defesa em profundidade: mesmo pedindo Published no cliente, mantenha o filtro final
  por status na etapa de seleção/ranker (ver RecoConfig.ALLOWED_STATUS).
- Se /api/trails passar a paginar, há suporte básico a iteração até um limite (API_MAX_PAGES).
"""

from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import UUID

import httpx

from .config import RecoConfig


# -----------------------------
# Helpers internos
# -----------------------------

def _build_timeout(cfg: RecoConfig) -> httpx.Timeout:
    """Monta timeouts granulares a partir do RecoConfig."""
    return httpx.Timeout(
        connect=cfg.HTTP_TIMEOUT_CONNECT,
        read=cfg.HTTP_TIMEOUT_READ,
        write=cfg.HTTP_TIMEOUT_WRITE,
        pool=cfg.HTTP_TIMEOUT_POOL,
    )


def _should_retry(status_code: Optional[int], exc: Optional[BaseException]) -> bool:
    """
    Define se vale a pena tentar novamente a requisição.
    - Retries em falhas transitórias de rede (ConnectError, ReadError, etc.)
    - Retries em HTTP 429, 408 e 5xx.
    - 4xx (exceto 408/429) normalmente não devem ser re-tentados.
    """
    if exc is not None:
        # Erros de rede/transientes típicos do httpx
        return isinstance(
            exc,
            (
                httpx.ConnectError,
                httpx.ReadError,
                httpx.NetworkError,
                httpx.RemoteProtocolError,
                httpx.PoolTimeout,
                httpx.WriteError,
            ),
        )

    if status_code is None:
        return False

    if status_code in (408, 429):
        return True
    if 500 <= status_code <= 599:
        return True

    return False


def _sleep_backoff(attempt_idx: int, base: float) -> None:
    """
    Espera com backoff exponencial simples.
    attempt_idx: 0, 1, 2, ...
    tempo = base * (2 ** attempt_idx)
    """
    delay = base * (2 ** attempt_idx)
    time.sleep(delay)


def _join_url(base: str, path: str) -> str:
    base = base.rstrip("/")
    path = path.lstrip("/")
    return f"{base}/{path}"


# -----------------------------
# Cliente HTTP (context manager)
# -----------------------------

class TrailsApiClient:
    """
    Encapsula o httpx.Client com configurações de timeout. Reutiliza conexões (pool).
    """

    def __init__(self, cfg: RecoConfig) -> None:
        self._cfg = cfg
        self._client = httpx.Client(
            base_url=cfg.TRAILS_API_BASE,
            timeout=_build_timeout(cfg),
            http2=True,  # opcional; httpx negocia HTTP/2 se disponível
        )

    def close(self) -> None:
        self._client.close()

    def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Faz uma requisição com tentativas adicionais em caso de erro transitório.
        """
        attempts = 1 + max(0, self._cfg.HTTP_RETRIES)
        last_exc: Optional[BaseException] = None
        last_status: Optional[int] = None

        for i in range(attempts):
            try:
                resp = self._client.request(method, url, params=params)
                last_status = resp.status_code

                if _should_retry(last_status, None) and i < attempts - 1:
                    _sleep_backoff(i, self._cfg.HTTP_BACKOFF_BASE)
                    continue

                # Erros 4xx/5xx não-retentáveis explodem aqui:
                resp.raise_for_status()
                return resp

            except httpx.HTTPStatusError as e:
                last_exc = e
                last_status = e.response.status_code
                if _should_retry(last_status, None) and i < attempts - 1:
                    _sleep_backoff(i, self._cfg.HTTP_BACKOFF_BASE)
                    continue
                raise

            except (httpx.ConnectError, httpx.ReadError, httpx.NetworkError,
                    httpx.RemoteProtocolError, httpx.PoolTimeout, httpx.WriteError) as e:
                last_exc = e
                if _should_retry(None, e) and i < attempts - 1:
                    _sleep_backoff(i, self._cfg.HTTP_BACKOFF_BASE)
                    continue
                raise

        # Se chegou aqui, algo deu errado sem raise anterior; relança a última exceção conhecida
        if last_exc:
            raise last_exc
        raise RuntimeError("Falha desconhecida ao executar requisição HTTP.")

    # -----------------------------
    # Endpoints
    # -----------------------------

    def fetch_trails(self) -> List[Dict[str, Any]]:
        """
        Busca lista de trilhas em /api/trails.
        - Se API_FILTER_PUBLISHED=True, envia ?status=Published.
        - Suporte básico a paginação caso a API passe a devolver { items, nextPageToken }.
        - Retorna SEM normalizar (lista de dicts).
        """
        path = "/api/trails"
        params: Dict[str, Any] = {}
        if self._cfg.API_FILTER_PUBLISHED:
            params["status"] = "Published"

        # Primeira página
        resp = self._request_with_retry("GET", path, params=params)
        data = resp.json()

        # Caso tradicional: API retorna uma lista direta
        if isinstance(data, list):
            return _ensure_list_of_dicts(data)

        # Suporte básico a paginação futura: { "items": [...], "nextPageToken": "..." }
        if isinstance(data, dict) and "items" in data:
            items: List[Dict[str, Any]] = _ensure_list_of_dicts(data.get("items", []))
            next_token = data.get("nextPageToken")
            pages = 1

            # Itera enquanto houver token e não ultrapassar o limite configurado
            while next_token and pages < self._cfg.API_MAX_PAGES:
                params_with_token = dict(params)
                params_with_token["pageToken"] = next_token
                resp = self._request_with_retry("GET", path, params=params_with_token)
                page_data = resp.json()
                page_items = []
                if isinstance(page_data, list):
                    page_items = _ensure_list_of_dicts(page_data)
                    next_token = None
                elif isinstance(page_data, dict):
                    page_items = _ensure_list_of_dicts(page_data.get("items", []))
                    next_token = page_data.get("nextPageToken")
                else:
                    # Resposta inesperada: interrompe paginação
                    next_token = None

                items.extend(page_items)
                pages += 1

            return items

        # Formato inesperado
        raise ValueError("Resposta inesperada de /api/trails: esperado list ou dict com chave 'items'.")

    def fetch_trail_detail(self, public_id: UUID | str) -> Optional[Dict[str, Any]]:
        """
        Busca o detalhe de uma trilha via /api/trails/{publicId}.
        Retorna dict ou None se 404.
        """
        pid = str(public_id)
        path = f"/api/trails/{pid}"

        try:
            resp = self._request_with_retry("GET", path)
        except httpx.HTTPStatusError as e:
            # 404 → None, demais erros propagam
            if e.response.status_code == 404:
                return None
            raise

        data = resp.json()
        if not isinstance(data, dict):
            raise ValueError("Resposta inesperada de /api/trails/{publicId}: esperado objeto JSON (dict).")
        return data


# -----------------------------
# API de alto nível (funções)
# -----------------------------

def fetch_trails(cfg: RecoConfig) -> List[Dict[str, Any]]:
    """
    Função de conveniência para uso fora da classe.
    Exemplo:
        from reco.data_loader_api import fetch_trails
        raw_trails = fetch_trails(config)
    """
    client = TrailsApiClient(cfg)
    try:
        return client.fetch_trails()
    finally:
        client.close()


def fetch_trail_detail(cfg: RecoConfig, public_id: UUID | str) -> Optional[Dict[str, Any]]:
    client = TrailsApiClient(cfg)
    try:
        return client.fetch_trail_detail(public_id)
    finally:
        client.close()


# -----------------------------
# Utilidades
# -----------------------------

def _ensure_list_of_dicts(data: Iterable[Any]) -> List[Dict[str, Any]]:
    """
    Valida que 'data' é uma sequência de objetos JSON (dicts).
    Retorna uma nova lista de dicts.
    """
    out: List[Dict[str, Any]] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Entrada inválida na lista de trilhas (índice {i}): esperado objeto JSON (dict).")
        out.append(item)
    return out
