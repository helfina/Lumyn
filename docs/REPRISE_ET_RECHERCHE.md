# Reprises Google/local et recherche de lieux — 06/09/2026

## Ollama local et Web Search — décision ciblée du 06/09/2026

Ollama local est chargé uniquement lorsque `LUMYN_IA_LOCALE=ollama` et qu'un modèle
est configuré. Il intervient après l'analyse déterministe, pendant une recherche
explicitement déclenchée. Sa sortie JSON est limitée à personne, établissement,
profession, ville, mode, date, heure et indices ; tout champ adresse ou inconnu est
refusé. Seuls personne/profession/établissement/ville enrichissent la requête vers
les sources publiques. Les date, heure, mode et validations du rendez-vous ne sont
jamais remplacés par le modèle. L'URL Ollama doit rester en loopback.

La [documentation Web Search officielle](https://docs.ollama.com/capabilities/web-search)
décrit `POST https://ollama.com/api/web_search`, un compte gratuit et une clé
`OLLAMA_API_KEY`. La réponse contient `title`, `url` et `content`, avec dix résultats
maximum côté service ; Lumyn se limite à trois. Le [plan Free](https://ollama.com/pricing)
est affiché à 0 $, fournit des crédits de démarrage et une requête concurrente,
mais aucun quota chiffré spécifique à Web Search n'est publié. Les pages consultées
n'indiquent pas de carte obligatoire pour Free ; cela ne garantit ni un volume
gratuit précis, ni un accès illimité.

Point bloquant : les [conditions Ollama](https://ollama.com/terms), mises à jour en
mai 2026, exigent 18 ans minimum pour utiliser le service. La factory refuse donc
l'activation réelle de Web Search dans ce lot, même avec une clé. Aucun compte n'est
créé et aucune requête réelle n'est envoyée. L'adaptateur reste prêt pour une future
utilisation par une personne éligible après nouvelle vérification des conditions.

Avec un transport simulé, l'adaptateur envoie seulement la requête minimale suivie
de « adresse professionnelle ». Il refuse un résultat sans URL ou sans adresse
française exploitable, conserve le domaine et l'URL, et ne tranche pas des adresses
contradictoires. Chaque adresse est soumise à Géoplateforme/BAN : numéro identique,
code postal compatible et rapprochement lexical minimal. Si le rapprochement passe,
l'adresse BAN remplace la forme Web et les deux provenances restent visibles. Sinon,
la proposition demeure explicitement non vérifiée et exige toujours un choix.

Les conditions donnent à l'utilisateur ses sorties mais rappellent que les services
tiers gardent leurs propres règles. La licence BAN couvre l'adresse normalisée, pas
automatiquement le titre, l'association au professionnel ou l'extrait Web. Le modèle
actuel du Carnet ne sait pas sauvegarder seulement le sous-ensemble BAN : toute
proposition issue du Web reste donc `conservation_autorisee=False`, même vérifiée.

## Architecture gratuite par défaut — décision finale du 06/09/2026

Le parcours normal est désormais `Maison/Carnet → source publique adaptée → choix
explicite → confirmation`. `RouteurLieuxPublics` envoie uniquement le texte minimal
nécessaire : une adresse partielle à Géoplateforme, un nom/ville à l'API Recherche
d'entreprises, ou la même requête avec filtre `est_finess=true` pour un établissement
de santé. Aucun calendrier, Carnet complet, note privée ou identité de patient n'est
envoyé. Google n'est appelé qu'après la confirmation existante.

Adresses : endpoints officiels actuels `https://data.geopf.fr/geocodage/search` et
`/completion/`, sans clé. Recherche limitée à cinq réponses, timeout 6 s, aucun
retry/polling et débit interne plafonné à quatre appels/s, très inférieur aux
limites officielles (50/s géocodage, 10/s autocomplétion). L'UI conserve quatre
caractères minimum, debounce 650 ms, dernier résultat mémoire et réponses périmées
ignorées. BAN est le référentiel officiel, sous [Licence Ouverte Etalab 2.0](https://adresse.data.gouv.fr/decouvrir-la-BAN) :
adresse normalisée, identifiant BAN utile et provenance peuvent être conservés
volontairement. Aucun choix automatique, Maison jamais écrasée.

Établissements : `https://recherche-entreprises.api.gouv.fr/search`, accès ouvert
sans clé, cinq résultats. Nom public, adresse d'établissement, commune, activité,
SIRET et provenance sont proposés ; le filtre FINESS fournit les établissements de
santé actifs. Cette source ne remplace pas un annuaire de praticiens. L'adresse
Entreprise/FINESS n'est pas encore renormalisée par un second appel BAN : elle reste
une proposition externe que l'utilisatrice doit vérifier avant confirmation.

L'[API FHIR Annuaire Santé](https://github.com/ansforge/annuaire-sante-fhir-documentation)
publie Practitioner/PractitionerRole/Organization, mais sa documentation exige
`ESANTE-API-KEY` et l'appel sans clé a répondu 403 le 06/09/2026. Aucun compte, clé
ou téléchargement massif n'a été créé ; la recherche RPPS individuelle reste donc
non disponible dans le parcours sans compte.

Ollama : `InterpreteurOllama` est un adaptateur local, URL loopback imposée, modèle
configurable, timeout, JSON validé et tout champ adresse/inconnu rejeté. Il est
maintenant facultativement appelé par Toga pour enrichir la requête publique ;
Synapse déterministe reste la source de vérité.

Gemini : l'adaptateur Interactions/Google Search exige des citations URL et reste
non persistable. La [tarification officielle](https://ai.google.dev/gemini-api/docs/pricing)
indique que Search grounding n'est pas disponible au Free Tier ; les 5 000 requêtes
incluses appartiennent au Paid Tier, dont l'activation lie un compte de facturation
et demande un prépaiement minimal. La factory refuse donc toute activation, même
avec `GEMINI_API_KEY`. Aucune donnée n'est envoyée à Gemini.

Geoapify reste isolé et testé pour préserver le travail historique, mais il n'est
plus injecté au démarrage et aucune clé n'est demandée dans le parcours normal.

## Décision et implémentation Geoapify — 06/09/2026

Geoapify est retenu comme premier fournisseur structuré, offre gratuite uniquement.
L'offre officielle consultée le 06/09 reste à 3 000 crédits/jour, sans carte
bancaire, jusqu'à 5 requêtes/s. Un appel simple de géocodage, autocomplétion ou
Places coûte généralement un crédit. Les conditions permettent un usage commercial
limité, imposent de surveiller le quota et rendent obligatoires les attributions
Geoapify et OpenStreetMap. Aucun forfait payant ou mécanisme de dépassement n'est
configuré par Lumyn.

`FournisseurGeoapify` utilise les endpoints HTTP de géocodage libre et
d'autocomplétion, convertit au plus cinq résultats en `PropositionLieu`, préfère
la France par biais (sans exclure le reste du monde), demande le français et
conserve nom, adresse formatée, ville, catégorie/type, place_id et provenance
`Geoapify / OpenStreetMap`. Un résultat reste une proposition à choisir. La
couverture de tous les professionnels n'est ni mesurée ni garantie.

Activation Windows, pour la session PowerShell courante :

```powershell
$env:LUMYN_GEOAPIFY = "1"
$env:GEOAPIFY_API_KEY = "COLLER_ICI_LA_CLE_PERSONNELLE"
briefcase dev
```

Pour conserver les variables dans les prochaines sessions Windows :

```powershell
setx LUMYN_GEOAPIFY "1"
setx GEOAPIFY_API_KEY "COLLER_ICI_LA_CLE_PERSONNELLE"
```

Fermer et rouvrir PowerShell après `setx`. `LUMYN_GEOAPIFY=off` désactive
explicitement le fournisseur, même si une clé existe. La clé n'est lue que dans
l'environnement, jamais écrite par Lumyn. Une activation sans clé affiche une
erreur claire au moment de la recherche. Les fichiers `.env` locaux sont ignorés
par Git mais Lumyn ne les charge pas automatiquement.

Pour obtenir la clé : un titulaire **majeur et juridiquement compétent** doit
ouvrir [Geoapify MyProjects](https://myprojects.geoapify.com/), créer un compte,
créer un projet, puis copier la clé générée dans « API Keys ». Geoapify indique
qu'aucune carte bancaire n'est nécessaire pour l'offre gratuite. Ne pas choisir
`API 10` ou un autre plan payant. Les conditions Geoapify interdisent l'inscription
aux mineurs ; le compte ne doit donc pas être créé ou contourné par un mineur.

### Réseau, quota et interface

La recherche Rendez-vous part seulement d'un clic après l'analyse locale ; Maison,
Carnet, VISIO, DOMICILE et Téléphone restent locaux. IA/web est conservée dans le
contrat mais aucun fournisseur n'est injecté : elle ne peut pas être appelée dans
la configuration réelle. Le travail HTTP utilise `asyncio.to_thread`, avec timeout
6 s, sans retry ni polling. Le bouton est désactivé pendant la demande puis rétabli.
Une réponse dont la phrase ou le calendrier a changé est ignorée.

Dans le Carnet, l'autocomplétion commence à quatre caractères après 650 ms sans
frappe, donne cinq choix maximum et ne sélectionne rien. Une frappe plus récente
annule l'attente ou rend la réponse ancienne inutilisable. Une requête identique
peut réutiliser uniquement le dernier résultat en mémoire de la session ; aucun
cache durable n'est créé. Le texte manuel reste modifiable après erreur ou timeout.

### Conservation : blocage volontaire

Les conditions publiques obligent l'attribution mais ne disent pas assez clairement
quelles données de géocodage/POI peuvent être copiées durablement dans un carnet
personnel. Le résultat des sources sous-jacentes peut aussi porter sa propre licence.
Lumyn marque donc toute proposition Geoapify `conservation_autorisee=False` : elle
peut servir au rendez-vous après choix, mais le bouton de sauvegarde est désactivé
et l'API métier refuse également l'écriture. Le défaut du contrat est désormais
le refus ; un futur fournisseur devra déclarer positivement un droit vérifié.

La saisie manuelle reste disponible pour une adresse obtenue indépendamment ; elle
ne doit pas servir à recopier un résultat Geoapify et contourner ce verrou. Il faut
demander à Geoapify une clarification écrite couvrant la copie
durable de `formatted`, nom, catégorie et provenance dans une application locale,
puis documenter les obligations ODbL/attribution avant de lever ce verrou. Le
consentement utilisateur ne suffit pas à donner ce droit contractuel.

Sources officielles : [tarifs](https://www.geoapify.com/pricing/),
[conditions](https://www.geoapify.com/terms-and-conditions/),
[géocodage](https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/),
[autocomplétion](https://apidocs.geoapify.com/docs/geocoding/address-autocomplete/).


Base : main 0.0.4, PR #2 fusionnée, 0460534. Branche :
`feature/google-reprise-recherche-lieux`. Version inchangée. Ce lot améliore les
pannes et prépare une recherche optionnelle ; aucune API de lieux/IA réelle active.

## Audit et stratégie minimale

Le stockage JSON reste atomique par remplacement, à un seul processus écrivain.
Il ne constitue pas une transaction avec Google. Les opérations locales seules
restent disponibles sans connexion ; la copie liée est écrite après l'appel Google.

| Opération / panne | Traitement dans ce lot | Limite / intervention |
| --- | --- | --- |
| CREATE : réponse perdue après insertion | Réserver sur disque un UUID avant insert ; rejouer la même demande avec le même ID | Rejouer exactement le même contenu et calendrier |
| CREATE : 409 | Lire l'événement ; vérifier ID, marqueur privé Lumyn, contenu, horaires et rappels avant réutilisation | Divergence ou événement annulé : bloquer et vérifier Google |
| CREATE : écriture locale puis nettoyage du journal échoue | La réservation reste ; retrouver la même liaison locale lors de la reprise | Fichier local illisible ou liaison divergente : bloquer |
| CREATE : écriture locale échoue | Tenter de supprimer l'événement créé ; conserver la réservation si compensation échoue | Double panne : reprise de la demande identique, pas nouvelle saisie modifiée |
| UPDATE : Google échoue | Pas de nouvelle copie locale ; erreur indique qu'une réponse perdue n'établit pas un échec distant | État distant incertain à contrôler avant nouvelle opération |
| UPDATE : stockage échoue | Tenter de restaurer le contenu Google original, signaler une restauration incomplète | Pas de garantie si réseau/stockage restent indisponibles |
| MOVE reconnu puis UPDATE/stockage échoue | Tenter restauration du contenu et retour séparément ; un échec du premier n'empêche pas le second ; conserver l'ID retourné quand possible | Réponse MOVE perdue : ne pas déplacer à l'aveugle, vérifier les deux calendriers |
| DELETE : Google réussit puis stockage échoue | Garder la ligne locale et ses IDs ; message de reprise ; aucune recréation compensatoire | Réparer l'accès au stockage puis reprendre Supprimer |
| DELETE réessayé | Seul HTTP 410 avec raison `deleted` vaut suppression déjà faite | 404 peut aussi signifier absence de droits ; 403/404/500 et autres 410 restent des erreurs |

Le [contrat d'insertion Google](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert)
permet de fournir l'identifiant. Le [guide des erreurs Calendar](https://developers.google.com/workspace/calendar/api/guides/errors)
distingue les conflits, suppressions et défauts d'accès. Les tests ne supposent
jamais qu'une exception réseau prouve l'absence de modification côté serveur.

`~/.lumyn/creations_google.json` contient une empreinte de la demande, l'ID du
calendrier et l'ID réservé. Il est écrit avant toute insertion, par temporaire,
flush/fsync puis remplacement. Il ne contient ni texte du rendez-vous ni jeton ;
l'ID de calendrier peut cependant identifier un compte : fichier personnel à ne
pas publier. Un journal illisible est conservé et bloque les nouvelles créations.
Le marqueur `extendedProperties.private.lumyn_creation` est envoyé à Google pour
reconnaître une insertion de Lumyn ; aucun lien Meet supplémentaire n'est créé.

### Garanties limitées

La reprise CREATE vaut pour la même empreinte tant que sa réservation demeure.
Après succès complet, une nouvelle création identique reste une nouvelle intention.
Modifier la demande après une réponse incertaine peut donc produire un doublon.
Ne pas supprimer le journal pour débloquer une erreur sans avoir vérifié les IDs
et les calendriers concernés ; sauvegarder les fichiers avant réparation manuelle.

Pas de journal transactionnel complet UPDATE/MOVE, pas d'ETag/conflit avec un autre
client, pas de garantie multiprocessus ou de résistance absolue à une coupure
électrique. Des compensations restent au mieux, notamment le chemin ancien de
vérification d'une liaison perdue après écriture : une seconde panne ou un ID
modifié lors du retour peut nécessiter une réparation manuelle. L'application ne
prétend pas assurer l'exactement-une-fois sur toutes les opérations.

## Architecture et parcours externe préparés

`FournisseurLieux.rechercher(requete)` et `FournisseurIAWeb` retournent des
`PropositionLieu` immuables : nom/adresse/source obligatoires, profession, ville,
identifiant optionnels. Aucun moteur concret ni secret. L'application existante
construit `InterfaceRendezVous()` sans fournisseurs : panneau invisible.
L'injection optionnelle permet de tester le parcours complet avec des doubles.

1. Analyse locale et validation déterministe ; Maison/Carnet fiables restent prioritaires.
2. Recherche structurée au clic explicite seulement pour une saisie exploitable
   non résolue. VISIO/DOMICILE/Téléphone et ambiguïtés locales ne déclenchent rien.
3. Si zéro résultat fiable ou erreur, IA/web seulement si disponible et autorisée
   séparément. Un résultat structuré utilisable suffit à éviter l'appel IA.
4. Afficher nom, profession, adresse, ville et source. Même un seul résultat
   demande un choix ; résultat absent/invalide ne vaut jamais adresse confirmée.
5. Choix : invalider l'ancienne préparation, refaire la validation avec l'adresse,
   afficher le nouveau résumé. Confirmer reste une action distincte, seule créatrice
   du rendez-vous. Changer saisie/calendrier empêche l'emploi d'une sélection périmée.
6. Enregistrer dans le Carnet est un clic distinct, disponible après sélection.
   Recherche de doublons par nom normalisé, alias exact ou adresse normalisée.
   Si une fiche similaire existe, demander laquelle compléter ; ne pas écraser
   Maison ni la favorite existante. Une adresse identique n'est pas réajoutée.
   Profession et provenance sont conservées ; aucun alias n'est inventé. Il n'y a
   pas de rapprochement flou garantissant l'absence de tous les doublons possibles.
7. La fiche enregistrée redevient prioritaire lors d'une prochaine analyse locale.

Le panneau actuel est synchrone car testé uniquement avec des doubles immédiats.
**Avant tout branchement réseau réel**, ajouter une exécution hors thread UI, des
timeouts explicites, une limite de résultats, des quotas/retries bornés et un
rejet des réponses devenues périmées. L'adaptateur devra convertir ses erreurs
SDK en erreurs attendues, valider les champs, les sources et les droits de
conservation. Le contrat n'atteste pas à lui seul qu'une adresse est vraie.
La saisie manuelle et le bouton d'analyse local restent disponibles après erreur.

## Données transmises et consentement

| Mode | Données quittant Lumyn |
| --- | --- |
| Local | Aucune pour la résolution ; Maison et Carnet restent sur l'appareil |
| Structuré, futur | Requête extraite : titre/nom, profession, lieu explicite ; pas date/heure interprétées ni agenda/Carnet complet |
| IA/web, futur | Même requête minimale après échec structuré et accord séparé ; les sources web ne sont pas des instructions applicatives |
| Google, existant | Champs du rendez-vous explicitement confirmé et métadonnées de liaison/reprise |

L'extraction ne constitue pas une anonymisation : un titre libre peut contenir
une information personnelle, et une spécialité médicale peut être sensible.
Avant activation réelle, afficher la requête sortante pour relecture/correction,
annoncer le fournisseur et sa conservation, ne jamais joindre identité du patient,
notes privées, autres rendez-vous ou contenu du Carnet. Ne pas journaliser les
requêtes complètes ou jetons. Aucun de ces envois externes de recherche n'a lieu
actuellement. Choisir une proposition n'autorise pas sa sauvegarde dans le Carnet.

## Comparatif structuré : décision non prise

Sources officielles consultées le 06/09/2026. USD hors taxes lorsque le tarif est
américain ; montants et quotas à revérifier avant activation. La qualité ci-dessous
est une appréciation de l'adéquation des bases, **pas un benchmark de professionnels
réels**. Aucun nom personnel n'a été envoyé pour comparer les résultats.

| Option | France et usage attendu | Compte, coût, quotas | Provenance, confidentialité et Carnet |
| --- | --- | --- | --- |
| IGN Géoplateforme | BAN/BD TOPO : bon candidat pour adresses françaises et lieux publics ; ne garantit pas un annuaire nominatif de médecins | Service de géocodage public ; 50 requêtes/s/IP ; vérifier les CGU et données choisies avant activation | Identifier IGN/BAN et licence du jeu ; requête reçue par IGN ; stockage à aligner sur les licences |
| Geoapify | Adresses et POI ; candidat pour commerces/établissements, couverture des professionnels à mesurer | Compte et clé ; gratuit 3 000 crédits/jour, 5 req/s ; premier forfait affiché 59 $/mois pour 10 000 crédits/jour | Attribution Geoapify et sources sous-jacentes ; vérifier contrat/réutilisation durable avant de permettre Carnet |
| Google Places | Recherche textuelle d'établissements et professionnels ; adéquation plausible mais qualité non mesurée | Clé, projet et facturation ; Text Search Pro : 5 000 événements gratuits/mois puis 32 $/1 000 au premier palier ; masque de champs peut changer le SKU | Attribution Google Maps ; restrictions de stockage/cache, exception pour place_id ; ne pas activer l'import permanent d'adresses sans validation des droits, y compris conditions EEE |
| Nominatim public OSM | Adresses/POI OSM ; professionnels variables selon contributions | Sans clé commerciale ; plafond global application 1 req/s, identification, pas d'autocomplétion | Attribution/ODbL ; interdit d'envoyer des données confidentielles ; politique exclut l'intégration automatique comme géocodeur générique sans décision informée du développeur |

Références : [géocodage IGN](https://www.data.gouv.fr/dataservices/api-geoplateforme-geocodage),
[CGU IGN](https://cartes.gouv.fr/cgu/),
[tarifs Geoapify](https://www.geoapify.com/pricing/),
[conditions Geoapify](https://www.geoapify.com/terms-and-conditions/),
[tarifs Google Maps](https://developers.google.com/maps/billing-and-pricing/pricing),
[politique Places](https://developers.google.com/maps/documentation/places/web-service/policies),
[politique Nominatim](https://operations.osmfoundation.org/policies/nominatim/).

Ces API HTTP sont techniquement accessibles sous Windows et Android. Cela ne
résout ni la protection d'une clé distribuée dans un APK ni les droits de stockage.
Nominatim public n'est pas proposé comme défaut automatique. Un proxy/cache
éventuel crée une responsabilité d'hébergement et reste un choix utilisateur.

## Options IA/web : architecture prête, fournisseur non choisi

| Option | Intérêt | Tarification et limites | Données et sources |
| --- | --- | --- | --- |
| OpenAI Responses + web_search | Recherche avec citations, adaptable au contrat | Compte/clé ; outil 10 $/1 000 appels + tokens aux tarifs du modèle ; quotas liés au compte | API non entraînée sur les données par défaut ; rétention opérationnelle possible, `store=false` ne signifie pas zéro rétention ; citations à afficher |
| Gemini + Google Search | Ancrage dans les résultats Google | Compte/clé ; tarification dépend du modèle, Gemini 3 facture les recherches déclenchées, pas seulement la requête Lumyn ; modèle et budget non choisis | Conditions du service et du grounding à relire ; traitement gratuit/payant et région peuvent différer ; conserver liens et attributions |
| Perplexity Sonar | Recherche web et réponses sourcées | Compte/clé ; Sonar : 1 $/million tokens entrée et sortie, plus 5/8/12 $ pour 1 000 requêtes selon contexte | Politique contractuelle de rétention à vérifier avant choix ; ne pas assimiler les conditions de l'application grand public à celles de l'API |

Références : [outil OpenAI](https://developers.openai.com/api/docs/guides/tools-web-search),
[tarifs API OpenAI](https://developers.openai.com/api/docs/pricing),
[données API OpenAI](https://developers.openai.com/api/docs/guides/your-data),
[grounding Gemini](https://ai.google.dev/gemini-api/docs/google-search),
[tarifs Gemini](https://ai.google.dev/gemini-api/docs/pricing),
[conditions Gemini](https://ai.google.dev/gemini-api/terms),
[tarifs Sonar](https://docs.perplexity.ai/docs/getting-started/pricing).

La présence d'une citation n'établit ni l'exactitude d'une adresse ni son droit de
réutilisation permanente. Privilégier une source officielle du professionnel,
refuser les résultats sans preuve exploitable, et demander le choix utilisateur.
Aucun modèle ne reçoit de pouvoir d'écriture Carnet ou Google.

## Prochaine décision

Geoapify est choisi et l'adaptateur est actif seulement si l'environnement le
demande. La prochaine décision porte sur le droit de conserver ses résultats :
obtenir une confirmation écrite de Geoapify, puis choisir les champs et attributions
à garder. IA/web reste désactivée. Après clarification, valider manuellement la
qualité sur des lieux publics français et le rendu Windows avant d'autoriser la
sauvegarde Carnet.
