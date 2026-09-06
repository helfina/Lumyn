# Feuille de route de Lumyn

État au 06/09/2026. 0.0.4 fusionnée dans main (PR #2, `0460534`).
Travail courant : `feature/google-reprise-recherche-lieux`, version conservée à 0.0.4.

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
- [x] Validation native Carnet/Synapse et CRUD Google réel du 05/09/2026 sur c92aaab.
- [x] 132 tests confirmés sous Windows/Python 3.13.
- [x] Correctif du focus après changement de calendrier ; 137 tests Linux et Windows réussis.
- [x] Contrôle natif Windows du nouveau correctif de focus.
- [x] Crash de fermeture Windows intermittent reproduit sur f244bd0, c92aaab et main 0.0.3 (78093a0) ; défaut préexistant, non introduit par Synapse ni le correctif de focus.
- [x] Audit de e030674 face à main 78093a0 ; aucun nouveau défaut bloquant identifié.
- [x] Investigation du crash documentée ; aucune correction sûre démontrée.
- [x] Version 0.0.4 et CHANGELOG préparés, 137 tests Linux relancés.
- [x] PR #2 fusionnée dans main, commit 0460534 ; candidate finale Windows : 137 tests en 4.44 s.
- [ ] Publication/installateurs : décision distincte, aucune publication effectuée dans ce lot.

## Lot courant après 0.0.4

- [x] Réservations persistantes CREATE ; reprise DELETE sans recréation.
- [x] Tests de pannes partielles UPDATE/MOVE et remontée des restaurations incomplètes.
- [x] Propositions sourcées, sélection explicite, repli IA autorisé, Carnet volontaire.
- [x] Étape préparatoire à 175 tests, puis intégration Geoapify à 188 tests Linux.
- [x] Comparatif des fournisseurs et audit préparatoire Android/OAuth documentés.
- [x] Geoapify choisi et intégré en offre gratuite, clé hors dépôt.
- [x] Recherche et autocomplétion hors thread UI, bornées, sans IA réelle.
- [ ] Clarification écrite des droits de conservation Geoapify avant sauvegarde Carnet.
- [x] Adaptateur réel : timeout, cinq résultats, attribution et réponses périmées.
- [x] Géoplateforme/BAN par défaut, sans compte ni clé, Licence Ouverte 2.0.
- [x] API Recherche d'entreprises et établissements FINESS sans authentification.
- [x] Routeur adresse/entreprise/santé ; BAN jamais utilisée comme annuaire.
- [x] Geoapify relégué en adaptateur optionnel non injecté.
- [x] Adaptateur Ollama local strict relié facultativement, sans téléchargement de modèle.
- [x] Adaptateur Gemini Web préparé mais activation payante explicitement refusée.
- [x] IA locale hors thread : enrichissement du Carnet puis de la requête publique ; Synapse reste déterministe.
- [x] Adaptateur Ollama Web sourcé et vérification BAN testés avec doubles.
- [ ] Ollama Web réel : bloqué (compte 18+, clé et quota gratuit non chiffré).
- [ ] Source RPPS individuelle sans compte : non disponible via FHIR (clé requise).
- [ ] Validation WinForms réelle des services publics avec des lieux non sensibles.
- [ ] Validation native Windows/Google du lot courant.
- [ ] Construction Android : tentative bloquée avant génération par JDK incomplet/téléchargement expiré.
- [ ] OAuth natif et validation sur appareil après build réussi.

## Au-delà

Historique de résolution, Notes et Tâches restent différés. Le crash Windows fait
l'objet d'un chantier natif séparé. Aucun de ces sujets n'est développé ici.
