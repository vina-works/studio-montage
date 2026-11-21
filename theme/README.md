# Thème

Les panneaux d'illustration (`outils/panneaux.py`) et les shorts (`outils/shorts.py`) prennent leurs couleurs, leurs polices et leur signature dans un thème.

- `defaut.json` : le thème neutre livré avec le dépôt.
- `local.json` : ton thème à toi (ta charte graphique). Il est ignoré par git, et il complète `defaut.json` clé par clé : tu n'y mets que ce que tu changes.
- La variable d'environnement `THEME` peut pointer vers un autre fichier, qui remplace alors `local.json`.

## Clés

| Clé | Rôle |
|---|---|
| `couleurs.fond` | fond des panneaux et du cadre d'accroche des shorts |
| `couleurs.encadre`, `couleurs.bordure` | encadrés et barres dans les panneaux |
| `couleurs.texte` | texte principal |
| `couleurs.accent` | une seule couleur d'accent : filet, mot en cours dans les sous-titres des shorts |
| `couleurs.texte_2`, `couleurs.texte_3` | textes secondaires |
| `polices.titre`, `polices.titre_graisse`, `polices.texte` | familles de polices (CSS) |
| `polices.url` | feuille de style qui charge ces polices (Google Fonts par exemple) |
| `signatures` | petits motifs texte affichés en bas à droite d'un panneau, par nom (`"content": "^_^"`) ; un `<b>` y prend la couleur d'accent |
| `signature_defaut` | nom de la signature quand le panneau n'en précise pas |

Dans `panneaux.json`, un panneau choisit sa signature avec `"signature": "<nom>"` (l'ancien nom de champ `renard` est encore lu).
