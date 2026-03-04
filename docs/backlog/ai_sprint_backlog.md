# FoyerApp — Backlog AI Scrum Team

> **Projet** : FoyerApp  
> **Version** : 1.1 — MVP POC (stack corrigée)  
> **Date** : 2026-03-04  
> **Stories** : 11 | **Total points** : 32

---

## Stack technique officielle

| Couche | Technologie |
|---|---|
| **Frontend** | Next.js 14+ (App Router) — mobile-first PWA |
| **UI** | TailwindCSS |
| **Backend** | API Routes Next.js (`/api/v1/*`) |
| **Database** | Supabase Postgres |
| **Auth** | Supabase Auth |
| **Hosting** | Vercel |

> **Note de migration** : Ce document remplace la version précédente référençant Flutter / Riverpod / GoRouter / Material Design 3. Toutes les descriptions techniques sont désormais alignées sur la stack Next.js + Supabase.

---

## Conventions

| Champ | Description |
|---|---|
| **Story Points** | Fibonacci (1–2–3–5–8). Référence : AUTH-01 = 5 pts |
| **Dependencies** | IDs des stories qui doivent être *Done* avant de démarrer |
| **Definition of Done** | Checklist commune à toutes les stories + critères spécifiques |
| **Technical Tasks** | Tâches atomiques à assigner à un Developer ou QA |

### DoD globale (s'applique à toutes les stories)
- [ ] Code revu et approuvé via Pull Request (merge sur `main` bloqué sans approbation)
- [ ] Aucune erreur ESLint ni TypeScript (`next build` passe sans erreur)
- [ ] Tests unitaires écrits et passants (Jest / Testing Library) pour la logique métier
- [ ] Tests de composants écrits pour les formulaires et interactions UI clés
- [ ] Comportement vérifié sur mobile (375px) **et** desktop (1280px) via DevTools
- [ ] Aucune régression sur les stories précédentes (test suite complète verte)
- [ ] Story démontrée et acceptée par le Product Owner en Sprint Review

---

## SPRINT 1 — Fondations (11 pts)

> **Objectif** : Un utilisateur peut s'inscrire, se connecter et voir le squelette de navigation.  
> **Livrable** : App déployée sur Vercel, auth fonctionnelle, 3 onglets de navigation accessibles.

---

### AUTH-01 — Inscription email + mot de passe

> **En tant que** nouvel utilisateur, **je veux** m'inscrire avec mon email et un mot de passe, **afin d'** accéder à l'application.

| Champ | Valeur |
|---|---|
| **EPIC** | E1 — Authentification |
| **Sprint** | Sprint 1 |
| **Story Points** | 5 |
| **Priorité** | Must Have |
| **Dependencies** | Aucune — première story du projet |

#### Critères d'acceptation
- [ ] La page `/register` affiche 3 champs : email, mot de passe, confirmation du mot de passe
- [ ] Validation en temps réel (React Hook Form + Zod) : format email invalide → erreur inline
- [ ] Validation en temps réel : mot de passe < 8 caractères → erreur inline
- [ ] Validation en temps réel : mots de passe non concordants → erreur inline
- [ ] Bouton "S'inscrire" désactivé tant que le formulaire est invalide
- [ ] Email déjà utilisé → message : "Un compte existe déjà avec cet email"
- [ ] Indicateur de chargement (`disabled` + spinner) pendant l'appel réseau
- [ ] Erreur réseau → message : "Une erreur est survenue, veuillez réessayer"
- [ ] Succès → profil créé dans la table `profiles` avec l'`id` Supabase Auth
- [ ] Succès → session Supabase active (cookie HTTP-only posé par le middleware)
- [ ] Succès → redirection Next.js vers `/household-setup`

#### Definition of Done
- [ ] *DoD globale respectée*
- [ ] Intégration Supabase Auth testée avec un compte réel (pas de mock)
- [ ] INSERT dans `profiles` vérifié dans le dashboard Supabase
- [ ] Les 3 cas d'erreur de validation couverts par des tests React Testing Library
- [ ] Aucun mot de passe visible en clair dans les logs serveur ou client
- [ ] Variables d'environnement Supabase configurées sur Vercel (preview + production)

#### Technical Tasks

| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T1.1 | Configurer `@supabase/ssr` + client browser et server, variables d'environnement `.env.local` | Dev | 2h |
| T1.2 | Créer la table `profiles` dans Supabase (migration SQL) + RLS policy | Dev | 1h |
| T1.3 | Créer le Server Action ou API Route `POST /api/v1/auth/register` avec validation Zod | Dev | 2h |
| T1.4 | Créer le hook `useAuth` (React state : idle / loading / success / error) | Dev | 1h |
| T1.5 | Implémenter la page `app/(auth)/register/page.tsx` avec React Hook Form + Zod | Dev | 3h |
| T1.6 | Implémenter le trigger Supabase `on_auth_user_created` → INSERT dans `profiles` | Dev | 1h |
| T1.7 | Configurer la redirection Next.js post-inscription : `/household-setup` | Dev | 30min |
| T1.8 | Écrire les tests RTL : validation formulaire (3 cas) + état loading + redirection | QA | 2h |
| T1.9 | Test d'intégration manuel : parcours complet inscription → profil en base | QA | 1h |

---

### AUTH-02 — Connexion email + mot de passe

> **En tant qu'** utilisateur, **je veux** me connecter avec mon email et mon mot de passe, **afin d'** accéder à mon foyer.

| Champ | Valeur |
|---|---|
| **EPIC** | E1 — Authentification |
| **Sprint** | Sprint 1 |
| **Story Points** | 2 |
| **Priorité** | Must Have |
| **Dependencies** | AUTH-01 (API auth et routing initialisés) |

#### Critères d'acceptation
- [ ] La page `/login` affiche 2 champs : email et mot de passe
- [ ] Lien "Pas encore de compte ?" → redirection vers `/register`
- [ ] Identifiants incorrects → message : "Email ou mot de passe incorrect"
- [ ] Indicateur de chargement pendant l'appel réseau
- [ ] Succès → redirection vers `/dashboard` (foyer actif) ou `/household-setup` (aucun foyer)

#### Definition of Done
- [ ] *DoD globale respectée*
- [ ] Cas d'erreur "mauvais identifiants" couvert par test RTL
- [ ] Redirection conditionnelle testée : avec foyer → `/dashboard` / sans foyer → `/household-setup`
- [ ] Cookie de session HTTP-only posé et non accessible via `document.cookie`

#### Technical Tasks

| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T2.1 | Ajouter `POST /api/v1/auth/login` avec `supabase.auth.signInWithPassword` | Dev | 1h |
| T2.2 | Implémenter la page `app/(auth)/login/page.tsx` avec gestion d'erreurs | Dev | 2h |
| T2.3 | Implémenter la logique de redirection post-login (foyer existant ou non) | Dev | 1h |
| T2.4 | Configurer le lien `/register` depuis la page `/login` | Dev | 15min |
| T2.5 | Écrire tests RTL : mauvais identifiants + redirection succès | QA | 1h |

---

### AUTH-03 — Session persistante

> **En tant qu'** utilisateur, **je veux** rester connecté automatiquement, **afin de** ne pas ressaisir mes identifiants à chaque ouverture.

| Champ | Valeur |
|---|---|
| **EPIC** | E1 — Authentification |
| **Sprint** | Sprint 1 |
| **Story Points** | 2 |
| **Priorité** | Must Have |
| **Dependencies** | AUTH-01, AUTH-02 |

#### Critères d'acceptation
- [ ] À la réouverture de l'app, session valide → redirection directe vers `/dashboard` sans repasser par `/login`
- [ ] Session persistante après fermeture de l'onglet et réouverture
- [ ] Session persistante après redémarrage du navigateur
- [ ] Pas de session valide → affichage de `/login`

#### Definition of Done
- [ ] *DoD globale respectée*
- [ ] Middleware Next.js (`middleware.ts`) intercepte les routes protégées et redirige si non authentifié
- [ ] Refresh automatique du token géré par `@supabase/ssr` (cookie rotation)
- [ ] Testé sur Chrome desktop et Safari mobile (mode privé exclu)
- [ ] Testé après fermeture complète du navigateur et réouverture

#### Technical Tasks

| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T3.1 | Implémenter `middleware.ts` Next.js avec vérification de session Supabase sur routes protégées | Dev | 1h |
| T3.2 | Configurer `updateSession` Supabase dans le middleware pour le refresh automatique des tokens | Dev | 1h |
| T3.3 | Définir les matchers de routes : `/(app)/*` protégé, `/(auth)/*` public | Dev | 30min |
| T3.4 | Test manuel : fermer onglet → rouvrir URL protégée → vérifier redirection sans login | QA | 30min |
| T3.5 | Test manuel : fermer navigateur → rouvrir → vérifier persistance de session | QA | 30min |

---

### HOME-02 — Navigation par onglets

> **En tant que** membre, **je veux** naviguer entre les onglets, **afin d'** accéder rapidement aux features.

| Champ | Valeur |
|---|---|
| **EPIC** | E5 — Accueil & Navigation |
| **Sprint** | Sprint 1 |
| **Story Points** | 2 |
| **Priorité** | Must Have |
| **Dependencies** | AUTH-03 (routes protégées par le middleware) |

#### Critères d'acceptation
- [ ] Une barre de navigation bottom (mobile) ou latérale (desktop) affiche 3 destinations : **Accueil**, **Tâches**, **Courses**
- [ ] L'onglet actif est mis en évidence (TailwindCSS — classe active différenciée)
- [ ] Navigation entre onglets via liens Next.js (`<Link>`) — instantanée, sans rechargement de page
- [ ] L'état de chaque page est conservé lors des allers-retours (Next.js App Router layout persistant)
- [ ] Les pages Tâches et Courses affichent un placeholder "À venir" pour ce sprint

#### Definition of Done
- [ ] *DoD globale respectée*
- [ ] Layout `app/(app)/layout.tsx` partagé par les 3 routes, rendu une seule fois
- [ ] Navigation testée sur mobile 375px (bottom nav) et desktop 1280px (sidebar ou top nav)
- [ ] Liens actifs détectés via `usePathname()` Next.js
- [ ] Test RTL : rendu du layout + présence des 3 liens de navigation

#### Technical Tasks

| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T4.1 | Créer le layout `app/(app)/layout.tsx` avec `BottomNav` (mobile) responsive | Dev | 1h |
| T4.2 | Implémenter le composant `NavBar` avec `usePathname()` pour la détection de l'onglet actif | Dev | 1h |
| T4.3 | Créer les 3 routes et pages placeholder : `app/(app)/dashboard/`, `app/(app)/tasks/`, `app/(app)/shopping/` | Dev | 30min |
| T4.4 | Styler la `NavBar` en TailwindCSS : bottom bar sur mobile (`fixed bottom-0`), sidebar sur `md:` | Dev | 1h |
| T4.5 | Test RTL : rendu du layout + 3 liens présents + lien actif mis en évidence | QA | 1h |

---

## SPRINT 2 — Foyer & Tâches (14 pts)

> **Objectif** : Deux utilisateurs peuvent former un foyer et collaborer sur des tâches.  
> **Livrable** : Foyer créé, membre invité via code, tâches créées et complétées.

---

### FOYER-01 — Créer un foyer

> **En tant que** membre, **je veux** créer un foyer, **afin d'** inviter ma famille.

| Champ | Valeur |
|---|---|
| **EPIC** | E2 — Gestion du foyer |
| **Sprint** | Sprint 2 |
| **Story Points** | 5 |
| **Priorité** | Must Have |
| **Dependencies** | AUTH-01, AUTH-02, AUTH-03 |

#### Critères d'acceptation
- [ ] La page `/household-setup` propose un formulaire avec champ "Nom du foyer" (obligatoire, min 2 chars, max 50)
- [ ] Bouton "Créer" désactivé si le champ est vide
- [ ] À la création → code d'invitation à 6 caractères alphanumériques généré (uppercase) et stocké en base
- [ ] L'utilisateur est inscrit dans `household_members` avec le rôle `admin`
- [ ] Le foyer apparaît immédiatement dans les données de l'utilisateur
- [ ] Redirection automatique vers `/dashboard` après création

#### Definition of Done
- [ ] *DoD globale respectée*
- [ ] `POST /api/v1/households` validé avec Zod côté API Route
- [ ] INSERT dans `households` et `household_members` vérifiés dans Supabase dashboard
- [ ] Unicité du `invite_code` assurée par contrainte UNIQUE en base
- [ ] RLS policy : un utilisateur ne voit que les foyers dont il est membre
- [ ] Test RTL : formulaire vide → bouton désactivé / soumission valide → redirection

#### Technical Tasks

| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T5.1 | Créer les tables `households` et `household_members` (migration SQL + RLS) | Dev | 2h |
| T5.2 | Implémenter `POST /api/v1/households` avec validation Zod + génération du code invitation | Dev | 2h |
| T5.3 | Créer le hook `useHousehold` (React state : idle / loading / success / error) | Dev | 1h |
| T5.4 | Implémenter la fonction utilitaire de génération du code (6 chars, uppercase, unique) | Dev | 1h |
| T5.5 | Implémenter la page `app/(app)/household-setup/page.tsx` avec formulaire validé | Dev | 2h |
| T5.6 | Configurer la redirection Next.js post-création : `/dashboard` | Dev | 30min |
| T5.7 | Test RTL : formulaire vide désactivé + soumission valide + redirection | QA | 1h |
| T5.8 | Test d'intégration manuel : création foyer → vérification Supabase + code généré | QA | 1h |

---

### FOYER-02 — Rejoindre un foyer via code

> **En tant que** membre, **je veux** rejoindre un foyer via un code à 6 caractères, **afin d'** intégrer le foyer de quelqu'un.

| Champ | Valeur |
|---|---|
| **EPIC** | E2 — Gestion du foyer |
| **Sprint** | Sprint 2 |
| **Story Points** | 3 |
| **Priorité** | Must Have |
| **Dependencies** | FOYER-01 (table `households` avec `invite_code` existante) |

#### Critères d'acceptation
- [ ] La page `/household-setup` propose également un champ "Rejoindre avec un code" (insensible à la casse)
- [ ] Code invalide ou inexistant → message : "Code invalide ou introuvable"
- [ ] Utilisateur déjà membre → message : "Vous êtes déjà membre de ce foyer"
- [ ] Succès → INSERT dans `household_members` avec rôle `member`
- [ ] Succès → redirection vers `/dashboard` du foyer rejoint

#### Definition of Done
- [ ] *DoD globale respectée*
- [ ] `POST /api/v1/households/join` validé avec Zod
- [ ] Contrainte UNIQUE sur `(household_id, profile_id)` vérifiée en base
- [ ] Les 2 cas d'erreur couverts par tests RTL
- [ ] Test multi-utilisateurs : utilisateur A crée un foyer, utilisateur B rejoint avec le code → les deux voient le même foyer

#### Technical Tasks

| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T6.1 | Implémenter `POST /api/v1/households/join` avec lookup `invite_code` case-insensitive | Dev | 1h |
| T6.2 | Ajouter la section "Rejoindre" dans la page `household-setup` avec champ code | Dev | 1h |
| T6.3 | Gérer les 2 cas d'erreur : code introuvable + déjà membre | Dev | 1h |
| T6.4 | Tests RTL : code invalide + déjà membre + succès | QA | 1h |
| T6.5 | Test d'intégration multi-utilisateurs : A crée, B rejoint, les deux accèdent au foyer | QA | 1h |

---

### FOYER-03 — Partager le code d'invitation

> **En tant que** membre, **je veux** copier ou partager le code d'invitation, **afin d'** inviter facilement les autres.

| Champ | Valeur |
|---|---|
| **EPIC** | E2 — Gestion du foyer |
| **Sprint** | Sprint 2 |
| **Story Points** | 2 |
| **Priorité** | Must Have |
| **Dependencies** | FOYER-01 (code généré et stocké) |

#### Critères d'acceptation
- [ ] Le code d'invitation est visible dans les paramètres ou la page du foyer
- [ ] Bouton "Copier" → code copié via `navigator.clipboard.writeText()` + toast de confirmation "Code copié !"
- [ ] Bouton "Partager" → Web Share API (`navigator.share`) avec message : "Rejoins mon foyer sur FoyerApp avec le code : XXXXXX"
- [ ] Si Web Share API non supportée (desktop) → fallback vers copie dans le presse-papier

#### Definition of Done
- [ ] *DoD globale respectée*
- [ ] Testé sur navigateur mobile Chrome et Safari (Web Share API)
- [ ] Testé sur navigateur desktop (fallback copie)
- [ ] Test RTL : affichage du code + clic "Copier" → toast visible

#### Technical Tasks

| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T7.1 | Créer le composant `InviteCodeCard` (affichage code + boutons Copier/Partager) | Dev | 1h |
| T7.2 | Implémenter `navigator.share` avec fallback `navigator.clipboard.writeText` | Dev | 1h |
| T7.3 | Implémenter le toast de confirmation avec `useState` + `useEffect` (auto-dismiss 2s) | Dev | 30min |
| T7.4 | Intégrer `InviteCodeCard` dans la page dashboard ou foyer | Dev | 30min |
| T7.5 | Test RTL : affichage du code + toast après "Copier" | QA | 1h |
| T7.6 | Test manuel sur mobile Chrome et Safari : Web Share API fonctionnelle | QA | 30min |

---

### TASK-01 — Créer une tâche

> **En tant que** parent, **je veux** créer une tâche avec titre et description, **afin d'** organiser le foyer.

| Champ | Valeur |
|---|---|
| **EPIC** | E3 — Tâches |
| **Sprint** | Sprint 2 |
| **Story Points** | 2 |
| **Priorité** | Must Have |
| **Dependencies** | FOYER-01 (`household_id` disponible en session) |

#### Critères d'acceptation
- [ ] Un bouton "+" flottant (`fixed bottom-6 right-6` Tailwind) ouvre un formulaire de création (modale ou drawer)
- [ ] Champ titre : obligatoire, max 100 caractères
- [ ] Champ description : optionnel, texte libre
- [ ] Soumission impossible si le titre est vide → message d'erreur inline
- [ ] Tâche créée liée au `household_id` actif
- [ ] La tâche apparaît immédiatement dans la liste (revalidation via `router.refresh()` ou optimistic update)

#### Definition of Done
- [ ] *DoD globale respectée*
- [ ] `POST /api/v1/tasks` validé avec Zod côté API Route
- [ ] INSERT dans `tasks` vérifié avec `household_id` correct dans Supabase
- [ ] RLS policy : un membre ne voit que les tâches de son foyer
- [ ] Test RTL : titre vide → erreur / titre valide → tâche dans la liste
- [ ] Revalidation Next.js (`revalidatePath`) ou optimistic update React fonctionnel

#### Technical Tasks

| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T8.1 | Créer la table `tasks` (migration SQL + RLS policy) | Dev | 1h |
| T8.2 | Implémenter `POST /api/v1/tasks` avec validation Zod | Dev | 1h |
| T8.3 | Implémenter `GET /api/v1/tasks?householdId=` pour la liste du foyer | Dev | 1h |
| T8.4 | Créer le hook `useTasks` avec `useState` + `useEffect` pour le fetching | Dev | 1h |
| T8.5 | Implémenter la modale/drawer de création avec React Hook Form + Zod | Dev | 2h |
| T8.6 | Implémenter le composant `TaskList` avec rendu des tâches du foyer | Dev | 1h |
| T8.7 | Tests RTL : formulaire vide → erreur + création valide → liste mise à jour | QA | 1h |

---

### TASK-04 — Compléter une tâche

> **En tant que** membre, **je veux** marquer une tâche comme complétée, **afin de** signaler mon avancement.

| Champ | Valeur |
|---|---|
| **EPIC** | E3 — Tâches |
| **Sprint** | Sprint 2 |
| **Story Points** | 2 |
| **Priorité** | Must Have |
| **Dependencies** | TASK-01 (tâches existantes en base et affichées) |

#### Critères d'acceptation
- [ ] Une case à cocher (`<input type="checkbox">` stylée Tailwind) sur chaque carte de tâche → `is_completed = true`
- [ ] Tâche complétée : titre barré (`line-through`) + opacité réduite (`opacity-50`) — feedback visuel immédiat
- [ ] Action réversible : décocher remet `is_completed = false`
- [ ] Le statut est visible par tous les membres du foyer (rechargement ou Supabase Realtime)

#### Definition of Done
- [ ] *DoD globale respectée*
- [ ] `PATCH /api/v1/tasks/:id` vérifié en base (UPDATE `is_completed`)
- [ ] Feedback visuel `line-through` + `opacity-50` testé sur mobile et desktop
- [ ] Action réversible couverte par test RTL
- [ ] Aucune tâche d'un autre foyer n'est modifiable (RLS vérifié)

#### Technical Tasks

| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T9.1 | Implémenter `PATCH /api/v1/tasks/:id` avec validation du `household_id` de l'appelant | Dev | 1h |
| T9.2 | Ajouter la checkbox stylée TailwindCSS sur `TaskCard` avec feedback visuel (line-through + opacity) | Dev | 1h |
| T9.3 | Connecter le toggle au hook `useTasks` → appel API + mise à jour optimiste du state React | Dev | 1h |
| T9.4 | (Optionnel) Activer Supabase Realtime sur `tasks` pour sync multi-membres sans polling | Dev | 1h |
| T9.5 | Tests RTL : cocher → style `line-through` / décocher → style restauré | QA | 1h |
| T9.6 | Test multi-membres : utilisateur A coche une tâche → utilisateur B voit le changement | QA | 30min |

---

## SPRINT 3 — Courses & Accueil (7 pts)

> **Objectif** : Liste de courses collaborative et dashboard d'accueil synthèse.  
> **Livrable** : POC complet — parcours bout-en-bout démontrable en 5 minutes.

---

### SHOP-01 — Ajouter un article

> **En tant que** membre, **je veux** ajouter un article avec nom et quantité, **afin de** préparer mes courses.

| Champ | Valeur |
|---|---|
| **EPIC** | E4 — Liste de courses |
| **Sprint** | Sprint 3 |
| **Story Points** | 2 |
| **Priorité** | Must Have |
| **Dependencies** | FOYER-01, HOME-02 (page Courses accessible via la navigation) |

#### Critères d'acceptation
- [ ] Un bouton "+" ouvre un formulaire rapide (modale ou drawer en bas sur mobile)
- [ ] Champ nom : obligatoire
- [ ] Champ quantité : optionnel, texte libre ("1 kg", "une bouteille", "3")
- [ ] Article lié au `household_id` actif
- [ ] Article visible immédiatement dans la liste après ajout

#### Definition of Done
- [ ] *DoD globale respectée*
- [ ] `POST /api/v1/shopping` validé avec Zod
- [ ] INSERT dans `shopping_items` avec `household_id` correct
- [ ] RLS policy : membres ne voient que les articles de leur foyer
- [ ] Test RTL : ajout valide → article dans liste / nom vide → soumission bloquée

#### Technical Tasks

| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T10.1 | Créer la table `shopping_items` (migration SQL + RLS policy) | Dev | 1h |
| T10.2 | Implémenter `POST /api/v1/shopping` et `GET /api/v1/shopping?householdId=` | Dev | 1h |
| T10.3 | Créer le hook `useShopping` avec `useState` + `useEffect` | Dev | 1h |
| T10.4 | Implémenter la modale/drawer d'ajout rapide (nom + quantité, React Hook Form) | Dev | 1h |
| T10.5 | Implémenter le composant `ShoppingList` avec rendu des articles | Dev | 1h |
| T10.6 | Tests RTL : champ vide → bloqué + ajout valide → liste mise à jour | QA | 1h |

---

### SHOP-02 — Marquer un article comme acheté

> **En tant que** membre, **je veux** marquer un article comme acheté, **afin de** suivre ma progression en magasin.

| Champ | Valeur |
|---|---|
| **EPIC** | E4 — Liste de courses |
| **Sprint** | Sprint 3 |
| **Story Points** | 2 |
| **Priorité** | Must Have |
| **Dependencies** | SHOP-01 (articles existants en base et affichés) |

#### Critères d'acceptation
- [ ] Tap sur un article (ou checkbox) → `is_purchased = true`
- [ ] Article acheté : texte barré (`line-through`) + déplacé en bas de liste dans une section "Déjà acheté"
- [ ] Section visuelle distincte : "À acheter" / "Déjà acheté" (séparateur Tailwind)
- [ ] Action réversible : re-tap remet `is_purchased = false`
- [ ] Statut visible en temps réel par tous les membres du foyer

#### Definition of Done
- [ ] *DoD globale respectée*
- [ ] `PATCH /api/v1/shopping/:id` vérifié en base
- [ ] Séparation visuelle "À acheter" / "Acheté" testée sur mobile 375px et desktop
- [ ] Tests RTL : cocher → déplacement section "Acheté" + décocher → retour section "À acheter"
- [ ] Test multi-membres : synchronisation entre 2 sessions navigateur

#### Technical Tasks

| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T11.1 | Implémenter `PATCH /api/v1/shopping/:id` avec validation du `household_id` | Dev | 1h |
| T11.2 | Ajouter la checkbox stylée TailwindCSS sur `ShoppingItemCard` + style `line-through` | Dev | 1h |
| T11.3 | Implémenter le tri réactif dans `useShopping` : non-achetés en haut, achetés en bas | Dev | 1h |
| T11.4 | (Optionnel) Activer Supabase Realtime sur `shopping_items` pour sync temps réel | Dev | 1h |
| T11.5 | Tests RTL : toggle + tri automatique + action réversible | QA | 1h |
| T11.6 | Test multi-membres : 2 onglets navigateur — synchronisation du statut d'un article | QA | 30min |

---

### HOME-01 — Résumé accueil

> **En tant que** membre, **je veux** voir un résumé sur la page d'accueil, **afin d'** avoir une vue rapide de mon foyer.

| Champ | Valeur |
|---|---|
| **EPIC** | E5 — Accueil & Navigation |
| **Sprint** | Sprint 3 |
| **Story Points** | 3 |
| **Priorité** | Must Have |
| **Dependencies** | TASK-01, TASK-04, SHOP-01, SHOP-02 (données existantes en base) |

#### Critères d'acceptation
- [ ] Section **Tâches** : affiche les 3 premières tâches non complétées du foyer
- [ ] Section **Courses** : affiche le nombre d'articles restants à acheter
- [ ] Tap sur la section Tâches → navigation Next.js vers `/tasks`
- [ ] Tap sur la section Courses → navigation Next.js vers `/shopping`
- [ ] Aucune tâche en cours → message d'état vide : "Aucune tâche pour aujourd'hui 🎉"
- [ ] Liste de courses vide → message : "La liste de courses est vide"
- [ ] Salutation personnalisée avec le `display_name` de l'utilisateur connecté

#### Definition of Done
- [ ] *DoD globale respectée*
- [ ] Les données affichées proviennent exclusivement du foyer actif (RLS vérifié)
- [ ] Les 4 états couverts par tests RTL : tâches présentes, tâches vides, courses présentes, courses vides
- [ ] Temps de chargement de la page < 2s mesuré via Lighthouse sur mobile (réseau 4G simulé)
- [ ] Navigation via `<Link>` Next.js vers les onglets correspondants testée

#### Technical Tasks

| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T12.1 | Implémenter `GET /api/v1/dashboard?householdId=` : tâches non complétées (max 3) + nb articles restants | Dev | 2h |
| T12.2 | Créer le hook `useDashboard` avec `useState` + `useEffect` pour le fetching agrégé | Dev | 1h |
| T12.3 | Implémenter le composant `TaskSummaryCard` (3 tâches + lien `/tasks`) | Dev | 1h |
| T12.4 | Implémenter le composant `ShoppingSummaryCard` (compteur articles + lien `/shopping`) | Dev | 1h |
| T12.5 | Implémenter la salutation dynamique avec `display_name` depuis le contexte auth | Dev | 30min |
| T12.6 | Implémenter les états vides TailwindCSS pour chaque section | Dev | 1h |
| T12.7 | Assembler la page `app/(app)/dashboard/page.tsx` avec les composants et le hook | Dev | 1h |
| T12.8 | Tests RTL : 4 états (tâches présentes/vides × courses présentes/vides) | QA | 2h |
| T12.9 | Test Lighthouse mobile : score Performance ≥ 80 et LCP < 2s | QA | 30min |

---

## Récapitulatif du backlog

### Par sprint

| Sprint | Stories | Points | Livrable |
|---|---|---|---|
| **Sprint 1** | AUTH-01, AUTH-02, AUTH-03, HOME-02 | 11 pts | Auth fonctionnelle + navigation |
| **Sprint 2** | FOYER-01, FOYER-02, FOYER-03, TASK-01, TASK-04 | 14 pts | Foyer collaboratif + tâches |
| **Sprint 3** | SHOP-01, SHOP-02, HOME-01 | 7 pts | Courses + accueil synthèse |
| **Total** | **11 stories** | **32 pts** | **POC bout-en-bout** |

### Par rôle

| Rôle | Responsabilités dans ce backlog |
|---|---|
| **Product Owner** | Valider les critères d'acceptation avant chaque sprint · Prononcer le "Done" en Sprint Review · Prioriser les ajustements de périmètre |
| **Scrum Master** | Suivre les dépendances entre stories · S'assurer que chaque sprint démarre avec des DoD claires · Faciliter la levée des blocages techniques |
| **Developer** | Réaliser toutes les tâches préfixées Dev · Respecter l'ordre des dépendances techniques · Notifier le QA dès qu'une story est prête à tester |
| **QA** | Réaliser toutes les tâches préfixées QA · Écrire les tests (RTL / Jest) avant la Review · Valider les tests multi-utilisateurs et les métriques de performance |

### Dépendances globales

```
AUTH-01 ──► AUTH-02 ──► AUTH-03 ──► HOME-02
                                        │
                                        ▼
                              FOYER-01 ──► FOYER-02
                                   │
                              FOYER-03
                                   │
                    ┌──────────────┤
                    ▼              ▼
                TASK-01        SHOP-01
                    │              │
                TASK-04        SHOP-02
                    │              │
                    └──────┬───────┘
                           ▼
                        HOME-01
```

### Correspondance stack par couche

| Couche | Technologies utilisées dans ce backlog |
|---|---|
| **Routing & Pages** | Next.js App Router (`app/` directory, `layout.tsx`, `page.tsx`) |
| **Navigation** | Composant `<Link>` Next.js + `usePathname()` pour l'onglet actif |
| **UI & Style** | TailwindCSS (classes utilitaires, responsive `md:`, états `active:`) |
| **State management** | `useState` + `useEffect` (hooks React) — pas de state manager externe |
| **Formulaires** | React Hook Form + Zod (validation client et serveur) |
| **Backend** | API Routes Next.js (`app/api/v1/*/route.ts`) |
| **Auth** | Supabase Auth + `@supabase/ssr` + middleware Next.js (cookies HTTP-only) |
| **Base de données** | Supabase Postgres avec RLS policies par `household_id` |
| **Temps réel** | Supabase Realtime (optionnel Sprint 2–3, TASK-04 et SHOP-02) |
| **Tests** | Jest + React Testing Library (RTL) |
| **Déploiement** | Vercel (preview par PR + production sur `main`) |

---

*Backlog maintenu dans `docs/backlog/`. Toute modification de périmètre est soumise à validation PO avant le Sprint Planning.*
