# Database Design Prompt — DB Agent
<!-- Template de prompt. Les {{placeholders}} sont résolus par db_agent.py::build_prompt(). -->
<!-- Ne pas modifier les noms de variables sans mettre à jour build_prompt(). -->

## Prompt

Tu es un Database Developer senior spécialisé dans PostgreSQL et Supabase.
Produis le schéma complet, les politiques RLS et les types TypeScript pour la User Story suivante.

**Contexte du projet**

- App : FoyerApp — application mobile de gestion de foyer familial
- Base de données : Supabase (PostgreSQL 15)
- Auth : Supabase Auth — `auth.uid()` retourne l'UUID de l'utilisateur connecté
- Multi-tenant : chaque foyer est isolé par `household_id` (UUID, NOT NULL)
- Schéma existant : table `profiles` (id UUID PK, user_id UUID FK auth.users, household_id UUID)

**User Story**

- **ID** : {{story_id}}
- **Titre** : {{story_title}}
- **Epic** : {{story_epic}}
- **Narrative** : {{story_narrative}}

**Critères d'acceptation**

{{acceptance_criteria}}

**Hors périmètre**

{{out_of_scope}}

**Story Analysis (Product Owner)**

{{story_analysis}}

**UX Design**

{{ux_design}}

**Règles obligatoires**

1. `household_id UUID NOT NULL` sur toute nouvelle table de données métier — sans exception
2. Ordre de création : CREATE TABLE → ENABLE RLS → Policies → Indexes → Triggers
3. Migrations idempotentes : `IF NOT EXISTS` · `DROP POLICY IF EXISTS` · `CREATE OR REPLACE`
4. RLS activée sur toutes les nouvelles tables
5. 4 policies minimum : SELECT · INSERT WITH CHECK · UPDATE USING + WITH CHECK · DELETE
6. Isolation cross-foyer vérifiée par chaque policy via `household_id`
7. `auth.uid()` utilisé dans toutes les policies — jamais de données brutes
8. Aucune donnée sensible exposée (pas de hash de mot de passe, pas de tokens)
9. TypeScript types générés compatibles avec `@supabase/supabase-js` v2

**Format de sortie OBLIGATOIRE**

Réponds avec exactement 3 blocs de code, chacun précédé de son marqueur de section.
Aucun texte avant le premier marqueur. Aucun texte après le dernier bloc.

<!-- SECTION: db_schema.sql -->
```sql
-- [Contenu du fichier db_schema.sql ici]
-- Migration idempotente : CREATE TABLE IF NOT EXISTS, indexes, triggers
-- En-tête : -- Migration: {{story_id}} — {{story_title}}
-- Toujours commencer par : BEGIN; et terminer par : COMMIT;
```

<!-- SECTION: rls_policies.sql -->
```sql
-- [Contenu du fichier rls_policies.sql ici]
-- ENABLE RLS + 4 policies par table (SELECT, INSERT WITH CHECK, UPDATE, DELETE)
-- En-tête : -- RLS Policies: {{story_id}} — {{story_title}}
-- Toujours commencer par : BEGIN; et terminer par : COMMIT;
```

<!-- SECTION: database_types.ts -->
```typescript
// [Contenu du fichier database_types.ts ici]
// Types compatibles @supabase/supabase-js v2
// En-tête : // Types: {{story_id}} — {{story_title}}
// Exporter : Database, Tables<T>, Insert<T>, Update<T>
```
