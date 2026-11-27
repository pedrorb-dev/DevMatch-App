import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';

import { useTheme } from '@/core/theme/ThemeContext';

import type { UserProfile } from '../../domain/entities/UserProfile';
import { ProfileDevMenu } from '../components/ProfileDevMenu';
import { useProfile } from '../context/ProfileContext';

export function ProfileScreen() {
  const router = useRouter();
  const { profile, saveProfile, clearProfile } = useProfile();
  const { colors, spacing, radius, fontSize, fontWeight } = useTheme();
  const [isDevMenuOpen, setIsDevMenuOpen] = useState(false);

  const openDevMenuGesture = Gesture.LongPress()
    .numberOfPointers(3)
    .minDuration(1000)
    .onEnd((_event, success) => {
      if (success && profile) {
        setIsDevMenuOpen(true);
      }
    })
    .runOnJS(true);

  const handleClear = async () => {
    await clearProfile();
    router.replace('/onboarding');
  };

  const handleDevMenuSubmit = async (next: UserProfile) => {
    await saveProfile(next);
    setIsDevMenuOpen(false);
  };

  if (!profile) {
    return (
      <View style={[styles.centered, { backgroundColor: colors.background }]}>
        <Text style={{ fontSize: fontSize.sm, color: colors.textSecondary }}>
          No hay perfil configurado.
        </Text>
      </View>
    );
  }

  return (
    <GestureDetector gesture={openDevMenuGesture}>
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <ScrollView
          style={[styles.container, { backgroundColor: colors.background }]}
          contentContainerStyle={{
            padding: spacing.lg,
            gap: spacing.md,
            paddingBottom: spacing.xxl,
          }}
        >
          <View
            style={{
              backgroundColor: colors.surface,
              borderRadius: radius.lg,
              padding: spacing.lg,
              borderWidth: 1,
              borderColor: colors.border,
              gap: spacing.xs,
            }}
          >
            <Text
              style={{
                marginTop: spacing.sm,
                fontSize: fontSize.xs,
                fontWeight: fontWeight.semibold,
                color: colors.textSecondary,
                textTransform: 'uppercase',
              }}
            >
              Stack
            </Text>
            <View style={[styles.stackRow, { gap: spacing.sm }]}>
              {profile.stack.map((tech) => (
                <View
                  key={tech}
                  style={{
                    paddingVertical: spacing.xs,
                    paddingHorizontal: spacing.sm,
                    borderRadius: radius.full,
                    backgroundColor: colors.primaryLight,
                  }}
                >
                  <Text style={{ fontSize: fontSize.sm, color: colors.primaryText, fontWeight: fontWeight.medium }}>
                    {tech}
                  </Text>
                </View>
              ))}
            </View>

            <Text
              style={{
                marginTop: spacing.sm,
                fontSize: fontSize.xs,
                fontWeight: fontWeight.semibold,
                color: colors.textSecondary,
                textTransform: 'uppercase',
              }}
            >
              Experiencia
            </Text>
            <Text style={{ fontSize: fontSize.md, color: colors.text }}>
              {profile.experienceYears} años
            </Text>

            <Text
              style={{
                marginTop: spacing.sm,
                fontSize: fontSize.xs,
                fontWeight: fontWeight.semibold,
                color: colors.textSecondary,
                textTransform: 'uppercase',
              }}
            >
              Inglés
            </Text>
            <Text style={{ fontSize: fontSize.md, color: colors.text }}>{profile.englishLevel}</Text>

            <Text
              style={{
                marginTop: spacing.sm,
                fontSize: fontSize.xs,
                fontWeight: fontWeight.semibold,
                color: colors.textSecondary,
                textTransform: 'uppercase',
              }}
            >
              Ubicación
            </Text>
            <Text style={{ fontSize: fontSize.md, color: colors.text }}>{profile.locationText}</Text>
          </View>
          
          
          <Pressable
            style={{
              paddingVertical: spacing.lg,
              borderRadius: radius.md,
              backgroundColor: colors.primary,
              alignItems: 'center',
            }}
            onPress={() => {if(profile) {
              setIsDevMenuOpen(true);
            } else {
              router.push('/onboarding');
            }
          
          }}
            accessibilityRole="button"
          >
            <Text style={{ fontSize: fontSize.md, fontWeight: fontWeight.semibold, color: colors.white }}>
              Editar perfil
            </Text>
          </Pressable>

          <Pressable style={{ paddingVertical: spacing.md, alignItems: 'center' }} onPress={handleClear} accessibilityRole="button">
            <Text style={{ fontSize: fontSize.sm, fontWeight: fontWeight.medium, color: colors.danger }}>
              Borrar perfil
            </Text>
          </Pressable>
        </ScrollView>

        <ProfileDevMenu
          visible={isDevMenuOpen}
          initialProfile={profile}
          onSubmit={handleDevMenuSubmit}
          onClose={() => setIsDevMenuOpen(false)}
        />
      </View>
    </GestureDetector>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stackRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
});
