# Audit technique de la candidate 0.0.4 — 05/09/2026

## Périmètre et conclusion

Dépôt helfina/Lumyn, branche feature/synapse-rendez-vous, base de reprise
`e0306746ecd44d3657b8419daf87685ffbb8fc32`, comparée à main `78093a0`.
Les 30 fichiers du diff de branche ont été examinés par catégorie : documentation,
configuration, navigation, Carnet, Synapse, intégration Rendez-vous et tests.

**Recommandation : prête à fusionner**, avec le crash de fermeture préexistant
explicitement conservé comme défaut connu. Aucun nouveau défaut bloquant n'a été
mis en évidence dans les parcours validés. Ce constat ne garantit pas l'absence
de défaut sur toutes les formulations ou toutes les plateformes. Il concerne
la fusion du code, pas la certification d'un installateur Windows ou Android.
La fusion et la sortie du brouillon restent soumises à l'autorisation utilisateur.

## Résultats de l'audit

| Zone | Contrôles et conclusion |
| --- | --- |
| Rendez-vous/Google | agenda_google.py, stockage.py, analyseur.py et calendrier_ui.py sont identiques à main. Les fonctions CRUD Google du contrôleur ne sont pas modifiées ; seuls préparation, rechargement du lieu, ambiguïtés et clavier évoluent. |
| Validation | La validation déterministe extraite dans gestion.py conserve les contrôles existants ; Synapse l'appelle après résolution locale. |
| Carnet | Modèle, validation, recherche, CRUD, copies, migration des identifiants, écriture atomique et interface relus. Les fiches illisibles sont conservées et les choix ambigus bloqués. |
| Synapse | Priorité intention/carnet, favorite/site, Maison pour VISIO/DOMICILE, modes et provenance relus ; pas de réseau dans l'interpréteur. Le chargement du carnet peut migrer les anciens identifiants : « préparation sans écriture » n'est pas une garantie absolue pour ce cas ancien. |
| Navigation et focus | Écrans conservés, callbacks installés après construction, préparation invalidée au changement de calendrier. Validation native Windows déjà confirmée. |
| Code non actif | Le contrat de recherche externe est intentionnel et testé, sans fournisseur branché. Les fonctions de recherche du Carnet et le point d'entrée déterministe sont conservés ; aucune suppression opportuniste. |
| Tests | 137 cas passent ; stockage temporaire et Google simulé. Le test arithmétique initial n'apporte pas de couverture métier : il est conservé, sans être utilisé comme preuve fonctionnelle. |
| Dépendances/version | Une seule version applicative déclarée, tool.briefcase.version dans pyproject.toml. Passage à 0.0.4 uniquement ; dépendances inchangées. Les fichiers générés Briefcase ne sont pas des sources à versionner. |
| Documentation | CHANGELOG ne mentionnait que 0.0.1 ; ajout des notes de candidate 0.0.4. Synchronisation des documents de reprise sans effacer les validations historiques. |

La syntaxe de tous les fichiers Python de src/ et tests/ a été vérifiée par
compileall. Le TOML est lisible et déclare 0.0.4. Le diff de branche et le diff
final passent git diff --check. Aucun code applicatif ni test n'a été modifié
pendant cet audit ; aucun test de régression ajouté sans correction correspondante.
La suite complète passe avant et après le changement de version et la documentation.

Les tests s'appuient sur un backend Dummy : ils ne constituent pas des tests
WinForms/CLR. Le blocage de socket.connect couvre les connexions utilisées par
les tests actuels ; il ne constitue pas un pare-feu couvrant toutes les API réseau.
Les validations natives et Google proviennent des essais utilisateur documentés.

## Crash Windows : faits établis

Environnement rapporté : Python 3.13.3, Briefcase 0.4.4, toga-winforms 0.5.6,
pythonnet 3.1.0, clr_loader 0.3.1. Access violation intermittent à la fermeture,
trace dans proactor.py et pythonnet.unload()/clr_loader.

Reproductions rapportées : f244bd0, c92aaab et main 0.0.3 (78093a0), y compris
sur main avec environnement Briefcase neuf et fermeture immédiate sans interaction.
Ces comparaisons établissent l'antériorité à Synapse et au correctif de focus.
Elles n'excluent pas à elles seules un facteur commun au code Lumyn et à ses
dépendances. Aucune corruption de données n'a été observée ; absence d'observation
ne signifie pas garantie d'innocuité d'une violation mémoire.

## Lecture des sources amont et hypothèses

- [Toga 0.5.6, proactor.py](https://github.com/beeware/toga/blob/v0.5.6/winforms/src/toga_winforms/libs/proactor.py) : les ticks utilisent des continuations Task.Delay et un dispatcher .NET ; le rappel de sécurité se reprogramme. Le chemin de sortie ne montre pas d'annulation explicite de toutes ces continuations. Un rappel tardif pendant le déchargement est donc une hypothèse à instrumenter, pas une cause démontrée du crash Lumyn.
- [Toga 0.5.6, app.py](https://github.com/beeware/toga/blob/v0.5.6/winforms/src/toga_winforms/app.py) : thread STA, attente de sa fin, fermeture de la boucle dans le chemin normal. Le simple conseil « fermer la boucle » existe déjà en amont.
- [pythonnet 3.1.0](https://github.com/pythonnet/pythonnet/blob/v3.1.0/pythonnet/__init__.py) : unload est enregistré via atexit et appelle le shutdown du runtime. Cela explique la présence de cette couche dans la trace, sans prouver qu'elle a créé l'accès mémoire invalide.
- [Toga #3270](https://github.com/beeware/toga/pull/3270) corrige l'ancien nettoyage incomplet de boucle signalé dans #3266. Les mécanismes ApplicationExit et loop.close correspondants sont déjà présents dans 0.5.6 : réappliquer cet ancien correctif n'est pas une solution démontrée.
- [pythonnet #1977](https://github.com/pythonnet/pythonnet/issues/1977) contient des crashs de shutdown et une analyse de pointeur libéré, sur d'autres versions. La ressemblance ne prouve pas une cause identique pour Python 3.13.3/pythonnet 3.1.0. Changer l'allocateur pourrait seulement masquer un symptôme : ce n'est pas retenu comme correction.

## Pourquoi aucun correctif du crash n'est livré

L'environnement d'audit est Linux, sans WinForms ni runtime CLR Windows. Il ne
permet ni reproduction native, ni débogage du pointeur fautif, ni comparaison
avant/après d'un correctif. Le dépôt contient les comptes rendus et versions,
mais pas de dump natif permettant d'identifier l'instruction fautive.
Aucun correctif amont consulté n'est établi comme résolvant ce cas exact.

Ne pas désenregistrer pythonnet.unload, forcer os._exit, changer l'allocateur,
ajouter un délai arbitraire, appeler soi-même le shutdown CLR ou modifier les
internes privés de la boucle : cela pourrait masquer le défaut ou introduire
un blocage, sans démontrer sa résolution. Aucun de ces changements n'a été fait.

## Investigation native restante, distincte de la livraison

Dans un environnement Windows isolé aux mêmes versions, comparer une fenêtre
Toga minimale (sans Lumyn, sans Google) à Lumyn, en lancement direct puis via
Briefcase avec les mêmes options de développement. Conserver les versions
complètes, l'architecture, le runtime .NET, la commande, les options Python et
les traces de tous les threads pour chaque fermeture en erreur.

Un dump natif avec symboles doit permettre de distinguer un callback tardif d'un
problème de finalisation d'objet CLR/Python. Seulement après cette distinction,
valider une correction minimale sur l'exemple isolé puis les parcours Lumyn.
Ne pas publier de dump ou de journal contenant des données personnelles sans
vérification. Aucun signalement externe ni demande à un mainteneur envoyé ici.

## Défauts et limites conservés pour la livraison

- Crash intermittent de fermeture Windows, non corrigé, préexistant à 0.0.4.
- Parseur par règles : formulations non couvertes et dates concurrentes limitées ;
  lieu littéral non vérifié. Résumé à relire avant confirmation.
- Google synchrone, pas de transaction globale Google/local ni reprise garantie
  après double panne ; écritures multiprocessus non prises en charge.
- Parcours Carnet « Ajouter l'adresse » puis « Enregistrer la fiche » inchangé.
- Fournisseur externe inactif ; Android/OAuth Android/APK non validés.
- Aucun installateur 0.0.4 construit ou testé pendant cet audit.
