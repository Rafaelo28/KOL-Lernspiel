"""Platzhalter-Screens, bis die echten da sind (Arbeitsplan 6.1).

Das Gerüst aus 6.1 braucht etwas, zwischen dem es umschalten kann. Jeder
Platzhalter nennt die Aufgabe, die ihn ersetzt, und fliegt dort wieder
heraus.

Sie sind nur so weit ausgebaut, dass sich das Gerüst durchklicken lässt:

* eine Figur wählen – damit ein Durchlauf entsteht,
* nach dem Story-Intro (schon der echte Screen aus 6.3, :mod:`ui.intro`)
  Level 1 beginnen – damit die Uhr läuft,
* eine Übung stellen und mit der Musterlösung abschliessen – damit das
  Protokoll geschrieben wird,
* ein Level vorzeitig beenden – damit man für den Weg bis zum Abschluss nicht
  eine Stunde warten muss.

Richtig gerechnet wird hier noch nichts; das kommt mit dem Aufgaben-Screen
in 6.5.
"""

import tkinter as tk

from content import charaktere, verfahren
from ui import intro
from ui.screen import Screen
from ui.stil import ABSTAND, SCHRIFT_TITEL


def _ueberschrift(screen, text):
    tk.Label(screen, text=text, font=SCHRIFT_TITEL, anchor="w").pack(fill="x")


def _text(screen, text):
    tk.Label(screen, text=text, anchor="w", justify="left", wraplength=700).pack(
        fill="x", pady=(ABSTAND // 2, 0)
    )


def _vermerk(screen, aufgabe):
    """Die Zeile, die zeigt, dass hier noch ein Platzhalter steht."""
    _text(screen, f"(Platzhalter – der richtige Screen entsteht in Aufgabe {aufgabe}.)")


def _knopf(screen, text, befehl):
    tk.Button(screen, text=text, command=befehl).pack(anchor="w", pady=(ABSTAND, 0))


class Start(Screen):
    titel = "Der Diamantenraub"

    def __init__(self, fenster):
        super().__init__(fenster)
        _ueberschrift(self, "Der Diamantenraub")
        _vermerk(self, "6.2")
        _knopf(self, "Spiel starten", lambda: fenster.zeige(Figurwahl))


class Figurwahl(Screen):
    titel = "Wähle deine Figur"

    def __init__(self, fenster):
        super().__init__(fenster)
        _ueberschrift(self, "Wer bist du?")
        _vermerk(self, "6.2")
        for figur in charaktere.SPIELBARE_CHARAKTERE:
            _knopf(self, f"{figur.name} – {figur.rolle}", lambda f=figur: self._waehlen(f))

    def _waehlen(self, figur):
        self.fenster.starte_durchlauf(figur)
        self.fenster.zeige(intro.Intro, danach=level_1_beginnen)


def level_1_beginnen(fenster):
    """Nach dem Intro: Level 1 beginnt, ab jetzt läuft die Uhr."""
    fenster.durchlauf.starte_level()
    fenster.zeige(Handbuch, level=fenster.durchlauf.spielstand.aktuelles_level)


class Handbuch(Screen):
    def __init__(self, fenster, level, hinweis=""):
        super().__init__(fenster)
        self.titel = f"Handbuch – Level {level}"
        _ueberschrift(self, verfahren.BEZEICHNUNG[verfahren.VERFAHREN_NACH_LEVEL[level]])
        if hinweis:
            _text(self, hinweis)
        _vermerk(self, "6.4")
        _knopf(self, "Zu den Übungen", lambda: fenster.zeige(Uebung))


class Uebung(Screen):
    titel = "Übung"

    def __init__(self, fenster):
        super().__init__(fenster)
        _ueberschrift(self, "Übung")
        _vermerk(self, "6.5")
        self._aufgabentext = tk.Label(self, anchor="w", justify="left")
        self._aufgabentext.pack(fill="x", pady=(ABSTAND, 0))
        erledigt = len(fenster.durchlauf.spielstand.erledigte_aufgaben)
        _text(self, f"Erledigte Aufgaben: {erledigt} – gespeichert in {fenster.durchlauf.protokoll.pfad}")
        _knopf(self, "Musterlösung eintragen", self._musterloesung)
        _knopf(self, "Level vorzeitig beenden", self._level_beenden)

    def beim_anzeigen(self):
        # Erst hier, nicht im Konstruktor: Mit dem Stellen beginnt die Uhr der
        # Aufgabe.
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
