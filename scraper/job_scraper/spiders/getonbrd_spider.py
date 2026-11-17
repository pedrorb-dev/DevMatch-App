import re
import unicodedata
from html import unescape
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import scrapy

from ..items import JobOfferItem
from ..utils.query_builder import SearchQueryBuilder


GETONBRD_BASE = "https://www.getonbrd.com"

# Prefijos de ficha: el listado enlaza `/empleos/<categoría>/<slug>` y la
# canónica es `/jobs/<categoría>/<slug>`. Se aceptan ambos.
DETAIL_PATH_MARKERS = ("/empleos/", "/jobs/")
NON_DETAIL_PATH_PREFIXES = ("/jobs/tag/", "/jobs/city/", "/jobs/companies/")

# Texto de modalidad que publica Get on Board en el DOM (`span.location` y
# `span[itemprop="qualifications"]`).
MODALITY_PATTERN = re.compile(
    r"\b(remote|remoto|telecommute|telework|hybrid|h[ií]brido|"
    r"on[- ]?site|onsite|in[- ]?office|presencial)\b",
    re.IGNORECASE,
)

# Países distintos de México que se consideran "extranjero conocido". El resto
# de valores no listados se conservan (fail-safe).
FOREIGN_COUNTRIES = {
    # LATAM
    "cl",
    "chile",
    "co",
    "colombia",
    "ar",
    "argentina",
    "pe",
    "peru",
    "uy",
    "uruguay",
    "br",
    "brasil",
    "brazil",
    "ec",
    "ecuador",
    "ve",
    "venezuela",
    "py",
    "paraguay",
    "bo",
    "bolivia",
    "sv",
    "el salvador",
    "gt",
    "guatemala",
    "hn",
    "honduras",
    "ni",
    "nicaragua",
    "cr",
    "costa rica",
    "pa",
    "panama",
    "do",
    "republica dominicana",
    "dominican republic",
    "cu",
    "cuba",
    # Otros frecuentes
    "us",
    "usa",
    "united states",
    "estados unidos",
    "ca",
    "canada",
    "es",
    "spain",
    "espana",
    "pt",
    "portugal",
    "gb",
    "uk",
    "united kingdom",
}


def _strip_accents(text):
    normalized = unicodedata.normalize("NFD", text or "")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _normalize_text(text):
    return re.sub(r"\s+", " ", _strip_accents(str(text or "")).lower()).strip()


def _is_mexico(value):
    """`MX` / `Mexico` (con o sin acento) → True."""
    return _normalize_text(value) in {"mx", "mexico"}


def _is_known_foreign(value):
    """País extranjero conocido (código ISO o nombre normalizado)."""
    return _normalize_text(value) in FOREIGN_COUNTRIES


def _as_country_list(value):
    """Normaliza `str` o lista de países a una lista sin vacíos."""
    if not value:
        return []
    values = value if isinstance(value, (list, tuple, set)) else [value]
    return [str(item).strip() for item in values if str(item or "").strip()]


def _is_eligible(job_location_type, applicant_countries, address_countries):
    """Filtro autoritativo México/Remoto (solo ficha, fail-safe)."""
    if _normalize_text(job_location_type) == "telecommute":  # remoto
        countries = _as_country_list(applicant_countries)
        if not countries:  # "Remote" sin restricción → conservar
            return True
        if len(countries) == 1 and not _is_mexico(countries[0]):
            return False  # "Remote (Chile)" / "Remote (US)" → descartar
        return True  # México, múltiple/LATAM → conservar

    # Presencial / híbrido. `jobLocation` puede repetirse (varias sedes).
    countries = _as_country_list(address_countries)
    if not countries:  # fail-safe
        return True
    if any(_is_mexico(country) for country in countries):  # alguna sede MX → conservar
        return True
    if all(_is_known_foreign(country) for country in countries):  # CL, CO, US, ... → descartar
        return False
    return True  # desconocido → fail-safe conservar


class GetOnBrdSpider(scrapy.Spider):
    name = "getonbrd"
    allowed_domains = ["getonbrd.com", "www.getonbrd.com"]
    max_pages = 4

    custom_settings = {
        # Get on Board puede limitar el crawl: ir lento, con poca concurrencia y
        # reintentar los códigos transitorios.
        "DOWNLOAD_DELAY": 2.5,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [429, 500, 502, 503, 504],
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seen_detail_urls = set()
        self._query_builder = None

    @property
    def query_builder(self):
        # `self.settings` only exists once Scrapy attaches the crawler, so the
        # builder is created lazily on first use.
        if self._query_builder is None:
            self._query_builder = SearchQueryBuilder.from_settings(self.settings)
        return self._query_builder

    @query_builder.setter
    def query_builder(self, builder):
        self._query_builder = builder

    async def start(self):
        for request in self.start_requests():
            yield request

    def start_requests(self):
        urls = self.query_builder.build_urls("getonbrd")
        if not urls:
            self.logger.warning(
                "SearchQueryBuilder returned no Get on Board URLs; nothing to crawl."
            )
        self.logger.info("SearchQueryBuilder generated %d Get on Board URLs", len(urls))

        seen = set()
        for url in urls:
            if url in seen:
                continue
            seen.add(url)
            yield scrapy.Request(url, callback=self.parse, meta={"page": 1, "base_url": url})

    # --- helpers ----------------------------------------------------------

    @staticmethod
    def _with_page(url, page_number):
        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["page"] = str(page_number)
        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    def _clean_text(self, value):
        if value is None:
            return ""
        if isinstance(value, (list, tuple)):
            value = " ".join(str(v) for v in value if v)
        text = scrapy.Selector(text=str(value)).xpath("string(.)").get() or str(value)
        return re.sub(r"\s+", " ", text).strip()

    def _html_to_text(self, value):
        if not value:
            return ""
        text = re.sub(
            r"<\s*(?:br|/p|/li|/div|/h[1-6]|/tr|/td)\s*/?\s*>",
            "\n",
            str(value),
            flags=re.IGNORECASE,
        )
        text = re.sub(r"<[^>]+>", " ", text)
        text = unescape(text)
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]
        return "\n".join(line for line in lines if line)

    def _detail_url(self, response, href):
        """Convierte un enlace del listado en URL de ficha sin `#...` ni query."""
        if not href:
            return ""
        absolute = response.urljoin(href)
        parsed = urlparse(absolute)
        host = parsed.netloc.lower().split(":")[0]
        if not (host == "getonbrd.com" or host.endswith(".getonbrd.com")):
            return ""

        path = parsed.path
        if not any(marker in path for marker in DETAIL_PATH_MARKERS):
            return ""
        if any(path.startswith(prefix) for prefix in NON_DETAIL_PATH_PREFIXES):
            return ""
        if len([part for part in path.strip("/").split("/") if part]) < 3:
            return ""
        # Get on Board publica algunos enlaces con el puerto interno `:2053`;
        # se normaliza el host para no guardar URLs inválidas ni duplicar fichas.
        return urlunparse(
            parsed._replace(
                scheme="https",
                netloc="www.getonbrd.com",
                query="",
                fragment="",
            )
        )

    @staticmethod
    def _dedupe_key(url):
        """Clave estable entre `/empleos/<cat>/<slug>` y `/jobs/<cat>/<slug>`."""
        parsed = urlparse(url)
        path = re.sub(r"^/empleos/", "/jobs/", parsed.path)
        netloc = re.sub(r":\d+$", "", parsed.netloc.lower())
        return f"{netloc}{path}".rstrip("/")

    @staticmethod
    def _canonical_url(value):
        # Get on Board alterna entre `/empleos/...` y `/jobs/...` en su propio
        # `rel=canonical` según la ruta de entrada; se conserva la URL visitada
        # (siempre `/empleos/...` desde el listado) sin fragmento ni query.
        text = str(value or "").split("#", 1)[0].split("?", 1)[0].strip()
        parsed = urlparse(text)
        if parsed.netloc:
            netloc = re.sub(r":\d+$", "", parsed.netloc.lower())
            text = urlunparse(parsed._replace(scheme="https", netloc=netloc))
        return text

    def _location_text(self, scope):
        """Texto visible de `span.location` (excluye tooltips ocultos)."""
        nodes = scope.css("span.location")
        if not nodes:
            return ""
        texts = nodes[0].xpath(
            ".//text()[not(ancestor::div[contains(@class, 'location-tooltip-content')])]"
        ).getall()
        return self._clean_text(texts)

    @staticmethod
    def _modality(job_location_type, location_text, qualifications):
        if _normalize_text(job_location_type) == "telecommute":
            return "Remoto"
        text = _normalize_text(f"{location_text or ''} {qualifications or ''}")
        if not text:
            return ""
        if re.search(r"\bhibrido\b|\bhybrid\b", text):
            return "Híbrido"
        if re.search(r"\bremoto\b|\bremote\b|\btelecommute\b|\btelework\b", text):
            return "Remoto"
        if re.search(r"\bon[- ]?site\b|\bonsite\b|\bin[- ]?office\b|\bpresencial\b", text):
            return "Presencial"
        return ""

    # --- listado ----------------------------------------------------------

    def _extract_card_jobs(self, response):
        """Extrae las fichas (`a.results-item`) del listado."""
        jobs = []
        for card in response.css("a.results-item[href]"):
            detail_url = self._detail_url(response, card.attrib.get("href"))
            if not detail_url:
                continue
            key = self._dedupe_key(detail_url)
            if key in self._seen_detail_urls:
                continue

            title = self._clean_text(card.css("h4.results-list-title strong::text").getall())
            if not title:
                title = self._clean_text(card.css("h4.results-list-title ::text").getall())

            self._seen_detail_urls.add(key)
            jobs.append({"url": detail_url, "title": title})
        return jobs

    def _extract_link_jobs(self, response):
        """Fallback: enlaces de ficha sueltos si cambia el markup de las cards."""
        jobs = []
        for link in response.css("a[href*='/empleos/']"):
            detail_url = self._detail_url(response, link.attrib.get("href"))
            if not detail_url:
                continue
            key = self._dedupe_key(detail_url)
            if key in self._seen_detail_urls:
                continue
            self._seen_detail_urls.add(key)
            jobs.append(
                {
                    "url": detail_url,
                    "title": self._clean_text(link.css("::text").getall()),
                }
            )
        return jobs

    def parse(self, response):
        jobs = self._extract_card_jobs(response)
        if not jobs:
            jobs = self._extract_link_jobs(response)
        if not jobs and int(response.meta.get("page", 1)) == 1:
            self.logger.warning("No job cards found on %s", response.url)

        for job in jobs:
            title = job.get("title") or ""
            if title and not self.query_builder.should_follow_job(title):
                self.logger.debug(
                    "Skipping %s (title=%r) by seniority pre-filter", job["url"], title
                )
                continue
            yield scrapy.Request(job["url"], callback=self.parse_detail)

        page = int(response.meta.get("page", 1))
        # `jobs` (no el conteo filtrado) maneja la paginación: el pre-filtro no
        # debe cortar el listado cuando una página es de títulos senior/entry.
        # Si la página no trae fichas nuevas, se detiene.
        if page < self.max_pages and jobs:
            base_url = response.meta.get("base_url") or response.url
            yield scrapy.Request(
                self._with_page(base_url, page + 1),
                callback=self.parse,
                meta={"page": page + 1, "base_url": base_url},
            )

    # --- ficha ------------------------------------------------------------

    @staticmethod
    def _job_root(response):
        root = response.css('div#right-col[itemscope][itemtype*="JobPosting"]')
        if not root:
            root = response.css('[itemscope][itemtype*="JobPosting"]')
        return root

    def _itemprop_text(self, scope, selector):
        values = scope.css(f"{selector}::attr(content)").getall()
        if not values:
            values = scope.css(f"{selector}::text").getall()
        return self._clean_text(values)

    def _itemprop_list(self, scope, selector):
        values = scope.css(f"{selector}::attr(content)").getall()
        if not values:
            values = scope.css(f"{selector}::text").getall()
        cleaned = []
        for value in values:
            text = self._clean_text(value)
            if text and text.lower() not in {c.lower() for c in cleaned}:
                cleaned.append(text)
        return cleaned

    def _applicant_countries(self, scope):
        countries = []
        for node in scope.css('[itemprop="applicantLocationRequirements"]'):
            values = (
                node.css('[itemprop="name"]::attr(content)').getall()
                or node.css('[itemprop="name"]::text').getall()
                or node.css("::attr(content)").getall()
                or node.css("::text").getall()
            )
            for value in values:
                text = self._clean_text(value)
                if text and text.lower() not in {c.lower() for c in countries}:
                    countries.append(text)
        return countries

    def _skills(self, scope):
        tags = []
        for value in scope.css('[itemprop="skills"] a::text').getall():
            text = self._clean_text(value)
            if text and text.lower() not in {t.lower() for t in tags}:
                tags.append(text)
        if not tags:
            for value in scope.css(".gb-tags__item::text").getall():
                text = self._clean_text(value)
                if text and text.lower() not in {t.lower() for t in tags}:
                    tags.append(text)
        return tags

    def _location_fields(self, scope):
        """Devuelve las sedes (`jobLocation` puede repetirse) y sus países."""
        locations = []
        countries = []
        for node in scope.css('[itemprop="jobLocation"]'):
            locality = self._itemprop_text(
                node, '[itemprop="address"] [itemprop="addressLocality"]'
            )
            country = self._itemprop_text(
                node, '[itemprop="address"] [itemprop="addressCountry"]'
            )
            if locality or country:
                locations.append((locality, country))
            if country and country.lower() not in {c.lower() for c in countries}:
                countries.append(country)
        return locations, countries

    @staticmethod
    def _format_locations(locations, fallback=""):
        """Formatea las sedes sin repetir: `Lima, PE; Santiago, CL`."""
        parts = []
        for locality, country in locations:
            text = ", ".join(part for part in (locality, country) if part)
            if text and text not in parts:
                parts.append(text)
        return "; ".join(parts) or fallback

    def _extract_from_microdata(self, response):
        root = self._job_root(response)
        if not root:
            return {}

        title = self._clean_text(root.css('[itemprop="title"]::text').getall())
        company = self._clean_text(
            root.css('[itemprop="hiringOrganization"] [itemprop="name"]::text').getall()
        )
        description_html = (
            root.css('#job-body[itemprop="description"]').get()
            or root.css('[itemprop="description"]').get()
            or ""
        )
        job_location_type = self._itemprop_text(root, '[itemprop="jobLocationType"]')
        applicant_countries = self._applicant_countries(root)
        locations, address_countries = self._location_fields(root)
        location_text = self._location_text(root)
        qualifications = self._clean_text(
            root.css('[itemprop="qualifications"]::text').getall()
        )

        ubicacion = self._format_locations(locations, location_text)

        return {
            "titulo": title,
            "empresa": company,
            "descripcion": self._html_to_text(description_html),
            "modalidad_raw": self._modality(
                job_location_type, location_text, qualifications
            ),
            "ubicacion_texto": ubicacion,
            "tags_tecnologias": self._skills(root),
            "job_location_type": job_location_type,
            "applicant_countries": applicant_countries,
            "address_countries": address_countries,
        }

    def _extract_from_css(self, response):
        title = (
            response.css("h1.gb-landing-cover__title [itemprop='title']::text").get()
            or response.css("h1.gb-landing-cover__title::text").get()
            or response.css("h1::text").get()
            or response.css("meta[property='og:title']::attr(content)").get()
            or ""
        )

        company = self._clean_text(
            response.css("[itemprop='hiringOrganization'] [itemprop='name']::text").getall()
        )
        if not company:
            company = self._clean_text(
                response.css("a[href^='/companies/'] strong::text").getall()
            )

        description_html = (
            response.css("#job-body").get()
            or response.css("div.gb-rich-txt").get()
            or response.css("[class*='description']").get()
            or ""
        )

        job_location_type = self._itemprop_text(response, '[itemprop="jobLocationType"]')
        applicant_countries = self._applicant_countries(response)
        locations, address_countries = self._location_fields(response)
        location_text = self._location_text(response)
        qualifications = self._clean_text(
            response.css('[itemprop="qualifications"]::text').getall()
        )

        ubicacion = self._format_locations(locations, location_text)

        return {
            "titulo": self._clean_text(title),
            "empresa": company,
            "descripcion": self._html_to_text(description_html),
            "modalidad_raw": self._modality(
                job_location_type, location_text, qualifications
            ),
            "ubicacion_texto": ubicacion,
            "tags_tecnologias": self._skills(response),
            "job_location_type": job_location_type,
            "applicant_countries": applicant_countries,
            "address_countries": address_countries,
        }

    def parse_detail(self, response):
        microdata = self._extract_from_microdata(response)
        css_data = self._extract_from_css(response)

        def pick(key, default=""):
            value = microdata.get(key)
            if value:
                return value
            return css_data.get(key, default)

        job_location_type = pick("job_location_type")
        applicant_countries = pick("applicant_countries", [])
        address_countries = pick("address_countries", [])

        if not _is_eligible(job_location_type, applicant_countries, address_countries):
            self.logger.debug("Skipping %s (not eligible for Mexico)", response.url)
            return

        yield JobOfferItem(
            titulo=pick("titulo"),
            empresa=pick("empresa") or "Empresa confidencial",
            modalidad_raw=pick("modalidad_raw"),
            ubicacion_texto=pick("ubicacion_texto"),
            descripcion=pick("descripcion"),
            tags_tecnologias=pick("tags_tecnologias", []),
            requirements=[],
            benefits=[],
            url_oferta=self._canonical_url(response.url),
        )
