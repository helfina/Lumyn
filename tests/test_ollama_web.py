from unittest.mock import Mock

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


def test_cle_absente_et_activation_reelle_verrouillee():
    with pytest.raises(ErreurConfigurationOllamaWeb, match="OLLAMA_API_KEY"):
        FournisseurOllamaWeb("", ban=Mock())
    assert fournisseur_ollama_web_depuis_environnement({}) is None
    with pytest.raises(ErreurConfigurationOllamaWeb, match=r"18\+"):
        fournisseur_ollama_web_depuis_environnement(
            {"LUMYN_OLLAMA_WEB": "1", "OLLAMA_API_KEY": "fictive"}, ban=Mock())


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
        "Cabinet", "12 rue Test 56000 Vannes", "Ollama Web Search — source",
        adresse_verifiee=False,
    )
    public = Mock(rechercher=Mock(return_value=[]))
    web = Mock(rechercher=Mock(return_value=[proposition]))
    resultat = proposer_recherche_externe(
        PHRASE, public, autoriser=True, fournisseur_ia=web, autoriser_ia=True)
    assert resultat["fournisseur_utilise"] == "ia_web"
    web.rechercher.assert_called_once()
    assert not carnet.FICHIER_LIEUX.exists()

    public.rechercher.return_value = [BAN]
    web.reset_mock()
    proposer_recherche_externe(
        PHRASE, public, autoriser=True, fournisseur_ia=web, autoriser_ia=True)
    web.rechercher.assert_not_called()
