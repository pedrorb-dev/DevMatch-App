import { useRouter } from 'expo-router';
import { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { theme } from '@/core/theme/theme';
import { JobCard } from '../components/JobCard';
import { useJobs } from '../hooks/useJobs';

const DAYS_BACK = 15;

type DayFilter = {
  daysAgo: number;
  label: string;
};

const dayLabel = (daysAgo: number): string => {
  if (daysAgo === 0) return 'Hoy';
  if (daysAgo === 1) return 'Ayer';
  return `Hace ${daysAgo} días`;
};

const dayFilters: DayFilter[] = Array.from({ length: DAYS_BACK + 1 }, (_, daysAgo) => ({
  daysAgo,
  label: dayLabel(daysAgo),
}));

/** Compara la fecha de publicación contra el día calendario de hace `daysAgo`. */
const isCreatedOnDay = (isoDate: string, daysAgo: number, now: Date): boolean => {
  const created = new Date(isoDate);
  const target = new Date(now.getFullYear(), now.getMonth(), now.getDate() - daysAgo);
  return (
    created.getFullYear() === target.getFullYear() &&
    created.getMonth() === target.getMonth() &&
    created.getDate() === target.getDate()
  );
};

export function FeedScreen() {
  const router = useRouter();
  const { jobs, isLoading, error } = useJobs();
  const [selectedDaysAgo, setSelectedDaysAgo] = useState<number | null>(null);

  const visibleJobs = useMemo(() => {
    if (selectedDaysAgo === null) return jobs;
    const now = new Date();
    return jobs.filter((job) => isCreatedOnDay(job.createdAt, selectedDaysAgo, now));
  }, [jobs, selectedDaysAgo]);

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
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.chipsScroll}
        contentContainerStyle={styles.chipsRow}
      >
        <Pressable
          onPress={() => setSelectedDaysAgo(null)}
          style={[styles.chip, selectedDaysAgo === null && styles.chipActive]}
          accessibilityRole="button"
          accessibilityState={{ selected: selectedDaysAgo === null }}
        >
          <Text style={[styles.chipText, selectedDaysAgo === null && styles.chipTextActive]}>
            Todos
          </Text>
        </Pressable>

        {dayFilters.map(({ daysAgo, label }) => {
          const isActive = selectedDaysAgo === daysAgo;
          return (
            <Pressable
              key={daysAgo}
              onPress={() => setSelectedDaysAgo(daysAgo)}
              style={[styles.chip, isActive && styles.chipActive]}
              accessibilityRole="button"
              accessibilityState={{ selected: isActive }}
            >
              <Text style={[styles.chipText, isActive && styles.chipTextActive]}>{label}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

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
  chipsScroll: {
    flexGrow: 0,
  },
  chipsRow: {
    flexDirection: 'row',
    alignItems: 'center',
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
