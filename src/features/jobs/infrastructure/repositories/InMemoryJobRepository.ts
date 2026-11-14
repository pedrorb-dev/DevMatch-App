import type { JobOffer } from '../../domain/entities/JobOffer';
import type { JobRepository } from '../../domain/repositories/JobRepository';
import { mockJobs } from '../mocks/jobs.mock';

export class InMemoryJobRepository implements JobRepository {
  async getJobs(): Promise<JobOffer[]> {
    return [...mockJobs].sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    );
  }

  async getJobById(id: string): Promise<JobOffer | null> {
    return mockJobs.find((job) => job.id === id) ?? null;
  }
}

export const jobRepository: JobRepository = new InMemoryJobRepository();
