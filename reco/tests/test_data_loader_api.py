import pytest
import respx
import httpx

from reco.config import RecoConfig
from reco.data_loader_api import fetch_trails, fetch_trail_detail

API_BASE = "http://api.local"


@respx.mock
def test_fetch_trails_happy_path_list():
    cfg = RecoConfig(TRAILS_API_BASE=API_BASE, API_FILTER_PUBLISHED=True, API_PAGE_SIZE_HINT=50)
    route = respx.get(f"{API_BASE}/api/trails").mock(
        return_value=httpx.Response(
            200,
            json=[{"publicId": "1", "status": "Published"}, {"publicId": "2", "status": "Published"}],
            headers={"Content-Type": "application/json"},
        )
    )
    data = fetch_trails(cfg)
    assert route.called
    assert [d["publicId"] for d in data] == ["1", "2"]


@respx.mock
def test_fetch_trails_pagination_items_next_token():
    cfg = RecoConfig(TRAILS_API_BASE=API_BASE, HTTP_RETRIES=0)

    # 1ª página: items + nextPageToken
    respx.get(f"{API_BASE}/api/trails").mock(
        return_value=httpx.Response(
            200,
            json={"items": [{"publicId": "a"}], "nextPageToken": "t2"},
            headers={"Content-Type": "application/json"},
        )
    )
    # 2ª página: items finais, sem token
    respx.get(f"{API_BASE}/api/trails").mock(
        return_value=httpx.Response(
            200,
            json={"items": [{"publicId": "b"}]},
            headers={"Content-Type": "application/json"},
        )
    )

    data = fetch_trails(cfg)
    assert [d["publicId"] for d in data] == ["a", "b"]


@respx.mock
def test_fetch_trails_retry_after_429_then_success():
    cfg = RecoConfig(TRAILS_API_BASE=API_BASE, HTTP_RETRIES=2, HTTP_BACKOFF_BASE=0.0)

    # Primeira tentativa → 429 com Retry-After
    respx.get(f"{API_BASE}/api/trails").mock(
        return_value=httpx.Response(
            429, json={"items": [], "nextPageToken": "t1"}, headers={"Retry-After": "0.01", "Content-Type": "application/json"}
        )
    )
    # Retry → sucesso com lista direta
    respx.get(f"{API_BASE}/api/trails").mock(
        return_value=httpx.Response(200, json=[{"publicId": "x"}], headers={"Content-Type": "application/json"})
    )

    data = fetch_trails(cfg)
    assert [d["publicId"]] == ["x"]


@respx.mock
def test_fetch_trails_retry_5xx_then_success():
    cfg = RecoConfig(TRAILS_API_BASE=API_BASE, HTTP_RETRIES=1, HTTP_BACKOFF_BASE=0.0)

    # 1ª tentativa → 503
    respx.get(f"{API_BASE}/api/trails").mock(return_value=httpx.Response(503, json={"error": "unavailable"}, headers={"Content-Type": "application/json"}))
    # Retry → sucesso
    respx.get(f"{API_BASE}/api/trails").mock(
        return_value=httpx.Response(200, json=[{"publicId": "ok"}], headers={"Content-Type": "application/json"})
    )

    data = fetch_trails(cfg)
    assert [d["publicId"]] == ["ok"]


@respx.mock
def test_fetch_trails_non_json_raises_value_error():
    cfg = RecoConfig(TRAILS_API_BASE=API_BASE)
    respx.get(f"{API_BASE}/api/trails").mock(
        return_value=httpx.Response(200, text="<html>oops</html>", headers={"Content-Type": "text/html"})
    )
    with pytest.raises(ValueError):
        fetch_trails(cfg)


@respx.mock
def test_fetch_trail_detail_404_returns_none():
    cfg = RecoConfig(TRAILS_API_BASE=API_BASE)
    respx.get(f"{API_BASE}/api/trails/abc").mock(return_value=httpx.Response(404, json={"message": "not found"}, headers={"Content-Type": "application/json"}))
    assert fetch_trail_detail(cfg, "abc") is None


@respx.mock
def test_fetch_trail_detail_success_dict():
    cfg = RecoConfig(TRAILS_API_BASE=API_BASE)
    respx.get(f"{API_BASE}/api/trails/abc").mock(
        return_value=httpx.Response(200, json={"publicId": "abc", "status": "Published"}, headers={"Content-Type": "application/json"})
    )
    detail = fetch_trail_detail(cfg, "abc")
    assert isinstance(detail, dict) and detail["publicId"] == "abc"
