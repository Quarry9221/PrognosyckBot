import pytest
import httpx
import sys
import types
import asyncio
from services.geocode import geocode_place

# Patch imports for testing
sys.modules["config"] = types.SimpleNamespace(GEOAPIFY_KEY="test_key")
sys.modules["bot.logger_config"] = types.SimpleNamespace(
    logger=types.SimpleNamespace(
        info=lambda *a, **kw: None,
        warning=lambda *a, **kw: None,
        error=lambda *a, **kw: None,
    )
)


class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self._status_code = status_code
        self._json_data = json_data or {}

    def raise_for_status(self):
        if self._status_code != 200:
            raise httpx.HTTPStatusError("error", request=None, response=self)

    def json(self):
        return self._json_data

    @property
    def status_code(self):
        return self._status_code


class MockAsyncClient:
    def __init__(self, response=None, raise_timeout=False, raise_request_error=False):
        self.response = response
        self.raise_timeout = raise_timeout
        self.raise_request_error = raise_request_error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url):
        if self.raise_timeout:
            raise httpx.TimeoutException("timeout")
        if self.raise_request_error:
            raise httpx.RequestError("network error")
        return self.response


@pytest.mark.asyncio
async def test_geocode_place_success(monkeypatch):
    mock_result = {
        "results": [
            {
                "lat": 50.45,
                "lon": 30.523,
                "city": "Kyiv",
                "state": "Kyiv City",
                "country": "Ukraine",
                "formatted": "Kyiv, Ukraine",
            }
        ]
    }
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda timeout: MockAsyncClient(response=MockResponse(json_data=mock_result)),
    )
    result = await geocode_place("Kyiv")
    assert result["lat"] == 50.45
    assert result["lon"] == 30.523
    assert result["city"] == "Kyiv"
    assert result["country"] == "Ukraine"


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_input", ["", None, " ", "a", 123])
async def test_geocode_place_invalid_input(bad_input):
    with pytest.raises(ValueError, match="Введіть коректну назву місця"):
        await geocode_place(bad_input)


@pytest.mark.asyncio
async def test_geocode_place_no_results(monkeypatch):
    mock_result = {"results": []}
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda timeout: MockAsyncClient(response=MockResponse(json_data=mock_result)),
    )
    with pytest.raises(ValueError, match="Я не знайшов таке місце"):
        await geocode_place("UnknownPlace")


@pytest.mark.asyncio
async def test_geocode_place_missing_coords(monkeypatch):
    mock_result = {"results": [{"lat": None, "lon": None}]}
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda timeout: MockAsyncClient(response=MockResponse(json_data=mock_result)),
    )
    with pytest.raises(ValueError, match="Не вдалося отримати координати місця"):
        await geocode_place("NoCoordsPlace")


@pytest.mark.asyncio
async def test_geocode_place_timeout(monkeypatch):
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda timeout: MockAsyncClient(raise_timeout=True)
    )
    with pytest.raises(ValueError, match="Сервіс геокодування не відповідає"):
        await geocode_place("Kyiv")


@pytest.mark.asyncio
async def test_geocode_place_http_error(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda timeout: MockAsyncClient(response=MockResponse(status_code=404)),
    )
    with pytest.raises(ValueError, match="Помилка геокодування"):
        await geocode_place("Kyiv")


@pytest.mark.asyncio
async def test_geocode_place_network_error(monkeypatch):
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda timeout: MockAsyncClient(raise_request_error=True)
    )
    with pytest.raises(ValueError, match="Проблема з мережею"):
        await geocode_place("Kyiv")


@pytest.mark.asyncio
async def test_geocode_place_unexpected_error(monkeypatch):
    class BrokenClient(MockAsyncClient):
        async def get(self, url):
            raise Exception("unexpected")

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: BrokenClient())
    with pytest.raises(ValueError, match="Технічна помилка геокодування"):
        await geocode_place("Kyiv")
