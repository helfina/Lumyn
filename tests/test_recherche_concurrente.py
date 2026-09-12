import asyncio
import threading
from unittest.mock import Mock

import pytest

from lumyn.modules.synapse.recherche_lieux import PropositionLieu
from lumyn.modules.synapse.recherche_ui import RechercheLieuxUI
from tests.test_ui import interface


PHRASE_A = "rendez-vous avec dentiste Martin mardi 10h au cabinet de Vannes"
PHRASE_B = "rendez-vous avec dentiste Dupont mercredi 11h au cabinet de Lorient"


def proposition(nom, ville):
    return PropositionLieu(
        nom, f"2 rue Exemple, 56000 {ville}", "FINESS simulé",
        "dentiste", ville, conservation_autorisee=True,
    )


class FournisseurControle:
    def __init__(self, resultats=None, erreurs=None):
        self.departs = {nom: threading.Event() for nom in ("Martin", "Dupont")}
        self.fins = {nom: threading.Event() for nom in ("Martin", "Dupont")}
        self.resultats = resultats or {}
        self.erreurs = erreurs or {}

    def rechercher(self, requete):
        nom = "Martin" if "Martin" in requete else "Dupont"
        self.departs[nom].set()
        assert self.fins[nom].wait(5), "Le test n'a pas libéré le fournisseur"
        if nom in self.erreurs:
            raise self.erreurs[nom]
        return self.resultats.get(nom, [])


async def attendre(event):
    assert await asyncio.to_thread(event.wait, 5)


def test_b_termine_avant_a_et_a_est_totalement_ignoree(interface):
    async def scenario():
        fournisseur = FournisseurControle({
            "Martin": [proposition("Cabinet Martin", "Vannes")],
            "Dupont": [proposition("Cabinet Dupont", "Lorient")],
        })
        panneau = RechercheLieuxUI(interface, fournisseur)
        interface.rdv_input.value = PHRASE_A
        a = asyncio.create_task(panneau.rechercher())
        await attendre(fournisseur.departs["Martin"])
        interface.rdv_input.value = PHRASE_B
        b = asyncio.create_task(panneau.rechercher())
        await attendre(fournisseur.departs["Dupont"])
        fournisseur.fins["Dupont"].set()
        await b
        etat_b = (list(panneau.propositions), panneau.statut.text,
                  panneau.rechercher_button.enabled)
        fournisseur.fins["Martin"].set()
        await a
        assert (panneau.propositions, panneau.statut.text,
                panneau.rechercher_button.enabled) == etat_b
        assert panneau.propositions[0].nom == "Cabinet Dupont"
        assert not interface.confirmer_button.enabled
    asyncio.run(scenario())


@pytest.mark.parametrize("erreur_a,erreur_b", [
    (OSError("A échoue"), None),
    (None, OSError("B échoue")),
])
def test_reponses_desordonnees_succes_et_echec_gardent_seulement_b(
        interface, erreur_a, erreur_b):
    async def scenario():
        erreurs = {k: v for k, v in (("Martin", erreur_a), ("Dupont", erreur_b)) if v}
        fournisseur = FournisseurControle({
            "Martin": [proposition("Cabinet Martin", "Vannes")],
            "Dupont": [proposition("Cabinet Dupont", "Lorient")],
        }, erreurs)
        panneau = RechercheLieuxUI(interface, fournisseur)
        interface.rdv_input.value = PHRASE_A
        a = asyncio.create_task(panneau.rechercher())
        await attendre(fournisseur.departs["Martin"])
        interface.rdv_input.value = PHRASE_B
        b = asyncio.create_task(panneau.rechercher())
        await attendre(fournisseur.departs["Dupont"])
        fournisseur.fins["Dupont"].set()
        await b
        attendu = list(panneau.propositions)
        fournisseur.fins["Martin"].set()
        await a
        assert panneau.propositions == attendu
        assert all("Martin" not in p.nom for p in panneau.propositions)
        assert panneau.rechercher_button.enabled
        assert not interface.confirmer_button.enabled
    asyncio.run(scenario())


def test_consentement_web_est_fige_pour_la_recherche_lancee(interface):
    async def scenario():
        public = FournisseurControle({"Martin": []})
        web = Mock(rechercher=Mock(return_value=[proposition("Martin", "Vannes")]))
        panneau = RechercheLieuxUI(interface, public, fournisseur_ia=web)
        interface.rdv_input.value = PHRASE_A
        panneau.ia_switch.value = False
        tache = asyncio.create_task(panneau.rechercher())
        await attendre(public.departs["Martin"])
        panneau.ia_switch.value = True
        public.fins["Martin"].set()
        await tache
        web.rechercher.assert_not_called()
    asyncio.run(scenario())


def test_annulation_logique_ignore_le_thread_tardif(interface):
    async def scenario():
        fournisseur = FournisseurControle({
            "Martin": [proposition("Cabinet Martin", "Vannes")],
        })
        panneau = RechercheLieuxUI(interface, fournisseur)
        interface.rdv_input.value = PHRASE_A
        tache = asyncio.create_task(panneau.rechercher())
        await attendre(fournisseur.departs["Martin"])
        tache.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tache
        assert panneau.rechercher_button.enabled
        assert not interface.confirmer_button.enabled
        fournisseur.fins["Martin"].set()
        await asyncio.to_thread(fournisseur.fins["Martin"].wait)
        assert panneau.propositions == []
    asyncio.run(scenario())


def test_invalidation_pendant_recherche_interdit_reponse_et_enregistrement(interface):
    async def scenario():
        fournisseur = FournisseurControle({
            "Martin": [proposition("Cabinet Martin", "Vannes")],
        })
        panneau = RechercheLieuxUI(interface, fournisseur)
        interface.rdv_input.value = PHRASE_A
        tache = asyncio.create_task(panneau.rechercher())
        await attendre(fournisseur.departs["Martin"])
        panneau.invalider()
        fournisseur.fins["Martin"].set()
        await tache
        assert panneau.propositions == []
        assert panneau.selection is None
        assert not panneau.enregistrer_button.enabled
        assert not interface.confirmer_button.enabled
    asyncio.run(scenario())
