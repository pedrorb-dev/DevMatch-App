import type { JobOffer } from '../entities/JobOffer';

export interface JobRepository {
  getJobs(): Promise<JobOffer[]>;
  getJobById(id: string): Promise<JobOffer | null>;
}
