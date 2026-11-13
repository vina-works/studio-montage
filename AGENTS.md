# <nom du projet>

<!-- Décris ici le projet en 2-3 lignes : stack, architecture, commandes. Ce fichier est lu par les agents (Claude Code, Codex, etc.). Les sections ci-dessous viennent de repo-home : ne les modifie pas ici, modifie-les dans repo-home. -->

## Commandes

- `pnpm check` : lint + typecheck + tests, à lancer avant de conclure une tâche (si le projet le définit).

## Git

- **Hooks** (`.githooks/`) : `commit-msg` (format du message) et `pre-push` (lance `pnpm check` s'il existe). Activation : `node scripts/setup-hooks.mjs` (déjà fait par `pnpm install` si le projet appelle ce script dans `prepare`). Ne jamais utiliser `--no-verify` sans que l'utilisateur le demande.
- **Messages de commit** : `type(scope): #numéro_issue description` (Conventional Commits + numéro d'issue obligatoire ; types : feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert ; scope optionnel). **Première ligne de 55 caractères maximum, `#42` compris**, corps libre. Exemple : `feat(admin): #42 ajoute le changement de rôle`. Si le numéro d'issue n'est pas connu, le demander à l'utilisateur plutôt que d'en inventer un. Écrire des sujets courts dès le départ.
- **PR** : titre au même format que les commits, description via le template `.github/PULL_REQUEST_TEMPLATE.md`.

## Conventions

- Les erreurs attendues se retournent, on ne `throw` que pour l'imprévu.
- Toute autorisation est vérifiée côté serveur.
- Pas de secrets dans le dépôt : `.env*` est ignoré, documenter les variables dans `.env.example`.

## Style d'écriture

Règle commune à tous les dépôts Vina Works, pour tout texte publié en français (site, docs, newsletters, README, messages destinés aux utilisateurs) :

- Aucun emoji, aucun point médian (U+00B7), aucun tiret cadratin (U+2014).
- Pas de tics d'écriture de LLM : formules d'introduction creuses, structures « ce n'est pas X, c'est Y » répétées, listes de trois adjectifs, conclusions qui résument ce qui vient d'être dit, enthousiasme de façade.
- Phrases courtes, concrètes, à la voix active. Préférer une virgule, deux-points ou une parenthèse au tiret cadratin.
- Contrôle : `node scripts/check-style.mjs` (le hook `pre-commit` l'exécute et avertit, sans bloquer). `--strict` pour échouer. Ajouter `style-ok` sur une ligne pour tolérer une citation.

## Mise à jour de la base

Ce dépôt est dérivé de `vina-works/repo-home`. Pour récupérer les dernières règles : `node scripts/home-sync.mjs` (ou la commande `/home-sync`), puis relire le diff et committer.
