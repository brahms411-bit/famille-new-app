# MVP POC — Périmètre de développement

> **Projet** : FoyerApp  
> **Document** : Sélection des User Stories pour POC AI Scrum Team  
> **Rôle** : Product Owner senior  
> **Date** : 2026-03-04  
> **Source** : FoyerNewApp_backlog_complet.md (29 stories, 8 EPICs)  
> **Objectif du POC** : Valider un système AI Scrum Team simulé sur un périmètre fonctionnel cohérent, déployable et démontrable

---

## 1. EPICs retenus

Sur les 8 EPICs du backlog, **5 sont retenus** pour le MVP POC. Les EPICs Calendrier/Événements, Planning repas et Paramètres sont explicitement exclus.

| # | EPIC | Stories sélectionnées | Statut |
|---|---|---|---|
| **E1** | Authentification | AUTH-01, AUTH-02, AUTH-03 | ✅ Retenu |
| **E2** | Gestion du foyer | FOYER-01, FOYER-02, FOYER-03 | ✅ Retenu |
| **E3** | Tâches | TASK-01, TASK-04 | ✅ Retenu (périmètre réduit) |
| **E4** | Liste de courses | SHOP-01, SHOP-02 | ✅ Retenu (périmètre réduit) |
| **E5** | Accueil & Navigation | HOME-01, HOME-02 | ✅ Retenu |
| ~~E6~~ | ~~Calendrier & Événements~~ | — | ❌ Hors POC |
| ~~E7~~ | ~~Planning repas~~ | — | ❌ Hors POC |
| ~~E8~~ | ~~Paramètres & Profil~~ | — | ❌ Hors POC |

---

## 2. User Stories MVP — 11 stories sélectionnées

### EPIC 1 — Authentification

#### ✅ AUTH-01 — Inscription email + mot de passe
> En tant que nouvel utilisateur, je veux m'inscrire avec mon email et un mot de passe, afin d'accéder à l'application.

**Critères d'acceptation retenus pour le POC :**
- Formulaire avec 3 champs : email, mot de passe, confirmation
- Validation en temps réel (format email, min 8 caractères, concordance)
- Création du profil en base (`profiles`) + session Supabase active
- Redirection vers "Créer ou rejoindre un foyer"

---

#### ✅ AUTH-02 — Connexion email + mot de passe
> En tant qu'utilisateur, je veux me connecter avec mon email et mon mot de passe, afin d'accéder à mon foyer.

**Critères d'acceptation retenus pour le POC :**
- Formulaire email + mot de passe
- Message d'erreur si identifiants incorrects
- Redirection vers l'accueil du foyer actif en cas de succès

---

#### ✅ AUTH-03 — Session persistante
> En tant qu'utilisateur, je veux rester connecté automatiquement, afin de ne pas ressaisir mes identifiants à chaque ouverture.

**Critères d'acceptation retenus pour le POC :**
- Session Supabase valide → redirection directe vers l'accueil sans repasser par le login
- Persistance après fermeture complète de l'app

> ⚠️ AUTH-04 (reset mot de passe) et AUTH-05 (déconnexion) sont exclus du POC.  
> La déconnexion sera gérée minimalement via un bouton sans écran dédié si nécessaire en cours de sprint.

---

### EPIC 2 — Gestion du foyer

#### ✅ FOYER-01 — Créer un foyer
> En tant que membre, je veux créer un foyer, afin d'inviter ma famille.

**Critères d'acceptation retenus pour le POC :**
- Saisie du nom du foyer (min 2 chars, max 50)
- Génération automatique d'un code d'invitation à 6 caractères
- Utilisateur devient `admin` dans `household_members`
- Redirection vers l'accueil du foyer créé

---

#### ✅ FOYER-02 — Rejoindre un foyer via code
> En tant que membre, je veux rejoindre un foyer via un code à 6 caractères, afin d'intégrer le foyer de quelqu'un.

**Critères d'acceptation retenus pour le POC :**
- Champ de saisie du code (insensible à la casse)
- Erreur si code invalide ou déjà membre
- Ajout avec rôle `member` dans `household_members`
- Redirection vers l'accueil du foyer rejoint

---

#### ✅ FOYER-03 — Partager le code d'invitation
> En tant que membre, je veux copier ou partager le code d'invitation, afin d'inviter facilement les autres.

**Critères d'acceptation retenus pour le POC :**
- Code visible sur la page du foyer
- Bouton "Copier" avec snackbar de confirmation
- Bouton "Partager" ouvrant le panneau natif iOS/Android

> ⚠️ FOYER-04 (switch multi-foyers) et FOYER-05 (avatars membres) sont exclus du POC.  
> Un utilisateur POC appartient à un seul foyer actif.

---

### EPIC 3 — Tâches *(périmètre réduit)*

#### ✅ TASK-01 — Créer une tâche
> En tant que parent, je veux créer une tâche avec titre et description, afin d'organiser le foyer.

**Critères d'acceptation retenus pour le POC :**
- Formulaire avec titre (obligatoire, max 100 chars) et description (optionnelle)
- Tâche liée au `household_id` actif
- Apparaît immédiatement dans la liste

---

#### ✅ TASK-04 — Compléter une tâche
> En tant que membre, je veux marquer une tâche comme complétée, afin de signaler mon avancement.

**Critères d'acceptation retenus pour le POC :**
- Case à cocher ou tap → `is_completed` = true
- Différenciation visuelle immédiate
- Action réversible
- Visible par tous les membres du foyer

> ⚠️ TASK-02 (assignation), TASK-03 (mes tâches), TASK-05 (date limite), TASK-06 (modification/suppression) sont exclus du POC.  
> La liste affiche toutes les tâches du foyer sans filtre ni assignation.

---

### EPIC 4 — Liste de courses *(périmètre réduit)*

#### ✅ SHOP-01 — Ajouter un article
> En tant que membre, je veux ajouter un article avec nom et quantité, afin de préparer mes courses.

**Critères d'acceptation retenus pour le POC :**
- Formulaire rapide : nom (obligatoire) + quantité (optionnelle, texte libre)
- Article lié au `household_id` actif
- Apparaît immédiatement dans la liste

---

#### ✅ SHOP-02 — Marquer un article comme acheté
> En tant que membre, je veux marquer un article comme acheté, afin de suivre ma progression en magasin.

**Critères d'acceptation retenus pour le POC :**
- Tap → `is_purchased` = true, différenciation visuelle (barré, déplacé en bas)
- Action réversible
- Statut visible en temps réel par tous les membres

> ⚠️ SHOP-03 (suppression) est exclu du POC. Priorité à la lisibilité du flux d'achat.

---

### EPIC 5 — Accueil & Navigation

#### ✅ HOME-01 — Résumé accueil
> En tant que membre, je veux voir un résumé sur la page d'accueil, afin d'avoir une vue rapide de mon foyer.

**Critères d'acceptation retenus pour le POC :**
- Affichage des tâches non complétées du foyer (max 3)
- Affichage du nombre d'articles de courses restants
- Tap sur chaque section → redirection vers l'écran correspondant
- Messages d'état vide si aucune donnée

> ⚠️ La section événements et repas est retirée du résumé (EPICs exclus du POC).

---

#### ✅ HOME-02 — Navigation par onglets
> En tant que membre, je veux naviguer entre les onglets, afin d'accéder rapidement aux features.

**Critères d'acceptation retenus pour le POC :**
- **3 onglets** (réduits vs les 5 du backlog) : Accueil, Tâches, Courses
- Onglet actif mis en évidence (Material Design 3)
- Navigation instantanée
- État de chaque onglet conservé (Riverpod)

> ⚠️ Les onglets Calendrier et Repas sont retirés — leurs EPICs sont hors POC.

---

## 3. Justification des choix

### Pourquoi ces 11 stories ?

**Principe directeur** : un utilisateur doit pouvoir, en moins de 5 minutes, créer un compte, créer ou rejoindre un foyer, ajouter une tâche et une course, puis voir le résumé depuis l'accueil. Ce parcours bout-en-bout est la valeur démontrable minimale du POC.

**Ce qui a été conservé :**

| Critère | Explication |
|---|---|
| AUTH-01/02/03 | Sans authentification fonctionnelle, rien n'est testable. La session persistante (AUTH-03) est indispensable pour ne pas avoir à se reconnecter à chaque test de sprint. |
| FOYER-01/02/03 | Le foyer est l'unité de données centrale. Sans création et invitation, l'aspect collaboratif — cœur de l'app — ne peut pas être testé. FOYER-03 (partage du code) est conservé car c'est la passerelle vers le test multi-utilisateurs. |
| TASK-01/04 | Le duo créer + compléter est le flux CRUD minimum pour valider l'architecture tâches sans complexité (pas d'assignation, pas de date). |
| SHOP-01/02 | Identique : ajouter + cocher couvre le flux courses sans surcharger le sprint. |
| HOME-01/02 | L'accueil résumé est la "vitrine" du POC : il agrège les données des autres modules et prouve que l'architecture fonctionne de bout en bout. La navigation par onglets est le squelette sans lequel aucun écran n'est accessible. |

**Ce qui a été exclu et pourquoi :**

| Story exclue | Raison |
|---|---|
| AUTH-04 (reset mdp) | Supabase gère le flow email nativement, non bloquant pour un POC en environnement contrôlé |
| AUTH-05 (déconnexion) | L'app peut être réinstallée pour les tests — non bloquant POC |
| FOYER-04 (multi-foyer) | Complexité UX non nécessaire pour valider l'AI Scrum Team sur un foyer unique |
| FOYER-05 (avatars) | Cosmétique — aucune valeur technique pour le POC |
| TASK-02/03/05/06 | Assignation, filtres et dates : couche de complexité inutile au premier sprint de validation |
| SHOP-03 (suppression) | Le flux d'achat fonctionne sans suppression pour un POC |
| EPICs Calendrier et Repas | Fonctionnalités secondaires absentes des objectifs POC définis |
| PARAM-01/02/03 | Paramètres non testables tant que le foyer de base ne fonctionne pas |

### Cohérence de la sélection

```
AUTH (3)  →  Accès sécurisé
    │
    ▼
FOYER (3)  →  Contexte collaboratif (créer + rejoindre + partager)
    │
    ▼
TASK (2) + SHOP (2)  →  Données fonctionnelles dans le foyer
    │
    ▼
HOME (2)  →  Synthèse visuelle prouvant le bout-en-bout
```

Chaque couche dépend de la précédente. La progression est linéaire et sans dépendance circulaire.

---

## 4. Ordre de développement recommandé

### Découpage en 3 sprints de 2 semaines

```
Sprint 1 ──────────────────────────────────────────── Fondations
  AUTH-01   Inscription
  AUTH-02   Connexion
  AUTH-03   Session persistante
  HOME-02   Navigation par onglets (squelette vide)

  → Livrable : un utilisateur peut s'inscrire, se connecter
    et voir la navigation. Aucune données réelles encore.

Sprint 2 ──────────────────────────────────────────── Foyer & Données
  FOYER-01  Créer un foyer
  FOYER-02  Rejoindre un foyer via code
  FOYER-03  Partager le code d'invitation
  TASK-01   Créer une tâche
  TASK-04   Compléter une tâche

  → Livrable : deux utilisateurs peuvent former un foyer
    et collaborer sur une liste de tâches.

Sprint 3 ──────────────────────────────────────────── Courses & Accueil
  SHOP-01   Ajouter un article
  SHOP-02   Marquer un article comme acheté
  HOME-01   Résumé accueil

  → Livrable : POC complet. L'accueil résumé agrège
    tâches et courses. Parcours bout-en-bout démontrable.
```

### Dépendances techniques à respecter

```
AUTH-01 ──► AUTH-02 ──► AUTH-03
                │
                ▼
           FOYER-01 ──► FOYER-02
                │             │
                ▼             ▼
           FOYER-03       HOME-02 (squelette)
                │
                ├──► TASK-01 ──► TASK-04
                │
                └──► SHOP-01 ──► SHOP-02
                                      │
                                      ▼
                                   HOME-01
```

### Estimation indicative (story points)

| Story | Complexité | Points |
|---|---|---|
| AUTH-01 | Moyenne (formulaire + Supabase) | 5 |
| AUTH-02 | Faible (réutilise AUTH-01) | 2 |
| AUTH-03 | Faible (config Supabase session) | 2 |
| HOME-02 | Faible (squelette navigation) | 2 |
| FOYER-01 | Moyenne (DB + code génération) | 5 |
| FOYER-02 | Moyenne (lookup + join) | 3 |
| FOYER-03 | Faible (clipboard + share) | 2 |
| TASK-01 | Faible (formulaire simple) | 2 |
| TASK-04 | Faible (toggle DB) | 2 |
| SHOP-01 | Faible (réutilise TASK-01) | 2 |
| SHOP-02 | Faible (réutilise TASK-04) | 2 |
| HOME-01 | Moyenne (agrégation multi-tables) | 3 |
| **Total** | | **32 pts** |

Vélocité cible pour une AI Scrum Team : **10–12 points par sprint** → couvert en 3 sprints.

---

## Récapitulatif

| Sprint | Stories | Points | Livrable clé |
|---|---|---|---|
| Sprint 1 | AUTH-01, AUTH-02, AUTH-03, HOME-02 | 11 | Authentification + navigation |
| Sprint 2 | FOYER-01, FOYER-02, FOYER-03, TASK-01, TASK-04 | 14 | Foyer collaboratif + tâches |
| Sprint 3 | SHOP-01, SHOP-02, HOME-01 | 7 | Courses + accueil synthèse |
| **Total** | **11 stories** | **32 pts** | **POC bout-en-bout** |

---

*Ce document est la référence de périmètre pour le POC. Toute story ajoutée en cours de sprint doit être validée par le Product Owner.*
