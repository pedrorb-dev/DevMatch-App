import { useEffect } from 'react';
import * as Notifications from 'expo-notifications';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import * as SystemUI from 'expo-system-ui';
import { StyleSheet } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import {
  canUseRemotePush,
  registerForPushNotificationsAsync,
} from '@/core/push/registerPushToken';
import { ThemeProvider, useTheme } from '@/core/theme/ThemeContext';
import { FavoritesProvider } from '@/features/jobs/presentation/context/FavoritesContext';
import { ProfileProvider } from '@/features/profile/presentation/context/ProfileContext';

function RootNavigator() {
  const { isDark, colors } = useTheme();

  useEffect(() => {
    // El Stack nativo deja el fondo del contenedor sin color; sin esto se ve
    // blanco durante las transiciones cuando el tema es oscuro.
    void SystemUI.setBackgroundColorAsync(colors.background);
  }, [colors.background]);

  return (
    <>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <Stack
        screenOptions={{
          headerShown: false,
          headerStyle: { backgroundColor: colors.surface },
          headerTintColor: colors.text,
          contentStyle: { backgroundColor: colors.background },
        }}
      >
        <Stack.Screen
          name="work/[id]"
          options={{ headerShown: true, title: 'Más Información' }}
        />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  useEffect(() => {
    if (!canUseRemotePush()) {
      return undefined;
    }

    void registerForPushNotificationsAsync();

    // El listener entrega el token nativo; volvemos a obtener el token Expo
    // para re-sincronizar el mismo valor que consume Expo Push API.
    let subscription: { remove(): void } | undefined;
    try {
      subscription = Notifications.addPushTokenListener(() => {
        void registerForPushNotificationsAsync();
      });
    } catch (error) {
      console.warn('No se pudo suscribir al cambio de token push:', error);
    }

    return () => subscription?.remove();
  }, []);

  return (
    <GestureHandlerRootView style={styles.root}>
      <SafeAreaProvider>
        <ThemeProvider>
          <ProfileProvider>
            <FavoritesProvider>
              <RootNavigator />
            </FavoritesProvider>
          </ProfileProvider>
        </ThemeProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
});
