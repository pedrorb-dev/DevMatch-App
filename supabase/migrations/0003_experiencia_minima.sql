-- SPEC 05 — Scraper dinámico multi-fuente
-- Sustituye el booleano es_practicante por el entero experiencia_minima.
-- Reglas en el pipeline: 0 = entrada/practicante, 1 = sin mención,
-- 2/4/... = años explícitos o indicador senior.

alter table public.vacantes
  add column experiencia_minima integer not null default 1;

update public.vacantes
  set experiencia_minima = 0
  where es_practicante = true;

alter table public.vacantes
  drop column es_practicante;
