# 07. Shorts

Objectif : donner envie de voir l'épisode complet. Règle de base : **on ne réécrit aucune parole**, on coupe et on déplace seulement. Les textes à l'écran sont de l'habillage.

## Format

- Vertical 1080x1920, visage de la personne qui parle cadré serré.
- Première phrase prononcée = accroche. Pas de générique ni de logo au début.
- Texte d'accroche en haut pendant 3 s (encadré couleur `fond`, filet couleur `accent`, police de titre du thème en 58 px, à 130 px du haut).
- Sous-titres mot à mot incrustés ([06](06-sous-titres.md)).
- **Pas d'écran de fin muet.** La V1 finissait sur 2 s d'écran fixe et silencieux, ce qui fait décrocher et casse la relecture en boucle. En V2, un bandeau « Épisode complet », avec le nom du podcast et le numéro d'épisode, s'affiche sur les 1,8 dernières secondes, pendant que la personne parle encore. Le lien vers la vidéo longue se met avec la fonction « vidéo associée » de YouTube, au moment de publier.
- Durée : 17 à 45 s en V2. Au-delà de 45 s, il faut une raison.

## Cadrage plan par plan

La vidéo source est déjà montée en multicaméra (gros plans, plans moyens, plans larges). Pour chaque plan détecté (`select='gt(scene,0.2)'`) on choisit un recadrage :

| Type de plan | Largeur recadrée dans le 1920x1080 |
|---|---|
| Gros plan | 500 px (hauteur 889) |
| Plan moyen | 405 px |
| Plan large | 360 px, voire 270 px pour un zoom serré (image plus douce) |

Le visage est placé au tiers haut. Les positions se lisent sur une planche d'images avec une graduation tous les 240 px (`outils/planche_plans.py`). Pas de détection de visage automatique pour l'instant : OpenCV et MediaPipe ne sont pas installés, et le choix à l'œil est plus juste quand plusieurs personnes sont dans le cadre.

Limite connue : quand le montage d'origine montre quelqu'un qui écoute (l'animateur pendant qu'un invité parle), on ne peut pas cadrer la personne qui parle.

## Qui parle

Le brief des shorts attribuait l'aveu « une grosse partie de mes bugs, c'est parce que j'ai mal demandé » à l'invité développeur. Tous les plans montraient un autre invité, qui n'est pas développeur, et la comparaison de voix penchait vers lui. Le short « Un dev avoue » aurait été faux. Avant de monter un short dont l'angle dépend de l'identité de quelqu'un, lancer `outils/qui_parle.py` et regarder les plans.

Pour reconnaître les intervenants sur la planche des plans, s'appuyer sur les bandeaux incrustés.

## Revue de viralité (épisode 1)

Classement avant recoupe, de mon jugement, sans données d'audience :

1. « Vous priez » : quiz qui appelle les commentaires, gag rapide, fin forte.
2. « Crises de nerfs » : émotion vécue, chute « t'es dev ? ».
3. « Option C » : astuce à copier, donc sauvegardes.
4. « Direct en prod » : scène reconnaissable, mais démarrait sur une phrase abstraite.
5. « Deux réflexes » : utile mais trop long, trois sujets.
6. « Je garde mon dev » : bonne idée qui arrive tard.
7. « Une IA qui vérifie l'IA » : ressemble à un pitch. À publier pour que l'invité concerné le relaie.

Ce que la revue a fait changer :

- **Ouvrir sur la phrase forte**, pas sur ce qui la précède (« waouh, c'est sublime » plutôt que « l'objectif, ce n'est pas de dire »). La phrase de cadrage peut passer à la fin.
- **Couper ce qui dilue après la chute** (les utilisateurs en bêta après le gag « vous priez »).
- **Un short, un sujet.** « Deux réflexes » est devenu deux shorts : fenêtre de contexte (27 s) et code dupliqué (17 s).
- **L'accroche ne répète pas la première phrase** et n'exagère pas (« chaque prompt » devenu « souvent »).
- **Pas de hashtag sans rapport** avec ce qui est dit (#lovable, #bolt retirés).
- **Finir sur une phrase qui se tient**, pas sur une formule d'entreprise.

## Calendrier

Un short la veille de la sortie, un le jour même avec la vidéo longue en vidéo associée, puis un tous les deux jours. Proposer à chaque invité le short où il est la vedette pour qu'il le relaie.
