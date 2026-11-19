# 11. Travailler avec Claude

## Le brief qui marche

Le brief du chef monteur ([`modeles/brief_chef_monteur.md`](../modeles/brief_chef_monteur.md)) donne le rôle, ce qui est figé (le plan éditorial), ce qui est attendu avant tout rendu (`edit.json`, bilan, raccords à écouter) et une consigne d'attente. Remplir les champs entre crochets (ton, énergie, fichier source) : vides, Claude choisit des valeurs par défaut et le dit.

Donner tout de suite :

- le fichier qui sera publié (MP4 habillé ou non) ;
- la DA ;
- le nom du podcast ;
- si les sous-titres doivent être incrustés.

## Les retours qui marchent

Des timestamps de sortie et une intention, en une ligne chacun : « sur la présentation du deuxième invité, plus de naturel », « 14:50 : il manque la fin de sa phrase », « le nom du quiz on s'en fout ». Claude corrige `edit.json`, refait une préécoute, et la vérifie par retranscription.

Le plus simple est de les poser dans la [salle de revue](12-salle-de-revue.md) : chaque commentaire est attaché au bon timecode, et le bouton « Envoyer à Claude » lui transmet tout, avec une consigne (« corrige ces points », « propose des shorts avec les moments 3 étoiles »).

## Ce que Claude vérifie seul

- Durées et synchro image/son (`ffprobe` par piste).
- Mots mangés ou en trop aux raccords (retranscription).
- Images aux moments clés (planches).
- Qui parle (comparaison de voix, à confirmer).

## Ce qu'il faut écouter soi-même

- La musicalité des raccords : Claude ne les entend pas.
- Les rires et les silences gardés.
- Les sous-titres, à relire en entier.

## Où sont les choses

- Ce wiki et les outils : ce dépôt.
- Le dossier de travail d'un épisode : à côté des médias, hors dépôt. Seuls les plans, specs et le journal de l'épisode entrent dans `episodes/`.
