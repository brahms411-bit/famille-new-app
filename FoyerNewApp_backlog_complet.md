# Backlog FoyerApp — Toutes les User Stories

## Contexte projet
- **App** : FoyerApp — application mobile de gestion de foyer familial
- **Stack** : Flutter + Supabase + Riverpod + GoRouter
- **UI** : Material Design 3, navigation par onglets, interface en français
- **Utilisateurs** : familles et colocataires partageant un foyer

## Schéma base de données Supabase
```
profiles        (id, display_name, first_name, last_name, avatar_url, language)
households      (id, name, invite_code)
household_members (household_id, profile_id, role)
tasks           (household_id, title, description, assigned_to, due_date, is_completed)
events          (household_id, title, description, event_date)
meals           (household_id, name, meal_type, date)
shopping_items  (household_id, name, quantity, is_purchased)
```

---

# EPIC 1 — Authentification

## AUTH-01 — Inscription email + mot de passe
> **En tant que** nouvel utilisateur, **je veux** m'inscrire avec mon email et un mot de passe, **afin d'** accéder à l'application.

### Critères d'acceptation
#### Formulaire
- [ ] L'écran d'inscription affiche 3 champs : email, mot de passe, confirmation mot de passe
- [ ] Un bouton "S'inscrire" est visible et accessible
- [ ] Un lien "Déjà un compte ? Se connecter" redirige vers l'écran de connexion

#### Validation en temps réel
- [ ] Si l'email est invalide → message d'erreur inline : "Adresse email invalide"
- [ ] Si le mot de passe fait moins de 8 caractères → message d'erreur inline : "Le mot de passe doit contenir au moins 8 caractères"
- [ ] Si les deux mots de passe ne correspondent pas → message d'erreur inline : "Les mots de passe ne correspondent pas"
- [ ] Tant que le formulaire est invalide → le bouton "S'inscrire" est désactivé

#### Soumission
- [ ] Si l'email est déjà utilisé → message d'erreur : "Un compte existe déjà avec cet email"
- [ ] Pendant l'appel réseau → un indicateur de chargement est affiché sur le bouton
- [ ] En cas d'erreur réseau → message d'erreur : "Une erreur est survenue, veuillez réessayer"

#### Succès
- [ ] En cas de succès → un profil est créé en base (table `profiles`) avec l'`id` de l'utilisateur Supabase
- [ ] En cas de succès → l'utilisateur est automatiquement connecté (session Supabase active)
- [ ] En cas de succès → redirection via GoRouter vers l'écran "Créer ou rejoindre un foyer"

**Out of scope** : Magic Link, connexion Google/Apple, vérification email par lien

---

## AUTH-02 — Connexion email + mot de passe
> **En tant qu'** utilisateur, **je veux** me connecter avec mon email et mon mot de passe, **afin d'** accéder à mon foyer.

### Critères d'acceptation
- [ ] L'écran de connexion affiche 2 champs : email et mot de passe
- [ ] Un bouton "Se connecter" est visible
- [ ] Un lien "Pas encore de compte ? S'inscrire" redirige vers l'écran d'inscription
- [ ] Un lien "Mot de passe oublié ?" redirige vers l'écran de réinitialisation
- [ ] Si les identifiants sont incorrects → message d'erreur : "Email ou mot de passe incorrect"
- [ ] Pendant l'appel réseau → indicateur de chargement sur le bouton
- [ ] En cas de succès → redirection vers l'accueil du foyer actif

---

## AUTH-03 — Session persistante
> **En tant qu'** utilisateur, **je veux** rester connecté automatiquement, **afin de** ne pas ressaisir mes identifiants à chaque ouverture.

### Critères d'acceptation
- [ ] À la réouverture de l'app, si une session Supabase valide existe → l'utilisateur est directement redirigé vers l'accueil sans repasser par l'écran de connexion
- [ ] La session persiste après fermeture complète de l'app
- [ ] La session persiste après redémarrage du téléphone

---

## AUTH-04 — Réinitialisation du mot de passe
> **En tant qu'** utilisateur, **je veux** réinitialiser mon mot de passe, **afin de** récupérer l'accès si je l'oublie.

### Critères d'acceptation
- [ ] Un écran dédié affiche un champ email et un bouton "Envoyer le lien de réinitialisation"
- [ ] Si l'email est invalide → message d'erreur inline
- [ ] Après soumission → message de confirmation : "Un email vous a été envoyé"
- [ ] Le lien reçu par email permet de définir un nouveau mot de passe (géré par Supabase)
- [ ] Si l'email n'existe pas en base → afficher le même message de confirmation (sécurité)

---

## AUTH-05 — Déconnexion
> **En tant qu'** utilisateur connecté, **je veux** me déconnecter, **afin de** sécuriser mon compte.

### Critères d'acceptation
- [ ] Un bouton "Se déconnecter" est accessible depuis l'écran Paramètres
- [ ] Une confirmation est demandée avant déconnexion
- [ ] Après déconnexion → redirection vers l'écran de connexion
- [ ] La session Supabase est invalidée (impossible de revenir en arrière sans se reconnecter)

---

# EPIC 2 — Gestion du foyer

## FOYER-01 — Créer un foyer
> **En tant que** membre, **je veux** créer un foyer, **afin d'** inviter ma famille.

### Critères d'acceptation
- [ ] Un écran permet de saisir le nom du foyer (obligatoire, min 2 caractères, max 50)
- [ ] Si le champ est vide → bouton de création désactivé
- [ ] À la création → un code d'invitation unique à 6 caractères alphanumériques est généré automatiquement
- [ ] Le foyer créé apparaît immédiatement dans la liste des foyers de l'utilisateur
- [ ] L'utilisateur devient automatiquement membre avec le rôle `admin` (table `household_members`)

---

## FOYER-02 — Rejoindre un foyer via code
> **En tant que** membre, **je veux** rejoindre un foyer via un code à 6 caractères, **afin d'** intégrer le foyer de quelqu'un.

### Critères d'acceptation
- [ ] Un champ de saisie accepte un code à 6 caractères (insensible à la casse)
- [ ] Si le code est invalide ou inexistant → message d'erreur : "Code invalide ou introuvable"
- [ ] Si l'utilisateur est déjà membre de ce foyer → message d'erreur : "Vous êtes déjà membre de ce foyer"
- [ ] En cas de succès → l'utilisateur est ajouté avec le rôle `member` dans `household_members`
- [ ] En cas de succès → redirection vers l'accueil du foyer rejoint

---

## FOYER-03 — Partager le code d'invitation
> **En tant que** membre, **je veux** copier ou partager le code d'invitation, **afin d'** inviter facilement les autres.

### Critères d'acceptation
- [ ] Le code d'invitation est visible sur la page de gestion du foyer
- [ ] Un bouton "Copier" copie le code dans le presse-papier et affiche un snackbar : "Code copié !"
- [ ] Un bouton "Partager" ouvre le panneau de partage natif iOS/Android
- [ ] Le message partagé contient le code et une phrase d'invitation lisible en français

---

## FOYER-04 — Lister et basculer entre foyers
> **En tant que** membre, **je veux** voir mes foyers et basculer entre eux, **afin de** gérer plusieurs foyers.

### Critères d'acceptation
- [ ] La liste de tous les foyers de l'utilisateur est accessible depuis les Paramètres
- [ ] Le foyer actif est clairement identifié visuellement (badge, couleur, icône)
- [ ] Un tap sur un foyer le définit comme foyer actif
- [ ] Après changement de foyer → toutes les données (tâches, repas, courses, événements) se rechargent pour ce foyer
- [ ] Si l'utilisateur n'a qu'un seul foyer, la liste reste visible

---

## FOYER-05 — Avatars des membres
> **En tant que** membre, **je veux** voir les avatars des membres du foyer, **afin de** savoir qui en fait partie.

### Critères d'acceptation
- [ ] Les avatars des 5 premiers membres sont affichés
- [ ] Si le foyer compte plus de 5 membres → affichage "+X" pour les membres supplémentaires
- [ ] Si un membre n'a pas d'avatar → affichage de son initiale sur fond coloré
- [ ] Les avatars sont visibles sur la page d'accueil du foyer

---

# EPIC 3 — Tâches

## TASK-01 — Créer une tâche
> **En tant que** parent, **je veux** créer une tâche avec titre et description, **afin d'** organiser le foyer.

### Critères d'acceptation
- [ ] Un formulaire de création contient : titre (obligatoire, max 100 caractères), description (optionnelle)
- [ ] Si le titre est vide → soumission impossible, message d'erreur affiché
- [ ] La tâche créée apparaît immédiatement dans la liste des tâches du foyer actif
- [ ] La tâche est liée au `household_id` du foyer actif

---

## TASK-02 — Assigner une tâche
> **En tant que** parent, **je veux** assigner une tâche à un membre, **afin de** responsabiliser chacun.

### Critères d'acceptation
- [ ] Lors de la création ou modification, une liste déroulante affiche les membres du foyer actif
- [ ] Un seul membre peut être assigné à la fois (champ `assigned_to`)
- [ ] L'assignation est optionnelle
- [ ] Le nom du membre assigné est visible sur la carte de la tâche

---

## TASK-03 — Voir ses tâches assignées
> **En tant que** membre, **je veux** voir les tâches qui me sont assignées, **afin de** savoir ce que j'ai à faire.

### Critères d'acceptation
- [ ] Un filtre "Mes tâches" est disponible sur l'écran Tâches
- [ ] Les tâches filtrées correspondent uniquement à celles dont `assigned_to` = l'utilisateur connecté
- [ ] Les tâches complétées sont visuellement distinguées (barrées ou dans une section séparée)

---

## TASK-04 — Compléter une tâche
> **En tant que** membre, **je veux** marquer une tâche comme complétée, **afin de** signaler mon avancement.

### Critères d'acceptation
- [ ] Une case à cocher ou un bouton permet de compléter une tâche en un tap (champ `is_completed`)
- [ ] La tâche complétée est visuellement différenciée immédiatement
- [ ] L'action est réversible (décocher remet `is_completed` à false)
- [ ] Le statut est visible par tous les membres du foyer

---

## TASK-05 — Date limite sur une tâche
> **En tant que** parent, **je veux** définir une date limite sur une tâche, **afin de** prioriser les urgences.

### Critères d'acceptation
- [ ] Un sélecteur de date est disponible dans le formulaire de création/modification (champ `due_date`)
- [ ] La date limite est affichée sur la carte de la tâche
- [ ] Les tâches en retard (due_date dépassée, is_completed = false) sont signalées visuellement (couleur rouge ou icône)
- [ ] La date limite est optionnelle

---

## TASK-06 — Modifier ou supprimer une tâche
> **En tant que** parent, **je veux** modifier ou supprimer une tâche, **afin de** maintenir la liste à jour.

### Critères d'acceptation
- [ ] Un tap sur une tâche ouvre le formulaire de modification pré-rempli
- [ ] Tous les champs (titre, description, assignation, date) sont modifiables
- [ ] Une option "Supprimer" est disponible avec une confirmation avant suppression
- [ ] Après suppression → la tâche disparaît immédiatement de la liste

---

# EPIC 4 — Calendrier & Événements

## EVENT-01 — Calendrier mensuel
> **En tant que** membre, **je veux** voir un calendrier mensuel, **afin d'** avoir une vue d'ensemble.

### Critères d'acceptation
- [ ] Un calendrier mensuel s'affiche sur l'onglet Calendrier
- [ ] Les jours ayant des événements sont marqués visuellement (point ou indicateur coloré)
- [ ] Un tap sur un jour affiche la liste des événements de ce jour
- [ ] Navigation possible vers le mois précédent et suivant

---

## EVENT-02 — Créer un événement
> **En tant que** membre, **je veux** créer un événement avec titre, description et date, **afin de** planifier.

### Critères d'acceptation
- [ ] Un formulaire contient : titre (obligatoire), description (optionnelle), date (obligatoire, champ `event_date`)
- [ ] Si le titre ou la date est manquant → message d'erreur, soumission bloquée
- [ ] L'événement créé apparaît immédiatement sur le calendrier au bon jour
- [ ] L'événement est lié au `household_id` du foyer actif

---

## EVENT-03 — Modifier ou supprimer un événement
> **En tant que** membre, **je veux** modifier ou supprimer un événement, **afin de** le maintenir à jour.

### Critères d'acceptation
- [ ] Un tap sur un événement ouvre le formulaire de modification pré-rempli
- [ ] Tous les champs sont modifiables
- [ ] Une option "Supprimer" est disponible avec une confirmation
- [ ] Après suppression → l'événement disparaît immédiatement du calendrier

---

# EPIC 5 — Planning repas

## MEAL-01 — Planifier les repas
> **En tant que** membre, **je veux** planifier les repas par type et par jour, **afin d'** organiser la semaine.

### Critères d'acceptation
- [ ] Une vue hebdomadaire affiche les 3 types de repas par jour : petit-déjeuner, déjeuner, dîner (champ `meal_type`)
- [ ] Un tap sur un créneau vide permet d'ajouter un repas (champ `name` obligatoire)
- [ ] Le repas ajouté s'affiche immédiatement dans le bon créneau
- [ ] Navigation entre les semaines possible (semaine précédente / suivante)

---

## MEAL-02 — Modifier ou supprimer un repas
> **En tant que** membre, **je veux** modifier ou supprimer un repas planifié, **afin d'** ajuster en cas de changement.

### Critères d'acceptation
- [ ] Un tap sur un repas existant permet de le modifier ou supprimer
- [ ] Une confirmation est demandée avant suppression
- [ ] Après modification/suppression → le créneau se met à jour immédiatement

---

# EPIC 6 — Liste de courses

## SHOP-01 — Ajouter un article
> **En tant que** membre, **je veux** ajouter un article avec nom et quantité, **afin de** préparer mes courses.

### Critères d'acceptation
- [ ] Un formulaire rapide permet de saisir le nom (obligatoire) et la quantité (optionnelle)
- [ ] L'article apparaît immédiatement dans la liste
- [ ] La quantité peut être un nombre ou un texte libre ("1 kg", "une bouteille")
- [ ] L'article est lié au `household_id` du foyer actif

---

## SHOP-02 — Marquer un article comme acheté
> **En tant que** membre, **je veux** marquer un article comme acheté, **afin de** suivre ma progression en magasin.

### Critères d'acceptation
- [ ] Un tap sur un article (ou case à cocher) met `is_purchased` à true
- [ ] Les articles achetés sont visuellement différenciés (barrés, déplacés en bas de liste)
- [ ] L'action est réversible
- [ ] Le statut est visible en temps réel par tous les membres du foyer

---

## SHOP-03 — Supprimer un article
> **En tant que** membre, **je veux** supprimer un article de la liste, **afin de** la nettoyer.

### Critères d'acceptation
- [ ] Un swipe ou bouton permet de supprimer un article
- [ ] Une confirmation est demandée si l'article n'est pas encore acheté
- [ ] Les articles achetés peuvent être supprimés en masse via "Vider les articles achetés"
- [ ] Après suppression → l'article disparaît immédiatement

---

# EPIC 7 — Accueil & Navigation

## HOME-01 — Résumé accueil
> **En tant que** membre, **je veux** voir un résumé sur la page d'accueil, **afin d'** avoir une vue rapide de mon foyer.

### Critères d'acceptation
- [ ] L'accueil affiche les tâches non complétées assignées à l'utilisateur (max 3 affichées)
- [ ] L'accueil affiche les événements du jour et du lendemain
- [ ] L'accueil affiche les repas du jour (petit-déj, déj, dîner)
- [ ] Un tap sur chaque élément redirige via GoRouter vers la section correspondante
- [ ] Si une section est vide → message d'état vide encourageant (ex : "Aucune tâche pour aujourd'hui 🎉")

---

## HOME-02 — Navigation par onglets
> **En tant que** membre, **je veux** naviguer entre les onglets, **afin d'** accéder rapidement aux features.

### Critères d'acceptation
- [ ] 5 onglets sont visibles en barre de navigation bas : Accueil, Tâches, Calendrier, Repas, Courses
- [ ] L'onglet actif est clairement mis en évidence (Material Design 3)
- [ ] La navigation entre onglets est instantanée
- [ ] L'état de chaque onglet est conservé lors des allers-retours (Riverpod)

---

# EPIC 8 — Paramètres & Profil

## PARAM-01 — Modifier son profil
> **En tant que** membre, **je veux** modifier mon profil, **afin de** me représenter dans le foyer.

### Critères d'acceptation
- [ ] L'écran Paramètres donne accès aux champs : prénom, nom, pseudo (`display_name`), avatar (`avatar_url`)
- [ ] L'avatar peut être modifié via la galerie photo du téléphone (upload vers Supabase Storage)
- [ ] Les modifications sont sauvegardées dans la table `profiles`
- [ ] Un snackbar de confirmation s'affiche après sauvegarde
- [ ] Les modifications sont visibles immédiatement dans le foyer (avatars, noms)

---

## PARAM-02 — Changer la langue
> **En tant que** membre, **je veux** changer la langue de l'interface, **afin d'** utiliser l'app dans ma langue.

### Critères d'acceptation
- [ ] Un sélecteur de langue est disponible dans les Paramètres (champ `language` dans `profiles`)
- [ ] Les langues disponibles pour le MVP : Français, Anglais
- [ ] Le changement de langue s'applique immédiatement sans redémarrage de l'app
- [ ] La préférence est sauvegardée en base et restaurée à la reconnexion

---

## PARAM-03 — Gérer ses foyers
> **En tant que** membre, **je veux** gérer mes foyers depuis les Paramètres, **afin d'** avoir le contrôle.

### Critères d'acceptation
- [ ] La liste des foyers de l'utilisateur est affichée dans les Paramètres
- [ ] L'utilisateur peut quitter un foyer (suppression dans `household_members`) avec une confirmation
- [ ] Un admin peut renommer le foyer (champ `name` dans `households`)
- [ ] Si l'utilisateur quitte son dernier foyer → redirection vers l'écran "Créer ou rejoindre un foyer"
- [ ] Un admin ne peut pas quitter un foyer s'il est le seul admin → message d'erreur : "Vous êtes le seul administrateur, désignez un autre admin avant de quitter"

---

# Récap MoSCoW

| Epic | Stories | Must | Should | Could |
|------|---------|------|--------|-------|
| Authentification | 5 | 5 | 0 | 0 |
| Gestion foyer | 5 | 3 | 2 | 0 |
| Tâches | 6 | 6 | 0 | 0 |
| Calendrier | 3 | 3 | 0 | 0 |
| Repas | 2 | 0 | 2 | 0 |
| Courses | 3 | 3 | 0 | 0 |
| Accueil / Nav | 2 | 2 | 0 | 0 |
| Paramètres | 3 | 0 | 2 | 1 |
| **Total** | **29** | **22** | **6** | **1** |
