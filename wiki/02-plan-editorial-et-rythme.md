# 02. Plan éditorial et rythme

Deux métiers différents, deux passes différentes. Le plan éditorial décide **quoi** garder. Le rythme décide **comment** ça respire. Le monteur de rythme ne remet jamais en cause une décision éditoriale validée.

## Le plan éditorial

Format qui a marché sur l'épisode 1 (modèle : [`modeles/plan_editorial.md`](../modeles/plan_editorial.md)) :

1. Diagnostic en quelques lignes : accroche, invités, segments qui marchent ou pas, meilleur moment.
2. Cold open : 2 ou 3 candidats chronométrés, un recommandé, et ce que chacun dévoile (ne jamais dévoiler une réponse de quiz).
3. Présentation des invités : on garde la légitimité de chacun, on remplace les CV dits à l'oral par des bandeaux.
4. Segments : verdict par bloc (garder, resserrer, couper), avec timestamps et raison.
5. Coupes en trois niveaux : **indispensable**, **recommandé**, **optionnel**, avec le gain de chaque coupe.
6. Points de continuité : ce qu'une coupe rend incohérent plus loin.
7. Bilan de durée par niveau.

Le plan donne des timestamps de **début de phrase** issus du `.transcript.md`. Le monteur les recale sur les bornes de mots du `.json`, et suit la **citation** quand citation et timestamp divergent.

## Le rythme : réglages validés

Les réglages de la V1 ont été jugés trop agressifs (« ça manque de fluidité », « un peu haché »). Voici ceux de la V2, validés à l'écoute :

| Réglage | V1 (rejetée) | V2 (validée) | Shorts |
|---|---|---|---|
| Marge autour d'un mot à chaque coupe | 0,12 s | **0,15 s** | 0,12 s |
| Pause gardée entre deux phrases | 0,35 s | **0,50 s** | 0,32 s |
| Pause gardée entre deux idées (pause d'origine de 1,2 s ou plus, ou après une question) | 0,60 s | **0,80 s** | 0,32 s |
| Pause gardée autour d'une hésitation coupée | 0,24 s | **0,40 s** | |
| On ne raccourcit une pause que si elle dépasse la cible de | 0,10 s | **0,25 s** | 0,18 s |
| On coupe une hésitation seulement si le trou fait au moins | 0,30 s | **0,65 s** | |
| Coupe d'un « euh » caché dans un mot étiré | oui | **non** | non |
| Fondu audio à chaque raccord | 20 ms | 20 ms | 20 ms |

Résultat sur l'ouverture de l'épisode 1 : 165 segments en V1, 103 en V2, pour une minute de plus seulement.

## Ce qu'on coupe

- **Hésitations** (« euh », « hum ») : seulement quand elles laissent un vrai trou. « Bah », « ben » restent quand ils portent la phrase (« ah bah oui », « ben, il sera pas résolu »).
- **Faux départs et bégaiements** (« c'est pas, c'est pas par volonté ») : on garde la dernière prise. Attention aux faux doublons inventés par Whisper, voir [03](03-transcription-et-verification.md).
- **Silences** : jamais entiers. On garde ceux qui servent : rire, après une question forte, avant une chute.

## Ce qu'on ne coupe pas (retours d'écoute)

- **Les relances et les ponts.** Couper la relance de l'animateur entre deux invités rend la transition abrupte. Sur la présentation d'un invité, on a rendu la question entière et la relance de l'animateur : « il faut un peu plus de naturel ».
- **Les fins de phrases.** Une phrase qui s'arrête sur « jusqu'au moment » est un défaut, même si le plan coupait là.
- **Les passages qui portent la valeur.** L'auteur a demandé de rendre la fin sur la duplication de code (« là je donne de la valeur ») et la fin d'un invité sur Git.
- **Une réponse adressée à quelqu'un d'autre.** Après un déplacement, « Ok, c'est très intéressant » répondait à un invité mais suivait la réponse d'un autre. On démarre la réplique au mot utile (« toi, tu commences à t'intéresser… »).

Et une exception dans l'autre sens : **le nom du quiz « on s'en fout »**. Un élément qui n'a de sens que pour l'animateur peut sauter.

## Découper un épisode long

Une ouverture de 19 minutes devient une **partie 1** qui finit sur une vraie sortie (rire, carte de fin) et une **partie 2** publiée plus tard. Pour que la coupe soit naturelle, prévoir une séquence de conclusion tournée après coup qui teasera la suite. Vérifier que la suite existe bien dans les fichiers avant de l'annoncer.
