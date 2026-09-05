# Architecture de Lumyn

## Objectif

Ce document décrit l'organisation technique du projet Lumyn.

L'architecture doit rester simple, lisible, modulaire et évolutive.

Chaque partie du projet possède une seule responsabilité.

---

# Structure actuelle

```text
Lumyn/
│
├── .github/
├── .venv/
├── assets/
├── docs/
├── logs/
├── src/
│   └── lumyn/
│       ├── app.py
│       ├── __init__.py
│       ├── __main__.py
│       │
│       ├── modules/
│       │   ├── __init__.py
│       │   │
│       │   └── rendez_vous/
│       │       ├── __init__.py
│       │       ├── ui.py
│       │       ├── gestion.py
│       │       └── analyseur.py
│       │
│       └── resources/
│
├── tests/
│
├── README.md
├── PROJECT_STATE.md
├── ROADMAP.md
├── JOURNAL.md
├── DECISIONS.md
├── DEV_GUIDE.md
├── AI_CONTEXT.md
└── pyproject.toml
```

---

# Principe d'organisation

Lumyn est organisé par **modules**.

Chaque module représente une fonctionnalité complète de l'application.

Exemples futurs :

```text
modules/
├── rendez_vous/
├── notes/
├── taches/
├── courses/
├── budget/
├── sante/
└── synapse/
```

Chaque module est indépendant.

---

# Organisation d'un module

Chaque module possède sa propre structure.

Exemple :

```text
rendez_vous/
├── ui.py
├── gestion.py
├── analyseur.py
└── __init__.py
```

## ui.py

Contient l’interface graphique et, dans le prototype actuel, le contrôleur des
opérations local/Google.

Responsabilités :

- affichage ;
- boutons ;
- champs de saisie ;
- disposition.

La validation textuelle reste dans gestion.py ; l’orchestration des créations,
modifications et tentatives de restauration est actuellement dans ui.py.
Cette séparation pourra être améliorée après la validation du prototype.

---

## gestion.py

Contient la logique métier.

Responsabilités :

- validation ;
- préparation des données ;
- création du rendez-vous ;
- communication avec les autres modules.

---

## analyseur.py

Comprend le texte écrit par l'utilisateur.

Exemples :

- mardi ;
- demain ;
- 17 juillet ;
- 14h30 ;
- lieu ;
- titre.

Il ne crée jamais un rendez-vous.

Il extrait uniquement les informations.

---

## app.py

Le fichier `app.py` ne contient jamais de logique métier.

Il démarre Lumyn et charge les modules.

---

# Philosophie

Chaque fichier possède une seule responsabilité.

Lorsqu'une fonctionnalité grandit, on ajoute un nouveau fichier dans son module plutôt que de créer un fichier géant.

---

# Évolution

Une nouvelle fonctionnalité = un nouveau dossier dans `modules`.

Exemple :

```text
modules/
├── rendez_vous/
├── notes/
├── taches/
└── synapse/
```

Ainsi, chaque fonctionnalité évolue indépendamment.

---

# Règles importantes

- Une fonctionnalité = un module.
- Une responsabilité = un fichier.
- Le code doit être simple à retrouver.
- L'architecture ne doit pas être compliquée avant d'être nécessaire.
- Chaque nouvelle fonctionnalité doit s'intégrer à cette architecture.
## Fichiers complémentaires présents (05/09/2026)

- modele.py et resultat.py : dictionnaires structurés de rendez-vous et résultat.
- stockage.py : JSON local, migration des identifiants et écriture atomique.
- agenda_google.py : OAuth, service partagé, pagination et opérations Google.
- calendrier_ui.py : HTML du mois, navigation et préférences de filtres.
- tests/ : analyse, stockage, interface Toga Dummy et appels Google simulés.

Le stockage local se trouve dans `~/.lumyn/rendez_vous.json`. Il ne gère pas
les écritures concurrentes de plusieurs processus. Google et le fichier local
ne forment pas une transaction atomique ; les tentatives de restauration
restent limitées en cas de plusieurs pannes simultanées.
