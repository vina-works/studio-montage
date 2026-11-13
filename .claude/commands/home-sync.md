---
description: Met à jour la config de base (hooks, scripts, templates, commandes) depuis vina-works/repo-home
allowed-tools: Bash(node scripts/home-sync.mjs:*), Bash(git status:*), Bash(git diff:*)
---

1. Lance `node scripts/home-sync.mjs --dry-run` et résume ce qui va changer.
2. Si tout est cohérent, lance `node scripts/home-sync.mjs`, relis `git diff`, signale tout conflit avec des réglages locaux.
3. Ne commit pas : laisse l'utilisateur valider (ou utilise `/commit` s'il le demande, par ex. `chore: #<issue> synchronise repo-home`).
