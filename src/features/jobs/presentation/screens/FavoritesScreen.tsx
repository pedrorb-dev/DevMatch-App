import { useRouter } from 'expo-router';
import { useMemo } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/core/theme/theme';
import { JobCard } from '../components/JobCard';
import { useFavorites } from '../context/FavoritesContext';
import { useJobs } from '../hooks/useJobs';

export function FavoritesScreen() {
  const router = useRouter();
  const { jobs, isLoading } = useJobs();
  const { favoriteIds } = useFavorites();

  const favoriteJobs = useMemo(
    () => jobs.filter((job) => favoriteIds.has(job.id)),
    [jobs, favoriteIds],
  );

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={favoriteJobs}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => (
          <JobCard job={item} onPress={() => router.push(`/work/${item.id}`)} />
        )}
        ListEmptyComponent={
          <Text style={styles.empty}>Aún no tienes vacantes guardadas.</Text>
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
  listContent: {
    padding: theme.spacing.lg,
    gap: theme.spacing.md,
  },
  empty: {
    textAlign: 'center',
    marginTop: theme.spacing.xl,
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
  },
});
