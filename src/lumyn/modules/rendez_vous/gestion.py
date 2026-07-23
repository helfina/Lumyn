"""Gestion et validation des rendez-vous dans Lumyn."""

from lumyn.modules.rendez_vous.analyseur import analyser_rendez_vous


def preparer_rendez_vous(texte):
    """Analyse une saisie et prépare le message de confirmation."""

    texte = texte.strip()

    if not texte:
        return "Écris d'abord un rendez-vous."

    titre, jour, heure = analyser_rendez_vous(texte)

    informations_manquantes = []

    if not titre:
        informations_manquantes.append("le titre")

    if not jour:
        informations_manquantes.append("le jour")

    if not heure:
        informations_manquantes.append("l'heure")

    if informations_manquantes:
        manquants = ", ".join(informations_manquantes)

        return (
            "Je n'ai pas toutes les informations.\n"
            f"Il manque : {manquants}."
        )

    return (
        "Lumyn a compris :\n"
        f"Titre : {titre}\n"
        f"Jour : {jour}\n"
        f"Heure : {heure}\n\n"
        "Confirmer ce rendez-vous ?"
    )