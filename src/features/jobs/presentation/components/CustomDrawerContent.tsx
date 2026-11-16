import { Ionicons } from '@expo/vector-icons';
import { DrawerContentScrollView, type DrawerContentComponentProps } from 'expo-router/drawer';
import type { ComponentProps } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@/core/theme/ThemeContext';
import { useProfile } from '@/features/profile/presentation/context/ProfileContext';

type IoniconName = ComponentProps<typeof Ionicons>['name'];

const MENU_ITEMS: { route: string; label: string; icon: IoniconName }[] = [
  { route: 'feed', label: 'Inicio', icon: 'home-outline' },
  { route: 'favorites', label: 'Favoritos', icon: 'heart-outline' },
  { route: 'profile', label: 'Perfil', icon: 'person-outline' },
];

export function CustomDrawerContent(props: DrawerContentComponentProps) {
  const { profile } = useProfile();
  const { colors, spacing, radius, fontSize, fontWeight } = useTheme();
  const activeRoute = props.state.routes[props.state.index]?.name;

  const goTo = (route: string) => {
    props.navigation.navigate(route);
    props.navigation.closeDrawer();
  };

  return (
    <DrawerContentScrollView
      {...props}
      contentContainerStyle={[styles.scroll, { backgroundColor: colors.surface }]}
    >
      <View
        style={{
          margin: spacing.lg,
          padding: spacing.lg,
          borderRadius: radius.lg,
          backgroundColor: colors.primaryLight,
          gap: spacing.xs,
        }}
      >
        <Text
          style={{
            fontSize: fontSize.sm,
            fontWeight: fontWeight.semibold,
            color: colors.primaryText,
            textTransform: 'uppercase',
          }}
        >
          Mi perfil
        </Text>
        {profile ? (
          <></>
        ) : (
          <Text style={{ fontSize: fontSize.sm, color: colors.textSecondary }}>
            Perfil sin configurar
          </Text>
        )}
      </View>

      <View style={{ paddingHorizontal: spacing.sm, gap: spacing.xs }}>
        {MENU_ITEMS.map((item) => {
          const isActive = activeRoute === item.route;
          return (
            <Pressable
              key={item.route}
              onPress={() => goTo(item.route)}
              style={[
                styles.menuItem,
                {
                  gap: spacing.md,
                  paddingVertical: spacing.md,
                  paddingHorizontal: spacing.lg,
                  borderRadius: radius.md,
                  backgroundColor: isActive ? colors.primaryLight : 'transparent',
                },
              ]}
            >
              <Ionicons
                name={item.icon}
                size={20}
                color={isActive ? colors.primaryText : colors.textSecondary}
              />
              <Text
                style={{
                  fontSize: fontSize.md,
                  color: isActive ? colors.primaryText : colors.textSecondary,
                  fontWeight: isActive ? fontWeight.semibold : fontWeight.medium,
                }}
              >
                {item.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </DrawerContentScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flexGrow: 1,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
});
