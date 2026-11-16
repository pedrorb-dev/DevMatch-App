# SPEC 05 — Scraper dinámico multi-fuente (Hireline + OCCMundial)

> **Estado:** Aprobado
> **Depende de:** SPEC 02, SPEC 04
> **Fecha:** 2026-11-16
> **Objetivo:** Hacer 100 % dinámico el spider de Hireline y añadir OCCMundial como segunda fuente, generando las rutas de búsqueda desde `user_profiles` (`stack` y `experiencia_anos`), pre-filtrando por seniority con `should_follow_job` y sustituyendo `es_practicante` por el entero `experiencia_minima` en item, pipeline y tabla `vacantes`.

## Scope

**Incluido:**

- `scraper/job_scraper/utils/query_builder.py` nuevo con `SearchQueryBuilder` para `platform='hireline'` y `platform='occ'`.
- `SearchQueryBuilder.build_urls(platform)` que consulta `user_profiles` para obtener el `stack` único y los `experiencia_anos` activos, y genera URLs por rango (0 / 1-3 / 4+).
- `should_follow_job(title, active_experience_levels) -> bool` para pre-filtrar por título antes de descargar la ficha.
- `items.py`: sustituir `es_practicante` (bool) por `experiencia_minima` (int).
- `pipelines.py`: `_detect_experiencia_minima` bilingüe, `TELECOMMUTE` → `Remoto`, detección de stack con límites `\b`, y payload con `experiencia_minima`.
- Migración `supabase/migrations/0003_experiencia_minima.sql` que reemplaza `es_practicante` por `experiencia_minima` con backfill.
- Ajuste mínimo en la app: `src/features/jobs/infrastructure/mappers/JobMapper.ts`.
- Refactor de `spiders/hireline_spider.py` para delegar en `SearchQueryBuilder` y validar con `should_follow_job`.
- `spiders/occ_spider.py` nuevo.
- `run_spiders.py` con `CrawlerProcess` para correr ambos spiders secuencialmente.
- `.github/workflows/daily_scrape.yml` actualizado a `python run_spiders.py`.
- Suite de tests pytest nueva.

**Fuera de alcance (specs futuras):**

- Campo `interests` (no existe en `user_profiles`; se usa solo `stack`).
- Renombrar `experiencia_anos` a `experience_years`.
- Geocodificación con Nominatim, PostGIS y la columna `coordenadas` (diferida desde SPEC 04).
- Otros portales (solo Hireline y OCCMundial).
- Matching engine, % de afinidad y notificaciones Expo Push.
- Multiusuario.

## Data model

Cambios en `JobOfferItem` (`scraper/job_scraper/items.py`):

```python
# se elimina
es_practicante = scrapy.Field()  # bool

# se añade
experiencia_minima = scrapy.Field()  # int (0, 1, 2, 4, ...)
```

Migración `0003`:

```sql
alter table public.vacantes
  add column experiencia_minima integer not null default 1;

update public.vacantes
  set experiencia_minima = 0
  where es_practicante = true;

alter table public.vacantes
  drop column es_practicante;
```

- El resto de columnas no cambia. `created_at` lo sigue poniendo la BD (`now()`).
- `0002_seed_vacantes.sql` no se edita (historia de migraciones inmutable); `0003` hace el backfill.

Reglas de `experiencia_minima` en `JobEnrichmentPipeline` (bilingüe, por precedencia):

1. Patrón explícito `(\d+)\+?\s*(años|years|yrs)` → el entero (mínimo del rango).
2. Indicador de entrada (`sin experiencia`, `no experience`, `becario`, `practicante`, `trainee`, `intern`, `estadías`) → `0`.
3. Indicador senior (`senior`, `sr.`, `lead` sin número) → `4`.
4. Sin mención → `1`.

Mapeo OCC en `parse_detail` (los nombres de la derecha son campos reales de `JobOfferItem`):

| Fuente (JSON-LD / DOM)                                        | Campo del item                      |
| ------------------------------------------------------------- | ----------------------------------- |
| `title`                                                       | `titulo`                            |
| `hiringOrganization.name` (fallback `"Empresa confidencial"`) | `empresa`                           |
| `description` (sin HTML)                                      | `descripcion`                       |
| `jobLocationType` + `jobLocation.address`                     | `modalidad_raw` + `ubicacion_texto` |

Ajuste mínimo en la app (la entidad `JobOffer` y la UI no cambian):

```ts
// JobMapper.ts
experiencia_minima: number;                           // (antes es_practicante: boolean)
isPracticante: (row.experiencia_minima ?? 1) === 0,   // (antes row.es_practicante)
```

## Implementation plan

Cada paso deja el scraper funcional y verificable.

1. Crear `supabase/migrations/0003_experiencia_minima.sql` (add + backfill + drop) y aplicar.
2. En `items.py`, quitar `es_practicante` y añadir `experiencia_minima`. En `pipelines.py`, sustituir `_detect_es_practicante` por `_detect_experiencia_minima`, mapear `telecommute` → `Remoto` en `_detect_modalidad`, ajustar `_detect_stack` a límites `\b` (para que `Java` no matchee `JavaScript`) y cambiar el payload de `SupabaseUpsertPipeline` a `experiencia_minima`.
3. Actualizar `JobMapper.ts` (tipo de fila + `isPracticante` derivado). Verificar `npx tsc --noEmit`.
4. Crear `scraper/job_scraper/utils/__init__.py` y `query_builder.py` con `SearchQueryBuilder` (consulta `user_profiles.stack` y `user_profiles.experiencia_anos`, cachea el resultado para `build_urls` y `should_follow_job`) y `should_follow_job`.
5. Refactor `hireline_spider.py`: `start_requests()` delega en `SearchQueryBuilder.build_urls('hireline')`; `parse()` extrae título + enlace de cada card y valida con `should_follow_job` antes de seguir al detalle.
6. Crear `occ_spider.py` (dominio `occ.com.mx`, JSON-LD con fallback CSS, paginación `?page=N` con `max_pages=4`, `custom_settings` de resiliencia).
7. Crear `run_spiders.py` con `CrawlerProcess` ejecutando `HirelineSpider` y luego `OccSpider` de forma secuencial.
8. Actualizar `.github/workflows/daily_scrape.yml` para correr `python run_spiders.py`.
9. Actualizar `tests/test_pipelines.py` (de `es_practicante` a `experiencia_minima`) y añadir tests de generación de URLs, `should_follow_job`, JSON-LD OCC y `experiencia_minima` bilingüe. Correr `pytest`.

## Acceptance criteria

- [ ] `pytest` dentro de `scraper/` termina en verde (incluye los casos nuevos).
- [ ] `SearchQueryBuilder.build_urls('hireline')` y `('occ')` generan URLs correctas para perfiles de `0`, `2` y `5` años.
- [ ] `should_follow_job` descarta títulos con `becario/practicante/estadías/intern` cuando ningún perfil tiene 0 años, y con `senior/sr/lead/architect/manager` cuando todos tienen 0 años.
- [ ] `experiencia_minima` se infiere en ES y EN: `0`, `1`, `2` y `4` según las reglas.
- [ ] `es_practicante` desaparece de `items.py`, `pipelines.py`, la tabla `vacantes` y `JobMapper.ts`.
- [ ] `TELECOMMUTE` se normaliza a `'Remoto'` y `url_oferta` de OCC queda sin query params.
- [ ] `hireline_spider.py` no contiene `start_urls`/categorías hardcodeadas y delega en `SearchQueryBuilder`.
- [ ] `occ_spider.py` extrae vía JSON-LD `JobPosting` con fallback CSS/XPath.
- [ ] `run_spiders.py` ejecuta `HirelineSpider` y `OccSpider` secuencialmente.
- [ ] `.github/workflows/daily_scrape.yml` invoca `python run_spiders.py`.

## Decisions

- **Sí:** usar solo `stack` de `user_profiles`. **No:** campo `interests` (no existe en la BD ni en la app).
- **Sí:** leer `experiencia_anos` tal cual. **No:** renombrar a `experience_years`.
- **Sí:** sustituir `es_practicante` por `experiencia_minima int` con backfill en `0003`. **No:** mantener ambas columnas.
- **Sí:** ajuste mínimo en la app (`JobMapper` deriva `isPracticante`). La entidad y la UI no cambian.
- **Sí:** mapear `description` del JSON-LD al campo existente `descripcion` (no existe `descripcion_completa`; SPEC 04 definió `descripcion` = texto limpio completo).
- **No:** geocodificación/PostGIS/coordenadas. Se mantiene diferida desde SPEC 04.
- **Sí:** búsqueda Hireline por `?k={tech}` (verificado en vivo en SPEC 04). **No:** slugs `empleos-de-{tech}` (no existen para tecnologías arbitrarias).
- **Sí:** rutas de categoría de entrada (`trainee`, `becario-ti`) solo cuando algún perfil activo tiene `0` años.
- **Sí:** URLs OCC `de-{slug}` y JSON-LD `JobPosting` como válidos (verificados en vivo).
- **Sí:** `run_spiders.py` con `CrawlerProcess` secuencial. **No:** correr ambos spiders en paralelo.

## Risks

| Riesgo                                                   | Mitigación                                                                                                                |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| OCC cambia su HTML o el JSON-LD                          | Extracción con prioridad JSON-LD y fallback CSS/XPath; selectores aislados en `occ_spider.py`.                            |
| Rate-limit / bloqueo en OCC                              | `DOWNLOAD_DELAY=3.0`, `RANDOMIZE_DOWNLOAD_DELAY`, `CONCURRENT_REQUESTS=2`, `RETRY_TIMES=3` (`[429, 500, 502, 503, 504]`). |
| `ROBOTSTXT_OBEY=True` global podría bloquear a OCC       | Revisar `robots.txt` de occ.com.mx antes de producción.                                                                   |
| `user_profiles.stack` vacío                              | Fail-safe: Hireline usa solo rutas de entrada; OCC no genera URLs de tecnología.                                          |
| La migración rompe la app si no se actualiza `JobMapper` | El paso 3 actualiza el mapper; verificar con `npx tsc --noEmit`.                                                          |
| Upsert falla si el esquema de `vacantes` no coincide     | Validar columnas contra `supabase/migrations/0003_experiencia_minima.sql`.                                                |

## Qué **no** está en esta spec

- Campo `interests`.
- Geocodificación, PostGIS y `coordenadas`.
- Renombrar `experiencia_anos`.
- Otras fuentes de empleo.
- Matching engine, % de afinidad y notificaciones push.
- Multiusuario.

Cada uno de esos, si llega, va en su propia spec.
