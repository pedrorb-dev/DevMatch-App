import { Ionicons } from '@expo/vector-icons';
import { DrawerContentScrollView, type DrawerContentComponentProps } from 'expo-router/drawer';
import type { ComponentProps } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/core/theme/theme';
import { useProfile } from '@/features/profile/presentation/context/ProfileContext';

type IoniconName = ComponentProps<typeof Ionicons>['name'];

const MENU_ITEMS: { route: string; label: string; icon: IoniconName }[] = [
  { route: 'feed', label: 'Inicio', icon: 'home-outline' },
  { route: 'favorites', label: 'Favoritos', icon: 'heart-outline' },
  { route: 'profile', label: 'Perfil', icon: 'person-outline' },
];

export function CustomDrawerContent(props: DrawerContentComponentProps) {
  const { profile } = useProfile();
  const activeRoute = props.state.routes[props.state.index]?.name;

  const goTo = (route: string) => {
    props.navigation.navigate(route);
    props.navigation.closeDrawer();
  };

  return (
    <DrawerContentScrollView {...props} contentContainerStyle={styles.scroll}>
      {<View style={styles.profileCard}>
        <Text style={styles.profileTitle}>Mi perfil</Text>
        {profile ? (
          <>
          {/*<Text style={styles.profileStack} numberOfLines={2}>
              {profile.stack.join(' - ')}
            </Text>
            <Text style={styles.profileMeta}>
              {profile.experienceYears} años - Inglés {profile.englishLevel}
            </Text>
            <Text style={styles.profileMeta}>{profile.locationText}</Text>*/}
          </>
        ) : (
          <Text style={styles.profileMeta}>Perfil sin configurar</Text>
        )}
      </View>}

      <View style={styles.menu}>
        {MENU_ITEMS.map((item) => {
          const isActive = activeRoute === item.route;
          return (
            <Pressable
              key={item.route}
              onPress={() => goTo(item.route)}
              style={[styles.menuItem, isActive && styles.menuItemActive]}
            >
              <Ionicons
                name={item.icon}
                size={20}
                color={isActive ? theme.colors.primary : theme.colors.textSecondary}
              />
              <Text style={[styles.menuLabel, isActive && styles.menuLabelActive]}>
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
    backgroundColor: theme.colors.surface,
  },
  profileCard: {
    margin: theme.spacing.lg,
    padding: theme.spacing.lg,
    borderRadius: theme.radius.lg,
    backgroundColor: theme.colors.primaryLight,
    gap: theme.spacing.xs,
  },
  profileTitle: {
    fontSize: theme.fontSize.sm,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.primary,
    textTransform: 'uppercase',
  },
  profileStack: {
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.text,
  },
  profileMeta: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
  menu: {
    paddingHorizontal: theme.spacing.sm,
    gap: theme.spacing.xs,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.radius.md,
  },
  menuItemActive: {
    backgroundColor: theme.colors.primaryLight,
  },
  menuLabel: {
    fontSize: theme.fontSize.md,
    color: theme.colors.textSecondary,
    fontWeight: theme.fontWeight.medium,
  },
  menuLabelActive: {
    color: theme.colors.primary,
    fontWeight: theme.fontWeight.semibold,
  },
});
