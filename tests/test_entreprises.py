from urllib.parse import parse_qs, urlsplit

import pytest

from lumyn.modules.synapse.entreprises import FournisseurEntreprises


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

