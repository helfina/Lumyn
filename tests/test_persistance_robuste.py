import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from lumyn.modules.lieux import stockage as lieux
from lumyn.modules.rendez_vous import calendrier_ui, reprise_google, stockage


@pytest.mark.parametrize("module,fonction,fichier,donnees", [
    (stockage, stockage.sauvegarder_rendez_vous,
     lambda: stockage.FICHIER_RENDEZ_VOUS, [{"id": "rdv-1", "titre": "École d'Élise"}]),
    (lieux, lieux.sauvegarder_lieux,
     lambda: lieux.FICHIER_LIEUX, [{"id": "lieu-1", "nom": "Cabinet d'Élise"}]),
    (reprise_google, reprise_google._sauvegarder,
     lambda: reprise_google.FICHIER_REPRISE,
     {"empreinte": {"id": "a" * 32, "calendrier": "Famille Élise"}}),
])
def test_remplacement_atomique_preserve_ancien_fichier(
        module, fonction, fichier, donnees, monkeypatch):
    destination = fichier()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("contenu sain", encoding="utf-8")
    monkeypatch.setattr(module.os, "replace", Mock(side_effect=PermissionError("verrouillé")))

    with pytest.raises(PermissionError):
        fonction(donnees)

    assert destination.read_text(encoding="utf-8") == "contenu sain"
    assert list(destination.parent.glob("*.tmp")) == []


def test_preferences_calendrier_ecriture_atomique(monkeypatch):
    fichier = calendrier_ui.FICHIER_PREFERENCES_CALENDRIERS
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text('{"famille": true}', encoding="utf-8")
    monkeypatch.setattr(
        calendrier_ui.os, "replace", Mock(side_effect=OSError("disque indisponible")))

    with pytest.raises(OSError):
        calendrier_ui.sauvegarder_preferences_calendriers({"famille": False})

    assert fichier.read_text(encoding="utf-8") == '{"famille": true}'
    assert list(fichier.parent.glob("calendriers-*.tmp")) == []


@pytest.mark.parametrize("module,fonction,donnees", [
    (stockage, stockage.sauvegarder_rendez_vous, []),
    (lieux, lieux.sauvegarder_lieux, []),
    (reprise_google, reprise_google._sauvegarder, {}),
])
def test_echec_creation_temporaire_ne_touche_pas_destination(
        module, fonction, donnees, monkeypatch):
    destination = getattr(module, "FICHIER_RENDEZ_VOUS", None) or getattr(
        module, "FICHIER_LIEUX", None) or module.FICHIER_REPRISE
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("sain", encoding="utf-8")
    monkeypatch.setattr(
        module.tempfile, "NamedTemporaryFile",
        Mock(side_effect=FileNotFoundError("dossier disparu")),
    )
    with pytest.raises(FileNotFoundError):
        fonction(donnees)
    assert destination.read_text(encoding="utf-8") == "sain"


@pytest.mark.parametrize("contenu", ["", "[", "{}", "[42]", "null", "\ufeff[]"])
def test_corruption_rendez_vous_est_conservee(contenu):
    stockage.FICHIER_RENDEZ_VOUS.write_text(contenu, encoding="utf-8")
    with pytest.raises(ValueError):
        stockage.enregistrer_rendez_vous({"titre": "Nouveau"})
    assert stockage.FICHIER_RENDEZ_VOUS.read_text(encoding="utf-8") == contenu


@pytest.mark.parametrize("contenu", ["", "[", "{}", "[null]", "null", "\ufeff[]"])
def test_corruption_carnet_est_conservee(contenu):
    lieux.FICHIER_LIEUX.write_text(contenu, encoding="utf-8")
    with pytest.raises(ValueError):
        lieux.enregistrer_lieu({"nom": "Nouveau"})
    assert lieux.FICHIER_LIEUX.read_text(encoding="utf-8") == contenu


@pytest.mark.parametrize("module,fichier,contenu", [
    (stockage, lambda: stockage.FICHIER_RENDEZ_VOUS,
     '[{"id":"meme","titre":"A"},{"id":"meme","titre":"B"}]'),
    (lieux, lambda: lieux.FICHIER_LIEUX,
     '[{"id":"meme","nom":"A"},{"id":"meme","nom":"B"}]'),
])
def test_identifiants_dupliques_sont_refuses_sans_ecriture(module, fichier, contenu):
    destination = fichier()
    destination.write_text(contenu, encoding="utf-8")
    chargeur = module.charger_rendez_vous if module is stockage else module.charger_lieux
    with pytest.raises(ValueError, match="même identifiant"):
        chargeur()
    assert destination.read_text(encoding="utf-8") == contenu


def test_champs_supplementaires_et_unicode_survivent_a_la_relecture():
    rdv = stockage.enregistrer_rendez_vous({
        "titre": "Rendez-vous d'Élise à Guémené", "extension": {"clé": "été"}})
    assert stockage.charger_rendez_vous()[0] == rdv
    fiche = lieux.enregistrer_lieu({
        "nom": "Centre médical Ker Anna", "champ_supplémentaire": "été"})
    assert lieux.charger_lieux()[0]["champ_supplémentaire"] == "été"
    assert fiche["id"] == lieux.charger_lieux()[0]["id"]


def test_journal_plusieurs_operations_ne_perd_que_celle_terminee():
    premier = reprise_google.reserver_creation("famille", {"summary": "A"})
    second = reprise_google.reserver_creation("travail", {"summary": "B"})
    assert premier != second
    reprise_google.terminer_creation("famille", premier)
    journal = json.loads(reprise_google.FICHIER_REPRISE.read_text(encoding="utf-8"))
    assert list(journal.values()) == [{"id": second, "calendrier": "travail"}]
    reprise_google.terminer_creation("famille", premier)
    assert json.loads(reprise_google.FICHIER_REPRISE.read_text(encoding="utf-8")) == journal


def test_journal_refuse_une_meme_cle_json_dupliquee_sans_la_recrire():
    cle = "b" * 64
    entree = '{"id":"' + "a" * 32 + '","calendrier":"famille"}'
    contenu = '{"' + cle + '":' + entree + ',"' + cle + '":' + entree + '}'
    reprise_google.FICHIER_REPRISE.write_text(contenu, encoding="utf-8")
    with pytest.raises(ValueError, match="journal de reprise"):
        reprise_google._charger()
    assert reprise_google.FICHIER_REPRISE.read_text(encoding="utf-8") == contenu


def test_journal_ne_contient_ni_corps_ni_secret():
    secret = "cle-oauth-fictive-ne-pas-conserver"
    reprise_google.reserver_creation(
        "famille", {"summary": "Consultation", "description": secret})
    texte = reprise_google.FICHIER_REPRISE.read_text(encoding="utf-8")
    assert secret not in texte
    assert "Consultation" not in texte


@pytest.mark.parametrize("entree", [
    {"id": "a" * 32},
    {"id": "a" * 32, "calendrier": "famille", "token": "fictif"},
])
def test_journal_refuse_champs_absents_ou_supplementaires(entree):
    contenu = json.dumps({"b" * 64: entree})
    reprise_google.FICHIER_REPRISE.write_text(contenu, encoding="utf-8")
    with pytest.raises(ValueError, match="journal de reprise"):
        reprise_google._charger()
    assert reprise_google.FICHIER_REPRISE.read_text(encoding="utf-8") == contenu


def test_echec_pendant_ecriture_temporaire_preserve_destination(monkeypatch):
    destination = stockage.FICHIER_RENDEZ_VOUS
    destination.write_text('[{"id":"sain"}]', encoding="utf-8")
    ouverture = stockage.tempfile.NamedTemporaryFile

    class EcritureEnPanne:
        def __init__(self, *args, **kwargs):
            self.fichier = ouverture(*args, **kwargs)
            self.name = self.fichier.name

        def __enter__(self):
            return self

        def write(self, contenu):
            self.fichier.write(contenu[:3])
            raise OSError("écriture interrompue")

        def __exit__(self, *args):
            return self.fichier.__exit__(*args)

    monkeypatch.setattr(stockage.tempfile, "NamedTemporaryFile", EcritureEnPanne)
    with pytest.raises(OSError, match="écriture interrompue"):
        stockage.sauvegarder_rendez_vous([{"id": "nouveau"}])
    assert destination.read_text(encoding="utf-8") == '[{"id":"sain"}]'
    assert list(destination.parent.glob("rendez_vous-*.tmp")) == []


def test_chemin_unicode_espaces_et_apostrophe_est_portable(tmp_path, monkeypatch):
    dossier = tmp_path / "Données d'Élise"
    fichier = dossier / "mes rendez-vous.json"
    monkeypatch.setattr(stockage, "DOSSIER_DONNEES", dossier)
    monkeypatch.setattr(stockage, "FICHIER_RENDEZ_VOUS", fichier)
    enregistre = stockage.enregistrer_rendez_vous({"titre": "Médecin à Vannes"})
    assert stockage.charger_rendez_vous() == [enregistre]
    assert list(dossier.glob("*.tmp")) == []
