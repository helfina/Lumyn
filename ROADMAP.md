# Feuille de route de Lumyn

État au 05/09/2026. Version déclarée : 0.0.3 ; travail courant exclusivement sur
`feature/synapse-rendez-vous`.

## 0.0.3 — Rendez-vous stable

- [x] Saisie, dates, heures, confirmation et stockage local.
- [x] Calendrier Google, filtres, création, modification, déplacement, suppression.
- [x] 57 tests isolés et validation réelle Windows/Google du 05/09/2026.
- [x] Fusion dans main effectuée avant cette reprise.

## 0.0.4 — Carnet et Synapse Rendez-vous

- [x] Carnet CRUD, alias, professions, plusieurs adresses, favorite et navigation.
- [x] Validation Windows du carnet sur la base à 78 tests.
- [x] Validation renforcée des fiches, Maison unique, fichiers illisibles protégés.
- [x] Synapse local intégré avec validation déterministe et priorité au carnet.
- [x] VISIO/DOMICILE à Maison, site explicite, ambiguïtés bloquantes.
- [x] Parcours clavier préparation puis confirmation ; CRUD Google conservé.
- [x] Abstraction externe testée, sans fournisseur actif ni sauvegarde silencieuse.
- [x] 132 tests automatiques isolés réussis après documentation.
- [ ] Validation Windows/Google des nouveaux scénarios Synapse.
- [ ] Investigation native du crash de fermeture signalé.
- [ ] Décision de livraison, changement de version et fusion autorisée.

## Au-delà

Historique de résolution et fournisseur externe réel nécessitent une définition
et un choix explicite. Restent également : reprise après pannes Google/local,
Android/APK/OAuth, puis notes et tâches selon les priorités de l'utilisatrice.
