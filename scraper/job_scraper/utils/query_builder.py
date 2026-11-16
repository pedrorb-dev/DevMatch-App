"""Generación dinámica de URLs de búsqueda a partir de `user_profiles`.

El spider ya no lleva categorías ni tecnologías hardcodeadas: `SearchQueryBuilder`
consulta `user_profiles.stack` y `user_profiles.experiencia_anos` una sola vez
(resultado cacheado) y deriva las URLs de cada plataforma.

Rangos de experiencia y qué aportan a las URLs:

- `0`      -> rutas de entrada (Hireline `trainee`/`becario-ti`, OCC `de-practicante`).
- `1..3`   -> ruta junior de Hireline.
- `4+`     -> ruta senior de Hireline.
- todos    -> una búsqueda por tecnología (`?k={tech}` en Hireline, `de-{slug}` en OCC).

Las búsquedas por tecnología cubren todos los niveles: el filtro fino de seniority
lo hace `should_follow_job` sobre el título antes de descargar la ficha.
"""

import re
import unicodedata
from urllib.parse import quote_plus

from supabase import create_client

HIRELINE_BASE = "https://hireline.io"
OCC_BASE = "https://www.occ.com.mx"

HIRELINE_PLATFORM = "hireline"
OCC_PLATFORM = "occ"


def _strip_accents(text):
    normalized = unicodedata.normalize("NFD", text or "")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _normalize_text(text):
    return re.sub(r"\s+", " ", _strip_accents(str(text or "")).lower()).strip()


def _slugify(text):
    text = _normalize_text(text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


# Indicadores de entrada en el título (bilingüe).
ENTRY_TITLE_PATTERNS = [
    r"\bbecari[oa]s?\b",
    r"\bpracticantes?\b",
    r"\bestadias?\b",
    r"\bintern(?:ship)?s?\b",
    r"\btrainees?\b",
    r"\bsin experiencia\b",
    r"\bno experience\b",
]

# Indicadores senior en el título.
SENIOR_TITLE_PATTERNS = [
    r"\bsenior\b",
    r"\bsr\b\.?",
    r"\blead\b",
    r"\barchitect\b",
    r"\bmanager\b",
]

# Slugs de OCC para los stacks canónicos que detecta el pipeline. El resto se
# resuelve con `_slugify`.
OCC_STACK_SLUGS = {
    "spring boot": "spring-boot",
    "angular": "angular",
    "react": "react",
    "vue": "vue",
    "java": "java",
    "javascript": "javascript",
    "typescript": "typescript",
    "python": "python",
    "sql": "sql",
    "postgresql": "postgresql",
    "mysql": "mysql",
    "mongodb": "mongodb",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "aws": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "node.js": "node-js",
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    ".net": "dotnet",
    "c#": "c-sharp",
    "php": "php",
    "laravel": "laravel",
    "ruby": "ruby",
    "ruby on rails": "ruby-on-rails",
    "go": "go",
    "git": "git",
    "linux": "linux",
    "redis": "redis",
    "graphql": "graphql",
    "rest": "rest",
}


def should_follow_job(title, active_experience_levels):
    """Pre-filtra por título antes de descargar la ficha del detalle.

    - Descarta títulos de entrada (becario/practicante/estadías/intern/...) cuando
      ningún perfil activo tiene 0 años.
    - Descarta títulos senior (senior/sr/lead/architect/manager) cuando ningún
      perfil activo tiene 4 años o más.
    """
    levels = set()
    for level in active_experience_levels or []:
        try:
            levels.add(int(level))
        except (TypeError, ValueError):
            continue

    text = _normalize_text(title)
    if not text:
        return True

    # Sin perfiles conocidos no se descarta nada (fail-safe).
    if not levels:
        return True

    if not any(level <= 0 for level in levels):
        if any(re.search(pattern, text) for pattern in ENTRY_TITLE_PATTERNS):
            return False

    if not any(level >= 4 for level in levels):
        if any(re.search(pattern, text) for pattern in SENIOR_TITLE_PATTERNS):
            return False

    return True


class SearchQueryBuilder:
    """Construye las URLs de búsqueda de cada plataforma a partir de `user_profiles`."""

    HIRELINE_ENTRY_ROUTES = (
        "/mx/empleos-de-trainee",
        "/mx/empleos-de-becario-ti",
    )
    HIRELINE_JUNIOR_ROUTE = "/mx/empleos-de-desarrollador-junior"
    HIRELINE_SENIOR_ROUTE = "/mx/empleos-de-senior"
    HIRELINE_TECH_SEARCH = "/mx/empleos?k={tech}"
    OCC_ENTRY_SLUG = "practicante"
    OCC_TECH_SEARCH = "/empleos/de-{slug}/"

    def __init__(self, supabase_url=None, supabase_key=None, client=None, rows=None):
        self._supabase_url = (supabase_url or "").strip()
        self._supabase_key = (supabase_key or "").strip()
        self._client = client
        # `rows` permite inyectar el resultado de user_profiles (tests).
        self._rows = rows
        self._profile = None

    @classmethod
    def from_settings(cls, settings):
        return cls(
            supabase_url=settings.get("SUPABASE_URL"),
            supabase_key=settings.get("SUPABASE_SERVICE_ROLE_KEY"),
        )

    # --- perfil -----------------------------------------------------------

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._supabase_url or not self._supabase_key:
            return None
        self._client = create_client(self._supabase_url, self._supabase_key)
        return self._client

    def _fetch_user_profiles(self):
        if self._rows is not None:
            return self._rows
        client = self._get_client()
        if client is None:
            return []
        try:
            response = client.table("user_profiles").select("stack, experiencia_anos").execute()
            return getattr(response, "data", None) or []
        except Exception:
            return []

    def _load_profile(self):
        if self._profile is not None:
            return self._profile

        stack = set()
        levels = set()
        for row in self._fetch_user_profiles() or []:
            if not isinstance(row, dict):
                continue

            raw_stack = row.get("stack")
            if isinstance(raw_stack, str):
                raw_stack = [raw_stack]
            if isinstance(raw_stack, (list, tuple)):
                for value in raw_stack:
                    if isinstance(value, str) and value.strip():
                        stack.add(value.strip())

            raw_level = row.get("experiencia_anos")
            if raw_level is not None:
                try:
                    levels.add(int(raw_level))
                except (TypeError, ValueError):
                    continue

        self._profile = (
            sorted(stack, key=str.lower),
            tuple(sorted(levels)),
        )
        return self._profile

    @property
    def stack(self):
        return list(self._load_profile()[0])

    @property
    def active_experience_levels(self):
        return list(self._load_profile()[1])

    @property
    def has_entry_level(self):
        return any(level <= 0 for level in self.active_experience_levels)

    @property
    def has_junior_level(self):
        return any(1 <= level <= 3 for level in self.active_experience_levels)

    @property
    def has_senior_level(self):
        return any(level >= 4 for level in self.active_experience_levels)

    @property
    def _entry_allowed(self):
        # Fail-safe: sin stack o sin perfiles, Hireline solo puede usar rutas de
        # entrada y OCC solo la de practicante.
        levels = self.active_experience_levels
        return not self.stack or not levels or self.has_entry_level

    def should_follow_job(self, title):
        """Igual que el helper de módulo, usando los niveles cacheados."""
        return should_follow_job(title, self.active_experience_levels)

    # --- URLs --------------------------------------------------------------

    def build_urls(self, platform):
        platform = (platform or "").strip().lower()
        if platform == HIRELINE_PLATFORM:
            urls = self._build_hireline_urls()
        elif platform == OCC_PLATFORM:
            urls = self._build_occ_urls()
        else:
            raise ValueError(f"Plataforma no soportada: {platform!r} (usa 'hireline' u 'occ')")
        return list(dict.fromkeys(urls))

    def _build_hireline_urls(self):
        urls = []

        if self._entry_allowed:
            urls.extend(f"{HIRELINE_BASE}{route}" for route in self.HIRELINE_ENTRY_ROUTES)
        if self.has_junior_level:
            urls.append(f"{HIRELINE_BASE}{self.HIRELINE_JUNIOR_ROUTE}")
        if self.has_senior_level:
            urls.append(f"{HIRELINE_BASE}{self.HIRELINE_SENIOR_ROUTE}")

        for tech in self.stack:
            urls.append(f"{HIRELINE_BASE}{self.HIRELINE_TECH_SEARCH.format(tech=quote_plus(tech))}")

        return urls

    def _build_occ_urls(self):
        urls = []

        if self._entry_allowed:
            urls.append(f"{OCC_BASE}{self.OCC_TECH_SEARCH.format(slug=self.OCC_ENTRY_SLUG)}")

        for tech in self.stack:
            slug = OCC_STACK_SLUGS.get(tech.strip().lower()) or _slugify(tech)
            if slug:
                urls.append(f"{OCC_BASE}{self.OCC_TECH_SEARCH.format(slug=slug)}")

        return urls
