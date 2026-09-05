"""Contrat pour un futur fournisseur ; aucune API ni recherche active par défaut."""
from dataclasses import dataclass
from typing import Protocol, Sequence
from lumyn.modules.synapse.orchestrateur_rendez_vous import preparer_rendez_vous_synapse


@dataclass(frozen=True)
class PropositionLieu:
    nom: str
    adresse: str
    source: str


class FournisseurLieux(Protocol):
    def rechercher(self, texte: str) -> Sequence[PropositionLieu]:
        """Propose des adresses sourcées sans enregistrer de fiche personnelle."""
        ...


def proposer_recherche_externe(texte, fournisseur=None, *, autoriser=False, lieux=None):
    """Résout localement d'abord ; les propositions externes exigent un choix.

    Point d'extension non branché sur l'UI. Aucun fournisseur concret n'est livré.
    Même une unique proposition ne modifie jamais le rendez-vous ou le carnet.
    """
    resultat = preparer_rendez_vous_synapse(texte, lieux)
    rdv = resultat.get('rendez_vous') or {}
    if (
        not autoriser or fournisseur is None
        or rdv.get('lieu_source') in ('carnet', 'maison')
        or rdv.get('lieu_id')
        or rdv.get('mode') in ('visio', 'domicile', 'telephone')
        or resultat['etat'] != 'confirmation'
    ):
        return resultat
    try:
        propositions = list(fournisseur.rechercher(texte))
        if not all(isinstance(p, PropositionLieu) and all(
            isinstance(v, str) and v.strip() for v in (p.nom, p.adresse, p.source)
        ) for p in propositions):
            raise ValueError('Propositions de lieux invalides ou non sourcées.')
    except (OSError, ValueError) as erreur:
        resultat['etat'] = 'incomplet'
        resultat['message'] = f'Recherche indisponible : {erreur}. Précise le lieu.'
        return resultat
    resultat['propositions_externes'] = propositions
    if propositions:
        resultat['etat'] = 'ambigu'
        resultat['message'] = 'Choisis et vérifie une adresse proposée avant de confirmer.'
    else:
        resultat['etat'] = 'incomplet'
        resultat['message'] = 'Aucune adresse fiable proposée. Précise le lieu.'
    return resultat
