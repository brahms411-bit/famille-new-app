# Architecture — Source of Truth

## Objectif

Ce document définit la stack technique officielle du projet FoyerApp.

Tous les développements, prompts IA et décisions d'architecture doivent respecter cette stack.

---

## Frontend

Framework : Next.js (App Router)
Type : Progressive Web App (mobile-first)
Langage : TypeScript
UI : TailwindCSS

Principes :

* Mobile-first design
* Composants React modulaires
* Server Components privilégiés
* Client components seulement si nécessaire

---

## Backend

Backend : Next.js API routes
Architecture : serverless
Langage : TypeScript

Responsabilités :

* logique métier
* validation des requêtes
* orchestration avec Supabase

---

## Database

Base de données : Supabase Postgres

Principes :

* multi-tenant par `household_id`
* Row Level Security activé
* migrations versionnées

Tables principales :

profiles
households
household_members
tasks
shopping_items

---

## Authentification

Service : Supabase Auth

Méthode :

email + mot de passe

Session persistante gérée par Supabase.

---

## Déploiement

Hosting : Vercel

Pipeline :

GitHub → Vercel deployment automatique

---

## Principes d'architecture

1. Mobile-first
2. Simplicité avant optimisation
3. Architecture modulaire
4. Code lisible par humains et agents IA
5. Données isolées par `household_id`

---

## Règle importante pour les agents IA

Toute implémentation doit respecter cette stack.

Les technologies suivantes sont explicitement exclues :

* Flutter
* React Native
* Firebase
* Express.js standalone
* architectures monolithiques non serverless
