# Tester Lumyn

## État actuel — 12/09/2026

La PR #3 est terminée et fusionnée dans `main` au commit
`629e63ce68827e19387bc4f24a74b5c697a0611b`. La suite complète vérifiée sur cette
base compte **430 tests réussis** sous Linux avec Toga Dummy, services réseau et
Google simulés. La CI de la PR validait également Windows/Python 3.13.

Le chantier courant, `fix/windows-shutdown-crash`, est un diagnostic natif séparé.
Il ne modifie pas les garanties fonctionnelles acquises par la PR #3.

## Historique — Ollama local/Web et vérification BAN — 06/09/2026

À cette étape du chantier, la suite comptait **226 tests réussis** sous
Linux/Python 3.12. Les nouveaux tests utilisaient exclusivement des transports
injectés : aucun appel à Ollama local, Ollama Cloud, au Web ou à BAN.
Ils couvrent enrichissement local facultatif, indisponibilité/timeout/JSON invalide,
absence de clé Web, activation locale explicite, BAN obligatoire, zéro résultat, URL obligatoire,
adresses contradictoires, timeout/erreur, normalisation BAN et maintien d'une
proposition non vérifiée en cas d'échec. Les tests existants conservent la priorité
Carnet/public, les réponses périmées, le choix explicite, l'absence d'écriture
automatique et l'absence de Google avant confirmation.

Validation Windows fournie le 06/09/2026 : Ollama installé, `llama3.2:1b` présent et
extraction réelle correcte de Laporte / psy / Lorient / jeudi / 10h, sans adresse
inventée. Restent à valider sous Windows : arrêt du service ou modèle absent ;
parcours public/BAN et saisie manuelle. Web Search doit rester absent de l'interface
sauf configuration locale explicite et ne produire aucun trafic sinon. Aucun essai
Android demandé dans ce lot.

## Services publics et adaptateurs IA — 06/09/2026

Suite complète de cette étape : **212 passed in 1.41s** sous Linux/Python 3.12, Toga Dummy.
Compilation Python et `git diff --check` réussis. Les sockets externes restent
bloquées dans les tests ; Géoplateforme, Entreprises, FINESS, Ollama et Gemini sont
entièrement simulés par transports injectés.

Les cas nouveaux couvrent recherche/autocomplétion BAN, zéro/plusieurs/invalides,
timeouts et erreurs, limite de débit interne, Licence Ouverte et sauvegarde
volontaire ; Entreprises/FINESS sans clé ; routage exclusif ; absence d'IA locale,
JSON strict, champ adresse halluciné refusé et timeout ; Gemini absent, activation
payante refusée, citations obligatoires, borne et non-persistance. Les tests Toga
existants couvrent déjà debounce, réponse périmée, choix explicite, saisie manuelle
et absence de création Google avant confirmation.

À refaire sous Windows : suite complète, rendu WinForms, autocomplétion BAN réelle,
recherche d'un établissement Entreprises/FINESS, panne réseau, choix/sauvegarde et
réutilisation locale, puis non-régression Google CREATE/UPDATE/MOVE/DELETE. Ne pas
installer Ollama avant que son raccordement UI soit développé. Gemini et Geoapify
ne doivent produire aucun appel dans la configuration normale.

## Validation Geoapify — 06/09/2026

Suite complète après intégration : **188 passed** sous Linux/Python 3.12,
Toga Dummy. Tous les tests Geoapify utilisent un transport injecté ou des mocks :
aucune vraie clé, aucun compte et aucun appel au service. Cas ajoutés : configuration
absente/activation sans clé, conversion zéro/un/plusieurs/invalides, timeout/erreur,
limite et attribution, refus de conservation, activation des deux écrans, debounce,
minimum de caractères, dernier résultat mémoire, réponse périmée, saisie manuelle,
choix explicite et recherche Rendez-vous hors thread UI. Les tests Google/local
existants restent inchangés et verts.

Validation manuelle restante : clé gratuite créée par un adulte, rendu WinForms,
requêtes sur lieux publics, débit/quota dans MyProjects, erreurs hors ligne et
qualité réelle des POI. Ne pas utiliser de données médicales/personnelles pour ce
premier essai. La sauvegarde Geoapify vers le Carnet doit rester indisponible.

Android réel : `briefcase create android --no-input` a échoué avant génération :
OpenJDK présent sans `javac`, puis téléchargement du JDK 17 Briefcase expiré.
Aucun manifeste, package, permission ou APK vérifié. Détails dans ANDROID_OAUTH.md.


## Résultat courant — 06/09/2026

`.venv-tests/bin/python -m pytest -q` : **175 passed in 1.13s** sous Linux,
Python 3.12, Toga Dummy. Les 137 tests existants restent réussis ; 38 nouveaux cas.
Les résultats chronologiques ci-dessous ne doivent pas être confondus avec ce lot.
La candidate finale 0.0.4 a été validée sous Windows/Python 3.13 : **137 passed in
4.44s**, puis fusionnée (PR #2, `0460534`). Les validations natives sont conservées.

Nouveaux tests : `test_reprise_google.py` (22 cas) et `test_selection_lieux.py`
(16 cas). Ils couvrent perte de réponse CREATE, conflit 409 vérifié, journal
illisible/écriture impossible, double panne locale/Google, nettoyage tardif,
DELETE répété après suppression distante, erreurs HTTP non assimilées à un succès,
MOVE partiel et restauration échouée. Recherche : zéro/un/plusieurs/invalides,
erreur/timeout, priorités locales, IA absente ou inutile, choix/changement, aucune
écriture automatique, Carnet volontaire sans doublon exact et réutilisation locale.

Aucun fournisseur réseau réel appelé dans ces scénarios. Les adaptateurs sont
simulés ; les données de reprise sont également redirigées vers un dossier temporaire.
Le blocage socket des tests est une protection supplémentaire, pas un pare-feu système.

### Validation manuelle restante pour ce lot

1. Sous Windows : relancer toute la suite avec les commandes ci-dessous.
2. Avec un agenda de test choisi par l'utilisatrice : CREATE, UPDATE, MOVE, DELETE,
   vérifier un seul événement et les identifiants locaux ; refaire après redémarrage.
3. Les pannes d'écriture/compensation restent simulées automatiquement ; ne pas
   provoquer volontairement de corruption sur les données personnelles réelles.
4. Le panneau externe nécessite un fournisseur injecté : aucun bouton nouveau
   visible par défaut. Après choix et intégration du fournisseur, valider rendu
   WinForms, navigation clavier, délai réseau, changement de proposition et Carnet.
5. Android : suivre [ANDROID_OAUTH.md](ANDROID_OAUTH.md). Aucun APK ni OAuth Android
   n'a été construit ou validé pendant cette séance.

Ne pas considérer les validations natives de 0.0.4 comme celles des 175 tests.


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
réutilise Pillow installé dans le runtime ; l'installation Windows avec
requirements-test.txt a depuis été confirmée, avec les 132 tests réussis ci-dessous.

## Validation complète réelle — 05/09/2026, base `c92aaab`

Résultats rapportés par l'utilisatrice sous Windows/Python 3.13, application Toga
WinForms et Google Calendar réel. Après installation de requirements-test.txt,
la suite automatique a donné **132 passed in 3.94s** sous Windows/Python 3.13.
Ces tests utilisent Toga Dummy ; les essais natifs ci-dessous ont été réalisés
séparément dans l'application avec `briefcase dev`.

| Scénario réel | Résultat confirmé |
| --- | --- |
| Lancement, écrans Rendez-vous/Carnet, navigation | OK |
| Carnet : création, modification, suppression, plusieurs adresses, favorite | OK |
| `infirmière vendredi 9h à domicile`, création locale | Infirmière — DOMICILE, adresse Maison, provenance carnet affichée |
| `Dr Laporte psychiatre jeudi 10h` | Professionnel reconnu, site favori Lorient, provenance carnet affichée |
| `Dr Laporte psychiatre Guégon jeudi 10h` | Site secondaire Guégon choisi, prioritaire sur Lorient |
| `Laporte jeudi 10h visio` | Dr Laporte — VISIO, adresse Maison, pas celle du cabinet |
| Deux fiches avec alias Laporte | Ambiguïté signalée, Confirmer désactivé, aucun choix arbitraire ; fiche de test ensuite supprimée |
| Création Google VISIO dans Famille | Titre, date/heure, Maison, calendrier et liaison corrects ; un événement ; rappels présents |
| Lien automatique pour VISIO | Aucun Google Meet ni lien visio créé |
| Création Google DOMICILE | Titre et adresse Maison corrects, un événement |
| Modification VISIO de 10h à 11h | Même événement, effet immédiat, aucun doublon |
| Déplacement Famille → Gaelle | Disparu de Famille, présent dans Gaelle, un événement ; titre, heure et Maison conservés |
| Suppression depuis Lumyn | Disparu de Lumyn et du calendrier Google Gaelle |
| Calendrier choisi avant saisie, puis deux Entrées | Résumé puis confirmation : OK sous Windows |

Maison disposait d'une adresse favorite et des alias Maison, domicile, chez moi.
Le CRUD Google avec Synapse, la liaison et l'absence de doublon sont validés pour
ces essais. Le navigateur Google Agenda a nécessité un rafraîchissement manuel
pour voir une création déjà effectuée côté Google ; ce constat n'est pas retenu
comme défaut Lumyn. La présence des rappels est confirmée, pas leur déclenchement.

Dans le Carnet, ajouter une adresse nécessite « Ajouter l'adresse », puis
« Enregistrer la fiche ». Le parcours fonctionne ; son ergonomie reste inchangée.

### Crash de fermeture Windows intermittent

Un crash de fermeture reste observable de manière intermittente sous Windows :

    Windows fatal exception: access violation

La trace observée pointe vers :

    toga_winforms/libs/proactor.py
    clr_loader/types.py
    pythonnet/__init__.py -> unload()

Environnement confirmé :
- Python 3.13.3
- Briefcase 0.4.4
- toga-winforms 0.5.6
- pythonnet 3.1.0
- clr_loader 0.3.1

Le problème a été reproduit plusieurs fois sur `f244bd0`, sur l'ancien commit
`c92aaab`, ainsi que sur la version stable 0.0.3 de `main` au commit `78093a0`.

Le test sur `main` a été effectué dans un environnement Briefcase neuf. Lumyn a
été ouvert puis fermé immédiatement sans interaction ; le même
`Windows fatal exception: access violation` s'est produit avec la même trace
Toga WinForms / pythonnet / clr_loader.

Un test d'isolation avait également remplacé entièrement
`src/lumyn/modules/rendez_vous/ui.py` de `f244bd0` par la version de `c92aaab` :
le crash s'était encore produit.

Ces comparaisons avaient confirmé, avant les fusions de la 0.0.4, que le défaut
préexistait à la branche Synapse et au correctif de focus. Il n'est donc pas
considéré comme une régression introduite par ces travaux.

Certaines fermetures restent propres, ce qui confirme le caractère intermittent.
Aucune corruption de données ni régression fonctionnelle n'a été observée avant
la fermeture.

La cause exacte reste à investiguer séparément côté Toga WinForms/pythonnet.
Aucun correctif spéculatif Toga/pythonnet/asyncio n'est appliqué pour le moment.

#### Reproduction du 12/09/2026 sur le chantier dédié

Sur la branche locale `fix/windows-shutdown-crash`, créée depuis `629e63c`, Lumyn
complet a de nouveau produit l'access violation avec `PYTHONFAULTHANDLER=1`,
`PYTHONASYNCIODEBUG=1` et `briefcase dev -v`. La trace implique toujours le tick
du proactor Toga WinForms, `pythonnet.unload()` et `clr_loader`.

Une application Toga minimale a ensuite été exécutée avec le Python de
l'environnement Briefcase de Lumyn. Elle s'est fermée proprement avec
`$LASTEXITCODE = 0`, sans access violation. Ce résultat ne prouve pas que
Toga/pythonnet est innocent ; il établit seulement que Toga minimal ne suffit pas,
dans cet essai, à reproduire le crash de Lumyn.

Le prochain test doit isoler les éléments propres à Lumyn encore actifs à la
fermeture : tâches asyncio, threads, executors/`asyncio.to_thread`, callbacks,
services/adaptateurs et ordre de finalisation. Aucun correctif n'est retenu avant
démonstration de la cause.

### Correctif de focus de ce lot

Défaut observé : après saisie puis changement de calendrier, le focus restait
sur le sélecteur et Entrée n'atteignait plus le champ texte.

`Selection.on_change` appelle maintenant `changer_calendrier` : effacement du
résultat et de l'instantané analysé, désactivation des boutons liés au résumé,
puis `rdv_input.focus()`. Le texte est conservé. La prochaine Entrée prépare
avec le nouveau calendrier ; seule la suivante confirme. Même un aller-retour
entre calendriers impose une nouvelle analyse. Aucun appel Google au changement.
Le callback est installé après construction des widgets et sélection initiale.

L'API Toga **0.5.6** a été vérifiée dans le paquet installé et dans ses sources :
[Widget.focus](https://github.com/beeware/toga/blob/v0.5.6/core/src/toga/widgets/base.py)
délègue au backend ; [WinForms](https://github.com/beeware/toga/blob/v0.5.6/winforms/src/toga_winforms/widgets/base.py)
utilise `native.Focus()`. Aucun contournement spécifique asyncio ou temporisateur.

Après ce correctif : **137 tests réussis sous Linux/Python 3.12**, dont cinq cas
supplémentaires dans test_synapse_ui.py : destinations Google/local, calendrier
choisi avant saisie ou après préparation, et aller-retour entre calendriers.
Ils vérifient le callback, l'appel au backend focus, l'invalidation, les deux
Entrées et l'absence d'écriture accidentelle. Tous les tests ont été relancés
après les modifications de documentation.

**Validation Windows du correctif : réussie le 05/09/2026.**

La suite complète a été relancée sous Windows/Python 3.13 après récupération du
correctif :

    137 passed in 3.83s

Le comportement natif Toga WinForms a ensuite été vérifié manuellement :
après saisie d'un rendez-vous puis changement de calendrier, le focus revient
automatiquement dans le champ de saisie sans clic supplémentaire. La préparation
précédente est invalidée ; la première Entrée effectue une nouvelle analyse avec
le nouveau calendrier et la seconde Entrée confirme.

Le défaut de focus observé avant le correctif est donc corrigé et validé sous
Windows. Toga Dummy ne simule toujours pas visuellement le focus natif, mais cette
limite est désormais couverte par la validation manuelle WinForms.

### Historique — Branche et livraison au 05/09/2026

La stabilisation 0.0.3 avait été fusionnée avant cette reprise. Le travail courant
à cette date restait sur `feature/synapse-rendez-vous`, sans fusion ni changement
d'état de PR.
Le contrôle natif Windows du correctif de focus est validé. Le crash de fermeture
Windows restait un défaut intermittent connu, reproduit indépendamment du correctif
de focus et sans régression fonctionnelle observée. La décision de livraison 0.0.4
restait alors à prendre en tenant compte de ce défaut connu. Depuis, la 0.0.4 et
la PR #3 ont été fusionnées dans `main` ; aucune release n'est créée par le
chantier de diagnostic actuel.


## Audit final et candidate 0.0.4 — 05/09/2026

Reprise de e030674 et comparaison à main 78093a0. `python -m pytest -q` :
**137 réussis** sous Linux/Python 3.12 avant et après changement de version et
chaque document de ce lot. Aucun test ajouté, aucun code applicatif modifié.
Les 137 tests Windows/Python 3.13 (3.83 s), le focus natif et Google réel restent
les validations utilisateur déjà acquises ; ils n'ont pas été rejoués sous Linux.

`python -m compileall -q src tests` : réussi. Version TOML vérifiée : 0.0.4.
`git diff --check` et comparaison avec main : réussis. En début d'audit, un cache
bytecode local incomplet empêchait pytest de démarrer ; suppression des seuls
.pyc de l'environnement de test puis relance réussie, sans changement du dépôt.

Le rapport [AUDIT_0.0.4.md](AUDIT_0.0.4.md) détaille le crash : aucune correction
native sûre démontrée, aucun contournement appliqué. Aucun exécutable Windows ou
APK 0.0.4 construit ici. La candidate est recommandée pour fusion avec défaut
connu ; publication et fusion restent des décisions utilisateur.
