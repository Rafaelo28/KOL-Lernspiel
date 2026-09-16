"""Der Satz des Handbuchs (Arbeitsplan 6.4): Was auf welcher Buchseite steht.

Das Handbuch ist ein aufgeschlagenes Buch mit festen Seiten – gescrollt wird
nicht, geblättert. Also muss vorher feststehen, was auf welche Seite passt.
Hier werden die Absätze aus ``content/handbuch.py`` in Zeilen umbrochen und
die Zeilen auf Seiten verteilt, mit den Regeln, die man aus Büchern kennt:

* Eine Überschrift steht nie allein unten auf einer Seite – sie nimmt
  mindestens den Anfang dessen mit, was unter ihr steht.
* Läuft ein Absatz über das Seitenende, bleiben unten mindestens zwei Zeilen
  stehen, und oben auf der nächsten Seite kommen mindestens zwei an.
* Tabellen, Merksätze und Randnotizen werden nicht geteilt. Eine Randnotiz
  bleibt bei dem, worauf sie sich bezieht.
* Das Vigenère-Quadrat bekommt eine Seite für sich.
* Tabellen mit 26 Buchstaben sind für eine Buchseite zu breit. Sie werden in
  Teile untereinander zerlegt (A–M, N–Z) – jeder Teil mit der Beschriftung.

Gezeichnet wird hier nichts. Das Ergebnis sind Seiten mit ihren Stücken –
Zeilen, Tabellen, dem Quadrat, der Merksatz-Karte – und deren Lage auf der
Textfläche. Gemessen wird mit genau den Tk-Schriften, mit denen
``ui/handbuch.py`` danach zeichnet; darum passt es aufs Pixel.

Die erste Seite ist die Titelseite: der Titel des Handbuchs, darunter der
Inhalt des Kapitels mit Seitenzahlen und der Stempel "STRENG GEHEIM".
"""

import math
from typing import NamedTuple

from tkinter import font as tkfont

from content import handbuch as buch
from ui import stil

# Abstände – Pixel im Maßstab 1, umgerechnet mit ``px`` (siehe ui/stil.py).
ABSTAND_ABSATZ = 6
ABSTAND_VOR_ABSCHNITT = 14
ABSTAND_NACH_ABSCHNITT = 3
ABSTAND_TABELLE = 8
#: So weit ist der Text einer Aufzählung eingerückt.
EINZUG = 22
#: Innenrand der Merksatz-Karte.
KARTENRAND = 10
#: Die Karte wirft einen Schatten nach rechts unten, und oben ragt das
#: Klebeband über ihre Kante – beides muss noch auf die Textfläche passen.
KARTENSCHATTEN = 3
KLEBEBAND_UEBERSTAND = 12
#: So breit wird eine Randnotiz höchstens.
NOTIZBREITE = 240
#: Randnotizen stehen etwas schief – wie schnell hingeschrieben (Grad, gegen den Uhrzeigersinn).
NOTIZWINKEL = 3
#: Innenränder der Tabellenzellen, waagrecht und senkrecht.
ZELLRAND = 3
ZELLRAND_SENKRECHT = 2
#: Abstand der Seitenzahl unter der Textfläche.
SEITENZAHL_ABSTAND = 12

# Schriftgrössen in Punkt (im Maßstab 1).
TEXTGROESSE = 12
ABSCHNITTGROESSE = 13
KAPITELGROESSE = 15
BUCHTITELGROESSE = 17
NOTIZGROESSE = 14
KLEINGROESSE = 10


# ── Die Schriften ──────────────────────────────────────────────────────────

class Schriften(NamedTuple):
    """Die Schriften des Buchs. Wer sie hält, behält sie – Tk löscht sonst jede, die niemand mehr braucht."""

    text: tkfont.Font
    betont: tkfont.Font
    kursiv: tkfont.Font
    abschnitt: tkfont.Font
    kapitel: tkfont.Font
    buchtitel: tkfont.Font
    notiz: tkfont.Font
    #: Klein und kursiv – Seitenzahlen und die Beschriftung des Quadrats.
    klein: tkfont.Font


def schriften(master, massstab):
    """Legt die Schriften des Buchs an: eine Buchschrift und für Bobs Notizen eine Handschrift."""
    familie = stil.erste_schrift(master, stil.BUCHSCHRIFTEN) or tkfont.nametofont(
        "TkDefaultFont", root=master).actual("family")
    hand = stil.erste_schrift(master, stil.HANDSCHRIFTEN)

    def schrift(groesse, **art):
        return tkfont.Font(root=master, family=familie, size=stil.skaliert(groesse, massstab), **art)

    notiz = (tkfont.Font(root=master, family=hand, size=stil.skaliert(NOTIZGROESSE, massstab)) if hand
             else schrift(TEXTGROESSE, slant="italic"))
    return Schriften(
        text=schrift(TEXTGROESSE),
        betont=schrift(TEXTGROESSE, weight="bold"),
        kursiv=schrift(TEXTGROESSE, slant="italic"),
        abschnitt=schrift(ABSCHNITTGROESSE, weight="bold"),
        kapitel=schrift(KAPITELGROESSE, weight="bold"),
        buchtitel=schrift(BUCHTITELGROESSE, weight="bold"),
        notiz=notiz,
        klein=schrift(KLEINGROESSE, slant="italic"),
    )


# ── Was auf einer Seite steht ──────────────────────────────────────────────
#
# Alle Lagen sind relativ zur linken oberen Ecke der Textfläche einer Seite.

class Zeile(NamedTuple):
    """Text – eine Zeile oder mehrere, durch Zeilenumbrüche getrennt.

    ``schrift`` ist der Name eines Feldes in :class:`Schriften`, ``art``
    sagt, wofür der Text steht ("absatz", "abschnitt", "punkt", "notiz" …).
    ``anker`` wie bei Tk: "nw" heisst, ``x, y`` ist die linke obere Ecke.
    """

    x: int
    y: int
    text: str
    schrift: str
    farbe: str
    art: str
    anker: str = "nw"
    winkel: float = 0


class Karte(NamedTuple):
    """Die Merksatz-Karte, die ins Buch geklebt ist."""

    x: int
    y: int
    breite: int
    hoehe: int


class Raster(NamedTuple):
    """Eine Tabelle – oder ein Teil davon, wenn sie zerlegt werden musste.

    ``zeilen`` wie in ``content/handbuch.py``: vorne die Beschriftung (schon
    umbrochen), dann die Zellen.
    """

    x: int
    y: int
    zeilen: tuple
    beschriftungsbreite: int
    zellbreite: int
    #: Je Zeile – eine Beschriftung, die umbrochen werden musste, macht ihre Zeile höher.
    zeilenhoehen: tuple

    @property
    def breite(self):
        return self.beschriftungsbreite + (len(self.zeilen[0]) - 1) * self.zellbreite

    @property
    def hoehe(self):
        return sum(self.zeilenhoehen)

    def oben(self, zeile):
        """Wo die Zeile ``zeile`` beginnt, gemessen von der Oberkante des Rasters."""
        return sum(self.zeilenhoehen[:zeile])


class Quadrat(NamedTuple):
    """Das Vigenère-Quadrat: 27 × 27 Felder mit Kopfzeile und Kopfspalte."""

    x: int
    y: int
    feld: int

    @property
    def kante(self):
        return 27 * self.feld


class Verzierung(NamedTuple):
    """Eine feine Linie mit einem Diamanten in der Mitte (Titelseite)."""

    x: int
    y: int
    breite: int


class Punktlinie(NamedTuple):
    """Die Pünktchen im Inhaltsverzeichnis zwischen Überschrift und Seitenzahl."""

    x0: int
    x1: int
    y: int


class Stempel(NamedTuple):
    """Der Stempel "STRENG GEHEIM" (ein Bild) mit seiner linken oberen Ecke."""

    x: int
    y: int
    breite: int
    hoehe: int


class Buchseite(NamedTuple):
    """Eine gesetzte Seite. ``nummer`` ist ``None`` auf der Titelseite."""

    stuecke: tuple
    nummer: object = None


class Satz(NamedTuple):
    """Das ganze gesetzte Kapitel.

    ``inhalt`` sind (Überschrift, Seitennummer) für das Inhaltsverzeichnis,
    ``lesezeichen`` die Nummer der Seite, zu der das Lesezeichen führt.
    """

    seiten: tuple
    inhalt: tuple
    lesezeichen: int


# ── Umbrechen ──────────────────────────────────────────────────────────────

def umbrechen(text, schrift, breite):
    """Bricht ``text`` an Leerzeichen in Zeilen um, die höchstens ``breite`` Pixel breit sind.

    Ein Wort, das allein schon breiter ist, bekommt eine Zeile für sich.
    """
    zeilen, zeile = [], ""
    for wort in text.split():
        probe = f"{zeile} {wort}" if zeile else wort
        if zeile and schrift.measure(probe) > breite:
            zeilen.append(zeile)
            zeile = wort
        else:
            zeile = probe
    if zeile:
        zeilen.append(zeile)
    return zeilen


# ── Der Fluss: Kisten, die auf Seiten verteilt werden ──────────────────────

class _Kiste(NamedTuple):
    """Etwas Unteilbares im Fluss – eine Zeile, eine Tabelle, eine Karte.

    ``stuecke`` liegen relativ zur Oberkante der Kiste. ``vorher`` ist der
    Abstand davor; oben auf einer Seite fällt er weg. ``trennbar`` sagt, ob
    vor dieser Kiste eine Seite enden darf.
    """

    hoehe: int
    stuecke: tuple
    vorher: int = 0
    trennbar: bool = True
    neue_seite: bool = False
    marke: tuple = ()


class _Fluss:
    """Sammelt die Kisten in Lesereihenfolge und merkt sich, was zusammenbleiben muss."""

    def __init__(self):
        self.kisten = []
        self._festhalten = False
        self._neue_seite = False

    def dazu(self, kiste):
        if self._festhalten:
            kiste = kiste._replace(trennbar=False)
        if self._neue_seite:
            kiste = kiste._replace(neue_seite=True)
        self._festhalten = self._neue_seite = False
        self.kisten.append(kiste)

    def festhalten(self):
        """Die nächste Kiste bleibt auf derselben Seite wie die letzte."""
        self._festhalten = True

    def danach_neue_seite(self):
        """Die nächste Kiste beginnt eine neue Seite."""
        self._neue_seite = True


def _verschoben(stueck, dy):
    return stueck._replace(y=stueck.y + dy)


class _Setzer:
    """Macht aus einer Handbuchseite den Fluss aus Kisten."""

    def __init__(self, schriften, breite, hoehe, px):
        self.s = schriften
        self.breite = breite
        self.hoehe = hoehe
        self.px = px
        self.fluss = _Fluss()

    def zeilenhoehe(self, schrift):
        return getattr(self.s, schrift).metrics("linespace")

    # Absätze, Überschriften, Aufzählungen

    def absatz(self, text, schrift="text", farbe=stil.FARBE_TINTE, art="absatz", vorher=None, einzug=0,
               zeichen="", ausrichtung="links", marke=(), trennbar_davor=True):
        """Ein Absatz als Zeilen-Kisten, mit Schusterjungen- und Hurenkinder-Regel.

        Vor der i-ten Zeile (ab 0) darf eine Seite nur enden, wenn davor und
        danach je mindestens zwei Zeilen stehen. Vor der ersten, wenn
        ``trennbar_davor``.
        """
        vorher = self.px(ABSTAND_ABSATZ) if vorher is None else vorher
        font = getattr(self.s, schrift)
        zeilen = umbrechen(text, font, self.breite - einzug)
        hoehe = self.zeilenhoehe(schrift)
        for nr, inhalt in enumerate(zeilen):
            if ausrichtung == "mitte":
                stueck = Zeile(self.breite // 2, 0, inhalt, schrift, farbe, art, anker="n")
            else:
                stueck = Zeile(einzug, 0, inhalt, schrift, farbe, art)
            stuecke = (stueck,)
            if nr == 0 and zeichen:
                stuecke = (Zeile(self.px(4), 0, zeichen, schrift, farbe, "zeichen"),) + stuecke
            trennbar = trennbar_davor if nr == 0 else 2 <= nr <= len(zeilen) - 2
            self.fluss.dazu(_Kiste(hoehe, stuecke, vorher if nr == 0 else 0, trennbar,
                                   marke=marke if nr == 0 else ()))

    def ueberschrift(self, text, schrift="abschnitt", art="abschnitt", marke=()):
        self.absatz(text, schrift, stil.FARBE_ROTSTIFT, art, vorher=self.px(ABSTAND_VOR_ABSCHNITT),
                    marke=marke)
        # Die Überschrift nimmt den Anfang des Folgenden mit auf ihre Seite.
        self.fluss.festhalten()

    def aufzaehlung(self, block):
        """Punkte oder Schritte. Wie bei Zeilen: Geteilt wird nur, wenn je zwei Punkte zusammenbleiben."""
        anzahl = len(block.punkte)
        for nr, punkt in enumerate(block.punkte):
            zeichen = f"{nr + 1}." if block.nummeriert else "•"
            self.absatz(punkt, einzug=self.px(EINZUG), zeichen=zeichen, art="punkt",
                        vorher=self.px(ABSTAND_ABSATZ // 2) if nr else None,
                        trennbar_davor=nr == 0 or 2 <= nr <= anzahl - 2)

    # Tabellen und Quadrat

    def tabelle(self, block):
        s, px = self.s, self.px
        abstand = px(ABSTAND_TABELLE)
        marke = ("lesezeichen",) if block.lesezeichen else ()
        if block.titel:
            self.absatz(block.titel, "kursiv", art="tabellentitel", vorher=abstand, ausrichtung="mitte",
                        marke=marke)
            self.fluss.festhalten()
            marke = ()
            abstand = px(2)
        beschriftungen = [zeile[0] for zeile in block.zeilen]
        zellen = [zelle for zeile in block.zeilen for zelle in zeile[1:]]
        innen = 2 * px(ZELLRAND + 2)
        einzeilig = s.text.metrics("linespace") + 2 * px(ZELLRAND_SENKRECHT)
        zelle_eng = max(s.text.measure(z) for z in zellen) + 2 * px(ZELLRAND)
        zelle_bequem = max(zelle_eng, round(einzeilig * 1.1))
        beschriftung_ganz = max(s.text.measure(b) for b in beschriftungen) + innen
        beschriftung_eng = max(s.text.measure(wort) for b in beschriftungen for wort in b.split()) + innen
        # So wenige Teile wie möglich. Reicht der Platz nicht für die ganze
        # Beschriftung, wird sie in ihrer Spalte umbrochen – aber kein Wort zerteilt.
        anzahl = len(block.zeilen[0]) - 1
        for teile in range(1, anzahl + 1):
            je_teil = math.ceil(anzahl / teile)
            spalte = min(beschriftung_ganz, self.breite - je_teil * zelle_eng)
            if spalte >= beschriftung_eng:
                break
        zellbreite = min(zelle_bequem, (self.breite - spalte) // je_teil)
        umbrochen = ["\n".join(umbrechen(b, s.text, spalte - innen)) for b in beschriftungen]
        zeilenhoehen = tuple(einzeilig + b.count("\n") * s.text.metrics("linespace") for b in umbrochen)
        for teil in range(teile):
            if teil:
                # Die Teile einer Tabelle gehören zusammen.
                self.fluss.festhalten()
            von = 1 + teil * je_teil
            stueck_zeilen = tuple((beschriftung, *zeile[von:von + je_teil])
                                  for beschriftung, zeile in zip(umbrochen, block.zeilen))
            raster = Raster(0, 0, stueck_zeilen, spalte, zellbreite, zeilenhoehen)
            raster = raster._replace(x=(self.breite - raster.breite) // 2)
            self.fluss.dazu(_Kiste(raster.hoehe, (raster,), abstand, marke=marke))
            marke = ()
            abstand = px(4)

    def quadrat(self, block):
        """Das Quadrat auf einer eigenen Seite, so gross, wie sie es erlaubt."""
        marke = ("lesezeichen",) if block.lesezeichen else ()
        # Die Beschriftung klein, damit für das Quadrat viel Platz bleibt.
        schrift = self.s.klein
        beschriftung = umbrechen(block.beschriftung, schrift, self.breite) if block.beschriftung else []
        oben = len(beschriftung) * schrift.metrics("linespace") + self.px(6)
        feld = min(self.breite, self.hoehe - oben) // 27
        stuecke = tuple(Zeile(self.breite // 2, nr * schrift.metrics("linespace"), text, "klein",
                              stil.FARBE_TINTE, "tabellentitel", anker="n")
                        for nr, text in enumerate(beschriftung))
        quadrat = Quadrat((self.breite - 27 * feld) // 2, oben, feld)
        self.fluss.dazu(_Kiste(oben + quadrat.kante, stuecke + (quadrat,), neue_seite=True, marke=marke))
        self.fluss.danach_neue_seite()

    # Merksatz und Randnotiz

    def merksatz(self, abschnitt):
        """Der Merksatz als Karte – ein Stück, das nicht geteilt wird."""
        s, px = self.s, self.px
        rand = px(KARTENRAND)
        innen = self.breite - px(KARTENSCHATTEN) - 2 * rand
        stuecke = []
        y = rand
        for text in umbrechen(abschnitt.ueberschrift, s.abschnitt, innen):
            stuecke.append(Zeile(rand, y, text, "abschnitt", stil.FARBE_ROTSTIFT, "merksatz_titel"))
            y += s.abschnitt.metrics("linespace")
        y += px(ABSTAND_NACH_ABSCHNITT)
        for block in abschnitt.bloecke:
            for text in umbrechen(block.text, s.text, innen):
                stuecke.append(Zeile(rand, y, text, "text", stil.FARBE_TINTE, "merksatz"))
                y += s.text.metrics("linespace")
            y += px(ABSTAND_ABSATZ // 2)
        hoehe = y - px(ABSTAND_ABSATZ // 2) + rand
        oben, schatten = px(KLEBEBAND_UEBERSTAND), px(KARTENSCHATTEN)
        karte = Karte(0, oben, self.breite - schatten, hoehe)
        stuecke = [stueck._replace(y=stueck.y + oben) for stueck in stuecke]
        self.fluss.dazu(_Kiste(oben + hoehe + schatten, (karte, *stuecke), px(ABSTAND_VOR_ABSCHNITT),
                               marke=("abschnitt", abschnitt.ueberschrift)))

    def randnotiz(self, notiz):
        """Bobs Notiz: rechtsbündig, etwas schief, bei dem, worauf sie sich bezieht."""
        s, px = self.s, self.px
        zeilen = umbrechen(notiz.text, s.notiz, px(NOTIZBREITE))
        breite = max(s.notiz.measure(z) for z in zeilen)
        # Schief gestellt ragt das linke Ende nach unten – dafür Platz lassen.
        hoehe = len(zeilen) * s.notiz.metrics("linespace") + math.ceil(breite * math.sin(math.radians(NOTIZWINKEL)))
        stueck = Zeile(self.breite - px(6), 0, "\n".join(zeilen), "notiz", stil.FARBE_KULI, "notiz",
                       anker="ne", winkel=NOTIZWINKEL)
        self.fluss.dazu(_Kiste(hoehe, (stueck,), px(2), trennbar=False))

    # Das Kapitel

    def kapitel(self, seite):
        self.absatz(seite.titel, "kapitel", stil.FARBE_ROTSTIFT, "kapitel", vorher=0)
        self.fluss.festhalten()
        for abschnitt in seite.abschnitte:
            if abschnitt.hervorgehoben:
                self.merksatz(abschnitt)
                continue
            self.ueberschrift(abschnitt.ueberschrift, marke=("abschnitt", abschnitt.ueberschrift))
            for block in abschnitt.bloecke:
                if isinstance(block, buch.Absatz):
                    self.absatz(block.text, "betont" if block.betont else "text",
                                art="betont" if block.betont else "absatz")
                    if block.text.rstrip().endswith(":"):
                        # Ein Absatz mit Doppelpunkt kündigt an, was folgt – er bleibt dabei.
                        self.fluss.festhalten()
                elif isinstance(block, buch.Aufzaehlung):
                    self.aufzaehlung(block)
                elif isinstance(block, buch.Tabelle):
                    self.tabelle(block)
                elif isinstance(block, buch.VigenereQuadrat):
                    self.quadrat(block)
                elif isinstance(block, buch.Randnotiz):
                    self.randnotiz(block)
                else:
                    raise TypeError(f"Diesen Block kennt das Handbuch nicht: {block!r}")
        return self.fluss.kisten


def seiten_verteilen(kisten, hoehe):
    """Verteilt die Kisten auf Seiten der Höhe ``hoehe``.

    Passt eine Kiste nicht mehr auf die Seite, geht es zurück bis zur
    letzten Stelle, an der eine Seite enden darf; alles danach wandert auf
    die nächste Seite. Gibt es auf der ganzen Seite keine solche Stelle,
    endet sie eben vor der Kiste, die nicht mehr passt – lieber eine Regel
    gebrochen als eine Seite, die überläuft.

    Rückgabe: je Seite eine Liste von (Kiste, y).
    """
    seiten, seite, y, i = [], [], 0, 0
    while i < len(kisten):
        kiste = kisten[i]
        if kiste.neue_seite and seite:
            seiten.append(seite)
            seite, y = [], 0
        abstand = kiste.vorher if seite else 0
        if not seite or y + abstand + kiste.hoehe <= hoehe:
            seite.append((kiste, y + abstand))
            y += abstand + kiste.hoehe
            i += 1
            continue
        # Zurück bis zur letzten erlaubten Trennstelle auf dieser Seite.
        zurueck = 0
        while not kisten[i - zurueck].trennbar and zurueck < len(seite) - 1:
            zurueck += 1
        if not kisten[i - zurueck].trennbar:
            zurueck = 0
        if zurueck:
            del seite[-zurueck:]
        seiten.append(seite)
        seite, y = [], 0
        i -= zurueck
    if seite:
        seiten.append(seite)
    return seiten


def _titelseite(satz_inhalt, schriften, breite, hoehe, px, stempel):
    """Titel, Untertitel, Verzierung, Inhaltsverzeichnis – und unten der Stempel."""
    s = schriften
    stuecke = []
    y = px(6)
    for text in umbrechen(buch.HANDBUCH_TITEL, s.buchtitel, breite):
        stuecke.append(Zeile(breite // 2, y, text, "buchtitel", stil.FARBE_ROTSTIFT, "buchtitel", anker="n"))
        y += s.buchtitel.metrics("linespace")
    y += px(6)
    for text in umbrechen(buch.HANDBUCH_UNTERTITEL, s.kursiv, breite - 2 * px(16)):
        stuecke.append(Zeile(breite // 2, y, text, "kursiv", stil.FARBE_TINTE, "untertitel", anker="n"))
        y += s.kursiv.metrics("linespace")
    y += px(12)
    stuecke.append(Verzierung(px(30), y, breite - 2 * px(30)))
    y += px(20)
    stuecke.append(Zeile(breite // 2, y, "Inhalt", "abschnitt", stil.FARBE_ROTSTIFT, "inhalt_titel", anker="n"))
    y += s.abschnitt.metrics("linespace") + px(4)
    zeile = s.text.metrics("linespace")
    rand = px(18)
    for ueberschrift, nummer in satz_inhalt:
        zahl = str(nummer)
        platz = breite - 2 * rand - s.text.measure(zahl) - px(12)
        text, woerter = ueberschrift, ueberschrift.split()
        # Zu lang für eine Zeile im Verzeichnis: vorne so viel, wie passt, und "…".
        while s.text.measure(text) > platz and len(woerter) > 1:
            woerter.pop()
            text = " ".join(woerter).rstrip(" –,:") + " …"
        stuecke.append(Zeile(rand, y, text, "text", stil.FARBE_TINTE, "inhalt"))
        stuecke.append(Zeile(breite - rand, y, zahl, "text", stil.FARBE_TINTE, "inhalt_seite", anker="ne"))
        grundlinie = y + s.text.metrics("ascent")
        stuecke.append(Punktlinie(rand + s.text.measure(text) + px(6),
                                  breite - rand - s.text.measure(zahl) - px(6), grundlinie))
        y += zeile
    if stempel is not None:
        stempel_breite, stempel_hoehe = stempel
        stuecke.append(Stempel((breite - stempel_breite) // 2, max(y + px(8), hoehe - stempel_hoehe),
                               stempel_breite, stempel_hoehe))
    return Buchseite(tuple(stuecke))


def setzen(seite, schriften, breite, hoehe, px, stempel=None):
    """Setzt eine Handbuchseite als Buch: Titelseite, dann das Kapitel auf so vielen Seiten wie nötig.

    ``breite`` und ``hoehe`` sind die Textfläche einer Buchseite in Pixeln,
    ``px`` rechnet Pixel aus dem Maßstab 1 um (``Screen.px``), ``stempel``
    ist (Breite, Höhe) des Stempelbilds oder ``None`` ohne Stempel.
    """
    setzer = _Setzer(schriften, breite, hoehe, px)
    verteilt = seiten_verteilen(setzer.kapitel(seite), hoehe)
    seiten, inhalt, lesezeichen = [], [], None
    zahl_y = hoehe + px(SEITENZAHL_ABSTAND)
    for nummer, kisten in enumerate(verteilt, 1):
        stuecke = []
        for kiste, y in kisten:
            stuecke.extend(_verschoben(stueck, y) for stueck in kiste.stuecke)
            if kiste.marke[:1] == ("abschnitt",):
                inhalt.append((kiste.marke[1], nummer))
            if kiste.marke == ("lesezeichen",) and lesezeichen is None:
                lesezeichen = nummer
        stuecke.append(Zeile(breite // 2, zahl_y, f"– {nummer} –", "klein", stil.FARBE_TINTE,
                             "seitenzahl", anker="n"))
        seiten.append(Buchseite(tuple(stuecke), nummer))
    titel = _titelseite(inhalt, schriften, breite, hoehe, px, stempel)
    return Satz((titel, *seiten), tuple(inhalt), lesezeichen if lesezeichen is not None else 1)
