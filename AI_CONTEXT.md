# Contexte du projet Lumyn

## Identité et objectif

Lumyn est un assistant personnel modulaire destiné à réduire la charge mentale.

Synapse possède actuellement une première implémentation locale par règles pour
les rendez-vous.

Chaque fonctionnalité doit répondre à un problème réel, en privilégiant la
simplicité et le stockage local lorsque cela est possible.

Les plateformes visées sont Windows et Android. Le projet utilise Python,
BeeWare, Toga et Briefcase. Le poste de développement Windows utilise
Python 3.13.

## Reprendre le travail

Lire d'abord :

- `PROJECT_STATE.md`
- `ROADMAP.md`
- `DEV_GUIDE.md`
- `docs/TESTING.md`

La version stable actuelle est **0.0.3**, déjà fusionnée dans `main`.

Elle contient notamment :
- les rendez-vous locaux ;
- l'intégration Google Calendar ;
- le calendrier filtrable.

La branche `feature/synapse-rendez-vous` déclare maintenant la candidate 0.0.4 avec :
- le Carnet ;
- Synapse local ;
- l'interprétation des rendez-vous ;
- la résolution des lieux via le Carnet ;
- les comportements VISIO et DOMICILE ;
- la gestion des ambiguïtés ;
- le parcours clavier analyse puis confirmation.

La branche dispose de **137 tests automatisés**.

Ne pas repartir de l'ancienne étape « installer BeeWare » : cette étape est
largement dépassée.

La reprise du 05/09/2026 a intégré trois fichiers provenant de `Lumyn.zip`,
plus avancés que le commit GitHub `0d35547`. Le fonctionnement local du dépôt a
été conservé parallèlement aux opérations Google apportées par cette archive.

## Méthode de travail

Avancer avec une seule prochaine étape claire à la fois.

Ne supprimer ni modifier une fonctionnalité existante sans nécessité démontrée.

Tester après chaque modification de code.

Mettre à jour la documentation quand l'état réel du projet change, en particulier :
- `PROJECT_STATE.md`
- `docs/TESTING.md`
- `ROADMAP.md`
- `JOURNAL.md`
- `README.md`
- ce fichier lorsque nécessaire.

Créer des commits clairs et pousser le travail sur une branche révisable.

S'arrêter lorsqu'une décision importante n'est pas déjà tranchée par la
documentation ou par l'utilisatrice.

Pour les manipulations locales, fournir des commandes PowerShell directement
utilisables.

## Sécurité et données

Ne jamais committer :
- identifiants Google ;
- jetons OAuth ;
- secrets ;
- données personnelles réelles inutiles au dépôt.

Ne jamais utiliser le compte Google réel dans les tests automatisés.

Les appels Google réels sont réservés aux validations manuelles explicitement
effectuées par l'utilisatrice.

Aucun fournisseur externe de recherche de lieux n'est actuellement activé.

## État de validation au 05/09/2026

### Tests automatisés

Sur `c92aaab`, l'utilisatrice a confirmé :

    132 passed in 3.94s

sous Windows/Python 3.13.

Après le correctif de focus publié dans `f244bd0`, la suite complète contient
**137 tests**.

Les 137 tests passent :
- sous Linux ;
- sous Windows/Python 3.13.

Validation Windows confirmée :

    137 passed in 3.83s

### Validation native Windows

L'application démarre et fonctionne avec Toga WinForms.

Le Carnet a été validé manuellement :
- création ;
- modification ;
- suppression ;
- plusieurs adresses ;
- adresse favorite.

Synapse a été validé manuellement pour :
- professionnel reconnu ;
- priorité au Carnet ;
- adresse favorite ;
- site explicite non favori ;
- `VISIO` ;
- `DOMICILE` ;
- utilisation de l'adresse Maison ;
- ambiguïtés bloquant la confirmation.

Le correctif de focus après changement de calendrier est également validé
nativement sous Windows.

Après saisie d'un rendez-vous puis changement de calendrier :
1. le focus revient automatiquement dans le champ de saisie ;
2. la première Entrée relance l'analyse avec la nouvelle destination ;
3. la seconde Entrée confirme.

Le correctif utilise `on_change` et `focus()` et invalide la préparation
précédente avant une nouvelle confirmation.

## Validation Google Calendar réelle

La validation manuelle réelle avec Google Calendar a confirmé :
- création d'un rendez-vous ;
- affichage dans Lumyn et Google Calendar ;
- modification d'un rendez-vous existant ;
- suppression ;
- déplacement d'un événement d'un calendrier Google vers un autre ;
- absence de doublon après déplacement ;
- cohérence de la liaison Lumyn / Google ;
- rappels présents ;
- absence de création automatique de lien Google Meet.

Les scénarios VISIO et DOMICILE ont également été validés avec Google réel.

Le navigateur Google Calendar a nécessité une fois un rafraîchissement manuel
pour afficher un événement déjà créé côté Google. Ce comportement n'est pas
considéré comme un défaut Lumyn.

## Crash de fermeture Windows intermittent

Un crash de fermeture Windows reste connu :

    Windows fatal exception: access violation

La trace observée implique notamment :

    toga_winforms/libs/proactor.py
    clr_loader/types.py
    pythonnet/__init__.py -> unload()

Environnement concerné :
- Python 3.13.3
- Briefcase 0.4.4
- toga-winforms 0.5.6
- pythonnet 3.1.0
- clr_loader 0.3.1

Le crash a été reproduit :
- sur `f244bd0` ;
- sur l'ancien commit `c92aaab` ;
- sur la version stable 0.0.3 de `main`, commit `78093a0`.

Le test sur `main` a été réalisé dans un environnement Briefcase neuf, avec
ouverture puis fermeture immédiate de Lumyn sans aucune interaction. Le même
`Windows fatal exception: access violation` s'est produit avec la même famille
de trace Toga WinForms / pythonnet / clr_loader.

Un test d'isolation avait également remplacé entièrement
`src/lumyn/modules/rendez_vous/ui.py` de `f244bd0` par la version de `c92aaab`.
Le crash s'est encore produit.

Le défaut préexistait donc :
- à Synapse ;
- au correctif de focus ;
- à la future 0.0.4.

Il n'est pas considéré comme une régression introduite par la branche
`feature/synapse-rendez-vous`.

Certaines fermetures restent parfaitement propres, ce qui confirme le caractère
intermittent du problème.

Aucun impact fonctionnel ni corruption de données n'a été observé avant la
fermeture.

La cause exacte reste à investiguer séparément côté Toga WinForms/pythonnet.
Ne pas appliquer de correctif spéculatif Toga/pythonnet/asyncio sans
investigation dédiée.

## Limites encore ouvertes

L'interprétation Synapse repose actuellement sur des règles et reste limitée aux
formulations couvertes.

Plusieurs dates concurrentes et certaines formulations comme
« la semaine prochaine » restent à fiabiliser.

Un lieu saisi littéralement n'est pas automatiquement une adresse vérifiée :
toujours relire le résumé avant confirmation.

L'historique de résolution et un fournisseur externe réel ne sont pas encore
développés.

Les ambiguïtés sont actuellement résolues par correction de la saisie ou du
Carnet, sans sélecteur de propositions dédié.

Les appels Google restent synchrones.

Il n'existe pas encore :
- de transaction atomique Google/local ;
- de garantie complète de reprise après double panne ;
- de gestion multiprocessus des écritures locales.

Android/APK/OAuth Android, les rappels locaux, les tâches et les notes restent
à développer ou à valider.

## Point de reprise courant

Travailler uniquement sur :

    feature/synapse-rendez-vous

La candidate **0.0.4** est déclarée dans pyproject.toml après l'audit autorisé
par l'utilisatrice depuis e030674, comparé à main 78093a0. main reste en 0.0.3.

Le Carnet, Synapse, les 137 tests, le correctif de focus natif Windows et le CRUD
Google réel sont validés. L'audit n'a pas identifié de nouveau défaut bloquant
dans ce périmètre ; code applicatif et tests inchangés. 137 tests Linux relancés
après la version et les documents, syntaxe Python/TOML/diff vérifiés.

Le crash de fermeture reste préexistant et non corrigé. La lecture des sources
Toga/pythonnet n'établit pas de correction sûre pour le cas utilisateur ; aucune
modification de boucle, de runtime ou d'allocateur appliquée. Voir
`docs/AUDIT_0.0.4.md` pour les preuves, hypothèses et diagnostic natif restant.

Recommandation : **prête à fusionner avec défaut connu**. La PR est préparée en
brouillon. Ne pas fusionner dans main, changer l'état final de PR, créer un tag
ou publier une release sans autorisation explicite. Aucun installateur 0.0.4
construit ou testé pendant cet audit. Prochaine étape : décision utilisateur.
