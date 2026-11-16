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

import { useTheme } from '@/core/theme/ThemeContext';
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
  const { colors, spacing, radius, fontSize, fontWeight } = useTheme();
  const [selectedDaysAgo, setSelectedDaysAgo] = useState<number | null>(null);

  const visibleJobs = useMemo(() => {
    if (selectedDaysAgo === null) return jobs;
    const now = new Date();
    return jobs.filter((job) => isCreatedOnDay(job.createdAt, selectedDaysAgo, now));
  }, [jobs, selectedDaysAgo]);

  if (isLoading) {
    return (
      <View style={[styles.centered, { backgroundColor: colors.background }]}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.centered, { backgroundColor: colors.background }]}>
        <Text style={{ fontSize: fontSize.sm, color: colors.danger }}>{error}</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.chipsScroll}
        contentContainerStyle={{
          flexDirection: 'row',
          alignItems: 'center',
          paddingHorizontal: spacing.lg,
          paddingVertical: spacing.md,
          gap: spacing.sm,
        }}
      >
        <Pressable
          onPress={() => setSelectedDaysAgo(null)}
          style={[
            styles.chip,
            {
              paddingVertical: spacing.sm,
              paddingHorizontal: spacing.lg,
              borderRadius: radius.full,
              borderColor: selectedDaysAgo === null ? colors.primary : colors.border,
              backgroundColor: selectedDaysAgo === null ? colors.primary : colors.surface,
            },
          ]}
          accessibilityRole="button"
          accessibilityState={{ selected: selectedDaysAgo === null }}
        >
          <Text
            style={{
              fontSize: fontSize.sm,
              fontWeight: fontWeight.medium,
              color: selectedDaysAgo === null ? colors.white : colors.textSecondary,
            }}
          >
            Todos
          </Text>
        </Pressable>

        {dayFilters.map(({ daysAgo, label }) => {
          const isActive = selectedDaysAgo === daysAgo;
          return (
            <Pressable
              key={daysAgo}
              onPress={() => setSelectedDaysAgo(daysAgo)}
              style={[
                styles.chip,
                {
                  paddingVertical: spacing.sm,
                  paddingHorizontal: spacing.lg,
                  borderRadius: radius.full,
                  borderColor: isActive ? colors.primary : colors.border,
                  backgroundColor: isActive ? colors.primary : colors.surface,
                },
              ]}
              accessibilityRole="button"
              accessibilityState={{ selected: isActive }}
            >
              <Text
                style={{
                  fontSize: fontSize.sm,
                  fontWeight: fontWeight.medium,
                  color: isActive ? colors.white : colors.textSecondary,
                }}
              >
                {label}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <FlatList
        data={visibleJobs}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{
          paddingHorizontal: spacing.lg,
          paddingBottom: spacing.xl,
          gap: spacing.md,
        }}
        renderItem={({ item }) => (
          <JobCard job={item} onPress={() => router.push(`/work/${item.id}`)} />
        )}
        ListEmptyComponent={
          <Text
            style={{
              textAlign: 'center',
              marginTop: spacing.xl,
              fontSize: fontSize.sm,
              color: colors.textSecondary,
            }}
          >
            No hay vacantes para este filtro.
          </Text>
        }
      />
    </View>
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
  chipsScroll: {
    flexGrow: 0,
  },
  chip: {
    borderWidth: 1,
  },
});
