"""Autocomplétion d'adresse Toga, déclenchée après une pause de saisie."""

import asyncio
import toga
from toga.style.pack import COLUMN, Pack


class AutocompletionAdresseUI:
    def __init__(self, champ, fournisseur, *, delai=0.65, minimum=4):
        self.champ = champ
        self.fournisseur = fournisseur
        self.delai = delai
        self.minimum = minimum
        self.generation = 0
        self.tache = None
        self.propositions = []
        self.dernier_texte = None
        self.dernieres_propositions = []
        self.resultats = toga.Box(style=Pack(direction=COLUMN, gap=4))
        self.statut = toga.Label('')
        self.zone = toga.Box(style=Pack(direction=COLUMN, gap=4))
        self.zone.add(self.statut, self.resultats)
        self.champ.on_change = self.planifier

    def planifier(self, widget=None, **kwargs):
        self.generation += 1
        generation = self.generation
        if self.tache and not self.tache.done():
            self.tache.cancel()
        self.propositions = []
        self.resultats.clear()
        texte = str(self.champ.value or '').strip()
        if len(texte) < self.minimum:
            self.statut.text = ''
            self.tache = None
            return
        if texte == self.dernier_texte:
            self._afficher(self.dernieres_propositions)
            self.tache = None
            return
        self.statut.text = 'Suggestions après une courte pause…'
        try:
            self.tache = asyncio.create_task(self._rechercher(generation, texte))
        except RuntimeError:
            self.tache = None
            self.statut.text = 'Autocomplétion disponible lorsque l’application est lancée.'

    async def _rechercher(self, generation, texte):
        try:
            await asyncio.sleep(self.delai)
            propositions = await asyncio.to_thread(self.fournisseur.autocompleter, texte)
        except asyncio.CancelledError:
            return
        except (OSError, ValueError, TimeoutError) as erreur:
            if generation == self.generation:
                self.statut.text = str(erreur) or 'Suggestions indisponibles. Continue la saisie manuelle.'
            return
        if generation != self.generation or texte != str(self.champ.value or '').strip():
            return
        self.dernier_texte = texte
        self.dernieres_propositions = list(propositions)[:5]
        self._afficher(self.dernieres_propositions)

    def _afficher(self, propositions):
        self.propositions = list(propositions)[:5]
        self.resultats.clear()
        if not self.propositions:
            self.statut.text = 'Aucune suggestion. Continue la saisie manuelle.'
            return
        self.statut.text = 'Choisis une suggestion, ou continue la saisie manuelle.'
        for proposition in self.propositions:
            self.resultats.add(toga.Label(
                f'{proposition.adresse}\\n{proposition.ville} — Source : {proposition.source}'
            ))
            self.resultats.add(toga.Button(
                'Utiliser cette adresse',
                on_press=lambda widget, p=proposition, **kw: self.choisir(p),
            ))

    def choisir(self, proposition):
        if proposition not in self.propositions:
            raise ValueError('Suggestion périmée ; relance la recherche.')
        self.generation += 1
        self.propositions = []
        self.resultats.clear()
        self.champ.value = proposition.adresse
        self.statut.text = f'Adresse proposée par {proposition.source}. Vérifie-la avant enregistrement.'
