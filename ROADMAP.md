# Feuille de route de Lumyn

État vérifié dans le code le 05/09/2026. Les numéros ci-dessous décrivent les
jalons envisagés ; le prototype courant reste en version 0.0.3.

## Bases

- [x] Nom, vision, documentation, Git et GitHub.
- [x] Application BeeWare et première interface.
- [x] Module Rendez-vous avec saisie, validation et stockage local.

## Module Rendez-vous et Google

- [x] Dates, heures, jours et confirmation explicite.
- [x] Lieu et dates relatives « dans N jours ».
- [x] Création, modification, suppression locales.
- [x] Code OAuth et lecture multi-agendas, filtres persistants et calendrier.
- [x] Code de création, modification, déplacement et suppression Google liés.
- [x] Rappels Google à J-1 et H-1.
- [x] 57 tests isolés et premières corrections de fiabilité.
- [ ] Validation native Windows et Google réel sur un calendrier de test.
- [ ] Reprise fiable après pannes simultanées Google/local.
- [ ] Validation Android, construction APK et adaptation OAuth.

## Prochaine étape unique

Validation manuelle Windows de la branche de stabilisation (docs/TESTING.md).

## Version publique 1.0

Nécessite une validation réelle Windows et Android, une gestion fiable des erreurs
et une documentation d'installation. Notes, tâches et Synapse restent des idées
futures ; aucune nouvelle fonctionnalité de ces modules n'est engagée.
