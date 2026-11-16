import { registerDevMenuItems } from 'expo-dev-client';
import { router } from 'expo-router';
import { Alert } from 'react-native';

import { SINGLE_USER_ID } from '@/core/config/user';

type EditProfileListener = () => void;

const editProfileListeners = new Set<EditProfileListener>();
let pendingEditRequest = false;
let hasRegistered = false;

export function onEditProfileRequest(listener: EditProfileListener): () => void {
  editProfileListeners.add(listener);
  return () => {
    editProfileListeners.delete(listener);
  };
}

/**
 * Indica si el DevMenu pidió editar el perfil mientras la pantalla no estaba
 * montada (en ese caso el menú navegó a `/profile`). La bandera se consume.
 */
export function consumePendingEditRequest(): boolean {
  const pending = pendingEditRequest;
  pendingEditRequest = false;
  return pending;
}

function requestEditProfile() {
  if (editProfileListeners.size === 0) {
    // La pantalla de perfil no está montada: navegamos y dejamos la intención
    // pendiente para que se active el modo edición al montarse.
    pendingEditRequest = true;
    router.push('/profile');
    return;
  }

  editProfileListeners.forEach((listener) => listener());
}

function showConfig() {
  const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL ?? '(sin definir)';

  Alert.alert(
    'Configuración',
    [
      `SINGLE_USER_ID: ${SINGLE_USER_ID}`,
      `Supabase URL: ${supabaseUrl}`,
      `Entorno: ${__DEV__ ? 'desarrollo' : 'producción'}`,
    ].join('\n'),
  );
}

/**
 * Registra los items personalizados en el DevMenu de Expo. Debe llamarse una
 * sola vez al arrancar. Solo hace algo en desarrollo y en un development build
 * (en Expo Go no existe el módulo nativo y el error se ignora).
 */
export function registerDevMenu(): void {
  if (!__DEV__ || hasRegistered) {
    return;
  }

  hasRegistered = true;

  registerDevMenuItems([
    {
      name: 'Editar perfil (inline)',
      callback: requestEditProfile,
      shouldCollapse: true,
    },
    {
      name: 'Ver config',
      callback: showConfig,
      shouldCollapse: true,
    },
  ]).catch((error: unknown) => {
    console.warn(
      'No se pudo registrar el DevMenu. Se requiere un development build (no Expo Go).',
      error,
    );
  });
}
