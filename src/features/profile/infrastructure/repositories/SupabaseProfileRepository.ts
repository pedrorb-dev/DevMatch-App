import { supabase } from '@/core/api/supabase';
import { SINGLE_USER_ID } from '@/core/config/user';

import type { UserProfile } from '../../domain/entities/UserProfile';
import type { ProfileRepository } from '../../domain/repositories/ProfileRepository';
import {
  toUserProfile,
  toUserProfileRow,
  type UserProfileRow,
} from '../mappers/ProfileMapper';

export class SupabaseProfileRepository implements ProfileRepository {
  async getProfile(): Promise<UserProfile | null> {
    const { data, error } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('id', SINGLE_USER_ID)
      .maybeSingle();

    if (error) {
      throw new Error(`No se pudo cargar el perfil: ${error.message}`);
    }

    return data ? toUserProfile(data as UserProfileRow) : null;
  }

  async saveProfile(profile: UserProfile): Promise<void> {
    const { error } = await supabase
      .from('user_profiles')
      .upsert(toUserProfileRow(profile, SINGLE_USER_ID), { onConflict: 'id' });

    if (error) {
      throw new Error(`No se pudo guardar el perfil: ${error.message}`);
    }
  }

  async clearProfile(): Promise<void> {
    const { error } = await supabase.from('user_profiles').delete().eq('id', SINGLE_USER_ID);

    if (error) {
      throw new Error(`No se pudo borrar el perfil: ${error.message}`);
    }
  }
}

export const profileRepository: ProfileRepository = new SupabaseProfileRepository();
