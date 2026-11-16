import { useRouter } from 'expo-router';
import { useMemo } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@/core/theme/ThemeContext';
import { JobCard } from '../components/JobCard';
import { useFavorites } from '../context/FavoritesContext';
import { useJobs } from '../hooks/useJobs';

export function FavoritesScreen() {
  const router = useRouter();
  const { jobs, isLoading } = useJobs();
  const { favoriteIds } = useFavorites();
  const { colors, spacing, fontSize } = useTheme();

  const favoriteJobs = useMemo(
    () => jobs.filter((job) => favoriteIds.has(job.id)),
    [jobs, favoriteIds],
  );

  if (isLoading) {
    return (
      <View style={[styles.centered, { backgroundColor: colors.background }]}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FlatList
        data={favoriteJobs}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: spacing.lg, gap: spacing.md }}
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
            Aún no tienes vacantes guardadas.
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
});
