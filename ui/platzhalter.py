"""Platzhalter-Screens, bis die echten da sind (Arbeitsplan 6.1).

Das Gerüst aus 6.1 braucht etwas, zwischen dem es umschalten kann. Jeder
Platzhalter nennt die Aufgabe, die ihn ersetzt, und fliegt dort wieder
heraus.

Startbildschirm, Figurwahl (6.2), Story-Intro (6.3) und Handbuch (6.4) sind
schon die echten Screens. Die Platzhalter sind nur so weit ausgebaut, dass
sich das Gerüst durchklicken lässt:

* eine Übung stellen und mit der Musterlösung abschliessen – damit das
  Protokoll geschrieben wird,
* mitten in der Übung im Handbuch nachschlagen und zur selben Übung
  zurückkehren – so, wie es der Aufgaben-Screen in 6.5 übernimmt,
* ein Level vorzeitig beenden – damit man für den Weg bis zum Abschluss nicht
  eine Stunde warten muss.

Richtig gerechnet wird hier noch nichts; das kommt mit dem Aufgaben-Screen
in 6.5.
"""

import tkinter as tk

from ui import handbuch
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


class Uebung(Screen):
    """Stellt eine Übung – oder setzt mit ``fortsetzen`` die offene fort (nach dem Nachschlagen)."""

    titel = "Übung"

    def __init__(self, fenster, fortsetzen=False):
        super().__init__(fenster)
        self._fortsetzen = fortsetzen
        _ueberschrift(self, "Übung")
        _vermerk(self, "6.5")
        self._aufgabentext = tk.Label(self, anchor="w", justify="left")
        self._aufgabentext.pack(fill="x", pady=(self.px(ABSTAND), 0))
        erledigt = len(fenster.durchlauf.spielstand.erledigte_aufgaben)
        _text(self, f"Erledigte Aufgaben: {erledigt} – gespeichert in {fenster.durchlauf.protokoll.pfad}")
        _knopf(self, "Musterlösung eintragen", self._musterloesung)
        _knopf(self, "Im Handbuch nachschlagen", self._nachschlagen)
        _knopf(self, "Level vorzeitig beenden", self._level_beenden)

    def beim_anzeigen(self):
        stand = self.durchlauf.spielstand
        if self._fortsetzen and stand.aktuelle_aufgabe is not None:
            # Zurück vom Nachschlagen: dieselbe Aufgabe, ihre Uhr lief weiter.
            aufgabe = stand.aktuelle_aufgabe
        else:
            # Erst hier, nicht im Konstruktor: Mit dem Stellen beginnt die Uhr
            # der Aufgabe.
            aufgabe = self.durchlauf.naechste_uebung()
            if aufgabe is None:
                return  # Die Zeit war um – der Levelwechsel hat schon umgeschaltet.
        self._aufgabentext.config(
            text=f"{aufgabe.kennung}: {aufgabe.richtung} – {aufgabe.anzeigetext}"
        )

    def _musterloesung(self):
        stand = self.durchlauf.spielstand
        stand.versuchen(stand.aktuelle_aufgabe.loesung)
        self.durchlauf.aufgabe_abschliessen()
        self.fenster.zeige(Uebung)

    def _nachschlagen(self):
        handbuch.nachschlagen(self.fenster, self.durchlauf.spielstand.aktuelles_level,
                              zurueck=lambda fenster: fenster.zeige(Uebung, fortsetzen=True))

    def _level_beenden(self):
        self.durchlauf.naechstes_level()


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
