# SPEC 12 — Catálogo unificado de stacks

> **Estado:** Aprobado
> **Depende de:** SPEC 03, SPEC 04-08, SPEC 09
> **Fecha:** 2026-11-27
> **Objetivo:** Consolidar el vocabulario de tecnologías en una sola fuente de verdad compartida por la app y el scraper, ampliar el catálogo y corregir las inconsistencias actuales (React Native nunca se detecta, `FastApi` vs `FastAPI`, stacks detectables solo por tags), de modo que añadir un stack nuevo implique tocar un solo archivo y quede consistente en perfil, búsqueda, detección y matching de notificaciones.

## Scope

**Incluido:**

- Crear `src/core/config/stacks.json`: catálogo canónico único con nombre, categoría, `selectable`, aliases, patrones de detección y slugs por portal.
- Ampliar el catálogo con la lista por defecto propuesta (~39 tecnologías seleccionables + 5 solo detección).
- Refactorizar `scraper/job_scraper/pipelines.py`: derivar `STACK_KEYWORDS` y `STACK_PATTERNS` del JSON; detectar `React Native` antes que `React`; añadir patrones de descripción que hoy solo existen como tags (`Azure`, `Ruby on Rails`, `Linux`, `Redis`, `REST`).
- Refactorizar `scraper/job_scraper/utils/query_builder.py`: sustituir los tres dicts duplicados (`OCC_STACK_SLUGS`, `COMPUTRABAJO_STACK_SLUGS`, `GETONBRD_STACK_SLUGS`) por un único mapa derivado del JSON, conservando `_slugify` como fallback.
- Refactorizar `scraper/job_scraper/matching.py`: `canonical_tech` debe usar el catálogo en lugar de `STACK_KEYWORDS` + `_EXTRA_STACK_ALIASES`.
- Refactorizar `src/features/profile/presentation/components/ProfileForm.tsx`: derivar `TECH_OPTIONS` del JSON filtrando `selectable: true` y corregir `FastApi` → `FastAPI`.
- Tests: cobertura de las nuevas tecnologías y casos límite (`C#`, `.NET`, `Go`, `React Native` vs `React`), más un test de consistencia del catálogo.
- Script de backfill `scraper/backfill_stacks.py` para recalcular `stack_detectado` en vacantes existentes (ejecución manual).
- Verificación manual de los slugs reales en los tres portales.

**Fuera de alcance (specs futuras):**

- Cambiar el algoritmo de match (ponderación, umbrales, semántica de `stack_match_percent`).
- Rediseñar la UI del selector (búsqueda, agrupación visual, scroll).
- Añadir fuentes de scraping nuevas.
- Migrar `UserProfile.stack` de `string[]` a un enum/union tipado.
- Programar el backfill automático (se ejecuta a mano).
- Re-scrapear las vacantes completas para actualizar otros campos.

## Data model

```jsonc
// src/core/config/stacks.json
[
  {
    "name": "React Native",
    "category": "mobile",
    "selectable": true,
    "aliases": ["react native", "react-native", "reactnative"],
    "patterns": ["react native", "react-native"],
    "slugs": {
      "occ": "react-native",
      "computrabajo": "react-native",
      "getonbrd": "react-native",
    },
  },
]
```

- `name`: nombre canónico; es lo que se guarda en `user_profiles.stack` y en `vacantes.stack_detectado`.
- `category`: `'frontend' | 'mobile' | 'backend' | 'data' | 'cloud' | 'other'` (informativa; no condiciona el match).
- `selectable`: si aparece en el selector del perfil. Los stacks de infraestructura genérica (`Git`, `Linux`, `REST`, `Kafka`, `GraphQL`) se detectan pero no se ofrecen al usuario.
- `aliases`: normalizados en minúsculas/sin acentos; alimentan `STACK_KEYWORDS`, `canonical_tech` y la canonicalización de tags.
- `patterns`: subcadenas a buscar con límites de palabra en título+descripción; alimentan `STACK_PATTERNS`.
- `slugs`: slug por portal; si falta, se usa `_slugify(name)` como hoy.

**Catálogo por defecto (selectable):**

| Categoría            | Tecnologías                                                                  |
| -------------------- | ---------------------------------------------------------------------------- |
| Frontend             | React, Vue, Angular, Svelte, Next.js, JavaScript, TypeScript                 |
| Móvil                | React Native, Flutter, Swift, Kotlin                                         |
| Backend (lenguajes)  | Node.js, Python, Java, C#, Go, PHP, Ruby, Rust                               |
| Backend (frameworks) | Django, Flask, FastAPI, Spring Boot, Laravel, Ruby on Rails, Express, NestJS |
| Datos / DB           | SQL, PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch                        |
| Cloud / DevOps       | AWS, Azure, GCP, Docker, Kubernetes, Terraform                               |

**Solo detección (`selectable: false`):** GraphQL, REST, Git, Linux, Kafka.

**Casos que necesitan slugs/patrones explícitos:** `C#`, `.NET`, `C++` (si se añade), `Node.js`, `Ruby on Rails`, `React Native`, `Next.js`, `NestJS`, `Go` (palabra corta) y `FastAPI`.

## Implementation plan

Cada paso deja la app y el scraper verificables.

1. Crear `src/core/config/stacks.json` con el catálogo completo (aliases, patrones, slugs y `selectable`) y un adaptador `src/core/config/stacks.ts` que lo importe y tipifique. Verificar que el JSON es válido y que `npx tsc --noEmit` pasa.
2. Crear `scraper/job_scraper/stack_catalog.py`: carga el JSON (ruta resuelta desde `scraper/`), expone las listas derivadas y un `canonical_tech`. Verificar con un test de carga.
3. Refactorizar `JobEnrichmentPipeline` para usar `stack_catalog` en lugar de `STACK_KEYWORDS`/`STACK_PATTERNS` locales; ordenar `React Native` antes de `React` y añadir los patrones que faltan (`Azure`, `Ruby on Rails`, `Linux`, `Redis`, `REST`). Verificar `pytest scraper/tests/test_pipelines.py`.
4. Refactorizar `query_builder.py` para derivar los slugs de un único mapa del catálogo y eliminar los tres dicts duplicados. Verificar `pytest scraper/tests/test_query_builder.py`.
5. Refactorizar `matching.py` para usar `canonical_tech` del catálogo (las APIs públicas `canonical_tech`, `stack_match_percent` e `is_full_match` no cambian). Verificar `pytest scraper/tests/test_matching.py`.
6. Refactorizar `ProfileForm.tsx` para derivar `TECH_OPTIONS` del catálogo filtrando `selectable: true`; corregir `FastApi` → `FastAPI`. Verificar `npx tsc --noEmit`.
7. Añadir tests de consistencia (todos los nombres canónicos tienen alias/slug; las opciones del perfil son subconjunto del catálogo; `React Native` no es capturado por `React`; `C#`/`.NET`/`Go` canonicalizan bien) y correr `pytest` completo + `npx tsc --noEmit`.
8. Crear `scraper/backfill_stacks.py` (recalcula `stack_detectado` desde `descripcion`/tags de las vacantes existentes) y verificar manualmente los slugs de los tres portales y el selector de perfil en app.

## Acceptance criteria

- [ ] Existe `src/core/config/stacks.json` como única fuente canónica; no quedan listas de stacks duplicadas en Python ni en TS (salvo las derivadas en tiempo de carga).
- [ ] `npx tsc --noEmit` termina sin errores.
- [ ] `pytest` dentro de `scraper/` termina en verde.
- [ ] El selector de perfil (onboarding y dev menu) muestra el catálogo ampliado filtrado por `selectable` y guarda nombres canónicos (`FastAPI`, no `FastApi`).
- [ ] El scraper detecta las nuevas tecnologías en descripción y en tags, incluido `React Native` sin colisionar con `React`.
- [ ] Los tres portales usan slugs correctos para los stacks con caracteres especiales (verificación manual).
- [ ] `stack_match_percent` e `is_full_match` usan el mismo vocabulario canónico que la detección.
- [ ] No hay regresiones en detección de modalidad, nivel de inglés, experiencia, Favoritos ni detalle de vacante.

## Decisions

- **Sí:** un JSON canónico compartido. **No:** mantener cuatro listas en paralelo.
- **Sí:** nombres canónicos guardados en perfil y vacante. **No:** aceptar alias libres en `user_profiles.stack`.
- **Sí:** flag `selectable` para ocultar stacks de infra genérica en el perfil. **No:** mostrar `Git`/`Linux`/`REST` como "stack" del usuario.
- **Sí:** detectar `React Native` explícitamente. **No:** dejar una opción de perfil que nunca pueda hacer match.
- **Sí:** slugs explícitos por portal para tokens con puntuación. **No:** depender solo de `_slugify`.
- **Sí:** backfill manual mediante script. **No:** re-scrapeo ni backfill automático en esta spec.
- **Sí:** mantener `UserProfile.stack` como `string[]`. **No:** migrar a enum/union en esta spec.

## Risks

| Riesgo                                                                               | Mitigación                                                                               |
| ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Slugs incorrectos por portal → URLs de búsqueda vacías                               | Slugs explícitos en el JSON + verificación manual de los tres portales.                  |
| El patrón de `React` capture `React Native`                                          | Pattern de `React Native` primero y límites de palabra; test específico.                 |
| Tokens cortos o con puntuación (`Go`, `C#`, `C++`, `.NET`, `Node.js`) mal detectados | Aliases y patrones explícitos + tests de canonicalización.                               |
| Más stacks en el perfil → más URLs de búsqueda → bloqueo/rate limit                  | Revisar el número de URLs generadas; el builder ya deduplica.                            |
| Perfiles existentes con `FastApi`/`React Native` guardados                           | `canonical_tech` normaliza aliases; `React Native` pasa a ser detectable con el fix.     |
| Importar JSON desde TypeScript/Metro                                                 | Adaptador tipado en `src/core/config/stacks.ts`; verificar con `tsc` y arranque de Expo. |
| Backfill modifique `stack_detectado` de vacantes favoritas                           | Script manual y revisable; no se ejecuta automáticamente.                                |

## Qué **no** está en esta spec

- Cambios en el algoritmo de match (solo se unifica el vocabulario).
- Rediseño de la UI del selector de stack.
- Nuevas fuentes de scraping.
- Migración de `stack` a tipos literales.
- Backfill automático o programado.

Cada uno de esos, si llega, va en su propia spec.
