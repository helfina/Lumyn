# Journal du projet Lumyn

---

# Séance 1 — 21/07/2026

## Objectif

Lancer officiellement le projet Lumyn.

## Réalisé

- Définition de la vision du projet.
- Choix du nom **Lumyn**.
- Choix du moteur intelligent **Synapse**.
- Choix provisoire de BeeWare, Toga et Briefcase.
- Diagnostic complet du PC.
- Création de l'architecture du projet.
- Initialisation de Git.
- Création du dépôt GitHub.
- Premier push vers GitHub.
- Création de la documentation initiale.
- Rédaction du README.

## Décisions importantes

- Lumyn sera un assistant personnel modulaire.
- Chaque fonctionnalité devra répondre à un problème réel.
- Le projet sera développé par petites versions successives.
- Les données seront stockées localement autant que possible.

## Difficultés rencontrées

Aucune difficulté bloquante.

## Prochaine étape

Créer un environnement virtuel Python puis installer BeeWare.

---
---

# Séance 2 — 21/07/2026

## Objectif

Créer la première application BeeWare.

## Réalisé

- Création de l'environnement virtuel Python.
- Installation de Briefcase.
- Création du projet BeeWare.
- Premier lancement réussi de Lumyn.
- Analyse de la structure générée.
- Compréhension du fichier `app.py`.

## Décisions importantes

- Conserver la structure générée par BeeWare jusqu'à sa complète compréhension.
- Commencer le développement par des interfaces simples avant d'ajouter de la logique.

## Prochaine étape

Ajouter un premier widget (`Label`) dans la fenêtre.

---

# Séance 3 — 22/07/2026

## Objectif

Découvrir les premiers widgets BeeWare.

## Réalisé

- Compréhension du fonctionnement d'un `Label`.
- Création du premier texte.
- Ajout d'un second texte.
- Découverte de `Box`.
- Compréhension de `Pack`.
- Utilisation de `COLUMN` pour organiser les widgets verticalement.

## Concepts appris

- Widget
- Label
- Variable
- Box
- add()
- Pack
- COLUMN

## Ce que j'ai compris

Un widget est créé puis ajouté à un conteneur.

Le conteneur utilise `Pack` pour organiser ses éléments.

## Prochaine étape

Créer le premier bouton de Lumyn.

# 23/07/2026

## Module Rendez-vous

- Réorganisation complète du module.
- Création d'un modèle de rendez-vous.
- Séparation des responsabilités :
  - analyseur.py
  - gestion.py
  - resultat.py
  - modele.py
  - ui.py
- L'analyseur calcule désormais une vraie date.
- Prise en charge :
  - jours de la semaine
  - aujourd'hui
  - demain
  - après-demain
  - dates numériques
  - dates écrites
- Détection des incohérences entre un jour et une date.
- Création d'un objet résultat (`etat`, `message`, `rendez_vous`).
- L'interface utilise désormais cet objet résultat.
- Ajout d'un bouton Confirmer (préparation de la suite).

# 05/09/2026 — Reprise et stabilisation

- Comparaison du dépôt et de l'archive, puis conservation des ajouts Google.
- Préservation du mode local, correction des écritures et des confirmations.
- Saisie du lieu, délais en jours, heures invalides et dates bissextiles.
- 57 tests isolés réussis après les corrections, avec Google simulé.
- Documentation actualisée ; prochaine étape : validation native Windows.


# 05/09/2026 — Validation manuelle réelle Windows et Google Calendar

Résultats des essais réels confirmés par l'utilisatrice sur la branche
`codex/lumyn-fiabilisation-rendez-vous` :

- Démarrage Windows avec `briefcase dev` : OK ; aucun `ResourceWarning` SSL
  observé au lancement.
- Création Google et affichage dans Lumyn et Google Calendar : OK.
- Modification et suppression d'un rendez-vous : OK, effet immédiat observé.
- Déplacement entre calendriers Google : OK, aucun doublon observé.
- Liaison Lumyn/Google cohérente pendant ces opérations.

Cette validation réelle complète les 57 tests automatiques avec Google simulé.
PROJECT_STATE.md et docs/TESTING.md distinguent désormais les résultats confirmés
et les contrôles complémentaires non confirmés, notamment Android.
Tous les tests ont été relancés après les modifications documentaires : 57 réussis.
Aucune fonctionnalité, aucun code applicatif et aucun test modifié.
Arrêt après documentation ; PR conservée en brouillon, sans fusion.


# 05/09/2026 — Carnet fiabilisé et première intégration Synapse locale

- Reprise vérifiée de `feature/synapse-rendez-vous` au commit `3f0f119` ; la
  stabilisation 0.0.3 était déjà fusionnée. Les 78 tests de la base passent.
- Validation Carnet/navigation Windows rapportée par l'utilisatrice ; crash de
  fermeture pythonnet signalé puis relance réussie. Diagnostic natif encore ouvert.
- Renforcement des fiches, des alias, de Maison et des sauvegardes ; isolation
  globale des fichiers personnels dans les tests.
- Interpréteur et orchestrateur Synapse locaux intégrés au parcours existant :
  métier, alias, site explicite, VISIO/DOMICILE à Maison, ambiguïtés bloquantes.
- Préparation/confirmation au clavier, préservation des identifiants Google lors
  d'une modification, aucun changement du mécanisme de déplacement/suppression.
- Abstraction externe ajoutée après les tests locaux ; aucun fournisseur actif.
- Régressions supplémentaires : ville après alias, lieu physique manquant et
  distinction entre Maison et Maison médicale.
- 132 tests réussis après code et documentation, soit 54 cas ajoutés ; Google simulé.
- Documentation synchronisée ; version conservée à 0.0.3. Prochaine étape : essais
  natifs de cette branche avant décision 0.0.4. Aucun merge effectué par cette séance.


# 05/09/2026 — Validation complète Windows/Google, focus et crash de fermeture

- Compte rendu utilisateur sur `c92aaab` : 132 tests réussis en 3.94 s sous
  Windows/Python 3.13 ; application native WinForms, démarrage et navigation OK.

- Carnet validé manuellement : création, modification, suppression, plusieurs
  adresses et adresse favorite.

- Synapse validé manuellement : professionnel reconnu, priorité au Carnet,
  adresse favorite, site explicite non favori, VISIO/DOMICILE à Maison et
  ambiguïtés bloquant la confirmation.

- Google Calendar réel validé : créations VISIO/DOMICILE, rappels présents,
  aucun lien Google Meet automatique, modification du même événement,
  déplacement Famille → Gaelle et suppression. Aucun doublon observé et liaison
  Lumyn / Google cohérente.

- Défaut de focus identifié : après saisie puis changement de calendrier, le
  focus restait sur le sélecteur. Correctif ajouté via `on_change` et
  `TextInput.focus()`, avec invalidation de la préparation précédente.

- Après publication du correctif `f244bd0`, récupération et validation sur le
  poste Windows réel : 137 tests réussis sous Python 3.13 en 3.83 s.

- Validation native Toga WinForms du focus réussie : après saisie puis changement
  de calendrier, le focus revient automatiquement dans le champ ; première
  Entrée = nouvelle analyse avec la nouvelle destination, seconde Entrée =
  confirmation.

- Pendant les contrôles de fermeture, le crash
  `Windows fatal exception: access violation` a été reproduit plusieurs fois.
  La trace implique notamment `toga_winforms/libs/proactor.py`,
  `pythonnet/__init__.py -> unload()` et `clr_loader/types.py`.

- Le crash a été reproduit sur `f244bd0` et sur l'ancien commit `c92aaab`.
  Certaines fermetures de `c92aaab` restent néanmoins propres, confirmant le
  caractère intermittent.

- Test d'isolation supplémentaire : sur `f244bd0`,
  `src/lumyn/modules/rendez_vous/ui.py` a été entièrement remplacé par la version
  de `c92aaab`. Le crash s'est encore produit. Le correctif de focus n'est donc
  pas retenu comme cause.

- Comparaison finale avec la vraie version stable 0.0.3 de `main`, commit
  `78093a0` : création d'un environnement Briefcase neuf, lancement de Lumyn puis
  fermeture immédiate sans interaction. Le même
  `Windows fatal exception: access violation` s'est produit avec la même famille
  de trace Toga WinForms / pythonnet / clr_loader.

- Le crash de fermeture est donc confirmé comme préexistant à Synapse, au
  correctif de focus et à la future 0.0.4. Il n'est pas considéré comme une
  régression introduite par `feature/synapse-rendez-vous`.

- Aucun impact fonctionnel ni corruption de données n'a été observé avant
  fermeture. La cause exacte reste à investiguer séparément côté
  Toga WinForms/pythonnet. Aucun correctif spéculatif appliqué.

- Version déclarée conservée à 0.0.3. Aucun merge dans `main` ni changement de
  version sans décision explicite de l'utilisatrice. La prochaine décision
  concerne la livraison de la future 0.0.4.

# 05/09/2026 — Audit final et préparation technique 0.0.4

- Reprise de e030674, lecture prioritaire des documents, audit du diff avec main
  78093a0. Aucun nouveau défaut bloquant mis en évidence dans le périmètre validé.
- Code Carnet/Synapse/Rendez-vous/Google conservé, aucun test supplémentaire ajouté.
- Investigation des sources Toga 0.5.6/pythonnet 3.1.0 et signalements amont :
  callbacks tardifs et finalisation restent des pistes, pas une cause prouvée.
  Aucun correctif sûr démontré sous Linux ; crash préexistant conservé et documenté.
- 137 tests Linux réussis avant et après préparation, syntaxe Python et diff
  vérifiés. Les validations Windows 137 tests, focus et Google réel sont conservées.
- pyproject.toml passé à 0.0.4 selon l'autorisation de préparer la livraison après
  audit ; CHANGELOG et documents synchronisés. Rapport docs/AUDIT_0.0.4.md ajouté.
- Recommandation : prête à fusionner avec le défaut de fermeture connu. Préparation
  d'une PR en brouillon ; aucune fusion, sortie de brouillon, release ou tag créé.
