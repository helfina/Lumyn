from urllib.parse import parse_qs, urlsplit
import pytest

from lumyn.modules.synapse.geoapify import (
    ErreurConfigurationGeoapify, FournisseurGeoapify,
    fournisseur_geoapify_depuis_environnement,
)
from lumyn.modules.synapse.selection_lieux import enregistrer_proposition


def reponse(*resultats):
    return {"results": list(resultats)}


def test_configuration_absente_inactive_et_activation_sans_cle_claire():
    assert fournisseur_geoapify_depuis_environnement({}) is None
    assert fournisseur_geoapify_depuis_environnement({"LUMYN_GEOAPIFY":"off", "GEOAPIFY_API_KEY":"secret"}) is None
    fournisseur = fournisseur_geoapify_depuis_environnement({"LUMYN_GEOAPIFY":"1"})
    with pytest.raises(ErreurConfigurationGeoapify, match="GEOAPIFY_API_KEY"):
        fournisseur.rechercher("Hôpital Lorient")


def test_recherche_convertit_borne_et_attribue_sans_exposer_cle():
    appels=[]
    donnees=reponse(*[
        {"name":f"Lieu {i}", "formatted":f"{i} rue Test, Vannes, France",
         "city":"Vannes", "category":"healthcare.clinic", "place_id":f"p{i}"}
        for i in range(8)
    ])
    fournisseur=FournisseurGeoapify("cle-test", limite=3,
        transport=lambda url,timeout: appels.append((url,timeout)) or donnees)
    propositions=fournisseur.rechercher("Dr Test Vannes")
    assert len(propositions)==3
    assert propositions[0].ville=="Vannes"
    assert propositions[0].profession=="healthcare · clinic"
    assert propositions[0].source=="Geoapify / OpenStreetMap"
    assert propositions[0].identifiant=="p0"
    assert propositions[0].conservation_autorisee is False
    params=parse_qs(urlsplit(appels[0][0]).query)
    assert params["bias"]==["countrycode:fr"] and params["limit"]==["3"]
    assert params["apiKey"]==["cle-test"] and appels[0][1]==6


def test_zero_invalide_doublon_et_autocompletion():
    fournisseur=FournisseurGeoapify("x",transport=lambda u,t:reponse())
    assert fournisseur.rechercher("Garage Test")==[]
    fournisseur._transport=lambda u,t: reponse(
        {"name":"Cabinet", "formatted":"1 rue A, Ploërmel"},
        {"name":"Cabinet", "formatted":"1 rue A, Ploërmel"},
        {"formatted":"sans nom"}, None)
    assert len(fournisseur.autocompleter("1 rue A"))==1
    fournisseur._transport=lambda u,t:{"features":[]}
    with pytest.raises(ValueError,match="invalide"): fournisseur.rechercher("Garage Test")


@pytest.mark.parametrize("erreur,attendue", [
    (TimeoutError(), TimeoutError),
    (OSError(), OSError),
])
def test_erreurs_reseau_sans_url_ni_cle(erreur,attendue):
    fournisseur=FournisseurGeoapify("tres-secret",transport=lambda u,t: (_ for _ in ()).throw(erreur))
    with pytest.raises(attendue) as capture: fournisseur.rechercher("Centre hospitalier Lorient")
    assert "tres-secret" not in str(capture.value)


def test_resultat_geoapify_ne_peut_pas_etre_persiste_sans_droit_clair():
    proposition=FournisseurGeoapify("x",transport=lambda u,t:reponse(
        {"name":"Cabinet", "formatted":"1 rue A, Vannes"})).rechercher("Cabinet Vannes")[0]
    with pytest.raises(ValueError,match="conservation durable"):
        enregistrer_proposition(proposition,autoriser=True)
