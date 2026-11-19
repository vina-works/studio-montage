# 01. Déroulé d'un épisode

Chaque étape produit un fichier qu'on peut relire. Rien n'est rendu en version finale sans validation de l'auteur.

| # | Étape | Entrée | Sortie | Outil |
|---|---|---|---|---|
| 1 | Transcrire | MP3 ou MP4 | `.transcript.json` (mots horodatés), `.transcript.md`, `.srt` | `outils/transcrire.py` |
| 2 | Plan éditorial | transcription | `plan_editorial.md` : ce qu'on garde, l'ordre, le cold open, les coupes | l'auteur, ou Claude puis validation |
| 3 | Rythme | plan éditorial | `edit.json` : segments à garder, pauses resserrées, hésitations coupées | `outils/rythme.py` |
| 4 | Préécoute | `edit.json` | audio puis vidéo 720p dans `tmp/` | `outils/rendu.py --apercu` |
| 5 | Retours | préécoute | corrections de `edit.json` | l'auteur commente dans la [salle de revue](12-salle-de-revue.md) (timestamps de sortie) |
| 6 | Illustrations | moments à vulgariser | panneaux PNG 960x1080 | `outils/panneaux.py` |
| 7 | Rendu final | `edit.json` validé | MP4 1080p dans `rendus/`, `.srt` à côté | `outils/rendu.py` |
| 8 | Vérification | rendu | durée, synchro, mots mangés, liste des raccords à écouter | `outils/verifier.py` |
| 9 | Shorts | brief shorts, moments forts marqués dans la salle de revue | MP4 9:16 et légendes | `outils/shorts.py` |

## Ce qui a pris du temps sur l'épisode 1

- **La source n'était pas la bonne.** Le plan avait été fait sur le MP3 (52:12) alors que la vidéo à monter était un MP4 déjà habillé (50:46), décalé de 0,832 s et sans le teaser du MP3. Voir [04](04-source-video-synchro-rendu.md). Demander dès le départ quel fichier sera publié.
- **Le premier montage était trop haché.** Les réglages de pauses de la V1 ont été rejetés à l'écoute. Les réglages de la V2 sont dans [02](02-plan-editorial-et-rythme.md).
- **Les fins de phrases coupées.** Une coupe calée sur un timestamp du plan tombait au milieu d'une phrase (« on essaie de remonter la boucle jusqu'au moment »). Toujours couper sur une fin de phrase, même si le plan dit autre chose.

## Versions

On numérote les préécoutes (`preecoute_v2.mp4`, `v3`) et on garde la précédente. L'auteur commente en timestamps **de sortie** : « 04:38 coupe le Ok », « 14:26 remets le rire ». Le script de rythme doit pouvoir convertir un timestamp de sortie en timestamp source, et inversement.

## Arborescence de travail

```
<dossier de travail>/
  edit.json          plan de coupe courant (le précédent part dans tmp/edit_vN.json)
  rendus/            sorties finales, jamais écrasées
  tmp/               préécoutes, fichiers intermédiaires
  illustrations/     panneaux HTML et PNG
  shorts/            specs et cadrages des shorts
  revue/             commentaires et moments forts de la salle de revue
```

La source n'est jamais modifiée ni écrasée.
