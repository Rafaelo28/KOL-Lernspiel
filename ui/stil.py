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

#: Grösse der Erzähltexte über einer Szene (Story-Intro).
ERZAEHLGROESSE = 14

#: Name der Erzählschrift, ebenfalls aus :func:`schriften_einrichten`.
SCHRIFT_ERZAEHLUNG = "Erzaehlung"

#: Name der fetten Schrift in Grundgrösse – für Namen und Initialen in der
#: Figurwahl. Ebenfalls aus :func:`schriften_einrichten`.
SCHRIFT_FETT = "Fett"

#: Farbe der Meldungszeile – für Probleme, die die Lehrkraft sehen muss.
FARBE_MELDUNG = "#9a1c1c"

#: Farbe der Trennlinie unter der Kopfzeile.
FARBE_LINIE = "#b0b0b0"

#: Innenabstand in Pixeln – um die Screens und in der Kopfzeile.
ABSTAND = 16

# Farben der Story-Szenen – dieselben wie in der Wüstenszene (grafik/wrack.svg):
#: Nachthimmel, der Grund um eine Szene.
FARBE_NACHT = "#11132a"
#: Sand – Erzähltext auf dem Nachthimmel.
FARBE_SAND = "#ecd8b4"
#: Dunkler Sand – leise Beschriftungen.
FARBE_DUENE = "#a98567"
#: Schatten unter dem Erzähltext, damit er auch vor Sternen lesbar bleibt.
FARBE_SCHATTEN = "#05060f"

# Farben der Figurwahl:
#: Grund der Karten in der Figurwahl. Die Rollen-Symbole (grafik/figur_*.svg)
#: sind auf genau diese Farbe gemalt – wer sie ändert, muss dort mitziehen.
FARBE_KARTE = "#1a1d3a"
#: Rand einer Karte, die gerade nicht gewählt ist.
FARBE_KARTENRAND = "#363d7a"
#: Rand einer Karte unter dem Mauszeiger.
FARBE_KARTENRAND_HELL = "#7078c0"
#: Gold – die gewählte Karte und die Initialen.
FARBE_GOLD = "#e2b651"


def schriften_einrichten(wurzel):
    """Stellt die Grundschriften ein und legt die benannten Schriften an.

    Rückgabe sind die Schriftobjekte. Wer sie aufbewahrt, behält die Schriften:
    Tkinter löscht eine benannte Schrift, sobald ihr Objekt verschwindet.
    """
    for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont"):
        tkfont.nametofont(name, root=wurzel).configure(size=SCHRIFTGROESSE)
    familie = tkfont.nametofont("TkDefaultFont", root=wurzel).actual("family")
    return (
        tkfont.Font(root=wurzel, name=SCHRIFT_TITEL, family=familie, size=TITELGROESSE, weight="bold"),
        tkfont.Font(root=wurzel, name=SCHRIFT_ERZAEHLUNG, family=familie, size=ERZAEHLGROESSE),
        tkfont.Font(root=wurzel, name=SCHRIFT_FETT, family=familie, size=SCHRIFTGROESSE, weight="bold"),
    )
