# Architecture Overview — famille_new_app

> **Version** : 2.0  
> **Statut** : Draft  
> **Auteur** : Software Architect  
> **Dernière mise à jour** : 2026-03-04  
> **Stack** : Next.js · Supabase · Vercel · TailwindCSS

---

## Table des matières

1. [Vue d'ensemble de l'architecture](#1-vue-densemble-de-larchitecture)
2. [Modèle de données principal](#2-modèle-de-données-principal)
3. [Relations entre les entités](#3-relations-entre-les-entités)
4. [Gestion des invitations](#4-gestion-des-invitations)
5. [Structure des modules](#5-structure-des-modules)
6. [Flux de données](#6-flux-de-données)
7. [Principes d'architecture](#7-principes-darchitecture)
8. [Considérations de sécurité](#8-considérations-de-sécurité)
9. [Scalabilité future](#9-scalabilité-future)

---

## 1. Vue d'ensemble de l'architecture

### 1.1 Topologie générale

```
╔══════════════════════════════════════════════════════════════════════╗
║                        CLIENT (PWA)                                  ║
║            Next.js App Router — TailwindCSS                          ║
║   Pages · Components · Hooks · Context · Service Workers (PWA)       ║
╚══════════════════════╦═══════════════════════════════════════════════╝
                       ║  HTTPS / fetch / Supabase Realtime (WS)
╔══════════════════════╩═══════════════════════════════════════════════╗
║                       API LAYER (BFF)                                ║
║             Next.js API Routes  /api/v1/*                            ║
║   Auth middleware · Zod validation · Business logic · RLS enforcer   ║
╚══════════════════════╦═══════════════════════════════════════════════╝
                       ║  Supabase JS Client (service role)
╔══════════════════════╩═══════════════════════════════════════════════╗
║                      DATA LAYER                                      ║
║                    Supabase Cloud                                     ║
║    Postgres + RLS  │  Supabase Auth  │  Realtime  │  Storage         ║
╚══════════════════════╦═══════════════════════════════════════════════╝
                       ║  Deploy / Edge Functions / Emails
╔══════════════════════╩═══════════════════════════════════════════════╗
║                      HOSTING & SERVICES                              ║
║     Vercel (Edge Network · CDN · CI/CD)  +  Resend (emails)          ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 1.2 Choix d'architecture : BFF (Backend For Frontend)

Les API Routes Next.js jouent le rôle de **Backend For Frontend** : elles centralisent la logique métier, valident les entrées, gèrent les invitations et garantissent que les accès Supabase s'effectuent toujours avec les droits corrects. Le client ne communique **jamais directement** avec Supabase pour les mutations — seul le Realtime (lecture seule) est initié côté client.

### 1.3 Caractéristique clé : un utilisateur, plusieurs foyers

Un utilisateur Supabase Auth peut appartenir à **N foyers** via la table de jonction `membres_foyers`. Chaque action est contextualisée par un `foyer_id` actif, sélectionné en session côté client.

```
user (Supabase Auth)
  └── membre_foyer (rôle: admin | adulte | junior)
        ├── foyer A  ← foyer actif en session
        ├── foyer B
        └── foyer C
```

### 1.4 Deux mécanismes d'invitation coexistants

```
Inviter un membre
      │
      ├── Par email ──► invitation en DB + email Resend
      │                 └── lien sécurisé /join?token=<uuid>
      │
      └── Par code ───► code court alphanumérique (8 chars)
                        └── page /join?code=<CODE>
```

Les deux mécanismes aboutissent au même résultat : création d'une ligne dans `membres_foyers`. Ils sont traités par le même endpoint `POST /api/v1/foyers/join`.

---

## 2. Modèle de données principal

### 2.1 DDL Postgres (schéma public)

```sql
-- ─────────────────────────────────────────────
-- FOYERS
-- ─────────────────────────────────────────────
CREATE TABLE foyers (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nom             TEXT NOT NULL,
  code_invitation TEXT UNIQUE NOT NULL
                  DEFAULT upper(substring(md5(random()::text), 1, 8)),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────
-- MEMBRES (table de jonction user ↔ foyer)
-- ─────────────────────────────────────────────
CREATE TYPE membre_role AS ENUM ('admin', 'adulte', 'junior');

CREATE TABLE membres_foyers (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  foyer_id    UUID NOT NULL REFERENCES foyers(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  nom         TEXT NOT NULL,
  avatar_url  TEXT,
  role        membre_role NOT NULL DEFAULT 'adulte',
  actif       BOOLEAN NOT NULL DEFAULT true,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (foyer_id, user_id)
);

-- ─────────────────────────────────────────────
-- INVITATIONS (email uniquement)
-- ─────────────────────────────────────────────
CREATE TYPE invitation_statut AS ENUM ('en_attente', 'acceptee', 'expiree', 'annulee');

CREATE TABLE invitations (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  foyer_id      UUID NOT NULL REFERENCES foyers(id) ON DELETE CASCADE,
  invite_par    UUID NOT NULL REFERENCES membres_foyers(id),
  email         TEXT NOT NULL,
  token         UUID UNIQUE DEFAULT gen_random_uuid(),
  role_attribue membre_role NOT NULL DEFAULT 'adulte',
  statut        invitation_statut NOT NULL DEFAULT 'en_attente',
  expire_at     TIMESTAMPTZ NOT NULL DEFAULT now() + INTERVAL '7 days',
  acceptee_par  UUID REFERENCES auth.users(id),
  acceptee_at   TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_invitations_token  ON invitations(token) WHERE statut = 'en_attente';
CREATE INDEX idx_invitations_foyer  ON invitations(foyer_id);
CREATE INDEX idx_invitations_email  ON invitations(email);

-- ─────────────────────────────────────────────
-- CATÉGORIES DE DÉPENSES
-- ─────────────────────────────────────────────
CREATE TABLE categories_depenses (
  id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  foyer_id  UUID REFERENCES foyers(id) ON DELETE CASCADE,
  nom       TEXT NOT NULL,
  couleur   TEXT NOT NULL DEFAULT '#6B7280',
  icone     TEXT,
  systeme   BOOLEAN NOT NULL DEFAULT false
);

-- ─────────────────────────────────────────────
-- DÉPENSES
-- ─────────────────────────────────────────────
CREATE TABLE depenses (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  foyer_id     UUID NOT NULL REFERENCES foyers(id) ON DELETE CASCADE,
  membre_id    UUID NOT NULL REFERENCES membres_foyers(id),
  categorie_id UUID REFERENCES categories_depenses(id),
  montant      NUMERIC(10, 2) NOT NULL CHECK (montant > 0),
  description  TEXT,
  date         DATE NOT NULL DEFAULT CURRENT_DATE,
  recurrente   BOOLEAN NOT NULL DEFAULT false,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────
-- TÂCHES
-- ─────────────────────────────────────────────
CREATE TYPE tache_statut   AS ENUM ('a_faire', 'en_cours', 'terminee');
CREATE TYPE tache_priorite AS ENUM ('basse', 'normale', 'haute');

CREATE TABLE taches (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  foyer_id       UUID NOT NULL REFERENCES foyers(id) ON DELETE CASCADE,
  titre          TEXT NOT NULL,
  description    TEXT,
  assigne_a      UUID REFERENCES membres_foyers(id),
  cree_par       UUID NOT NULL REFERENCES membres_foyers(id),
  statut         tache_statut   NOT NULL DEFAULT 'a_faire',
  priorite       tache_priorite NOT NULL DEFAULT 'normale',
  date_echeance  DATE,
  recurrente     BOOLEAN NOT NULL DEFAULT false,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────
-- LISTES DE COURSES
-- ─────────────────────────────────────────────
CREATE TABLE listes_courses (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  foyer_id   UUID NOT NULL REFERENCES foyers(id) ON DELETE CASCADE,
  nom        TEXT NOT NULL,
  archivee   BOOLEAN NOT NULL DEFAULT false,
  created_by UUID REFERENCES membres_foyers(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE articles_courses (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  liste_id   UUID NOT NULL REFERENCES listes_courses(id) ON DELETE CASCADE,
  nom        TEXT NOT NULL,
  quantite   NUMERIC(6, 2) DEFAULT 1,
  unite      TEXT,
  coche      BOOLEAN NOT NULL DEFAULT false,
  coche_par  UUID REFERENCES membres_foyers(id),
  coche_at   TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2.2 Index complémentaires

```sql
CREATE INDEX idx_membres_foyers_user   ON membres_foyers(user_id);
CREATE INDEX idx_membres_foyers_foyer  ON membres_foyers(foyer_id);
CREATE INDEX idx_depenses_foyer_date   ON depenses(foyer_id, date DESC);
CREATE INDEX idx_taches_foyer_statut   ON taches(foyer_id, statut);
CREATE INDEX idx_articles_liste        ON articles_courses(liste_id);
```

---

## 3. Relations entre les entités

### 3.1 Diagramme entité-relation

```
┌─────────────┐         ┌──────────────────┐         ┌───────────────┐
│  auth.users │ 1 ─── N │  membres_foyers  │ N ─── 1 │    foyers     │
│  (Supabase) │         │  (rôle, actif)   │         │ (code_inv.)   │
└──────┬──────┘         └────────┬─────────┘         └──────┬────────┘
       │                         │ 1                         │ 1
       │ 1                  ┌────┼──────────────┐            │
       │                    │    │              │            │
      N│                   N│   N│             N│           N│
┌──────┴──────┐     ┌───────┴─┐ ┌┴───────┐ ┌───┴──────┐ ┌──┴─────────────┐
│ invitations │     │depenses │ │ taches │ │ articles │ │listes_courses  │
│  (token)    │     └─────────┘ └────────┘ │ _courses │ └────────────────┘
└─────────────┘          │                 └──────────┘
                        N│
                 ┌───────┴──────────┐
                 │categories_depenses│
                 └──────────────────┘
```

### 3.2 Cardinalités clés

| Relation | Type | Détail |
|---|---|---|
| `auth.users` → `membres_foyers` | 1–N | Un user peut être membre de N foyers |
| `foyers` → `membres_foyers` | 1–N | Un foyer a N membres |
| `foyers` → `invitations` | 1–N | Un foyer peut avoir N invitations actives |
| `membres_foyers` → `invitations` | 1–N | Un admin peut envoyer N invitations |
| `auth.users` → `invitations` (acceptee_par) | 0–1 | Une invitation est acceptée par au plus 1 user |
| `foyers` → `depenses` | 1–N | Toutes les dépenses sont scoped par foyer |
| `membres_foyers` → `taches` (assigne_a) | 0–N | Optionnel — une tâche peut être non assignée |
| `listes_courses` → `articles_courses` | 1–N | Une liste contient N articles |

### 3.3 Règles de suppression

| Suppression de | Comportement |
|---|---|
| `foyers` | CASCADE → membres_foyers, invitations, dépenses, tâches, listes, articles |
| `listes_courses` | CASCADE → articles_courses |
| `membres_foyers` | Les dépenses/tâches associées sont conservées dans l'historique du foyer |

---

## 4. Gestion des invitations

### 4.1 Vue d'ensemble des deux mécanismes

```
┌────────────────────────────────────────────────────────────────────┐
│                      INVITATION PAR EMAIL                          │
│                                                                    │
│  Admin saisit un email + rôle                                      │
│       │                                                            │
│       ▼                                                            │
│  POST /api/v1/foyers/:id/invitations                               │
│  { email: "...", role: "adulte" }                                  │
│       │                                                            │
│       ├── INSERT invitations (token UUID généré automatiquement)   │
│       └── Resend envoie email → /join?token=<UUID>                 │
│                                                                    │
│  Destinataire clique le lien                                       │
│       │                                                            │
│       ▼                                                            │
│  GET /join?token=<UUID>  →  page de confirmation                   │
│  POST /api/v1/foyers/join { token: "<UUID>" }                      │
│       ├── Vérifie : token valide, non expiré, statut en_attente    │
│       ├── Vérifie : email correspond au compte connecté            │
│       ├── INSERT membres_foyers                                    │
│       └── UPDATE invitations SET statut = 'acceptee'              │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                      INVITATION PAR CODE                           │
│                                                                    │
│  Admin partage le code court (ex: "A3F7K2B9")                      │
│  → visible dans Paramètres du foyer                                │
│  → partageable par copier/coller, SMS, QR code                     │
│                                                                    │
│  Nouveau membre saisit le code sur /join                           │
│  POST /api/v1/foyers/join { code: "A3F7K2B9" }                     │
│       ├── SELECT foyers WHERE code_invitation = 'A3F7K2B9'         │
│       ├── Vérifie que le user n'est pas déjà membre                │
│       ├── INSERT membres_foyers (rôle: 'adulte' par défaut)        │
│       └── Retourne foyer_id → redirect /dashboard                  │
└────────────────────────────────────────────────────────────────────┘
```

### 4.2 Comparaison des deux mécanismes

| Caractéristique | Email | Code |
|---|---|---|
| Tracé en DB | ✓ table `invitations` | ✗ (direct sur `foyers`) |
| Rôle pré-assigné | ✓ configurable | ✗ adulte par défaut |
| Expiration | 7 jours | Permanent (renouvelable) |
| Usage unique | ✓ | ✗ illimité |
| Vérification email | ✓ obligatoire | ✗ |
| Qui peut inviter | Admin uniquement | Admin + Adulte (lecture du code) |
| Audit trail | ✓ complet | ✗ (juste l'INSERT membres) |

### 4.3 Endpoint unifié `/api/v1/foyers/join`

```typescript
// Payload accepté — l'un ou l'autre, jamais les deux
type JoinPayload =
  | { token: string }   // invitation par email
  | { code: string }    // invitation par code

async function POST(req: Request) {
  const user = await getAuthenticatedUser(req)  // JWT obligatoire
  const body = JoinSchema.parse(await req.json())

  if ('token' in body) return handleTokenJoin(user, body.token)
  if ('code'  in body) return handleCodeJoin(user, body.code)
}
```

### 4.4 Règles métier

**Invitation par email :**
- Seuls les membres `admin` peuvent envoyer des invitations email
- Un email ne peut avoir qu'une seule invitation `en_attente` par foyer
- Le token expire après 7 jours
- L'email du destinataire doit correspondre à l'email du compte Supabase Auth au moment de l'acceptation
- Une invitation `acceptee` ou `expiree` ne peut pas être réutilisée

**Invitation par code :**
- Le code est visible par les membres `admin` et `adulte` dans les paramètres du foyer
- Tout utilisateur authentifié connaissant le code peut rejoindre
- Un user déjà membre du foyer ne peut pas rejoindre à nouveau (contrainte UNIQUE sur `foyer_id, user_id`)
- L'admin peut régénérer le code à tout moment — l'ancien code devient immédiatement invalide

### 4.5 Email d'invitation — contenu

```
Objet : Invitation à rejoindre le foyer "<nom_foyer>" sur famille_new_app

<prénom_invitant> vous invite à rejoindre le foyer "<nom_foyer>".

[ Rejoindre le foyer ]
→ https://app.famille-new-app.com/join?token=<UUID>

Ce lien est valable 7 jours et ne peut être utilisé qu'une seule fois.
Si vous n'attendiez pas cette invitation, ignorez cet email.
```

### 4.6 Régénération du code

```
POST /api/v1/foyers/:id/regenerate-code
  ├── Vérifie rôle admin
  ├── UPDATE foyers SET code_invitation = upper(substring(md5(random()::text), 1, 8))
  └── Retourne { code: "<NOUVEAU_CODE>" }
```

---

## 5. Structure des modules

### 5.1 Arborescence Next.js (App Router)

```
src/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   │
│   ├── join/
│   │   └── page.tsx                   # Page publique (token OU code)
│   │
│   ├── (app)/                         # Routes protégées
│   │   ├── layout.tsx                 # Auth guard + FoyerContext
│   │   ├── foyer/
│   │   │   ├── switch/page.tsx        # Sélecteur de foyer actif
│   │   │   ├── page.tsx               # Paramètres du foyer
│   │   │   └── invitations/page.tsx   # Gestion des invitations (admin)
│   │   ├── dashboard/page.tsx
│   │   ├── depenses/
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   ├── taches/
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   └── courses/
│   │       ├── page.tsx
│   │       └── [listId]/page.tsx
│   │
│   └── api/v1/
│       ├── foyers/
│       │   ├── route.ts                       # GET, POST
│       │   ├── join/route.ts                  # POST { token } | { code }
│       │   └── [id]/
│       │       ├── route.ts                   # GET, PATCH, DELETE
│       │       ├── membres/route.ts           # GET, PATCH rôle, DELETE
│       │       ├── invitations/route.ts       # GET, POST (email)
│       │       ├── invitations/[invId]/route.ts  # DELETE (annuler)
│       │       └── regenerate-code/route.ts   # POST
│       ├── depenses/
│       │   ├── route.ts
│       │   └── [id]/route.ts
│       ├── taches/
│       │   ├── route.ts
│       │   └── [id]/route.ts
│       └── courses/
│           ├── listes/route.ts
│           ├── listes/[id]/route.ts
│           └── listes/[id]/articles/route.ts
│
├── components/
│   ├── ui/                    # Button, Input, Modal, Badge…
│   ├── layout/                # Header, BottomNav, Sidebar
│   ├── foyer/                 # FoyerSwitcher, InviteModal, MemberCard, CodeShare
│   ├── depenses/
│   ├── taches/
│   ├── courses/
│   └── dashboard/
│
├── hooks/
│   ├── useFoyer.ts            # Foyer actif, liste des foyers
│   ├── useInvitations.ts      # CRUD invitations + régénération code
│   ├── useDepenses.ts
│   ├── useTaches.ts
│   └── useCourses.ts          # + Realtime subscription
│
├── lib/
│   ├── supabase/
│   │   ├── client.ts          # Client browser (anon key)
│   │   └── server.ts          # Client serveur (service role)
│   ├── email/
│   │   └── resend.ts          # Templates et envoi
│   ├── validations/           # Schémas Zod par domaine
│   └── utils/
│
└── types/index.ts
```

### 5.2 Responsabilités par couche

| Couche | Responsabilité | Ne doit pas |
|---|---|---|
| `app/(app)/` | Rendu UI, routing, état local | Contenir de la logique métier |
| `app/join/` | Page publique d'acceptation | Être protégée par auth guard |
| `hooks/` | Fetching, mutations, Realtime | Appeler Supabase directement |
| `app/api/v1/` | Validation, auth, logique métier, emails | Exposer des données d'autres foyers |
| `lib/email/` | Construction et envoi des emails | Contenir de la logique métier |
| `lib/supabase/` | Instanciation du client | Contenir des règles métier |

---

## 6. Flux de données

### 6.1 Invitation par email — envoi

```
Admin              API Route              Supabase DB          Resend
  │── POST /invitations ──►│                   │                  │
  │  { email, role }       │── vérif. admin ──►│                  │
  │                        │◄─ OK ─────────────│                  │
  │                        │── INSERT invitation►│                  │
  │                        │◄─ { token } ───────│                  │
  │                        │─────────────────── sendEmail(token) ──►│
  │◄── 201 Created ────────│                   │       email ──────►destinataire
```

### 6.2 Invitation par email — acceptation

```
Destinataire           API Route              Supabase DB
  │── GET /join?token ──►│ (page statique)         │
  │◄── page confirm. ────│                         │
  │── POST /foyers/join ─►│                         │
  │   { token }           │── SELECT invitation ───►│
  │                       │── vérifie statut,       │
  │                       │   expiration, email     │
  │                       │── INSERT membres_foyers ►│
  │                       │── UPDATE invitation ────►│
  │                       │   statut='acceptee'     │
  │◄── 200 { foyer_id } ──│                         │
  │── redirect /dashboard─►│                         │
```

### 6.3 Rejoindre par code

```
Nouveau membre         API Route              Supabase DB
  │── POST /foyers/join─►│                         │
  │   { code }           │── SELECT foyers ────────►│
  │                      │   WHERE code=...        │
  │                      │── vérifie not member    │
  │                      │── INSERT membres ───────►│
  │◄── 200 { foyer_id } ─│                         │
  │── redirect /dashboard►│                         │
```

### 6.4 Lecture standard (ex. : liste des dépenses)

```
Page monte → useDépenses(foyer_id)
  → GET /api/v1/depenses?foyer_id=<id>
  → Middleware vérifie JWT
  → API vérifie appartenance au foyer
  → SELECT Supabase (service role + filtre foyer_id)
  → RLS en backup côté Postgres
  → JSON → state → render
```

### 6.5 Écriture standard (ex. : ajouter une dépense)

```
Formulaire soumis
  → POST /api/v1/depenses { montant, categorie, … }
  → Middleware extrait user_id du JWT
  → Zod valide le payload
  → API vérifie appartenance au foyer
  → INSERT Supabase
  → 201 + objet créé → optimistic update
```

### 6.6 Realtime — synchronisation liste de courses

```
Client A                   Supabase DB              Client B
  │── subscribe 'liste:<id>'►│◄── subscribe 'liste:<id>'│
  │── PATCH article (coche) ─► (via API Route)          │
  │◄── 200 OK ───────────────│── broadcast UPDATE ──────►│
  │                          │                          │◄── state update
```

---

## 7. Principes d'architecture

### 7.1 Foyer comme unité d'isolation

Toutes les entités métier sont obligatoirement rattachées à un `foyer_id`. Il n'existe aucune ressource globale accessible sans contexte de foyer. Ce principe simplifie les règles RLS et garantit l'isolation des données.

### 7.2 API Routes comme seul point d'entrée métier

Le client ne fait jamais de mutations directes sur Supabase. Tout passe par les API Routes, ce qui centralise validation, logs, contrôles d'accès et envoi d'emails en un seul endroit.

Exception acceptée : les subscriptions Realtime (lecture seule) sont initiées directement depuis le client.

### 7.3 TypeScript strict end-to-end

Types générés depuis le schéma Supabase (`supabase gen types typescript`), partagés entre API Routes et composants. Aucun `any` en production.

### 7.4 Mobile-first, PWA by design

Breakpoints Tailwind `base` = mobile. Navigation par bottom nav sur mobile, sidebar sur desktop. Service Worker pour le cache des assets statiques. Manifest PWA pour l'installation sur écran d'accueil.

### 7.5 Validation à deux niveaux

```
Client (React Hook Form + Zod)  →  feedback immédiat UX
API Route (Zod)                 →  source de vérité, non contournable
```

### 7.6 Optimistic updates pour les interactions fréquentes

Cochage d'articles et changement de statut des tâches : l'UI se met à jour immédiatement, rollback déclenché en cas d'erreur API.

### 7.7 Page `/join` publique et universelle

Accessible sans authentification. Détecte automatiquement le mécanisme via les query params (`?token=` ou `?code=`) et gère les deux parcours : utilisateur déjà connecté ou nouvel utilisateur à inscrire.

---

## 8. Considérations de sécurité

### 8.1 Row Level Security (RLS)

Activé sur toutes les tables. Dernière ligne de défense côté base de données, indépendante de la couche API.

```sql
-- Membres : chaque user ne voit que ses propres entrées
ALTER TABLE membres_foyers ENABLE ROW LEVEL SECURITY;
CREATE POLICY "membres_select_own"
ON membres_foyers FOR SELECT USING (user_id = auth.uid());

-- Dépenses : scoped aux foyers du user
ALTER TABLE depenses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "depenses_select_own_foyers"
ON depenses FOR SELECT
USING (
  foyer_id IN (
    SELECT foyer_id FROM membres_foyers
    WHERE user_id = auth.uid() AND actif = true
  )
);

-- Invitations : visibles uniquement par les membres du foyer
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "invitations_select_membres"
ON invitations FOR SELECT
USING (
  foyer_id IN (
    SELECT foyer_id FROM membres_foyers WHERE user_id = auth.uid()
  )
);
```

Le même pattern est appliqué sur `taches`, `listes_courses`, `articles_courses`.

### 8.2 Sécurité des invitations

| Risque | Mitigation |
|---|---|
| Token devinable | UUID v4 — 122 bits d'entropie, non séquentiel |
| Réutilisation d'un token | Statut `acceptee` → rejet immédiat à toute nouvelle tentative |
| Token expiré | Vérification `expire_at > now()` côté API + index partiel |
| Email usurpé | `invitation.email` doit correspondre à `auth.user.email` à l'acceptation |
| Abus du code court | Rate limiting 10 tentatives/IP/heure sur `/foyers/join` |
| Code indûment exposé | Visible uniquement aux rôles `admin` et `adulte` |
| Code perpétuellement valide | Admin peut régénérer le code à tout moment |

### 8.3 Gestion des tokens d'authentification

| Pratique | Implémentation |
|---|---|
| Stockage | Cookies HTTP-only (pas de localStorage) |
| Refresh automatique | Middleware Next.js via `@supabase/ssr` |
| Expiration access token | 1 heure (défaut Supabase) |
| Rotation refresh token | Activée côté Supabase |

### 8.4 Matrice des autorisations par rôle

```
Action                         | admin | adulte | junior
-------------------------------|-------|--------|-------
Créer un foyer                 |  ✓    |   ✓    |   ✗
Inviter par email              |  ✓    |   ✗    |   ✗
Voir le code d'invitation      |  ✓    |   ✓    |   ✗
Régénérer le code              |  ✓    |   ✗    |   ✗
Modifier le rôle d'un membre   |  ✓    |   ✗    |   ✗
Saisir une dépense             |  ✓    |   ✓    |   ✗
Voir le dashboard budget       |  ✓    |   ✓    |  lecture
Créer / modifier une tâche     |  ✓    |   ✓    |   ✗
Cocher une tâche assignée      |  ✓    |   ✓    |   ✓
Gérer les listes de courses    |  ✓    |   ✓    |   ✓
Supprimer le foyer             |  ✓    |   ✗    |   ✗
```

### 8.5 Variables d'environnement

```bash
# .env.local — jamais commité
NEXT_PUBLIC_SUPABASE_URL=...        # Public — client browser
NEXT_PUBLIC_SUPABASE_ANON_KEY=...   # Public — RLS actif
SUPABASE_SERVICE_ROLE_KEY=...       # Privé — API Routes UNIQUEMENT
RESEND_API_KEY=...                  # Privé — envoi d'emails
NEXT_PUBLIC_APP_URL=...             # Public — construction des liens /join
```

La `SERVICE_ROLE_KEY` bypasse le RLS — elle n'est **jamais** exposée côté client.

### 8.6 Rate limiting et headers HTTP

- `/api/v1/foyers/join` : 10 tentatives/IP/heure
- `/api/v1/foyers/:id/invitations` : 20 invitations/foyer/jour
- Headers HTTP configurés dans `next.config.js` : `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`

---

## 9. Scalabilité future

### 9.1 Limites actuelles et seuils d'alerte

| Composant | Limite estimée | Signal d'alerte |
|---|---|---|
| Supabase Free | 500 MB DB, 2 GB bandwidth | > 200 foyers actifs |
| Vercel Hobby | 100 GB bandwidth | > 500 DAU |
| Supabase Realtime | 200 connexions simultanées | > 100 foyers en temps réel |
| Code d'invitation 8 chars | Risque de collision | > 100 000 foyers → passer à 12 chars |

### 9.2 Axes d'évolution

**Axe 1 — Performance budget** : table `budget_snapshots` (agrégats précalculés) alimentée par un cron Supabase Edge Function quand les dépenses dépassent ~10 000 lignes par foyer.

**Axe 2 — Notifications** : rappels de tâches et alertes budget via Supabase Edge Functions + Web Push API (PWA) en v2.

**Axe 3 — Offline avancé** : Service Worker Workbox + file de mutations offline via IndexedDB.

**Axe 4 — Application native** : React Native / Expo en réutilisant hooks, validations Zod et types. Les API Routes restent inchangées.

**Axe 5 — Invitations avancées** : QR code généré côté serveur, expiration configurable, limite de membres par code, invitation par SMS (Twilio).

### 9.3 Roadmap technique

```
MVP  (maintenant)
  └── Architecture décrite dans ce document
  └── Invitation email + code, RLS, Realtime courses

v1.1  (3 mois)
  └── QR code pour le code d'invitation
  └── Notifications email (rappels tâches, alertes budget)
  └── Snapshot budget mensuel (cron)
  └── Tests E2E Playwright

v2.0  (6 mois)
  └── Mode offline PWA (Workbox + IndexedDB)
  └── Membre junior avec permissions restreintes
  └── Export PDF budget mensuel

v3.0  (12 mois)
  └── App React Native (iOS + Android)
  └── Intégrations open banking
```

---

## Annexes

### A. ADR references

| ID | Décision | Statut |
|---|---|---|
| ADR-001 | Next.js App Router vs Pages Router | Accepté |
| ADR-002 | BFF pattern — pas d'accès Supabase direct depuis le client | Accepté |
| ADR-003 | RLS activé sur toutes les tables | Accepté |
| ADR-004 | Endpoint `/join` unifié pour token et code | Accepté |
| ADR-005 | `code_invitation` sur `foyers`, `token` sur `invitations` | Accepté |
| ADR-006 | Optimistic updates pour tâches et courses | Accepté |
| ADR-007 | Tokens auth en cookies HTTP-only vs localStorage | Accepté |

*Les ADR détaillés sont dans `docs/decisions/`.*

### B. Glossaire

| Terme | Définition |
|---|---|
| BFF | Backend For Frontend — couche API dédiée au client |
| RLS | Row Level Security — isolation des données au niveau Postgres |
| PWA | Progressive Web App — web app installable avec capacités natives |
| Realtime | WebSocket Supabase pour la synchronisation temps réel |
| Optimistic update | Mise à jour UI avant confirmation serveur, rollback si erreur |
| Service Role Key | Clé Supabase bypassant le RLS — usage serveur uniquement |
| ADR | Architecture Decision Record |
| Token d'invitation | UUID à usage unique, valable 7 jours, lié à un email |
| Code d'invitation | Code court alphanumérique permanent sur le foyer |

### C. Liens

| Ressource | Référence |
|---|---|
| Product Spec | `docs/product/product_spec.md` |
| Setup repo | `playbook/02-setup-repo.md` |
| Setup Supabase | `playbook/03-setup-supabase.md` |
| Décisions archi | `docs/decisions/` |
| Supabase RLS | https://supabase.com/docs/guides/auth/row-level-security |
| Supabase SSR Next.js | https://supabase.com/docs/guides/auth/server-side/nextjs |
| Resend (emails) | https://resend.com/docs |
| Next.js App Router | https://nextjs.org/docs/app |

---

*Ce document est la référence d'architecture pour l'équipe. Toute décision qui s'en écarte doit faire l'objet d'un ADR dans `docs/decisions/`.*
