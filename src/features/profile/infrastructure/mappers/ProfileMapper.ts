import type { UserProfile } from '../../domain/entities/UserProfile';

/** Fila de `public.user_profiles` tal como llega de Supabase (snake_case). */
export interface UserProfileRow {
  id: string;
  stack: string[];
  experiencia_anos: number;
  nivel_ingles: UserProfile['englishLevel'];
  ubicacion_texto: string;
}

/** Convierte una fila de `user_profiles` en la entidad de dominio `UserProfile`. */
export function toUserProfile(row: UserProfileRow): UserProfile {
  return {
    stack: row.stack ?? [],
    experienceYears: row.experiencia_anos,
    englishLevel: row.nivel_ingles,
    locationText: row.ubicacion_texto,
  };
}

/** Convierte la entidad `UserProfile` en una fila de `user_profiles`. */
export function toUserProfileRow(profile: UserProfile, id: string): UserProfileRow {
  return {
    id,
    stack: profile.stack,
    experiencia_anos: profile.experienceYears,
    nivel_ingles: profile.englishLevel,
    ubicacion_texto: profile.locationText,
  };
}
