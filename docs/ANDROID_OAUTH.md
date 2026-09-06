# Android et OAuth Google — préparation du 06/09/2026

**État : audité et documenté, pas implémenté ni validé sur appareil.** Aucun SDK,
émulateur, APK/AAB, compte Cloud ou jeton mobile créé pendant cette séance.
Version Lumyn 0.0.4 inchangée. Les validations Windows ne prouvent pas Android.

## État du dépôt

| Élément | Présent | Travail restant |
| --- | --- | --- |
| Briefcase Android | Section pyproject, toga-android~=0.5.0, thème Material, dépendance Material 1.13.0 | Générer puis vérifier template, API SDK, ABI/Python et manifeste réels |
| Interface | Toga commun, widgets testés sous Dummy | Clavier mobile, focus, navigation, liste de propositions et reprise d'activité |
| Google client Python | Dépendances Google communes déclarées | Vérifier toutes les roues/transitives Android ; ne pas déclarer incompatibilité sans résultat de build |
| OAuth desktop | InstalledAppFlow.run_local_server(port=0), credentials.json et token.json près de la racine | Flux natif distinct ; ne pas réutiliser le callback loopback desktop |
| Stockage métier | JSON sous Path.home()/.lumyn | Vérifier le dossier privé mobile ; préparer migration vers App.paths.data sans perdre les fichiers desktop |
| Secrets | Fichiers OAuth desktop exclus de Git | Ne pas les inclure dans APK, logs ou sauvegardes Android ; gestion du jeton natif à concevoir |
| Permissions | Pas de déclaration réseau Android explicite dans le projet | Vérifier INTERNET dans manifeste généré ; aucun besoin de localisation GPS pour une ville saisie |

La [documentation Briefcase Gradle](https://briefcase.beeware.org/en/stable/reference/platforms/android/gradle/)
décrit les trois sorties : AAB, APK release, APK debug. Les dépendances binaires
nécessitent des roues Android compatibles ; seul un build permet de conclure pour
ce projet. La documentation stable a été consultée ; la page versionnée 0.4.4
n'était pas accessible pendant cet audit. Vérifier l'aide de la version installée.

## OAuth : séparation nécessaire

Le flux Google actuel est un flux desktop, avec serveur loopback et écriture
locale de jeton. Google ne supporte plus ce schéma de redirection pour Android ;
un schéma URI personnalisé n'est pas une substitution générique sûre.
Les applications installées ne peuvent pas garder un secret client confidentiel.
Voir [OAuth applications natives](https://developers.google.com/identity/protocols/oauth2/native-app).

Voie à évaluer : `AuthorizationClient` Google Identity pour demander les scopes
Calendar, via le pont Java Android, avec gestion des résultats d'activité,
annulation, expiration et renouvellement. Il s'agit d'autoriser Calendar, pas
seulement de connecter une identité. L'intégration Toga/Chaquopy reste à développer
et tester ; aucun client web/serveur ni pont Java spéculatif n'est ajouté ici.

Dans Google Cloud, l'utilisatrice devra vérifier Calendar API, l'écran de
consentement/audience, les comptes de test et les scopes réellement nécessaires.
Créer le client OAuth Android avec **le package généré vérifié** et l'empreinte
SHA-1 du certificat utilisé (debug puis release/Play distincts). Le bundle
`fr.helfina` et l'app `lumyn` suggèrent `fr.helfina.lumyn`, à confirmer dans le
projet généré. Voir [autorisation Android Google](https://developer.android.com/identity/authorization).
Ne pas modifier le client desktop validé pour faire cet essai.

Éviter un token.json en clair à la racine de l'application. Privilégier la gestion
native Google des accès ; si un secret doit être persisté, stockage privé chiffré
avec clé protégée par Android Keystore, exclusion des sauvegardes, effacement à
la déconnexion et masquage des logs. Keystore protège des clés, pas directement
un fichier JSON : [documentation Android](https://developer.android.com/privacy-and-security/keystore).
Aucune migration de jetons existants n'est effectuée dans ce lot.

## Commandes PowerShell pour une future validation

À exécuter volontairement sur le poste Windows avec connexion Internet. Ces
commandes téléchargent outils et dépendances ; elles n'ont pas été exécutées ici.
Conserver l'environnement desktop existant. Depuis la racine du dépôt :

```powershell
git fetch origin
git switch feature/google-reprise-recherche-lieux
git status --short --branch
py -3.13 -m venv .venv-android
.\.venv-android\Scripts\python.exe -m pip install "briefcase==0.4.4"
.\.venv-android\Scripts\python.exe -m briefcase --version
.\.venv-android\Scripts\python.exe -m briefcase create android --help
.\.venv-android\Scripts\python.exe -m briefcase package android --help
.\.venv-android\Scripts\python.exe -m briefcase create android
.\.venv-android\Scripts\python.exe -m briefcase build android
.\.venv-android\Scripts\python.exe -m briefcase run android
.\.venv-android\Scripts\python.exe -m briefcase package android -p debug-apk
Get-ChildItem .\dist\ -Filter *.apk
```

Choisir explicitement le téléphone ou l'émulateur proposé par Briefcase. Après
changement de source, `briefcase update android` puis `briefcase build android`
avec le même exécutable de l'environnement ci-dessus. Pour les dépendances,
consulter les options de `update android --help` avant mise à jour.

Après création, inspecter les identifiants/permissions et relever le certificat
debug du projet ; avec le JDK utilisé par Briefcase disponible pour Gradle :

```powershell
Get-ChildItem .\build\lumyn\android\ -Recurse -Filter AndroidManifest.xml |
    Select-String -Pattern 'package=|android.permission.INTERNET'
Get-ChildItem .\build\lumyn\android\ -Recurse -Filter build.gradle* |
    Select-String -Pattern 'applicationId|namespace'
$lumynGradle = Get-ChildItem .\build\lumyn\android\ -Recurse -Filter gradlew.bat |
    Select-Object -First 1
if ($null -eq $lumynGradle) { throw 'Projet Gradle non généré' }
Push-Location $lumynGradle.DirectoryName
try { & $lumynGradle.FullName signingReport } finally { Pop-Location }
```

Ne jamais publier de clé privée ni de jeton avec ces résultats. Les empreintes
identifient le certificat : ne pas confondre debug, upload et signature Play.
Si JDK/SDK manque, suivre le diagnostic Briefcase ; ne pas changer les dépendances
Windows pour contourner une erreur Android.

Plus tard seulement, après validation et décision de signature/distribution :

```powershell
.\.venv-android\Scripts\python.exe -m briefcase package android -p apk
.\.venv-android\Scripts\python.exe -m briefcase package android -p aab
```

Ces commandes préparent des artefacts ; elles ne constituent pas une publication
Play ni une preuve de signature/distribution valide. Conserver les clés de
signature hors dépôt. Ne pas lancer OAuth desktop sur Android en guise de test.

## Contrôles avant de déclarer Android utilisable

1. Démarrer et utiliser le mode local sans Google : Carnet, Maison, saisie,
   confirmation, navigation, données conservées après fermeture/redémarrage.
2. Vérifier les dépendances, permissions finales, absence de secrets empaquetés,
   stockage privé, clavier et mise en arrière-plan/reprise de l'activité.
3. Après intégration native : consentement/refus, retour à l'application,
   expiration, révocation et déconnexion, sans fuite dans les logs.
4. Avec un calendrier de test explicitement choisi : CREATE/UPDATE/MOVE/DELETE,
   cohérence des IDs et un seul événement ; panne réseau et reprise contrôlées.
5. Réexécuter les tests simulés et documenter appareil, Android, ABI, Python,
   Briefcase/Toga, commit et résultats. Un build réussi ne valide pas OAuth.

Ces étapes nécessitent l'intervention de l'utilisatrice pour Cloud Console,
certificats, appareil et Google réel. Aucun de ces résultats n'est acquis ici.
