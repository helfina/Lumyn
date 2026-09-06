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


## 05/09/2026 — Préparation autorisée de 0.0.4 après audit

L'instruction de finalisation autorise le changement de version si l'audit est
satisfaisant. Aucun nouveau défaut bloquant identifié dans les parcours validés :
version 0.0.4 préparée sur la branche, main inchangée. Le crash de fermeture
préexistant reste connu ; aucune correction native sûre n'est démontrée.
Ne pas remplacer l'absence de diagnostic par un contournement de shutdown.
Recommandation de fusion avec défaut documenté ; décision finale de fusion,
statut de PR et publication réservés à l'utilisatrice.


## 06/09/2026 — Après fusion, reprises et recherche optionnelle

La PR #2 est fusionnée (0460534). Les consignes de branche/candidate du 05/09 sont
historiques. Développement sur feature/google-reprise-recherche-lieux uniquement.

Conserver 0.0.4 et le socle local. Réserver l'identifiant CREATE avant l'appel
Google et vérifier tout conflit ; une suppression Google suivie d'une panne
locale ne recrée plus un événement. Le modèle reste à un seul écrivain et ne
prétend pas assurer une transaction distribuée ni toutes les doubles pannes.

Priorité Maison/Carnet ; recherche structurée explicitement déclenchée ; repli
IA/web séparément autorisé. Sélection et confirmation distinctes, sauvegarde
Carnet volontaire, rapprochement de fiches confirmé. Aucune clé ou donnée réelle.

Décisions en attente : fournisseur, conditions de conservation Carnet, budget,
clés personnelles ou serveur ; voir docs/REPRISE_ET_RECHERCHE.md. Aucun service
réel activé avant ce choix. Avant activation : adaptateur borné et travail réseau
hors thread UI. Android/OAuth natif exige une validation séparée sur appareil et
un choix de configuration Google Cloud ; seule la procédure est préparée.
Crash Windows exclu, aucune fusion/release/changement final de PR sans accord.
