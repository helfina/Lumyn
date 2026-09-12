from unittest.mock import Mock
import toga
from lumyn.modules.lieux.ui import InterfaceLieux
from lumyn.modules.rendez_vous import calendrier_ui, ui


def test_geoapify_injecte_les_deux_parcours_sans_ia(monkeypatch,tmp_path):
    toga.App("Activation Geoapify", "fr.helfina.lumyn.tests.activation")
    fournisseur=Mock()
    calendriers=[{'id':'famille','nom':'Famille','access_role':'owner','principal':True}]
    monkeypatch.setattr(ui,'lister_calendriers_google',lambda:calendriers)
    monkeypatch.setattr(calendrier_ui,'lister_calendriers_google',lambda:calendriers)
    monkeypatch.setattr(calendrier_ui,'lister_evenements_google_simples',lambda *a:[])
    rendez_vous=ui.InterfaceRendezVous(fournisseur)
    rendez_vous.construire()
    carnet=InterfaceLieux(fournisseur)
    carnet.construire()
    assert rendez_vous.recherche_lieux_ui.fournisseur is fournisseur
    assert rendez_vous.recherche_lieux_ui.fournisseur_ia is None
    assert carnet.autocompletion_adresse.fournisseur is fournisseur
