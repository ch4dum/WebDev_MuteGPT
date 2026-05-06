-- Add birth_FAN to profiles table for Love Oracle
-- This allows storing the partner's birthdate in the user's profile.

alter table if exists public.profiles 
add column if not exists birth_FAN date;
