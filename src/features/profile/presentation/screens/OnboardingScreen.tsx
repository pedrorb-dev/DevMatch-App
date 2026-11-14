import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { theme } from '@/core/theme/theme';
import type { UserProfile } from '../../domain/entities/UserProfile';
import { useProfile } from '../context/ProfileContext';

const TECH_OPTIONS = [
  'Angular',
  'Spring Boot',
  'React',
  'Node.js',
  'Python',
  'React Native',
  'Java',
  '.NET',
];

const ENGLISH_OPTIONS: UserProfile['englishLevel'][] = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

export function OnboardingScreen() {
  const router = useRouter();
  const { profile, saveProfile } = useProfile();

  const [stack, setStack] = useState<string[]>(profile?.stack ?? []);
  const [englishLevel, setEnglishLevel] = useState<UserProfile['englishLevel']>(
    profile?.englishLevel ?? 'B1',
  );
  const [experienceYears, setExperienceYears] = useState(profile?.experienceYears ?? 0);
  const [locationText, setLocationText] = useState(profile?.locationText ?? '');
  const [isSaving, setIsSaving] = useState(false);

  const toggleTech = (tech: string) => {
    setStack((current) =>
      current.includes(tech) ? current.filter((item) => item !== tech) : [...current, tech],
    );
  };

  const canSave = stack.length > 0 && locationText.trim().length > 0 && !isSaving;

  const handleSave = async () => {
    if (!canSave) {
      return;
    }

    setIsSaving(true);
    await saveProfile({
      stack,
      englishLevel,
      experienceYears,
      locationText: locationText.trim(),
    });
    setIsSaving(false);
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

        <Text style={styles.label}>Stack tecnológico</Text>
        <View style={styles.chips}>
          {TECH_OPTIONS.map((tech) => {
            const selected = stack.includes(tech);
            return (
              <Pressable
                key={tech}
                onPress={() => toggleTech(tech)}
                style={[styles.chip, selected && styles.chipSelected]}
                accessibilityRole="button"
                accessibilityState={{ selected }}
              >
                <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{tech}</Text>
              </Pressable>
            );
          })}
        </View>

        <Text style={styles.label}>Nivel de inglés</Text>
        <View style={styles.chips}>
          {ENGLISH_OPTIONS.map((level) => {
            const selected = englishLevel === level;
            return (
              <Pressable
                key={level}
                onPress={() => setEnglishLevel(level)}
                style={[styles.chip, selected && styles.chipSelected]}
                accessibilityRole="button"
                accessibilityState={{ selected }}
              >
                <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{level}</Text>
              </Pressable>
            );
          })}
        </View>

        <Text style={styles.label}>Años de experiencia</Text>
        <View style={styles.stepper}>
          <Pressable
            onPress={() => setExperienceYears((value) => Math.max(0, value - 1))}
            style={styles.stepperButton}
            accessibilityRole="button"
            accessibilityLabel="Restar un año"
          >
            <Text style={styles.stepperButtonText}>−</Text>
          </Pressable>
          <Text style={styles.stepperValue}>{experienceYears}</Text>
          <Pressable
            onPress={() => setExperienceYears((value) => value + 1)}
            style={styles.stepperButton}
            accessibilityRole="button"
            accessibilityLabel="Sumar un año"
          >
            <Text style={styles.stepperButtonText}>+</Text>
          </Pressable>
        </View>

        <Text style={styles.label}>Ubicación</Text>
        <TextInput
          value={locationText}
          onChangeText={setLocationText}
          placeholder="Ej. Monterrey, México"
          placeholderTextColor={theme.colors.textMuted}
          style={styles.input}
        />

        <Pressable
          onPress={handleSave}
          disabled={!canSave}
          style={[styles.saveButton, !canSave && styles.saveButtonDisabled]}
          accessibilityRole="button"
        >
          <Text style={styles.saveButtonText}>{isSaving ? 'Guardando…' : 'Continuar'}</Text>
        </Pressable>
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
  label: {
    marginTop: theme.spacing.md,
    fontSize: theme.fontSize.sm,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.text,
  },
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
  },
  chip: {
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.radius.full,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface,
  },
  chipSelected: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  chipText: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    fontWeight: theme.fontWeight.medium,
  },
  chipTextSelected: {
    color: theme.colors.white,
  },
  stepper: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.lg,
  },
  stepperButton: {
    width: 44,
    height: 44,
    borderRadius: theme.radius.full,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepperButtonText: {
    fontSize: theme.fontSize.xl,
    color: theme.colors.primary,
    fontWeight: theme.fontWeight.semibold,
  },
  stepperValue: {
    fontSize: theme.fontSize.xl,
    fontWeight: theme.fontWeight.bold,
    color: theme.colors.text,
    minWidth: 32,
    textAlign: 'center',
  },
  input: {
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.surface,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
    fontSize: theme.fontSize.md,
    color: theme.colors.text,
  },
  saveButton: {
    marginTop: theme.spacing.xl,
    paddingVertical: theme.spacing.lg,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
  },
  saveButtonDisabled: {
    opacity: 0.5,
  },
  saveButtonText: {
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.white,
  },
});
