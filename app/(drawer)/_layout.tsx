import { Drawer } from 'expo-router/drawer';

import { useTheme } from '@/core/theme/ThemeContext';
import { CustomDrawerContent } from '@/features/jobs/presentation/components/CustomDrawerContent';

export default function DrawerLayout() {
  const { colors } = useTheme();

  return (
    <Drawer
      drawerContent={(props) => <CustomDrawerContent {...props} />}
      screenOptions={{
        headerTintColor: colors.text,
        headerStyle: { backgroundColor: colors.surface },
        drawerActiveTintColor: colors.primary,
        drawerInactiveTintColor: colors.textSecondary,
        sceneStyle: { backgroundColor: colors.background },
      }}
    >
      <Drawer.Screen name="feed" options={{ title: 'Inicio' }} />
      <Drawer.Screen name="favorites" options={{ title: 'Favoritos' }} />
      <Drawer.Screen name="profile" options={{ title: 'Perfil' }} />
    </Drawer>
  );
}
