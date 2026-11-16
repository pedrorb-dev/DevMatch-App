import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { useTheme } from '@/core/theme/ThemeContext';

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
  'Laravel',
];

const ENGLISH_OPTIONS: UserProfile['englishLevel'][] = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

interface ProfileFormProps {
  initialProfile: UserProfile | null;
  submitLabel: string;
  onSubmit: (profile: UserProfile) => Promise<void> | void;
  variant?: 'light' | 'dark';
}

/**
 * Formulario de edición de perfil compartido por el onboarding y el dev menu de perfil.
 */
export function ProfileForm({
  initialProfile,
  submitLabel,
  onSubmit,
}: ProfileFormProps) {
  const { colors, spacing, radius, fontSize, fontWeight } = useTheme();
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

  const labelStyle = {
    marginTop: spacing.md,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.semibold,
    color: colors.text,
  } as const;

  const chipBaseStyle = {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: radius.full,
    borderWidth: 1,
  } as const;

  return (
    <View style={{ gap: spacing.sm }}>
      <Text style={labelStyle}>Stack tecnológico</Text>
      <View style={[styles.chips, { gap: spacing.sm }]}>
        {TECH_OPTIONS.map((tech) => {
          const selected = stack.includes(tech);
          return (
            <Pressable
              key={tech}
              onPress={() => toggleTech(tech)}
              style={[
                chipBaseStyle,
                {
                  borderColor: selected ? colors.primary : colors.border,
                  backgroundColor: selected ? colors.primary : colors.surface,
                },
              ]}
              accessibilityRole="button"
              accessibilityState={{ selected }}
            >
              <Text
                style={{
                  fontSize: fontSize.sm,
                  fontWeight: fontWeight.medium,
                  color: selected ? colors.white : colors.textSecondary,
                }}
              >
                {tech}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <Text style={labelStyle}>Nivel de inglés</Text>
      <View style={[styles.chips, { gap: spacing.sm }]}>
        {ENGLISH_OPTIONS.map((level) => {
          const selected = englishLevel === level;
          return (
            <Pressable
              key={level}
              onPress={() => setEnglishLevel(level)}
              style={[
                chipBaseStyle,
                {
                  borderColor: selected ? colors.primary : colors.border,
                  backgroundColor: selected ? colors.primary : colors.surface,
                },
              ]}
              accessibilityRole="button"
              accessibilityState={{ selected }}
            >
              <Text
                style={{
                  fontSize: fontSize.sm,
                  fontWeight: fontWeight.medium,
                  color: selected ? colors.white : colors.textSecondary,
                }}
              >
                {level}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <Text style={labelStyle}>Años de experiencia</Text>
      <View style={[styles.stepper, { gap: spacing.lg }]}>
        <Pressable
          onPress={() => setExperienceYears((value) => Math.max(0, value - 1))}
          style={[
            styles.stepperButton,
            {
              borderRadius: radius.full,
              borderColor: colors.border,
              backgroundColor: colors.surface,
            },
          ]}
          accessibilityRole="button"
          accessibilityLabel="Restar un año"
        >
          <Text style={{ fontSize: fontSize.xl, fontWeight: fontWeight.semibold, color: colors.primaryText }}>
            −
          </Text>
        </Pressable>
        <Text
          style={{
            fontSize: fontSize.xl,
            fontWeight: fontWeight.bold,
            minWidth: 32,
            textAlign: 'center',
            color: colors.text,
          }}
        >
          {experienceYears}
        </Text>
        <Pressable
          onPress={() => setExperienceYears((value) => value + 1)}
          style={[
            styles.stepperButton,
            {
              borderRadius: radius.full,
              borderColor: colors.border,
              backgroundColor: colors.surface,
            },
          ]}
          accessibilityRole="button"
          accessibilityLabel="Sumar un año"
        >
          <Text style={{ fontSize: fontSize.xl, fontWeight: fontWeight.semibold, color: colors.primaryText }}>
            +
          </Text>
        </Pressable>
      </View>

      <Text style={labelStyle}>Ubicación</Text>
      <TextInput
        value={locationText}
        onChangeText={setLocationText}
        placeholder="Ej. Monterrey, México"
        placeholderTextColor={colors.textMuted}
        style={{
          borderWidth: 1,
          borderRadius: radius.md,
          paddingHorizontal: spacing.lg,
          paddingVertical: spacing.md,
          fontSize: fontSize.md,
          borderColor: colors.border,
          backgroundColor: colors.surface,
          color: colors.text,
        }}
      />

      <Pressable
        onPress={handleSubmit}
        disabled={!canSubmit}
        style={[
          {
            marginTop: spacing.xl,
            paddingVertical: spacing.lg,
            borderRadius: radius.md,
            backgroundColor: colors.primary,
            alignItems: 'center',
          },
          !canSubmit && styles.submitButtonDisabled,
        ]}
        accessibilityRole="button"
      >
        <Text style={{ fontSize: fontSize.md, fontWeight: fontWeight.semibold, color: colors.white }}>
          {isSubmitting ? 'Guardando…' : submitLabel}
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  stepper: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stepperButton: {
    width: 44,
    height: 44,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
});
