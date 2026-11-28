"""Catálogo canónico de tecnologías compartido por el scraper y la app.

Las listas derivadas (aliases, patrones y slugs) se calculan desde
``src/core/config/stacks.json``, que es la única fuente de verdad.
"""

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "src" / "core" / "config" / "stacks.json"
)

PORTALS = ("occ", "computrabajo", "getonbrd")


def _normalize_key(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if unicodedata.combining(char) == 0)
    return re.sub(r"\s+", " ", text).lower().strip()


def _compact_key(value):
    return value.replace(".", "").replace("#", "")


@lru_cache(maxsize=1)
def load_catalog():
    """Carga el JSON canónico (una sola vez por proceso)."""
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


STACK_KEYWORDS = {}
for _stack in load_catalog():
    for _alias in (*_stack.get("aliases", []), _normalize_key(_stack["name"])):
        _key = _normalize_key(_alias)
        if _key:
            STACK_KEYWORDS.setdefault(_key, _stack["name"])

_STACK_KEYWORDS_BY_COMPACT = {}
for _alias, _canonical in STACK_KEYWORDS.items():
    _STACK_KEYWORDS_BY_COMPACT.setdefault(_compact_key(_alias), _canonical)

# Aliases compuestos: permiten resolver tags como "spring boot 3" sin
# hardcodear nombres concretos en la lógica de canonicalización.
_MULTIWORD_ALIASES = sorted(
    (
        (_normalize_key(alias), canonical)
        for alias, canonical in STACK_KEYWORDS.items()
        if re.search(r"[ ._-]", alias) and len(_normalize_key(alias)) > 3
    ),
    key=lambda item: len(item[0]),
    reverse=True,
)

# El orden por longitud garantiza que "react native" se evalúe antes que
# "react" y que "ruby on rails" se evalúe antes que "ruby".
STACK_PATTERNS = sorted(
    (
        (pattern, stack["name"])
        for stack in load_catalog()
        for pattern in stack.get("patterns", [])
    ),
    key=lambda item: len(item[0]),
    reverse=True,
)

STACK_SLUGS = {
    portal: {
        _normalize_key(stack["name"]): (stack.get("slugs") or {}).get(portal)
        for stack in load_catalog()
        if (stack.get("slugs") or {}).get(portal)
    }
    for portal in PORTALS
}


def canonical_tech(token):
    """Nombre canónico de una tecnología, resolviendo alias del catálogo."""
    text = str(token or "").strip()
    if not text:
        return ""

    norm = _normalize_key(text)
    if norm in STACK_KEYWORDS:
        return STACK_KEYWORDS[norm]

    compact = _compact_key(norm)
    if compact in _STACK_KEYWORDS_BY_COMPACT:
        return _STACK_KEYWORDS_BY_COMPACT[compact]

    for alias, canonical in _MULTIWORD_ALIASES:
        if alias in norm:
            return canonical

    # Lo desconocido se conserva tal cual, igual que en el pipeline.
    return text


def stack_slug(tech, portal):
    """Slug del portal para un nombre/alias canónico, o None si no existe."""
    canonical = canonical_tech(tech)
    return STACK_SLUGS.get(portal, {}).get(_normalize_key(canonical))
