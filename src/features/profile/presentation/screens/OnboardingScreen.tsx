import { useRouter } from 'expo-router';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text } from 'react-native';

import { useTheme } from '@/core/theme/ThemeContext';

import type { UserProfile } from '../../domain/entities/UserProfile';
import { ProfileForm } from '../components/ProfileForm';
import { useProfile } from '../context/ProfileContext';

export function OnboardingScreen() {
  const router = useRouter();
  const { profile, saveProfile } = useProfile();
  const { colors, spacing, fontSize, fontWeight } = useTheme();

  const handleSave = async (next: UserProfile) => {
    await saveProfile(next);
    router.replace('/feed');
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={{
          padding: spacing.lg,
          gap: spacing.sm,
          paddingBottom: spacing.xxl,
        }}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={{ fontSize: fontSize.xxl, fontWeight: fontWeight.bold, color: colors.text }}>
          Configura tu perfil
        </Text>
        <Text
          style={{
            fontSize: fontSize.sm,
            color: colors.textSecondary,
            marginBottom: spacing.sm,
          }}
        >
          Cuéntanos tu stack y experiencia para personalizar las vacantes.
        </Text>

        <ProfileForm initialProfile={profile} submitLabel="Continuar" onSubmit={handleSave} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
