import json
import re
from html import unescape
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import scrapy

from ..utils.query_builder import SearchQueryBuilder


OCC_BASE = "https://www.occ.com.mx"


class OccSpider(scrapy.Spider):
    name = "occ"
    allowed_domains = ["occ.com.mx"]
    max_pages = 4

    custom_settings = {
        # OCC rate-limits aggressively (HTTP 403 after a burst): crawl slowly,
        # keep concurrency low and retry the transient status codes.
        "DOWNLOAD_DELAY": 3.0,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [429, 500, 502, 503, 504],
    }

    # Mapeo del enlace "Espacio de trabajo" de la ficha al texto que entiende
    # `JobEnrichmentPipeline._detect_modalidad`.
    WORKSPACE_MODALITY = {
        "tipo-home-office-remoto": "Remoto",
        "tipo-home-office-mixto": "Híbrido",
        "tipo-en-oficina": "Presencial",
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
        urls = self.query_builder.build_urls("occ")
        if not urls:
            self.logger.warning("SearchQueryBuilder returned no OCC URLs; nothing to crawl.")
        self.logger.info("SearchQueryBuilder generated %d OCC URLs", len(urls))

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
        query["page"] = str(page_number)
        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    def _clean_text(self, value):
        if value is None:
            return ""
        if isinstance(value, (list, tuple)):
            value = " ".join(str(v) for v in value if v)
        text = scrapy.Selector(text=str(value)).xpath("string(.)").get() or str(value)
        return re.sub(r"\s+", " ", text).strip()

    def _extract_card_jobs(self, response):
        """Extrae (url_detalle, titulo) de las cards del listado."""
        jobs = []
        cards = response.css("li.vacancy-card, [data-vacancy-card]")
        for card in cards:
            offer_id = card.attrib.get("data-id") or card.css("::attr(data-id)").get()
            if not offer_id:
                continue
            offer_id = str(offer_id).strip()
            if not offer_id.isdigit():
                continue

            title = self._clean_text(
                " ".join(card.css("h2::text, h2 *::text, [class*='title'] ::text").getall())
            )
            detail_url = f"{OCC_BASE}/empleo/oferta/{offer_id}"
            if detail_url not in self._seen_detail_urls:
                self._seen_detail_urls.add(detail_url)
                jobs.append((detail_url, title))
        return jobs

    def _extract_item_list_jobs(self, response):
        """Fallback: URLs del JSON-LD ItemList del listado (sin query params)."""
        jobs = []
        for item in self._find_ld_nodes(response, "ItemList"):
            for element in item.get("itemListElement") or []:
                if not isinstance(element, dict):
                    continue
                url = element.get("url")
                if not url and isinstance(element.get("item"), dict):
                    url = element["item"].get("url")
                if not isinstance(url, str):
                    continue
                detail_url = url.split("?")[0].replace("//empleo/", "/empleo/")
                if "occ.com.mx" not in urlparse(detail_url).netloc:
                    continue
                slug = urlparse(detail_url).path.rsplit("/", 1)[-1]
                slug = re.sub(r"^\d+-?", "", slug)
                title = slug.replace("-", " ").strip()
                if detail_url not in self._seen_detail_urls:
                    self._seen_detail_urls.add(detail_url)
                    jobs.append((detail_url, title))
        return jobs

    def parse(self, response):
        jobs = self._extract_card_jobs(response)
        if not jobs:
            jobs = self._extract_item_list_jobs(response)
        if not jobs:
            self.logger.warning("No job cards found on %s", response.url)

        followed = 0
        for detail_url, title in jobs:
            if title and not self.query_builder.should_follow_job(title):
                self.logger.debug("Skipping %s (title=%r) by seniority pre-filter", detail_url, title)
                continue
            followed += 1
            yield scrapy.Request(detail_url, callback=self.parse_detail)

        page = int(response.meta.get("page", 1))
        # `jobs` (not `followed`) drives pagination: the pre-filter must not cut
        # the listing short when a page is full of senior/entry-level titles.
        if page < self.max_pages and jobs:
            base_url = response.meta.get("base_url") or response.url
            next_url = self._with_page(base_url, page + 1)
            yield scrapy.Request(
                next_url,
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
                # OCC añade un `;` después del objeto y, a veces, contenido extra.
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

    def _format_address(self, value):
        if not isinstance(value, dict):
            return self._clean_text(value)
        lowered = {str(k).lower(): v for k, v in value.items()}
        parts = []
        for key in ("streetAddress", "addressLocality", "addressRegion", "postalCode", "addressCountry"):
            part = lowered.get(key.lower())
            if isinstance(part, dict):
                part = part.get("name")
            if part:
                parts.append(self._clean_text(part))
        return ", ".join(parts)

    def _extract_from_ld_json(self, ld):
        if not ld:
            return {}

        title = self._pick(ld, "title", "name")
        company = self._as_name(self._pick(ld, "hiringOrganization"))
        description = self._html_to_text(self._pick(ld, "description"))

        job_location_type = self._as_name(self._pick(ld, "jobLocationType"))
        locations = self._pick(ld, "jobLocation")
        if not isinstance(locations, list):
            locations = [locations] if locations else []

        location_parts = []
        for location in locations:
            address = self._pick(location, "address")
            formatted = self._format_address(address)
            if formatted:
                location_parts.append(formatted)

        return {
            "titulo": self._clean_text(title),
            "empresa": company,
            "descripcion": description,
            "modalidad_raw": job_location_type,
            "ubicacion_texto": ", ".join(location_parts),
        }

    def _workspace_modality(self, response):
        node = response.xpath(
            "//p[contains(normalize-space(.), 'Espacio de trabajo')]/following-sibling::a[1]"
        )
        text = self._clean_text(node.xpath("string(.)").get())
        href = node.xpath("@href").get() or ""
        for key, modality in self.WORKSPACE_MODALITY.items():
            if key in href:
                return modality
        return text

    def _extract_from_css(self, response):
        title = (
            response.css("h1::text").get()
            or response.css("h1 *::text").get()
            or response.css("meta[property='og:title']::attr(content)").get()
            or ""
        )

        description_html = (
            response.css("div.rich-text").get()
            or response.css("[class*='description']").get()
            or ""
        )
        description = self._html_to_text(description_html)

        # La ficha de OCC no expone empresa/ubicación con clases semánticas:
        # el meta description sí las trae como "{empresa} - {ubicación}".
        company = ""
        location = ""
        meta = response.css("meta[name='description']::attr(content)").get() or ""
        match = re.search(
            r"Ofertas de trabajo de .*?\.\s*(?P<company>.+?)\s+-\s+(?P<location>.+?)\.\s*Descubre",
            meta,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            company = match.group("company")
            location = match.group("location")

        return {
            "titulo": self._clean_text(title),
            "empresa": self._clean_text(company),
            "descripcion": description,
            "modalidad_raw": self._workspace_modality(response),
            "ubicacion_texto": self._clean_text(location),
        }

    def parse_detail(self, response):
        ld_data = self._extract_from_ld_json(self._extract_job_posting(response))
        css_data = self._extract_from_css(response)

        def pick(key, default=""):
            value = ld_data.get(key)
            if value:
                return value
            return css_data.get(key, default)

        modality_parts = [
            self._clean_text(ld_data.get("modalidad_raw")),
            self._clean_text(css_data.get("modalidad_raw")),
        ]
        modality_parts = list(dict.fromkeys(part for part in modality_parts if part))

        yield {
            "titulo": pick("titulo"),
            "empresa": pick("empresa") or "Empresa confidencial",
            "modalidad_raw": " ".join(modality_parts),
            "ubicacion_texto": pick("ubicacion_texto"),
            "descripcion": pick("descripcion"),
            "tags_tecnologias": [],
            "requirements": [],
            "benefits": [],
            # Requisito de la spec: sin query params.
            "url_oferta": response.url.split("?")[0],
        }
