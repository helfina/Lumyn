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

Version actuelle :

**0.0.3**

Le prototype gère les rendez-vous locaux et Google et dispose de 57 tests automatisés.
Le rendu natif Windows/Android et la connexion Google réelle restent à valider.

---

# Feuille de route

Version 0.1 :

- première application BeeWare ;
- première fenêtre ;
- première interface.

Version 0.2 :

- création rapide de rendez-vous.

Version 0.3 :

- synchronisation Google Agenda.

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
