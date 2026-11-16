export const lightColors = {
  // Marca
  primary: '#4B0082',
  primaryDark: '#330057',
  primaryLight: '#EEF2FF',
  primaryText: '#4B0082',

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

export const darkColors = {
  // Marca
  primary: '#4B0082',
  primaryDark: '#330057',
  primaryLight: '#1E1B4B',
  primaryText: '#A78BFA',

  // Superficies
  background: '#0F172A',
  surface: '#0B0F1A',

  // Texto
  text: '#F9FAFB',
  textSecondary: '#9CA3AF',
  textMuted: '#6B7280',

  // Bordes y estados
  border: '#374151',
  danger: '#F87171',
  success: '#22C55E',
  warning: '#F59E0B',
  white: '#F9FAFB',
} as const;

export type ThemeColors = { [K in keyof typeof lightColors]: string };

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

export type ThemeMode = 'light' | 'dark';

export const createTheme = (colors: ThemeColors) => ({
  colors,
  spacing,
  radius,
  fontSize,
  fontWeight,
});

export type AppTheme = ReturnType<typeof createTheme>;

export const lightTheme = createTheme(lightColors);
export const darkTheme = createTheme(darkColors);

// Compatibilidad temporal
export const theme = lightTheme;
export type Theme = AppTheme;
