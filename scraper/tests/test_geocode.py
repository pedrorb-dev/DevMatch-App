import json

import pytest

from job_scraper import geocode as geocode_module


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Ningún test escribe cities_cache.json del repositorio ni duerme."""
    monkeypatch.setattr(geocode_module, "CACHE_PATH", tmp_path / "cities_cache.json")
    monkeypatch.setattr(geocode_module.time, "sleep", lambda _seconds: None)


def capture_get(payload):
    calls = []

    def fake_get(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return FakeResponse(payload)

    return calls, fake_get


def test_geocode_monterrey_devuelve_coordenadas(monkeypatch):
    calls, fake_get = capture_get([{"lat": "25.6866", "lon": "-100.3161"}])
    monkeypatch.setattr(geocode_module.requests, "get", fake_get)

    result = geocode_module.geocode("Monterrey, México", {})

    assert result == pytest.approx((25.6866, -100.3161))
    assert len(calls) == 1
    assert calls[0]["url"] == geocode_module.NOMINATIM_URL
    assert calls[0]["params"] == {"q": "Monterrey, México", "format": "jsonv2", "limit": 1}
    assert "DevMatch" in calls[0]["headers"]["User-Agent"]
    assert calls[0]["timeout"] == geocode_module.REQUEST_TIMEOUT


@pytest.mark.parametrize("text", ["", "   ", None])
def test_geocode_texto_vacio_no_hace_request(monkeypatch, text):
    def fail(*args, **kwargs):
        raise AssertionError("No se debe llamar a Nominatim sin texto")

    monkeypatch.setattr(geocode_module.requests, "get", fail)

    assert geocode_module.geocode(text, {}) is None


def test_geocode_sin_resultados_devuelve_none(monkeypatch):
    calls, fake_get = capture_get([])
    monkeypatch.setattr(geocode_module.requests, "get", fake_get)

    assert geocode_module.geocode("Lugar que no existe, México", {}) is None
    assert len(calls) == 1


def test_geocode_fallo_http_devuelve_none(monkeypatch):
    def fail_get(*args, **kwargs):
        raise geocode_module.requests.ConnectionError("Nominatim caído")

    monkeypatch.setattr(geocode_module.requests, "get", fail_get)

    assert geocode_module.geocode("Monterrey, México", {}) is None


def test_cache_evita_repetir_request_y_guarda_ciudad(monkeypatch):
    calls, fake_get = capture_get([{"lat": "25.6866", "lon": "-100.3161"}])
    monkeypatch.setattr(geocode_module.requests, "get", fake_get)
    cache = {}

    first = geocode_module.geocode("Monterrey, México", cache)
    second = geocode_module.geocode("MONTERREY, MEXICO", cache)

    assert first == second == pytest.approx((25.6866, -100.3161))
    assert len(calls) == 1
    assert cache == {"monterrey, mexico": {"lat": 25.6866, "lng": -100.3161}}
    assert json.loads(geocode_module.CACHE_PATH.read_text(encoding="utf-8")) == cache


def test_geocode_respeta_delay_solo_en_cache_miss(monkeypatch):
    sleeps = []
    _, fake_get = capture_get([{"lat": "25.6866", "lon": "-100.3161"}])
    monkeypatch.setattr(geocode_module.requests, "get", fake_get)
    monkeypatch.setattr(geocode_module.time, "sleep", sleeps.append)
    cache = {}

    geocode_module.geocode("Monterrey, México", cache)
    geocode_module.geocode("Monterrey, México", cache)

    assert sleeps == [geocode_module.DELAY_SECONDS]


def test_load_cache_sin_archivo_devuelve_vacio():
    assert geocode_module.load_cache() == {}


def test_save_y_load_cache(tmp_path):
    cache = {"monterrey, mexico": {"lat": 25.68, "lng": -100.31}}
    custom_path = tmp_path / "cities_cache.json"

    geocode_module.save_cache(cache, custom_path)

    assert json.loads(custom_path.read_text(encoding="utf-8")) == cache
    assert geocode_module.load_cache(custom_path) == cache


@pytest.mark.parametrize(
    "text",
    [
        "Remoto",
        "Remote",
        "Home Office, México",
        "Remoto (4 ubicaciones)",
        "Remoto (Sudamérica y Centroamérica)",
    ],
)
def test_geocode_modalidad_no_es_lugar_no_hace_request(monkeypatch, text):
    """Textos de modalidad no son coordenadas, aunque Nominatim los 'encuentre'."""

    def fail(*args, **kwargs):
        raise AssertionError("No se debe geocodificar una modalidad como lugar")

    monkeypatch.setattr(geocode_module.requests, "get", fail)

    assert geocode_module.geocode(text, {}) is None


def test_geocode_ciudad_con_home_office_si_geocodifica(monkeypatch):
    """Si además de la modalidad hay una ciudad real, se conserva la ciudad."""
    calls, fake_get = capture_get([{"lat": "19.4071", "lon": "-99.1906"}])
    monkeypatch.setattr(geocode_module.requests, "get", fake_get)

    result = geocode_module.geocode("Miguel Hidalgo, Home Office, México", {})

    assert result == pytest.approx((19.4071, -99.1906))
    assert len(calls) == 1
    assert calls[0]["params"]["q"] == "Miguel Hidalgo, México"
