import json

import pytest

from lumyn.modules.synapse.gemini_web import (
    ErreurConfigurationGemini,
    FournisseurGeminiWeb,
    fournisseur_gemini_depuis_environnement,
)
from lumyn.modules.synapse.selection_lieux import enregistrer_proposition


def reponse(items, citations):
    return {"steps": [{"type": "model_output", "content": [{
        "type": "text", "text": json.dumps(items),
        "annotations": [{"type": "url_citation", "url": url} for url in citations],
    }]}]}


def test_gemini_absent_et_activation_payante_refusee():
    assert fournisseur_gemini_depuis_environnement({}) is None
    with pytest.raises(ErreurConfigurationGemini, match="niveau payant"):
        fournisseur_gemini_depuis_environnement({"LUMYN_GEMINI_WEB": "1", "GEMINI_API_KEY": "secret"})
    with pytest.raises(ErreurConfigurationGemini, match="API_KEY"):
        FournisseurGeminiWeb("")


def test_resultat_simule_exige_source_et_reste_non_persistable():
    url = "https://professionnel.example/adresse"
    items = [{"nom": "Cabinet Test", "adresse": "1 rue Test, Vannes",
              "profession": "médecin", "ville": "Vannes", "source_url": url}]
    fournisseur = FournisseurGeminiWeb("secret", transport=lambda *args: reponse(items, [url]))
    proposition = fournisseur.rechercher("Cabinet Test Vannes")[0]
    assert proposition.source.endswith(url)
    assert proposition.conservation_autorisee is False
    with pytest.raises(ValueError, match="conservation durable"):
        enregistrer_proposition(proposition, autoriser=True)


def test_resultat_sans_citation_est_rejete_et_plusieurs_sont_bornes():
    items = [{"nom": f"Lieu {i}", "adresse": f"{i} rue Test", "source_url": f"https://s{i}.example"}
             for i in range(5)]
    fournisseur = FournisseurGeminiWeb("secret", limite=2,
        transport=lambda *args: reponse(items, ["https://s1.example", "https://s2.example"]))
    propositions = fournisseur.rechercher("Lieu Test")
    assert [p.nom for p in propositions] == ["Lieu 1", "Lieu 2"]


def test_timeout_et_reponse_invalide_sans_exposer_cle():
    fournisseur = FournisseurGeminiWeb("tres-secret", transport=lambda *args:
        (_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(TimeoutError) as capture:
        fournisseur.rechercher("Lieu Test")
    assert "tres-secret" not in str(capture.value)
    fournisseur._transport = lambda *args: {"steps": []}
    with pytest.raises(ValueError):
        fournisseur.rechercher("Lieu Test")
