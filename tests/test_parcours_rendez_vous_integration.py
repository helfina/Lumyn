import asyncio
from unittest.mock import Mock

from lumyn.modules.lieux import stockage as carnet
from lumyn.modules.rendez_vous import stockage, ui
from lumyn.modules.synapse.recherche_lieux import PropositionLieu
from lumyn.modules.synapse.recherche_ui import RechercheLieuxUI
from tests.test_ui import interface


PHRASE_CARNET = (
    "j'ai rendez-vous avec ma psy Laporte jeudi vers 10h "
    "à son cabinet de Lorient"
)
PHRASE_EXTERNE = (
    "rendez-vous avec le dermatologue Dupont mardi 14h "
    "à son cabinet de Vannes"
)
PUBLIC = PropositionLieu(
    "Dr Dupont", "1 rue Exemple, 56000 Vannes", "FINESS — source simulée",
    "dermatologue", "Vannes", conservation_autorisee=True,
)
PUBLIC_2 = PropositionLieu(
    "Cabinet Dupont", "8 avenue Exemple, 56000 Vannes",
    "Entreprises — source simulée", "dermatologue", "Vannes",
    conservation_autorisee=True,
)
WEB = PropositionLieu(
    "Dr Dupont", "4 place Exemple, 56000 Vannes",
    "Ollama Web — https://annuaire.example/dupont", "dermatologue",
    "Vannes", conservation_autorisee=False, adresse_verifiee=False,
)


def test_bout_en_bout_carnet_confirmation_google_et_persistance(
        interface, monkeypatch):
    externe = Mock()
    creation = Mock(return_value={"id": "google-carnet"})
    monkeypatch.setattr(ui, "creer_evenement_google", creation)
    carnet.enregistrer_lieu({
        "nom": "Dr Laporte", "alias": ["Laporte"], "profession": "psy",
        "adresses": [{"adresse": "2 rue Exemple, 56100 Lorient",
                       "favorite": True}],
    })
    interface.fournisseur_lieux = externe
    interface.rdv_input.value = PHRASE_CARNET
    interface.analyser_rendez_vous(None)
    assert interface.resultat_courant["rendez_vous"]["lieu_source"] == "carnet"
    externe.rechercher.assert_not_called()
    creation.assert_not_called()
    interface.confirmer_rendez_vous(None)
    creation.assert_called_once()
    sauvegarde = stockage.charger_rendez_vous()
    assert len(sauvegarde) == 1
    assert sauvegarde[0]["google_event_id"] == "google-carnet"


def test_bout_en_bout_public_choix_confirmation_google_sans_ecriture_carnet(
        interface, monkeypatch):
    fournisseur = Mock(rechercher=Mock(return_value=[PUBLIC]))
    creation = Mock(return_value={"id": "google-public"})
    monkeypatch.setattr(ui, "creer_evenement_google", creation)
    panneau = RechercheLieuxUI(interface, fournisseur)
    interface.rdv_input.value = PHRASE_EXTERNE
    interface.analyser_rendez_vous(None)
    assert not interface.confirmer_button.enabled
    asyncio.run(panneau.rechercher())
    assert panneau.propositions == [PUBLIC]
    assert not interface.confirmer_button.enabled
    panneau.choisir(PUBLIC)
    assert interface.resultat_courant["rendez_vous"]["lieu_provenance"] == PUBLIC.source
    assert interface.confirmer_button.enabled
    assert not carnet.FICHIER_LIEUX.exists()
    interface.confirmer_rendez_vous(None)
    creation.assert_called_once()
    assert stockage.charger_rendez_vous()[0]["google_event_id"] == "google-public"
    assert not carnet.FICHIER_LIEUX.exists()


def test_choix_externe_devient_invalide_apres_modification(interface):
    fournisseur = Mock(rechercher=Mock(return_value=[PUBLIC]))
    panneau = RechercheLieuxUI(interface, fournisseur)
    interface.rdv_input.value = PHRASE_EXTERNE
    asyncio.run(panneau.rechercher())
    panneau.choisir(PUBLIC)
    assert interface.confirmer_button.enabled
    interface.rdv_input.value = "Dr Dupont dermatologue Rennes mardi 14h"
    panneau.choisir(PUBLIC)
    assert panneau.selection is None
    assert not interface.confirmer_button.enabled


def test_google_echoue_avant_succes_sans_fausse_persistance(
        interface, monkeypatch):
    creation = Mock(side_effect=OSError("Google simulé indisponible"))
    monkeypatch.setattr(ui, "creer_evenement_google", creation)
    interface.rdv_input.value = "CAF demain 10h"
    interface.analyser_rendez_vous(None)
    interface.confirmer_rendez_vous(None)
    assert "Synchronisation impossible" in interface.resultat_label.text
    assert "Google simulé indisponible" in interface.resultat_label.text
    assert stockage.charger_rendez_vous() == []


def test_double_confirmation_ne_cree_quun_evenement(interface, monkeypatch):
    creation = Mock(return_value={"id": "google-unique"})
    monkeypatch.setattr(ui, "creer_evenement_google", creation)
    interface.rdv_input.value = "CAF demain 10h"
    interface.analyser_rendez_vous(None)
    interface.confirmer_rendez_vous(None)
    interface.confirmer_rendez_vous(None)
    creation.assert_called_once()
    assert len(stockage.charger_rendez_vous()) == 1


def test_mode_local_bout_en_bout_nappelle_pas_google(interface, monkeypatch):
    creation = Mock()
    monkeypatch.setattr(ui, "creer_evenement_google", creation)
    choix = next(x for x in interface.calendrier_selection.items
                 if x.calendar_id == ui.CALENDRIER_LOCAL_ID)
    interface.calendrier_selection.value = choix
    interface.rdv_input.value = "CAF demain 10h"
    interface.analyser_rendez_vous(None)
    interface.confirmer_rendez_vous(None)
    creation.assert_not_called()
    assert len(stockage.charger_rendez_vous()) == 1


def test_deux_professionnels_du_carnet_bloquent_confirmation(interface):
    for suffixe in ("A", "B"):
        carnet.enregistrer_lieu({
            "nom": f"Dr Laporte {suffixe}", "alias": ["Laporte"],
            "profession": "psy",
            "adresses": [{"adresse": "2 rue Exemple, 56100 Lorient"}],
        })
    interface.rdv_input.value = PHRASE_CARNET
    interface.analyser_rendez_vous(None)
    assert interface.resultat_courant["etat"] == "ambigu"
    assert interface.resultat_courant["rendez_vous"]["lieu"] is None
    assert not interface.confirmer_button.enabled


def test_deux_sites_compatibles_du_carnet_bloquent_confirmation(interface):
    carnet.enregistrer_lieu({
        "nom": "Dr Laporte", "alias": ["Laporte"], "profession": "psy",
        "adresses": [
            {"adresse": "2 rue Exemple, 56100 Lorient"},
            {"adresse": "8 avenue Exemple, 56100 Lorient"},
        ],
    })
    interface.rdv_input.value = PHRASE_CARNET
    interface.analyser_rendez_vous(None)
    assert interface.resultat_courant["etat"] == "ambigu"
    assert interface.resultat_courant["rendez_vous"]["lieu"] is None
    assert not interface.confirmer_button.enabled


def test_plusieurs_propositions_externes_exigent_un_choix(interface):
    fournisseur = Mock(rechercher=Mock(return_value=[PUBLIC, PUBLIC_2]))
    panneau = RechercheLieuxUI(interface, fournisseur)
    interface.rdv_input.value = PHRASE_EXTERNE
    asyncio.run(panneau.rechercher())
    assert panneau.propositions == [PUBLIC, PUBLIC_2]
    assert panneau.selection is None
    assert interface.resultat_courant is None
    assert not interface.confirmer_button.enabled


def test_web_exige_activation_et_autorisation_par_recherche(interface):
    public = Mock(rechercher=Mock(return_value=[]))
    web = Mock(rechercher=Mock(return_value=[WEB]))
    panneau = RechercheLieuxUI(interface, public, fournisseur_ia=web)
    interface.rdv_input.value = PHRASE_EXTERNE

    asyncio.run(panneau.rechercher())
    web.rechercher.assert_not_called()
    assert panneau.propositions == []

    panneau.ia_switch.value = True
    asyncio.run(panneau.rechercher())
    web.rechercher.assert_called_once()
    assert panneau.propositions == [WEB]
    assert not panneau.propositions[0].conservation_autorisee
    assert not interface.confirmer_button.enabled


def test_resultat_public_fiable_interdit_le_repli_web(interface):
    public = Mock(rechercher=Mock(return_value=[PUBLIC]))
    web = Mock(rechercher=Mock(return_value=[WEB]))
    panneau = RechercheLieuxUI(interface, public, fournisseur_ia=web)
    panneau.ia_switch.value = True
    interface.rdv_input.value = PHRASE_EXTERNE
    asyncio.run(panneau.rechercher())
    assert panneau.propositions == [PUBLIC]
    web.rechercher.assert_not_called()


def test_echec_externe_ne_reactive_pas_ancienne_confirmation(interface):
    interface.rdv_input.value = "CAF demain 10h"
    interface.analyser_rendez_vous(None)
    assert interface.confirmer_button.enabled
    panneau = RechercheLieuxUI(
        interface, Mock(rechercher=Mock(side_effect=OSError("indisponible"))))
    interface.rdv_input.value = PHRASE_EXTERNE
    asyncio.run(panneau.rechercher())
    assert interface.resultat_courant["etat"] == "incomplet"
    assert interface.resultat_courant["rendez_vous"]["titre"] != "CAF"
    assert not interface.confirmer_button.enabled
