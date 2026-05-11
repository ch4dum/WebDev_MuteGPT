-- Tarot reading persistence schema
-- Run this in the Supabase SQL editor.

create extension if not exists pgcrypto;

create table if not exists public.tarot_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  category text not null check (category in ('three_situations', 'daily', 'love', 'work', 'finance', 'study', 'health')),
  category_label text not null,
  subcategory text,
  subcategory_label text,
  spread_type text not null,
  question_input text not null,
  title text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.tarot_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.tarot_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.tarot_readings (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.tarot_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  category text not null check (category in ('three_situations', 'daily', 'love', 'work', 'finance', 'study', 'health')),
  subcategory text,
  spread_type text not null,
  question_input text not null,
  cards jsonb not null default '[]'::jsonb,
  prediction text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_tarot_sessions_user_category_updated
  on public.tarot_sessions (user_id, category, updated_at desc);

create index if not exists idx_tarot_messages_session_created
  on public.tarot_messages (session_id, created_at asc);

create index if not exists idx_tarot_readings_session_created
  on public.tarot_readings (session_id, created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_tarot_sessions_updated_at on public.tarot_sessions;
create trigger set_tarot_sessions_updated_at
before update on public.tarot_sessions
for each row execute function public.set_updated_at();

alter table public.tarot_sessions enable row level security;
alter table public.tarot_messages enable row level security;
alter table public.tarot_readings enable row level security;

drop policy if exists "Users can read own tarot sessions" on public.tarot_sessions;
create policy "Users can read own tarot sessions"
on public.tarot_sessions for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own tarot sessions" on public.tarot_sessions;
create policy "Users can insert own tarot sessions"
on public.tarot_sessions for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can update own tarot sessions" on public.tarot_sessions;
create policy "Users can update own tarot sessions"
on public.tarot_sessions for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own tarot sessions" on public.tarot_sessions;
create policy "Users can delete own tarot sessions"
on public.tarot_sessions for delete
using (auth.uid() = user_id);

drop policy if exists "Users can read own tarot messages" on public.tarot_messages;
create policy "Users can read own tarot messages"
on public.tarot_messages for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own tarot messages" on public.tarot_messages;
create policy "Users can insert own tarot messages"
on public.tarot_messages for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own tarot messages" on public.tarot_messages;
create policy "Users can delete own tarot messages"
on public.tarot_messages for delete
using (auth.uid() = user_id);

drop policy if exists "Users can read own tarot readings" on public.tarot_readings;
create policy "Users can read own tarot readings"
on public.tarot_readings for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own tarot readings" on public.tarot_readings;
create policy "Users can insert own tarot readings"
on public.tarot_readings for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own tarot readings" on public.tarot_readings;
create policy "Users can delete own tarot readings"
on public.tarot_readings for delete
using (auth.uid() = user_id);
