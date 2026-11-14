import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react';

interface FavoritesContextValue {
  favoriteIds: ReadonlySet<string>;
  isFavorite: (jobId: string) => boolean;
  toggleFavorite: (jobId: string) => void;
}

const FavoritesContext = createContext<FavoritesContextValue | undefined>(undefined);

export function FavoritesProvider({ children }: PropsWithChildren) {
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(() => new Set());

  const toggleFavorite = useCallback((jobId: string) => {
    setFavoriteIds((current) => {
      const next = new Set(current);
      if (next.has(jobId)) {
        next.delete(jobId);
      } else {
        next.add(jobId);
      }
      return next;
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
