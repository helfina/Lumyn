from concurrent.futures import ThreadPoolExecutor
import threading

from lumyn.modules.lieux import stockage as lieux
from lumyn.modules.rendez_vous import reprise_google, stockage


def executer_deux(appel_a, appel_b):
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(appel_a)
        b = pool.submit(appel_b)
        return a.result(timeout=5), b.result(timeout=5)


def test_deux_ajouts_rendez_vous_ne_secrasent_pas():
    executer_deux(
        lambda: stockage.enregistrer_rendez_vous({"titre": "A"}),
        lambda: stockage.enregistrer_rendez_vous({"titre": "B"}),
    )
    assert {r["titre"] for r in stockage.charger_rendez_vous()} == {"A", "B"}


def test_deux_ajouts_carnet_ne_secrasent_pas():
    executer_deux(
        lambda: lieux.enregistrer_lieu({"nom": "A"}),
        lambda: lieux.enregistrer_lieu({"nom": "B"}),
    )
    assert {r["nom"] for r in lieux.charger_lieux()} == {"A", "B"}


def test_deux_reservations_google_independantes_survivent():
    ids = executer_deux(
        lambda: reprise_google.reserver_creation("famille", {"summary": "A"}),
        lambda: reprise_google.reserver_creation("travail", {"summary": "B"}),
    )
    journal = reprise_google._charger()
    assert {v["id"] for v in journal.values()} == set(ids)


def test_resolution_et_ajout_journal_concurrents_preservent_nouvelle_entree():
    ancien = reprise_google.reserver_creation("famille", {"summary": "ancien"})
    _, nouveau = executer_deux(
        lambda: reprise_google.terminer_creation("famille", ancien),
        lambda: reprise_google.reserver_creation("travail", {"summary": "nouveau"}),
    )
    assert [v["id"] for v in reprise_google._charger().values()] == [nouveau]
