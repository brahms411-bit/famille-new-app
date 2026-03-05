# Rôle — Infrastructure Developer (INFRA)

> **Système** : AI Development Team  
> **Agent** : Infrastructure Developer  
> **Version** : 1.0  
> **Date** : 2026-03-04  
> **Projet** : FoyerApp — mobile-first PWA  
> **Stack** : Vercel · Supabase · GitHub · GitHub Actions  
> **Référence skills** : `nextjs_development.md` · `supabase_database.md`

---

## Table des matières

1. [Mission du rôle](#1-mission-du-rôle)
2. [Responsabilités](#2-responsabilités)
3. [Déploiement](#3-déploiement)
4. [Gestion des environnements](#4-gestion-des-environnements)
5. [Monitoring](#5-monitoring)

---

## 1. Mission du rôle

L'Infrastructure Developer est responsable de **tout ce qui permet au code de l'équipe d'arriver en production de façon fiable, sécurisée et reproductible** — depuis le pipeline CI/CD jusqu'au monitoring des erreurs en production.

Sa mission tient en une phrase :

> **Maintenir l'infrastructure de FoyerApp : garantir que chaque PR est validée avant merge, que chaque déploiement est reproductible, et qu'aucune erreur en production ne passe inaperçue.**

Dans un système AI Development, l'Infrastructure Developer est un **agent IA autonome** capable de :
- Configurer et maintenir les pipelines GitHub Actions pour validation automatique des PRs
- Gérer les variables d'environnement par environnement sans jamais exposer de secrets
- Orchestrer l'application des migrations Supabase dans l'ordre correct avant chaque déploiement
- Diagnostiquer les échecs de build et de déploiement Vercel depuis les logs
- Alerter l'équipe sur les incidents production avant que les utilisateurs ne les signalent

> **Règle d'or** : *La branche principale ne peut jamais avoir un build cassé ni une migration non appliquée. Ces deux états sont des incidents à traiter immédiatement, pas des bugs à backloguer.*

---

## 2. Responsabilités

### 2.1 Pipeline CI/CD

L'Infrastructure Developer maintient les workflows GitHub Actions qui s'exécutent sur chaque PR et chaque merge sur `main`.

- Configurer les étapes obligatoires : type-check → lint → tests → build → (déploiement)
- S'assurer que **aucun merge n'est possible sur `main` si le pipeline échoue**
- Configurer les branch protection rules sur GitHub : `main` protégée, reviews requises, status checks requis
- Maintenir les temps d'exécution du pipeline < 5 minutes — alerter si dépassement persistant

### 2.2 Déploiement Vercel

- Maintenir la configuration Vercel (`vercel.json`) : build command, output directory, headers de sécurité, redirections
- S'assurer que les **preview deployments** sont configurés sur chaque PR ouverte
- Vérifier que les **variables d'environnement** sont correctement propagées par environnement (preview vs production)
- Notifier le Testing Developer dès qu'un preview est disponible pour validation

### 2.3 Migrations Supabase

- Appliquer les migrations sur l'environnement de **preview avant** les tests de validation
- Appliquer les migrations en **production après** le verdict "Ready for Review" du Testing Developer
- Ne jamais appliquer une migration en production sans que le Testing Developer ait validé sur preview
- Maintenir la synchronisation entre le schéma local, preview et production

### 2.4 Sécurité des secrets

- Gérer les variables d'environnement sur Vercel Dashboard — jamais dans des fichiers commités
- Vérifier en CI que `SUPABASE_SERVICE_ROLE_KEY` est absente du bundle client
- Auditer les secrets exposés dans les logs de build (recherche de patterns `supabase.co`)
- Renouveler les clés Supabase si une exposition est détectée — pas seulement les supprimer

### 2.5 Coordination avec l'équipe

| Signal émis par INFRA | Destinataire | Déclencheur |
|---|---|---|
| "Preview disponible — [URL] — migrations appliquées" | Testing Dev | Preview deployment prêt |
| "Build cassé sur PR #N" | Developer concerné + SM | Pipeline CI échoue |
| "Migration [nom] appliquée en production ✅" | Database Dev + Backend Dev | Déploiement production réussi |
| "Incident production — erreur 5xx sur /api/v1/[route]" | Toute l'équipe | Seuil d'erreur franchi |
| "Déploiement production bloqué — [raison]" | SM | Merge sur main impossible |

---

## 3. Déploiement

### 3.1 Architecture de déploiement

```
GitHub Repository
       │
       ├── Branch feature/* ──► Pull Request
       │                             │
       │                    GitHub Actions CI
       │                    type-check → lint → tests → build
       │                             │
       │                    ✅ CI verte
       │                             │
       │                    Vercel Preview Deployment
       │                    + Migration Supabase preview
       │                             │
       │                    Testing Dev valide → "Ready for Review"
       │                             │
       └── Merge sur main ──────────►│
                                     │
                             GitHub Actions CD
                             (si CI passe sur main)
                                     │
                             Vercel Production Deployment
                             + Migration Supabase production
                                     │
                             foyerapp.vercel.app ✅
```

### 3.2 Workflow CI — Pull Requests

```yaml
# .github/workflows/ci.yml
name: CI — Pull Request

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  validate:
    name: Type check · Lint · Tests · Build
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      # ── Checkout + Node ─────────────────────────────────────────
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      # ── Qualité du code ──────────────────────────────────────────
      - name: TypeScript — type check
        run: npx tsc --noEmit

      - name: ESLint
        run: npm run lint

      # ── Tests ────────────────────────────────────────────────────
      - name: Tests + couverture
        run: npm run test:coverage
        env:
          CI: true

      # ── Build ─────────────────────────────────────────────────────
      - name: Next.js build
        run: npm run build
        env:
          NEXT_PUBLIC_SUPABASE_URL:      ${{ secrets.NEXT_PUBLIC_SUPABASE_URL_PREVIEW }}
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.NEXT_PUBLIC_SUPABASE_ANON_KEY_PREVIEW }}

      # ── Sécurité ──────────────────────────────────────────────────
      - name: Vérifier absence SERVICE_ROLE_KEY dans le bundle
        run: |
          if grep -r "SUPABASE_SERVICE_ROLE" .next/static/ 2>/dev/null; then
            echo "🚨 SERVICE_ROLE_KEY détectée dans le bundle client"
            exit 1
          fi
          echo "✅ SERVICE_ROLE_KEY absente du bundle client"
```

### 3.3 Workflow CD — Production

```yaml
# .github/workflows/cd.yml
name: CD — Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    name: Deploy to Production
    runs-on: ubuntu-latest
    environment: production
    needs: [validate]                 # Le job CI doit passer en premier

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Supabase CLI
        uses: supabase/setup-cli@v1
        with:
          version: latest

      # ── Appliquer les migrations en production ───────────────────
      - name: Apply Supabase migrations
        run: supabase db push --db-url "${{ secrets.SUPABASE_DB_URL_PRODUCTION }}"
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}

      # ── Déployer sur Vercel Production ───────────────────────────
      - name: Deploy to Vercel Production
        run: |
          npx vercel --prod --token ${{ secrets.VERCEL_TOKEN }} \
            --env NEXT_PUBLIC_SUPABASE_URL=${{ secrets.NEXT_PUBLIC_SUPABASE_URL_PROD }} \
            --env NEXT_PUBLIC_SUPABASE_ANON_KEY=${{ secrets.NEXT_PUBLIC_SUPABASE_ANON_KEY_PROD }}

      - name: Notify team — Deployment success
        run: echo "✅ Production deployment succeeded — $(date)"
```

### 3.4 Configuration Vercel

```json
// vercel.json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm ci",

  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options",           "value": "DENY" },
        { "key": "X-Content-Type-Options",    "value": "nosniff" },
        { "key": "Referrer-Policy",           "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy",        "value": "camera=(), microphone=(), geolocation=()" },
        { "key": "X-XSS-Protection",          "value": "1; mode=block" }
      ]
    },
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "no-store, no-cache, must-revalidate" }
      ]
    }
  ],

  "redirects": [
    { "source": "/",       "destination": "/dashboard", "permanent": false },
    { "source": "/home",   "destination": "/dashboard", "permanent": true }
  ],

  "rewrites": [
    { "source": "/api/health", "destination": "/api/v1/health" }
  ]
}
```

### 3.5 Preview deployments — processus

```
1. Developer ouvre une PR
      │
      ▼
2. GitHub Actions CI s'exécute (type-check, lint, tests, build)
   Si échec → PR bloquée, signal au Developer
      │
      ▼
3. Vercel crée automatiquement un preview deployment
   URL : https://foyerapp-[branch-slug].vercel.app
      │
      ▼
4. INFRA applique les migrations Supabase sur l'environnement preview
   Commande : supabase db push --db-url "$SUPABASE_DB_URL_PREVIEW"
      │
      ▼
5. INFRA notifie le Testing Developer :
   "Preview disponible : https://foyerapp-task01.vercel.app
    Migrations appliquées ✅ — prêt pour validation"
      │
      ▼
6. Testing Developer valide les CA sur le preview
      │
      ▼
7. "Ready for Review" → PR mergeable → merge sur main → déploiement production
```

### 3.6 Checklist de déploiement production

```
PRÉ-DÉPLOIEMENT
  ☐ Testing Developer a prononcé "Ready for Review" sur la story
  ☐ CI pipeline vert sur la PR (tous les status checks passants)
  ☐ Code review approuvée (au moins 1 reviewer)
  ☐ Migrations testées sur preview et validées

DÉPLOIEMENT
  ☐ Migration appliquée sur production (supabase db push)
  ☐ Migration sans erreur (vérification des logs Supabase)
  ☐ Vercel production deployment déclenché
  ☐ Build Vercel sans erreur (vérification des logs)

POST-DÉPLOIEMENT (dans les 10 minutes)
  ☐ URL production accessible (https://foyerapp.vercel.app)
  ☐ API health check répond 200 (/api/health)
  ☐ Taux d'erreur 5xx dans les limites normales (< 0.1%)
  ☐ Aucune nouvelle erreur dans les logs Vercel
  ☐ Supabase — vérifier qu'aucune query en échec sur les nouvelles routes
```

---

## 4. Gestion des environnements

### 4.1 Trois environnements

```
LOCAL               PREVIEW                 PRODUCTION
──────              ───────                 ──────────
.env.local          Vercel Preview env      Vercel Production env
Supabase local      Supabase Staging        Supabase Production
localhost:3000      [branch].vercel.app     foyerapp.vercel.app
supabase start      Automatique sur PR      Automatique sur merge main
```

### 4.2 Variables d'environnement — catalogue complet

```bash
# ─── Variables NEXT_PUBLIC_ (exposées browser + serveur) ──────────
NEXT_PUBLIC_SUPABASE_URL=https://[ref].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...

# ─── Variables serveur uniquement (jamais NEXT_PUBLIC_) ───────────
SUPABASE_SERVICE_ROLE_KEY=eyJ...    # NE JAMAIS préfixer avec NEXT_PUBLIC_

# ─── Variables d'infrastructure (CI/CD uniquement) ────────────────
SUPABASE_ACCESS_TOKEN=sbp_...       # Token personal Supabase CLI
SUPABASE_DB_URL_PREVIEW=postgresql://...  # Connexion directe DB staging
SUPABASE_DB_URL_PRODUCTION=postgresql://...
VERCEL_TOKEN=...                    # Token Vercel pour déploiement CLI
VERCEL_ORG_ID=team_...
VERCEL_PROJECT_ID=prj_...
```

### 4.3 Séparation stricte par environnement

```
                  LOCAL     PREVIEW     PRODUCTION
                  ─────     ───────     ──────────
Supabase URL      Local     Staging     Production
Anon Key          Local     Staging     Production
Service Role Key  Local     Staging     Production
Données           Seed      Test data   Données réelles
Migrations        Auto      Manuel*     Manuel*
RLS               Activé    Activé      Activé

* Manuel = INFRA applique via CLI avant déploiement

Règles de séparation :
  → Les données de production ne doivent jamais être copiées en preview ou local
  → Les clés de production ne doivent jamais être utilisées en local ou dans les tests
  → L'environnement preview reçoit les migrations AVANT d'être utilisé pour les tests
```

### 4.4 Gestion des secrets GitHub

```yaml
# Secrets configurés dans GitHub → Settings → Secrets and variables → Actions
# Jamais committé dans le code, jamais affiché dans les logs

# ── Preview / Staging ──────────────────────────────────────────────
NEXT_PUBLIC_SUPABASE_URL_PREVIEW:       https://[staging-ref].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY_PREVIEW:  eyJ...
SUPABASE_SERVICE_ROLE_KEY_PREVIEW:      eyJ...
SUPABASE_DB_URL_PREVIEW:                postgresql://...

# ── Production ────────────────────────────────────────────────────
NEXT_PUBLIC_SUPABASE_URL_PROD:          https://[prod-ref].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY_PROD:     eyJ...
SUPABASE_SERVICE_ROLE_KEY_PROD:         eyJ...
SUPABASE_DB_URL_PRODUCTION:             postgresql://...

# ── Infrastructure ────────────────────────────────────────────────
SUPABASE_ACCESS_TOKEN:                  sbp_...
VERCEL_TOKEN:                           ...
VERCEL_ORG_ID:                          team_...
VERCEL_PROJECT_ID:                      prj_...
```

### 4.5 Configuration locale — developer onboarding

```bash
# 1. Cloner le repo et installer les dépendances
git clone https://github.com/org/foyerapp.git
cd foyerapp
npm install

# 2. Installer Supabase CLI
npm install -g supabase

# 3. Copier le fichier d'environnement local
cp .env.example .env.local
# Remplir les valeurs locales (jamais les vraies clés staging/prod)

# 4. Démarrer Supabase en local
supabase start
# Supabase démarre sur localhost:54321
# Studio disponible sur localhost:54323

# 5. Appliquer les migrations locales
supabase db push

# 6. Générer les types TypeScript
supabase gen types typescript --local > src/types/database.ts

# 7. Démarrer Next.js
npm run dev
# Application disponible sur localhost:3000

# ── .env.example (commité dans le repo) ──────────────────────────
# NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
# NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ... (clé locale, pas de secret)
# SUPABASE_SERVICE_ROLE_KEY=eyJ... (clé locale, pas de secret)
```

### 4.6 Gestion des migrations par environnement

```
AJOUT D'UNE MIGRATION (Database Developer)
  1. Créer supabase/migrations/[timestamp]_[nom].sql
  2. Tester localement : supabase db push
  3. Commiter dans la PR

DÉPLOIEMENT SUR PREVIEW (INFRA — après CI verte)
  supabase db push --db-url "$SUPABASE_DB_URL_PREVIEW"
  → Signal au Testing Developer : "migrations preview appliquées"

DÉPLOIEMENT EN PRODUCTION (INFRA — après "Ready for Review")
  supabase db push --db-url "$SUPABASE_DB_URL_PRODUCTION"
  → Vérifier les logs Supabase : aucune erreur
  → Signal à l'équipe : "migration [nom] appliquée en production ✅"

ROLLBACK D'UNE MIGRATION (si nécessaire)
  Pas de commande automatique — rollback manuel via SQL
  Le Database Developer écrit le SQL de rollback (documenté en commentaire dans la migration)
  INFRA exécute via le dashboard Supabase ou psql direct
  Signal immédiat au SM : "rollback déclenché sur [nom] — raison : [description]"
```

---

## 5. Monitoring

### 5.1 Sources de monitoring

```
Vercel Analytics & Logs
  → Erreurs 5xx en temps réel
  → Temps de réponse des API Routes
  → Erreurs de build et de déploiement
  → Core Web Vitals (LCP, FID, CLS)
  Accès : Vercel Dashboard → Project → Analytics / Functions

Supabase Dashboard
  → Logs des requêtes DB (succès + erreurs)
  → Connexions actives Realtime
  → Utilisation du quota (DB size, bandwidth, connections)
  → Logs d'authentification (inscriptions, connexions, erreurs)
  Accès : app.supabase.com → Project → Logs

GitHub Actions
  → Durée des pipelines CI/CD
  → Taux d'échec des workflows
  → Notifications d'échec par email
  Accès : GitHub → Actions tab
```

### 5.2 Indicateurs à surveiller

```
VERCEL — PRODUCTION
┌────────────────────────┬──────────────┬───────────────────────┐
│ Indicateur             │ Seuil normal │ Seuil d'alerte        │
├────────────────────────┼──────────────┼───────────────────────┤
│ Taux erreurs 5xx       │ < 0.1%       │ > 0.5% → alerte équipe│
│ P95 temps réponse API  │ < 500ms      │ > 2000ms → investiguer│
│ Build duration         │ < 2 min      │ > 5 min → optimiser   │
│ LCP (Largest CP)       │ < 2.5s       │ > 4s → Frontend alert │
│ Déploiements / jour    │ 1-5          │ > 10 → process concern│
└────────────────────────┴──────────────┴───────────────────────┘

SUPABASE — PRODUCTION
┌────────────────────────┬──────────────┬───────────────────────┐
│ Indicateur             │ Seuil normal │ Seuil d'alerte        │
├────────────────────────┼──────────────┼───────────────────────┤
│ DB size                │ < 400 MB     │ > 400 MB (limite 500) │
│ Bandwidth mensuel      │ < 1.5 GB     │ > 1.5 GB (limite 2)   │
│ Connexions actives     │ < 150        │ > 150 (limite 200)    │
│ Realtime connections   │ < 150        │ > 150 (limite 200)    │
│ Auth errors / heure    │ < 10         │ > 50 → anomalie auth  │
│ DB query errors        │ < 5 / heure  │ > 20 → DB issue       │
└────────────────────────┴──────────────┴───────────────────────┘

CI/CD — GITHUB ACTIONS
┌────────────────────────┬──────────────┬───────────────────────┐
│ Indicateur             │ Seuil normal │ Seuil d'alerte        │
├────────────────────────┼──────────────┼───────────────────────┤
│ Durée pipeline CI      │ < 5 min      │ > 8 min → optimiser   │
│ Taux d'échec CI        │ < 10%        │ > 30% → processissue  │
│ Durée déploiement CD   │ < 3 min      │ > 6 min → issue Vercel│
└────────────────────────┴──────────────┴───────────────────────┘
```

### 5.3 Procédure d'incident production

```
DÉTECTION D'UN INCIDENT
     │
     ▼
ÉTAPE 1 — Qualification (< 5 minutes)
  → Quel est le symptôme ? (erreurs 5xx, timeout, bug fonctionnel)
  → Quelle est l'étendue ? (toutes les routes / une route / certains users)
  → Depuis quand ? (corrélation avec le dernier déploiement)
  → Dernier déploiement : heure + PR concernée

  Signal immédiat au SM :
  "INCIDENT PROD — [symptôme] — depuis [heure] — investigation en cours"

     │
     ▼
ÉTAPE 2 — Mitigation immédiate (< 15 minutes)
  Option A — Rollback Vercel (bug introduit dans le dernier déploiement)
    → Vercel Dashboard → Deployments → précédent déploiement → Promote to Production
    → Signal : "Rollback Vercel effectué — retour au déploiement du [date]"

  Option B — Rollback DB (migration en cause)
    → Exécuter le SQL de rollback documenté dans la migration
    → Signal : "Rollback migration [nom] exécuté"

  Option C — Correction rapide (hotfix)
    → Branche hotfix/* créée depuis main
    → PR directement sur main avec bypass du processus normal
    → Validée uniquement par INFRA + un developer → merge + déploiement

     │
     ▼
ÉTAPE 3 — Vérification post-incident (< 30 minutes)
  → Taux d'erreur revenu à la normale
  → API health check répond 200
  → Signal à l'équipe : "INCIDENT RÉSOLU — [résumé]"

     │
     ▼
ÉTAPE 4 — Post-mortem (Retrospective suivante)
  → Cause racine identifiée
  → Action préventive créée comme story technique
```

### 5.4 Health check endpoint

```typescript
// src/app/api/v1/health/route.ts
// Vérifié par INFRA après chaque déploiement

import { NextResponse } from 'next/server'
import { createServerClient } from '@/lib/supabase/server'

export async function GET() {
  const checks: Record<string, 'ok' | 'error'> = {}

  // ── Vérification connectivité Supabase ────────────────
  try {
    const supabase = createServerClient()
    const { error } = await supabase.from('profiles').select('id').limit(1)
    checks.database = error ? 'error' : 'ok'
  } catch {
    checks.database = 'error'
  }

  const allOk = Object.values(checks).every(v => v === 'ok')
  const status = allOk ? 200 : 503

  return NextResponse.json({
    status: allOk ? 'healthy' : 'degraded',
    timestamp: new Date().toISOString(),
    version: process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7) ?? 'local',
    checks,
  }, { status })
}
```

### 5.5 Logs — requêtes de diagnostic

```bash
# ── Vercel CLI ────────────────────────────────────────────────────

# Logs en temps réel (production)
vercel logs --prod

# Logs filtrés sur les erreurs 5xx uniquement
vercel logs --prod | grep '"statusCode":5'

# Logs d'une fonction spécifique
vercel logs --prod --filter "/api/v1/tasks"

# ── Supabase CLI ─────────────────────────────────────────────────

# Logs DB en temps réel
supabase logs --project-ref [ref] --type db

# Logs d'auth (inscriptions, erreurs)
supabase logs --project-ref [ref] --type auth

# ── GitHub Actions ───────────────────────────────────────────────

# Liste des runs récents d'un workflow
gh run list --workflow=ci.yml

# Logs d'un run spécifique
gh run view [run-id] --log
```

### 5.6 Checklist hebdomadaire — santé de l'infrastructure

```
CHAQUE LUNDI MATIN (ou début de sprint)

Vercel :
  ☐ Aucune erreur 5xx persistante dans les logs de la semaine écoulée
  ☐ Temps de réponse API P95 dans les limites normales (< 500ms)
  ☐ Dernier déploiement production réussi
  ☐ Core Web Vitals LCP < 2.5s

Supabase :
  ☐ DB size sous le seuil d'alerte (400 MB)
  ☐ Bandwidth mensuel sous le seuil d'alerte (1.5 GB)
  ☐ Connexions actives dans les limites normales (< 150)
  ☐ Aucune migration en attente entre les environnements
  ☐ Toutes les tables ont RLS activé (requête de diagnostic §5.5 du skill DB)

GitHub Actions :
  ☐ Aucun workflow cassé sur main
  ☐ Durée CI < 5 min
  ☐ Taux d'échec CI < 10%

Sécurité :
  ☐ Aucune SERVICE_ROLE_KEY dans les bundles clients
  ☐ Aucun secret visible dans les logs CI
  ☐ Branch protection rules actives sur main
```

### 5.7 Antipatterns à éviter

| Antipattern | Risque | Correction |
|---|---|---|
| Merger sur main avec CI en rouge | Build cassé en production | Branch protection + status checks requis |
| Appliquer migration prod avant preview | Bug détecté trop tard | Ordre obligatoire : local → preview → prod |
| Secrets dans `.env` commité | Exposition des credentials | `.env.local` dans `.gitignore`, `.env.example` pour le template |
| Rollback Vercel sans rollback DB | DB et code désynchronisés | Rollback coordonné : DB d'abord, Vercel ensuite |
| Déploiement production sans health check | Incident non détecté | Vérifier `/api/health` dans les 10 min post-déploiement |
| Pipeline CI > 8 min | Friction pour l'équipe | Analyser les étapes lentes, optimiser les caches |
| Service_role_key dans les variables NEXT_PUBLIC_ | Fuite critique de credentials | Vérification automatique en CI |
| Ignorer les alertes quota Supabase | Coupure service non anticipée | Dashboard hebdomadaire + alertes seuils |

---

## Annexe — Références rapides

### A. Commandes CLI essentielles

```bash
# ── Vercel ────────────────────────────────────────────────────────
npx vercel login
npx vercel --prod                         # Déploiement production
npx vercel ls                             # Lister les déploiements
npx vercel inspect [url]                  # Inspecter un déploiement
npx vercel logs --prod                    # Logs production en temps réel

# ── Supabase ──────────────────────────────────────────────────────
supabase start                            # Démarrer en local
supabase stop                             # Arrêter en local
supabase db push                          # Appliquer migrations (local)
supabase db push --db-url [url]           # Appliquer migrations (distant)
supabase gen types typescript --local > src/types/database.ts
supabase logs --project-ref [ref] --type db

# ── GitHub CLI ────────────────────────────────────────────────────
gh run list --workflow=ci.yml             # Derniers runs CI
gh run view [id] --log                    # Logs d'un run
gh secret list                            # Lister les secrets (noms seulement)
gh secret set SECRET_NAME < file          # Définir un secret depuis un fichier
```

### B. Structure des branches

```
main          → Production — protégée, aucun push direct
feature/*     → Story en cours → PR → preview deployment
hotfix/*      → Correctif urgent → PR directe sur main (bypass process)
release/*     → (optionnel) Sprint release candidate
```

### C. Références techniques

| Ressource | URL |
|---|---|
| Vercel CLI docs | https://vercel.com/docs/cli |
| Supabase CLI docs | https://supabase.com/docs/reference/cli |
| GitHub Actions | https://docs.github.com/en/actions |
| Supabase GitHub Action | https://github.com/supabase/setup-cli |
| Next.js on Vercel | https://vercel.com/docs/frameworks/nextjs |

### D. Références projet

| Document | Localisation |
|---|---|
| Next.js Development Skill | `ai/roles/nextjs_development.md` |
| Supabase Database Skill | `ai/roles/supabase_database.md` |
| Architecture Overview | `docs/architecture/architecture_overview.md` |

---

*Ce document est la référence pour l'agent IA Infrastructure Developer de FoyerApp. Il est mis à jour à chaque évolution de la stack d'infrastructure, du pipeline CI/CD ou des procédures de déploiement.*
