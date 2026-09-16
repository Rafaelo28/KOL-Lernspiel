"""Platzhalter-Screens, bis die echten da sind (Arbeitsplan 6.1).

Das Gerüst aus 6.1 braucht etwas, zwischen dem es umschalten kann. Jeder
Platzhalter nennt die Aufgabe, die ihn ersetzt, und fliegt dort wieder
heraus.

Startbildschirm, Figurwahl (6.2), Story-Intro (6.3), Handbuch (6.4) und die
Übungen (6.5) sind schon die echten Screens. Übrig ist der Abschluss: Er
nennt nur, wo die Messdaten stehen, und lässt das Fenster schliessen – der
richtige Schluss-Screen entsteht in 6.8.
"""

import tkinter as tk

from ui.screen import Screen
from ui.stil import ABSTAND, SCHRIFT_TITEL


def _ueberschrift(screen, text):
    tk.Label(screen, text=text, font=SCHRIFT_TITEL, anchor="w").pack(fill="x")


def _text(screen, text):
    tk.Label(screen, text=text, anchor="w", justify="left", wraplength=screen.px(700)).pack(
        fill="x", pady=(screen.px(ABSTAND // 2), 0)
    )


def _vermerk(screen, aufgabe):
    """Die Zeile, die zeigt, dass hier noch ein Platzhalter steht."""
    _text(screen, f"(Platzhalter – der richtige Screen entsteht in Aufgabe {aufgabe}.)")


def _knopf(screen, text, befehl):
    tk.Button(screen, text=text, command=befehl).pack(anchor="w", pady=(screen.px(ABSTAND), 0))


class Abschluss(Screen):
    titel = "Geschafft"

    def __init__(self, fenster, durch_zeitablauf=False):
        super().__init__(fenster)
        _ueberschrift(self, "Hilfe ist unterwegs")
        _vermerk(self, "6.8")
        if durch_zeitablauf:
            _text(self, "Die Zeit für Level 3 ist abgelaufen.")
        _text(self, f"Die Messdaten stehen in {fenster.durchlauf.protokoll.pfad}")
        _knopf(self, "Spiel beenden", fenster.schliessen)
