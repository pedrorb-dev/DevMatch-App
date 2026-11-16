import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { registerDevMenu } from '@/core/devmenu/devMenu';
import { FavoritesProvider } from '@/features/jobs/presentation/context/FavoritesContext';
import { ProfileProvider } from '@/features/profile/presentation/context/ProfileContext';

export default function RootLayout() {
  useEffect(() => {
    registerDevMenu();
  }, []);

  return (
    <SafeAreaProvider>
      <ProfileProvider>
        <FavoritesProvider>
          <StatusBar style="dark" />
          <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen
              name="work/[id]"
              options={{ headerShown: true, title: 'Más Información' }}
            />
          </Stack>
        </FavoritesProvider>
      </ProfileProvider>
    </SafeAreaProvider>
  );
}
