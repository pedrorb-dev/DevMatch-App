import type { UserProfile } from '../../domain/entities/UserProfile';
import type { ProfileRepository } from '../../domain/repositories/ProfileRepository';

export class InMemoryProfileRepository implements ProfileRepository {
  private profile: UserProfile | null = null;

  async getProfile(): Promise<UserProfile | null> {
    return this.profile;
  }

  async saveProfile(profile: UserProfile): Promise<void> {
    this.profile = profile;
  }

  async clearProfile(): Promise<void> {
    this.profile = null;
  }
}

export const profileRepository: ProfileRepository = new InMemoryProfileRepository();
