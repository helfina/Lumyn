"""Interface du module Rendez-vous."""

import toga
from toga.style.pack import COLUMN, Pack

from lumyn.modules.rendez_vous.gestion import preparer_rendez_vous


def creer_interface_rendez_vous():
    """Construit et renvoie l'interface du module Rendez-vous."""

    resultat_courant = None

    main_box = toga.Box(
        style=Pack(
            direction=COLUMN,
            margin=20,
            gap=10,
        )
    )

    bonjour = toga.Label("Bonjour Gaëlle 👋")

    bienvenue = toga.Label(
        "Note rapidement ton rendez-vous, Lumyn ajoutera les rappels."
    )

    rdv_input = toga.TextInput(
        placeholder="Exemple : Dentiste mardi à 14h30",
        style=Pack(flex=1),
    )

    resultat_label = toga.Label("")

    modifier_button = toga.Button(
        "Modifier",
        enabled=False,
    )

    confirmer_button = toga.Button(
        "Confirmer",
        enabled=False,
    )

    def creer_rendez_vous(widget, **kwargs):
        """Analyse la saisie et adapte les boutons au résultat."""

        nonlocal resultat_courant

        resultat_courant = preparer_rendez_vous(rdv_input.value)
        resultat_label.text = resultat_courant["message"]

        etat = resultat_courant["etat"]

        if etat == "confirmation":
            modifier_button.enabled = True
            confirmer_button.enabled = True

        elif etat in ("erreur", "incomplet"):
            modifier_button.enabled = True
            confirmer_button.enabled = False

        else:
            modifier_button.enabled = False
            confirmer_button.enabled = False

    creer_button = toga.Button(
        "Créer le rendez-vous",
        on_press=creer_rendez_vous,
    )

    main_box.add(
        bonjour,
        bienvenue,
        rdv_input,
        creer_button,
        resultat_label,
        modifier_button,
        confirmer_button,
    )

    return main_box