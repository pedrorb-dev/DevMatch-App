
import re
import unicodedata
from urllib.parse import quote_plus

from supabase import create_client

from job_scraper import stack_catalog

HIRELINE_BASE = "https://hireline.io"
OCC_BASE = "https://www.occ.com.mx"
COMPUTRABAJO_BASE = "https://mx.computrabajo.com"
GETONBRD_BASE = "https://www.getonbrd.com"

HIRELINE_PLATFORM = "hireline"
OCC_PLATFORM = "occ"
COMPUTRABAJO_PLATFORM = "computrabajo"
GETONBRD_PLATFORM = "getonbrd"


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

def _stack_slug(tech, portal):
    """Slug del catálogo canónico para el portal; `_slugify` como fallback."""
    return stack_catalog.STACK_SLUGS.get(portal, {}).get(_normalize_text(tech)) or _slugify(tech)


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
    COMPUTRABAJO_ENTRY_ROUTE = "/trabajo-de-trainee-ti"
    COMPUTRABAJO_TECH_SEARCH = "/trabajo-de-{slug}"
    # Prefijos de entrada por tecnología (cuando hay perfiles de 0 años).
    COMPUTRABAJO_ENTRY_PREFIXES = ("practicante", "becario", "desarrollador-junior")
    COMPUTRABAJO_ENTRY_SEARCH = "/trabajo-de-{prefix}-{slug}"
    COMPUTRABAJO_JUNIOR_SEARCH = "/trabajo-de-desarrollador-{slug}"
    COMPUTRABAJO_SENIOR_SEARCHES = (
        "/trabajo-de-senior-{slug}",
        "/trabajo-de-lider-tecnico-{slug}",
    )

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
        elif platform == COMPUTRABAJO_PLATFORM:
            urls = self._build_computrabajo_urls()
        elif platform == GETONBRD_PLATFORM:
            urls = self._build_getonbrd_urls()
        else:
            raise ValueError(
                f"Plataforma no soportada: {platform!r} "
                "(usa 'hireline', 'occ', 'computrabajo' o 'getonbrd')"
            )
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
            slug = _stack_slug(tech, OCC_PLATFORM)
            if slug:
                urls.append(f"{OCC_BASE}{self.OCC_TECH_SEARCH.format(slug=slug)}")

        return urls

    def _build_computrabajo_urls(self):
        urls = []

        # Ruta estática única de entrada (sin slug).
        if self._entry_allowed:
            urls.append(f"{COMPUTRABAJO_BASE}{self.COMPUTRABAJO_ENTRY_ROUTE}")

        for tech in self.stack:
            slug = _stack_slug(tech, COMPUTRABAJO_PLATFORM)
            if not slug:
                continue

            # Búsqueda base por tecnología: siempre, en cualquier rango.
            urls.append(f"{COMPUTRABAJO_BASE}{self.COMPUTRABAJO_TECH_SEARCH.format(slug=slug)}")

            if self._entry_allowed:
                for prefix in self.COMPUTRABAJO_ENTRY_PREFIXES:
                    route = self.COMPUTRABAJO_ENTRY_SEARCH.format(prefix=prefix, slug=slug)
                    urls.append(f"{COMPUTRABAJO_BASE}{route}")
            if self.has_junior_level:
                route = self.COMPUTRABAJO_JUNIOR_SEARCH.format(slug=slug)
                urls.append(f"{COMPUTRABAJO_BASE}{route}")
            if self.has_senior_level:
                for route in self.COMPUTRABAJO_SENIOR_SEARCHES:
                    urls.append(f"{COMPUTRABAJO_BASE}{route.format(slug=slug)}")

        return urls

    def _build_getonbrd_urls(self):
        urls = []

        # Solo `jobs-{slug}` por tecnología: no se diferencia por
        # `experiencia_anos` (el seniority fino lo hacen `should_follow_job` y
        # `JobEnrichmentPipeline`) y se evita el doble prefijo `/jobs/`-`/empleos/`.
        for tech in self.stack:
            slug = _stack_slug(tech, GETONBRD_PLATFORM)
            if not slug:
                continue
            urls.append(f"{GETONBRD_BASE}/jobs-{slug}")

        return urls
