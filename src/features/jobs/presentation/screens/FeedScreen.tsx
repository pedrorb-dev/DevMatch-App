import { useRouter } from 'expo-router';
import { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { theme } from '@/core/theme/theme';
import { JobCard } from '../components/JobCard';
import { useJobs } from '../hooks/useJobs';

const isToday = (isoDate: string): boolean => {
  const date = new Date(isoDate);
  const now = new Date();
  return (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  );
};

export function FeedScreen() {
  const router = useRouter();
  const { jobs, isLoading, error } = useJobs();
  const [onlyToday, setOnlyToday] = useState(false);

  const visibleJobs = useMemo(
    () => (onlyToday ? jobs.filter((job) => isToday(job.createdAt)) : jobs),
    [jobs, onlyToday],
  );

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={theme.colors.primary} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.error}>{error}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.chipsRow}>
        <Pressable
          onPress={() => setOnlyToday((current) => !current)}
          style={[styles.chip, onlyToday && styles.chipActive]}
          accessibilityRole="button"
          accessibilityState={{ selected: onlyToday }}
        >
          <Text style={[styles.chipText, onlyToday && styles.chipTextActive]}>
            Nuevos hoy
          </Text>
        </Pressable>
      </View>

      <FlatList
        data={visibleJobs}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => (
          <JobCard job={item} onPress={() => router.push(`/work/${item.id}`)} />
        )}
        ListEmptyComponent={
          <Text style={styles.empty}>No hay vacantes para este filtro.</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.background,
  },
  error: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.danger,
  },
  chipsRow: {
    flexDirection: 'row',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
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
  chipActive: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  chipText: {
    fontSize: theme.fontSize.sm,
    fontWeight: theme.fontWeight.medium,
    color: theme.colors.textSecondary,
  },
  chipTextActive: {
    color: theme.colors.white,
  },
  listContent: {
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.xl,
    gap: theme.spacing.md,
  },
  empty: {
    textAlign: 'center',
    marginTop: theme.spacing.xl,
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
});
