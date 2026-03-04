# 02 — Initialisation du repository GitHub

> **Playbook — famille-new-app**  
> Niveau : équipe technique | Durée estimée : 15–20 min

---

## 1. Objectif

Créer et initialiser un repository GitHub pour un nouveau projet, mettre en place la structure de dossiers standard, et effectuer le premier push. Cette procédure est reproductible pour tout nouveau projet client.

---

## 2. Pré-requis

| Élément | Détail |
|---|---|
| Compte GitHub | Droits de création de repository dans l'organisation cible |
| Git | Version ≥ 2.35 (`git --version`) |
| Authentification GitHub | SSH configuré **ou** token HTTPS (PAT) |
| Terminal | Bash, Zsh ou équivalent |
| Dossier parent | Le répertoire parent du projet existe localement (ex. `bramsmala/`) |

Vérification rapide :

```bash
git --version
gh auth status          # si GitHub CLI installé
ssh -T git@github.com   # si SSH configuré
```

---

## 3. Étapes de création du repository GitHub

### 3.1 Via l'interface web GitHub

1. Se connecter sur [github.com](https://github.com)
2. Cliquer sur **New repository** (bouton `+` en haut à droite)
3. Renseigner les champs :
   - **Repository name** : `famille-new-app` *(kebab-case, sans espaces)*
   - **Description** : courte description du projet
   - **Visibility** : `Private` (recommandé pour un projet client)
   - ❌ Ne pas cocher *"Add a README file"* — on le crée localement
   - ❌ Ne pas ajouter `.gitignore` ni licence depuis GitHub
4. Cliquer **Create repository**
5. Copier l'URL SSH affichée : `git@github.com:<org>/famille-new-app.git`

### 3.2 Via GitHub CLI *(optionnel, plus rapide)*

```bash
gh repo create famille-new-app --private --description "Description du projet"
```

---

## 4. Étapes terminal

### 4.1 Se placer dans le dossier parent et créer le projet

```bash
cd ~/bramsmala          # adapter au chemin réel
mkdir famille-new-app
cd famille-new-app
```

### 4.2 Créer la structure de dossiers

```bash
mkdir -p docs/{product,backlog,architecture,sprints,decisions} \
         ai/{roles,prompts,workflows} \
         scripts src tests playbook

# .gitkeep pour que git tracke les dossiers vides
find . -type d -empty -exec touch {}/.gitkeep \;
```

### 4.3 Créer les fichiers racine

```bash
touch README.md .gitignore
```

Remplir `.gitignore` (Python + Node) :

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
.venv/
venv/
env/
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
.coverage
htmlcov/

# Node
node_modules/
.next/
dist/
npm-debug.log*
yarn-error.log*

# Env & secrets
.env
.env.local
.env.*.local
*.secret

# IDEs & OS
.vscode/
.idea/
.DS_Store
Thumbs.db
EOF
```

### 4.4 Initialiser Git et effectuer le premier commit

```bash
git init
git add .
git commit -m "chore: init project structure"
```

### 4.5 Lier le remote GitHub et pousser

```bash
# Remplacer <org> par le nom de l'organisation ou du compte
git remote add origin git@github.com:<org>/famille-new-app.git

git branch -M main
git push -u origin main
```

---

## 5. Structure finale du repository

```
famille-new-app/
├── .gitignore
├── README.md
├── ai/
│   ├── prompts/
│   ├── roles/
│   └── workflows/
├── docs/
│   ├── architecture/
│   ├── backlog/
│   ├── decisions/
│   ├── product/
│   └── sprints/
├── playbook/
├── scripts/
├── src/
└── tests/
```

Chaque dossier vide contient un fichier `.gitkeep` pour être tracké par Git.

---

## 6. Vérification de l'installation

```bash
# 1. L'arborescence est correcte
find . -not -path './.git/*' | sort

# 2. Git est bien initialisé sur main
git status
git log --oneline

# 3. Le remote est correctement configuré
git remote -v

# 4. Le repository est visible sur GitHub
# → Ouvrir https://github.com/<org>/famille-new-app
# → Vérifier que les dossiers et fichiers apparaissent
```

Résultat attendu pour `git remote -v` :

```
origin  git@github.com:<org>/famille-new-app.git (fetch)
origin  git@github.com:<org>/famille-new-app.git (push)
```

---

## 7. Erreurs fréquentes et résolution

### `Permission denied (publickey)`

**Cause** : clé SSH non configurée ou non enregistrée sur GitHub.

```bash
# Vérifier les clés locales
ls ~/.ssh/

# Générer une nouvelle clé si absente
ssh-keygen -t ed25519 -C "votre@email.com"

# Ajouter la clé publique dans GitHub > Settings > SSH Keys
cat ~/.ssh/id_ed25519.pub
```

---

### `error: remote origin already exists`

**Cause** : un remote `origin` a déjà été ajouté.

```bash
git remote remove origin
git remote add origin git@github.com:<org>/famille-new-app.git
```

---

### `refusing to merge unrelated histories`

**Cause** : le repository GitHub a été initialisé avec un README (ne pas le faire).

```bash
git pull origin main --allow-unrelated-histories
# Résoudre le conflit, puis
git push -u origin main
```

---

### `src refspec main does not match any`

**Cause** : aucun commit n'a encore été créé.

```bash
git add .
git commit -m "chore: init project structure"
git push -u origin main
```

---

### Les dossiers vides n'apparaissent pas sur GitHub

**Cause** : Git ne tracke pas les dossiers vides.

```bash
find . -type d -empty -not -path './.git/*' -exec touch {}/.gitkeep \;
git add .
git commit -m "chore: add .gitkeep to empty dirs"
git push
```

---

*Document maintenu dans `playbook/` — mettre à jour lors de tout changement de convention.*
