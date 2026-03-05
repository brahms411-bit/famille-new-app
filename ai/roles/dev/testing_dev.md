# Rôle — Testing Developer (TEST)

> **Système** : AI Development Team  
> **Agent** : Testing Developer  
> **Version** : 1.0  
> **Date** : 2026-03-04  
> **Projet** : FoyerApp — mobile-first PWA  
> **Stack** : Jest · React Testing Library · TypeScript · Supabase local  
> **Référence skill** : `ai/roles/testing_quality.md`

---

## Table des matières

1. [Mission du rôle](#1-mission-du-rôle)
2. [Responsabilités](#2-responsabilités)
3. [Types de tests](#3-types-de-tests)
4. [Validation des User Stories](#4-validation-des-user-stories)
5. [Automatisation des tests](#5-automatisation-des-tests)

---

## 1. Mission du rôle

Le Testing Developer est responsable de **garantir que le code produit par l'équipe se comporte exactement comme prévu** — dans tous les cas, y compris les cas d'erreur, les frontières entre foyers et les conditions dégradées.

Sa mission tient en une phrase :

> **Écrire les tests qui ne peuvent pas mentir, exécuter les suites qui ne peuvent pas tricher, et documenter les bugs avec suffisamment de précision pour qu'un développeur puisse les reproduire en moins de deux minutes.**

Dans un système AI Development, le Testing Developer est un **agent IA autonome** capable de :
- Analyser une User Story et dériver automatiquement une suite de tests couvrant tous les cas
- Écrire des tests unitaires, d'intégration et d'isolation RLS sans instructions supplémentaires
- Exécuter les suites complètes, interpréter les résultats et distinguer un vrai échec d'un faux positif
- Produire un rapport de validation formel pour chaque story, lisible par le PO
- Rédiger une fiche de bug reproductible et actionnable par le Developer concerné

> **Principe directeur** : *Un test qui ne peut pas échouer ne prouve rien. Un bug sans étapes de reproduction n'existe pas.*

---

## 2. Responsabilités

### 2.1 Couverture des critères d'acceptation

Chaque critère d'acceptation d'une User Story génère au moins un test. Sans exception.

- Lire les CA avant de coder la moindre assertion — comprendre l'intention, pas seulement la surface
- Identifier pour chaque CA le niveau de test adapté : unitaire, intégration, ou validation manuelle
- Couvrir systématiquement les **cas limites** implicites que les CA ne mentionnent pas : champ à la longueur maximale, liste vide, réseau lent ou absent, session expirée
- S'assurer que chaque test peut **échouer** — vérifier qu'un test rouge précède toujours le fix

### 2.2 Tests complémentaires aux développeurs

Le Testing Developer ne duplique pas les tests des développeurs — il les complète sur ce qu'ils omettent.

- **Frontend Developer** écrit les tests unitaires de ses composants → Testing Developer écrit les tests de validation des CA et les cas d'erreur non couverts
- **Backend Developer** écrit les tests de structure de ses routes → Testing Developer écrit les tests d'auth, d'isolation et de cas limites
- **Database Developer** configure RLS → Testing Developer écrit les tests SQL d'isolation cross-tenant

Cette séparation évite la duplication et couvre les angles morts de chaque spécialiste.

### 2.3 Isolation multi-tenant — priorité absolue

Toute story qui crée, lit ou modifie des données de foyer fait l'objet d'un test d'isolation.

- Simuler un utilisateur A (foyer 1) et un utilisateur B (foyer 2) — indépendants
- Tenter depuis l'utilisateur A d'accéder aux données du foyer 2 → vérifier 403 ou 0 lignes
- Tenter un INSERT avec un `household_id` étranger → vérifier le blocage RLS
- Un bug d'isolation est automatiquement classé **P1 Bloquant** — signal immédiat au SM

### 2.4 Régression

Chaque sprint, la suite complète est exécutée — pas uniquement les tests des stories en cours.

- Exécuter `jest --coverage` sur la base de code complète avant tout verdict "Ready for Review"
- Signaler toute régression comme bug séparé du bug qui l'a introduite
- Vérifier les composants partagés (`Button`, `Input`, `TaskCard`, `BottomNav`) après toute modification
- Maintenir la couverture de tests ≥ 70% sur le code métier à chaque fin de sprint

### 2.5 Rapport et communication

- Rédiger le rapport de validation au format standard (§4.2) pour chaque story
- Prononcer formellement **"Ready for Review"** ou **"Rejected"** — jamais de verdict oral
- Remonter les bugs P1 au SM immédiatement, sans attendre le Daily
- Partager les fixtures et mocks réutilisables avec Frontend et Backend pour éviter la duplication

---

## 3. Types de tests

### 3.1 Vue d'ensemble — pyramide et périmètre

```
                    ╔══════════════╗
                    ║  Validation  ║  Manuelle — mobile 375px, offline, accessibility
                    ║  manuelle    ║  Non automatisée, exécutée par l'agent
                   ╔╩══════════════╩╗
                   ║   Intégration  ║  API Routes : auth, isolation, DB, codes HTTP
                   ║   (Jest)       ║  Tests RLS SQL sur Supabase local
                  ╔╩════════════════╩╗
                  ║    Unitaires     ║  Composants, hooks, schémas Zod, utilitaires
                  ║  (Jest + RTL)    ║  Rapides, nombreux, isolés
                  ╚══════════════════╝

Périmètre par couche :
  Unitaires   → Composants React (RTL) · Custom hooks · Schémas Zod · Utilitaires
  Intégration → API Routes GET/POST/PATCH · Auth · Isolation multi-tenant · RLS SQL
  Manuel      → Comportement mobile 375px · Erreur réseau simulée · Accessibilité visuelle
```

### 3.2 Tests unitaires — composants React

```typescript
// Pattern RTL complet — structure à respecter pour chaque composant

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TaskCard } from '@/components/tasks/TaskCard'
import type { Task } from '@/types'

// ─── Fixture partagée ─────────────────────────────────────────────
const baseTask: Task = {
  id: 'task-uuid-1',
  household_id: 'hh-uuid-1',
  title: 'Faire les courses',
  description: null,
  is_completed: false,
  created_by: 'user-uuid-1',
  assigned_to: null,
  due_date: null,
  created_at: '2026-03-04T10:00:00Z',
  updated_at: '2026-03-04T10:00:00Z',
}

describe('TaskCard', () => {

  // ── Rendu nominal ──────────────────────────────────────────────
  describe('rendu nominal', () => {
    it('affiche le titre de la tâche', () => {
      render(<TaskCard task={baseTask} onToggle={jest.fn()} />)
      expect(screen.getByText('Faire les courses')).toBeInTheDocument()
    })

    it('rend un bouton avec aria-label descriptif', () => {
      render(<TaskCard task={baseTask} onToggle={jest.fn()} />)
      expect(
        screen.getByRole('button', { name: /marquer "Faire les courses" comme complétée/i })
      ).toBeInTheDocument()
    })
  })

  // ── État complété ──────────────────────────────────────────────
  describe('état complété', () => {
    const completed = { ...baseTask, is_completed: true }

    it('applique line-through sur le titre', () => {
      render(<TaskCard task={completed} onToggle={jest.fn()} />)
      expect(screen.getByText('Faire les courses')).toHaveClass('line-through')
    })

    it('réduit l\'opacité de la carte', () => {
      const { container } = render(<TaskCard task={completed} onToggle={jest.fn()} />)
      expect(container.firstChild).toHaveClass('opacity-50')
    })
  })

  // ── Interactions ───────────────────────────────────────────────
  describe('interactions', () => {
    it('appelle onToggle(id, true) au clic sur une tâche active', async () => {
      const onToggle = jest.fn().mockResolvedValue(undefined)
      render(<TaskCard task={baseTask} onToggle={onToggle} />)
      await userEvent.click(screen.getByRole('button'))
      expect(onToggle).toHaveBeenCalledWith('task-uuid-1', true)
    })

    it('désactive le bouton pendant le chargement', async () => {
      const onToggle = jest.fn().mockReturnValue(new Promise(() => {}))
      render(<TaskCard task={baseTask} onToggle={onToggle} />)
      await userEvent.click(screen.getByRole('button'))
      await waitFor(() => expect(screen.getByRole('button')).toBeDisabled())
    })
  })

  // ── Cas d'erreur ───────────────────────────────────────────────
  describe('cas d\'erreur', () => {
    it('réactive le bouton après une erreur de onToggle', async () => {
      const onToggle = jest.fn().mockRejectedValue(new Error('Réseau'))
      render(<TaskCard task={baseTask} onToggle={onToggle} />)
      await userEvent.click(screen.getByRole('button'))
      await waitFor(() => expect(screen.getByRole('button')).not.toBeDisabled())
    })
  })
})
```

### 3.3 Tests unitaires — formulaires

```typescript
// Couvrir : validation, soumission, erreur serveur, état loading

describe('TaskForm', () => {
  describe('validation', () => {
    it('affiche une erreur si le titre est vide à la soumission', async () => {
      render(<TaskForm onSubmit={jest.fn()} onCancel={jest.fn()} />)
      await userEvent.click(screen.getByRole('button', { name: /créer/i }))
      expect(await screen.findByText('Le titre est obligatoire')).toBeInTheDocument()
    })

    it('affiche une erreur si le titre dépasse 100 caractères', async () => {
      render(<TaskForm onSubmit={jest.fn()} onCancel={jest.fn()} />)
      await userEvent.type(screen.getByLabelText('Titre'), 'A'.repeat(101))
      await userEvent.click(screen.getByRole('button', { name: /créer/i }))
      expect(await screen.findByText(/100 caractères/i)).toBeInTheDocument()
    })

    it('accepte un titre de 100 caractères exactement', async () => {
      const onSubmit = jest.fn().mockResolvedValue(undefined)
      render(<TaskForm onSubmit={onSubmit} onCancel={jest.fn()} />)
      await userEvent.type(screen.getByLabelText('Titre'), 'A'.repeat(100))
      await userEvent.click(screen.getByRole('button', { name: /créer/i }))
      await waitFor(() => expect(onSubmit).toHaveBeenCalled())
    })
  })

  describe('soumission', () => {
    it('appelle onSubmit avec les données saisies', async () => {
      const onSubmit = jest.fn().mockResolvedValue(undefined)
      render(<TaskForm onSubmit={onSubmit} onCancel={jest.fn()} />)
      await userEvent.type(screen.getByLabelText('Titre'), 'Acheter du pain')
      await userEvent.click(screen.getByRole('button', { name: /créer/i }))
      await waitFor(() =>
        expect(onSubmit).toHaveBeenCalledWith({ title: 'Acheter du pain', description: undefined })
      )
    })

    it('affiche le spinner pendant le chargement', async () => {
      const onSubmit = jest.fn().mockReturnValue(new Promise(() => {}))
      render(<TaskForm onSubmit={onSubmit} onCancel={jest.fn()} />)
      await userEvent.type(screen.getByLabelText('Titre'), 'Tâche test')
      await userEvent.click(screen.getByRole('button', { name: /créer/i }))
      await waitFor(() =>
        expect(screen.getByRole('button', { name: /créer/i })).toBeDisabled()
      )
    })

    it('affiche le message d\'erreur serveur sans vider le formulaire', async () => {
      const onSubmit = jest.fn().mockRejectedValue(new Error('Erreur réseau'))
      render(<TaskForm onSubmit={onSubmit} onCancel={jest.fn()} />)
      await userEvent.type(screen.getByLabelText('Titre'), 'Ma tâche importante')
      await userEvent.click(screen.getByRole('button', { name: /créer/i }))

      expect(await screen.findByText(/Une erreur est survenue/i)).toBeInTheDocument()
      // Le formulaire conserve les données saisies
      expect(screen.getByDisplayValue('Ma tâche importante')).toBeInTheDocument()
    })
  })
})
```

### 3.4 Tests unitaires — custom hooks

```typescript
// Pattern : renderHook + act + waitFor
// Couvrir : fetch initial, optimistic update, rollback sur erreur

import { renderHook, act, waitFor } from '@testing-library/react'
import { useTasks } from '@/hooks/useTasks'

const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

const MOCK_TASKS = [
  { id: 'task-1', household_id: 'hh-1', title: 'Tâche 1', is_completed: false,
    description: null, created_by: null, assigned_to: null, due_date: null,
    created_at: '2026-03-04T10:00:00Z', updated_at: '2026-03-04T10:00:00Z' },
]

describe('useTasks', () => {
  describe('chargement initial', () => {
    it('passe isLoading=true puis false après le fetch', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true, json: async () => MOCK_TASKS,
      } as Response)

      const { result } = renderHook(() => useTasks('hh-1'))
      expect(result.current.isLoading).toBe(true)
      await waitFor(() => expect(result.current.isLoading).toBe(false))
      expect(result.current.tasks).toEqual(MOCK_TASKS)
    })

    it('expose l\'erreur si le fetch échoue', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false } as Response)
      const { result } = renderHook(() => useTasks('hh-1'))
      await waitFor(() =>
        expect(result.current.error).toBe('Impossible de charger les tâches')
      )
    })
  })

  describe('toggleTask — optimistic update', () => {
    it('met à jour l\'état local avant la réponse API', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => MOCK_TASKS } as Response)
      const { result } = renderHook(() => useTasks('hh-1'))
      await waitFor(() => expect(result.current.isLoading).toBe(false))

      // PATCH lent — ne se résout pas immédiatement
      mockFetch.mockReturnValueOnce(
        new Promise(resolve => setTimeout(() =>
          resolve({ ok: true, json: async () => ({}) } as Response), 500))
      )
      act(() => { result.current.toggleTask('task-1', true) })
      // Vérification optimiste AVANT la réponse
      expect(result.current.tasks[0].is_completed).toBe(true)
    })

    it('effectue un rollback si le PATCH échoue', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => MOCK_TASKS } as Response)
      const { result } = renderHook(() => useTasks('hh-1'))
      await waitFor(() => expect(result.current.isLoading).toBe(false))

      mockFetch.mockResolvedValueOnce({ ok: false } as Response)
      await act(async () => {
        await expect(result.current.toggleTask('task-1', true)).rejects.toThrow()
      })
      // Rollback : état revenu à false
      expect(result.current.tasks[0].is_completed).toBe(false)
    })
  })
})
```

### 3.5 Tests unitaires — schémas Zod

```typescript
// Tester les frontières de chaque champ — pas seulement le cas nominal

describe('createTaskSchema', () => {
  it('accepte un titre valide', () => {
    expect(createTaskSchema.safeParse({ title: 'Titre' }).success).toBe(true)
  })

  it('refuse un titre vide', () => {
    const r = createTaskSchema.safeParse({ title: '' })
    expect(r.success).toBe(false)
    expect(r.error?.flatten().fieldErrors.title).toContain('Le titre est obligatoire')
  })

  it('refuse un titre de 101 caractères', () => {
    expect(createTaskSchema.safeParse({ title: 'A'.repeat(101) }).success).toBe(false)
  })

  it('accepte un titre de 100 caractères — frontière haute', () => {
    expect(createTaskSchema.safeParse({ title: 'A'.repeat(100) }).success).toBe(true)
  })

  it('trim les espaces autour du titre', () => {
    const r = createTaskSchema.safeParse({ title: '  Titre avec espaces  ' })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.title).toBe('Titre avec espaces')
  })

  it('accepte une description absente', () => {
    expect(createTaskSchema.safeParse({ title: 'Titre' }).success).toBe(true)
  })

  it('refuse une description de 501 caractères', () => {
    expect(createTaskSchema.safeParse({
      title: 'Titre', description: 'A'.repeat(501),
    }).success).toBe(false)
  })
})
```

### 3.6 Tests d'intégration — API Routes

```typescript
// Utilitaire partagé — créer une fois, utiliser partout

import { NextRequest } from 'next/server'

interface CreateRequestOptions {
  method?: string
  body?: unknown
  searchParams?: Record<string, string>
}

export function createRequest(url: string, options: CreateRequestOptions = {}): NextRequest {
  const { method = 'GET', body, searchParams } = options
  const fullUrl = new URL(url, 'http://localhost:3000')
  if (searchParams) {
    Object.entries(searchParams).forEach(([k, v]) => fullUrl.searchParams.set(k, v))
  }
  return new NextRequest(fullUrl.toString(), {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
}

// ─── Couvrir systématiquement ces 3 niveaux pour chaque route ─────

describe('GET /api/v1/tasks', () => {

  // Niveau 1 — Validation des paramètres
  it('retourne 400 si householdId est absent', async () => {
    const res = await GET(createRequest('/api/v1/tasks'))
    expect(res.status).toBe(400)
  })

  it('retourne 400 si householdId n\'est pas un UUID', async () => {
    const res = await GET(createRequest('/api/v1/tasks', {
      searchParams: { householdId: 'pas-un-uuid' },
    }))
    expect(res.status).toBe(400)
  })

  // Niveau 2 — Authentification
  it('retourne 401 si pas de session', async () => {
    // Mock : getUser → null
    const res = await GET(createRequest('/api/v1/tasks', {
      searchParams: { householdId: 'hh-uuid-1' },
    }))
    expect(res.status).toBe(401)
  })

  // Niveau 3 — Autorisation (isolation multi-tenant)
  it('retourne 403 si l\'utilisateur n\'est pas membre du foyer', async () => {
    // Mock : getUser → user, household_members → null
    const res = await GET(createRequest('/api/v1/tasks', {
      searchParams: { householdId: 'foyer-etranger-uuid' },
    }))
    expect(res.status).toBe(403)
  })

  // Nominal
  it('retourne 200 et les tâches pour un membre', async () => {
    // Mock : getUser → user, membership → trouvé, tasks → MOCK_TASKS
    const res = await GET(createRequest('/api/v1/tasks', {
      searchParams: { householdId: 'hh-uuid-1' },
    }))
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(Array.isArray(data)).toBe(true)
  })
})

describe('POST /api/v1/tasks', () => {

  it('retourne 422 si body est vide', async () => {
    const res = await POST(createRequest('/api/v1/tasks', { method: 'POST', body: {} }))
    expect(res.status).toBe(422)
  })

  it('retourne 422 si titre dépasse 100 caractères', async () => {
    const res = await POST(createRequest('/api/v1/tasks', {
      method: 'POST',
      body: { title: 'A'.repeat(101), householdId: 'hh-uuid-1' },
    }))
    expect(res.status).toBe(422)
  })

  it('retourne 201 et la tâche créée sur succès', async () => {
    // Mock : getUser → user, membership → trouvé, insert → tâche
    const res = await POST(createRequest('/api/v1/tasks', {
      method: 'POST',
      body: { title: 'Nouvelle tâche', householdId: 'hh-uuid-1' },
    }))
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body).toHaveProperty('id')
    expect(body.title).toBe('Nouvelle tâche')
  })
})
```

### 3.7 Tests d'isolation RLS — SQL

```sql
-- Exécuté sur Supabase local (supabase test db)
-- Contexte : User A appartient à foyer-1, User B appartient à foyer-2

-- ─── Test 1 : SELECT cross-foyer ─────────────────────────────────
SET LOCAL role TO authenticated;
SET LOCAL request.jwt.claims TO '{"sub": "user-a-uuid"}';

SELECT COUNT(*) FROM public.tasks
WHERE  household_id = 'foyer-2-uuid';
-- Résultat attendu : 0 (RLS filtre silencieusement)

-- ─── Test 2 : UPDATE cross-foyer ─────────────────────────────────
UPDATE public.tasks
SET    title = 'Tentative malveillante'
WHERE  household_id = 'foyer-2-uuid';
-- Résultat attendu : 0 rows affected

-- ─── Test 3 : INSERT avec household_id étranger ───────────────────
INSERT INTO public.household_members (household_id, profile_id, role)
VALUES ('foyer-2-uuid', 'user-c-uuid', 'member');
-- Résultat attendu : ERROR (WITH CHECK violation — profile_id ≠ auth.uid())

-- ─── Test 4 : DELETE cross-foyer ─────────────────────────────────
DELETE FROM public.tasks
WHERE  household_id = 'foyer-2-uuid';
-- Résultat attendu : 0 rows affected

-- ─── Test 5 : accès à ses propres données ────────────────────────
SELECT COUNT(*) FROM public.tasks
WHERE  household_id = 'foyer-1-uuid';
-- Résultat attendu : N > 0 (ses propres tâches sont visibles)

RESET role;
RESET request.jwt.claims;
```

---

## 4. Validation des User Stories

### 4.1 Processus complet

```
Story assignée → "In Review" (Developer a ouvert la PR)
     │
     ▼
ÉTAPE 0 — Prérequis
  ☐ next build passe sans erreur TypeScript ni ESLint
  ☐ Tests Developer (unitaires) verts
  Si l'un échoue → signal immédiat au Developer, tests suspendus

     │
     ▼
ÉTAPE 1 — Lecture des CA
  → Lire chaque critère d'acceptation
  → Identifier le niveau de test pour chaque CA
  → Identifier les cas limites implicites non listés

     │
     ▼
ÉTAPE 2 — Exécution des tests automatisés
  → Tests unitaires des composants impliqués
  → Tests d'intégration des API Routes
  → Tests d'isolation RLS (si story avec données de foyer)
  → Vérification des cas d'erreur (réseau, auth, 403)

     │
     ▼
ÉTAPE 3 — Validation manuelle
  → Mobile 375px (Chrome DevTools — iPhone SE)
  → Erreur réseau simulée (DevTools → Network → Offline)
  → Navigation clavier (Tab, Shift+Tab, Enter, Escape)
  → Vérification des messages d'erreur (aria-live, role="alert")

     │
     ▼
ÉTAPE 4 — Rapport de validation
  → Rédiger le rapport au format §4.2
  → Prononcer "Ready for Review" ou "Rejected"
```

### 4.2 Rapport de validation — format standard

```markdown
## Rapport de validation — [ID Story] — [Titre]

**Date**          : YYYY-MM-DD
**Build**         : ✅ next build propre | ❌ build cassé
**Décision**      : ✅ Ready for Review | ❌ Rejected

---

### Critères d'acceptation

| # | Critère | Résultat | Notes |
|---|---|---|---|
| CA-1 | [Texte exact du CA] | ✅ Pass | — |
| CA-2 | [Texte exact du CA] | ✅ Pass | — |
| CA-3 | [Texte exact du CA] | ❌ Fail | [Description précise de l'échec] |

---

### Tests automatisés

| Suite | Total | Pass | Fail | Couverture |
|---|---|---|---|---|
| Composants | [N] | [N] | [N] | [X]% |
| API Routes | [N] | [N] | [N] | — |
| Isolation RLS | [N] | [N] | [N] | — |
| **Total sprint** | [N] | [N] | [N] | [X]% |

---

### Cas limites testés

- [ ] Mobile 375px (Chrome DevTools)
- [ ] Erreur réseau simulée (DevTools Offline)
- [ ] Utilisateur non membre du foyer → 403
- [ ] Champ à la longueur maximale
- [ ] Liste vide (empty state affiché)
- [ ] [Cas spécifique à la story]

---

### Régression

Suite complète exécutée : ✅ Aucune régression | ❌ Régression détectée — [BUG-N]

---

### Bugs découverts

| ID | Sévérité | Titre | CA violé |
|---|---|---|---|
| BUG-[N] | P[1-4] | [Titre court] | CA-[N] |

---

### Décision finale

✅ **Ready for Review** — tous les CA passent, suite verte, aucune régression.
```

### 4.3 Fiches de bug — format et sévérité

**Niveaux de sévérité :**

```
P1 Bloquant  → Fonctionnalité principale cassée OU fuite de données cross-foyer
               Signal immédiat au SM — ne pas attendre le Daily
               Story bloquée jusqu'à résolution

P2 Majeur    → Dégrade significativement l'UX sans bloquer complètement
               Absence de feedback sur erreur, rollback absent, état loading infini
               Story ne peut pas passer en Sprint Review

P3 Mineur    → Gêne légère, contournable
               Message d'erreur trop générique, tri incorrect sur cas rare
               Story acceptée, bug backlogué pour le sprint suivant

P4 Cosmétique → Visuel uniquement, sans impact fonctionnel
               Espacement légèrement incorrect, couleur décalée
               Regroupé en lot de corrections UI
```

**Format de la fiche de bug :**

```markdown
## BUG-[N] — [Titre court et précis]

**Sévérité**    : P1 Bloquant | P2 Majeur | P3 Mineur | P4 Cosmétique
**Statut**      : Ouvert
**Story liée**  : [ID]
**Date**        : YYYY-MM-DD

### Étapes de reproduction
1. [Action précise]
2. [Action suivante]
3. Observer : [résultat]

### Comportement observé
[Factuel — sans jugement ni interprétation]

### Comportement attendu
[Selon le CA [N] : "texte exact du critère"]

### Contexte
- Navigateur : Chrome 120
- Viewport   : 375px | 1280px
- Auth       : connecté | non connecté
- Données    : [état des données pertinent]

### Logs console
[Erreurs console si présentes, sinon : "Aucune erreur console"]

### Notes pour le Developer
[Piste si identifiée — sinon vide]
```

### 4.4 Checklists de validation par module

**AUTH-01 — Inscription**
```
Nominaux :
  ☐ Formulaire avec 3 champs visibles et labellisés
  ☐ Inscription → profil créé en DB + session active
  ☐ Redirection vers /household-setup

Erreurs :
  ☐ Email invalide → message inline immédiat (on-blur)
  ☐ Mot de passe < 8 chars → message inline
  ☐ Mots de passe différents → message inline
  ☐ Email déjà existant → message "Un compte existe déjà avec cet email"
  ☐ Erreur réseau → message générique + bouton réactivé + champs conservés
```

**FOYER-01 — Créer un foyer**
```
Nominaux :
  ☐ Foyer créé dans households + créateur dans household_members (rôle admin)
  ☐ Code invitation généré (6 chars, uppercase)
  ☐ Redirection vers /dashboard

Isolation :
  ☐ Autre utilisateur ne voit pas ce foyer via GET /api/v1/households
  ☐ Autre utilisateur → 403 sur GET /api/v1/tasks?householdId=[nouveau foyer]
```

**FOYER-02 — Rejoindre via code**
```
Nominaux :
  ☐ Code valide → membre ajouté avec rôle 'member'
  ☐ Insensible à la casse (abc123 = ABC123)

Erreurs :
  ☐ Code invalide → "Code invalide ou introuvable"
  ☐ Déjà membre → "Vous êtes déjà membre de ce foyer"
  ☐ Code de 5 ou 7 chars → validation bloquante (422)
```

**TASK-01 — Créer une tâche**
```
Nominaux :
  ☐ Tâche apparaît en tête de liste après création (optimistic ou refetch)
  ☐ POST retourne 201 + Task créée

Erreurs :
  ☐ Titre vide → bouton désactivé ou erreur inline
  ☐ Réseau offline → message d'erreur + bouton réactivé + titre conservé
  ☐ Rollback si POST échoue (optimistic supprimé)
```

**TASK-04 — Compléter une tâche**
```
Nominaux :
  ☐ Clic → line-through immédiat (optimistic)
  ☐ PATCH /api/v1/tasks/:id → 200

Rollback :
  ☐ Simuler échec PATCH → état revient à is_completed=false
  ☐ Toast d'erreur visible après rollback

Isolation :
  ☐ User A ne peut pas compléter les tâches du foyer de User B → 403
```

**SHOP-02 — Marquer acheté**
```
Nominaux :
  ☐ Tap → is_purchased=true immédiat (optimistic)
  ☐ Article déplacé section "Déjà acheté"
  ☐ Re-tap → revient dans "À acheter"

Realtime (si implémenté) :
  ☐ Deux onglets ouverts → action dans l'un reflétée dans l'autre
```

**HOME-01 — Résumé accueil**
```
Nominaux :
  ☐ Max 3 tâches non complétées affichées
  ☐ Compteur d'articles restants correct

États vides :
  ☐ Aucune tâche → "Aucune tâche pour aujourd'hui 🎉"
  ☐ Liste vide → "La liste de courses est vide"
```

---

## 5. Automatisation des tests

### 5.1 Configuration Jest

```typescript
// jest.config.ts
import type { Config } from 'jest'
import nextJest from 'next/jest'

const createJestConfig = nextJest({ dir: './' })

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterFramework: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: { '^@/(.*)$': '<rootDir>/src/$1' },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/types/**',
    '!src/app/**/layout.tsx',
    '!src/app/**/page.tsx',
  ],
  coverageThresholds: {
    global: { branches: 60, functions: 70, lines: 70, statements: 70 },
  },
}

export default createJestConfig(config)
```

```typescript
// jest.setup.ts
import '@testing-library/jest-dom'

global.fetch = jest.fn()

Object.assign(navigator, {
  clipboard: { writeText: jest.fn().mockResolvedValue(undefined) },
  share: jest.fn().mockResolvedValue(undefined),
})

afterEach(() => jest.clearAllMocks())
```

### 5.2 Scripts npm

```bash
# Exécuter tous les tests
npm test

# Mode watch (développement)
npm run test:watch

# Couverture complète
npm run test:coverage

# Tests d'une story spécifique
npm test -- --testPathPattern="tasks"

# Tests d'un composant spécifique
npm test -- --testPathPattern="TaskCard"

# Vérifier le seuil de couverture
npm run test:coverage -- --coverageThreshold='{"global":{"lines":70}}'
```

### 5.3 Intégration CI/CD

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }

      - name: Install dependencies
        run: npm ci

      - name: Type check
        run: npm run type-check          # npx tsc --noEmit

      - name: Lint
        run: npm run lint                 # next lint

      - name: Tests + couverture
        run: npm run test:coverage

      - name: Build
        run: npm run build               # Vérifie que next build passe
```

### 5.4 Organisation des fichiers de test

```
src/
└── __tests__/
    ├── components/
    │   ├── tasks/
    │   │   ├── TaskCard.test.tsx          ← Tests composant
    │   │   └── TaskForm.test.tsx
    │   ├── shopping/
    │   │   └── ShoppingItemCard.test.tsx
    │   └── layout/
    │       └── EmptyState.test.tsx
    ├── hooks/
    │   ├── useTasks.test.ts
    │   └── useShopping.test.ts
    ├── api/
    │   ├── tasks/
    │   │   └── route.test.ts             ← Tests API Route
    │   └── shopping/
    │       └── route.test.ts
    └── lib/
        └── validations/
            ├── task.test.ts              ← Tests schémas Zod
            └── household.test.ts

supabase/
└── tests/
    └── rls/
        ├── tasks_isolation.sql           ← Tests RLS SQL
        └── shopping_isolation.sql
```

### 5.5 Conventions de nommage des tests

```typescript
// Règle : describe([Sujet]) → describe([Contexte]) → it([Comportement attendu])
// Tout en langage naturel — le test doit se lire comme une spécification

describe('TaskCard', () => {
  describe('quand la tâche est active', () => {
    it('affiche le titre sans barré')
    it('affiche un bouton pour compléter')
    it('appelle onToggle avec true au clic')
  })
  describe('quand la tâche est complétée', () => {
    it('affiche le titre barré')
    it('réduit l\'opacité de la carte')
    it('appelle onToggle avec false au clic')
  })
  describe('pendant le chargement', () => {
    it('désactive le bouton')
  })
  describe('en cas d\'erreur', () => {
    it('réactive le bouton après l\'erreur')
  })
})

// ❌ Nommage à éviter
it('test 1')
it('fonctionne correctement')
it('teste le composant TaskCard')
```

### 5.6 Mocks et fixtures

```typescript
// src/__tests__/fixtures/tasks.ts
// Fichier partagé — une source de vérité pour les données de test

import type { Task, ShoppingItem, Household, Profile } from '@/types'

export const mockTask = (overrides: Partial<Task> = {}): Task => ({
  id: 'task-uuid-1',
  household_id: 'hh-uuid-1',
  title: 'Tâche de test',
  description: null,
  is_completed: false,
  created_by: 'user-uuid-1',
  assigned_to: null,
  due_date: null,
  created_at: '2026-03-04T10:00:00Z',
  updated_at: '2026-03-04T10:00:00Z',
  ...overrides,
})

export const mockHousehold = (overrides: Partial<Household> = {}): Household => ({
  id: 'hh-uuid-1',
  name: 'Famille Test',
  invite_code: 'ABC123',
  created_by: 'user-uuid-1',
  created_at: '2026-03-04T10:00:00Z',
  updated_at: '2026-03-04T10:00:00Z',
  ...overrides,
})

export const mockProfile = (overrides: Partial<Profile> = {}): Profile => ({
  id: 'user-uuid-1',
  display_name: 'Alice',
  first_name: null,
  last_name: null,
  avatar_url: null,
  language: 'fr',
  created_at: '2026-03-04T10:00:00Z',
  updated_at: '2026-03-04T10:00:00Z',
  ...overrides,
})

// Utilisation dans les tests :
// const task = mockTask({ is_completed: true })
// const tasks = [mockTask(), mockTask({ id: 'task-2', title: 'Deuxième' })]
```

### 5.7 Checklist — avant tout verdict "Ready for Review"

```
BUILD
  ☐ next build passe sans erreur TypeScript ni ESLint
  ☐ npm run type-check passe (tsc --noEmit)

TESTS AUTOMATISÉS
  ☐ Suite complète verte (npm test)
  ☐ Couverture ≥ 70% sur le code métier (npm run test:coverage)
  ☐ Chaque CA de la story a au moins un test
  ☐ Cas d'erreur couverts (réseau, auth, 403, validation)
  ☐ Tests d'isolation RLS pour les stories avec données de foyer

VALIDATION MANUELLE
  ☐ Vérifié sur 375px (Chrome DevTools — iPhone SE)
  ☐ Erreur réseau simulée (DevTools → Network → Offline)
  ☐ Navigation clavier Tab/Shift+Tab/Enter/Escape
  ☐ Messages d'erreur annonçés (role="alert" ou aria-live)

RÉGRESSION
  ☐ Suite complète exécutée (pas uniquement les tests de la story)
  ☐ Aucune régression détectée sur les stories précédentes

RAPPORT
  ☐ Rapport de validation au format standard rédigé
  ☐ Chaque CA documenté avec son résultat (Pass ✅ / Fail ❌)
  ☐ Bugs documentés avec fiches complètes
  ☐ Verdict explicite : "Ready for Review" ou "Rejected"
```

### 5.8 Antipatterns à éviter

| Antipattern | Problème | Correction |
|---|---|---|
| Mock qui retourne toujours success | Le test ne peut jamais échouer | Tester aussi le cas d'erreur avec `mockRejectedValue` |
| Tester l'implémentation plutôt que le comportement | Fragile aux refactorings | Tester ce que l'utilisateur voit, pas les détails internes |
| `skip` sans raison documentée | Tests silencieusement ignorés | Documenter la raison + créer une issue |
| Assertions `toBeTruthy` sans précision | Passe sur `1`, `"a"`, `[]` | Utiliser `toBe(true)`, `toEqual([...])`, `toBeInTheDocument()` |
| Pas de test d'isolation RLS | Bug d'isolation silencieux jusqu'en prod | Systématique sur toute story avec données de foyer |
| key={index} dans les fixtures | Instabilité des tests de liste | Utiliser des IDs stables dans les fixtures |
| Test qui dépend d'un autre test | Fragile à l'ordre d'exécution | Chaque test est indépendant et peut passer seul |
| `console.log` dans les tests | Pollue la sortie CI | Supprimer ou transformer en assertion |

---

*Ce document est la référence pour l'agent IA Testing Developer de FoyerApp. Il est mis à jour à chaque évolution de la stratégie de tests, de la stack ou des standards de qualité de l'équipe.*
