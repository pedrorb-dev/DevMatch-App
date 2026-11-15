import { useEffect, useState } from 'react';

import type { JobOffer } from '../../domain/entities/JobOffer';
import { jobRepository } from '../../infrastructure/repositories/SupabaseJobRepository';

interface UseJobResult {
  job: JobOffer | null;
  isLoading: boolean;
}

export function useJob(jobId: string): UseJobResult {
  const [job, setJob] = useState<JobOffer | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);

    jobRepository
      .getJobById(jobId)
      .then((data) => {
        if (isMounted) {
          setJob(data);
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
  }, [jobId]);

  return { job, isLoading };
}
