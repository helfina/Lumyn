from urllib.parse import parse_qs, urlsplit
from urllib.error import HTTPError

import pytest

from lumyn.modules.synapse.entreprises import FournisseurEntreprises, SOURCE_ENTREPRISES


def test_recherche_entreprise_sans_compte_convertit_et_dedoublonne():
    appels = []
    etablissement = {"adresse": "1 RUE TEST 56000 VANNES", "libelle_commune": "VANNES",
                     "siret": "123", "etat_administratif": "A", "activite_principale": "45.20A"}
    fournisseur = FournisseurEntreprises(limite=2,
        transport=lambda url, timeout: appels.append((url, timeout)) or {"results": [{
            "nom_complet": "GARAGE TEST", "matching_etablissements": [etablissement],
            "siege": etablissement,
        }]})
    propositions = fournisseur.rechercher("Garage Test Vannes")
    assert len(propositions) == 1
    assert propositions[0].adresse == "1 RUE TEST 56000 VANNES"
    assert propositions[0].identifiant == "123"
    assert propositions[0].conservation_autorisee is True
    params = parse_qs(urlsplit(appels[0][0]).query)
    assert params["per_page"] == ["2"]
    assert "key" not in params and "token" not in params


def test_entreprises_zero_invalide_timeout_et_reseau():
    fournisseur = FournisseurEntreprises(transport=lambda url, timeout: {"results": []})
    assert fournisseur.rechercher("Garage Test") == []
    fournisseur._transport = lambda url, timeout: {}
    with pytest.raises(ValueError, match="invalide"):
        fournisseur.rechercher("Garage Test")
    for erreur, type_attendu in ((TimeoutError(), TimeoutError), (OSError(), OSError)):
        fournisseur._transport = lambda url, timeout, e=erreur: (_ for _ in ()).throw(e)
        with pytest.raises(type_attendu):
            fournisseur.rechercher("Garage Test")


def test_entreprises_reponse_partielle_et_codes_http_sont_maitrises():
    fournisseur = FournisseurEntreprises(transport=lambda *args: {"results": [{
        "nom_complet": "TEST", "matching_etablissements": 42,
        "siege": None,
    }]})
    assert fournisseur.rechercher("Entreprise Test") == []
    for code in (401, 403, 429, 500, 503):
        fournisseur._transport = lambda *args, c=code: (_ for _ in ()).throw(
            HTTPError("https://example.invalid", c, "erreur", {}, None))
        with pytest.raises(OSError, match="indisponible"):
            fournisseur.rechercher("Entreprise Test")


def test_entreprises_ignore_entrees_non_dictionnaire_et_etablissement_ferme():
    charge = {"results": [
        "pas une entreprise",
        {"nom_complet": "FERME", "matching_etablissements": [{
            "adresse": "1 rue Fermee", "etat_administratif": "F",
        }]},
    ]}
    fournisseur = FournisseurEntreprises(
        transport=lambda url, timeout: charge)

    assert fournisseur.rechercher("Entreprise Test") == []


def test_entreprises_utilise_les_champs_de_secours_et_le_siege_valide():
    charge = {"results": [{
        "nom_raison_sociale": "SOCIETE TEST",
        "matching_etablissements": [],
        "siege": {
            "geo_adresse": "1 rue Test 56000 Vannes",
            "libelle_commune": "Vannes", "siret": "12345678900010",
            "etat_administratif": "A",
        },
    }]}
    fournisseur = FournisseurEntreprises(
        transport=lambda url, timeout: charge)

    propositions = fournisseur.rechercher("Societe Test")

    assert len(propositions) == 1
    proposition = propositions[0]
    assert proposition.nom == "SOCIETE TEST"
    assert proposition.adresse == "1 rue Test 56000 Vannes"
    assert proposition.ville == "Vannes"
    assert proposition.identifiant == "12345678900010"
    assert proposition.source == SOURCE_ENTREPRISES
    assert proposition.conservation_autorisee is True


def test_entreprises_dedoublonne_matching_siege_et_variantes_de_casse():
    etablissement = {
        "adresse": "1 RUE TEST 56000 VANNES", "libelle_commune": "Vannes",
        "siret": "123", "etat_administratif": "A",
    }
    charge = {"results": [
        {"nom_complet": "SOCIETE TEST", "matching_etablissements": [etablissement],
         "siege": etablissement},
        {"nom_complet": "societe test", "matching_etablissements": [{
            **etablissement, "adresse": "1 rue test 56000 vannes", "siret": "456",
        }]},
    ]}
    fournisseur = FournisseurEntreprises(
        transport=lambda url, timeout: charge)

    propositions = fournisseur.rechercher("Societe Test")

    assert len(propositions) == 1
    assert propositions[0].identifiant == "123"


def test_entreprises_applique_la_limite_apres_filtrage_et_dedoublonnage():
    def entreprise(nom, adresse, siret):
        return {"nom_complet": nom, "matching_etablissements": [{
            "adresse": adresse, "siret": siret, "etat_administratif": "A",
        }]}

    charge = {"results": [
        entreprise("SOCIETE A", "1 rue A", "1"),
        entreprise("societe a", "1 RUE A", "2"),
        entreprise("SOCIETE B", "2 rue B", "3"),
        entreprise("SOCIETE C", "3 rue C", "4"),
    ]}
    fournisseur = FournisseurEntreprises(
        limite=2, transport=lambda url, timeout: charge)

    propositions = fournisseur.rechercher("Societe Test")

    assert [proposition.identifiant for proposition in propositions] == ["1", "3"]
