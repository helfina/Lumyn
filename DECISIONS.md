# Décisions du projet Lumyn

---

# 21/07/2026

## Nom du projet

### Décision

Le projet portera le nom **Lumyn**.

### Pourquoi ?

Le nom évoque la lumière, la clarté et un assistant qui aide à réduire la charge mentale. Il n'est pas limité à une seule fonctionnalité et pourra accompagner l'évolution du projet.

---

## Moteur intelligent

### Décision

Le futur moteur intelligent s'appellera **Synapse**.

### Pourquoi ?

Synapse représentera l'intelligence de Lumyn et permettra de relier les informations entre elles sans être le nom de l'application.

---

## Vision

### Décision

Lumyn sera un assistant personnel modulaire.

### Pourquoi ?

L'objectif est de résoudre progressivement des problèmes réels du quotidien plutôt que de créer une application qui essaie de tout faire dès le départ.

---

## Première fonctionnalité

### Décision

Commencer par la création rapide de rendez-vous avec rappels automatiques.

### Pourquoi ?

Ce problème est vécu au quotidien et permettra de construire une première version simple, utile et concrète.

---

## Technologies

### Décision

Le développement commencera avec :

- Python
- BeeWare
- Toga
- Briefcase

### Pourquoi ?

Ces technologies permettent de développer une application Windows et Android à partir d'une même base de code Python.

---

## Méthode de développement

### Décision

Le projet sera développé par petites versions successives.

### Pourquoi ?

Cette méthode permet de rester motivé, de limiter la complexité et d'obtenir rapidement des résultats utilisables.

---
## 21/07/2026

### Structure BeeWare

La structure générée par BeeWare est conservée pour le moment.

Une éventuelle réorganisation sera décidée uniquement après avoir compris son fonctionnement.

## 22/07/2026

### Construction progressive de l'interface

Chaque nouveau composant graphique sera appris individuellement avant de construire des écrans plus complexes.

L'objectif est de comprendre chaque concept avant d'en introduire un nouveau.

## 05/09/2026 — Carnet et Synapse local

- Poursuivre uniquement `feature/synapse-rendez-vous` ; conserver 0.0.3 tant que
  la future 0.0.4 n'est pas validée. Ne pas modifier main.
- Garder le parseur déterministe comme validation et repli. Synapse local utilise
  des règles explicites ; aucun LLM ou service distant ajouté.
- Respecter l'intention, puis le carnet personnel. Un site explicite prime sur la
  favorite ; plusieurs fiches/adresses ou un qualificatif inconnu bloquent le choix.
- VISIO/DOMICILE emploient Maison pour le champ Google location, avec suffixe du
  mode dans le titre. Pas de lien visio récurrent, ni adresse professionnelle
  substituée au domicile. Le téléphone ne reçoit pas d'adresse physique implicite.
- Une seule Maison, alias dédupliqués et une favorite au maximum à l'enregistrement.
  Les données anciennes conflictuelles demandent correction sans effacement.
- Conserver la confirmation : première Entrée pour le résumé, seconde Entrée
  pour enregistrer la même saisie et le même calendrier.
- Préparer seulement l'interface d'un fournisseur externe. Aucun fournisseur
  choisi, aucune adresse importée ni fiche enregistrée sans intervention explicite.
- Ne pas modifier l'arrêt WinForms/pythonnet sans reproduction du crash Windows.
