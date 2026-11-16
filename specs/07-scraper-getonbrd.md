# SPEC 07 — Scraper Get on Board (cuarta fuente dinámica)

> **Estado:** Aprobado
> **Depende de:** SPEC 05, SPEC 06
> **Fecha:** 2026-11-16
> **Objetivo:** Añadir `getonbrd.com` como cuarta fuente dinámica del scraper, generando búsquedas por tecnología (`jobs-{slug}`) desde `SearchQueryBuilder` y con un spider propio (`GetOnBrdSpider`) que extrae vía microdata schema.org y descarta en ficha las ofertas no elegibles para México/Remoto antes de emitir `JobOfferItem`.

## Scope

**Incluido:**

- `scraper/job_scraper/utils/query_builder.py`: soporte de `platform='getonbrd'` en `SearchQueryBuilder` (constantes `GETONBRD_BASE`, `GETONBRD_PLATFORM`, `GETONBRD_STACK_SLUGS` y `_build_getonbrd_urls()`).
- Reutilización de `should_follow_job(title, active_experience_levels)` en el listado antes de descargar cada ficha.
- `scraper/job_scraper/spiders/getonbrd_spider.py` nuevo (extracción por microdata `itemprop` con fallback CSS/XPath, filtro de elegibilidad México/Remoto en ficha, paginación `?page=N` con `max_pages=4`, `custom_settings` de resiliencia).
- `scraper/job_scraper/pipelines.py`: mapear `"English required"` / `"Inglés requerido"` → `'B1'` en `JobEnrichmentPipeline._detect_nivel_ingles` (única adición; las variantes `remote`/`telecommute`/`remoto` ya están cubiertas por `_detect_modalidad`).
- `scraper/run_spiders.py`: registrar `GetOnBrdSpider` en la tupla `SPIDERS`.
- Tests pytest nuevos/ampliados en `scraper/tests/`.

**Fuera de alcance (specs futuras):**

- Geocodificación, Nominatim, `cities_cache.json`, PostGIS y columna `coordenadas` (diferida desde SPEC 04; va en una spec futura). Las vacantes remotas quedan con `coordenadas` NULL porque el scraper nunca escribe ese campo.
- Filtro de seniority por URL (`?seniority=`, `empleos/sin-experiencia`): descartado (rutas rotas/no verificadas); el seniority fino lo hace `should_follow_job` y la detección de `experiencia_minima` del pipeline.
- Campo `interests` (no existe en `user_profiles`).
- Otros portales.
- Matching engine, % de afinidad y notificaciones Expo Push.
- Multiusuario.

## Data model

Sin cambios en la base de datos ni en `JobOfferItem`. No se añade migración. La descripción de Get on Board se mapea al campo existente `descripcion` (no existe `descripcion_completa` en `JobOfferItem`).

Cambios en `scraper/job_scraper/utils/query_builder.py`:

```python
GETONBRD_BASE = "https://www.getonbrd.com"
GETONBRD_PLATFORM = "getonbrd"

# Mismos slugs canónicos que OCC_STACK_SLUGS / COMPUTRABAJO_STACK_SLUGS; el resto
# se resuelve con _slugify.
GETONBRD_STACK_SLUGS = {
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
```

Reglas de `_build_getonbrd_urls()` (determinista, sobre el `stack` único ordenado):

1. Por cada tecnología activa, obtener `slug = GETONBRD_STACK_SLUGS.get(tech.strip().lower()) or _slugify(tech)` y emitir **una** ruta `{GETONBRD_BASE}/jobs-{slug}`.
2. **No** se diferencia por `experiencia_anos`: perfiles con `0`, `2` y `5` años generan las mismas URLs por tecnología. El filtro fino de seniority lo hace `should_follow_job` y `JobEnrichmentPipeline` detecta `experiencia_minima`.
3. Solo se usa el prefijo inglés (`jobs-`) para evitar duplicar el mismo job bajo los prefijos `/jobs/...` y `/empleos/...`.
4. Con `stack` vacío no se generan URLs (fail-safe).

### Extracción por microdata (Get on Board no usa JSON-LD `<script>`)

La ficha usa microdata `itemscope`/`itemprop` (`http://schema.org/JobPosting`). Prioridad 1: microdata; Prioridad 2: fallback CSS/XPath.

| Fuente (microdata `itemprop` / DOM)                                           | Campo del item             |
| ----------------------------------------------------------------------------- | -------------------------- |
| `title`                                                                       | `titulo`                   |
| `hiringOrganization` → `name`                                                 | `empresa`                  |
| `description` (`div#job-body`)                                                | `descripcion` (sin HTML)   |
| `jobLocationType` (`TELECOMMUTE`)                                             | `modalidad_raw` (remoto)   |
| `jobLocation` → `address` → `addressLocality`, `addressCountry`               | `ubicacion_texto`          |
| `applicantLocationRequirements` → `Country` → `name` (puede haber varios)     | países del remoto (filtro) |
| `skills` (tags en DOM)                                                        | `tags_tecnologias`         |
| `qualifications` / span de modalidad en DOM (`Remote`, `Hybrid`, `In-office`) | `modalidad_raw` (fallback) |

### Filtro de elegibilidad México/Remoto (solo en ficha, fail-safe)

```python
def _is_eligible(job_location_type, applicant_countries, address_country):
    if job_location_type == "TELECOMMUTE":            # remoto
        if not applicant_countries:                    # "Remote" sin restricción → conservar
            return True
        if len(applicant_countries) == 1 and not _is_mexico(applicant_countries[0]):
            return False                               # "Remote (Chile)" / "Remote (US)" → descartar
        return True                                    # México, múltiple/LATAM → conservar
    # presencial / híbrido
    if not address_country:                            # fail-safe
        return True
    if _is_mexico(address_country):                    # MX → conservar
        return True
    if _is_known_foreign(address_country):             # CL, CO, US, ... → descartar
        return False
    return True                                        # desconocido → fail-safe conservar
```

- `_is_mexico`: normaliza a minúsculas y sin acentos, y compara contra `{"mx", "mexico"}`.
- `_is_known_foreign`: conjunto extensible de códigos ISO y nombres normalizados de países distintos de México (LATAM y otros frecuentes), por ejemplo `cl/chile`, `co/colombia`, `ar/argentina`, `pe/peru`, `uy/uruguay`, `br/brasil/brazil`, `ec/ecuador`, `ve/venezuela`, `py/paraguay`, `bo/bolivia`, `sv/el salvador`, `gt/guatemala`, `hn/honduras`, `ni/nicaragua`, `cr/costa rica`, `pa/panama`, `do/republica dominicana/dominican republic`, `cu/cuba`, `us/usa/united states/estados unidos`, `ca/canada`, `es/spain/espana`, `pt/portugal`, `gb/uk/united kingdom`.

## Implementation plan

Cada paso deja el scraper funcional y verificable.

1. En `scraper/job_scraper/utils/query_builder.py`, añadir `GETONBRD_BASE`, `GETONBRD_PLATFORM`, `GETONBRD_STACK_SLUGS` y `_build_getonbrd_urls()`; cablear el dispatch en `build_urls` y actualizar el mensaje de `ValueError` para mencionar `getonbrd`. Ampliar `scraper/tests/test_query_builder.py` con casos para `0`, `2` y `5` años (mismas URLs por tecnología), slugs canónicos (`C#`→`c-sharp`, `.NET`→`dotnet`, `Node.js`→`node-js`), fallback `_slugify` y stack vacío. Correr `pytest`.
2. En `scraper/job_scraper/pipelines.py`, añadir detección de `\benglish required\b` y `\bingles requerido\b` en la rama `B1` de `_detect_nivel_ingles` (sin romper precedencias existentes de `B2`/`C1`). Ampliar `scraper/tests/test_pipelines.py`. Correr `pytest`.
3. Crear `scraper/job_scraper/spiders/getonbrd_spider.py`: dominio `getonbrd.com`, `max_pages=4`, `custom_settings` (`DOWNLOAD_DELAY=2.5`, `RANDOMIZE_DOWNLOAD_DELAY=True`, `CONCURRENT_REQUESTS=2`, `CONCURRENT_REQUESTS_PER_DOMAIN=2`, `RETRY_TIMES=3`, `RETRY_HTTP_CODES=[429, 500, 502, 503, 504]`, headers `Accept-Language: es-MX,es;q=0.9,en;q=0.8` y `User-Agent` de escritorio). `start_requests()` delega en `SearchQueryBuilder.build_urls("getonbrd")`. `parse()` extrae enlaces de detalle desde `a.results-item` (título + URL), aplica `should_follow_job(title, active_experience_levels)` antes de `parse_detail`, evita duplicados con `_seen_detail_urls`, y pagina con `?page=N` hasta `max_pages=4` deteniéndose si no hay fichas nuevas. `parse_detail()` prioriza `_extract_from_microdata` y usa fallback CSS/XPath; aplica `_is_eligible`; emite `JobOfferItem` mapeando la descripción a `descripcion` y limpiando `url_oferta` (fragmento `#...` y query params de rastreo).
4. Registrar `GetOnBrdSpider` en la tupla `SPIDERS` de `scraper/run_spiders.py` para ejecución secuencial junto con `HirelineSpider`, `OccSpider` y `ComputrabajoSpider`.
5. Añadir `scraper/tests/test_getonbrd_spider.py` con casos de microdata: remoto México (conservar), remoto Chile (descartar), remoto US (descartar), remoto multi-país/LATAM (conservar), remoto sin restricción (conservar), presencial `CL` (descartar), presencial `MX` (conservar), híbrido `MX` (conservar), presencial sin país (fail-safe conservar), fallback CSS/XPath y `url_oferta` sin `#...` ni query params de rastreo. Correr `pytest` completo.

## Acceptance criteria

- [ ] `pytest` dentro de `scraper/` termina en verde (incluye los casos nuevos).
- [ ] `SearchQueryBuilder.build_urls("getonbrd")` genera `https://www.getonbrd.com/jobs-{slug}` por tecnología, y es idéntico para perfiles de `0`, `2` y `5` años.
- [ ] Slugs canónicos correctos (`C#`→`c-sharp`, `.NET`→`dotnet`, `Node.js`→`node-js`) y fallback `_slugify` para tecnologías no mapeadas.
- [ ] `should_follow_job` se reutiliza en el listado de Get on Board antes de descargar cada ficha.
- [ ] `"English required"` y `"Inglés requerido"` se normalizan a `'B1'`.
- [ ] `scraper/job_scraper/spiders/getonbrd_spider.py` extrae vía microdata `itemprop` con fallback CSS/XPath.
- [ ] El filtro descarta "Remote (Chile)", "Remote (US)" y presencial/híbrido fuera de México, y conserva "Remote (Mexico)", "Remote" sin restricción, remoto multi-país/LATAM y presencial/híbrido en `MX`.
- [ ] `url_oferta` queda sin fragmento `#...` ni query params de rastreo tras `DataCleaningPipeline`.
- [ ] `scraper/run_spiders.py` ejecuta `HirelineSpider`, `OccSpider`, `ComputrabajoSpider` y `GetOnBrdSpider` secuencialmente.
- [ ] No se introduce migración ni código de geocodificación.

## Decisions

- **Sí:** usar solo `jobs-{slug}` por tecnología, sin diferenciar por `experiencia_anos`. **No:** rutas de seniority por URL (`?seniority=`, `empleos/sin-experiencia`), porque `empleos/sin-experiencia` devuelve 404, `?seniority=` no está verificado y el doble prefijo `/jobs/`–`/empleos/` duplicaría fichas.
- **Sí:** extraer por microdata `itemprop` (`itemscope` schema.org). **No:** JSON-LD `<script type="application/ld+json">`, que Get on Board no expone en las fichas verificadas.
- **Sí:** aplicar el filtro geográfico autoritativo solo en ficha, usando microdata (`jobLocationType`, `applicantLocationRequirements`, `addressCountry`). **No:** pre-filtro en listado.
- **Sí:** fail-safe: presencial/híbrido sin país detectable y remoto sin `applicantLocationRequirements` se conservan.
- **Sí:** descartar remoto restringido a un solo país distinto de México; conservar remoto México, remoto multi-país/LATAM y remoto sin restricción.
- **Sí:** mapear `"English required"` / `"Inglés requerido"` → `'B1'`. **No:** inferir niveles mayores sin mención explícita (las menciones explícitas de `B2`/`C1` mantienen prioridad).
- **Sí:** mapear la descripción al campo existente `descripcion`. **No:** crear `descripcion_completa`.
- **Sí:** `GETONBRD_STACK_SLUGS` con los mismos valores canónicos que OCC/Computrabajo + fallback `_slugify`.
- **No:** modificar `.github/workflows/daily_scrape.yml` (ejecuta `python run_spiders.py` como único punto de entrada).
- **No:** geocodificación/`coordenadas` en esta spec (va en una spec futura).

## Risks

| Riesgo                                                      | Mitigación                                                                                                                                                    |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Get on Board cambia microdata o el HTML de ficha/listado    | Prioridad microdata + fallback CSS/XPath; selectores y parsing aislados en `scraper/job_scraper/spiders/getonbrd_spider.py`.                                  |
| Rate-limit / bloqueo                                        | `DOWNLOAD_DELAY=2.5`, `RANDOMIZE_DOWNLOAD_DELAY`, `CONCURRENT_REQUESTS=2`, `CONCURRENT_REQUESTS_PER_DOMAIN=2`, `RETRY_TIMES=3` (`[429, 500, 502, 503, 504]`). |
| `ROBOTSTXT_OBEY=True` global podría bloquear a Get on Board | Revisar `robots.txt` de `www.getonbrd.com` antes de producción.                                                                                               |
| Paginación `?page=N` no verificada en vivo                  | Limitar a `max_pages=4` y detener si no aparecen fichas nuevas (`_seen_detail_urls`).                                                                         |
| Slugs de tecnología sin verificar en vivo                   | `GETONBRD_STACK_SLUGS` ajustable + fallback `_slugify`.                                                                                                       |
| Duplicados por prefijo `/jobs/` vs `/empleos/`              | Se rastrea solo `jobs-{slug}` + `_seen_detail_urls` + upsert por `url_oferta` en `SupabaseUpsertPipeline`.                                                    |
| `user_profiles.stack` vacío                                 | Fail-safe: `build_urls("getonbrd")` devuelve `[]` y el spider no rastrea nada.                                                                                |

## Qué **no** está en esta spec

- Geocodificación, PostGIS, `cities_cache.json` y `coordenadas`.
- Filtro de seniority por URL (`?seniority=`, `empleos/sin-experiencia`).
- Campo `interests`.
- Otras fuentes de empleo.
- Matching engine, % de afinidad y notificaciones push.
- Multiusuario.

Cada uno de esos, si llega, va en su propia spec.
