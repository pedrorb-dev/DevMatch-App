import re
import unicodedata
from datetime import datetime, timedelta, timezone

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from supabase import create_client

from job_scraper.utils import sectionizer


def _strip_accents(text):
    normalized = unicodedata.normalize("NFD", text or "")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _normalize_text(text):
    return re.sub(r"\s+", " ", _strip_accents(str(text or "")).lower()).strip()


class DataCleaningPipeline:
    def _clean_string(self, value):
        if value is None:
            return ""
        if isinstance(value, (list, tuple)):
            value = " ".join(str(v) for v in value if v is not None)
        # Remove tags if any HTML slipped through and collapse whitespace
        text = re.sub(r"<[^>]+>", " ", str(value))
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _canonical_url(self, value):
        text = self._clean_string(value)
        # Primero el fragmento: puede contener `?` o `#` extra.
        text = text.split("#", 1)[0]
        text = text.split("?", 1)[0]
        return text.strip()

    def _clean_list(self, value):
        if value is None:
            return []
        if isinstance(value, str):
            items = re.split(r"\n+|[•]", value)
        elif isinstance(value, (list, tuple)):
            items = list(value)
        else:
            items = [value]
        cleaned = []
        seen = set()
        for item in items:
            text = self._clean_string(item)
            text = re.sub(r"^[\-–—*·]+\s*", "", text).strip()
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(text)
        return cleaned

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        for field in ["titulo", "empresa", "modalidad_raw", "ubicacion_texto", "descripcion"]:
            adapter[field] = self._clean_string(adapter.get(field))

        adapter["url_oferta"] = self._canonical_url(adapter.get("url_oferta"))

        tags = adapter.get("tags_tecnologias") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in re.split(r"[,;/|]", tags) if t.strip()]
        cleaned_tags = []
        seen = set()
        for tag in tags:
            tag_clean = self._clean_string(tag)
            if tag_clean and tag_clean.lower() not in seen:
                seen.add(tag_clean.lower())
                cleaned_tags.append(tag_clean)
        adapter["tags_tecnologias"] = cleaned_tags

        adapter["requirements"] = self._clean_list(adapter.get("requirements"))
        adapter["benefits"] = self._clean_list(adapter.get("benefits"))

        if not adapter.get("titulo") or not adapter.get("url_oferta"):
            raise DropItem("Missing required field: titulo or url_oferta")

        return item


class JobEnrichmentPipeline:
    STACK_KEYWORDS = {
        "spring boot": "Spring Boot",
        "springboot": "Spring Boot",
        "spring": "Spring Boot",
        "angular": "Angular",
        "react": "React",
        "vue": "Vue",
        "java": "Java",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "python": "Python",
        "sql": "SQL",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "node": "Node.js",
        "nodejs": "Node.js",
        "node.js": "Node.js",
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI",
        ".net": ".NET",
        "dotnet": ".NET",
        "c#": "C#",
        "php": "PHP",
        "laravel": "Laravel",
        "ruby": "Ruby",
        "rails": "Ruby on Rails",
        "go": "Go",
        "golang": "Go",
        "git": "Git",
        "linux": "Linux",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "graphql": "GraphQL",
        "rest": "REST",
    }

    # Pre-filtro por título/descripción; el texto se normaliza (minúsculas, sin acentos).
    ENTRY_LEVEL_PATTERNS = [
        r"\bsin experiencia\b",
        r"\bno experience\b",
        r"\bbecari[oa]s?\b",
        r"\bpracticantes?\b",
        r"\btrainees?\b",
        r"\bintern(?:ship)?s?\b",
        r"\bestadias?\b",
    ]

    SENIOR_PATTERNS = [
        r"\bsenior\b",
        r"\bsr\b\.?",
        r"\blead\b",
    ]

    STACK_PATTERNS = [
        (r"\bspring\s*boot\b", "Spring Boot"),
        (r"\bangular(?:js)?\b", "Angular"),
        (r"\btypescript\b", "TypeScript"),
        (r"\bjavascript\b", "JavaScript"),
        (r"\bnode\.?\s?js\b", "Node.js"),
        (r"\bpostgres(?:ql)?\b", "PostgreSQL"),
        (r"\bmysql\b", "MySQL"),
        (r"\bmongodb\b", "MongoDB"),
        (r"\bkubernetes\b|\bk8s\b", "Kubernetes"),
        (r"\bdocker\b", "Docker"),
        (r"\bgraphql\b", "GraphQL"),
        (r"\bfastapi\b", "FastAPI"),
        (r"\bdjango\b", "Django"),
        (r"\bflask\b", "Flask"),
        (r"\blaravel\b", "Laravel"),
        (r"\breact(?:js)?\b", "React"),
        (r"\bpython\b", "Python"),
        (r"\bjava\b", "Java"),
        (r"\bsql\b", "SQL"),
        (r"\baws\b", "AWS"),
        (r"\bgcp\b|\bgoogle cloud\b", "GCP"),
        (r"\bgit\b", "Git"),
        (r"\.net\b|\bdotnet\b", ".NET"),
        (r"\bc#", "C#"),
        (r"\bphp\b", "PHP"),
        (r"\bruby\b", "Ruby"),
        (r"\bgolang\b|\bgo\b", "Go"),
        (r"\bvue(?:\.js)?\b", "Vue"),
    ]

    def _detect_modalidad(self, adapter):
        text = _normalize_text(
            " ".join(
                [
                    str(adapter.get("modalidad_raw") or ""),
                    str(adapter.get("ubicacion_texto") or ""),
                    str(adapter.get("descripcion") or ""),
                ]
            )
        )
        # Check híbrido/hybrid before remoto in case of mixed strings, but signals are explicit
        if re.search(r"\bhibrido\b|\bhibrid\b|\bhybrid\b", text):
            return "Híbrido"
        if re.search(r"\bremoto\b|\bremote\b|\btelecommute\b|\btelework\b|\bdesde casa\b|\bteletrabajo\b", text):
            return "Remoto"
        if re.search(r"\bpresencial\b|\bon[- ]?site\b|\bonsite\b", text):
            return "Presencial"
        return "Presencial"

    def _canonicalize_stack_token(self, token):
        norm = _normalize_text(token)
        norm_compact = norm.replace(".", "").replace("#", " sharp").strip()
        # direct map
        for key, canonical in self.STACK_KEYWORDS.items():
            key_norm = _normalize_text(key)
            if norm == key_norm or norm_compact == _normalize_text(key.replace(".", "")):
                return canonical
        # contains-based fallbacks for common variants
        if "spring" in norm and "boot" in norm:
            return "Spring Boot"
        if norm in {"js", "javascript"}:
            return "JavaScript"
        if norm in {"ts", "typescript"}:
            return "TypeScript"
        if norm == "nodejs":
            return "Node.js"
        # Title-case reasonable default for unknown tags
        return token.strip()

    def _detect_stack(self, adapter):
        found = {}
        tags = adapter.get("tags_tecnologias") or []
        for tag in tags:
            canon = self._canonicalize_stack_token(tag)
            if canon:
                key = canon.lower()
                if key not in found:
                    found[key] = canon

        haystack = _normalize_text(f"{adapter.get('titulo') or ''} {adapter.get('descripcion') or ''}")
        # keyword matching over title+description, with word boundaries so that
        # e.g. "Java" does not match "JavaScript" and "SQL" does not match "PostgreSQL"
        for pattern, canonical in self.STACK_PATTERNS:
            if not re.search(pattern, haystack):
                continue
            key = canonical.lower()
            if key not in found:
                found[key] = canonical

        return list(found.values())

    def _detect_experiencia_minima(self, adapter):
        text = _normalize_text(f"{adapter.get('titulo') or ''} {adapter.get('descripcion') or ''}")

        # 1. Años explícitos: "3 años", "2+ years", "1 a 3 años" (se toma el mínimo del rango)
        rango = re.search(r"(\d{1,2})\s*(?:-|a|to)\s*(\d{1,2})\s*(?:anos|anios|ano|years?|yrs?)", text)
        if rango:
            return min(int(rango.group(1)), int(rango.group(2)))
        explicito = re.search(r"(\d{1,2})\s*\+?\s*(?:anos|anios|ano|years?|yrs?)", text)
        if explicito:
            return int(explicito.group(1))

        # 2. Indicador de entrada
        for pattern in self.ENTRY_LEVEL_PATTERNS:
            if re.search(pattern, text):
                return 0

        # 3. Indicador senior sin número
        for pattern in self.SENIOR_PATTERNS:
            if re.search(pattern, text):
                return 4

        # 4. Sin mención
        return 1

    def _is_mostly_english(self, text):
        sample = str(text or "")
        if len(sample) < 40:
            # short texts: rely on common english words
            words = re.findall(r"[a-zA-Z]+", _normalize_text(sample))
        else:
            words = re.findall(r"[a-zA-Z]+", sample.lower())
        if not words:
            return False
        english_common = {
            "the", "and", "with", "you", "for", "our", "are", "will", "experience", "team",
            "work", "knowledge", "skills", "development", "software", "engineer", "developer",
            "we", "in", "to", "of", "on", "as", "or", "be", "is", "at", "an", "this",
            "that", "from", "requirements", "responsibilities", "benefits", "about", "role",
            "looking", "years", "ability", "working", "position", "company", "job",
        }
        hits = sum(1 for w in words if w in english_common)
        # also consider absence of common spanish markers
        spanish_markers = re.findall(r"\b(de|la|el|y|en|con|para|que|los|las|del|experiencia|conocimientos|requisitos|responsabilidades|empresa|puesto)\b", _normalize_text(sample))
        if len(words) >= 30:
            return hits >= max(5, len(words) * 0.08) and len(spanish_markers) <= hits
        return hits >= 4 and len(spanish_markers) == 0

    def _detect_nivel_ingles(self, adapter):
        text = _normalize_text(f"{adapter.get('titulo') or ''} {adapter.get('descripcion') or ''}")
        # C1 / bilingual / native
        if re.search(r"\bbilingual\b|\bnativo\b|\bnative\b|\bc1\b", text):
            return "C1"
        # B2 / advanced / fluent
        if re.search(r"\bavanzado\b|\badvanced\b|\bfluent\b|\bfluido\b", text):
            return "B2"
        # B1 / intermediate / conversational / requisito explícito de inglés
        if re.search(
            r"\bintermedio\b|\bintermediate\b|\bconversational\b|\bconversacional\b"
            r"|\benglish required\b|\bingles requerido\b",
            text,
        ):
            return "B1"

        descripcion = str(adapter.get("descripcion") or "")
        if descripcion and self._is_mostly_english(descripcion):
            return "B1"
        return "No especificado"

    def _normalize_string_list(self, values):
        if not values:
            return []
        if isinstance(values, str):
            values = [values]
        cleaned = []
        seen = set()
        for v in values:
            if v is None:
                continue
            text = re.sub(r"<[^>]+>", " ", str(v))
            text = re.sub(r"\s+", " ", text).strip()
            text = re.sub(r"^[\-–—*·]+\s*", "", text).strip()
            if not text:
                continue
            key = _normalize_text(text)
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(text)
        return cleaned

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        adapter["modalidad"] = self._detect_modalidad(adapter)
        adapter["stack_detectado"] = self._detect_stack(adapter)
        adapter["experiencia_minima"] = self._detect_experiencia_minima(adapter)
        adapter["nivel_ingles"] = self._detect_nivel_ingles(adapter)

        requirements = self._normalize_string_list(adapter.get("requirements") or [])
        benefits = self._normalize_string_list(adapter.get("benefits") or [])
        descripcion = str(adapter.get("descripcion") or "").strip()

        if (not requirements and not benefits) and descripcion:
            split = sectionizer.split_sections(descripcion)
            if split.get("requirements") or split.get("benefits"):
                requirements = split.get("requirements") or []
                benefits = split.get("benefits") or []
                descripcion = split.get("descripcion") or descripcion

        adapter["requirements"] = requirements
        adapter["benefits"] = benefits
        adapter["descripcion"] = descripcion
        return item


class SupabaseUpsertPipeline:
    def __init__(self, supabase_url, supabase_key):
        self.supabase_url = (supabase_url or "").strip()
        self.supabase_key = (supabase_key or "").strip()
        self.client = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            supabase_url=crawler.settings.get("SUPABASE_URL"),
            supabase_key=crawler.settings.get("SUPABASE_SERVICE_ROLE_KEY"),
        )

    def open_spider(self, spider):
        if not self.supabase_url or not self.supabase_key:
            spider.logger.warning("SupabaseUpsertPipeline disabled: missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY.")
            self.client = None
            return
        self.client = create_client(self.supabase_url, self.supabase_key)
        spider.logger.info("SupabaseUpsertPipeline connected.")

    @staticmethod
    def _coerce_experiencia_minima(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 1

    def process_item(self, item, spider):
        if not self.client:
            return item
        adapter = ItemAdapter(item)
        payload = {
            "titulo": adapter.get("titulo") or "",
            "empresa": adapter.get("empresa") or "",
            "modalidad": adapter.get("modalidad") or "Presencial",
            "descripcion": adapter.get("descripcion") or "",
            "requirements": adapter.get("requirements") or [],
            "benefits": adapter.get("benefits") or [],
            "stack_detectado": adapter.get("stack_detectado") or [],
            "nivel_ingles": adapter.get("nivel_ingles") or "No especificado",
            "experiencia_minima": self._coerce_experiencia_minima(adapter.get("experiencia_minima")),
            "ubicacion_texto": adapter.get("ubicacion_texto") or "",
            "url_oferta": adapter.get("url_oferta") or "",
        }
        try:
            self.client.table("vacantes").upsert(payload, on_conflict="url_oferta").execute()
        except Exception as exc:
            spider.logger.error("Failed to upsert vacante '%s': %s", payload.get("url_oferta"), exc)
        return item

    def close_spider(self, spider):
        if not self.client:
            return
        try:
            # Exclude vacantes referenced by saved_jobs
            saved_resp = self.client.table("saved_jobs").select("job_id").execute()
            saved_rows = getattr(saved_resp, "data", None) or []
            saved_ids = [row.get("job_id") for row in saved_rows if isinstance(row, dict) and row.get("job_id")]

            cutoff = (datetime.now(timezone.utc) - timedelta(days=15)).isoformat()

            if saved_ids:
                # Delete old vacantes not in saved_jobs. Chunk to avoid very large filters.
                # Fetch candidates and delete by id to be safe across postgrest versions.
                old_resp = (
                    self.client.table("vacantes")
                    .select("job_id, created_at")
                    .lt("created_at", cutoff)
                    .execute()
                )
                old_rows = getattr(old_resp, "data", None) or []
                to_delete = [
                    row.get("job_id")
                    for row in old_rows
                    if isinstance(row, dict) and row.get("job_id") and row.get("job_id") not in set(saved_ids)
                ]
                for job_id in to_delete:
                    self.client.table("vacantes").delete().eq("job_id", job_id).execute()
                spider.logger.info("Purged %d old vacantes (kept saved).", len(to_delete))
            else:
                self.client.table("vacantes").delete().lt("created_at", cutoff).execute()
                spider.logger.info("Purged old vacantes older than 15 days (no saved jobs).")
        except Exception as exc:
            spider.logger.error("Failed to purge old vacantes: %s", exc)
