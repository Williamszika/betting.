# SportPredix — App (Next.js + Supabase + Vercel)

Dashboard de suivi des coupons (🟢/🔴, ROI, rétros) qui lit **Supabase**.
Mode **hybride** : le pipeline d'analyse tourne dans **Claude Code** (jobs 20h/12h)
et pousse les résultats dans Supabase via `scripts/push_to_supabase.py` ; l'app
ne fait qu'**afficher et gérer**.

## 1. Supabase (base)
1. Crée un projet sur https://supabase.com.
2. SQL Editor → colle et exécute `supabase/migrations/0001_init.sql`
   (ou `supabase db push` avec la CLI).
3. Project Settings → API : note `Project URL`, `anon key`, `service_role key`.

## 2. App en local
```bash
cd web
cp .env.example .env.local     # renseigne URL + anon key
npm install
npm run dev                    # http://localhost:3000
```

## 3. Déploiement Vercel
1. Push ce repo sur GitHub (déjà fait).
2. https://vercel.com → New Project → importe le repo.
3. **Root Directory : `web`** (important).
4. Variables d'env : `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
5. Deploy. (Framework Next.js détecté automatiquement.)

## 4. Alimenter la base (bridge hybride)
Le job Claude Code (ou toi, manuellement) synchronise le registre local :
```bash
SUPABASE_URL=https://xxx.supabase.co \
SUPABASE_SERVICE_KEY=eyJ...service_role... \
python3 scripts/push_to_supabase.py
```
> ⚠️ La `service_role key` contourne la RLS : **jamais côté client**, uniquement
> dans le job/bridge (secret d'environnement).

## Sécurité / RLS
La migration ouvre la **lecture publique** (dashboard sans login). Pour restreindre
à des utilisateurs connectés : remplace `to anon` par `to authenticated` dans les
policies et branche **Supabase Auth** (magic link) côté app.

## Ce qui reste à brancher (étapes suivantes)
- Auth (login) si tu veux un dashboard privé.
- Une route API `/api/coupon/today` + Vercel Cron si tu veux, plus tard, faire
  tourner une version légère du pipeline hors Claude Code (nécessite une clé
  Anthropic + un worker pour la recherche, cf. limite de temps serverless).

**Estimations, pas des garanties. Jeu responsable — joueurs-info-service.fr.**
