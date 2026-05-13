-- Allow Thai Astrology/Hora sessions without a known birth time.
-- Run this if the hora tables already exist from the older schema.

alter table public.hora_sessions
  alter column birth_time drop not null;
