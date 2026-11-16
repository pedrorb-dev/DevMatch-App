import { Ionicons } from '@expo/vector-icons';
import {
  ActivityIndicator,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { useTheme } from '@/core/theme/ThemeContext';
import { ModalityBadge } from '../components/ModalityBadge';
import { useFavorites } from '../context/FavoritesContext';
import { useJob } from '../hooks/useJob';

interface WorkScreenProps {
  jobId: string;
}

export function WorkScreen({ jobId }: WorkScreenProps) {
  const { job, isLoading } = useJob(jobId);
  const { isFavorite, toggleFavorite } = useFavorites();
  const { colors, spacing, radius, fontSize, fontWeight } = useTheme();

  if (isLoading) {
    return (
      <View style={[styles.centered, { backgroundColor: colors.background }]}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (!job) {
    return (
      <View style={[styles.centered, { backgroundColor: colors.background }]}>
        <Text style={{ fontSize: fontSize.sm, color: colors.textSecondary }}>
          Vacante no encontrada.
        </Text>
      </View>
    );
  }

  const favorite = isFavorite(job.id);

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={{ padding: spacing.lg, gap: spacing.md }}
    >
      <Text style={{ fontSize: fontSize.xxl, fontWeight: fontWeight.bold, color: colors.text }}>
        {job.title}
      </Text>
      <Text style={{ fontSize: fontSize.md, color: colors.textSecondary }}>{job.company}</Text>

      <View style={[styles.metaRow, { gap: spacing.sm }]}>
        <ModalityBadge modality={job.modality} />
        <Text style={{ fontSize: fontSize.sm, color: colors.textSecondary }}>{job.locationText}</Text>
      </View>

      <Text style={{ fontSize: fontSize.sm, color: colors.textSecondary }}>
        Inglés: {job.englishLevel}
      </Text>

      <Text
        style={{
          marginTop: spacing.sm,
          fontSize: fontSize.md,
          fontWeight: fontWeight.semibold,
          color: colors.text,
        }}
      >
        Stack
      </Text>
      <View style={[styles.stackRow, { gap: spacing.sm }]}>
        {job.stack.map((tech) => (
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
          fontSize: fontSize.md,
          fontWeight: fontWeight.semibold,
          color: colors.text,
        }}
      >
        Descripción
      </Text>
      <Text style={{ fontSize: fontSize.sm, lineHeight: 22, color: colors.text }}>
        {job.description}
      </Text>

      {job.requirements.length > 0 && (
        <>
          <Text
            style={{
              marginTop: spacing.sm,
              fontSize: fontSize.md,
              fontWeight: fontWeight.semibold,
              color: colors.text,
            }}
          >
            Qué necesitan
          </Text>
          <View style={{ gap: spacing.xs }}>
            {job.requirements.map((item) => (
              <View key={item} style={[styles.bulletItem, { gap: spacing.sm }]}>
                <Text style={{ fontSize: fontSize.sm, lineHeight: 22, color: colors.primaryText }}>•</Text>
                <Text style={{ flex: 1, fontSize: fontSize.sm, lineHeight: 22, color: colors.text }}>
                  {item}
                </Text>
              </View>
            ))}
          </View>
        </>
      )}

      {job.benefits.length > 0 && (
        <>
          <Text
            style={{
              marginTop: spacing.sm,
              fontSize: fontSize.md,
              fontWeight: fontWeight.semibold,
              color: colors.text,
            }}
          >
            Qué ofrecen
          </Text>
          <View style={{ gap: spacing.xs }}>
            {job.benefits.map((item) => (
              <View key={item} style={[styles.bulletItem, { gap: spacing.sm }]}>
                <Text style={{ fontSize: fontSize.sm, lineHeight: 22, color: colors.primaryText }}>•</Text>
                <Text style={{ flex: 1, fontSize: fontSize.sm, lineHeight: 22, color: colors.text }}>
                  {item}
                </Text>
              </View>
            ))}
          </View>
        </>
      )}

      <Pressable
        onPress={() => {
          void Linking.openURL(job.url);
        }}
        style={{
          marginTop: spacing.lg,
          paddingVertical: spacing.lg,
          borderRadius: radius.md,
          backgroundColor: colors.primary,
          alignItems: 'center',
        }}
        accessibilityRole="button"
      >
        <Text style={{ fontSize: fontSize.md, fontWeight: fontWeight.semibold, color: colors.white }}>
          Ver oferta original
        </Text>
      </Pressable>

      <Pressable
        onPress={() => toggleFavorite(job.id)}
        style={[
          styles.secondaryButton,
          {
            marginTop: spacing.md,
            paddingVertical: spacing.md,
            borderRadius: radius.md,
            borderColor: favorite ? colors.primary : colors.border,
            gap: spacing.sm,
          },
        ]}
        accessibilityRole="button"
      >
        <Ionicons
          name={favorite ? 'bookmark' : 'bookmark-outline'}
          size={20}
          color={favorite ? colors.primaryText : colors.textSecondary}
        />
        <Text
          style={{
            fontSize: fontSize.md,
            fontWeight: fontWeight.medium,
            color: favorite ? colors.primaryText : colors.textSecondary,
          }}
        >
          {favorite ? 'Quitar de favoritos' : 'Guardar en favoritos'}
        </Text>
      </Pressable>
    </ScrollView>
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
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stackRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  secondaryButton: {
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
