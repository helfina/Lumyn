import asyncio
from unittest.mock import Mock

import toga

from lumyn.modules.synapse.autocompletion_ui import AutocompletionAdresseUI
from lumyn.modules.synapse.recherche_lieux import PropositionLieu

P = PropositionLieu("Cabinet", "1 rue A, 56000 Vannes, France", "Geoapify / OpenStreetMap", ville="Vannes", conservation_autorisee=False)
Q = PropositionLieu("Hôpital", "2 rue B, 56000 Vannes, France", "Geoapify / OpenStreetMap", ville="Vannes", conservation_autorisee=False)


def construire(fournisseur, delai=0.01):
    toga.App("Test autocomplete", "fr.helfina.lumyn.tests.autocomplete")
    champ=toga.TextInput()
    return champ, AutocompletionAdresseUI(champ,fournisseur,delai=delai)


def test_minimum_debounce_et_choix_explicite():
    async def scenario():
        fournisseur=Mock(autocompleter=Mock(return_value=[P,Q]))
        champ, aide=construire(fournisseur)
        champ.value="1 r"
        aide.planifier()
        assert aide.tache is None
        champ.value="1 rue"
        aide.planifier()
        premiere=aide.tache
        champ.value="1 rue A"
        aide.planifier()
        await asyncio.gather(premiere,aide.tache,return_exceptions=True)
        fournisseur.autocompleter.assert_called_once_with("1 rue A")
        assert champ.value=="1 rue A" and len(aide.propositions)==2
        aide.choisir(Q)
        assert champ.value==Q.adresse and not aide.propositions
    asyncio.run(scenario())


def test_reponse_perimee_ignoree_et_saisie_manuelle_conservee():
    async def scenario():
        fournisseur=Mock(autocompleter=Mock(return_value=[P]))
        champ,aide=construire(fournisseur,delai=0)
        import time
        def chercher(texte):
            if texte == "Cabinet Vannes":
                time.sleep(0.04)
                return [P]
            return [Q]
        fournisseur.autocompleter.side_effect = chercher
        champ.value="Cabinet Vannes"
        await asyncio.sleep(0.01)
        premiere = aide.tache
        champ.value="Texte corrigé manuellement"
        seconde = aide.tache
        await seconde
        await asyncio.sleep(0.05)
        assert aide.propositions==[Q]
        assert champ.value=="Texte corrigé manuellement"
        assert premiere.done()
    asyncio.run(scenario())


def test_timeout_ne_bloque_pas_la_saisie():
    async def scenario():
        fournisseur=Mock(autocompleter=Mock(side_effect=TimeoutError("Délai")))
        champ,aide=construire(fournisseur,delai=0)
        champ.value="Adresse assez longue"
        aide.planifier()
        await aide.tache
        assert "Délai" in aide.statut.text
        assert champ.value=="Adresse assez longue"
    asyncio.run(scenario())


def test_requete_identique_reutilise_seulement_le_dernier_resultat_en_memoire():
    async def scenario():
        fournisseur=Mock(autocompleter=Mock(return_value=[P]))
        champ,aide=construire(fournisseur,delai=0)
        champ.value="Cabinet Vannes"
        await aide.tache
        aide.planifier()
        assert aide.tache is None
        fournisseur.autocompleter.assert_called_once_with("Cabinet Vannes")
        assert aide.propositions==[P]
    asyncio.run(scenario())
