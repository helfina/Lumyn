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

Les tests définissent TOGA_BACKEND=toga_dummy et bloquent les connexions réseau.
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

## Relance des tests après documentation

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

## État de la PR

La PR reste en brouillon et non fusionnée. Sa fusion ou sa sortie du mode brouillon
nécessite l'accord explicite de l'utilisatrice. Aucune étape de développement
supplémentaire n'est engagée par cette mise à jour.
