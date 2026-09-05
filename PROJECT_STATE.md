# État actuel de Lumyn

## Version et phase

0.0.3 — prototype Rendez-vous en cours de stabilisation (05/09/2026).
Le prototype a été validé manuellement sous Windows avec Google Calendar réel
le 05/09/2026 pour les opérations détaillées ci-dessous. Android et la compilation
APK restent à valider ; cette validation ne constitue pas une livraison empaquetée.

## Sources de cette reprise

- Dépôt `helfina/Lumyn`, base `0d35547` du 03/09/2026.
- Archive Lumyn.zip : trois fichiers plus avancés (`agenda_google.py`,
  `calendrier_ui.py`, `ui.py`), intégrés dans une branche de travail.
- Lecture du code applicatif, tests, configuration et documentation des deux versions.
  Les environnements Windows générés et caches ne constituent pas le code à maintenir.
- Les identifiants Google présents dans l'archive ne sont pas copiés dans le dépôt.

## Fonctionnalités présentes

- Analyse d'un rendez-vous, informations manquantes et incohérences jour/date.
- Confirmation explicite avant enregistrement ; changement de texte ou de calendrier
  après analyse impose une nouvelle analyse.
- Dates numériques et écrites, jours, aujourd'hui/demain/après-demain, dans N jours.
- Lieu introduit par « à » et conservation de la casse des noms/acronymes.
- Création, modification et suppression locales avec identifiants stables.
- Choix explicite « Sur cet appareil uniquement » ou calendrier Google.
  Le mode local reste disponible sans connexion, sans notification automatique locale.
- Création, modification, déplacement et suppression des événements Google liés.
- Durée Google conservée à 60 minutes par défaut ; rappels à J-1 et H-1.
- Calendrier mensuel, couleurs, filtres persistants, navigation et défilement.

## Corrections de cette séance

- Un fichier local illisible n'est plus considéré comme une liste vide.
- Écriture dans un fichier temporaire puis remplacement atomique ; protection
  de l'ancien contenu si la sérialisation ou le remplacement échoue.
- Refus des heures invalides ou multiples (exemple : 14:99).
- Gestion du prochain 29 février lorsque l'année n'est pas indiquée.
- Lieu affiché avant confirmation et rechargé lors d'une modification.
- Une saisie de lieu seul ne devient pas un titre de rendez-vous.
- Tentative de restauration Google aussi si l'écriture locale lève une exception
  lors d'une modification liée.
- Un événement d'un autre mois n'est plus affiché au même numéro de jour.

## Vérification automatique effectuée

- À l'origine : 1 test purement arithmétique, réussi dans les deux versions.
- Après les modifications : 57 tests réussis sous Linux / Python 3.12.13,
  Toga Dummy 0.5.6. La commande `python -m pytest -q` est relancée après chaque
  modification ; les nouveaux tests de régression ont d'abord reproduit les défauts.
- Tests : analyse, stockage réel dans un dossier temporaire, pannes d'écriture,
  contrôleur Toga avec backend de test, cycle local, liaison Google simulée,
  pagination, fuseaux horaires, rappels et HTML du calendrier.
- Accès réseau bloqué pendant les tests automatiques ; Google y reste simulé.
- Syntaxe de tous les fichiers Python vérifiée.

## Validation manuelle réelle — 05/09/2026

Résultats des essais effectués sous Windows et confirmés par l'utilisatrice sur
la branche `codex/lumyn-fiabilisation-rendez-vous`. Ils complètent les 57 tests
automatiques ; ils ne proviennent pas d'une simulation Google.

- `briefcase dev` démarre correctement sous Windows.
- Aucun `ResourceWarning` SSL observé au lancement.
- Création d'un rendez-vous dans Google Calendar : OK.
- Affichage du rendez-vous dans Lumyn et Google Calendar : OK.
- Modification d'un rendez-vous existant : OK, effet immédiat observé.
- Suppression d'un rendez-vous : OK, effet immédiat observé.
- Déplacement entre deux calendriers Google : OK.
- Aucun doublon observé après déplacement.
- Liaison entre Lumyn et Google cohérente pendant les opérations testées.

L'affichage Windows et l'utilisation de Google réel sont donc validés pour ce
périmètre. Les détails et les contrôles non confirmés figurent dans docs/TESTING.md.
Les tests automatiques ont été relancés après cette mise à jour documentaire :
57 réussis. Aucune fonctionnalité ni aucun test modifié.

## Limites connues et validations restantes

- Android, compilation APK et parcours OAuth initial/renouvellement des jetons
  non confirmés par ce compte rendu. La connexion Google réelle sous Windows
  a bien été utilisée pour les opérations validées.
- Les appels Google sont synchrones : une connexion lente peut figer l'interface.
- Le stockage n'est pas prévu pour plusieurs processus écrivant simultanément.
- En cas de panne Google ET locale, les tentatives de restauration ne garantissent
  pas la cohérence. Une stratégie de reprise persistante reste à concevoir.
- Les événements Google sur plusieurs jours ne sont pas déployés sur chaque case.
- L'analyse reste fondée sur des règles : plusieurs dates concurrentes, certaines
  formulations ambiguës et « la semaine prochaine » ne sont pas fiabilisées.
  Toujours relire la date et le titre proposés avant confirmation.
- Les rappels locaux, tâches, notes et Synapse ne sont pas développés.

## Prochaine étape unique

La validation Windows/Google décrite ci-dessus est terminée. Attendre les
instructions de l’utilisatrice avant toute nouvelle étape. La PR reste en brouillon
et ne doit être ni fusionnée ni sortie du brouillon sans son accord explicite.

## Choix à demander avant une évolution importante

Ne pas décider seul d'une synchronisation automatique en arrière-plan, de règles
  de résolution des conflits ou d'une nouvelle architecture Android/OAuth.
Le présent travail reste limité à la fiabilisation du module existant et à la
  saisie structurée prévue dans la documentation.
