"""Tests du carnet de lieux de Lumyn."""

import json

import pytest

from lumyn.modules.lieux import stockage
from lumyn.modules.lieux.gestion import (
    est_fiche_maison,
    normaliser_recherche,
    obtenir_adresse_favorite,
    rechercher_lieux,
    trouver_maison,
)
from lumyn.modules.lieux.modele import creer_modele_adresse, creer_modele_lieu


@pytest.fixture
def stockage_temporaire(tmp_path, monkeypatch):
    """Utilise un dossier temporaire au lieu du vrai ~/.lumyn."""

    dossier = tmp_path / ".lumyn"
    fichier = dossier / "lieux.json"

    monkeypatch.setattr(stockage, "DOSSIER_DONNEES", dossier)
    monkeypatch.setattr(stockage, "FICHIER_LIEUX", fichier)

    return fichier


def test_modeles_vides():
    """Les modèles contiennent les champs attendus."""

    adresse = creer_modele_adresse()
    lieu = creer_modele_lieu()

    assert adresse == {
        "libelle": None,
        "adresse": None,
        "favorite": False,
    }

    assert lieu == {
        "id": None,
        "nom": None,
        "categorie": None,
        "profession": None,
        "alias": [],
        "adresses": [],
        "visio": False,
        "notes": None,
    }


def test_enregistrer_et_charger_lieu(stockage_temporaire):
    """Une fiche enregistrée peut être relue."""

    lieu = creer_modele_lieu()
    lieu["nom"] = "ITEP Vannes"
    lieu["alias"] = ["ITEP"]
    lieu["adresses"] = [
        {
            "libelle": "Lieu des rendez-vous",
            "adresse": "Adresse de test",
            "favorite": True,
        }
    ]

    enregistre = stockage.enregistrer_lieu(lieu)
    lieux = stockage.charger_lieux()

    assert enregistre["id"]
    assert len(lieux) == 1
    assert lieux[0]["id"] == enregistre["id"]
    assert lieux[0]["nom"] == "ITEP Vannes"
    assert lieux[0]["alias"] == ["ITEP"]
    assert lieux[0]["adresses"][0]["favorite"] is True


def test_modifier_et_supprimer_lieu(stockage_temporaire):
    """Une fiche peut être modifiée puis supprimée."""

    lieu = creer_modele_lieu()
    lieu["nom"] = "Maison"

    enregistre = stockage.enregistrer_lieu(lieu)

    modifie = creer_modele_lieu()
    modifie["nom"] = "Maison"
    modifie["alias"] = ["maison", "domicile", "chez moi"]

    resultat = stockage.modifier_lieu(enregistre["id"], modifie)

    assert resultat is not None
    assert resultat["id"] == enregistre["id"]
    assert resultat["alias"] == ["maison", "domicile", "chez moi"]

    assert stockage.supprimer_lieu(enregistre["id"]) is True
    assert stockage.charger_lieux() == []


def test_fichier_invalide_est_conserve(stockage_temporaire):
    """Un fichier JSON illisible n'est pas remplacé silencieusement."""

    stockage.DOSSIER_DONNEES.mkdir(parents=True)
    stockage_temporaire.write_text("{invalide", encoding="utf-8")

    with pytest.raises(ValueError):
        stockage.charger_lieux()

    assert stockage_temporaire.read_text(encoding="utf-8") == "{invalide"


def test_ajout_identifiant_aux_anciennes_fiches(stockage_temporaire):
    """Une ancienne fiche sans identifiant reçoit automatiquement un UUID."""

    stockage.DOSSIER_DONNEES.mkdir(parents=True)

    stockage_temporaire.write_text(
        json.dumps([{"nom": "Ancien lieu"}]),
        encoding="utf-8",
    )

    lieux = stockage.charger_lieux()

    assert len(lieux) == 1
    assert lieux[0]["id"]


def test_normalisation_ignore_accents_majuscules_et_espaces():
    """La recherche tolère accents, casse et espaces superflus."""

    assert normaliser_recherche("  GuÉGon  ") == "guegon"
    assert normaliser_recherche("Chez   Moi") == "chez moi"


def test_rechercher_lieu_par_nom_et_alias():
    """Une fiche est retrouvée par son nom ou un de ses alias."""

    itep = creer_modele_lieu()
    itep["nom"] = "ITEP Vannes"
    itep["alias"] = ["ITEP", "Institut Vannes"]

    dentiste = creer_modele_lieu()
    dentiste["nom"] = "Dentiste Guégon"
    dentiste["alias"] = ["dentiste"]

    lieux = [itep, dentiste]

    assert rechercher_lieux("ITEP", lieux) == [itep]
    assert rechercher_lieux("itep vannes", lieux) == [itep]
    assert rechercher_lieux("guegon", lieux) == [dentiste]


def test_correspondance_exacte_est_prioritaire():
    """Une correspondance exacte passe avant une correspondance partielle."""

    exact = creer_modele_lieu()
    exact["nom"] = "ITEP"

    partiel = creer_modele_lieu()
    partiel["nom"] = "ITEP Vannes"

    assert rechercher_lieux("ITEP", [partiel, exact]) == [exact, partiel]


def test_obtenir_adresse_favorite():
    """L'adresse marquée favorite est utilisée."""

    lieu = creer_modele_lieu()
    lieu["adresses"] = [
        {
            "libelle": "Administration",
            "adresse": "Adresse administrative",
            "favorite": False,
        },
        {
            "libelle": "Rendez-vous",
            "adresse": "Adresse réelle des rendez-vous",
            "favorite": True,
        },
    ]

    assert obtenir_adresse_favorite(lieu) == lieu["adresses"][1]


def test_adresse_unique_utilisee_sans_favorite():
    """Une seule adresse peut être utilisée même sans étoile."""

    lieu = creer_modele_lieu()
    lieu["adresses"] = [
        {
            "libelle": "Cabinet",
            "adresse": "10 rue de Test",
            "favorite": False,
        }
    ]

    assert obtenir_adresse_favorite(lieu) == lieu["adresses"][0]


def test_plusieurs_adresses_sans_favorite_sont_ambigues():
    """Lumyn ne choisit pas arbitrairement entre plusieurs adresses."""

    lieu = creer_modele_lieu()
    lieu["adresses"] = [
        {
            "libelle": "Site A",
            "adresse": "Adresse A",
            "favorite": False,
        },
        {
            "libelle": "Site B",
            "adresse": "Adresse B",
            "favorite": False,
        },
    ]

    assert obtenir_adresse_favorite(lieu) is None


def test_maison_domicile_et_chez_moi_designent_la_meme_fiche():
    """Les alias du domicile correspondent à une seule fiche Maison."""

    maison = creer_modele_lieu()
    maison["nom"] = "Maison"
    maison["alias"] = ["domicile", "chez moi"]

    assert est_fiche_maison(maison) is True
    assert trouver_maison([maison]) is maison

    assert rechercher_lieux("maison", [maison]) == [maison]
    assert rechercher_lieux("domicile", [maison]) == [maison]
    assert rechercher_lieux("chez moi", [maison]) == [maison]


def test_plusieurs_fiches_maison_sont_ambigues():
    """Lumyn refuse de choisir si plusieurs fiches représentent le domicile."""

    maison = creer_modele_lieu()
    maison["nom"] = "Maison"

    domicile = creer_modele_lieu()
    domicile["nom"] = "Domicile"

    assert trouver_maison([maison, domicile]) is None
