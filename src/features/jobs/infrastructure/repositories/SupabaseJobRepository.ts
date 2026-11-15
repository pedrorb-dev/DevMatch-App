import { supabase } from '@/core/api/supabase';

import type { JobOffer } from '../../domain/entities/JobOffer';
import type { JobRepository } from '../../domain/repositories/JobRepository';
import { toJobOffer, type VacanteRow } from '../mappers/JobMapper';

export class SupabaseJobRepository implements JobRepository {
  async getJobs(): Promise<JobOffer[]> {
    const { data, error } = await supabase
      .from('vacantes')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      throw new Error(`No se pudieron cargar las vacantes: ${error.message}`);
    }

    return (data as VacanteRow[]).map(toJobOffer);
  }

  async getJobById(id: string): Promise<JobOffer | null> {
    const { data, error } = await supabase
      .from('vacantes')
      .select('*')
      .eq('id', id)
      .maybeSingle();

    if (error) {
      throw new Error(`No se pudo cargar la vacante: ${error.message}`);
    }

    return data ? toJobOffer(data as VacanteRow) : null;
  }
}

export const jobRepository: JobRepository = new SupabaseJobRepository();
