import { StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@/core/theme/ThemeContext';
import type { WorkModality } from '../../domain/types';

interface ModalityBadgeProps {
  modality: WorkModality;
}

export function ModalityBadge({ modality }: ModalityBadgeProps) {
  const { colors, spacing, radius, fontSize, fontWeight, isDark } = useTheme();

  const badgeBackground: Record<WorkModality, string> = {
    Remoto: isDark ? '#14532D' : '#DCFCE7',
    Híbrido: isDark ? '#78350F' : '#FEF3C7',
    Presencial: colors.primaryLight,
  };

  const badgeTextColor: Record<WorkModality, string> = {
    Remoto: isDark ? '#86EFAC' : '#166534',
    Híbrido: isDark ? '#FCD34D' : '#92400E',
    Presencial: colors.primaryText,
  };

  return (
    <View
      style={[
        styles.badge,
        {
          paddingVertical: spacing.xs,
          paddingHorizontal: spacing.sm,
          borderRadius: radius.full,
          /*backgroundColor: badgeBackground[modality],*/
        },
      ]}
    >
      <Text
        style={{
          fontSize: fontSize.xs,
          fontWeight: fontWeight.semibold,
          color: colors.textSecondary,
          /*color: badgeTextColor[modality],*/
        }}
      >
        {modality}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {},
});
