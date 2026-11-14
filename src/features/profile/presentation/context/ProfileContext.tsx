import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react';

import type { UserProfile } from '../../domain/entities/UserProfile';
import { profileRepository } from '../../infrastructure/repositories/InMemoryProfileRepository';

interface ProfileContextValue {
  profile: UserProfile | null;
  isLoading: boolean;
  saveProfile: (profile: UserProfile) => Promise<void>;
  clearProfile: () => Promise<void>;
}

const ProfileContext = createContext<ProfileContextValue | undefined>(undefined);

export function ProfileProvider({ children }: PropsWithChildren) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    profileRepository.getProfile().then((stored) => {
      if (isMounted) {
        setProfile(stored);
        setIsLoading(false);
      }
    });

    return () => {
      isMounted = false;
    };
  }, []);

  const saveProfile = useCallback(async (next: UserProfile) => {
    await profileRepository.saveProfile(next);
    setProfile(next);
  }, []);

  const clearProfile = useCallback(async () => {
    await profileRepository.clearProfile();
    setProfile(null);
  }, []);

  const value = useMemo(
    () => ({ profile, isLoading, saveProfile, clearProfile }),
    [profile, isLoading, saveProfile, clearProfile],
  );

  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>;
}

export function useProfile(): ProfileContextValue {
  const context = useContext(ProfileContext);
  if (!context) {
    throw new Error('useProfile debe usarse dentro de <ProfileProvider>.');
  }
  return context;
}
