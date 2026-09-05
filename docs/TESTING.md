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

## Validation manuelle Windows restante

Depuis l'environnement habituel de développement :

```powershell
briefcase dev
```

1. Vérifier le démarrage, le défilement, les filtres et les boutons de navigation.
2. Choisir « Sur cet appareil uniquement », saisir « CAF demain 10h à Lorient ».
3. Vérifier le résumé, confirmer, fermer et relancer : le rendez-vous doit rester.
4. Modifier son heure et son lieu, analyser puis confirmer ; le même rendez-vous
   doit être modifié. Le supprimer ensuite.
5. Analyser un rendez-vous, changer ensuite son heure et confirmer : Lumyn doit
   demander une nouvelle analyse, sans enregistrer l'ancienne heure.
6. Saisir « Dentiste demain 14:99 » : aucune confirmation ne doit être possible.

## Validation Google restante

Utiliser un calendrier dédié aux essais et uniquement des rendez-vous fictifs.
Les fichiers OAuth restent locaux et sont ignorés par Git. Le prototype utilise
le flux OAuth pour ordinateur ; son adaptation Android n'est pas validée.

- Créer après confirmation et vérifier heure, lieu, durée d'une heure et rappels.
- Modifier puis déplacer vers un deuxième calendrier de test : vérifier l'absence
  de doublon et la conservation de la liaison locale.
- Supprimer le rendez-vous fictif et vérifier les deux côtés.
- Couper le réseau : vérifier l'erreur Google et la disponibilité du stockage local.

Ces opérations réelles n'ont pas été effectuées pendant la reprise du 05/09/2026.
