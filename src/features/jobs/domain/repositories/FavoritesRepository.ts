export interface FavoritesRepository {
  getFavoriteJobIds(): Promise<string[]>;
  addFavorite(jobId: string): Promise<void>;
  removeFavorite(jobId: string): Promise<void>;
}
