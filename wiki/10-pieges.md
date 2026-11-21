# 10. Pièges

Chaque ligne a coûté au moins un aller-retour sur l'épisode 1.

| Symptôme | Cause | Parade |
|---|---|---|
| `transcrire --gpu` refuse l'option | l'option n'existe pas | la carte graphique est le choix par défaut |
| `open() got an unexpected keyword argument 'metadata_errors'` | faster-whisper 1.2.1 contre PyAV 19 | `transcrire.py` retire l'argument avant l'appel à `av.open` |
| `cublas64_12.dll is not found` dans un script maison | DLL CUDA installées par pip non visibles | ajouter les dossiers `nvidia/*/bin` au `PATH` **et** via `os.add_dll_directory` avant d'importer faster-whisper |
| Le plan de coupe ne colle pas à la vidéo | plan fait sur le MP3, vidéo décalée de 0,832 s | mesurer le décalage avec `aligner.py` |
| Fin de phrase coupée | borne du plan prise au mot près | couper sur une fin de phrase, suivre la citation |
| « Ok, c'est très intéressant » qui répond au mauvais invité | passage déplacé | démarrer la réplique au mot utile |
| Un « non » ou un « dit » qui traîne au raccord | mot étiré par Whisper, marge de 0,12 s | borne forcée à la main, vérifiée par retranscription |
| La seule vraie prise coupée | doublon inventé par Whisper pris pour un faux départ | confirmer avec la seconde passe |
| Les hésitations coupées mangent de la parole | `silencedetect` ne sépare pas silence et relance | ne couper que ce que la seconde passe entend comme « euh » |
| Vidéo 1,6 s plus longue que le son | `-shortest` avec une image en `-loop 1` | `-t <durée>` |
| Le zip contient les anciens shorts | rendu en échec, la commande suivante tourne quand même | tester le code de sortie avant d'emballer |
| Un panneau dévoile la réponse du quiz | placé avant la réponse | placer après, vérifier par retranscription |
| Un short attribue une phrase à la mauvaise personne | brief fait sur la transcription | `qui_parle.py` et planche des plans |
| Sous-titre « par là très » | groupe de mots à cheval sur deux coupes | couper les groupes aux raccords |
| Calcul qui ne finit pas, sans progression | FFT naïve sur toute la piste | taille fixe en puissance de 2, signal sous-échantillonné, afficher la progression |
| Une commande PowerShell `gh ... --jq '... | @tsv'` échoue | les guillemets internes cassent l'argument | variables intermédiaires ou script |
| Le fichier temporaire a disparu entre deux sessions | dossier temporaire de session effacé | tout script utile va dans le dépôt, pas dans un dossier temporaire |
| Le plan signalé ne correspond pas au libellé de la piste | une annotation de navigateur vise toute la piste et peut reprendre le texte de son premier clip | relever la version, le timecode affiché et le clip sélectionné, puis remonter aux rushs à travers les coupes manuelles |
| La carte latérale reste visible tandis que la vidéo disparaît | le lecteur Chromium peut perdre l’image d’une vidéo soumise à un masque et à une transformation | utiliser un conteneur de recadrage à débordement masqué, puis vérifier au timecode signalé après un saut dans la vidéo |
| Les lèvres se décalent brièvement au retour plateau | l’ancienne ouverture passe d’une piste OBS à l’autre avec une avance différente | vérifier les deux pistes par corrélation sur la réplique et corriger son décalage local |
| La crête dépasse le plafond après export | l’encodage AAC crée des crêtes absentes de la mesure PCM | mesurer après encodage et régler le plafond en conséquence |
| Le dépôt du master échoue dès l’ouverture du fichier | le connecteur Drive de cet export plafonnait à 512 Mio | vérifier la taille avant l’envoi et choisir un mode de transfert adapté |
