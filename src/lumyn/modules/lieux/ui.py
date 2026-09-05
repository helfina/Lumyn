"""Interface du carnet de lieux de Lumyn."""

import toga

from toga.style.pack import COLUMN, ROW, Pack

from lumyn.modules.lieux.modele import creer_modele_lieu
from lumyn.modules.lieux.stockage import (
    charger_lieux,
    enregistrer_lieu,
    modifier_lieu,
    supprimer_lieu,
)


def _copier_adresses(adresses):
    """Crée une copie indépendante d'une liste d'adresses."""

    return [
        dict(adresse)
        for adresse in (adresses or [])
        if isinstance(adresse, dict)
    ]


def _extraire_alias(texte):
    """Transforme une saisie séparée par des virgules en liste d'alias."""

    alias = []

    for valeur in str(texte or "").split(","):
        valeur = valeur.strip()

        if valeur and valeur not in alias:
            alias.append(valeur)

    return alias


class InterfaceLieux:
    """Contrôleur de l'interface du carnet de lieux."""

    def __init__(self):
        self.main_box = None

        self.nom_input = None
        self.categorie_input = None
        self.profession_input = None
        self.alias_input = None
        self.visio_switch = None
        self.notes_input = None

        self.libelle_adresse_input = None
        self.adresse_input = None
        self.favorite_switch = None
        self.ajouter_adresse_button = None
        self.liste_adresses = None

        self.statut_label = None
        self.enregistrer_button = None
        self.annuler_button = None

        self.liste_lieux = None
        self.titre_liste = None

        self.lieu_en_modification_id = None
        self.adresse_en_modification_index = None
        self.adresses_en_cours = []

    def construire(self):
        """Construit et renvoie l'interface complète."""

        self.main_box = toga.Box(
            style=Pack(
                direction=COLUMN,
                margin=20,
                gap=15,
            )
        )

        self._construire_entete()
        self._construire_formulaire()
        self._construire_liste()

        self.actualiser_liste_adresses()
        self.actualiser_liste_lieux()

        return toga.ScrollContainer(
            content=self.main_box,
            horizontal=False,
            vertical=True,
            style=Pack(
                flex=1,
            ),
        )

    # =========================================================
    # EN-TÊTE
    # =========================================================

    def _construire_entete(self):
        """Construit le titre du carnet."""

        entete = toga.Box(
            style=Pack(
                direction=COLUMN,
                gap=4,
            )
        )

        titre = toga.Label(
            "Carnet de lieux",
            style=Pack(
                font_size=22,
                font_weight="bold",
            ),
        )

        description = toga.Label(
            (
                "Enregistre les lieux que Lumyn doit utiliser en priorité "
                "pour tes rendez-vous."
            ),
            style=Pack(
                color="#6c757d",
            ),
        )

        entete.add(
            titre,
            description,
        )

        self.main_box.add(entete)

    # =========================================================
    # FORMULAIRE DE FICHE
    # =========================================================

    def _construire_formulaire(self):
        """Construit le formulaire de création et modification."""

        carte = toga.Box(
            style=Pack(
                direction=COLUMN,
                gap=8,
                background_color="#f8f9fa",
                margin_bottom=5,
            )
        )

        titre = toga.Label(
            "Ajouter un lieu",
            style=Pack(
                font_size=16,
                font_weight="bold",
                margin_top=12,
                margin_left=12,
                margin_right=12,
            ),
        )

        self.nom_input = toga.TextInput(
            placeholder="Nom : ITEP Vannes, Maison, Dr Laporte...",
            style=Pack(
                margin_left=12,
                margin_right=12,
            ),
        )

        self.categorie_input = toga.TextInput(
            placeholder="Catégorie : établissement, professionnel, domicile...",
            style=Pack(
                margin_left=12,
                margin_right=12,
            ),
        )

        self.profession_input = toga.TextInput(
            placeholder="Profession éventuelle : psychiatre, dentiste...",
            style=Pack(
                margin_left=12,
                margin_right=12,
            ),
        )

        self.alias_input = toga.TextInput(
            placeholder="Alias séparés par des virgules : ITEP, institut Vannes",
            style=Pack(
                margin_left=12,
                margin_right=12,
            ),
        )

        self.visio_switch = toga.Switch(
            "Visio possible",
            value=False,
            style=Pack(
                margin_left=12,
                margin_right=12,
            ),
        )

        self.notes_input = toga.TextInput(
            placeholder="Notes éventuelles",
            style=Pack(
                margin_left=12,
                margin_right=12,
            ),
        )

        carte.add(
            titre,
            self.nom_input,
            self.categorie_input,
            self.profession_input,
            self.alias_input,
            self.visio_switch,
            self.notes_input,
        )

        self._construire_formulaire_adresses(carte)

        self.statut_label = toga.Label(
            "",
            style=Pack(
                margin_left=12,
                margin_right=12,
            ),
        )

        actions = toga.Box(
            style=Pack(
                direction=ROW,
                gap=6,
                margin_left=12,
                margin_right=12,
                margin_bottom=12,
            )
        )

        self.annuler_button = toga.Button(
            "Annuler",
            on_press=self.annuler_modification,
            enabled=False,
            style=Pack(
                flex=1,
            ),
        )

        self.enregistrer_button = toga.Button(
            "Enregistrer la fiche",
            on_press=self.enregistrer_fiche,
            style=Pack(
                flex=1,
            ),
        )

        actions.add(
            self.annuler_button,
            self.enregistrer_button,
        )

        carte.add(
            self.statut_label,
            actions,
        )

        self.main_box.add(carte)

    # =========================================================
    # ADRESSES DE LA FICHE
    # =========================================================

    def _construire_formulaire_adresses(self, carte):
        """Construit la zone permettant de gérer plusieurs adresses."""

        titre = toga.Label(
            "Adresses",
            style=Pack(
                font_weight="bold",
                margin_top=8,
                margin_left=12,
                margin_right=12,
            ),
        )

        aide = toga.Label(
            (
                "Une fiche peut avoir plusieurs adresses. "
                "L'adresse favorite sera utilisée par défaut."
            ),
            style=Pack(
                color="#6c757d",
                margin_left=12,
                margin_right=12,
            ),
        )

        self.libelle_adresse_input = toga.TextInput(
            placeholder="Libellé : Rendez-vous, Administration, Cabinet...",
            style=Pack(
                margin_left=12,
                margin_right=12,
            ),
        )

        self.adresse_input = toga.TextInput(
            placeholder="Adresse complète",
            style=Pack(
                margin_left=12,
                margin_right=12,
            ),
        )

        self.favorite_switch = toga.Switch(
            "Adresse favorite",
            value=False,
            style=Pack(
                margin_left=12,
                margin_right=12,
            ),
        )

        self.ajouter_adresse_button = toga.Button(
            "Ajouter l'adresse",
            on_press=self.enregistrer_adresse,
            style=Pack(
                margin_left=12,
                margin_right=12,
            ),
        )

        self.liste_adresses = toga.Box(
            style=Pack(
                direction=COLUMN,
                gap=6,
                margin_left=12,
                margin_right=12,
                margin_bottom=4,
            )
        )

        carte.add(
            titre,
            aide,
            self.libelle_adresse_input,
            self.adresse_input,
            self.favorite_switch,
            self.ajouter_adresse_button,
            self.liste_adresses,
        )

    def enregistrer_adresse(self, widget=None, **kwargs):
        """Ajoute ou modifie une adresse dans la fiche en cours."""

        adresse = str(self.adresse_input.value or "").strip()

        if not adresse:
            self.statut_label.text = (
                "Indique une adresse avant de l'ajouter."
            )
            return

        libelle = str(
            self.libelle_adresse_input.value or ""
        ).strip()

        if not libelle:
            libelle = "Adresse"

        favorite = bool(self.favorite_switch.value)

        if not self.adresses_en_cours:
            favorite = True

        if favorite:
            for adresse_existante in self.adresses_en_cours:
                adresse_existante["favorite"] = False

        nouvelle_adresse = {
            "libelle": libelle,
            "adresse": adresse,
            "favorite": favorite,
        }

        if self.adresse_en_modification_index is None:
            self.adresses_en_cours.append(nouvelle_adresse)

        else:
            self.adresses_en_cours[
                self.adresse_en_modification_index
            ] = nouvelle_adresse

        self._vider_formulaire_adresse()
        self.actualiser_liste_adresses()

        self.statut_label.text = "Adresse enregistrée dans la fiche."

    def modifier_adresse(self, index):
        """Charge une adresse dans le formulaire pour la modifier."""

        if not 0 <= index < len(self.adresses_en_cours):
            return

        adresse = self.adresses_en_cours[index]

        self.adresse_en_modification_index = index

        self.libelle_adresse_input.value = (
            adresse.get("libelle") or ""
        )
        self.adresse_input.value = (
            adresse.get("adresse") or ""
        )
        self.favorite_switch.value = bool(
            adresse.get("favorite")
        )

        self.ajouter_adresse_button.text = (
            "Enregistrer les modifications"
        )

    def supprimer_adresse(self, index):
        """Supprime une adresse de la fiche en cours."""

        if not 0 <= index < len(self.adresses_en_cours):
            return

        etait_favorite = bool(
            self.adresses_en_cours[index].get("favorite")
        )

        del self.adresses_en_cours[index]

        if etait_favorite and len(self.adresses_en_cours) == 1:
            self.adresses_en_cours[0]["favorite"] = True

        self._vider_formulaire_adresse()
        self.actualiser_liste_adresses()

        self.statut_label.text = "Adresse retirée de la fiche."

    def definir_adresse_favorite(self, index):
        """Définit une seule adresse comme favorite."""

        if not 0 <= index < len(self.adresses_en_cours):
            return

        for position, adresse in enumerate(
            self.adresses_en_cours
        ):
            adresse["favorite"] = position == index

        self.actualiser_liste_adresses()

    def _vider_formulaire_adresse(self):
        """Réinitialise les champs d'adresse."""

        self.adresse_en_modification_index = None

        self.libelle_adresse_input.value = ""
        self.adresse_input.value = ""
        self.favorite_switch.value = False

        self.ajouter_adresse_button.text = "Ajouter l'adresse"

    def actualiser_liste_adresses(self):
        """Rafraîchit les adresses visibles dans le formulaire."""

        if self.liste_adresses is None:
            return

        self.liste_adresses.clear()

        if not self.adresses_en_cours:
            self.liste_adresses.add(
                toga.Label(
                    "Aucune adresse enregistrée pour cette fiche.",
                    style=Pack(
                        color="#6c757d",
                    ),
                )
            )
            return

        for index, adresse in enumerate(
            self.adresses_en_cours
        ):
            favorite = "★ " if adresse.get("favorite") else ""

            contenu = (
                f"{favorite}{adresse.get('libelle') or 'Adresse'}\n"
                f"{adresse.get('adresse') or ''}"
            )

            carte = toga.Box(
                style=Pack(
                    direction=COLUMN,
                    gap=4,
                    background_color="#ffffff",
                    margin_bottom=4,
                )
            )

            carte.add(
                toga.Label(
                    contenu,
                    style=Pack(
                        margin=8,
                    ),
                )
            )

            actions = toga.Box(
                style=Pack(
                    direction=ROW,
                    gap=4,
                    margin_left=8,
                    margin_right=8,
                    margin_bottom=8,
                )
            )

            if not adresse.get("favorite"):
                actions.add(
                    toga.Button(
                        "Favorite",
                        on_press=(
                            lambda widget,
                            index=index,
                            **kwargs:
                            self.definir_adresse_favorite(index)
                        ),
                        style=Pack(
                            flex=1,
                        ),
                    )
                )

            actions.add(
                toga.Button(
                    "Modifier",
                    on_press=(
                        lambda widget,
                        index=index,
                        **kwargs:
                        self.modifier_adresse(index)
                    ),
                    style=Pack(
                        flex=1,
                    ),
                )
            )

            actions.add(
                toga.Button(
                    "Supprimer",
                    on_press=(
                        lambda widget,
                        index=index,
                        **kwargs:
                        self.supprimer_adresse(index)
                    ),
                    style=Pack(
                        flex=1,
                    ),
                )
            )

            carte.add(actions)
            self.liste_adresses.add(carte)

    # =========================================================
    # ENREGISTREMENT DE LA FICHE
    # =========================================================

    def enregistrer_fiche(self, widget=None, **kwargs):
        """Crée ou modifie une fiche du carnet."""

        nom = str(self.nom_input.value or "").strip()

        if not nom:
            self.statut_label.text = (
                "Indique un nom pour cette fiche."
            )
            return

        lieu = creer_modele_lieu()

        lieu["nom"] = nom
        lieu["categorie"] = (
            str(self.categorie_input.value or "").strip()
            or None
        )
        lieu["profession"] = (
            str(self.profession_input.value or "").strip()
            or None
        )
        lieu["alias"] = _extraire_alias(
            self.alias_input.value
        )
        lieu["adresses"] = _copier_adresses(
            self.adresses_en_cours
        )
        lieu["visio"] = bool(self.visio_switch.value)
        lieu["notes"] = (
            str(self.notes_input.value or "").strip()
            or None
        )

        try:
            if self.lieu_en_modification_id:
                modifier_lieu(
                    self.lieu_en_modification_id,
                    lieu,
                )
                message = f"{nom} a été modifié."

            else:
                enregistrer_lieu(lieu)
                message = f"{nom} a été ajouté au carnet."

        except (OSError, ValueError) as erreur:
            self.statut_label.text = (
                "Impossible d'enregistrer la fiche : "
                f"{erreur}"
            )
            return

        self._vider_formulaire_fiche()
        self.actualiser_liste_lieux()

        self.statut_label.text = message

    def charger_fiche(self, lieu):
        """Charge une fiche existante dans le formulaire."""

        self.lieu_en_modification_id = lieu.get("id")

        self.nom_input.value = lieu.get("nom") or ""
        self.categorie_input.value = (
            lieu.get("categorie") or ""
        )
        self.profession_input.value = (
            lieu.get("profession") or ""
        )
        self.alias_input.value = ", ".join(
            lieu.get("alias") or []
        )
        self.visio_switch.value = bool(
            lieu.get("visio")
        )
        self.notes_input.value = lieu.get("notes") or ""

        self.adresses_en_cours = _copier_adresses(
            lieu.get("adresses")
        )

        self._vider_formulaire_adresse()
        self.actualiser_liste_adresses()

        self.enregistrer_button.text = "Enregistrer les modifications"
        self.annuler_button.enabled = True

        self.statut_label.text = (
            f"Modification de {lieu.get('nom') or 'la fiche'}."
        )

    def annuler_modification(self, widget=None, **kwargs):
        """Annule la création ou modification en cours."""

        self._vider_formulaire_fiche()
        self.statut_label.text = ""

    def _vider_formulaire_fiche(self):
        """Réinitialise entièrement le formulaire."""

        self.lieu_en_modification_id = None

        self.nom_input.value = ""
        self.categorie_input.value = ""
        self.profession_input.value = ""
        self.alias_input.value = ""
        self.visio_switch.value = False
        self.notes_input.value = ""

        self.adresses_en_cours = []

        self._vider_formulaire_adresse()
        self.actualiser_liste_adresses()

        self.enregistrer_button.text = "Enregistrer la fiche"
        self.annuler_button.enabled = False

    # =========================================================
    # LISTE DU CARNET
    # =========================================================

    def _construire_liste(self):
        """Construit la liste des fiches enregistrées."""

        section = toga.Box(
            style=Pack(
                direction=COLUMN,
                gap=8,
            )
        )

        self.titre_liste = toga.Label(
            "Lieux enregistrés",
            style=Pack(
                font_size=16,
                font_weight="bold",
            ),
        )

        self.liste_lieux = toga.Box(
            style=Pack(
                direction=COLUMN,
                gap=8,
            )
        )

        section.add(
            self.titre_liste,
            self.liste_lieux,
        )

        self.main_box.add(section)

    def actualiser_liste_lieux(self):
        """Recharge les fiches du carnet."""

        if self.liste_lieux is None:
            return

        self.liste_lieux.clear()

        try:
            lieux = charger_lieux()

        except ValueError as erreur:
            self.liste_lieux.add(
                toga.Label(
                    f"Impossible de lire le carnet : {erreur}"
                )
            )
            return

        lieux = sorted(
            lieux,
            key=lambda lieu: str(
                lieu.get("nom") or ""
            ).casefold(),
        )

        self.titre_liste.text = (
            f"Lieux enregistrés ({len(lieux)})"
        )

        if not lieux:
            self.liste_lieux.add(
                toga.Label(
                    "Ton carnet de lieux est vide.",
                    style=Pack(
                        color="#6c757d",
                    ),
                )
            )
            return

        for lieu in lieux:
            self._ajouter_carte_lieu(lieu)

    def _ajouter_carte_lieu(self, lieu):
        """Ajoute une fiche à la liste visible."""

        carte = toga.Box(
            style=Pack(
                direction=COLUMN,
                gap=5,
                background_color="#f8f9fa",
                margin_bottom=4,
            )
        )

        nom = lieu.get("nom") or "Lieu sans nom"

        carte.add(
            toga.Label(
                nom,
                style=Pack(
                    font_weight="bold",
                    margin_top=10,
                    margin_left=10,
                    margin_right=10,
                ),
            )
        )

        informations = []

        if lieu.get("profession"):
            informations.append(
                str(lieu["profession"])
            )

        if lieu.get("categorie"):
            informations.append(
                str(lieu["categorie"])
            )

        if lieu.get("visio"):
            informations.append("Visio possible")

        if informations:
            carte.add(
                toga.Label(
                    " • ".join(informations),
                    style=Pack(
                        color="#6c757d",
                        margin_left=10,
                        margin_right=10,
                    ),
                )
            )

        alias = lieu.get("alias") or []

        if alias:
            carte.add(
                toga.Label(
                    "Alias : " + ", ".join(alias),
                    style=Pack(
                        margin_left=10,
                        margin_right=10,
                    ),
                )
            )

        adresse_favorite = None

        for adresse in lieu.get("adresses") or []:
            if adresse.get("favorite") and adresse.get("adresse"):
                adresse_favorite = adresse
                break

        if adresse_favorite is None:
            adresses_valides = [
                adresse
                for adresse in (lieu.get("adresses") or [])
                if adresse.get("adresse")
            ]

            if len(adresses_valides) == 1:
                adresse_favorite = adresses_valides[0]

        if adresse_favorite:
            carte.add(
                toga.Label(
                    (
                        "★ "
                        f"{adresse_favorite.get('libelle') or 'Adresse'} : "
                        f"{adresse_favorite.get('adresse')}"
                    ),
                    style=Pack(
                        margin_left=10,
                        margin_right=10,
                    ),
                )
            )

        actions = toga.Box(
            style=Pack(
                direction=ROW,
                gap=6,
                margin_left=10,
                margin_right=10,
                margin_bottom=10,
            )
        )

        actions.add(
            toga.Button(
                "Modifier",
                on_press=(
                    lambda widget,
                    lieu=dict(lieu),
                    **kwargs:
                    self.charger_fiche(lieu)
                ),
                style=Pack(
                    flex=1,
                ),
            ),
            toga.Button(
                "Supprimer",
                on_press=(
                    lambda widget,
                    lieu=dict(lieu),
                    **kwargs:
                    self.supprimer_fiche(lieu)
                ),
                style=Pack(
                    flex=1,
                ),
            ),
        )

        carte.add(actions)
        self.liste_lieux.add(carte)

    def supprimer_fiche(self, lieu):
        """Supprime une fiche enregistrée."""

        lieu_id = lieu.get("id")

        if not lieu_id:
            return

        try:
            supprime = supprimer_lieu(lieu_id)

        except (OSError, ValueError) as erreur:
            self.statut_label.text = (
                "Impossible de supprimer la fiche : "
                f"{erreur}"
            )
            return

        if not supprime:
            self.statut_label.text = (
                "Cette fiche n'existe plus."
            )
            return

        if self.lieu_en_modification_id == lieu_id:
            self._vider_formulaire_fiche()

        self.actualiser_liste_lieux()

        self.statut_label.text = (
            f"{lieu.get('nom') or 'La fiche'} a été supprimé du carnet."
        )


def creer_interface_lieux():
    """Crée l'interface complète du carnet de lieux."""

    return InterfaceLieux().construire()
