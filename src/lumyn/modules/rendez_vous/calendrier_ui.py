"""Calendrier mensuel responsive de Lumyn."""

import re
import calendar
from datetime import date
from html import escape

import toga
from toga.style.pack import COLUMN, ROW, Pack

from lumyn.modules.rendez_vous.agenda_google import (
    lister_evenements_google_simples,
)


NOMS_MOIS = [
    "",
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]

JOURS = [
    "Lun",
    "Mar",
    "Mer",
    "Jeu",
    "Ven",
    "Sam",
    "Dim",
]

def nettoyer_titre_evenement(titre, heure):
    """Retire l'heure du titre si elle correspond à l'heure du rendez-vous."""

    if not titre or not heure:
        return titre

    heure_google = re.match(
        r"^(\d{1,2})h(\d{2})$",
        heure,
    )

    heure_titre = re.match(
        r"^\s*(\d{1,2})\s*(?:h|:)\s*(\d{0,2})"
        r"\s*[-–—:]?\s*",
        titre,
        re.IGNORECASE,
    )

    if not heure_google or not heure_titre:
        return titre

    heure_google_h = int(
        heure_google.group(1)
    )

    heure_google_m = int(
        heure_google.group(2)
    )

    heure_titre_h = int(
        heure_titre.group(1)
    )

    minutes_titre = heure_titre.group(2)

    heure_titre_m = (
        int(minutes_titre)
        if minutes_titre
        else 0
    )

    if (
        heure_google_h == heure_titre_h
        and heure_google_m == heure_titre_m
    ):
        titre_nettoye = titre[
            heure_titre.end():
        ].strip()

        return titre_nettoye or titre

    return titre

    
def creer_html_calendrier(annee, mois, evenements):
    """Construit le calendrier mensuel HTML."""

    aujourd_hui = date.today()

    evenements_par_jour = {}

    for evenement in evenements:
        date_evenement = evenement.get("date")

        if not date_evenement:
            continue

        jour = int(date_evenement.split("-")[2])

        evenements_par_jour.setdefault(
            jour,
            [],
        ).append(evenement)

    calendrier = calendar.Calendar(
        firstweekday=0,
    )

    semaines = calendrier.monthdayscalendar(
        annee,
        mois,
    )

    cellules = []

    # En-têtes
    for nom_jour in JOURS:
        cellules.append(
            f'<div class="weekday">{nom_jour}</div>'
        )

    # Jours
    for semaine in semaines:
        for numero_jour in semaine:

            if numero_jour == 0:
                cellules.append(
                    '<div class="day empty"></div>'
                )
                continue

            classes = ["day"]

            if (
                numero_jour == aujourd_hui.day
                and mois == aujourd_hui.month
                and annee == aujourd_hui.year
            ):
                classes.append("today")

            contenus_evenements = []

            evenements_du_jour = evenements_par_jour.get(
                numero_jour,
                [],
            )

            # Maximum 3 événements visibles dans la case.
            for evenement in evenements_du_jour[:3]:

                heure_brute = evenement.get("heure") or ""

                titre_brut = evenement.get(
                    "titre",
                    "Sans titre",
                )

                titre_brut = nettoyer_titre_evenement(
                    titre_brut,
                    heure_brute,
                )

                titre = escape(titre_brut)
                heure = escape(heure_brute)
                
                if heure:
                    contenu = (
                        f'<span class="event-time">'
                        f'{heure}</span> '
                        f'<span class="event-title">'
                        f'{titre}</span>'
                    )
                else:
                    contenu = (
                        f'<span class="event-title">'
                        f'{titre}</span>'
                    )

                contenus_evenements.append(
                    f'<div class="event">{contenu}</div>'
                )

            nombre_cache = (
                len(evenements_du_jour)
                - len(contenus_evenements)
            )

            if nombre_cache > 0:
                contenus_evenements.append(
                    f'<div class="more">'
                    f'+{nombre_cache} autre(s)'
                    f'</div>'
                )

            cellules.append(
                f"""
                <div class="{" ".join(classes)}">
                    <div class="day-number">
                        {numero_jour}
                    </div>

                    <div class="events">
                        {"".join(contenus_evenements)}
                    </div>
                </div>
                """
            )

    return f"""
    <!DOCTYPE html>

    <html lang="fr">

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >

        <style>

            * {{
                box-sizing: border-box;
            }}

            html,
            body {{
                margin: 0;
                padding: 0;

                font-family:
                    -apple-system,
                    BlinkMacSystemFont,
                    "Segoe UI",
                    sans-serif;

                background: #f8f9fa;

                color: #212529;
            }}

            .calendar {{
                width: 100%;

                display: grid;

                /*
                IMPORTANT :
                toujours exactement
                7 colonnes identiques.
                */
                grid-template-columns:
                    repeat(7, minmax(0, 1fr));

                border-top: 1px solid #dee2e6;
                border-left: 1px solid #dee2e6;
            }}

            .weekday {{
                min-width: 0;

                padding: 10px 4px;

                text-align: center;

                font-weight: 700;

                background: #f1f3f5;

                border-right: 1px solid #dee2e6;
                border-bottom: 1px solid #dee2e6;
            }}

            .day {{
                /*
                min-width: 0 empêche le texte
                d'élargir la colonne.
                */
                min-width: 0;

                min-height:
                    clamp(75px, 9vw, 125px);

                padding: 7px;

                overflow: hidden;

                background: white;

                border-right: 1px solid #dee2e6;
                border-bottom: 1px solid #dee2e6;
            }}

            .day.empty {{
                background: #f8f9fa;
            }}

            .day-number {{
                margin-bottom: 5px;

                font-weight: 700;

                font-size: 14px;
            }}

            .today .day-number {{
                display: inline-block;

                padding: 2px 7px;

                border-radius: 100px;

                background: #212529;

                color: white;
            }}

            .events {{
                min-width: 0;
            }}

            .event {{
                min-width: 0;

                margin-bottom: 4px;

                padding: 4px 6px;

                border-radius: 5px;

                background: #eef2f6;

                font-size: 12px;

                line-height: 1.25;

                /*
                Le texte n'a jamais
                le droit d'agrandir la case.
                */
                overflow: hidden;

                overflow-wrap: anywhere;

                word-break: break-word;
            }}

            .event-time {{
                font-weight: 700;
            }}

            .event-title {{
                /*
                Maximum deux lignes.
                */
                display: -webkit-box;

                -webkit-box-orient: vertical;
                -webkit-line-clamp: 2;

                overflow: hidden;
            }}

            .more {{
                padding-left: 3px;

                font-size: 11px;

                font-weight: 600;

                color: #6c757d;
            }}


            /*
            TABLETTE / PETITE FENÊTRE
            */

            @media (max-width: 900px) {{

                .weekday {{
                    padding: 8px 2px;

                    font-size: 12px;
                }}

                .day {{
                    min-height: 90px;

                    padding: 5px;
                }}

                .day-number {{
                    font-size: 12px;
                }}

                .event {{
                    padding: 3px 4px;

                    font-size: 10px;
                }}

            }}


            /*
            MOBILE
            */

            @media (max-width: 550px) {{

                .weekday {{
                    padding: 6px 1px;

                    font-size: 10px;
                }}

                .day {{
                    min-height: 70px;

                    padding: 3px;
                }}

                .day-number {{
                    margin-bottom: 2px;

                    font-size: 11px;
                }}

                .event {{
                    margin-bottom: 2px;

                    padding: 2px;

                    font-size: 9px;

                    border-radius: 3px;
                }}

                /*
                Sur téléphone :
                une seule ligne par événement.
                */
                .event-title {{
                    -webkit-line-clamp: 1;
                }}

                .more {{
                    font-size: 8px;
                }}

            }}

        </style>

    </head>

    <body>

        <div class="calendar">

            {"".join(cellules)}

        </div>

    </body>

    </html>
    """


def creer_calendrier_mensuel():
    """Crée le calendrier Google responsive."""

    aujourd_hui = date.today()

    etat = {
        "annee": aujourd_hui.year,
        "mois": aujourd_hui.month,
    }

    conteneur = toga.Box(
        style=Pack(
            direction=COLUMN,
            gap=8,
            margin_top=15,
        )
    )

    # ---------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------

    navigation = toga.Box(
        style=Pack(
            direction=ROW,
            gap=8,
        )
    )

    titre = toga.Label(
        "",
        style=Pack(
            flex=1,
            text_align="center",
            font_size=18,
            font_weight="bold",
            margin_top=7,
        )
    )

    webview = toga.WebView(
        style=Pack(
            flex=1,
            height=650,
        )
    )

    def charger_mois():
        """Charge les événements et actualise le calendrier."""

        annee = etat["annee"]
        mois = etat["mois"]

        titre.text = (
            f"{NOMS_MOIS[mois]} {annee}"
        )

        try:
            evenements = (
                lister_evenements_google_simples(
                    annee,
                    mois,
                )
            )

            contenu = creer_html_calendrier(
                annee,
                mois,
                evenements,
            )

        except Exception as erreur:

            contenu = f"""
            <html>
            <body
                style="
                    font-family: sans-serif;
                    padding: 20px;
                "
            >
                Impossible de charger le calendrier :
                {escape(str(erreur))}
            </body>
            </html>
            """

        webview.set_content(
            "",
            contenu,
        )

    def mois_precedent(widget, **kwargs):
        """Affiche le mois précédent."""

        etat["mois"] -= 1

        if etat["mois"] == 0:
            etat["mois"] = 12
            etat["annee"] -= 1

        charger_mois()

    def mois_suivant(widget, **kwargs):
        """Affiche le mois suivant."""

        etat["mois"] += 1

        if etat["mois"] == 13:
            etat["mois"] = 1
            etat["annee"] += 1

        charger_mois()

    precedent = toga.Button(
        "←",
        on_press=mois_precedent,
        style=Pack(
            width=50,
        )
    )

    suivant = toga.Button(
        "→",
        on_press=mois_suivant,
        style=Pack(
            width=50,
        )
    )

    navigation.add(
        precedent,
        titre,
        suivant,
    )

    conteneur.add(
        navigation,
        webview,
    )

    charger_mois()

    return conteneur