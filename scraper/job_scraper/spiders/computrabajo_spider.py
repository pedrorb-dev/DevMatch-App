import json
import re
from html import unescape
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import scrapy

from ..utils.query_builder import SearchQueryBuilder


COMPUTRABAJO_BASE = "https://mx.computrabajo.com"
DETAIL_PATH_PREFIX = "/ofertas-de-trabajo/oferta-de-trabajo-de-"

# Empresas que Computrabajo oculta detrás de una etiqueta genérica.
CONFIDENTIAL_MARKERS = (
    "importante empresa",
    "empresa confidencial",
    "confidencial",
)

# Texto de modalidad que publica Computrabajo en el listado (span con icono
# `i_home_office`) o en la cabecera de la ficha.
MODALITY_PATTERN = re.compile(
    r"\b(remoto|desde casa|teletrabajo|h[ií]brido|presencial)\b",
    re.IGNORECASE,
)


class ComputrabajoSpider(scrapy.Spider):
    name = "computrabajo"
    allowed_domains = ["mx.computrabajo.com"]
    max_pages = 4

    custom_settings = {
        # Computrabajo rate-limits aggressive crawls: crawl slowly, keep
        # concurrency low and retry the transient status codes.
        "DOWNLOAD_DELAY": 3.5,
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
        urls = self.query_builder.build_urls("computrabajo")
        if not urls:
            self.logger.warning("SearchQueryBuilder returned no Computrabajo URLs; nothing to crawl.")
        self.logger.info("SearchQueryBuilder generated %d Computrabajo URLs", len(urls))

        seen = set()
        for url in urls:
            if url in seen:
                continue
            seen.add(url)
            yield scrapy.Request(url, callback=self.parse, meta={"page": 1, "base_url": url})

    # --- listado ----------------------------------------------------------

    def _with_page(self, url, page_number):
        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["p"] = str(page_number)
        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    def _clean_text(self, value):
        if value is None:
            return ""
        if isinstance(value, (list, tuple)):
            value = " ".join(str(v) for v in value if v)
        text = scrapy.Selector(text=str(value)).xpath("string(.)").get() or str(value)
        return re.sub(r"\s+", " ", text).strip()

    def _detail_url(self, response, href):
        """Convierte un enlace del listado en URL de ficha sin `#...` ni query."""
        if not href:
            return ""
        absolute = response.urljoin(href)
        parsed = urlparse(absolute)
        host = parsed.netloc.lower().split(":")[0]
        if not host.endswith("computrabajo.com"):
            return ""
        path = parsed.path
        if DETAIL_PATH_PREFIX not in path and "/trabajo-de-" not in path:
            return ""
        return urlunparse(parsed._replace(query="", fragment=""))

    def _card_modality(self, card):
        texts = card.xpath(".//span[span[contains(@class, 'i_home_office')]]//text()").getall()
        value = self._clean_text(texts)
        if value:
            return value
        # El mismo contenedor `div.fs13 span.dIB` también muestra el salario:
        # solo se acepta si el texto es realmente una modalidad.
        for text in card.css("div.fs13 span.dIB::text").getall():
            cleaned = self._clean_text(text)
            if cleaned and MODALITY_PATTERN.search(cleaned):
                return cleaned
        return ""

    def _extract_card_jobs(self, response):
        """Extrae las fichas (`article.box_offer`) del listado."""
        jobs = []
        cards = response.css(
            "article.box_offer[data-id], article[data-offers-grid-offer-item-container]"
        )
        for card in cards:
            href = card.css("h2 a[href]::attr(href)").get()
            if not href:
                href = card.css(f"a[href*='{DETAIL_PATH_PREFIX}']::attr(href)").get()
            detail_url = self._detail_url(response, href)
            if not detail_url or detail_url in self._seen_detail_urls:
                continue

            title = self._clean_text(card.css("h2 a::text").getall())
            if not title:
                title = self._clean_text(card.css("h2 ::text").getall())

            self._seen_detail_urls.add(detail_url)
            jobs.append(
                {
                    "url": detail_url,
                    "title": title,
                    "company": self._clean_text(
                        card.css("a[offer-grid-article-company-url]::text").getall()
                    ),
                    "location": self._clean_text(card.css("p.fs16 span.mr10::text").getall()),
                    "modalidad_raw": self._card_modality(card),
                }
            )
        return jobs

    def _extract_link_jobs(self, response):
        """Fallback: enlaces de ficha sueltos si cambia el markup de las cards."""
        jobs = []
        links = response.css(f"a[href*='{DETAIL_PATH_PREFIX}']")
        for link in links:
            detail_url = self._detail_url(response, link.attrib.get("href"))
            if not detail_url or detail_url in self._seen_detail_urls:
                continue
            self._seen_detail_urls.add(detail_url)
            jobs.append(
                {
                    "url": detail_url,
                    "title": self._clean_text(link.css("::text").getall()),
                    "company": "",
                    "location": "",
                    "modalidad_raw": "",
                }
            )
        return jobs

    def parse(self, response):
        jobs = self._extract_card_jobs(response)
        if not jobs:
            jobs = self._extract_link_jobs(response)
        if not jobs:
            self.logger.warning("No job cards found on %s", response.url)

        for job in jobs:
            title = job.get("title") or ""
            if title and not self.query_builder.should_follow_job(title):
                self.logger.debug(
                    "Skipping %s (title=%r) by seniority pre-filter", job["url"], title
                )
                continue
            yield scrapy.Request(
                job["url"],
                callback=self.parse_detail,
                meta={"modalidad_raw": job.get("modalidad_raw") or ""},
            )

        page = int(response.meta.get("page", 1))
        # `jobs` (not the filtered count) drives pagination: the pre-filter must
        # not cut the listing short when a page is full of senior/entry titles.
        if page < self.max_pages and jobs:
            base_url = response.meta.get("base_url") or response.url
            yield scrapy.Request(
                self._with_page(base_url, page + 1),
                callback=self.parse,
                meta={"page": page + 1, "base_url": base_url},
            )

    # --- ficha ------------------------------------------------------------

    def _find_ld_nodes(self, response, wanted_type):
        """Devuelve los nodos JSON-LD de un tipo, tolerando `;` final y @graph."""
        nodes = []
        scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        for raw in scripts:
            raw = (raw or "").strip()
            if not raw:
                continue
            data = None
            try:
                data = json.loads(raw)
            except Exception:
                try:
                    data, _ = json.JSONDecoder().raw_decode(raw)
                except Exception:
                    continue

            candidates = data if isinstance(data, list) else [data]
            expanded = []
            for candidate in candidates:
                if isinstance(candidate, dict) and isinstance(candidate.get("@graph"), list):
                    expanded.extend(candidate["@graph"])
                else:
                    expanded.append(candidate)

            for node in expanded:
                if not isinstance(node, dict):
                    continue
                node_type = node.get("@type")
                types = node_type if isinstance(node_type, list) else [node_type]
                if any(str(t).lower() == wanted_type.lower() for t in types if t):
                    nodes.append(node)
        return nodes

    def _extract_job_posting(self, response):
        nodes = self._find_ld_nodes(response, "JobPosting")
        return nodes[0] if nodes else None

    @staticmethod
    def _pick(data, *names):
        if not isinstance(data, dict):
            return None
        lowered = {str(k).lower(): v for k, v in data.items()}
        for name in names:
            value = lowered.get(name.lower())
            if value not in (None, "", []):
                return value
        return None

    def _as_name(self, value):
        if isinstance(value, dict):
            return self._clean_text(self._pick(value, "name"))
        if isinstance(value, list):
            for item in value:
                name = self._as_name(item)
                if name:
                    return name
            return ""
        return self._clean_text(value)

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

    def _format_location(self, value):
        if not isinstance(value, dict):
            return self._clean_text(value)
        lowered = {str(k).lower(): v for k, v in value.items()}
        parts = []
        # Computrabajo muestra primero el municipio (`addressRegion`) y después
        # el estado (`addressLocality`).
        for key in ("addressregion", "addresslocality", "addresscountry"):
            part = lowered.get(key)
            if isinstance(part, dict):
                part = part.get("name")
            text = self._clean_text(part)
            if text and text.lower() not in {p.lower() for p in parts}:
                parts.append(text)
        return ", ".join(parts)

    def _extract_from_ld_json(self, ld):
        if not ld:
            return {}

        title = self._pick(ld, "title", "name")
        company = self._as_name(self._pick(ld, "hiringOrganization"))
        description = self._html_to_text(self._pick(ld, "description"))

        locations = self._pick(ld, "jobLocation")
        if not isinstance(locations, list):
            locations = [locations] if locations else []

        location_parts = []
        for location in locations:
            address = self._pick(location, "address")
            formatted = self._format_location(address or location)
            if formatted and formatted.lower() not in {p.lower() for p in location_parts}:
                location_parts.append(formatted)

        return {
            "titulo": self._clean_text(title),
            "empresa": company,
            "descripcion": description,
            "ubicacion_texto": ", ".join(location_parts),
        }

    def _header_line(self, response):
        """Cabecera de la ficha: `{empresa} - {ubicación}`."""
        return self._clean_text(
            response.xpath(
                "//h1[contains(@class, 'box_detail')]/following-sibling::p[1]//text()"
            ).getall()
        )

    def _extract_modality_from_dom(self, response):
        """Modalidad desde el DOM (el JSON-LD no la expone de forma fiable)."""
        parts = []

        meta_value = self._clean_text(response.meta.get("modalidad_raw"))
        if meta_value:
            parts.append(meta_value)

        # Ficha: span con el icono de home office (p. ej. "Desde casa").
        icon_texts = response.xpath(
            "//span[span[contains(@class, 'i_home_office')]]//text()"
        ).getall()
        icon_value = self._clean_text(icon_texts)
        if icon_value:
            parts.append(icon_value)

        # Algunas fichas solo indican la modalidad en la cabecera.
        header = self._header_line(response)
        if header and MODALITY_PATTERN.search(header):
            parts.append(header)

        unique = []
        for part in parts:
            if part and part.lower() not in {p.lower() for p in unique}:
                unique.append(part)
        return " ".join(unique)

    def _extract_from_css(self, response):
        title = (
            response.css("h1.box_detail::text").get()
            or response.css("h1::text").get()
            or response.css("h1 *::text").get()
            or response.css("meta[property='og:title']::attr(content)").get()
            or ""
        )

        company = ""
        location = ""
        header = self._header_line(response)
        if header:
            company, separator, location = header.partition(" - ")
            if not separator:
                company, location = "", header

        if not company:
            company = self._clean_text(
                response.css("a[href*='/empresas/']::text").getall()
                or response.css("a.dIB.fs16.js-o-link::text").getall()
            )

        description_html = (
            response.css("div[div-link='oferta'] p.mbB").get()
            or response.css("div[div-link='oferta']").get()
            or response.css("[class*='description']").get()
            or ""
        )

        return {
            "titulo": self._clean_text(title),
            "empresa": self._clean_text(company),
            "ubicacion_texto": self._clean_text(location),
            "descripcion": self._html_to_text(description_html),
            "modalidad_raw": self._extract_modality_from_dom(response),
        }

    def _normalize_company(self, value):
        text = self._clean_text(value)
        if not text:
            return ""
        lowered = text.lower()
        if any(marker in lowered for marker in CONFIDENTIAL_MARKERS):
            return "Empresa confidencial"
        return text

    @staticmethod
    def _canonical_url(value):
        return str(value or "").split("#", 1)[0].split("?", 1)[0].strip()

    def parse_detail(self, response):
        ld_data = self._extract_from_ld_json(self._extract_job_posting(response))
        css_data = self._extract_from_css(response)

        def pick(key, default=""):
            value = ld_data.get(key)
            if value:
                return value
            return css_data.get(key, default)

        yield {
            "titulo": pick("titulo"),
            "empresa": self._normalize_company(pick("empresa")) or "Empresa confidencial",
            "modalidad_raw": pick("modalidad_raw"),
            "ubicacion_texto": pick("ubicacion_texto"),
            "descripcion": pick("descripcion"),
            "tags_tecnologias": [],
            "requirements": [],
            "benefits": [],
            "url_oferta": self._canonical_url(response.url),
        }
