# 12. Salle de revue

Une page web locale, sur le modèle de Frame.io, pour regarder une préécoute ou un rendu, noter les retouches au bon timecode et marquer les moments forts. Tout reste sur la machine : le serveur ne sert que `localhost`, aucun média ne part en ligne. Code et référence technique : [`outils/revue/`](../outils/README.md#salle-de-revue).

## Pour une nouvelle vidéo

1. **Ranger la vidéo dans un dossier de travail.** La salle liste toutes les vidéos et tous les audios du dossier qu'on lui donne, sous-dossiers compris (`rendus/`, `tmp/`, `shorts/`...). Lui donner le dossier de l'épisode, pas `Téléchargements` ni le disque entier : elle parcourt tout ce qui s'y trouve.
2. **Lancer la salle** depuis n'importe où :

   ```powershell
   python outils\revue\serveur.py --racine "D:\ep02"
   ```

   Le navigateur s'ouvre sur http://localhost:8765. Une seule salle par port : si une autre tourne déjà, le serveur le dit et s'arrête ; pour en ouvrir une deuxième en parallèle, ajouter `--port 8766`. `Ctrl+C` dans le terminal l'arrête.
3. **Choisir la vidéo** dans la colonne de gauche. Si un `.srt` du même nom est à côté, les sous-titres s'affichent (touche `S`).
4. **Regarder vite** : `2` ou `3` pour lire en x2 ou x3, `1` pour revenir. Le son garde sa hauteur.
5. **Marquer et commenter** (voir plus bas).
6. **Envoyer à Claude** avec le bouton violet, en ajoutant ce qu'on attend de lui. Ou lui dire « lis mes commentaires sur `<vidéo>` ».

Les commentaires d'une vidéo se retrouvent quand on la rouvre, ainsi que la position de lecture.

## Deux façons de marquer

| Pour | Touche | Ce que ça fait |
|---|---|---|
| Une retouche | `C` | Met en pause et ouvre la saisie, attachée à l'instant courant |
| Une retouche sur un passage | `I`, `O`, puis `C` | Le commentaire couvre la plage entre les deux points |
| Montrer quelque chose dans l'image | `D` | Dessin à main levée sur l'image, joint au commentaire |
| Un moment fort | `H` | Marque l'instant **sans arrêter la lecture**, même en x3 |
| Un moment fort sur un passage | `I`, `O`, puis `H` | Le moment couvre la plage |

Méthode qui marche : un premier passage en x2 ou x3 en tapant `H` à chaque passage intéressant, sans s'arrêter ; puis l'onglet « Moments forts » pour donner un titre, une catégorie et une note à chacun, et recaler les bornes avec « Début ici » et « Fin ici ».

Catégories des moments : moment fort, idée de short, citation, rire, à couper. La catégorie appliquée par `H` se choisit en bas de l'onglet. Les étoiles (de 1 à 3) servent à trier : « les shorts, ce sont les moments 3 étoiles ».

`?` affiche tous les raccourcis.

## Enregistrer, exporter, importer

- **Enregistrement** : automatique à chaque modification. L'état est affiché en haut. « Enregistrer » (`Ctrl+S`) garde en plus une copie horodatée, utile avant une grosse séance de tri.
- **Exporter** : Markdown dans le presse-papiers (à coller dans une conversation), fichier `.md`, `.json` complet, moments forts en `edit.json` ou en CSV.
- **Importer** : un `.json` exporté par la salle, par exemple les retours d'une autre personne sur la même vidéo. « Fusionner » ajoute ce qui manque, « Remplacer » écrase après une copie de sauvegarde.

## Où sont les fichiers

Dans le dossier de travail, jamais dans ce dépôt :

```
<dossier de travail>/
  revue/
    commentaires/   un .json et un .md par vidéo commentée
    sauvegardes/    copies horodatées (Enregistrer, Remplacer)
    envois.jsonl    une ligne par clic sur « Envoyer à Claude »
  tmp/revue_cache/  miniatures et durées, régénérables
```

## Envoyer à Claude

Le bouton enregistre, puis écrit une ligne dans `revue/envois.jsonl` : la vidéo, le message tapé, le chemin du `.md`. Une session Claude qui surveille ce fichier reçoit l'envoi dans la seconde ; Claude sait le faire (consigne dans le `CLAUDE.md` du dossier de travail). Si aucune session ne surveille, l'envoi attend dans le fichier : dire à Claude « lis mes envois ».

Claude garde les règles habituelles : il propose un `edit.json` et attend la validation avant tout rendu final.

## Les timecodes

Un timecode se rapporte **à la vidéo commentée**. Sur une préécoute ou un rendu, ce sont des timecodes de sortie : Claude les reconvertit en temps source avec l'`edit.json` qui a produit cette vidéo (voir [01](01-deroule-d-un-episode.md#versions)). Le dire en envoyant si la vidéo commentée n'est pas évidente (« retours sur preecoute_v3 »).

L'export « Moments forts en edit.json » garde ces timecodes tels quels. Un moment ponctuel y devient une fenêtre de 3 s avant à 7 s après, à recaler sur la transcription avant de rendre quoi que ce soit.

## Limites

- Lecture arrière impossible (le navigateur ne la gère pas) : `J` recule de 5 s, `←` d'une image.
- Une seule personne à la fois : deux onglets ouverts sur la même vidéo s'écrasent l'un l'autre.
- Formats lus : ceux du navigateur (MP4 H.264, M4A, MP3, WAV, WebM). Un `.mov` en ProRes ne se lit pas ; faire une préécoute H.264 avec `rendu.py --apercu`.
