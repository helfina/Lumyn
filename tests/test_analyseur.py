from datetime import date
import pytest
from lumyn.modules.rendez_vous import analyseur as a
from lumyn.modules.rendez_vous.gestion import preparer_rendez_vous

@pytest.fixture(autouse=True)
def date_fixe(monkeypatch):
    class DateFixe(date):
        @classmethod
        def today(cls):
            return cls(2026, 9, 5)
    monkeypatch.setattr(a, 'date', DateFixe)

@pytest.mark.parametrize('heure,attendu', [('14h','14h'),('14h30','14h30'),('14 h 30','14h30'),('14:30','14h30'),('9h','09h'),('09h00','09h')])
def test_formats_heures(heure, attendu):
    r = preparer_rendez_vous(f'Dentiste demain {heure}')
    assert r['etat'] == 'confirmation'
    assert r['rendez_vous']['heure'] == attendu

@pytest.mark.parametrize('heure', ['14:99', '14h 99', '25h', '9h5', '14:', '14h30 15h'])
def test_heures_invalides_ou_multiples(heure):
    assert preparer_rendez_vous(f'Dentiste demain {heure}')['etat'] == 'erreur'

@pytest.mark.parametrize('texte,attendu', [('demain',date(2026,9,6)),('après-demain',date(2026,9,7)),('aujourd’hui',date(2026,9,5)),('mardi',date(2026,9,8)),('samedi',date(2026,9,12)),('dans 15 jours',date(2026,9,20)),('dans 1 jour',date(2026,9,6)),('03/10',date(2026,10,3)),('3 octobre',date(2026,10,3)),('29/02',date(2028,2,29))])
def test_dates(texte, attendu):
    r=preparer_rendez_vous(f'CAF {texte} à 10h')
    assert r['etat'] == 'confirmation'
    assert r['rendez_vous']['date'] == attendu
    assert r['rendez_vous']['titre'] == 'CAF'

@pytest.mark.parametrize('texte', ['31/02/2026','00/09','12/13','29 février 2027'])
def test_dates_invalides(texte):
    assert preparer_rendez_vous(f'Dentiste {texte} 10h')['etat'] == 'erreur'

@pytest.mark.parametrize('phrase', ['Dentiste mardi 14h30 à Lorient','Dentiste à Lorient mardi à 14h30','À 14h30 mardi Dentiste à Lorient'])
def test_lieu_et_ordre(phrase):
    r=preparer_rendez_vous(phrase)
    assert r['etat'] == 'confirmation'
    assert r['rendez_vous']['lieu'] == 'Lorient'
    assert r['rendez_vous']['titre'] == 'Dentiste'
    assert 'Lieu : Lorient' in r['message']


def test_manquants_et_incoherence():
    assert preparer_rendez_vous(' ')['etat'] == 'vide'
    assert preparer_rendez_vous('Dentiste mardi')['etat'] == 'incomplet'
    assert preparer_rendez_vous('demain 10h')['etat'] == 'incomplet'
    assert preparer_rendez_vous('Dentiste lundi 08/09/2026 10h')['etat'] == 'erreur'
