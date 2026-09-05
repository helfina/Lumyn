from datetime import date
from unittest.mock import Mock
import pytest
import toga
from lumyn.modules.rendez_vous import ui, calendrier_ui, stockage

@pytest.fixture
def interface(monkeypatch, tmp_path):
    toga.App('Lumyn tests', 'fr.helfina.lumyn.tests')
    calendriers=[{'id':'famille','nom':'Famille','access_role':'owner','principal':True}]
    monkeypatch.setattr(ui,'lister_calendriers_google',lambda:calendriers)
    monkeypatch.setattr(calendrier_ui,'lister_calendriers_google',lambda:calendriers)
    monkeypatch.setattr(calendrier_ui,'lister_evenements_google_simples',lambda *args:[])
    monkeypatch.setattr(calendrier_ui,'FICHIER_PREFERENCES_CALENDRIERS',tmp_path/'prefs.json')
    monkeypatch.setattr(calendrier_ui,'DOSSIER_LUMYN',tmp_path)
    x=ui.InterfaceRendezVous()
    x.construire()
    return x


def test_creation_google_apres_confirmation(interface, monkeypatch):
    creation=Mock(return_value={'id':'google-1'})
    monkeypatch.setattr(ui,'creer_evenement_google',creation)
    interface.rdv_input.value='CAF demain 10h à Lorient'
    interface.analyser_rendez_vous(None)
    creation.assert_not_called()
    interface.confirmer_rendez_vous(None)
    creation.assert_called_once()
    rdv=stockage.charger_rendez_vous()[0]
    assert rdv['google_event_id']=='google-1'
    assert rdv['lieu']=='Lorient'
    interface.confirmer_rendez_vous(None)
    creation.assert_called_once()


def test_saisie_changee_invalide_confirmation(interface, monkeypatch):
    creation=Mock(return_value={'id':'google-1'})
    monkeypatch.setattr(ui,'creer_evenement_google',creation)
    interface.rdv_input.value='CAF demain 10h'
    interface.analyser_rendez_vous(None)
    interface.rdv_input.value='CAF demain 11h'
    interface.confirmer_rendez_vous(None)
    creation.assert_not_called()


def test_creation_locale_reste_disponible(interface, monkeypatch):
    creation=Mock()
    monkeypatch.setattr(ui,'creer_evenement_google',creation)
    choix=next(x for x in interface.calendrier_selection.items if x.calendar_id==ui.CALENDRIER_LOCAL_ID)
    interface.calendrier_selection.value=choix
    interface.rdv_input.value='CAF demain 10h'
    interface.analyser_rendez_vous(None)
    interface.confirmer_rendez_vous(None)
    creation.assert_not_called()
    assert len(stockage.charger_rendez_vous())==1
    assert not stockage.charger_rendez_vous()[0].get('google_event_id')


def test_modification_recharge_lieu(interface):
    rdv=stockage.enregistrer_rendez_vous({'titre':'CAF','date':date(2026,9,8),'heure':'10h','lieu':'Lorient'})
    interface.charger_modification(None,rdv)
    assert 'à Lorient' in interface.rdv_input.value


def test_creation_annulee_si_stockage_echoue(interface, monkeypatch):
    monkeypatch.setattr(ui,'creer_evenement_google',Mock(return_value={'id':'google-1'}))
    monkeypatch.setattr(ui,'enregistrer_rendez_vous',Mock(side_effect=OSError('Disque plein')))
    supprimer=Mock()
    monkeypatch.setattr(ui,'supprimer_evenement_google',supprimer)
    with pytest.raises(OSError):
        interface._creer_rendez_vous_lie({'titre':'CAF','date':date(2026,9,8),'heure':'10h'})
    supprimer.assert_called_once_with('famille','google-1')


def test_modification_google_annulee_si_stockage_leve_exception(interface, monkeypatch):
    original={'id':'local-1','titre':'CAF','date':'2026-09-08','heure':'10h','google_event_id':'g1','google_calendar_id':'famille'}
    interface.rendez_vous_en_modification=original
    modification=Mock(return_value={'id':'g1'})
    monkeypatch.setattr(ui,'modifier_evenement_google',modification)
    monkeypatch.setattr(ui,'modifier_rendez_vous_stockage',Mock(side_effect=OSError('Disque plein')))
    with pytest.raises((RuntimeError,OSError)):
        interface._modifier_rendez_vous_lie(dict(original,heure='11h'))
    assert modification.call_count==2
    assert modification.call_args.args[0]['heure']=='10h'


def test_mode_local_sans_google_et_cycle_complet(interface, monkeypatch):
    monkeypatch.setattr(ui,'lister_calendriers_google',Mock(side_effect=OSError('Hors ligne')))
    interface._charger_calendriers_google()
    interface.calendrier_selection.items=interface._items_calendriers()
    interface._selectionner_calendrier_defaut()
    interface.rdv_input.value='CAF demain 10h à Lorient'
    interface.analyser_rendez_vous(None)
    assert interface.confirmer_button.enabled
    interface.confirmer_rendez_vous(None)
    original=stockage.charger_rendez_vous()[0]
    interface.charger_modification(None,original)
    interface.rdv_input.value=interface.rdv_input.value.replace('10h','11h').replace(' à Lorient','')
    interface.analyser_rendez_vous(None)
    interface.confirmer_rendez_vous(None)
    nouveau=stockage.charger_rendez_vous()[0]
    assert nouveau['id']==original['id']
    assert nouveau['heure']=='11h'
    assert nouveau['lieu'] is None
    assert interface._supprimer_rendez_vous_lie(nouveau)['local_supprime']
    assert stockage.charger_rendez_vous()==[]


def test_calendrier_change_exige_nouvelle_analyse(interface, monkeypatch):
    creation=Mock()
    monkeypatch.setattr(ui,'creer_evenement_google',creation)
    interface.rdv_input.value='CAF demain 10h'
    interface.analyser_rendez_vous(None)
    interface._selectionner_calendrier_par_id(ui.CALENDRIER_LOCAL_ID)
    interface.confirmer_rendez_vous(None)
    creation.assert_not_called()
    assert stockage.charger_rendez_vous()==[]


def test_modification_et_deplacement_google(interface, monkeypatch):
    original=stockage.enregistrer_rendez_vous({'titre':'CAF','date':'2026-09-08','heure':'10h','google_event_id':'g1','google_calendar_id':'autre','champ_conserve':True})
    interface.rendez_vous_en_modification=original
    deplacer=Mock(return_value={'id':'g2'})
    modifier=Mock(return_value={'id':'g2'})
    monkeypatch.setattr(ui,'deplacer_evenement_google',deplacer)
    monkeypatch.setattr(ui,'modifier_evenement_google',modifier)
    interface._modifier_rendez_vous_lie({'titre':'CAF','date':'2026-09-08','heure':'11h'})
    deplacer.assert_called_once_with('autre','famille','g1')
    sauvegarde=stockage.charger_rendez_vous()[0]
    assert sauvegarde['google_event_id']=='g2'
    assert sauvegarde['google_calendar_id']=='famille'
    assert sauvegarde['champ_conserve'] is True


def test_suppression_google_reussie_et_echec(interface, monkeypatch):
    rdv=stockage.enregistrer_rendez_vous({'titre':'CAF','google_event_id':'g1','google_calendar_id':'famille'})
    suppression=Mock(side_effect=OSError('Hors ligne'))
    monkeypatch.setattr(ui,'supprimer_evenement_google',suppression)
    with pytest.raises(OSError):
        interface._supprimer_rendez_vous_lie(rdv)
    assert stockage.charger_rendez_vous()==[rdv]
    suppression.side_effect=None
    interface._supprimer_rendez_vous_lie(rdv)
    assert stockage.charger_rendez_vous()==[]
