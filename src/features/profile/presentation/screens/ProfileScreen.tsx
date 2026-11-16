import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { consumePendingEditRequest, onEditProfileRequest } from '@/core/devmenu/devMenu';
import { theme } from '@/core/theme/theme';

import type { UserProfile } from '../../domain/entities/UserProfile';
import { ProfileForm } from '../components/ProfileForm';
import { useProfile } from '../context/ProfileContext';

export function ProfileScreen() {
  const router = useRouter();
  const { profile, saveProfile, clearProfile } = useProfile();
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (consumePendingEditRequest()) {
      setIsEditing(true);
    }

    return onEditProfileRequest(() => setIsEditing(true));
  }, []);

  const handleSave = async (next: UserProfile) => {
    await saveProfile(next);
    setIsEditing(false);
  };

  const handleClear = async () => {
    await clearProfile();
    router.replace('/onboarding');
  };

  if (!profile) {
    return (
      <View style={styles.centered}>
        <Text style={styles.empty}>No hay perfil configurado.</Text>
      </View>
    );
  }

  if (isEditing) {
    return (
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Text style={styles.editTitle}>Editar perfil</Text>

          <ProfileForm initialProfile={profile} submitLabel="Guardar cambios" onSubmit={handleSave} />

          <Pressable
            style={styles.secondaryButton}
            onPress={() => setIsEditing(false)}
            accessibilityRole="button"
          >
            <Text style={styles.secondaryButtonText}>Cancelar</Text>
          </Pressable>
        </ScrollView>
      </KeyboardAvoidingView>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.card}>
        <Text style={styles.label}>Stack</Text>
        <View style={styles.stackRow}>
          {profile.stack.map((tech) => (
            <View key={tech} style={styles.techChip}>
              <Text style={styles.techText}>{tech}</Text>
            </View>
          ))}
        </View>

        <Text style={styles.label}>Experiencia</Text>
        <Text style={styles.value}>{profile.experienceYears} años</Text>

        <Text style={styles.label}>Inglés</Text>
        <Text style={styles.value}>{profile.englishLevel}</Text>

        <Text style={styles.label}>Ubicación</Text>
        <Text style={styles.value}>{profile.locationText}</Text>
      </View>

      <Pressable
        style={styles.primaryButton}
        onPress={() => router.push('/onboarding')}
        accessibilityRole="button"
      >
        <Text style={styles.primaryButtonText}>Editar perfil</Text>
      </Pressable>

      <Pressable style={styles.dangerButton} onPress={handleClear} accessibilityRole="button">
        <Text style={styles.dangerButtonText}>Borrar perfil</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    padding: theme.spacing.lg,
    gap: theme.spacing.md,
    paddingBottom: theme.spacing.xxl,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.background,
  },
  empty: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    gap: theme.spacing.xs,
  },
  label: {
    marginTop: theme.spacing.sm,
    fontSize: theme.fontSize.xs,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.textSecondary,
    textTransform: 'uppercase',
  },
  value: {
    fontSize: theme.fontSize.md,
    color: theme.colors.text,
  },
  stackRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
  },
  techChip: {
    paddingVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.sm,
    borderRadius: theme.radius.full,
    backgroundColor: theme.colors.primaryLight,
  },
  techText: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.primary,
    fontWeight: theme.fontWeight.medium,
  },
  primaryButton: {
    paddingVertical: theme.spacing.lg,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.white,
  },
  dangerButton: {
    paddingVertical: theme.spacing.md,
    alignItems: 'center',
  },
  dangerButtonText: {
    fontSize: theme.fontSize.sm,
    fontWeight: theme.fontWeight.medium,
    color: theme.colors.danger,
  },
  editTitle: {
    fontSize: theme.fontSize.xl,
    fontWeight: theme.fontWeight.bold,
    color: theme.colors.text,
  },
  secondaryButton: {
    paddingVertical: theme.spacing.md,
    alignItems: 'center',
  },
  secondaryButtonText: {
    fontSize: theme.fontSize.sm,
    fontWeight: theme.fontWeight.medium,
    color: theme.colors.textSecondary,
  },
});
