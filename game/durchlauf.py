"""Ein Durchlauf: Spielstand und Protokoll in einer Hand (Arbeitsplan 6.1).

Der Spielstand kennt keine Dateien, das Protokoll kein Spiel. Irgendwer muss
nach jeder Aufgabe speichern, im Takt die Zeit prüfen und den Fehler
abfangen, der kommt, wenn eine Aufgabe zu spät gestellt wird. Stünde das in
der Oberfläche, stünde es in jedem Screen – und irgendeiner vergässe es. Dann
fehlten Zeilen im Log, ohne dass es jemand merkt.

Hier steht es einmal, ohne Tkinter, und lässt sich deshalb ohne Bildschirm
testen.

Die Tür für die Oberfläche
──────────────────────────
Alles, was eine Aufgabe **stellt**, **abschliesst** oder ein **Level
wechselt**, geht über den Durchlauf. Lesen und Eingaben prüfen geht direkt am
Spielstand (``durchlauf.spielstand.versuchen(...)``) – dabei ändert sich
nichts, was gespeichert werden müsste.

Wann gespeichert wird
─────────────────────
Beim Start des ersten Levels, nach jeder abgeschlossenen Aufgabe, nach jedem
Levelwechsel und beim Beenden – so, wie es Arbeitsplan 5.5 verlangt. Das
erste Speichern gleich zu Beginn hat einen Nebeneffekt, der gewollt ist: Ist
der Log-Ordner nicht beschreibbar, zeigt sich das nach Sekunden und nicht
erst nach der ersten Viertelstunde.

Scheitert das Schreiben (etwa weil die Datei unter Windows in Excel offen
ist), wird der Fehler nicht verschluckt: :attr:`Durchlauf.speicherhinweis`
sagt, was los ist, und ``bei_speicherproblem`` meldet es der Oberfläche. Beim
nächsten Speichern wird es erneut versucht; weil jedes Mal alles geschrieben
wird, geht dabei nichts verloren.

Levelwechsel
────────────
Ein Level endet auf zwei Wegen: am Timer (:meth:`Durchlauf.takt`) oder weil
die Geschichte weitergeht (:meth:`Durchlauf.naechstes_level`). Beide melden
sich über ``bei_levelwechsel`` mit einem :class:`Levelwechsel`. So entscheidet
genau eine Stelle der Oberfläche, was nach einem Level kommt – nicht jeder
Screen für sich.
"""

from typing import NamedTuple

from game.protokoll import Protokoll
from game.spielstand import LEVEL, LEVELENDE_ZEITABLAUF, Spielstand, ZeitIstUm


class Levelwechsel(NamedTuple):
    """Ein Level ist zu Ende.

    ``altes_level``      das Level, das eben endete
    ``neues_level``      das nächste – ``None``, wenn das Spiel vorbei ist
    ``durch_zeitablauf`` endete es am Timer? Sonst ging die Geschichte weiter.

    >>> Levelwechsel(3, None, False).spielende
    True
    """

    altes_level: int
    neues_level: int | None
    durch_zeitablauf: bool

    @property
    def spielende(self):
        """War das das letzte Level?"""
        return self.neues_level is None


def _nichts(*_):
    """Voreinstellung für Rückrufe, die niemand angemeldet hat."""


class Durchlauf:
    """Spielstand und Protokoll eines Durchlaufs.

    ``bei_levelwechsel(levelwechsel)`` wird nach jedem Levelwechsel gerufen,
    ``bei_speicherproblem(text)`` mit dem Hinweis, wenn das Speichern scheitert,
    und mit ``""``, sobald es wieder klappt.
    """

    def __init__(self, spielstand, protokoll, bei_levelwechsel=None, bei_speicherproblem=None):
        self.spielstand = spielstand
        self.protokoll = protokoll
        self.bei_levelwechsel = bei_levelwechsel or _nichts
        self.bei_speicherproblem = bei_speicherproblem or _nichts
        self._speicherfehler = None

    @classmethod
    def neu(cls, figur, pseudonym=None, zeitgeber=None, protokollordner=None, **rueckrufe):
        """Beginnt einen Durchlauf für die gewählte Figur."""
        spielstand = Spielstand(figur, pseudonym=pseudonym, zeitgeber=zeitgeber)
        protokoll = Protokoll(spielstand, ordner=protokollordner)
        return cls(spielstand, protokoll, **rueckrufe)

    # ── Level ──────────────────────────────────────────────────────────────

    def starte_level(self, level=LEVEL[0]):
        """Beginnt den Durchlauf mit diesem Level – ab hier läuft die Uhr."""
        self.spielstand.starte_level(level)
        self.sichern()

    def takt(self):
        """Prüft das Zeitfenster. Die Oberfläche ruft das mindestens einmal pro
        Sekunde auf.

        Rückgabe ist der :class:`Levelwechsel`, wenn die Zeit um war, sonst
        ``None``.
        """
        altes_level = self.spielstand.aktuelles_level
        if not self.spielstand.pruefe_zeitfenster():
            return None
        return self._nach_levelwechsel(altes_level)

    def naechstes_level(self):
        """Beendet das laufende Level, weil die Geschichte weitergeht."""
        altes_level = self.spielstand.aktuelles_level
        self.spielstand.naechstes_level()
        return self._nach_levelwechsel(altes_level)

    def _nach_levelwechsel(self, altes_level):
        wechsel = Levelwechsel(
            altes_level=altes_level,
            neues_level=self.spielstand.aktuelles_level,
            # Aus dem Spielstand und nicht aus dem Weg, auf dem es hierher
            # ging: Ruft die Oberfläche naechstes_level() erst, als die Zeit
            # schon um war, steht im Log "zeitablauf" – dann hier auch.
            durch_zeitablauf=self.spielstand.levelende(altes_level) == LEVELENDE_ZEITABLAUF,
        )
        self.sichern()
        self.bei_levelwechsel(wechsel)
        return wechsel

    # ── Aufgaben ───────────────────────────────────────────────────────────

    def naechste_uebung(self, zusatzaufgabe=False):
        """Stellt die nächste Übung – oder gibt ``None`` zurück, wenn die Zeit
        schon um war.

        Dann ist der Levelwechsel bereits geschehen und gemeldet. Der Screen,
        der gefragt hat, ist womöglich schon abgerissen und darf danach nichts
        mehr anfassen.
        """
        try:
            return self.spielstand.naechste_uebung(zusatzaufgabe=zusatzaufgabe)
        except ZeitIstUm:
            self.takt()
            return None

    def stelle_funkspruch(self, funkspruch):
        """Stellt einen Funkspruch – ``None`` wie bei :meth:`naechste_uebung`."""
        try:
            return self.spielstand.stelle_funkspruch(funkspruch)
        except ZeitIstUm:
            self.takt()
            return None

    def aufgabe_abschliessen(self):
        """Legt die laufende Aufgabe zu den erledigten und speichert."""
        self.spielstand.aufgabe_abschliessen()
        self.sichern()

    def beenden(self):
        """Für das Schliessen des Fensters: ein letztes Mal speichern.

        Eine Aufgabe, die gerade läuft, wird vorher als abgebrochen
        festgehalten. Sonst fehlte im Log genau die Stelle, an der jemand
        aufgehört hat.

        Hat noch kein Level begonnen, gibt es nichts zu speichern – es
        entsteht dann auch keine Datei. Sonst hinterliesse jedes Fenster, das
        vor dem ersten Level geschlossen wird, eine leere Tabelle im Log-Ordner.

        Rückgabe wie bei :meth:`sichern`.
        """
        if not self.hat_begonnen:
            return True
        if self.spielstand.aktuelle_bearbeitung is not None:
            self.spielstand.aufgabe_abschliessen()
        return self.sichern()

    @property
    def hat_begonnen(self):
        """Hat schon ein Level begonnen? Abgelesen am Spielstand, nicht mitgezählt."""
        return any(self.spielstand.levelende(level) is not None for level in LEVEL)

    # ── Speichern ──────────────────────────────────────────────────────────

    def sichern(self):
        """Schreibt das Protokoll. Rückgabe ``True``, wenn es geklappt hat."""
        try:
            self.protokoll.schreiben()
        except OSError as fehler:
            self._speicherfehler = fehler
            self.bei_speicherproblem(self.speicherhinweis)
            return False
        if self._speicherfehler is not None:
            self._speicherfehler = None
            self.bei_speicherproblem("")
        return True

    @property
    def speicherfehler(self):
        """Der Fehler beim letzten Speichern, oder ``None``, wenn es klappte."""
        return self._speicherfehler

    @property
    def speicherhinweis(self):
        """Was die Oberfläche anzeigt, solange das Speichern scheitert."""
        if self._speicherfehler is None:
            return ""
        grund = self._speicherfehler.strerror or str(self._speicherfehler)
        return (
            f"Die Messdaten konnten nicht gespeichert werden ({grund}). Ist die "
            f"Datei {self.protokoll.dateiname} gerade in einem anderen Programm "
            "geöffnet, etwa in Excel?"
        )

    def __repr__(self):
        return f"Durchlauf({self.spielstand!r}, datei={self.protokoll.dateiname!r})"
