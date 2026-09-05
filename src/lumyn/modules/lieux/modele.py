"""Modèles de données du carnet de lieux de Lumyn."""


def creer_modele_adresse():
    """Crée une adresse vide associée à un lieu."""

    return {
        "libelle": None,
        "adresse": None,
        "favorite": False,
    }


def creer_modele_lieu():
    """Crée une fiche de lieu vide."""

    return {
        "id": None,
        "nom": None,
        "categorie": None,
        "profession": None,
        "alias": [],
        "adresses": [],
        "visio": False,
        "notes": None,
    }
