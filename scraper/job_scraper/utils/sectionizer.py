"""Split de descripciones en requisitos, beneficios y descripción.

Extraído de ``job_scraper.pipelines`` y ampliado (SPEC 08) con:
- diccionario de encabezados bilingüe (español + inglés),
- heurística de viñetas sin encabezado clasificadas por señales de contenido,
- reglas de pie de fuente (``GETONBRD Job ID`` y equivalentes) y atribución.

Las comparaciones se hacen con texto normalizado (minúsculas, sin acentos);
los items devueltos conservan su capitalización original.
"""

import re
import unicodedata


# Diccionario de encabezados (normalizado: minúsculas, sin acentos).
REQUIREMENT_HEADINGS = (
    "requisitos", "requerimientos", "requerido", "requisitos minimos",
    "requisitos excluyentes", "perfil", "perfil buscado", "lo que buscamos",
    "que buscamos", "que necesitas", "que necesitamos", "conocimientos",
    "conocimientos de", "conocimientos deseables", "conocimientos obligatorios",
    "experiencia requerida", "competencias", "habilidades", "habilidades tecnicas",
    "indispensable", "deseable", "requirements", "minimum requirements",
    "required skills", "what we're looking for", "what we are looking for",
    "qualifications", "must have", "must-have", "nice to have", "nice-to-have",
    "skills", "desired skills", "preferred skills", "preferred qualifications",
    "experience required",
)

BENEFIT_HEADINGS = (
    "ofrecemos", "que ofrecemos", "lo que ofrecemos", "que te ofrecemos",
    "te ofrecemos", "nosotros ofrecemos", "beneficios", "beneficios y prestaciones",
    "prestaciones", "condiciones", "salario", "sueldo", "compensacion",
    "compensation", "compensation and benefits", "que obtienes", "que recibes",
    "ventajas", "incentivos", "why join", "why join us", "benefits", "perks",
    "what we offer", "we offer", "salary", "what you'll get", "what you get",
)

DESCRIPTION_HEADINGS = (
    "actividades", "responsabilidades", "funciones", "descripcion general",
    "que haras", "sobre el puesto", "acerca del puesto", "sobre nosotros",
    "acerca de nosotros", "sobre la empresa", "core responsibilities",
    "how you work", "responsibilities", "what you'll do", "what you will do",
    "about the role", "about us", "the role",
    # Caso real de Hireline: funciones bajo un sub-encabezado dentro de
    # "Requerido"; se mapea a descripcion para no mezclarlas con requisitos.
    "experiencia en sistemas financieros",
)

# Señales de contenido para viñetas sin encabezado reconocible.
REQUIREMENT_SIGNALS = (
    r"\d+\s*(?:anos|anios|años|years?)",
    r"\bexperiencia\b",
    r"\bconocimientos?\b",
    r"\bingles\b|\benglish\b",
    r"\btitulo universitario\b",
    r"\blicenciatura\b",
    r"\bingenieria\b",
    r"\bdegree\b",
    r"\bnivel\b",
    r"\bdominio de\b",
    r"\bmanejo de\b",
    r"\beducacion minima\b",
)

BENEFIT_SIGNALS = (
    r"\bseguro\b", r"\bremoto\b", r"\bremote\b", r"\bhome office\b",
    r"\bhorario flexible\b", r"\bbono\b", r"\bprestaciones\b", r"\bsalario\b",
    r"\bsueldo\b", r"\bvacaciones\b", r"\bcapacitacion\b", r"\bcrecimiento\b",
    r"\bestabilidad\b", r"\bcontrato\b", r"\bpago en\b", r"\busd\b", r"\bmxn\b",
    r"\bsnacks\b", r"\bequipo de trabajo\b", r"\bequity\b", r"\bvestimenta\b",
    r"\benfermedad\b",
)

ATTRIBUTION_PATTERN = re.compile(
    r"(?i)este\s+empleo\s+es\s+original\s+de\s+get\s+on\s+board\.?"
    r"|oferta\s+exclusiva\s+de\s+(?:www\.)?getonbrd\.com\.?",
)

FOOTER_MARKER_PATTERN = re.compile(
    r"\b(?:getonbrd|occ|computrabajo|hireline)?\s*job\s*id\b"
)

_BULLET_SPLIT_RE = re.compile(r"\n+|(?<=[\s.])(?:[•]|[-–—*·])\s+")
_LEADING_BULLET_RE = re.compile(r"^[\-–—*·•]+\s*")
_CONTENT_START_RE = re.compile(r"(?:[A-ZÁÉÍÓÚÜÑ0-9(]|[-–—*·•](?:\s|$))")
_MID_SENTENCE_CONNECTOR_RE = re.compile(
    r"\b(?:and|or|of|with|for|to|in|on|the|a|an|y|o|de|con|para|en|el|la|los|las)\s*$"
)

_ALL_HEADINGS = tuple(
    sorted(
        set(REQUIREMENT_HEADINGS + BENEFIT_HEADINGS + DESCRIPTION_HEADINGS),
        key=len,
        reverse=True,
    )
)
_HEADING_RE = re.compile(
    r"(?<![\w-])(?:" + "|".join(re.escape(key) for key in _ALL_HEADINGS) + r")(?!\w)"
)
# Las descripciones almacenadas pueden tener el encabezado pegado al texto
# ("Sobre nosotrosALPRO", "OfrecemosSueldo") porque DataCleaningPipeline
# colapsa los saltos de línea. Esta segunda pasada solo acepta esos casos
# cuando la siguiente letra en el texto original es mayúscula.
_HEADING_CONCAT_RE = re.compile(
    r"(?<![\w-])(?:" + "|".join(re.escape(key) for key in _ALL_HEADINGS) + r")"
)


def _strip_accents(text):
    normalized = unicodedata.normalize("NFD", text or "")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _normalize_text(text):
    return re.sub(r"\s+", " ", _strip_accents(str(text or "")).lower()).strip()


def _normalize_with_map(text):
    """Normaliza conservando un mapa de índices hacia el texto original."""
    symbols, offsets = [], []
    for index, char in enumerate(text):
        decomposed = unicodedata.normalize("NFD", char)
        base = "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower()
        if not base:
            base = char.lower()
        for symbol in base:
            symbols.append(symbol)
            offsets.append(index)
    return "".join(symbols), offsets


def classify_heading(text):
    """Clasifica un encabezado en ``requirements``, ``benefits`` o ``description``."""
    heading = re.sub(r"[:\-–—]+$", "", _normalize_text(text)).strip()
    for key in sorted(BENEFIT_HEADINGS, key=len, reverse=True):
        if key in heading:
            return "benefits"
    for key in sorted(REQUIREMENT_HEADINGS, key=len, reverse=True):
        if key in heading:
            return "requirements"
    for key in sorted(DESCRIPTION_HEADINGS, key=len, reverse=True):
        if key in heading:
            return "description"
    return "description"


def _clean_item(value):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return _LEADING_BULLET_RE.sub("", text).strip()


def _dedupe(items):
    result, seen = [], set()
    for item in items:
        key = _normalize_text(item)
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _split_bullets(text):
    parts = _BULLET_SPLIT_RE.split(str(text or "").strip())
    return [item for item in (_clean_item(part) for part in parts) if item]


def _has_signal(item, patterns):
    normalized = _normalize_text(item)
    return any(re.search(pattern, normalized) for pattern in patterns)


def _split_unheaded(text):
    """Sin encabezados: clasifica viñetas por señales; prosa corrida no se divide."""
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    parts = _split_bullets(text)
    if len(parts) <= 1:
        return {"descripcion": clean, "requirements": [], "benefits": []}

    buckets = {"description": [], "requirements": [], "benefits": []}
    for item in parts:
        if _has_signal(item, REQUIREMENT_SIGNALS):
            buckets["requirements"].append(item)
        elif _has_signal(item, BENEFIT_SIGNALS):
            buckets["benefits"].append(item)
        else:
            buckets["description"].append(item)

    return {
        "descripcion": "\n\n".join(buckets["description"]).strip(),
        "requirements": _dedupe(buckets["requirements"]),
        "benefits": _dedupe(buckets["benefits"]),
    }


def _is_heading_context(text, start, end):
    """Evita clasificar palabras del diccionario en medio de prosa."""
    prefix = text[:start]
    line_prefix = prefix.split("\n")[-1]
    after = text[end:]
    blank_line = not line_prefix.strip()
    bullet_only = not blank_line and re.fullmatch(
        r"\s*(?:[-–—*·•]\s*)?", line_prefix
    ) is not None

    if blank_line:
        return True
    # "- CONOCIMIENTOS de SQL" es una viñeta, no un encabezado.
    if bullet_only:
        return after.startswith(":")
    # "Requerido:" y "Compensation:" son encabezados incluso dentro de una línea.
    if after.startswith(":"):
        return True
    if after.startswith("\n"):
        return False

    content_start = after.lstrip()
    if not _CONTENT_START_RE.match(content_start):
        return False
    if re.search(r"[.!?]\s*$", prefix):
        return True
    # "and requirements alongside ..." es prosa, no un encabezado.
    return _MID_SENTENCE_CONNECTOR_RE.search(_normalize_text(prefix)) is None


def _find_headings(text):
    normalized, offsets = _normalize_with_map(text)
    candidates = {}
    for pattern in (_HEADING_RE, _HEADING_CONCAT_RE):
        for match in pattern.finditer(normalized):
            start = offsets[match.start()]
            end = offsets[match.end() - 1] + 1
            # Un encabezado pegado solo vale si sigue una mayúscula; así se
            # evita confundir prosa como "requirements alongside" con un título.
            if pattern is _HEADING_CONCAT_RE and not (
                end < len(text) and text[end].isupper()
            ):
                continue
            if _is_heading_context(text, start, end):
                candidates[(start, end)] = True

    # Si dos keywords se solapan (p. ej. "minimum requirements"), gana la más larga.
    accepted = []
    for start, end in sorted(candidates, key=lambda pos: (pos[0], -pos[1])):
        if any(previous_start < end and start < previous_end for previous_start, previous_end, _ in accepted):
            continue
        accepted.append((start, end, classify_heading(text[start:end])))
    return accepted


def _footer_items(footer):
    """El bloque posterior al pie de fuente siempre son beneficios."""
    items = []
    for line in re.split(r"\n+", str(footer or "")):
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            cleaned = _clean_item(sentence)
            if cleaned:
                items.append(cleaned)
    return items


def split_sections(text):
    """Divide una descripción en ``descripcion``, ``requirements`` y ``benefits``."""
    raw = str(text or "").strip()
    if not raw:
        return {"descripcion": "", "requirements": [], "benefits": []}

    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    raw = ATTRIBUTION_PATTERN.sub(" ", raw)
    raw = re.sub(r"[ \t]+", " ", raw).strip()

    normalized, offsets = _normalize_with_map(raw)
    marker = FOOTER_MARKER_PATTERN.search(normalized)
    if marker:
        body = raw[: offsets[marker.start()]].strip()
        tail = raw[offsets[marker.end() - 1] + 1:]
        skipped = re.match(r"\s*:?\s*\d+\s*", tail)
        footer = tail[skipped.end():] if skipped else tail
    else:
        body, footer = raw, ""

    if not body:
        return {
            "descripcion": "",
            "requirements": [],
            "benefits": _dedupe(_footer_items(footer)),
        }

    headings = _find_headings(body)
    if not headings:
        result = _split_unheaded(body)
        result["benefits"] = _dedupe(result["benefits"] + _footer_items(footer))
        return result

    buckets = {"description": [], "requirements": [], "benefits": []}
    intro = re.sub(r"\s+", " ", body[: headings[0][0]]).strip()
    if intro:
        buckets["description"].append(intro)

    for index, (start, end, section) in enumerate(headings):
        stop = headings[index + 1][0] if index + 1 < len(headings) else len(body)
        if section in {"requirements", "benefits"}:
            # El encabezado no se conserva; tampoco el ':' que lo sigue.
            segment = re.sub(r"^[\s:]+", "", body[end:stop]).strip()
            if not segment:
                continue
            items = _split_bullets(segment)
            buckets[section].extend(items or [re.sub(r"\s+", " ", segment).strip()])
        else:
            # Los encabezados de descripción quedan como parte del texto.
            segment = body[start:stop].strip()
            if segment:
                buckets["description"].append(re.sub(r"\s+", " ", segment).strip())

    buckets["benefits"].extend(_footer_items(footer))
    return {
        "descripcion": "\n\n".join(p for p in buckets["description"] if p).strip(),
        "requirements": _dedupe(buckets["requirements"]),
        "benefits": _dedupe(buckets["benefits"]),
    }
