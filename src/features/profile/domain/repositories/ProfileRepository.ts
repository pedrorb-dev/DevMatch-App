import type { UserProfile } from '../entities/UserProfile';

export interface ProfileRepository {
  getProfile(): Promise<UserProfile | null>;
  saveProfile(profile: UserProfile): Promise<void>;
  clearProfile(): Promise<void>;
}
