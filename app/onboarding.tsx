import { Stack } from 'expo-router';
import { StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useTheme } from '@/core/theme/ThemeContext';
import { useProfile } from '@/features/profile/presentation/context/ProfileContext';
import { OnboardingScreen } from '@/features/profile/presentation/screens/OnboardingScreen';

export default function OnboardingRoute() {
  const { profile } = useProfile();
  const { colors } = useTheme();
  const isEditing = profile !== null;
  const edges: ('top' | 'bottom')[] = isEditing ? ['bottom'] : ['top', 'bottom'];

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: isEditing,
          title: 'Editar perfil',
        }}
      />
      <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.background }]} edges={edges}>
        <OnboardingScreen />
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
});
