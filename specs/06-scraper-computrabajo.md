# SPEC 06 — Scraper Computrabajo México (tercera fuente dinámica)

> **Estado:** Aprobado
> **Depende de:** SPEC 05
> **Fecha:** 2026-11-16
> **Objetivo:** Añadir `mx.computrabajo.com` como tercera fuente dinámica del scraper, generando rutas de búsqueda por `stack` y `experiencia_anos` desde `SearchQueryBuilder`, con un spider propio (`ComputrabajoSpider`) y normalización de modalidad y URL canónica en los pipelines.

## Scope

**Incluido:**

- `scraper/job_scraper/utils/query_builder.py`: soporte de `platform='computrabajo'` en `SearchQueryBuilder` (constantes `COMPUTRABAJO_BASE`, `COMPUTRABAJO_PLATFORM`, `COMPUTRABAJO_STACK_SLUGS` y `_build_computrabajo_urls()`).
- Reutilización de `should_follow_job(title, active_experience_levels)` en el listado antes de entrar al detalle.
- `scraper/job_scraper/spiders/computrabajo_spider.py` nuevo (JSON-LD `JobPosting` con fallback CSS/XPath, paginación `?p=N` con `max_pages=4`, `custom_settings` de resiliencia).
- `scraper/job_scraper/pipelines.py`: normalizar `"Desde casa"` y `"Teletrabajo"` → `'Remoto'` en `JobEnrichmentPipeline`, y canónizar `url_oferta` (quitar fragmento `#...` y query params) en `DataCleaningPipeline` para los 3 spiders.
- `scraper/run_spiders.py`: registrar `ComputrabajoSpider` en la tupla `SPIDERS`.
- Tests pytest nuevos/ampliados en `scraper/tests/`.

**Fuera de alcance (specs futuras):**

- Geocodificación con Nominatim, `cities_cache.json`, PostGIS y columna `coordenadas` (diferida desde SPEC 04; solo se extrae `ubicacion_texto` limpia).
- Campo `interests` (no existe en `user_profiles`).
- Otros portales (solo Hireline, OCCMundial y Computrabajo).
- Matching engine, % de afinidad y notificaciones Expo Push.
- Multiusuario.

## Data model

Sin cambios en la base de datos ni en `JobOfferItem`. No se añade migración. La descripción de Computrabajo se mapea al campo existente `descripcion` (no existe `descripcion_completa` en `JobOfferItem`).

Cambios en `scraper/job_scraper/utils/query_builder.py`:

```python
COMPUTRABAJO_BASE = "https://mx.computrabajo.com"
COMPUTRABAJO_PLATFORM = "computrabajo"

# Mapa de slugs canónicos (mismos valores que OCC_STACK_SLUGS) + fallback _slugify.
COMPUTRABAJO_STACK_SLUGS = {
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

Reglas de `_build_computrabajo_urls()` (orden determinista, sobre `stack` único ordenado):

1. Si hay nivel de entrada (`_entry_allowed`, mismo fail-safe que Hireline/OCC) → emitir una vez la ruta estática `trabajo-de-trainee-ti`.
2. Por cada tecnología (`slug = COMPUTRABAJO_STACK_SLUGS.get(tech.strip().lower()) or _slugify(tech)`):
   - **Siempre:** `trabajo-de-{slug}` (búsqueda base por tecnología).
   - **Si `_entry_allowed`:** `trabajo-de-practicante-{slug}`, `trabajo-de-becario-{slug}`, `trabajo-de-desarrollador-junior-{slug}`.
   - **Si `has_junior_level` (1–3):** `trabajo-de-desarrollador-{slug}`.
   - **Si `has_senior_level` (4+):** `trabajo-de-senior-{slug}`, `trabajo-de-lider-tecnico-{slug}`.

Ejemplos (stack `["Java", "Python"]`):

- `0` años → `trabajo-de-trainee-ti`, `trabajo-de-java`, `trabajo-de-practicante-java`, `trabajo-de-becario-java`, `trabajo-de-desarrollador-junior-java`, `trabajo-de-python`, `trabajo-de-practicante-python`, `trabajo-de-becario-python`, `trabajo-de-desarrollador-junior-python`.
- `2` años → `trabajo-de-java`, `trabajo-de-desarrollador-java`, `trabajo-de-python`, `trabajo-de-desarrollador-python`.
- `5` años → `trabajo-de-java`, `trabajo-de-senior-java`, `trabajo-de-lider-tecnico-java`, `trabajo-de-python`, `trabajo-de-senior-python`, `trabajo-de-lider-tecnico-python`.

## Implementation plan

Cada paso deja el scraper funcional y verificable.

1. En `scraper/job_scraper/utils/query_builder.py`, añadir `COMPUTRABAJO_BASE`, `COMPUTRABAJO_PLATFORM`, `COMPUTRABAJO_STACK_SLUGS` y `_build_computrabajo_urls()`; cablear el dispatch en `build_urls` y actualizar el mensaje de `ValueError` para mencionar `computrabajo`. Ampliar `scraper/tests/test_query_builder.py` con casos `0/2/5` y slugs. Correr `pytest`.
2. En `scraper/job_scraper/pipelines.py`, añadir `\bdesde casa\b` y `\bteletrabajo\b` a la rama `Remoto` de `_detect_modalidad`, y canónizar `url_oferta` en `DataCleaningPipeline` (quitar primero el fragmento `#...` y después los query params `?...`). Ampliar `scraper/tests/test_pipelines.py`. Correr `pytest`.
3. Crear `scraper/job_scraper/spiders/computrabajo_spider.py`: dominio `mx.computrabajo.com`, `custom_settings` (`DOWNLOAD_DELAY=3.5`, `RANDOMIZE_DOWNLOAD_DELAY=True`, `CONCURRENT_REQUESTS=2`, `RETRY_TIMES=3`, `RETRY_HTTP_CODES=[429, 500, 502, 503, 504]`), headers `Accept-Language: es-MX,es;q=0.9,en;q=0.8` y `User-Agent` de escritorio. `start_requests()` delega en `SearchQueryBuilder.build_urls('computrabajo')`. `parse()` extrae fichas `/ofertas-de-trabajo/oferta-de-trabajo-de-...`, aplica `should_follow_job(title, active_experience_levels)` antes de `parse_detail`, y pagina con `?p=N` hasta `max_pages=4`. `parse_detail()` prioriza JSON-LD `JobPosting` (`title`, `hiringOrganization.name`, `description`, `jobLocation`) y usa fallback CSS/XPath para `h1`, empresa, `ubicacion_texto`, `modalidad_raw` (`Desde casa`, `Híbrido`, `Presencial`) y descripción; normaliza empresa confidencial/importante a `"Empresa confidencial"` y emite `JobOfferItem` (mapeando la descripción a `descripcion`).
4. Registrar `ComputrabajoSpider` en la tupla `SPIDERS` de `scraper/run_spiders.py` para ejecución secuencial junto con `HirelineSpider` y `OccSpider`.
5. Añadir `scraper/tests/test_computrabajo_spider.py` con casos de JSON-LD, fallback CSS, empresa confidencial y un caso end-to-end que valide `"Desde casa"` → `'Remoto'` y `url_oferta` sin `#...` ni query params. Correr `pytest` completo.

## Acceptance criteria

- [ ] `pytest` dentro de `scraper/` termina en verde (incluye los casos nuevos).
- [ ] `SearchQueryBuilder.build_urls('computrabajo')` genera las URLs correctas para perfiles de `0`, `2` y `5` años (base siempre + rutas de rango).
- [ ] `should_follow_job` se reutiliza en el listado de Computrabajo antes de descargar cada ficha.
- [ ] `"Desde casa"` y `"Teletrabajo"` se normalizan a `'Remoto'`.
- [ ] `url_oferta` queda sin fragmento `#...` y sin query params tras `DataCleaningPipeline`.
- [ ] `"Importante empresa del sector"` (o confidencial) se normaliza a `"Empresa confidencial"`.
- [ ] `computrabajo_spider.py` extrae vía JSON-LD `JobPosting` con fallback CSS/XPath.
- [ ] `run_spiders.py` ejecuta `HirelineSpider`, `OccSpider` y `ComputrabajoSpider` secuencialmente.
- [ ] No se introduce migración ni código de geocodificación.

## Decisions

- **Sí:** diferir geocodificación/PostGIS/`cities_cache.json` (consistente con SPEC 04/05). Solo se extrae `ubicacion_texto` limpia.
- **Sí:** centralizar la canónización de `url_oferta` (fragmento + query) en `DataCleaningPipeline`. **No:** limpiarla solo en el spider de Computrabajo.
- **Sí:** `COMPUTRABAJO_STACK_SLUGS` + fallback `_slugify`. **No:** solo `_slugify` (rompería `C#`, `.NET`, `Node.js`, etc.).
- **Sí:** generar siempre `trabajo-de-{slug}` por tecnología. **No:** limitarla al rango 1–3 (perdería cobertura para perfiles solo senior).
- **Sí:** mapear la descripción de Computrabajo al campo existente `descripcion` (no existe `descripcion_completa` en `JobOfferItem`).
- **Sí:** `trabajo-de-trainee-ti` como ruta estática única (sin slug), emitida cuando hay nivel de entrada.
- **Sí:** reutilizar `_entry_allowed` como flag de entrada (fail-safe idéntico al de Hireline/OCC).
- **Sí:** `modalidad_raw` de Computrabajo se extrae del DOM; el JSON-LD no expone la modalidad de forma fiable.
- **No:** modificar `.github/workflows/daily_scrape.yml` (ejecuta `python run_spiders.py`, único punto de entrada).

## Risks

| Riesgo                                                      | Mitigación                                                                                                                |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Computrabajo cambia su HTML o el JSON-LD                    | Prioridad JSON-LD + fallback CSS/XPath; selectores aislados en `computrabajo_spider.py`.                                  |
| Rate-limit / bloqueo en Computrabajo                        | `DOWNLOAD_DELAY=3.5`, `RANDOMIZE_DOWNLOAD_DELAY`, `CONCURRENT_REQUESTS=2`, `RETRY_TIMES=3` (`[429, 500, 502, 503, 504]`). |
| `ROBOTSTXT_OBEY=True` global podría bloquear a Computrabajo | Revisar `robots.txt` de `mx.computrabajo.com` antes de producción.                                                        |
| Slugs de Computrabajo sin verificar en vivo                 | `COMPUTRABAJO_STACK_SLUGS` ajustable + fallback `_slugify`.                                                               |
| `user_profiles.stack` vacío                                 | Fail-safe: solo `trabajo-de-trainee-ti`.                                                                                  |

## Qué **no** está en esta spec

- Geocodificación, PostGIS, `cities_cache.json` y `coordenadas`.
- Campo `interests`.
- Otras fuentes de empleo.
- Matching engine, % de afinidad y notificaciones push.
- Multiusuario.

Cada uno de esos, si llega, va en su propia spec.
