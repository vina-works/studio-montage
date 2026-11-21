# Contribuer

Merci de prendre le temps d'améliorer ce studio. Ce guide explique comment proposer un changement pour qu'il soit facile à relire et à fusionner.

## Ce qui est utile

- **Signaler un bug** : ce que tu as lancé, ce que tu attendais, ce qui s'est passé.
- **Améliorer un outil** existant ou en proposer un nouveau.
- **Documenter** : une étape du wiki pas claire, un piège que tu as rencontré, un réglage qui marche mieux.
- **Porter** les outils sur macOS ou Linux (aujourd'hui seul Windows est testé).

Pour un changement important (nouvel outil, changement du format de `edit.json`), ouvre d'abord une issue pour en discuter. Ça évite de coder quelque chose qui ne sera pas fusionné.

## Signaler un bug

Ouvre une issue avec le modèle « Bug » et indique :

- la commande exacte et le message d'erreur complet ;
- ton système, ta version de Python (`python --version`) et de FFmpeg (`ffmpeg -version`, première ligne) ;
- si tu as une carte NVIDIA, et si le problème disparaît avec `--cpu` ;
- un extrait de `edit.json` ou du JSON en cause, si c'est lié.

Ne joins jamais une vidéo, une transcription complète ou des données d'autres personnes. Un extrait de quelques secondes ou de quelques mots suffit en général.

## Installer l'environnement

```powershell
git clone https://github.com/vina-works/studio-montage.git
cd studio-montage
python -m venv $HOME\.video-env
& $HOME\.video-env\Scripts\python.exe -m pip install -r outils\requirements.txt
node scripts/setup-hooks.mjs
```

La dernière commande active les hooks Git du dépôt (Node.js requis) : format des messages de commit, contrôle de style.

## Proposer un changement

1. **Fork** le dépôt (ou crée une branche si tu as les droits d'écriture). `main` est protégée : tout passe par une PR.
2. **Crée une branche** depuis `main`, nommée `type/sujet-court` : `feat/recadrage-auto`, `fix/fondu-raccords`, `docs/wiki-shorts`.
3. **Fais des commits** au format ci-dessous.
4. **Ouvre une PR** vers `main` en remplissant le modèle : ce qui change, pourquoi, comment tu l'as testé.
5. **Relecture** : un mainteneur relit, pose des questions ou demande des retouches. Pousse les corrections sur la même branche.
6. **Fusion** en squash : la PR devient un seul commit sur `main`, avec le titre de la PR.

### Format des commits et des titres de PR

```
type(scope): #issue description
```

- Types : `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Le scope est facultatif : `outils`, `revue`, `wiki`, `theme`...
- Le numéro d'issue est obligatoire. Pas d'issue pour ton changement ? Crée-la d'abord, même courte.
- Première ligne de 55 caractères maximum, `#12` compris. Le corps du message est libre.
- Exemple : `fix(outils): #12 corrige le fondu des raccords`.

Le hook `commit-msg` refuse les messages hors format. Ne le contourne pas avec `--no-verify`.

## Écrire ou modifier un outil

Les outils de `outils/` suivent quelques règles communes :

- **Une docstring en tête** avec la ligne `Usage :` et les options. C'est la documentation de référence de l'outil.
- **Entrées et sorties en JSON lisible**, qu'on peut relire et corriger à la main.
- **Ne jamais écraser** une source ni un rendu existant : refuser, ou choisir un autre nom.
- **Pas de chemin propre à une machine** : passer par un argument ou une variable d'environnement (`CHROME`, `THEME`).
- **Réutiliser `commun.py`** (temps, décodage audio, glossaire, thème, appel à FFmpeg) plutôt que de dupliquer.
- **Messages et noms en français**, comme le reste du dépôt.
- Ajouter l'outil au tableau de [`outils/README.md`](outils/README.md), et au wiki s'il change la méthode.

## Tester

Il n'y a pas encore de suite de tests automatique. Avant d'ouvrir la PR :

- lance l'outil modifié sur une vidéo à toi, rangée dans `episodes/` (ignoré par git) ;
- pour un rendu, contrôle la durée des pistes (`ffprobe`) et lance `verifier.py` ;
- pour un visuel (panneau, short), regarde l'image produite ;
- décris dans la PR ce que tu as lancé, ce que tu as vérifié, et ce que tu n'as pas pu tester.

Une PR qui ajoute de vrais tests automatiques est bienvenue.

## Ce qui ne doit jamais entrer dans le dépôt

- Médias, rendus, transcriptions complètes (le `.gitignore` les écarte, vérifie quand même `git status`).
- Le contenu de `episodes/`, ton thème (`theme/local.json`) et ton glossaire (`outils/*.local.json`).
- Des noms, voix ou images de personnes qui n'ont pas donné leur accord.
- Des secrets (clés, jetons).

## Style d'écriture

Textes en français, phrases courtes et concrètes, sans emoji, point médian ni tiret cadratin. `node scripts/check-style.mjs` le vérifie ; le hook `pre-commit` avertit sans bloquer.

## Code de conduite

Les échanges sur ce dépôt suivent le [code de conduite](CODE_OF_CONDUCT.md).

## Licence

En contribuant, tu acceptes que ta contribution soit publiée sous [licence MIT](LICENSE).
