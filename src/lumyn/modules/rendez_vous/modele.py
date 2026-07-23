"""Modèle de données d'un rendez-vous."""


def creer_modele_rendez_vous():
    """Crée un rendez-vous vide."""

    return {
        "titre": None,
        "date": None,
        "heure": None,
        "lieu": None,
        "jour_saisi": None,
        "jour_calcule": None,
        "erreurs": [],
        "manquants": [],
    }