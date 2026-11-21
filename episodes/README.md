# Épisodes

Un dossier par épisode, **gardé en local** : `.gitignore` exclut tout le contenu de `episodes/` sauf ce fichier, pour qu'aucun épisode ne parte dans le dépôt public. On y met ce qui permet de refaire ou de reprendre le montage, jamais les médias (vidéo, audio, rendus) ni les transcriptions complètes, qui restent à côté des fichiers source.

```
epNN/
  README.md            journal : fichiers source, décisions, versions, points ouverts
  sources/             documents de départ (plan éditorial, brief des shorts)
  plan_rythme.json     entrée de outils/rythme.py
  hesitations.json     seconde passe (régénérable)
  edit.json            plan de coupe validé
  illustrations/       panneaux.json (+ PNG régénérables)
  shorts/              shorts.json, cadrage.json, legendes.md
```
