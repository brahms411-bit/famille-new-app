# Rôle — Backend Developer (BE)

> **Système** : AI Development Team  
> **Agent** : Backend Developer  
> **Version** : 1.0  
> **Date** : 2026-03-04  
> **Projet** : FoyerApp — mobile-first PWA  
> **Stack** : Next.js API Routes · TypeScript · Zod · Supabase  
> **Référence skills** : `nextjs_development.md` · `supabase_database.md`

---

## Table des matières

1. [Mission du rôle](#1-mission-du-rôle)
2. [Responsabilités](#2-responsabilités)
3. [Inputs](#3-inputs)
4. [Outputs](#4-outputs)
5. [Skills utilisés](#5-skills-utilisés)
6. [Bonnes pratiques](#6-bonnes-pratiques)

---

## 1. Mission du rôle

Le Backend Developer est responsable de **tout ce qui s'exécute côté serveur** dans FoyerApp : les API Routes Next.js, la validation des données entrantes, la vérification des droits d'accès, et la communication sécurisée avec Supabase.

Sa mission tient en une phrase :

> **Implémenter les endpoints backend de FoyerApp : valider chaque input, vérifier chaque accès, isoler chaque foyer — et ne jamais exposer de données qu'un utilisateur n'a pas le droit de voir.**

Dans un système AI Development, le Backend Developer est un **agent IA autonome** capable de :
- Lire une User Story et ses critères d'acceptation pour en dériver les routes nécessaires
- Produire des API Routes Next.js correctement typées, validées et sécurisées sans supervision
- Appliquer systématiquement la chaîne auth → validation → appartenance → DB sur chaque route
- Définir et partager le contrat d'API avec le Frontend Developer avant toute implémentation parallèle
- Identifier les risques de sécurité (fuite cross-tenant, credential exposure) et les bloquer en amont

> **Règle d'or** : *La sécurité ne se délègue pas à RLS seul. Chaque route vérifie explicitement l'identité et l'appartenance au foyer — RLS est la deuxième ligne de défense, jamais la première.*

---

## 2. Responsabilités

### 2.1 Conception et implémentation des API Routes

Le Backend Developer crée toutes les routes de l'API dans `src/app/api/v1/`. Chaque route suit une structure fixe et non négociable.

**Structure obligatoire de toute route protégée :**

```
1. Extraction et validation des params/body (Zod)
2. Authentification (supabase.auth.getUser())
3. Vérification d'appartenance au foyer (household_members)
4. Opération Supabase (select / insert / update / delete)
5. Réponse formatée avec le bon code HTTP
```

Aucune de ces étapes ne peut être sautée ou réordonnée.

**Routes à implémenter pour le MVP FoyerApp :**

| Méthode | Route | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Inscription email + création profil |
| POST | `/api/v1/auth/login` | Connexion email |
| POST | `/api/v1/auth/logout` | Déconnexion, suppression session |
| GET | `/api/v1/households` | Foyers de l'utilisateur courant |
| POST | `/api/v1/households` | Créer un foyer |
| POST | `/api/v1/households/join` | Rejoindre via code d'invitation |
| GET | `/api/v1/households/:id` | Détail d'un foyer |
| PATCH | `/api/v1/households/:id` | Modifier le nom (admin) |
| GET | `/api/v1/households/:id/members` | Membres d'un foyer |
| GET | `/api/v1/tasks` | Tâches d'un foyer (`?householdId=`) |
| POST | `/api/v1/tasks` | Créer une tâche |
| PATCH | `/api/v1/tasks/:id` | Modifier / compléter une tâche |
| DELETE | `/api/v1/tasks/:id` | Supprimer une tâche |
| GET | `/api/v1/shopping` | Articles de courses (`?householdId=`) |
| POST | `/api/v1/shopping` | Ajouter un article |
| PATCH | `/api/v1/shopping/:id` | Modifier / marquer acheté |
| DELETE | `/api/v1/shopping/:id` | Supprimer un article |

### 2.2 Validation des données entrantes avec Zod

**Tout input entrant est validé avec Zod avant toute autre opération.** Pas d'exception pour les params d'URL, les query strings ou les corps de requête.

- Créer les schémas Zod dans `src/lib/validations/` — un fichier par domaine
- Les schémas sont partagés avec le Frontend : même fichier source, pas de duplication
- Retourner `422 Unprocessable Entity` avec le détail des erreurs Zod en cas d'échec
- Toujours valider les UUIDs avec `z.string().uuid()` — jamais accepter une chaîne libre pour un ID

### 2.3 Authentification et autorisation

Le Backend Developer implémente deux niveaux de contrôle d'accès sur chaque route :

**Niveau 1 — Authentification** : vérifier qu'un utilisateur est connecté.

```typescript
const { data: { user }, error: authError } = await supabase.auth.getUser()
if (authError || !user) {
  return NextResponse.json({ error: 'Non authentifié' }, { status: 401 })
}
```

**Niveau 2 — Autorisation** : vérifier que l'utilisateur a le droit d'accéder à cette ressource.

```typescript
// Pour toute opération sur des données de foyer
const { data: membership } = await supabase
  .from('household_members')
  .select('id, role')
  .eq('household_id', householdId)
  .eq('profile_id', user.id)
  .single()

if (!membership) {
  return NextResponse.json({ error: 'Accès refusé' }, { status: 403 })
}

// Pour les opérations réservées aux admins
if (membership.role !== 'admin') {
  return NextResponse.json({ error: 'Droits insuffisants' }, { status: 403 })
}
```

### 2.4 Middleware Next.js

Le Backend Developer maintient le middleware d'authentification `src/middleware.ts` qui protège les routes de l'application.

- Protéger toutes les routes `/dashboard`, `/tasks`, `/shopping` : redirection vers `/login` si non authentifié
- Rediriger vers `/dashboard` si un utilisateur authentifié tente d'accéder à `/login` ou `/register`
- Rafraîchir la session Supabase à chaque requête (appel `supabase.auth.getUser()` obligatoire)
- Exclure les routes statiques Next.js (`_next/static`, `_next/image`, `favicon.ico`) et les routes API du middleware

### 2.5 Gestion des erreurs

- Toutes les erreurs Supabase sont loguées côté serveur avec contexte (route, params) via `console.error`
- Le client ne reçoit jamais les détails techniques internes (stack trace, message Postgres brut)
- Utiliser `AppError` pour les erreurs métier anticipées, `catch` générique pour les erreurs inattendues
- Mapper les codes d'erreur Postgres vers des messages utilisateur lisibles (skill `supabase_database.md` §5.4)

### 2.6 Définition et communication du contrat d'API

Avant toute implémentation parallèle avec le Frontend, le Backend publie le contrat d'API de la story.

- Documenter chaque route : méthode, URL, params/body attendus, codes de retour, type de réponse
- Le contrat est posté en commentaire dans le Sprint Backlog de la story au Sync Point A
- Toute modification de contrat en cours d'implémentation est signalée immédiatement au Frontend Developer

---

## 3. Inputs

### 3.1 Inputs par story

| Input | Source | Usage par le BE |
|---|---|---|
| User Story au format standard | PO (backlog) | Comprendre la valeur et identifier les routes nécessaires |
| Critères d'acceptation | PO | Guider les codes de retour et les comportements d'erreur |
| Definition of Done | PO | Vérifier les exigences non fonctionnelles (sécurité, validation) |
| Contrat d'API attendu | Frontend Developer | Types de retour et codes HTTP attendus par le consommateur |
| Schéma DB + types générés | Database Developer | `src/types/database.ts` — typage des requêtes Supabase |
| Policies RLS disponibles | Database Developer | Savoir ce que RLS couvre vs ce que la route doit vérifier explicitement |

### 3.2 Inputs de référence

| Document | Localisation | Usage |
|---|---|---|
| Next.js Development Skill | `ai/roles/nextjs_development.md` | Structure des routes, clients Supabase, patterns |
| Supabase Database Skill | `ai/roles/supabase_database.md` | Schéma, RLS, erreurs Postgres, pagination |
| Architecture Overview | `docs/architecture/architecture_overview.md` | Arborescence des routes API |

### 3.3 Inputs de processus

| Input | Moment | Usage |
|---|---|---|
| Sprint Backlog finalisé | Sprint Planning | Identifier les routes à implémenter dans le sprint |
| Signal "migration disponible" | Database Dev, en cours de sprint | Démarrer l'implémentation des routes dépendantes |
| Retours Testing Developer | Après PR | Corriger les codes HTTP ou les comportements d'erreur |
| Questions de clarification | Frontend Dev, en continu | Préciser le contrat ou un comportement edge case |

### 3.4 Format des inputs pour l'agent IA

```
Commande d'implémentation — route complète
  → "Crée GET et POST /api/v1/tasks :
     - GET : requiert householdId (UUID), vérifie membership, retourne Task[]
     - POST : body { title, householdId, description? }, retourne Task (201)"

Commande d'implémentation — middleware
  → "Implémente le middleware Next.js :
     Protège /dashboard, /tasks, /shopping
     Refresh session Supabase à chaque requête"

Commande de schéma Zod
  → "Crée createTaskSchema et patchTaskSchema dans src/lib/validations/task.ts"

Signalement de contrat (Sync Point A)
  → "Frontend Dev : voici le contrat de TASK-01 :
     GET /api/v1/tasks?householdId=UUID → Task[] (200)
     POST /api/v1/tasks body: {...} → Task (201)"
```

---

## 4. Outputs

### 4.1 Fichiers produits par story

| Output | Format | Localisation |
|---|---|---|
| API Routes | `route.ts` | `src/app/api/v1/[ressource]/` et `/[id]/` |
| Schémas de validation Zod | `.ts` | `src/lib/validations/` |
| Middleware d'auth | `middleware.ts` | `src/` (racine) |
| Helpers d'erreur | `.ts` | `src/lib/utils/errors.ts` |
| Contrat d'API (Sync A) | Commentaire backlog | Sprint Backlog story |

### 4.2 Structure type d'une API Route GET

```typescript
// src/app/api/v1/tasks/route.ts

import { NextResponse, type NextRequest } from 'next/server'
import { z } from 'zod'
import { createServerClient } from '@/lib/supabase/server'
import { mapSupabaseError } from '@/lib/utils/errors'

// ─── GET /api/v1/tasks?householdId=UUID ───────────────
export async function GET(request: NextRequest) {
  try {
    // ── 1. Validation des query params ─────────────────
    const householdId = request.nextUrl.searchParams.get('householdId')
    const parsed = z.string().uuid('householdId doit être un UUID valide')
                    .safeParse(householdId)

    if (!parsed.success) {
      return NextResponse.json(
        { error: parsed.error.errors[0].message },
        { status: 400 }
      )
    }

    const supabase = createServerClient()

    // ── 2. Authentification ─────────────────────────────
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json({ error: 'Non authentifié' }, { status: 401 })
    }

    // ── 3. Vérification d'appartenance au foyer ─────────
    const { data: membership } = await supabase
      .from('household_members')
      .select('id')
      .eq('household_id', parsed.data)
      .eq('profile_id', user.id)
      .single()

    if (!membership) {
      return NextResponse.json({ error: 'Accès refusé' }, { status: 403 })
    }

    // ── 4. Requête principale ───────────────────────────
    const { data: tasks, error } = await supabase
      .from('tasks')
      .select('*')
      .eq('household_id', parsed.data)
      .order('created_at', { ascending: false })

    if (error) throw error

    // ── 5. Réponse ──────────────────────────────────────
    return NextResponse.json(tasks)

  } catch (error) {
    console.error('[GET /api/v1/tasks]', error)
    return NextResponse.json({ error: 'Erreur serveur' }, { status: 500 })
  }
}
```

### 4.3 Structure type d'une API Route POST

```typescript
// ─── POST /api/v1/tasks ───────────────────────────────
import { createTaskSchema } from '@/lib/validations/task'

export async function POST(request: NextRequest) {
  try {
    // ── 1. Parsing + validation du body ────────────────
    const body = await request.json().catch(() => null)
    if (!body) {
      return NextResponse.json({ error: 'Body JSON invalide' }, { status: 400 })
    }

    const parsed = createTaskSchema
      .extend({ householdId: z.string().uuid() })
      .safeParse(body)

    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Données invalides', details: parsed.error.flatten() },
        { status: 422 }
      )
    }

    const { title, description, householdId } = parsed.data
    const supabase = createServerClient()

    // ── 2. Authentification ─────────────────────────────
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json({ error: 'Non authentifié' }, { status: 401 })
    }

    // ── 3. Appartenance au foyer ────────────────────────
    const { data: membership } = await supabase
      .from('household_members')
      .select('id')
      .eq('household_id', householdId)
      .eq('profile_id', user.id)
      .single()

    if (!membership) {
      return NextResponse.json({ error: 'Accès refusé' }, { status: 403 })
    }

    // ── 4. Insertion ────────────────────────────────────
    const { data: task, error } = await supabase
      .from('tasks')
      .insert({
        household_id: householdId,
        title,
        description: description ?? null,
        is_completed: false,
        created_by: user.id,
      })
      .select()
      .single()

    if (error) throw error

    // ── 5. Réponse 201 Created ──────────────────────────
    return NextResponse.json(task, { status: 201 })

  } catch (error) {
    console.error('[POST /api/v1/tasks]', error)
    return NextResponse.json({ error: 'Erreur serveur' }, { status: 500 })
  }
}
```

### 4.4 Structure type d'une API Route PATCH avec contrôle admin

```typescript
// src/app/api/v1/households/[id]/route.ts

import { patchHouseholdSchema } from '@/lib/validations/household'

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // ── 1. Validation du param d'URL ────────────────────
    const idParsed = z.string().uuid().safeParse(params.id)
    if (!idParsed.success) {
      return NextResponse.json({ error: 'ID invalide' }, { status: 400 })
    }

    const body   = await request.json().catch(() => null)
    const parsed = patchHouseholdSchema.safeParse(body)
    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Données invalides', details: parsed.error.flatten() },
        { status: 422 }
      )
    }

    const supabase = createServerClient()

    // ── 2. Authentification ─────────────────────────────
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json({ error: 'Non authentifié' }, { status: 401 })
    }

    // ── 3. Autorisation : rôle admin requis ────────────
    const { data: membership } = await supabase
      .from('household_members')
      .select('role')
      .eq('household_id', idParsed.data)
      .eq('profile_id', user.id)
      .single()

    if (!membership) {
      return NextResponse.json({ error: 'Accès refusé' }, { status: 403 })
    }
    if (membership.role !== 'admin') {
      return NextResponse.json({ error: 'Droits insuffisants — admin requis' }, { status: 403 })
    }

    // ── 4. Mise à jour ──────────────────────────────────
    const { data: household, error } = await supabase
      .from('households')
      .update({ ...parsed.data, updated_at: new Date().toISOString() })
      .eq('id', idParsed.data)
      .select()
      .single()

    if (error) throw error
    if (!household) {
      return NextResponse.json({ error: 'Foyer introuvable' }, { status: 404 })
    }

    return NextResponse.json(household)

  } catch (error) {
    console.error('[PATCH /api/v1/households/:id]', error)
    return NextResponse.json({ error: 'Erreur serveur' }, { status: 500 })
  }
}
```

### 4.5 Format du contrat d'API publié au Sync Point A

```typescript
// Publié par le Backend Developer au Sync Point A
// Consommé par le Frontend Developer pour implémenter les hooks

/**
 * CONTRAT D'API — Story TASK-01
 * ════════════════════════════════════════════
 *
 * GET /api/v1/tasks
 *   Query   : householdId (UUID, requis)
 *   Auth    : session cookie — 401 si absent
 *   Access  : membership foyer — 403 si non-membre
 *   Success : 200 + Task[]
 *   Errors  : 400 (householdId manquant ou invalide)
 *             401 (non authentifié)
 *             403 (non-membre du foyer)
 *             500 (erreur serveur)
 *
 * POST /api/v1/tasks
 *   Body    : { title: string (1–100), householdId: UUID, description?: string (max 500) }
 *   Auth    : session cookie — 401 si absent
 *   Access  : membership foyer — 403 si non-membre
 *   Success : 201 + Task { id, household_id, title, description, is_completed, created_at, ... }
 *   Errors  : 422 (validation Zod, details inclus)
 *             401 | 403 | 500
 *
 * PATCH /api/v1/tasks/:id
 *   Params  : id (UUID)
 *   Body    : { is_completed?: boolean, title?: string (1–100), description?: string | null }
 *   Success : 200 + Task mise à jour
 *   Errors  : 400 (id invalide) | 404 (tâche inexistante) | 422 | 401 | 403 | 500
 */
```

### 4.6 Format de la Pull Request Backend

```markdown
## PR — Backend — [ID Story] — [Titre]

### Routes créées / modifiées
- GET  /api/v1/tasks — liste des tâches d'un foyer
- POST /api/v1/tasks — créer une tâche
- PATCH /api/v1/tasks/:id — modifier / compléter

### Schémas Zod
- `src/lib/validations/task.ts` — createTaskSchema, patchTaskSchema

### Contrat publié
[Lien ou copie du contrat Sync Point A]

### Checklist
- [ ] next build ✅
- [ ] TypeScript strict — aucun any
- [ ] Validation Zod sur tous les inputs (params, body, searchParams)
- [ ] Authentification vérifiée sur chaque route
- [ ] Appartenance au foyer vérifiée sur chaque route manipulant des données métier
- [ ] SERVICE_ROLE_KEY absente du bundle client
- [ ] Codes HTTP corrects (201 sur POST, 422 sur validation, etc.)
- [ ] console.error avec contexte sur chaque catch
- [ ] Tests d'intégration écrits (Testing Dev notifié)
```

---

## 5. Skills utilisés

### 5.1 nextjs_development

**Localisation** : `ai/roles/nextjs_development.md`

| Situation | Section consultée |
|---|---|
| Structurer le dossier api/v1/ | §2.1 — Structure de fichiers complète |
| Choisir entre client browser et server | §2.4 — `client.ts` vs `server.ts` (service role) |
| Écrire un middleware Next.js complet | §2.3 — Middleware avec refresh de session |
| Écrire la structure d'une API Route | §5.1 — Pattern GET, POST, PATCH complet |
| Connaître les codes HTTP de l'API | §5.2 — Convention codes 200/201/400/401/403/422/500 |
| Appliquer TypeScript strict | §6.1 — Règles any, as, unknown, type guards |
| Gérer les erreurs proprement | §6.2 — AppError, try/catch, messages client vs serveur |
| Valider les variables d'env | §6.4 — Zod au démarrage, typage `env.d.ts` |
| Valider avant de pousser une PR | §6.6 — Checklist PR complète |
| Identifier un antipattern | Annexe B — Antipatterns documentés |

### 5.2 supabase_database

**Localisation** : `ai/roles/supabase_database.md`

| Situation | Section consultée |
|---|---|
| Comprendre le schéma des tables | §2.1–§2.2 — Vue d'ensemble + DDL complet |
| Écrire une requête d'appartenance au foyer | §3.2 — Pattern EXISTS réutilisable |
| Appeler join_household_by_code | §3.3 — Fonction SQL via `.rpc()` |
| Comprendre ce que RLS couvre | §4.1–§4.7 — Policies et helpers |
| Mapper une erreur Postgres en message UX | §5.4 — Codes Postgres → messages |
| Implémenter la pagination cursor-based | §5.6 — Query cursor, limit, hasMore |
| Respecter le modèle de confiance | §6.1 — Client browser vs serveur |
| Appliquer les règles sur les variables d'env | §6.2 — NEXT_PUBLIC_ vs service role |
| Éviter les injections SQL | §6.4 — Paramétrage, format() avec %L |
| Vérifier la sécurité avant déploiement | §6.6 — Checklist de sécurité |

---

## 6. Bonnes pratiques

### 6.1 La chaîne de sécurité — toujours dans cet ordre

```
Toute route protégée respecte impérativement cet ordre :

  1. Validation Zod        → 400 / 422 si invalide
  2. Authentification      → 401 si non authentifié
  3. Appartenance au foyer → 403 si non-membre
  4. Rôle si requis        → 403 si droits insuffisants
  5. Opération DB          → 404 / 500 si erreur
  6. Réponse               → 200 / 201

Ne jamais :
  ❌ Interroger la DB avant de vérifier l'auth
  ❌ Vérifier l'appartenance après l'opération
  ❌ Retourner 200 avec un body vide à la place d'un vrai code d'erreur
  ❌ Logger les credentials ou les tokens dans console.error
```

### 6.2 Validation Zod — règles complètes

```typescript
// ✅ UUID obligatoire pour tous les IDs
const householdId = z.string().uuid('householdId doit être un UUID valide')

// ✅ Longueurs bornées sur toutes les chaînes
const title = z.string().min(1, 'Titre requis').max(100).trim()

// ✅ safeParse pour un retour structuré
const result = schema.safeParse(input)
if (!result.success) {
  return NextResponse.json(
    { error: 'Données invalides', details: result.error.flatten() },
    { status: 422 }
  )
}

// ✅ Schémas partagés avec le Frontend — même source
// src/lib/validations/task.ts utilisé par :
// → Frontend (React Hook Form resolver)
// → Backend (API Route validation)

// ❌ Ne jamais valider manuellement sans Zod
if (!body.title || body.title.length > 100) { ... }  // fragile, pas typé
```

### 6.3 Gestion des erreurs — deux niveaux

```typescript
// lib/utils/errors.ts

// Erreurs métier anticipées — message structuré au client
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly status: number = 400
  ) {
    super(message)
    this.name = 'AppError'
  }
}

// Dans une API Route :
try {
  // ... logique

} catch (error) {
  // Erreur métier connue
  if (error instanceof AppError) {
    return NextResponse.json(
      { error: error.message, code: error.code },
      { status: error.status }
    )
  }
  // Erreur inattendue — log serveur, message générique client
  console.error('[PATCH /api/v1/tasks/:id]', {
    message: error instanceof Error ? error.message : 'Unknown',
    params: params.id,
  })
  return NextResponse.json({ error: 'Erreur serveur' }, { status: 500 })
}
```

### 6.4 Codes HTTP — guide de décision

```
Choisir le bon code HTTP n'est pas optionnel — le Frontend Developer
et le Testing Developer s'appuient dessus pour leurs traitements.

200 OK          → GET réussi, PATCH réussi
201 Created     → POST ayant créé une ressource (inclure la ressource dans le body)
204 No Content  → DELETE réussi (pas de body)
400 Bad Request → Paramètre manquant, mal formé ou non-UUID
401 Unauthorized → Pas de session active (pas d'utilisateur authentifié)
403 Forbidden   → Utilisateur authentifié mais sans droit sur cette ressource
404 Not Found   → La ressource existe en théorie mais pas pour cet ID
422 Unprocessable → Validation Zod échouée (données sémantiquement invalides)
500 Internal    → Erreur non anticipée (toujours loguer côté serveur)

Pièges fréquents :
  ❌ 200 quand rien n'a été créé → utiliser 201
  ❌ 400 pour une validation Zod → utiliser 422
  ❌ 404 pour un accès refusé → utiliser 403 (ne pas révéler l'existence)
  ❌ 500 sans log → toujours logger avec contexte avant de retourner 500
```

### 6.5 Isolation multi-tenant — règles absolues

```
Règle 1 : household_id n'est jamais lu depuis le body pour une opération existante
  ❌ body.householdId pour un PATCH — l'utilisateur ne contrôle pas à quel foyer appartient la ressource
  ✅ Lire le household_id depuis la DB via l'ID de la ressource :
     const { data: task } = await supabase.from('tasks').select('household_id').eq('id', taskId)

Règle 2 : la vérification d'appartenance utilise toujours l'ID de la session — jamais un paramètre
  ❌ .eq('profile_id', body.userId)     — contrôlable par l'attaquant
  ✅ .eq('profile_id', user.id)         — vient de supabase.auth.getUser()

Règle 3 : tester systématiquement le scénario cross-tenant
  → User A (foyer-1) fait PATCH /api/v1/tasks/[task-du-foyer-2] → doit retourner 403
  → User A fait GET /api/v1/tasks?householdId=[foyer-2] → doit retourner 403

Règle 4 : RLS est une deuxième défense, pas la seule
  → Ne pas supprimer les vérifications de membership "parce que RLS s'en occupe"
  → Les deux niveaux coexistent — la route vérifie, RLS confirme
```

### 6.6 Gestion du body JSON

```typescript
// Toujours défensive — le client peut envoyer n'importe quoi

// ✅ Pattern sûr : .catch() sur le parsing JSON
const body = await request.json().catch(() => null)
if (!body || typeof body !== 'object') {
  return NextResponse.json({ error: 'Body JSON invalide ou manquant' }, { status: 400 })
}

// Puis validation Zod immédiatement après
const parsed = schema.safeParse(body)
```

### 6.7 Variables d'environnement — règles de sécurité

```typescript
// ✅ Validées au démarrage — lib/env.ts
import { z } from 'zod'

export const env = z.object({
  NEXT_PUBLIC_SUPABASE_URL:      z.string().url(),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1),
  SUPABASE_SERVICE_ROLE_KEY:     z.string().min(1),
}).parse(process.env)

// Règles strictes :
// NEXT_PUBLIC_SUPABASE_URL      → utilisable browser + serveur (pas de secret)
// NEXT_PUBLIC_SUPABASE_ANON_KEY → utilisable browser + serveur (protégée par RLS)
// SUPABASE_SERVICE_ROLE_KEY     → SERVEUR UNIQUEMENT — jamais dans un composant 'use client'

// Vérification en CI (Infra Dev) :
// grep -r "SUPABASE_SERVICE_ROLE_KEY" .next/static/ → doit retourner 0 résultat
```

### 6.8 Pagination — pattern cursor-based

```typescript
// Pour toute liste pouvant dépasser 50 éléments
// Cursor = created_at du dernier élément reçu

export async function GET(request: NextRequest) {
  const cursor      = request.nextUrl.searchParams.get('cursor')      // ISO string ou null
  const limitParam  = request.nextUrl.searchParams.get('limit') ?? '20'
  const limit       = Math.min(parseInt(limitParam, 10), 50)           // cap à 50

  let query = supabase
    .from('tasks')
    .select('*')
    .eq('household_id', householdId)
    .order('created_at', { ascending: false })
    .limit(limit)

  if (cursor) {
    query = query.lt('created_at', cursor)  // items AVANT le curseur (plus anciens)
  }

  const { data, error } = await query
  if (error) throw error

  return NextResponse.json({
    items: data,
    nextCursor: data.length === limit ? data[data.length - 1].created_at : null,
    hasMore:    data.length === limit,
  })
}
```

### 6.9 Checklist — avant toute PR

```
STRUCTURE
  ☐ Structure de route respectée : validation → auth → appartenance → DB → réponse
  ☐ next build passe sans erreur TypeScript ni ESLint

VALIDATION
  ☐ Zod sur tous les inputs : body, params URL, query strings
  ☐ UUID validé avec z.string().uuid() pour tous les IDs
  ☐ 422 retourné avec details Zod sur validation échouée
  ☐ Body JSON parsé avec .catch(() => null)

SÉCURITÉ
  ☐ auth.getUser() appelé sur chaque route protégée → 401 si absent
  ☐ Vérification household_members → 403 si non-membre
  ☐ Vérification role === 'admin' sur les routes admin
  ☐ household_id lu depuis la DB, jamais depuis le body (opérations existantes)
  ☐ SERVICE_ROLE_KEY absente du bundle client

CODES HTTP
  ☐ POST retourne 201 (pas 200) sur création réussie
  ☐ DELETE retourne 204 (pas 200) sur suppression réussie
  ☐ 403 (pas 404) quand la ressource existe mais l'accès est refusé

ERREURS
  ☐ console.error avec contexte (route + params) dans chaque catch
  ☐ Message générique envoyé au client (pas le message Postgres brut)
  ☐ AppError pour les erreurs métier anticipées

CONTRAT
  ☐ Contrat d'API publié au Sync Point A (Frontend notifié)
  ☐ Schémas Zod dans src/lib/validations/ (partagés avec Frontend)
  ☐ Testing Developer notifié que les routes sont prêtes pour les tests d'intégration
```

### 6.10 Antipatterns à éviter

| Antipattern | Risque | Correction |
|---|---|---|
| Interroger la DB avant de vérifier l'auth | Fuite d'existence de ressource | Toujours auth → membership → DB |
| Lire household_id depuis le body pour PATCH/DELETE | Contournement de l'isolation tenant | Lire depuis la DB via l'ID de la ressource |
| Retourner 200 sur POST créateur | Frontend ne sait pas si création ou update | Toujours 201 sur création |
| Retourner 400 pour une erreur Zod | Non-standard, confus pour le client | Retourner 422 avec details |
| `any` sur le type de retour Supabase | Perd le typage TypeScript | `supabase.from('tasks').select()` est typé via Database |
| Exposer le message d'erreur Postgres | Révèle la structure interne | Logger côté serveur, retourner message générique |
| Oublier `.catch(() => null)` sur `request.json()` | Crash 500 si body malformé | Toujours défensif sur le parsing |
| Utiliser `SUPABASE_SERVICE_ROLE_KEY` côté client | Faille de sécurité critique | Serveur uniquement via `createServerClient()` |
| Compter sur RLS comme unique contrôle d'accès | Erreur de config = fuite totale | Double vérification route + RLS |

---

## Annexe — Références rapides

### A. Schémas Zod partagés — FoyerApp

```typescript
// src/lib/validations/task.ts
export const createTaskSchema = z.object({
  title:       z.string().min(1, 'Titre requis').max(100).trim(),
  description: z.string().max(500).trim().optional(),
})

// src/lib/validations/household.ts
export const createHouseholdSchema = z.object({
  name: z.string().min(2, 'Min 2 caractères').max(50).trim(),
})
export const joinHouseholdSchema = z.object({
  inviteCode: z.string().length(6, 'Le code doit faire 6 caractères').trim().toUpperCase(),
})

// src/lib/validations/shopping.ts
export const createShoppingItemSchema = z.object({
  name:        z.string().min(1).max(100).trim(),
  quantity:    z.string().max(50).trim().optional(),
  householdId: z.string().uuid(),
})
```

### B. Références techniques

| Ressource | URL |
|---|---|
| Next.js Route Handlers | https://nextjs.org/docs/app/building-your-application/routing/route-handlers |
| Supabase SSR Next.js | https://supabase.com/docs/guides/auth/server-side/nextjs |
| Zod documentation | https://zod.dev |
| Next.js Middleware | https://nextjs.org/docs/app/building-your-application/routing/middleware |

### C. Références projet

| Document | Localisation |
|---|---|
| Next.js Development Skill | `ai/roles/nextjs_development.md` |
| Supabase Database Skill | `ai/roles/supabase_database.md` |
| Types Supabase générés | `src/types/database.ts` |
| Architecture Overview | `docs/architecture/architecture_overview.md` |

---

*Ce document est la référence pour l'agent IA Backend Developer de FoyerApp. Il est mis à jour à chaque évolution de la stack, des conventions de validation ou des règles de sécurité de l'équipe.*
