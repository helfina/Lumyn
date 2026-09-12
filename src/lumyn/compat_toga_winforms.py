"""Correctif temporaire du shutdown Toga WinForms sous Python 3.13.

Toga WinForms 0.5.6 programme ses réveils asyncio avec
Task.Delay(...).ContinueWith(callback_python). Une continuation encore en
attente pendant la finalisation de pythonnet peut provoquer une access violation.

Ce correctif annule les délais à ApplicationExit et interdit l'exécution de leur
continuation lorsqu'ils ont été annulés.
"""

import sys
from importlib.metadata import PackageNotFoundError, version


_CORRECTIF_APPLIQUE = False


def appliquer_correctif_shutdown_toga_winforms():
    """Applique le correctif uniquement à l'environnement Windows concerné."""

    global _CORRECTIF_APPLIQUE

    if _CORRECTIF_APPLIQUE:
        return True

    if sys.platform != "win32":
        return False

    if sys.version_info < (3, 13):
        return False

    try:
        version_toga = version("toga-winforms")
    except PackageNotFoundError:
        return False

    if version_toga != "0.5.6":
        return False

    import clr

    from System import Action
    from System.Threading import CancellationTokenSource
    from System.Threading.Tasks import Task, TaskContinuationOptions
    from toga_winforms.libs.proactor import WinformsProactorEventLoop

    if getattr(
        WinformsProactorEventLoop,
        "_lumyn_shutdown_patch",
        False,
    ):
        _CORRECTIF_APPLIQUE = True
        return True

    initialisation_originale = WinformsProactorEventLoop.__init__
    sortie_originale = WinformsProactorEventLoop.winforms_application_exit

    def initialisation_corrigee(self):
        initialisation_originale(self)
        self._lumyn_tick_cancellation = CancellationTokenSource()

    def enqueue_tick_corrige(self, delay=5, tick=None):
        if not tick:
            tick = self.tick

        self.task = Action[Task](tick)

        Task.Delay(
            delay,
            self._lumyn_tick_cancellation.Token,
        ).ContinueWith(
            self.task,
            TaskContinuationOptions.OnlyOnRanToCompletion,
        )

    def sortie_corrigee(self, app, event):
        self._lumyn_tick_cancellation.Cancel()
        return sortie_originale(self, app, event)

    WinformsProactorEventLoop.__init__ = initialisation_corrigee
    WinformsProactorEventLoop.enqueue_tick = enqueue_tick_corrige
    WinformsProactorEventLoop.winforms_application_exit = sortie_corrigee
    WinformsProactorEventLoop._lumyn_shutdown_patch = True

    _CORRECTIF_APPLIQUE = True
    return True
