from unittest.mock import Mock

import pytest

from lumyn.modules.synapse.routeur_lieux import RouteurLieuxPublics, classifier_requete


def test_routage_adresse_entreprise_et_sante_sans_melanger_les_sources():
    ban = Mock()
    entreprises = Mock()
    sante = Mock()
    routeur = RouteurLieuxPublics(adresses=ban, entreprises=entreprises, sante=sante)

    routeur.rechercher("12 rue du Général de Gaulle Vannes")
    ban.rechercher.assert_called_once()
    routeur.rechercher("Garage Renault Josselin")
    entreprises.rechercher.assert_called_once()
    routeur.rechercher("Dr Dupont dermatologue Vannes")
    sante.rechercher.assert_called_once()


def test_centre_hospitalier_est_route_vers_sante_et_pas_entreprises():
    ban = Mock()
    entreprises = Mock()
    sante = Mock(rechercher=Mock(return_value=[]))
    routeur = RouteurLieuxPublics(
        adresses=ban,
        entreprises=entreprises,
        sante=sante,
    )

    requete = "Centre Hospitalier Bretagne Atlantique Vannes"

    assert routeur.rechercher(requete) == []
    sante.rechercher.assert_called_once_with(requete)
    entreprises.rechercher.assert_not_called()
    ban.rechercher.assert_not_called()


def test_classification_des_centres_hospitaliers_sans_faux_positifs():
    assert classifier_requete(
        "Centre Hospitalier Bretagne Atlantique Vannes"
    ) == "sante"
    assert classifier_requete("centre hospitalier de Lorient") == "sante"
    assert classifier_requete(
        "centre hospitalier universitaire Rennes"
    ) == "sante"
    assert classifier_requete("centre commercial Atlantique") == "entreprise"
    assert classifier_requete("centre culturel Vannes") == "entreprise"


def test_sante_absente_ne_retombe_pas_sur_ban_ou_entreprises():
    ban = Mock()
    entreprises = Mock()
    routeur = RouteurLieuxPublics(adresses=ban, entreprises=entreprises, sante=Mock(rechercher=Mock(return_value=[])))
    assert routeur.rechercher("Dentiste Dupont Vannes") == []
    ban.rechercher.assert_not_called()
    entreprises.rechercher.assert_not_called()


def test_autocompletion_est_toujours_ban_et_classification():
    ban = Mock(autocompleter=Mock(return_value=[]))
    routeur = RouteurLieuxPublics(adresses=ban, entreprises=Mock())
    routeur.autocompleter("12 rue du gén")
    ban.autocompleter.assert_called_once_with("12 rue du gén")
    assert classifier_requete("Centre commercial Vannes") == "entreprise"


@pytest.mark.parametrize("requete,categorie", [
    ("Hôpital Bretagne Atlantique Vannes", "sante"),
    ("Centre hospitalier de Vannes", "sante"),
    ("Centre culturel Vannes", "entreprise"),
])
def test_classification_des_variantes_d_etablissements(requete, categorie):
    assert classifier_requete(requete) == categorie
