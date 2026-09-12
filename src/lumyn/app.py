"""
Assistant personnel modulaire pensé pour alléger la charge mentale.
"""

import toga

from toga.style.pack import COLUMN, ROW, Pack

from lumyn.configuration import charger_env_local
from lumyn.compat_toga_winforms import appliquer_correctif_shutdown_toga_winforms
from lumyn.modules.lieux.ui import creer_interface_lieux
from lumyn.modules.rendez_vous.ui import creer_interface_rendez_vous
from lumyn.modules.synapse.routeur_lieux import RouteurLieuxPublics
from lumyn.modules.synapse.ia_locale import interpreteur_local_depuis_environnement
from lumyn.modules.synapse.ollama_web import fournisseur_ollama_web_depuis_environnement


def creer_fournisseurs_synapse():
    """Charge la configuration locale avant de construire les fournisseurs."""
    charger_env_local()
    fournisseur_lieux = RouteurLieuxPublics()
    try:
        interpreteur_local = interpreteur_local_depuis_environnement()
    except ValueError:
        interpreteur_local = None
    try:
        fournisseur_ia = fournisseur_ollama_web_depuis_environnement(
            ban=fournisseur_lieux.adresses)
    except ValueError:
        fournisseur_ia = None
    return fournisseur_lieux, interpreteur_local, fournisseur_ia


class Lumyn(toga.App):
    """Application principale Lumyn."""

    def startup(self):
        """Démarre Lumyn et construit la navigation principale."""

        self.main_window = toga.MainWindow(
            title=self.formal_name
        )

        fournisseur_lieux, interpreteur_local, fournisseur_ia = (
            creer_fournisseurs_synapse()
        )
        self.interface_rendez_vous = creer_interface_rendez_vous(
            fournisseur_lieux, fournisseur_ia=fournisseur_ia,
            interpreteur_local=interpreteur_local)
        self.interface_lieux = creer_interface_lieux(fournisseur_lieux)

        self.zone_contenu = toga.Box(
            style=Pack(
                direction=COLUMN,
                flex=1,
            )
        )

        navigation = toga.Box(
            style=Pack(
                direction=ROW,
                gap=6,
                margin=8,
            )
        )

        bouton_rendez_vous = toga.Button(
            "Rendez-vous",
            on_press=self.afficher_rendez_vous,
            style=Pack(
                flex=1,
            ),
        )

        bouton_lieux = toga.Button(
            "Carnet de lieux",
            on_press=self.afficher_lieux,
            style=Pack(
                flex=1,
            ),
        )

        navigation.add(
            bouton_rendez_vous,
            bouton_lieux,
        )

        contenu_principal = toga.Box(
            style=Pack(
                direction=COLUMN,
                flex=1,
            )
        )

        contenu_principal.add(
            navigation,
            self.zone_contenu,
        )

        self.afficher_rendez_vous()

        self.main_window.content = contenu_principal
        self.main_window.show()

    def afficher_rendez_vous(self, widget=None, **kwargs):
        """Affiche le module Rendez-vous."""

        self.zone_contenu.clear()
        self.zone_contenu.add(
            self.interface_rendez_vous
        )

    def afficher_lieux(self, widget=None, **kwargs):
        """Affiche le carnet de lieux."""

        self.zone_contenu.clear()
        self.zone_contenu.add(
            self.interface_lieux
        )


def main():
    appliquer_correctif_shutdown_toga_winforms()
    return Lumyn()
