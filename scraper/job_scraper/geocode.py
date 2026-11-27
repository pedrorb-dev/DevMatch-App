"""Geocodificación de ubicaciones de vacantes con Nominatim (SPEC 10).

La caché por ciudad evita repetir llamadas HTTP para la misma ubicación y se
persiste en ``scraper/cities_cache.json``. Ante cualquier fallo, ``geocode``
devuelve ``None`` para que la vacante quede sin coordenadas (orden neutral).
"""

import json
import logging
import re
import time
import unicodedata
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "DevMatch-App-Scraper/1.0 (geocodificacion de vacantes del proyecto DevMatch)"
DELAY_SECONDS = 1.0
REQUEST_TIMEOUT = 10
CACHE_PATH = Path(__file__).resolve().parent.parent / "cities_cache.json"


def normalize_city(text):
    """Clave de caché: minúsculas, sin acentos y espacios colapsados."""
    decomposed = unicodedata.normalize("NFD", str(text or ""))
    without_accents = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", without_accents).strip().lower()


# Palabras que describen la modalidad, no un lugar geográfico. Si la ubicación
# solo contiene estas (o country/continente sueltos), no hay coordenadas que
# calcular: Nominatim las resolvería a lugares inventados (SPEC 10).
NON_GEO_PARTS = {
    "remoto",
    "remote",
    "home office",
    "homeoffice",
    "telecommute",
    "desde casa",
    "teletrabajo",
    "en casa",
    "work from home",
    "wfh",
    "anywhere",
    "worldwide",
    "global",
}
GENERIC_PARTS = {
    "mexico",
    "mx",
    "sudamerica",
    "centroamerica",
    "america latina",
    "latam",
    "mundo",
    "todos",
    "todo",
}
_PARENTHETICAL = re.compile(r"\([^)]*\)")


def _location_query(text):
    """Devuelve la parte geográfica de ``text``, o None si solo hay modalidad.

    Conserva la capitalización original para Nominatim; la clave de caché se
    normaliza aparte. Así ``"Remoto (4 ubicaciones)"`` -> None, mientras que
    ``"Miguel Hidalgo, Home Office, México"`` -> ``"Miguel Hidalgo, México"``.
    """
    clean = _PARENTHETICAL.sub(" ", str(text or ""))
    kept = [
        part.strip()
        for part in clean.split(",")
        if part.strip() and normalize_city(part) not in NON_GEO_PARTS
    ]
    if not any(normalize_city(part) not in GENERIC_PARTS for part in kept):
        return None
    return ", ".join(kept)


def load_cache(path=None):
    """Carga la caché de ciudades; devuelve {} si no existe o es inválida."""
    target = Path(path) if path is not None else CACHE_PATH
    try:
        with target.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_cache(cache, path=None):
    """Guarda la caché de ciudades como JSON legible."""
    target = Path(path) if path is not None else CACHE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(cache, handle, ensure_ascii=False, indent=2, sort_keys=True)


def geocode(text: str, cache: dict) -> tuple[float, float] | None:
    """Devuelve ``(lat, lng)`` para la parte geográfica de ``text``.

    Los textos de modalidad ("Remoto", "Remote", "Home Office") no son lugares
    y devuelven None sin llamar a Nominatim. El resto usa ``cache`` por ciudad,
    una sola request (limit=1) en cache miss y un delay de 1s.
    """
    query = _location_query(text)
    if not query:
        return None

    key = normalize_city(query)
    cached = cache.get(key)
    if isinstance(cached, dict):
        try:
            return (float(cached["lat"]), float(cached["lng"]))
        except (KeyError, TypeError, ValueError):
            pass

    time.sleep(DELAY_SECONDS)
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "jsonv2", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        results = response.json()
        if not results:
            return None
        lat = float(results[0]["lat"])
        lng = float(results[0]["lon"])
    except (requests.RequestException, ValueError, TypeError, KeyError, IndexError, AttributeError):
        return None

    cache[key] = {"lat": lat, "lng": lng}
    try:
        save_cache(cache)
    except OSError as exc:
        logger.warning("No se pudo guardar la caché de ciudades: %s", exc)
    return (lat, lng)
