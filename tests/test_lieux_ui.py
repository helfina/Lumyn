"""Tests de l'interface du carnet de lieux."""

import pytest
import toga

from lumyn.modules.lieux import stockage, ui


@pytest.fixture
def interface_lieux(monkeypatch, tmp_path):
    """Construit le carnet avec un stockage temporaire."""

    toga.App(
        "Lumyn tests lieux",
        "fr.helfina.lumyn.tests.lieux",
    )

    dossier = tmp_path / ".lumyn"
    fichier = dossier / "lieux.json"

    monkeypatch.setattr(
        stockage,
        "DOSSIER_DONNEES",
        dossier,
    )
    monkeypatch.setattr(
        stockage,
        "FICHIER_LIEUX",
        fichier,
    )

    interface = ui.InterfaceLieux()
    interface.construire()

    return interface


def test_interface_se_construit(interface_lieux):
    """Le formulaire et la liste sont disponibles."""

    assert interface_lieux.nom_input is not None
    assert interface_lieux.adresse_input is not None
    assert interface_lieux.enregistrer_button is not None
    assert interface_lieux.liste_lieux is not None
    assert interface_lieux.titre_liste.text == "Lieux enregistrés (0)"


def test_premiere_adresse_devient_favorite(interface_lieux):
    """La première adresse devient favorite automatiquement."""

    interface_lieux.libelle_adresse_input.value = "Rendez-vous"
    interface_lieux.adresse_input.value = "10 rue de Test"
    interface_lieux.favorite_switch.value = False

    interface_lieux.enregistrer_adresse()

    assert len(interface_lieux.adresses_en_cours) == 1
    assert interface_lieux.adresses_en_cours[0] == {
        "libelle": "Rendez-vous",
        "adresse": "10 rue de Test",
        "favorite": True,
    }


def test_nouvelle_favorite_remplace_ancienne(interface_lieux):
    """Une seule adresse peut être favorite."""

    interface_lieux.libelle_adresse_input.value = "Administration"
    interface_lieux.adresse_input.value = "Adresse A"
    interface_lieux.enregistrer_adresse()

    interface_lieux.libelle_adresse_input.value = "Rendez-vous"
    interface_lieux.adresse_input.value = "Adresse B"
    interface_lieux.favorite_switch.value = True
    interface_lieux.enregistrer_adresse()

    assert interface_lieux.adresses_en_cours[0]["favorite"] is False
    assert interface_lieux.adresses_en_cours[1]["favorite"] is True


def test_creation_fiche_complete(interface_lieux):
    """Une fiche complète peut être enregistrée puis relue."""

    interface_lieux.nom_input.value = "ITEP Vannes"
    interface_lieux.categorie_input.value = "établissement"
    interface_lieux.alias_input.value = "ITEP, institut Vannes"
    interface_lieux.notes_input.value = "Lieu réel des rendez-vous"

    interface_lieux.libelle_adresse_input.value = "Rendez-vous"
    interface_lieux.adresse_input.value = "Adresse réelle ITEP"
    interface_lieux.enregistrer_adresse()

    interface_lieux.enregistrer_fiche()

    lieux = stockage.charger_lieux()

    assert len(lieux) == 1

    lieu = lieux[0]

    assert lieu["nom"] == "ITEP Vannes"
    assert lieu["categorie"] == "établissement"
    assert lieu["alias"] == [
        "ITEP",
        "institut Vannes",
    ]
    assert lieu["notes"] == "Lieu réel des rendez-vous"
    assert lieu["adresses"][0]["adresse"] == "Adresse réelle ITEP"
    assert lieu["adresses"][0]["favorite"] is True


def test_creation_fiche_maison(interface_lieux):
    """Maison peut contenir les alias domicile et chez moi."""

    interface_lieux.nom_input.value = "Maison"
    interface_lieux.categorie_input.value = "domicile"
    interface_lieux.alias_input.value = "domicile, chez moi"

    interface_lieux.libelle_adresse_input.value = "Maison"
    interface_lieux.adresse_input.value = "Adresse personnelle de test"
    interface_lieux.enregistrer_adresse()

    interface_lieux.enregistrer_fiche()

    maison = stockage.charger_lieux()[0]

    assert maison["nom"] == "Maison"
    assert maison["alias"] == [
        "domicile",
        "chez moi",
    ]
    assert maison["adresses"][0]["adresse"] == (
        "Adresse personnelle de test"
    )


def test_modification_conserve_identifiant(interface_lieux):
    """Modifier une fiche ne crée pas une nouvelle fiche."""

    original = stockage.enregistrer_lieu(
        {
            "nom": "Dr Test",
            "categorie": "professionnel",
            "profession": "médecin",
            "alias": ["docteur"],
            "adresses": [],
            "visio": False,
            "notes": None,
        }
    )

    interface_lieux.charger_fiche(original)

    interface_lieux.nom_input.value = "Dr Test Modifié"
    interface_lieux.visio_switch.value = True

    interface_lieux.enregistrer_fiche()

    lieux = stockage.charger_lieux()

    assert len(lieux) == 1
    assert lieux[0]["id"] == original["id"]
    assert lieux[0]["nom"] == "Dr Test Modifié"
    assert lieux[0]["visio"] is True


def test_suppression_fiche(interface_lieux):
    """Une fiche peut être supprimée depuis l'interface."""

    lieu = stockage.enregistrer_lieu(
        {
            "nom": "Lieu test",
            "categorie": None,
            "profession": None,
            "alias": [],
            "adresses": [],
            "visio": False,
            "notes": None,
        }
    )

    interface_lieux.actualiser_liste_lieux()

    interface_lieux.supprimer_fiche(lieu)

    assert stockage.charger_lieux() == []


def test_adresse_peut_etre_modifiee(interface_lieux):
    """Une adresse existante peut être corrigée."""

    interface_lieux.libelle_adresse_input.value = "Ancien site"
    interface_lieux.adresse_input.value = "Ancienne adresse"
    interface_lieux.enregistrer_adresse()

    interface_lieux.modifier_adresse(0)

    interface_lieux.libelle_adresse_input.value = "Rendez-vous"
    interface_lieux.adresse_input.value = "Bonne adresse"
    interface_lieux.enregistrer_adresse()

    assert len(interface_lieux.adresses_en_cours) == 1
    assert interface_lieux.adresses_en_cours[0]["libelle"] == (
        "Rendez-vous"
    )
    assert interface_lieux.adresses_en_cours[0]["adresse"] == (
        "Bonne adresse"
    )
    assert interface_lieux.adresses_en_cours[0]["favorite"] is True
