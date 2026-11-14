import { Redirect } from 'expo-router';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { theme } from '@/core/theme/theme';
import { useProfile } from '@/features/profile/presentation/context/ProfileContext';

export default function Index() {
  const { profile, isLoading } = useProfile();

  if (isLoading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator color={theme.colors.primary} />
      </View>
    );
  }

  if (!profile) {
    return <Redirect href="/onboarding" />;
  }

  return <Redirect href="/feed" />;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.background,
  },
});
