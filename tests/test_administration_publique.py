import json
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

from lumyn.modules.synapse.administration_publique import (
    FournisseurAdministration,
    SOURCE_ADMINISTRATION,
)


def organisme(nom="Caisse d'allocations familiales (Caf) du Morbihan - siège de Vannes",
              identifiant="c29811a7-0462-46f0-9775-edd274a8bbc8",
              voie="70 rue de Sainte-Anne", ville="Vannes Cedex"):
    return {
        "nom": nom,
        "id": identifiant,
        "adresse": json.dumps([{
            "type_adresse": "Adresse", "complement1": "", "complement2": "",
            "numero_voie": voie, "service_distribution": "",
            "code_postal": "56018", "nom_commune": ville,
        }]),
    }


def test_recherche_caf_convertit_le_schema_dila_reel_sans_cle():
    appels = []
    fournisseur = FournisseurAdministration(
        limite=3,
        transport=lambda url, timeout: appels.append((url, timeout)) or {
            "total_count": 1, "results": [organisme()]},
    )

    propositions = fournisseur.rechercher("CAF Vannes")

    assert len(propositions) == 1
    proposition = propositions[0]
    assert proposition.nom == (
        "Caisse d'allocations familiales (Caf) du Morbihan - siège de Vannes")
    assert proposition.adresse == "70 rue de Sainte-Anne, 56018 Vannes Cedex"
    assert proposition.ville == "Vannes Cedex"
    assert proposition.identifiant == "c29811a7-0462-46f0-9775-edd274a8bbc8"
    assert proposition.source == SOURCE_ADMINISTRATION
    assert proposition.conservation_autorisee is True
    assert proposition.adresse_verifiee is False
    parametres = parse_qs(urlsplit(appels[0][0]).query)
    assert parametres == {
        "where": ['search(*, "CAF Vannes")'], "limit": ["3"]}
    assert appels[0][1] == 6


def test_reponse_vide_et_entrees_partielles_sont_ignorees():
    fournisseur = FournisseurAdministration(
        transport=lambda url, timeout: {"results": []})
    assert fournisseur.rechercher("CAF Vannes") == []
    fournisseur._transport = lambda url, timeout: {"results": [
        "invalide", {"nom": "Sans adresse"},
        {"nom": "Adresse invalide", "adresse": "{json tronqué"},
        {"nom": "Adresse postale", "adresse": json.dumps([{
            "type_adresse": "Adresse postale", "numero_voie": "70 rue Test",
        }])},
    ]}
    assert fournisseur.rechercher("CAF Vannes") == []


@pytest.mark.parametrize("charge", [{}, {"results": {}}, [], None])
def test_reponse_globale_invalide_est_signalee(charge):
    fournisseur = FournisseurAdministration(
        transport=lambda url, timeout: charge)
    with pytest.raises(ValueError, match="invalide"):
        fournisseur.rechercher("CAF Vannes")


@pytest.mark.parametrize("erreur,type_attendu", [
    (TimeoutError(), TimeoutError),
    (OSError(), OSError),
    (HTTPError("https://example.invalid", 503, "erreur", {}, None), OSError),
])
def test_erreurs_transport_sont_maitrisees(erreur, type_attendu):
    fournisseur = FournisseurAdministration(
        transport=lambda *args: (_ for _ in ()).throw(erreur))
    with pytest.raises(type_attendu):
        fournisseur.rechercher("CAF Vannes")


def test_dedoublonnage_et_limite_s_appliquent_aux_adresses_valides():
    premier = organisme()
    doublon = organisme(
        nom=premier["nom"].upper(), voie="70 RUE DE SAINTE-ANNE",
        ville="VANNES CEDEX")
    second = organisme("Mairie de Vannes", "mairie-1", "Place Maurice Marchais", "Vannes")
    troisieme = organisme("CCAS de Vannes", "ccas-1", "22 avenue Victor Hugo", "Vannes")
    fournisseur = FournisseurAdministration(
        limite=2, transport=lambda url, timeout: {
            "results": [premier, doublon, second, troisieme]})

    propositions = fournisseur.rechercher("administration Vannes")

    assert [p.identifiant for p in propositions] == [premier["id"], "mairie-1"]
