-- Thai Astrology (Hora) persistence schema
-- Run this in the Supabase SQL editor.

create extension if not exists pgcrypto;

create table if not exists public.hora_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  birth_date date not null,
  birth_time time,
  birth_location text not null,
  birth_lat text,
  birth_lon text,
  transit_date date not null,
  transit_time time not null,
  transit_location text not null,
  transit_lat text,
  transit_lon text,
  chart_data jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.hora_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.hora_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.hora_readings (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.hora_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  category text not null check (category in ('THAI_ASTROLOGY_OVERVIEW', 'THAI_ASTROLOGY')),
  prediction text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_hora_sessions_user_updated
  on public.hora_sessions (user_id, updated_at desc);

create index if not exists idx_hora_messages_session_created
  on public.hora_messages (session_id, created_at asc);

create index if not exists idx_hora_readings_session_created
  on public.hora_readings (session_id, created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_hora_sessions_updated_at on public.hora_sessions;
create trigger set_hora_sessions_updated_at
before update on public.hora_sessions
for each row execute function public.set_updated_at();

alter table public.hora_sessions enable row level security;
alter table public.hora_messages enable row level security;
alter table public.hora_readings enable row level security;

drop policy if exists "Users can read own hora sessions" on public.hora_sessions;
create policy "Users can read own hora sessions"
on public.hora_sessions for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own hora sessions" on public.hora_sessions;
create policy "Users can insert own hora sessions"
on public.hora_sessions for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can update own hora sessions" on public.hora_sessions;
create policy "Users can update own hora sessions"
on public.hora_sessions for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own hora sessions" on public.hora_sessions;
create policy "Users can delete own hora sessions"
on public.hora_sessions for delete
using (auth.uid() = user_id);

drop policy if exists "Users can read own hora messages" on public.hora_messages;
create policy "Users can read own hora messages"
on public.hora_messages for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own hora messages" on public.hora_messages;
create policy "Users can insert own hora messages"
on public.hora_messages for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own hora messages" on public.hora_messages;
create policy "Users can delete own hora messages"
on public.hora_messages for delete
using (auth.uid() = user_id);

drop policy if exists "Users can read own hora readings" on public.hora_readings;
create policy "Users can read own hora readings"
on public.hora_readings for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own hora readings" on public.hora_readings;
create policy "Users can insert own hora readings"
on public.hora_readings for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own hora readings" on public.hora_readings;
create policy "Users can delete own hora readings"
on public.hora_readings for delete
using (auth.uid() = user_id);
