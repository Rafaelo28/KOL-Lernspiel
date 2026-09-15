"""Gemeinsame Hilfen für die Oberflächen-Tests."""

import re

import pytest


def ereignis_ausloesen(widget, sequenz, x_root=0, y_root=0, zeichen=""):
    """Ruft die Bindung ``sequenz`` von ``widget`` so auf, wie Tk es täte.

    In einem versteckten Fenster (``withdraw``) lassen sich Mausklicks und
    Tasten nicht mit ``event_generate`` auslösen – Tk stellt sie nur sichtbaren
    Fenstern zu. Tkinter legt aber für jede Bindung einen Tcl-Befehl an und
    trägt ihn mit den Platzhaltern der Ereignisfelder ein (``%x``, ``%W`` …).
    Hier wird genau dieser Befehl mit passenden Werten aufgerufen – derselbe
    Weg, den ein echter Klick nähme, nur ohne die Zustellung durch Tk.

    ``zeichen`` ist bei Tastenereignissen das getippte Zeichen. Tks eigene
    Bindung (etwa die, die das Zeichen ins Feld schreibt) läuft dabei nicht mit
    – die muss ein Test selbst nachstellen.
    """
    import tkinter as tk

    skript = widget.bind(sequenz)
    treffer = re.search(r"\[(\S+) %#", skript)
    assert treffer, f"{widget} hat keine Bindung für {sequenz}"
    felder = {"%#": "0", "%b": "1", "%f": "0", "%h": "0", "%k": "0", "%s": "0", "%t": "0", "%w": "0",
              "%x": "5", "%y": "5", "%A": zeichen, "%E": "0", "%K": zeichen, "%N": "0", "%W": str(widget),
              "%T": "4", "%X": str(x_root), "%Y": str(y_root), "%D": "0"}
    return widget.tk.call(treffer.group(1), *(felder[feld] for feld in tk.Misc._subst_format))


@pytest.fixture
def ausloesen():
    """Die Funktion :func:`ereignis_ausloesen` – als Fixture, weil tests/ kein Paket ist."""
    return ereignis_ausloesen


@pytest.fixture
def massstab():
    """Der Maßstab der Fenster in den Tests – fest 1, damit sie auf jedem Bildschirm gleich laufen.

    Ohne Vorgabe richtete sich das Spiel nach dem Bildschirm, auf dem die Tests
    gerade laufen. Ein Test, der den grossen Maßstab braucht, überschreibt die
    Fixture mit ``@pytest.mark.parametrize("massstab", [1, 1.5])``.
    """
    return 1


@pytest.fixture
def platz(massstab):
    """So viel Platz hat das Fenster im jeweiligen Maßstab: (Breite, Höhe).

    Im kleinen die Standardgrösse, im grossen ein maximiertes Fenster auf einem
    1080p-Schulmonitor: 1080 Pixel Höhe abzüglich Titelleiste und Taskleiste
    lassen unter Windows 11 rund 1000. Verlangt werden 20 Pixel weniger – als
    Luft, weil Schriften unter Windows etwas anders ausfallen als hier.
    """
    return (1000, 700) if massstab == 1 else (1920, 980)
