# repo-home

Base commune des dépôts Vina Works : la config qu'on ne veut pas réécrire à chaque nouveau projet. Ce dépôt est un **template GitHub** (« Template repository »), sans aucun code applicatif.

## Contenu

| Fichier | Rôle | Mise à jour |
|---|---|---|
| `.githooks/commit-msg` + `scripts/check-commit-msg.mjs` | Format `type(scope): #issue description`, 55 caractères max | gérée |
| `.githooks/pre-push` | lance `pnpm check` s'il existe | gérée |
| `scripts/check-style.mjs` + `.githooks/pre-commit` | avertit sur emoji, point médian, tiret cadratin dans les fichiers de contenu (`--strict` pour bloquer) | gérée |
| `scripts/setup-hooks.mjs` | active `core.hooksPath` | gérée |
| `scripts/home-sync.mjs` | récupère les mises à jour de repo-home | gérée |
| `.claude/commands/` | `/commit`, `/home-sync` | gérée |
| `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/` | templates PR et issues | gérée |
| `.editorconfig` | style d'édition | gérée |
| `AGENTS.md` (+ `CLAUDE.md` qui l'importe) | consignes pour les agents | **copiée une fois**, ensuite à vous |
| `.claude/settings.json`, `.gitignore` | réglages de départ | **copiés une fois**, ensuite à vous |

« Gérée » = écrasée à chaque synchronisation (listes dans `.home/managed.txt` et `.home/seed.txt`). Pas de lint/format ni de CI ici : ils dépendent de la stack, ils restent dans les starters.

## Démarrer un nouveau dépôt

```bash
gh repo create vina-works/mon-projet --private --template vina-works/repo-home --clone
cd mon-projet
node scripts/setup-hooks.mjs   # active les hooks (inutile si `pnpm install` l'appelle via "prepare")
```

Puis : renseigner `AGENTS.md` (nom, stack, commandes) et, si le projet utilise pnpm, ajouter `"prepare": "node scripts/setup-hooks.mjs"` et un script `check` dans `package.json`.

## Mettre à jour un dépôt existant

Depuis la racine du dépôt dérivé (nécessite `gh auth login`) :

```bash
node scripts/home-sync.mjs --dry-run   # voir ce qui changerait
node scripts/home-sync.mjs             # appliquer
git diff                               # relire, puis committer
```

Dans Claude Code : `/home-sync`. Pour un dépôt qui n'a pas encore le script, une seule fois :

```bash
gh api repos/vina-works/repo-home/contents/scripts/home-sync.mjs -H "Accept: application/vnd.github.raw" > /tmp/home-sync.mjs
mkdir -p scripts && cp /tmp/home-sync.mjs scripts/ && node scripts/home-sync.mjs
```

Le commit de repo-home appliqué est noté dans `.home/version`. Le script ne committe jamais, et ne touche ni à `AGENTS.md` ni à `.gitignore` s'ils existent.

## Faire évoluer la base

Modifier ici (jamais dans un dépôt dérivé : ce serait écrasé), committer au format habituel, puis lancer `/home-sync` dans les dépôts concernés. Pour qu'un nouveau fichier soit propagé, l'ajouter à `.home/managed.txt` (ou `.home/seed.txt`).
