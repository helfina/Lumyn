from datetime import date, datetime

import pytest

from lumyn.modules.rendez_vous import agenda_google, analyseur, stockage


@pytest.mark.parametrize("expression,reference,attendu", [
    ("aujourd'hui", date(2026, 12, 31), date(2026, 12, 31)),
    ("demain", date(2026, 12, 31), date(2027, 1, 1)),
    ("demain", date(2027, 1, 31), date(2027, 2, 1)),
    ("demain", date(2028, 2, 28), date(2028, 2, 29)),
    ("demain", date(2027, 2, 28), date(2027, 3, 1)),
    ("lundi", date(2026, 9, 7), date(2026, 9, 14)),
    ("lundi prochain", date(2026, 9, 6), date(2026, 9, 7)),
    ("mardi", date(2026, 9, 6), date(2026, 9, 8)),
])
def test_dates_relatives_utilisent_reference_injectee(expression, reference, attendu):
    rdv = analyseur.analyser_rendez_vous(
        f"Dentiste {expression} 10h", date_reference=reference)
    assert rdv["date"] == attendu


@pytest.mark.parametrize("heure,normalisee", [
    ("00h00", "00h"), ("23h59", "23h59"),
    ("10h30", "10h30"), ("10 h 30", "10h30"),
])
def test_heures_extremes_et_formats_ne_changent_pas(heure, normalisee):
    rdv = analyseur.analyser_rendez_vous(
        f"Dentiste 31/12/2026 {heure}", date_reference=date(2026, 1, 1))
    assert rdv["date"] == date(2026, 12, 31)
    assert rdv["heure"] == normalisee


def test_google_franchit_minuit_sans_decaler_le_debut():
    corps = agenda_google.construire_corps_evenement_google({
        "titre": "Réveillon", "date": "2026-12-31", "heure": "23h59"})
    assert corps["start"]["dateTime"] == "2026-12-31T23:59:00+01:00"
    assert corps["end"]["dateTime"] == "2027-01-01T00:59:00+01:00"


def test_passage_heure_ete_conserve_une_heure_reelle():
    corps = agenda_google.construire_corps_evenement_google({
        "titre": "Avant DST", "date": "2026-03-29", "heure": "01h30"})
    assert corps["start"]["dateTime"] == "2026-03-29T01:30:00+01:00"
    assert corps["end"]["dateTime"] == "2026-03-29T03:30:00+02:00"
    debut = datetime.fromisoformat(corps["start"]["dateTime"])
    fin = datetime.fromisoformat(corps["end"]["dateTime"])
    assert fin.timestamp() - debut.timestamp() == 3600


def test_heure_inexistante_est_refusee_explicitement():
    with pytest.raises(ValueError, match="n'existe pas en Europe/Paris"):
        agenda_google.construire_corps_evenement_google({
            "titre": "DST", "date": "2026-03-29", "heure": "02h30"})


def test_heure_hiver_ambigue_garde_choix_historique_et_duree_reelle():
    corps = agenda_google.construire_corps_evenement_google({
        "titre": "DST", "date": "2026-10-25", "heure": "02h30"})
    assert corps["start"]["dateTime"] == "2026-10-25T02:30:00+02:00"
    assert corps["end"]["dateTime"] == "2026-10-25T02:30:00+01:00"
    debut = datetime.fromisoformat(corps["start"]["dateTime"])
    fin = datetime.fromisoformat(corps["end"]["dateTime"])
    assert fin.timestamp() - debut.timestamp() == 3600


def test_json_redemarrage_preserve_date_heure_unicode_et_lieu():
    original = stockage.enregistrer_rendez_vous({
        "titre": "Élodie — consultation d'été",
        "date": date(2028, 2, 29), "heure": "00h",
        "lieu": "12 rue de l'Église, Guémené-sur-Scorff",
    })
    relu = stockage.charger_rendez_vous()[0]
    assert relu == original
    corps = agenda_google.construire_corps_evenement_google(relu)
    assert corps["start"]["dateTime"] == "2028-02-29T00:00:00+01:00"
    assert corps["summary"] == original["titre"]
    assert corps["location"] == original["lieu"]
