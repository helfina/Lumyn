# Feuille de route de Lumyn

## Google → Lumyn — 13/09/2026

Chantier courant : `feature/google-vers-lumyn`, depuis
`e442ebffe4468816ed03141fe43b1baa89266784` (PR #4 Windows fusionnée).
Version conservée : **0.0.4**. Le crash Windows reste corrigé et validé.
Validation automatisée actuelle : **481 tests réussis**, dont **83 tests ciblés**
(synchronisation, interface et reprises Google). Les tests restent sans compte
Google réel ; la validation native ci-dessous a été effectuée séparément.

L'action explicite « Synchroniser Google » réconcilie uniquement les rendez-vous
locaux déjà liés. Aucun polling ni nouvel appel au démarrage. Une référence
`google_reference` est conservée dans le rendez-vous après écriture Google ou
rapprochement identique. Titre, date, heure, durée et lieu compatibles peuvent
être actualisés ; une divergence locale ou une ancienne liaison sans référence
et différente de Google reste en conflit. Aucun écrasement distant n'est effectué.
L'écriture locale compare à nouveau le rendez-vous complet sous le verrou existant
et utilise le remplacement atomique du stockage.

**Règle définitive : 404/410 ciblé signifie absent ou inaccessible, jamais une
suppression certaine.** Lumyn conserve intégralement le rendez-vous et ses
identifiants puis propose « Conserver dans Lumyn » et « Supprimer de Lumyn ».
La conservation est le comportement par défaut. Seul le second choix supprime
localement, après contrôle de la version examinée ; il ne contacte pas Google.
Après redémarrage avant décision, relancer la synchronisation pour réafficher le
choix. Après suppression confirmée, aucune recréation automatique.
Timeout, OAuth, 401/403/429/5xx, calendrier inaccessible et réponses invalides
conservent les données. Les erreurs d'un rendez-vous n'empêchent pas les suivants.

Limites : aucun rapprochement de déplacement par titre/date/lieu ; les déplacements
ambigus restent conservés. Les réponses `cancelled`, récurrences, journées entières
et heures non représentables sont conservées avec une erreur contrôlée. Les anciens
rendez-vous divergents exigent une réconciliation manuelle. La synchronisation
utilise actuellement les appels Google synchrones existants ; l'interface peut
attendre pendant une requête. La sélection d'un calendrier local ne déclenche pas
la synchronisation ; le bouton explicite examine toutes les liaisons enregistrées.

### Validation réelle Windows et Google Calendar — 13/09/2026

- `briefcase dev` : démarrage Windows réussi.
- Rendez-vous fictif créé depuis Lumyn : présent dans Lumyn et Google Calendar.
- Modifications Google seules (heure 18h → 18h30, puis titre) : reprises dans
  Lumyn après « Synchroniser Google ».
- Disparition de l'événement côté Google : rendez-vous local conservé avec le
  statut « non synchronisé : conservé, réessayer » ; conservation confirmée après
  fermeture, redémarrage et nouvelle synchronisation.
- Suppression manuelle du rendez-vous depuis Lumyn : suppression locale réussie
  et aucune réapparition après redémarrage.
- Le défaut d'interface qui laissait ce statut après suppression a été corrigé au
  commit `691d89e` et couvert par une régression UI.

Le cas HTTP 404/410 qui affiche « Conserver dans Lumyn » / « Supprimer de Lumyn »
n'a pas été produit naturellement par Google pendant cet essai. Il reste couvert
par les tests automatisés ; le comportement réel observé est resté non destructif.
Android/APK/OAuth Android et préparation 0.0.5 restent ultérieurs.


État au 12/09/2026. La version reste **0.0.4**. La PR #3 est terminée et
fusionnée dans `main` au commit `629e63c`. Le chantier
`fix/windows-shutdown-crash` est terminé techniquement au commit `79033bc`.

## Ordre actuel

1. PR #3 : terminée et fusionnée.
2. Chantier Windows : terminé et validé.
3. PR #5 Google → Lumyn : en brouillon, validation Windows/Google effectuée.
4. Android, APK et OAuth Android.
5. Définition et préparation de 0.0.5.
6. Historique de résolution, Notes, Tâches, rappels locaux et autres modules.

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

## PR #5 — Google vers Lumyn — en brouillon

- [x] Synchronisation/réconciliation explicite des rendez-vous liés.
- [x] Mise à jour locale des modifications Google compatibles et détection des conflits.
- [x] Conservation sur 404/410 avec décision utilisateur explicite, sans suppression
  automatique ni recréation Google.
- [x] Conservation sur timeout, panne réseau, OAuth et tout état ambigu.
- [x] Tests de redémarrage, d'idempotence et de reprise.
- [x] Validation réelle Windows/Google du 13/09/2026 : modification d'heure et de
  titre reprises ; disparition conservée localement après redémarrage.
- [ ] Valider manuellement le rendu WinForms des choix proposés par un 404/410 si
  Google produit naturellement ce cas ; ce chemin est déjà couvert automatiquement.

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
