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

import { theme } from '@/core/theme/theme';
import { ModalityBadge } from '../components/ModalityBadge';
import { useFavorites } from '../context/FavoritesContext';
import { useJob } from '../hooks/useJob';

interface WorkScreenProps {
  jobId: string;
}

export function WorkScreen({ jobId }: WorkScreenProps) {
  const { job, isLoading } = useJob(jobId);
  const { isFavorite, toggleFavorite } = useFavorites();

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={theme.colors.primary} />
      </View>
    );
  }

  if (!job) {
    return (
      <View style={styles.centered}>
        <Text style={styles.empty}>Vacante no encontrada.</Text>
      </View>
    );
  }

  const favorite = isFavorite(job.id);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>{job.title}</Text>
      <Text style={styles.company}>{job.company}</Text>

      <View style={styles.metaRow}>
        <ModalityBadge modality={job.modality} />
        <Text style={styles.meta}>{job.locationText}</Text>
      </View>

      <Text style={styles.meta}>Inglés: {job.englishLevel}</Text>

      <Text style={styles.sectionTitle}>Stack</Text>
      <View style={styles.stackRow}>
        {job.stack.map((tech) => (
          <View key={tech} style={styles.techChip}>
            <Text style={styles.techText}>{tech}</Text>
          </View>
        ))}
      </View>

      <Text style={styles.sectionTitle}>Descripción</Text>
      <Text style={styles.description}>{job.description}</Text>

      {job.requirements.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>Qué necesitan</Text>
          <View style={styles.bulletList}>
            {job.requirements.map((item) => (
              <View key={item} style={styles.bulletItem}>
                <Text style={styles.bullet}>•</Text>
                <Text style={styles.bulletText}>{item}</Text>
              </View>
            ))}
          </View>
        </>
      )}

      {job.benefits.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>Qué ofrecen</Text>
          <View style={styles.bulletList}>
            {job.benefits.map((item) => (
              <View key={item} style={styles.bulletItem}>
                <Text style={styles.bullet}>•</Text>
                <Text style={styles.bulletText}>{item}</Text>
              </View>
            ))}
          </View>
        </>
      )}

        <Pressable
        onPress={() => {
          void Linking.openURL(job.url);
        }}
        style={styles.primaryButton}
        accessibilityRole="button"
      >
        <Text style={styles.primaryButtonText}>Ver oferta original</Text>
      </Pressable>

      <Pressable
        onPress={() => toggleFavorite(job.id)}
        style={[styles.secondaryButton, favorite && styles.secondaryButtonActive]}
        accessibilityRole="button"
      >
        <Ionicons
          name={favorite ? 'bookmark' : 'bookmark-outline'}
          size={20}
          color={favorite ? theme.colors.primary : theme.colors.textSecondary}
        />
        <Text
          style={[styles.secondaryButtonText, favorite && styles.secondaryButtonTextActive]}
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
    backgroundColor: theme.colors.background,
  },
  content: {
    padding: theme.spacing.lg,
    gap: theme.spacing.md,
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
  title: {
    fontSize: theme.fontSize.xxl,
    fontWeight: theme.fontWeight.bold,
    color: theme.colors.text,
  },
  company: {
    fontSize: theme.fontSize.md,
    color: theme.colors.textSecondary,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  meta: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
  sectionTitle: {
    marginTop: theme.spacing.sm,
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.semibold,
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
  description: {
    fontSize: theme.fontSize.sm,
    lineHeight: 22,
    color: theme.colors.text,
  },
  bulletList: {
    gap: theme.spacing.xs,
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.sm,
  },
  bullet: {
    fontSize: theme.fontSize.sm,
    lineHeight: 22,
    color: theme.colors.primary,
  },
  bulletText: {
    flex: 1,
    fontSize: theme.fontSize.sm,
    lineHeight: 22,
    color: theme.colors.text,
  },
  secondaryButton: {
    marginTop: theme.spacing.md,
    paddingVertical: theme.spacing.md,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
  },
  secondaryButtonActive: {
    borderColor: theme.colors.primary,
  },
  secondaryButtonText: {
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.medium,
    color: theme.colors.textSecondary,
  },
  secondaryButtonTextActive: {
    color: theme.colors.primary,
  },
  primaryButton: {
    marginTop: theme.spacing.lg,
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
});
