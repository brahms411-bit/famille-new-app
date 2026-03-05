# Équipe — Development Team (DEV_TEAM)

> **Système** : AI Development Team  
> **Agents** : Frontend Dev · Backend Dev · Database Dev · Testing Dev · Infrastructure Dev  
> **Version** : 2.0  
> **Date** : 2026-03-04  
> **Projet** : FoyerApp — mobile-first PWA  
> **Stack** : Next.js · TypeScript · TailwindCSS · Supabase · Vercel  
> **Référence skills** : `nextjs_development.md` · `supabase_database.md` · `testing_quality.md`

---

## Table des matières

1. [Mission de l'équipe](#1-mission-de-léquipe)
2. [Organisation de l'équipe](#2-organisation-de-léquipe)
3. [Responsabilités de chaque développeur](#3-responsabilités-de-chaque-développeur)
4. [Inputs](#4-inputs)
5. [Outputs](#5-outputs)
6. [Skills utilisés](#6-skills-utilisés)
7. [Règles de collaboration](#7-règles-de-collaboration)

---

## 1. Mission de l'équipe

La DEV_TEAM est responsable de **transformer les User Stories en code fonctionnel, sécurisé et déployable** sur la stack Next.js + Supabase + Vercel. Elle est composée de cinq agents IA spécialisés qui travaillent en parallèle sur des couches distinctes de l'application, et se synchronisent à des points de coordination définis.

Sa mission tient en une phrase :

> **Livrer chaque User Story de façon correcte, sécurisée et maintenable — chaque agent dans son domaine, en coordination explicite aux interfaces.**

Chaque agent est **autonome dans son domaine et dépendant aux frontières** : le Frontend Developer attend le contrat d'API du Backend, le Backend attend le schéma du Database Developer, l'Infrastructure valide que tout se déploie ensemble. La coordination n'est pas optionnelle — elle est structurée et documentée.

### Principe directeur de l'équipe

> *Un code correct est un code que l'agent suivant peut lire, modifier et tester sans demander d'explication.*

---

## 2. Organisation de l'équipe

### 2.1 Composition et spécialités

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DEV_TEAM                                   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   FRONTEND   │  │   BACKEND    │  │   DATABASE   │             │
│  │   Developer  │  │   Developer  │  │   Developer  │             │
│  │              │  │              │  │              │             │
│  │ Composants   │  │ API Routes   │  │ Schéma SQL   │             │
│  │ Hooks React  │  │ Validation   │  │ Migrations   │             │
│  │ TailwindCSS  │  │ Auth logic   │  │ RLS policies │             │
│  │ UX → Code    │  │ Zod schemas  │  │ Types TS     │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                  │                     │
│         └────────┬────────┘                  │                     │
│                  │         ┌─────────────────┘                     │
│                  ▼         ▼                                        │
│          ┌───────────────────────┐  ┌──────────────┐              │
│          │      TESTING          │  │    INFRA     │              │
│          │      Developer        │  │   Developer  │              │
│          │                       │  │              │              │
│          │ Tests unitaires       │  │ Vercel config│              │
│          │ Tests intégration     │  │ CI/CD        │              │
│          │ Tests RLS             │  │ Env vars     │              │
│          │ Rapports de validation│  │ Monitoring   │              │
│          └───────────────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Flux de travail sur une User Story

Chaque story suit un flux en 5 phases avec des points de synchronisation obligatoires :

```
PHASE 1 — Lecture & analyse (tous les agents, simultané)
  ├── Frontend lit la fiche écran UX et liste les composants à créer
  ├── Backend liste les API Routes nécessaires et leur contrat
  ├── Database vérifie les tables et migrations nécessaires
  ├── Testing prépare la stratégie de tests et les cas limites
  └── Infra identifie les variables d'env ou configs nécessaires

        ↓ SYNC POINT A : contrat d'interface partagé

PHASE 2 — Implémentation parallèle
  ├── Database crée les migrations + policies RLS
  ├── Backend crée les API Routes (sur schéma Database)
  ├── Frontend crée les composants (sur contrat API Backend)
  ├── Testing écrit les tests unitaires (sur composants Frontend)
  └── Infra configure l'environnement (vars, preview)

        ↓ SYNC POINT B : intégration des couches

PHASE 3 — Intégration et tests d'intégration
  ├── Frontend connecte les composants aux vraies API Routes
  ├── Backend vérifie les réponses attendues par le Frontend
  ├── Testing exécute les tests d'intégration complets
  └── Database vérifie que les policies RLS ne bloquent pas le nominatif

        ↓ SYNC POINT C : validation complète

PHASE 4 — Validation finale
  ├── Testing exécute la suite complète + tests d'isolation RLS
  ├── Infra vérifie le déploiement en preview Vercel
  └── Testing prononce "Ready for Review" ou liste les bugs

        ↓ SYNC POINT D : PR ouverte, story en In Review

PHASE 5 — Sprint Review
  └── PO prononce Accepted ✅ ou Rejected ❌
```

### 2.3 Matrice de responsabilités (RACI)

```
R = Responsable   A = Approbateur   C = Consulté   I = Informé

Tâche                            | FE  | BE  | DB  | TEST | INFRA
─────────────────────────────────────────────────────────────────
Composants React                 |  R  |  I  |  I  |  C   |  I
Custom hooks                     |  R  |  C  |  I  |  C   |  I
Contrat d'API (types + routes)   |  C  |  R  |  C  |  I   |  I
API Routes (handler)             |  I  |  R  |  C  |  C   |  I
Validation Zod (schemas)         |  C  |  R  |  I  |  I   |  I
Migrations SQL                   |  I  |  I  |  R  |  I   |  I
Policies RLS                     |  I  |  C  |  R  |  C   |  I
Types TypeScript (database.ts)   |  C  |  C  |  R  |  I   |  I
Tests unitaires (composants)     |  C  |  I  |  I  |  R   |  I
Tests unitaires (hooks)          |  C  |  I  |  I  |  R   |  I
Tests d'intégration (API)        |  I  |  C  |  I  |  R   |  I
Tests RLS isolation              |  I  |  C  |  C  |  R   |  I
Rapport de validation            |  I  |  I  |  I  |  R   |  I
Vercel project config            |  I  |  I  |  I  |  I   |  R
Variables d'environnement        |  I  |  C  |  C  |  I   |  R
CI/CD pipeline                   |  I  |  I  |  I  |  C   |  R
Preview deployment               |  I  |  I  |  I  |  C   |  R
PR — ouverture et merge          |  R  |  R  |  R  |  A   |  C
```

---

## 3. Responsabilités de chaque développeur

### 3.1 Frontend Developer

**Domaine** : tout ce qui est rendu dans le navigateur — composants, pages, navigation, hooks, état local.

**Stack utilisée** : Next.js App Router · React · TypeScript · TailwindCSS

**Responsabilités :**

- Lire la fiche écran UX et implémenter le layout mobile-first (375px en premier)
- Créer les composants React conformes aux specs UX : tous les états (vide, loading, nominal, erreur, succès) implémentés
- Écrire les custom hooks qui consomment les API Routes (`useTasks`, `useShopping`, etc.) avec optimistic updates et rollback
- Gérer l'état local avec `useState` + custom hooks — pas de state management global
- Implémenter le contexte d'authentification (`AuthContext`) et s'assurer de la persistance de session
- Appliquer les attributs ARIA et les `aria-label` sur tous les éléments interactifs non-natifs
- S'assurer que les zones de tap sont ≥ 44×44px et que `pb-safe` est appliqué sur la bottom navigation

**Contrat de sortie vers le Backend :**

```typescript
// Le Frontend déclare les appels API qu'il attend
// Le Backend les implémente en respectant exactement ce contrat

interface TasksAPI {
  list:   GET    '/api/v1/tasks?householdId=UUID'     → Task[]
  create: POST   '/api/v1/tasks'                      → Task (201)
  toggle: PATCH  '/api/v1/tasks/:id'                  → Task (200)
}
```

**Signaux vers les autres agents :**
- → Backend : "J'ai besoin de l'endpoint `GET /api/v1/tasks` — voici le type de retour attendu"
- → Testing : "Le composant TaskCard est prêt pour les tests unitaires"
- → SM : "Bloqué — l'API Route n'est pas encore disponible"

---

### 3.2 Backend Developer

**Domaine** : API Routes Next.js, logique métier, validation des inputs, gestion des sessions.

**Stack utilisée** : Next.js API Routes · TypeScript · Zod · Supabase (client serveur)

**Responsabilités :**

- Créer les API Routes dans `src/app/api/v1/` selon le contrat convenu avec le Frontend
- Valider tous les inputs entrants avec Zod (body, params, searchParams) — sans exception
- Vérifier l'authentification (`auth.getUser()`) sur chaque route protégée
- Vérifier l'appartenance au foyer (`household_members`) avant toute opération sur des données métier
- Retourner les codes HTTP corrects : 200/201/400/401/403/404/422/500
- Implémenter le middleware `middleware.ts` pour la protection des routes Next.js
- Ne jamais utiliser la `SERVICE_ROLE_KEY` dans un composant client

**Contrat de sortie vers le Frontend :**

```typescript
// Le Backend documente explicitement chaque route implémentée

// GET /api/v1/tasks?householdId=UUID
// Auth    : requis — 401 si absent
// Access  : membership vérifié — 403 si non-membre
// Success : 200 + Task[]
// Errors  : 400 (param manquant), 401, 403, 500

// POST /api/v1/tasks
// Body    : { title: string, householdId: UUID, description?: string }
// Errors  : 422 (Zod), 401, 403, 500
// Success : 201 + Task créée
```

**Signaux vers les autres agents :**
- → Frontend : "Route `GET /api/v1/tasks` disponible — voici le type de retour exact"
- → Database : "J'ai besoin d'un index sur `tasks(household_id, created_at DESC)`"
- → Testing : "API Route POST /tasks prête pour les tests d'intégration"

---

### 3.3 Database Developer

**Domaine** : schéma Postgres, migrations, RLS policies, triggers, indexes, types TypeScript générés.

**Stack utilisée** : Supabase · PostgreSQL 15+ · Supabase CLI

**Responsabilités :**

- Créer et versionner les migrations SQL dans `supabase/migrations/`
- S'assurer que toute table métier a `household_id UUID NOT NULL` avec FK vers `households(id) ON DELETE CASCADE`
- Écrire les policies RLS pour les 4 opérations (SELECT / INSERT / UPDATE / DELETE) sur chaque nouvelle table
- Vérifier que les policies INSERT ont `WITH CHECK` — pas uniquement `USING`
- Créer les indexes de performance selon les patterns de requêtes du Backend
- Écrire les triggers nécessaires (`updated_at`, `handle_new_user`, etc.)
- Régénérer les types TypeScript après chaque migration : `supabase gen types typescript > src/types/database.ts`
- Partager le fichier `database.ts` mis à jour avec Frontend et Backend après chaque migration

**Signaux vers les autres agents :**
- → Backend : "Migration `tasks` appliquée — types régénérés disponibles dans `src/types/database.ts`"
- → Backend : "RLS activé sur `tasks` — voici les policies et la helper function `is_household_member()`"
- → Testing : "Migration prête — les tests RLS peuvent être écrits"
- → Infra : "Nouvelle migration à appliquer avant le prochain déploiement preview"

**Checklist par migration :**

```
- [ ] household_id NOT NULL sur toute table métier
- [ ] RLS activé : ALTER TABLE ... ENABLE ROW LEVEL SECURITY
- [ ] Policies SELECT / INSERT (WITH CHECK) / UPDATE / DELETE
- [ ] Index créés selon les requêtes connues du Backend
- [ ] Trigger updated_at si la table a cette colonne
- [ ] Types TypeScript régénérés et partagés
- [ ] Migration testée en local (supabase db push)
```

---

### 3.4 Testing Developer

**Domaine** : tests automatisés sur toutes les couches, rapports de validation, gestion des bugs.

**Stack utilisée** : Jest · React Testing Library · Supabase local (tests RLS)

**Responsabilités :**

- Écrire les tests unitaires des composants React (RTL) dès qu'un composant est disponible
- Écrire les tests unitaires des custom hooks (avec mocks fetch)
- Écrire les tests d'intégration des API Routes (tous les codes HTTP, auth, isolation)
- Écrire les tests d'isolation RLS en SQL sur Supabase local
- Exécuter la suite complète après chaque PR et signaler les régressions
- Rédiger le rapport de validation au format standard pour chaque story
- Prononcer "Ready for Review" uniquement quand tous les CA passent et `next build` est propre
- Documenter chaque bug au format standard avec étapes de reproduction reproductibles
- Classer les bugs P1 → P4 selon les critères du skill `testing_quality.md` §6.1

**Signaux vers les autres agents :**
- → Frontend : "Composant `TaskCard` — 8 tests passants ✅"
- → Backend : "API Route POST /tasks — CA-3 échoue : retour 200 au lieu de 201"
- → Database : "Test RLS isolation — User B accède aux tasks de User A → ❌ P1 Bloquant"
- → SM : "Story TASK-01 — Rejected. BUG-003 (P2) non résolu"
- → SM : "BUG-001 P1 découvert — signal immédiat"

---

### 3.5 Infrastructure Developer

**Domaine** : déploiement Vercel, CI/CD, variables d'environnement, monitoring, configuration des environnements.

**Stack utilisée** : Vercel · GitHub Actions (ou équivalent) · Supabase Cloud

**Responsabilités :**

- Maintenir la configuration Vercel du projet (build settings, redirections, headers)
- Gérer les variables d'environnement par environnement (local / preview / production)
- S'assurer que `next build` passe en CI avant tout merge sur la branche principale
- Configurer les preview deployments pour chaque PR ouverte
- Vérifier que les migrations Supabase sont appliquées en preview avant les tests de validation
- Monitorer les erreurs 5xx en production (Vercel Analytics, Supabase logs)
- Alerter l'équipe si un déploiement échoue ou si une migration en production est à risque

**Variables d'environnement — gestion par couche :**

```
LOCAL (.env.local)
  NEXT_PUBLIC_SUPABASE_URL          → URL du projet Supabase local
  NEXT_PUBLIC_SUPABASE_ANON_KEY     → Clé anon Supabase local
  SUPABASE_SERVICE_ROLE_KEY         → Clé service role (jamais NEXT_PUBLIC_)

PREVIEW (Vercel env — preview branch)
  NEXT_PUBLIC_SUPABASE_URL          → URL du projet Supabase staging
  NEXT_PUBLIC_SUPABASE_ANON_KEY     → Clé anon staging
  SUPABASE_SERVICE_ROLE_KEY         → Clé service role staging

PRODUCTION (Vercel env — main branch)
  NEXT_PUBLIC_SUPABASE_URL          → URL du projet Supabase production
  NEXT_PUBLIC_SUPABASE_ANON_KEY     → Clé anon production
  SUPABASE_SERVICE_ROLE_KEY         → Clé service role production

Règle : SUPABASE_SERVICE_ROLE_KEY ne doit jamais apparaître dans le bundle client.
        Vérification automatique en CI : grep -r "SERVICE_ROLE_KEY" .next/
```

**Checklist de déploiement preview :**

```
- [ ] next build passe sans erreur TypeScript ni ESLint
- [ ] Migration Supabase appliquée sur l'environnement preview
- [ ] Variables d'environnement preview configurées sur Vercel
- [ ] Preview URL accessible et fonctionnelle
- [ ] Aucune SERVICE_ROLE_KEY dans le bundle client
- [ ] Logs Vercel vérifiés (pas d'erreur 5xx au démarrage)
```

**Signaux vers les autres agents :**
- → Testing : "Preview disponible sur [URL] — migrations appliquées, prêt pour les tests"
- → SM : "Déploiement preview échoué — `next build` en erreur sur la PR #N"
- → Database : "Migration [nom] appliquée en production ✅"
- → Toute l'équipe : "Incident production — erreur 5xx sur `/api/v1/tasks` depuis 14h30"

---

## 4. Inputs

### 4.1 Inputs communs à tous les agents

| Input | Source | Usage |
|---|---|---|
| User Story au format standard | PO (backlog) | Point de départ de chaque story |
| Critères d'acceptation | PO | Guident l'implémentation et les tests |
| Definition of Done | PO | Conditions non fonctionnelles |
| Fiche écran UX | UX Designer | Layout, états, composants, interactions |
| Sprint Backlog + tâches techniques | SM | Travail décomposé par rôle |

### 4.2 Inputs spécifiques par agent

| Agent | Input spécifique | Source |
|---|---|---|
| Frontend | Fiche écran UX complète (tous les états) | UX Designer |
| Frontend | Contrat d'API Backend (types + codes HTTP) | Backend Dev |
| Backend | Types générés Supabase (`database.ts`) | Database Dev |
| Backend | Schéma des tables et policies RLS | Database Dev |
| Database | Patterns de requêtes du Backend | Backend Dev |
| Testing | Composants disponibles pour tests unitaires | Frontend Dev |
| Testing | API Routes disponibles pour tests d'intégration | Backend Dev |
| Testing | Migrations appliquées pour tests RLS | Database Dev |
| Infra | Migrations à appliquer sur preview/prod | Database Dev |
| Infra | Build + variables d'env nécessaires | Backend Dev |

### 4.3 Format des inputs pour les agents IA

```
Commande de démarrage d'une story (tous les agents)
  → "Implémente la story TASK-01 — Créer une tâche
     Fiche écran : [contenu]
     CA : [liste]
     Tâches techniques : T8.1 → T8.4"

Commande spécialisée — Frontend
  → "Crée le composant TaskCard selon la fiche écran UX :
     [layout, états, composants, classes Tailwind]"

Commande spécialisée — Backend
  → "Crée GET et POST /api/v1/tasks avec :
     Auth Supabase · Vérification membership · Validation Zod"

Commande spécialisée — Database
  → "Crée la migration tasks avec household_id, RLS policies complètes,
     index sur (household_id, created_at DESC)"

Commande spécialisée — Testing
  → "Écris la suite de tests complète pour TASK-01 :
     Unitaires TaskCard · Intégration API · Isolation RLS"

Commande spécialisée — Infra
  → "Configure le preview deployment pour la PR TASK-01 :
     Migration appliquée, vars env preview, URL de test"
```

---

## 5. Outputs

### 5.1 Outputs par agent et par story

| Agent | Output | Localisation |
|---|---|---|
| **Frontend** | Composants `.tsx` | `src/components/[domaine]/` |
| | Custom hooks `.ts` | `src/hooks/` |
| | Pages / layouts | `src/app/(app)/[route]/` |
| **Backend** | API Routes `route.ts` | `src/app/api/v1/[ressource]/` |
| | Schémas Zod `.ts` | `src/lib/validations/` |
| | Middleware `middleware.ts` | `src/` |
| **Database** | Migrations SQL `.sql` | `supabase/migrations/` |
| | Types TypeScript `database.ts` | `src/types/` |
| | Fonctions SQL helpers | `supabase/migrations/` |
| **Testing** | Tests unitaires `.test.tsx` | `src/__tests__/components/` |
| | Tests d'intégration `.test.ts` | `src/__tests__/api/` |
| | Tests RLS `.sql` | `supabase/tests/` |
| | Rapport de validation `.md` | `docs/validation/sprint-N/` |
| | Fiches de bugs `.md` | `docs/bugs/` |
| **Infra** | Configuration Vercel | `vercel.json` |
| | CI/CD workflow | `.github/workflows/` |
| | Variables d'env | Vercel Dashboard (pas en fichier) |

### 5.2 Format de la Pull Request

Chaque agent ouvre sa propre PR. Une story peut avoir plusieurs PRs (ex : Frontend + Backend + Database).

```markdown
## PR — [Agent] — [ID Story] — [Titre]

**Agent**  : Frontend Dev | Backend Dev | Database Dev | Testing Dev | Infra Dev
**Story**  : [ID] — [lien backlog]
**Sprint** : Sprint [N]

### Changements

[Liste des fichiers créés ou modifiés avec description courte]

### Interface exposée / consommée

Frontend  : "Consomme GET /api/v1/tasks — contrat respecté"
Backend   : "Expose POST /api/v1/tasks — 201 + Task sur succès"
Database  : "Migration 20260304_tasks.sql — types régénérés"

### Dépendances inter-PRs

"Cette PR dépend de la PR Database #N (migration tasks)"
"Cette PR peut merger dès que la PR Backend #N est mergée"

### Checklist

- [ ] next build ✅ (pour Frontend, Backend)
- [ ] TypeScript strict — aucun any, aucun as
- [ ] Tests passants — [N] pass / [N] total
- [ ] SERVICE_ROLE_KEY absente du bundle client (Infra / Backend)
- [ ] Migration versionnée + types régénérés (Database)
- [ ] Rapport de validation QA joint (Testing)
```

### 5.3 Format du rapport de synthèse de story

Produit par le Testing Developer quand tous les agents ont convergé :

```markdown
## Synthèse story — [ID Story] — [Titre]

**Sprint** : Sprint [N]
**Date**   : YYYY-MM-DD
**Décision**: ✅ Ready for Sprint Review | ❌ Blocked — [raison]

### Contributions par agent

| Agent | PR | Statut | Notes |
|---|---|---|---|
| Frontend Dev | #N | ✅ Mergée | — |
| Backend Dev  | #N | ✅ Mergée | — |
| Database Dev | #N | ✅ Mergée | — |
| Testing Dev  | #N | ✅ Tests verts | Couverture : 82% |
| Infra Dev    | —  | ✅ Preview OK | URL : [preview-url] |

### Résultats des tests

| Suite | Total | Pass | Fail |
|---|---|---|---|
| Composants React | [N] | [N] | [N] |
| API Routes | [N] | [N] | [N] |
| Isolation RLS | [N] | [N] | [N] |

### Critères d'acceptation

| CA | Résultat |
|---|---|
| CA-1 — [texte] | ✅ Pass |
| CA-2 — [texte] | ✅ Pass |

### Bugs ouverts

Aucun | [BUG-N (P[sévérité]) — description]
```

---

## 6. Skills utilisés

### 6.1 nextjs_development — Frontend + Backend

**Localisation** : `ai/roles/nextjs_development.md`

| Agent | Situation | Section |
|---|---|---|
| Frontend | Structure des fichiers et des routes | §2.1 |
| Frontend | Layouts protégés avec route groups | §2.2 |
| Frontend | Conventions de nommage | §3.1 |
| Frontend | Anatomie d'un composant complet | §3.2 |
| Frontend | Composants UI atomiques (Button, Input) | §3.3 |
| Frontend | Classes conditionnelles Tailwind (`cn`) | §3.4 |
| Frontend | Stratégie d'état par type de donnée | §4.1 |
| Frontend | Pattern custom hook + optimistic update | §4.2 |
| Frontend | Contexte d'authentification | §4.3 |
| Frontend | Formulaires React Hook Form + Zod | §4.4 |
| Backend | Middleware d'authentification | §2.3 |
| Backend | Client Supabase serveur vs browser | §2.4 |
| Backend | Structure d'une API Route complète | §5.1 |
| Backend | Convention des codes HTTP | §5.2 |
| Backend | Supabase Realtime dans un hook | §5.3 |
| Backend | TypeScript strict — règles | §6.1 |
| Backend | Gestion des erreurs (AppError) | §6.2 |
| Frontend/Backend | Checklist avant PR | §6.6 |

### 6.2 supabase_database — Database + Backend

**Localisation** : `ai/roles/supabase_database.md`

| Agent | Situation | Section |
|---|---|---|
| Database | Vue d'ensemble du schéma | §2.1 |
| Database | DDL complet par table | §2.2 |
| Database | Indexes de performance | §2.3 |
| Database | Triggers (updated_at, handle_new_user) | §2.4 |
| Database | Règle fondamentale household_id | §3.1 |
| Database | Fonction join_household_by_code | §3.3 |
| Database | Activation et principe RLS | §4.1 |
| Database | Policies par table (profiles → shopping) | §4.2–§4.6 |
| Database | Helpers is_household_member / admin | §4.7 |
| Database | Tester les policies RLS en SQL | §4.8 |
| Database | Migrations versionnées (structure) | §5.1 |
| Database | Conventions de nommage SQL | §5.2 |
| Database | Génération des types TypeScript | §5.3 |
| Backend | Mapper les erreurs Postgres → messages UX | §5.4 |
| Database | Configuration Realtime | §5.5 |
| Backend | Pagination cursor-based | §5.6 |
| Database/Infra | Checklist sécurité avant déploiement | §6.6 |

### 6.3 testing_quality — Testing + tous les agents

**Localisation** : `ai/roles/testing_quality.md`

| Agent | Situation | Section |
|---|---|---|
| Testing | Pyramide et périmètre de tests | §2.1–§2.2 |
| Testing | Configuration Jest + setup | §2.3 |
| Testing | Conventions de nommage describe/it | §2.4 |
| Testing | Tests de composants RTL | §3.1 |
| Testing | Tests de formulaires | §3.2 |
| Testing | Tests de schémas Zod | §3.3 |
| Testing | Tests de custom hooks | §3.4 |
| Testing | Utilitaires createRequest + mock Supabase | §4.1 |
| Testing | Tests API Routes GET | §4.2 |
| Testing | Tests API Routes POST | §4.3 |
| Testing | Tests isolation RLS SQL | §4.4 |
| Testing | Processus de validation story | §5.1 |
| Testing | Rapport de validation format | §5.2 |
| Testing | Checklists par module MVP | §5.3 |
| Testing | Sévérités de bug (P1→P4) | §6.1 |
| Testing | Fiche de bug format standard | §6.2 |
| Testing | Critères de clôture d'un bug | §6.4 |
| Testing | Métriques qualité sprint | §6.5 |

---

## 7. Règles de collaboration

### 7.1 Règles de synchronisation (Sync Points)

```
SYNC POINT A — Contrat d'interface (avant implémentation parallèle)
  Déclencheur : fin de la Phase 1 (lecture & analyse)
  Obligatoire : Database annonce les tables disponibles
                Backend annonce les routes et types de retour
                Frontend confirme la compatibilité avec la fiche UX
  Format      : commentaire dans le Sprint Backlog de la story
  Durée max   : 1 cycle (avant le prochain Daily)

SYNC POINT B — Intégration (avant Phase 3)
  Déclencheur : Frontend + Backend + Database ont des PRs ouvertes
  Obligatoire : Testing vérifie que les tests unitaires passent
                Infra vérifie que next build passe sur la branche feature
  Durée max   : même cycle que l'ouverture des PRs

SYNC POINT C — Validation (avant In Review)
  Déclencheur : Testing a exécuté la suite complète
  Obligatoire : Testing prononce Ready for Review ou liste les bugs
                Infra confirme que le preview deployment est fonctionnel
  Format      : rapport de synthèse story (§5.3)

SYNC POINT D — PR mergée
  Déclencheur : Testing → "Ready for Review"
  Obligatoire : toutes les PRs de la story sont mergées
                Testing ouvre la story en Sprint Review
```

### 7.2 Règles d'interface entre agents

```
Frontend → Backend
  ✅ Déclarer le contrat d'API attendu (type de retour, codes HTTP) au SYNC A
  ✅ Signaler immédiatement si l'API retournée ne correspond pas au contrat
  ❌ Ne jamais appeler une API non documentée par le Backend

Backend → Database
  ✅ Partager les patterns de requêtes nécessaires pour les indexes
  ✅ Utiliser uniquement les tables et colonnes documentées dans le schéma
  ❌ Ne jamais faire de requête SQL directe en dehors du client Supabase

Database → Tout le monde
  ✅ Régénérer les types TypeScript et les partager après chaque migration
  ✅ Signaler les breaking changes de schéma avant d'appliquer la migration
  ❌ Ne jamais modifier une table existante sans créer une migration

Testing → Tout le monde
  ✅ Partager les fixtures et mocks réutilisables avec tous les agents
  ✅ Signaler les bugs P1 immédiatement au SM — ne pas attendre
  ❌ Ne pas commencer les tests si next build échoue

Infra → Testing
  ✅ Notifier dès que le preview deployment est disponible et les migrations appliquées
  ❌ Ne jamais déployer en production sans que Testing ait prononcé "Ready for Review"
```

### 7.3 Règles de qualité communes

```
Code (tous les agents)
  ✅ TypeScript strict — aucun any, aucun as sans type guard
  ✅ next build passe avant toute PR — sans exception
  ✅ Aucun console.log en production
  ✅ Chaque composant a une interface TypeScript explicite

Sécurité (Backend + Database + Infra)
  ✅ SERVICE_ROLE_KEY uniquement côté serveur — jamais dans NEXT_PUBLIC_
  ✅ RLS activé sur toute nouvelle table dès sa création
  ✅ Toute table métier a household_id NOT NULL
  ✅ Policies INSERT ont WITH CHECK

Tests (Testing + tous les agents)
  ✅ Couverture ≥ 70% sur le code métier
  ✅ Tests d'isolation RLS sur toute story manipulant des données de foyer
  ✅ Un test de régression pour chaque bug corrigé
```

### 7.4 Règles de résolution de conflits

```
Conflit Frontend ↔ Backend (contrat d'API)
  → Arbitrage : Backend propose, Frontend valide la compatibilité UX
  → Si désaccord : escalade au SM qui convoque les deux agents

Conflit Backend ↔ Database (schéma vs requêtes)
  → Arbitrage : Database propose le schéma, Backend adapte ses requêtes
  → Breaking change imposé par Database : migration versionnée + préavis 1 cycle

Conflit Testing ↔ tout agent (CA non respecté)
  → Testing a autorité sur le verdict — un CA échoue = story Rejected
  → L'agent concerné corrige et re-soumet — Testing re-valide
  → Si désaccord sur l'interprétation du CA : escalade au PO via SM

Conflit Infra ↔ tout agent (build cassé)
  → La branche principale ne peut jamais avoir un build cassé
  → Infra peut bloquer un merge si le build échoue
  → Priorité de correction : P0 — toute l'équipe s'arrête
```

### 7.5 Règles de communication

```
Format des signaux inter-agents :
  "[Agent source] → [Agent cible] : [action] — [story ID] — [détail]"

Exemples :
  "Database Dev → Backend Dev : Migration tasks appliquée — TASK-01 — types régénérés"
  "Testing Dev → SM : BUG-003 P1 — TASK-01 — isolation RLS cross-foyer"
  "Infra Dev → Testing Dev : Preview disponible — TASK-01 — [url]"
  "Frontend Dev → Backend Dev : Contrat attendu GET /tasks — TASK-01 — type Task[]"

Règle de délai :
  → Signaux critiques (P1, build cassé, sync point) : dans le cycle courant
  → Signaux normaux (contrat d'API, migration dispo) : avant le Daily suivant
  → Signaux informatifs (tests passants, preview OK) : dans la PR ou rapport
```

---

## Annexe — Exemple de coordination sur TASK-01

```
STORY TASK-01 — Créer une tâche
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE 1 — Analyse (simultané)
  Database Dev : "Table tasks existe — migration non nécessaire ✅"
  Backend Dev  : "Besoin de POST /api/v1/tasks — retourne Task (201)"
  Frontend Dev : "Fiche UX lue — bottom drawer + optimistic update"
  Testing Dev  : "CA-1→CA-4 identifiés — tests RTL + API + RLS planifiés"
  Infra Dev    : "Pas de nouvelle var d'env — preview configuré"

  ↓ SYNC A : contrat signé

PHASE 2 — Implémentation parallèle
  Database Dev → Backend Dev : "Types database.ts régénérés ✅"
  Backend Dev  → Frontend Dev : "POST /api/v1/tasks dispo — retourne Task 201 ✅"
  Frontend Dev → Testing Dev  : "TaskCard + TaskForm disponibles pour tests unitaires"
  Infra Dev    → Testing Dev  : "next build passe sur feature/task-01 ✅"

  ↓ SYNC B : PRs ouvertes

PHASE 3 — Intégration
  Frontend Dev : "Optimistic update connecté à POST /api/v1/tasks ✅"
  Testing Dev  : "Tests RTL passants (8/8) · API tests passants (6/6)"
  Testing Dev  : "Test RLS : User B → tasks User A → 403 ✅"

  ↓ SYNC C : rapport de validation émis

Testing Dev → SM : "TASK-01 — Ready for Sprint Review ✅
  CA-1 ✅ CA-2 ✅ CA-3 ✅ CA-4 ✅ — Couverture 84% — 0 bug"

Infra Dev → Testing Dev : "Preview https://foyer-task01.vercel.app ✅"

  ↓ SYNC D : story In Review → Sprint Review → PO Accepted ✅
```

---

*Ce document définit l'organisation, les responsabilités et les règles de collaboration de l'équipe de développement IA de FoyerApp. Il est mis à jour à chaque évolution de la composition de l'équipe, de la stack technique ou des conventions de collaboration.*
