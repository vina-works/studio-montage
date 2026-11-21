# studio-montage

Un studio de montage par transcript. On monte des podcasts et des vidéos face caméra en éditant le texte, pas la timeline : transcription au mot, plan de coupe en JSON, rendu FFmpeg, vérification par retranscription. Le même matériau sert ensuite aux shorts verticaux et aux illustrations.

Ce dépôt contient quatre choses :

- [`wiki/`](wiki/README.md) : la méthode, les réglages qui marchent, les pièges déjà rencontrés et les retours d'écoute. C'est le point d'entrée.
- [`outils/`](outils/README.md) : les scripts Python, réutilisables d'un épisode à l'autre, dont la [salle de revue](wiki/12-salle-de-revue.md) pour commenter les préécoutes et marquer les moments forts.
- [`modeles/`](modeles/) : plan éditorial, brief du chef monteur, brief des shorts.
- [`episodes/`](episodes/README.md) : le dossier de chaque épisode (plans, `edit.json`, specs des shorts et des panneaux, journal des décisions). Il reste en local : git ignore tout son contenu.

Les couleurs, polices et signatures des visuels viennent d'un [thème](theme/README.md). Le dépôt fournit un thème neutre ; ta charte à toi va dans `theme/local.json`, ignoré par git. De même, tes corrections de transcription personnelles (noms des intervenants, marques) vont dans `outils/glossaire.local.json`.

## Démarrer

Prérequis : Windows, FFmpeg et FFprobe dans le `PATH`, Python 3.12, Google Chrome ou Chromium (pour rendre les panneaux ; chemin trouvé tout seul, ou via la variable `CHROME`), une carte NVIDIA pour aller vite (sinon le processeur prend le relais).

```powershell
python -m venv $HOME\.video-env
& $HOME\.video-env\Scripts\python.exe -m pip install -r outils\requirements.txt
node scripts/setup-hooks.mjs
```

Puis suivre [le déroulé d'un épisode](wiki/01-deroule-d-un-episode.md).

## Contribuer

Les issues et les PR sont les bienvenues. Le format des commits et la façon de tester un outil sont décrits dans [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

[MIT](LICENSE).
