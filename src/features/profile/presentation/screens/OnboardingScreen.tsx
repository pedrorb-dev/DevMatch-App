import { useRouter } from 'expo-router';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text } from 'react-native';

import { theme } from '@/core/theme/theme';

import type { UserProfile } from '../../domain/entities/UserProfile';
import { ProfileForm } from '../components/ProfileForm';
import { useProfile } from '../context/ProfileContext';

export function OnboardingScreen() {
  const router = useRouter();
  const { profile, saveProfile } = useProfile();

  const handleSave = async (next: UserProfile) => {
    await saveProfile(next);
    router.replace('/feed');
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>Configura tu perfil</Text>
        <Text style={styles.subtitle}>
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
    backgroundColor: theme.colors.background,
  },
  content: {
    padding: theme.spacing.lg,
    gap: theme.spacing.sm,
    paddingBottom: theme.spacing.xxl,
  },
  title: {
    fontSize: theme.fontSize.xxl,
    fontWeight: theme.fontWeight.bold,
    color: theme.colors.text,
  },
  subtitle: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm,
  },
});
