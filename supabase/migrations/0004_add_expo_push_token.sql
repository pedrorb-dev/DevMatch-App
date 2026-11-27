-- SPEC 09 — Notificaciones push con match de stack al 100%
-- Guarda el token Expo del dispositivo en el perfil del usuario único.
-- Nullable: solo se rellena cuando la app obtiene el token.

alter table public.user_profiles
  add column expo_push_token text;
