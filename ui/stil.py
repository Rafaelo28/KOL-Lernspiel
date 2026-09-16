"""Schriften, Farben und Abstände der Oberfläche – an einer Stelle (Arbeitsplan 6.1).

Die Screens nennen Schriften beim Namen (``font=SCHRIFT_TITEL``), statt Grösse
und Familie jedes Mal neu anzugeben. So lässt sich nach dem ersten Test auf
einem Schulmonitor alles mit einem Handgriff grösser stellen – Arbeitsplan 6.7
verlangt ausdrücklich, dass es dort lesbar bleibt.

Der Maßstab
───────────
Alle Grössen hier gelten für ein Fenster von 1000 × 700 Pixeln. Auf einem
1080p-Schulmonitor (1920 × 1080) stünde das Spiel darin klein oben in der
Mitte. Dort wird deshalb alles 1,5-mal so gross gezeichnet: Schriften,
Abstände und die vorgerenderten Bilder, für die es einen eigenen, schärferen
Satz gibt (siehe ``grafik/rendern.py``). Welcher Maßstab gilt, entscheidet
:func:`massstab_fuer` einmal beim Start nach der Bildschirmgrösse; die Screens
rechnen ihre Pixelangaben mit ``self.px(…)`` um.

Warum nicht jede beliebige Grösse: Die Bilder gibt es nur in den Maßstäben aus
:data:`MASSSTAEBE`. Tkinter kann ein fertiges Bild nur um ganze Faktoren
vergrössern, und das sähe grob aus.
"""

from tkinter import font as tkfont

#: Die Maßstäbe, in denen das Spiel gezeichnet werden kann. Für jeden gibt es
#: einen Satz vorgerenderter Bilder; muss zu MASSSTAEBE in grafik/rendern.py
#: passen – ein Test prüft das.
MASSSTAEBE = (1, 1.5)

#: Ab dieser Bildschirmgrösse (Breite, Höhe) wird alles 1,5-mal so gross
#: gezeichnet. Ein 1080p-Schulmonitor liegt genau darauf, ein Laptop mit
#: 1366 × 768 darunter. Im grossen Maßstab braucht das Spiel rund 985 Pixel
#: Höhe – mit Titelzeile und Taskleiste passt das erst ab 1080.
GROSSER_BILDSCHIRM = (1600, 1080)


def massstab_fuer(breite, hoehe):
    """Welcher Maßstab zu einem Bildschirm dieser Grösse passt.

    >>> massstab_fuer(1920, 1080), massstab_fuer(1366, 768), massstab_fuer(1680, 1050)
    (1.5, 1, 1)
    """
    gross = breite >= GROSSER_BILDSCHIRM[0] and hoehe >= GROSSER_BILDSCHIRM[1]
    return 1.5 if gross else 1


def skaliert(wert, massstab):
    """Eine Pixelangabe im Maßstab – auf ganze Pixel gerundet.

    >>> skaliert(16, 1.5), skaliert(16, 1)
    (24, 16)
    """
    return round(wert * massstab)


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

#: Zwischenüberschriften im Handbuch – fett und etwas grösser als dessen Text.
SCHRIFT_ABSCHNITT = "Abschnitt"
ABSCHNITTGROESSE = 16

#: Betonte Zeilen im Handbuch (Ergebnisse, Beispiel-Überschriften): fett in
#: der Grösse der Erzählschrift.
SCHRIFT_BETONT = "Betont"

#: Kursiv in Grundgrösse – Untertitel und Tabellenbeschriftungen im Handbuch.
SCHRIFT_KURSIV = "Kursiv"

#: Farbe der Meldungszeile – für Probleme, die die Lehrkraft sehen muss. Hell
#: genug für den dunklen Grund, auf dem sie steht.
FARBE_MELDUNG = "#ff9a76"

#: Farbe der feinen Trennlinie unter der Kopfzeile – kaum heller als der
#: Nachthimmel, damit oben keine helle Leiste entsteht.
FARBE_LINIE = "#2c3160"

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
#: Hinweis auf dem Nachthimmel, dass noch etwas fehlt (etwa an der ID) –
#: hell genug, um auf dem dunklen Grund lesbar zu sein.
FARBE_WARNUNG = "#ff9a76"

# Farben des Handbuchs – ein Blatt Papier auf dem Nachthimmel:
#: Papier.
FARBE_PAPIER = "#f7f0dc"
#: Etwas dunkleres Papier – Kopfzellen der Tabellen.
FARBE_PAPIER_DUNKEL = "#eadcb6"
#: Linien der Tabellen.
FARBE_PAPIERLINIE = "#c5b186"
#: Schrift auf dem Papier.
FARBE_TINTE = "#2a2433"
#: Überschriften auf dem Papier – wie mit Rotstift.
FARBE_ROTSTIFT = "#8a2d1b"
#: Hinterlegung der Merksätze.
FARBE_MERKSATZ = "#f2dc9b"

# Das Handbuch als aufgeschlagenes Buch (ui/handbuch.py, ui/buchsatz.py):
#: Linien der Tabellen im Buch – wie mit brauner Tinte gezogen.
FARBE_BUCHLINIE = "#9c8456"
#: Kante der Merksatz-Karte, die ins Buch geklebt ist.
FARBE_KARTENKANTE = "#c9a24a"
#: Das Klebeband darauf.
FARBE_KLEBEBAND = "#efe6cc"
#: Bobs Randnotizen – blauer Kugelschreiber.
FARBE_KULI = "#284b8f"
#: Was die Spielenden selbst ins Buch schreiben – Bleistift (ui/uebung.py).
FARBE_BLEISTIFT = "#3b3a38"
#: Grün für "stimmt" – dieselbe Tinte wie im Stempel "GELÖST".
FARBE_HAKEN = "#2f7a46"

#: Das Handbuch ist in einer Buchschrift gesetzt – der ersten aus dieser
#: Liste, die der Rechner kennt. Die ersten beiden hat jedes Windows; "P052"
#: ist ihr Gegenstück unter Linux.
BUCHSCHRIFTEN = ("Palatino Linotype", "Georgia", "Book Antiqua", "P052", "DejaVu Serif",
                 "Liberation Serif", "Times New Roman")

#: Bobs Randnotizen stehen in einer Handschrift. "Ink Free" und "Segoe Print"
#: gibt es unter Windows 10 und 11; fehlen alle, werden sie kursiv gesetzt.
HANDSCHRIFTEN = ("Ink Free", "Segoe Print", "Segoe Script", "Z003", "Comic Sans MS")


def erste_schrift(wurzel, wunschliste):
    """Die erste Schriftfamilie aus ``wunschliste``, die es auf diesem Rechner gibt – sonst ``None``."""
    vorhanden = set(tkfont.families(wurzel))
    return next((familie for familie in wunschliste if familie in vorhanden), None)


def schriften_einrichten(wurzel, massstab=1):
    """Stellt die Grundschriften ein und legt die benannten Schriften an.

    Die Grössen wachsen mit dem ``massstab`` – im grossen 18 statt 12 Punkt.

    Rückgabe sind die Schriftobjekte. Wer sie aufbewahrt, behält die Schriften:
    Tkinter löscht eine benannte Schrift, sobald ihr Objekt verschwindet.
    """
    grund, titel, erzaehlung, abschnitt = (
        skaliert(g, massstab) for g in (SCHRIFTGROESSE, TITELGROESSE, ERZAEHLGROESSE, ABSCHNITTGROESSE)
    )
    for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont"):
        tkfont.nametofont(name, root=wurzel).configure(size=grund)
    familie = tkfont.nametofont("TkDefaultFont", root=wurzel).actual("family")
    return (
        tkfont.Font(root=wurzel, name=SCHRIFT_TITEL, family=familie, size=titel, weight="bold"),
        tkfont.Font(root=wurzel, name=SCHRIFT_ERZAEHLUNG, family=familie, size=erzaehlung),
        tkfont.Font(root=wurzel, name=SCHRIFT_FETT, family=familie, size=grund, weight="bold"),
        tkfont.Font(root=wurzel, name=SCHRIFT_ABSCHNITT, family=familie, size=abschnitt, weight="bold"),
        tkfont.Font(root=wurzel, name=SCHRIFT_BETONT, family=familie, size=erzaehlung, weight="bold"),
        tkfont.Font(root=wurzel, name=SCHRIFT_KURSIV, family=familie, size=grund, slant="italic"),
    )
