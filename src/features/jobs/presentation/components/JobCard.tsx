import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@/core/theme/ThemeContext';
import type { JobOffer } from '../../domain/entities/JobOffer';
import { useFavorites } from '../context/FavoritesContext';
import { ModalityBadge } from './ModalityBadge';

interface JobCardProps {
  job: JobOffer;
  distanceKm?: number | null;
  onPress: () => void;
}

export function JobCard({ job, distanceKm, onPress }: JobCardProps) {
  const { isFavorite, toggleFavorite } = useFavorites();
  const favorite = isFavorite(job.id);
  const { colors, spacing, radius, fontSize, fontWeight } = useTheme();

  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.card,
        {
          backgroundColor: colors.surface,
          borderRadius: radius.lg,
          padding: spacing.lg,
          gap: spacing.sm,
          borderColor: colors.border,
        },
      ]}
    >
      <View style={[styles.header, { gap: spacing.sm }]}>
        <Text
          style={{
            flex: 1,
            fontSize: fontSize.lg,
            fontWeight: fontWeight.semibold,
            color: colors.text,
          }}
          numberOfLines={2}
        >
          {job.title}
        </Text>
        <Pressable
          onPress={() => toggleFavorite(job.id)}
          hitSlop={10}
          accessibilityRole="button"
          accessibilityLabel={favorite ? 'Quitar de favoritos' : 'Guardar en favoritos'}
          style={{ padding: spacing.xs }}
        >
          <Ionicons
            name={favorite ? 'bookmark' : 'bookmark-outline'}
            size={22}
            color={favorite ? colors.primaryText : colors.textMuted}
          />
        </Pressable>
      </View>

      <Text style={{ fontSize: fontSize.sm, color: colors.textSecondary }} numberOfLines={1}>
        {job.company}
      </Text>

      <View style={[styles.footer, { gap: spacing.sm, marginTop: spacing.xs }]}>
        <ModalityBadge modality={job.modality} />
        {distanceKm != null && (
          <Text
            style={{
              fontSize: fontSize.xs,
              fontWeight: fontWeight.medium,
              color: colors.primaryText,
            }}
            numberOfLines={1}
          >
            a {Math.round(distanceKm)} km
          </Text>
        )}
        <Text
          style={{
            flex: 1,
            textAlign: 'right',
            fontSize: fontSize.sm,
            color: colors.textSecondary,
          }}
          numberOfLines={1}
        >
          {job.locationText}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
});
