"""Die Zeitfenster der Level (Arbeitsplan 5.2).

15, 10 und 25 Minuten – dieselben Zeiten wie bei der Frontalunterrichts-Gruppe
(Anhang A4). Sie sind der Kern des Versuchsaufbaus: Wären die Fenster nicht
gleich lang, liesse sich am Ende nicht sagen, ob eine Gruppe mehr gelernt hat
oder nur mehr Zeit hatte.

Warum Level 2 das kürzeste ist
──────────────────────────────
Geplant waren 15/20/25 – von Level zu Level mehr, weil die Verfahren
aufwendiger werden. Für Level 2 stimmt das nicht, und der Pilotdurchlauf hat
es gezeigt: Die Substitution ist das **schnellste** Verfahren, weil man nur
in einer Tabelle nachschlägt, statt zu rechnen. Je Übung brauchten die fünf
Testpersonen im Median 67 Sekunden – bei Caesar 130, bei Vigenère 298. Der
Pflichtteil des Levels (zwei Übungen und der abgefangene Funkspruch) war nach
3,9 bis 7,7 Minuten erledigt; die restlichen zwölf bis sechzehn Minuten
füllten Zusatzaufgaben, bis zu sechzehn Substitutionsübungen hintereinander.
Zwei Testpersonen nannten genau das "viel zu lang" beziehungsweise
langweilig.

Zehn Minuten decken den Pflichtteil der langsamsten Pilotperson (7,7 Minuten)
und den Aufschlag dafür, dass der Funkspruch jetzt ohne das lange Warmlaufen
kommt (:mod:`game.levelablauf`). Wer trotzdem nicht fertig wird, verliert die
Geschichte nicht: Der Funkspruch steht nach dem Levelwechsel zum Mitlesen da
(Projektregel 1). Die drei Level zusammen sind damit 50 statt 60 Minuten
lang; die Kontrollgruppe bekommt dieselbe Kürzung, sonst wäre der Vergleich
hin.

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
#: den Vergleich mit der Kontrollgruppe – und muss deren Stundenplan
#: mitändern. Level 2 ist seit dem Pilotdurchlauf das kürzeste (siehe oben).
DAUER_JE_LEVEL_MINUTEN = {1: 15, 2: 10, 3: 25}

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
        """Startet die Uhr – ab jetzt läuft die Zeit dieses Levels.

        ``dauer_sekunden`` steht danach fest; verlängern lässt sich ein
        Zeitfenster nicht (Projektregel 1). ``zeitgeber`` ist die Funktion,
        die die Uhrzeit liefert – ohne Angabe die Systemuhr, in Tests eine
        Attrappe wie im Beispiel oben.
        """
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

        >>> Zeitfenster(61, zeitgeber=lambda: 0).restzeit_text
        '01:01'
        """
        return als_text(self.verbleibende_sekunden)

    def __repr__(self):
        """Kurzfassung für die Fehlersuche – so erscheint das Objekt in Meldungen und im Debugger."""
        return (
            f"Zeitfenster({self.dauer_sekunden:.0f}s, "
            f"rest={self.restzeit_text}, abgelaufen={self.ist_abgelaufen})"
        )


def als_text(sekunden):
    """Sekunden als "MM:SS" für die Anzeige.

    Aufgerundet: Solange auch nur eine Sekunde übrig ist, steht dort nicht
    "00:00". Sonst zeigte die Anzeige das Ende an, während noch Zeit war.

    >>> als_text(61), als_text(0.2), als_text(0)
    ('01:01', '00:01', '00:00')
    """
    ganze = math.ceil(sekunden)
    return f"{ganze // 60:02d}:{ganze % 60:02d}"


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
