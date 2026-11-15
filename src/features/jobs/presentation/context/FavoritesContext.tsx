import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PropsWithChildren,
} from 'react';

import { favoritesRepository } from '../../infrastructure/repositories/SupabaseFavoritesRepository';

interface FavoritesContextValue {
  favoriteIds: ReadonlySet<string>;
  isFavorite: (jobId: string) => boolean;
  toggleFavorite: (jobId: string) => void;
}

const FavoritesContext = createContext<FavoritesContextValue | undefined>(undefined);

export function FavoritesProvider({ children }: PropsWithChildren) {
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(() => new Set());

  // Espejo síncrono del estado para poder hacer el toggle optimista sin depender
  // de si React ya aplicó el último setState.
  const favoriteIdsRef = useRef<Set<string>>(new Set());
  const isMountedRef = useRef(true);
  const hasToggledRef = useRef(false);

  useEffect(() => {
    isMountedRef.current = true;

    favoritesRepository
      .getFavoriteJobIds()
      .then((ids) => {
        // Si el usuario ya tocó un favorito, no pisamos su cambio optimista.
        if (!isMountedRef.current || hasToggledRef.current) {
          return;
        }
        const next = new Set(ids);
        favoriteIdsRef.current = next;
        setFavoriteIds(next);
      })
      .catch(() => {
        // Sin favoritos cargados: el toggle seguirá intentando persistir.
      });

    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const toggleFavorite = useCallback((jobId: string) => {
    hasToggledRef.current = true;

    const wasFavorite = favoriteIdsRef.current.has(jobId);
    const next = new Set(favoriteIdsRef.current);
    if (wasFavorite) {
      next.delete(jobId);
    } else {
      next.add(jobId);
    }

    // Toggle optimista: la UI cambia de inmediato.
    favoriteIdsRef.current = next;
    setFavoriteIds(next);

    const persistence = wasFavorite
      ? favoritesRepository.removeFavorite(jobId)
      : favoritesRepository.addFavorite(jobId);

    persistence.catch(() => {
      // Si Supabase falla, revertimos el cambio optimista.
      const reverted = new Set(favoriteIdsRef.current);
      if (wasFavorite) {
        reverted.add(jobId);
      } else {
        reverted.delete(jobId);
      }
      favoriteIdsRef.current = reverted;
      setFavoriteIds(reverted);
    });
  }, []);

  const isFavorite = useCallback(
    (jobId: string) => favoriteIds.has(jobId),
    [favoriteIds],
  );

  const value = useMemo(
    () => ({ favoriteIds, isFavorite, toggleFavorite }),
    [favoriteIds, isFavorite, toggleFavorite],
  );

  return <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>;
}

export function useFavorites(): FavoritesContextValue {
  const context = useContext(FavoritesContext);
  if (!context) {
    throw new Error('useFavorites debe usarse dentro de <FavoritesProvider>.');
  }
  return context;
}
