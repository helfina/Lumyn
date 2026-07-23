"""Gestion et validation des rendez-vous dans Lumyn."""

from lumyn.modules.rendez_vous.analyseur import analyser_rendez_vous
from lumyn.modules.rendez_vous.resultat import creer_resultat


def preparer_rendez_vous(texte):
    """Analyse une saisie et prépare le résultat."""

    texte = texte.strip()

    if not texte:
        return creer_resultat(
            etat="vide",
            message="Écris d'abord un rendez-vous.",
        )

    rendez_vous = analyser_rendez_vous(texte)

    if rendez_vous["erreurs"]:
        erreurs = "\n".join(rendez_vous["erreurs"])

        return creer_resultat(
            etat="erreur",
            message=(
                "Lumyn a détecté une erreur :\n"
                f"{erreurs}\n\n"
                "Corrige la saisie avant de confirmer."
            ),
            rendez_vous=rendez_vous,
        )

    if rendez_vous["manquants"]:
        manquants = ", ".join(rendez_vous["manquants"])

        return creer_resultat(
            etat="incomplet",
            message=(
                "Je n'ai pas toutes les informations.\n"
                f"Il manque : {manquants}."
            ),
            rendez_vous=rendez_vous,
        )

    date_formatee = rendez_vous["date"].strftime("%d/%m/%Y")

    return creer_resultat(
        etat="confirmation",
        message=(
            "Lumyn a compris :\n"
            f"Titre : {rendez_vous['titre']}\n"
            f"Jour : {rendez_vous['jour_calcule']}\n"
            f"Date : {date_formatee}\n"
            f"Heure : {rendez_vous['heure']}\n\n"
            "Confirmer ce rendez-vous ?"
        ),
        rendez_vous=rendez_vous,
    )