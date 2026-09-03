"""Connexion de Lumyn à Google Calendar."""

from datetime import datetime
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

def obtenir_identifiants():
    """Obtient une autorisation valide pour Google Calendar."""

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
            identifiants.refresh(Request())

        else:
            if not FICHIER_CREDENTIALS.exists():
                raise FileNotFoundError(
                    "Le fichier credentials.json est introuvable."
                )

            flux = InstalledAppFlow.from_client_secrets_file(
                FICHIER_CREDENTIALS,
                SCOPES,
            )

            identifiants = flux.run_local_server(port=0)

        FICHIER_TOKEN.write_text(
            identifiants.to_json(),
            encoding="utf-8",
        )

    return identifiants


def obtenir_service_google_calendar():
    """Crée une connexion autorisée à Google Calendar."""

    identifiants = obtenir_identifiants()

    return build(
        "calendar",
        "v3",
        credentials=identifiants,
    )

def lister_calendriers_google():
    """Récupère la liste des calendriers disponibles dans Google."""

    service = obtenir_service_google_calendar()

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
            if calendrier.get("deleted"):
                continue

            calendrier_id = calendrier.get("id")

            if not calendrier_id:
                continue

            calendriers.append(
                {
                    "id": calendrier_id,

                    "nom": (
                        calendrier.get("summaryOverride")
                        or calendrier.get("summary")
                        or "Calendrier Google"
                    ),

                    "couleur": (
                        calendrier.get("backgroundColor")
                        or "#6c757d"
                    ),

                    "selectionne_google": bool(
                        calendrier.get("selected")
                    ),

                    "masque_google": bool(
                        calendrier.get("hidden")
                    ),
                }
            )

        page_token = resultat.get(
            "nextPageToken"
        )

        if not page_token:
            break

    return calendriers

def lister_evenements_google(annee, mois):
    """Récupère les événements de tous les calendriers Google."""

    service = obtenir_service_google_calendar()

    debut = datetime(
        annee,
        mois,
        1,
    ).astimezone()

    # Premier jour du mois suivant.
    if mois == 12:
        fin = datetime(
            annee + 1,
            1,
            1,
        ).astimezone()
    else:
        fin = datetime(
            annee,
            mois + 1,
            1,
        ).astimezone()

    # ---------------------------------------------------------
    # Liste des calendriers Google
    # ---------------------------------------------------------

    calendriers = []
    page_token = None

    while True:

        resultat_calendriers = (
            service.calendarList()
            .list(
                pageToken=page_token,
                showHidden=True,
            )
            .execute()
        )

        calendriers.extend(
            resultat_calendriers.get(
                "items",
                [],
            )
        )

        page_token = resultat_calendriers.get(
            "nextPageToken"
        )

        if not page_token:
            break

    # ---------------------------------------------------------
    # Événements de chaque calendrier
    # ---------------------------------------------------------

    tous_les_evenements = []

    for calendrier_google in calendriers:

        calendrier_id = calendrier_google["id"]

        nom_calendrier = calendrier_google.get(
            "summary",
            "Calendrier Google",
        )

        couleur_calendrier = calendrier_google.get(
            "backgroundColor"
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
                    pageToken=page_token,
                )
                .execute()
            )

            for evenement in resultat.get(
                "items",
                [],
            ):

                # Informations propres à Lumyn.
                evenement["_lumyn_calendar_id"] = (
                    calendrier_id
                )

                evenement["_lumyn_calendar_name"] = (
                    nom_calendrier
                )

                evenement["_lumyn_calendar_color"] = (
                    couleur_calendrier
                )

                tous_les_evenements.append(
                    evenement
                )

            page_token = resultat.get(
                "nextPageToken"
            )

            if not page_token:
                break

    return tous_les_evenements


def simplifier_evenement_google(evenement):
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
        debut_datetime = datetime.fromisoformat(
            date_heure.replace("Z", "+00:00")
        )

        if debut_datetime.tzinfo is None:
            debut_datetime = debut_datetime.replace(
                tzinfo=FUSEAU_LUMYN
            )
        else:
            debut_datetime = debut_datetime.astimezone(
                FUSEAU_LUMYN
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
        "google_event_id": evenement.get("id"),

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

def lister_evenements_google_simples(annee, mois):
    """Récupère tous les événements Google au format Lumyn."""

    evenements = lister_evenements_google(
        annee,
        mois,
    )

    return [
        simplifier_evenement_google(evenement)
        for evenement in evenements
    ]