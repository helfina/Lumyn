"""Interface du module Rendez-vous."""

import toga
from toga.style.pack import COLUMN, Pack

from lumyn.modules.rendez_vous.gestion import preparer_rendez_vous


def creer_interface_rendez_vous():
    """Construit et renvoie l'interface du module Rendez-vous."""

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

    def creer_rendez_vous(widget, **kwargs):
        """Affiche le résultat de l'analyse du rendez-vous."""

        resultat_label.text = preparer_rendez_vous(
            rdv_input.value
        )

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
    )

    return main_box