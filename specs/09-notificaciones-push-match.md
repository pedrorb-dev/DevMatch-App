# SPEC 09 — Notificaciones push con match de stack al 100%

> **Estado:** Aprobado
> **Depende de:** SPEC 02, SPEC 03, SPEC 05
> **Fecha:** 2026-11-27
> **Objetivo:** Añadir notificaciones push remotas que, al final de la corrida diaria del scraper, avisen únicamente sobre las vacantes nuevas que cubren al 100 % el stack del perfil y son compatibles en experiencia e inglés, guardando el token Expo del dispositivo en `user_profiles`.

## Scope

**Incluido:**

- Migración `supabase/migrations/0004_add_expo_push_token.sql` que añade `expo_push_token text` (nullable) a `public.user_profiles`.
- App: instalar `expo-notifications` con `npx expo install expo-notifications` y añadir el config plugin en `app.json`.
- App: `src/core/push/registerPushToken.ts` para pedir permisos, crear el canal de Android, obtener el token Expo con `getExpoPushTokenAsync` y guardarlo en la fila `SINGLE_USER_ID`.
- App: `addPushTokenListener` para re-sincronizar el token si el sistema lo rota.
- App: botón "Probar push" en `ProfileDevMenu` que dispara una notificación de prueba al propio token.
- Scraper: `scraper/job_scraper/matching.py` con `canonical_tech`, `stack_match_percent`, `english_rank` e `is_full_match`.
- Scraper: `scraper/job_scraper/notify.py` con el envío a Expo Push API y `notify_full_matches(supabase_url, supabase_key, run_started_at)`.
- Scraper: cablear `notify_full_matches` en `scraper/run_spiders.py` (registrar `run_started_at` antes de `process.start()` y llamar después).
- Tests pytest `scraper/tests/test_matching.py`.

**Fuera de alcance (specs futuras):**

- Mostrar el % de match en el feed (cálculo client-side en `JobCard`).
- Manejo del tap de la notificación (deep-link a `/work/[id]`); el payload ya incluye `data.url` para una spec futura.
- Multiusuario y autenticación (la app sigue siendo de un solo usuario).
- Enhanced push security de Expo (access token); se usa el endpoint sin autenticación.
- Re-notificar vacantes ya existentes en corridas anteriores.
- GPS, PostGIS, `coordenadas` y otras fuentes de empleo.

## Data model

Migración `0004`:

```sql
alter table public.user_profiles
  add column expo_push_token text;
```

No cambia ninguna otra columna. `vacantes` y `saved_jobs` no se tocan. `expo_push_token` es nullable: solo se rellena cuando la app obtiene el token.

### Reglas de match (evaluadas en el scraper)

```python
# scraper/job_scraper/matching.py
ENGLISH_RANK = {"No especificado": 0, "B1": 1, "B2": 2, "C1": 3}

def canonical_tech(token: str) -> str: ...        # alias-aware, reusa STACK_KEYWORDS
def stack_match_percent(user_stack, job_stack) -> float: ...  # |∩| / |user_stack|
def english_rank(level: str) -> int: ...
def is_full_match(user: dict, job: dict) -> bool: ...  # AND de las 3 condiciones
```

1. **Stack — cobertura 100 % (hard).** `stack_match_percent = |canonical(user.stack) ∩ canonical(job.stack_detectado)| / |canonical(user.stack)|`. 100 % significa que la vacante cubre **todas** las tecnologías del usuario, aunque pida alguna extra (`job.stack_detectado ⊇ user.stack`). `user.stack` vacío → 0 (no se evalúa).
2. **Experiencia (hard).** `experiencia_anos == 0` (modo practicante) ⇒ notifica solo si `experiencia_minima == 0`. Si `experiencia_anos > 0` ⇒ notifica solo si `experiencia_minima <= experiencia_anos`.
3. **Inglés (hard, estricto).** `english_rank(job.nivel_ingles) <= english_rank(user.nivel_ingles)`.

`canonical_tech` reutiliza el mismo vocabulario canónico del pipeline (`JobEnrichmentPipeline.STACK_KEYWORDS`, minúsculas + sin acentos + alias), de modo que `AngularJS`/`angular` → `Angular`, `springboot`/`Spring Boot` → `Spring Boot`.

### Mensaje de push

```python
{
    "to": token,
    "title": "100% match con tu stack",
    "body": f"{empresa} · {titulo}",
    "data": {"url": f"/work/{job_id}"},
    "sound": "default",
    "priority": "high",
}
```

Se envía en un solo POST (array de hasta 100 mensajes) a `https://exp.host/--/api/v2/push/send` y se registran los push tickets en el log.

### `notify_full_matches(supabase_url, supabase_key, run_started_at)`

1. Consulta `vacantes` con `created_at >= run_started_at` (id, titulo, empresa, stack_detectado, experiencia_minima, nivel_ingles).
2. Consulta `user_profiles` con `expo_push_token is not null` (id, stack, experiencia_anos, nivel_ingles, expo_push_token).
3. Para cada vacante nueva × perfil, calcula `is_full_match`; acumula un mensaje por cada match completo.
4. Envía el batch y loguea los tickets. Sale sin hacer nada si faltan `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` o no hay tokens.

## Implementation plan

Cada paso deja el sistema funcional y verificable.

1. Crear `supabase/migrations/0004_add_expo_push_token.sql` y aplicarla con `apply_migration`. Verificar con `list_migrations`.
2. Instalar `expo-notifications` (`npx expo install expo-notifications`) y añadir el config plugin a `app.json` (mínimo `"expo-notifications"`; opcional `defaultChannel`/`icon`/`color`). Verificar `npx tsc --noEmit`.
3. Crear `src/core/push/registerPushToken.ts`: `setNotificationHandler`, `registerForPushNotificationsAsync()` (canal Android vía `setNotificationChannelAsync` antes del token, `requestPermissionsAsync`, `getExpoPushTokenAsync({ projectId })` desde `Constants`) y `savePushToken(token)` que escribe `expo_push_token` en la fila `SINGLE_USER_ID` sin pisar `stack`/`experiencia_anos`/`nivel_ingles`/`ubicacion_texto` (`update` con fallback `insert`). Cablear en `app/_layout.tsx`: registrar al montar y con `addPushTokenListener`. Verificar `npx tsc --noEmit`.
4. Añadir el botón "Probar push" en `ProfileDevMenu` (junto a la fila "Modo oscuro") que obtiene/guarda el token y dispara una notificación de prueba. Verificar `npx tsc --noEmit`.
5. Crear `scraper/job_scraper/matching.py` (reutilizando `JobEnrichmentPipeline.STACK_KEYWORDS` para `canonical_tech`) y `scraper/tests/test_matching.py`. Correr `pytest`.
6. Crear `scraper/job_scraper/notify.py` (envío por batch con `requests`/`httpx`, log de tickets) y cablear en `scraper/run_spiders.py`: `run_started_at = datetime.now(timezone.utc)` antes de `process.start()` y `notify_full_matches(...)` después, leyendo `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` de los settings. Correr `pytest`.
7. Verificación manual end-to-end: development build, registro del token, botón "Probar push" y una corrida de `notify_full_matches` con una vacante nueva que haga 100 % match.

## Acceptance criteria

- [ ] `npx tsc --noEmit` termina sin errores.
- [ ] `pytest` dentro de `scraper/` termina en verde (incluye `test_matching.py`).
- [ ] `public.user_profiles` tiene la columna `expo_push_token text`.
- [ ] `getExpoPushTokenAsync` devuelve un token y `savePushToken` lo escribe en la fila `SINGLE_USER_ID` sin sobrescribir `stack`, `experiencia_anos`, `nivel_ingles` ni `ubicacion_texto`.
- [ ] El botón "Probar push" entrega una notificación en el dispositivo.
- [ ] `stack_match_percent` devuelve 100, 50 y 0 para los casos de cobertura total, parcial y nula; `user.stack` vacío devuelve 0.
- [ ] `canonical_tech` colapsa alias (`AngularJS`→`Angular`, `springboot`→`Spring Boot`).
- [ ] `is_full_match` exige simultáneamente stack 100 %, experiencia compatible e inglés `<=` (B1 no recibe vacantes B2/C1).
- [ ] `notify_full_matches` envía push solo a perfiles con `is_full_match` y solo sobre vacantes con `created_at >= run_started_at`.
- [ ] Las vacantes ya existentes no se re-notifican.
- [ ] Los perfiles sin `expo_push_token` se ignoran.
- [ ] No se introduce migración en `vacantes`/`saved_jobs` ni cambios en el cálculo del feed.

## Decisions

- **Sí:** cobertura (`|∩| / |user.stack|`) para el % de match. **No:** igualdad exacta de conjuntos ni Jaccard (una vacante que pide tecnología extra igual cubre todo el stack del usuario).
- **Sí:** match completo (stack 100 % + experiencia + inglés). **No:** filtrar solo por stack.
- **Sí:** inglés estricto (`requerido <= nivel del usuario`). **No:** la regla flexible del feed (+1 nivel con aviso), que es una decisión de presentación, no de notificación.
- **Sí:** calcular y enviar desde el scraper (Python). **No:** Edge Function de Supabase (el pipeline ya recorre perfiles y es el punto natural).
- **Sí:** notificar solo vacantes nuevas (`created_at >= run_started_at`). **No:** re-notificar cada corrida.
- **Sí:** usuario único: la app guarda el token en `SINGLE_USER_ID`; el scraper itera todas las filas de `user_profiles` de forma genérica. **No:** multidispositivo (requiere decidir identidad/autenticación).
- **Sí:** canonicalización alias-aware reusando `STACK_KEYWORDS`. **No:** comparación estricta de strings (rompería `AngularJS` vs `Angular`).
- **Sí:** endpoint de Expo Push sin access token (por defecto). **No:** enhanced push security (se puede activar luego).
- **Sí:** botón "Probar push" en `ProfileDevMenu` para verificación manual.
- **No:** mostrar el % en el feed ni manejar el tap de la notificación (van en specs futuras).

## Risks

| Riesgo                                                          | Mitigación                                                                                                                                  |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Las push remotas no funcionan en Expo Go (Android desde SDK 53) | Requiere development build; se documenta como prerrequisito junto con el `projectId` de EAS y las credenciales FCM v1 / APNs.               |
| `getExpoPushTokenAsync` rechaza sin `projectId`                 | Leer `projectId` de `Constants`; fallar con log claro si no existe.                                                                         |
| Upsert del token pisaría `stack`/`experiencia_anos`/etc.        | `savePushToken` usa `update` con fallback `insert`, nunca un `upsert` que reemplace la fila completa.                                       |
| Token inválido (`DeviceNotRegistered`)                          | Se loguea el ticket/receipt; la limpieza del token se deja para una spec futura.                                                            |
| `created_at` vs zona horaria en el filtro de "nuevas"           | `run_started_at` en `timezone.utc` y comparación contra `timestamptz` (UTC).                                                                |
| Stack del usuario fuera del vocabulario canónico                | `canonical_tech` colapsa alias conocidos; lo no reconocido queda tal cual (puede no matchear 100 %, comportamiento aceptado y documentado). |
| Android exige canal antes de obtener el token                   | `setNotificationChannelAsync` se llama antes de `getExpoPushTokenAsync`.                                                                    |

## Qué **no** está en esta spec

- Mostrar el % de match en el feed (cálculo client-side).
- Manejo del tap de la notificación (deep-link a `/work/[id]`).
- Multiusuario y autenticación.
- Enhanced push security (access token).
- Re-notificar vacantes existentes.
- GPS, PostGIS, `coordenadas` y otras fuentes de empleo.

Cada uno de esos, si llega, va en su propia spec.
