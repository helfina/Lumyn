"""Interface du module Rendez-vous."""

import toga
from toga.style.pack import COLUMN, Pack

from lumyn.modules.rendez_vous.gestion import preparer_rendez_vous
from lumyn.modules.rendez_vous.stockage import (
    charger_rendez_vous,
    enregistrer_rendez_vous,
    modifier_rendez_vous as modifier_rendez_vous_stockage,
    supprimer_rendez_vous,
)

from lumyn.modules.rendez_vous.calendrier_ui import (
    creer_calendrier_mensuel,
)

def creer_interface_rendez_vous():
    """Construit et renvoie l'interface du module Rendez-vous."""

    resultat_courant = None
    rendez_vous_en_modification = None

    # ---------------------------------------------------------
    # Contenu principal
    # ---------------------------------------------------------

    main_box = toga.Box(
        style=Pack(
            direction=COLUMN,
            margin=20,
            gap=10,
        )
    )

    bonjour = toga.Label(
        "Bonjour Gaëlle 👋"
    )

    bienvenue = toga.Label(
        "Note rapidement ton rendez-vous, "
        "Lumyn ajoutera les rappels."
    )

    rdv_input = toga.TextInput(
        placeholder=(
            "Exemple : Dentiste mardi à 14h30"
        ),
        style=Pack(
            flex=1,
        ),
    )

    resultat_label = toga.Label(
        ""
    )

    # ---------------------------------------------------------
    # Liste des rendez-vous enregistrés
    # ---------------------------------------------------------

    liste_rendez_vous = toga.Box(
        style=Pack(
            direction=COLUMN,
            gap=5,
        )
    )

    def actualiser_liste_rendez_vous():
        """Affiche les rendez-vous actuellement enregistrés."""

        liste_rendez_vous.clear()

        rendez_vous_enregistres = (
            charger_rendez_vous()
        )

        if not rendez_vous_enregistres:

            liste_rendez_vous.add(
                toga.Label(
                    "Aucun rendez-vous enregistré."
                )
            )

            return

        rendez_vous_enregistres.sort(
            key=lambda rdv: (
                rdv.get(
                    "date",
                    "",
                ),
                rdv.get(
                    "heure",
                    "",
                ),
            )
        )

        for rendez_vous in (
            rendez_vous_enregistres
        ):

            date_iso = rendez_vous.get(
                "date",
                "",
            )

            try:

                annee, mois, jour = (
                    date_iso.split("-")
                )

                date_affichee = (
                    f"{jour}/{mois}/{annee}"
                )

            except ValueError:

                date_affichee = date_iso

            texte = (
                f"{rendez_vous['jour_calcule']} "
                f"{date_affichee} à "
                f"{rendez_vous['heure']} — "
                f"{rendez_vous['titre']}"
            )

            ligne = toga.Box(
                style=Pack(
                    gap=10,
                )
            )

            label = toga.Label(
                texte,
                style=Pack(
                    flex=1,
                ),
            )

            # -------------------------------------------------
            # Charger un rendez-vous pour modification
            # -------------------------------------------------

            def charger_modification(
                widget,
                rdv=rendez_vous.copy(),
                **kwargs,
            ):
                """Charge un rendez-vous existant pour le modifier."""

                nonlocal resultat_courant
                nonlocal rendez_vous_en_modification

                rendez_vous_en_modification = (
                    rdv["id"]
                )

                resultat_courant = None

                date_rdv = rdv.get(
                    "date",
                    "",
                )

                heure_rdv = rdv.get(
                    "heure",
                    "",
                )

                titre_rdv = rdv.get(
                    "titre",
                    "",
                )

                try:

                    annee, mois, jour = (
                        date_rdv.split("-")
                    )

                    date_saisie = (
                        f"{jour}/{mois}/{annee}"
                    )

                except ValueError:

                    date_saisie = date_rdv

                rdv_input.value = (
                    f"{titre_rdv} "
                    f"{date_saisie} "
                    f"{heure_rdv}"
                )

                resultat_label.text = (
                    "Rendez-vous chargé.\n"
                    "Modifie la phrase puis clique sur "
                    "« Créer le rendez-vous »."
                )

                modifier_button.enabled = False
                confirmer_button.enabled = False

            # -------------------------------------------------
            # Supprimer un rendez-vous
            # -------------------------------------------------

            def supprimer(
                widget,
                rdv_id=rendez_vous["id"],
                **kwargs,
            ):
                """Supprime le rendez-vous sélectionné."""

                nonlocal resultat_courant
                nonlocal rendez_vous_en_modification

                if supprimer_rendez_vous(
                    rdv_id
                ):

                    if (
                        rendez_vous_en_modification
                        == rdv_id
                    ):

                        rendez_vous_en_modification = (
                            None
                        )

                        resultat_courant = None

                        rdv_input.value = ""

                    resultat_label.text = (
                        "Rendez-vous supprimé."
                    )

                    actualiser_liste_rendez_vous()

                else:

                    resultat_label.text = (
                        "Impossible de trouver "
                        "ce rendez-vous."
                    )

            modifier_rdv_button = (
                toga.Button(
                    "Modifier",
                    on_press=charger_modification,
                )
            )

            supprimer_button = toga.Button(
                "Supprimer",
                on_press=supprimer,
            )

            ligne.add(
                label,
                modifier_rdv_button,
                supprimer_button,
            )

            liste_rendez_vous.add(
                ligne
            )

    # ---------------------------------------------------------
    # Analyse d'une nouvelle saisie
    # ---------------------------------------------------------

    def creer_rendez_vous(
        widget,
        **kwargs,
    ):
        """Analyse la saisie et prépare le rendez-vous."""

        nonlocal resultat_courant

        resultat_courant = (
            preparer_rendez_vous(
                rdv_input.value
            )
        )

        resultat_label.text = (
            resultat_courant["message"]
        )

        etat = resultat_courant[
            "etat"
        ]

        if etat == "confirmation":

            modifier_button.enabled = True
            confirmer_button.enabled = True

        elif etat in (
            "erreur",
            "incomplet",
        ):

            modifier_button.enabled = True
            confirmer_button.enabled = False

        else:

            modifier_button.enabled = False
            confirmer_button.enabled = False

    # ---------------------------------------------------------
    # Modifier la saisie avant confirmation
    # ---------------------------------------------------------

    def modifier_saisie(
        widget,
        **kwargs,
    ):
        """Permet de reprendre la saisie avant confirmation."""

        nonlocal resultat_courant

        resultat_courant = None

        resultat_label.text = (
            "Modifie la phrase puis clique "
            "de nouveau sur "
            "« Créer le rendez-vous »."
        )

        modifier_button.enabled = False
        confirmer_button.enabled = False

    # ---------------------------------------------------------
    # Confirmer création ou modification
    # ---------------------------------------------------------

    def confirmer_rendez_vous(
        widget,
        **kwargs,
    ):
        """Enregistre ou modifie le rendez-vous préparé."""

        nonlocal resultat_courant
        nonlocal rendez_vous_en_modification

        if not resultat_courant:

            resultat_label.text = (
                "Aucun rendez-vous à confirmer."
            )

            return

        if (
            resultat_courant["etat"]
            != "confirmation"
        ):

            resultat_label.text = (
                "Le rendez-vous n'est pas "
                "prêt à être confirmé."
            )

            return

        rendez_vous = (
            resultat_courant[
                "rendez_vous"
            ]
        )

        if rendez_vous_en_modification:

            resultat = (
                modifier_rendez_vous_stockage(
                    rendez_vous_en_modification,
                    rendez_vous,
                )
            )

            if resultat is None:

                resultat_label.text = (
                    "Impossible de modifier "
                    "ce rendez-vous."
                )

                return

            message_action = (
                "Rendez-vous modifié ✅"
            )

        else:

            enregistrer_rendez_vous(
                rendez_vous
            )

            message_action = (
                "Rendez-vous enregistré ✅"
            )

        resultat_label.text = (
            f"{message_action}\n"
            f"{rendez_vous['titre']} "
            f"le "
            f"{rendez_vous['date'].strftime('%d/%m/%Y')} "
            f"à {rendez_vous['heure']}."
        )

        rdv_input.value = ""

        modifier_button.enabled = False
        confirmer_button.enabled = False

        resultat_courant = None
        rendez_vous_en_modification = None

        actualiser_liste_rendez_vous()

    # ---------------------------------------------------------
    # Boutons
    # ---------------------------------------------------------

    creer_button = toga.Button(
        "Créer le rendez-vous",
        on_press=creer_rendez_vous,
    )

    modifier_button = toga.Button(
        "Modifier",
        on_press=modifier_saisie,
        enabled=False,
    )

    confirmer_button = toga.Button(
        "Confirmer",
        on_press=confirmer_rendez_vous,
        enabled=False,
    )

    # ---------------------------------------------------------
    # Partie création
    # ---------------------------------------------------------

    main_box.add(
        bonjour,
        bienvenue,
        rdv_input,
        creer_button,
        resultat_label,
        modifier_button,
        confirmer_button,
        liste_rendez_vous,
    )

    actualiser_liste_rendez_vous()

    # ---------------------------------------------------------
    # Calendrier Google
    # ---------------------------------------------------------

    calendrier = (
        creer_calendrier_mensuel()
    )

    main_box.add(
        calendrier
    )

    # ---------------------------------------------------------
    # Défilement de toute l'interface
    # ---------------------------------------------------------

    scroll_container = toga.ScrollContainer(
        content=main_box,
        horizontal=False,
        vertical=True,
        style=Pack(
            flex=1,
        ),
    )

    return scroll_container


    calendrier = creer_calendrier_mensuel()

    main_box.add(calendrier)

    return main_box