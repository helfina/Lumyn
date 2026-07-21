# Architecture de Lumyn

## Structure actuelle

Lumyn/
├── README.md
├── ROADMAP.md
├── JOURNAL.md
├── DECISIONS.md
├── PROJECT_STATE.md
├── DEV_GUIDE.md
├── AI_CONTEXT.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── HISTORY.md
│   └── IDEAS.md
├── src/
├── tests/
└── assets/

## Rôle des éléments

- README.md : présentation publique du projet.
- ROADMAP.md : étapes et versions prévues.
- JOURNAL.md : résumé de chaque séance.
- DECISIONS.md : décisions techniques et leurs raisons.
- PROJECT_STATE.md : état actuel et prochaine action.
- DEV_GUIDE.md : règles de développement.
- AI_CONTEXT.md : résumé permettant de reprendre le projet avec une IA.
- docs/ : documentation détaillée.
- src/ : code source Python.
- tests/ : tests automatisés.
- assets/ : logo, images et captures d'écran.

## Architecture fonctionnelle prévue

Lumyn
├── Interface utilisateur
├── Modules du quotidien
│   ├── Rendez-vous
│   ├── Notes
│   ├── Tâches
│   └── Futurs modules
├── Stockage local
└── Synapse
    └── Futur moteur intelligent

Cette architecture évoluera progressivement. Aucun module inutile ne doit être ajouté à l'avance.
