-- Color Oracle persistence schema
-- Run this in the Supabase SQL editor.

create extension if not exists pgcrypto;

create table if not exists public.color_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  category text not null check (category in ('daily', 'personal', 'wealth', 'general')),
  category_label text not null,
  question_input text not null,
  title text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.color_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.color_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.color_readings (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.color_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  category text not null check (category in ('daily', 'personal', 'wealth', 'general')),
  prediction text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_color_sessions_user_category_updated
  on public.color_sessions (user_id, category, updated_at desc);

create index if not exists idx_color_messages_session_created
  on public.color_messages (session_id, created_at asc);

create index if not exists idx_color_readings_session_created
  on public.color_readings (session_id, created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_color_sessions_updated_at on public.color_sessions;
create trigger set_color_sessions_updated_at
before update on public.color_sessions
for each row execute function public.set_updated_at();

alter table public.color_sessions enable row level security;
alter table public.color_messages enable row level security;
alter table public.color_readings enable row level security;

drop policy if exists "Users can read own color sessions" on public.color_sessions;
create policy "Users can read own color sessions"
on public.color_sessions for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own color sessions" on public.color_sessions;
create policy "Users can insert own color sessions"
on public.color_sessions for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can update own color sessions" on public.color_sessions;
create policy "Users can update own color sessions"
on public.color_sessions for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own color sessions" on public.color_sessions;
create policy "Users can delete own color sessions"
on public.color_sessions for delete
using (auth.uid() = user_id);

drop policy if exists "Users can read own color messages" on public.color_messages;
create policy "Users can read own color messages"
on public.color_messages for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own color messages" on public.color_messages;
create policy "Users can insert own color messages"
on public.color_messages for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own color messages" on public.color_messages;
create policy "Users can delete own color messages"
on public.color_messages for delete
using (auth.uid() = user_id);

drop policy if exists "Users can read own color readings" on public.color_readings;
create policy "Users can read own color readings"
on public.color_readings for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own color readings" on public.color_readings;
create policy "Users can insert own color readings"
on public.color_readings for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own color readings" on public.color_readings;
create policy "Users can delete own color readings"
on public.color_readings for delete
using (auth.uid() = user_id);
