# Outils

Scripts Python à lancer avec l'environnement `$HOME\.video-env` (faster-whisper, NumPy). Tous lisent et écrivent des fichiers JSON qu'on peut relire et corriger à la main. Aucun n'écrase un rendu existant.

| Script | Rôle | Entrée | Sortie |
|---|---|---|---|
| `transcrire.py` | Transcription au mot (GPU par défaut, `--cpu` sinon) | média | `.transcript.json`, `.md`, `.srt` à côté |
| `hesitations.py` | Seconde passe qui entend les « euh » | média, plan | `hesitations.json` |
| `aligner.py` | Décalage entre deux versions d'un enregistrement | MP3, MP4 | décalages par zone, médiane |
| `rythme.py` | Plan éditorial vers `edit.json` (pauses, hésitations, faux départs) | `plan_rythme.json` | `edit.json`, bilan |
| `rendu.py` | Montage, préécoute ou rendu final, panneaux en option | `edit.json` | MP4 ou M4A |
| `sous_titres.py` | `.srt` de la vidéo montée | `edit.json`, transcription | `.srt` |
| `verifier.py` | Retranscrit le montage et liste les écarts | `edit.json`, transcription, rendu | rapport texte |
| `panneaux.py` | Illustrations mi-écran (Chrome sans interface) | `panneaux.json` | PNG, incrustations de contrôle |
| `qui_parle.py` | Qui parle sur chaque intervalle (indice) | média, références | rapport texte |
| `planche_plans.py` | Plans d'un intervalle et planche pour cadrer | média, intervalles | `plans.json`, planches |
| `shorts.py` | Shorts 9:16 avec sous-titres mot à mot | `shorts.json`, `cadrage.json` | MP4 |
| `revue/serveur.py` | Salle de revue locale : lecture x0,5 à x3, commentaires horodatés | dossier de travail | `revue/commentaires/*.json`, `.md` |
| `commun.py` | Fonctions partagées | | |
| `glossaire.json` | Corrections des noms pour les sous-titres | | |

## Enchaînement type

```powershell
$py = "$HOME\.video-env\Scripts\python.exe"
& $py transcrire.py "D:\ep02\audio.mp3"
& $py aligner.py "D:\ep02\audio.mp3" "D:\ep02\video.mp4"
& $py hesitations.py "D:\ep02\audio.mp3" -o ..\episodes\ep02\hesitations.json --plages ..\episodes\ep02\plan_rythme.json
& $py rythme.py ..\episodes\ep02\plan_rythme.json -o ..\episodes\ep02\edit.json --rapport ..\episodes\ep02\bilan.md
& $py rendu.py ..\episodes\ep02\edit.json -o D:\ep02\tmp\preecoute_v1.mp4 --apercu
& $py verifier.py ..\episodes\ep02\edit.json "D:\ep02\audio.transcript.json"
& $py rendu.py ..\episodes\ep02\edit.json -o D:\ep02\rendus\episode.mp4 --panneaux ..\episodes\ep02\illustrations\panneaux.json
& $py sous_titres.py ..\episodes\ep02\edit.json "D:\ep02\audio.transcript.json" -o D:\ep02\rendus\episode.srt
& $py verifier.py ..\episodes\ep02\edit.json "D:\ep02\audio.transcript.json" --rendu D:\ep02\rendus\episode.mp4
```

## Salle de revue

Page web locale, sur le modèle de Frame.io, pour relire un rendu ou une préécoute et noter les retouches au bon timecode. Aucune dépendance : Python, ffmpeg et ffprobe suffisent. Rien ne quitte la machine.

```powershell
python outils\revue\serveur.py --racine "D:\ep02" --session ep02-montage
```

La page s'ouvre sur http://localhost:8765, ou sur le port libre suivant (jusqu'à +20) si une autre salle l'occupe. Options : `--port` (premier port essayé), `--port-exact` (échouer plutôt que d'en prendre un autre), `--no-browser`. Le port est pris en exclusivité : sous Windows, deux serveurs pouvaient sinon écouter le même. Mode d'emploi complet : [wiki/12](../wiki/12-salle-de-revue.md).

- Bibliothèque : toutes les vidéos et tous les audios du dossier de travail, groupés par dossier, avec miniature, durée et nombre de commentaires ouverts.
- Lecture : vitesses x0,5, x1, x1,5, x2, x3 (touches `1`, `2`, `3`), image par image (`←` `→`), sauts de 5 s (`J` `L`), sous-titres si un `.srt` de même nom est à côté du média.
- Commentaires : `C` commente l'instant courant, `I` et `O` posent une plage, `A` la boucle, `D` dessine sur l'image. Réponses, modification, résolution et filtres dans le panneau de droite. `?` affiche tous les raccourcis.
- Moments forts : `H` (ou l'étoile de la barre) marque l'instant courant sans arrêter la lecture, même en x3, et marque la plage si `I` et `O` sont posés. Onglet « Moments forts » : catégorie (moment fort, idée de short, citation, rire, à couper), note sur 3, titre, bornes recalées sur la tête de lecture (« Début ici », « Fin ici »). Losanges de couleur sur la timeline.
- Enregistrement : automatique à chaque modification. « Enregistrer » (`Ctrl+S`) garde en plus une copie horodatée dans `<racine>/revue/sauvegardes/`.
- Exporter : Markdown dans le presse-papiers (pour Claude), `.md`, `.json` complet réimportable, moments forts en `edit.json` (liste `keep`, base d'un plan de coupe ou de shorts ; un moment ponctuel donne -3 s / +7 s, à ajuster) ou en CSV.
- Importer : un `.json` exporté par la salle. « Fusionner » ajoute ce qui manque, « Remplacer » écrase après une copie dans `revue/sauvegardes/`. Les champs sont vérifiés à l'import.
- Envoyer à Claude : enregistre, puis ajoute une ligne au fichier d'envois de la salle (média, session, compteurs, message facultatif, chemin du `.md`). Une salle par conversation : avec `--session <nom>`, ce fichier est `<racine>/revue/envois/<nom>.jsonl` et seule la conversation qui le surveille (`tail -n 0 -F` lancé avec l'outil Monitor) reçoit l'envoi ; sans `--session`, c'est `<racine>/revue/envois.jsonl`. `GET /api/info` donne la session et le chemin du fichier. Sans surveillance, l'envoi attend dans le fichier : demander à Claude de lire les envois.
- Sortie : `<racine>/revue/commentaires/<chemin_du_media>.json` (commentaires et moments, `type: "moment"` pour ces derniers, `t` et `fin` en secondes) et un `.md` lisible, réécrits à chaque modification.

Les timecodes se rapportent au média commenté. Un commentaire posé sur un rendu se convertit en temps source avec son `edit.json`.

## Format de `edit.json`

```json
{"source": "C:/…/video.mp4", "offset": 0.832, "keep": [
  {"start": 2368.003, "end": 2376.27, "why": "cold open"},
  {"start": 3031.9, "end": 3045.8, "why": "Q5", "sous_titres_jusqu_a": 3035.032}
]}
```

`start` et `end` sont en temps de la **source vidéo**, arrondis à l'image (1/30 s). `offset` est le décalage transcription vers vidéo, utilisé pour les sous-titres et la vérification. `sous_titres_jusqu_a` arrête les sous-titres avant une carte de fin.

## État des tests

Testés sur l'épisode 1 le 2026-11-13 : `rythme.py` redonne 103 segments et 19:09 (le montage validé fait 19:10 ; la seconde passe varie un peu d'une exécution à l'autre), `rendu.py` sort image et son de même durée, `shorts.py` redonne les durées des shorts livrés, `aligner.py` retrouve +0,832 s, `qui_parle.py` retrouve le bon invité sur l'aveu du short 2. `transcrire.py` est celui qui a servi à l'épisode 1, avec le correctif PyAV.
