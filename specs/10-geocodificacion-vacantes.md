# SPEC 10 — Geocodificación de vacantes (lat/lng)

> **Estado:** Aprobado
> **Depende de:** SPEC 02, SPEC 05
> **Fecha:** 2026-11-27
> **Objetivo:** Añadir coordenadas `lat`/`lng` a cada vacante geocodificando su `ubicacion_texto` con Nominatim durante el pipeline del scraper, con caché por ciudad y un backfill para las vacantes existentes.

## Scope

**Incluido:**

- Migración `supabase/migrations/0005_add_vacante_coordenadas.sql`: añade `lat double precision` y `lng double precision` (nullable) a `public.vacantes`.
- `scraper/job_scraper/geocode.py`: función `geocode(text)` vía Nominatim con caché `cities_cache.json` (clave normalizada minúsculas/sin acentos por ciudad).
- Integrar la geocodificación en `JobEnrichmentPipeline.process_item` (setear `lat`/`lng` en el item).
- `SupabaseUpsertPipeline.process_item`: incluir `lat`/`lng` en el payload del upsert.
- `scraper/backfill_coordenadas.py`: geocodificar las filas actuales con `ubicacion_texto <> ''` y `lat is null`.
- Tests pytest `scraper/tests/test_geocode.py` (HTTP mockeado).

**Fuera de alcance (specs futuras):**

- La app: GPS, orden por distancia y "a X km" (SPEC 11).
- PostGIS (`geography`); se usan columnas float + haversine en la app.
- Geocodificar en la app (runtime).
- Gestión sofisticada de rate-limit más allá del delay y la caché.

## Data model

```sql
alter table public.vacantes
  add column lat double precision,
  add column lng double precision;
```

`lat`/`lng` son nullable: `null` significa "sin coordenadas" (ubicación no geocodificable). `ubicacion_texto` se mantiene intacto.

```python
# scraper/job_scraper/geocode.py
def geocode(text: str, cache: dict) -> tuple[float, float] | None: ...
# Nominatim search (limit=1), User-Agent propio, delay de 1s.
# Cache por ciudad normalizada: {"monterrey, mexico": {"lat": 25.68, "lng": -100.31}, ...}
```

## Implementation plan

Cada paso deja el scraper funcional y verificable.

1. Crear `supabase/migrations/0005_add_vacante_coordenadas.sql` y aplicarla con `apply_migration`. Verificar con `list_migrations`.
2. Crear `scraper/job_scraper/geocode.py` (`geocode` + carga/guardado de `cities_cache.json`) y `scraper/tests/test_geocode.py` con HTTP mockeado. Correr `pytest`.
3. Integrar en `JobEnrichmentPipeline.process_item` (setear `lat`/`lng`) y en `SupabaseUpsertPipeline.process_item` (añadir `lat`/`lng` al payload). Correr `pytest` completo.
4. Crear `scraper/backfill_coordenadas.py` (mismo patrón que `backfill_sections.py`, env `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY`). Ejecutarlo sobre las vacantes actuales.
5. Verificación: `select count(*) from vacantes where lat is not null` > 0 y una corrida del scraper deja lat/lng en las nuevas.

## Acceptance criteria

- [ ] `pytest` dentro de `scraper/` termina en verde (incluye `test_geocode.py`).
- [ ] `public.vacantes` tiene las columnas `lat` y `lng` (double precision).
- [ ] `geocode("Monterrey, México")` devuelve (lat, lng) y `geocode("")` o un texto no encontrado devuelve `None` (con HTTP mockeado).
- [ ] La caché evita repetir la llamada HTTP para la misma ciudad (una sola request por ciudad en el test).
- [ ] `SupabaseUpsertPipeline` incluye `lat`/`lng` en el payload del upsert.
- [ ] `backfill_coordenadas.py` rellena `lat`/`lng` en filas con `ubicacion_texto` no vacía y `lat is null`.
- [ ] No se toca la app ni `ubicacion_texto`.

## Decisions

- **Sí:** columnas `lat`/`lng` float. **No:** PostGIS (la distancia se calcula en la app con haversine; no hace falta geografía en SQL).
- **Sí:** geocodificar en el pipeline del scraper. **No:** en la app.
- **Sí:** Nominatim (gratis, sin API key). **No:** Google Geocoding (requiere key y billing).
- **Sí:** caché `cities_cache.json` por ciudad normalizada. **No:** geocodificar cada item sin caché (rompería el rate limit).
- **Sí:** `lat`/`lng` nullable. **No:** valor por defecto `(0,0)` (ensuciaría el cálculo de distancia).
- **Sí:** los textos de modalidad (`Remoto`, `Remote`, `Home Office`, `Remoto (N ubicaciones)`) devuelven `None` sin llamar a Nominatim; no son lugares. **No:** geocodificarlos (Nominatim los resuelve a Italia/Oregón/Campeche y rompería la etiqueta "a X km" de SPEC 11). Si el texto además contiene una ciudad real (ej. `Miguel Hidalgo, Home Office, México`), se geocodifica solo la ciudad.
- **Sí:** backfill como script Python. **No:** migración SQL (la geocodificación es HTTP, no SQL).

## Risks

| Riesgo                                        | Mitigación                                                                                  |
| --------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Rate limit / ToS de Nominatim                 | Delay de 1s + caché por ciudad; ante fallo la vacante queda `lat/lng null` (orden neutral). |
| Geocodificación ambigua (homónimos)           | Aceptado: es orden, no filtro.                                                              |
| `ubicacion_texto` genérico ("México", "CDMX") | Nominatim devuelve centro aproximado; comportamiento aceptado.                              |
| Caché desactualizada                          | Bajo impacto; se re-geocodifica al borrar el archivo.                                       |

## Qué **no** está en esta spec

- GPS y orden por distancia en la app (SPEC 11).
- PostGIS.
- Geocodificación en cliente.

Cada uno de esos, si llega, va en su propia spec.
