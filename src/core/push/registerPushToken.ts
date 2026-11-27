import { isRunningInExpoGo } from 'expo';
import Constants from 'expo-constants';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

import { supabase } from '@/core/api/supabase';
import { SINGLE_USER_ID } from '@/core/config/user';

const PUSH_CHANNEL_ID = 'default';

/**
 * Las push remotas no están disponibles en web ni en Expo Go en Android
 * (SDK 53+). En esos casos la app debe seguir funcionando sin registrar token.
 */
export function canUseRemotePush(): boolean {
  return Platform.OS !== 'web' && !(Platform.OS === 'android' && isRunningInExpoGo());
}

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

/**
 * Escribe el token Expo en el perfil del usuario único sin reemplazar el resto de columnas.
 */
export async function savePushToken(token: string): Promise<void> {
  const { data: profile, error: selectError } = await supabase
    .from('user_profiles')
    .select('id')
    .eq('id', SINGLE_USER_ID)
    .maybeSingle();

  if (selectError) {
    throw new Error(`No se pudo buscar el perfil para el token push: ${selectError.message}`);
  }

  const { error } = profile
    ? await supabase
        .from('user_profiles')
        .update({ expo_push_token: token })
        .eq('id', SINGLE_USER_ID)
    : await supabase
        .from('user_profiles')
        .insert({ id: SINGLE_USER_ID, expo_push_token: token });

  if (error) {
    throw new Error(`No se pudo guardar el token push: ${error.message}`);
  }
}

/**
 * Pide permisos, obtiene el token Expo y lo guarda en el perfil.
 * Devuelve null cuando el dispositivo no puede registrarse (web, permisos denegados,
 * falta de projectId o error de red).
 */
export async function registerForPushNotificationsAsync(): Promise<string | null> {
  if (!canUseRemotePush()) {
    console.warn(
      'Push remoto no disponible: usa un development build (Expo Go no soporta push en Android desde SDK 53).',
    );
    return null;
  }

  try {
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync(PUSH_CHANNEL_ID, {
        name: 'Notificaciones de empleo',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#FF231F7C',
      });
    }

    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    const finalStatus =
      existingStatus === 'granted'
        ? existingStatus
        : (await Notifications.requestPermissionsAsync()).status;

    if (finalStatus !== 'granted') {
      console.warn('Permisos de notificación denegados: no se registró el token push.');
      return null;
    }

    const projectId =
      Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;

    if (!projectId) {
      console.error('No se encontró el projectId de EAS en la configuración de la app.');
      return null;
    }

    const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
    await savePushToken(token);
    return token;
  } catch (error) {
    console.error('No se pudo registrar el token push:', error);
    return null;
  }
}

/**
 * Notificación local para verificar el handler y la presentación en Expo Go,
 * donde el push remoto no está disponible en Android.
 */
export async function sendLocalTestNotification(): Promise<void> {
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  const finalStatus =
    existingStatus === 'granted'
      ? existingStatus
      : (await Notifications.requestPermissionsAsync()).status;

  if (finalStatus !== 'granted') {
    throw new Error('Permisos de notificación denegados.');
  }

  await Notifications.scheduleNotificationAsync({
    content: {
      title: 'Notificación local de prueba',
      body: 'Expo Go muestra notificaciones locales; el push remoto requiere development build.',
      sound: 'default',
      data: { url: '/work/test' },
    },
    trigger: null,
  });
}

interface ExpoPushResponse {
  data?: Array<{ status: 'ok' | 'error'; message?: string }>;
  errors?: Array<{ code: string; message: string }>;
}

/**
 * Envía una notificación de prueba al token Expo del dispositivo a través de Expo Push API.
 */
export async function sendTestPushNotification(token: string): Promise<void> {
  const response = await fetch('https://exp.host/--/api/v2/push/send', {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      to: token,
      title: 'Notificación de prueba',
      body: 'El registro de push funciona correctamente.',
      sound: 'default',
      priority: 'high',
      channelId: PUSH_CHANNEL_ID,
    }),
  });

  if (!response.ok) {
    throw new Error(`Expo Push API respondió con el estado ${response.status}.`);
  }

  const result = (await response.json()) as ExpoPushResponse;

  if (result.errors?.length) {
    throw new Error(result.errors.map((error) => error.message).join('; '));
  }

  const ticket = result.data?.[0];
  console.log('Ticket push de prueba:', ticket);

  if (ticket?.status === 'error') {
    throw new Error(ticket.message ?? 'Expo rechazó el push de prueba.');
  }
}
