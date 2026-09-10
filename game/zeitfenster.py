"""Die Zeitfenster der Level (Arbeitsplan 5.2).

15, 20 und 25 Minuten – dieselben Zeiten wie bei der Frontalunterrichts-Gruppe
(Anhang A4). Sie sind der Kern des Versuchsaufbaus: Wären die Fenster nicht
gleich lang, liesse sich am Ende nicht sagen, ob eine Gruppe mehr gelernt hat
oder nur mehr Zeit hatte.

Warum die Uhr von aussen kommt
──────────────────────────────
:class:`Zeitfenster` bekommt einen ``zeitgeber`` übergeben – eine Funktion, die
Sekunden liefert. Im Spiel ist das ``time.monotonic``; in Tests eine Attrappe,
die man vorstellen kann. Ohne das liessen sich fünfzehn Minuten nur durch
fünfzehn Minuten Warten prüfen.

Warum ``time.monotonic`` und nicht ``time.time``
────────────────────────────────────────────────
``time.time`` kann springen: Ein Schulrechner gleicht seine Uhr per Zeitserver
ab, oder die Sommerzeit wechselt. Ein Sprung nach vorn würde ein Zeitfenster
mitten im Level beenden, ein Sprung zurück es verlängern – und in beiden
Fällen wären die Messdaten dieses Durchlaufs wertlos. ``time.monotonic``
läuft gleichmässig weiter und kennt keine Sprünge.

Was das Zeitfenster **nicht** tut
─────────────────────────────────
Es hält nie an. Projektregel 1: Zusatzaufgaben verlängern ein Fenster nie, und
die Erzählzeit im Weiterrechnen-Knopf ("zwanzig Minuten später …") ist reine
Fiktion. Es gibt deshalb bewusst kein ``anhalten()``.
"""

import math
import time

#: Die Zeitfenster in Minuten. Diese Zahlen sind **keine Einstellung**,
#: sondern Teil des Versuchsaufbaus (Projektregel 1). Wer sie ändert, ändert
#: den Vergleich mit der Kontrollgruppe.
DAUER_JE_LEVEL_MINUTEN = {1: 15, 2: 20, 3: 25}

#: Dieselben Zeiten in Sekunden – damit rechnet der Code.
DAUER_JE_LEVEL_SEKUNDEN = {
    level: minuten * 60 for level, minuten in DAUER_JE_LEVEL_MINUTEN.items()
}


class Zeitfenster:
    """Ein laufendes Zeitfenster.

    >>> uhr = [0.0]                      # eine Attrappe statt einer echten Uhr
    >>> fenster = Zeitfenster(900, zeitgeber=lambda: uhr[0])
    >>> fenster.restzeit_text, fenster.ist_abgelaufen
    ('15:00', False)
    >>> uhr[0] = 60.5
    >>> fenster.restzeit_text
    '14:00'
    >>> uhr[0] = 900.0
    >>> fenster.restzeit_text, fenster.ist_abgelaufen
    ('00:00', True)

    Über die Zeit hinaus wird nicht ins Minus gezählt:

    >>> uhr[0] = 5000.0
    >>> fenster.verbleibende_sekunden
    0.0
    """

    def __init__(self, dauer_sekunden, zeitgeber=None):
        if isinstance(dauer_sekunden, bool) or not isinstance(
            dauer_sekunden, (int, float)
        ):
            raise TypeError(
                "Die Dauer muss eine Zahl in Sekunden sein, nicht "
                f"{type(dauer_sekunden).__name__}."
            )
        if dauer_sekunden <= 0:
            raise ValueError(
                f"Die Dauer muss grösser als null sein, ist aber {dauer_sekunden}."
            )
        self._zeitgeber = zeitgeber if zeitgeber is not None else time.monotonic
        self.dauer_sekunden = float(dauer_sekunden)
        self._start = self._zeitgeber()

    @property
    def verstrichene_sekunden(self):
        """Wie lange das Fenster schon läuft."""
        return max(0.0, self._zeitgeber() - self._start)

    @property
    def verbleibende_sekunden(self):
        """Wie viel Zeit noch bleibt – nie weniger als null."""
        return max(0.0, self.dauer_sekunden - self.verstrichene_sekunden)

    @property
    def ist_abgelaufen(self):
        """Ist die Zeit um?"""
        return self.verbleibende_sekunden <= 0

    @property
    def anteil_verbraucht(self):
        """Wie viel des Fensters verbraucht ist, als Zahl zwischen 0 und 1.

        Gedacht für einen Fortschrittsbalken in Phase 6.
        """
        return min(1.0, self.verstrichene_sekunden / self.dauer_sekunden)

    @property
    def restzeit_text(self):
        """Die Restzeit als "MM:SS" für die Anzeige.

        Aufgerundet: Solange auch nur eine Sekunde übrig ist, steht dort nicht
        "00:00". Sonst zeigte die Anzeige das Ende an, während noch Zeit war.

        >>> Zeitfenster(61, zeitgeber=lambda: 0).restzeit_text
        '01:01'
        """
        sekunden = math.ceil(self.verbleibende_sekunden)
        return f"{sekunden // 60:02d}:{sekunden % 60:02d}"

    def __repr__(self):
        return (
            f"Zeitfenster({self.dauer_sekunden:.0f}s, "
            f"rest={self.restzeit_text}, abgelaufen={self.ist_abgelaufen})"
        )


def fuer_level(level, zeitgeber=None):
    """Baut das Zeitfenster eines Levels.

    >>> fuer_level(2, zeitgeber=lambda: 0).restzeit_text
    '20:00'
    """
    if level not in DAUER_JE_LEVEL_SEKUNDEN:
        raise ValueError(
            f"Level {level!r} gibt es nicht; erlaubt sind "
            f"{sorted(DAUER_JE_LEVEL_SEKUNDEN)}."
        )
    return Zeitfenster(DAUER_JE_LEVEL_SEKUNDEN[level], zeitgeber=zeitgeber)
