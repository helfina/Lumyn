from unittest.mock import Mock
from urllib.error import HTTPError

import pytest

from lumyn.modules.lieux import stockage as carnet
from lumyn.modules.synapse.ollama_web import (
    ErreurConfigurationOllamaWeb,
    FournisseurOllamaWeb,
    fournisseur_ollama_web_depuis_environnement,
)
from lumyn.modules.synapse.recherche_lieux import (
    PropositionLieu,
    proposer_recherche_externe,
)


PHRASE = "Dr Laporte psychiatre Lorient jeudi 10h"
WEB = {
    "title": "Cabinet du Dr Laporte",
    "url": "https://cabinet.example/contact",
    "content": "Consultations au 12 rue des Fleurs, 56000 Vannes.",
}
BAN = PropositionLieu(
    "12 rue des Fleurs", "12 Rue des Fleurs 56000 Vannes",
    "Géoplateforme / Base Adresse Nationale — Licence Ouverte 2.0",
    ville="Vannes", conservation_autorisee=True, adresse_verifiee=True,
)


def test_cle_absente_et_activation_locale_explicite():
    with pytest.raises(ErreurConfigurationOllamaWeb, match="OLLAMA_API_KEY"):
        FournisseurOllamaWeb("", ban=Mock())
    assert fournisseur_ollama_web_depuis_environnement({}) is None
    with pytest.raises(ErreurConfigurationOllamaWeb, match="OLLAMA_API_KEY"):
        fournisseur_ollama_web_depuis_environnement(
            {"LUMYN_OLLAMA_WEB": "1"}, ban=Mock())
    ban = Mock()
    fournisseur = fournisseur_ollama_web_depuis_environnement(
        {"LUMYN_OLLAMA_WEB": "1", "OLLAMA_API_KEY": "fictive"}, ban=ban)
    assert isinstance(fournisseur, FournisseurOllamaWeb)
    assert fournisseur.ban is ban


def test_activation_web_exige_ban_et_valeur_connue():
    with pytest.raises(ErreurConfigurationOllamaWeb, match="BAN"):
        fournisseur_ollama_web_depuis_environnement(
            {"LUMYN_OLLAMA_WEB": "1", "OLLAMA_API_KEY": "fictive"})
    with pytest.raises(ErreurConfigurationOllamaWeb, match="doit valoir"):
        fournisseur_ollama_web_depuis_environnement(
            {"LUMYN_OLLAMA_WEB": "peut-etre", "OLLAMA_API_KEY": "fictive"},
            ban=Mock())


@pytest.mark.parametrize("activation", [None, "", "0", "false", "off"])
def test_cle_seule_ou_web_desactive_ne_cree_aucun_trafic(activation):
    environnement = {"OLLAMA_API_KEY": "secret-fictif"}
    if activation is not None:
        environnement["LUMYN_OLLAMA_WEB"] = activation
    transport = Mock()
    assert fournisseur_ollama_web_depuis_environnement(
        environnement, ban=Mock()) is None
    transport.assert_not_called()


@pytest.mark.parametrize("code", [401, 403, 429, 500, 503])
def test_secret_absent_des_exceptions_reseau(code):
    secret = "cle-super-secrete-fictive"
    moteur = FournisseurOllamaWeb(
        secret, ban=Mock(),
        transport=lambda *args: (_ for _ in ()).throw(
            HTTPError("https://ollama.com", code, secret, {}, None)))
    with pytest.raises(OSError) as capture:
        moteur.rechercher("Laporte Lorient")
    assert secret not in str(capture.value)


def test_resultat_source_verifie_et_normalise_par_ban():
    appels = []
    ban = Mock(rechercher=Mock(return_value=[BAN]))
    moteur = FournisseurOllamaWeb(
        "cle-fictive", ban=ban,
        transport=lambda url, corps, timeout, cle:
            appels.append((url, corps, timeout, cle)) or {"results": [WEB]},
    )
    propositions = moteur.rechercher("Dr Laporte psychiatre Lorient")
    assert len(propositions) == 1
    proposition = propositions[0]
    assert proposition.adresse == BAN.adresse and proposition.adresse_verifiee
    assert WEB["url"] in proposition.source and "Géoplateforme" in proposition.source
    assert not proposition.conservation_autorisee
    ban.rechercher.assert_called_once_with("12 rue des Fleurs, 56000 Vannes")
    assert appels[0][1] == {
        "query": "Dr Laporte psychiatre Lorient adresse professionnelle",
        "max_results": 3,
    }
    assert appels[0][3] == "cle-fictive"


def test_echec_ban_garde_proposition_explicitement_non_verifiee():
    ban = Mock(rechercher=Mock(side_effect=OSError("indisponible")))
    moteur = FournisseurOllamaWeb(
        "fictive", ban=ban,
        transport=lambda *args: {"results": [WEB]},
    )
    proposition = moteur.rechercher("Laporte Lorient")[0]
    assert proposition.adresse == "12 rue des Fleurs, 56000 Vannes"
    assert not proposition.adresse_verifiee
    assert not proposition.conservation_autorisee


def test_zero_resultat_et_resultat_sans_source_ou_adresse_sont_insuffisants():
    moteur = FournisseurOllamaWeb(
        "fictive", ban=Mock(), transport=lambda *args: {"results": []})
    assert moteur.rechercher("Laporte Lorient") == []


def test_url_invalide_doublons_et_limite_web():
    invalides = [
        dict(WEB, url="http://"),
        dict(WEB, url="ftp://cabinet.example/contact"),
        dict(WEB, url="pas-une-url"),
        dict(WEB, url="https://utilisateur:secret@cabinet.example/contact"),
    ]
    valides = [dict(WEB), dict(WEB)] + [
        dict(WEB, title=f"Cabinet {i}", url=f"https://cabinet{i}.example/contact",
             content=f"Adresse : {i} rue Test, 56000 Vannes.")
        for i in range(1, 6)
    ]
    moteur = FournisseurOllamaWeb(
        "fictive", ban=Mock(rechercher=Mock(return_value=[])), limite=3,
        transport=lambda *args: {"results": invalides + valides})
    propositions = moteur.rechercher("Laporte Lorient")
    assert len(propositions) == 3
    assert len({(p.identifiant, p.adresse) for p in propositions}) == 3
    assert all(p.identifiant.startswith("https://") for p in propositions)
    assert all(not p.conservation_autorisee for p in propositions)


def test_ban_ne_verifie_pas_deux_rues_differentes_aux_mots_generiques_communs():
    faux = PropositionLieu(
        "12 rue des Lilas", "12 rue des Lilas 56000 Vannes", "BAN",
        ville="Vannes", adresse_verifiee=True)
    ban = Mock(rechercher=Mock(return_value=[faux]))
    web = dict(WEB, content="Adresse : 12 rue des Fleurs, 56000 Vannes.")
    moteur = FournisseurOllamaWeb(
        "fictive", ban=ban, transport=lambda *args: {"results": [web]})
    proposition = moteur.rechercher("Laporte Lorient")[0]
    assert proposition.adresse == "12 rue des Fleurs, 56000 Vannes"
    assert not proposition.adresse_verifiee
    assert not proposition.conservation_autorisee
    assert WEB["url"] in proposition.source
    moteur._transport = lambda *args: {"unexpected": []}
    with pytest.raises(ValueError, match="invalide"):
        moteur.rechercher("Laporte Lorient")
    moteur._transport = lambda *args: {"results": [
        dict(WEB, url=""),
        dict(WEB, content="Cabinet à Vannes sans adresse complète"),
    ]}
    assert moteur.rechercher("Laporte Lorient") == []


def test_adresses_contradictoires_restent_deux_propositions():
    second = dict(WEB, url="https://annuaire.example/laporte",
                  content="Adresse : 8 avenue Victor Hugo, 56100 Lorient.")
    ban = Mock(rechercher=Mock(return_value=[]))
    moteur = FournisseurOllamaWeb(
        "fictive", ban=ban,
        transport=lambda *args: {"results": [WEB, second]},
    )
    propositions = moteur.rechercher("Laporte psychiatre Lorient")
    assert [p.adresse for p in propositions] == [
        "12 rue des Fleurs, 56000 Vannes", "8 avenue Victor Hugo, 56100 Lorient"]
    assert all(not p.adresse_verifiee for p in propositions)


@pytest.mark.parametrize("erreur,type_attendu", [
    (TimeoutError(), TimeoutError), (OSError(), OSError),
])
def test_timeout_et_erreur_web_restent_propres(erreur, type_attendu):
    moteur = FournisseurOllamaWeb(
        "fictive", ban=Mock(),
        transport=lambda *args: (_ for _ in ()).throw(erreur),
    )
    with pytest.raises(type_attendu):
        moteur.rechercher("Laporte Lorient")


def test_web_dernier_recours_uniquement_et_aucune_ecriture():
    proposition = PropositionLieu(
        "Cabinet Dr Laporte", "12 rue Test 56100 Lorient", "Ollama Web Search — source",
        profession="psychiatre", ville="Lorient",
        adresse_verifiee=False,
    )
    public = Mock(rechercher=Mock(return_value=[]))
    web = Mock(rechercher=Mock(return_value=[proposition]))
    resultat = proposer_recherche_externe(
        PHRASE, public, autoriser=True, fournisseur_ia=web, autoriser_ia=True)
    assert resultat["fournisseur_utilise"] == "ia_web"
    web.rechercher.assert_called_once()
    assert not carnet.FICHIER_LIEUX.exists()

    public.rechercher.return_value = [PropositionLieu(
        "Cabinet Dr Laporte", "8 rue Test 56100 Lorient", "FINESS",
        profession="psychiatre", ville="Lorient")]
    web.reset_mock()
    proposer_recherche_externe(
        PHRASE, public, autoriser=True, fournisseur_ia=web, autoriser_ia=True)
    web.rechercher.assert_not_called()
