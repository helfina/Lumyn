# Tester Lumyn

## Tests automatiques isolés

Depuis la racine du dépôt, dans un environnement de test distinct de Briefcase :

```powershell
py -3.13 -m venv .venv-tests
.\.venv-tests\Scripts\python.exe -m pip install -r requirements-test.txt
.\.venv-tests\Scripts\python.exe -m pytest -q
```

Sous Linux : `python -m pip install -r requirements-test.txt`, puis
`python -m pytest -q` depuis la racine, de préférence dans un environnement virtuel.

Les tests définissent TOGA_BACKEND=toga_dummy et bloquent les connexions externes (loopback autorisé pour asyncio Windows).
Ils remplacent les appels Google par des doubles et redirigent les données locales
vers un répertoire temporaire. Ils ne lisent ni token.json ni credentials.json.
Le backend Dummy vérifie la construction et les interactions, pas le rendu natif.

## Validation manuelle réelle Windows et Google — 05/09/2026

Essais réels effectués sous Windows et confirmés par l'utilisatrice sur la branche
`codex/lumyn-fiabilisation-rendez-vous`, avec Google Calendar réel. Ces résultats
complètent les 57 tests automatiques isolés ; ils ne sont pas issus de Toga Dummy
ou d'appels Google simulés.

| Contrôle effectué | Résultat confirmé |
| --- | --- |
| Démarrage avec `briefcase dev` sous Windows | OK |
| `ResourceWarning` SSL au lancement | Aucun observé |
| Création d'un rendez-vous Google | OK |
| Affichage du rendez-vous dans Lumyn et Google Calendar | OK |
| Modification d'un rendez-vous existant | OK, effet immédiat observé |
| Suppression d'un rendez-vous | OK, effet immédiat observé |
| Déplacement d'un calendrier Google vers un autre | OK |
| Doublons après déplacement | Aucun observé |
| Liaison Lumyn/Google pendant ces opérations | Cohérente |

L'affichage Windows et Google réel sont validés pour ces scénarios. L'effet
immédiat et l'absence de doublon sont des observations de cette séance, pas une
garantie de délai ou de cohérence dans toutes les conditions réseau.

## Relance historique après documentation 0.0.3

`python -m pytest -q` : **57 tests réussis** après les modifications documentaires.
Aucun code applicatif, aucune fonctionnalité et aucun test n'a été modifié.

## Contrôles complémentaires non confirmés dans ce compte rendu

La liste suivante conserve les essais précédemment proposés sans les considérer
comme réalisés. Elle ne remet pas en attente les opérations validées ci-dessus.

- Défilement, filtres et boutons de navigation, vérifiés individuellement.
- Cycle local avec « Sur cet appareil uniquement », fermeture et relance pour
  vérifier la persistance, puis modification de l'heure/du lieu et suppression.
- Changement de saisie après analyse : demande de nouvelle analyse avant création.
- Saisie `Dentiste demain 14:99` : confirmation impossible.
- Vérification explicite du lieu, de la durée d'une heure et des rappels J-1/H-1
  dans Google ; leur déclenchement n'est pas confirmé par les résultats fournis.
- Coupure réseau : erreur Google et disponibilité du stockage local.
- Parcours OAuth initial et renouvellement des jetons testés séparément.
- Affichage natif Android, adaptation OAuth Android et compilation APK.

Pour de futurs essais Google, utiliser un calendrier dédié et des rendez-vous
fictifs. Les fichiers OAuth restent locaux et sont ignorés par Git.

## Reprise Carnet et Synapse — 05/09/2026

La base `3f0f119` avait 78 tests réussis, reproduits avant les changements.
L'utilisatrice a confirmé sous Windows/Python 3.13 le CRUD Carnet et la navigation.
Après les modifications de cette séance : **132 tests réussis** sous Linux,
Python 3.12 et Toga Dummy. Suite complète relancée après chaque lot de code et
chaque fichier documentaire modifié. Les nouvelles adresses des tests sont fictives.

Les 54 nouveaux cas sont dans `test_lieux_validation.py` (16), `test_synapse.py`
(27), `test_synapse_ui.py` (5) et `test_synapse_recherche.py` (6). Ils couvrent
copies profondes, alias, Maison/favorite, données anciennes et pannes, exemples de
saisie, priorités/ambiguïtés, clavier, modification liée et fournisseur inactif.
`conftest.py` isole globalement carnet, rendez-vous et préférences de calendrier.
Pillow est déclaré explicitement pour Toga Dummy. Ici, l'environnement virtuel
réutilise Pillow installé dans le runtime ; l'installation Windows propre avec
requirements-test.txt reste à vérifier sur le poste utilisateur.

### Validation manuelle à effectuer sur cette branche

Avec des fiches et rendez-vous de test, préparer Maison avec une adresse, un
professionnel avec alias/métier et deux sites dont une favorite, puis un ITEP.
Adapter les villes des fiches aux exemples :

- `mardi 15h dentiste à Lorient` et `dentiste mardi 15h Lorient` : même site attendu.
- `Dr Laporte psychiatre Lorient jeudi 10h` : professionnel et site du carnet.
- `mardi 15h dentiste Guégon` : site explicitement indiqué, même non favori.
- `Laporte jeudi 10h visio` : titre VISIO, adresse Maison, aucun lien récurrent.
- `infirmière vendredi 9h à domicile` : titre DOMICILE et adresse Maison.
- `ITEP mardi 14h` : fiche et favorite, sinon demande de précision.
- Deux correspondances, site inconnu après alias, Maison absente ou plusieurs
  adresses sans favorite : pas de confirmation tant que le problème reste présent.
- Entrée affiche le résumé ; seconde Entrée confirme. Changer le texte ou le
  calendrier oblige à préparer à nouveau. Vérifier aussi les boutons habituels.
- Créer, modifier, déplacer puis supprimer dans Google : vérifier le même événement,
  l'adresse, l'absence de doublon et la cohérence dans Lumyn. Tester également le
  cycle local, les filtres, le CRUD Carnet et la navigation.

Ces essais Synapse natifs et Google réel restent à faire ; les validations réelles
0.0.3 et Carnet ci-dessus ne sont pas présentées comme une validation de ce nouveau code.

### Crash de fermeture Windows : protocole de reproduction

Un access violation lors du déchargement pythonnet/WinForms/proactor a été signalé ;
le lancement suivant a réussi. Linux/Toga Dummy ne peut pas reproduire cet arrêt
natif. Aucun correctif spéculatif d'asyncio ou de fermeture n'a été appliqué.

Dans l'environnement Windows utilisé pour Briefcase, relever `python --version`,
`briefcase --version` et `python -m pip show toga-winforms pythonnet clr-loader`.
Lancer `briefcase dev`, fermer normalement la fenêtre, puis répéter avec navigation
Carnet/Rendez-vous et une opération locale. Noter le scénario, l'heure et le code
retour ; conserver le journal complet localement. Si le crash revient, comparer
le même scénario sur la base `3f0f119` avant de choisir une correction. Ne pas
inclure de jetons OAuth ou de données personnelles dans un rapport GitHub.

### Branche et livraison

La stabilisation 0.0.3 a été fusionnée avant cette reprise. Le travail courant
reste sur `feature/synapse-rendez-vous`, sans fusion ni changement d'état de PR.
La livraison 0.0.4 attend la validation et la décision de l'utilisatrice.
