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
* Abschnitte mit einem Werkzeug (``Abschnitt.gegenueber``) stehen immer auf
  linken Seiten, und rechts daneben liegt das Werkzeug – die Tabelle oder
  das Quadrat. Folgen mehrere Abschnitte mit demselben Werkzeug aufeinander,
  laufen sie ineinander weiter, jede ihrer Seiten mit dem Werkzeug daneben.
  Wäre die erste davon eine rechte Seite, bleibt die leer – wie vor einem
  neuen Kapitel. Was danach ohne Werkzeug kommt, beginnt auf einer neuen Seite.
* Ein Beispiel, das auf eine Seite passt, wird nicht geteilt – es beginnt
  lieber auf einer neuen. Ist es länger, bleiben wenigstens seine Schritte
  beisammen, und das Ergebnis bleibt bei ihnen. Jedes Stück, das zu einem
  Schritt gehört, trägt dessen :class:`Schrittmarke` – daran markiert das
  Handbuch im Werkzeug, wo gesucht wird.

Gezeichnet wird hier nichts. Das Ergebnis sind Seiten mit ihren Stücken –
Zeilen, Tabellen, dem Quadrat, der Merksatz-Karte – und deren Lage auf der
Textfläche. Gemessen wird mit genau den Tk-Schriften, mit denen
``ui/handbuch.py`` danach zeichnet; darum passt es aufs Pixel.

Die erste Seite ist die Titelseite: der Titel des Handbuchs, darunter der
Inhalt des Kapitels mit Seitenzahlen und der Stempel "STRENG GEHEIM".

Der Weg durch diese Datei
─────────────────────────
Gesetzt wird in drei Schritten; :func:`setzen` ganz unten ruft sie der Reihe
nach auf:

1. Der :class:`_Setzer` liest die Handbuchseite Block für Block und macht
   daraus **Kisten** (:class:`_Kiste`) – jede Kiste ein Stück, das nicht
   auseinandergerissen werden darf: eine Textzeile, eine Tabelle, die
   Merksatz-Karte. Er weiss, wie hoch jede wird, weil er mit denselben
   Schriften misst, mit denen später gezeichnet wird.
2. Die Kisten sammeln sich im :class:`_Fluss` – in Lesereihenfolge, mit
   Merkern daran, was zusammenbleiben oder eine neue Seite beginnen muss.
3. :func:`seiten_verteilen` schneidet den Fluss in Seiten, und zwar an den
   Stellen, an denen es erlaubt ist.

Übrig bleiben :class:`Buchseite`-Objekte mit den **Stücken** darauf (Zeile,
Raster, Quadrat, Karte …) und deren Lage in Pixeln. Gezeichnet werden sie
erst in :mod:`ui.buchleinwand`.
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
        """Eine Schrift der Buchfamilie in dieser Größe, schon auf den Maßstab umgerechnet."""
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
    #: Gehört die Zeile zu einem Schritt eines Beispiels? Dann seine :class:`Schrittmarke`.
    schritt: object = None


class Schrittmarke(NamedTuple):
    """Wofür ein Stück eines Beispiels steht: den Schritt ``nummer`` (ab 0) im Abschnitt ``abschnitt``.

    Die Nummer des Abschnitts unterscheidet zwei Beispiele mit denselben
    Schritten – Ver- und Entschlüsseln rechnen beide HUND und ROT.
    """

    abschnitt: int
    nummer: int
    #: Was dabei im Werkzeug markiert wird (:class:`content.handbuch.Schritt`).
    schritt: object


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
    #: Sind die Spalten die Schritte eines Beispiels? Dann je Spalte ihre :class:`Schrittmarke`.
    schritte: tuple = ()

    @property
    def breite(self):
        """Wie breit die Tabelle wird: die Beschriftungsspalte plus alle Zellen."""
        return self.beschriftungsbreite + (len(self.zeilen[0]) - 1) * self.zellbreite

    @property
    def hoehe(self):
        """Wie hoch die Tabelle wird – alle Zeilenhöhen zusammen."""
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
        """Die Seitenlänge des ganzen Quadrats: 26 Buchstaben plus Kopfzeile beziehungsweise Kopfspalte."""
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
    """Ein Stempel (ein vorgerendertes Bild) mit seiner linken oberen Ecke.

    ``name`` ist der Ordner unter ``content/animationen/``.
    """

    x: int
    y: int
    breite: int
    hoehe: int
    name: str = "stempel"


class Buchseite(NamedTuple):
    """Eine gesetzte Seite. ``nummer`` ist ``None`` auf der Titelseite.

    ``schritte`` sind die :class:`Schrittmarke`-n der Beispielschritte auf
    der Seite, in Lesereihenfolge. Auf der Seite gegenüber steht dann in
    ``werkzeug`` das Werkzeug, in dem sie markiert werden – ein Block aus
    :mod:`content.handbuch`.
    """

    stuecke: tuple
    nummer: object = None
    schritte: tuple = ()
    werkzeug: object = None


class Satz(NamedTuple):
    """Das ganze gesetzte Kapitel.

    ``inhalt`` sind (Überschrift, Seitennummer) für das Inhaltsverzeichnis.
    """

    seiten: tuple
    inhalt: tuple


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


def _schrittmarken(stueck):
    """Die Schrittmarken eines Stücks – eine Zeile hat höchstens eine, ein Raster eine je Spalte."""
    if isinstance(stueck, Zeile):
        return (stueck.schritt,) if stueck.schritt is not None else ()
    if isinstance(stueck, Raster):
        return stueck.schritte
    return ()


class _Fluss:
    """Sammelt die Kisten in Lesereihenfolge und merkt sich, was zusammenbleiben muss."""

    def __init__(self):
        """Beginnt mit einem leeren Fluss – ohne Kisten und ohne offene Merker."""
        self.kisten = []
        self._festhalten = False
        self._neue_seite = False

    def dazu(self, kiste):
        """Hängt eine Kiste hinten an und wendet dabei an, was vorgemerkt war.

        Vorgemerkt sein kann: "bleibt bei der vorigen Kiste"
        (:meth:`festhalten`) oder "beginnt eine neue Seite"
        (:meth:`danach_neue_seite`). Beides gilt nur für die nächste Kiste
        und ist danach wieder vergessen.
        """
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
    """Dasselbe Stück, nur ``dy`` Pixel weiter unten.

    Die Stücke sind unveränderliche Objekte (``NamedTuple``); statt sie zu
    verschieben, entsteht hier eine Kopie mit anderem ``y``.
    """
    return stueck._replace(y=stueck.y + dy)


class _Setzer:
    """Macht aus einer Handbuchseite den Fluss aus Kisten."""

    def __init__(self, schriften, breite, hoehe, px):
        """Merkt sich Schriften und das Format einer Seite; gesetzt wird noch nichts."""
        self.s = schriften
        self.breite = breite
        self.hoehe = hoehe
        self.px = px
        self.fluss = _Fluss()

    def zeilenhoehe(self, schrift):
        """Wie hoch eine Zeile in dieser Schrift wird – Zeilenabstand inklusive."""
        return getattr(self.s, schrift).metrics("linespace")

    # Absätze, Überschriften, Aufzählungen

    def absatz(self, text, schrift="text", farbe=stil.FARBE_TINTE, art="absatz", vorher=None, einzug=0,
               zeichen="", ausrichtung="links", marke=(), trennbar_davor=True, schritt=None, zusammen=False):
        """Ein Absatz als Zeilen-Kisten, mit Schusterjungen- und Hurenkinder-Regel.

        Die beiden Namen kommen aus dem Buchdruck und meinen eine einzelne
        Zeile eines Absatzes, die allein unten auf einer Seite stehen bleibt
        oder allein oben auf der nächsten ankommt. Beides sieht schlecht aus
        und wird hier verhindert:

        Vor der i-ten Zeile (ab 0) darf eine Seite nur enden, wenn davor und
        danach je mindestens zwei Zeilen stehen – und gar nicht, wenn der
        Absatz ``zusammen`` bleiben soll. Vor der ersten, wenn
        ``trennbar_davor``. ``schritt`` ist die :class:`Schrittmarke` aller Zeilen.
        """
        vorher = self.px(ABSTAND_ABSATZ) if vorher is None else vorher
        font = getattr(self.s, schrift)
        zeilen = umbrechen(text, font, self.breite - einzug)
        hoehe = self.zeilenhoehe(schrift)
        for nr, inhalt in enumerate(zeilen):
            if ausrichtung == "mitte":
                stueck = Zeile(self.breite // 2, 0, inhalt, schrift, farbe, art, anker="n", schritt=schritt)
            else:
                stueck = Zeile(einzug, 0, inhalt, schrift, farbe, art, schritt=schritt)
            stuecke = (stueck,)
            if nr == 0 and zeichen:
                stuecke = (Zeile(self.px(4), 0, zeichen, schrift, farbe, "zeichen", schritt=schritt),) + stuecke
            trennbar = trennbar_davor if nr == 0 else not zusammen and 2 <= nr <= len(zeilen) - 2
            self.fluss.dazu(_Kiste(hoehe, stuecke, vorher if nr == 0 else 0, trennbar,
                                   marke=marke if nr == 0 else ()))

    def ueberschrift(self, text, schrift="abschnitt", art="abschnitt", marke=()):
        """Setzt eine Überschrift – mit Abstand davor und ohne Umbruch zu dem, was folgt."""
        self.absatz(text, schrift, stil.FARBE_ROTSTIFT, art, vorher=self.px(ABSTAND_VOR_ABSCHNITT),
                    marke=marke)
        # Die Überschrift nimmt den Anfang des Folgenden mit auf ihre Seite.
        self.fluss.festhalten()

    def aufzaehlung(self, block, schritte=()):
        """Punkte oder Schritte. Wie bei Zeilen: Geteilt wird nur, wenn je zwei Punkte zusammenbleiben.

        Sind es die ``schritte`` eines Beispiels (je Punkt eine
        :class:`Schrittmarke`), wird gar nicht geteilt: Wer rechnet, soll
        nicht mitten im Beispiel umblättern müssen.
        """
        anzahl = len(block.punkte)
        for nr, punkt in enumerate(block.punkte):
            zeichen = f"{nr + 1}." if block.nummeriert else "•"
            trennbar = nr == 0 or (not schritte and 2 <= nr <= anzahl - 2)
            self.absatz(punkt, einzug=self.px(EINZUG), zeichen=zeichen, art="punkt",
                        vorher=self.px(ABSTAND_ABSATZ // 2) if nr else None, trennbar_davor=trennbar,
                        schritt=schritte[nr] if schritte else None, zusammen=bool(schritte))

    # Tabellen und Quadrat

    def tabelle(self, block, schritte=()):
        """Eine Tabelle – in so wenigen Teilen wie nötig. ``schritte``: je Spalte eine :class:`Schrittmarke`."""
        s, px = self.s, self.px
        abstand = px(ABSTAND_TABELLE)
        if block.titel:
            self.absatz(block.titel, "kursiv", art="tabellentitel", vorher=abstand, ausrichtung="mitte")
            self.fluss.festhalten()
            abstand = px(2)
        beschriftungen = [zeile[0] for zeile in block.zeilen]
        zellen = [zelle for zeile in block.zeilen for zelle in zeile[1:]]
        innen = 2 * px(ZELLRAND + 2)
        einzeilig = s.text.metrics("linespace") + 2 * px(ZELLRAND_SENKRECHT)
        zelle_eng = max(s.text.measure(z) for z in zellen) + 2 * px(ZELLRAND)
        zelle_bequem = max(zelle_eng, round(einzeilig * 1.1))
        # Ein Band ohne Beschriftungen (das Alphabet zum Abzählen) bekommt auch
        # keine Spalte dafür.
        beschriftet = any(b.strip() for b in beschriftungen)
        beschriftung_ganz = (max(s.text.measure(b) for b in beschriftungen) + innen) if beschriftet else 0
        beschriftung_eng = (max(s.text.measure(wort) for b in beschriftungen for wort in b.split())
                            + innen) if beschriftet else 0
        # So wenige Teile wie möglich. Reicht der Platz nicht für die ganze
        # Beschriftung, wird sie in ihrer Spalte umbrochen – aber kein Wort zerteilt.
        anzahl = len(block.zeilen[0]) - 1
        for teile in range(1, anzahl + 1):
            je_teil = math.ceil(anzahl / teile)
            spalte = min(beschriftung_ganz, self.breite - je_teil * zelle_eng)
            if spalte >= beschriftung_eng:
                break
        zellbreite = min(zelle_bequem, (self.breite - spalte) // je_teil)
        umbrochen = ["\n".join(umbrechen(b, s.text, spalte - innen)) if beschriftet else ""
                     for b in beschriftungen]
        zeilenhoehen = tuple(einzeilig + b.count("\n") * s.text.metrics("linespace") for b in umbrochen)
        for teil in range(teile):
            if teil:
                # Die Teile einer Tabelle gehören zusammen.
                self.fluss.festhalten()
            von = 1 + teil * je_teil
            stueck_zeilen = tuple((beschriftung, *zeile[von:von + je_teil])
                                  for beschriftung, zeile in zip(umbrochen, block.zeilen))
            raster = Raster(0, 0, stueck_zeilen, spalte, zellbreite, zeilenhoehen,
                            tuple(schritte[von - 1:von - 1 + je_teil]))
            raster = raster._replace(x=(self.breite - raster.breite) // 2)
            self.fluss.dazu(_Kiste(raster.hoehe, (raster,), abstand))
            abstand = px(4)

    def quadrat(self, block):
        """Das Quadrat auf einer eigenen Seite, so gross, wie sie es erlaubt."""
        # Die Beschriftung klein, damit für das Quadrat viel Platz bleibt.
        schrift = self.s.klein
        beschriftung = umbrechen(block.beschriftung, schrift, self.breite) if block.beschriftung else []
        oben = len(beschriftung) * schrift.metrics("linespace") + self.px(6)
        feld = min(self.breite, self.hoehe - oben) // 27
        stuecke = tuple(Zeile(self.breite // 2, nr * schrift.metrics("linespace"), text, "klein",
                              stil.FARBE_TINTE, "tabellentitel", anker="n")
                        for nr, text in enumerate(beschriftung))
        quadrat = Quadrat((self.breite - 27 * feld) // 2, oben, feld)
        self.fluss.dazu(_Kiste(oben + quadrat.kante, stuecke + (quadrat,), neue_seite=True))
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

    def block(self, block, schritte=()):
        """Setzt einen Block aus :mod:`content.handbuch` – mit ``schritte``, wenn er die eines Beispiels trägt."""
        if isinstance(block, buch.Absatz):
            self.absatz(block.text, "betont" if block.betont else "text",
                        art="betont" if block.betont else "absatz")
            if block.text.rstrip().endswith(":"):
                # Ein Absatz mit Doppelpunkt kündigt an, was folgt – er bleibt dabei.
                self.fluss.festhalten()
        elif isinstance(block, buch.Aufzaehlung):
            self.aufzaehlung(block, schritte)
        elif isinstance(block, buch.Tabelle):
            self.tabelle(block, schritte)
        elif isinstance(block, buch.VigenereQuadrat):
            self.quadrat(block)
        elif isinstance(block, buch.Randnotiz):
            self.randnotiz(block)
        else:
            raise TypeError(f"Diesen Block kennt das Handbuch nicht: {block!r}")

    def kapiteltitel(self, seite):
        """Setzt den Titel einer Handbuchseite ganz oben – der erste Absatz bleibt bei ihm."""
        self.absatz(seite.titel, "kapitel", stil.FARBE_ROTSTIFT, "kapitel", vorher=0)
        self.fluss.festhalten()

    def abschnitt(self, abschnitt, nummer):
        """Ein Abschnitt: der Merksatz als Karte, sonst Überschrift und Blöcke.

        ``nummer`` ist die Stelle des Abschnitts auf der Handbuchseite – sie
        steht in den Schrittmarken seines Beispiels.
        """
        if abschnitt.hervorgehoben:
            self.merksatz(abschnitt)
            return
        anfang = len(self.fluss.kisten)
        self.ueberschrift(abschnitt.ueberschrift, marke=("abschnitt", abschnitt.ueberschrift))
        traeger = schritttraeger(abschnitt)
        marken = tuple(Schrittmarke(nummer, nr, schritt) for nr, schritt in enumerate(abschnitt.schritte))
        for nr, block in enumerate(abschnitt.bloecke):
            if block is not traeger:
                self.block(block)
                continue
            teile = len(block.punkte) if isinstance(block, buch.Aufzaehlung) else len(block.zeilen[0]) - 1
            if teile != len(marken):
                raise ValueError(f"{abschnitt.ueberschrift!r}: {len(marken)} Schritte, aber {teile} im Beispiel")
            self.block(block, marken)
            if nr + 1 < len(abschnitt.bloecke):
                # Das Ergebnis bleibt bei den Schritten.
                self.fluss.festhalten()
        kisten = self.fluss.kisten
        hoehe = sum(kiste.vorher + kiste.hoehe for kiste in kisten[anfang + 1:]) + kisten[anfang].hoehe
        if abschnitt.schritte and hoehe <= self.hoehe:
            # Das Beispiel passt auf eine Seite – dann steht es auch auf einer.
            kisten[anfang + 1:] = [kiste._replace(trennbar=False) for kiste in kisten[anfang + 1:]]


def schritttraeger(abschnitt):
    """Der Block, dessen Teile die Schritte des Beispiels sind – oder ``None``, wenn es keine gibt.

    Die nummerierten Punkte, wo es welche gibt, sonst die letzte Tabelle des
    Abschnitts: die Beispieltabelle, deren Spalten die Schritte sind.
    """
    if not abschnitt.schritte:
        return None
    for block in abschnitt.bloecke:
        if isinstance(block, buch.Aufzaehlung) and block.nummeriert:
            return block
    tabellen = [block for block in abschnitt.bloecke if isinstance(block, buch.Tabelle)]
    return tabellen[-1] if tabellen else None


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


def leerseite(breite, hoehe, px, nummer=None):
    """Eine leere Seite – bis auf eine Verzierung in der Mitte, damit sie nicht vergessen aussieht."""
    return Buchseite((Verzierung(px(90), hoehe // 2, breite - px(180)),), nummer)


def einzelseite(teile, schriften, breite, hoehe, px):
    """Setzt ein paar Blöcke auf **eine** Seite – das Werkzeug neben der Übung (Arbeitsplan 6.5).

    ``teile`` sind Blöcke aus :mod:`content.handbuch`; ein ganzer
    :class:`content.handbuch.Abschnitt` wird zur Merksatz-Karte. Was nicht
    mehr auf die Seite passt, fällt weg: Neben der Aufgabe steht nur, wofür
    Platz ist – beim Vigenère-Quadrat ist das die ganze Seite.
    """
    setzer = _Setzer(schriften, breite, hoehe, px)
    for teil in teile:
        if isinstance(teil, buch.Abschnitt):
            setzer.merksatz(teil)
        else:
            setzer.block(teil)
    seiten = seiten_verteilen(setzer.fluss.kisten, hoehe)
    stuecke = []
    for kiste, y in (seiten[0] if seiten else ()):
        stuecke.extend(_verschoben(stueck, y) for stueck in kiste.stuecke)
    return Buchseite(tuple(stuecke))


def setzen(seite, schriften, breite, hoehe, px, stempel=None):
    """Setzt eine Handbuchseite als Buch: Titelseite, dann das Kapitel auf so vielen Seiten wie nötig.

    ``breite`` und ``hoehe`` sind die Textfläche einer Buchseite in Pixeln,
    ``px`` rechnet Pixel aus dem Maßstab 1 um (``Screen.px``), ``stempel``
    ist (Breite, Höhe) des Stempelbilds oder ``None`` ohne Stempel.
    """
    # Das Kapitel läuft in Strecken: Abschnitte hintereinander, die dasselbe
    # Werkzeug gegenüber haben – oder keines. Jede Strecke beginnt auf einer
    # neuen Seite, die mit Werkzeug auf einer linken.
    strecken = []
    for nummer, abschnitt in enumerate(seite.abschnitte):
        if not strecken or abschnitt.gegenueber != strecken[-1][0]:
            strecken.append((abschnitt.gegenueber, []))
        strecken[-1][1].append((nummer, abschnitt))

    rohseiten = []          # je Seite: (Kisten mit ihrem y, Werkzeug) – oder None für eine leere
    for nr, (werkzeug, abschnitte) in enumerate(strecken):
        setzer = _Setzer(schriften, breite, hoehe, px)
        if nr == 0:
            setzer.kapiteltitel(seite)
        for nummer, abschnitt in abschnitte:
            setzer.abschnitt(abschnitt, nummer)
        if werkzeug is None:
            rohseiten += [(kisten, None) for kisten in seiten_verteilen(setzer.fluss.kisten, hoehe)]
            continue
        if len(rohseiten) % 2 == 0:
            # Die nächste Seite wäre eine rechte – sie bleibt leer.
            rohseiten.append(None)
        werkzeugsetzer = _Setzer(schriften, breite, hoehe, px)
        werkzeugsetzer.block(werkzeug)
        # Das Werkzeug passt auf eine Seite; tests/test_handbuch_screen.py prüft das.
        werkzeugseite = seiten_verteilen(werkzeugsetzer.fluss.kisten, hoehe)[0]
        for kisten in seiten_verteilen(setzer.fluss.kisten, hoehe):
            rohseiten += [(kisten, None), (werkzeugseite, werkzeug)]

    seiten, inhalt = [], []
    zahl_y = hoehe + px(SEITENZAHL_ABSTAND)
    for nummer, roh in enumerate(rohseiten, 1):
        if roh is None:
            seiten.append(leerseite(breite, hoehe, px, nummer))
            continue
        kisten, werkzeug = roh
        stuecke = []
        for kiste, y in kisten:
            stuecke.extend(_verschoben(stueck, y) for stueck in kiste.stuecke)
            if kiste.marke[:1] == ("abschnitt",):
                inhalt.append((kiste.marke[1], nummer))
        schritte = tuple(marke for stueck in stuecke for marke in _schrittmarken(stueck))
        stuecke.append(Zeile(breite // 2, zahl_y, f"– {nummer} –", "klein", stil.FARBE_TINTE,
                             "seitenzahl", anker="n"))
        seiten.append(Buchseite(tuple(stuecke), nummer, tuple(dict.fromkeys(schritte)), werkzeug))
    titel = _titelseite(inhalt, schriften, breite, hoehe, px, stempel)
    return Satz((titel, *seiten), tuple(inhalt))
