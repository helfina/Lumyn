"""Connexion de Lumyn à Google Calendar.

Cette version réutilise une seule connexion Google Calendar pendant toute
la durée de l'application, puis la ferme proprement à la fermeture de Lumyn.
Cela évite de recréer un client HTTP à chaque lecture, création, modification
ou suppression.
"""

import atexit
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


RACINE_PROJET = Path(__file__).resolve().parents[4]

FICHIER_CREDENTIALS = RACINE_PROJET / "credentials.json"
FICHIER_TOKEN = RACINE_PROJET / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
]

FUSEAU_LUMYN = ZoneInfo("Europe/Paris")


# ============================================================
# CONNEXION GOOGLE PARTAGÉE
# ============================================================

_IDENTIFIANTS_GOOGLE = None
_SERVICE_GOOGLE = None
_EVENEMENTS_GOOGLE_SUPPRIMES = set()

def obtenir_identifiants():
    """Obtient une autorisation valide pour Google Calendar."""

    global _IDENTIFIANTS_GOOGLE

    if (
        _IDENTIFIANTS_GOOGLE is not None
        and _IDENTIFIANTS_GOOGLE.valid
    ):
        return _IDENTIFIANTS_GOOGLE

    identifiants = None

    if FICHIER_TOKEN.exists():
        identifiants = Credentials.from_authorized_user_file(
            FICHIER_TOKEN,
            SCOPES,
        )

    if not identifiants or not identifiants.valid:

        if (
            identifiants
            and identifiants.expired
            and identifiants.refresh_token
        ):
            requete_refresh = Request()

            try:
                identifiants.refresh(
                    requete_refresh
                )

            finally:
                session = getattr(
                    requete_refresh,
                    "session",
                    None,
                )

                if session is not None:
                    try:
                        session.close()
                    except Exception:
                        pass

        else:
            if not FICHIER_CREDENTIALS.exists():
                raise FileNotFoundError(
                    "Le fichier credentials.json est introuvable."
                )

            flux = InstalledAppFlow.from_client_secrets_file(
                FICHIER_CREDENTIALS,
                SCOPES,
            )

            identifiants = flux.run_local_server(
                port=0
            )

        FICHIER_TOKEN.write_text(
            identifiants.to_json(),
            encoding="utf-8",
        )

    _IDENTIFIANTS_GOOGLE = identifiants

    return identifiants


def obtenir_service_google_calendar():
    """Retourne l'unique connexion Google Calendar utilisée par Lumyn."""

    global _SERVICE_GOOGLE

    if _SERVICE_GOOGLE is not None:
        return _SERVICE_GOOGLE

    identifiants = obtenir_identifiants()

    _SERVICE_GOOGLE = build(
        "calendar",
        "v3",
        credentials=identifiants,
        cache_discovery=False,
    )

    return _SERVICE_GOOGLE


def fermer_service_google_calendar():
    """Ferme proprement la connexion HTTP Google Calendar."""

    global _SERVICE_GOOGLE

    service = _SERVICE_GOOGLE
    _SERVICE_GOOGLE = None

    if service is None:
        return

    fermeture = getattr(
        service,
        "close",
        None,
    )

    if callable(fermeture):
        try:
            fermeture()
            return
        except Exception:
            pass

    # Secours pour les versions où Resource.close()
    # n'est pas disponible.
    http = getattr(
        service,
        "_http",
        None,
    )

    if http is not None:
        fermeture_http = getattr(
            http,
            "close",
            None,
        )

        if callable(fermeture_http):
            try:
                fermeture_http()
            except Exception:
                pass


atexit.register(
    fermer_service_google_calendar
)


# ============================================================
# CALENDRIERS GOOGLE
# ============================================================

def _lister_calendriers_bruts(service):
    """Récupère les objets CalendarList bruts depuis Google."""

    calendriers = []
    page_token = None

    while True:
        resultat = (
            service.calendarList()
            .list(
                pageToken=page_token,
                showHidden=True,
            )
            .execute()
        )

        for calendrier in resultat.get(
            "items",
            [],
        ):
            if calendrier.get(
                "deleted"
            ):
                continue

            if not calendrier.get(
                "id"
            ):
                continue

            calendriers.append(
                calendrier
            )

        page_token = resultat.get(
            "nextPageToken"
        )

        if not page_token:
            break

    return calendriers


def lister_calendriers_google():
    """Récupère la liste des calendriers Google disponibles."""

    service = obtenir_service_google_calendar()

    calendriers = []

    for calendrier in _lister_calendriers_bruts(
        service
    ):
        calendrier_id = calendrier[
            "id"
        ]

        calendriers.append(
            {
                "id": calendrier_id,

                "nom": (
                    calendrier.get(
                        "summaryOverride"
                    )
                    or calendrier.get(
                        "summary"
                    )
                    or "Calendrier Google"
                ),

                "couleur": (
                    calendrier.get(
                        "backgroundColor"
                    )
                    or "#6c757d"
                ),

                "selectionne_google": bool(
                    calendrier.get(
                        "selected"
                    )
                ),

                "masque_google": bool(
                    calendrier.get(
                        "hidden"
                    )
                ),

                "principal": bool(
                    calendrier.get(
                        "primary"
                    )
                ),

                "access_role": calendrier.get(
                    "accessRole",
                    "reader",
                ),
            }
        )

    return calendriers


# ============================================================
# CONSTRUCTION D'UN ÉVÉNEMENT
# ============================================================

def construire_corps_evenement_google(
    rendez_vous,
    duree_minutes=60,
):
    """Transforme un rendez-vous Lumyn en événement Google."""

    date_rdv = rendez_vous.get(
        "date"
    )

    if not date_rdv:
        raise ValueError(
            "Le rendez-vous n'a pas de date."
        )

    if isinstance(
        date_rdv,
        str,
    ):
        date_objet = datetime.fromisoformat(
            date_rdv
        ).date()

    else:
        date_objet = date_rdv

    heure_rdv = rendez_vous.get(
        "heure"
    )

    if not heure_rdv:
        raise ValueError(
            "Le rendez-vous n'a pas d'heure."
        )

    heure_texte = (
        str(heure_rdv)
        .strip()
        .lower()
        .replace(" ", "")
        .replace(":", "h")
    )

    if "h" not in heure_texte:
        raise ValueError(
            "Format d'heure invalide."
        )

    heures_texte, minutes_texte = (
        heure_texte.split(
            "h",
            1,
        )
    )

    heures = int(
        heures_texte
    )

    minutes = (
        int(minutes_texte)
        if minutes_texte
        else 0
    )

    debut = datetime(
        date_objet.year,
        date_objet.month,
        date_objet.day,
        heures,
        minutes,
        tzinfo=FUSEAU_LUMYN,
    )

    duree = rendez_vous.get(
        "duree_minutes",
        duree_minutes,
    )

    try:
        duree = int(
            duree
        )

    except (
        TypeError,
        ValueError,
    ):
        duree = duree_minutes

    if duree <= 0:
        duree = duree_minutes

    fin = debut + timedelta(
        minutes=duree
    )

    corps = {
        "summary": rendez_vous.get(
            "titre",
            "Rendez-vous Lumyn",
        ),

        "start": {
            "dateTime": debut.isoformat(),
            "timeZone": "Europe/Paris",
        },

        "end": {
            "dateTime": fin.isoformat(),
            "timeZone": "Europe/Paris",
        },

        # Notifications Lumyn par défaut :
        # - 1 jour avant
        # - 1 heure avant
        "reminders": {
            "useDefault": False,
            "overrides": [
                {
                    "method": "popup",
                    "minutes": 1440,
                },
                {
                    "method": "popup",
                    "minutes": 60,
                },
            ],
        },
    }

    lieu = rendez_vous.get(
        "lieu"
    )

    if lieu:
        corps[
            "location"
        ] = lieu

    return corps


# ============================================================
# CREATE
# ============================================================

def creer_evenement_google(
    rendez_vous,
    calendrier_id,
):
    """Crée réellement un rendez-vous dans Google Calendar."""

    service = obtenir_service_google_calendar()

    corps = construire_corps_evenement_google(
        rendez_vous
    )

    return (
        service.events()
        .insert(
            calendarId=calendrier_id,
            body=corps,
            sendUpdates="none",
        )
        .execute()
    )


# ============================================================
# UPDATE
# ============================================================

def modifier_evenement_google(
    rendez_vous,
    calendrier_id,
    google_event_id,
):
    """Met à jour un rendez-vous créé par Lumyn dans Google."""

    service = obtenir_service_google_calendar()

    corps = construire_corps_evenement_google(
        rendez_vous
    )

    return (
        service.events()
        .update(
            calendarId=calendrier_id,
            eventId=google_event_id,
            body=corps,
            sendUpdates="none",
        )
        .execute()
    )


def deplacer_evenement_google(
    calendrier_source_id,
    calendrier_destination_id,
    google_event_id,
):
    """Déplace un événement Lumyn vers un autre calendrier."""

    if (
        calendrier_source_id
        == calendrier_destination_id
    ):
        return {
            "id": google_event_id
        }

    service = obtenir_service_google_calendar()

    return (
        service.events()
        .move(
            calendarId=calendrier_source_id,
            eventId=google_event_id,
            destination=calendrier_destination_id,
            sendUpdates="none",
        )
        .execute()
    )


# ============================================================
# DELETE
# ============================================================

def supprimer_evenement_google(
    calendrier_id,
    google_event_id,
):
    """Supprime un rendez-vous Google et le masque immédiatement dans Lumyn."""

    service = obtenir_service_google_calendar()

    (
        service.events()
        .delete(
            calendarId=calendrier_id,
            eventId=google_event_id,
            sendUpdates="none",
        )
        .execute()
    )

    # Google a accepté la suppression.
    # Même si une lecture faite juste après renvoie encore
    # temporairement l'événement, Lumyn ne doit plus l'afficher.
    _EVENEMENTS_GOOGLE_SUPPRIMES.add(
        (
            calendrier_id,
            google_event_id,
        )
    )

    return True
# ============================================================
# READ
# ============================================================

def lister_evenements_google(
    annee,
    mois,
):
    """Récupère les événements Google visibles dans Lumyn."""

    service = obtenir_service_google_calendar()

    debut = datetime(
        annee,
        mois,
        1,
        tzinfo=FUSEAU_LUMYN,
    )

    if mois == 12:

        fin = datetime(
            annee + 1,
            1,
            1,
            tzinfo=FUSEAU_LUMYN,
        )

    else:

        fin = datetime(
            annee,
            mois + 1,
            1,
            tzinfo=FUSEAU_LUMYN,
        )

    calendriers = (
        _lister_calendriers_bruts(
            service
        )
    )

    tous_les_evenements = []

    for calendrier_google in calendriers:

        calendrier_id = (
            calendrier_google[
                "id"
            ]
        )

        nom_calendrier = (
            calendrier_google.get(
                "summaryOverride"
            )
            or calendrier_google.get(
                "summary"
            )
            or "Calendrier Google"
        )

        couleur_calendrier = (
            calendrier_google.get(
                "backgroundColor"
            )
        )

        page_token = None

        while True:

            resultat = (
                service.events()
                .list(
                    calendarId=calendrier_id,
                    timeMin=debut.isoformat(),
                    timeMax=fin.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                    showDeleted=False,
                    pageToken=page_token,
                )
                .execute()
            )

            for evenement in resultat.get(
                "items",
                [],
            ):

                evenement_id = (
                    evenement.get(
                        "id"
                    )
                )

                # -------------------------------------------------
                # Événement déjà supprimé par Lumyn
                # -------------------------------------------------

                if (
                    calendrier_id,
                    evenement_id,
                ) in _EVENEMENTS_GOOGLE_SUPPRIMES:

                    continue

                # -------------------------------------------------
                # Google indique lui-même qu'il est supprimé
                # -------------------------------------------------

                if (
                    evenement.get(
                        "status"
                    )
                    == "cancelled"
                ):

                    continue

                evenement[
                    "_lumyn_calendar_id"
                ] = calendrier_id

                evenement[
                    "_lumyn_calendar_name"
                ] = nom_calendrier

                evenement[
                    "_lumyn_calendar_color"
                ] = couleur_calendrier

                tous_les_evenements.append(
                    evenement
                )

            page_token = resultat.get(
                "nextPageToken"
            )

            if not page_token:

                break

    return tous_les_evenements

def simplifier_evenement_google(
    evenement,
):
    """Transforme un événement Google au format utilisé par Lumyn."""

    debut = evenement.get(
        "start",
        {},
    )

    date_heure = debut.get(
        "dateTime"
    )

    date_journee = debut.get(
        "date"
    )

    if date_heure:
        debut_datetime = (
            datetime.fromisoformat(
                date_heure.replace(
                    "Z",
                    "+00:00",
                )
            )
        )

        if debut_datetime.tzinfo is None:
            debut_datetime = (
                debut_datetime.replace(
                    tzinfo=FUSEAU_LUMYN
                )
            )

        else:
            debut_datetime = (
                debut_datetime.astimezone(
                    FUSEAU_LUMYN
                )
            )

        date_evenement = (
            debut_datetime.date().isoformat()
        )

        heure = debut_datetime.strftime(
            "%Hh%M"
        )

    else:
        date_evenement = date_journee
        heure = None

    return {
        "google_event_id": evenement.get(
            "id"
        ),

        "google_calendar_id": evenement.get(
            "_lumyn_calendar_id"
        ),

        "calendrier": evenement.get(
            "_lumyn_calendar_name",
            "Google Calendar",
        ),

        "couleur_calendrier": evenement.get(
            "_lumyn_calendar_color"
        ),

        "titre": evenement.get(
            "summary",
            "Sans titre",
        ),

        "date": date_evenement,

        "heure": heure,

        "type": evenement.get(
            "eventType",
            "default",
        ),
    }


def lister_evenements_google_simples(
    annee,
    mois,
):
    """Récupère tous les événements Google au format Lumyn."""

    evenements = lister_evenements_google(
        annee,
        mois,
    )

    return [
        simplifier_evenement_google(
            evenement
        )
        for evenement in evenements
    ]
