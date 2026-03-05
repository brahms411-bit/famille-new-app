# Skill — Supabase Database

> **Système** : AI Development Team  
> **Rôle** : Database Engineer (agent IA)  
> **Version** : 1.0  
> **Date** : 2026-03-04  
> **Stack** : Supabase · PostgreSQL 15+ · Row Level Security · Next.js API Routes  
> **Scope** : Conception, sécurisation et exploitation d'une base de données multi-tenant

---

## Table des matières

1. [Mission du skill](#1-mission-du-skill)
2. [Structure des tables](#2-structure-des-tables)
3. [Gestion du multi-tenant (household_id)](#3-gestion-du-multi-tenant-household_id)
4. [Row Level Security](#4-row-level-security)
5. [Bonnes pratiques Supabase](#5-bonnes-pratiques-supabase)
6. [Sécurité des données](#6-sécurité-des-données)

---

## 1. Mission du skill

Le skill Supabase Database permet à un agent IA jouant le rôle de **Database Engineer** de concevoir, migrer et sécuriser une base de données Postgres multi-tenant hébergée sur Supabase.

Son objectif central est de **garantir l'isolation des données entre foyers, la cohérence relationnelle et la sécurité des accès** — à la fois par la structure des tables et par les policies Row Level Security (RLS).

Le Database Engineer ne code pas le frontend ni les API Routes. Il est responsable du schéma, des migrations, des policies RLS, des indexes, des fonctions SQL et des triggers. Tout ce qui touche à la donnée en base lui appartient.

> **Principe directeur** : *La sécurité des données ne se délègue pas à l'application — elle se garantit au niveau de la base de données via RLS.*

---

## 2. Structure des tables

### 2.1 Vue d'ensemble du schéma

```
auth.users (Supabase géré)
    │
    │ 1─────N
    ▼
profiles                ← Données publiques du profil utilisateur
    │
    │ 1─────N
    ▼
household_members ──────► households          ← Foyers + code d'invitation
    │                         │
    │                         │ 1─────N
    │                    ┌────┴──────────────┐
    │                    ▼                   ▼
    │                  tasks           shopping_items
    │                    
    └──────────────► (created_by, assigned_to sur tasks)
```

### 2.2 DDL complet — schéma public

```sql
-- ═══════════════════════════════════════════════════════
-- EXTENSIONS
-- ═══════════════════════════════════════════════════════
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- gen_random_uuid() (dispo par défaut PG14+)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- Recherche full-text sur les noms


-- ═══════════════════════════════════════════════════════
-- TYPES ÉNUMÉRÉS
-- ═══════════════════════════════════════════════════════
CREATE TYPE household_role AS ENUM ('admin', 'member');


-- ═══════════════════════════════════════════════════════
-- TABLE : profiles
-- Données publiques du profil utilisateur
-- Créée automatiquement via trigger on_auth_user_created
-- ═══════════════════════════════════════════════════════
CREATE TABLE public.profiles (
    id            UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name  TEXT        NOT NULL DEFAULT '',
    first_name    TEXT,
    last_name     TEXT,
    avatar_url    TEXT,
    language      TEXT        NOT NULL DEFAULT 'fr'
                              CHECK (language IN ('fr', 'en')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.profiles IS 'Profil public de chaque utilisateur, lié 1-1 à auth.users';


-- ═══════════════════════════════════════════════════════
-- TABLE : households
-- Représente un foyer familial ou une colocation
-- ═══════════════════════════════════════════════════════
CREATE TABLE public.households (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name           TEXT        NOT NULL
                               CHECK (char_length(name) BETWEEN 2 AND 50),
    invite_code    TEXT        NOT NULL UNIQUE
                               DEFAULT upper(substring(md5(gen_random_uuid()::text), 1, 6)),
    created_by     UUID        NOT NULL REFERENCES auth.users(id),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  public.households             IS 'Foyers — unité d''isolation centrale du multi-tenant';
COMMENT ON COLUMN public.households.invite_code IS 'Code alphanumérique 6 chars, insensible à la casse';
COMMENT ON COLUMN public.households.created_by  IS 'Référence auth.users — pas household_members (chicken-and-egg)';


-- ═══════════════════════════════════════════════════════
-- TABLE : household_members
-- Table de jonction user ↔ foyer avec rôle
-- ═══════════════════════════════════════════════════════
CREATE TABLE public.household_members (
    id           UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    household_id UUID          NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
    profile_id   UUID          NOT NULL REFERENCES public.profiles(id)   ON DELETE CASCADE,
    role         household_role NOT NULL DEFAULT 'member',
    joined_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT household_members_unique_member UNIQUE (household_id, profile_id)
);

COMMENT ON TABLE public.household_members IS 'Appartenance et rôle d''un utilisateur dans un foyer';
COMMENT ON CONSTRAINT household_members_unique_member
    ON public.household_members IS 'Un utilisateur ne peut appartenir qu''une fois au même foyer';


-- ═══════════════════════════════════════════════════════
-- TABLE : tasks
-- Tâches du foyer
-- ═══════════════════════════════════════════════════════
CREATE TABLE public.tasks (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    household_id UUID        NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
    title        TEXT        NOT NULL
                             CHECK (char_length(title) BETWEEN 1 AND 100),
    description  TEXT        CHECK (char_length(description) <= 500),
    is_completed BOOLEAN     NOT NULL DEFAULT false,
    created_by   UUID        REFERENCES public.profiles(id) ON DELETE SET NULL,
    assigned_to  UUID        REFERENCES public.profiles(id) ON DELETE SET NULL,
    due_date     DATE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  public.tasks              IS 'Tâches d''un foyer — scoped par household_id';
COMMENT ON COLUMN public.tasks.assigned_to  IS 'NULL = non assignée';
COMMENT ON COLUMN public.tasks.due_date     IS 'NULL = pas d''échéance';


-- ═══════════════════════════════════════════════════════
-- TABLE : shopping_items
-- Articles de la liste de courses
-- ═══════════════════════════════════════════════════════
CREATE TABLE public.shopping_items (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    household_id UUID        NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
    name         TEXT        NOT NULL
                             CHECK (char_length(name) BETWEEN 1 AND 100),
    quantity     TEXT        CHECK (char_length(quantity) <= 50),
    is_purchased BOOLEAN     NOT NULL DEFAULT false,
    purchased_by UUID        REFERENCES public.profiles(id) ON DELETE SET NULL,
    purchased_at TIMESTAMPTZ,
    created_by   UUID        REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  public.shopping_items                IS 'Articles de courses — scoped par household_id';
COMMENT ON COLUMN public.shopping_items.quantity       IS 'Texte libre : "1 kg", "3 bouteilles"';
COMMENT ON COLUMN public.shopping_items.purchased_at   IS 'Renseigné automatiquement via trigger';
```

### 2.3 Indexes de performance

```sql
-- ─── profiles ────────────────────────────────────────────────
-- Pas d'index supplémentaire — PK uuid suffit

-- ─── households ──────────────────────────────────────────────
-- Index sur invite_code pour le lookup JOIN (insensible à la casse)
CREATE INDEX idx_households_invite_code
    ON public.households (lower(invite_code));

-- ─── household_members ───────────────────────────────────────
-- Index couvrant pour "quels foyers appartient cet user ?"
CREATE INDEX idx_household_members_profile_id
    ON public.household_members (profile_id);

-- Index couvrant pour "quels membres a ce foyer ?"
CREATE INDEX idx_household_members_household_id
    ON public.household_members (household_id);

-- ─── tasks ───────────────────────────────────────────────────
-- Index principal : liste des tâches d'un foyer, triées par date décroissante
CREATE INDEX idx_tasks_household_created
    ON public.tasks (household_id, created_at DESC);

-- Index pour filtrer les tâches non complétées (dashboard)
CREATE INDEX idx_tasks_household_incomplete
    ON public.tasks (household_id)
    WHERE is_completed = false;

-- Index pour les tâches assignées à un membre
CREATE INDEX idx_tasks_assigned_to
    ON public.tasks (assigned_to)
    WHERE assigned_to IS NOT NULL;

-- ─── shopping_items ──────────────────────────────────────────
-- Index principal : liste des articles d'un foyer
CREATE INDEX idx_shopping_household_created
    ON public.shopping_items (household_id, created_at DESC);

-- Index pour les articles non achetés (liste de courses active)
CREATE INDEX idx_shopping_not_purchased
    ON public.shopping_items (household_id)
    WHERE is_purchased = false;
```

### 2.4 Triggers

```sql
-- ─── Trigger : updated_at automatique ───────────────────────
-- Fonction réutilisée par toutes les tables avec updated_at

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_households_updated_at
    BEFORE UPDATE ON public.households
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_tasks_updated_at
    BEFORE UPDATE ON public.tasks
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─── Trigger : création automatique du profil ───────────────
-- Déclenché par Supabase Auth sur chaque inscription

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, display_name)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1))
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ─── Trigger : créateur du foyer → admin automatique ────────
-- Quand un foyer est créé, son créateur devient admin

CREATE OR REPLACE FUNCTION public.handle_new_household()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.household_members (household_id, profile_id, role)
    VALUES (NEW.id, NEW.created_by, 'admin');
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_household_created
    AFTER INSERT ON public.households
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_household();


-- ─── Trigger : purchased_at automatique ─────────────────────
-- Renseigne purchased_at quand is_purchased passe à true

CREATE OR REPLACE FUNCTION public.handle_item_purchased()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.is_purchased = true AND OLD.is_purchased = false THEN
        NEW.purchased_at = now();
    END IF;
    IF NEW.is_purchased = false THEN
        NEW.purchased_at = NULL;
        NEW.purchased_by  = NULL;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_shopping_purchased_at
    BEFORE UPDATE ON public.shopping_items
    FOR EACH ROW EXECUTE FUNCTION public.handle_item_purchased();
```

---

## 3. Gestion du multi-tenant (household_id)

### 3.1 Principe d'isolation par household_id

FoyerApp est une application **multi-tenant logique** : toutes les données métier sont isolées par `household_id`. Un utilisateur peut appartenir à plusieurs foyers — chaque entité (tâche, article) appartient à **un seul foyer**.

```
Règle fondamentale :
  Toute table contenant des données métier DOIT avoir une colonne household_id NOT NULL
  avec une FK vers households(id) ON DELETE CASCADE.

  ✅ tasks.household_id
  ✅ shopping_items.household_id
  ❌ Une table sans household_id = donnée globale non isolée (interdit hors profiles)
```

### 3.2 Requête d'appartenance — pattern standard

Toute requête qui doit vérifier qu'un utilisateur a le droit d'accéder à un foyer utilise ce sous-select :

```sql
-- Pattern réutilisable : "l'utilisateur courant est membre de ce foyer"

EXISTS (
    SELECT 1
    FROM   public.household_members hm
    WHERE  hm.household_id = <table>.household_id
    AND    hm.profile_id   = auth.uid()
)

-- Exemples d'application :

-- Sélectionner les tâches accessibles à l'utilisateur courant
SELECT *
FROM   public.tasks t
WHERE  EXISTS (
    SELECT 1 FROM public.household_members
    WHERE  household_id = t.household_id
    AND    profile_id   = auth.uid()
);

-- Sélectionner uniquement les foyers dont l'utilisateur est admin
SELECT h.*
FROM   public.households h
JOIN   public.household_members hm
       ON hm.household_id = h.id
WHERE  hm.profile_id = auth.uid()
AND    hm.role       = 'admin';
```

### 3.3 Rejoindre un foyer via code — fonction SQL

```sql
-- Fonction sécurisée pour rejoindre un foyer via son code d'invitation
-- Appelée depuis une API Route (client service role)

CREATE OR REPLACE FUNCTION public.join_household_by_code(
    p_invite_code TEXT,
    p_profile_id  UUID
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_household   public.households%ROWTYPE;
    v_existing    public.household_members%ROWTYPE;
BEGIN
    -- Lookup du foyer (insensible à la casse)
    SELECT * INTO v_household
    FROM   public.households
    WHERE  lower(invite_code) = lower(p_invite_code);

    IF NOT FOUND THEN
        RETURN json_build_object('error', 'CODE_INVALID', 'message', 'Code invalide ou introuvable');
    END IF;

    -- Vérifier si déjà membre
    SELECT * INTO v_existing
    FROM   public.household_members
    WHERE  household_id = v_household.id
    AND    profile_id   = p_profile_id;

    IF FOUND THEN
        RETURN json_build_object('error', 'ALREADY_MEMBER', 'message', 'Vous êtes déjà membre de ce foyer');
    END IF;

    -- Créer l'adhésion
    INSERT INTO public.household_members (household_id, profile_id, role)
    VALUES (v_household.id, p_profile_id, 'member');

    RETURN json_build_object(
        'success', true,
        'household_id', v_household.id,
        'household_name', v_household.name
    );
END;
$$;
```

### 3.4 Régénération du code d'invitation

```sql
-- Régénérer le code d'invitation d'un foyer (admin uniquement)
-- Vérification du rôle effectuée dans l'API Route avant l'appel

CREATE OR REPLACE FUNCTION public.regenerate_invite_code(p_household_id UUID)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_new_code TEXT;
BEGIN
    -- Générer un code unique
    LOOP
        v_new_code := upper(substring(md5(gen_random_uuid()::text), 1, 6));
        EXIT WHEN NOT EXISTS (
            SELECT 1 FROM public.households WHERE invite_code = v_new_code
        );
    END LOOP;

    UPDATE public.households
    SET    invite_code = v_new_code,
           updated_at  = now()
    WHERE  id          = p_household_id;

    RETURN v_new_code;
END;
$$;
```

### 3.5 Vue agrégée pour le dashboard

```sql
-- Vue matérialisée du résumé par foyer (utilisée par HOME-01)

CREATE OR REPLACE VIEW public.household_dashboard AS
SELECT
    h.id                                      AS household_id,
    h.name                                    AS household_name,
    COUNT(t.id) FILTER (WHERE NOT t.is_completed) AS pending_tasks,
    COUNT(s.id) FILTER (WHERE NOT s.is_purchased)  AS pending_shopping_items
FROM      public.households       h
LEFT JOIN public.tasks            t ON t.household_id = h.id
LEFT JOIN public.shopping_items   s ON s.household_id = h.id
GROUP BY  h.id, h.name;

COMMENT ON VIEW public.household_dashboard IS 'Agrégats dashboard — toujours passer par RLS';
```

---

## 4. Row Level Security

### 4.1 Principe et activation

RLS est activé sur **toutes les tables métier**. C'est la dernière ligne de défense : même si une API Route est compromise, les données des autres foyers restent inaccessibles.

```sql
-- Activer RLS sur toutes les tables (OBLIGATOIRE)
ALTER TABLE public.profiles         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.households       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.household_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shopping_items   ENABLE ROW LEVEL SECURITY;

-- Important : sans policy définie, RLS bloque TOUT accès (deny by default)
-- Il faut créer des policies explicites pour chaque opération autorisée.
```

### 4.2 Policies — profiles

```sql
-- Un utilisateur voit son propre profil
CREATE POLICY "profiles_select_own"
ON public.profiles FOR SELECT
USING (id = auth.uid());

-- Un utilisateur voit les profils des membres de ses foyers
CREATE POLICY "profiles_select_household_members"
ON public.profiles FOR SELECT
USING (
    id IN (
        SELECT hm.profile_id
        FROM   public.household_members hm
        WHERE  hm.household_id IN (
            SELECT household_id
            FROM   public.household_members
            WHERE  profile_id = auth.uid()
        )
    )
);

-- Un utilisateur ne modifie que son propre profil
CREATE POLICY "profiles_update_own"
ON public.profiles FOR UPDATE
USING  (id = auth.uid())
WITH CHECK (id = auth.uid());

-- Pas de DELETE direct (suppression via auth.users CASCADE)
-- Pas d'INSERT direct (via trigger handle_new_user)
```

### 4.3 Policies — households

```sql
-- Un membre voit les foyers dont il fait partie
CREATE POLICY "households_select_member"
ON public.households FOR SELECT
USING (
    id IN (
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
    )
);

-- Tout utilisateur authentifié peut créer un foyer
CREATE POLICY "households_insert_authenticated"
ON public.households FOR INSERT
WITH CHECK (auth.uid() IS NOT NULL AND created_by = auth.uid());

-- Seul un admin peut modifier le nom du foyer
CREATE POLICY "households_update_admin"
ON public.households FOR UPDATE
USING (
    id IN (
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
        AND    role = 'admin'
    )
)
WITH CHECK (
    id IN (
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
        AND    role = 'admin'
    )
);

-- Seul un admin peut supprimer un foyer
CREATE POLICY "households_delete_admin"
ON public.households FOR DELETE
USING (
    id IN (
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
        AND    role = 'admin'
    )
);
```

### 4.4 Policies — household_members

```sql
-- Un membre voit les autres membres de ses foyers
CREATE POLICY "household_members_select_same_household"
ON public.household_members FOR SELECT
USING (
    household_id IN (
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
    )
);

-- Un utilisateur peut rejoindre un foyer (INSERT sur lui-même)
-- Note : la vérification du code se fait dans join_household_by_code()
CREATE POLICY "household_members_insert_self"
ON public.household_members FOR INSERT
WITH CHECK (profile_id = auth.uid());

-- Un admin peut changer le rôle d'un membre du foyer
CREATE POLICY "household_members_update_admin"
ON public.household_members FOR UPDATE
USING (
    household_id IN (
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
        AND    role = 'admin'
    )
)
WITH CHECK (
    household_id IN (
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
        AND    role = 'admin'
    )
);

-- Un membre peut quitter un foyer (DELETE sur lui-même)
-- Un admin peut exclure un membre
CREATE POLICY "household_members_delete"
ON public.household_members FOR DELETE
USING (
    profile_id = auth.uid()  -- Quitter soi-même
    OR
    household_id IN (         -- Admin qui exclut
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
        AND    role = 'admin'
    )
);
```

### 4.5 Policies — tasks

```sql
-- Un membre du foyer voit toutes les tâches du foyer
CREATE POLICY "tasks_select_member"
ON public.tasks FOR SELECT
USING (
    household_id IN (
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
    )
);

-- Un membre peut créer une tâche dans son foyer
CREATE POLICY "tasks_insert_member"
ON public.tasks FOR INSERT
WITH CHECK (
    household_id IN (
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
    )
);

-- Un membre peut modifier une tâche de son foyer
CREATE POLICY "tasks_update_member"
ON public.tasks FOR UPDATE
USING (
    household_id IN (
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
    )
)
WITH CHECK (
    household_id IN (
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
    )
);

-- Un membre peut supprimer une tâche de son foyer
CREATE POLICY "tasks_delete_member"
ON public.tasks FOR DELETE
USING (
    household_id IN (
        SELECT household_id
        FROM   public.household_members
        WHERE  profile_id = auth.uid()
    )
);
```

### 4.6 Policies — shopping_items

```sql
-- Même pattern que tasks — un membre du foyer a accès complet

CREATE POLICY "shopping_select_member"
ON public.shopping_items FOR SELECT
USING (
    household_id IN (
        SELECT household_id FROM public.household_members
        WHERE  profile_id = auth.uid()
    )
);

CREATE POLICY "shopping_insert_member"
ON public.shopping_items FOR INSERT
WITH CHECK (
    household_id IN (
        SELECT household_id FROM public.household_members
        WHERE  profile_id = auth.uid()
    )
);

CREATE POLICY "shopping_update_member"
ON public.shopping_items FOR UPDATE
USING (
    household_id IN (
        SELECT household_id FROM public.household_members
        WHERE  profile_id = auth.uid()
    )
)
WITH CHECK (
    household_id IN (
        SELECT household_id FROM public.household_members
        WHERE  profile_id = auth.uid()
    )
);

CREATE POLICY "shopping_delete_member"
ON public.shopping_items FOR DELETE
USING (
    household_id IN (
        SELECT household_id FROM public.household_members
        WHERE  profile_id = auth.uid()
    )
);
```

### 4.7 Helper function — réduire la duplication RLS

```sql
-- Fonction helper pour éviter de répéter le sous-select dans chaque policy
-- Utilisée en tant que fonction de sécurité stable (exécutée une fois par requête)

CREATE OR REPLACE FUNCTION public.is_household_member(p_household_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM   public.household_members
        WHERE  household_id = p_household_id
        AND    profile_id   = auth.uid()
    );
$$;

CREATE OR REPLACE FUNCTION public.is_household_admin(p_household_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM   public.household_members
        WHERE  household_id = p_household_id
        AND    profile_id   = auth.uid()
        AND    role         = 'admin'
    );
$$;

-- Usage simplifié dans les policies :
-- USING (public.is_household_member(household_id))
-- USING (public.is_household_admin(household_id))
```

### 4.8 Tester les policies RLS

```sql
-- ─── Simuler un utilisateur pour tester les policies ─────────

-- Activer la simulation
SET LOCAL role TO authenticated;
SET LOCAL request.jwt.claims TO '{"sub": "uuid-de-l-utilisateur-test"}';

-- Tester qu'un utilisateur ne voit pas les tâches d'un autre foyer
SELECT * FROM public.tasks WHERE household_id = 'foyer-autre-uuid';
-- → Doit retourner 0 lignes

-- Tester qu'un utilisateur voit bien ses propres tâches
SELECT * FROM public.tasks WHERE household_id = 'son-foyer-uuid';
-- → Doit retourner ses tâches

-- Réinitialiser
RESET role;
RESET request.jwt.claims;

-- ─── Vérifier qu'une table a bien RLS activé ─────────────────
SELECT tablename, rowsecurity
FROM   pg_tables
WHERE  schemaname = 'public'
ORDER  BY tablename;
-- rowsecurity = true sur toutes les tables métier

-- ─── Lister toutes les policies actives ──────────────────────
SELECT tablename, policyname, cmd, qual
FROM   pg_policies
WHERE  schemaname = 'public'
ORDER  BY tablename, policyname;
```

---

## 5. Bonnes pratiques Supabase

### 5.1 Migrations versionnées

```
Toutes les modifications de schéma passent par des fichiers de migration versionnés.
Jamais de modification directe via le dashboard Supabase en production.

Structure :
  supabase/
  └── migrations/
      ├── 20260301000000_init_schema.sql          ← Schéma initial
      ├── 20260302000000_add_rls_policies.sql     ← Policies RLS
      ├── 20260303000000_add_indexes.sql          ← Index de performance
      └── 20260304000000_add_triggers.sql         ← Triggers et fonctions

Commandes :
  supabase migration new <nom>    → Crée un nouveau fichier de migration
  supabase db push               → Applique les migrations en local
  supabase db push --db-url <url> → Applique en production
```

### 5.2 Nommage des migrations et des objets

```sql
-- Conventions de nommage :
-- Tables     : snake_case, pluriel           → household_members
-- Colonnes   : snake_case                    → created_at, is_completed
-- Indexes    : idx_<table>_<colonnes>        → idx_tasks_household_created
-- Triggers   : trg_<table>_<action>          → trg_tasks_updated_at
-- Fonctions  : verbe_sujet                   → handle_new_user, set_updated_at
-- Policies   : <table>_<opération>_<acteur>  → tasks_select_member
-- Contraintes : <table>_<description>        → household_members_unique_member
-- Types      : snake_case                    → household_role
```

### 5.3 Génération des types TypeScript

```bash
# Générer les types depuis le schéma local
supabase gen types typescript --local > src/types/database.ts

# Générer depuis le projet Supabase Cloud
supabase gen types typescript --project-id <project_ref> > src/types/database.ts
```

```typescript
// src/types/database.ts (extrait généré)
export type Database = {
  public: {
    Tables: {
      tasks: {
        Row: {
          id: string
          household_id: string
          title: string
          description: string | null
          is_completed: boolean
          created_by: string | null
          assigned_to: string | null
          due_date: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          household_id: string
          title: string
          // ...
        }
        Update: {
          title?: string
          is_completed?: boolean
          // ...
        }
      }
      // ...
    }
  }
}

// Utilisation dans les API Routes :
import type { Database } from '@/types/database'
type Task = Database['public']['Tables']['tasks']['Row']
type NewTask = Database['public']['Tables']['tasks']['Insert']
```

### 5.4 Gestion des erreurs Postgres

```typescript
// lib/utils/supabase-errors.ts
// Mapper les codes d'erreur Postgres vers des messages utilisateur

const PG_ERROR_CODES: Record<string, string> = {
  '23505': 'Cette valeur existe déjà',           // unique_violation
  '23503': 'Référence introuvable',               // foreign_key_violation
  '23514': 'La valeur ne respecte pas les règles', // check_violation
  '42501': 'Permission refusée',                  // insufficient_privilege
  'PGRST116': 'Aucun résultat trouvé',            // Supabase: 0 rows returned
}

export function mapSupabaseError(error: { code?: string; message: string }): string {
  if (error.code && PG_ERROR_CODES[error.code]) {
    return PG_ERROR_CODES[error.code]
  }
  // Log l'erreur technique côté serveur
  console.error('[Supabase error]', error)
  // Message générique côté client
  return 'Une erreur est survenue. Veuillez réessayer.'
}
```

### 5.5 Realtime — configuration et abonnements

```sql
-- Activer Realtime sur les tables nécessaires
-- (dans le dashboard Supabase → Database → Replication)
-- Ou via SQL :

ALTER PUBLICATION supabase_realtime ADD TABLE public.tasks;
ALTER PUBLICATION supabase_realtime ADD TABLE public.shopping_items;

-- NE PAS activer Realtime sur :
-- profiles (données sensibles, faible fréquence de changement)
-- households (rarement modifié)
-- household_members (faible fréquence)
```

```typescript
// Subscription Realtime typée
import type { Database } from '@/types/database'

type TaskRow = Database['public']['Tables']['tasks']['Row']

const channel = supabase
  .channel(`tasks:${householdId}`)
  .on<TaskRow>(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'tasks',
      filter: `household_id=eq.${householdId}`,
    },
    (payload) => {
      // payload.new et payload.old sont typés TaskRow
      console.log(payload.eventType, payload.new)
    }
  )
  .subscribe()

// Toujours unsubscribe dans le cleanup React
return () => { supabase.removeChannel(channel) }
```

### 5.6 Pagination des listes

```typescript
// API Route avec pagination cursor-based
// Plus performante que offset/limit sur les grandes tables

export async function GET(request: NextRequest) {
  const cursor    = request.nextUrl.searchParams.get('cursor')     // created_at ISO string
  const limit     = parseInt(request.nextUrl.searchParams.get('limit') ?? '20', 10)
  const householdId = request.nextUrl.searchParams.get('householdId')

  let query = supabase
    .from('tasks')
    .select('*')
    .eq('household_id', householdId!)
    .order('created_at', { ascending: false })
    .limit(Math.min(limit, 50))  // Cap à 50 pour protéger la DB

  if (cursor) {
    query = query.lt('created_at', cursor)  // Récupérer les items AVANT le curseur
  }

  const { data, error } = await query
  if (error) throw error

  return NextResponse.json({
    items: data,
    nextCursor: data.length === limit ? data[data.length - 1].created_at : null,
    hasMore: data.length === limit,
  })
}
```

---

## 6. Sécurité des données

### 6.1 Modèle de confiance

```
CLIENT (navigateur)
  │
  │  anon key — RLS actif — accès limité aux données de l'utilisateur connecté
  ▼
SUPABASE AUTH + RLS
  │
  │  service_role key — RLS BYPASSÉ — accès total
  ▼
API ROUTES Next.js (serveur uniquement)
  │
  │  Toute la logique de vérification d'accès est ici
  ▼
SUPABASE POSTGRES

Règle : le client browser ne doit jamais avoir plus d'accès que ce que RLS lui accorde.
        La service_role key n'apparaît jamais côté client.
```

### 6.2 Variables d'environnement — règles strictes

```bash
# .env.local

# ✅ NEXT_PUBLIC_ → accessible browser + serveur — RLS protège
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...

# ✅ Sans préfixe → serveur UNIQUEMENT (API Routes, Server Components)
# ❌ Ne jamais utiliser dans un composant avec 'use client'
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Vérification au démarrage (lib/env.ts) :
# La présence de SUPABASE_SERVICE_ROLE_KEY dans le bundle client = faille critique
```

### 6.3 Données sensibles — règles de stockage

```sql
-- Ce qui NE DOIT PAS être stocké en clair dans la DB :
-- ❌ Mots de passe       → gérés par Supabase Auth (bcrypt)
-- ❌ Tokens              → gérés par Supabase Auth (cookies HTTP-only)
-- ❌ Numéros de CB       → hors scope, jamais en DB applicative
-- ❌ Codes PIN           → si nécessaire : hash bcrypt via pgcrypto

-- Ce qui peut être stocké :
-- ✅ Emails (via auth.users — pas dupliqués dans profiles)
-- ✅ Noms d'affichage, avatars
-- ✅ Données métier (tâches, courses, montants)
-- ✅ Codes d'invitation (non sensibles — peuvent être régénérés)
```

### 6.4 Protection contre les injections SQL

```typescript
// Supabase JS utilise des requêtes paramétrées par défaut — pas d'injection possible
// via les méthodes .eq(), .insert(), .update()

// ✅ Sûr — paramétré automatiquement
const { data } = await supabase
  .from('tasks')
  .select()
  .eq('household_id', householdId)   // householdId est paramétré

// ⚠️ Attention avec .rpc() et les fonctions SQL — utiliser des paramètres
const { data } = await supabase.rpc('join_household_by_code', {
  p_invite_code: code,
  p_profile_id: userId,
})

// ❌ Ne jamais interpoler des valeurs utilisateur dans du SQL brut
// Interdit dans les fonctions plpgsql :
-- EXECUTE 'SELECT * FROM tasks WHERE id = ' || p_id;  -- INJECTION
-- EXECUTE format('SELECT * FROM tasks WHERE id = %L', p_id);  -- OK avec %L
```

### 6.5 Audit et traçabilité

```sql
-- Colonnes de traçabilité sur toutes les tables métier :
-- created_at  : TIMESTAMPTZ NOT NULL DEFAULT now()
-- updated_at  : TIMESTAMPTZ NOT NULL DEFAULT now() (mis à jour par trigger)
-- created_by  : UUID REFERENCES profiles(id) ON DELETE SET NULL

-- Pour les opérations critiques (ex : exclusion d'un membre),
-- envisager une table d'audit en v2 :

CREATE TABLE public.audit_log (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name   TEXT        NOT NULL,
    record_id    UUID        NOT NULL,
    action       TEXT        NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data     JSONB,
    new_data     JSONB,
    performed_by UUID        REFERENCES auth.users(id),
    performed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.6 Checklist de sécurité — avant déploiement

```
SCHÉMA
- [ ] RLS activé sur toutes les tables avec données métier
- [ ] Toutes les tables métier ont household_id NOT NULL
- [ ] Les FKs ont ON DELETE CASCADE (households) ou ON DELETE SET NULL (profiles)
- [ ] Les contraintes CHECK couvrent les champs à longueur limitée
- [ ] Aucune colonne sensitive stockée en clair

RLS POLICIES
- [ ] Chaque table a des policies pour les 4 opérations (SELECT, INSERT, UPDATE, DELETE)
- [ ] Les policies INSERT ont WITH CHECK (pas seulement USING)
- [ ] Les policies vérifient auth.uid() IS NOT NULL
- [ ] Test réalisé avec simulation de différents utilisateurs

SUPABASE CONFIGURATION
- [ ] service_role key absente du bundle client Next.js
- [ ] Realtime activé seulement sur les tables nécessaires (tasks, shopping_items)
- [ ] Email confirm désactivé ou configuré si requis
- [ ] JWT expiry configuré (défaut : 3600s — acceptable)

MIGRATIONS
- [ ] Toutes les modifications passent par des fichiers de migration versionnés
- [ ] Les migrations sont idempotentes (IF NOT EXISTS, OR REPLACE)
- [ ] Les types TypeScript sont régénérés après chaque migration
- [ ] La migration est testée en local avant push en production
```

---

## Annexes

### A. Requêtes de diagnostic fréquentes

```sql
-- Lister les membres d'un foyer avec leur profil
SELECT p.display_name, p.avatar_url, hm.role, hm.joined_at
FROM   public.household_members hm
JOIN   public.profiles p ON p.id = hm.profile_id
WHERE  hm.household_id = '<household_id>';

-- Vérifier qu'un utilisateur est admin d'un foyer
SELECT EXISTS (
    SELECT 1 FROM public.household_members
    WHERE  household_id = '<household_id>'
    AND    profile_id   = '<user_id>'
    AND    role         = 'admin'
) AS is_admin;

-- Statistiques d'un foyer
SELECT
    COUNT(*) FILTER (WHERE NOT is_completed)  AS pending_tasks,
    COUNT(*) FILTER (WHERE is_completed)       AS done_tasks,
    COUNT(*)                                   AS total_tasks
FROM public.tasks
WHERE household_id = '<household_id>';

-- Taille des tables (utile pour surveiller les limites Supabase Free)
SELECT
    relname                               AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    n_live_tup                            AS row_count
FROM   pg_stat_user_tables
WHERE  schemaname = 'public'
ORDER  BY pg_total_relation_size(relid) DESC;
```

### B. Antipatterns à éviter

| Antipattern | Risque | Correction |
|---|---|---|
| Table sans household_id | Fuite de données inter-foyers | FK household_id NOT NULL obligatoire |
| RLS désactivé "temporairement" | Faille permanente si oublié | RLS activé dès la création de table |
| Policy sans WITH CHECK sur INSERT | Contournement RLS possible | Toujours USING + WITH CHECK sur INSERT/UPDATE |
| service_role dans un composant client | Fuite de credentials | Serveur uniquement, jamais NEXT_PUBLIC_ |
| Pas de contrainte UNIQUE sur invite_code | Collision silencieuse | UNIQUE + loop de génération |
| ON DELETE CASCADE absent sur tasks | Orphelins en base | CASCADE sur toutes les FKs vers households |
| Migration manuelle via dashboard | Schéma non versionné | Toujours via fichiers de migration |
| Offset pagination sur grande table | Performances dégradées | Cursor-based pagination |

### C. Limites Supabase Free et seuils d'alerte

| Ressource | Limite Free | Alerte à | Action |
|---|---|---|---|
| Base de données | 500 MB | 400 MB | Archiver les données anciennes |
| Bandwidth | 2 GB/mois | 1.5 GB | Optimiser les requêtes, activer CDN |
| Realtime connections | 200 simultanées | 150 | Limiter les abonnements actifs |
| Edge Functions | 500 000 invocations/mois | 400 000 | Passer au plan Pro |
| Storage | 1 GB | 800 MB | Nettoyer les avatars obsolètes |

### D. Références

| Ressource | URL |
|---|---|
| Supabase RLS Guide | https://supabase.com/docs/guides/auth/row-level-security |
| Supabase SSR Next.js | https://supabase.com/docs/guides/auth/server-side/nextjs |
| PostgreSQL RLS | https://www.postgresql.org/docs/current/ddl-rowsecurity.html |
| Supabase Realtime | https://supabase.com/docs/guides/realtime |
| Supabase CLI | https://supabase.com/docs/reference/cli |

### E. Références projet

| Document | Localisation |
|---|---|
| Architecture Overview | `docs/architecture/architecture_overview.md` |
| Next.js Development Skill | `ai/roles/nextjs_development.md` |
| Backlog AI Scrum | `docs/backlog/ai_scrum_backlog.md` |

---

*Ce document est la référence base de données pour l'agent IA Database Engineer. Il est mis à jour à chaque nouvelle migration ou évolution du schéma.*
