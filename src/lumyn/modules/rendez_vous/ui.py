"""Interface du module Rendez-vous.

Le CRUD est lié à Google Calendar :
- CREATE : crée l'événement Google puis enregistre ses identifiants dans Lumyn.
- READ   : affiche les rendez-vous locaux et le calendrier Google.
- UPDATE : modifie le même événement Google, même si le calendrier change.
- DELETE : supprime l'événement Google lié puis la copie locale.

Les anciens rendez-vous locaux sans google_event_id restent identifiés comme
"non liés". S'ils sont modifiés, Lumyn crée alors leur événement Google et
les lie à partir de ce moment.
"""

import toga

from toga.style.pack import COLUMN, ROW, Pack

from lumyn.modules.rendez_vous.gestion import preparer_rendez_vous

from lumyn.modules.rendez_vous.stockage import (
    charger_rendez_vous,
    enregistrer_rendez_vous,
    modifier_rendez_vous as modifier_rendez_vous_stockage,
    supprimer_rendez_vous,
)

from lumyn.modules.rendez_vous.calendrier_ui import (
    creer_calendrier_mensuel,
)

from lumyn.modules.rendez_vous.agenda_google import (
    creer_evenement_google,
    deplacer_evenement_google,
    lister_calendriers_google,
    modifier_evenement_google,
    supprimer_evenement_google,
)


NOM_CALENDRIER_DEFAUT = "Famille"
DUREE_PAR_DEFAUT_MINUTES = 60
CALENDRIER_LOCAL_ID = "__lumyn_local__"


def _date_iso(valeur):
    """Retourne une date sous forme YYYY-MM-DD pour le tri et l'affichage."""

    if valeur is None:
        return ""

    if hasattr(valeur, "isoformat"):
        try:
            return valeur.isoformat()
        except TypeError:
            pass

    return str(valeur)


def _date_affichee(valeur):
    """Retourne une date lisible au format JJ/MM/AAAA."""

    texte = _date_iso(valeur)

    try:
        annee, mois, jour = texte.split("-")
        return f"{jour}/{mois}/{annee}"
    except ValueError:
        return texte


def _heure_affichee(valeur):
    """Retourne une heure lisible."""

    if valeur is None:
        return ""

    return str(valeur)


def _copie_rendez_vous(rendez_vous):
    """Crée une copie indépendante du dictionnaire de rendez-vous."""

    if not rendez_vous:
        return {}

    return dict(rendez_vous)


class InterfaceRendezVous:
    """Contrôleur de l'interface Rendez-vous."""

    def __init__(self):
        self.resultat_courant = None
        self.saisie_analysee = None

        # Contient le rendez-vous LOCAL original complet pendant une modification.
        # On garde ainsi son id Lumyn + google_event_id + google_calendar_id.
        self.rendez_vous_en_modification = None

        self.calendriers_google = []
        self.calendriers_ecriture = []
        self.erreur_calendriers = None

        self.main_box = None

        self.rdv_input = None
        self.calendrier_selection = None
        self.statut_calendrier = None
        self.resultat_label = None

        self.analyser_button = None
        self.modifier_button = None
        self.confirmer_button = None

        self.titre_liste = None
        self.liste_rendez_vous = None

        self.zone_calendrier = None

    # =========================================================
    # CONSTRUCTION GÉNÉRALE
    # =========================================================

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
        self._charger_calendriers_google()
        self._construire_creation()
        self._construire_liste_locale()
        self._construire_agenda()

        self.actualiser_liste_rendez_vous()
        self.actualiser_calendrier_google()

        scroll_container = toga.ScrollContainer(
            content=self.main_box,
            horizontal=False,
            vertical=True,
            style=Pack(
                flex=1,
            ),
        )

        return scroll_container

    # =========================================================
    # EN-TÊTE
    # =========================================================

    def _construire_entete(self):
        """Construit l'en-tête de la page."""

        entete = toga.Box(
            style=Pack(
                direction=COLUMN,
                gap=4,
                margin_bottom=5,
            )
        )

        bonjour = toga.Label(
            "Bonjour Gaëlle 👋",
            style=Pack(
                font_size=22,
                font_weight="bold",
            )
        )

        bienvenue = toga.Label(
            "Organise tes rendez-vous simplement avec Lumyn.",
            style=Pack(
                color="#6c757d",
            )
        )

        entete.add(
            bonjour,
            bienvenue,
        )

        self.main_box.add(
            entete
        )

    # =========================================================
    # CALENDRIERS GOOGLE DISPONIBLES
    # =========================================================

    def _charger_calendriers_google(self):
        """Charge les calendriers Google dans lesquels Lumyn peut écrire."""

        try:
            self.calendriers_google = (
                lister_calendriers_google()
            )

            self.erreur_calendriers = None

        except Exception as erreur:
            self.calendriers_google = []
            self.erreur_calendriers = str(
                erreur
            )

        self.calendriers_ecriture = [
            calendrier
            for calendrier in self.calendriers_google
            if calendrier.get("access_role") in (
                "owner",
                "writer",
            )
        ]

        self.calendriers_ecriture.sort(
            key=lambda calendrier: (
                0
                if (
                    calendrier.get("nom", "")
                    .strip()
                    .casefold()
                    == NOM_CALENDRIER_DEFAUT.casefold()
                )
                else (
                    1
                    if calendrier.get("principal")
                    else 2
                ),
                calendrier.get(
                    "nom",
                    "",
                ).casefold(),
            )
        )

    def _items_calendriers(self):
        """Construit les éléments du menu déroulant."""

        return [
            {
                "nom": calendrier.get(
                    "nom",
                    "Calendrier Google",
                ),
                "calendar_id": calendrier.get(
                    "id"
                ),
            }
            for calendrier in self.calendriers_ecriture
            if calendrier.get("id")
        ] + [{"nom": "Sur cet appareil uniquement", "calendar_id": CALENDRIER_LOCAL_ID}]

    def _selectionner_calendrier_defaut(self):
        """Sélectionne Famille par défaut, puis le principal en secours."""

        if not self.calendrier_selection:
            return

        items = list(
            self.calendrier_selection.items
        )

        if not items:
            return

        # 1. Famille
        for choix in items:
            if (
                str(
                    getattr(
                        choix,
                        "nom",
                        "",
                    )
                )
                .strip()
                .casefold()
                == NOM_CALENDRIER_DEFAUT.casefold()
            ):
                self.calendrier_selection.value = (
                    choix
                )
                return

        # 2. Calendrier principal
        ids_principaux = {
            calendrier.get("id")
            for calendrier in self.calendriers_ecriture
            if calendrier.get("principal")
        }

        for choix in items:
            if (
                getattr(
                    choix,
                    "calendar_id",
                    None,
                )
                in ids_principaux
            ):
                self.calendrier_selection.value = (
                    choix
                )
                return

        # 3. Premier calendrier disponible
        self.calendrier_selection.value = items[
            0
        ]

    def _selectionner_calendrier_par_id(
        self,
        calendrier_id,
    ):
        """Sélectionne un calendrier Google à partir de son ID."""

        if (
            not calendrier_id
            or not self.calendrier_selection
        ):
            return False

        for choix in self.calendrier_selection.items:
            if (
                getattr(
                    choix,
                    "calendar_id",
                    None,
                )
                == calendrier_id
            ):
                self.calendrier_selection.value = (
                    choix
                )
                return True

        return False

    def _calendrier_selectionne(self):
        """Retourne l'ID et le nom du calendrier choisi."""

        if not self.calendrier_selection:
            raise ValueError(
                "Aucun calendrier Google disponible."
            )

        choix = self.calendrier_selection.value

        if choix is None:
            raise ValueError(
                "Choisis un calendrier Google."
            )

        calendrier_id = getattr(
            choix,
            "calendar_id",
            None,
        )

        nom = getattr(
            choix,
            "nom",
            "Google Calendar",
        )

        if not calendrier_id:
            raise ValueError(
                "Le calendrier sélectionné n'a pas d'identifiant Google."
            )

        return calendrier_id, str(nom)

    # =========================================================
    # CARTE DE CRÉATION / MODIFICATION
    # =========================================================

    def _construire_creation(self):
        """Construit la carte de création et de modification."""

        carte_creation = toga.Box(
            style=Pack(
                direction=COLUMN,
                gap=8,
                background_color="#f8f9fa",
                margin_bottom=5,
            )
        )

        titre_creation = toga.Label(
            "Ajouter un rendez-vous",
            style=Pack(
                font_size=16,
                font_weight="bold",
                margin_top=12,
                margin_left=12,
                margin_right=12,
            )
        )

        aide_creation = toga.Label(
            "Écris ton rendez-vous naturellement.",
            style=Pack(
                color="#6c757d",
                margin_left=12,
                margin_right=12,
            )
        )

        self.rdv_input = toga.TextInput(
            placeholder=(
                "Exemple : Dentiste mardi à 14h30"
            ),
            style=Pack(
                margin_left=12,
                margin_right=12,
            ),
        )

        label_calendrier = toga.Label(
            "Enregistrer dans",
            style=Pack(
                font_weight="bold",
                margin_left=12,
                margin_right=12,
                margin_top=4,
            )
        )

        self.calendrier_selection = (
            toga.Selection(
                items=self._items_calendriers(),
                accessor="nom",
                enabled=True,
                style=Pack(
                    margin_left=12,
                    margin_right=12,
                ),
            )
        )

        self._selectionner_calendrier_defaut()

        self.statut_calendrier = toga.Label(
            "",
            style=Pack(
                color="#6c757d",
                margin_left=12,
                margin_right=12,
            )
        )

        if self.erreur_calendriers:
            self.statut_calendrier.text = (
                "Impossible de récupérer les calendriers Google : "
                f"{self.erreur_calendriers}. Enregistrement local disponible, sans rappel."
            )

        elif not self.calendriers_ecriture:
            self.statut_calendrier.text = (
                "Enregistrement local disponible, sans rappel sur cet appareil."
            )

        else:
            self.statut_calendrier.text = (
                "Durée par défaut : 1 heure • "
                "rappels : 1 jour et 1 heure avant."
            )

        self.resultat_label = toga.Label(
            "",
            style=Pack(
                margin_left=12,
                margin_right=12,
            )
        )

        self.analyser_button = toga.Button(
            "Analyser le rendez-vous",
            on_press=self.analyser_rendez_vous,
            style=Pack(
                margin_left=12,
                margin_right=12,
            )
        )

        actions_creation = toga.Box(
            style=Pack(
                direction=ROW,
                gap=6,
                margin_left=12,
                margin_right=12,
                margin_bottom=12,
            )
        )

        self.modifier_button = toga.Button(
            "Modifier",
            on_press=self.modifier_saisie,
            enabled=False,
            style=Pack(
                flex=1,
            )
        )

        self.confirmer_button = toga.Button(
            "Confirmer",
            on_press=self.confirmer_rendez_vous,
            enabled=False,
            style=Pack(
                flex=1,
            )
        )

        actions_creation.add(
            self.modifier_button,
            self.confirmer_button,
        )

        carte_creation.add(
            titre_creation,
            aide_creation,
            self.rdv_input,
            label_calendrier,
            self.calendrier_selection,
            self.statut_calendrier,
            self.analyser_button,
            self.resultat_label,
            actions_creation,
        )

        self.main_box.add(
            carte_creation
        )

    # =========================================================
    # LISTE LOCALE
    # =========================================================

    def _construire_liste_locale(self):
        """Construit la section des rendez-vous enregistrés par Lumyn."""

        section_liste = toga.Box(
            style=Pack(
                direction=COLUMN,
                gap=8,
            )
        )

        self.titre_liste = toga.Label(
            "Rendez-vous Lumyn",
            style=Pack(
                font_size=16,
                font_weight="bold",
            )
        )

        description_liste = toga.Label(
            "Rendez-vous créés ou gérés par Lumyn.",
            style=Pack(
                color="#6c757d",
                margin_bottom=3,
            )
        )

        self.liste_rendez_vous = toga.Box(
            style=Pack(
                direction=COLUMN,
                gap=8,
            )
        )

        section_liste.add(
            self.titre_liste,
            description_liste,
            self.liste_rendez_vous,
        )

        self.main_box.add(
            section_liste
        )

    # =========================================================
    # AGENDA
    # =========================================================

    def _construire_agenda(self):
        """Construit la zone du calendrier mensuel."""

        section_calendrier = toga.Box(
            style=Pack(
                direction=COLUMN,
                gap=5,
                margin_top=10,
            )
        )

        titre_calendrier = toga.Label(
            "Agenda",
            style=Pack(
                font_size=16,
                font_weight="bold",
            )
        )

        description_calendrier = toga.Label(
            "Tes calendriers Google et tes événements.",
            style=Pack(
                color="#6c757d",
            )
        )

        self.zone_calendrier = toga.Box(
            style=Pack(
                direction=COLUMN,
            )
        )

        section_calendrier.add(
            titre_calendrier,
            description_calendrier,
            self.zone_calendrier,
        )

        self.main_box.add(
            section_calendrier
        )

    def actualiser_calendrier_google(self):
        """Recharge l'affichage mensuel après une opération CRUD."""

        if self.zone_calendrier is None:
            return

        self.zone_calendrier.clear()

        self.zone_calendrier.add(
            creer_calendrier_mensuel()
        )

    # =========================================================
    # OUTILS DE LIAISON LOCAL <-> GOOGLE
    # =========================================================

    def _ajouter_metadonnees_google(
        self,
        rendez_vous,
        evenement_google,
        calendrier_id,
        calendrier_nom,
    ):
        """Ajoute les identifiants de liaison Google au rendez-vous."""

        evenement_id = (
            evenement_google.get("id")
            if evenement_google
            else None
        )

        if not evenement_id:
            raise RuntimeError(
                "Google Calendar n'a pas renvoyé d'identifiant d'événement."
            )

        rendez_vous[
            "google_event_id"
        ] = evenement_id

        rendez_vous[
            "google_calendar_id"
        ] = calendrier_id

        rendez_vous[
            "google_calendar_name"
        ] = calendrier_nom

        rendez_vous[
            "duree_minutes"
        ] = rendez_vous.get(
            "duree_minutes",
            DUREE_PAR_DEFAUT_MINUTES,
        )

        return rendez_vous

    def _rendez_vous_local_par_id(
        self,
        rendez_vous_id,
    ):
        """Retrouve un rendez-vous local par son UUID."""

        for rendez_vous in charger_rendez_vous():
            if (
                rendez_vous.get("id")
                == rendez_vous_id
            ):
                return rendez_vous

        return None

    def _liaison_google_persistee(
        self,
        google_event_id,
    ):
        """Vérifie que le stockage local a bien conservé l'ID Google."""

        if not google_event_id:
            return False

        for rendez_vous in charger_rendez_vous():
            if (
                rendez_vous.get(
                    "google_event_id"
                )
                == google_event_id
            ):
                return True

        return False

    def _preparer_nouveau_pour_modification(
        self,
        nouveau,
        original,
    ):
        """Préserve les champs que le parseur ne reconstruit pas encore."""

        nouveau = {**original, **nouveau}

        nouveau[
            "duree_minutes"
        ] = nouveau.get(
            "duree_minutes",
            original.get(
                "duree_minutes",
                DUREE_PAR_DEFAUT_MINUTES,
            ),
        )

        return nouveau

    # =========================================================
    # CREATE LIÉ
    # =========================================================

    def _creer_rendez_vous_lie(
        self,
        rendez_vous,
    ):
        """Crée Google puis la copie locale avec les IDs de liaison."""

        calendrier_id, calendrier_nom = (
            self._calendrier_selectionne()
        )

        rendez_vous = _copie_rendez_vous(
            rendez_vous
        )

        rendez_vous[
            "duree_minutes"
        ] = rendez_vous.get(
            "duree_minutes",
            DUREE_PAR_DEFAUT_MINUTES,
        )

        evenement_google = (
            creer_evenement_google(
                rendez_vous,
                calendrier_id,
            )
        )

        rendez_vous = (
            self._ajouter_metadonnees_google(
                rendez_vous,
                evenement_google,
                calendrier_id,
                calendrier_nom,
            )
        )

        google_event_id = rendez_vous[
            "google_event_id"
        ]

        try:
            enregistrer_rendez_vous(
                rendez_vous
            )

            # Important :
            # on vérifie que le stockage a vraiment conservé google_event_id.
            if not self._liaison_google_persistee(
                google_event_id
            ):
                raise RuntimeError(
                    "Le rendez-vous local a été enregistré, "
                    "mais son google_event_id n'a pas été conservé."
                )

        except Exception:
            # Si le stockage local échoue, on annule la création Google
            # pour éviter un événement orphelin.
            try:
                supprimer_evenement_google(
                    calendrier_id,
                    google_event_id,
                )
            except Exception:
                pass

            raise

        return rendez_vous

    # =========================================================
    # UPDATE LIÉ
    # =========================================================

    def _modifier_rendez_vous_lie(
        self,
        nouveau_rendez_vous,
    ):
        """Modifie le même rendez-vous dans Google et Lumyn."""

        original = _copie_rendez_vous(
            self.rendez_vous_en_modification
        )

        rendez_vous_id = original.get(
            "id"
        )

        if not rendez_vous_id:
            raise ValueError(
                "Le rendez-vous local n'a pas d'identifiant."
            )

        calendrier_destination_id, calendrier_destination_nom = (
            self._calendrier_selectionne()
        )

        nouveau = (
            self._preparer_nouveau_pour_modification(
                nouveau_rendez_vous,
                original,
            )
        )

        ancien_event_id = original.get(
            "google_event_id"
        )

        ancien_calendrier_id = original.get(
            "google_calendar_id"
        )

        # -----------------------------------------------------
        # CAS 1 : rendez-vous déjà lié
        # -----------------------------------------------------

        if (
            ancien_event_id
            and ancien_calendrier_id
        ):
            event_id_courant = (
                ancien_event_id
            )

            deplace = False

            try:
                if (
                    ancien_calendrier_id
                    != calendrier_destination_id
                ):
                    evenement_deplace = (
                        deplacer_evenement_google(
                            ancien_calendrier_id,
                            calendrier_destination_id,
                            event_id_courant,
                        )
                    )

                    if evenement_deplace:
                        event_id_courant = (
                            evenement_deplace.get(
                                "id",
                                event_id_courant,
                            )
                        )

                    deplace = True

                evenement_google = (
                    modifier_evenement_google(
                        nouveau,
                        calendrier_destination_id,
                        event_id_courant,
                    )
                )

                nouveau = (
                    self._ajouter_metadonnees_google(
                        nouveau,
                        evenement_google,
                        calendrier_destination_id,
                        calendrier_destination_nom,
                    )
                )

            except Exception:
                # Si le déplacement a réussi mais que la modification a échoué,
                # on essaie de remettre l'événement dans son calendrier d'origine.
                if deplace:
                    try:
                        deplacer_evenement_google(
                            calendrier_destination_id,
                            ancien_calendrier_id,
                            event_id_courant,
                        )
                    except Exception:
                        pass

                raise

            try:
                resultat_local = modifier_rendez_vous_stockage(rendez_vous_id, nouveau)
                if resultat_local is None or resultat_local is False:
                    raise RuntimeError("Rendez-vous local introuvable.")
            except Exception as erreur_locale:
                # Rollback Google : on restaure autant que possible
                # l'ancien rendez-vous.
                try:
                    modifier_evenement_google(
                        original,
                        calendrier_destination_id,
                        nouveau.get(
                            "google_event_id",
                            event_id_courant,
                        ),
                    )

                    if (
                        calendrier_destination_id
                        != ancien_calendrier_id
                    ):
                        deplacer_evenement_google(
                            calendrier_destination_id,
                            ancien_calendrier_id,
                            nouveau.get(
                                "google_event_id",
                                event_id_courant,
                            ),
                        )
                except Exception:
                    pass

                raise RuntimeError(
                    "Lumyn n'a pas réussi à mettre à jour sa copie locale. "
                    "La modification a été annulée autant que possible."
                ) from erreur_locale

            sauvegarde = (
                self._rendez_vous_local_par_id(
                    rendez_vous_id
                )
            )

            if (
                not sauvegarde
                or sauvegarde.get(
                    "google_event_id"
                )
                != nouveau.get(
                    "google_event_id"
                )
                or sauvegarde.get(
                    "google_calendar_id"
                )
                != calendrier_destination_id
            ):
                # Le stockage a perdu les métadonnées Google.
                # On remet la copie locale d'origine et on tente le rollback Google.
                try:
                    modifier_rendez_vous_stockage(
                        rendez_vous_id,
                        original,
                    )
                except Exception:
                    pass

                try:
                    modifier_evenement_google(
                        original,
                        calendrier_destination_id,
                        nouveau.get(
                            "google_event_id",
                            event_id_courant,
                        ),
                    )

                    if (
                        calendrier_destination_id
                        != ancien_calendrier_id
                    ):
                        deplacer_evenement_google(
                            calendrier_destination_id,
                            ancien_calendrier_id,
                            nouveau.get(
                                "google_event_id",
                                event_id_courant,
                            ),
                        )
                except Exception:
                    pass

                raise RuntimeError(
                    "Le stockage local n'a pas conservé la liaison Google."
                )

            return nouveau

        # -----------------------------------------------------
        # CAS 2 : ancien rendez-vous local non lié
        #
        # Sa première modification crée l'événement Google puis
        # enregistre ses IDs : il devient alors complètement lié.
        # -----------------------------------------------------

        evenement_google = (
            creer_evenement_google(
                nouveau,
                calendrier_destination_id,
            )
        )

        nouveau = (
            self._ajouter_metadonnees_google(
                nouveau,
                evenement_google,
                calendrier_destination_id,
                calendrier_destination_nom,
            )
        )

        nouvel_event_id = nouveau[
            "google_event_id"
        ]

        try:
            resultat_local = (
                modifier_rendez_vous_stockage(
                    rendez_vous_id,
                    nouveau,
                )
            )

            if (
                resultat_local is None
                or resultat_local is False
            ):
                raise RuntimeError(
                    "Impossible de mettre à jour "
                    "le rendez-vous local."
                )

            sauvegarde = (
                self._rendez_vous_local_par_id(
                    rendez_vous_id
                )
            )

            if (
                not sauvegarde
                or sauvegarde.get(
                    "google_event_id"
                )
                != nouvel_event_id
            ):
                raise RuntimeError(
                    "Le stockage local n'a pas conservé "
                    "la nouvelle liaison Google."
                )

        except Exception:
            # On supprime l'événement Google créé pour ne pas créer de doublon
            # si le stockage local n'a pas pu être mis à jour.
            try:
                supprimer_evenement_google(
                    calendrier_destination_id,
                    nouvel_event_id,
                )
            except Exception:
                pass

            try:
                modifier_rendez_vous_stockage(
                    rendez_vous_id,
                    original,
                )
            except Exception:
                pass

            raise

        return nouveau

    # =========================================================
    # DELETE LIÉ
    # =========================================================

    def _supprimer_rendez_vous_lie(
        self,
        rendez_vous,
    ):
        """Supprime Google puis la copie locale correspondante."""

        rendez_vous = _copie_rendez_vous(
            rendez_vous
        )

        rendez_vous_id = rendez_vous.get(
            "id"
        )

        if not rendez_vous_id:
            raise ValueError(
                "Le rendez-vous local n'a pas d'identifiant."
            )

        google_event_id = rendez_vous.get(
            "google_event_id"
        )

        google_calendar_id = rendez_vous.get(
            "google_calendar_id"
        )

        google_supprime = False

        if (
            google_event_id
            and google_calendar_id
        ):
            supprimer_evenement_google(
                google_calendar_id,
                google_event_id,
            )

            google_supprime = True

        try:
            local_supprime = (
                supprimer_rendez_vous(
                    rendez_vous_id
                )
            )

        except Exception as erreur_locale:
            # Si Google a été supprimé mais que le fichier local n'a pas pu
            # être écrit, on essaie de recréer Google pour restaurer la liaison.
            if google_supprime:
                try:
                    evenement_recree = (
                        creer_evenement_google(
                            rendez_vous,
                            google_calendar_id,
                        )
                    )

                    restauration = (
                        _copie_rendez_vous(
                            rendez_vous
                        )
                    )

                    restauration[
                        "google_event_id"
                    ] = evenement_recree.get(
                        "id"
                    )

                    modifier_rendez_vous_stockage(
                        rendez_vous_id,
                        restauration,
                    )

                except Exception:
                    pass

            raise erreur_locale

        return {
            "local_supprime": bool(
                local_supprime
            ),
            "google_supprime": (
                google_supprime
            ),
            "etait_lie": bool(
                google_event_id
                and google_calendar_id
            ),
        }

    # =========================================================
    # READ : LISTE DES RENDEZ-VOUS LOCAUX
    # =========================================================

    def actualiser_liste_rendez_vous(self):
        """Affiche les rendez-vous locaux et leur état de liaison Google."""

        self.liste_rendez_vous.clear()

        try:
            rendez_vous_enregistres = (
                charger_rendez_vous()
            )
        except Exception as erreur:
            self.titre_liste.text = (
                "Rendez-vous Lumyn"
            )

            self.liste_rendez_vous.add(
                toga.Label(
                    "Impossible de charger les rendez-vous : "
                    f"{erreur}",
                    style=Pack(
                        color="#6c757d",
                        margin=10,
                    )
                )
            )

            return

        nombre_rendez_vous = len(
            rendez_vous_enregistres
        )

        if nombre_rendez_vous == 0:
            self.titre_liste.text = (
                "Rendez-vous Lumyn"
            )

            self.liste_rendez_vous.add(
                toga.Label(
                    "Aucun rendez-vous enregistré.",
                    style=Pack(
                        color="#6c757d",
                        margin=10,
                    )
                )
            )

            return

        self.titre_liste.text = (
            f"Rendez-vous Lumyn "
            f"({nombre_rendez_vous})"
        )

        rendez_vous_enregistres.sort(
            key=lambda rdv: (
                _date_iso(
                    rdv.get("date")
                ),
                _heure_affichee(
                    rdv.get("heure")
                ),
            )
        )

        for rendez_vous in rendez_vous_enregistres:
            self._ajouter_carte_rendez_vous(
                rendez_vous
            )

    def _ajouter_carte_rendez_vous(
        self,
        rendez_vous,
    ):
        """Ajoute une carte de rendez-vous à la liste."""

        rendez_vous = _copie_rendez_vous(
            rendez_vous
        )

        jour_calcule = (
            rendez_vous.get(
                "jour_calcule"
            )
            or ""
        )

        date_affichee = (
            _date_affichee(
                rendez_vous.get(
                    "date"
                )
            )
        )

        heure = _heure_affichee(
            rendez_vous.get(
                "heure"
            )
        )

        titre_rdv = rendez_vous.get(
            "titre",
            "Sans titre",
        )

        calendrier_nom = rendez_vous.get(
            "google_calendar_name"
        )

        google_event_id = rendez_vous.get(
            "google_event_id"
        )

        google_calendar_id = rendez_vous.get(
            "google_calendar_id"
        )

        est_lie = bool(
            google_event_id
            and google_calendar_id
        )

        carte_rdv = toga.Box(
            style=Pack(
                direction=COLUMN,
                gap=6,
                background_color="#f8f9fa",
            )
        )

        ligne_date = toga.Label(
            (
                f"{jour_calcule} "
                f"{date_affichee} • "
                f"{heure}"
            ).strip(),
            style=Pack(
                font_weight="bold",
                margin_top=10,
                margin_left=10,
                margin_right=10,
            )
        )

        ligne_titre = toga.Label(
            titre_rdv,
            style=Pack(
                margin_left=10,
                margin_right=10,
            )
        )

        carte_rdv.add(
            ligne_date,
            ligne_titre,
        )

        if est_lie:
            ligne_liaison = toga.Label(
                (
                    "✓ Lié à Google Calendar"
                    + (
                        f" • {calendrier_nom}"
                        if calendrier_nom
                        else ""
                    )
                ),
                style=Pack(
                    color="#6c757d",
                    margin_left=10,
                    margin_right=10,
                )
            )

        else:
            ligne_liaison = toga.Label(
                (
                    "Ancien rendez-vous non lié à Google. "
                    "Tu peux le garder local ou choisir un calendrier Google."
                ),
                style=Pack(
                    color="#6c757d",
                    margin_left=10,
                    margin_right=10,
                )
            )

        carte_rdv.add(
            ligne_liaison
        )

        actions_rdv = toga.Box(
            style=Pack(
                direction=ROW,
                gap=6,
                margin_left=10,
                margin_right=10,
                margin_bottom=10,
            )
        )

        bouton_modifier = toga.Button(
            "Modifier",
            on_press=(
                lambda widget,
                rdv=_copie_rendez_vous(
                    rendez_vous
                ),
                **kwargs:
                self.charger_modification(
                    widget,
                    rdv,
                    **kwargs,
                )
            ),
            style=Pack(
                flex=1,
            )
        )

        bouton_supprimer = toga.Button(
            "Supprimer",
            on_press=(
                lambda widget,
                rdv=_copie_rendez_vous(
                    rendez_vous
                ),
                **kwargs:
                self.supprimer_rendez_vous_ui(
                    widget,
                    rdv,
                    **kwargs,
                )
            ),
            style=Pack(
                flex=1,
            )
        )

        actions_rdv.add(
            bouton_modifier,
            bouton_supprimer,
        )

        carte_rdv.add(
            actions_rdv
        )

        self.liste_rendez_vous.add(
            carte_rdv
        )

    # =========================================================
    # CHARGEMENT D'UN RENDEZ-VOUS POUR UPDATE
    # =========================================================

    def charger_modification(
        self,
        widget,
        rendez_vous,
        **kwargs,
    ):
        """Charge un rendez-vous existant dans le formulaire."""

        self.rendez_vous_en_modification = (
            _copie_rendez_vous(
                rendez_vous
            )
        )

        self.resultat_courant = None

        titre = rendez_vous.get(
            "titre",
            "",
        )

        date_saisie = _date_affichee(
            rendez_vous.get(
                "date"
            )
        )

        heure = _heure_affichee(
            rendez_vous.get(
                "heure"
            )
        )

        self.rdv_input.value = (
            f"{titre} "
            f"{date_saisie} "
            f"{heure}"
            + (f" à {rendez_vous['lieu']}" if rendez_vous.get("lieu") else "")
        ).strip()

        calendrier_id = rendez_vous.get(
            "google_calendar_id"
        )

        if calendrier_id:
            trouve = (
                self._selectionner_calendrier_par_id(
                    calendrier_id
                )
            )

            if not trouve:
                self._selectionner_calendrier_defaut()

        else:
            self._selectionner_calendrier_par_id(CALENDRIER_LOCAL_ID)

        if (
            rendez_vous.get(
                "google_event_id"
            )
            and calendrier_id
        ):
            self.resultat_label.text = (
                "Rendez-vous lié chargé. "
                "Modifie la phrase, éventuellement le calendrier, "
                "puis analyse de nouveau."
            )

        else:
            self.resultat_label.text = (
                "Ancien rendez-vous non lié chargé. "
                "Garde-le sur cet appareil ou sélectionne un calendrier Google."
            )

        self.modifier_button.enabled = False
        self.confirmer_button.enabled = False

    # =========================================================
    # ANALYSE
    # =========================================================

    def analyser_rendez_vous(
        self,
        widget,
        **kwargs,
    ):
        """Analyse la phrase saisie."""

        self.resultat_courant = (
            preparer_rendez_vous(
                self.rdv_input.value
            )
        )

        self.resultat_label.text = (
            self.resultat_courant[
                "message"
            ]
        )

        self.saisie_analysee = (self.rdv_input.value, self._calendrier_selectionne()[0])

        etat_resultat = (
            self.resultat_courant[
                "etat"
            ]
        )

        if etat_resultat == "confirmation":
            self.modifier_button.enabled = True

            self.confirmer_button.enabled = True
            calendrier_id, nom = self._calendrier_selectionne()
            self.resultat_label.text += f"\nDestination : {nom}."
            if calendrier_id == CALENDRIER_LOCAL_ID:
                self.resultat_label.text += "\nAucun rappel automatique en mode local."

        elif etat_resultat in (
            "erreur",
            "incomplet",
        ):
            self.modifier_button.enabled = True
            self.confirmer_button.enabled = False

        else:
            self.modifier_button.enabled = False
            self.confirmer_button.enabled = False

    def modifier_saisie(
        self,
        widget,
        **kwargs,
    ):
        """Réouvre simplement la saisie avant une nouvelle analyse."""

        self.resultat_courant = None

        self.resultat_label.text = (
            "Modifie la phrase puis clique de nouveau sur "
            "« Analyser le rendez-vous »."
        )

        self.modifier_button.enabled = False
        self.confirmer_button.enabled = False

    # =========================================================
    # CONFIRMATION CREATE / UPDATE
    # =========================================================

    def confirmer_rendez_vous(
        self,
        widget,
        **kwargs,
    ):
        """Crée ou modifie le rendez-vous en gardant Local et Google liés."""

        if not self.resultat_courant:
            self.resultat_label.text = (
                "Aucun rendez-vous à confirmer."
            )
            return

        if (
            self.resultat_courant.get(
                "etat"
            )
            != "confirmation"
        ):
            self.resultat_label.text = (
                "Le rendez-vous n'est pas prêt à être confirmé."
            )
            return

        if self.saisie_analysee != (
            self.rdv_input.value, self._calendrier_selectionne()[0]
        ):
            self.modifier_saisie(widget)
            return

        rendez_vous = (
            self.resultat_courant.get(
                "rendez_vous"
            )
        )

        if not rendez_vous:
            self.resultat_label.text = (
                "Le rendez-vous préparé est vide."
            )
            return

        try:
            calendrier_id, _ = self._calendrier_selectionne()
            if calendrier_id == CALENDRIER_LOCAL_ID:
                original = self.rendez_vous_en_modification
                if original and original.get("google_event_id"):
                    raise ValueError(
                        "Ce rendez-vous est lié à Google. Choisis son calendrier "
                        "Google pour conserver la synchronisation."
                    )
                if original:
                    rendez_vous_final = modifier_rendez_vous_stockage(
                        original["id"], self._preparer_nouveau_pour_modification(rendez_vous, original)
                    )
                    if rendez_vous_final is None:
                        raise ValueError("Le rendez-vous local est introuvable.")
                else:
                    rendez_vous_final = enregistrer_rendez_vous(rendez_vous)
                message_action = "Rendez-vous enregistré sur cet appareil ✅"
            elif self.rendez_vous_en_modification:
                rendez_vous_final = (
                    self._modifier_rendez_vous_lie(
                        rendez_vous
                    )
                )

                message_action = (
                    "Rendez-vous modifié dans "
                    "Lumyn et Google Calendar ✅"
                )

            else:
                rendez_vous_final = (
                    self._creer_rendez_vous_lie(
                        rendez_vous
                    )
                )

                message_action = (
                    "Rendez-vous créé dans "
                    "Lumyn et Google Calendar ✅"
                )

        except Exception as erreur:
            self.resultat_label.text = (
                "Synchronisation impossible : "
                f"{erreur}"
            )
            return

        calendrier_nom = (
            rendez_vous_final.get(
                "google_calendar_name"
            )
            or "Sur cet appareil uniquement"
        )

        self.resultat_label.text = (
            f"{message_action}\n"
            f"{rendez_vous_final.get('titre', 'Rendez-vous')} "
            f"le "
            f"{_date_affichee(rendez_vous_final.get('date'))} "
            f"à "
            f"{_heure_affichee(rendez_vous_final.get('heure'))} "
            f"dans « {calendrier_nom} »."
        )

        self._reinitialiser_formulaire()

        self.actualiser_liste_rendez_vous()
        self.actualiser_calendrier_google()

    # =========================================================
    # SUPPRESSION UI
    # =========================================================

    def supprimer_rendez_vous_ui(
        self,
        widget,
        rendez_vous,
        **kwargs,
    ):
        """Supprime le rendez-vous puis rafraîchit immédiatement l'agenda."""

        widget.enabled = False

        try:

            resultat = (
                self._supprimer_rendez_vous_lie(
                    rendez_vous
                )
            )

        except Exception as erreur:

            widget.enabled = True

            self.resultat_label.text = (
                "Suppression impossible : "
                f"{erreur}"
            )

            return

        rendez_vous_id = (
            rendez_vous.get(
                "id"
            )
        )

        if (
            self.rendez_vous_en_modification
            and self.rendez_vous_en_modification.get(
                "id"
            )
            == rendez_vous_id
        ):

            self._reinitialiser_formulaire()

        if resultat[
            "etait_lie"
        ]:

            self.resultat_label.text = (
                "Rendez-vous supprimé de "
                "Lumyn et Google Calendar ✅"
            )

        else:

            self.resultat_label.text = (
                "Ancien rendez-vous supprimé de Lumyn. "
                "Il n'avait pas d'identifiant Google lié."
            )

        # Mise à jour locale immédiate.
        self.actualiser_liste_rendez_vous()

        # Mise à jour immédiate du calendrier.
        # agenda_google.py connaît maintenant l'ID supprimé
        # et ne pourra plus le réafficher.
        self.actualiser_calendrier_google()

    # =========================================================
    # RÉINITIALISATION
    # =========================================================

    def _reinitialiser_formulaire(self):
        """Réinitialise le formulaire après une opération réussie."""

        self.resultat_courant = None
        self.rendez_vous_en_modification = None

        self.rdv_input.value = ""

        self.modifier_button.enabled = False
        self.confirmer_button.enabled = False

        self._selectionner_calendrier_defaut()


def creer_interface_rendez_vous():
    """Point d'entrée utilisé par app.py."""

    interface = InterfaceRendezVous()

    return interface.construire()
