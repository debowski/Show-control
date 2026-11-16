"""Nowe okno główne aplikacji zgodne z fazą 5 refaktoru."""

from __future__ import annotations

import sys

from showcontrol.app import App
from showcontrol.bootstrap import create_application


class MainWindow(App):
    """Alias klasy okna dla nowej struktury modułowej."""


def main(argv=None):
    args = sys.argv if argv is None else argv
    app, settings = create_application(args)
    window = MainWindow(settings)
    window.show()
    sys.exit(app.exec())
