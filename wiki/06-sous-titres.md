# 06. Sous-titres

## Épisode long : un `.srt` séparé

- Recalculé à partir de `edit.json` et des mots horodatés, jamais repris du `.srt` d'origine.
- Un mot entre dans un segment si son milieu y tombe. Les « euh » ne s'affichent pas.
- Glossaire appliqué (`outils/glossaire.json`).
- Coupure de sous-titre sur une pause de plus de 0,45 s, au-delà de 74 caractères, au-delà de 5,5 s, ou à une fin de phrase Whisper quand le sous-titre fait déjà 30 caractères. Jamais devant un mot qui commence par une apostrophe ou un trait d'union.
- Deux lignes au plus, coupées au milieu.
- Aucun mot après la fin du contenu (sinon des mots apparaissent sur la carte de fin).

Par défaut, le `.srt` reste séparé : c'est corrigeable après coup et suffisant pour YouTube. On incruste seulement pour les réseaux qui n'affichent pas les sous-titres.

## Shorts : mot à mot, incrustés

- Format ASS, police Segoe UI Black 104 (sur 1080x1920), texte et contour (7 px) aux couleurs `texte` et `fond` du thème, **mot en cours en couleur `accent`**.
- Placés à 500 px du bas, au-dessus de l'interface YouTube.
- Groupes de 4 mots et 20 caractères au plus. Nouveau groupe après une pause de 0,3 s et **à chaque coupe** : un groupe à cheval sur deux coupes affiche des mots de deux phrases (« par là très »).
- Les tokens Whisper `'est`, `-ce`, `?` se recollent au mot précédent. Espace insécable avant `?`, `!`, `%`.

La police des sous-titres des shorts ne vient pas du thème : libass a besoin d'un fichier de police installé, et Segoe UI Black l'est sur Windows.

## Relire avant publication

Les sous-titres viennent de la transcription. Il reste des fautes. Les relire en entier avant de publier.
