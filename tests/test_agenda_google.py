from datetime import date
from unittest.mock import Mock
import pytest
from lumyn.modules.rendez_vous import agenda_google as g

@pytest.fixture
def service(monkeypatch):
    service=Mock()
    monkeypatch.setattr(g,'obtenir_service_google_calendar',lambda:service)
    monkeypatch.setattr(g,'_EVENEMENTS_GOOGLE_SUPPRIMES',set())
    return service


def test_corps_google_date_lieu_et_rappels():
    corps=g.construire_corps_evenement_google({'titre':'CAF','date':date(2026,9,8),'heure':'23h30','lieu':'Lorient'})
    assert corps['start']['dateTime']=='2026-09-08T23:30:00+02:00'
    assert corps['end']['dateTime']=='2026-09-09T00:30:00+02:00'
    assert corps['location']=='Lorient'
    assert [r['minutes'] for r in corps['reminders']['overrides']]==[1440,60]


def test_creation_google(service):
    service.events().insert().execute.return_value={'id':'g1'}
    resultat=g.creer_evenement_google({'date':'2026-12-03','heure':'10h','titre':'CAF'},'famille')
    assert resultat=={'id':'g1'}
    args=service.events().insert.call_args.kwargs
    assert args['calendarId']=='famille'
    assert args['sendUpdates']=='none'
    assert args['body']['start']['dateTime'].endswith('+01:00')


def test_pagination_filtres_et_bornes(service):
    service.calendarList().list().execute.side_effect=[{'items':[{'id':'a','summary':'A'}],'nextPageToken':'suite'},{'items':[{'deleted':True,'id':'b'}]}]
    service.events().list().execute.side_effect=[{'items':[{'id':'1','status':'cancelled'},{'id':'2'}],'nextPageToken':'page2'},{'items':[{'id':'3'}]}]
    g._EVENEMENTS_GOOGLE_SUPPRIMES.add(('a','3'))
    assert [x['id'] for x in g.lister_evenements_google(2026,12)]==['2']
    args=service.events().list.call_args.kwargs
    assert args['timeMin']=='2026-12-01T00:00:00+01:00'
    assert args['timeMax']=='2027-01-01T00:00:00+01:00'
    assert args['pageToken']=='page2'


def test_suppression_masquee_seulement_apres_succes(service):
    service.events().delete().execute.side_effect=OSError('Hors ligne')
    with pytest.raises(OSError):g.supprimer_evenement_google('a','1')
    assert ('a','1') not in g._EVENEMENTS_GOOGLE_SUPPRIMES
    service.events().delete().execute.side_effect=None
    g.supprimer_evenement_google('a','1')
    assert ('a','1') in g._EVENEMENTS_GOOGLE_SUPPRIMES


def test_conversion_google_fuseau_et_journee():
    assert g.simplifier_evenement_google({'start':{'dateTime':'2026-09-08T22:30:00Z'}})['date']=='2026-09-09'
    assert g.simplifier_evenement_google({'start':{'date':'2026-09-08'}})['heure'] is None
