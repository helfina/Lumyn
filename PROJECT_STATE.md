# État actuel de Lumyn

## Version et branche — 05/09/2026

Version déclarée : **0.0.3**, stable et fusionnée dans main avant cette reprise.
La version **0.0.4 Carnet de lieux + Synapse Rendez-vous** est en préparation sur
`feature/synapse-rendez-vous`, reprise au commit `3f0f119` après les trois commits
Carnet (`81ab732`, `ab3cd5e`, `3f0f119`). Cette séance ne modifie ni ne fusionne main.
La version dans pyproject.toml reste 0.0.3 en attendant une décision de livraison.

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
et navigation entre les deux écrans validés manuellement. La validation complète de Synapse sur c92aaab est désormais rapportée ci-dessous.

## Limites connues

- Crash de fermeture Windows intermittent : `Windows fatal exception: access violation`
  observé dans `toga_winforms/libs/proactor.py` pendant le déchargement de
  `pythonnet` / `clr_loader`. Le problème a été reproduit plusieurs fois sur
  `f244bd0`, mais aussi sur l'ancien commit `c92aaab`.
- Le crash se produit même sans interaction avec Lumyn et a également été reproduit
  après remplacement complet de `rendez_vous/ui.py` par la version de `c92aaab`.
  Le correctif de focus n'est donc pas identifié comme cause.
- Certaines fermetures restent parfaitement propres : le défaut est intermittent.
  Aucun impact sur les données ou le fonctionnement de Lumyn n'a été observé avant
  la fermeture. Aucun correctif spéculatif Toga/pythonnet n'est appliqué pour le moment.
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

Le correctif de focus après changement de calendrier est désormais validé
nativement sous Windows. Les 137 tests passent également sous Windows/Python 3.13
en 3.83 s. Les scénarios Synapse et le CRUD Google réel sont validés.

La branche feature/synapse-rendez-vous peut maintenant passer à la décision de
livraison 0.0.4. Aucun fournisseur externe n'est activé. Ne pas fusionner ni
changer la version sans décision explicite de l'utilisatrice.

## Dernière validation et correctif de focus — 05/09/2026

Base c92aaab : **132 tests réussis sous Windows/Python 3.13 en 3.94 s** après
installation des dépendances. Validation native WinForms : démarrage, navigation,
CRUD Carnet, multi-adresses et favorite. Synapse : DOMICILE local à Maison,
professionnel et favorite Lorient, site explicite secondaire Guégon, VISIO à
Maison, provenance carnet affichée, ambiguïtés bloquées avec Confirmer désactivé.
Google réel : créations VISIO/DOMICILE, rappels présents, aucun Google Meet/lien
visio généré ; modification 10h → 11h du même événement, déplacement Famille →
Gaelle conservant titre/heure/Maison, suppression des deux côtés. Un seul événement
et liaison cohérente. Tous les résultats détaillés figurent dans docs/TESTING.md.

Le défaut découvert concerne le focus après choix du calendrier. Le callback
on_change invalide maintenant le résumé et son instantané, désactive Confirmer
et rend le focus au champ via l'API Toga 0.5.6 focus(). Deux nouvelles Entrées sont
nécessaires : analyser puis confirmer. Aucun changement de Synapse ou du CRUD.
**137 tests réussis sous Linux et sous Windows/Python 3.13** après ce lot.
Sous Windows, les 137 tests passent en 3.83 s. Le correctif de focus a également
été validé manuellement avec Toga WinForms : après saisie puis changement de
calendrier, le focus revient dans le champ, la première Entrée réanalyse avec la
nouvelle destination et la seconde Entrée confirme. Le contrôle natif du focus
est donc validé. L'UX d'ajout d'adresse au Carnet est conservée.
Le crash de fermeture pythonnet/WinForms reste toutefois présent de façon
intermittente. Il a été reproduit sur `f244bd0` et sur `c92aaab`, avec la même
trace `proactor.py` / `pythonnet.unload()` / `clr_loader`. Il a aussi été reproduit
sur `f244bd0` après remplacement de tout `rendez_vous/ui.py` par celui de
`c92aaab`. Le correctif de focus n'est donc pas retenu comme cause.
