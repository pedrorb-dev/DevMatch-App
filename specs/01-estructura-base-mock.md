# SPEC 01 — Estructura principal con datos mock

> **Estado:** Aprobado
> **Depende de:** —
> **Fecha:** 2026-11-14
> **Objetivo:** Crear la estructura principal del proyecto (Expo Router, tema y carpeta feature-based) con las pantallas de Onboarding, Inicio, Favoritos, Perfil y Detalle navegables y alimentadas con datos mock en memoria.

## Scope

**Incluido:**

- Configurar **Expo Router** (entrypoint, layout raíz, redirección, grupo Drawer y ruta dinámica `work/[id]`).
- **Tema centralizado** en `src/core/theme/theme.ts` (Indigo `#4F46E5` + Blanco `#FFFFFF` / `#F8FAFC`).
- **Estructura feature-based**: `src/core/` + `src/features/jobs` + `src/features/profile` (domain / infrastructure / presentation).
- **Entidades y tipos**: `JobOffer`, `UserProfile`, `WorkModality`, `EnglishLevel`.
- **Repositorio mock en memoria** (`InMemoryJobRepository` y `InMemoryProfileRepository`) detrás de sus interfaces.
- **Pantallas**: Onboarding, Inicio/Feed, Favoritos, Perfil y Detalle (`WorkScreen`).
- **Feed con un único filtro "Nuevos hoy"** (solo vacantes creadas hoy).
- **Tarjeta de vacante (`JobCard`)** que muestra **puesto, empresa, modalidad y lugar**.
- **Favoritos con toggle en memoria** reflejado en Feed, Detalle y Favoritos.
- **Perfil en memoria + redirección** desde `app/index.tsx`.
- **Custom Drawer** con tarjeta resumen del perfil y acceso a Inicio, Favoritos y Perfil.

**Fuera de alcance (specs futuras):**

- **% de afinidad / match con el puesto** (no se muestra en la tarjeta).
- **Matching engine completo** (compatibilidad de stack, filtro flexible de inglés, modo practicante).
- **Chips de filtro adicionales** (`100% Match`, `Practicante`, `Remoto`, `Cerca de mí`).
- Supabase y persistencia real.
- Caché offline (TanStack Query + MMKV + NetInfo).
- GPS real (`expo-location`).
- DevMenu integrado en Perfil.
- Notificaciones push.
- Scraper (Scrapy) y GitHub Actions.

## Data model

Nuevas estructuras introducidas (TypeScript, `camelCase` en la app):

```ts
// src/features/jobs/domain/types.ts
export type WorkModality = "Remoto" | "Híbrido" | "Presencial";
export type EnglishLevel = "A1" | "A2" | "B1" | "B2" | "C1" | "C2";

// src/features/jobs/domain/entities/JobOffer.ts
export interface JobOffer {
  id: string;
  title: string; // puesto
  company: string; // empresa
  modality: WorkModality; // Remoto / Híbrido / Presencial
  description: string;
  stack: string[];
  englishLevel: EnglishLevel;
  isPracticante: boolean;
  locationText: string; // lugar
  url: string;
  createdAt: string; // fecha ISO (base del filtro "Nuevos hoy")
}

// src/features/profile/domain/entities/UserProfile.ts
export interface UserProfile {
  stack: string[];
  experienceYears: number; // 0 activa el modo practicante
  englishLevel: "A1" | "A2" | "B1" | "B2" | "C1" | "C2";
  locationText: string; // mock, sin GPS real
}
```

Los favoritos son un `Set<string>` de ids de vacante en memoria. El filtro "Nuevos hoy" es un booleano local en `FeedScreen` que compara `createdAt` con la fecha actual.

## Implementation plan

Cada paso deja el sistema funcional y verificable con `npx tsc --noEmit`.

1. Instalar dependencias con `npx expo install expo-router react-native-safe-area-context react-native-screens expo-linking expo-constants` (no `npm install`). Reconfigurar el entrypoint: `package.json` → `"main": "expo-router/entry"`, `app.json` → `scheme` + plugin `expo-router`, `tsconfig.json` → alias `@/*` → `./src/*`. Eliminar `App.tsx` e `index.ts`.
2. Crear `src/core/theme/theme.ts` con los design tokens (colores, espaciado, tipografía).
3. Crear el dominio de jobs: `types.ts`, `JobOffer` e interfaz `JobRepository`.
4. Crear la infraestructura de jobs: `InMemoryJobRepository` + archivo de datos mock (~12–15 vacantes variadas en modalidad, inglés, practicante, stack, lugar y fecha).
5. Crear el dominio e infraestructura de profile: `UserProfile`, interfaz `ProfileRepository` y `InMemoryProfileRepository`.
6. Crear los contextos `ProfileProvider` y `FavoritesProvider` y renderizarlos en `app/_layout.tsx` junto con el `<Stack>` raíz. Crear `app/index.tsx` con el `<Redirect>` según exista perfil.
7. Crear el grupo `(drawer)` con `_layout.tsx` (Drawer + `CustomDrawerContent`) y las pantallas vacías (`feed`, `favorites`, `profile`) para verificar que la navegación funciona. La pantalla Inicio vive en `(drawer)/feed` (URL `/feed`) para evitar el choque con `app/index.tsx` en `/`.
8. Implementar `FeedScreen` con `FlatList` + filtro único "Nuevos hoy" + `JobCard` (puesto, empresa, modalidad y lugar).
9. Implementar `FavoritesScreen` y `WorkScreen` (`app/work/[id].tsx`) con toggle de favorito y botón "Ver oferta original" (`Linking.openURL`).
10. Implementar `OnboardingScreen` (guardar perfil y redirigir) y `ProfileScreen` (resumen del perfil).
11. Verificación final: `npx tsc --noEmit` sin errores y `npx expo start` cargando en Expo Go.

## Acceptance criteria

- [ ] `npx tsc --noEmit` termina sin errores.
- [ ] `npx expo start` arranca y la app carga en Expo Go sin errores en consola.
- [ ] Al abrir la app sin perfil, redirige a `/onboarding`.
- [ ] Completar el onboarding guarda el perfil en memoria y redirige al Drawer (Inicio).
- [ ] El Drawer muestra Inicio, Favoritos y Perfil con la tarjeta resumen del perfil.
- [ ] Inicio muestra la lista de vacantes mock y cada tarjeta muestra puesto, empresa, modalidad y lugar.
- [ ] El filtro "Nuevos hoy" muestra solo las vacantes con `createdAt` de hoy.
- [ ] Marcar favorito en una tarjeta actualiza el ícono en Inicio y la vacante aparece en Favoritos.
- [ ] Abrir una vacante muestra su detalle y "Ver oferta original" abre la URL.
- [ ] Perfil muestra el stack, nivel de inglés y años de experiencia guardados.

## Decisions

- **Sí:** Expo Router. Alinea con el README y da enrutamiento por archivos (`app/`, grupo `(drawer)`, `work/[id]`).
- **Sí:** gate en `app/index.tsx` y Feed en `(drawer)/feed` (URL `/feed`). Evita la ruta duplicada `/` que Expo Router rechaza.
- **Sí:** repositorio mock en memoria detrás de la interfaz del repositorio. Sustituir por Supabase después no toca las pantallas.
- **Sí:** React Context (`useState`) para perfil y favoritos. Sin TanStack Query ni MMKV en esta fase.
- **Sí:** un único filtro en el Feed ("Nuevos hoy"). Los chips de la visión completa del README se dejan para specs posteriores.
- **No:** % de afinidad / match con el puesto en la tarjeta. Queda fuera; va en otra spec.
- **No:** TanStack Query + MMKV (offline). Va en otra spec.
- **No:** `expo-location` / GPS real. La ubicación es un texto mock.
- **No:** DevMenu. Va en otra spec.
- **No:** Supabase, scraper y GitHub Actions. Specs futuras.

## Risks

| Riesgo                                  | Mitigación                                                                                                    |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Versionado de Expo Router en SDK 58     | Instalar con `npx expo install` y consultar `https://docs.expo.dev/versions/v58.0.0/`; no confiar en memoria. |
| Cambio de entrypoint rompe el arranque  | El paso 1 se verifica con `npx tsc --noEmit` antes de continuar.                                              |
| Estado en memoria se pierde al recargar | Aceptado por diseño: es mock; la persistencia llega con la spec de offline.                                   |

## Qué **no** está en esta spec

- % de afinidad / match con el puesto y matching engine completo.
- Chips de filtro adicionales (`100% Match`, `Practicante`, `Remoto`, `Cerca de mí`).
- Persistencia real (Supabase / MMKV / TanStack Query).
- GPS y cálculo de distancia por coordenadas.
- DevMenu, notificaciones push y scraper.

Cada uno de esos, si llega, va en su propia spec.
