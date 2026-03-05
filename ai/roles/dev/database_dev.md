# Rôle — Database Developer (DB)

> **Système** : AI Development Team  
> **Agent** : Database Developer  
> **Version** : 1.0  
> **Date** : 2026-03-04  
> **Projet** : FoyerApp — mobile-first PWA  
> **Stack** : Supabase · PostgreSQL 15+ · Supabase CLI  
> **Référence skill** : `ai/roles/supabase_database.md`

---

## Table des matières

1. [Mission du rôle](#1-mission-du-rôle)
2. [Responsabilités](#2-responsabilités)
3. [Structure des tables](#3-structure-des-tables)
4. [Gestion multi-tenant](#4-gestion-multi-tenant)
5. [Row Level Security](#5-row-level-security)
6. [Bonnes pratiques](#6-bonnes-pratiques)

---

## 1. Mission du rôle

Le Database Developer est responsable de **tout ce qui vit dans Postgres** : le schéma des tables, les migrations, les policies RLS, les triggers, les indexes et les types TypeScript générés. Il est la fondation sur laquelle Backend et Frontend construisent.

Sa mission tient en une phrase :

> **Concevoir et maintenir un schéma Postgres correct, sécurisé et performant — garantissant l'isolation des données entre foyers par structure, pas uniquement par convention.**

Dans un système AI Development, le Database Developer est un **agent IA autonome** capable de :
- Analyser une User Story et déduire les changements de schéma nécessaires
- Écrire des migrations SQL versionnées, correctes et idempotentes
- Configurer RLS sur chaque nouvelle table dès sa création — sans attendre
- Générer et partager les types TypeScript avec Backend et Frontend après chaque migration
- Anticiper les risques de performance (index manquants, requêtes N+1) avant qu'ils arrivent

> **Règle d'or** : *L'isolation des données entre foyers est garantie par le schéma — pas seulement par les conventions de code. Une table sans `household_id NOT NULL` est une faille, pas un oubli.*

---

## 2. Responsabilités

### 2.1 Conception du schéma

Le Database Developer est le propriétaire du schéma. Toute modification de table, colonne, contrainte ou index passe par lui.

- Analyser les User Stories et identifier les tables, colonnes et relations nécessaires
- Définir les contraintes `NOT NULL`, `CHECK`, `UNIQUE` et `FOREIGN KEY` dès la création — jamais après-coup
- S'assurer que chaque table métier a `household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE`
- Choisir les types Postgres appropriés : `UUID` pour les IDs, `TIMESTAMPTZ` pour les dates, `TEXT` avec `CHECK` pour les chaînes bornées
- Concevoir le schéma pour les requêtes connues du Backend — pas en isolation

### 2.2 Migrations versionnées

Toute modification du schéma est une migration. Aucune modification directe via le dashboard Supabase.

- Créer les migrations dans `supabase/migrations/` avec le format `YYYYMMDDHHMMSS_description.sql`
- Chaque migration est **idempotente** : elle peut être appliquée plusieurs fois sans erreur (`IF NOT EXISTS`, `OR REPLACE`)
- Chaque migration est **atomique** : elle réussit entièrement ou échoue entièrement — grouper les instructions liées dans une transaction
- Tester chaque migration en local (`supabase db push`) avant tout push sur la branche feature
- Signaler au Backend Developer et à l'Infra Developer dès qu'une migration est prête à être appliquée

### 2.3 Row Level Security

RLS est activé sur chaque nouvelle table **dès sa création** — pas une fois la fonctionnalité livrée.

- Écrire les policies pour les 4 opérations : `SELECT`, `INSERT` (avec `WITH CHECK`), `UPDATE`, `DELETE`
- Utiliser les fonctions helper `is_household_member()` et `is_household_admin()` pour éviter la duplication
- Tester les policies en SQL avec simulation d'utilisateurs (`SET LOCAL role TO authenticated`)
- Partager le résultat des tests RLS avec le Testing Developer pour les tests d'intégration

### 2.4 Triggers et fonctions SQL

- Écrire les triggers pour automatiser les comportements prévisibles : `updated_at`, création du profil, admin automatique, `purchased_at`
- Toutes les fonctions SQL avec `SECURITY DEFINER` ont `SET search_path = public` — sans exception
- Les fonctions appelées par le Backend via `.rpc()` utilisent des paramètres nommés typés — jamais d'interpolation

### 2.5 Indexes de performance

- Créer les indexes selon les patterns de requêtes documentés par le Backend Developer
- Préférer les **indexes partiels** (`WHERE is_completed = false`) quand les filtres sont connus et stables
- Créer les indexes **composites** dans l'ordre sélectivité décroissante (colonne la plus sélective en premier)
- Ne pas créer d'index sur toutes les colonnes par défaut — mesurer avant d'ajouter

### 2.6 Types TypeScript et communication

- Régénérer les types TypeScript après chaque migration : `supabase gen types typescript --local > src/types/database.ts`
- Commiter le fichier `database.ts` mis à jour dans la même PR que la migration
- Signaler au Backend et Frontend developers que les types sont à jour
- Documenter tout breaking change de schéma avec un préavis d'un cycle minimum

---

## 3. Structure des tables

### 3.1 Schéma global — FoyerApp

```
auth.users  (géré par Supabase)
     │
     │ 1:1  (trigger on_auth_user_created)
     ▼
profiles                     ← Données publiques du profil
     │
     │ 1:N
     ▼
household_members ──────────► households          ← Foyers + code invitation
     │                              │
     │                              │ 1:N
     │                   ┌──────────┴──────────┐
     │                   ▼                     ▼
     │                 tasks            shopping_items
     │
     └──────────────► (created_by, assigned_to sur tasks)
```

### 3.2 Règles de conception par table

**profiles**
```
- id          : UUID PK, FK auth.users(id) ON DELETE CASCADE
- display_name: TEXT NOT NULL DEFAULT ''
- language    : TEXT NOT NULL DEFAULT 'fr' CHECK (IN ('fr', 'en'))
- created_at  : TIMESTAMPTZ NOT NULL DEFAULT now()
- updated_at  : TIMESTAMPTZ NOT NULL DEFAULT now()

Triggers : trg_profiles_updated_at, on_auth_user_created (INSERT automatique)
RLS      : SELECT (propre profil + membres du même foyer), UPDATE (soi-même)
           Pas d'INSERT direct (trigger), pas de DELETE direct (CASCADE depuis auth.users)
```

**households**
```
- id          : UUID PK DEFAULT gen_random_uuid()
- name        : TEXT NOT NULL CHECK (char_length BETWEEN 2 AND 50)
- invite_code : TEXT NOT NULL UNIQUE DEFAULT upper(substring(md5(gen_random_uuid()::text), 1, 6))
- created_by  : UUID NOT NULL REFERENCES auth.users(id)
- created_at  : TIMESTAMPTZ NOT NULL DEFAULT now()
- updated_at  : TIMESTAMPTZ NOT NULL DEFAULT now()

Note sur created_by : référence auth.users (pas household_members) — évite le
                       problème de chicken-and-egg à la création du foyer
Trigger  : on_household_created → INSERT automatique dans household_members (rôle admin)
RLS      : SELECT (membres), INSERT (authentifié), UPDATE/DELETE (admin)
```

**household_members**
```
- id          : UUID PK DEFAULT gen_random_uuid()
- household_id: UUID NOT NULL FK households(id) ON DELETE CASCADE
- profile_id  : UUID NOT NULL FK profiles(id)   ON DELETE CASCADE
- role        : household_role NOT NULL DEFAULT 'member'
- joined_at   : TIMESTAMPTZ NOT NULL DEFAULT now()
- UNIQUE (household_id, profile_id)   ← contrainte explicite, pas juste un index

Type enum : CREATE TYPE household_role AS ENUM ('admin', 'member')
RLS       : SELECT (même foyer), INSERT (soi-même via join), UPDATE (admin), DELETE (soi-même ou admin)
```

**tasks**
```
- id          : UUID PK DEFAULT gen_random_uuid()
- household_id: UUID NOT NULL FK households(id) ON DELETE CASCADE
- title       : TEXT NOT NULL CHECK (char_length BETWEEN 1 AND 100)
- description : TEXT CHECK (char_length <= 500)           ← NULLable intentionnellement
- is_completed: BOOLEAN NOT NULL DEFAULT false
- created_by  : UUID REFERENCES profiles(id) ON DELETE SET NULL   ← SET NULL, pas CASCADE
- assigned_to : UUID REFERENCES profiles(id) ON DELETE SET NULL   ← idem
- due_date    : DATE                                              ← NULLable = pas d'échéance
- created_at  : TIMESTAMPTZ NOT NULL DEFAULT now()
- updated_at  : TIMESTAMPTZ NOT NULL DEFAULT now()

Trigger : trg_tasks_updated_at
RLS     : CRUD complet pour tout membre du foyer
```

**shopping_items**
```
- id          : UUID PK DEFAULT gen_random_uuid()
- household_id: UUID NOT NULL FK households(id) ON DELETE CASCADE
- name        : TEXT NOT NULL CHECK (char_length BETWEEN 1 AND 100)
- quantity    : TEXT CHECK (char_length <= 50)                    ← Texte libre "1 kg", "3 bouteilles"
- is_purchased: BOOLEAN NOT NULL DEFAULT false
- purchased_by: UUID REFERENCES profiles(id) ON DELETE SET NULL
- purchased_at: TIMESTAMPTZ                                       ← Renseigné par trigger
- created_by  : UUID REFERENCES profiles(id) ON DELETE SET NULL
- created_at  : TIMESTAMPTZ NOT NULL DEFAULT now()

Trigger : trg_shopping_purchased_at (SET purchased_at=now() quand is_purchased passe à true,
                                      NULL quand is_purchased repasse à false)
RLS     : CRUD complet pour tout membre du foyer
```

### 3.3 Indexes — justification par cas

```sql
-- ─── household_members ────────────────────────────────────────────
-- Utilisé dans CHAQUE vérification d'appartenance (routes Backend)
CREATE INDEX idx_household_members_profile_id    ON household_members (profile_id);
CREATE INDEX idx_household_members_household_id  ON household_members (household_id);

-- ─── households ───────────────────────────────────────────────────
-- Lookup du code d'invitation — insensible à la casse
CREATE INDEX idx_households_invite_code ON households (lower(invite_code));

-- ─── tasks ────────────────────────────────────────────────────────
-- Liste principale : toutes les tâches d'un foyer, triées par date desc
CREATE INDEX idx_tasks_household_created
    ON tasks (household_id, created_at DESC);

-- Dashboard : uniquement les tâches non complétées (index partiel)
CREATE INDEX idx_tasks_household_incomplete
    ON tasks (household_id)
    WHERE is_completed = false;

-- Filtrage par assigné (vue "mes tâches")
CREATE INDEX idx_tasks_assigned_to
    ON tasks (assigned_to)
    WHERE assigned_to IS NOT NULL;

-- ─── shopping_items ───────────────────────────────────────────────
-- Liste principale : tous les articles d'un foyer
CREATE INDEX idx_shopping_household_created
    ON shopping_items (household_id, created_at DESC);

-- Liste active : articles non achetés uniquement
CREATE INDEX idx_shopping_not_purchased
    ON shopping_items (household_id)
    WHERE is_purchased = false;
```

### 3.4 Triggers — catalogue complet

```sql
-- ── 1. updated_at automatique ────────────────────────────────────
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

-- Appliqué sur : profiles, households, tasks
CREATE TRIGGER trg_profiles_updated_at  BEFORE UPDATE ON profiles  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_households_updated_at BEFORE UPDATE ON households FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_tasks_updated_at     BEFORE UPDATE ON tasks     FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── 2. Création automatique du profil à l'inscription ────────────
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public AS $$
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
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ── 3. Créateur du foyer → admin automatique ─────────────────────
CREATE OR REPLACE FUNCTION public.handle_new_household()
RETURNS TRIGGER LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public AS $$
BEGIN
    INSERT INTO public.household_members (household_id, profile_id, role)
    VALUES (NEW.id, NEW.created_by, 'admin');
    RETURN NEW;
END;
$$;
CREATE TRIGGER on_household_created
    AFTER INSERT ON households
    FOR EACH ROW EXECUTE FUNCTION handle_new_household();

-- ── 4. purchased_at automatique ──────────────────────────────────
CREATE OR REPLACE FUNCTION public.handle_item_purchased()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
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
    BEFORE UPDATE ON shopping_items
    FOR EACH ROW EXECUTE FUNCTION handle_item_purchased();
```

---

## 4. Gestion multi-tenant

### 4.1 Le principe fondamental

FoyerApp est une application **multi-tenant logique** : toutes les données métier sont isolées par `household_id`. Pas de tenant physiquement séparé — une seule base, des politiques d'isolation strictes.

```
Règle absolue :
  Toute table contenant des données métier DOIT avoir :

    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE

  Sans cette colonne et cette contrainte, la table n'a pas de place dans le schéma.

  ✅ tasks.household_id          → tâches d'un foyer
  ✅ shopping_items.household_id → courses d'un foyer
  ❌ Une table "notes" sans household_id → données globales = faille d'isolation
```

### 4.2 Règle de cascade

```sql
-- ON DELETE CASCADE sur household_id :
--   Supprimer un foyer supprime toutes ses données métier automatiquement
--   Pas d'orphelins, pas de nettoyage manuel

-- ON DELETE SET NULL sur les références à des profils (created_by, assigned_to) :
--   Supprimer un utilisateur ne supprime pas ses tâches
--   La donnée reste accessible aux autres membres du foyer

-- ON DELETE CASCADE sur household_members.profile_id :
--   Supprimer un utilisateur le retire de tous ses foyers automatiquement
```

### 4.3 Pattern de requête d'appartenance

```sql
-- Pattern réutilisable dans toutes les requêtes qui doivent
-- vérifier qu'un utilisateur appartient à un foyer

EXISTS (
    SELECT 1
    FROM   household_members
    WHERE  household_id = <alias_table>.household_id
    AND    profile_id   = auth.uid()
)

-- Exemples d'utilisation :

-- Dans une policy RLS (tâches)
USING (
    EXISTS (
        SELECT 1 FROM household_members
        WHERE household_id = tasks.household_id
        AND   profile_id   = auth.uid()
    )
)

-- Dans une requête directe (dashboard)
SELECT * FROM tasks t
WHERE EXISTS (
    SELECT 1 FROM household_members
    WHERE household_id = t.household_id
    AND   profile_id   = auth.uid()
);
```

### 4.4 Fonctions SQL pour les opérations métier

```sql
-- ── join_household_by_code ────────────────────────────────────────
-- Appelée par le Backend via .rpc() — valide le code, crée le membership
CREATE OR REPLACE FUNCTION public.join_household_by_code(
    p_invite_code TEXT,
    p_profile_id  UUID
)
RETURNS JSON LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public AS $$
DECLARE
    v_household   public.households%ROWTYPE;
    v_existing    public.household_members%ROWTYPE;
BEGIN
    SELECT * INTO v_household
    FROM   households
    WHERE  lower(invite_code) = lower(p_invite_code);

    IF NOT FOUND THEN
        RETURN json_build_object('error', 'CODE_INVALID');
    END IF;

    SELECT * INTO v_existing
    FROM   household_members
    WHERE  household_id = v_household.id AND profile_id = p_profile_id;

    IF FOUND THEN
        RETURN json_build_object('error', 'ALREADY_MEMBER');
    END IF;

    INSERT INTO household_members (household_id, profile_id, role)
    VALUES (v_household.id, p_profile_id, 'member');

    RETURN json_build_object(
        'success', true,
        'household_id', v_household.id,
        'household_name', v_household.name
    );
END;
$$;

-- ── regenerate_invite_code ────────────────────────────────────────
-- Boucle jusqu'à trouver un code unique — sécurisé contre les collisions
CREATE OR REPLACE FUNCTION public.regenerate_invite_code(p_household_id UUID)
RETURNS TEXT LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public AS $$
DECLARE v_new_code TEXT;
BEGIN
    LOOP
        v_new_code := upper(substring(md5(gen_random_uuid()::text), 1, 6));
        EXIT WHEN NOT EXISTS (SELECT 1 FROM households WHERE invite_code = v_new_code);
    END LOOP;
    UPDATE households SET invite_code = v_new_code, updated_at = now() WHERE id = p_household_id;
    RETURN v_new_code;
END;
$$;
```

### 4.5 Règles de nommage du schéma

```
Tables      : snake_case, pluriel              → household_members
Colonnes    : snake_case                       → created_at, is_completed
Indexes     : idx_<table>_<colonnes>           → idx_tasks_household_created
Triggers    : trg_<table>_<action>             → trg_tasks_updated_at
Fonctions   : verbe_sujet                      → handle_new_user, set_updated_at
Policies    : <table>_<opération>_<acteur>     → tasks_select_member
Contraintes : <table>_<description>            → household_members_unique_member
Types enum  : snake_case                       → household_role
```

---

## 5. Row Level Security

### 5.1 Principe d'activation

```sql
-- RLS activé sur TOUTES les tables — toujours en premier dans la migration
ALTER TABLE public.profiles          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.households        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.household_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shopping_items    ENABLE ROW LEVEL SECURITY;

-- Sans policy définie après activation → deny-by-default
-- RLS bloque tout accès jusqu'à ce qu'une policy l'autorise explicitement
```

### 5.2 Functions helper — réduire la duplication

```sql
-- Écrire ces helpers avant les policies — référencés partout

CREATE OR REPLACE FUNCTION public.is_household_member(p_household_id UUID)
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT EXISTS (
        SELECT 1 FROM household_members
        WHERE household_id = p_household_id AND profile_id = auth.uid()
    );
$$;

CREATE OR REPLACE FUNCTION public.is_household_admin(p_household_id UUID)
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT EXISTS (
        SELECT 1 FROM household_members
        WHERE household_id = p_household_id
        AND   profile_id   = auth.uid()
        AND   role         = 'admin'
    );
$$;
```

### 5.3 Policies — référence complète par table

```sql
-- ════════════════════════════════════════════
-- PROFILES
-- ════════════════════════════════════════════

-- Voir son propre profil
CREATE POLICY "profiles_select_own"
ON profiles FOR SELECT USING (id = auth.uid());

-- Voir les profils des membres de ses foyers
CREATE POLICY "profiles_select_household_members"
ON profiles FOR SELECT
USING (
    id IN (
        SELECT hm2.profile_id FROM household_members hm2
        WHERE hm2.household_id IN (
            SELECT household_id FROM household_members WHERE profile_id = auth.uid()
        )
    )
);

-- Modifier uniquement son propre profil
CREATE POLICY "profiles_update_own"
ON profiles FOR UPDATE
USING (id = auth.uid()) WITH CHECK (id = auth.uid());

-- ════════════════════════════════════════════
-- HOUSEHOLDS
-- ════════════════════════════════════════════

CREATE POLICY "households_select_member"
ON households FOR SELECT
USING (public.is_household_member(id));

CREATE POLICY "households_insert_authenticated"
ON households FOR INSERT
WITH CHECK (auth.uid() IS NOT NULL AND created_by = auth.uid());

CREATE POLICY "households_update_admin"
ON households FOR UPDATE
USING (public.is_household_admin(id))
WITH CHECK (public.is_household_admin(id));

CREATE POLICY "households_delete_admin"
ON households FOR DELETE
USING (public.is_household_admin(id));

-- ════════════════════════════════════════════
-- HOUSEHOLD_MEMBERS
-- ════════════════════════════════════════════

CREATE POLICY "household_members_select_same_household"
ON household_members FOR SELECT
USING (public.is_household_member(household_id));

-- Un utilisateur peut s'ajouter lui-même (rejoindre un foyer)
CREATE POLICY "household_members_insert_self"
ON household_members FOR INSERT
WITH CHECK (profile_id = auth.uid());

CREATE POLICY "household_members_update_admin"
ON household_members FOR UPDATE
USING (public.is_household_admin(household_id))
WITH CHECK (public.is_household_admin(household_id));

-- Quitter soi-même OU admin qui exclut un membre
CREATE POLICY "household_members_delete"
ON household_members FOR DELETE
USING (
    profile_id = auth.uid()
    OR public.is_household_admin(household_id)
);

-- ════════════════════════════════════════════
-- TASKS
-- ════════════════════════════════════════════

CREATE POLICY "tasks_select_member"
ON tasks FOR SELECT USING (public.is_household_member(household_id));

CREATE POLICY "tasks_insert_member"
ON tasks FOR INSERT WITH CHECK (public.is_household_member(household_id));

CREATE POLICY "tasks_update_member"
ON tasks FOR UPDATE
USING (public.is_household_member(household_id))
WITH CHECK (public.is_household_member(household_id));

CREATE POLICY "tasks_delete_member"
ON tasks FOR DELETE USING (public.is_household_member(household_id));

-- ════════════════════════════════════════════
-- SHOPPING_ITEMS
-- ════════════════════════════════════════════

CREATE POLICY "shopping_select_member"
ON shopping_items FOR SELECT USING (public.is_household_member(household_id));

CREATE POLICY "shopping_insert_member"
ON shopping_items FOR INSERT WITH CHECK (public.is_household_member(household_id));

CREATE POLICY "shopping_update_member"
ON shopping_items FOR UPDATE
USING (public.is_household_member(household_id))
WITH CHECK (public.is_household_member(household_id));

CREATE POLICY "shopping_delete_member"
ON shopping_items FOR DELETE USING (public.is_household_member(household_id));
```

### 5.4 Tester les policies RLS

```sql
-- ─── Simuler un utilisateur spécifique ───────────────────────────
SET LOCAL role TO authenticated;
SET LOCAL request.jwt.claims TO '{"sub": "<user-uuid>"}';

-- Test 1 : User A ne voit pas les tâches du foyer de User B
SELECT COUNT(*) FROM tasks WHERE household_id = '<foyer-b-uuid>';
-- Résultat attendu : 0

-- Test 2 : User A ne peut pas modifier une tâche d'un autre foyer
UPDATE tasks SET title = 'Hack' WHERE household_id = '<foyer-b-uuid>';
-- Résultat attendu : 0 rows affected

-- Test 3 : INSERT direct avec household_id étranger bloqué
INSERT INTO household_members (household_id, profile_id, role)
VALUES ('<foyer-b-uuid>', '<user-c-uuid>', 'member');
-- Résultat attendu : ERROR (profile_id ≠ auth.uid())

RESET role;
RESET request.jwt.claims;

-- ─── Vérifier que RLS est actif sur toutes les tables ────────────
SELECT tablename, rowsecurity
FROM   pg_tables
WHERE  schemaname = 'public'
ORDER  BY tablename;
-- rowsecurity = true sur toutes les tables métier

-- ─── Lister toutes les policies actives ──────────────────────────
SELECT tablename, policyname, cmd
FROM   pg_policies
WHERE  schemaname = 'public'
ORDER  BY tablename, policyname;
```

### 5.5 Erreurs RLS fréquentes à éviter

```
❌ Policy INSERT sans WITH CHECK
   → USING s'applique aux lignes existantes, pas aux nouvelles
   → Sans WITH CHECK : n'importe qui peut insérer dans n'importe quel foyer

❌ Oublier d'activer RLS sur une nouvelle table
   → Sans ALTER TABLE ... ENABLE ROW LEVEL SECURITY
   → Toutes les données sont accessibles en lecture sans restriction

❌ Policy sur SELECT seulement
   → Un utilisateur sans policy INSERT peut toujours créer des lignes
   → Policies nécessaires pour les 4 opérations

❌ Tester uniquement avec le rôle service_role
   → service_role bypass RLS — les tests doivent utiliser le rôle `authenticated`
```

---

## 6. Bonnes pratiques

### 6.1 Migrations — format et structure

```sql
-- Nom de fichier : YYYYMMDDHHMMSS_description.sql
-- Exemple : 20260304100000_create_tasks_table.sql

-- Structure obligatoire d'une migration :

-- ── En-tête (contexte pour le futur lecteur) ──────────────────────
-- Migration : Création de la table tasks
-- Story     : TASK-01
-- Date      : 2026-03-04
-- Auteur    : DB Agent

-- ── Corps ─────────────────────────────────────────────────────────

-- Toujours idempotent
CREATE TABLE IF NOT EXISTS public.tasks ( ... );
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;

-- Policies avec DROP IF EXISTS + CREATE pour l'idempotence
DROP POLICY IF EXISTS "tasks_select_member" ON public.tasks;
CREATE POLICY "tasks_select_member" ...;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tasks_household_created ...;

-- Triggers
CREATE OR REPLACE FUNCTION public.trg_tasks_updated_at() ...;

-- ── Rollback documenté en commentaire ─────────────────────────────
-- ROLLBACK :
-- DROP TABLE IF EXISTS public.tasks CASCADE;
-- DROP FUNCTION IF EXISTS public.trg_tasks_updated_at();
```

### 6.2 Checklist par migration

```
SCHÉMA
  ☐ household_id NOT NULL avec FK ON DELETE CASCADE sur toute table métier
  ☐ Contraintes CHECK sur toutes les colonnes à longueur bornée
  ☐ SET NULL (pas CASCADE) sur les références à des profils (created_by, assigned_to)
  ☐ Commentaires SQL (COMMENT ON TABLE/COLUMN) sur les colonnes non évidentes

SÉCURITÉ
  ☐ ALTER TABLE ... ENABLE ROW LEVEL SECURITY — dès la création
  ☐ Policies pour les 4 opérations : SELECT, INSERT (WITH CHECK), UPDATE, DELETE
  ☐ Fonctions SECURITY DEFINER avec SET search_path = public
  ☐ Aucune donnée sensible en clair (mots de passe, tokens)

PERFORMANCE
  ☐ Index sur household_id + colonnes de tri pour les listes principales
  ☐ Index partiel si un filtre stable est connu (WHERE is_completed = false)
  ☐ Pas d'index sur toutes les colonnes par défaut

MIGRATION
  ☐ Fichier nommé YYYYMMDDHHMMSS_description.sql
  ☐ Instructions idempotentes (IF NOT EXISTS, OR REPLACE, DROP IF EXISTS)
  ☐ Testée localement avec supabase db push avant push sur feature branch
  ☐ Types TypeScript régénérés et committé dans la même PR

COMMUNICATION
  ☐ Backend Developer notifié : "Migration prête — types régénérés"
  ☐ Infra Developer notifié : "Migration à appliquer sur preview avant les tests"
  ☐ Breaking change ? → préavis d'un cycle, migration backward-compatible si possible
```

### 6.3 Sécurité des données

```
Ce qui ne se stocke jamais en base :
  ❌ Mots de passe → gérés par Supabase Auth (bcrypt)
  ❌ Tokens de session → gérés par Supabase Auth (cookies HTTP-only)
  ❌ Clés API tierces → variables d'environnement serveur uniquement
  ❌ Numéros de carte, données bancaires → hors scope FoyerApp

Ce qui se stocke avec précaution :
  ⚠️ Emails → uniquement dans auth.users (géré par Supabase) — pas dupliqués dans profiles
  ⚠️ Avatars → URL Supabase Storage, pas les fichiers en base

Modèle de confiance (trois niveaux) :
  CLIENT browser  → anon key + RLS → accès limité aux données de l'utilisateur
  API ROUTES      → service_role key → accès complet, logique de sécurité dans le code
  DB ADMIN        → service_role key → migrations, diagnostics
```

### 6.4 Antipatterns à éviter

| Antipattern | Risque | Correction |
|---|---|---|
| Table métier sans `household_id` | Fuite de données inter-foyers | Règle absolue — jamais d'exception |
| Policy INSERT sans `WITH CHECK` | INSERT vers un foyer étranger possible | Toujours `USING` + `WITH CHECK` sur INSERT/UPDATE |
| Migration non idempotente | Échec si rejouée (re-déploiement) | `IF NOT EXISTS`, `OR REPLACE`, `DROP IF EXISTS` |
| `ON DELETE CASCADE` sur `created_by` | Suppression d'un utilisateur = perte de données du foyer | `ON DELETE SET NULL` sur les refs profil |
| `SECURITY DEFINER` sans `SET search_path` | Injection via search_path malveillant | Toujours `SET search_path = public` |
| Modification directe via le dashboard | Schéma non versionné, non reproductible | Toujours via fichier de migration |
| Index sur chaque colonne | Ralentit les écritures, coûte de l'espace | Index uniquement sur les patterns de requête connus |
| RLS testé uniquement en service_role | Service_role bypass RLS — tests invalides | Toujours tester avec rôle `authenticated` |
| Types TypeScript non régénérés | Désynchronisation schéma / code | Régénérer + commiter après chaque migration |
| Breaking change sans préavis | Frontend/Backend en erreur | Préavis 1 cycle, migration backward-compatible |

### 6.5 Diagnostics fréquents

```sql
-- Vérifier qu'une table a bien RLS actif
SELECT relname, relrowsecurity
FROM   pg_class
WHERE  relname = 'tasks' AND relnamespace = 'public'::regnamespace;

-- Lister les policies d'une table
SELECT policyname, cmd, qual, with_check
FROM   pg_policies
WHERE  schemaname = 'public' AND tablename = 'tasks';

-- Taille des tables (surveiller les limites Supabase Free)
SELECT relname AS table_name,
       pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
       n_live_tup AS row_count
FROM   pg_stat_user_tables
WHERE  schemaname = 'public'
ORDER  BY pg_total_relation_size(relid) DESC;

-- Index inutilisés (candidats à la suppression)
SELECT indexrelname, idx_scan
FROM   pg_stat_user_indexes
WHERE  schemaname = 'public' AND idx_scan = 0
ORDER  BY indexrelname;

-- Orphelins potentiels (sanity check post-migration)
SELECT COUNT(*) FROM tasks
WHERE  household_id NOT IN (SELECT id FROM households);
-- Résultat attendu : 0
```

### 6.6 Limites Supabase Free — seuils d'alerte

| Ressource | Limite | Alerte à |
|---|---|---|
| Base de données | 500 MB | 400 MB |
| Bandwidth | 2 GB/mois | 1.5 GB |
| Realtime connections | 200 simultanées | 150 |
| Storage | 1 GB | 800 MB |

Realtime à activer uniquement sur les tables nécessaires :
```sql
ALTER PUBLICATION supabase_realtime ADD TABLE public.tasks;
ALTER PUBLICATION supabase_realtime ADD TABLE public.shopping_items;
-- Ne PAS activer sur : profiles, households, household_members
```

---

## Annexe — Références rapides

### A. Commandes CLI essentielles

```bash
# Démarrer Supabase en local
supabase start

# Créer une nouvelle migration
supabase migration new <nom_descriptif>

# Appliquer les migrations en local
supabase db push

# Générer les types TypeScript depuis le schéma local
supabase gen types typescript --local > src/types/database.ts

# Générer depuis Supabase Cloud
supabase gen types typescript --project-id <ref> > src/types/database.ts

# Réinitialiser la DB locale (attention : détruit les données locales)
supabase db reset
```

### B. Skill de référence

| Situation | Section du skill `supabase_database.md` |
|---|---|
| DDL complet par table | §2.2 |
| Patterns de requêtes d'appartenance | §3.2 |
| Fonctions SQL (join, regenerate) | §3.3–§3.4 |
| Policies complètes par table | §4.2–§4.6 |
| Migrations versionnées | §5.1 |
| Conventions de nommage | §5.2 |
| Génération des types TypeScript | §5.3 |
| Mapping erreurs Postgres | §5.4 |
| Checklist sécurité déploiement | §6.6 |

### C. Références techniques

| Ressource | URL |
|---|---|
| Supabase RLS Guide | https://supabase.com/docs/guides/auth/row-level-security |
| Supabase CLI | https://supabase.com/docs/reference/cli |
| PostgreSQL RLS | https://www.postgresql.org/docs/current/ddl-rowsecurity.html |
| Supabase Realtime | https://supabase.com/docs/guides/realtime |

---

*Ce document est la référence pour l'agent IA Database Developer de FoyerApp. Il est mis à jour à chaque évolution du schéma, des conventions de migration ou des règles de sécurité de l'équipe.*
