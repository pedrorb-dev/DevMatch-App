# SPEC 02 — Persistencia real en Supabase

> **Estado:** Aprobado
> **Depende de:** SPEC 01
> **Fecha:** 2026-11-14
> **Objetivo:** Reemplazar los repositorios mock en memoria por repositorios que lean y escriban en tablas reales de Supabase (`vacantes`, `user_profiles` y `saved_jobs`), con datos semilla y sin autenticación por ser una app de un solo usuario.

## Scope

**Incluido:**

- Crear el cliente de Supabase en `src/core/api/supabase.ts` leyendo `EXPO_PUBLIC_SUPABASE_URL` y `EXPO_PUBLIC_SUPABASE_ANON_KEY` (ya presentes en `.env`).
- Definir un identificador fijo de usuario único (`SINGLE_USER_ID`) en `src/core/config/user.ts` para perfil y favoritos.
- Crear las tablas `vacantes`, `user_profiles` y `saved_jobs` con migraciones versionadas en `supabase/migrations/`.
- Habilitar Row Level Security con políticas permisivas (postura temporal de un solo usuario).
- Repositorios Supabase para jobs, perfil y favoritos, con mappers `snake_case` → `camelCase`.
- Sembrar `vacantes` con las 14 vacantes que hoy viven en `jobs.mock.ts`.
- Sustituir los repositorios in-memory en hooks y contextos sin tocar las pantallas.

**Fuera de alcance (specs futuras):**

- Cualquier forma de autenticación (anónima, email/contraseña) y soporte multiusuario.
- RLS estricta por usuario (requiere autenticación).
- Matching engine y % de afinidad.
- GPS real y cálculo de distancia (PostGIS + `coordenadas`).
- Caché offline (TanStack Query + MMKV + NetInfo).
- DevMenu y notificaciones push.
- Scraper (Scrapy) y GitHub Actions: el llenado real de vacantes llega después.
- Persistencia local del perfil (MMKV / AsyncStorage); el perfil vive solo en Supabase.

## Data model

Migración SQL aplicada con `apply_migration` desde `supabase/migrations/0001_init_tables.sql`:

```sql
create table public.vacantes (
  id              uuid primary key default gen_random_uuid(),
  titulo          text not null,
  empresa         text not null,
  modalidad       text not null check (modalidad in ('Remoto', 'Híbrido', 'Presencial')),
  descripcion     text not null default '',
  requirements    text[] not null default '{}',
  benefits        text[] not null default '{}',
  stack_detectado text[] not null default '{}',
  nivel_ingles    text not null default 'No especificado',
  es_practicante  boolean not null default false,
  ubicacion_texto text not null default '',
  url_oferta      text not null unique,
  created_at      timestamptz not null default now()
);

create table public.user_profiles (
  id               uuid primary key,
  stack            text[] not null default '{}',
  experiencia_anos integer not null default 0,
  nivel_ingles     text not null default 'B1',
  ubicacion_texto  text not null default ''
);

create table public.saved_jobs (
  id       uuid primary key default gen_random_uuid(),
  user_id  uuid not null references public.user_profiles (id) on delete cascade,
  job_id   uuid not null references public.vacantes (id) on delete cascade,
  saved_at timestamptz not null default now(),
  unique (user_id, job_id)
);
```

Políticas RLS permisivas (misma migración): `select` para `anon` y `authenticated` en las tres tablas, y `insert/update/delete` para `anon` y `authenticated`. Es una postura temporal de un solo usuario; cuando llegue el multiusuario se reemplazan por políticas basadas en `auth.uid()`.

Identificador fijo de usuario (nuevo archivo):

```ts
// src/core/config/user.ts
export const SINGLE_USER_ID = "00000000-0000-0000-0000-000000000001";
```

Las entidades `JobOffer` y `UserProfile` **no cambian**. Se añade una interfaz nueva:

```ts
// src/features/jobs/domain/repositories/FavoritesRepository.ts
export interface FavoritesRepository {
  getFavoriteJobIds(): Promise<string[]>;
  addFavorite(jobId: string): Promise<void>;
  removeFavorite(jobId: string): Promise<void>;
}
```

`gen_random_uuid()` usa `pgcrypto` (ya instalada). Los slugs `devmatch-01` desaparecen: ahora son UUIDs.

## Implementation plan

Cada paso deja el sistema funcional y verificable con `npx tsc --noEmit`.

1. Instalar `@supabase/supabase-js` con `npx expo install @supabase/supabase-js` (añadir `react-native-url-polyfill` solo si supabase-js lo exige en SDK 58).
2. Crear `src/core/config/user.ts` con `SINGLE_USER_ID` y `src/core/api/supabase.ts` con el cliente (`auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false }`).
3. Crear `supabase/migrations/0001_init_tables.sql` (tablas + RLS permisiva) y aplicarlo con `apply_migration`. Verificar con `list_migrations`.
4. Crear `supabase/migrations/0002_seed_vacantes.sql` con 14 `INSERT` (uno por vacante de `jobs.mock.ts`, `created_at = now() - interval 'N days'`) y aplicarlo. Verificar `select count(*) from vacantes` = 14.
5. Crear `src/features/jobs/infrastructure/mappers/JobMapper.ts` y `src/features/jobs/infrastructure/repositories/SupabaseJobRepository.ts`; apuntar `useJobs` y `useJob` al nuevo repositorio. Eliminar `InMemoryJobRepository.ts` y `jobs.mock.ts`. Verificar que el Feed carga desde Supabase.
6. Crear `src/features/profile/infrastructure/mappers/ProfileMapper.ts` y `src/features/profile/infrastructure/repositories/SupabaseProfileRepository.ts` (usa `SINGLE_USER_ID`); apuntar `ProfileContext` al nuevo repositorio y eliminar `InMemoryProfileRepository.ts`. Verificar que el onboarding persiste en `user_profiles`.
7. Crear `src/features/jobs/domain/repositories/FavoritesRepository.ts` y `src/features/jobs/infrastructure/repositories/SupabaseFavoritesRepository.ts`; reescribir `FavoritesContext` con carga asíncrona y toggle optimista. Verificar que los favoritos persisten en `saved_jobs`.
8. Verificación final: `npx tsc --noEmit` sin errores y `npx expo start` cargando en Expo Go.

## Acceptance criteria

- [ ] `npx tsc --noEmit` termina sin errores.
- [ ] Existen las tablas `vacantes`, `user_profiles` y `saved_jobs` con RLS habilitado.
- [ ] `vacantes` contiene 14 filas sembradas.
- [ ] La app arranca sin autenticación y el Feed muestra las 14 vacantes desde Supabase.
- [ ] Completar el onboarding hace upsert de una fila en `user_profiles` con `id = SINGLE_USER_ID`.
- [ ] Cerrar y reabrir la app restaura el perfil guardado.
- [ ] Marcar un favorito inserta una fila en `saved_jobs` con `user_id = SINGLE_USER_ID`; persiste tras recargar.
- [ ] Desmarcar un favorito elimina su fila de `saved_jobs` y desaparece de Favoritos.
- [ ] "Ver oferta original" abre la URL de `url_oferta`.

## Decisions

- **Sí:** app de un solo usuario sin autenticación. **No:** anonymous sign-in ni email/contraseña; llegan en una spec de multiusuario.
- **Sí:** `SINGLE_USER_ID` fijo como llave del perfil y los favoritos. **No:** UUID de dispositivo local (no aporta nada con un solo usuario).
- **Sí:** RLS habilitada con políticas permisivas. **No:** políticas estrictas basadas en `auth.uid()` (requieren autenticación y quedan para la spec de multiusuario).
- **Sí:** supabase-js directo (BaaS). **No:** Edge Functions intermedias.
- **Sí:** adaptar `vacantes` a la entidad (`requirements text[]`, `benefits text[]`, `descripcion`). **No:** `resumen_descripcion` del README.
- **Sí:** diferir PostGIS/`coordenadas` y `expo_push_token`. **No:** incluirlos ahora.
- **Sí:** sembrar con las 14 vacantes mock. **No:** empezar vacía.
- **Sí:** migraciones versionadas en `supabase/migrations/` aplicadas vía `apply_migration`. **No:** configurar el CLI local de Supabase.
- **Sí:** `id uuid` con `gen_random_uuid()` (se pierden los slugs `devmatch-NN`). **No:** mantener `id` de texto.

## Risks

| Riesgo                                                                   | Mitigación                                                                                                         |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| supabase-js en React Native requiere polyfill de `URL`                   | Añadir `react-native-url-polyfill/auto` si el cliente falla al importar en SDK 58.                                 |
| RLS permisiva: cualquiera con la publishable key puede leer/escribir     | Aceptado por diseño en la etapa de un solo usuario; se endurece en la spec de multiusuario.                        |
| `saved_jobs` falla por FK si no existe `user_profiles`                   | El onboarding bloquea el acceso al Feed antes de marcar favoritos; `saveProfile` hace upsert con `SINGLE_USER_ID`. |
| "Nuevos hoy" deja de mostrar resultados con el tiempo                    | Aceptado: es un límite de sembrar datos estáticos; lo resuelve el scraper (spec futura).                           |
| `clearProfile` borra el perfil y, por `on delete cascade`, los favoritos | Comportamiento esperado: sin perfil no hay favoritos que conservar.                                                |

## Qué **no** está en esta spec

- Autenticación y soporte multiusuario (anonymous sign-in, email/contraseña, RLS por usuario).
- Matching engine / % de afinidad y filtros adicionales.
- GPS, PostGIS y distancia.
- Caché offline (TanStack Query + MMKV + NetInfo).
- DevMenu, notificaciones push, scraper y GitHub Actions.

Cada uno de esos, si llega, va en su propia spec.
