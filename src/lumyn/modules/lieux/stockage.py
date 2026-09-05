"""Stockage local du carnet de lieux de Lumyn."""

import json
import os
import tempfile
import uuid
from pathlib import Path


DOSSIER_DONNEES = Path.home() / ".lumyn"
FICHIER_LIEUX = DOSSIER_DONNEES / "lieux.json"


def ajouter_identifiants_manquants(lieux):
    """Ajoute un identifiant aux anciennes fiches qui n'en ont pas."""

    modification = False

    for lieu in lieux:
        if not lieu.get("id"):
            lieu["id"] = str(uuid.uuid4())
            modification = True

    return modification


def sauvegarder_lieux(lieux):
    """Écrit toute la liste des lieux dans le fichier local."""

    contenu = json.dumps(lieux, ensure_ascii=False, indent=4)

    DOSSIER_DONNEES.mkdir(parents=True, exist_ok=True)

    temporaire = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DOSSIER_DONNEES,
            prefix="lieux-",
            suffix=".tmp",
            delete=False,
        ) as fichier:
            temporaire = Path(fichier.name)
            fichier.write(contenu)
            fichier.flush()
            os.fsync(fichier.fileno())

        os.replace(temporaire, FICHIER_LIEUX)

    finally:
        if temporaire is not None:
            temporaire.unlink(missing_ok=True)


def charger_lieux():
    """Charge les lieux déjà enregistrés."""

    if not FICHIER_LIEUX.exists():
        return []

    try:
        with FICHIER_LIEUX.open("r", encoding="utf-8") as fichier:
            lieux = json.load(fichier)

    except (json.JSONDecodeError, UnicodeError) as erreur:
        raise ValueError(
            "Le fichier du carnet de lieux est illisible. "
            "Il a été conservé sans modification."
        ) from erreur

    if not isinstance(lieux, list) or not all(
        isinstance(lieu, dict) for lieu in lieux
    ):
        raise ValueError(
            "Le fichier du carnet de lieux doit contenir une liste de fiches. "
            "Il a été conservé sans modification."
        )

    if ajouter_identifiants_manquants(lieux):
        sauvegarder_lieux(lieux)

    return lieux


def enregistrer_lieu(lieu):
    """Ajoute une nouvelle fiche au carnet de lieux."""

    lieux = charger_lieux()

    nouveau_lieu = lieu.copy()
    nouveau_lieu["id"] = str(uuid.uuid4())

    lieux.append(nouveau_lieu)
    sauvegarder_lieux(lieux)

    return nouveau_lieu


def modifier_lieu(lieu_id, nouvelles_donnees):
    """Modifie une fiche existante."""

    lieux = charger_lieux()

    for index, lieu in enumerate(lieux):
        if lieu.get("id") == lieu_id:
            lieu_modifie = nouvelles_donnees.copy()
            lieu_modifie["id"] = lieu_id

            lieux[index] = lieu_modifie
            sauvegarder_lieux(lieux)

            return lieu_modifie

    return None


def supprimer_lieu(lieu_id):
    """Supprime une fiche du carnet à partir de son identifiant."""

    lieux = charger_lieux()

    nouvelle_liste = [
        lieu
        for lieu in lieux
        if lieu.get("id") != lieu_id
    ]

    if len(nouvelle_liste) == len(lieux):
        return False

    sauvegarder_lieux(nouvelle_liste)

    return True
