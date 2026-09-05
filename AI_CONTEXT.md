# Contexte du projet Lumyn

## Identité et objectif

Lumyn est un assistant personnel modulaire destiné à réduire la charge mentale.
Synapse est le nom envisagé pour un futur moteur intelligent, pas encore développé.
Chaque fonctionnalité répond à un problème réel ; simplicité et données locales
lorsque possible. Windows et Android sont les plateformes visées, en Python,
BeeWare, Toga et Briefcase. Le poste de développement utilise Python 3.13.

## Reprendre le travail

Lire d'abord PROJECT_STATE.md, ROADMAP.md, DEV_GUIDE.md et docs/TESTING.md.
Version 0.0.3 : le code contient un module Rendez-vous local et Google, un
calendrier filtrable et 57 tests. Ne pas repartir de l'ancienne étape
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
