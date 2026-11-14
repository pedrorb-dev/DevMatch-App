import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/core/theme/theme';
import type { JobOffer } from '../../domain/entities/JobOffer';
import { useFavorites } from '../context/FavoritesContext';
import { ModalityBadge } from './ModalityBadge';

interface JobCardProps {
  job: JobOffer;
  onPress: () => void;
}

export function JobCard({ job, onPress }: JobCardProps) {
  const { isFavorite, toggleFavorite } = useFavorites();
  const favorite = isFavorite(job.id);

  return (
    <Pressable onPress={onPress} style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title} numberOfLines={2}>
          {job.title}
        </Text>
        <Pressable
          onPress={() => toggleFavorite(job.id)}
          hitSlop={10}
          accessibilityRole="button"
          accessibilityLabel={favorite ? 'Quitar de favoritos' : 'Guardar en favoritos'}
          style={styles.favoriteButton}
        >
          <Ionicons
            name={favorite ? 'bookmark' : 'bookmark-outline'}
            size={22}
            color={favorite ? theme.colors.primary : theme.colors.textMuted}
          />
        </Pressable>
      </View>

      <Text style={styles.company} numberOfLines={1}>
        {job.company}
      </Text>

      <View style={styles.footer}>
        <ModalityBadge modality={job.modality} />
        <Text style={styles.location} numberOfLines={1}>
          {job.locationText}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.lg,
    gap: theme.spacing.sm,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.sm,
  },
  title: {
    flex: 1,
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.text,
  },
  favoriteButton: {
    padding: theme.spacing.xs,
  },
  company: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.xs,
  },
  location: {
    flex: 1,
    textAlign: 'right',
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
});
