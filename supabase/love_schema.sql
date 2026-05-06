-- Love Oracle persistence schema
-- Run this in the Supabase SQL editor.

create extension if not exists pgcrypto;

create table if not exists public.love_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  status_key text not null check (status_key in ('single', 'talking', 'couple', 'broken')),
  status_label text not null,
  status_focus text not null,
  fan_birthdate date,
  title text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.love_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.love_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.love_readings (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.love_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  category text not null check (category in ('LOVE_OVERVIEW', 'LOVE')),
  prediction text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_love_sessions_user_updated
  on public.love_sessions (user_id, updated_at desc);

create index if not exists idx_love_messages_session_created
  on public.love_messages (session_id, created_at asc);

create index if not exists idx_love_readings_session_created
  on public.love_readings (session_id, created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_love_sessions_updated_at on public.love_sessions;
create trigger set_love_sessions_updated_at
before update on public.love_sessions
for each row execute function public.set_updated_at();

alter table public.love_sessions enable row level security;
alter table public.love_messages enable row level security;
alter table public.love_readings enable row level security;

drop policy if exists "Users can read own love sessions" on public.love_sessions;
create policy "Users can read own love sessions"
on public.love_sessions for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own love sessions" on public.love_sessions;
create policy "Users can insert own love sessions"
on public.love_sessions for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can update own love sessions" on public.love_sessions;
create policy "Users can update own love sessions"
on public.love_sessions for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own love sessions" on public.love_sessions;
create policy "Users can delete own love sessions"
on public.love_sessions for delete
using (auth.uid() = user_id);

drop policy if exists "Users can read own love messages" on public.love_messages;
create policy "Users can read own love messages"
on public.love_messages for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own love messages" on public.love_messages;
create policy "Users can insert own love messages"
on public.love_messages for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own love messages" on public.love_messages;
create policy "Users can delete own love messages"
on public.love_messages for delete
using (auth.uid() = user_id);

drop policy if exists "Users can read own love readings" on public.love_readings;
create policy "Users can read own love readings"
on public.love_readings for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own love readings" on public.love_readings;
create policy "Users can insert own love readings"
on public.love_readings for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own love readings" on public.love_readings;
create policy "Users can delete own love readings"
on public.love_readings for delete
using (auth.uid() = user_id);
