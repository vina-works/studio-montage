# 03. Transcription et vérification

## Transcrire

`outils/transcrire.py` (faster-whisper `large-v3-turbo`, mots horodatés, français par défaut). Sur une RTX 5080 : 52 minutes en 4 minutes. Sorties à côté du fichier : `.transcript.json`, `.transcript.md`, `.srt`.

La commande `transcrire` utilise la carte graphique par défaut. Il n'y a pas d'option `--gpu`, seulement `--cpu` pour forcer le processeur.

## Les défauts de Whisper qui comptent pour le montage

| Défaut | Exemple ép. 1 | Conséquence | Parade |
|---|---|---|---|
| Pas d'hésitations dans le texte | 2 « euh » transcrits sur toute l'ouverture | On ne voit pas ce qu'il y a à couper | Seconde passe sans VAD, amorcée avec des « euh » (`outils/hesitations.py`) : 121 hésitations trouvées |
| Mots étirés | « responsable » dure 1,64 s parce qu'il contient « euh alors je suis » | Une coupe calée sur ses bornes mange ou laisse une hésitation | Ne pas couper dans un mot de plus de 0,6 s sans le vérifier |
| Doublons inventés | « J'ai blindé de vérification » écrit deux fois, dit une seule | On coupe la seule prise réelle | Confirmer tout faux départ avec la seconde passe |
| Noms mal entendus | vibe coding devient « webcoding », « Level Coding » ; les noms de personnes et de marques sont déformés | Sous-titres faux | Glossaire dans `outils/glossaire.json`, et `outils/glossaire.local.json` pour les noms propres à tes vidéos |
| Ponctuation et majuscules aléatoires | Majuscule à chaque début de segment | Sous-titres peu lisibles | Normaliser la casse, garder les noms propres |
| Pas d'attribution des voix | « Très honnêtement, mes bugs… » attribué à un invité par le plan, dit par un autre | Erreur de fond dans un short | `outils/qui_parle.py`, voir [07](07-shorts.md) |

## Les silences ne se détectent pas au volume

La consigne d'origine était : « un trou entre deux mots qui n'est pas un silence pour `silencedetect`, c'est une hésitation ». Sur l'épisode 1, **126 trous sur 157** n'étaient pas des silences à −35 dB, et beaucoup contenaient des mots (relances, rires, voix qui se chevauchent). Couper ces trous à l'aveugle aurait mangé de la parole. On ne coupe qu'un trou où la seconde passe entend une hésitation, et on garde tel quel un trou bruité de plus d'une seconde (rire probable), en le signalant.

## Vérifier un rendu sans l'écouter

`outils/verifier.py` recolle l'audio selon `edit.json`, le retranscrit et compare aux mots attendus. Ce contrôle a trouvé :

- un « non » resté dans « ça a été, non non, ça a été » ;
- « dit » collé devant « toi tu commences » ;
- le « mais » mangé dans la phrase de la perceuse ;
- la seule vraie prise de « j'ai blindé de vérifications » coupée.

Il ne dit rien de la musicalité d'un raccord. Après chaque rendu, on donne à l'auteur la liste des raccords délicats en timestamps de sortie, avec la raison en une ligne, pour qu'il les écoute en priorité.

## Les durées s'estiment avant de se promettre

Avant d'annoncer une durée de calcul, mesurer la progression (segments faits, temps écoulé). Une corrélation audio écrite naïvement (FFT de toute la piste à chaque fenêtre) a tourné 17 minutes sans fin prévisible. La même, avec une FFT de taille fixe en puissance de 2 sur un signal à 2 kHz, prend moins d'une minute.
