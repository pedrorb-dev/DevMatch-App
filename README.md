# DevMatch — Buscador Inteligente de Vacantes Tech

Aplicación móvil multiplataforma diseñada para automatizar la búsqueda de empleo en tecnología, filtrando y priorizando ofertas según tu **stack tecnológico**, **años de experiencia**, **nivel de inglés** y **cercanía geográfica** respecto a tu ubicación actual.

## Características Principales

- **Perfil Técnico Personalizado:** Configuración de stack (ej. `Angular` + `Spring Boot`), nivel de inglés (`B1`, `B2`, `C1`), años de experiencia y ubicación GPS.
- **Motor de Matching Inteligente:**
  - **Modo Practicante (`0 años`):** Mapea automáticamente perfiles sin experiencia a vacantes de tipo _Practicante, Becario, Trainee, Intern_ o _Junior_, descartando ofertas que exijan experiencia previa.
  - **Compatibilidad de Stack:** Calcula un porcentaje de afinidad detectando coincidencias completas (100%) o parciales (ej. solo `Spring Boot` o solo `Angular`).
  - **Filtro Flexible de Inglés:** Si tu nivel es `B1`, prioriza ofertas `B1` o sin requisito de idioma, muestra ofertas `B2` con una etiqueta informativa y filtra ofertas `C1 / Bilingüe`.
- **Geolocalización y Modalidad:** Prioriza vacantes **Remotas** y ordena las ofertas **Presenciales / Híbridas** por distancia en kilómetros respecto a las coordenadas del dispositivo.
- **Navegación con Custom Drawer y Filtros Inline:**
  - **Drawer Personalizado:** Menú lateral con tarjeta resumen de tu perfil activo y acceso directo a **Inicio**, **Favoritos** y **Perfil**.
  - **Chipset Inline en Inicio:** Barra horizontal de filtros rápidos (`Nuevos hoy`, `100% Match`, `Practicante`, `Remoto`, `Cerca de mí`) procesados en memoria (`useMemo`) para una respuesta instantánea incluso sin conexión.
  - **Gestión de Favoritos:** Posibilidad de guardar vacantes desde el feed o desde el detalle para consultarlas en su propia pantalla del Drawer mediante _Optimistic Updates_.
- **Detalle de Vacante y Acceso Directo a la Oferta Real:** Pantalla de detalle (`WorkScreen`) fuera del Drawer que muestra el resumen de la oferta, permite marcarla como favorita e incluye un botón principal (_"Ver oferta original / Postularme"_) para abrir directamente el enlace real (`url_oferta`).
- **Soporte Offline-First y Retención de 15 Días:**
  - Almacenamiento en caché local con **TanStack Query + MMKV** para navegar sin Wi-Fi, sincronizando y reemplazando datos al recuperar internet.
  - Purga automática en Supabase al llegar al **día 16** (`> 15 días`), protegiendo las vacantes que hayas marcado en **Favoritos**.
- **Alertas Push Automáticas:** Notificaciones push enviadas directamente al dispositivo cuando el scraper diario detecta una vacante con alto porcentaje de compatibilidad.
- **DevMenu Integrado en Perfil:** Panel oculto dentro de la pantalla de Perfil para actualizar/simular coordenadas GPS, probar presets de experiencia o stack, inspeccionar la caché de TanStack Query y disparar notificaciones de prueba.

## Stack Tecnológico

### Frontend (Mobile)

- **Framework:** React Native + Expo (SDK moderno) + TypeScript
- **Navegación:** Expo Router (`Slot`, `Stack`, `Drawer`, `Redirect`) + `react-native-safe-area-context` (`SafeAreaView`)
- **Estado y Caché Offline:** TanStack Query (`@tanstack/react-query`) + Persistencia local (`react-native-mmkv`) + `@react-native-community/netinfo`
- **UI e Iconografía:** Design Tokens centralizados (Paleta **Indigo** `#4F46E5` + **Blanco** `#FFFFFF`), `FlatList` optimizado e `@expo/vector-icons` (**Ionicons**)
- **Geolocalización, Notificaciones y Enlaces Externos:** `expo-location`, `expo-notifications` y `expo-web-browser` / `Linking`

### Backend & Base de Datos

- **BaaS / DB:** Supabase (PostgreSQL + extensión **PostGIS** para consultas geoespaciales por distancia)

### Automatización & Web Scraping

- **Scraper:** Python + **Scrapy** (pipelines de limpieza, normalización y geocodificación con Nominatim)
- **CI/CD & Scheduler:** GitHub Actions (ejecución programada **1 vez al día** vía `cron` + ejecución manual con `workflow_dispatch`)

## Arquitectura del Proyecto

El proyecto implementa **Feature-Based Architecture + Clean Architecture + Separación por Capas**, manteniendo **Expo Router** como una capa delgada de enrutamiento desacoplada de la lógica de negocio.

### Principios de Diseño

1. **Separación por Capas dentro de cada Feature:**
   - `domain/`: Entidades puras (`JobOffer`, `UserProfile`), interfaces de repositorios y tipos estrictos (`types`).
   - `infrastructure/`: Comunicación con Supabase, DTOs (`snake_case`), Mappers hacia entidades (`camelCase`) y servicios nativos (GPS).
   - `presentation/`: Pantallas (`FeedScreen`, `FavoritesScreen`, `ProfileScreen`, `WorkScreen`), componentes UI (`CustomDrawerContent`, `InlineFilterChips`, `JobCard`), interfaces `Props`, custom hooks con TanStack Query y estilos locales.
2. **Design Tokens Centralizados:** Los colores (Indigo `#4F46E5`, Blanco `#FFFFFF` / `#F8FAFC`), espaciados y tipografías viven en `src/core/theme/theme.ts`, mientras que cada componente encapsula su propio `StyleSheet`.
3. **Flujo de Navegación:**
   - `app/_layout.tsx` provee el contexto global (`SafeAreaProvider`, `QueryClientProvider`) y renderiza `<Slot />`.
   - `app/index.tsx` evalúa si existe un perfil local; si no existe, redirige con `<Redirect href="/onboarding" />`, de lo contrario entra al grupo `<Drawer />`.
   - `app/(drawer)/_layout.tsx` renderiza el **Custom Drawer** con acceso a **Inicio**, **Favoritos** y **Perfil**.
   - `app/work/[id].tsx` vive dentro del `<Stack />` raíz (fuera del Drawer) para abrir `WorkScreen` en pantalla completa con navegación de regreso limpia y botón directo hacia la oferta real.

### Estructura de Carpetas

```text
devmatch/
├── app/                              # Capa delgada de enrutamiento (Expo Router)
│   ├── _layout.tsx                   # Root Layout con Providers, <Stack /> y <Slot />
│   ├── index.tsx                     # Control de acceso con <Redirect />
│   ├── onboarding.tsx                # Configuración inicial del perfil
│   ├── (drawer)/                     # Grupo de navegación con Custom Drawer
│   │   ├── _layout.tsx               # Configuración del Drawer + CustomDrawerContent
│   │   ├── index.tsx                 # Inicio (Feed con chipset inline del día)
│   │   ├── favorites.tsx             # Favoritos (Vacantes guardadas)
│   │   └── profile.tsx               # Perfil de usuario + DevMenu integrado
│   └── work/
│       └── [id].tsx                  # Renderiza <WorkScreen /> pasando el id
│
├── src/
│   ├── core/                         # Utilidades transversales de la aplicación
│   │   ├── api/                      # Cliente de Supabase y configuración QueryClient
│   │   ├── storage/                  # Persistencia offline (MMKV + NetInfo)
│   │   └── theme/
│   │       └── theme.ts              # Design Tokens centralizados (Indigo & Blanco)
│   │
│   └── features/
│       ├── jobs/                     # Dominio de Vacantes y Favoritos
│       │   ├── domain/
│       │   │   ├── entities/         # JobOffer.ts
│       │   │   ├── repositories/     # JobRepository.ts (interfaces)
│       │   │   └── types/            # WorkModality, EnglishLevel, JobFilterChip
│       │   ├── infrastructure/
│       │   │   ├── datasources/      # SupabaseJobDatasource.ts
│       │   │   ├── mappers/          # JobMapper.ts
│       │   │   └── repositories/     # JobRepositoryImpl.ts
│       │   └── presentation/
│       │       ├── components/       # JobCard.tsx, InlineFilterChips.tsx, CustomDrawerContent.tsx
│       │       ├── hooks/            # useJobsQuery.ts, useToggleFavoriteMutation.ts
│       │       └── screens/          # FeedScreen.tsx, FavoritesScreen.tsx, WorkScreen.tsx
│       │
│       ├── profile/                  # Dominio de Perfil y Geolocalización
│       │   ├── domain/
│       │   ├── infrastructure/
│       │   └── presentation/
│       │       └── screens/          # ProfileScreen.tsx, OnboardingScreen.tsx
│       │
│       └── dev-menu/                 # Herramientas de desarrollo en Perfil
│           └── presentation/
│               └── components/       # DevMenuSection.tsx (GPS mock, caché, push test)
│
├── scraper/                          # Proyecto Scrapy en Python
│   ├── scrapy.cfg
│   ├── geocache.json                 # Caché local de coordenadas por ciudad
│   └── job_scraper/
│       ├── items.py                  # Modelo estandarizado de la vacante
│       ├── pipelines.py              # Limpieza, scoring, PostGIS y Expo Push
│       ├── settings.py
│       └── spiders/                  # Spiders por portal de empleo
│
└── .github/
    └── workflows/
        └── daily_scrape.yml          # Cron diario (1 vez/día) para ejecutar Scrapy
```

## Modelo de Datos (Supabase)

### Tabla: `vacantes`

| Columna               | Tipo               | Descripción                                                                     |
| :-------------------- | :----------------- | :------------------------------------------------------------------------------ |
| `id`                  | `uuid` (PK)        | Identificador único de la vacante.                                              |
| `titulo`              | `text`             | Título normalizado de la oferta.                                                |
| `empresa`             | `text`             | Nombre de la empresa reclutadora.                                               |
| `modalidad`           | `text`             | `Remoto`, `Híbrido` o `Presencial`.                                             |
| `resumen_descripcion` | `text`             | Extracto limpio (~600 caracteres) con requisitos clave para lectura offline.    |
| `stack_detectado`     | `text[]`           | Tecnologías identificadas (ej. `['Angular', 'Spring Boot']`).                   |
| `nivel_ingles`        | `text`             | `No especificado`, `B1`, `B2` o `C1`.                                           |
| `es_practicante`      | `boolean`          | `true` si aplica para 0 años de experiencia / becario / trainee.                |
| `ubicacion_texto`     | `text`             | Ciudad y estado extraídos del portal.                                           |
| `coordenadas`         | `geography(Point)` | Punto geográfico `(lng, lat)` para cálculo de distancia con PostGIS.            |
| `url_oferta`          | `text` (Unique)    | Enlace directo utilizado por el botón de `WorkScreen` para ir a la oferta real. |
| `created_at`          | `timestamptz`      | Fecha de inserción (usada para filtrar vacantes del día y purgar en el día 16). |

### Tabla: `user_profiles`

| Columna            | Tipo               | Descripción                                                 |
| :----------------- | :----------------- | :---------------------------------------------------------- |
| `id`               | `uuid` (PK)        | Identificador del dispositivo / usuario.                    |
| `stack`            | `text[]`           | Tecnologías del usuario (ej. `['Angular', 'Spring Boot']`). |
| `experiencia_anos` | `integer`          | Años de experiencia (`0` activa el modo practicante).       |
| `nivel_ingles`     | `text`             | Nivel actual (`B1`, `B2`, `C1`).                            |
| `coordenadas`      | `geography(Point)` | Última ubicación GPS registrada del teléfono.               |
| `expo_push_token`  | `text`             | Token para envío de notificaciones push desde el pipeline.  |

### Tabla: `saved_jobs` (Favoritos)

| Columna    | Tipo          | Descripción                                                |
| :--------- | :------------ | :--------------------------------------------------------- |
| `id`       | `uuid` (PK)   | Identificador único del registro guardado.                 |
| `user_id`  | `uuid` (FK)   | Referencia a `user_profiles(id)`.                          |
| `job_id`   | `uuid` (FK)   | Referencia a `vacantes(id)` con `ON DELETE CASCADE`.       |
| `saved_at` | `timestamptz` | Fecha en la que el usuario marcó la vacante como favorita. |

## Automatización y Política de Retención (15 Días)

El workflow `.github/workflows/daily_scrape.yml` ejecuta el pipeline **1 vez al día** (07:30 AM hora centro de México):

1. **Extracción y Normalización:** Scrapy recolecta vacantes recientes, detecta modalidad (`Remoto` / `Híbrido` / `Presencial`), stack tecnológico, nivel de inglés y perfil practicante.
2. **Geocodificación:** Convierte `ubicacion_texto` a coordenadas `(lat, lng)` usando `geocache.json` y Nominatim.
3. **Inserción y Notificaciones:** Guarda nuevas vacantes en Supabase (evitando duplicados por `url_oferta`) y envía alertas vía Expo Push API cuando hay alta afinidad con `user_profiles`.
4. **Purga Automática al Día 16:** Al finalizar el pipeline, se eliminan las vacantes que superan los **15 días** de antigüedad, excluyendo aquellas que el usuario haya guardado en **Favoritos**:

```sql
DELETE FROM vacantes
WHERE created_at < NOW() - INTERVAL '15 days'
  AND id NOT IN (SELECT job_id FROM saved_jobs);
```

## Inicio Rápido (Desarrollo Local)

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/devmatch.git
cd devmatch
```

### 2. Configurar la App Móvil (React Native + Expo)

```bash
npm install
```

Crea un archivo `.env` en la raíz con tus credenciales de Supabase:

```env
EXPO_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=tu-anon-key
```

Inicia el servidor de desarrollo:

```bash
npx expo start
```

### 3. Configurar el Scraper (Python + Scrapy)

```bash
cd scraper
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install scrapy supabase requests python-dotenv
```

Ejecuta una prueba local del spider:

```bash
scrapy crawl empleos_spider
```

## Roadmap de Desarrollo

- [ ] **Fase 1: Base de Datos y Core Mobile**
  - [ ] Crear tablas `vacantes`, `user_profiles` y `saved_jobs` con PostGIS habilitado en Supabase.
  - [ ] Inicializar proyecto Expo con TypeScript y configurar `theme.ts` (Indigo + Blanco).
  - [ ] Implementar navegación con `Slot`, `Redirect`, `Stack`, `SafeAreaView` y el **Custom Drawer** (`Inicio`, `Favoritos`, `Perfil`).
- [ ] **Fase 2: Features de Vacantes, Favoritos y Perfil**
  - [ ] Construir `FeedScreen` con `FlatList`, chipset inline del día y botón de favorito en cada tarjeta.
  - [ ] Implementar `FavoritesScreen` con _Optimistic Updates_ y `WorkScreen` en `app/work/[id].tsx` con el botón para abrir la oferta real.
  - [ ] Desarrollar `ProfileScreen` (Stack, Inglés B1, 0 años, GPS) integrando el `DevMenu`.
  - [ ] Configurar caché offline con TanStack Query + MMKV + NetInfo.
- [ ] **Fase 3: Scraper y Automatización**
  - [ ] Desarrollar spider en Scrapy y pipeline de normalización/geocodificación.
  - [ ] Configurar GitHub Action diario (`daily_scrape.yml`), purga al día 16 respetando favoritos y notificaciones Expo Push.
