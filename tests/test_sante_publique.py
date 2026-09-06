from urllib.parse import parse_qs, urlsplit

import pytest

from lumyn.modules.synapse.sante_publique import FournisseurEtablissementsSante


def test_recherche_sante_limitee_aux_etablissements_finess_sans_cle():
    appels = []
    fournisseur = FournisseurEtablissementsSante(transport=lambda url, timeout:
        appels.append(url) or {"results": [{
            "nom_complet": "CENTRE HOSPITALIER TEST",
            "siege": {"adresse": "1 RUE TEST 56000 VANNES", "libelle_commune": "VANNES",
                      "siret": "123", "etat_administratif": "A"},
        }]})
    propositions = fournisseur.rechercher("Centre hospitalier Vannes")
    assert len(propositions) == 1
    assert "FINESS" in propositions[0].source
    params = parse_qs(urlsplit(appels[0]).query)
    assert params["est_finess"] == ["true"]
    assert params["etat_administratif"] == ["A"]
    assert "key" not in params and "token" not in params


def test_sante_reponse_invalide_et_erreurs_propres():
    fournisseur = FournisseurEtablissementsSante(transport=lambda url, timeout: {})
    with pytest.raises(ValueError, match="invalide"):
        fournisseur.rechercher("Clinique Test")
    for erreur, attendu in ((TimeoutError(), TimeoutError), (OSError(), OSError)):
        fournisseur._transport = lambda url, timeout, e=erreur: (_ for _ in ()).throw(e)
        with pytest.raises(attendu):
            fournisseur.rechercher("Clinique Test")
