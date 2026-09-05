# Contexte du projet Lumyn

## Identité et objectif

Lumyn est un assistant personnel modulaire destiné à réduire la charge mentale.
Synapse possède une première implémentation locale par règles pour les rendez-vous.
Chaque fonctionnalité répond à un problème réel ; simplicité et données locales
lorsque possible. Windows et Android sont les plateformes visées, en Python,
BeeWare, Toga et Briefcase. Le poste de développement utilise Python 3.13.

## Reprendre le travail

Lire d'abord PROJECT_STATE.md, ROADMAP.md, DEV_GUIDE.md et docs/TESTING.md.
Version 0.0.3 : le code contient un module Rendez-vous local et Google, un
calendrier filtrable. La branche feature/synapse-rendez-vous prépare 0.0.4 avec
le carnet et Synapse local ; elle dispose maintenant de 137 tests. Ne pas repartir de l'ancienne étape
« installer BeeWare » : elle est largement dépassée.

La reprise du 05/09/2026 a intégré trois fichiers de Lumyn.zip plus avancés que
le commit GitHub 0d35547. Le mode local du dépôt a été préservé en parallèle des
opérations Google apportées par l'archive.

## Méthode

Une seule prochaine étape ; ne supprimer aucune fonctionnalité.
Tester après chaque modification. Mettre à jour PROJECT_STATE.md, puis créer des
commits clairs et pousser une branche révisable. S'arrêter pour un choix important
non tranché par la documentation. Fournir des explications simples et, si besoin,
des commandes PowerShell directement utilisables.

## Limites à ne pas masquer

Les tests de cette reprise tournent sous Linux avec Toga Dummy et Google simulé.
Ils ne prouvent pas le rendu Windows/Android ni une synchronisation réelle.
Ne jamais committer identifiants Google, jetons ou données personnelles.
Ne pas utiliser le compte Google réel pour des tests automatiques.


## Point de reprise courant — validation complète du 05/09/2026

Travailler uniquement sur feature/synapse-rendez-vous, reprise de f244bd0.
0.0.3 est déjà fusionnée dans main ; version déclarée inchangée.
L'utilisatrice confirme 132 tests sous Windows/Python 3.13 (3.94 s), l'installation
des dépendances et la validation native WinForms du Carnet et de Synapse.
Favorite, site explicite non favori, VISIO/DOMICILE à Maison et ambiguïtés bloquées
sont validés. CRUD Google réel complet, absence de doublon, liaison et rappels
confirmés ; aucun Meet/lien visio automatique. Voir docs/TESTING.md.

Crash de fermeture Windows intermittent : `Windows fatal exception: access violation`
reproduit plusieurs fois dans `toga_winforms/libs/proactor.py` pendant le
déchargement `pythonnet` / `clr_loader`. Le même crash a été reproduit sur
`f244bd0` et sur l'ancien commit `c92aaab`, y compris sans interaction avec
l'application. Il persiste aussi avec le fichier `rendez_vous/ui.py` de
`c92aaab`, donc le correctif de focus n'est pas retenu comme cause.

Certaines fermetures restent propres. Aucun impact fonctionnel ou corruption de
données n'a été observé avant fermeture. Ne pas appliquer de correctif spéculatif
Toga/pythonnet/asyncio sans investigation dédiée.

Le correctif de focus après changement de calendrier via `on_change` et `focus()`
est validé. Il invalide le résumé précédent avant les deux Entrées. Les 137 tests
réussissent sous Linux et sous Windows/Python 3.13 ; validation native WinForms du
retour de focus réussie le 05/09/2026. Après changement de calendrier, la première
Entrée réanalyse avec la nouvelle destination et la seconde confirme.