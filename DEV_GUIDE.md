# Guide de développement de Lumyn

## Objectif

Ce document décrit la méthode de développement du projet.

Il permet de garder une façon de travailler cohérente, même après plusieurs mois.

---

# Philosophie

Lumyn est développé pour résoudre des problèmes réels.

Chaque fonctionnalité doit apporter une valeur concrète.

La simplicité est toujours préférée à la complexité.

---

# Méthode

Une seule étape principale à la fois.

Avant de développer :

- comprendre le problème ;
- définir une solution simple ;
- seulement ensuite écrire le code.

---

# Cycle de travail

Chaque séance suit le même déroulement.

## 1. Lire

- PROJECT_STATE.md
- ROADMAP.md

## 2. Développer

Une seule fonctionnalité.

## 3. Tester

Vérifier que tout fonctionne.

## 4. Documenter

Mettre à jour si nécessaire :

- JOURNAL.md
- PROJECT_STATE.md
- DECISIONS.md

## 5. Git

Créer un commit clair.

Faire un push vers GitHub.

---

# Style de code

Le code doit être :

- simple ;
- lisible ;
- commenté lorsque nécessaire.

Les noms des variables et fonctions doivent être explicites.

---

# Documentation

Chaque nouvelle fonctionnalité importante doit être documentée.

Une décision importante doit être ajoutée dans DECISIONS.md.

---

# Règles Git

Un commit = une seule modification logique.

Toujours utiliser un message explicite.

Exemple :

Ajout du module de création de rendez-vous

Éviter :

Modifications

---

# Sécurité

Ne jamais enregistrer :

- mots de passe ;
- clés API ;
- données personnelles.

---

# Objectif final

Construire progressivement un assistant personnel fiable, simple, évolutif et agréable à maintenir.