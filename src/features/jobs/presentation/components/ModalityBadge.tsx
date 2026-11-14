import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/core/theme/theme';
import type { WorkModality } from '../../domain/types';

const badgeBackground: Record<WorkModality, string> = {
  Remoto: '#DCFCE7',
  Híbrido: '#FEF3C7',
  Presencial: theme.colors.primaryLight,
};

const badgeTextColor: Record<WorkModality, string> = {
  Remoto: '#166534',
  Híbrido: '#92400E',
  Presencial: theme.colors.primary,
};

interface ModalityBadgeProps {
  modality: WorkModality;
}

export function ModalityBadge({ modality }: ModalityBadgeProps) {
  return (
    <View style={[styles.badge, {/*{ backgroundColor: badgeBackground[modality] }*/}]}>
      <Text style={[styles.text, {/*{ color: badgeTextColor[modality] }*/}]}>{modality}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.sm,
    borderRadius: theme.radius.full,
  },
  text: {
    fontSize: theme.fontSize.xs,
    fontWeight: theme.fontWeight.semibold,
  },
});
