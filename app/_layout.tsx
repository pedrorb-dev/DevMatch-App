import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { FavoritesProvider } from '@/features/jobs/presentation/context/FavoritesContext';
import { ProfileProvider } from '@/features/profile/presentation/context/ProfileContext';

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <ProfileProvider>
        <FavoritesProvider>
          <StatusBar style="dark" />
          <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen
              name="work/[id]"
              options={{ headerShown: true, title: 'Detalle' }}
            />
          </Stack>
        </FavoritesProvider>
      </ProfileProvider>
    </SafeAreaProvider>
  );
}
