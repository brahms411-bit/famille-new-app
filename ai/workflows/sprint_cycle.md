# Cycle de Sprint — AI Scrum Team

> **Système** : AI Scrum Team  
> **Document** : Guide d'exécution opérationnel  
> **Version** : 1.0  
> **Date** : 2026-03-04  
> **Projet** : FoyerApp — mobile-first PWA  
> **Stack** : Next.js · TypeScript · TailwindCSS · Supabase · Vercel

---

## Avant de commencer

Ce document décrit **ce qui se passe concrètement** à chaque étape du développement d'une User Story dans le système AI Scrum — qui fait quoi, avec quoi, et selon quelles règles. Il est le guide d'exécution que chaque agent lit pour savoir comment contribuer.

Il est **complémentaire** à `scrum_orchestrator.md` (qui décrit comment l'Orchestrateur pilote l'équipe) : là où l'Orchestrateur décrit le flux de coordination, ce document décrit l'exécution interne de chaque étape.

### Structure de chaque étape

```
┌─ Rôle responsable    Qui porte l'étape
├─ Inputs              Ce qui doit exister avant de commencer
├─ Outputs             Ce qui doit exister quand l'étape est Done
├─ Règles d'exécution  Comment le travail est réalisé
└─ Gate de sortie      Conditions vérifiables avant de passer à l'étape suivante
```

### Vue d'ensemble du cycle

```
Jour 1           Jour 1–2          Jour 2–9                     Jour 9–10
   │                 │                 │                              │
SPRINT           STORY            DÉVELOPPEMENT                  CLÔTURE
PLANNING         ANALYSIS         ─────────────                  ────────
   │                 │            UX → DB → BE ║ FE              REVIEW
   ▼                 ▼            → TESTS → QA                   RETRO
[Étape 1]        [Étape 2]       [Étapes 3–8]                  [Étape 9]
```

---

## Étape 1 — Sprint Planning

### Rôle responsable
**Scrum Master** (anime) · **Product Owner** (décide) · tous les agents (informés)

### Inputs

| Input | Source | Obligatoire |
|---|---|---|
| Backlog priorisé avec stories Ready | PO | ✅ |
| Vélocité des 2 derniers sprints | SM (historique) | ✅ |
| Capacité de l'équipe pour ce sprint | SM | ✅ |
| Dépendances inter-stories documentées | PO + SM | ✅ |
| Actions de Retrospective du sprint précédent | SM | ⚠️ Sprint 2+ |

**Définition de "Ready" pour une story :**
```
✅ Story au format standard (ID · Titre · Récit · Points · Priorité)
✅ ≥ 3 critères d'acceptation formulés en comportement observable
✅ Au moins 1 CA couvre un cas d'erreur (réseau, validation, accès refusé)
✅ Dépendances documentées et résolues (stories prérequises Done)
✅ Pour toute story FOYER / TASK / SHOP : 1 CA d'isolation multi-tenant
✅ Estimée en points de Fibonacci (1, 2, 3, 5, 8)
✅ ≤ 8 points (sinon décomposée avant le Planning)
```

### Outputs

```
1. Sprint Goal
   Format : 1–2 phrases, valeur utilisateur, pas technique
   Exemple : "L'utilisateur peut créer un foyer et y inviter un proche."

2. Sprint Backlog
   Liste ordonnée des stories sélectionnées avec :
   - Somme des points ≤ vélocité historique × 0.9 (marge de sécurité 10%)
   - Dépendances inter-stories résolues ou clairement signalées
   - Chaque story a le statut READY

3. Plan de tâches par story (au format ci-dessous)
```

**Format du plan de tâches :**
```markdown
### Story [ID] — [Titre] — [N] points

| ID  | Tâche | Agent | Effort | Dépend de |
|-----|-------|-------|--------|-----------|
| T01 | Migrations SQL + RLS policies | DB   | 2h | — |
| T02 | Fiche écran UX (tous les états) | UX   | 2h | — |
| T03 | Contrat d'API (SYNC A) | BE   | 1h | T01 |
| T04 | API Routes + schémas Zod | BE   | 3h | T01 |
| T05 | Composants React | FE   | 3h | T02, T03 |
| T06 | Custom hooks + optimistic | FE   | 2h | T03 |
| T07 | Tests unitaires (composants + hooks) | TEST | 2h | T05, T06 |
| T08 | Tests intégration (API Routes) | TEST | 2h | T04 |
| T09 | Tests RLS isolation | TEST | 1h | T01 |
| T10 | Preview deployment + migrations | INFRA| 1h | T04, T05 |
| T11 | Validation QA sur preview | QA   | 2h | T07–T10 |

**Sync Points** :
  SYNC A : T01 Done → DB partage types TypeScript → BE + FE
  SYNC B : T03 Done → BE partage contrat API → FE
  SYNC C : T07–T10 Done → TEST + INFRA confirment → QA démarre
```

### Règles d'exécution

```
SÉLECTION DES STORIES
  → SM propose, PO décide du périmètre final
  → Jamais de story non-Ready dans le Sprint Backlog — sans exception
  → Si une story prérequise n'est pas Done : reporter la story dépendante
  → Inclure les actions de Retro si elles ont généré des stories techniques

ESTIMATION DE LA CAPACITÉ
  → Capacité = vélocité moyenne (N-1, N-2 sprints) × 0.9
  → Si sprint 1 (pas d'historique) : capacité = 12 points par défaut
  → Ajuster si un agent sera partiellement indisponible

SPRINT GOAL
  → Doit être validé par le PO avant de fermer le Planning
  → Formulé du point de vue de l'utilisateur ("L'utilisateur peut...")
  → Ne pas lister des tâches techniques ("Implémenter la table tasks")
  → Si les stories sélectionnées ne forment pas de cohérence narrative : revoir la sélection

DÉCOMPOSITION EN TÂCHES
  → Chaque story est décomposée en tâches avant la fin du Planning
  → Tâche = unité de travail pour un seul agent, durée ≤ 4h
  → Toute tâche > 4h est re-décomposée
  → Les dépendances entre tâches sont documentées explicitement
```

### Gate de sortie

```
☐ Sprint Goal validé par le PO — formulé en 1–2 phrases
☐ Sprint Backlog : toutes les stories ont le statut READY
☐ Somme des points ≤ capacité calculée
☐ Dépendances inter-stories vérifiées
☐ Plan de tâches produit pour chaque story
☐ Tous les agents ont lu les stories qui les concernent
```

---

## Étape 2 — Story Analysis

### Rôle responsable
**Orchestrateur** (analyse) · **Product Owner** (clarification si nécessaire)

### Inputs

| Input | Source |
|---|---|
| User Story au format standard | PO (Sprint Backlog) |
| Critères d'acceptation | PO |
| Definition of Done du projet | `docs/backlog/ai_scrum_backlog.md` |
| Matrice de dépendances | SM (Étape 1) |

### Outputs

```
1. Rapport d'analyse de la story
   Contenu :
   - Résultat checklist INVEST (7 critères)
   - Points d'attention par agent (ex: "CA-3 implique Realtime")
   - Dépendances confirmées Done ou signalées
   - Questions de clarification si nécessaire (max 1 par cycle)

2. Stories décomposées (si > 8 points)
   - Proposition de 2–3 sous-stories avec CA redistribués
   - Soumises au PO pour validation

3. Feu vert "Story analysée — prête pour UX + DB"
```

**Format du rapport d'analyse :**
```markdown
## Analyse — [ID Story] — [Titre]

### Checklist INVEST
- [x] Indépendante — pas de blocage sur les autres stories en cours
- [x] Négociable — CA formulés en comportements, pas en implémentation
- [x] Valuable — valeur utilisateur explicite dans le récit
- [x] Estimable — [N] points
- [x] Small — ≤ 8 points
- [x] Testable — chaque CA est vérifiable

### Règles FoyerApp
- [x] CA d'isolation multi-tenant : CA-[N] ("L'utilisateur ne voit que les données de son foyer")
- [x] CA d'erreur réseau : CA-[N] ("Si le réseau est indisponible, un message d'erreur s'affiche")
- [ ] ⚠️ CA d'état vide manquant — à ajouter (liste vide non couverte)

### Points d'attention par agent
- UX  : L'état vide doit être conçu (liste sans tâches au premier lancement)
- BE  : Route PATCH doit vérifier le rôle 'admin' sur CA-4
- TEST : Tester le rollback de l'optimistic update (CA-3)

### Dépendances
- FOYER-01 : Done ✅

### Décision
✅ Story prête — lancer UX + DB en parallèle
```

### Règles d'exécution

```
CHECKLIST INVEST
  Vérifier les 7 critères dans l'ordre
  Un seul critère non satisfait → blocage avec question précise au PO
  Ne jamais avancer avec une ambiguïté sur un CA

RÈGLES FOYERAPP SPÉCIFIQUES
  Toute story FOYER / TASK / SHOP doit avoir :
  → 1 CA d'isolation : "L'utilisateur A ne voit pas les données du foyer de l'utilisateur B"
  → 1 CA d'erreur réseau sur chaque mutation (POST, PATCH, DELETE)
  Si ces CA manquent → les signaler au PO pour ajout avant de continuer

QUESTIONS DE CLARIFICATION
  → 1 seule question par cycle de réponse
  → Formulée avec des options si possible : "CA-3 : optimistic update (immédiat) ou refetch (après API) ?"
  → Adressée au PO uniquement — pas d'interprétation silencieuse
  → Story suspendue jusqu'à la réponse

DÉCOMPOSITION
  → Story > 8 points : proposer la décomposition avant de continuer
  → Ne jamais passer à l'Étape 3 avec une story > 8 points
```

### Gate de sortie

```
☐ Checklist INVEST : 7/7 critères satisfaits
☐ CA d'isolation multi-tenant présent (stories avec données de foyer)
☐ CA d'erreur réseau présent (stories avec mutations)
☐ Toutes les ambiguïtés levées
☐ Dépendances confirmées Done
☐ Points d'attention rédigés pour chaque agent concerné
☐ Rapport d'analyse produit et partagé
```

---

## Étape 3 — UX Design

### Rôle responsable
**UX Designer**

### Inputs

| Input | Source |
|---|---|
| User Story + CA | PO |
| Rapport d'analyse (points d'attention UX) | Orchestrateur (Étape 2) |
| Inventaire des composants existants | `ux_design.md` §3.5 |
| Système de design (grille, typo, couleurs) | `ux_design.md` §3.2–§3.4 |
| Structure de navigation FoyerApp | `ux_design.md` §4.1 |

### Outputs

```
1. Fiche(s) écran — une par écran impliqué dans la story
   Contenu obligatoire :
   → Route ou nom du composant
   → Layout mobile 375px (description haut → bas, composants, classes Tailwind clés)
   → 5 états : loading · vide · nominal · erreur · succès
   → Comportements (déclencheur → résultat observable)
   → Adaptation desktop ≥ 768px (delta vs mobile)
   → Composants utilisés (existants) + composants à créer (nouveaux)
   → Accessibilité : ratios de contraste, aria-labels, ordre de focus

2. Nouveaux composants documentés dans l'inventaire
   → Ajout à ux_design.md §3.5 si un composant nouveau est requis
```

**Format de la fiche écran :**
```markdown
## FICHE ÉCRAN — [Nom]

**Story**        : [ID] — [Titre]
**Route**        : /[route] ou Composant [Nom]
**Objectif**     : [Ce que l'utilisateur accomplit]

---

### Layout mobile (375px)

[En-tête] PageHeader — titre "[Titre de la page]" + bouton "[Label CTA]"
[Liste]   [Composant]List
  [Item]  [Composant]Card × N
    [Contenu de l'item]
[Nav]     BottomNav — onglets : Accueil / Tâches / Courses (pb-safe)

---

### États

| État | Déclencheur | Rendu |
|---|---|---|
| Loading | Fetch en cours | [Composant]Skeleton — animate-pulse, 3 lignes |
| Vide | Liste vide | EmptyState — icône + "Aucun [item]" + CTA |
| Nominal | Données présentes | [Composant]List avec items |
| Erreur | Échec API | Message d'erreur inline + bouton "Réessayer" |
| Succès | Action réussie | Toast haut (top-4) + transition |

---

### Comportements

- Tap sur checkbox → optimistic toggle → PATCH /api/v1/[ressource]/:id
- Tap sur CTA "+" → ouverture bottom drawer → [Composant]Form
- Soumission du formulaire → POST → item ajouté en tête de liste

---

### Adaptation desktop (≥ 768px)

- Sidebar 240px remplace BottomNav (hidden md:flex)
- Liste centrée max-w-2xl
- Bottom drawer → modale centrée max-w-lg

---

### Composants

| Composant | Statut | Props clés |
|---|---|---|
| [Composant]Card | Existant / Nouveau | task, onToggle, className |
| [Composant]Form | Nouveau | onSubmit, onCancel |
| EmptyState | Existant | title, description, cta |

---

### Accessibilité

- Contraste texte/fond : #1F2937 sur #F9FAFB → 15.3:1 ✅ (cible ≥ 4.5:1)
- aria-label : bouton toggle → "Marquer '[titre]' comme [état]"
- Focus order : PageHeader → [items de liste] → BottomNav
- Zones de tap : checkbox 44×44px · bouton CTA 44px de hauteur
```

### Règles d'exécution

```
MOBILE-FIRST ABSOLU
  → Toujours concevoir le layout 375px en premier
  → Ne jamais écrire "comme sur desktop mais plus petit"
  → pb-safe obligatoire sur tout élément en bas d'écran
  → L'adaptation desktop est un delta, pas une refonte

5 ÉTATS OBLIGATOIRES
  → Loading : skeleton (animate-pulse) — jamais d'écran blanc pendant le chargement
  → Vide : empty state avec illustration/icône + texte + CTA si action possible
  → Nominal : contenu avec données réelles
  → Erreur : message en langage humain + action de récupération (bouton réessayer ou lien)
  → Succès : feedback positif (toast en haut, 3s, pas en bas sur mobile)

ACCESSIBILITÉ BY DESIGN
  → Calculer les ratios de contraste dès la conception (jamais en correction)
  → aria-label sur tout bouton dont le texte visible est insuffisant
  → Définir l'ordre de focus logique pour chaque écran
  → Focus trap spécifié pour toute modale ou drawer

COMPOSANTS EXISTANTS AVANT NOUVEAUX
  → Consulter l'inventaire §3.5 du skill ux_design.md avant de créer
  → Documenter tout nouveau composant dans l'inventaire immédiatement
  → 1 question au PO si un CA implique un comportement non couvert par les composants existants
```

### Gate de sortie

```
☐ Fiche écran produite pour chaque écran impliqué dans la story
☐ 5 états spécifiés (loading, vide, nominal, erreur, succès)
☐ Zones de tap ≥ 44×44px sur tous les éléments interactifs
☐ aria-labels définis sur les éléments non-natifs
☐ Adaptation desktop (≥ 768px) spécifiée
☐ Nouveaux composants documentés dans l'inventaire
☐ Checklist de revue Annexe A (ux_design.md) passante
```

---

## Étape 4 — Database Design

### Rôle responsable
**Database Developer**

### Inputs

| Input | Source |
|---|---|
| User Story + CA | PO |
| Rapport d'analyse (points d'attention DB) | Orchestrateur (Étape 2) |
| Schéma actuel | `supabase_database.md` §2 |
| Patterns RLS | `supabase_database.md` §4 |
| `src/types/database.ts` actuel | Repo |

### Outputs

```
1. Fichier de migration SQL
   Localisation : supabase/migrations/[YYYYMMDDHHMMSS]_[description].sql
   Contenu :
   → Commentaire en-tête (story, date, description)
   → CREATE TABLE IF NOT EXISTS avec toutes les contraintes
   → ALTER TABLE ... ENABLE ROW LEVEL SECURITY
   → Policies DROP IF EXISTS + CREATE pour les 4 opérations
   → CREATE INDEX IF NOT EXISTS pour les requêtes connues
   → Triggers si nécessaires (updated_at, handle_*)

2. src/types/database.ts mis à jour
   → Généré via : supabase gen types typescript --local
   → Commité dans la même PR que la migration

3. Signal SYNC A
   → Message structuré vers Backend Dev et Frontend Dev
   → Contenu : tables modifiées, nouvelles colonnes, types disponibles
```

**Contenu type d'une migration :**
```sql
-- ─────────────────────────────────────────────────────
-- Migration : [Description]
-- Story     : [ID]
-- Date      : YYYY-MM-DD
-- ─────────────────────────────────────────────────────

-- ── 1. Table ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.tasks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    title        TEXT NOT NULL CHECK (char_length(title) BETWEEN 1 AND 100),
    description  TEXT CHECK (char_length(description) <= 500),
    is_completed BOOLEAN NOT NULL DEFAULT false,
    created_by   UUID REFERENCES profiles(id) ON DELETE SET NULL,
    assigned_to  UUID REFERENCES profiles(id) ON DELETE SET NULL,
    due_date     DATE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── 2. Sécurité ───────────────────────────────────────
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "tasks_select_member" ON public.tasks;
CREATE POLICY "tasks_select_member"
ON public.tasks FOR SELECT
USING (public.is_household_member(household_id));

DROP POLICY IF EXISTS "tasks_insert_member" ON public.tasks;
CREATE POLICY "tasks_insert_member"
ON public.tasks FOR INSERT
WITH CHECK (public.is_household_member(household_id));

DROP POLICY IF EXISTS "tasks_update_member" ON public.tasks;
CREATE POLICY "tasks_update_member"
ON public.tasks FOR UPDATE
USING  (public.is_household_member(household_id))
WITH CHECK (public.is_household_member(household_id));

DROP POLICY IF EXISTS "tasks_delete_member" ON public.tasks;
CREATE POLICY "tasks_delete_member"
ON public.tasks FOR DELETE
USING (public.is_household_member(household_id));

-- ── 3. Performance ────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_tasks_household_created
    ON public.tasks (household_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_tasks_household_incomplete
    ON public.tasks (household_id)
    WHERE is_completed = false;

-- ── 4. Trigger updated_at ─────────────────────────────
CREATE TRIGGER trg_tasks_updated_at
    BEFORE UPDATE ON public.tasks
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ROLLBACK :
-- DROP TABLE IF EXISTS public.tasks CASCADE;
```

### Règles d'exécution

```
RÈGLE ABSOLUE — household_id
  → Toute table avec des données métier doit avoir :
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE
  → Sans cette colonne et cette contrainte → la table n'entre pas en production

ORDRE DANS LA MIGRATION
  → CREATE TABLE → ENABLE RLS → Policies → Indexes → Triggers
  → Toujours dans cet ordre — les policies référencent la table

IDEMPOTENCE OBLIGATOIRE
  → CREATE TABLE IF NOT EXISTS
  → DROP POLICY IF EXISTS avant CREATE POLICY
  → CREATE INDEX IF NOT EXISTS
  → CREATE OR REPLACE FUNCTION
  → La migration doit pouvoir être rejoouée sans erreur

VALIDATION AVANT SYNC A
  → Appliquer localement : supabase db push
  → Exécuter les tests RLS (supabase_database.md §4.8)
  → Vérifier : User A ne voit pas les données du foyer de User B
  → Régénérer les types : supabase gen types typescript --local > src/types/database.ts
  → Seulement alors : émettre SYNC A

BREAKING CHANGES
  → Renommer une colonne existante = breaking change = préavis 1 cycle
  → Supprimer une colonne = toujours migration en 2 étapes (déprécier → supprimer)
  → Signaler au BE et FE avant d'appliquer
```

### Gate de sortie

```
☐ Migration SQL créée dans supabase/migrations/ avec timestamp correct
☐ household_id NOT NULL sur toute nouvelle table métier
☐ RLS activé (ALTER TABLE ... ENABLE ROW LEVEL SECURITY)
☐ 4 policies présentes (SELECT / INSERT WITH CHECK / UPDATE / DELETE)
☐ Indexes créés selon les patterns de requêtes du Backend
☐ Migration testée localement sans erreur (supabase db push)
☐ Tests RLS passants (isolation cross-foyer vérifiée)
☐ Types TypeScript régénérés et commités
☐ SYNC A émis vers BE + FE
```

---

## Étape 5 — Backend Implementation

### Rôle responsable
**Backend Developer**

### Inputs

| Input | Source |
|---|---|
| User Story + CA | PO |
| SYNC A (schéma + types TypeScript) | Database Developer (Étape 4) |
| Rapport d'analyse (points d'attention BE) | Orchestrateur (Étape 2) |
| Patterns API Routes | `nextjs_development.md` §5 |
| Pattern d'appartenance | `supabase_database.md` §3.2 |

### Outputs

```
1. Schémas Zod
   Localisation : src/lib/validations/[domaine].ts
   Contenu : createSchema, patchSchema pour chaque entité touchée

2. API Routes
   Localisation : src/app/api/v1/[ressource]/route.ts (GET, POST)
                  src/app/api/v1/[ressource]/[id]/route.ts (PATCH, DELETE)
   Contenu : chaîne validation → auth → membership → DB → réponse

3. Contrat d'API (SYNC B)
   Format : documentation TypeScript des routes avec types de retour et codes HTTP
   Partagé avec : Frontend Developer
```

**Structure obligatoire d'une API Route :**
```typescript
export async function [METHOD](request: NextRequest) {
  try {
    // ── 1. Validation ────────────────────────────────
    // Zod sur params, searchParams, body — retourner 400 ou 422

    // ── 2. Authentification ──────────────────────────
    // const { data: { user } } = await supabase.auth.getUser()
    // 401 si user null

    // ── 3. Appartenance au foyer ─────────────────────
    // Vérifier household_members — 403 si non-membre
    // Vérifier role === 'admin' si opération admin

    // ── 4. Opération DB ──────────────────────────────
    // Requête Supabase typée via Database

    // ── 5. Réponse ───────────────────────────────────
    // 200 (GET/PATCH), 201 (POST), 204 (DELETE)

  } catch (error) {
    console.error('[METHOD /api/v1/[ressource]]', error)
    return NextResponse.json({ error: 'Erreur serveur' }, { status: 500 })
  }
}
```

**Format du contrat d'API (SYNC B) :**
```typescript
/**
 * CONTRAT D'API — Story [ID]
 *
 * GET /api/v1/[ressource]?householdId=UUID
 *   Auth    : session requis → 401
 *   Access  : membership → 403
 *   Success : 200 + [Type][]
 *   Errors  : 400 | 401 | 403 | 500
 *
 * POST /api/v1/[ressource]
 *   Body    : { field: type, householdId: UUID }
 *   Success : 201 + [Type] créé
 *   Errors  : 422 (Zod) | 401 | 403 | 500
 *
 * PATCH /api/v1/[ressource]/:id
 *   Body    : { field?: type }
 *   Success : 200 + [Type] mis à jour
 *   Errors  : 400 | 404 | 422 | 401 | 403 | 500
 */
```

### Règles d'exécution

```
CHAÎNE DE SÉCURITÉ — ordre non négociable
  validation → auth → membership → DB → réponse
  Aucune étape ne peut être réordonnée ou sautée

VALIDATION ZOD
  → z.string().uuid() sur tous les IDs — jamais accepter une chaîne libre
  → z.string().min(1).max(N).trim() sur toutes les chaînes saisies par l'utilisateur
  → safeParse — retourner 422 avec error.flatten() pour les erreurs de validation
  → request.json().catch(() => null) — toujours défensif sur le parsing JSON

CODES HTTP
  → POST créateur → 201 (pas 200)
  → DELETE → 204 (pas 200)
  → Validation Zod → 422 (pas 400)
  → Non-membre → 403 (pas 404 — ne pas révéler l'existence de la ressource)

ISOLATION MULTI-TENANT
  → household_id lu depuis la DB pour les opérations sur ressources existantes
  → Jamais depuis le body pour un PATCH ou DELETE
  → Vérifier household_members avec l'ID de l'utilisateur authentifié — jamais un paramètre

SERVICE_ROLE_KEY
  → Uniquement dans createServerClient() côté serveur
  → Vérifier avant toute PR : grep -r "SUPABASE_SERVICE_ROLE" .next/static/ → 0 résultat
```

### Gate de sortie

```
☐ Schémas Zod créés dans src/lib/validations/
☐ API Routes créées avec chaîne de sécurité complète
☐ Codes HTTP corrects (201 pour POST, 204 pour DELETE, 422 pour Zod)
☐ next build passe sans erreur TypeScript ni ESLint
☐ SERVICE_ROLE_KEY absente du bundle client
☐ Contrat d'API (SYNC B) documenté et partagé avec Frontend Dev
```

---

## Étape 6 — Frontend Implementation

### Rôle responsable
**Frontend Developer**

### Inputs

| Input | Source |
|---|---|
| Fiche(s) écran UX | UX Designer (Étape 3) |
| SYNC B — contrat d'API | Backend Developer (Étape 5) |
| SYNC A — types TypeScript | Database Developer (Étape 4) |
| Inventaire des composants | `ux_design.md` §3.5 |
| Patterns composants et hooks | `nextjs_development.md` §3–§4 |

### Outputs

```
1. Composants React
   Localisation : src/components/[domaine]/[Composant].tsx
   Contenu : tous les états (loading, vide, nominal, erreur, succès)
             props TypeScript explicites
             zones de tap ≥ 44×44px
             aria-labels sur éléments non-natifs

2. Custom hooks
   Localisation : src/hooks/use[Domaine].ts
   Contenu : fetch initial, mutations, optimistic update, rollback

3. Page assemblée
   Localisation : src/app/(app)/[route]/page.tsx
   Contenu : orchestration composants + hook

4. Auto-validation self-reported
   Liste des vérifications effectuées avant de signaler Done
```

**Pattern hook avec optimistic update :**
```typescript
// Structure type — à adapter par domaine

const toggle[Item] = useCallback(async (id: string, newValue: boolean) => {
  // 1. Mise à jour optimiste immédiate
  set[Items](prev => prev.map(item =>
    item.id === id ? { ...item, [field]: newValue } : item
  ))
  try {
    // 2. Appel API en arrière-plan
    const res = await fetch(`/api/v1/[ressource]/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [field]: newValue }),
    })
    if (!res.ok) throw new Error('Mise à jour impossible')
  } catch (err) {
    // 3. Rollback si erreur
    set[Items](prev => prev.map(item =>
      item.id === id ? { ...item, [field]: !newValue } : item
    ))
    throw err  // propagé pour affichage du toast d'erreur
  }
}, [])
```

### Règles d'exécution

```
RESPECT DE LA FICHE ÉCRAN
  → La fiche écran est la source de vérité — pas d'interprétation libre
  → Si un comportement de la fiche n'est pas implémentable tel quel :
    signaler à l'UX Designer avant de dévier, pas après
  → Les classes Tailwind sont celles de la fiche — utiliser cn() pour les variantes

ÉTATS OBLIGATOIRES
  → Les 5 états doivent être implémentés avant de déclarer Done
  → Ne jamais rendre un écran blanc pendant le chargement
  → Ne jamais laisser une liste vide sans empty state
  → Les messages d'erreur sont en langage humain (jamais "Error 403")

OPTIMISTIC UPDATES
  → Obligatoire sur les actions fréquentes : cocher/décocher
  → Pattern strict : mise à jour locale → appel API → rollback si erreur
  → Le rollback remet l'état exactement comme avant l'action

ACCESSIBILITÉ
  → focus-visible:ring-2 sur tous les éléments focusables — vérifier avant PR
  → aria-label sur tout bouton dont le texte seul est insuffisant
  → motion-reduce:transition-none sur toutes les animations
  → Focus trap dans les drawers et modales — Tab ne sort pas du dialog

VÉRIFICATIONS AVANT SIGNAL DONE
  → next build propre
  → Viewport 375px testé dans Chrome DevTools (iPhone SE)
  → pb-safe sur les éléments en bas d'écran vérifiés
  → Zones de tap ≥ 44×44px vérifiées en DevTools mobile
```

### Gate de sortie

```
☐ Composants créés avec les 5 états implémentés
☐ Custom hooks avec optimistic update + rollback (si applicable)
☐ Page assemblée dans src/app/(app)/[route]/page.tsx
☐ next build passe sans erreur TypeScript ni ESLint
☐ TypeScript strict — aucun any, aucun as non justifié
☐ Vérifié sur 375px (Chrome DevTools)
☐ pb-safe présent sur les éléments proches du bas
☐ aria-labels sur les boutons sans texte suffisant
☐ focus-visible:ring sur tous les éléments focusables
```

---

## Étape 7 — Automated Testing

### Rôle responsable
**Testing Developer** (tests) · **Infrastructure Developer** (preview, en parallèle)

### Inputs

| Input | Source |
|---|---|
| Composants FE | Frontend Developer (Étape 6) |
| API Routes BE | Backend Developer (Étape 5) |
| Migration DB + policies RLS | Database Developer (Étape 4) |
| User Story + CA | PO |
| Patterns de tests | `testing_quality.md` §3–§4 |

### Outputs Testing Developer

```
1. Tests unitaires
   src/__tests__/components/[domaine]/[Composant].test.tsx
   src/__tests__/hooks/use[Domaine].test.ts
   src/__tests__/lib/validations/[domaine].test.ts
   Couverture : chaque CA couvert par ≥ 1 test

2. Tests d'intégration
   src/__tests__/api/[ressource]/route.test.ts
   Cas couverts : validation (400/422) · auth (401) · isolation (403) · nominal (200/201)

3. Tests RLS
   supabase/tests/rls/[table]_isolation.sql
   Vérification : User A ne voit/ne modifie pas les données du foyer de User B

4. Rapport de couverture
   Coverage ≥ 70% sur le code métier
```

### Outputs Infrastructure Developer

```
1. CI pipeline vert (GitHub Actions)
   type-check ✅ · lint ✅ · tests ✅ · build ✅

2. Preview deployment accessible
   URL : https://foyerapp-[branch-slug].vercel.app

3. Migrations appliquées sur l'environnement preview
   Confirmation : supabase db push --db-url $PREVIEW_DB_URL

4. Signal SYNC C vers QA
   "Preview disponible : [URL] — CI verte — migrations preview appliquées"
```

**Structure type d'un test d'intégration API :**
```typescript
describe('[METHOD] /api/v1/[ressource]', () => {

  describe('validation', () => {
    it('retourne 400 si [param] est absent', async () => { ... })
    it('retourne 422 si [field] dépasse [N] caractères', async () => { ... })
  })

  describe('authentification', () => {
    it('retourne 401 si pas de session', async () => { ... })
  })

  describe('autorisation', () => {
    it('retourne 403 si l\'utilisateur n\'est pas membre du foyer', async () => { ... })
  })

  describe('nominal', () => {
    it('retourne 200/201 avec les données attendues', async () => { ... })
  })
})
```

### Règles d'exécution Testing Developer

```
RÈGLE FONDAMENTALE
  → Un test qui ne peut pas échouer ne prouve rien
  → Vérifier qu'un test rouge existe avant le fix pour chaque scénario d'erreur
  → Chaque CA de la story = au moins 1 test automatisé

CE QUE LE TESTING DEV COUVRE (complément des Dev)
  → Tests de validation des CA (pas de duplication des tests unitaires Developer)
  → Tests de cas limites implicites (longueurs max, listes vides, valeurs null)
  → Tests d'isolation multi-tenant (ce que le Developer omet naturellement)
  → Tests des cas d'erreur réseau et d'authentification

ISOLATION RLS — SYSTÉMATIQUE
  → Obligatoire sur toute story FOYER / TASK / SHOP
  → Tester les 4 opérations : SELECT / INSERT / UPDATE / DELETE cross-foyer
  → Un bug d'isolation = P1 Bloquant → signal immédiat au SM

COUVERTURE
  → Exécuter npm run test:coverage avant de valider
  → Seuil global : 70% sur branches, functions, lines, statements
  → Si seuil non atteint : identifier les chemins non couverts et ajouter les tests
```

### Règles d'exécution Infrastructure Developer

```
ORDRE D'EXÉCUTION
  → CI doit passer avant de créer le preview
  → Migrations preview appliquées AVANT de notifier le QA
  → Ne jamais signaler "preview prêt" si CI en rouge

VÉRIFICATION DU BUNDLE
  → Après chaque build CI : vérifier absence SERVICE_ROLE_KEY
  → grep -r "SUPABASE_SERVICE_ROLE" .next/static/ → 0 résultat attendu

HEALTH CHECK POST-PREVIEW
  → Vérifier /api/health répond 200 sur le preview
  → Vérifier que la page d'accueil se charge sans erreur console
```

### Gate de sortie

```
Testing Developer :
  ☐ Tests unitaires : composants, hooks, schémas Zod — tous verts
  ☐ Tests intégration : GET/POST/PATCH — validation, auth, 403, nominal
  ☐ Tests RLS : isolation cross-foyer vérifiée (si story avec données de foyer)
  ☐ Couverture ≥ 70% — npm run test:coverage

Infrastructure Developer :
  ☐ CI pipeline vert (type-check + lint + tests + build)
  ☐ Migrations appliquées sur l'environnement preview
  ☐ Preview URL accessible et fonctionnelle
  ☐ /api/health retourne 200 sur le preview

SYNC C émis vers QA :
  ☐ URL preview communicée
  ☐ Résultats de tests communicés
  ☐ Confirmation migrations preview
```

---

## Étape 8 — QA Validation

### Rôle responsable
**QA Engineer**

### Inputs

| Input | Source |
|---|---|
| User Story + CA exacts | PO |
| SYNC C — URL preview + résultats tests | Testing Dev + Infra Dev (Étape 7) |
| Fiche(s) écran UX | UX Designer (Étape 3) |
| Checklists de validation par module | `testing_quality.md` §5.3 |

### Outputs

```
1. Rapport de validation complet
   Un rapport par story, au format standard
   Contenu : tableau CA (Pass/Fail) · tests automatisés · cas limites · bugs · décision

2. Fiches de bug (si applicable)
   Une fiche par CA non respecté
   Format standard avec étapes de reproduction reproductibles

3. Verdict formel
   "✅ Ready for Sprint Review" → story passe en Sprint Review
   "❌ Rejected — [raison précise]" → story retourne au Developer concerné
```

**Format du rapport de validation :**
```markdown
## Rapport de validation — [ID] — [Titre]

**Date**          : YYYY-MM-DD
**Preview**       : https://foyerapp-[slug].vercel.app
**Build**         : ✅ next build propre
**Décision**      : ✅ Ready for Sprint Review | ❌ Rejected

---

### Critères d'acceptation

| # | Critère (texte exact) | Résultat | Notes |
|---|---|---|---|
| CA-1 | [Texte] | ✅ Pass | — |
| CA-2 | [Texte] | ❌ Fail | [Description précise] |

---

### Tests automatisés

| Suite | Total | Pass | Fail | Couverture |
|---|---|---|---|---|
| Composants | [N] | [N] | [N] | [X]% |
| API Routes | [N] | [N] | [N] | — |
| RLS | [N] | [N] | [N] | — |

---

### Cas limites testés

- [ ] Mobile 375px (Chrome DevTools — iPhone SE)
- [ ] Erreur réseau simulée (DevTools → Network → Offline)
- [ ] Utilisateur non-membre du foyer → 403
- [ ] Champ à longueur maximale ([N] chars)
- [ ] [Cas spécifique à la story]

---

### Régression

- [ ] Suite complète exécutée
- [ ] Aucune régression | [BUG-N détecté]

---

### Bugs

| ID | Sévérité | Titre | CA violé |
|---|---|---|---|
| BUG-[N] | P[1-4] | [Titre court] | CA-[N] |

---

### Décision finale

✅ Ready for Sprint Review — tous les CA passent, aucune régression.
```

### Règles d'exécution

```
PRÉREQUIS AVANT DE COMMENCER
  → next build vert (vérifié dans CI)
  → Tests unitaires et d'intégration verts
  → Preview URL accessible et /api/health → 200
  Si un prérequis échoue : signal au Developer concerné — tests QA suspendus

VALIDATION PAR CA
  → Chaque CA testé individuellement — un résultat Pass ou Fail explicite
  → Texte exact du CA copié dans le rapport — jamais paraphrasé
  → Un seul CA en Fail suffit pour rejeter la story

VALIDATION MANUELLE OBLIGATOIRE
  → Mobile 375px : DevTools Chrome, simulation iPhone SE
  → Erreur réseau : DevTools → Network → Offline pendant une action
  → Navigation clavier : Tab, Shift+Tab, Enter, Escape sur les formulaires et modales
  → Messages d'erreur : vérifier role="alert" ou aria-live sur les erreurs inline

ISOLATION MULTI-TENANT
  → Tester depuis un compte d'un foyer différent pour toute story FOYER/TASK/SHOP
  → Tentative d'accès aux données d'un autre foyer → 403 attendu
  → Un bug d'isolation = P1 Bloquant — signal immédiat au SM, pas en fin de rapport

SÉVÉRITÉ DES BUGS
  P1 Bloquant  : isolation cassée, fonctionnalité principale inaccessible
  P2 Majeur    : feedback absent, rollback manquant, état loading infini
  P3 Mineur    : gêne légère, contournable, pas de blocage
  P4 Cosmétique: visuel uniquement, aucun impact fonctionnel

RÈGLE DE VERDICT
  "Ready for Sprint Review" uniquement si :
  → TOUS les CA sont Pass
  → Aucun bug P1 ou P2
  → Aucune régression sur les stories précédentes
  → next build vert

  "Rejected" si :
  → Au moins 1 CA est Fail
  → Au moins 1 bug P1 ou P2
  → Une régression est introduite
```

### Gate de sortie

```
☐ Rapport de validation rédigé au format standard
☐ Chaque CA documenté avec résultat Pass ✅ ou Fail ❌
☐ Mobile 375px vérifié
☐ Erreur réseau simulée vérifiée
☐ Isolation multi-tenant vérifiée (si applicable)
☐ Suite complète exécutée (régression)
☐ Bugs documentés avec fiches complètes
☐ Verdict formel prononcé : "Ready for Sprint Review" ou "Rejected"
```

---

## Étape 9 — Sprint Review

### Rôle responsable
**Product Owner** (verdict final) · **Scrum Master** (animation) · tous les agents (participants)

### Inputs

| Input | Source |
|---|---|
| Stories "Ready for Sprint Review" | QA Engineer (Étape 8) |
| Rapports de validation QA | QA Engineer |
| Tableau de bord du sprint | SM (mis à jour tout au long) |
| Métriques qualité | Testing Developer |

### Outputs

```
1. Verdicts PO par story
   "✅ Accepted" ou "❌ Rejected — [raison]" pour chaque story présentée

2. Rapport de Sprint Review
   Contenu : Sprint Goal atteint ? · vélocité réalisée · taux d'acceptance · actions

3. Backlog mis à jour post-Review
   Stories acceptées : statut Done
   Stories rejetées : retour BACKLOG avec correction story créée

4. Métriques sprint
   Vélocité, taux d'acceptance, bugs, couverture — partagés avec l'équipe
```

**Format du rapport de Sprint Review :**
```markdown
## Sprint Review — Sprint [N] — [Date]

**Sprint Goal** : [Rappel]
**Atteint** : ✅ Oui / ❌ Partiellement / ❌ Non

---

### Vélocité

| Planifié | Réalisé | Taux |
|---|---|---|
| [X] pts | [Y] pts | [Z]% |

---

### Verdicts

| Story | Points | Verdict | Justification |
|---|---|---|---|
| [ID] — [Titre] | [N] | ✅ Accepted | — |
| [ID] — [Titre] | [N] | ❌ Rejected | CA-[N] non respecté |

---

### Métriques qualité

| Métrique | Valeur | Cible |
|---|---|---|
| Taux acceptance 1er coup | [X]% | ≥ 80% |
| Bugs P1/P2 | [N] | 0 P1 / ≤ 1 P2 |
| Couverture tests | [X]% | ≥ 70% |

---

### Actions post-Review

Stories rejetées repriorisées : [liste]
Stories de correction créées : [liste]
```

### Règles d'exécution

```
CRITÈRES D'ACCEPTANCE PO
  → "Accepted" uniquement si TOUS les CA sont vérifiés (rapport QA)
  → "Rejected" toujours avec le CA précis non respecté
  → Le PO ne peut pas négocier les CA en Review — ils ont été définis avant le sprint
  → Le PO ne peut pas accepter si le DoD global n'est pas satisfait
    (next build, lint, tests passants, code review faite)

STORIES REJETÉES
  → Retournent au backlog avec statut BACKLOG
  → Une story de correction est créée avec le CA manquant précisé
  → Elle est repriorisée par le PO pour le sprint suivant

CALCUL DE LA VÉLOCITÉ
  → Vélocité = somme des points des stories Accepted uniquement
  → Stories partiellement faites = 0 points (pas de points partiels)
  → La vélocité sert de base pour le prochain Sprint Planning

ENCHAÎNEMENT REVIEW → RETRO
  → La Review précède toujours la Retrospective
  → Pas de Retrospective sur un sprint dont la Review n'est pas terminée
```

### Gate de sortie

```
☐ Verdict PO prononcé pour chaque story (Accepted ou Rejected)
☐ Rapport de Sprint Review produit
☐ Vélocité calculée et documentée
☐ Backlog mis à jour (stories Done / retour BACKLOG + corrections créées)
☐ Métriques qualité partagées avec l'équipe
☐ Retrospective planifiée (agenda prêt)
```

---

## Récapitulatif — Gates de passage

```
ÉTAPE 1 — SPRINT PLANNING
  → Toutes les stories sélectionnées sont Ready
  → Somme des points ≤ capacité calculée
  → Plan de tâches produit pour chaque story

ÉTAPE 2 — STORY ANALYSIS
  → Checklist INVEST 7/7 satisfaite
  → CA d'isolation + CA d'erreur réseau présents
  → Dépendances confirmées Done

ÉTAPE 3 — UX DESIGN
  → 5 états spécifiés pour chaque écran
  → Zones de tap ≥ 44×44px, aria-labels, adaptation desktop

ÉTAPE 4 — DATABASE DESIGN
  → Migration testée localement, RLS + 4 policies, types régénérés
  → SYNC A émis

ÉTAPE 5 — BACKEND IMPLEMENTATION
  → next build propre, chaîne sécurité complète, SYNC B émis

ÉTAPE 6 — FRONTEND IMPLEMENTATION
  → next build propre, 5 états, optimistic update, mobile 375px vérifié

ÉTAPE 7 — AUTOMATED TESTING
  → Suite tests verte, couverture ≥ 70%, preview accessible
  → SYNC C émis vers QA

ÉTAPE 8 — QA VALIDATION
  → Rapport de validation avec tous CA Pass
  → Aucun bug P1/P2, aucune régression
  → Verdict "Ready for Sprint Review"

ÉTAPE 9 — SPRINT REVIEW
  → PO accepte OU rejette avec justification précise
  → Vélocité calculée, backlog mis à jour
```

---

*Ce document est le guide d'exécution opérationnel du cycle de sprint pour le système AI Scrum de FoyerApp. Il est mis à jour à chaque évolution significative du processus, de la stack technique ou des règles de qualité de l'équipe.*
