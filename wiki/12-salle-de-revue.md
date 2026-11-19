# 12. Salle de revue

Une page web locale, sur le modèle de Frame.io, pour regarder une préécoute ou un rendu, noter les retouches au bon timecode et marquer les moments forts. Tout reste sur la machine : le serveur ne sert que `localhost`, aucun média ne part en ligne. Code et référence technique : [`outils/revue/`](../outils/README.md#salle-de-revue).

## Pour une nouvelle vidéo

1. **Ranger la vidéo dans un dossier de travail.** La salle liste toutes les vidéos et tous les audios du dossier qu'on lui donne, sous-dossiers compris (`rendus/`, `tmp/`, `shorts/`...). Lui donner le dossier de l'épisode, pas `Téléchargements` ni le disque entier : elle parcourt tout ce qui s'y trouve.
2. **Ouvrir la salle.** Le plus simple : dans la conversation Claude qui travaille sur cette vidéo, dire « ouvre la salle de revue sur `D:\ep02` ». Claude la lance pour cette conversation (voir [Une salle par conversation](#une-salle-par-conversation)) et donne l'adresse. À la main :

   ```powershell
   python outils\revue\serveur.py --racine "D:\ep02" --session ep02-montage
   ```

   Le navigateur s'ouvre sur http://localhost:8765, ou sur le port libre suivant si une autre salle l'occupe déjà (le terminal affiche l'adresse). `Ctrl+C` dans le terminal l'arrête.
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
    envois/         un fichier par conversation : une ligne par clic sur « Envoyer à Claude »
  tmp/revue_cache/  miniatures et durées, régénérables
```

## Envoyer à Claude

Le bouton enregistre, puis écrit une ligne dans le fichier d'envois de la salle : la vidéo, le message tapé, le chemin du `.md`. La conversation Claude qui surveille ce fichier reçoit l'envoi dans la seconde ; Claude sait le faire (consigne dans le `CLAUDE.md` du dossier de travail). Si elle ne surveille pas (conversation fermée, surveillance expirée), l'envoi attend dans le fichier : dire à Claude « lis mes envois ».

## Montage : retoucher la timeline à la main

Le bouton « Montage » (touche `T`) ouvre une timeline éditable du dernier plan de coupe (`edit*.json` à la racine du dossier de travail, le plus récent d'abord). Elle montre les plans (une couleur par prise), les cartes et captures, les bandeaux, et rejoue le montage directement depuis les prises d'origine, sans rien regénérer : cartes qui glissent, captures avec l'encadré de l'orateur, sous-titres recalculés (mêmes corrections que le rendu, bouton « Sous-titres »), fondu de 20 ms aux raccords. On ne rend qu'à la fin, une fois validé.

| Geste | Effet |
|---|---|
| Clic sur un plan | Le sélectionner et s'y placer |
| Tirer le bord gauche ou droit d'un plan | Le raccourcir ou le rallonger ; les plans suivants se recollent seuls. L'aimant cale le bord sur les mots |
| `S` puis `Suppr` | Couper le plan à la tête de lecture, puis supprimer la partie en trop |
| Glisser une carte | La déplacer ; elle reste attachée au plan sous elle. Tirer son bord droit : la rallonger |
| `Ctrl`+`Z` / `Ctrl`+`Maj`+`Z` | Annuler / rétablir |
| `+` / `-`, `Espace`, `←` `→` | Zoom, lecture, image par image (`Maj` : 1 s) |

Une piste « Repères » montre les commentaires et moments forts posés dans la revue, sur les rendus comme sur les prises, ramenés à leur place dans le montage (un plan de coupe liste ses rendus dans `rendus`). Ceux qui tombent sur un passage coupé sont grisés et posés au raccord. `M` pose un repère à la main ; l'onglet « Repères » les liste tous.

Les retouches s'enregistrent toutes seules, 0,6 s après chaque geste, dans `revue/montage/<plan>.manuel.json` ; `Ctrl`+`S` enregistre en plus une copie horodatée dans `revue/sauvegardes/`. Le plan d'origine n'est jamais modifié. « Plan d'origine » revient en arrière. « Envoyer à Claude » enregistre puis prévient la conversation, qui rend la nouvelle version à partir de ce fichier (nouveau nom de rendu, sans écraser les précédents).

Les cartes viennent de `<plan>.overlays.json` à côté du plan (id, type, temps source, durée, image) ; sans lui, seule la coupe est éditable.

## Une salle par conversation

Chaque conversation Claude a sa propre salle, lancée avec `--session <nom>`. Ses envois vont dans `revue/envois/<nom>.jsonl`, et seule cette conversation les reçoit. Deux conversations peuvent ainsi travailler en même temps, sur le même dossier ou non, sans recevoir les retours de l'autre.

- Le nom de la conversation s'affiche à côté du logo, dans l'onglet du navigateur et dans la fenêtre d'envoi : vérifier qu'on est dans la bonne salle avant d'envoyer.
- Chaque salle prend son port (8765, puis 8766...). Garder un onglet par salle.
- Sans `--session`, les envois vont dans `revue/envois.jsonl`, que n'importe quelle conversation peut lire.
- Les commentaires, eux, restent communs : ils appartiennent à la vidéo, pas à la conversation. Deux salles ouvertes sur la même vidéo s'écrasent l'une l'autre ; en commenter une seule à la fois.

Claude garde les règles habituelles : il propose un `edit.json` et attend la validation avant tout rendu final.

## Les timecodes

Un timecode se rapporte **à la vidéo commentée**. Sur une préécoute ou un rendu, ce sont des timecodes de sortie : Claude les reconvertit en temps source avec l'`edit.json` qui a produit cette vidéo (voir [01](01-deroule-d-un-episode.md#versions)). Le dire en envoyant si la vidéo commentée n'est pas évidente (« retours sur preecoute_v3 »).

L'export « Moments forts en edit.json » garde ces timecodes tels quels. Un moment ponctuel y devient une fenêtre de 3 s avant à 7 s après, à recaler sur la transcription avant de rendre quoi que ce soit.

## Limites

- Lecture arrière impossible (le navigateur ne la gère pas) : `J` recule de 5 s, `←` d'une image.
- Une seule personne à la fois par vidéo : deux onglets ou deux salles ouverts sur la même vidéo s'écrasent l'un l'autre.
- Formats lus : ceux du navigateur (MP4 H.264, M4A, MP3, WAV, WebM). Un `.mov` en ProRes ne se lit pas ; faire une préécoute H.264 avec `rendu.py --apercu`.
