# Product Specification — famille_new_app

> **Version** : 1.0  
> **Statut** : Draft  
> **Product Owner** : à compléter  
> **Dernière mise à jour** : 2026-03-04  
> **Équipe** : Scrum — à compléter

---

## Table des matières

1. [Vision produit](#1-vision-produit)
2. [Utilisateurs cibles](#2-utilisateurs-cibles)
3. [Fonctionnalités principales](#3-fonctionnalités-principales)
4. [MVP Scope](#4-mvp-scope)
5. [Contraintes techniques](#5-contraintes-techniques)
6. [Architecture générale](#6-architecture-générale)
7. [Critères de succès](#7-critères-de-succès)

---

## 1. Vision produit

### 1.1 Énoncé de vision

> *Pour les familles qui peinent à coordonner la gestion quotidienne de leur foyer, **famille_new_app** est une application web collaborative qui centralise dépenses, tâches, courses et budget en un seul endroit. Contrairement aux outils génériques (tableurs, applications séparées), notre solution est conçue dès le départ pour le foyer : multi-membres, simple et accessible à tous les âges.*

### 1.2 Problème résolu

Les familles jonglent aujourd'hui avec plusieurs outils épars — une application pour les courses, un tableur pour le budget, un groupe WhatsApp pour les tâches — ce qui génère de la friction, des doublons et des oublis. Il n'existe pas de solution simple, unifiée et adaptée à la dynamique familiale.

### 1.3 Proposition de valeur

- **Centralisation** : un seul endroit pour tout gérer
- **Collaboration** : chaque membre du foyer a son accès et ses responsabilités
- **Clarté budgétaire** : vision en temps réel des dépenses et de l'équilibre du budget
- **Simplicité** : interface pensée pour des utilisateurs non-techniques, y compris les enfants

### 1.4 Positionnement

| Dimension | Choix |
|---|---|
| Marché | B2C — familles francophones |
| Modèle | Freemium (MVP gratuit) |
| Plateforme | Web responsive (desktop + mobile) |
| Langue | Français (v1), multilingue envisagé (v2) |

---

## 2. Utilisateurs cibles

### 2.1 Personas

#### Persona 1 — Le gestionnaire du foyer *(utilisateur principal)*

- **Profil** : adulte 30–50 ans, gère les finances et l'organisation familiale
- **Objectifs** : suivre les dépenses, répartir les tâches, ne rien oublier
- **Frustrations** : manque de visibilité globale, outils trop complexes ou trop génériques
- **Usage attendu** : quotidien, sur desktop et mobile

#### Persona 2 — Le co-gérant *(conjoint/partenaire)*

- **Profil** : adulte 30–50 ans, partage les responsabilités du foyer
- **Objectifs** : consulter, contribuer aux tâches et courses, rester informé du budget
- **Frustrations** : ne pas être dans la boucle, devoir redemander les informations
- **Usage attendu** : quotidien, principalement mobile

#### Persona 3 — Le membre junior *(adolescent)*

- **Profil** : 12–17 ans, veut participer à la gestion de son espace
- **Objectifs** : voir ses tâches, cocher les courses, avoir de la responsabilité
- **Frustrations** : interfaces trop complexes, sentiment d'exclusion
- **Usage attendu** : ponctuel, mobile

### 2.2 Rôles dans l'application

| Rôle | Permissions |
|---|---|
| **Admin du foyer** | Création du foyer, gestion des membres, toutes les fonctionnalités |
| **Membre adulte** | Accès complet aux modules (dépenses, tâches, courses, budget) |
| **Membre junior** | Accès tâches et courses, lecture seule sur le budget |

---

## 3. Fonctionnalités principales

### 3.1 Module — Gestion des membres du foyer

- Création d'un foyer avec un code d'invitation
- Invitation de membres par email ou lien
- Profil par membre (nom, avatar, rôle)
- Gestion des rôles (Admin / Adulte / Junior)
- Désactivation d'un membre sans suppression des données

**Valeur** : socle de toute l'application — chaque action est rattachée à un membre.

---

### 3.2 Module — Dépenses

- Saisie d'une dépense (montant, catégorie, date, payeur, description)
- Catégories prédéfinies (alimentation, logement, transport, loisirs, santé, autre)
- Catégories personnalisables par le foyer
- Historique des dépenses avec filtres (période, catégorie, membre)
- Modification et suppression d'une dépense
- Tag de dépenses récurrentes (loyer, abonnements)

---

### 3.3 Module — Dashboard budget

- Solde mensuel : revenus déclarés − dépenses du mois
- Répartition des dépenses par catégorie (graphique)
- Comparaison mois en cours vs mois précédent
- Indicateurs d'alerte si dépassement de seuil (paramétrable)
- Contribution de chaque membre aux dépenses du foyer
- Export mensuel (CSV)

---

### 3.4 Module — Tâches

- Création d'une tâche (titre, description, assigné à, date d'échéance, priorité)
- Statuts : À faire / En cours / Terminé
- Vue liste et vue kanban
- Tâches récurrentes (hebdomadaires, mensuelles)
- Notifications de rappel (in-app, v2 : email/push)
- Historique des tâches complétées

---

### 3.5 Module — Liste de courses

- Création de listes de courses nommées
- Ajout d'articles (nom, quantité, unité, catégorie)
- Cochage en temps réel (synchronisé entre membres)
- Suggestions basées sur les articles fréquents
- Archivage automatique d'une liste complétée
- Partage d'une liste avec un membre non inscrit (lien public, v2)

---

## 4. MVP Scope

### 4.1 Principe de priorisation

Le MVP doit être livrable en **3 sprints de 2 semaines** et démontrer la valeur fondamentale : *une famille peut gérer son foyer depuis un seul outil*.

### 4.2 Ce qui est dans le MVP ✅

| # | Fonctionnalité | Priorité |
|---|---|---|
| M1 | Authentification (inscription, connexion, déconnexion) | Must have |
| M2 | Création et gestion d'un foyer | Must have |
| M3 | Invitation et gestion des membres | Must have |
| M4 | Saisie et liste des dépenses (sans récurrence) | Must have |
| M5 | Dashboard budget — solde mensuel + répartition par catégorie | Must have |
| M6 | Tâches — CRUD, assignation, statut | Must have |
| M7 | Liste de courses — CRUD, cochage synchronisé | Must have |
| M8 | Navigation responsive (desktop + mobile) | Must have |
| M9 | Rôles Admin / Adulte | Should have |

### 4.3 Ce qui est hors MVP ❌ *(backlog v2)*

- Tâches et dépenses récurrentes
- Notifications email / push
- Export CSV
- Membre junior avec permissions restreintes
- Graphiques comparatifs multi-mois
- Partage de liste de courses en lien public
- Mode multilingue

### 4.4 Découpage en sprints indicatif

| Sprint | Objectif | Stories incluses |
|---|---|---|
| **Sprint 1** | Authentification & foyer | M1, M2, M3 |
| **Sprint 2** | Dépenses & budget | M4, M5 |
| **Sprint 3** | Tâches, courses & polish | M6, M7, M8, M9 |

---

## 5. Contraintes techniques

### 5.1 Stack imposée

| Couche | Technologie | Version cible |
|---|---|---|
| Frontend | Next.js (App Router) | 14+ |
| Backend | API Routes Next.js | — |
| Base de données | Supabase Postgres | — |
| Authentification | Supabase Auth | — |
| Hébergement | Vercel (frontend) + Supabase Cloud | — |
| Styling | Tailwind CSS | 3+ |

### 5.2 Contraintes de sécurité

- Authentification obligatoire sur toutes les routes protégées
- Row Level Security (RLS) activé sur toutes les tables Supabase — un utilisateur ne peut accéder qu'aux données de son foyer
- Variables d'environnement pour toutes les clés API (jamais en dur dans le code)
- HTTPS obligatoire en production

### 5.3 Contraintes de performance

- First Contentful Paint < 2s sur mobile 4G
- Les listes (dépenses, tâches, courses) supportent jusqu'à 500 items sans dégradation perceptible
- La synchronisation de la liste de courses doit être quasi-temps réel (Supabase Realtime)

### 5.4 Contraintes de qualité

- Couverture de tests unitaires ≥ 70% sur les fonctions utilitaires et les API routes
- Lint (ESLint) et formatage (Prettier) obligatoires — bloquants en CI
- Revue de code systématique (PR approuvée par au moins 1 reviewer avant merge)
- Pas de `console.log` en production

### 5.5 Contraintes d'accessibilité

- Conformité WCAG 2.1 niveau AA sur les pages principales
- Support des navigateurs : Chrome, Firefox, Safari (2 dernières versions majeures)

---

## 6. Architecture générale

### 6.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT                                  │
│              Next.js App Router (React)                         │
│         Pages / Components / Hooks / Context                    │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP / fetch
┌────────────────────────▼────────────────────────────────────────┐
│                      API LAYER                                  │
│              Next.js API Routes (/api/*)                        │
│         Validation (Zod) — Auth check — Business logic          │
└────────────────────────┬────────────────────────────────────────┘
                         │ Supabase JS Client
┌────────────────────────▼────────────────────────────────────────┐
│                      DATA LAYER                                 │
│                  Supabase (Cloud)                               │
│         Postgres + RLS │ Auth │ Realtime (courses)              │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Modèle de données (simplifié)

```
foyers
  id, nom, code_invitation, created_at

membres
  id, foyer_id, user_id (Supabase Auth), nom, avatar_url, role, created_at

depenses
  id, foyer_id, membre_id, montant, categorie, description, date, created_at

categories_depenses
  id, foyer_id, nom, couleur, icone

taches
  id, foyer_id, titre, description, assigne_a (membre_id), statut,
  priorite, date_echeance, created_at, updated_at

listes_courses
  id, foyer_id, nom, archivee, created_at

articles_courses
  id, liste_id, nom, quantite, unite, coche, coche_par (membre_id), created_at
```

### 6.3 Flux d'authentification

```
1. Utilisateur s'inscrit → Supabase Auth crée un user
2. Callback → création automatique d'un profil membre en DB
3. JWT Supabase stocké en cookie HTTP-only (Next.js middleware)
4. Chaque requête API vérifie le JWT → récupère le foyer_id du membre
5. RLS Supabase garantit l'isolation des données par foyer
```

### 6.4 Synchronisation temps réel (liste de courses)

```
1. Client s'abonne au channel Supabase Realtime pour sa liste
2. Cochage d'un article → UPDATE en base → événement broadcast
3. Tous les clients abonnés reçoivent la mise à jour en < 500ms
```

---

## 7. Critères de succès

### 7.1 Critères de lancement (MVP)

Ces critères doivent être satisfaits avant la mise en production :

- [ ] Un foyer peut être créé, et des membres invités s'y connectent avec leur propre compte
- [ ] Les dépenses saisies apparaissent correctement dans le dashboard budget
- [ ] Une tâche peut être créée, assignée, et passée à "Terminé" par un membre différent de celui qui l'a créée
- [ ] Deux membres peuvent cocher des articles d'une même liste de courses simultanément, et les deux voient les mises à jour en temps réel
- [ ] Un utilisateur ne peut pas voir les données d'un autre foyer (RLS vérifié par test)
- [ ] L'application est utilisable sur mobile sans défilement horizontal

### 7.2 KPIs produit (3 mois post-lancement)

| Indicateur | Cible |
|---|---|
| Foyers créés | ≥ 50 |
| Taux de rétention à 30 jours | ≥ 40% |
| Membres actifs par foyer (moyenne) | ≥ 2 |
| Actions par session (dépense / tâche / course) | ≥ 3 |
| Taux de complétion d'une liste de courses | ≥ 60% |

### 7.3 Critères de qualité technique

| Indicateur | Cible |
|---|---|
| Couverture de tests | ≥ 70% |
| Taux d'erreurs API (production) | < 1% |
| Uptime | ≥ 99,5% |
| FCP mobile | < 2s |
| Score Lighthouse Performance | ≥ 80 |

### 7.4 Critères d'expérience utilisateur

- Un nouveau membre peut créer un compte, rejoindre un foyer et saisir sa première dépense en moins de **5 minutes**
- Aucun parcours critique ne dépasse **3 clics** depuis le dashboard
- L'application est utilisable sans documentation ni formation

---

## Annexes

### A. Glossaire

| Terme | Définition |
|---|---|
| Foyer | Unité familiale regroupant un ou plusieurs membres dans l'application |
| Membre | Utilisateur authentifié appartenant à un foyer |
| Admin du foyer | Membre avec droits de gestion du foyer et des autres membres |
| RLS | Row Level Security — mécanisme Supabase d'isolation des données |
| FCP | First Contentful Paint — métrique de performance web |

### B. Liens utiles

| Ressource | URL |
|---|---|
| Repository GitHub | `https://github.com/<org>/famille-new-app` |
| Documentation Supabase | https://supabase.com/docs |
| Documentation Next.js | https://nextjs.org/docs |
| Backlog | `docs/backlog/` |
| Décisions d'architecture | `docs/decisions/` |

---

*Ce document est la référence produit pour l'équipe Scrum. Il est mis à jour à chaque fin de sprint ou lors d'un changement de périmètre validé en refinement.*
