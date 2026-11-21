# Sécurité

## Signaler une faille

Ne signale pas une faille dans une issue publique. Utilise le signalement privé de GitHub : onglet **Security** du dépôt, puis **Report a vulnerability**. Seuls les mainteneurs voient le rapport.

Indique ce que tu as trouvé, comment le reproduire et ce que ça permet. Tu reçois une première réponse sous sept jours. Une fois la faille corrigée, elle est décrite dans un avis de sécurité, avec ton nom si tu le souhaites.

## Périmètre

Les outils tournent en local, sur tes fichiers. Les points sensibles sont :

- **la salle de revue** (`outils/revue/serveur.py`) : un serveur HTTP local qui lit et écrit dans le dossier de travail. Elle n'est pas faite pour être exposée sur un réseau ;
- **les fichiers JSON** (`edit.json`, `panneaux.json`, `shorts.json`) : leur contenu est passé à FFmpeg et à Chrome. N'ouvre pas un plan reçu d'une source inconnue sans le relire.

## Versions

Seule la branche `main` reçoit des correctifs.
