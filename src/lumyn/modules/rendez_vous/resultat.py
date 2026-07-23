"""Résultat renvoyé par le module Rendez-vous."""


def creer_resultat(etat, message, rendez_vous=None):
    """Construit le résultat d'une opération."""

    return {
        "etat": etat,
        "message": message,
        "rendez_vous": rendez_vous,
    }