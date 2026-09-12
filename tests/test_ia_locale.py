import pytest
from unittest.mock import Mock

from lumyn.modules.synapse.ia_locale import (
    ErreurConfigurationIALocale,
    InterpreteurOllama,
    interpreteur_local_depuis_environnement,
)
from lumyn.modules.synapse.interpreteur_rendez_vous import interpreter_rendez_vous
from lumyn.modules.synapse.recherche_lieux import proposer_recherche_externe


def test_absence_ia_laisse_synapse_fonctionner():
    assert interpreteur_local_depuis_environnement({}) is None
    resultat = interpreter_rendez_vous("Dentiste mardi 14h")
    assert resultat["date"] and resultat["heure"] == "14h"


def test_activation_ollama_absente_ne_cree_ni_nappelle_transport():
    transport = Mock()
    assert interpreteur_local_depuis_environnement(
        {}, transport=transport) is None
    transport.assert_not_called()


def test_ollama_sortie_valide_et_requete_locale_minimale():
    appels = []
    moteur = InterpreteurOllama("qwen-test", transport=lambda url, corps, timeout:
        appels.append((url, corps, timeout)) or {"response":
            '{"personne":"Laporte","profession":"psychologue","ville":"Lorient","mode":"physique"}'})
    resultat = moteur.interpreter("ma psy Laporte jeudi 10h à Lorient")
    assert resultat == {"personne": "Laporte", "profession": "psychologue",
                        "ville": "Lorient", "mode": "physique"}
    assert appels[0][0] == "http://127.0.0.1:11434/api/generate"
    assert appels[0][1]["stream"] is False and appels[0][1]["format"] == "json"


@pytest.mark.parametrize("reponse", [
    "pas du json",
    '{"adresse":"1 rue inventée"}',
    '{"mode":"magique"}',
    '{"indices":"pas une liste"}',
])
def test_sortie_invalide_hallucination_ou_champ_inconnu_rejetee(reponse):
    moteur = InterpreteurOllama("test", transport=lambda u, c, t: {"response": reponse})
    with pytest.raises(ValueError):
        moteur.interpreter("demande")


def test_timeout_et_configuration_stricte():
    moteur = InterpreteurOllama("test", transport=lambda u, c, t:
        (_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(TimeoutError):
        moteur.interpreter("demande")
    configure = interpreteur_local_depuis_environnement({"LUMYN_IA_LOCALE": "ollama"})
    assert configure.modele == "llama3.2:1b"
    with pytest.raises(ErreurConfigurationIALocale, match="local"):
        InterpreteurOllama("test", url="https://serveur.example")


def test_ollama_local_enrichit_seulement_la_requete_externe():
    interpreteur = Mock(interpreter=Mock(return_value={
        "personne": "Laporte", "profession": "psychologue", "ville": "Lorient",
        "date": "jeudi", "heure": "10h", "mode": "physique",
    }))
    public = Mock(rechercher=Mock(return_value=[]))
    resultat = proposer_recherche_externe(
        "j'ai rdv avec ma psy Laporte jeudi vers 10h à son cabinet de Lorient",
        public, autoriser=True, interpreteur_local=interpreteur)
    requete = public.rechercher.call_args.args[0]
    assert "Laporte" in requete and "psychologue" in requete and "Lorient" in requete
    assert "jeudi" not in requete and "10h" not in requete
    assert resultat["rendez_vous"]["heure"] == "10h"
    interpreteur.interpreter.assert_called_once()


def test_ollama_local_peut_retrouver_le_carnet_avant_le_reseau():
    interpreteur = Mock(interpreter=Mock(return_value={
        "personne": "Laporte", "profession": "psychologue", "ville": "Lorient",
    }))
    lieux = [{
        "id": "laporte", "nom": "Dr Laporte", "alias": ["Laporte"],
        "profession": "psychologue", "categorie": "professionnel",
        "adresses": [{"adresse": "2 rue Exemple, 56100 Lorient", "favorite": True}],
    }]
    public = Mock()
    resultat = proposer_recherche_externe(
        "j'ai rdv avec ma psy Laporte jeudi vers 10h à son cabinet de Lorient",
        public, autoriser=True, interpreteur_local=interpreteur, lieux=lieux)
    public.rechercher.assert_not_called()
    assert resultat["rendez_vous"]["lieu_source"] == "carnet"
    assert resultat["rendez_vous"]["lieu"] == "2 rue Exemple, 56100 Lorient"


@pytest.mark.parametrize("erreur", [OSError(), TimeoutError(), ValueError()])
def test_panne_ollama_local_conserve_synapse_et_recherche_publique(erreur):
    interpreteur = Mock(interpreter=Mock(side_effect=erreur))
    public = Mock(rechercher=Mock(return_value=[]))
    resultat = proposer_recherche_externe(
        "Dentiste Lorient mardi 14h", public, autoriser=True,
        interpreteur_local=interpreteur)
    public.rechercher.assert_called_once()
    assert resultat["etat"] == "incomplet"
    assert type(erreur).__name__ in resultat["problemes_recherche"]
