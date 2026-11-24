# SPEC 08 — Descripción por secciones (split de requisitos y beneficios)

> **Estado:** Aprobado
> **Depende de:** SPEC 05
> **Fecha:** 2026-11-23
> **Objetivo:** Ampliar el splitter de descripciones del scraper con un diccionario bilingüe de encabezados, una heurística de viñetas con clasificación por señales de contenido y reglas de pie de fuente, para dividir la descripción completa en `requirements` (Qué necesitan) y `benefits` (Qué ofrecen), y reprocesar las vacantes existentes con un backfill que reusa esa misma lógica.

## Scope

**Incluido:**

- Extraer `_classify_heading` y `_split_sections_from_text` de `scraper/job_scraper/pipelines.py` a `scraper/job_scraper/utils/sectionizer.py` (funciones públicas `classify_heading(text)` y `split_sections(text)`).
- Ampliar el diccionario de encabezados bilingüe (español + inglés) con los encabezados observados en Hireline y Get on Board.
- Añadir heurística de viñetas: sin encabezado reconocible, dividir por marcadores de lista y clasificar cada punto por señales de contenido (requisito / beneficio / descripción).
- Añadir reglas de pie de fuente: el marcador `GETONBRD Job ID` (y equivalentes) delimita el fin del cuerpo e inicia un bloque de beneficios.
- `scraper/job_scraper/pipelines.py`: `JobEnrichmentPipeline` delega en `sectionizer.split_sections` (se elimina la lógica duplicada).
- `scraper/backfill_sections.py` nuevo: reprocesa las filas de `vacantes` con `requirements` y `benefits` vacíos y `descripcion` no vacía.
- Tests pytest nuevos/ampliados (`scraper/tests/test_sectionizer.py` y ampliar `scraper/tests/test_pipelines.py`).

**Fuera de alcance (specs futuras):**

- Cambios en la app (`WorkScreen` ya renderiza `requirements`/`benefits`; no se toca).
- Cambios en los spiders (siguen emitiendo `descripcion`; el split lo hace el pipeline).
- Migración SQL de datos (el backfill es un script Python, no una migración).
- Matching engine, notificaciones push, multiusuario, otras fuentes de empleo.

## Data model

Sin cambios en la base de datos. `requirements text[]` y `benefits text[]` ya existen (SPEC 02); `descripcion` sigue siendo `text`. No se añade migración.

```python
# scraper/job_scraper/utils/sectionizer.py
def split_sections(text: str) -> dict:
    # -> {"descripcion": str, "requirements": list[str], "benefits": list[str]}
    # Clasifica con texto normalizado (minúsculas, sin acentos); los items
    # devueltos conservan su capitalización original.
```

### Diccionario de encabezados (normalizado: minúsculas, sin acentos)

**→ `requirements`:**
`requisitos`, `requerimientos`, `requerido`, `requisitos minimos`, `requisitos excluyentes`, `perfil`, `perfil buscado`, `lo que buscamos`, `que buscamos`, `que necesitas`, `que necesitamos`, `conocimientos`, `conocimientos de`, `conocimientos deseables`, `conocimientos obligatorios`, `experiencia requerida`, `competencias`, `habilidades`, `habilidades tecnicas`, `indispensable`, `deseable`, `requirements`, `minimum requirements`, `required skills`, `what we're looking for`, `what we are looking for`, `qualifications`, `must have`, `must-have`, `nice to have`, `nice-to-have`, `skills`, `desired skills`, `preferred skills`, `preferred qualifications`, `experience required`.

**→ `benefits`:**
`ofrecemos`, `que ofrecemos`, `lo que ofrecemos`, `que te ofrecemos`, `te ofrecemos`, `nosotros ofrecemos`, `beneficios`, `beneficios y prestaciones`, `prestaciones`, `condiciones`, `salario`, `sueldo`, `compensacion`, `compensation`, `compensation and benefits`, `que obtienes`, `que recibes`, `ventajas`, `incentivos`, `why join`, `why join us`, `benefits`, `perks`, `what we offer`, `we offer`, `salary`, `what you'll get`, `what you get`.

**→ `description` (intro/funciones, queda en `descripcion`):**
`actividades`, `responsabilidades`, `funciones`, `descripcion general`, `que haras`, `sobre el puesto`, `acerca del puesto`, `sobre nosotros`, `acerca de nosotros`, `sobre la empresa`, `core responsibilities`, `how you work`, `responsibilities`, `what you'll do`, `what you will do`, `about the role`, `about us`, `the role`.

### Señales de contenido (viñetas sin encabezado)

- **Requisito:** `\d+\s*(anos|anios|años|years?)`, `experiencia`, `conocimientos?`, `ingles`, `english`, `titulo universitario`, `licenciatura`, `ingenieria`, `degree`, `nivel`, `dominio de`, `manejo de`, `educacion minima`.
- **Beneficio:** `seguro`, `remoto`, `remote`, `home office`, `horario flexible`, `bono`, `prestaciones`, `salario`, `sueldo`, `vacaciones`, `capacitacion`, `crecimiento`, `estabilidad`, `contrato`, `pago en`, `usd`, `mxn`, `snacks`, `equipo de trabajo`, `equity`, `vestimenta`, `enfermedad`.

### Reglas observadas en las fuentes

1. **Pie de fuente:** una línea que coincida con `(?i)\b(getonbrd|occ|computrabajo|hireline)?\s*job\s*id\b` (ej. `GETONBRD Job ID: 63780`) delimita el fin del cuerpo. Todo lo posterior se trata como beneficios: líneas "etiqueta + descripción" (ej. `Se ofrece equity en la empresa` + su descripción, `Política de trabajo remoto` + `Remoto sólo localmente`).
2. **Atribución:** frases como `Este empleo es original de Get on Board` u `Oferta exclusiva de getonbrd.com` se eliminan del `descripcion`.
3. **Sub-encabezados:** las líneas tipo título dentro de una sección (`Technical Architecture & Leadership` bajo `Core Responsibilities`) NO parten secciones; solo las palabras clave del diccionario lo hacen.
4. **Idioma mixto:** diccionario y señales bilingües; un cuerpo en inglés puede terminar con beneficios en español (Cocoon) y viceversa.

## Implementation plan

Cada paso deja el scraper funcional y verificable.

1. Crear `scraper/job_scraper/utils/sectionizer.py` con `classify_heading()` y `split_sections()` extraídas de `pipelines.py`, ampliando el diccionario bilingüe, añadiendo las señales de contenido y las reglas de pie de fuente/atribución (manteniendo el comportamiento actual para entradas ya cubiertas). Añadir `scraper/tests/test_sectionizer.py` con los tres casos reales (Cocoon, Hireline .NET, We Built It) y casos ES/EN. Correr `pytest`.
2. Refactorizar `scraper/job_scraper/pipelines.py`: `JobEnrichmentPipeline.process_item` usa `sectionizer.split_sections`; eliminar `_classify_heading` y `_split_sections_from_text` duplicadas. Ampliar `scraper/tests/test_pipelines.py` con casos de regresión. Correr `pytest` completo.
3. Crear `scraper/backfill_sections.py`: conexión a Supabase con `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` (mismo patrón que `SupabaseUpsertPipeline.open_spider`), selecciona filas de `vacantes` con `descripcion <> ''` y `requirements = '{}'` y `benefits = '{}'`, aplica `split_sections` y actualiza `requirements`/`benefits`/`descripcion` por `id`. Log de conteo y salida segura si faltan las env. Correr en seco contra una fila.
4. Ejecutar el backfill sobre las vacantes actuales y verificar en la app que las descripciones se ven divididas en "Qué necesitan" y "Qué ofrecen".

## Acceptance criteria

- [ ] `pytest` dentro de `scraper/` termina en verde (incluye los casos nuevos).
- [ ] `split_sections` separa "Requisitos"/"Ofrecemos" en español y "Requirements"/"Benefits" en inglés (regresión de los casos actuales de `test_pipelines.py`).
- [ ] El ejemplo de Hireline separa `Requerido`, `Conocimientos de`, `Habilidades` y `Deseable` en `requirements`, dejando `Experiencia en Sistemas Financieros` en `descripcion`.
- [ ] El ejemplo de Cocoon separa `What We Are Looking For` en `requirements` y `Why Join Cocoon` + `Compensation` en `benefits`; `Core Responsibilities` y `How You Work` quedan en `descripcion` sin que sus sub-encabezados partan secciones.
- [ ] El bloque posterior a `GETONBRD Job ID` (equity, enfermedad, vestimenta, vacaciones, trabajo remoto) se clasifica en `benefits`; la línea `GETONBRD Job ID` y las frases de atribución no aparecen en `descripcion`.
- [ ] Sin encabezado, las viñetas se clasifican por señales: "5+ años de experiencia…" → `requirements`, "seguro de gastos médicos" → `benefits`.
- [ ] `pipelines.py` ya no contiene `_split_sections_from_text` ni `_classify_heading` duplicadas.
- [ ] `backfill_sections.py` actualiza las filas con `requirements`/`benefits` vacíos y `descripcion` no vacía.
- [ ] Una vacante real que hoy se muestra como muro de texto queda dividida en "Qué necesitan" y "Qué ofrecen".
- [ ] No se introduce migración SQL ni cambios en la app ni en los spiders.

## Decisions

- **Sí:** extraer el splitter a `scraper/job_scraper/utils/sectionizer.py`. **No:** dejarlo solo en `pipelines.py` (lo necesitan el pipeline y el backfill).
- **Sí:** backfill como script Python que reusa `split_sections`. **No:** migración SQL con regex.
- **Sí:** diccionario bilingüe (español + inglés). **No:** solo español.
- **Sí:** tratar el marcador `GETONBRD Job ID` (y equivalentes) como delimitador del bloque de beneficios. **No:** dejarlo como texto en `descripcion`.
- **Sí:** clasificar viñetas sin encabezado por señales de contenido. **No:** dejarlas todas en Descripción ni forzar división de prosa corrida.
- **Sí:** solo las palabras clave del diccionario parten secciones; los sub-encabezados tipo título quedan dentro de su sección.
- **Sí:** mapear `How You Work` y `Core Responsibilities` a `descripcion` (cualitativos, no listas de requisitos).
- **No:** tocar la app, los spiders ni el workflow `.github/workflows/daily_scrape.yml`.

## Risks

| Riesgo                                                                | Mitigación                                                                                                                              |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Clasificación errónea de viñetas sin encabezado (beneficio↔requisito) | Señales conservadoras; lo no clasificable queda en `descripcion`. El backfill es idempotente y re-ejecutable.                           |
| Falso positivo en sub-encabezados tipo título                         | Solo las palabras clave del diccionario parten secciones; no se detectan "títulos" genéricos.                                           |
| Pie de fuente varía entre portales                                    | Delimitador con `\bjob id\b` opcionalmente prefijado por la plataforma; las líneas posteriores se clasifican por señales como fallback. |
| Backfill toca datos de producción                                     | Solo actualiza filas con `requirements`/`benefits` vacíos; si faltan las env de Supabase termina sin escribir; permite corrida en seco. |
| Regresión en encabezados ya soportados                                | Se conserva la lista previa y se amplía; `test_pipelines.py` mantiene los casos de regresión.                                           |
| Descripciones con prosa corrida sin estructura                        | Sin marcadores de lista no se divide (fallback: queda como párrafo en `descripcion`).                                                   |

## Qué **no** está en esta spec

- Cambios en la app o en `WorkScreen`.
- Cambios en los spiders.
- Migración SQL de datos.
- Matching engine, notificaciones push, multiusuario, otras fuentes de empleo.

Cada uno de esos, si llega, va en su propia spec.
