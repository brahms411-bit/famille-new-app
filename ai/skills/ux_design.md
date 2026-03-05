# Skill — UX Design Mobile-First

> **Système** : AI Scrum Team  
> **Rôle** : UX Designer (agent IA)  
> **Version** : 1.0  
> **Date** : 2026-03-04  
> **Stack** : Next.js (App Router) · TailwindCSS · PWA  
> **Scope** : Conception UX mobile-first — des principes à la livraison d'écrans prêts à développer

---

## Table des matières

1. [Mission du skill](#1-mission-du-skill)
2. [Principes UX mobile-first](#2-principes-ux-mobile-first)
3. [Conception des écrans](#3-conception-des-écrans)
4. [Navigation](#4-navigation)
5. [Accessibilité](#5-accessibilité)
6. [Bonnes pratiques UX](#6-bonnes-pratiques-ux)

---

## 1. Mission du skill

Le skill UX Design permet à un agent IA jouant le rôle de **UX Designer** de concevoir des interfaces mobiles-first cohérentes, accessibles et directement implémentables par le Developer dans une stack Next.js + TailwindCSS.

Son objectif central est de **transformer des User Stories en spécifications d'écrans précises** — wireframes textuels, systèmes de composants, comportements d'interaction et règles d'accessibilité — de sorte que le Developer n'ait jamais à deviner une intention de design.

Le UX Designer ne code pas. Il produit la **description complète et non ambiguë** de ce que l'interface doit être, comment elle se comporte, et pourquoi ces choix servent l'utilisateur.

> **Principe directeur** : *Concevoir d'abord pour le pouce, le réseau lent et la lumière du soleil — tout le reste en découle.*

---

## 2. Principes UX mobile-first

### 2.1 Mobile-first comme contrainte de conception, pas d'affichage

Mobile-first ne signifie pas "faire une version desktop et la rétrécir". C'est concevoir **à partir des contraintes les plus sévères** :

```
Contraintes mobiles à intégrer dès la conception :

  Écran      → 375px de large minimum (iPhone SE)
  Interaction → doigt, pas souris (zone de tap ≥ 44×44px)
  Réseau     → 3G/4G variable, pas de fibre garantie
  Contexte   → en mouvement, distrait, une main disponible
  Batterie   → animations coûteuses = UX dégradée
  Lumière    → plein soleil = contraste critique
```

La version desktop est une **extension progressive** de la version mobile, pas l'inverse.

### 2.2 Hiérarchie de l'information

Sur mobile, l'espace est rare. Chaque pixel a un coût.

```
Règle des 3 niveaux :

  Niveau 1 — Ce que l'utilisateur DOIT voir        (above the fold)
    → Action principale, donnée critique, alerte

  Niveau 2 — Ce que l'utilisateur CHERCHE          (scroll court)
    → Liste principale, contenu secondaire

  Niveau 3 — Ce que l'utilisateur PEUT AVOIR       (scroll long ou modale)
    → Détails, paramètres, actions destructives
```

**Règle d'or** : si un élément est sur mobile au niveau 3, il est probablement inutile.

### 2.3 Touch-first design

Toutes les interactions sont conçues pour le doigt avant le curseur :

| Élément interactif | Taille minimale | Espacement minimal |
|---|---|---|
| Bouton principal | 48px height | 8px entre boutons |
| Zone de tap (icône) | 44×44px | 12px autour |
| Ligne de liste cliquable | 56px height | — |
| Champ de formulaire | 48px height | 16px entre champs |
| Case à cocher / toggle | 44×44px zone de tap | — |

> Ces valeurs correspondent aux guidelines Apple HIG et Google Material — les navigateurs mobiles les appliquent nativement pour le zoom automatique sur les inputs.

### 2.4 Performance perçue

L'UX mobile est directement liée à la performance perçue. Le UX Designer intègre ces contraintes dans ses choix :

```
Éviter                              Privilégier
─────────────────────────────────────────────────────────
Images non optimisées               next/image avec srcset
Animations JS complexes             CSS transitions simples
Fetch au chargement initial         Skeleton screens
Modales lourdes pour chaque action  Actions inline
États de chargement bloquants       Optimistic updates + spinner discret
```

### 2.5 Contexte d'usage de l'application

Pour FoyerApp, le UX Designer garde en permanence en tête le contexte réel d'usage :

```
Scénario A — Cuisine (usage fréquent)
  → Mains humides ou occupées, one-thumb navigation
  → Ajout d'article de courses : doit fonctionner en 2 taps maximum

Scénario B — Course en magasin
  → Lumière vive, distraction, temps limité
  → Cochage d'articles : target large, feedback visuel immédiat et lisible

Scénario C — Soirée canapé
  → Confort, moins de pression, two-thumb
  → Dashboard et création de tâches : plus de place pour le contenu

Scénario D — Invitation d'un membre
  → Usage ponctuel, premier contact avec l'app
  → Onboarding et code d'invitation : zéro friction, guidage explicite
```

---

## 3. Conception des écrans

### 3.1 Méthode de spécification d'un écran

Pour chaque écran, le UX Designer produit une **fiche écran** structurée :

```
FICHE ÉCRAN — [Nom de l'écran]
════════════════════════════════════════════════════════
Story liée        : [ID story — ex: AUTH-01]
URL / Route       : [ex: /register]
Objectif utilisateur : [Ce que l'utilisateur veut accomplir]
Contexte d'usage  : [Quand et comment cet écran est atteint]

LAYOUT MOBILE (375px)
────────────────────────────────────────
[Description textuelle du layout du haut vers le bas]

COMPORTEMENTS
────────────────────────────────────────
[Description des interactions, états, transitions]

ÉTATS DE L'ÉCRAN
────────────────────────────────────────
☐ État vide (empty state)
☐ État de chargement
☐ État nominal (données présentes)
☐ État d'erreur
☐ État de succès / confirmation

ADAPTATION DESKTOP (≥ 768px)
────────────────────────────────────────
[Ce qui change — layout, composants, tailles]

COMPOSANTS RÉUTILISABLES IDENTIFIÉS
────────────────────────────────────────
[Liste des composants TailwindCSS à créer ou réutiliser]
════════════════════════════════════════════════════════
```

### 3.2 Système de grille TailwindCSS

Le UX Designer spécifie les layouts avec les utilitaires Tailwind standard :

```
Mobile (base)
  Padding horizontal : px-4 (16px)
  Padding vertical   : py-6 (24px)
  Espacement entre sections : space-y-6
  Max-width contenu  : w-full

Tablet (md: — 768px+)
  Padding horizontal : md:px-6 (24px)
  Grille 2 colonnes  : md:grid-cols-2

Desktop (lg: — 1024px+)
  Max-width conteneur : lg:max-w-4xl mx-auto
  Sidebar + contenu   : lg:flex lg:gap-8
```

### 3.3 Système de typographie

```
Hiérarchie typographique pour FoyerApp :

  Page title   (H1) : text-2xl font-bold      → 24px, présent une fois par page
  Section title (H2) : text-lg font-semibold   → 18px, sections majeures
  Card title   (H3) : text-base font-medium    → 16px, éléments de liste
  Body text         : text-sm                  → 14px, descriptions, metadata
  Caption / label   : text-xs text-gray-500    → 12px, labels, dates, statuts

Lisibilité mobile :
  → Jamais en dessous de text-xs (12px) pour du contenu actionnable
  → Toujours au moins text-sm (14px) pour du contenu informatif principal
  → line-height 1.5 minimum (leading-relaxed) pour les paragraphes
```

### 3.4 Système de couleurs (design tokens TailwindCSS)

Le UX Designer spécifie les couleurs par rôle sémantique, pas par valeur hexadécimale :

```
Couleurs fonctionnelles :

  Primaire (actions, liens actifs)   : couleur principale de la marque
  Secondaire (éléments de support)   : variante atténuée du primaire
  Succès (confirmations, done)       : green-600 / green-100 (bg)
  Erreur (validations, alertes)      : red-600 / red-50 (bg)
  Avertissement (risques, retards)   : amber-600 / amber-50 (bg)
  Neutre texte principal             : gray-900
  Neutre texte secondaire            : gray-500
  Neutre fond page                   : gray-50
  Neutre fond carte                  : white + shadow-sm
  Séparateur                        : gray-200

Règle de contraste (WCAG AA) :
  → Texte normal sur fond clair : ratio ≥ 4.5:1
  → Texte large (≥ 18px bold) : ratio ≥ 3:1
  → Icône interactive : ratio ≥ 3:1
```

### 3.5 Bibliothèque de composants — inventaire FoyerApp

Le UX Designer maintient l'inventaire des composants de l'application :

#### Composants atomiques

| Composant | Description | Props clés |
|---|---|---|
| `Button` | Bouton primaire / secondaire / destructif | `variant`, `size`, `loading`, `disabled` |
| `Input` | Champ de formulaire avec label et erreur | `label`, `error`, `type`, `placeholder` |
| `Checkbox` | Case à cocher stylée avec zone de tap | `checked`, `onChange`, `label` |
| `Toggle` | Switch on/off pour statuts | `checked`, `onChange` |
| `Badge` | Indicateur de statut coloré | `variant` (success/warning/error/neutral) |
| `Avatar` | Initiale ou image de profil | `name`, `src`, `size` |
| `Toast` | Notification temporaire | `message`, `variant`, `duration` |
| `Spinner` | Indicateur de chargement inline | `size` |

#### Composants composés

| Composant | Description | Usage |
|---|---|---|
| `PageHeader` | Titre + action principale | Toutes les pages de liste |
| `EmptyState` | Illustration + message + CTA | Listes vides |
| `TaskCard` | Carte de tâche avec checkbox | Liste des tâches |
| `ShoppingItemCard` | Article de courses cochable | Liste de courses |
| `SummaryCard` | Carte de résumé cliquable | Dashboard accueil |
| `InviteCodeCard` | Affichage code + Copier/Partager | Paramètres foyer |
| `FormModal` | Modale de formulaire bottom-sheet mobile | Création d'items |
| `ConfirmDialog` | Dialogue de confirmation destructive | Suppressions |

---

## 4. Navigation

### 4.1 Structure de navigation FoyerApp

```
App (authentifiée)
│
├── /dashboard          ← Accueil résumé
├── /tasks              ← Liste des tâches
└── /shopping           ← Liste de courses

Auth (non authentifiée)
│
├── /login
├── /register
└── /household-setup    ← Créer ou rejoindre un foyer
```

### 4.2 Navigation mobile — Bottom Navigation Bar

Sur mobile (< 768px), la navigation principale est une **barre fixe en bas d'écran** :

```
BOTTOM NAV BAR — Mobile

┌─────────────────────────────────────────────────┐
│                  [Contenu de la page]            │
│                                                  │
│                                                  │
│                                                  │
├─────────────────────────────────────────────────┤
│  🏠 Accueil    ✅ Tâches    🛒 Courses           │  ← 56px height
│   [actif]                                        │  ← safe-area-bottom
└─────────────────────────────────────────────────┘

Spécifications TailwindCSS :
  Conteneur : fixed bottom-0 left-0 right-0 z-50
              bg-white border-t border-gray-200
              pb-safe (safe-area-inset-bottom pour iPhone)
  Tab actif : text-primary font-medium
  Tab inactif : text-gray-400
  Zone de tap : flex-1 flex flex-col items-center py-2
  Icône : h-6 w-6
  Label : text-xs mt-1
```

**Règles de la Bottom Nav :**
- 3 onglets maximum sur mobile — au-delà, utiliser un menu "Plus"
- Le label est toujours visible — jamais d'icône seule sans label sur mobile
- L'onglet actif est identifiable par couleur ET par poids typographique (pas uniquement la couleur)
- La barre respecte le `safe-area-inset-bottom` (encoche iPhone)

### 4.3 Navigation desktop — Sidebar

Sur desktop (≥ 768px), la navigation devient une **sidebar gauche** :

```
SIDEBAR — Desktop

┌──────────────┬────────────────────────────────────┐
│  FoyerApp    │                                     │
│  [Logo]      │      [Contenu de la page]           │
│              │                                     │
│  ─────────   │                                     │
│  🏠 Accueil  │                                     │
│  ✅ Tâches   │                                     │
│  🛒 Courses  │                                     │
│              │                                     │
│  ─────────   │                                     │
│  [Foyer nom] │                                     │
│  [Avatar]    │                                     │
└──────────────┴────────────────────────────────────┘

Spécifications TailwindCSS :
  Sidebar : hidden md:flex md:flex-col md:w-64
            border-r border-gray-200 bg-white
  Contenu : flex-1 overflow-y-auto p-6
```

### 4.4 Patterns de navigation secondaire

#### Modale / Drawer (création d'items)

Sur mobile, les formulaires de création s'ouvrent en **bottom drawer** (glisse du bas) :

```
BOTTOM DRAWER — Mobile

┌─────────────────────────────────────────────────┐
│                [Fond assombri 50%]              │
├─────────────────────────────────────────────────┤
│  ▬  [Handle drag indicator]                     │
│                                                  │
│  Créer une tâche                                │
│                                                  │
│  [Champ titre]                                  │
│  [Champ description]                            │
│                                                  │
│  [Bouton Créer — full width]                    │
└─────────────────────────────────────────────────┘

Spécifications :
  Overlay : fixed inset-0 bg-black/50 z-40
  Drawer  : fixed bottom-0 left-0 right-0 z-50
            bg-white rounded-t-2xl p-6
            max-h-[90vh] overflow-y-auto
  Handle  : w-12 h-1 bg-gray-300 rounded-full mx-auto mb-6
```

Sur desktop (≥ 768px), le drawer devient une **modale centrée** :

```
  md:inset-auto md:top-1/2 md:left-1/2
  md:-translate-x-1/2 md:-translate-y-1/2
  md:w-full md:max-w-lg md:rounded-2xl
```

#### Toast / Notifications

Les confirmations d'action s'affichent en **toast** en haut de l'écran :

```
TOAST — Mobile et Desktop

┌─────────────────────────────────────────────────┐
│  ✅  Code copié !                          ✕    │  ← 48px height
└─────────────────────────────────────────────────┘

Position  : fixed top-4 left-4 right-4 z-50 (mobile)
            md:top-4 md:right-4 md:left-auto md:w-80 (desktop)
Durée     : 2 secondes auto-dismiss
Animation : slide-in depuis le haut + fade out
```

#### Confirmation destructive

Les actions irréversibles (suppression) déclenchent un **dialog de confirmation** :

```
⚠️  Supprimer la tâche ?

    Cette action est irréversible.

    [Annuler]          [Supprimer]
     (secondaire)       (destructif — red-600)
```

Règle : le bouton destructif est **toujours à droite** et jamais le premier visuellement mis en avant.

### 4.5 Transitions et animations

```
Principe : les animations servent la compréhension, pas le spectacle.

Transition de page     : fade (opacity 0→1, 150ms) — discret
Ouverture drawer       : slide-up (translateY 100%→0, 300ms ease-out)
Fermeture drawer       : slide-down (translateY 0→100%, 200ms ease-in)
Apparition toast       : slide-down + fade (200ms)
Cochage d'item         : line-through + opacity (150ms)
Bouton loading         : spinner inline, pas de changement de taille
État vide → données    : fade-in staggered (délai 50ms entre items)

TailwindCSS :
  transition-all duration-150 ease-in-out
  transition-opacity duration-200
```

**Règle d'accessibilité** : toutes les animations respectent `prefers-reduced-motion` :

```css
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
```

---

## 5. Accessibilité

### 5.1 Standard cible : WCAG 2.1 niveau AA

FoyerApp vise la conformité **WCAG 2.1 niveau AA** sur toutes les pages principales. Le UX Designer intègre les exigences d'accessibilité dès la conception — pas en post-traitement.

### 5.2 Contraste des couleurs

```
Texte normal (< 18px ou < 14px bold) :  ratio ≥ 4.5:1
Texte large  (≥ 18px ou ≥ 14px bold) :  ratio ≥ 3.0:1
Composant UI / graphique informatif  :  ratio ≥ 3.0:1

Outils de vérification :
  → WebAIM Contrast Checker (https://webaim.org/resources/contrastchecker/)
  → Chrome DevTools → Inspect → Accessibility

Paires validées pour FoyerApp :
  gray-900 sur white       : 16.1:1  ✅
  gray-500 sur white       : 4.6:1   ✅ (texte secondaire, min requis)
  white sur primary-600    : ≥ 4.5:1 ✅ (à vérifier selon la couleur primaire choisie)
  red-600 sur white        : 4.6:1   ✅ (messages d'erreur)
  gray-400 sur white       : 2.7:1   ❌ (placeholder — acceptable car décoratif)
```

### 5.3 Navigation au clavier et focus

Toutes les interactions sont accessibles au clavier :

```
Tab         → Naviguer entre éléments interactifs (ordre logique dans le DOM)
Shift+Tab   → Navigation inverse
Enter/Space → Activer boutons, checkboxes, liens
Escape      → Fermer modales, drawers, menus déroulants
Arrow keys  → Naviguer dans les listes et menus

Focus visible :
  → outline-2 outline-offset-2 outline-primary sur tous les éléments focusables
  → Ne jamais utiliser outline: none sans alternative visible
  → focus-visible:ring-2 focus-visible:ring-primary (TailwindCSS)

Pièges de focus (focus trap) :
  → Les modales et drawers capturent le focus tant qu'ils sont ouverts
  → À la fermeture, le focus retourne à l'élément qui a ouvert la modale
```

### 5.4 Attributs ARIA

Le UX Designer spécifie les attributs ARIA nécessaires pour chaque composant :

```
Bouton avec état de chargement :
  <button aria-busy="true" aria-label="Création en cours...">
    <Spinner /> Créer
  </button>

Checkbox de complétion de tâche :
  <input type="checkbox"
    aria-label="Marquer 'Faire les courses' comme complétée"
    checked={isCompleted} />

Navigation principale :
  <nav aria-label="Navigation principale">
    <a aria-current="page">Accueil</a>  ← sur l'onglet actif uniquement
  </nav>

Modale :
  <div role="dialog"
    aria-modal="true"
    aria-labelledby="modal-title">
    <h2 id="modal-title">Créer une tâche</h2>
  </div>

Message d'erreur de formulaire :
  <input aria-describedby="email-error" aria-invalid="true" />
  <p id="email-error" role="alert">Adresse email invalide</p>

Toast / notification :
  <div role="status" aria-live="polite">Code copié !</div>  ← succès
  <div role="alert"  aria-live="assertive">Erreur réseau</div> ← erreur critique
```

### 5.5 Sémantique HTML

```
Toujours utiliser les éléments HTML sémantiques avant ARIA :

  <button>      → Actions (pas <div onClick>)
  <a href>      → Navigation (pas <div onClick>)
  <nav>         → Zones de navigation
  <main>        → Contenu principal de la page
  <header>      → En-tête de page ou de section
  <h1>–<h6>     → Hiérarchie de titres (une seule <h1> par page)
  <ul> / <li>   → Listes (tâches, articles de courses)
  <form>        → Formulaires avec <label> associé à chaque <input>
  <time>        → Dates et heures (attribut datetime)

Règle : si un élément natif HTML existe pour l'usage, l'utiliser.
        ARIA est un patch, pas un remplacement.
```

### 5.6 Tailles de cible tactile

```
Règle WCAG 2.5.5 (AA) : cible ≥ 24×24px, cible recommandée ≥ 44×44px

Implémentation TailwindCSS :
  Icône seule dans une barre      : p-3 (zone de tap 44px avec icône 20px)
  Bouton texte                    : py-3 px-4 (hauteur 48px)
  Ligne de liste cliquable        : py-4 (hauteur 56px avec padding)
  Checkbox / toggle               : wrapper min-h-[44px] min-w-[44px]
```

---

## 6. Bonnes pratiques UX

### 6.1 Formulaires

Les formulaires sont souvent les points de friction les plus critiques sur mobile.

**Validation :**

```
✅ Validation en temps réel sur blur (après que l'utilisateur quitte le champ)
✅ Validation à la soumission pour les erreurs globales
❌ Validation on-change dès le premier caractère (frustrant)
❌ Message d'erreur uniquement après soumission (trop tardif)

Format des messages d'erreur :
  → Toujours positif et actionnable : "Saisissez un email valide"
  → Jamais accusateur : ❌ "Email invalide" → ✅ "Vérifiez le format de votre email"
  → Placé immédiatement sous le champ concerné, pas en haut de page
  → Couleur rouge (red-600) + icône ⚠️ pour visibilité mobile
```

**Champs :**

```
Toujours spécifier :
  → inputmode="email"    → clavier email sur mobile
  → inputmode="numeric"  → clavier numérique pour quantités
  → autocomplete="email" → suggestions navigateur
  → autocomplete="new-password" → pas de suggestion pour création mdp

Label toujours visible :
  → Jamais utiliser placeholder comme substitut au label
  → Le placeholder disparaît dès la saisie — l'utilisateur perd le contexte
  → Label au-dessus du champ, toujours visible
```

**Bouton de soumission :**

```
États à concevoir :
  1. Default    : [Créer]                      → couleur primaire
  2. Disabled   : [Créer]                      → opacity-50, cursor-not-allowed
  3. Loading    : [⟳ Création en cours...]    → disabled + spinner
  4. Success    : [✓ Créé !]                  → feedback 1s avant reset ou redirect
  5. Error      : [Réessayer]                 → après erreur réseau

Règle : le bouton ne change jamais de taille entre ses états.
        Aucun layout shift pendant le chargement.
```

### 6.2 États vides (Empty States)

Un état vide bien conçu est une opportunité de guidage, pas une absence de contenu.

```
Structure d'un état vide :

  [Illustration ou icône — 64px]
  [Titre : "Aucune tâche pour aujourd'hui"]
  [Sous-titre : "Créez votre première tâche pour organiser le foyer."]
  [Bouton CTA : "+ Créer une tâche"]

Règles :
  → Toujours inclure un CTA pour sortir de l'état vide
  → Ton encourageant, jamais alarmiste
  → Sur mobile : illustration légère (SVG inline), jamais d'image lourde
  → L'état vide est la première chose vue par un nouvel utilisateur — soigner son message
```

### 6.3 Feedback et confirmation

Chaque action de l'utilisateur doit recevoir un retour immédiat :

```
Action                       Feedback attendu                     Délai
─────────────────────────────────────────────────────────────────────────
Tap sur un bouton            Changement visuel (pressed state)    0ms
Soumission d'un formulaire   Spinner sur le bouton                0ms
Création réussie             Toast "Tâche créée" + item dans liste < 500ms
Cochage d'un item            line-through + opacity réduite        0ms (optimistic)
Copie dans le presse-papier  Toast "Code copié !" (2s)            0ms
Erreur réseau                Message d'erreur inline + retry CTA  après timeout
```

**Optimistic updates** : pour les actions fréquentes (cocher une tâche, cocher un article), l'UI se met à jour **immédiatement** sans attendre la réponse serveur. En cas d'échec, rollback discret avec message d'erreur.

### 6.4 Gestion des erreurs

```
Types d'erreurs et leur traitement UX :

  Erreur de validation (formulaire)
  → Inline, sous le champ, rouge, immédiate
  → Bouton de soumission reste actif pour retry

  Erreur réseau (appel API échoué)
  → Toast d'erreur : "Une erreur est survenue. Réessayer ?"
  → Bouton "Réessayer" dans le toast ou inline
  → Conserver les données saisies — ne jamais vider le formulaire sur erreur réseau

  Erreur 404 (ressource introuvable)
  → Page dédiée avec message compréhensible + lien retour
  → Ne pas exposer les codes d'erreur techniques à l'utilisateur

  Erreur d'autorisation (403)
  → Redirection vers /login avec message contextuel
  → Après login réussi, redirection vers la page initialement demandée
```

### 6.5 Onboarding (premier usage)

Pour FoyerApp, le premier parcours utilisateur est critique :

```
Étape 1 : Inscription (AUTH-01)
  → Formulaire minimaliste — 3 champs seulement
  → Pas de demande d'informations non essentielles (nom, téléphone → plus tard)
  → Progression visible si multi-étapes

Étape 2 : Création ou rejoindre un foyer (FOYER-01/02)
  → Deux options visuellement équilibrées : "Créer" et "Rejoindre"
  → Expliquer en une ligne la différence : "Vous organisez la famille" vs "Quelqu'un vous a invité"
  → Pas d'étape inutile — si code dans l'URL, pré-remplir automatiquement

Étape 3 : Premier accueil
  → État vide bienveillant avec CTA principal visible
  → Pas de tutorial forcé — permettre l'exploration libre
  → Hint discret sur la première action recommandée
```

### 6.6 Responsive design — règles de progression

```
Mobile (< 768px)  → Conception principale
  Layout    : colonne unique, full-width
  Nav       : bottom navigation bar fixe
  Formulaires : bottom drawer (full-width)
  Listes    : cartes full-width, dense
  Typographie : text-sm pour le contenu, text-base pour les titres

Tablet (768px–1024px)  → Adaptation
  Layout    : grille 2 colonnes pour les listes longues (md:grid-cols-2)
  Nav       : sidebar 240px ou top nav
  Formulaires : modale centrée (max-w-md)

Desktop (≥ 1024px)  → Extension
  Layout    : sidebar + contenu central max-w-4xl
  Dashboard : grille 3 colonnes pour les summary cards (lg:grid-cols-3)
  Formulaires : modale centrée (max-w-lg) avec padding généreux
```

### 6.7 Spécificités PWA

FoyerApp étant une PWA, le UX Designer prend en compte :

```
Installation :
  → Banner d'installation natif du navigateur (Add to Home Screen)
  → Ne pas créer de prompts d'installation custom intrusifs
  → Icônes d'app requises : 192×192px et 512×512px (SVG ou PNG)

Safe areas (iPhone avec encoche / Dynamic Island) :
  → padding-top  : env(safe-area-inset-top)
  → padding-bottom : env(safe-area-inset-bottom)    ← critique pour bottom nav
  → TailwindCSS : pb-safe (plugin ou extend)

Offline / réseau dégradé :
  → Banner discret si connexion perdue : "Vous êtes hors ligne"
  → Les données déjà chargées restent affichées (pas d'écran blanc)
  → Les actions offline sont mises en file d'attente (v2)

Splash screen :
  → Fond coloré + logo centré pendant le chargement initial
  → Configuré dans le manifest.json (background_color, theme_color)
```

---

## Annexes

### A. Checklist — Revue d'un écran

```
LAYOUT
- [ ] Conçu en 375px en premier (mobile-first)
- [ ] Zones de tap ≥ 44×44px pour tous les éléments interactifs
- [ ] Padding horizontal ≥ 16px (px-4)
- [ ] Aucun overflow horizontal non voulu

CONTENU
- [ ] Hiérarchie visuelle claire (H1 → H2 → body)
- [ ] Aucun texte en dessous de 12px
- [ ] Tous les états de l'écran spécifiés (vide, loading, erreur, succès)
- [ ] Empty state avec CTA si applicable

ACCESSIBILITÉ
- [ ] Contraste texte principal ≥ 4.5:1
- [ ] Contraste texte large ≥ 3:1
- [ ] Attributs ARIA spécifiés pour composants non-natifs
- [ ] Ordre de focus logique documenté
- [ ] Pas d'information transmise par la couleur seule

INTERACTION
- [ ] Feedback immédiat sur chaque action (0ms)
- [ ] États de chargement définis (spinner, skeleton, disabled)
- [ ] Optimistic updates identifiés
- [ ] Gestion des erreurs réseau spécifiée

RESPONSIVE
- [ ] Comportement md: (tablet) défini
- [ ] Comportement lg: (desktop) défini
- [ ] Safe areas prises en compte (bottom nav, top status bar)
```

### B. Antipatterns UX mobile à éviter

| Antipattern | Symptôme | Alternative |
|---|---|---|
| Placeholder comme label | Label disparaît à la saisie | Label visible au-dessus du champ |
| Bouton trop petit | Tap manqué, frustration | Zone de tap ≥ 44×44px minimum |
| Modal sur mobile plein écran | Navigation confuse, back button problématique | Bottom drawer avec handle |
| Validation on-change immédiate | Erreur dès le premier caractère | Validation on-blur |
| Toast en bas sur mobile | Caché par la bottom nav | Toast en haut de l'écran |
| Disabled sans explication | Utilisateur bloqué sans raison | Tooltip ou message explicatif |
| Infinite scroll sans feedback | Utilisateur perdu, pas de fin visible | Loader + message "Tout est chargé" |
| Couleur seule pour l'état | Inaccessible aux daltoniens | Couleur + icône + texte |
| Forcer l'orientation paysage | Casse l'usage naturel mobile | Concevoir pour les deux orientations |

### C. Références et outils

| Ressource | URL | Usage |
|---|---|---|
| TailwindCSS Docs | https://tailwindcss.com/docs | Référence des utilitaires CSS |
| WCAG 2.1 AA | https://www.w3.org/WAI/WCAG21/quickref/ | Critères d'accessibilité |
| WebAIM Contrast | https://webaim.org/resources/contrastchecker/ | Vérification des contrastes |
| Apple HIG Mobile | https://developer.apple.com/design/human-interface-guidelines/ | Conventions iOS |
| Google Material 3 | https://m3.material.io/ | Conventions Android |
| Next.js Image | https://nextjs.org/docs/app/api-reference/components/image | Optimisation images |

### D. Références projet

| Document | Localisation | Rôle dans ce skill |
|---|---|---|
| Product Spec | `docs/product/product_spec.md` | Personas et fonctionnalités cibles |
| Architecture Overview | `docs/architecture/architecture_overview.md` | Contraintes stack pour les composants |
| Backlog AI Scrum | `docs/backlog/ai_scrum_backlog.md` | Stories à traduire en écrans |
| Frontend Design Skill | `ai/skills/frontend-design/SKILL.md` | Référence pour la qualité visuelle |

---

*Ce document est la référence UX pour l'agent IA jouant le rôle de UX Designer. Il est mis à jour à chaque nouvelle feature ou évolution de la charte graphique de FoyerApp.*
