# 05. Illustrations mi-écran

Pendant qu'un invité emploie un terme technique, la vidéo se recentre sur la moitié gauche et un panneau glisse à droite. Le but : vulgariser les termes techniques (la fenêtre de contexte, par exemple).

## Quoi illustrer

Les dix panneaux validés pour l'épisode 1 :

| Panneau | Message en une phrase |
|---|---|
| 63 % | des personnes qui explorent le vibe coding ne sont pas développeuses ; ça compte les personnes, pas les lignes de code |
| Le terminal | parler à l'ordinateur en tapant des commandes |
| 380 000 apps visibles | des robots testent les adresses ; 380 000 publiques, environ 5 000 avec des données sensibles |
| Visible dans le navigateur | ce que le navigateur reçoit, n'importe quel visiteur peut le lire |
| Tester en local | ton ordinateur ou le site en ligne : qui voit la casse |
| Commit et PR | une sauvegarde nommée, puis une relecture avant d'intégrer |
| La fenêtre de contexte | la mémoire de travail de l'IA a une limite ; nouvelle conversation |
| Monter en puissance | IA standard, IA plus chère, mode ultra |
| Le code dupliqué | bug corrigé sur un bouton, toujours là sur sa copie |
| Une super perceuse | l'IA apporte la force, toi tu sais où percer |

Règles :

- **Un panneau complète ce qui est dit, il ne le contredit pas.** Les exemples (adresses, code, faux mot de passe) sont visiblement fictifs.
- **Une image incomplète à l'oral se complète au panneau**, pas en réécrivant la phrase (la perceuse).
- **Un panneau ne dévoile jamais une réponse de quiz.** Le panneau 63 % était placé à 07:56, la réponse tombait à 08:19 : déplacé à 08:22.
- **Ne pas corriger une erreur que le spectateur n'entend plus.** L'option « 63 % du code » barré a été écartée : l'explication fausse avait déjà été coupée, la barrer aurait embrouillé.

## Format et timing

- Panneau 960x1080, la vidéo occupe la moitié gauche (recadrage centré 960x1080 en 1080p).
- Entrée et sortie en glissé de 0,3 s.
- 7 s par panneau en moyenne. **En dessous de 4 s, on ne lit pas** : « Monter en puissance » à 3,8 s est trop court, à fusionner ou supprimer.
- Laisser respirer entre deux panneaux. Trois panneaux en 30 secondes, c'est trop.
- Le recadrage automatique au centre donne des plans larges où la personne est petite ou décentrée. Idéalement, recadrer plan par plan comme pour les shorts.

## Lisibilité

La première version était trop petite pour un téléphone. Tailles validées (sur 960x1080) : surtitre 30 px, titre 76 px, texte 36 px, encadrés 33 px. Les couleurs et polices viennent du [thème](../theme/README.md).

## Rendu

`outils/panneaux.py` écrit un HTML par panneau (polices Google Fonts), le fait capturer par Chrome sans interface, et produit une incrustation de contrôle sur une image de la vidéo au bon moment. Edge n'est pas installé sur la machine, Chrome l'est.
