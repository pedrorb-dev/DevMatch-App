import { Ionicons } from '@expo/vector-icons';
import { Tabs, type BottomTabNavigationOptions } from 'expo-router/tabs';
import type { ComponentProps } from 'react';
import type { OpaqueColorValue } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/core/theme/ThemeContext';

type IoniconName = ComponentProps<typeof Ionicons>['name'];

const tabBarIcon =
  (focusedIcon: IoniconName, unfocusedIcon: IoniconName): NonNullable<BottomTabNavigationOptions['tabBarIcon']> =>
  ({ focused, color, size }) => (
    <Ionicons
      name={focused ? focusedIcon : unfocusedIcon}
      size={size}
      color={color as string | OpaqueColorValue}
    />
  );

export default function TabsLayout() {
  const { colors, radius, spacing } = useTheme();
  const insets = useSafeAreaInsets();

  return (
    <Tabs
      screenOptions={{
        headerTintColor: colors.text,
        headerStyle: { backgroundColor: colors.surface },
        tabBarShowLabel: true,
        tabBarActiveTintColor: colors.primaryText,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarActiveBackgroundColor: colors.primaryLight,
        tabBarItemStyle: {
          borderRadius: radius.full,
          marginHorizontal: spacing.sm,
          marginVertical: spacing.xs,
          paddingHorizontal: spacing.sm,
        },
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          height: 60 + insets.bottom,
        },
        sceneStyle: { backgroundColor: colors.background },
      }}
    >
      <Tabs.Screen
        name="feed"
        options={{ title: 'Inicio', tabBarIcon: tabBarIcon('home', 'home-outline') }}
      />
      <Tabs.Screen
        name="favorites"
        options={{ title: 'Favoritos', tabBarIcon: tabBarIcon('heart', 'bookmark-outline') }}
      />
      <Tabs.Screen
        name="profile"
        options={{ title: 'Perfil', tabBarIcon: tabBarIcon('person', 'person-outline') }}
      />
    </Tabs>
  );
}
