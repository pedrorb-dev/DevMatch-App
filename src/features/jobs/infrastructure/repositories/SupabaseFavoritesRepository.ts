import { supabase } from '@/core/api/supabase';
import { SINGLE_USER_ID } from '@/core/config/user';

import type { FavoritesRepository } from '../../domain/repositories/FavoritesRepository';

interface SavedJobRow {
  job_id: string;
}

export class SupabaseFavoritesRepository implements FavoritesRepository {
  async getFavoriteJobIds(): Promise<string[]> {
    const { data, error } = await supabase
      .from('saved_jobs')
      .select('job_id')
      .eq('user_id', SINGLE_USER_ID);

    if (error) {
      throw new Error(`No se pudieron cargar los favoritos: ${error.message}`);
    }

    return (data as SavedJobRow[]).map((row) => row.job_id);
  }

  async addFavorite(jobId: string): Promise<void> {
    const { error } = await supabase
      .from('saved_jobs')
      .upsert(
        { user_id: SINGLE_USER_ID, job_id: jobId },
        { onConflict: 'user_id,job_id', ignoreDuplicates: true },
      );

    if (error) {
      throw new Error(`No se pudo guardar el favorito: ${error.message}`);
    }
  }

  async removeFavorite(jobId: string): Promise<void> {
    const { error } = await supabase
      .from('saved_jobs')
      .delete()
      .eq('user_id', SINGLE_USER_ID)
      .eq('job_id', jobId);

    if (error) {
      throw new Error(`No se pudo quitar el favorito: ${error.message}`);
    }
  }
}

export const favoritesRepository: FavoritesRepository = new SupabaseFavoritesRepository();
