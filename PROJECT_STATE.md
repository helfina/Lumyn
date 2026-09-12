# État actuel de Lumyn

## Situation courante — 12/09/2026

La PR #3 `feature/google-reprise-recherche-lieux` est **terminée et fusionnée**
dans `main`. Le commit de référence après fusion est
`629e63ce68827e19387bc4f24a74b5c697a0611b`. Elle ne constitue plus le chantier
courant.

La PR #3 a livré les reprises Lumyn vers Google, le stockage robuste, Synapse
déterministe avec priorité au Carnet, les fournisseurs BAN/Géoplateforme,
Recherche d'entreprises/SIRENE, FINESS et DILA/Administration, ainsi que leur
routage. Les propositions externes restent sourcées, jamais sélectionnées ou
enregistrées automatiquement, et Ollama local/Web reste facultatif. Les jobs CI
Linux et Windows interdisent le réseau réel pendant les tests. La suite complète
actuelle compte **437 tests réussis**.

Le chantier `fix/windows-shutdown-crash`, créé depuis `629e63c`, est terminé
techniquement au commit `79033bc583def28e8005706c6ae4b993f461e7f2`. La cause du
crash historique à la fermeture sous Windows/Python 3.13 est une continuation
.NET `Task.Delay(...).ContinueWith(...)` qui conservait un callback Python jusqu'à
la finalisation de `pythonnet` et pouvait entrer en collision avec
`pythonnet.unload()`.

Le correctif est intégré dans `src/lumyn/compat_toga_winforms.py` et appliqué avant
`Lumyn()` par `src/lumyn/app.py`. Il annule les délais avec un
`CancellationTokenSource` et limite la continuation à
`TaskContinuationOptions.OnlyOnRanToCompletion`. Sa portée est volontairement
restreinte à Windows, Python 3.13+ et `toga-winforms==0.5.6`, dépendance figée
pour reproductibilité. Un A/B/A sur le proactor et deux fermetures manuelles avec
le proactor Toga original ont validé le résultat ; le fichier `.briefcase` n'est
pas modifié manuellement.

## Ordre de travail

1. Finaliser proprement le chantier Windows et sa documentation.
2. Effectuer uniquement les validations natives encore nécessaires.
3. Ouvrir un chantier séparé Google vers Lumyn : suppressions et modifications
   distantes, conflits et réconciliation explicite.
4. Reprendre Android/APK/OAuth lorsque l'environnement JDK sera fonctionnel.
5. Définir et préparer la future 0.0.5.
6. Développer ultérieurement Historique de résolution, Notes, Tâches et rappels
   locaux.

Pour Google vers Lumyn, une suppression ne pourra être conclue qu'après
vérification par `google_calendar_id + google_event_id` : 404/410 signifie une
suppression certaine ; timeout, panne réseau ou erreur OAuth ne doit jamais
supprimer le rendez-vous local. Le chantier devra aussi couvrir le redémarrage,
les modifications distantes, les conflits et la synchronisation/réconciliation
explicite.

Android reste au stade d'une tentative bloquée avant génération : runtime Java
sans `javac`, téléchargement du JDK 17 Briefcase expiré, aucun APK produit et
aucun manifeste, permission ou OAuth Android natif validé sur appareil.

La version reste **0.0.4**. La 0.0.5 est seulement à définir après stabilisation ;
aucun tag, release ou nouvel installateur n'est préparé à ce stade.

## Historique — Ollama local raccordé, Web activable localement — 06/09/2026

L'interpréteur Ollama local est injecté au démarrage seulement si sa configuration
est présente ; `llama3.2:1b` est le modèle par défaut. Lors d'une recherche explicite, il peut ajouter personne, profession,
établissement et ville à la requête publique. Les champs date/heure/mode restent
gérés par Synapse déterministe ; toute adresse ou champ inconnu est rejeté. Absence
du logiciel, du modèle, timeout ou réponse invalide laissent le parcours public et
la saisie manuelle fonctionner.

Ollama Web Search est implémenté derrière `FournisseurIAWeb`, avec requête minimale,
trois résultats maximum, URL obligatoire, extraction prudente et rapprochement BAN.
Une divergence BAN ne supprime pas la proposition mais la marque non vérifiée ;
plusieurs adresses restent plusieurs choix. Le service est injecté uniquement avec
`LUMYN_OLLAMA_WEB=1` et `OLLAMA_API_KEY` dans l'environnement local. Le compte
utilisateur indique une utilisation incluse gratuite, 0 % utilisé et une remise à
zéro mensuelle, sans crédit payant ; Lumyn n'effectue aucun achat.

Les réponses Web et leurs métadonnées tierces ne bénéficient pas automatiquement
de la licence BAN. Même normalisée, une proposition Web reste donc non persistable ;
une adresse provenant directement de BAN conserve le mécanisme volontaire actuel.
À cette étape, la suite comptait **226 tests Linux réussis**. Ollama local réel
est validé sous Windows avec `llama3.2:1b`, extraction correcte et aucune adresse
inventée.

## Historique — Architecture locale et services publics — 06/09/2026

La branche `feature/google-reprise-recherche-lieux` utilise désormais par défaut
un routeur sans compte : Géoplateforme/BAN pour les adresses et l'autocomplétion,
API Recherche d'entreprises pour les établissements, et son filtre FINESS pour les
établissements de santé. Maison/Carnet restent prioritaires. Toute proposition
externe exige choix puis confirmation ; l'enregistrement BAN/SIRENE dans le Carnet
reste volontaire et dédoublonné. La saisie manuelle et le fonctionnement local
restent disponibles hors ligne.

La BAN est diffusée sous Licence Ouverte Etalab 2.0 : les adresses normalisées
sont persistables avec leur provenance. Geoapify est conservé isolé et testé mais
n'est plus injecté. L'API FHIR Annuaire Santé répond 403 sans `ESANTE-API-KEY` :
aucun compte n'a été créé et les praticiens RPPS individuels ne sont pas intégrés.

Un adaptateur Ollama strictement local est préparé, testé et relié facultativement
au parcours Toga. Il ne télécharge aucun modèle et rejette tout champ adresse.
L'adaptateur Gemini Web est également testé avec doubles, mais son activation est
refusée : Google Search grounding n'est pas disponible au Free Tier et son niveau
payant exige une facturation/prépaiement. Aucun service payant n'est nécessaire.

À cette étape, la suite comptait **212 tests Linux réussis** et la PR #3 était
encore en brouillon. Android restait au diagnostic antérieur (échec avant
génération faute de JDK complet) ; aucune nouvelle tentative. Le crash Windows
était hors périmètre de ce lot.


## Étape préparatoire du 06/09/2026

**0.0.4 est fusionnée dans main**, PR #2, commit `0460534`.
La candidate finale a été validée par l'utilisatrice : **137 tests sous Windows /
Python 3.13 en 4.44 s**, Carnet, Synapse, focus WinForms et Google Calendar réel.
Ces validations concernent la 0.0.4 ; elles ne valent pas validation native du lot suivant.

Le travail courant à cette date était `feature/google-reprise-recherche-lieux`,
issue de ce merge.
Version applicative conservée à **0.0.4**, aucune nouvelle release préparée.
Le travail déjà présent dans le workspace a été conservé et complété.

- Reprise de CREATE Google par identifiant réservé sur disque ; DELETE partiel
  réessayable sans recréer l'événement ; restaurations UPDATE/MOVE mieux signalées.
- Parcours optionnel de propositions sourcées, choix explicite puis confirmation,
  ajout volontaire au Carnet et choix d'une fiche similaire avant ajout d'adresse.
- Fournisseur structuré puis repli IA/web autorisé séparément : architecture et
  interface testées par injection. Cette étape précédait le choix Geoapify ; le
  fournisseur est maintenant optionnel et reste désactivé sans configuration.
- Cette étape préparatoire comptait **175 tests Linux réussis**. L’intégration
  Geoapify réalisée ensuite porte la suite courante à **188 tests**. Validation
  Windows et Google réelle du nouveau lot encore à effectuer.
- Comparatif et limites : [docs/REPRISE_ET_RECHERCHE.md](docs/REPRISE_ET_RECHERCHE.md).
  Android/OAuth : [docs/ANDROID_OAUTH.md](docs/ANDROID_OAUTH.md), préparation uniquement.
- Arrêt avant le choix du fournisseur, des clés, du budget et de la politique de
  données. À cette date, la nouvelle PR devait rester en brouillon, sans fusion
  ni publication.
- Crash Windows préexistant : hors périmètre, aucun changement de runtime.

## Historique avant fusion de 0.0.4

Les sections datées ci-dessous décrivent les étapes antérieures ; leurs mentions
de candidate et de fusion en attente ne décrivent plus la situation courante.


## Version et branche — 05/09/2026

Version déclarée sur cette branche : **0.0.4**, candidate préparée après audit.
La version de main reste 0.0.3 (78093a0), sans fusion effectuée.
La version **0.0.4 Carnet de lieux + Synapse Rendez-vous** est en préparation sur
`feature/synapse-rendez-vous`, reprise au commit `3f0f119` après les trois commits
Carnet (`81ab732`, `ab3cd5e`, `3f0f119`). Cette séance ne modifie ni ne fusionne main.
La préparation de version 0.0.4 est autorisée pour cet audit ; sa publication
et la fusion restent en attente de décision.

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

### Historique — incident Windows résolu

- Crash de fermeture Windows historique : `Windows fatal exception: access violation`
  observé dans `toga_winforms/libs/proactor.py` pendant le déchargement de
  `pythonnet` / `clr_loader`.

- Le problème a été reproduit plusieurs fois sur `f244bd0`, sur l'ancien commit
  `c92aaab`, ainsi que sur la version stable 0.0.3 de `main` au commit `78093a0`.
  Sur `main`, le test a été effectué dans un environnement Briefcase neuf, avec
  ouverture puis fermeture immédiate de Lumyn sans interaction.

- Le crash a également été reproduit sur `f244bd0` après remplacement complet de
  `rendez_vous/ui.py` par la version de `c92aaab`. Le correctif de focus n'est donc
  pas identifié comme cause.

- Le crash était préexistant à la branche Synapse et au correctif de focus ; il
  n'était pas une régression introduite par la 0.0.4. Sa cause est désormais
  identifiée et le correctif validé au commit `79033bc`.

- Certaines fermetures étaient parfaitement propres, ce qui expliquait le caractère
  intermittent. Le correctif appliqué annule désormais la continuation retardée ;
  aucun correctif direct dans `.briefcase` n'est requis.

### Autres limites connues

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

La candidate 0.0.4 est préparée sur feature/synapse-rendez-vous après audit.
Recommandation : prête à fusionner avec le crash préexistant documenté.
Attendre l'autorisation explicite avant fusion ou changement d'état final de PR.
Aucun fournisseur externe n'est activé.

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


## Audit final depuis e030674 — 05/09/2026

Comparaison avec main 78093a0 : aucune régression bloquante mise en évidence dans
les parcours validés. Code applicatif et tests inchangés pendant ce lot.
137 tests Linux réussis avant/après version et documentation ; les 137 Windows
et le focus natif étaient déjà confirmés. Syntaxe Python, TOML et diff vérifiés.
Version applicative unique dans pyproject.toml passée à 0.0.4 ; CHANGELOG complété.

Le crash ne reçoit aucun correctif : les sources amont donnent une piste de
callbacks .NET tardifs et des précédents de finalisation, sans preuve suffisante
pour ce cas. Linux ne permet pas d'en valider une correction native. Le rapport
[docs/AUDIT_0.0.4.md](docs/AUDIT_0.0.4.md) distingue faits, hypothèses et diagnostic
restant. Recommandation : **prête à fusionner**, avec défaut connu, sous réserve
de l'autorisation de l'utilisatrice. Aucun installateur ni release publié.
