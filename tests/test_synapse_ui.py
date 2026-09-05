from unittest.mock import Mock
import pytest
from tests.test_ui import interface
from lumyn.modules.lieux import stockage as lieux
from lumyn.modules.rendez_vous import stockage, ui, agenda_google

@pytest.fixture
def carnet_enregistre():
    lieux.enregistrer_lieu({'nom':'Maison','adresses':[{'adresse':'1 rue Exemple, Ville Test','favorite':True}]})
    lieux.enregistrer_lieu({'nom':'Dr Laporte','alias':['Laporte'],'profession':'psychiatre','adresses':[{'adresse':'2 rue Exemple, Lorient','favorite':True}]})


def test_entree_creation_et_modification_meme_google(interface,carnet_enregistre,monkeypatch):
    creation=Mock(return_value={'id':'g1'})
    modification=Mock(return_value={'id':'g1'})
    monkeypatch.setattr(ui,'creer_evenement_google',creation)
    monkeypatch.setattr(ui,'modifier_evenement_google',modification)
    interface.rdv_input.value='Laporte jeudi 10h visio'
    interface.valider_depuis_saisie()
    creation.assert_not_called()
    assert '1 rue Exemple' in interface.resultat_label.text
    interface.valider_depuis_saisie()
    original=stockage.charger_rendez_vous()[0]
    assert original['titre']=='Dr Laporte — VISIO'
    assert creation.call_args.args[0]['lieu']=='1 rue Exemple, Ville Test'
    interface.charger_modification(None,original)
    interface.rdv_input.value=interface.rdv_input.value.replace('10h','11h')
    interface.valider_depuis_saisie()
    modification.assert_not_called()
    interface.valider_depuis_saisie()
    nouveau=stockage.charger_rendez_vous()[0]
    assert nouveau['id']==original['id'] and nouveau['google_event_id']=='g1'
    assert nouveau['lieu']==original['lieu']
    assert nouveau['titre']==original['titre']
    creation.assert_called_once()
    modification.assert_called_once()
    corps=agenda_google.construire_corps_evenement_google(nouveau)
    assert corps['summary']=='Dr Laporte — VISIO'
    assert corps['location']==original['lieu']
    assert 'conferenceData' not in corps


def test_entree_sur_saisie_changee_prepare_seulement(interface,monkeypatch):
    creation=Mock()
    monkeypatch.setattr(ui,'creer_evenement_google',creation)
    interface.rdv_input.value='CAF demain 10h'
    interface.valider_depuis_saisie()
    interface.rdv_input.value='CAF demain 11h'
    interface.valider_depuis_saisie()
    creation.assert_not_called()
    assert '11h' in interface.resultat_label.text


def test_maison_absente_bloque_google(interface,monkeypatch):
    creation=Mock()
    monkeypatch.setattr(ui,'creer_evenement_google',creation)
    interface.rdv_input.value='infirmière vendredi 9h à domicile'
    for _ in range(3):interface.valider_depuis_saisie()
    assert interface.resultat_courant['etat']=='incomplet'
    assert not interface.confirmer_button.enabled
    creation.assert_not_called()


def test_modification_domicile_sans_double_suffixe(interface,carnet_enregistre):
    interface._selectionner_calendrier_par_id(ui.CALENDRIER_LOCAL_ID)
    interface.rdv_input.value='infirmière vendredi 9h à domicile'
    interface.valider_depuis_saisie()
    interface.valider_depuis_saisie()
    original=stockage.charger_rendez_vous()[0]
    interface.charger_modification(None,original)
    interface.valider_depuis_saisie()
    assert interface.resultat_courant['rendez_vous']['titre']=='Infirmière — DOMICILE'


def test_carnet_illisible_bloque_sans_ecrire(interface,monkeypatch):
    lieux.FICHIER_LIEUX.write_text('{cassé')
    creation=Mock()
    monkeypatch.setattr(ui,'creer_evenement_google',creation)
    interface.rdv_input.value='ITEP mardi 14h'
    interface.valider_depuis_saisie()
    assert interface.resultat_courant['etat']=='erreur'
    interface.confirmer_rendez_vous(None)
    creation.assert_not_called()
    assert lieux.FICHIER_LIEUX.read_text()=='{cassé'


@pytest.mark.parametrize('destination', ['gaelle', ui.CALENDRIER_LOCAL_ID])
@pytest.mark.parametrize('preparer_avant', [True, False])
def test_calendrier_focus_et_double_entree(interface, monkeypatch, destination, preparer_avant):
    interface.calendrier_selection.items.append({'nom': 'Gaelle', 'calendar_id': 'gaelle'})
    creation = Mock(return_value={'id': 'g-focus'})
    monkeypatch.setattr(ui, 'creer_evenement_google', creation)
    focus = Mock(wraps=interface.rdv_input._impl.focus)
    monkeypatch.setattr(interface.rdv_input._impl, 'focus', focus)
    if preparer_avant:
        interface.rdv_input.value = 'CAF demain 10h'
        interface.rdv_input.on_confirm()
        assert interface.confirmer_button.enabled
    interface._selectionner_calendrier_par_id(destination)
    focus.assert_called_once()
    assert interface.resultat_courant is None
    assert interface.saisie_analysee is None
    assert not interface.confirmer_button.enabled
    interface.confirmer_rendez_vous(None)
    creation.assert_not_called()
    assert stockage.charger_rendez_vous() == []
    if not preparer_avant:
        interface.rdv_input.value = 'CAF demain 10h'
    interface.rdv_input.on_confirm()
    assert interface.saisie_analysee == ('CAF demain 10h', destination)
    assert interface.confirmer_button.enabled
    creation.assert_not_called()
    interface.rdv_input.on_confirm()
    assert len(stockage.charger_rendez_vous()) == 1
    if destination == ui.CALENDRIER_LOCAL_ID:
        creation.assert_not_called()
    else:
        creation.assert_called_once()
        assert creation.call_args.args[1] == destination


def test_aller_retour_calendrier_ne_restaure_pas_ancienne_preparation(interface, monkeypatch):
    creation = Mock()
    monkeypatch.setattr(ui, 'creer_evenement_google', creation)
    interface.rdv_input.value = 'CAF demain 10h'
    interface.rdv_input.on_confirm()
    interface._selectionner_calendrier_par_id(ui.CALENDRIER_LOCAL_ID)
    interface._selectionner_calendrier_par_id('famille')
    interface.rdv_input.on_confirm()
    creation.assert_not_called()
    assert interface.confirmer_button.enabled
    assert stockage.charger_rendez_vous() == []
