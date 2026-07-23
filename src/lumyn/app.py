"""
Assistant personnel modulaire pensé pour alléger la charge mentale.
"""

import toga

from lumyn.modules.rendez_vous.ui import creer_interface_rendez_vous


class Lumyn(toga.App):
    def startup(self):
        """Démarre Lumyn et affiche le module Rendez-vous."""

        self.main_window = toga.MainWindow(
            title=self.formal_name
        )

        self.main_window.content = creer_interface_rendez_vous()
        self.main_window.show()


def main():
    return Lumyn()