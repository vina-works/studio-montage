---
description: Commit les changements avec un message conforme (type(scope): #issue description, 55 car. max)
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*), Bash(git log:*)
---

Regarde `git status` et `git diff`, puis crée un commit.

Règles (vérifiées par le hook `commit-msg`) :
- Format `type(scope): #numéro_issue description`, types : feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert.
- Première ligne de 55 caractères maximum, `#42` compris.
- Si le numéro d'issue n'est pas dans $ARGUMENTS ni dans le nom de la branche, demande-le : n'en invente pas.
- Ne contourne jamais le hook avec `--no-verify`.
