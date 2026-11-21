# Contribuer

Merci de prendre le temps d'améliorer ce studio. Quelques règles pour que les changements restent faciles à relire.

## Avant de coder

- Ouvre une issue (bug ou idée) avant une PR importante, pour en discuter.
- Lis [`wiki/README.md`](wiki/README.md) : la méthode compte autant que les scripts.

## Installer

```powershell
python -m venv $HOME\.video-env
& $HOME\.video-env\Scripts\python.exe -m pip install -r outils\requirements.txt
node scripts/setup-hooks.mjs
```

La dernière commande active les hooks Git du dépôt (Node.js requis).

## Commits et PR

- Format : `type(scope): #issue description`, par exemple `fix(outils): #12 corrige le fondu des raccords`.
- Types : feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert. Le scope est facultatif.
- Première ligne de 55 caractères maximum, `#12` compris. Le hook `commit-msg` refuse les messages hors format.
- Une PR par sujet, titre au même format, description selon le modèle proposé.

## Tester

Il n'y a pas encore de suite de tests automatique. Teste l'outil modifié sur une vidéo à toi, rangée dans `episodes/` (ignoré par git), et décris dans la PR ce que tu as lancé et vérifié (voir « État des tests » dans [`outils/README.md`](outils/README.md)).

## Ce qui ne doit jamais entrer dans le dépôt

- Médias, rendus, transcriptions complètes (le `.gitignore` les écarte).
- Le contenu de `episodes/`, ton thème (`theme/local.json`) et ton glossaire (`outils/*.local.json`).
- Des chemins propres à ta machine : utilise une variable d'environnement.

## Style d'écriture

Textes en français, phrases courtes, sans emoji, point médian ni tiret cadratin. `node scripts/check-style.mjs` le vérifie (le hook `pre-commit` avertit sans bloquer).

## Licence

En contribuant, tu acceptes que ton code soit publié sous [licence MIT](LICENSE).
