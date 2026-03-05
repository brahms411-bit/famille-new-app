# Skill — Next.js Development

> **Système** : AI Development Team  
> **Rôle** : Developer (agent IA)  
> **Version** : 1.0  
> **Date** : 2026-03-04  
> **Stack** : Next.js 14+ · TypeScript · TailwindCSS · Supabase  
> **Scope** : Développement frontend et backend — de la structure de fichiers à la mise en production

---

## Table des matières

1. [Mission du skill](#1-mission-du-skill)
2. [Architecture Next.js recommandée](#2-architecture-nextjs-recommandée)
3. [Structure des composants](#3-structure-des-composants)
4. [Gestion des états](#4-gestion-des-états)
5. [Appels API](#5-appels-api)
6. [Bonnes pratiques](#6-bonnes-pratiques)

---

## 1. Mission du skill

Le skill Next.js Development permet à un agent IA jouant le rôle de **Developer** de produire un code Next.js de qualité production — lisible, typé, testé et conforme aux conventions de l'App Router.

Son objectif central est de **transformer des User Stories et des spécifications UX en code fonctionnel, maintenable et performant**, en respectant les contraintes de la stack (Next.js 14+, TypeScript strict, TailwindCSS, Supabase).

Le Developer ne décide pas du *quoi* (Product Owner) ni du *design* (UX Designer). Il implémente avec précision les spécifications reçues, signale les ambiguïtés techniques, et produit un code que n'importe quel autre Developer peut reprendre sans friction.

> **Principe directeur** : *Un code correct est un code que l'agent suivant peut lire, modifier et tester sans demander d'explication.*

---

## 2. Architecture Next.js recommandée

### 2.1 Structure de fichiers complète

```
src/
├── app/                              # App Router — routes et layouts
│   ├── layout.tsx                    # Root layout (html, body, providers)
│   ├── globals.css                   # TailwindCSS base + custom properties
│   ├── (auth)/                       # Route group — pages publiques
│   │   ├── layout.tsx                # Layout auth (centré, sans nav)
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── register/
│   │       └── page.tsx
│   ├── (app)/                        # Route group — pages protégées
│   │   ├── layout.tsx                # Layout app (nav + auth guard)
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── tasks/
│   │   │   └── page.tsx
│   │   └── shopping/
│   │       └── page.tsx
│   ├── household-setup/
│   │   └── page.tsx                  # Page publique post-inscription
│   └── api/
│       └── v1/                       # API Routes — BFF layer
│           ├── auth/
│           │   ├── register/route.ts
│           │   └── login/route.ts
│           ├── households/
│           │   ├── route.ts          # GET, POST
│           │   ├── join/route.ts     # POST
│           │   └── [id]/
│           │       └── route.ts      # GET, PATCH, DELETE
│           ├── tasks/
│           │   ├── route.ts          # GET, POST
│           │   └── [id]/route.ts     # PATCH, DELETE
│           └── shopping/
│               ├── route.ts          # GET, POST
│               └── [id]/route.ts     # PATCH, DELETE
│
├── components/                       # Composants React réutilisables
│   ├── ui/                           # Composants atomiques (Button, Input…)
│   ├── layout/                       # NavBar, BottomNav, PageHeader
│   ├── auth/                         # LoginForm, RegisterForm
│   ├── household/                    # InviteCodeCard, HouseholdForm
│   ├── tasks/                        # TaskCard, TaskList, TaskForm
│   └── shopping/                     # ShoppingItemCard, ShoppingList
│
├── hooks/                            # Custom React hooks
│   ├── useAuth.ts
│   ├── useHousehold.ts
│   ├── useTasks.ts
│   └── useShopping.ts
│
├── lib/                              # Utilitaires et clients
│   ├── supabase/
│   │   ├── client.ts                 # Client browser (anon key)
│   │   └── server.ts                 # Client serveur (service role)
│   ├── validations/                  # Schémas Zod par domaine
│   │   ├── auth.ts
│   │   ├── household.ts
│   │   ├── task.ts
│   │   └── shopping.ts
│   └── utils/
│       ├── cn.ts                     # Utilitaire classnames + TailwindMerge
│       └── errors.ts                 # Helpers gestion d'erreurs
│
├── types/
│   ├── database.ts                   # Types générés par Supabase CLI
│   └── index.ts                      # Types applicatifs partagés
│
└── middleware.ts                     # Auth guard + session refresh
```

### 2.2 Route Groups et layouts

Les **route groups** (`(auth)` et `(app)`) permettent d'isoler les layouts sans affecter l'URL :

```typescript
// app/(app)/layout.tsx
// Layout partagé par toutes les pages protégées
// S'affiche une seule fois — pas de re-render lors de la navigation entre onglets

import { NavBar } from '@/components/layout/NavBar'
import { redirect } from 'next/navigation'
import { createServerClient } from '@/lib/supabase/server'

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = createServerClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Double protection : middleware + layout
  if (!user) redirect('/login')

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <main className="flex-1 pb-16 md:pb-0 md:pl-64">
        {children}
      </main>
      <NavBar />
    </div>
  )
}
```

### 2.3 Middleware d'authentification

```typescript
// middleware.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => request.cookies.getAll(),
        setAll: (cookiesToSet) => {
          cookiesToSet.forEach(({ name, value, options }) => {
            supabaseResponse.cookies.set(name, value, options)
          })
        },
      },
    }
  )

  // Refresh session — NE PAS supprimer cet appel
  const { data: { user } } = await supabase.auth.getUser()

  const isAuthRoute = request.nextUrl.pathname.startsWith('/login') ||
                      request.nextUrl.pathname.startsWith('/register')
  const isAppRoute  = request.nextUrl.pathname.startsWith('/dashboard') ||
                      request.nextUrl.pathname.startsWith('/tasks') ||
                      request.nextUrl.pathname.startsWith('/shopping')

  if (!user && isAppRoute) {
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  if (user && isAuthRoute) {
    const url = request.nextUrl.clone()
    url.pathname = '/dashboard'
    return NextResponse.redirect(url)
  }

  return supabaseResponse
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api).*)'],
}
```

### 2.4 Clients Supabase

Deux clients distincts selon le contexte d'exécution :

```typescript
// lib/supabase/client.ts — Client browser (composants React)
import { createBrowserClient } from '@supabase/ssr'
import type { Database } from '@/types/database'

export function createClient() {
  return createBrowserClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

```typescript
// lib/supabase/server.ts — Client serveur (API Routes, Server Components)
import { createServerClient as createSupabaseServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import type { Database } from '@/types/database'

export function createServerClient() {
  const cookieStore = cookies()
  return createSupabaseServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,   // Service role : bypasse RLS
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: (cookiesToSet) => {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          )
        },
      },
    }
  )
}
```

> **Règle absolue** : La `SERVICE_ROLE_KEY` n'est utilisée que dans les API Routes et Server Components côté serveur. Elle ne doit jamais apparaître dans un composant client.

---

## 3. Structure des composants

### 3.1 Conventions de nommage et organisation

```
Règles de nommage :
  Composant React    : PascalCase        → TaskCard.tsx
  Hook custom        : camelCase + use   → useTasks.ts
  Utilitaire         : camelCase         → formatDate.ts
  Type / Interface   : PascalCase        → TaskWithMember
  Constante          : SCREAMING_SNAKE   → MAX_TASKS_DISPLAYED
  Variable / fonction : camelCase        → isCompleted

Un fichier = un composant principal (exports nommés acceptés pour les sous-composants)
```

### 3.2 Anatomie d'un composant

```typescript
// components/tasks/TaskCard.tsx

import { useState } from 'react'
import { cn } from '@/lib/utils/cn'
import type { Task } from '@/types'

// ─── Types ────────────────────────────────────────────
interface TaskCardProps {
  task: Task
  onToggle: (id: string, completed: boolean) => void
  className?: string
}

// ─── Composant ────────────────────────────────────────
export function TaskCard({ task, onToggle, className }: TaskCardProps) {
  const [isLoading, setIsLoading] = useState(false)

  async function handleToggle() {
    setIsLoading(true)
    try {
      await onToggle(task.id, !task.is_completed)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <li
      className={cn(
        'flex items-center gap-3 rounded-xl bg-white p-4 shadow-sm',
        'transition-opacity duration-150',
        task.is_completed && 'opacity-50',
        className
      )}
    >
      <button
        onClick={handleToggle}
        disabled={isLoading}
        aria-label={`Marquer "${task.title}" comme ${task.is_completed ? 'non complétée' : 'complétée'}`}
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg
                   border-2 border-gray-200 transition-colors
                   hover:border-primary focus-visible:outline-none
                   focus-visible:ring-2 focus-visible:ring-primary"
      >
        {task.is_completed && (
          <span className="text-primary text-lg" aria-hidden="true">✓</span>
        )}
      </button>

      <span
        className={cn(
          'flex-1 text-sm font-medium text-gray-900',
          task.is_completed && 'line-through text-gray-400'
        )}
      >
        {task.title}
      </span>
    </li>
  )
}
```

### 3.3 Composants UI atomiques

```typescript
// components/ui/Button.tsx

import { forwardRef } from 'react'
import { cn } from '@/lib/utils/cn'

const variants = {
  primary:     'bg-primary text-white hover:bg-primary/90 focus-visible:ring-primary',
  secondary:   'bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:ring-gray-400',
  destructive: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500',
  ghost:       'text-gray-600 hover:bg-gray-100 focus-visible:ring-gray-400',
} as const

const sizes = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-11 px-4 text-sm',
  lg: 'h-12 px-6 text-base',
} as const

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants
  size?: keyof typeof sizes
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      disabled,
      className,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        aria-busy={loading}
        className={cn(
          // Base
          'inline-flex items-center justify-center gap-2 rounded-xl font-medium',
          'transition-colors duration-150',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          'disabled:pointer-events-none disabled:opacity-50',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {loading && (
          <svg
            className="h-4 w-4 animate-spin"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
        )}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
```

```typescript
// components/ui/Input.tsx

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  hint?: string
}

export function Input({ label, error, hint, id, className, ...props }: InputProps) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={inputId}
        className="text-sm font-medium text-gray-700"
      >
        {label}
      </label>

      <input
        id={inputId}
        aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
        aria-invalid={!!error}
        className={cn(
          'h-11 w-full rounded-xl border border-gray-300 bg-white px-3',
          'text-sm text-gray-900 placeholder:text-gray-400',
          'transition-colors duration-150',
          'focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20',
          error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20',
          className
        )}
        {...props}
      />

      {error && (
        <p id={`${inputId}-error`} role="alert" className="text-xs text-red-600">
          {error}
        </p>
      )}
      {hint && !error && (
        <p id={`${inputId}-hint`} className="text-xs text-gray-500">
          {hint}
        </p>
      )}
    </div>
  )
}
```

### 3.4 Utilitaire `cn` (classnames + Tailwind Merge)

```typescript
// lib/utils/cn.ts
// Évite les conflits de classes Tailwind et gère les classes conditionnelles

import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Usage :
// cn('px-4 py-2', isActive && 'bg-primary', className)
// cn('text-sm text-gray-900', completed && 'line-through text-gray-400')
```

---

## 4. Gestion des états

### 4.1 Stratégie d'état — décision par type

```
Type de donnée                     Solution recommandée
──────────────────────────────────────────────────────────────────
État UI local (modal ouvert, tab)  useState
État formulaire                    React Hook Form
Données serveur (liste de tâches)  Custom hook avec useState + useEffect
Session auth                       Context React + Supabase listener
État global léger                  Context React (pas de lib externe)
Cache serveur                      Revalidation Next.js (revalidatePath)
Temps réel                         Supabase Realtime dans custom hook
```

### 4.2 Custom hooks — pattern standard

```typescript
// hooks/useTasks.ts

'use client'

import { useState, useEffect, useCallback } from 'react'
import type { Task } from '@/types'

interface UseTasksReturn {
  tasks: Task[]
  isLoading: boolean
  error: string | null
  createTask: (data: CreateTaskData) => Promise<void>
  toggleTask: (id: string, completed: boolean) => Promise<void>
  refetch: () => Promise<void>
}

interface CreateTaskData {
  title: string
  description?: string
}

export function useTasks(householdId: string): UseTasksReturn {
  const [tasks, setTasks]     = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)

  // ─── Fetch ────────────────────────────────────────────
  const fetchTasks = useCallback(async () => {
    if (!householdId) return
    setIsLoading(true)
    setError(null)

    try {
      const res = await fetch(`/api/v1/tasks?householdId=${householdId}`)
      if (!res.ok) throw new Error('Impossible de charger les tâches')
      const data: Task[] = await res.json()
      setTasks(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue')
    } finally {
      setIsLoading(false)
    }
  }, [householdId])

  useEffect(() => { fetchTasks() }, [fetchTasks])

  // ─── Create ───────────────────────────────────────────
  const createTask = useCallback(async (data: CreateTaskData) => {
    // Optimistic update — ID temporaire
    const tempId   = `temp-${Date.now()}`
    const optimistic: Task = {
      id: tempId,
      household_id: householdId,
      title: data.title,
      description: data.description ?? null,
      is_completed: false,
      created_at: new Date().toISOString(),
    }

    setTasks(prev => [optimistic, ...prev])

    try {
      const res = await fetch('/api/v1/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...data, householdId }),
      })

      if (!res.ok) throw new Error('Impossible de créer la tâche')
      const created: Task = await res.json()

      // Remplacer l'item optimiste par la vraie donnée
      setTasks(prev => prev.map(t => (t.id === tempId ? created : t)))
    } catch (err) {
      // Rollback
      setTasks(prev => prev.filter(t => t.id !== tempId))
      throw err  // Remonter pour affichage dans le composant
    }
  }, [householdId])

  // ─── Toggle ───────────────────────────────────────────
  const toggleTask = useCallback(async (id: string, completed: boolean) => {
    // Optimistic update
    setTasks(prev =>
      prev.map(t => (t.id === id ? { ...t, is_completed: completed } : t))
    )

    try {
      const res = await fetch(`/api/v1/tasks/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_completed: completed }),
      })
      if (!res.ok) throw new Error('Impossible de mettre à jour la tâche')
    } catch (err) {
      // Rollback
      setTasks(prev =>
        prev.map(t => (t.id === id ? { ...t, is_completed: !completed } : t))
      )
      throw err
    }
  }, [])

  return { tasks, isLoading, error, createTask, toggleTask, refetch: fetchTasks }
}
```

### 4.3 Contexte d'authentification

```typescript
// lib/context/AuthContext.tsx

'use client'

import {
  createContext, useContext, useEffect, useState, type ReactNode
} from 'react'
import type { User } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase/client'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  isLoading: true,
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]         = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const supabase                = createClient()

  useEffect(() => {
    // Récupérer la session initiale
    supabase.auth.getUser().then(({ data: { user } }) => {
      setUser(user)
      setIsLoading(false)
    })

    // Écouter les changements de session
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_, session) => setUser(session?.user ?? null)
    )

    return () => subscription.unsubscribe()
  }, [supabase])

  return (
    <AuthContext.Provider value={{ user, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuthContext() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuthContext must be used inside AuthProvider')
  return ctx
}
```

### 4.4 Gestion des formulaires avec React Hook Form + Zod

```typescript
// Schéma de validation — lib/validations/task.ts
import { z } from 'zod'

export const createTaskSchema = z.object({
  title: z
    .string()
    .min(1, 'Le titre est obligatoire')
    .max(100, 'Le titre ne peut pas dépasser 100 caractères')
    .trim(),
  description: z
    .string()
    .max(500, 'La description ne peut pas dépasser 500 caractères')
    .trim()
    .optional(),
})

export type CreateTaskInput = z.infer<typeof createTaskSchema>
```

```typescript
// Composant formulaire — components/tasks/TaskForm.tsx

'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { createTaskSchema, type CreateTaskInput } from '@/lib/validations/task'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useState } from 'react'

interface TaskFormProps {
  onSubmit: (data: CreateTaskInput) => Promise<void>
  onCancel: () => void
}

export function TaskForm({ onSubmit, onCancel }: TaskFormProps) {
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<CreateTaskInput>({
    resolver: zodResolver(createTaskSchema),
  })

  async function handleFormSubmit(data: CreateTaskInput) {
    setServerError(null)
    try {
      await onSubmit(data)
      reset()
    } catch {
      setServerError('Une erreur est survenue. Veuillez réessayer.')
    }
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="flex flex-col gap-4" noValidate>
      <Input
        label="Titre"
        placeholder="Ex : Faire les courses"
        error={errors.title?.message}
        {...register('title')}
      />

      <Input
        label="Description (optionnel)"
        placeholder="Détails supplémentaires…"
        error={errors.description?.message}
        {...register('description')}
      />

      {serverError && (
        <p role="alert" className="text-sm text-red-600">{serverError}</p>
      )}

      <div className="flex gap-3 pt-2">
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          className="flex-1"
        >
          Annuler
        </Button>
        <Button
          type="submit"
          loading={isSubmitting}
          className="flex-1"
        >
          Créer la tâche
        </Button>
      </div>
    </form>
  )
}
```

---

## 5. Appels API

### 5.1 Structure d'une API Route

```typescript
// app/api/v1/tasks/route.ts

import { NextResponse, type NextRequest } from 'next/server'
import { z } from 'zod'
import { createServerClient } from '@/lib/supabase/server'
import { createTaskSchema } from '@/lib/validations/task'

// ─── GET /api/v1/tasks?householdId= ───────────────────
export async function GET(request: NextRequest) {
  try {
    const householdId = request.nextUrl.searchParams.get('householdId')

    if (!householdId) {
      return NextResponse.json(
        { error: 'householdId est requis' },
        { status: 400 }
      )
    }

    const supabase = createServerClient()

    // Vérifier que l'utilisateur est authentifié
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json({ error: 'Non authentifié' }, { status: 401 })
    }

    // Vérifier que l'utilisateur appartient au foyer
    const { data: membership } = await supabase
      .from('household_members')
      .select('id')
      .eq('household_id', householdId)
      .eq('profile_id', user.id)
      .single()

    if (!membership) {
      return NextResponse.json({ error: 'Accès refusé' }, { status: 403 })
    }

    // Requête principale
    const { data: tasks, error } = await supabase
      .from('tasks')
      .select('*')
      .eq('household_id', householdId)
      .order('created_at', { ascending: false })

    if (error) throw error

    return NextResponse.json(tasks)
  } catch (error) {
    console.error('[GET /api/v1/tasks]', error)
    return NextResponse.json(
      { error: 'Erreur serveur' },
      { status: 500 }
    )
  }
}

// ─── POST /api/v1/tasks ───────────────────────────────
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Validation Zod
    const parsed = createTaskSchema.extend({
      householdId: z.string().uuid('householdId invalide'),
    }).safeParse(body)

    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Données invalides', details: parsed.error.flatten() },
        { status: 422 }
      )
    }

    const { title, description, householdId } = parsed.data
    const supabase = createServerClient()

    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json({ error: 'Non authentifié' }, { status: 401 })
    }

    const { data: task, error } = await supabase
      .from('tasks')
      .insert({
        household_id: householdId,
        title,
        description: description ?? null,
        is_completed: false,
      })
      .select()
      .single()

    if (error) throw error

    return NextResponse.json(task, { status: 201 })
  } catch (error) {
    console.error('[POST /api/v1/tasks]', error)
    return NextResponse.json({ error: 'Erreur serveur' }, { status: 500 })
  }
}
```

```typescript
// app/api/v1/tasks/[id]/route.ts

import { NextResponse, type NextRequest } from 'next/server'
import { z } from 'zod'
import { createServerClient } from '@/lib/supabase/server'

const patchTaskSchema = z.object({
  is_completed: z.boolean().optional(),
  title: z.string().min(1).max(100).optional(),
  description: z.string().max(500).nullable().optional(),
})

// ─── PATCH /api/v1/tasks/[id] ─────────────────────────
export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body   = await request.json()
    const parsed = patchTaskSchema.safeParse(body)

    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Données invalides', details: parsed.error.flatten() },
        { status: 422 }
      )
    }

    const supabase = createServerClient()
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json({ error: 'Non authentifié' }, { status: 401 })
    }

    // Vérifier que la tâche appartient à un foyer dont l'user est membre
    const { data: task } = await supabase
      .from('tasks')
      .select('household_id')
      .eq('id', params.id)
      .single()

    if (!task) {
      return NextResponse.json({ error: 'Tâche introuvable' }, { status: 404 })
    }

    const { data: membership } = await supabase
      .from('household_members')
      .select('id')
      .eq('household_id', task.household_id)
      .eq('profile_id', user.id)
      .single()

    if (!membership) {
      return NextResponse.json({ error: 'Accès refusé' }, { status: 403 })
    }

    const { data: updated, error } = await supabase
      .from('tasks')
      .update({ ...parsed.data, updated_at: new Date().toISOString() })
      .eq('id', params.id)
      .select()
      .single()

    if (error) throw error

    return NextResponse.json(updated)
  } catch (error) {
    console.error('[PATCH /api/v1/tasks/:id]', error)
    return NextResponse.json({ error: 'Erreur serveur' }, { status: 500 })
  }
}
```

### 5.2 Codes HTTP — convention de l'API

```
200 OK              → GET réussi, PATCH réussi
201 Created         → POST réussi (ressource créée)
204 No Content      → DELETE réussi
400 Bad Request     → Paramètre manquant ou mal formé
401 Unauthorized    → Non authentifié (pas de session)
403 Forbidden       → Authentifié mais pas autorisé (mauvais foyer)
404 Not Found       → Ressource inexistante
422 Unprocessable   → Validation Zod échouée (données invalides)
500 Internal Error  → Erreur serveur non anticipée
```

### 5.3 Supabase Realtime — synchronisation temps réel

```typescript
// hooks/useShopping.ts — exemple avec Realtime

import { useEffect, useCallback, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { RealtimeChannel } from '@supabase/supabase-js'

export function useShopping(householdId: string) {
  const [items, setItems]   = useState<ShoppingItem[]>([])
  const channelRef          = useRef<RealtimeChannel | null>(null)
  const supabase            = createClient()

  useEffect(() => {
    if (!householdId) return

    // Fetch initial
    fetchItems()

    // Subscription Realtime
    channelRef.current = supabase
      .channel(`shopping:${householdId}`)
      .on(
        'postgres_changes',
        {
          event: '*',           // INSERT | UPDATE | DELETE
          schema: 'public',
          table: 'shopping_items',
          filter: `household_id=eq.${householdId}`,
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            setItems(prev => [payload.new as ShoppingItem, ...prev])
          }
          if (payload.eventType === 'UPDATE') {
            setItems(prev =>
              prev.map(i => (i.id === payload.new.id ? (payload.new as ShoppingItem) : i))
            )
          }
          if (payload.eventType === 'DELETE') {
            setItems(prev => prev.filter(i => i.id !== payload.old.id))
          }
        }
      )
      .subscribe()

    return () => {
      channelRef.current?.unsubscribe()
    }
  }, [householdId])

  // ... reste du hook
}
```

---

## 6. Bonnes pratiques

### 6.1 TypeScript strict

```typescript
// tsconfig.json — configuration stricte obligatoire
{
  "compilerOptions": {
    "strict": true,               // Active tous les checks stricts
    "noUncheckedIndexedAccess": true,  // arr[0] est T | undefined
    "noImplicitReturns": true,
    "exactOptionalPropertyTypes": true
  }
}

// Règles inviolables :
// ❌ any  → utiliser unknown + type guard ou le type précis
// ❌ as X → utiliser des type guards ou Zod parse
// ❌ !    → vérifier la nullabilité explicitement
// ✅ type guards, discriminated unions, Zod infer

// Exemple de type guard :
function isTask(value: unknown): value is Task {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'title' in value &&
    'is_completed' in value
  )
}
```

### 6.2 Gestion d'erreurs

```typescript
// lib/utils/errors.ts

export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly status: number = 500
  ) {
    super(message)
    this.name = 'AppError'
  }
}

// Dans les API Routes — pattern try/catch cohérent :
try {
  // ... logique métier
} catch (error) {
  if (error instanceof AppError) {
    return NextResponse.json(
      { error: error.message, code: error.code },
      { status: error.status }
    )
  }
  // Erreur non anticipée → log côté serveur, message générique côté client
  console.error('[route]', error)
  return NextResponse.json({ error: 'Erreur serveur' }, { status: 500 })
}

// Dans les hooks — exposer l'erreur pour affichage :
const [error, setError] = useState<string | null>(null)
try {
  await apiCall()
} catch (err) {
  setError(err instanceof Error ? err.message : 'Une erreur est survenue')
}
```

### 6.3 Performance

```typescript
// Lazy loading des composants lourds
import dynamic from 'next/dynamic'

const TaskForm = dynamic(
  () => import('@/components/tasks/TaskForm').then(m => m.TaskForm),
  {
    loading: () => <div className="h-48 animate-pulse rounded-xl bg-gray-100" />,
    ssr: false,   // Formulaires : toujours côté client
  }
)

// Images optimisées
import Image from 'next/image'
// Toujours spécifier width + height ou fill + sizes
<Image
  src={avatar}
  alt={`Avatar de ${name}`}
  width={40}
  height={40}
  className="rounded-full"
/>

// Mémoïsation — uniquement quand mesurée nécessaire
// ❌ memo() sur tout par défaut
// ✅ memo() sur les composants de liste (TaskCard dans une liste de 100 items)
import { memo } from 'react'
export const TaskCard = memo(function TaskCard({ task, onToggle }: TaskCardProps) {
  // ...
})
```

### 6.4 Variables d'environnement

```typescript
// types/env.d.ts — typage des variables d'environnement
declare namespace NodeJS {
  interface ProcessEnv {
    NEXT_PUBLIC_SUPABASE_URL: string
    NEXT_PUBLIC_SUPABASE_ANON_KEY: string
    SUPABASE_SERVICE_ROLE_KEY: string
  }
}

// Validation au démarrage — lib/env.ts
import { z } from 'zod'

const envSchema = z.object({
  NEXT_PUBLIC_SUPABASE_URL: z.string().url(),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1),
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(1),
})

export const env = envSchema.parse(process.env)

// Règle : NEXT_PUBLIC_ → accessible browser + serveur
//         Sans préfixe  → serveur uniquement (jamais dans un composant client)
```

### 6.5 Tests

```typescript
// Pattern de test pour un composant
// __tests__/components/TaskCard.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { TaskCard } from '@/components/tasks/TaskCard'

const mockTask = {
  id: 'task-1',
  household_id: 'hh-1',
  title: 'Faire les courses',
  description: null,
  is_completed: false,
  created_at: '2026-03-04T00:00:00Z',
}

describe('TaskCard', () => {
  it('affiche le titre de la tâche', () => {
    render(<TaskCard task={mockTask} onToggle={vi.fn()} />)
    expect(screen.getByText('Faire les courses')).toBeInTheDocument()
  })

  it('applique line-through quand la tâche est complétée', () => {
    render(
      <TaskCard task={{ ...mockTask, is_completed: true }} onToggle={vi.fn()} />
    )
    expect(screen.getByText('Faire les courses')).toHaveClass('line-through')
  })

  it('appelle onToggle avec les bons arguments au clic', async () => {
    const onToggle = vi.fn().mockResolvedValue(undefined)
    render(<TaskCard task={mockTask} onToggle={onToggle} />)

    fireEvent.click(screen.getByRole('button'))

    await waitFor(() => {
      expect(onToggle).toHaveBeenCalledWith('task-1', true)
    })
  })
})

// Pattern de test pour une API Route
// __tests__/api/tasks.test.ts

import { GET, POST } from '@/app/api/v1/tasks/route'
import { createRequest } from '@/lib/test-utils'  // helper test

describe('GET /api/v1/tasks', () => {
  it('retourne 400 si householdId manquant', async () => {
    const req = createRequest('GET', '/api/v1/tasks')
    const res = await GET(req)
    expect(res.status).toBe(400)
  })

  it('retourne 401 si non authentifié', async () => {
    const req = createRequest('GET', '/api/v1/tasks?householdId=abc')
    const res = await GET(req)
    expect(res.status).toBe(401)
  })
})
```

### 6.6 Checklist — avant toute PR

```
CODE
- [ ] TypeScript strict : aucun any, aucun as non justifié
- [ ] Aucun console.log laissé dans le code de production
- [ ] Toutes les fonctions async ont un try/catch ou propagent l'erreur explicitement
- [ ] Les variables d'environnement sensibles ne sont pas dans un composant client

COMPOSANTS
- [ ] Chaque composant a une interface TypeScript explicite pour ses props
- [ ] Les composants interactifs ont un aria-label ou aria-labelledby
- [ ] Les zones de tap font ≥ 44×44px (vérifiable en DevTools mobile)
- [ ] Le composant fonctionne sans JS (dégradation gracieuse)

API ROUTES
- [ ] Validation Zod sur tout input entrant (body, params, searchParams)
- [ ] Vérification d'authentification avant toute opération en base
- [ ] Vérification d'appartenance au foyer (pas seulement l'auth)
- [ ] Codes HTTP corrects pour chaque cas de réponse

TESTS
- [ ] Tests des cas nominaux
- [ ] Tests des cas d'erreur (champ vide, non authentifié, accès refusé)
- [ ] Tests des interactions utilisateur (clic, soumission)
- [ ] Suite complète verte (aucune régression)

PERFORMANCE
- [ ] Aucune image sans next/image
- [ ] Aucun fetch sans gestion d'état de chargement
- [ ] Les listes > 20 items ont une stratégie de virtualisation ou pagination
```

---

## Annexes

### A. Scripts npm recommandés

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "db:types": "supabase gen types typescript --local > src/types/database.ts"
  }
}
```

### B. Antipatterns à éviter

| Antipattern | Problème | Solution |
|---|---|---|
| `fetch` dans un Server Component sans cache | Re-fetch à chaque requête | `fetch(url, { next: { revalidate: 60 } })` |
| `useEffect` pour synchroniser deux états | Race conditions | Dériver l'état via `useMemo` ou calcul inline |
| Mutation directe de l'état | Bug React silencieux | Toujours retourner un nouvel objet/tableau |
| `SERVICE_ROLE_KEY` dans un composant client | Fuite de credentials | Client serveur uniquement dans API Routes |
| Validation uniquement côté client | Contournable | Zod obligatoire côté API Route aussi |
| `any` comme type de retour d'API | Perd les bénéfices TypeScript | Typer avec `z.infer<typeof schema>` |
| Composant de 300+ lignes | Illisible, non testable | Extraire des sous-composants ou des hooks |
| `key={index}` dans une liste | Mauvaises animations / bugs | Utiliser un id stable (`key={task.id}`) |

### C. Références

| Ressource | URL |
|---|---|
| Next.js App Router | https://nextjs.org/docs/app |
| Supabase SSR | https://supabase.com/docs/guides/auth/server-side/nextjs |
| TailwindCSS | https://tailwindcss.com/docs |
| React Hook Form | https://react-hook-form.com/docs |
| Zod | https://zod.dev |
| Testing Library | https://testing-library.com/docs/react-testing-library/intro |

### D. Références projet

| Document | Localisation |
|---|---|
| Architecture Overview | `docs/architecture/architecture_overview.md` |
| UX Design Skill | `ai/roles/ux_design.md` |
| Backlog AI Scrum | `docs/backlog/ai_scrum_backlog.md` |
| Product Spec | `docs/product/product_spec.md` |

---

*Ce document est la référence technique pour l'agent IA Developer. Il est mis à jour à chaque évolution significative de la stack ou des conventions de l'équipe.*
