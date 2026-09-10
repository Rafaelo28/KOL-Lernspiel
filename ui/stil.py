"""Schriften, Farben und Abstände der Oberfläche – an einer Stelle (Arbeitsplan 6.1).

Die Screens nennen Schriften beim Namen (``font=SCHRIFT_TITEL``), statt Grösse
und Familie jedes Mal neu anzugeben. So lässt sich nach dem ersten Test auf
einem Schulmonitor alles mit einem Handgriff grösser stellen – Arbeitsplan 6.7
verlangt ausdrücklich, dass es dort lesbar bleibt.
"""

from tkinter import font as tkfont

#: Grundgrösse aller Texte in Punkt. Auf Schulmonitoren lieber zu gross als
#: zu klein.
SCHRIFTGROESSE = 12

#: Grösse der Überschriften in Punkt.
TITELGROESSE = 18

#: Name der Überschriftenschrift. Angelegt wird sie in :func:`schriften_einrichten`.
SCHRIFT_TITEL = "Titel"

#: Farbe der Meldungszeile – für Probleme, die die Lehrkraft sehen muss.
FARBE_MELDUNG = "#9a1c1c"

#: Farbe der Trennlinie unter der Kopfzeile.
FARBE_LINIE = "#b0b0b0"

#: Innenabstand in Pixeln – um die Screens und in der Kopfzeile.
ABSTAND = 16


def schriften_einrichten(wurzel):
    """Stellt die Grundschriften ein und legt die Überschriftenschrift an.

    Rückgabe ist das Schriftobjekt der Überschrift. Wer es aufbewahrt, behält
    die Schrift: Tkinter löscht eine benannte Schrift, sobald ihr Objekt
    verschwindet.
    """
    for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont"):
        tkfont.nametofont(name, root=wurzel).configure(size=SCHRIFTGROESSE)
    familie = tkfont.nametofont("TkDefaultFont", root=wurzel).actual("family")
    return tkfont.Font(
        root=wurzel, name=SCHRIFT_TITEL, family=familie, size=TITELGROESSE, weight="bold"
    )
