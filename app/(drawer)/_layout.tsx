import { Drawer } from 'expo-router/drawer';

import { theme } from '@/core/theme/theme';
import { CustomDrawerContent } from '@/features/jobs/presentation/components/CustomDrawerContent';

export default function DrawerLayout() {
  return (
    <Drawer
      drawerContent={(props) => <CustomDrawerContent {...props} />}
      screenOptions={{
        headerTintColor: theme.colors.text,
        headerStyle: { backgroundColor: theme.colors.surface },
        drawerActiveTintColor: theme.colors.primary,
        drawerInactiveTintColor: theme.colors.textSecondary,
        sceneStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Drawer.Screen name="feed" options={{ title: 'Inicio' }} />
      <Drawer.Screen name="favorites" options={{ title: 'Favoritos' }} />
      <Drawer.Screen name="profile" options={{ title: 'Perfil' }} />
    </Drawer>
  );
}
