export const colors = {
  // Marca
  primary: '#4B0082',
  primaryDark: '#330057',
  primaryLight: '#EEF2FF',

  // Superficies
  background: '#F8FAFC',
  surface: '#FFFFFF',

  // Texto
  text: '#0F172A',
  textSecondary: '#64748B',
  textMuted: '#94A3B8',

  // Bordes y estados
  border: '#E2E8F0',
  danger: '#56070c',
  success: '#16A34A',
  warning: '#F59E0B',
  white: '#FFFFFF',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  full: 999,
} as const;

export const fontSize = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 18,
  xl: 22,
  xxl: 28,
} as const;

export const fontWeight = {
  regular: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
} as const;

export const theme = {
  colors,
  spacing,
  radius,
  fontSize,
  fontWeight,
} as const;

export type Theme = typeof theme;
