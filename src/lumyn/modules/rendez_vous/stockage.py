"""Stockage local des rendez-vous de Lumyn."""

import json
import uuid
from datetime import date
from pathlib import Path


DOSSIER_DONNEES = Path.home() / ".lumyn"
FICHIER_RENDEZ_VOUS = DOSSIER_DONNEES / "rendez_vous.json"


def convertir_pour_json(rendez_vous):
    """Convertit les valeurs non compatibles JSON."""

    donnees = rendez_vous.copy()

    if isinstance(donnees.get("date"), date):
        donnees["date"] = donnees["date"].isoformat()

    return donnees


def ajouter_identifiants_manquants(rendez_vous):
    """Ajoute un identifiant aux anciens rendez-vous qui n'en ont pas."""

    modification = False

    for rendez_vous_existant in rendez_vous:
        if not rendez_vous_existant.get("id"):
            rendez_vous_existant["id"] = str(uuid.uuid4())
            modification = True

    return modification


def sauvegarder_rendez_vous(rendez_vous):
    """Écrit toute la liste des rendez-vous dans le fichier."""

    DOSSIER_DONNEES.mkdir(parents=True, exist_ok=True)

    with FICHIER_RENDEZ_VOUS.open("w", encoding="utf-8") as fichier:
        json.dump(
            rendez_vous,
            fichier,
            ensure_ascii=False,
            indent=4,
        )


def charger_rendez_vous():
    """Charge les rendez-vous déjà enregistrés."""

    if not FICHIER_RENDEZ_VOUS.exists():
        return []

    try:
        with FICHIER_RENDEZ_VOUS.open("r", encoding="utf-8") as fichier:
            rendez_vous = json.load(fichier)

    except (json.JSONDecodeError, OSError):
        return []

    if ajouter_identifiants_manquants(rendez_vous):
        sauvegarder_rendez_vous(rendez_vous)

    return rendez_vous


def enregistrer_rendez_vous(rendez_vous):
    """Ajoute un nouveau rendez-vous au stockage local."""

    rendez_vous_existants = charger_rendez_vous()

    rendez_vous_a_enregistrer = convertir_pour_json(rendez_vous)

    rendez_vous_a_enregistrer["id"] = str(uuid.uuid4())

    rendez_vous_existants.append(rendez_vous_a_enregistrer)

    sauvegarder_rendez_vous(rendez_vous_existants)

    return rendez_vous_a_enregistrer

def modifier_rendez_vous(rendez_vous_id, nouvelles_donnees):
    """Modifie un rendez-vous existant à partir de son identifiant."""

    rendez_vous_existants = charger_rendez_vous()

    for index, rendez_vous in enumerate(rendez_vous_existants):
        if rendez_vous.get("id") == rendez_vous_id:
            rendez_vous_modifie = convertir_pour_json(nouvelles_donnees)
            rendez_vous_modifie["id"] = rendez_vous_id

            rendez_vous_existants[index] = rendez_vous_modifie
            sauvegarder_rendez_vous(rendez_vous_existants)

            return rendez_vous_modifie

    return None


def supprimer_rendez_vous(rendez_vous_id):
    """Supprime un rendez-vous existant à partir de son identifiant."""

    rendez_vous_existants = charger_rendez_vous()

    nouvelle_liste = [
        rendez_vous
        for rendez_vous in rendez_vous_existants
        if rendez_vous.get("id") != rendez_vous_id
    ]

    if len(nouvelle_liste) == len(rendez_vous_existants):
        return False

    sauvegarder_rendez_vous(nouvelle_liste)

    return True