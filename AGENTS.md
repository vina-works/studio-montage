# studio-montage

Studio de montage par transcript : on monte podcasts, shorts et illustrations en éditant le texte (transcription au mot, `edit.json`, rendu FFmpeg). Pas d'application : un wiki (`wiki/`), des scripts Python (`outils/`), des modèles (`modeles/`) et le dossier de chaque épisode (`episodes/`). Testé sous Windows (PowerShell), avec une carte NVIDIA.

## Avant de monter

- Lire `wiki/README.md`, puis la page de l'étape en cours. Les réglages de rythme validés sont dans `wiki/02-plan-editorial-et-rythme.md` : ne pas revenir aux réglages de la V1, jugés trop hachés.
- Demander quel fichier sera publié (vidéo habillée ou non) avant de faire le plan de coupe, et mesurer le décalage avec `outils/aligner.py` si la transcription vient d'un autre fichier.
- Proposer `edit.json`, un bilan et la liste des raccords à écouter, puis **attendre la validation de l'auteur** avant tout rendu final.
- Vérifier chaque rendu : durée de chaque piste (`ffprobe`), retranscription (`outils/verifier.py`), planche d'images aux moments clés. Dire ce qui n'a pas été écouté.
- Ne jamais écraser une source ni un rendu. Ne jamais committer de média (vidéo, audio, rendus) ni de transcription complète.
- Vérifier qui parle (`outils/qui_parle.py` et plans) avant de bâtir un titre ou un short sur l'identité de quelqu'un.

## Commandes

- Environnement : `$HOME\.video-env\Scripts\python.exe` (faster-whisper 1.2.1, NumPy). Les outils se lancent depuis `outils/`.
- Pas de suite de tests automatique : tester un outil modifié sur un épisode local de `episodes/` (voir `outils/README.md`, « État des tests »).

## Git

- **Hooks** (`.githooks/`) : `commit-msg` (format du message) et `pre-commit` (contrôle de style, sans bloquer). Activation : `node scripts/setup-hooks.mjs`. Ne jamais utiliser `--no-verify` sans que l'utilisateur le demande.
- **Messages de commit** : `type(scope): #numéro_issue description` (Conventional Commits + numéro d'issue obligatoire ; types : feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert ; scope optionnel). **Première ligne de 55 caractères maximum, `#42` compris**, corps libre. Exemple : `feat(outils): #42 ajoute le recadrage auto`. Si le numéro d'issue n'est pas connu, le demander à l'utilisateur plutôt que d'en inventer un. Écrire des sujets courts dès le départ.
- **PR** : titre au même format que les commits, description via le template `.github/PULL_REQUEST_TEMPLATE.md`.

## Conventions

- Ne rien committer de personnel : épisodes (`episodes/*`), thème (`theme/local.json`), glossaire perso (`outils/*.local.json`) restent en local.
- Pas de chemin propre à une machine dans le code : passer par une variable d'environnement (ex. `CHROME`, `THEME`).
- Pas de secrets dans le dépôt : `.env*` est ignoré.

## Style d'écriture

Pour tout texte du dépôt (wiki, README, messages des outils) :

- Aucun emoji, aucun point médian (U+00B7), aucun tiret cadratin (U+2014).
- Pas de tics d'écriture de LLM : formules d'introduction creuses, structures « ce n'est pas X, c'est Y » répétées, listes de trois adjectifs, conclusions qui résument ce qui vient d'être dit, enthousiasme de façade.
- Phrases courtes, concrètes, à la voix active. Préférer une virgule, deux-points ou une parenthèse au tiret cadratin.
- Contrôle : `node scripts/check-style.mjs` (le hook `pre-commit` l'exécute et avertit, sans bloquer). `--strict` pour échouer. Ajouter `style-ok` sur une ligne pour tolérer une citation.
