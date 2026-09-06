# Contexte du projet Lumyn

## Décision Geoapify — 06/09/2026

Sur `feature/google-reprise-recherche-lieux`, Geoapify est le premier fournisseur
structuré, offre gratuite seulement. Activation par `GEOAPIFY_API_KEY` ou
`LUMYN_GEOAPIFY=1`; aucune clé dans Git. Recherche volontaire et autocomplétion
Toga s'exécutent hors thread UI avec délai/timeout, limites et réponses périmées
ignorées. IA/web reste désactivée.

La conservation durable d'une réponse Geoapify n'est pas assez clairement autorisée
par les conditions publiques : propositions non persistables, saisie manuelle du
Carnet conservée. 188 tests Linux passent. `briefcase create android` a
été tenté réellement mais arrêté avant génération faute de JDK complet et après
expiration du téléchargement. Voir les deux documents techniques.


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

La version stable actuelle est **0.0.4**, fusionnée dans `main` par la PR #2
au commit `0460534`. Le socle 0.0.3 décrit ci-dessous reste présent.

Elle contient notamment :
- les rendez-vous locaux ;
- l'intégration Google Calendar ;
- le calendrier filtrable.

La branche historique `feature/synapse-rendez-vous`, désormais fusionnée, a ajouté :
- le Carnet ;
- Synapse local ;
- l'interprétation des rendez-vous ;
- la résolution des lieux via le Carnet ;
- les comportements VISIO et DOMICILE ;
- la gestion des ambiguïtés ;
- le parcours clavier analyse puis confirmation.

La référence 0.0.4 dispose de **137 tests automatisés**. Le lot courant en compte **175**.

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

Les ambiguïtés locales sont résolues par correction de la saisie ou du Carnet.
Un sélecteur externe optionnel est maintenant testé ; il reste inactif par défaut.

Les appels Google restent synchrones.

Il n'existe pas encore :
- de transaction atomique Google/local ;
- de garantie complète de reprise après double panne ;
- de gestion multiprocessus des écritures locales.

Android/APK/OAuth Android, les rappels locaux, les tâches et les notes restent
à développer ou à valider.

## Étape préparatoire du 06/09/2026

**0.0.4 est fusionnée dans main**, PR #2, commit `0460534`.
La candidate finale a été validée par l'utilisatrice : **137 tests sous Windows /
Python 3.13 en 4.44 s**, Carnet, Synapse, focus WinForms et Google Calendar réel.
Ces validations concernent la 0.0.4 ; elles ne valent pas validation native du lot suivant.

Travail courant : `feature/google-reprise-recherche-lieux`, issue de ce merge.
Version applicative conservée à **0.0.4**, aucune nouvelle release préparée.
Le travail déjà présent dans le workspace a été conservé et complété.

- Reprise de CREATE Google par identifiant réservé sur disque ; DELETE partiel
  réessayable sans recréer l'événement ; restaurations UPDATE/MOVE mieux signalées.
- Parcours optionnel de propositions sourcées, choix explicite puis confirmation,
  ajout volontaire au Carnet et choix d'une fiche similaire avant ajout d'adresse.
- Fournisseur structuré puis repli IA/web autorisé séparément : architecture et
  interface testées par injection. Cette étape précédait le choix Geoapify ; le
  fournisseur est maintenant optionnel et reste désactivé sans configuration.
- Cette étape préparatoire comptait **175 tests Linux réussis**. L’intégration
  Geoapify réalisée ensuite porte la suite courante à **188 tests**. Validation
  Windows et Google réelle du nouveau lot encore à effectuer.
- Comparatif et limites : [docs/REPRISE_ET_RECHERCHE.md](docs/REPRISE_ET_RECHERCHE.md).
  Android/OAuth : [docs/ANDROID_OAUTH.md](docs/ANDROID_OAUTH.md), préparation uniquement.
- Arrêt avant le choix du fournisseur, des clés, du budget et de la politique de
  données. Nouvelle PR à conserver en brouillon. Aucune fusion ni publication.
- Crash Windows préexistant : hors périmètre, aucun changement de runtime.
