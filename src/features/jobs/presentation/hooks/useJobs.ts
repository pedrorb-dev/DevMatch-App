import { useEffect, useState } from 'react';

import type { JobOffer } from '../../domain/entities/JobOffer';
import { jobRepository } from '../../infrastructure/repositories/SupabaseJobRepository';

interface UseJobsResult {
  jobs: JobOffer[];
  isLoading: boolean;
  error: string | null;
}

export function useJobs(): UseJobsResult {
  const [jobs, setJobs] = useState<JobOffer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    jobRepository
      .getJobs()
      .then((data) => {
        if (isMounted) {
          setJobs(data);
        }
      })
      .catch(() => {
        if (isMounted) {
          setError('No se pudieron cargar las vacantes.');
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return { jobs, isLoading, error };
}
