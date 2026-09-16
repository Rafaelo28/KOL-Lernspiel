"""Der Handbuch-Screen (Arbeitsplan 6.4): Bobs Verschlüsselungshandbuch als Buch.

Zu Beginn jedes Levels liegt Bobs Handbuch aufgeschlagen vor den Spielenden:
ein altes, in Leder gebundenes Buch mit vergilbten Seiten (``grafik/buch.svg``).
Links steht die Titelseite mit dem Inhalt des Kapitels und dem Stempel
"STRENG GEHEIM", rechts beginnt das Kapitel des Levels. Darüber steht der
Einstiegssatz aus der Geschichte ("Du schlägst das Handbuch auf …").

Was auf welcher Seite steht, rechnet :mod:`ui.buchsatz` aus; hier wird es
nur gezeichnet. Das Vigenère-Quadrat auf Seite 3 entsteht aus der Formel
(``crypto/vigenere_quadrat.py``), nicht abgetippt. Hervorheben, welche Zeile
und Spalte gerade gebraucht wird, kommt mit Aufgabe 6.7 dazu – jedes Feld
trägt dafür schon die Tags ``z<Zeile>`` und ``s<Spalte>``.

Blättern
────────
Eine Doppelseite weiter oder zurück geht es mit den Knöpfen unter dem Buch,
den Pfeiltasten (auch Bild auf/ab), dem Mausrad und einem Klick auf die
hochgebogenen Ecken unten außen. Dabei schlägt das Blatt sichtbar um
(``grafik/umblaettern.svg``, abgespielt von :class:`ui.animation.Ablauf`):
Vorwärts liegt die neue rechte Seite schon unter dem Blatt, das umschlägt,
und die neue linke erscheint, wenn es gelandet ist – rückwärts umgekehrt.
Solange es umschlägt, wird nicht noch einmal geblättert; ein schnell
gedrehtes Mausrad blättert so nicht fünf Seiten auf einmal.

Das rote Lesezeichen-Band unten in der Mitte führt zur Tabelle, die man
beim Lösen immer wieder braucht (``lesezeichen`` in ``content/handbuch.py``).

Die Bilder des Umblätterns sind groß – im großen Maßstab rund 50 MB. Sie
werden erst geladen, wenn das Buch schon dasteht, und dann im
Zwischenspeicher des Fensters behalten: Das Handbuch wird zu Beginn jedes
Levels und bei jedem Nachschlagen neu aufgeschlagen.

Nachschlagen während der Aufgaben
─────────────────────────────────
Das Handbuch muss während der Übungen und Funksprüche erreichbar bleiben –
Nachschlagen ist erlaubt. :func:`nachschlagen` zeigt dasselbe Buch mit dem
Knopf "Zurück zur Aufgabe". Die Aufgabe bleibt dabei offen, und ihre Uhr
läuft weiter: Nachschlagen gehört zum Lösen. Den Rückweg gibt der Aufgaben-
Screen als ``zurueck(fenster)`` mit; er baut sich frisch auf und setzt
dieselbe Aufgabe fort, statt eine neue zu stellen – so macht es schon der
Platzhalter der Übung in :mod:`ui.platzhalter`.

Warum eine Leinwand
───────────────────
Ein Buch hat feste Seiten, und der Text liegt auf einem Bild: auf dem
Papier des Buchs, zwischen Stockflecken und Eselsohr. Das kann nur die
Leinwand (``tk.Canvas``) – Text und Linien über einem Bild, Randnotizen
schräg gestellt, und darüber das Blatt, das umschlägt.
"""

import tkinter as tk
from tkinter import font as tkfont

from content import handbuch as buch
from crypto.normalize import ALPHABET
from crypto.vigenere_quadrat import erzeuge_quadrat
from ui import buchsatz, stil
from ui.animation import Ablauf, Animation, Buehne
from ui.screen import Screen

#: Aufschrift des Knopfes zu Beginn eines Levels.
KNOPF_WEITER = "Zu den Übungen"

#: Aufschrift des Knopfes beim Nachschlagen mitten in einer Aufgabe.
KNOPF_ZURUECK = "Zurück zur Aufgabe"

#: Die Knöpfe zum Blättern.
KNOPF_VORBLAETTERN = "Weiterblättern ▶"
KNOPF_ZURUECKBLAETTERN = "◀ Zurückblättern"

#: Die Textflächen der beiden Seiten auf dem Buchbild (x0, y0, x1, y1) – in
#: Pixeln im Maßstab 1, wie alle festen Grössen hier (siehe ui/stil.py, "Der
#: Maßstab"). Das Buchbild ist halb so gross wie seine SVG; dort stehen
#: dieselben Flächen in SVG-Einheiten (``grafik/buch_zeichnen.py``).
TEXT_LINKS = (68, 48, 434, 433)
TEXT_RECHTS = (526, 48, 892, 433)

#: Wo man auf dem Buch klicken kann (x0, y0, x1, y1): die hochgebogenen Ecken
#: unten außen zum Blättern und das Lesezeichen-Band unten in der Mitte.
ECKE_LINKS = (18, 426, 86, 492)
ECKE_RECHTS = (874, 426, 942, 492)
BAND = (466, 414, 502, 492)

#: So lange nach dem Aufschlagen werden die Bilder des Umblätterns geladen –
#: erst steht das Buch da, dann kommt, was man erst beim Blättern braucht.
VORLADEN_MS = 150

#: Die Beschriftung am Lesezeichen, wenn die Maus darüber steht.
LESEZEICHEN = "zum Lesezeichen"

#: So breit dürfen die Zeilen über dem Buch werden: so breit wie das Buch.
#: Im grossen Maßstab dürfen sie breiter werden – siehe
#: :meth:`Handbuch._textbreite`.
TEXTBREITE = 960

#: Abstand des Screens nach oben und unten und der Knöpfe zum Buch – knapp,
#: weil das Buch fast die ganze Höhe braucht.
ABSTAND_KNAPP = 4


def nachschlagen(fenster, level, zurueck):
    """Schlägt das Handbuch mitten in einer Aufgabe auf.

    ``zurueck(fenster)`` ist der Weg zurück zur Aufgabe. Die Aufgabe bleibt
    offen, ihre Uhr läuft weiter – Nachschlagen gehört zum Lösen.
    """
    return fenster.zeige(Handbuch, level=level, danach=zurueck, knopf=KNOPF_ZURUECK)


class Handbuch(Screen):
    """Das Handbuch eines Levels. ``danach(fenster)`` ist, was der Knopf unten rechts tut.

    ``einleitung`` sind Absätze über dem Buch (der Einstieg ins Level),
    ``hinweis`` eine Zeile davor – etwa, dass die Zeit des letzten Levels
    abgelaufen ist.
    """

    def __init__(self, fenster, level, danach, knopf=KNOPF_WEITER, hinweis="", einleitung=()):
        super().__init__(fenster)
        self.configure(bg=stil.FARBE_NACHT, pady=self.px(ABSTAND_KNAPP))
        self.titel = f"Handbuch – Level {level}"
        self.seite = buch.SEITE_NACH_LEVEL[level]
        self._danach = danach
        self._doppelseite = 0
        self._ablauf = None
        self._unter_maus = None
        self._quadratschriften = {}

        self._hinweis = self._zeile(hinweis, stil.FARBE_WARNUNG, stil.SCHRIFT_FETT)
        self._einleitung = [self._zeile(absatz, stil.FARBE_SAND, stil.SCHRIFT_ERZAEHLUNG)
                            for absatz in einleitung]

        #: Die Leinwand mit dem aufgeschlagenen Buch.
        self.buch = Buehne(self, Animation("buch", massstab=self.massstab), bg=stil.FARBE_NACHT,
                           takefocus=True)
        self.buch.pack(side="top")
        stempel = Animation("stempel", massstab=self.massstab)
        self._stempelbild = tk.PhotoImage(master=self, file=str(stempel.ordner / stempel.hintergrund))

        #: Die Schriften des Buchs – gesetzt und gezeichnet wird mit denselben.
        self.schriften = buchsatz.schriften(self, self.massstab)
        x0, y0, x1, y1 = self.flaeche("links")
        #: Das gesetzte Kapitel: welche Stücke auf welcher Seite stehen.
        self.satz = buchsatz.setzen(self.seite, self.schriften, x1 - x0, y1 - y0, self.px,
                                    stempel=(self._stempelbild.width(), self._stempelbild.height()))

        self._leiste_bauen(knopf)
        self._bedienung_binden()
        self._seiten_zeichnen()
        self._leiste_aktualisieren()

    # ── Was dasteht ────────────────────────────────────────────────────────

    @property
    def hinweis(self):
        return self._hinweis.cget("text") if self._hinweis else ""

    @property
    def einleitung(self):
        return tuple(zeile.cget("text") for zeile in self._einleitung)

    @property
    def knopftext(self):
        return self._knopf.cget("text")

    @property
    def doppelseite(self):
        """Die aufgeschlagene Doppelseite, ab 0. Die erste zeigt links die Titelseite."""
        return self._doppelseite

    @property
    def anzahl_doppelseiten(self):
        return (len(self.satz.seiten) + 1) // 2

    @property
    def seitenanzeige(self):
        return self._seitenanzeige.cget("text")

    def flaeche(self, seite):
        """Die Textfläche der linken oder rechten Seite auf der Leinwand: (x0, y0, x1, y1)."""
        return tuple(self.px(wert) for wert in (TEXT_LINKS if seite == "links" else TEXT_RECHTS))

    def texte(self, seite=None):
        """Die Texte, die gerade im Buch stehen – auf der ``seite`` "links" oder "rechts", sonst auf beiden."""
        auswahl = f"text&&{seite}" if seite else "text"
        return [self.buch.itemcget(element, "text") for element in self.buch.find_withtag(auswahl)]

    def quadratfeld(self, schluesselbuchstabe, nachrichtenbuchstabe):
        """Was im gezeichneten Quadrat in dieser Zeile und Spalte steht (es muss aufgeschlagen sein)."""
        zeile, spalte = ALPHABET.index(schluesselbuchstabe), ALPHABET.index(nachrichtenbuchstabe)
        (element,) = self.buch.find_withtag(f"feld&&z{zeile}&&s{spalte}")
        return self.buch.itemcget(element, "text")

    # ── Bauen ──────────────────────────────────────────────────────────────

    def _zeile(self, text, farbe, schrift):
        if not text:
            return None
        # Ohne Abstand darunter: Hinweis und Einstieg lesen sich wie ein Absatz,
        # und um den Einband ist im Bild selbst schon ein Rand Nachthimmel.
        zeile = tk.Label(self, text=text, bg=stil.FARBE_NACHT, fg=farbe, font=schrift, anchor="w",
                         justify="left", wraplength=self._textbreite())
        zeile.pack(side="top", fill="x")
        return zeile

    def _textbreite(self):
        """So breit dürfen die Zeilen über dem Buch werden.

        Im kleinen Maßstab so breit wie das Buch – das Fenster ist dort nur
        wenig breiter. Im grossen so breit wie der Bildschirm: Ein 1080p-Monitor
        hat links und rechts vom Buch je 240 Pixel Platz, aber in der Höhe
        zählt jede Zeile – ist die Zeit des letzten Levels abgelaufen, stehen
        Hinweis und Einstieg über dem Buch, und beide müssen mit ihm auf den
        Bildschirm passen (tests/test_handbuch_screen.py).
        """
        if self.massstab == 1:
            return self.px(TEXTBREITE)
        return max(self.px(TEXTBREITE), self.winfo_screenwidth() - 2 * self.px(stil.ABSTAND) - self.px(8))

    def _leiste_bauen(self, knopf):
        leiste = tk.Frame(self, bg=stil.FARBE_NACHT)
        leiste.pack(side="top", fill="x", pady=(self.px(ABSTAND_KNAPP), 0))
        knopfart = dict(font=stil.SCHRIFT_FETT, highlightbackground=stil.FARBE_NACHT)
        self._zurueckblaettern = tk.Button(leiste, text=KNOPF_ZURUECKBLAETTERN,
                                           command=lambda: self._per_knopf(-1), **knopfart)
        self._zurueckblaettern.pack(side="left")
        self._vorblaettern = tk.Button(leiste, text=KNOPF_VORBLAETTERN, command=lambda: self._per_knopf(1),
                                       **knopfart)
        self._vorblaettern.pack(side="left", padx=(self.px(8), 0))
        self._seitenanzeige = tk.Label(leiste, bg=stil.FARBE_NACHT, fg=stil.FARBE_DUENE,
                                       font=stil.SCHRIFT_KURSIV)
        self._seitenanzeige.pack(side="left", padx=self.px(stil.ABSTAND))
        self._knopf = tk.Button(leiste, text=knopf, command=self.weiter, padx=self.px(stil.ABSTAND), **knopfart)
        self._knopf.pack(side="right")
        self._knopf.bind("<Return>", lambda _ereignis: self._knopf.invoke())

    def _bedienung_binden(self):
        leinwand = self.buch
        for taste, richtung in (("<Left>", -1), ("<Prior>", -1), ("<Right>", 1), ("<Next>", 1)):
            leinwand.bind(taste, lambda _ereignis, richtung=richtung: self.blaettern(richtung))
        leinwand.bind("<MouseWheel>", self._mausrad)
        leinwand.bind("<Button-4>", lambda _ereignis: self.blaettern(-1))
        leinwand.bind("<Button-5>", lambda _ereignis: self.blaettern(1))
        leinwand.bind("<Button-1>", lambda ereignis: self.klicken(ereignis.x, ereignis.y))
        leinwand.bind("<Motion>", lambda ereignis: self._maus_ueber(self.ziel(ereignis.x, ereignis.y)))
        leinwand.bind("<Leave>", lambda _ereignis: self._maus_ueber(None))

    def _leiste_aktualisieren(self):
        self._zurueckblaettern.configure(state="normal" if self._doppelseite > 0 else "disabled")
        weiter_moeglich = self._doppelseite < self.anzahl_doppelseiten - 1
        self._vorblaettern.configure(state="normal" if weiter_moeglich else "disabled")
        self._seitenanzeige.configure(text=f"Doppelseite {self._doppelseite + 1} von {self.anzahl_doppelseiten}")

    # ── Zeichnen ───────────────────────────────────────────────────────────

    def _seiten_zeichnen(self):
        self._seite_zeichnen("links")
        self._seite_zeichnen("rechts")

    def _seite_zeichnen(self, seite):
        """Zeichnet die linke oder rechte Seite der aufgeschlagenen Doppelseite neu."""
        self.buch.delete(seite)
        x0, y0, x1, y1 = self.flaeche(seite)
        nr = 2 * self._doppelseite + (seite == "rechts")
        tags = ("seite", seite)
        if nr < len(self.satz.seiten):
            for stueck in self.satz.seiten[nr].stuecke:
                self._stueck_zeichnen(stueck, x0, y0, tags)
        else:
            # Die letzte Seite eines Kapitels bleibt leer – bis auf eine Verzierung.
            self._verzierung_zeichnen(buchsatz.Verzierung(self.px(90), (y1 - y0) // 2, x1 - x0 - self.px(180)),
                                      x0, y0, tags)
        # Was die Maus gerade zeigt, bleibt obenauf.
        self.buch.tag_raise("maus")

    def _stueck_zeichnen(self, stueck, x0, y0, tags):
        if isinstance(stueck, buchsatz.Zeile):
            ausrichtung = {"n": "center", "ne": "right"}.get(stueck.anker, "left")
            self.buch.create_text(x0 + stueck.x, y0 + stueck.y, text=stueck.text, anchor=stueck.anker,
                                  justify=ausrichtung, angle=stueck.winkel, fill=stueck.farbe,
                                  font=getattr(self.schriften, stueck.schrift), tags=tags + ("text", stueck.art))
        elif isinstance(stueck, buchsatz.Karte):
            self._karte_zeichnen(stueck, x0, y0, tags)
        elif isinstance(stueck, buchsatz.Raster):
            self._raster_zeichnen(stueck, x0, y0, tags)
        elif isinstance(stueck, buchsatz.Quadrat):
            self._quadrat_zeichnen(stueck, x0, y0, tags)
        elif isinstance(stueck, buchsatz.Verzierung):
            self._verzierung_zeichnen(stueck, x0, y0, tags)
        elif isinstance(stueck, buchsatz.Punktlinie):
            # Einzelne Pünktchen statt einer gestrichelten Linie: Striche mit
            # eigenem Muster zeichnet Tk unter Windows nur ungefähr.
            schritt, groesse = self.px(5), max(1, self.px(1))
            for x in range(x0 + stueck.x0, x0 + stueck.x1, schritt):
                self.buch.create_rectangle(x, y0 + stueck.y - groesse, x + groesse, y0 + stueck.y,
                                           fill=stil.FARBE_TINTE, outline="", tags=tags)
        elif isinstance(stueck, buchsatz.Stempel):
            self.buch.create_image(x0 + stueck.x, y0 + stueck.y, image=self._stempelbild, anchor="nw",
                                   tags=tags + ("stempel",))
        else:
            raise TypeError(f"Dieses Stück kennt das Handbuch nicht: {stueck!r}")

    def _karte_zeichnen(self, karte, x0, y0, tags):
        """Die Merksatz-Karte: ein Stück Papier, oben mit Klebeband ins Buch geklebt."""
        px, leinwand = self.px, self.buch
        x, y = x0 + karte.x, y0 + karte.y
        schatten = px(buchsatz.KARTENSCHATTEN)
        leinwand.create_rectangle(x + schatten, y + schatten, x + karte.breite + schatten,
                                  y + karte.hoehe + schatten, fill=stil.FARBE_PAPIERLINIE, outline="", tags=tags)
        leinwand.create_rectangle(x, y, x + karte.breite, y + karte.hoehe, fill=stil.FARBE_MERKSATZ,
                                  outline=stil.FARBE_KARTENKANTE, tags=tags + ("karte",))
        # Das Klebeband: etwas schief über der Oberkante – so weit, wie der Satz Platz gelassen hat.
        schief = px(3)
        mitte, halb_b, halb_h = x + karte.breite / 2, px(34), px(buchsatz.KLEBEBAND_UEBERSTAND) - schief
        leinwand.create_polygon(mitte - halb_b, y - halb_h + schief, mitte + halb_b, y - halb_h - schief,
                                mitte + halb_b, y + halb_h - schief, mitte - halb_b, y + halb_h + schief,
                                fill=stil.FARBE_KLEBEBAND, outline=stil.FARBE_PAPIERLINIE, tags=tags)

    def _raster_zeichnen(self, raster, x0, y0, tags):
        """Eine Tabelle: vorne die Beschriftung auf dunklerem Grund, dahinter die Buchstaben."""
        px, leinwand = self.px, self.buch
        x, y = x0 + raster.x, y0 + raster.y
        breite, hoehe = raster.breite, raster.hoehe
        leinwand.create_rectangle(x, y, x + raster.beschriftungsbreite, y + hoehe, fill=stil.FARBE_PAPIER_DUNKEL,
                                  outline="", tags=tags)
        for nr, (beschriftung, *zellen) in enumerate(raster.zeilen):
            mitte = y + raster.oben(nr) + raster.zeilenhoehen[nr] / 2
            leinwand.create_text(x + px(buchsatz.ZELLRAND + 2), mitte, text=beschriftung, anchor="w",
                                 font=self.schriften.text, fill=stil.FARBE_TINTE,
                                 tags=tags + ("text", "beschriftung"))
            for spalte, zelle in enumerate(zellen):
                leinwand.create_text(x + raster.beschriftungsbreite + (spalte + .5) * raster.zellbreite, mitte,
                                     text=zelle, font=self.schriften.text, fill=stil.FARBE_TINTE,
                                     tags=tags + ("text", "zelle"))
        for nr in range(len(raster.zeilen) + 1):
            leinwand.create_line(x, y + raster.oben(nr), x + breite, y + raster.oben(nr),
                                 fill=stil.FARBE_BUCHLINIE, tags=tags)
        for spalte in range(len(raster.zeilen[0])):
            links = x + (raster.beschriftungsbreite + (spalte - 1) * raster.zellbreite if spalte else 0)
            leinwand.create_line(links, y, links, y + hoehe, fill=stil.FARBE_BUCHLINIE, tags=tags)
        leinwand.create_line(x + breite, y, x + breite, y + hoehe, fill=stil.FARBE_BUCHLINIE, tags=tags)

    def _quadratschrift(self, feld, fett):
        """Eine Schrift, deren Buchstaben in ein Feld des Quadrats passen – in Pixeln, nicht Punkt."""
        schluessel = (feld, fett)
        if schluessel not in self._quadratschriften:
            self._quadratschriften[schluessel] = tkfont.Font(
                root=self, family=self.schriften.text.actual("family"), size=-round(feld * .62),
                weight="bold" if fett else "normal")
        return self._quadratschriften[schluessel]

    def _quadrat_zeichnen(self, quadrat, x0, y0, tags):
        """Das Vigenère-Quadrat: Kopfzeile Nachricht, Kopfspalte Schlüssel, 26 × 26 Felder.

        Jedes Feld trägt die Tags ``z<Zeile>`` und ``s<Spalte>`` (ab 0) – damit
        lässt es sich finden und später hervorheben (Aufgabe 6.7).
        """
        leinwand, feld = self.buch, quadrat.feld
        x, y = x0 + quadrat.x, y0 + quadrat.y
        kante = quadrat.kante
        normal, fett = self._quadratschrift(feld, False), self._quadratschrift(feld, True)
        leinwand.create_rectangle(x, y, x + kante, y + feld, fill=stil.FARBE_PAPIER_DUNKEL, width=0, tags=tags)
        leinwand.create_rectangle(x, y, x + feld, y + kante, fill=stil.FARBE_PAPIER_DUNKEL, width=0, tags=tags)
        mitte = feld / 2
        for nr, buchstabe in enumerate(ALPHABET, 1):
            leinwand.create_text(x + nr * feld + mitte, y + mitte, text=buchstabe, font=fett,
                                 fill=stil.FARBE_ROTSTIFT, tags=tags + ("kopfzeile", f"s{nr - 1}"))
            leinwand.create_text(x + mitte, y + nr * feld + mitte, text=buchstabe, font=fett,
                                 fill=stil.FARBE_ROTSTIFT, tags=tags + ("kopfspalte", f"z{nr - 1}"))
        for zeile, reihe in enumerate(erzeuge_quadrat()):
            for spalte, buchstabe in enumerate(reihe):
                leinwand.create_text(x + (spalte + 1) * feld + mitte, y + (zeile + 1) * feld + mitte,
                                     text=buchstabe, font=normal, fill=stil.FARBE_TINTE,
                                     tags=tags + ("feld", f"z{zeile}", f"s{spalte}"))
        for nr in range(28):
            staerke = 2 if nr in (0, 1, 27) else 1
            leinwand.create_line(x + nr * feld, y, x + nr * feld, y + kante, fill=stil.FARBE_BUCHLINIE,
                                 width=staerke, tags=tags)
            leinwand.create_line(x, y + nr * feld, x + kante, y + nr * feld, fill=stil.FARBE_BUCHLINIE,
                                 width=staerke, tags=tags)

    def _verzierung_zeichnen(self, verzierung, x0, y0, tags):
        """Eine feine Linie mit einem kleinen Diamanten in der Mitte."""
        px, leinwand = self.px, self.buch
        x, y = x0 + verzierung.x, y0 + verzierung.y
        mitte, r = x + verzierung.breite / 2, px(5)
        leinwand.create_line(x, y, mitte - 2 * r, y, fill=stil.FARBE_BUCHLINIE, tags=tags)
        leinwand.create_line(mitte + 2 * r, y, x + verzierung.breite, y, fill=stil.FARBE_BUCHLINIE, tags=tags)
        leinwand.create_polygon(mitte, y - 1.4 * r, mitte + r, y, mitte, y + 1.4 * r, mitte - r, y,
                                fill=stil.FARBE_ROTSTIFT, outline="", tags=tags + ("diamant",))

    # ── Blättern ───────────────────────────────────────────────────────────

    @property
    def blaettert(self):
        """Schlägt gerade ein Blatt um?"""
        return self._ablauf is not None and self._ablauf.laeuft

    def blaettern(self, richtung, animiert=True):
        """Eine Doppelseite weiter (1) oder zurück (-1). ``False``, wenn es dort nicht weitergeht."""
        return self.aufschlagen(self._doppelseite + richtung, animiert)

    def aufschlagen(self, nr, animiert=True):
        """Schlägt die Doppelseite ``nr`` (ab 0) auf – mit Umblättern, wenn ``animiert``.

        ``False``, wenn es sie nicht gibt, sie schon aufgeschlagen ist oder
        gerade ein Blatt umschlägt.
        """
        if not 0 <= nr < self.anzahl_doppelseiten or nr == self._doppelseite or self.blaettert:
            return False
        vorwaerts = nr > self._doppelseite
        self._doppelseite = nr
        self._leiste_aktualisieren()
        self._maus_ueber(None)
        ablauf = self._umblaettern() if animiert else None
        if ablauf is None:
            self._seiten_zeichnen()
            return True
        # Vorwärts liegt die neue rechte Seite schon unter dem Blatt, das
        # umschlägt, und die linke kommt, wenn es gelandet ist. Rückwärts
        # umgekehrt: Das Blatt liegt anfangs links und landet rechts.
        zuerst, zuletzt = ("rechts", "links") if vorwaerts else ("links", "rechts")
        self._seite_zeichnen(zuerst)
        ablauf.abspielen(rueckwaerts=not vorwaerts, danach=lambda: self._seite_zeichnen(zuletzt))
        return True

    def zum_lesezeichen(self, animiert=True):
        """Schlägt die Doppelseite auf, in der das Lesezeichen liegt."""
        return self.aufschlagen(self.satz.lesezeichen // 2, animiert)

    def _umblaettern(self):
        """Der Ablauf, der ein Blatt umschlagen lässt – oder ``None``, wenn seine Bilder fehlen.

        Ohne Bilder wird eben ohne Umschlagen geblättert: Das Handbuch muss
        auch dann lesbar bleiben.
        """
        if self._ablauf is None:
            speicher = self.fenster.zwischenspeicher
            schluessel = ("umblaettern", self.massstab)
            try:
                animation = Animation("umblaettern", massstab=self.massstab)
                self._ablauf = Ablauf(self.buch, animation, bilder=speicher.get(schluessel))
            except (OSError, ValueError, tk.TclError):
                return None
            speicher[schluessel] = self._ablauf.bilder
        return self._ablauf

    # ── Maus und Tasten ────────────────────────────────────────────────────

    def _per_knopf(self, richtung):
        self.blaettern(richtung)
        # Danach sollen die Pfeiltasten gleich wieder im Buch blättern.
        self.buch.focus_set()

    def _mausrad(self, ereignis):
        # Windows meldet je Raste 120, macOS und Touchpads kleinere Werte.
        if ereignis.delta:
            self.blaettern(-1 if ereignis.delta > 0 else 1)

    def ziel(self, x, y):
        """Was ein Klick an dieser Stelle der Leinwand täte: "vor", "zurueck", "lesezeichen" oder ``None``."""
        def drin(bereich):
            x0, y0, x1, y1 = (self.px(wert) for wert in bereich)
            return x0 <= x <= x1 and y0 <= y <= y1

        if drin(ECKE_RECHTS) and self._doppelseite < self.anzahl_doppelseiten - 1:
            return "vor"
        if drin(ECKE_LINKS) and self._doppelseite > 0:
            return "zurueck"
        if drin(BAND) and self.satz.lesezeichen // 2 != self._doppelseite:
            return "lesezeichen"
        return None

    def klicken(self, x, y):
        """Ein Klick auf die Leinwand bei ``x, y``."""
        self.buch.focus_set()
        ziel = self.ziel(x, y)
        if ziel == "vor":
            self.blaettern(1)
        elif ziel == "zurueck":
            self.blaettern(-1)
        elif ziel == "lesezeichen":
            self.zum_lesezeichen()

    def _maus_ueber(self, ziel):
        """Zeigt, dass sich hier etwas tut: Hand als Zeiger, ein Pfeil an der Ecke, ein Wort am Band."""
        if ziel == self._unter_maus:
            return
        self._unter_maus = ziel
        px, leinwand = self.px, self.buch
        leinwand.delete("maus")
        leinwand.configure(cursor="hand2" if ziel else "")
        if ziel in ("vor", "zurueck"):
            spitze, hinten = (px(912), px(898)) if ziel == "vor" else (px(48), px(62))
            mitte = px(420)
            leinwand.create_polygon(hinten, mitte - px(7), spitze, mitte, hinten, mitte + px(7),
                                    fill=stil.FARBE_ROTSTIFT, outline="", tags=("maus",))
        elif ziel == "lesezeichen":
            leinwand.create_text(px(508), px(470), text=LESEZEICHEN, anchor="w", font=self.schriften.klein,
                                 fill=stil.FARBE_ROTSTIFT, tags=("maus",))

    # ── Screen ─────────────────────────────────────────────────────────────

    def beim_anzeigen(self):
        # Mit dem Fokus auf dem Buch blättern die Pfeiltasten.
        self.buch.focus_set()
        self.spaeter(VORLADEN_MS, self._umblaettern)

    def beim_verlassen(self):
        if self._ablauf is not None:
            self._ablauf.abbrechen()

    def weiter(self):
        """Zu den Übungen – oder zurück zur Aufgabe, wenn nachgeschlagen wurde."""
        self._danach(self.fenster)
