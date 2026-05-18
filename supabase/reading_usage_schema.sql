-- Daily AI reading quota tracking.
-- Run this in the Supabase SQL editor before enabling the gateway rate limit.

create extension if not exists pgcrypto;

create table if not exists public.reading_usage_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  module text not null check (module in ('love', 'numerology', 'color', 'hora', 'tarot')),
  endpoint text not null,
  used_at timestamptz not null default now()
);

create index if not exists idx_reading_usage_events_user_used_at
  on public.reading_usage_events (user_id, used_at desc);

alter table public.reading_usage_events enable row level security;

drop policy if exists "Users can read own reading usage events" on public.reading_usage_events;
create policy "Users can read own reading usage events"
on public.reading_usage_events for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own reading usage events" on public.reading_usage_events;
create policy "Users can insert own reading usage events"
on public.reading_usage_events for insert
with check (auth.uid() = user_id);
