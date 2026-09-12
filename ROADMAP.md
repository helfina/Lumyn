# Feuille de route de Lumyn

État au 12/09/2026. La version reste **0.0.4**. La PR #3 est terminée et
fusionnée dans `main` au commit `629e63c`. Le chantier
`fix/windows-shutdown-crash` est terminé techniquement au commit `79033bc`.

## Ordre actuel

1. PR #3 : terminée et fusionnée.
2. Finaliser proprement le chantier Windows et sa documentation.
3. Validations natives restantes réellement nécessaires.
4. Nouvelle PR Google vers Lumyn.
5. Android, APK et OAuth Android.
6. Définition et préparation de 0.0.5.
7. Historique de résolution, Notes, Tâches, rappels locaux et autres modules.

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

## PR #3 — Reprises Google et recherche de lieux — terminée

- [x] Réservations persistantes CREATE ; reprise DELETE sans recréation.
- [x] Tests de pannes partielles UPDATE/MOVE et remontée des restaurations incomplètes.
- [x] Propositions sourcées, sélection explicite, repli IA autorisé, Carnet volontaire.
- [x] Étape préparatoire à 175 tests, puis intégration Geoapify à 188 tests Linux.
- [x] Comparatif des fournisseurs et audit préparatoire Android/OAuth documentés.
- [x] Geoapify évalué et intégré pendant le chantier, puis relégué en adaptateur
  optionnel non injecté par défaut ; clé toujours hors dépôt.
- [x] Recherche et autocomplétion hors thread UI, bornées, sans IA réelle.
- [x] Conservation Geoapify interdite ; fournisseur optionnel non injecté par défaut.
- [x] Adaptateur réel : timeout, cinq résultats, attribution et réponses périmées.
- [x] Géoplateforme/BAN par défaut, sans compte ni clé, Licence Ouverte 2.0.
- [x] API Recherche d'entreprises et établissements FINESS sans authentification.
- [x] Routeur adresse/entreprise/santé ; BAN jamais utilisée comme annuaire.
- [x] Geoapify relégué en adaptateur optionnel non injecté.
- [x] Adaptateur Ollama local strict relié facultativement, sans téléchargement de modèle.
- [x] Adaptateur Gemini Web préparé mais activation payante explicitement refusée.
- [x] IA locale hors thread : enrichissement du Carnet puis de la requête publique ; Synapse reste déterministe.
- [x] Adaptateur Ollama Web sourcé et vérification BAN testés avec doubles.
- [x] Ollama Web raccordé, désactivé par défaut, clé et activation locales obligatoires.
- [x] Source RPPS individuelle sans compte indisponible via FHIR (clé requise) ;
  limite documentée, sans intégration supplémentaire.
- [x] DILA/Administration intégré pour CAF, CPAM, mairies et autres administrations prises en charge.
- [x] Tests d'intégration Rendez-vous, garde réseau, concurrence, persistance atomique et reprises après redémarrage.
- [x] CI GitHub Actions Linux/Python 3.12 et Windows/Python 3.13.
- [x] PR #3 fusionnée dans `main` au commit `629e63c`.

## Chantier Windows — crash à la fermeture corrigé

- [x] Crash confirmé comme antérieur à la PR #3 et à Synapse.
- [x] Reproduction de Lumyn complet avec faulthandler et debug asyncio ; trace
  `toga_winforms/libs/proactor.py`, `pythonnet.unload()` et `clr_loader`.
- [x] Test Toga minimal avec le Python Briefcase de Lumyn : fermeture propre,
  code de sortie 0, aucune access violation observée.
- [x] Reproducteur minimal pythonnet et A/B/A : une continuation .NET
  `Task.Delay(...).ContinueWith(...)` conservant un callback Python peut survivre
  jusqu'à `pythonnet.unload()`.
- [x] Correctif Lumyn au commit `79033bc` : annulation par
  `CancellationTokenSource` et `TaskContinuationOptions.OnlyOnRanToCompletion`.
- [x] Portée limitée à Windows, Python 3.13+ et `toga-winforms==0.5.6`, figé pour
  reproductibilité ; `proactor.py` dans `.briefcase` reste original et non modifié.
- [x] Deux fermetures manuelles propres avec le proactor Toga original ; 7 tests
  dédiés, suite complète à **437 tests réussis**.

## Validations natives restantes

- [ ] Confirmer sous Windows le démarrage, l'utilisation normale et la fermeture
  après le correctif ; les deux fermetures ciblées sont déjà validées.
- [ ] Vérifier le rendu WinForms du choix explicite des propositions publiques
  avec des lieux non sensibles.
- [ ] Si le cycle de vie Google est modifié pour corriger le crash, refaire une
  non-régression ciblée de la connexion Calendar ; sinon conserver les validations
  Google déjà acquises.

## Nouvelle PR future — Google vers Lumyn

- [ ] Détecter un événement supprimé dans Google.
- [ ] Vérifier par `google_calendar_id + google_event_id`.
- [ ] Traiter 404/410 comme une suppression distante certaine.
- [ ] Ne jamais supprimer localement sur timeout, panne réseau ou erreur OAuth.
- [ ] Vérifier la reprise après redémarrage suivant une suppression.
- [ ] Synchroniser les modifications Google vers Lumyn.
- [ ] Définir la gestion des conflits.
- [ ] Fournir une synchronisation/réconciliation explicite.

## Android / APK / OAuth Android

- [x] Première tentative effectuée.
- [x] Blocage identifié avant génération : runtime Java sans `javac`, puis
  téléchargement du JDK 17 Briefcase expiré.
- [ ] Obtenir un environnement JDK Android complet et fonctionnel.
- [ ] Réussir le premier build et examiner package, manifeste et permissions.
- [ ] Adapter et valider OAuth Google Android sur appareil réel.
- [ ] Produire et tester un APK ; aucun APK n'est actuellement validé.

## Version suivante

- [ ] Définir le périmètre de 0.0.5 après stabilisation.
- [ ] Préparer 0.0.5 seulement après décision explicite ; aucune release ni tag
  n'est actuellement prévu.

## Fonctionnalités ultérieures

Historique de résolution, Notes, Tâches, rappels locaux et autres extensions de
Lumyn restent différés. Aucun de ces sujets n'est développé dans le chantier
Windows courant.
