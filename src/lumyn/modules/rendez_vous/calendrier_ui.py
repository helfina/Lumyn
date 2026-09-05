"""Calendrier mensuel responsive de Lumyn."""

import calendar
import re
from datetime import date
from html import escape

import toga
from toga.style.pack import COLUMN, ROW, Pack

from lumyn.modules.rendez_vous.agenda_google import (
    lister_calendriers_google,
    lister_evenements_google_simples,
)

import json
from pathlib import Path

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

MAX_EVENEMENTS_PAR_JOUR = 3
COULEUR_PAR_DEFAUT = "#eef2f6"

DOSSIER_LUMYN = Path.home() / ".lumyn"

FICHIER_PREFERENCES_CALENDRIERS = (
    DOSSIER_LUMYN
    / "calendriers_affichage.json"
)


def nettoyer_titre_evenement(titre, heure):
    """Retire l'heure du titre si elle correspond à l'heure réelle."""

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

    heure_google_h = int(heure_google.group(1))
    heure_google_m = int(heure_google.group(2))

    heure_titre_h = int(heure_titre.group(1))

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


def couleur_valide(couleur):
    """Vérifie qu'une couleur est au format #RRGGBB."""

    return bool(
        couleur
        and re.fullmatch(
            r"#[0-9A-Fa-f]{6}",
            couleur,
        )
    )


def couleur_texte_pour_fond(couleur):
    """Choisit automatiquement du texte noir ou blanc."""

    if not couleur_valide(couleur):
        return "#212529"

    rouge = int(
        couleur[1:3],
        16,
    )

    vert = int(
        couleur[3:5],
        16,
    )

    bleu = int(
        couleur[5:7],
        16,
    )

    luminosite = (
        rouge * 0.299
        + vert * 0.587
        + bleu * 0.114
    )

    if luminosite > 160:
        return "#212529"

    return "#ffffff"

def charger_preferences_calendriers():
    """Charge les calendriers affichés ou masqués par l'utilisateur."""

    if not FICHIER_PREFERENCES_CALENDRIERS.exists():
        return {}

    try:
        with FICHIER_PREFERENCES_CALENDRIERS.open(
            "r",
            encoding="utf-8",
        ) as fichier:
            donnees = json.load(fichier)

        if not isinstance(donnees, dict):
            return {}

        return {
            str(calendrier_id): bool(actif)
            for calendrier_id, actif
            in donnees.items()
        }

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}


def sauvegarder_preferences_calendriers(
    preferences,
):
    """Enregistre les calendriers affichés ou masqués."""

    DOSSIER_LUMYN.mkdir(
        parents=True,
        exist_ok=True,
    )

    with FICHIER_PREFERENCES_CALENDRIERS.open(
        "w",
        encoding="utf-8",
    ) as fichier:
        json.dump(
            preferences,
            fichier,
            ensure_ascii=False,
            indent=4,
        )

def creer_html_calendrier(
    annee,
    mois,
    evenements,
):
    """Construit le calendrier mensuel HTML."""

    aujourd_hui = date.today()

    evenements_par_jour = {}

    # ---------------------------------------------------------
    # Classe les événements dans leur journée
    # ---------------------------------------------------------

    for evenement in evenements:

        date_evenement = evenement.get(
            "date"
        )

        if not date_evenement:
            continue

        try:
            jour = int(
                date_evenement.split("-")[2]
            )

        except (IndexError, ValueError):
            continue

        evenements_par_jour.setdefault(
            jour,
            [],
        ).append(
            evenement
        )

    # ---------------------------------------------------------
    # Trie les événements de chaque journée
    # ---------------------------------------------------------

    for evenements_du_jour in (
        evenements_par_jour.values()
    ):

        evenements_du_jour.sort(
            key=lambda evenement: (
                evenement.get("heure") is not None,
                evenement.get("heure") or "",
            )
        )

    # ---------------------------------------------------------
    # Construction du mois
    # ---------------------------------------------------------

    calendrier = calendar.Calendar(
        firstweekday=0,
    )

    semaines = calendrier.monthdayscalendar(
        annee,
        mois,
    )

    cellules = []

    # ---------------------------------------------------------
    # En-têtes
    # ---------------------------------------------------------

    for nom_jour in JOURS:

        cellules.append(
            f"""
            <div class="weekday">
                {escape(nom_jour)}
            </div>
            """
        )

    # ---------------------------------------------------------
    # Cases des journées
    # ---------------------------------------------------------

    for semaine in semaines:

        for numero_jour in semaine:

            if numero_jour == 0:

                cellules.append(
                    '<div class="day empty"></div>'
                )

                continue

            classes = [
                "day"
            ]

            if (
                numero_jour == aujourd_hui.day
                and mois == aujourd_hui.month
                and annee == aujourd_hui.year
            ):
                classes.append(
                    "today"
                )

            contenus_evenements = []

            evenements_du_jour = (
                evenements_par_jour.get(
                    numero_jour,
                    [],
                )
            )

            # -------------------------------------------------
            # Maximum 3 événements visibles dans une case
            # -------------------------------------------------

            for evenement in (
                evenements_du_jour[
                    :MAX_EVENEMENTS_PAR_JOUR
                ]
            ):

                heure_brute = (
                    evenement.get("heure")
                    or ""
                )

                titre_brut = evenement.get(
                    "titre",
                    "Sans titre",
                )

                titre_brut = nettoyer_titre_evenement(
                    titre_brut,
                    heure_brute,
                )

                titre = escape(
                    titre_brut
                )

                heure = escape(
                    heure_brute
                )

                # ---------------------------------------------
                # Couleur propre à cet événement
                # ---------------------------------------------

                couleur = evenement.get(
                    "couleur_calendrier"
                )

                if not couleur_valide(
                    couleur
                ):
                    couleur = COULEUR_PAR_DEFAUT

                couleur_texte = (
                    couleur_texte_pour_fond(
                        couleur
                    )
                )

                nom_calendrier = escape(
                    evenement.get(
                        "calendrier",
                        "Google Calendar",
                    )
                )

                # ---------------------------------------------
                # Contenu de l'événement
                # ---------------------------------------------

                if heure:

                    contenu = (
                        f'<span class="event-time">'
                        f'{heure}'
                        f'</span>'
                        f'<span class="event-title">'
                        f'{titre}'
                        f'</span>'
                    )

                else:

                    contenu = (
                        f'<span class="event-title">'
                        f'{titre}'
                        f'</span>'
                    )

                contenus_evenements.append(
                    f"""
                    <div
                        class="event"
                        title="{nom_calendrier}"
                        style="
                            background-color: {couleur};
                            color: {couleur_texte};
                        "
                    >
                        {contenu}
                    </div>
                    """
                )

            # -------------------------------------------------
            # Événements supplémentaires
            # -------------------------------------------------

            nombre_cache = (
                len(evenements_du_jour)
                - min(
                    len(evenements_du_jour),
                    MAX_EVENEMENTS_PAR_JOUR,
                )
            )

            if nombre_cache > 0:

                contenus_evenements.append(
                    f"""
                    <div class="more">
                        +{nombre_cache} autre(s)
                    </div>
                    """
                )

            # -------------------------------------------------
            # Case complète
            # -------------------------------------------------

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

    # ---------------------------------------------------------
    # HTML + CSS responsive
    # ---------------------------------------------------------

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

                grid-template-columns:
                    repeat(
                        7,
                        minmax(0, 1fr)
                    );

                border-top:
                    1px solid #dee2e6;

                border-left:
                    1px solid #dee2e6;
            }}

            .weekday {{
                min-width: 0;

                padding: 10px 4px;

                text-align: center;

                font-weight: 700;

                background: #f1f3f5;

                border-right:
                    1px solid #dee2e6;

                border-bottom:
                    1px solid #dee2e6;
            }}

            .day {{
                min-width: 0;

                min-height:
                    clamp(
                        75px,
                        9vw,
                        125px
                    );

                padding: 7px;

                overflow: hidden;

                background: white;

                border-right:
                    1px solid #dee2e6;

                border-bottom:
                    1px solid #dee2e6;
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

                padding: 5px 6px;

                border-radius: 6px;

                font-size: 12px;

                line-height: 1.25;

                overflow: hidden;

                overflow-wrap: anywhere;

                word-break: break-word;
            }}

            .event-time {{
                display: block;

                margin-bottom: 2px;

                font-weight: 700;
            }}

            .event-title {{
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

            /* -----------------------------------------------
               Tablette / petite fenêtre
               ----------------------------------------------- */

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
                    padding: 4px;

                    font-size: 10px;
                }}

            }}

            /* -----------------------------------------------
               Mobile
               ----------------------------------------------- */

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

                    padding: 3px;

                    font-size: 9px;

                    border-radius: 4px;
                }}

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
    """Crée le calendrier Google responsive avec filtres mémorisés."""

    aujourd_hui = date.today()

    etat = {
        "annee": aujourd_hui.year,
        "mois": aujourd_hui.month,
        "calendriers_actifs": {},
        "filtres_ouverts": False,
        "mise_a_jour_filtres": False,
    }

    preferences = (
        charger_preferences_calendriers()
    )

    cache_evenements = {
        "cle": None,
        "evenements": [],
    }

    interrupteurs = {}

    # ---------------------------------------------------------
    # Conteneur principal
    # ---------------------------------------------------------

    conteneur = toga.Box(
        style=Pack(
            direction=COLUMN,
            gap=8,
            margin_top=15,
        )
    )

    # ---------------------------------------------------------
    # Navigation du mois
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

    # ---------------------------------------------------------
    # Zone des filtres
    # ---------------------------------------------------------

    zone_filtres = toga.Box(
        style=Pack(
            direction=COLUMN,
            gap=5,
        )
    )

    filtres_contenu = toga.Box(
        style=Pack(
            direction=COLUMN,
            gap=4,
            margin_bottom=8,
        )
    )

    actions_filtres = toga.Box(
        style=Pack(
            direction=ROW,
            gap=6,
            margin_bottom=5,
        )
    )

    # ---------------------------------------------------------
    # WebView
    #
    # Sa hauteur sera recalculée selon le nombre
    # de semaines du mois pour éviter son propre scroll.
    # ---------------------------------------------------------

    webview = toga.WebView(
        style=Pack(
            height=800,
        )
    )

    # ---------------------------------------------------------
    # Calcule la hauteur nécessaire au calendrier
    # ---------------------------------------------------------

    def calculer_hauteur_calendrier(
        annee,
        mois,
    ):
        """Calcule une hauteur suffisante pour afficher le mois entier."""

        calendrier_python = calendar.Calendar(
            firstweekday=0,
        )

        semaines = (
            calendrier_python.monthdayscalendar(
                annee,
                mois,
            )
        )

        nombre_semaines = len(
            semaines
        )

        # En-tête Lun/Mar/Mer...
        hauteur_entete = 55

        # On laisse suffisamment de place à chaque semaine
        # pour les cartes de rendez-vous.
        hauteur_semaine = 150

        # Petite marge de sécurité.
        marge = 30

        return (
            hauteur_entete
            + (
                nombre_semaines
                * hauteur_semaine
            )
            + marge
        )

    # ---------------------------------------------------------
    # Mise à jour du bouton des filtres
    # ---------------------------------------------------------

    def mettre_a_jour_bouton_filtres():
        """Met à jour le nombre de calendriers affichés."""

        total = len(
            etat["calendriers_actifs"]
        )

        actifs = sum(
            1
            for actif
            in etat[
                "calendriers_actifs"
            ].values()
            if actif
        )

        if etat["filtres_ouverts"]:
            symbole = "▲"
        else:
            symbole = "▼"

        bouton_filtres.text = (
            f"⚙ Calendriers "
            f"({actifs}/{total} affichés) "
            f"{symbole}"
        )

    # ---------------------------------------------------------
    # Chargement du mois
    # ---------------------------------------------------------

    def charger_mois():
        """Charge les événements et actualise le calendrier."""

        annee = etat["annee"]
        mois = etat["mois"]

        titre.text = (
            f"{NOMS_MOIS[mois]} {annee}"
        )

        # Adapte la hauteur du WebView au mois.
        webview.style.height = (
            calculer_hauteur_calendrier(
                annee,
                mois,
            )
        )

        try:

            cle_mois = (
                annee,
                mois,
            )

            # Nouvel appel Google uniquement
            # lorsque le mois change.
            if (
                cache_evenements["cle"]
                != cle_mois
            ):

                cache_evenements[
                    "evenements"
                ] = (
                    lister_evenements_google_simples(
                        annee,
                        mois,
                    )
                )

                cache_evenements[
                    "cle"
                ] = cle_mois

            # -------------------------------------------------
            # Filtrage local
            # -------------------------------------------------

            evenements = [
                evenement

                for evenement
                in cache_evenements[
                    "evenements"
                ]

                if etat[
                    "calendriers_actifs"
                ].get(
                    evenement.get(
                        "google_calendar_id"
                    ),
                    True,
                )
            ]

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

    # ---------------------------------------------------------
    # Activation / désactivation d'un calendrier
    # ---------------------------------------------------------

    def changer_calendrier(
        widget,
        calendrier_id=None,
        **kwargs,
    ):
        """Affiche ou masque un calendrier."""

        if calendrier_id is None:
            return

        etat["calendriers_actifs"][
            calendrier_id
        ] = bool(
            widget.value
        )

        if etat[
            "mise_a_jour_filtres"
        ]:
            return

        sauvegarder_preferences_calendriers(
            etat[
                "calendriers_actifs"
            ]
        )

        mettre_a_jour_bouton_filtres()

        charger_mois()

    # ---------------------------------------------------------
    # Tout afficher
    # ---------------------------------------------------------

    def tout_afficher(
        widget,
        **kwargs,
    ):
        """Affiche tous les calendriers."""

        etat[
            "mise_a_jour_filtres"
        ] = True

        try:

            for calendrier_id, interrupteur in (
                interrupteurs.items()
            ):

                etat[
                    "calendriers_actifs"
                ][
                    calendrier_id
                ] = True

                interrupteur.value = True

        finally:

            etat[
                "mise_a_jour_filtres"
            ] = False

        sauvegarder_preferences_calendriers(
            etat[
                "calendriers_actifs"
            ]
        )

        mettre_a_jour_bouton_filtres()

        charger_mois()

    # ---------------------------------------------------------
    # Tout masquer
    # ---------------------------------------------------------

    def tout_masquer(
        widget,
        **kwargs,
    ):
        """Masque tous les calendriers."""

        etat[
            "mise_a_jour_filtres"
        ] = True

        try:

            for calendrier_id, interrupteur in (
                interrupteurs.items()
            ):

                etat[
                    "calendriers_actifs"
                ][
                    calendrier_id
                ] = False

                interrupteur.value = False

        finally:

            etat[
                "mise_a_jour_filtres"
            ] = False

        sauvegarder_preferences_calendriers(
            etat[
                "calendriers_actifs"
            ]
        )

        mettre_a_jour_bouton_filtres()

        charger_mois()

    # ---------------------------------------------------------
    # Ouverture / fermeture du panneau Calendriers
    # ---------------------------------------------------------

    def basculer_filtres(
        widget,
        **kwargs,
    ):
        """Ouvre ou ferme la liste des calendriers."""

        etat[
            "filtres_ouverts"
        ] = not etat[
            "filtres_ouverts"
        ]

        zone_filtres.clear()

        if etat[
            "filtres_ouverts"
        ]:

            zone_filtres.add(
                filtres_contenu
            )

        mettre_a_jour_bouton_filtres()

    bouton_filtres = toga.Button(
        "⚙ Calendriers",
        on_press=basculer_filtres,
    )

    # ---------------------------------------------------------
    # Actions générales des filtres
    # ---------------------------------------------------------

    bouton_tout_afficher = toga.Button(
        "Tout afficher",
        on_press=tout_afficher,
    )

    bouton_tout_masquer = toga.Button(
        "Tout masquer",
        on_press=tout_masquer,
    )

    actions_filtres.add(
        bouton_tout_afficher,
        bouton_tout_masquer,
    )

    filtres_contenu.add(
        actions_filtres
    )

    # ---------------------------------------------------------
    # Liste des calendriers Google
    # ---------------------------------------------------------

    try:

        calendriers_google = (
            lister_calendriers_google()
        )

    except Exception as erreur:

        calendriers_google = []

        filtres_contenu.add(
            toga.Label(
                "Impossible de récupérer "
                f"les calendriers : {erreur}"
            )
        )

    # ---------------------------------------------------------
    # Création des interrupteurs
    # ---------------------------------------------------------

    for calendrier_google in (
        calendriers_google
    ):

        calendrier_id = str(
            calendrier_google["id"]
        )

        nom = calendrier_google.get(
            "nom",
            "Calendrier Google",
        )

        couleur = calendrier_google.get(
            "couleur",
            "#6c757d",
        )

        if not couleur_valide(
            couleur
        ):
            couleur = "#6c757d"

        # -----------------------------------------------------
        # État initial du calendrier
        # -----------------------------------------------------

        if calendrier_id in preferences:

            actif = bool(
                preferences[
                    calendrier_id
                ]
            )

        else:

            actif = bool(
                calendrier_google.get(
                    "selectionne_google",
                    True,
                )
            )

            if calendrier_google.get(
                "masque_google",
                False,
            ):
                actif = False

        etat[
            "calendriers_actifs"
        ][
            calendrier_id
        ] = actif

        # -----------------------------------------------------
        # Ligne du calendrier
        # -----------------------------------------------------

        ligne_calendrier = toga.Box(
            style=Pack(
                direction=ROW,
                gap=6,
            )
        )

        indicateur = toga.Label(
            "●",
            style=Pack(
                color=couleur,
                width=20,
                margin_top=5,
            )
        )

        interrupteur = toga.Switch(
            nom,
            value=actif,
            on_change=(
                lambda widget,
                calendrier_id=calendrier_id,
                **kwargs:
                changer_calendrier(
                    widget,
                    calendrier_id=calendrier_id,
                )
            ),
            style=Pack(
                flex=1,
            )
        )

        interrupteurs[
            calendrier_id
        ] = interrupteur

        ligne_calendrier.add(
            indicateur,
            interrupteur,
        )

        filtres_contenu.add(
            ligne_calendrier
        )

    # ---------------------------------------------------------
    # Mois précédent
    # ---------------------------------------------------------

    def mois_precedent(
        widget,
        **kwargs,
    ):
        """Affiche le mois précédent."""

        etat["mois"] -= 1

        if etat["mois"] == 0:

            etat["mois"] = 12
            etat["annee"] -= 1

        charger_mois()

    # ---------------------------------------------------------
    # Mois suivant
    # ---------------------------------------------------------

    def mois_suivant(
        widget,
        **kwargs,
    ):
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

    # ---------------------------------------------------------
    # Assemblage
    # ---------------------------------------------------------

    conteneur.add(
        navigation,
        bouton_filtres,
        zone_filtres,
        webview,
    )

    # Panneau fermé au démarrage.
    mettre_a_jour_bouton_filtres()

    charger_mois()

    return conteneur