-- SportPredix — schéma initial (Supabase / Postgres)
-- Applique via : supabase db push   (ou copie-colle dans le SQL Editor Supabase)

-- ─────────────────────────────────────────────────────────────
-- Tables
-- ─────────────────────────────────────────────────────────────

-- Un coupon (combiné ou simple) généré un jour donné.
create table if not exists public.coupons (
  id            text primary key,                 -- ex. "2026-07-14" (+ suffixe si plusieurs)
  created_at    timestamptz not null default now(),
  match_date    date,
  bookmaker     text default 'Betano',
  total_odds    numeric,
  joint_prob    numeric,
  stake         numeric default 1,
  status        text not null default 'pending'   -- pending | won | lost | void
                  check (status in ('pending','won','lost','void')),
  out_of_range  boolean default false,            -- coupon de repli hors fourchette
  settled_at    timestamptz,
  retro         jsonb                              -- analyse rétro en cas de perte
);

-- Les jambes d'un coupon.
create table if not exists public.coupon_legs (
  id           bigint generated always as identity primary key,
  coupon_id    text not null references public.coupons(id) on delete cascade,
  match        text,
  sport        text,
  competition  text,
  market       text,
  pick         text,
  odds         numeric,
  est_prob     numeric,
  reliability  numeric,
  result       text not null default 'pending'    -- pending | won | lost | void
                 check (result in ('pending','won','lost','void')),
  note         text
);

-- Toutes les opportunités analysées (trace d'audit : gardées ET écartées).
create table if not exists public.opportunities (
  id            bigint generated always as identity primary key,
  run_id        text,
  coupon_id     text references public.coupons(id) on delete set null,
  match_date    date,
  match         text,
  sport         text,
  competition   text,
  market        text,
  pick          text,
  odds          numeric,
  est_prob      numeric,
  model_prob    numeric,
  research_prob numeric,
  edge          numeric,
  eff_edge      numeric,
  reliability   numeric,
  verdict       text,                              -- keep | drop | null
  rationale     text,
  created_at    timestamptz not null default now()
);

-- Leçons apprises (amélioration continue, alimentées par les rétros de pertes).
create table if not exists public.lessons (
  id          bigint generated always as identity primary key,
  created_at  timestamptz not null default now(),
  coupon_id   text,
  lesson      text not null
);

-- Métadonnées d'un run du pipeline (pour l'audit).
create table if not exists public.audit_runs (
  run_id        text primary key,
  created_at    timestamptz not null default now(),
  match_date    date,
  agents        int,
  matches       int,
  opportunities int,
  verified      int,
  meta          jsonb
);

create index if not exists idx_legs_coupon on public.coupon_legs(coupon_id);
create index if not exists idx_opps_run on public.opportunities(run_id);
create index if not exists idx_coupons_date on public.coupons(match_date desc);

-- ─────────────────────────────────────────────────────────────
-- Vue : bilan cumulé (ROI, taux de réussite)
-- ─────────────────────────────────────────────────────────────
create or replace view public.record_summary as
select
  count(*)                                            as total,
  count(*) filter (where status = 'won')              as won,
  count(*) filter (where status = 'lost')             as lost,
  count(*) filter (where status = 'pending')          as pending,
  coalesce(sum(stake) filter (where status in ('won','lost')), 0)                    as staked,
  coalesce(sum(stake * total_odds) filter (where status = 'won'), 0)
    - coalesce(sum(stake) filter (where status in ('won','lost')), 0)               as profit
from public.coupons;

-- ─────────────────────────────────────────────────────────────
-- RLS : lecture publique (dashboard), écriture réservée à la service key
-- (la service key contourne la RLS ; le bridge Python / le job l'utilisent).
-- Pour restreindre à des utilisateurs connectés, remplace `to anon` par
-- `to authenticated` et branche Supabase Auth côté app.
-- ─────────────────────────────────────────────────────────────
alter table public.coupons        enable row level security;
alter table public.coupon_legs    enable row level security;
alter table public.opportunities  enable row level security;
alter table public.lessons        enable row level security;
alter table public.audit_runs     enable row level security;

create policy "read coupons"       on public.coupons       for select to anon using (true);
create policy "read legs"          on public.coupon_legs   for select to anon using (true);
create policy "read opportunities" on public.opportunities for select to anon using (true);
create policy "read lessons"       on public.lessons       for select to anon using (true);
create policy "read audit"         on public.audit_runs    for select to anon using (true);
