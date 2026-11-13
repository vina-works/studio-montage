# 04. Source vidéo, synchro et rendu

## Identifier la vraie source avant tout

Sur l'épisode 1, il y avait deux fichiers :

| | MP3 « Copie de… » | MP4 « version longue » |
|---|---|---|
| Durée | 52:12 | 50:46 |
| Début | un teaser monté différemment | teaser avec sous-titres incrustés |
| Synchro | référence de la transcription | **MP3 + 0,832 s** pour toute la parole (+0,917 s dans le générique) |
| Fin | continue 1 minute après les remerciements | s'arrête sur le rire, puis carte « MERCI ! » et logo |
| Habillage | aucun | bandeau avec le nom du podcast, noms des invités, questions, carte de fin, tous incrustés |

Conséquences :

- Le plan de coupe se fait sur la transcription du MP3, puis se convertit en temps MP4 en ajoutant le décalage mesuré. `outils/aligner.py` le mesure par corrélation, fenêtre par fenêtre, et signale les zones où les deux fichiers divergent.
- Ce qui n'existe que dans le MP3 (la bascule « maintenant que l'échauffement est fait ») n'a pas d'image : on ne peut pas le garder.
- **L'habillage incrusté se coupe avec l'image.** Un bandeau de nom peut apparaître coupé à gauche sous un panneau, et le nom du podcast affiché ne se change pas depuis le MP4. Pour changer de nom, il faut repartir du projet de montage d'origine.

## Couper à l'image près, garder le son au sample près

Le pipeline qui donne une synchro parfaite (vérifiée par corrélation avec la préécoute : 1,0) :

1. **Image** : un fichier par segment, `ffmpeg -ss <début> -i source -frames:v <n>`. Le nombre d'images vient d'un **arrondi cumulé** (`round(cumul * 30) - déjà_faites`) pour que les erreurs d'arrondi ne s'additionnent pas. Intermédiaires en `libx264 -preset ultrafast -crf 10` (presque sans perte).
2. **Son** : on décode toute la source une fois en float 48 kHz (NumPy), on découpe les segments au sample près, on applique un fondu de 20 ms à chaque bord, on concatène.
3. **Assemblage** : demuxer `concat` pour l'image, son brut en entrée, encodage final `libx264 -preset veryfast -crf 20`, AAC 192k, `-movflags +faststart`.

Préécoute : même chose en 720p avec `h264_nvenc` (19 minutes rendues en 2 à 3 minutes).

## Pièges FFmpeg rencontrés

- **`-shortest` avec une image en boucle** (`-loop 1`) laisse la vidéo déborder d'environ 1,6 s après la fin du son : image figée et muette. Donner la durée exacte avec `-t`.
- **Une coupe peut tomber dans une zone sans plan connu** (ici une partie retirée du premier montage). Le script doit boucher les trous entre plans plutôt que d'échouer ou de livrer un fichier plus court.
- **Un script qui échoue au milieu d'une chaîne PowerShell** n'empêche pas la commande suivante (zip) de tourner avec les anciens fichiers. Tester `$LASTEXITCODE` avant d'emballer.
- **Chemins Windows** : guillemets partout (espaces), `/` dans les listes `concat`, le filtre `ass=` lancé depuis le dossier du fichier (`cwd`) pour éviter d'échapper `C:`.

## Vérifier un rendu

- `ffprobe` : durée du conteneur, **et durée de chaque piste**. C'est l'écart image/son qui a révélé le défaut de `-shortest`.
- Corrélation audio avec la préécoute validée.
- Pic audio de la source contre celui du rendu (le montage ne doit pas ajouter de saturation).
- Une planche d'images aux moments clés (panneaux, cartes, raccords).
