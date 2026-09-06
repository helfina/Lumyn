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

**0.0.4 — fusionnée dans main**, PR #2, commit `0460534`.

Carnet, Synapse local, focus WinForms et Google Calendar réel sont validés.
La candidate finale a passé 137 tests sous Windows/Python 3.13 en 4.44 s.
Le crash intermittent de fermeture Windows préexiste à cette version ; il reste
connu et hors périmètre du chantier courant.

La branche `feature/google-reprise-recherche-lieux` renforce les reprises
Google/local et prépare un parcours externe : propositions sourcées, sélection,
confirmation puis ajout volontaire au Carnet. **Aucun fournisseur externe réel
n'est activé**, le panneau optionnel reste invisible dans l'application par défaut.
175 tests Linux réussis ; Windows/Google du nouveau lot restent à valider.
Version applicative inchangée, Android/OAuth seulement préparé.

Voir le [comparatif et les limites](docs/REPRISE_ET_RECHERCHE.md) et la
[procédure Android/OAuth](docs/ANDROID_OAUTH.md).

---

# Feuille de route

Voir [ROADMAP.md](ROADMAP.md). Prochaine étape : choisir le fournisseur et sa politique de données, puis intégrer et valider son adaptateur.

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


## Historique de livraison 0.0.4

L'audit depuis e030674 face à main 78093a0 précède la fusion de la PR #2.
Voir [CHANGELOG](CHANGELOG) et le [rapport historique](docs/AUDIT_0.0.4.md).
La PR du nouveau lot doit rester en brouillon jusqu'à autorisation explicite.
