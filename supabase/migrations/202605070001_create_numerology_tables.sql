-- Numerology Oracle persistence schema
-- Run this in the Supabase SQL editor.

create extension if not exists pgcrypto;

create table if not exists public.numerology_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  category text not null check (category in ('phone', 'plate', 'address', 'bank', 'general')),
  category_label text not null,
  number_input text not null,
  title text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.numerology_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.numerology_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.numerology_readings (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.numerology_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  root_number integer,
  calculation_steps integer[],
  prediction text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_numerology_sessions_user_category_updated
  on public.numerology_sessions (user_id, category, updated_at desc);

create index if not exists idx_numerology_messages_session_created
  on public.numerology_messages (session_id, created_at asc);

create index if not exists idx_numerology_readings_session_created
  on public.numerology_readings (session_id, created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_numerology_sessions_updated_at on public.numerology_sessions;
create trigger set_numerology_sessions_updated_at
before update on public.numerology_sessions
for each row execute function public.set_updated_at();

alter table public.numerology_sessions enable row level security;
alter table public.numerology_messages enable row level security;
alter table public.numerology_readings enable row level security;

drop policy if exists "Users can read own numerology sessions" on public.numerology_sessions;
create policy "Users can read own numerology sessions"
on public.numerology_sessions for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own numerology sessions" on public.numerology_sessions;
create policy "Users can insert own numerology sessions"
on public.numerology_sessions for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can update own numerology sessions" on public.numerology_sessions;
create policy "Users can update own numerology sessions"
on public.numerology_sessions for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own numerology sessions" on public.numerology_sessions;
create policy "Users can delete own numerology sessions"
on public.numerology_sessions for delete
using (auth.uid() = user_id);

drop policy if exists "Users can read own numerology messages" on public.numerology_messages;
create policy "Users can read own numerology messages"
on public.numerology_messages for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own numerology messages" on public.numerology_messages;
create policy "Users can insert own numerology messages"
on public.numerology_messages for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own numerology messages" on public.numerology_messages;
create policy "Users can delete own numerology messages"
on public.numerology_messages for delete
using (auth.uid() = user_id);

drop policy if exists "Users can read own numerology readings" on public.numerology_readings;
create policy "Users can read own numerology readings"
on public.numerology_readings for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own numerology readings" on public.numerology_readings;
create policy "Users can insert own numerology readings"
on public.numerology_readings for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own numerology readings" on public.numerology_readings;
create policy "Users can delete own numerology readings"
on public.numerology_readings for delete
using (auth.uid() = user_id);
