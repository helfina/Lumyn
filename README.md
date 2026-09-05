# 💡 Lumyn

> **Votre second cerveau numérique.**

Lumyn est un assistant personnel modulaire conçu pour réduire la charge mentale.

Le projet est né d'un besoin concret : capturer rapidement une information sans avoir à réfléchir à l'outil.

L'objectif n'est pas d'ajouter des dizaines de fonctionnalités.

L'objectif est de résoudre un problème réel à la fois.

---

# Pourquoi Lumyn ?

Les applications d'organisation demandent souvent de s'adapter à leur fonctionnement.

Lumyn suit la philosophie inverse.

> **C'est l'application qui s'adapte à l'utilisateur.**

Chaque fonctionnalité est développée parce qu'elle répond à un besoin réel rencontré au quotidien.

---

# Vision

Construire progressivement un assistant personnel capable de :

- 📅 gérer les rendez-vous ;
- 📝 capturer des notes rapidement ;
- ✅ organiser les tâches ;
- 📂 retrouver facilement les informations ;
- 🧠 réduire la charge mentale.

---

# Première version

Le premier objectif est volontairement simple.

Créer un module permettant de :

- créer un rendez-vous rapidement ;
- ajouter automatiquement plusieurs rappels ;
- synchroniser l'événement avec Google Agenda.

---

# Philosophie du projet

Lumyn suit quelques règles simples :

- une fonctionnalité = un problème résolu ;
- simplicité avant complexité ;
- développement par petites versions ;
- documentation complète ;
- code propre et maintenable.

---

# Technologies

Le projet est développé avec :

- Python
- BeeWare
- Toga
- Briefcase
- Git
- GitHub

---

# Documentation

L’état de référence est décrit dans PROJECT_STATE.md.

| Document | Rôle |
|----------|------|
| PROJECT_STATE.md | État actuel du projet |
| ROADMAP.md | Versions prévues |
| JOURNAL.md | Journal des séances |
| DECISIONS.md | Décisions importantes |
| DEV_GUIDE.md | Méthode de développement |
| AI_CONTEXT.md | Mémoire du projet |
| docs/ARCHITECTURE.md | Architecture |
| docs/HISTORY.md | Histoire du projet |
| docs/IDEAS.md | Idées futures |

---

# État du projet

Version préparée sur cette branche :

**0.0.4 — candidate, non publiée**

La version 0.0.3 gère les rendez-vous locaux et Google, validés sous Windows avec
Google réel le 05/09/2026. Sur `feature/synapse-rendez-vous`, la candidate 0.0.4 ajoute
le Carnet et Synapse local, validés sous Windows/Google réel le 05/09/2026.

Les 137 tests passent sous Linux et sous Windows/Python 3.13. Le correctif de focus
après changement de calendrier est également validé nativement sous Windows.
Le Carnet, Synapse et le CRUD Google réel sont validés.

Un crash de fermeture Windows intermittent reste connu. Il a été reproduit sur
`feature/synapse-rendez-vous`, sur l'ancien commit `c92aaab`, ainsi que sur la
version stable 0.0.3 de `main` au commit `78093a0`.

Sur `main`, le test a été effectué dans un environnement Briefcase neuf, avec
ouverture puis fermeture immédiate de Lumyn sans interaction. Le même
`Windows fatal exception: access violation` a été observé dans le chemin
Toga WinForms / pythonnet / clr_loader.

Le défaut préexistait donc à Synapse et au correctif de focus ; il n'est pas
considéré comme une régression introduite par la future 0.0.4. La cause exacte
reste à investiguer séparément. Aucun impact fonctionnel ou corruption de données
n'a été observé avant fermeture.

Android reste à valider.

---

# Feuille de route

Voir [ROADMAP.md](ROADMAP.md). Prochaine étape : autoriser la fusion puis décider de la publication 0.0.4.

---

# Auteur

Développé par **helfina**.

Avec l'assistance de ChatGPT comme partenaire de développement.
## Essayer la saisie

- `Dentiste demain 14h30 à Lorient`
- `CAF dans 15 jours à 10h`
- `Contrôle technique 3 octobre à 10h`

Relire le résumé puis confirmer. La destination « Sur cet appareil uniquement »
conserve un rendez-vous local sans rappel automatique. Un calendrier Google
accessible en écriture permet les opérations liées et les rappels J-1 / H-1.

## Tests

Voir [docs/TESTING.md](docs/TESTING.md) pour les commandes PowerShell et les
vérifications manuelles restantes. Les tests automatiques n'utilisent pas de
compte Google réel.


## Préparation de livraison 0.0.4

Audit depuis e030674 face à main 78093a0 : aucune régression bloquante mise en
évidence dans les parcours validés, 137 tests Linux relancés. Version et documents
mis à jour sans changement applicatif. Voir [CHANGELOG](CHANGELOG) et le
[rapport d'audit](docs/AUDIT_0.0.4.md).

**Recommandation : prête à fusionner avec défaut connu.** Le crash intermittent de
fermeture Windows préexistait à cette branche et reste non corrigé ; aucune cause
précise n'est démontrée. Il ne doit pas être présenté comme résolu. La PR reste en
brouillon et aucune publication ni fusion n'est effectuée par cet audit.
