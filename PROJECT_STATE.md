# État actuel de Lumyn

## Version et branche — 05/09/2026

Version déclarée : **0.0.3**, stable et fusionnée dans main avant cette reprise.
La version **0.0.4 Carnet de lieux + Synapse Rendez-vous** est en préparation sur
`feature/synapse-rendez-vous`, reprise au commit `3f0f119` après les trois commits
Carnet (`81ab732`, `ab3cd5e`, `3f0f119`). Cette séance ne modifie ni ne fusionne main.
La version dans pyproject.toml reste 0.0.3 en attendant la validation native.

## Fonctionnalités présentes

- Rendez-vous locaux et Google : création, modification, suppression et déplacement
  liés, identifiants stables, durée Google de 60 minutes, rappels J-1/H-1.
- Calendrier mensuel, couleurs, filtres persistants et navigation.
- Carnet local : fiches, alias, profession, catégorie, notes, visio, plusieurs
  adresses et adresse favorite ; navigation Rendez-vous/Carnet conservée.
- Synapse local sépare titre, métier, date, heure, mode et lieu, puis utilise le
  parseur et la validation déterministes existants. Aucun modèle distant.
- Priorité à l'intention explicite, puis au carnet. Un site indiqué prime sur la
  favorite ; un qualificatif inconnu ou plusieurs correspondances demandent une
  précision. Aucune adresse inventée ni fiche enregistrée automatiquement.
- VISIO et DOMICILE utilisent l'adresse de la fiche Maison et ajoutent le mode au
  titre Google. Aucun lien récurrent de visioconférence n'est généré.
- Entrée prépare le résumé ; une seconde Entrée confirme si la saisie et le
  calendrier sont inchangés. Les boutons existants restent disponibles.
- Interface de fournisseur externe définie et testée avec des doubles, inactive
  dans l'application. Les propositions exigent une sélection explicite.

## Fiabilisation du carnet

Validation du nom, des alias et des adresses, copies profondes, une seule favorite
par fiche et une seule fiche Maison lors d'un enregistrement. Maison, domicile et
chez moi identifient cette même fiche. Les anciens champs inconnus sont conservés.
Les conflits anciens restent visibles pour correction et bloquent la résolution
ambiguë. Un fichier illisible n'est jamais remplacé silencieusement par une liste
vide. Le remplacement atomique du JSON et le CRUD existant sont conservés.

## Vérifications de cette reprise

- Base : **78 tests réussis**, résultat reproduit avant développement.
- Après développement et documentation : **132 tests réussis**, Linux/Python 3.12,
  Toga Dummy ; 54 cas supplémentaires. Suite relancée après les modifications.
- Couverture : carnet, données anciennes et pannes, expressions Synapse, priorités
  et ambiguïtés, Maison, parcours clavier et modification Google simulée, recherche
  externe inactive. Aucun compte Google réel utilisé par ces tests.
- Données des rendez-vous, du carnet et préférences redirigées dans les dossiers
  temporaires. Connexions externes bloquées ; loopback autorisé pour asyncio Windows.
- Pillow explicité dans les dépendances de test pour le backend Toga Dummy.

## Validation manuelle réelle — 05/09/2026

Résultats des essais effectués sous Windows et confirmés par l'utilisatrice sur
la branche `codex/lumyn-fiabilisation-rendez-vous`. Ils complètent les 57 tests
automatiques ; ils ne proviennent pas d'une simulation Google.

- `briefcase dev` démarre correctement sous Windows.
- Aucun `ResourceWarning` SSL observé au lancement.
- Création d'un rendez-vous dans Google Calendar : OK.
- Affichage du rendez-vous dans Lumyn et Google Calendar : OK.
- Modification d'un rendez-vous existant : OK, effet immédiat observé.
- Suppression d'un rendez-vous : OK, effet immédiat observé.
- Déplacement entre deux calendriers Google : OK.
- Aucun doublon observé après déplacement.
- Liaison entre Lumyn et Google cohérente pendant les opérations testées.

L'affichage Windows et l'utilisation de Google réel sont donc validés pour ce
périmètre. Les détails et les contrôles non confirmés figurent dans docs/TESTING.md.
La mise à jour documentaire historique avait été vérifiée avec 57 tests réussis.


## Validation Carnet rapportée par l'utilisatrice — 05/09/2026

Sur la base `3f0f119` : 78 tests réussis sous Windows/Python 3.13, CRUD du carnet
et navigation entre les deux écrans validés manuellement. Cette validation ne
couvre pas encore l'intégration Synapse ajoutée pendant cette séance.

## Limites connues

- Un crash de fermeture Windows (access violation, déchargement pythonnet,
  WinForms/proactor) a été signalé, puis le lancement suivant a réussi.
  Non reproduisible dans cet environnement Linux ; aucune correction spéculative.
  Protocole de diagnostic dans docs/TESTING.md.
- Interprétation par règles, limitée aux formulations couvertes ; plusieurs dates
  concurrentes et « la semaine prochaine » restent à fiabiliser. Un lieu saisi
  littéralement n'est pas une adresse vérifiée. Toujours relire le résumé.
- Historique et fournisseur externe réel non développés ; résolution des ambiguïtés
  par correction de la saisie ou du carnet, sans sélecteur de propositions dédié.
- Appels Google synchrones ; pas de transaction atomique Google/local, ni de
  garantie de reprise après double panne, ni d'écritures locales multiprocessus.
- Android/APK/OAuth Android, rappels locaux, tâches et notes restent à développer
  ou valider ; pas de livraison 0.0.4 annoncée.

## Prochaine étape et décisions réservées

Valider cette branche sous Windows avec les scénarios Synapse de docs/TESTING.md,
puis décider de la livraison 0.0.4. Aucun merge ni changement d'état de PR pendant
cette reprise. Demander le choix de l'utilisatrice avant un fournisseur externe
réel, une synchronisation en arrière-plan ou une nouvelle architecture OAuth.
