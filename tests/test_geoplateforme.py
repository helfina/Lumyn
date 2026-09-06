from urllib.parse import parse_qs, urlsplit
from urllib.error import HTTPError

import pytest

from lumyn.modules.synapse.geoplateforme import (
    FournisseurGeoplateforme,
    SOURCE_BAN,
)
from lumyn.modules.synapse.selection_lieux import enregistrer_proposition


def test_recherche_ban_sans_cle_convertit_borne_et_autorise_conservation():
    appels = []
    charge = {"features": [{"properties": {
        "_type": "address", "name": f"{i} rue Test",
        "label": f"{i} rue Test 56000 Vannes", "city": "Vannes",
        "banId": f"ban-{i}",
    }} for i in range(7)]}
    fournisseur = FournisseurGeoplateforme(
        limite=3, intervalle_minimum=0,
        transport=lambda url, timeout: appels.append((url, timeout)) or charge,
    )
    propositions = fournisseur.rechercher("12 rue Test Vannes")
    assert len(propositions) == 3
    assert propositions[0].source == SOURCE_BAN
    assert propositions[0].identifiant == "ban-0"
    assert propositions[0].conservation_autorisee is True
    params = parse_qs(urlsplit(appels[0][0]).query)
    assert params == {"q": ["12 rue Test Vannes"], "index": ["address"],
                      "autocomplete": ["0"], "limit": ["3"]}
    assert appels[0][1] == 6
    assert enregistrer_proposition(propositions[0], autoriser=True)["etat"] == "enregistre"


def test_autocompletion_officielle_et_selection_non_automatique():
    appels = []
    fournisseur = FournisseurGeoplateforme(intervalle_minimum=0, transport=lambda url, timeout: {
        "status": "OK", "results": [
            {"country": "StreetAddress", "fulltext": "12 Rue A, 56000 Vannes", "city": "Vannes"},
            {"country": "PositionOfInterest", "fulltext": "Lieu non adresse", "city": "Vannes"},
            {"country": "StreetAddress", "fulltext": "12 Rue A, 56000 Vannes", "city": "Vannes"},
        ]
    } if not appels.append(url) else {})
    propositions = fournisseur.autocompleter("12 rue A")
    assert len(propositions) == 1
    assert propositions[0].adresse == "12 Rue A, 56000 Vannes"
    params = parse_qs(urlsplit(appels[0]).query)
    assert params["type"] == ["StreetAddress"]
    assert params["maximumResponses"] == ["5"]


def test_zero_resultat_reponse_invalide_et_texte_trop_court():
    fournisseur = FournisseurGeoplateforme(intervalle_minimum=0,
        transport=lambda url, timeout: {"features": []})
    assert fournisseur.rechercher("12 rue Test") == []
    assert fournisseur.rechercher("ab") == []
    fournisseur._transport = lambda url, timeout: {"results": []}
    with pytest.raises(ValueError, match="invalide"):
        fournisseur.rechercher("12 rue Test")


@pytest.mark.parametrize("erreur,attendue", [
    (TimeoutError(), TimeoutError),
    (OSError(), OSError),
])
def test_erreurs_reseau_propres(erreur, attendue):
    fournisseur = FournisseurGeoplateforme(intervalle_minimum=0,
        transport=lambda url, timeout: (_ for _ in ()).throw(erreur))
    with pytest.raises(attendue):
        fournisseur.rechercher("12 rue Test")


def test_limiteur_de_debit_reste_sous_quota_officiel():
    instants = iter([10.0, 10.0, 10.1, 10.35])
    pauses = []
    fournisseur = FournisseurGeoplateforme(
        intervalle_minimum=0.25, horloge=lambda: next(instants),
        pause=pauses.append, transport=lambda url, timeout: {"features": []},
    )
    fournisseur.rechercher("12 rue Test")
    fournisseur.rechercher("13 rue Test")
    assert pauses == [pytest.approx(0.15)]


@pytest.mark.parametrize("code", [401, 403, 429, 500, 503])
def test_codes_http_geoplateforme_sont_des_erreurs_propres(code):
    fournisseur = FournisseurGeoplateforme(
        intervalle_minimum=0,
        transport=lambda *args: (_ for _ in ()).throw(
            HTTPError("https://example.invalid", code, "erreur", {}, None)))
    with pytest.raises(OSError, match="indisponible"):
        fournisseur.rechercher("12 rue Test")
