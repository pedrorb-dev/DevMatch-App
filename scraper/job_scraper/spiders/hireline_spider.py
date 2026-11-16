import json
import re
from html import unescape
from urllib.parse import quote_plus, urlencode, urljoin, urlparse, urlunparse, parse_qsl

import scrapy
from supabase import create_client


BASE_URL = "https://hireline.io"
BASE_ROUTES = [
    "/mx/empleos-de-trainee",
    "/mx/empleos-de-desarrollador-junior",
    "/mx/empleos-de-remoto",
    "/remoto/empleos-de-junior",
]


class HirelineSpider(scrapy.Spider):
    name = "hireline"
    allowed_domains = ["hireline.io"]
    max_pages = 5

    custom_settings = {
        # Ensure only hireline.io is crawled by this spider; Supabase is accessed via API client.
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seen_detail_urls = set()

    def _get_profile_stack_technologies(self):
        """Fetch unique technologies from user_profiles.stack. Fail-safe to empty list."""
        url = (self.settings.get("SUPABASE_URL") or "").strip()
        key = (self.settings.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
        if not url or not key:
            self.logger.info("Supabase credentials not configured; skipping stack-based queries.")
            return []

        try:
            client = create_client(url, key)
            response = client.table("user_profiles").select("stack").execute()
            rows = getattr(response, "data", None) or []
            techs = set()
            for row in rows:
                stack = row.get("stack") if isinstance(row, dict) else None
                if isinstance(stack, list):
                    for value in stack:
                        if isinstance(value, str):
                            cleaned = value.strip()
                            if cleaned:
                                techs.add(cleaned)
                elif isinstance(stack, str) and stack.strip():
                    techs.add(stack.strip())
            result = sorted(techs)
            self.logger.info("Loaded %d unique technologies from user_profiles.stack", len(result))
            return result
        except Exception as exc:
            self.logger.warning("Could not load user_profiles.stack (%s); using base routes only.", exc)
            return []

    async def start(self):
        for request in self.start_requests():
            yield request

    def start_requests(self):
        start_urls = [urljoin(BASE_URL, route) for route in BASE_ROUTES]
        for tech in self._get_profile_stack_technologies():
            start_urls.append(f"{BASE_URL}/mx/empleos?k={quote_plus(tech)}")

        # Deduplicate while preserving order
        seen = set()
        for url in start_urls:
            if url in seen:
                continue
            seen.add(url)
            yield scrapy.Request(url, callback=self.parse, meta={"page": 1, "base_url": url})

    def _with_page(self, url, page_number):
        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["page"] = str(page_number)
        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    def parse(self, response):
        cards = response.css("a.hl-vacancy-card")
        if not cards:
            # Fallback: try common card containers/links if class differs
            cards = response.css(".hl-vacancy-card a, a[href*='/empleo/'], a[href*='/vacante/']")

        detail_hrefs = []
        for card in cards:
            href = card.attrib.get("href") or card.css("::attr(href)").get()
            if not href:
                continue
            detail_url = response.urljoin(href)
            if "hireline.io" not in urlparse(detail_url).netloc:
                continue
            # Heuristic: treat job detail pages as those containing /empleo/ or /vacante/; if card itself is anchor to detail keep it
            if detail_url not in self._seen_detail_urls:
                self._seen_detail_urls.add(detail_url)
                detail_hrefs.append(detail_url)

        for detail_url in detail_hrefs:
            yield scrapy.Request(detail_url, callback=self.parse_detail)

        page = int(response.meta.get("page", 1))
        if page < self.max_pages and detail_hrefs:
            next_page = page + 1
            base_url = response.meta.get("base_url") or response.url
            next_url = self._with_page(base_url, next_page)
            # Avoid requesting the same paginated URL again
            if next_url != response.url or page == 1:
                yield scrapy.Request(
                    next_url,
                    callback=self.parse,
                    meta={"page": next_page, "base_url": base_url},
                )

    def _clean_text(self, value):
        if value is None:
            return ""
        if isinstance(value, (list, tuple)):
            value = " ".join(str(v) for v in value if v)
        text = scrapy.Selector(text=str(value)).xpath("string(.)").get() or str(value)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _extract_ld_json(self, response):
        scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        for raw in scripts:
            raw = (raw or "").strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            candidates = data if isinstance(data, list) else [data]
            # Flatten @graph if present
            expanded = []
            for item in candidates:
                if isinstance(item, dict) and isinstance(item.get("@graph"), list):
                    expanded.extend(item["@graph"])
                else:
                    expanded.append(item)
            for item in expanded:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("@type")
                types = item_type if isinstance(item_type, list) else [item_type]
                if any(t in ("JobPosting",) for t in types if t):
                    return item
        return None

    def _extract_from_css(self, response):
        title = (
            response.css("h1::text").get()
            or response.css("h1 *::text").get()
            or response.css("meta[property='og:title']::attr(content)").get()
            or ""
        )
        company = (
            response.css(".hl-company-name::text, .company-name::text, [class*='company']::text").get()
            or response.css("a[href*='/empresa/']::text, a[href*='/company/']::text").get()
            or ""
        )
        location = (
            " ".join(response.css("[class*='location'] *::text, [class*='ubicacion'] *::text").getall())
            or response.css("meta[name='job-location']::attr(content)").get()
            or ""
        )
        description_html = (
            response.css("[class*='description'], [class*='descripcion'], .hl-vacancy-description, article").get()
            or ""
        )
        description = self._clean_text(description_html)
        tags = [self._clean_text(t) for t in response.css(".hl-tag::text, [class*='tag']::text, .badge::text").getall()]
        tags = [t for t in tags if t]
        modality_raw = (
            " ".join(response.css("[class*='modality'] *::text, [class*='modalidad'] *::text").getall())
            or location
        )
        return {
            "titulo": self._clean_text(title),
            "empresa": self._clean_text(company),
            "modalidad_raw": self._clean_text(modality_raw),
            "ubicacion_texto": self._clean_text(location),
            "descripcion": description,
            "tags_tecnologias": tags,
        }

    def _normalize_heading(self, text):
        text = (text or "").strip().lower()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[:\-–—]+$", "", text).strip()
        return text

    def _classify_section(self, heading_text):
        h = self._normalize_heading(heading_text)
        if not h:
            return None
        req_keys = [
            "requisitos", "requerimientos", "conocimientos deseables", "conocimientos obligatorios",
            "conocimientos", "perfil", "lo que buscamos", "que buscamos", "qué necesitas", "que necesitas",
            "requisitos minimos", "requisitos mínimos", "requirements", "what we're looking for",
            "what we are looking for", "qualifications", "must have", "skills", "desired skills",
            "preferred qualifications", "key qualifications",
        ]
        ben_keys = [
            "ofrecemos", "qué ofrecemos", "que ofrecemos", "lo que ofrecemos", "beneficios", "prestaciones",
            "benefits", "what we offer", "we offer", "why join us", "perks", "compensation",
        ]
        for k in ben_keys:
            if k in h:
                return "benefits"
        for k in req_keys:
            if k in h:
                return "requirements"
        # descriptive/other sections stay in descripcion
        desc_keys = [
            "actividades", "responsabilidades", "funciones", "descripcion general", "descripción general",
            "qué harás", "que haras", "what you'll do", "what you will do", "responsibilities",
            "about the role", "about us", "role", "tu misión", "tu mision",
        ]
        for k in desc_keys:
            if k in h:
                return "description"
        # unknown short heading: keep in description
        return "description"

    def _extract_paragraph_parts(self, psel):
        html = psel.get() or ""
        html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
        text = scrapy.Selector(text=html).xpath("string(.)").get() or ""
        text = unescape(text)
        parts = []
        for raw in text.split("\n"):
            t = re.sub(r"\s+", " ", raw).strip()
            if not t:
                continue
            parts.append(t)
        bold_text = " ".join(
            self._clean_text(x)
            for x in psel.css("span[style*='font-weight'] ::text, b ::text, strong ::text").getall()
        ).strip()
        plain_text = self._clean_text(text)
        return plain_text, parts, bold_text

    def _is_heading_paragraph(self, plain_text, bold_text, parts):
        if not plain_text:
            return False
        if bold_text:
            # heading-like bold labels such as "Requisitos:" / "Ofrecemos:"
            bt = bold_text.strip()
            if len(bt) <= 80 and (":" in bt or self._classify_section(bt) in {"requirements", "benefits", "description"}):
                # if paragraph has much more text than bold label, it's probably mixed; still treat as heading if starts with label
                if plain_text.startswith(bt) or len(plain_text) <= len(bt) + 8:
                    return True
        # plain heading heuristic
        if len(plain_text) <= 80 and plain_text.endswith(":") and len(parts) <= 1:
            return self._classify_section(plain_text) is not None
        return False

    def _to_bullet_item(self, text):
        t = re.sub(r"\s+", " ", (text or "")).strip()
        t = re.sub(r"^[\-–—•*·]+\s*", "", t).strip()
        return t

    def _extract_structured_description(self, response):
        container = response.css(".ul-disc") or response.css(
            "[class*='descripcion'], [class*='description'], .hl-vacancy-description, article"
        )
        if not container:
            return None
        container = container[0]
        paragraphs = container.xpath("./p | ./li")
        if not paragraphs:
            return None

        sections = {"requirements": [], "benefits": [], "description": []}
        current = "intro"
        intro_parts = []
        found_heading = False

        for p in paragraphs:
            plain_text, parts, bold_text = self._extract_paragraph_parts(p)
            if not plain_text:
                continue
            if self._is_heading_paragraph(plain_text, bold_text, parts):
                label = bold_text or plain_text
                section = self._classify_section(label) or "description"
                current = section
                found_heading = True
                # if heading paragraph contains extra content beyond label, keep remainder
                remainder = plain_text
                if bold_text and plain_text.startswith(bold_text.strip()):
                    remainder = plain_text[len(bold_text.strip()):].strip(" :-–—")
                elif plain_text.endswith(":"):
                    remainder = ""
                if remainder:
                    parts = [remainder]
                else:
                    continue
            # route content
            if current == "intro":
                intro_parts.append(plain_text)
            elif current in {"requirements", "benefits"}:
                for part in parts:
                    item = self._to_bullet_item(part)
                    if item:
                        sections[current].append(item)
            else:  # description sections (actividades/responsabilidades/etc.)
                sections["description"].append(plain_text)

        # dedupe preserving order
        def dedupe(items):
            out = []
            seen = set()
            for it in items:
                k = it.lower()
                if k and k not in seen:
                    seen.add(k)
                    out.append(it)
            return out

        requirements = dedupe(sections["requirements"])
        benefits = dedupe(sections["benefits"])
        desc_parts = [p for p in intro_parts if p] + [p for p in sections["description"] if p]
        description = "\n\n".join(desc_parts).strip()

        if not found_heading and not requirements and not benefits:
            return None
        if not description and not requirements and not benefits:
            return None
        return {
            "descripcion": description,
            "requirements": requirements,
            "benefits": benefits,
        }

    def _split_description_text(self, text):
        raw = str(text or "").strip()
        if not raw:
            return {"descripcion": "", "requirements": [], "benefits": []}
        # Normalize line breaks for parsing
        t = raw.replace("\r\n", "\n").replace("\r", "\n")
        # Try to split on known headings
        pattern = re.compile(
            r"(?im)^(?:\s*)(requisitos|requerimientos|conocimientos deseables|conocimientos obligatorios|perfil|lo que buscamos|actividades|responsabilidades|funciones|descripción general|descripcion general|qué harás|que haras|ofrecemos|qué ofrecemos|que ofrecemos|lo que ofrecemos|beneficios|prestaciones|requirements|what we're looking for|what we are looking for|qualifications|what you'll do|what you will do|responsibilities|benefits|what we offer|we offer|why join us)\s*:?\s*$"
        )
        matches = list(pattern.finditer(t))
        if not matches:
            # inline headings fallback (same line content after heading)
            inline = re.compile(
                r"(?i)(requisitos|requerimientos|conocimientos deseables|actividades|responsabilidades|ofrecemos|qué ofrecemos|que ofrecemos|beneficios|requirements|what we're looking for|qualifications|responsibilities|benefits|what we offer)\s*:\s*"
            )
            matches = list(inline.finditer(t))
            if not matches:
                return {"descripcion": self._clean_text(t), "requirements": [], "benefits": []}

        intro = t[: matches[0].start()].strip()
        buckets = {"description": [intro] if intro else [], "requirements": [], "benefits": []}
        for i, m in enumerate(matches):
            heading = m.group(1)
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(t)
            body = t[start:end].strip()
            section = self._classify_section(heading) or "description"
            if not body:
                continue
            if section in {"requirements", "benefits"}:
                # split bullets/lines
                candidates = re.split(r"\n+|(?:\s+[•\-–—]\s+)", body)
                items = []
                for c in candidates:
                    for sub in re.split(r"\s*[•\-–—]\s+", c):
                        it = self._to_bullet_item(sub)
                        if it:
                            items.append(it)
                if not items and body:
                    items = [self._clean_text(body)]
                buckets[section].extend(items)
            else:
                buckets["description"].append(self._clean_text(body))

        def dedupe(items):
            out = []
            seen = set()
            for it in items:
                k = it.lower()
                if k and k not in seen:
                    seen.add(k)
                    out.append(it)
            return out

        return {
            "descripcion": "\n\n".join([p for p in buckets["description"] if p]).strip(),
            "requirements": dedupe([self._clean_text(x) for x in buckets["requirements"] if self._clean_text(x)]),
            "benefits": dedupe([self._clean_text(x) for x in buckets["benefits"] if self._clean_text(x)]),
        }

    def _extract_from_ld_json(self, ld):
        if not ld:
            return {}
        title = ld.get("title") or ld.get("name") or ""
        org = ld.get("hiringOrganization") or {}
        if isinstance(org, list):
            org = org[0] if org else {}
        company = org.get("name") if isinstance(org, dict) else ""

        job_location = ld.get("jobLocation")
        location_parts = []
        modality_raw = ""
        if isinstance(job_location, list):
            locations = job_location
        elif job_location:
            locations = [job_location]
        else:
            locations = []
        for loc in locations:
            if not isinstance(loc, dict):
                continue
            addr = loc.get("address") or {}
            if isinstance(addr, str):
                location_parts.append(addr)
            elif isinstance(addr, dict):
                for key in ("addressLocality", "addressRegion", "addressCountry"):
                    val = addr.get(key)
                    if isinstance(val, dict):
                        val = val.get("name")
                    if val:
                        location_parts.append(str(val))
            if not modality_raw:
                modality_raw = loc.get("name") or ""

        employment_type = ld.get("employmentType") or ld.get("jobLocationType") or ""
        if isinstance(employment_type, list):
            employment_type = " ".join(str(x) for x in employment_type)
        description = ld.get("description") or ""
        skills = ld.get("skills") or []
        if isinstance(skills, str):
            tags = [s.strip() for s in re.split(r"[,;]", skills) if s.strip()]
        elif isinstance(skills, list):
            tags = [self._clean_text(s) for s in skills if self._clean_text(s)]
        else:
            tags = []

        location_text = ", ".join([p for p in location_parts if p])
        modality_raw = modality_raw or str(employment_type) or location_text
        return {
            "titulo": self._clean_text(title),
            "empresa": self._clean_text(company),
            "modalidad_raw": self._clean_text(modality_raw),
            "ubicacion_texto": self._clean_text(location_text),
            "descripcion": self._clean_text(description),
            "tags_tecnologias": tags,
        }

    def parse_detail(self, response):
        ld = self._extract_ld_json(response)
        ld_data = self._extract_from_ld_json(ld)
        css_data = self._extract_from_css(response)
        structured = self._extract_structured_description(response)

        def pick(key, default=""):
            val = ld_data.get(key)
            if isinstance(val, list):
                if val:
                    return val
                return css_data.get(key, default)
            if val:
                return val
            return css_data.get(key, default)

        tags = ld_data.get("tags_tecnologias") or []
        if not tags:
            tags = css_data.get("tags_tecnologias") or []

        # Prefer structured HTML extraction for descripcion/requirements/benefits
        descripcion = ""
        requirements = []
        benefits = []
        if structured:
            descripcion = structured.get("descripcion") or ""
            requirements = structured.get("requirements") or []
            benefits = structured.get("benefits") or []

        if not descripcion and not (requirements or benefits):
            raw_desc = pick("descripcion", "")
            split = self._split_description_text(raw_desc)
            descripcion = split.get("descripcion") or self._clean_text(raw_desc)
            requirements = split.get("requirements") or []
            benefits = split.get("benefits") or []
        elif not descripcion:
            # if we got lists but no intro/desc, fall back to a short cleaned ld/css description
            raw_desc = pick("descripcion", "")
            descripcion = self._split_description_text(raw_desc).get("descripcion") or self._clean_text(raw_desc)

        item = {
            "titulo": pick("titulo", ""),
            "empresa": pick("empresa", ""),
            "modalidad_raw": pick("modalidad_raw", "") or pick("ubicacion_texto", ""),
            "ubicacion_texto": pick("ubicacion_texto", ""),
            "descripcion": descripcion,
            "tags_tecnologias": tags,
            "requirements": requirements,
            "benefits": benefits,
            "url_oferta": response.url.split("?")[0],
        }
        yield item
