import lumyn.compat_toga_winforms as compat


def test_correctif_inactif_hors_windows(monkeypatch):
    monkeypatch.setattr(compat.sys, "platform", "linux")
    monkeypatch.setattr(compat, "_CORRECTIF_APPLIQUE", False)

    assert compat.appliquer_correctif_shutdown_toga_winforms() is False
    assert compat._CORRECTIF_APPLIQUE is False


def test_correctif_inactif_version_toga_non_validee(monkeypatch):
    monkeypatch.setattr(compat.sys, "platform", "win32")
    monkeypatch.setattr(compat.sys, "version_info", (3, 13, 0))
    monkeypatch.setattr(compat, "_CORRECTIF_APPLIQUE", False)
    monkeypatch.setattr(compat, "version", lambda paquet: "0.5.7")

    assert compat.appliquer_correctif_shutdown_toga_winforms() is False
    assert compat._CORRECTIF_APPLIQUE is False


def test_correctif_inactif_avant_python_313(monkeypatch):
    monkeypatch.setattr(compat.sys, "platform", "win32")
    monkeypatch.setattr(compat.sys, "version_info", (3, 12, 10))
    monkeypatch.setattr(compat, "_CORRECTIF_APPLIQUE", False)

    assert compat.appliquer_correctif_shutdown_toga_winforms() is False
    assert compat._CORRECTIF_APPLIQUE is False


def test_correctif_inactif_si_toga_winforms_absent(monkeypatch):
    monkeypatch.setattr(compat.sys, "platform", "win32")
    monkeypatch.setattr(compat.sys, "version_info", (3, 13, 0))
    monkeypatch.setattr(compat, "_CORRECTIF_APPLIQUE", False)

    def paquet_absent(nom):
        raise compat.PackageNotFoundError(nom)

    monkeypatch.setattr(compat, "version", paquet_absent)

    assert compat.appliquer_correctif_shutdown_toga_winforms() is False
    assert compat._CORRECTIF_APPLIQUE is False


def test_correctif_applique_et_annule_les_callbacks(monkeypatch):
    import sys
    import types

    monkeypatch.setattr(compat.sys, "platform", "win32")
    monkeypatch.setattr(compat.sys, "version_info", (3, 13, 0))
    monkeypatch.setattr(compat, "_CORRECTIF_APPLIQUE", False)
    monkeypatch.setattr(compat, "version", lambda paquet: "0.5.6")

    class FauxTokenSource:
        def __init__(self):
            self.Token = object()
            self.annule = False

        def Cancel(self):
            self.annule = True

    class FauxAction:
        def __class_getitem__(cls, item):
            return lambda callback: callback

    class FauxContinuationOptions:
        OnlyOnRanToCompletion = object()

    appels = []

    class FauxDelay:
        def ContinueWith(self, callback, option):
            appels.append((callback, option))

    class FauxTask:
        @staticmethod
        def Delay(delay, token):
            appels.append((delay, token))
            return FauxDelay()

    class FauxLoop:
        def __init__(self):
            self.sortie_originale_appelee = False

        def winforms_application_exit(self, app, event):
            self.sortie_originale_appelee = True

        def tick(self):
            pass

        def enqueue_tick(self, delay=5, tick=None):
            raise AssertionError("La méthode originale ne doit plus être utilisée")

    faux_clr = types.ModuleType("clr")

    faux_system = types.ModuleType("System")
    faux_system.Action = FauxAction

    faux_threading = types.ModuleType("System.Threading")
    faux_threading.CancellationTokenSource = FauxTokenSource

    faux_tasks = types.ModuleType("System.Threading.Tasks")
    faux_tasks.Task = FauxTask
    faux_tasks.TaskContinuationOptions = FauxContinuationOptions

    faux_toga = types.ModuleType("toga_winforms")
    faux_libs = types.ModuleType("toga_winforms.libs")
    faux_proactor = types.ModuleType("toga_winforms.libs.proactor")
    faux_proactor.WinformsProactorEventLoop = FauxLoop

    monkeypatch.setitem(sys.modules, "clr", faux_clr)
    monkeypatch.setitem(sys.modules, "System", faux_system)
    monkeypatch.setitem(sys.modules, "System.Threading", faux_threading)
    monkeypatch.setitem(sys.modules, "System.Threading.Tasks", faux_tasks)
    monkeypatch.setitem(sys.modules, "toga_winforms", faux_toga)
    monkeypatch.setitem(sys.modules, "toga_winforms.libs", faux_libs)
    monkeypatch.setitem(
        sys.modules,
        "toga_winforms.libs.proactor",
        faux_proactor,
    )

    assert compat.appliquer_correctif_shutdown_toga_winforms() is True

    boucle = FauxLoop()

    assert hasattr(boucle, "_lumyn_tick_cancellation")

    boucle.enqueue_tick(delay=123, tick=boucle.tick)

    assert appels[0] == (
        123,
        boucle._lumyn_tick_cancellation.Token,
    )
    assert appels[1][1] is FauxContinuationOptions.OnlyOnRanToCompletion

    boucle.winforms_application_exit(None, None)

    assert boucle._lumyn_tick_cancellation.annule is True
    assert boucle.sortie_originale_appelee is True


def test_correctif_deja_applique_est_idempotent(monkeypatch):
    monkeypatch.setattr(compat, "_CORRECTIF_APPLIQUE", True)

    assert compat.appliquer_correctif_shutdown_toga_winforms() is True


def test_main_applique_correctif_avant_creation_app(monkeypatch):
    import lumyn.app as app

    appels = []

    def faux_correctif():
        appels.append("correctif")

    class FauxLumyn:
        def __init__(self):
            appels.append("lumyn")

    monkeypatch.setattr(
        app,
        "appliquer_correctif_shutdown_toga_winforms",
        faux_correctif,
    )
    monkeypatch.setattr(app, "Lumyn", FauxLumyn)

    resultat = app.main()

    assert isinstance(resultat, FauxLumyn)
    assert appels == ["correctif", "lumyn"]
