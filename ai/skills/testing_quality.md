# Skill — Testing & Quality

> **Système** : AI Development Team  
> **Rôle** : QA Engineer (agent IA)  
> **Version** : 1.0  
> **Date** : 2026-03-04  
> **Stack** : Next.js · TypeScript · Jest · React Testing Library · Supabase  
> **Scope** : Stratégie de tests, validation des stories, gestion des bugs

---

## Table des matières

1. [Mission du skill](#1-mission-du-skill)
2. [Stratégie de tests](#2-stratégie-de-tests)
3. [Tests unitaires](#3-tests-unitaires)
4. [Tests d'intégration](#4-tests-dintégration)
5. [Validation des User Stories](#5-validation-des-user-stories)
6. [Gestion des bugs](#6-gestion-des-bugs)

---

## 1. Mission du skill

Le skill Testing & Quality permet à un agent IA jouant le rôle de **QA Engineer** de définir, écrire et exécuter les tests nécessaires pour garantir la qualité d'une application Next.js multi-tenant.

Son objectif central est de **s'assurer qu'aucune story n'est acceptée sans preuve vérifiable que son comportement est correct** — nominalement, en cas d'erreur, et à la frontière entre foyers.

Le QA Engineer ne développe pas de fonctionnalités. Il valide les critères d'acceptation, produit les tests automatisés, identifie les régressions, et remonte les bugs avec suffisamment de précision pour qu'un Developer puisse les reproduire et les corriger sans aller-retour.

> **Principe directeur** : *Un test qui ne peut pas échouer ne prouve rien. Un bug sans étapes de reproduction n'existe pas.*

---

## 2. Stratégie de tests

### 2.1 Pyramide de tests

```
                        ╔══════════╗
                        ║  E2E     ║  ← Peu nombreux, lents, coûteux
                        ║  (Playwright)     couvrent les parcours critiques
                       ╔╩══════════╩╗
                       ║ Intégration ║ ← API Routes + DB (Supabase local)
                       ║  (Jest)     ║   isolation inter-foyers
                      ╔╩════════════╩╗
                      ║  Unitaires   ║ ← Nombreux, rapides, ciblés
                      ║  (Jest + RTL) ║  logique métier + composants UI
                      ╚══════════════╝

Cible de couverture :
  Unitaires    : 70 % des fonctions utilitaires et des composants clés
  Intégration  : 100 % des API Routes (cas nominal + cas d'erreur)
  E2E          : Parcours critiques uniquement (auth, création foyer, courses)
```

### 2.2 Périmètre de test par couche

| Couche | Outil | Ce qui est testé | Ce qui n'est pas testé |
|---|---|---|---|
| Composants UI | Jest + RTL | Rendu, interactions, états | Styling TailwindCSS pur |
| Hooks React | Jest + RTL | État, appels API mockés | Implémentation fetch interne |
| Validations Zod | Jest | Schémas valides et invalides | — |
| API Routes | Jest + Supabase local | Auth, validation, DB, codes HTTP | Middleware Next.js |
| Middleware | Jest | Redirections auth/non-auth | — |
| RLS Postgres | Supabase local | Isolation inter-foyers | — |
| Parcours E2E | Playwright | Flux complet utilisateur | UI pixel-perfect |

### 2.3 Configuration Jest

```typescript
// jest.config.ts
import type { Config } from 'jest'
import nextJest from 'next/jest'

const createJestConfig = nextJest({ dir: './' })

const config: Config = {
  testEnvironment: 'jsdom',           // Composants React
  setupFilesAfterFramework: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',   // Alias TypeScript
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/types/**',
    '!src/app/**/layout.tsx',         // Layouts — pas de logique métier
    '!src/app/**/page.tsx',           // Pages — testées via E2E
  ],
  coverageThresholds: {
    global: {
      branches:  60,
      functions: 70,
      lines:     70,
      statements: 70,
    },
  },
}

export default createJestConfig(config)
```

```typescript
// jest.setup.ts
import '@testing-library/jest-dom'

// Mock global fetch (remplacé par des mocks spécifiques dans les tests)
global.fetch = jest.fn()

// Mock navigator.clipboard (non disponible dans jsdom)
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn().mockResolvedValue(undefined),
  },
})

// Mock navigator.share
Object.assign(navigator, {
  share: jest.fn().mockResolvedValue(undefined),
})

// Nettoyage après chaque test
afterEach(() => {
  jest.clearAllMocks()
})
```

### 2.4 Conventions de nommage des tests

```
Structure des fichiers :
  src/
  ├── components/tasks/TaskCard.tsx
  └── __tests__/
      ├── components/
      │   └── tasks/TaskCard.test.tsx
      ├── hooks/
      │   └── useTasks.test.ts
      ├── api/
      │   └── tasks.test.ts
      └── lib/
          └── validations/task.test.ts

Nommage des blocs :
  describe('[NomDuComposant/Hook/Route]', () => {
    describe('[contexte ou état]', () => {
      it('[comportement attendu en langage naturel]', () => {})
    })
  })

Exemples valides :
  it('affiche le titre de la tâche')
  it('désactive le bouton si le titre est vide')
  it('appelle onToggle avec is_completed=true au premier clic')
  it('retourne 401 si le header Authorization est absent')
  it('retourne 403 si l\'utilisateur n\'est pas membre du foyer')
```

---

## 3. Tests unitaires

### 3.1 Tests de composants — React Testing Library

```typescript
// __tests__/components/tasks/TaskCard.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TaskCard } from '@/components/tasks/TaskCard'
import type { Task } from '@/types'

// ─── Fixture ──────────────────────────────────────────
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

// ─── Tests ────────────────────────────────────────────
describe('TaskCard', () => {
  describe('rendu nominal', () => {
    it('affiche le titre de la tâche', () => {
      render(<TaskCard task={baseTask} onToggle={jest.fn()} />)
      expect(screen.getByText('Faire les courses')).toBeInTheDocument()
    })

    it('n\'applique pas line-through quand la tâche est active', () => {
      render(<TaskCard task={baseTask} onToggle={jest.fn()} />)
      const title = screen.getByText('Faire les courses')
      expect(title).not.toHaveClass('line-through')
    })

    it('a un bouton accessible avec aria-label descriptif', () => {
      render(<TaskCard task={baseTask} onToggle={jest.fn()} />)
      expect(
        screen.getByRole('button', { name: /marquer "Faire les courses" comme complétée/i })
      ).toBeInTheDocument()
    })
  })

  describe('état complété', () => {
    const completedTask = { ...baseTask, is_completed: true }

    it('applique line-through sur le titre', () => {
      render(<TaskCard task={completedTask} onToggle={jest.fn()} />)
      expect(screen.getByText('Faire les courses')).toHaveClass('line-through')
    })

    it('réduit l\'opacité de la carte', () => {
      const { container } = render(
        <TaskCard task={completedTask} onToggle={jest.fn()} />
      )
      expect(container.firstChild).toHaveClass('opacity-50')
    })

    it('met à jour l\'aria-label pour refléter l\'état complété', () => {
      render(<TaskCard task={completedTask} onToggle={jest.fn()} />)
      expect(
        screen.getByRole('button', { name: /marquer "Faire les courses" comme non complétée/i }
      )).toBeInTheDocument()
    })
  })

  describe('interactions', () => {
    it('appelle onToggle(id, true) quand une tâche active est cochée', async () => {
      const onToggle = jest.fn().mockResolvedValue(undefined)
      render(<TaskCard task={baseTask} onToggle={onToggle} />)

      await userEvent.click(screen.getByRole('button'))

      expect(onToggle).toHaveBeenCalledTimes(1)
      expect(onToggle).toHaveBeenCalledWith('task-uuid-1', true)
    })

    it('appelle onToggle(id, false) quand une tâche complétée est décochée', async () => {
      const onToggle = jest.fn().mockResolvedValue(undefined)
      render(<TaskCard task={{ ...baseTask, is_completed: true }} onToggle={onToggle} />)

      await userEvent.click(screen.getByRole('button'))

      expect(onToggle).toHaveBeenCalledWith('task-uuid-1', false)
    })

    it('désactive le bouton pendant le chargement', async () => {
      // onToggle qui ne se résout pas immédiatement
      const onToggle = jest.fn().mockReturnValue(new Promise(() => {}))
      render(<TaskCard task={baseTask} onToggle={onToggle} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      await waitFor(() => {
        expect(button).toBeDisabled()
      })
    })
  })
})
```

### 3.2 Tests de formulaires

```typescript
// __tests__/components/tasks/TaskForm.test.tsx

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TaskForm } from '@/components/tasks/TaskForm'

describe('TaskForm', () => {
  describe('validation', () => {
    it('désactive le bouton de soumission quand le titre est vide', async () => {
      render(<TaskForm onSubmit={jest.fn()} onCancel={jest.fn()} />)
      // Bouton non disabled au rendu initial — mais Zod bloque à la soumission
      // Vérifier le message d'erreur après tentative de soumission
      await userEvent.click(screen.getByRole('button', { name: /créer/i }))
      expect(await screen.findByText('Le titre est obligatoire')).toBeInTheDocument()
    })

    it('affiche une erreur si le titre dépasse 100 caractères', async () => {
      render(<TaskForm onSubmit={jest.fn()} onCancel={jest.fn()} />)
      const input = screen.getByLabelText('Titre')
      await userEvent.type(input, 'A'.repeat(101))
      await userEvent.click(screen.getByRole('button', { name: /créer/i }))
      expect(
        await screen.findByText('Le titre ne peut pas dépasser 100 caractères')
      ).toBeInTheDocument()
    })

    it('n\'affiche pas d\'erreur avec un titre valide', async () => {
      const onSubmit = jest.fn().mockResolvedValue(undefined)
      render(<TaskForm onSubmit={onSubmit} onCancel={jest.fn()} />)

      await userEvent.type(screen.getByLabelText('Titre'), 'Acheter du pain')
      await userEvent.click(screen.getByRole('button', { name: /créer/i }))

      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument()
      })
    })
  })

  describe('soumission', () => {
    it('appelle onSubmit avec les données correctes', async () => {
      const onSubmit = jest.fn().mockResolvedValue(undefined)
      render(<TaskForm onSubmit={onSubmit} onCancel={jest.fn()} />)

      await userEvent.type(screen.getByLabelText('Titre'), 'Faire la vaisselle')
      await userEvent.type(
        screen.getByLabelText('Description (optionnel)'),
        'Avec le lave-vaisselle'
      )
      await userEvent.click(screen.getByRole('button', { name: /créer/i }))

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          title: 'Faire la vaisselle',
          description: 'Avec le lave-vaisselle',
        })
      })
    })

    it('affiche un message d\'erreur serveur si onSubmit lève une exception', async () => {
      const onSubmit = jest.fn().mockRejectedValue(new Error('Erreur réseau'))
      render(<TaskForm onSubmit={onSubmit} onCancel={jest.fn()} />)

      await userEvent.type(screen.getByLabelText('Titre'), 'Tâche quelconque')
      await userEvent.click(screen.getByRole('button', { name: /créer/i }))

      expect(
        await screen.findByText('Une erreur est survenue. Veuillez réessayer.')
      ).toBeInTheDocument()
    })

    it('affiche le spinner pendant le chargement', async () => {
      const onSubmit = jest.fn().mockReturnValue(new Promise(() => {}))
      render(<TaskForm onSubmit={onSubmit} onCancel={jest.fn()} />)

      await userEvent.type(screen.getByLabelText('Titre'), 'Tâche test')
      await userEvent.click(screen.getByRole('button', { name: /créer/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /créer/i })).toBeDisabled()
      })
    })
  })

  describe('annulation', () => {
    it('appelle onCancel au clic sur Annuler', async () => {
      const onCancel = jest.fn()
      render(<TaskForm onSubmit={jest.fn()} onCancel={onCancel} />)
      await userEvent.click(screen.getByRole('button', { name: /annuler/i }))
      expect(onCancel).toHaveBeenCalledTimes(1)
    })
  })
})
```

### 3.3 Tests des validations Zod

```typescript
// __tests__/lib/validations/task.test.ts

import { createTaskSchema } from '@/lib/validations/task'

describe('createTaskSchema', () => {
  describe('titre', () => {
    it('accepte un titre valide', () => {
      const result = createTaskSchema.safeParse({ title: 'Titre valide' })
      expect(result.success).toBe(true)
    })

    it('refuse un titre vide', () => {
      const result = createTaskSchema.safeParse({ title: '' })
      expect(result.success).toBe(false)
      expect(result.error?.flatten().fieldErrors.title).toContain(
        'Le titre est obligatoire'
      )
    })

    it('refuse un titre de 101 caractères', () => {
      const result = createTaskSchema.safeParse({ title: 'A'.repeat(101) })
      expect(result.success).toBe(false)
    })

    it('accepte un titre de 100 caractères exactement', () => {
      const result = createTaskSchema.safeParse({ title: 'A'.repeat(100) })
      expect(result.success).toBe(true)
    })

    it('trim les espaces autour du titre', () => {
      const result = createTaskSchema.safeParse({ title: '  Titre avec espaces  ' })
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.title).toBe('Titre avec espaces')
      }
    })
  })

  describe('description', () => {
    it('accepte une description absente', () => {
      const result = createTaskSchema.safeParse({ title: 'Titre' })
      expect(result.success).toBe(true)
    })

    it('accepte une description undefined', () => {
      const result = createTaskSchema.safeParse({ title: 'Titre', description: undefined })
      expect(result.success).toBe(true)
    })

    it('refuse une description de 501 caractères', () => {
      const result = createTaskSchema.safeParse({
        title: 'Titre',
        description: 'A'.repeat(501),
      })
      expect(result.success).toBe(false)
    })
  })
})
```

### 3.4 Tests des hooks

```typescript
// __tests__/hooks/useTasks.test.ts

import { renderHook, act, waitFor } from '@testing-library/react'
import { useTasks } from '@/hooks/useTasks'

// Mock global fetch
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

const mockTasks = [
  {
    id: 'task-1',
    household_id: 'hh-1',
    title: 'Première tâche',
    is_completed: false,
    created_at: '2026-03-04T10:00:00Z',
  },
]

describe('useTasks', () => {
  describe('fetchTasks', () => {
    it('charge les tâches au montage', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTasks,
      } as Response)

      const { result } = renderHook(() => useTasks('hh-1'))

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.tasks).toEqual(mockTasks)
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/tasks?householdId=hh-1')
    })

    it('expose une erreur si le fetch échoue', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      } as Response)

      const { result } = renderHook(() => useTasks('hh-1'))

      await waitFor(() => {
        expect(result.current.error).toBe('Impossible de charger les tâches')
      })
    })
  })

  describe('toggleTask (optimistic update)', () => {
    it('met à jour l\'état local immédiatement avant la réponse API', async () => {
      // Fetch initial
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTasks,
      } as Response)

      const { result } = renderHook(() => useTasks('hh-1'))
      await waitFor(() => expect(result.current.isLoading).toBe(false))

      // PATCH — réponse lente
      mockFetch.mockReturnValueOnce(
        new Promise(resolve =>
          setTimeout(() => resolve({ ok: true, json: async () => ({}) } as Response), 500)
        )
      )

      act(() => { result.current.toggleTask('task-1', true) })

      // Vérification optimiste AVANT que la réponse arrive
      expect(result.current.tasks[0].is_completed).toBe(true)
    })

    it('effectue un rollback si le PATCH échoue', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTasks,
      } as Response)

      const { result } = renderHook(() => useTasks('hh-1'))
      await waitFor(() => expect(result.current.isLoading).toBe(false))

      mockFetch.mockResolvedValueOnce({ ok: false } as Response)

      await act(async () => {
        await expect(result.current.toggleTask('task-1', true)).rejects.toThrow()
      })

      // Rollback : la tâche revient à son état initial
      expect(result.current.tasks[0].is_completed).toBe(false)
    })
  })
})
```

---

## 4. Tests d'intégration

### 4.1 Configuration de l'environnement de test API

```typescript
// lib/test-utils/api.ts
// Utilitaires pour tester les API Routes Next.js

import { NextRequest } from 'next/server'

interface CreateRequestOptions {
  method?: string
  body?: unknown
  searchParams?: Record<string, string>
  headers?: Record<string, string>
}

export function createRequest(
  url: string,
  options: CreateRequestOptions = {}
): NextRequest {
  const { method = 'GET', body, searchParams, headers = {} } = options

  const fullUrl = new URL(url, 'http://localhost:3000')
  if (searchParams) {
    Object.entries(searchParams).forEach(([key, value]) =>
      fullUrl.searchParams.set(key, value)
    )
  }

  return new NextRequest(fullUrl.toString(), {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  })
}

// Mock Supabase pour les tests d'API Routes
export function mockSupabaseUser(userId: string | null) {
  jest.mock('@/lib/supabase/server', () => ({
    createServerClient: () => ({
      auth: {
        getUser: jest.fn().mockResolvedValue({
          data: { user: userId ? { id: userId } : null },
          error: null,
        }),
      },
      from: jest.fn().mockReturnValue({
        select: jest.fn().mockReturnThis(),
        insert: jest.fn().mockReturnThis(),
        update: jest.fn().mockReturnThis(),
        eq: jest.fn().mockReturnThis(),
        single: jest.fn(),
        order: jest.fn().mockReturnThis(),
        limit: jest.fn().mockReturnThis(),
      }),
    }),
  }))
}
```

### 4.2 Tests des API Routes — GET

```typescript
// __tests__/api/tasks/route.test.ts

import { GET, POST } from '@/app/api/v1/tasks/route'
import { createRequest } from '@/lib/test-utils/api'

// Mock Supabase
jest.mock('@/lib/supabase/server')
import { createServerClient } from '@/lib/supabase/server'
const mockCreateServerClient = createServerClient as jest.MockedFunction<typeof createServerClient>

describe('GET /api/v1/tasks', () => {
  describe('validation des paramètres', () => {
    it('retourne 400 si householdId est absent', async () => {
      const req = createRequest('/api/v1/tasks')
      const res = await GET(req)
      expect(res.status).toBe(400)
      const body = await res.json()
      expect(body.error).toContain('householdId')
    })
  })

  describe('authentification', () => {
    it('retourne 401 si l\'utilisateur n\'est pas authentifié', async () => {
      mockCreateServerClient.mockReturnValue({
        auth: { getUser: jest.fn().mockResolvedValue({ data: { user: null }, error: null }) },
      } as any)

      const req = createRequest('/api/v1/tasks', {
        searchParams: { householdId: 'hh-uuid-1' },
      })
      const res = await GET(req)
      expect(res.status).toBe(401)
    })
  })

  describe('autorisation (isolation multi-tenant)', () => {
    it('retourne 403 si l\'utilisateur n\'est pas membre du foyer', async () => {
      mockCreateServerClient.mockReturnValue({
        auth: {
          getUser: jest.fn().mockResolvedValue({
            data: { user: { id: 'user-not-in-household' } },
            error: null,
          }),
        },
        from: jest.fn().mockReturnValue({
          select: jest.fn().mockReturnThis(),
          eq: jest.fn().mockReturnThis(),
          single: jest.fn().mockResolvedValue({ data: null, error: null }), // Pas de membership
        }),
      } as any)

      const req = createRequest('/api/v1/tasks', {
        searchParams: { householdId: 'autre-foyer-uuid' },
      })
      const res = await GET(req)
      expect(res.status).toBe(403)
    })

    it('retourne 200 et les tâches si l\'utilisateur est membre', async () => {
      const mockTasks = [
        { id: 'task-1', title: 'Ma tâche', household_id: 'hh-uuid-1', is_completed: false },
      ]

      mockCreateServerClient.mockReturnValue({
        auth: {
          getUser: jest.fn().mockResolvedValue({
            data: { user: { id: 'user-uuid-1' } }, error: null,
          }),
        },
        from: jest.fn().mockImplementation((table: string) => {
          if (table === 'household_members') {
            return {
              select: jest.fn().mockReturnThis(),
              eq: jest.fn().mockReturnThis(),
              single: jest.fn().mockResolvedValue({ data: { id: 'member-1' }, error: null }),
            }
          }
          if (table === 'tasks') {
            return {
              select: jest.fn().mockReturnThis(),
              eq: jest.fn().mockReturnThis(),
              order: jest.fn().mockResolvedValue({ data: mockTasks, error: null }),
            }
          }
        }),
      } as any)

      const req = createRequest('/api/v1/tasks', {
        searchParams: { householdId: 'hh-uuid-1' },
      })
      const res = await GET(req)
      expect(res.status).toBe(200)
      const body = await res.json()
      expect(body).toEqual(mockTasks)
    })
  })
})
```

### 4.3 Tests des API Routes — POST

```typescript
describe('POST /api/v1/tasks', () => {
  describe('validation Zod', () => {
    it('retourne 422 si le body est vide', async () => {
      const req = createRequest('/api/v1/tasks', { method: 'POST', body: {} })
      const res = await POST(req)
      expect(res.status).toBe(422)
    })

    it('retourne 422 si le titre dépasse 100 caractères', async () => {
      const req = createRequest('/api/v1/tasks', {
        method: 'POST',
        body: { title: 'A'.repeat(101), householdId: 'hh-uuid-1' },
      })
      const res = await POST(req)
      expect(res.status).toBe(422)
    })

    it('retourne 422 si householdId n\'est pas un UUID', async () => {
      const req = createRequest('/api/v1/tasks', {
        method: 'POST',
        body: { title: 'Tâche', householdId: 'pas-un-uuid' },
      })
      const res = await POST(req)
      expect(res.status).toBe(422)
    })
  })

  describe('création réussie', () => {
    it('retourne 201 et la tâche créée', async () => {
      const created = { id: 'new-task-uuid', title: 'Tâche valide', is_completed: false }

      mockCreateServerClient.mockReturnValue({
        auth: { getUser: jest.fn().mockResolvedValue({ data: { user: { id: 'u1' } }, error: null }) },
        from: jest.fn().mockReturnValue({
          insert: jest.fn().mockReturnThis(),
          select: jest.fn().mockReturnThis(),
          single: jest.fn().mockResolvedValue({ data: created, error: null }),
        }),
      } as any)

      const req = createRequest('/api/v1/tasks', {
        method: 'POST',
        body: { title: 'Tâche valide', householdId: 'hh-uuid-1' },
      })
      const res = await POST(req)
      expect(res.status).toBe(201)
      const body = await res.json()
      expect(body.id).toBe('new-task-uuid')
    })
  })
})
```

### 4.4 Tests d'isolation multi-tenant — RLS

```sql
-- Tests à exécuter dans Supabase local (supabase test db)
-- Vérifient que RLS empêche tout accès cross-foyer

-- Contexte : utilisateur A est dans foyer-1, utilisateur B est dans foyer-2

-- Test 1 : utilisateur A ne voit pas les tâches du foyer-2
SET LOCAL role TO authenticated;
SET LOCAL request.jwt.claims TO '{"sub": "user-a-uuid"}';

SELECT COUNT(*) FROM public.tasks WHERE household_id = 'foyer-2-uuid';
-- Résultat attendu : 0

-- Test 2 : utilisateur A ne peut pas modifier une tâche du foyer-2
UPDATE public.tasks
SET title = 'Tentative de modification cross-foyer'
WHERE household_id = 'foyer-2-uuid';
-- Résultat attendu : 0 rows affected (RLS bloque silencieusement)

-- Test 3 : utilisateur B ne peut pas rejoindre le foyer-1 via INSERT direct
INSERT INTO public.household_members (household_id, profile_id, role)
VALUES ('foyer-1-uuid', 'user-c-uuid', 'member');
-- Résultat attendu : ERROR - RLS policy violation (profile_id ≠ auth.uid())

RESET role;
RESET request.jwt.claims;
```

---

## 5. Validation des User Stories

### 5.1 Processus de validation

```
Story assignée au Developer
        │
        ▼
Developer → "Ready for QA" (PR créée, tâches techniques complétées)
        │
        ▼
QA reçoit la story
        │
   ┌────┴────────────────────────────────────┐
   │  1. Relire les critères d'acceptation  │
   │  2. Exécuter les tests automatisés     │
   │  3. Tester manuellement les cas limites│
   │  4. Vérifier l'accessibilité           │
   │  5. Vérifier le comportement mobile    │
   └────┬────────────────────────────────────┘
        │
   ┌────┴──────┐
   │  Résultat  │
   └────┬───────┘
        ├── ✅ Tous les CA passent → "Accepted" → Story Done
        └── ❌ Au moins 1 CA échoue → Bug créé → Story → Rejected
```

### 5.2 Rapport de validation — format standard

```markdown
## Rapport de validation — [ID Story] — [Titre]

**Date** : YYYY-MM-DD  
**Validé par** : QA Agent  
**Environnement** : Local / Preview Vercel  
**Décision** : ✅ Accepted | ❌ Rejected

### Critères d'acceptation

| # | Critère | Résultat | Notes |
|---|---|---|---|
| CA-1 | [Texte du critère] | ✅ Pass | — |
| CA-2 | [Texte du critère] | ✅ Pass | — |
| CA-3 | [Texte du critère] | ❌ Fail | [Description de l'échec] |

### Tests automatisés

| Suite | Tests | Pass | Fail | Skip |
|---|---|---|---|---|
| Composant TaskCard | 8 | 8 | 0 | 0 |
| Hook useTasks | 5 | 5 | 0 | 0 |
| API POST /tasks | 6 | 5 | 1 | 0 |

### Cas limites testés

- [ ] Comportement sur mobile 375px (Chrome DevTools)
- [ ] Comportement sur desktop 1280px
- [ ] Gestion de l'erreur réseau (DevTools → Network → Offline)
- [ ] Comportement si l'utilisateur n'est pas membre du foyer
- [ ] Contenu long (titre de 100 caractères)

### Bugs découverts

- BUG-003 (Bloquant) — Le bouton reste en état loading après erreur réseau

### Décision finale

❌ **Rejected** — CA-3 non respecté + BUG-003 bloquant.  
→ La story retourne en backlog avec les bugs associés.
```

### 5.3 Checklist de validation par module

#### AUTH-01 — Inscription

```
Cas nominaux :
- [ ] Formulaire s'affiche avec 3 champs (email, password, confirm)
- [ ] Bouton désactivé si formulaire vide
- [ ] Inscription réussie → profil créé dans Supabase profiles
- [ ] Inscription réussie → session active (cookie HTTP-only posé)
- [ ] Inscription réussie → redirection vers /household-setup

Cas d'erreur :
- [ ] Email invalide → message d'erreur inline sous le champ
- [ ] Mot de passe < 8 chars → message inline
- [ ] Mots de passe différents → message inline
- [ ] Email déjà utilisé → message "Un compte existe déjà avec cet email"
- [ ] Erreur réseau → message générique + bouton réactivé

Accessibilité :
- [ ] Labels visibles (pas uniquement placeholders)
- [ ] Erreurs annoncées via role="alert"
- [ ] Navigation clavier fonctionnelle (Tab → Shift+Tab → Enter)
```

#### FOYER-01 — Créer un foyer

```
Cas nominaux :
- [ ] Formulaire avec champ nom (min 2, max 50 chars)
- [ ] Bouton désactivé si champ vide
- [ ] Création → foyer dans households + membre admin dans household_members
- [ ] Code invitation 6 chars généré (uppercase, unique)
- [ ] Redirection vers /dashboard après création

Cas d'erreur :
- [ ] Nom < 2 chars → erreur inline
- [ ] Nom > 50 chars → erreur inline
- [ ] Erreur serveur → message + possibilité de retry

Isolation multi-tenant :
- [ ] Le foyer créé n'est visible que par son créateur
- [ ] Un autre utilisateur ne voit pas ce foyer via l'API
```

#### FOYER-02 — Rejoindre via code

```
Cas nominaux :
- [ ] Champ accepte 6 chars (insensible casse)
- [ ] Code valide → membre ajouté avec rôle 'member'
- [ ] Redirection vers /dashboard du foyer rejoint

Cas d'erreur :
- [ ] Code invalide → "Code invalide ou introuvable"
- [ ] Déjà membre → "Vous êtes déjà membre de ce foyer"
- [ ] Code de 5 ou 7 chars → validation bloquante

Multi-utilisateurs :
- [ ] User A crée le foyer → User B rejoint avec le code
- [ ] Les deux voient les mêmes tâches et courses
```

#### TASK-04 — Compléter une tâche

```
Cas nominaux :
- [ ] Clic checkbox → is_completed=true en DB
- [ ] line-through + opacity appliqués immédiatement (optimistic)
- [ ] Second clic → is_completed=false (toggle)

Multi-membres :
- [ ] User A coche → User B voit le changement (Realtime ou reload)

Rollback :
- [ ] Simuler erreur PATCH → état revient à l'état précédent
- [ ] Toast d'erreur affiché après rollback
```

#### SHOP-02 — Marquer acheté

```
Cas nominaux :
- [ ] Tap → is_purchased=true + déplacement section "Déjà acheté"
- [ ] Articles triés : non-achetés en haut, achetés en bas
- [ ] Re-tap → revient dans "À acheter"

Temps réel :
- [ ] Deux onglets navigateur ouverts → action dans l'un reflétée dans l'autre
```

#### HOME-01 — Résumé accueil

```
Données présentes :
- [ ] Max 3 tâches non complétées affichées
- [ ] Compteur articles restants correct
- [ ] Tap tâches → navigation vers /tasks
- [ ] Tap courses → navigation vers /shopping

États vides :
- [ ] Aucune tâche → "Aucune tâche pour aujourd'hui 🎉"
- [ ] Liste vide → "La liste de courses est vide"
- [ ] Salutation avec display_name de l'utilisateur

Performance :
- [ ] Lighthouse mobile ≥ 80 sur Performance
- [ ] LCP < 2s (réseau 4G simulé)
```

---

## 6. Gestion des bugs

### 6.1 Niveaux de sévérité

```
BLOQUANT (P1)
  → Empêche la fonctionnalité principale de fonctionner
  → Exemples : inscription impossible, données d'un autre foyer visibles,
               crash de l'application, perte de données
  → Action : stoppe le sprint, correction immédiate obligatoire

MAJEUR (P2)
  → Dégrade significativement l'expérience sans bloquer complètement
  → Exemples : rollback absent après erreur, formulaire non resetté,
               feedback visuel absent sur une action fréquente
  → Action : corrigé dans le sprint en cours si possible

MINEUR (P3)
  → Gêne légère, contournable par l'utilisateur
  → Exemples : message d'erreur trop générique, animation manquante,
               ordre de tri incorrect sur un cas rare
  → Action : ajouté au backlog pour le sprint suivant

COSMÉTIQUE (P4)
  → Problème visuel sans impact fonctionnel
  → Exemples : espacement légèrement incorrect, couleur décalée
  → Action : regroupé en lot de corrections UI
```

### 6.2 Fiche de bug — format standard

```markdown
## BUG-[N] — [Titre court et précis]

**Sévérité** : Bloquant | Majeur | Mineur | Cosmétique  
**Statut**   : Ouvert | En cours | Résolu | Fermé  
**Story liée** : [ID story]  
**Environnement** : Local / Preview / Production  
**Date** : YYYY-MM-DD  
**Découvert par** : QA Agent  

### Description
[Description factuelle du comportement observé]

### Étapes de reproduction
1. [Action précise]
2. [Action précise]
3. [Observer le résultat]

### Comportement observé
[Ce qui se passe réellement]

### Comportement attendu
[Ce qui devrait se passer selon les CA]

### Contexte
- Navigateur : Chrome 120 / Safari 17 / Firefox 121
- Viewport   : 375px (mobile) / 1280px (desktop)
- Utilisateur : authentifié / non authentifié
- Données     : foyer avec 3 tâches / foyer vide

### Logs / Erreurs console
```
[Coller ici les erreurs console si présentes]
```

### Critère d'acceptation violé
[CA-3 : "Si le champ email est vide → le bouton est désactivé"]

### Notes pour le Developer
[Piste de correction si identifiée, sinon laisser vide]
```

### 6.3 Exemples de fiches de bugs types

```markdown
## BUG-001 — Bouton "Créer" reste disabled après erreur serveur

**Sévérité** : Majeur  
**Story** : TASK-01

### Étapes de reproduction
1. Ouvrir la modale de création de tâche
2. Saisir un titre valide
3. Couper la connexion réseau (DevTools → Network → Offline)
4. Cliquer sur "Créer la tâche"

### Observé
Le bouton passe en état loading et reste disabled indéfiniment.
Aucun message d'erreur n'est affiché.

### Attendu
- Après timeout, le bouton revient à l'état normal (non loading)
- Un message d'erreur s'affiche : "Une erreur est survenue. Veuillez réessayer."

### CA violé
"En cas d'erreur réseau → message d'erreur : 'Une erreur est survenue, veuillez réessayer'"
```

```markdown
## BUG-002 — Isolation multi-tenant — tâches d'un autre foyer accessibles via API

**Sévérité** : BLOQUANT  
**Story** : TASK-01

### Étapes de reproduction
1. Créer User A avec foyer-A contenant la tâche "Tâche privée"
2. Créer User B avec foyer-B (User B non membre de foyer-A)
3. Appeler GET /api/v1/tasks?householdId=foyer-A-uuid avec le token de User B

### Observé
La réponse retourne 200 avec la tâche "Tâche privée" de User A.

### Attendu
La réponse doit retourner 403 Forbidden.
User B ne doit jamais voir les données de foyer-A.

### CA violé
RLS + vérification d'appartenance au foyer dans l'API Route.
```

### 6.4 Critères de fermeture d'un bug

```
Un bug est "Résolu" quand :
- [ ] Le Developer a soumis un fix (PR mergée)
- [ ] Le QA a ré-exécuté les étapes de reproduction → comportement attendu observé
- [ ] Un test automatisé couvre le scénario du bug (régression évitée)
- [ ] Aucune régression introduite sur les autres stories

Un bug "Bloquant" non résolu bloque la Sprint Review de la story concernée.
Un bug "Majeur" non résolu bloque l'acceptation de la story.
Un bug "Mineur" ou "Cosmétique" n'empêche pas l'acceptation — story ajoutée au backlog.
```

### 6.5 Métriques qualité

```
Métriques suivies par le QA à chaque sprint :

  Taux de stories acceptées du premier coup
  = Stories Accepted sans Rejected / Total stories présentées en Review × 100
  Cible : ≥ 80%

  Bugs découverts après acceptance (échappé au QA)
  Cible : 0 bug Bloquant, ≤ 1 bug Majeur par sprint

  Couverture de tests
  Cible : ≥ 70% lignes sur le code métier

  Durée moyenne de résolution des bugs
  Cible : P1 < 4h / P2 < 2 jours / P3 dans le sprint suivant

  Bugs récurrents (même composant > 2 fois)
  → Signal : revoir la conception ou les tests de ce composant
```

---

## Annexes

### A. Checklist — Story prête à tester

```
Reçu du Developer :
- [ ] PR créée et mergée sur la branche de dev
- [ ] Tests unitaires écrits et passants (suite verte)
- [ ] Aucune erreur ESLint / TypeScript (next build passe)
- [ ] Tâches techniques complétées (toutes les cases cochées dans le backlog)

À vérifier par le QA :
- [ ] Les critères d'acceptation sont tous couverts par les tests ou vérifiés manuellement
- [ ] Les cas d'erreur sont testés (pas uniquement le chemin nominal)
- [ ] L'isolation multi-tenant est vérifiée pour toute story liée à des données de foyer
- [ ] Le comportement mobile 375px est validé
- [ ] L'accessibilité de base est vérifiée (clavier, contraste, aria-labels)
```

### B. Checklist — Fin de sprint (QA)

```
- [ ] Toutes les stories du sprint ont un rapport de validation
- [ ] Les bugs Bloquants et Majeurs sont documentés avec étapes de reproduction
- [ ] Les tests écrits couvrent les régressions des bugs corrigés
- [ ] Couverture de tests ≥ 70% maintenue
- [ ] Résumé de qualité du sprint préparé pour la Sprint Review
```

### C. Antipatterns à éviter

| Antipattern | Conséquence | Correction |
|---|---|---|
| Tester uniquement le chemin nominal | Les erreurs réseau non couvertes | Systématiser les cas d'erreur dans chaque suite |
| Tests qui ne peuvent pas échouer | Fausse sécurité | Vérifier qu'un test rouge avant le fix confirme le bug |
| Mock trop profond de Supabase | Tests qui ne testent pas le vrai code | Utiliser Supabase local pour les tests d'intégration |
| Bug sans étapes de reproduction | Le Developer ne peut pas reproduire | Format fiche de bug obligatoire |
| Accepter une story avec un bug bloquant | Régression garantie en production | Bug P1/P2 = story non acceptée |
| Pas de test de régression sur les bugs | Même bug réintroduit | Test automatisé obligatoire sur chaque bug corrigé |

### D. Références

| Ressource | URL |
|---|---|
| React Testing Library | https://testing-library.com/docs/react-testing-library/intro |
| Jest | https://jestjs.io/docs/getting-started |
| Testing Library — user-event | https://testing-library.com/docs/user-event/intro |
| Supabase local dev | https://supabase.com/docs/guides/cli/local-development |
| WCAG 2.1 AA | https://www.w3.org/WAI/WCAG21/quickref |

### E. Références projet

| Document | Localisation |
|---|---|
| Backlog AI Scrum | `docs/backlog/ai_scrum_backlog.md` |
| Next.js Development Skill | `ai/roles/nextjs_development.md` |
| Supabase Database Skill | `ai/roles/supabase_database.md` |
| Product Management Skill | `ai/roles/product_management.md` |

---

*Ce document est la référence qualité pour l'agent IA QA Engineer. Il est mis à jour à chaque évolution des standards de test de l'équipe.*
