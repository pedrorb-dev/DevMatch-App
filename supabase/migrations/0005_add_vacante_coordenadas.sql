-- SPEC 10 — Geocodificación de vacantes (lat/lng)
-- Coordenadas de la ubicación de la vacante, geocodificadas en el pipeline del scraper.
-- Nullable: null significa "sin coordenadas" (ubicación no geocodificable).

alter table public.vacantes
  add column lat double precision,
  add column lng double precision;
