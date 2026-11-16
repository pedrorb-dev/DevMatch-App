import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { theme } from '@/core/theme/theme';

import type { UserProfile } from '../../domain/entities/UserProfile';

const TECH_OPTIONS = [
  'Angular',
  'Spring Boot',
  'React',
  'Node.js',
  'Python',
  'React Native',
  'Java',
  '.NET',
  'PHP',
  'FastApi',
  'Django',
  'Laravel'
];

const ENGLISH_OPTIONS: UserProfile['englishLevel'][] = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

interface ProfileFormProps {
  initialProfile: UserProfile | null;
  submitLabel: string;
  onSubmit: (profile: UserProfile) => Promise<void> | void;
}

/**
 * Formulario de edición de perfil compartido por el onboarding y el modo
 * edición inline de la pantalla de perfil.
 */
export function ProfileForm({ initialProfile, submitLabel, onSubmit }: ProfileFormProps) {
  const [stack, setStack] = useState<string[]>(initialProfile?.stack ?? []);
  const [englishLevel, setEnglishLevel] = useState<UserProfile['englishLevel']>(
    initialProfile?.englishLevel ?? 'B1',
  );
  const [experienceYears, setExperienceYears] = useState(initialProfile?.experienceYears ?? 0);
  const [locationText, setLocationText] = useState(initialProfile?.locationText ?? '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const toggleTech = (tech: string) => {
    setStack((current) =>
      current.includes(tech) ? current.filter((item) => item !== tech) : [...current, tech],
    );
  };

  const canSubmit = stack.length > 0 && locationText.trim().length > 0 && !isSubmitting;

  const handleSubmit = async () => {
    if (!canSubmit) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        stack,
        englishLevel,
        experienceYears,
        locationText: locationText.trim(),
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
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
        onPress={handleSubmit}
        disabled={!canSubmit}
        style={[styles.submitButton, !canSubmit && styles.submitButtonDisabled]}
        accessibilityRole="button"
      >
        <Text style={styles.submitButtonText}>
          {isSubmitting ? 'Guardando…' : submitLabel}
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: theme.spacing.sm,
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
  submitButton: {
    marginTop: theme.spacing.xl,
    paddingVertical: theme.spacing.lg,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
  submitButtonText: {
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.white,
  },
});
