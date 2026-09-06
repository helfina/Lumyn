"""Contrat pour un futur fournisseur ; aucune API ni recherche active par défaut."""
from dataclasses import dataclass
from typing import Protocol, Sequence
from lumyn.modules.synapse.interpreteur_rendez_vous import interpreter_rendez_vous
from lumyn.modules.synapse.orchestrateur_rendez_vous import preparer_rendez_vous_synapse


@dataclass(frozen=True)
class PropositionLieu:
    nom: str
    adresse: str
    source: str
    profession: str = ""
    ville: str = ""
    identifiant: str = ""
    conservation_autorisee: bool = False


class FournisseurLieux(Protocol):
    def rechercher(self, texte: str) -> Sequence[PropositionLieu]:
        """Propose des adresses sourcées sans enregistrer de fiche personnelle."""
        ...


class FournisseurIAWeb(FournisseurLieux, Protocol):
    """Repli sourcé sur la requête minimale, sans accès au Carnet ni à Google."""


def proposition_valide(p):
    return (
        isinstance(p, PropositionLieu)
        and all(isinstance(v, str) and v.strip() for v in (p.nom, p.adresse, p.source))
        and all(isinstance(v, str) for v in (p.profession, p.ville, p.identifiant))
        and isinstance(p.conservation_autorisee, bool)
    )


def requete_minimale(texte):
    interpretation = interpreter_rendez_vous(texte)
    morceaux = []
    for cle in ('titre', 'profession', 'lieu_explicite'):
        valeur = interpretation.get(cle)
        if valeur and valeur.casefold() not in ' '.join(morceaux).casefold():
            morceaux.append(valeur)
    return ' '.join(morceaux)


def proposer_recherche_externe(texte, fournisseur=None, *, autoriser=False, lieux=None,
                               fournisseur_ia=None, autoriser_ia=False):
    """Carnet d'abord, puis structuré, puis IA autorisée si aucun résultat valable.

    Fournisseurs concrets non configurés par défaut. Leur adaptateur doit borner
    les délais réseau. Une erreur n'écrit rien et laisse la saisie locale disponible.
    """
    resultat = preparer_rendez_vous_synapse(texte, lieux)
    rdv = resultat.get('rendez_vous') or {}
    if (not autoriser or fournisseur is None
        or rdv.get('lieu_source') in ('carnet', 'maison')
        or rdv.get('mode') in ('visio', 'domicile', 'telephone')
        or resultat['etat'] not in ('confirmation', 'incomplet')
        or any(not rdv.get(c) for c in ('titre','date','heure'))):
        return resultat
    requete = requete_minimale(texte)
    if not requete:
        return resultat
    fournisseurs = [('structure', fournisseur)]
    if autoriser_ia and fournisseur_ia is not None:
        fournisseurs.append(('ia_web', fournisseur_ia))
    problemes = []
    propositions = []
    for origine, moteur in fournisseurs:
        try:
            propositions = list(moteur.rechercher(requete))
            if not all(proposition_valide(p) for p in propositions):
                raise ValueError('Propositions invalides ou non sourcées')
        except (OSError, ValueError) as erreur:
            problemes.append(type(erreur).__name__)
            propositions = []
        if propositions:
            resultat['fournisseur_utilise'] = origine
            break
    resultat['propositions_externes'] = list(dict.fromkeys(propositions))
    resultat['requete_externe'] = requete
    resultat['problemes_recherche'] = problemes
    if propositions:
        resultat['etat'] = 'ambigu'
        resultat['message'] = 'Choisis et vérifie une adresse proposée avant de confirmer.'
    else:
        resultat['etat'] = 'incomplet'
        resultat['message'] = ('Recherche indisponible ou sans résultat fiable. '
                               'Tu peux préciser le lieu manuellement et analyser à nouveau.')
    return resultat
