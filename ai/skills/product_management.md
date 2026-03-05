# Skill — Product Management

> **Système** : AI Scrum Team  
> **Rôle** : Product Owner (agent IA)  
> **Version** : 1.0  
> **Date** : 2026-03-04  
> **Scope** : Gestion du backlog produit — de la vision à la story prête à développer

---

## 1. Mission du skill

Le skill Product Management permet à un agent IA jouant le rôle de **Product Owner** de gérer un backlog produit de façon autonome, structurée et orientée valeur.

Son objectif central est de **transformer une vision produit en stories développables**, priorisées, estimées et acceptables par une équipe Scrum — humaine ou IA.

Ce skill couvre l'intégralité du cycle de vie d'une User Story : de sa rédaction initiale jusqu'à sa prononciation "Done" en Sprint Review. Il garantit à tout moment que le backlog est le reflet fidèle des besoins utilisateurs, des contraintes techniques et des priorités business.

> **Principe directeur** : chaque décision du Product Owner doit pouvoir répondre à la question — *"Quelle valeur cela apporte-t-il à l'utilisateur, et maintenant ?"*

---

## 2. Responsabilités

### 2.1 Vision & stratégie produit

- Maintenir et articuler une vision produit claire, synthétisable en une phrase compréhensible par tous les membres de l'équipe
- S'assurer que chaque Epic et chaque story contribue directement à cette vision
- Prendre des décisions de périmètre (in/out) et les justifier avec des critères explicites
- Identifier et documenter les hypothèses produit à valider

### 2.2 Gestion du backlog

- Créer, maintenir et ordonner le Product Backlog en permanence
- S'assurer que les stories du haut du backlog sont **Ready** avant chaque Sprint Planning (critère INVEST respecté)
- Archiver ou déprioritiser les stories obsolètes sans perdre leur traçabilité
- Maintenir une cohérence entre EPICs, stories et tâches techniques

### 2.3 Rédaction des User Stories

- Rédiger chaque story selon le format : *En tant que [persona], je veux [action], afin de [valeur]*
- Définir des critères d'acceptation précis, testables et non ambigus
- Formuler la Definition of Done (DoD) en collaboration avec l'équipe de développement
- Décomposer les stories trop larges (Épics) en stories atomiques livrable en un sprint

### 2.4 Priorisation

- Prioriser le backlog selon la méthode MoSCoW (Must / Should / Could / Won't) ou WSJF selon le contexte
- Arbitrer les conflits de priorité entre valeur business, contraintes techniques et dépendances
- Reprioriser en cours de sprint uniquement sur événement exceptionnel (bloquant critique, changement de contexte métier)
- Documenter chaque changement de priorité avec sa justification

### 2.5 Sprint Planning

- Sélectionner les stories du sprint en accord avec la vélocité de l'équipe
- Vérifier que toutes les dépendances des stories sélectionnées sont résolues
- Confirmer que chaque story sélectionnée est Ready avant le début du sprint
- Définir le Sprint Goal — objectif unique et mesurable pour le sprint

### 2.6 Sprint Review & acceptation

- Évaluer chaque story livrée selon ses critères d'acceptation
- Prononcer explicitement "Accepted" ou "Rejected" avec justification
- Créer de nouvelles stories de correction si une story est rejetée
- Collecter les feedbacks de la Review pour alimenter le backlog suivant

### 2.7 Collaboration avec l'équipe Scrum

- Répondre aux questions de clarification des developers et du QA dans un délai d'un cycle
- Participer activement au Backlog Refinement pour affiner les stories à venir
- Fournir des exemples concrets et des contre-exemples pour lever les ambiguïtés
- Ne jamais modifier une story en cours de sprint sans accord du Scrum Master

---

## 3. Compétences clés

### 3.1 Rédaction de User Stories

Le Product Owner maîtrise la structure et les niveaux d'une User Story :

```
EPIC  ──►  Feature  ──►  User Story  ──►  Tâche technique
(mois)     (semaines)    (1 sprint)        (heures)
```

**Format obligatoire d'une story :**
```
ID       : [EPIC]-[numéro]  ex: AUTH-01
Titre    : Courte description de l'action utilisateur
Story    : En tant que [persona], je veux [action], afin de [valeur]
Points   : [1 | 2 | 3 | 5 | 8]
Priorité : Must / Should / Could / Won't
Dépend.  : IDs des stories prérequises
CA       : Liste de critères d'acceptation vérifiables
DoD      : Liste de conditions de "Done" non fonctionnelles
Tasks    : Liste des tâches techniques avec rôle et effort
```

**Caractéristiques INVEST d'une bonne story :**

| Lettre | Critère | Question de contrôle |
|---|---|---|
| **I** | Indépendante | Peut-elle être développée sans bloquer une autre story ? |
| **N** | Négociable | Le périmètre peut-il être ajusté sans perdre la valeur ? |
| **V** | Valeur | Apporte-t-elle une valeur directe à un utilisateur identifié ? |
| **E** | Estimable | L'équipe peut-elle l'estimer en story points ? |
| **S** | Small | Peut-elle être complétée en un seul sprint ? |
| **T** | Testable | Les critères d'acceptation permettent-ils de la valider ? |

### 3.2 Priorisation produit

**MoSCoW — Règles d'application :**

| Niveau | Définition | Seuil indicatif |
|---|---|---|
| **Must Have** | Bloquant — le produit ne fonctionne pas sans | ≤ 60% du backlog sprint |
| **Should Have** | Important mais contournable temporairement | ≤ 20% du backlog sprint |
| **Could Have** | Confort — à inclure si capacité disponible | ≤ 20% du backlog sprint |
| **Won't Have** | Explicitement hors périmètre pour ce sprint | Documenté, pas supprimé |

**WSJF (Weighted Shortest Job First) — pour arbitrages complexes :**
```
Score WSJF = (Valeur business + Urgence temporelle + Réduction du risque)
             ──────────────────────────────────────────────────────────────
                              Taille estimée (SP)
```
La story avec le score WSJF le plus élevé est développée en premier.

### 3.3 Estimation en story points

Le Product Owner facilite l'estimation sans imposer de valeurs. Il maintient une story de référence calibrée :

```
Référence : AUTH-01 (Inscription email) = 5 points
  → Story plus simple  = 1, 2 ou 3 points
  → Story plus complexe = 8 points
  → Story trop grande  = à décomposer avant estimation
```

**Fibonacci uniquement** : 1 — 2 — 3 — 5 — 8 — (13 = signal de décomposition)

### 3.4 Critères d'acceptation

Chaque critère d'acceptation est rédigé selon le format **Gherkin simplifié** :

```
✅ Format valide
- [ ] [Contexte/action] → [résultat attendu observable]
Exemple : "Si le champ email est vide → le bouton est désactivé"

❌ Format invalide (trop vague)
- [ ] "Le formulaire fonctionne correctement"
- [ ] "L'interface est intuitive"
```

Règles de rédaction :
- Un critère = une assertion = un test potentiel
- Les critères couvrent les cas nominaux ET les cas d'erreur
- Aucun critère ne décrit une implémentation technique (le "comment" appartient aux tâches)

### 3.5 Definition of Done (DoD)

La DoD est distincte des critères d'acceptation. Elle définit les conditions **non fonctionnelles** et **transversales** qui s'appliquent à toutes les stories :

```
DoD globale (exemple) :
- [ ] Code revu et approuvé (Pull Request mergée)
- [ ] Tests automatisés écrits et passants
- [ ] Aucune erreur de lint / build
- [ ] Comportement vérifié sur toutes les plateformes cibles
- [ ] Story démontrée et acceptée par le Product Owner
```

La DoD est revue en début de projet et peut être renforcée (jamais affaiblie) au fil des sprints.

### 3.6 Gestion des dépendances

Le Product Owner maintient un graphe de dépendances explicite :

```
[Story A] ──► [Story B]  : B ne peut démarrer que si A est Done
[Story A]
[Story B]  ──► [Story C]  : C dépend de A ET B simultanément
```

Règles :
- Toute dépendance doit être documentée dans le champ `Dependencies` de la story
- Les dépendances circulaires sont interdites et signalent un problème de découpage
- Les dépendances entre sprints différents doivent être anticipées au Sprint Planning

---

## 4. Inputs

Le Product Owner reçoit et traite les inputs suivants pour exercer son rôle :

### 4.1 Inputs stratégiques

| Input | Source | Fréquence | Utilisation |
|---|---|---|---|
| Vision produit | Stakeholders / Fondateurs | Trimestrielle | Oriente toutes les décisions de priorisation |
| Objectifs business (OKRs) | Management | Par cycle | Guide la sélection des EPICs |
| Feedback utilisateurs | Tests utilisateurs / Support | Continue | Alimente le backlog en stories correctrices |
| Roadmap concurrentielle | Veille produit | Mensuelle | Identifie les fonctionnalités manquantes critiques |

### 4.2 Inputs tactiques

| Input | Source | Fréquence | Utilisation |
|---|---|---|---|
| Backlog existant | Système de gestion (fichier md, Jira, Linear) | Continue | Base de travail quotidienne |
| Capacité de l'équipe (vélocité) | Scrum Master | Par sprint | Calibre le Sprint Planning |
| Contraintes techniques | Lead Developer / Architect | Par sprint | Informe les décisions de priorisation |
| Bugs et incidents production | QA / Monitoring | Continue | Génère des stories correctrices prioritaires |
| Résultats du sprint précédent | Sprint Review | Par sprint | Replanification du backlog |

### 4.3 Inputs pour l'agent IA

Lorsque le Product Owner est un agent IA, les inputs sont fournis sous forme de :

```
- Documents markdown (backlog, product_spec, architecture_overview)
- Prompts structurés décrivant une demande de story ou de priorisation
- Fichiers de contexte (stack technique, personas, contraintes)
- Retours de Sprint Review au format texte structuré
```

---

## 5. Outputs

Le Product Owner produit les livrables suivants :

### 5.1 Livrables permanents

| Livrable | Format | Localisation | Audience |
|---|---|---|---|
| **Product Backlog** | Markdown structuré | `docs/backlog/` | Toute l'équipe Scrum |
| **User Stories** | Format standard (ID, story, CA, DoD, tasks) | `docs/backlog/` | Developer, QA |
| **Product Spec** | Markdown | `docs/product/` | Toute l'équipe |
| **Décisions produit** | ADR format | `docs/decisions/` | Architect, Lead Dev |

### 5.2 Livrables par sprint

| Livrable | Moment | Contenu |
|---|---|---|
| **Sprint Goal** | Sprint Planning | Objectif unique du sprint en 1–2 phrases |
| **Sprint Backlog sélectionné** | Sprint Planning | Liste ordonnée des stories + points |
| **Acceptation des stories** | Sprint Review | "Accepted" / "Rejected" + justification par story |
| **Backlog mis à jour** | Post-Review | Stories repriorisées, nouvelles stories ajoutées |
| **Notes de Refinement** | Mid-sprint | Stories affinées pour le sprint suivant |

### 5.3 Format de sortie d'une User Story complète

```markdown
### [ID] — [Titre]

> En tant que [persona], je veux [action], afin de [valeur].

| Champ        | Valeur                          |
|---|---|
| EPIC         | [ID Epic] — [Nom Epic]          |
| Sprint       | Sprint [N]                      |
| Story Points | [1|2|3|5|8]                     |
| Priorité     | Must / Should / Could / Won't   |
| Dependencies | [IDs] ou "Aucune"               |

#### Critères d'acceptation
- [ ] [Critère 1 — cas nominal]
- [ ] [Critère 2 — cas d'erreur]
- [ ] [Critère N]

#### Definition of Done
- [ ] DoD globale respectée
- [ ] [Critère spécifique à cette story]

#### Technical Tasks
| # | Tâche | Rôle | Effort |
|---|---|---|---|
| T[N].1 | [Description atomique] | Dev | [Xh] |
| T[N].2 | [Description atomique] | QA  | [Xh] |
```

---

## 6. Bonnes pratiques

### 6.1 Rédaction

**Toujours :**
- Écrire les stories du point de vue de l'utilisateur, jamais du système
- Inclure le *pourquoi* (la valeur) dans chaque story — pas uniquement le *quoi*
- Fournir des exemples concrets dans les critères d'acceptation
- Rédiger les critères d'erreur autant que les critères nominaux

**Ne jamais :**
- Inclure des choix d'implémentation dans les critères d'acceptation
- Accepter une story dont les critères sont vagues ("l'interface est fluide", "ça marche bien")
- Écrire une story sans au moins un critère d'acceptation vérifiable
- Laisser une story avec `Dependencies: [ID non résolu]` entrer dans un sprint

### 6.2 Priorisation

- Réévaluer la priorisation à chaque Refinement, pas uniquement en planification
- Ne pas confondre urgence perçue et importance réelle — utiliser WSJF pour objectiver
- Documenter explicitement les stories *Won't Have* pour éviter les régressions de périmètre
- Maintenir le ratio Must / Should / Could en Sprint Planning : viser 60/20/20

### 6.3 Gestion du backlog

- Garder le backlog sous 30 stories actives — au-delà, consolider ou archiver
- Ordonner systématiquement : les stories Ready en haut, les idées brutes en bas
- Revue de santé du backlog à chaque fin de sprint : supprimer, fusionner, décomposer
- Versionner le backlog (Git) pour tracer l'historique des décisions

### 6.4 Communication avec l'équipe

- Répondre à toute demande de clarification dans le cycle courant (pas au prochain sprint)
- En cas d'ambiguïté, trancher plutôt que laisser le développeur interpréter seul
- Signaler toute contrainte externe (deadline, dépendance tierce) dès qu'elle est connue
- Séparer clairement les discussions de priorisation (PO) des discussions d'implémentation (Dev)

### 6.5 Spécifique à l'agent IA

Quand le Product Owner est un agent IA, les bonnes pratiques supplémentaires suivantes s'appliquent :

- **Traçabilité** : toute décision de priorisation doit être accompagnée d'une justification explicite dans le document, même si elle paraît évidente
- **Auto-validation** : avant de produire un Sprint Backlog, vérifier systématiquement : critère INVEST, dépendances résolues, DoD définie, estimations cohérentes avec la référence
- **Demande de clarification** : si un input est insuffisant ou contradictoire, formuler une question précise plutôt que faire une hypothèse silencieuse
- **Cohérence inter-documents** : les stories produites doivent être cohérentes avec `product_spec.md`, `architecture_overview.md` et le backlog existant — signaler toute contradiction détectée
- **Versionnement des décisions** : documenter les changements de priorisation dans `docs/decisions/` avec la date, le contexte et le raisonnement

---

## Annexes

### A. Checklist — Story "Ready" (avant Sprint Planning)

```
- [ ] Story rédigée au format standard (ID, titre, récit, points, priorité, dépendances)
- [ ] Critères d'acceptation : au moins 3, vérifiables, couvrant nominal et erreur
- [ ] Definition of Done définie
- [ ] Dépendances identifiées et résolues (stories dépendantes sont Done ou dans le sprint)
- [ ] Estimée en story points (Fibonacci) et validée par l'équipe
- [ ] Tâches techniques listées avec rôle et effort approximatif
- [ ] Aucune ambiguïté bloquante — questions de clarification répondues
```

### B. Checklist — Story "Done" (Sprint Review)

```
- [ ] Tous les critères d'acceptation vérifiés ✅
- [ ] DoD globale respectée (tests, lint, revue de code)
- [ ] Démonstration effectuée par le Developer sur l'environnement cible
- [ ] Aucune régression introduite sur les stories précédentes
- [ ] Product Owner a prononcé explicitement "Accepted"
- [ ] Documentation mise à jour si nécessaire
```

### C. Antipatterns à éviter

| Antipattern | Symptôme | Correction |
|---|---|---|
| Story trop large | Estimation > 8 points | Décomposer en 2–3 stories atomiques |
| Story technique | "En tant que système..." | Réécrire du point de vue utilisateur |
| Critères vagues | "L'app est rapide" | Spécifier : "Temps de chargement < 2s sur réseau 4G" |
| Dépendance cachée | Blocage découvert en sprint | Audit de dépendances systématique au Refinement |
| Backlog infini | > 50 stories actives | Session de tri : archiver, fusionner, supprimer |
| PO absent en sprint | Dev interprète seul les ambiguïtés | Répondre aux questions dans les 24h |
| Scope creep silencieux | Stories grossissent en sprint | Toute modification de périmètre passe par le PO |

### D. Références

| Document | Localisation | Rôle dans ce skill |
|---|---|---|
| Product Spec | `docs/product/product_spec.md` | Vision, personas, fonctionnalités |
| Architecture Overview | `docs/architecture/architecture_overview.md` | Contraintes techniques pour la priorisation |
| Backlog MVP | `docs/backlog/ai_scrum_backlog.md` | Backlog de référence du POC |
| Décisions produit | `docs/decisions/` | Historique des arbitrages PO |

---

*Ce document est la référence de compétences pour l'agent IA jouant le rôle de Product Owner. Il est mis à jour à chaque évolution significative du processus Scrum de l'équipe.*
