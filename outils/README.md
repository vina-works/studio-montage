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
