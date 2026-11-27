# SPEC 11 — Orden del feed por cercanía

> **Estado:** Aprobado
> **Depende de:** SPEC 02, SPEC 10
> **Fecha:** 2026-11-27
> **Objetivo:** Obtener la ubicación del dispositivo con `expo-location` y ordenar el feed por distancia a la empresa (más cercanas primero), mostrando "a X km" en cada tarjeta, con las vacantes remotas siempre arriba y orden neutral como fallback sin permiso.

## Scope

**Incluido:**

- Instalar `expo-location` con `npx expo install expo-location` y añadir el config plugin a `app.json`.
- `src/core/location/useDeviceLocation.ts`: hook que pide permiso (`requestForegroundPermissionsAsync`) y devuelve `{ coords, status }`.
- `src/core/location/distance.ts`: `haversineKm(a, b)`.
- Ampliar `JobOffer` con `lat: number | null` y `lng: number | null`, y `JobMapper`/`VacanteRow` para leerlas.
- Ordenar el feed: remoto primero → distancia ascendente → sin coordenadas al final en orden neutral.
- Mostrar "a X km" en `JobCard` (solo cuando hay distancia).
- Fallback sin permiso/coords: orden actual por `created_at`.

**Fuera de alcance (specs futuras):**

- Geocodificación (SPEC 10).
- Filtro por radio (se ordena sin umbral).
- Mapa o UI de distancia en la pantalla de detalle (`WorkScreen`).
- Permisos en background y seguimiento continuo.
- Re-ordenar al moverse (la ubicación se lee una vez al montar).

## Data model

```ts
// JobOffer (ampliado)
interface JobOffer {
  // ...campos actuales
  lat: number | null;
  lng: number | null;
}

// useDeviceLocation
type LocationStatus = "granted" | "denied" | "undetermined";
type UseDeviceLocation = {
  coords: { latitude: number; longitude: number } | null;
  status: LocationStatus;
};
```

## Implementation plan

Cada paso deja la app funcional y verificable con `npx tsc --noEmit`.

1. Instalar `expo-location` y añadir el config plugin a `app.json`. Verificar `npx tsc --noEmit`.
2. Crear `src/core/location/distance.ts` con `haversineKm`. Verificar `npx tsc --noEmit`.
3. Crear `src/core/location/useDeviceLocation.ts` (permiso + `getCurrentPositionAsync`). Verificar `npx tsc --noEmit`.
4. Ampliar `JobOffer`, `VacanteRow` y `JobMapper` con `lat`/`lng`. Verificar `npx tsc --noEmit`.
5. Añadir el orden por cercanía en `FeedScreen` (helper `sortByDistance`): remoto primero, luego distancia asc, sin coords al final. Verificar `npx tsc --noEmit`.
6. Mostrar "a X km" en `JobCard` cuando la vacante tenga coordenadas y haya ubicación. Verificar `npx tsc --noEmit`.
7. Verificación manual en development build (GPS) y en Expo Go si `expo-location` lo soporta en SDK 58.

## Acceptance criteria

- [ ] `npx tsc --noEmit` termina sin errores.
- [ ] `expo-location` está instalado y el config plugin está en `app.json`.
- [ ] `JobOffer` tiene `lat`/`lng` y `JobMapper` las lee desde `vacantes`.
- [ ] Con permiso concedido: el feed muestra remoto primero, luego por distancia ascendente.
- [ ] Las tarjetas con coordenadas muestran "a X km"; las que tienen `lat/lng null` no muestran distancia y van al final.
- [ ] Sin permiso de ubicación, el feed queda en orden neutral (`created_at`) sin "km".
- [ ] No cambia el comportamiento de Favoritos ni del detalle.

## Decisions

- **Sí:** `expo-location` + hook `useDeviceLocation`. **No:** otra librería de geolocalización.
- **Sí:** haversine en la app. **No:** SQL/PostGIS.
- **Sí:** remoto siempre primero (distancia no aplica → se trata como 0). **No:** remoto al final.
- **Sí:** sin umbral, solo ordenar. **No:** radio máximo.
- **Sí:** fallback neutral (`created_at`) sin permiso. **No:** usar el `ubicacion_texto` del perfil.
- **Sí:** leer la ubicación una vez al montar. **No:** seguimiento continuo.

## Risks

| Riesgo                                        | Mitigación                                                                      |
| --------------------------------------------- | ------------------------------------------------------------------------------- |
| Permiso de ubicación denegado                 | Fallback a orden neutral sin "km".                                              |
| `expo-location` en Expo Go (SDK 58)           | Verificar contra la doc v58; si no está en Expo Go, requiere development build. |
| Vacantes viejas sin `lat/lng`                 | Van al final en orden neutral (mitigado por el backfill de SPEC 10).            |
| El usuario se mueve y el orden queda obsoleto | Aceptado: se lee una vez al montar.                                             |

## Qué **no** está en esta spec

- Geocodificación de vacantes.
- Radio/filtro por distancia.
- Mapa.
- Seguimiento continuo o permisos en background.

Cada uno de esos, si llega, va en su propia spec.
