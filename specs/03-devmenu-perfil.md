# SPEC 03 — DevMenu de Perfil con gesto de 3 dedos

> **Estado:** Aprobado
> **Depende de:** SPEC 01, SPEC 02
> **Fecha:** 2026-11-15
> **Objetivo:** Reemplazar el dev menu de `expo-dev-client` por un panel oculto (bottom sheet estilo dev menu) en la pantalla de Perfil que despliega el formulario de edición al mantener pulsada la pantalla con 3 dedos.

## Scope

**Incluido:**

- Eliminar la integración con `expo-dev-client`: el archivo `src/core/devmenu/devMenu.ts`, su uso en `app/_layout.tsx`, el plugin en `app.json` y la dependencia en `package.json` / `package-lock.json`.
- Eliminar el modo de edición inline (`isEditing`) de `ProfileScreen` y sus imports de `consumePendingEditRequest` / `onEditProfileRequest`.
- Crear el componente `ProfileDevMenu` (`src/features/profile/presentation/components/ProfileDevMenu.tsx`): bottom sheet oscuro con `ProfileForm` dentro.
- Gesto de pulsación de 3 dedos (~1000 ms) sobre `ProfileScreen` que abre el panel solo si ya hay perfil.
- Guardar desde el panel con `saveProfile` (upsert en `user_profiles`) y cerrarlo; cancelar cierra sin guardar.
- Mantener el botón visible "Editar perfil" navegando a `/onboarding` (inciso A).

**Fuera de alcance (specs futuras):**

- Las demás secciones del DevMenu del README: mock de GPS, inspección de caché y push de prueba.
- El gesto de 3 dedos en pantallas distintas a Perfil.
- Cambios al flujo de onboarding.

## Data model

Esta spec no introduce estructuras de datos nuevas. Reutiliza:

- `UserProfile` (SPEC 01) como forma del formulario.
- `ProfileContext.saveProfile` (SPEC 02) para persistir el upsert en `user_profiles`.

El único estado nuevo es local de UI en `ProfileScreen`:

```ts
// ProfileScreen.tsx (estado local, no persistido)
const [isDevMenuOpen, setIsDevMenuOpen] = useState(false);
```

## Implementation plan

Cada paso deja el sistema funcional y verificable con `npx tsc --noEmit`.

1. Quitar `expo-dev-client`: eliminarlo de `plugins` en `app.json`, quitarlo de `package.json` y ejecutar `npm uninstall expo-dev-client` (actualiza `package-lock.json`). Verificar `npx tsc --noEmit`.
2. Borrar `src/core/devmenu/devMenu.ts` y quitar el `import { registerDevMenu }` y el `useEffect` que lo llama en `app/_layout.tsx`.
3. En `ProfileScreen.tsx`, quitar los imports de `consumePendingEditRequest` / `onEditProfileRequest`, el `useEffect` asociado y el bloque `if (isEditing)`. La pantalla queda solo con la vista de resumen y el botón "Editar perfil" → `/onboarding`.
4. Añadir a `ProfileForm` un prop opcional `variant?: "light" | "dark"` (por defecto `"light"`) que selecciona la paleta de chips, textos e input. El onboarding sigue en `"light"`.
5. Crear `ProfileDevMenu.tsx`: `Modal` transparente con `animationType="slide"`, overlay oscuro y sheet inferior (esquinas superiores redondeadas, grab handle, título "Editar perfil"), con `ProfileForm variant="dark"` y botones de guardar/cancelar. Recibe `visible`, `initialProfile`, `onSubmit` y `onClose`.
6. En `ProfileScreen.tsx`, agregar `isDevMenuOpen` y envolver el contenido en `GestureDetector` con `Gesture.LongPress().numberOfPointers(3).minDuration(1000)`; el callback abre el panel solo si `profile` existe. Renderizar `ProfileDevMenu`.
7. Envolver la raíz de `app/_layout.tsx` en `GestureHandlerRootView` si el gesto no responde (el Drawer ya provee uno; verificar antes de añadirlo).
8. Verificación final: `npx tsc --noEmit` sin errores y prueba manual en Expo Go.

## Acceptance criteria

- [ ] `npx tsc --noEmit` termina sin errores.
- [ ] `expo-dev-client` ya no aparece en `package.json`, en `package-lock.json` ni en `plugins` de `app.json`.
- [ ] `src/core/devmenu/devMenu.ts` no existe y no quedan referencias a `registerDevMenu`, `consumePendingEditRequest` ni `onEditProfileRequest`.
- [ ] `ProfileScreen` no tiene modo de edición inline.
- [ ] Con perfil guardado, mantener pulsada la pantalla de Perfil con 3 dedos (~1 s) abre el sheet.
- [ ] El sheet se ve oscuro, con esquinas superiores redondeadas, grab handle y título "Editar perfil".
- [ ] Guardar en el sheet hace upsert en `user_profiles`, cierra el sheet y actualiza el resumen del perfil.
- [ ] Cancelar/cerrar cierra el sheet sin modificar el perfil.
- [ ] Sin perfil guardado, el gesto no abre nada.
- [ ] El botón "Editar perfil" sigue navegando a `/onboarding`.
- [ ] El onboarding sigue mostrando `ProfileForm` con la paleta clara.

## Decisions

- **Sí:** reemplazar el dev menu de `expo-dev-client` por un panel propio. El dev menu nativo no funciona en Expo Go ni en producción.
- **Sí:** eliminar `expo-dev-client` (código y paquete). Era una vía solo de development build y no aporta al objetivo.
- **Sí:** bottom sheet oscuro estilo dev menu. Es lo pedido explícitamente.
- **Sí:** reutilizar `ProfileForm` y `ProfileContext.saveProfile`. No se duplica el formulario ni la persistencia.
- **Sí:** prop `variant` en `ProfileForm`. Permite reusarlo en el sheet oscuro sin tocar el onboarding.
- **Sí:** gesto de 3 dedos (~1000 ms) solo en Perfil y solo con perfil existente. Evita disparos accidentales y el caso sin perfil.
- **Sí:** el botón "Editar perfil" sigue yendo a `/onboarding` (inciso A). Mantiene el flujo visible y deja el gesto como vía oculta.
- **No:** GPS mock, inspección de caché y push de prueba. Van en specs futuras.
- **No:** gesto de 3 dedos en otras pantallas.

## Risks

| Riesgo                                                                              | Mitigación                                                                      |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| El gesto de 3 dedos no responde por falta de `GestureHandlerRootView`               | Envolver la raíz en `app/_layout.tsx` solo si la prueba falla.                  |
| El gesto de 3 dedos no es probable en simulador/emulador (requiere multitouch real) | Probar en dispositivo físico; en simulador puede no ser verificable.            |
| Eliminar `expo-dev-client` rompe el arranque si algo más lo importa                 | Buscar referencias y correr `npx tsc --noEmit` en el paso 1 antes de continuar. |
| El teclado tapa el input de ubicación dentro del sheet                              | Usar `KeyboardAvoidingView` y `keyboardShouldPersistTaps` dentro del sheet.     |

## Qué **no** está en esta spec

- Mock de GPS, inspección de caché y push de prueba.
- El gesto de 3 dedos fuera de la pantalla de Perfil.
- Cambios al onboarding.
- Autenticación y multiusuario.

Cada uno de esos, si llega, va en su propia spec.
