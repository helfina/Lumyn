"""Parcours de propositions optionnel ; aucun fournisseur concret par défaut."""
import asyncio

import toga
from toga.style.pack import COLUMN, Pack
from lumyn.modules.synapse.recherche_lieux import proposer_recherche_externe
from lumyn.modules.synapse.selection_lieux import choisir_proposition, enregistrer_proposition


class RechercheLieuxUI:
    def __init__(self, formulaire, fournisseur, fournisseur_ia=None,
                 interpreteur_local=None):
        self.formulaire = formulaire
        self.fournisseur = fournisseur
        self.fournisseur_ia = fournisseur_ia
        self.interpreteur_local = interpreteur_local
        self.propositions = []
        self.selection = None
        self.instantane = None
        self.resultat_recherche = None
        self._requete = 0
        self._recherche_en_cours = False
        self.zone = toga.Box(style=Pack(direction=COLUMN, gap=6))
        self.resultats = toga.Box(style=Pack(direction=COLUMN, gap=6))
        self.statut = toga.Label('')
        self.rechercher_button = toga.Button('Rechercher une adresse', on_press=self.rechercher)
        self.ia_switch = toga.Switch('Autoriser le complément IA/web pour cette recherche', value=False)
        self.enregistrer_button = toga.Button('Enregistrer ce lieu dans le Carnet pour les prochains rendez-vous',
                                             on_press=self.enregistrer, enabled=False)
        self.zone.add(self.rechercher_button)
        if fournisseur_ia is not None:
            self.zone.add(self.ia_switch)
        self.zone.add(self.statut, self.resultats, self.enregistrer_button)

    def _saisie(self):
        f = self.formulaire
        return f.rdv_input.value, f._calendrier_selectionne()[0]

    def invalider(self):
        self._requete += 1
        self._recherche_en_cours = False
        self.rechercher_button.enabled = True
        self.selection = None
        self.instantane = None
        self.resultat_recherche = None
        self.propositions = []
        self.enregistrer_button.enabled = False
        self.resultats.clear()
        self.statut.text = ''

    async def rechercher(self, widget=None, **kwargs):
        """Exécute le fournisseur hors du thread UI et rejette toute réponse périmée."""
        self.invalider()
        self._requete += 1
        requete = self._requete
        f = self.formulaire
        f.resultat_courant = None
        f.saisie_analysee = None
        f.confirmer_button.enabled = False
        self.instantane = self._saisie()
        self._recherche_en_cours = True
        self.rechercher_button.enabled = False
        self.statut.text = 'Recherche locale et publique en cours…'
        try:
            resultat = await asyncio.to_thread(
                proposer_recherche_externe,
                self.instantane[0],
                self.fournisseur,
                autoriser=True,
                fournisseur_ia=self.fournisseur_ia,
                autoriser_ia=self.ia_switch.value,
                interpreteur_local=self.interpreteur_local,
            )
        except (OSError, ValueError, TimeoutError) as erreur:
            if requete == self._requete:
                self.statut.text = str(erreur) or (
                    'Recherche indisponible. La saisie manuelle reste disponible.'
                )
            return
        finally:
            if requete == self._requete:
                self._recherche_en_cours = False
                self.rechercher_button.enabled = True
        if requete != self._requete or self.instantane != self._saisie():
            return
        self.propositions = resultat.get('propositions_externes', [])
        self.resultat_recherche = resultat
        self.statut.text = resultat['message']
        if not self.propositions:
            f.resultat_courant = resultat
            f.resultat_label.text = resultat['message']
            f.saisie_analysee = self.instantane
            f.confirmer_button.enabled = resultat['etat'] == 'confirmation'
            return
        for proposition in self.propositions:
            self.resultats.add(toga.Label(
                f'{proposition.nom} — {proposition.profession}\n{proposition.adresse}\n'
                f'{proposition.ville}\nSource : {proposition.source}\n'
                + ('Adresse vérifiée par BAN' if proposition.adresse_verifiee
                   else 'Adresse non vérifiée par BAN')))
            self.resultats.add(toga.Button('Choisir cette adresse',
                on_press=lambda widget, p=proposition, **kw: self.choisir(p)))

    def choisir(self, proposition):
        if self.instantane != self._saisie():
            self.invalider()
            self.statut.text = 'La saisie ou le calendrier a changé. Relance la recherche.'
            return
        f = self.formulaire
        f.resultat_courant = None
        f.saisie_analysee = None
        f.confirmer_button.enabled = False
        try:
            resultat = choisir_proposition(
                self.instantane[0], proposition, self.propositions,
                resultat_prepare=self.resultat_recherche)
        except (ValueError, OSError) as erreur:
            self.statut.text = str(erreur)
            return
        f.resultat_courant = resultat
        f.resultat_label.text = resultat['message']
        f.saisie_analysee = self.instantane
        f.confirmer_button.enabled = resultat['etat'] == 'confirmation'
        self.selection = proposition if resultat.get('rendez_vous', {}).get('lieu_source') == 'externe' else None
        self.enregistrer_button.enabled = bool(
            self.selection is not None and self.selection.conservation_autorisee
        )
        self.statut.text = 'Adresse sélectionnée. Relis le résumé puis confirme le rendez-vous.'
        if self.selection is not None and not self.selection.conservation_autorisee:
            self.statut.text += (' Cette proposition externe ne peut pas être '
                                 'enregistrée automatiquement dans le Carnet.')

    def enregistrer(self, widget=None, *, fiche_id=None, **kwargs):
        if self.selection is None or self.instantane != self._saisie():
            self.invalider()
            self.statut.text = 'Choisis une adresse de la saisie actuelle avant de l’enregistrer.'
            return
        try:
            resultat = enregistrer_proposition(self.selection, autoriser=True, fiche_id=fiche_id)
        except (ValueError, OSError) as erreur:
            self.statut.text = str(erreur)
            return
        if resultat['etat'] == 'choix_fiche':
            self.statut.text = 'Une fiche similaire existe. Choisis celle à compléter ; aucune fiche ajoutée.'
            self.resultats.clear()
            for fiche in resultat['fiches']:
                self.resultats.add(toga.Button('Compléter ' + fiche['nom'],
                    on_press=lambda widget, identifiant=fiche['id'], **kw:
                        self.enregistrer(fiche_id=identifiant)))
        else:
            self.statut.text = 'Lieu enregistré dans le Carnet pour les prochains rendez-vous.'
            self.enregistrer_button.enabled = False
