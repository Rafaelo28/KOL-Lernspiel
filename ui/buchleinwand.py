"""Die Leinwand mit dem aufgeschlagenen Buch (Arbeitsplan 6.4 und 6.5).

Zwei Screens teilen sich dieses Bauteil:

* Das **Handbuch** (:mod:`ui.handbuch`) blättert darin – links und rechts
  stehen die gesetzten Seiten aus :mod:`ui.buchsatz`.
* Der **Aufgaben-Screen** (:mod:`ui.uebung`) legt links das Werkzeug zum
  Lösen auf und schreibt rechts die Übung hin.

Hier steht alles, was beide brauchen: das Bild des Buchs (``grafik/buch.svg``),
die Schriften, die Stempel und das Zeichnen der Stücke, die der Satz
ausgerechnet hat. Was ein Screen daraus macht – blättern, schreiben,
nachschlagen –, steht in ihm selbst.

Die Seiten heissen "links" und "rechts". Jedes gezeichnete Stück trägt den
Namen seiner Seite als Tag; :meth:`Buchleinwand.seite_zeichnen` räumt damit
eine Seite ab, ohne die andere anzufassen. Text trägt zusätzlich den Tag
``text`` und seine Art ("absatz", "notiz", "zelle" …) – daran hängen die Tests.

Markiert wird mit Textmarker: unter der Schrift, aber über dem Papier. Die
Markierungen tragen den Tag ``markierung`` und verschwinden mit ihrer Seite.
"""

import tkinter as tk
from tkinter import font as tkfont

from crypto.normalize import ALPHABET
from crypto.vigenere_quadrat import erzeuge_quadrat
from ui import buchsatz, stil
from ui.animation import Animation, Buehne

#: Die Textflächen der beiden Seiten auf dem Buchbild (x0, y0, x1, y1) – in
#: Pixeln im Maßstab 1, wie alle festen Grössen hier (siehe ui/stil.py, "Der
#: Maßstab"). Das Buchbild ist halb so gross wie seine SVG; dort stehen
#: dieselben Flächen in SVG-Einheiten (``grafik/buch_zeichnen.py``).
TEXT_LINKS = (68, 48, 434, 433)
TEXT_RECHTS = (526, 48, 892, 433)

#: Die Seiten, die zugleich Tag jedes Stücks auf ihnen sind.
SEITEN = ("links", "rechts")

#: So weit steht der Textmarker links und rechts über den Text hinaus.
MARKERRAND = 3


class Buchleinwand(Buehne):
    """Das aufgeschlagene Buch als Leinwand: Bild, Schriften, Stempel, Zeichnen.

    ``px`` rechnet Pixelangaben in den Maßstab des Fensters um – dieselbe
    Funktion, die auch der Screen benutzt (``Screen.px``).
    """

    def __init__(self, master, massstab, px, **optionen):
        self.px = px
        self._massstab = massstab
        self._stempelbilder = {}
        self._quadratschriften = {}
        optionen.setdefault("bg", stil.FARBE_NACHT)
        super().__init__(master, Animation("buch", massstab=massstab), **optionen)
        #: Die Schriften des Buchs – gesetzt und gezeichnet wird mit denselben.
        self.schriften = buchsatz.schriften(self, massstab)

    # ── Masse und Bilder ───────────────────────────────────────────────────

    def flaeche(self, seite):
        """Die Textfläche der linken oder rechten Seite auf der Leinwand: (x0, y0, x1, y1)."""
        return tuple(self.px(wert) for wert in (TEXT_LINKS if seite == "links" else TEXT_RECHTS))

    def stempelbild(self, name):
        """Ein Stempelbild aus ``content/animationen/`` – geladen, wenn es zum ersten Mal gebraucht wird."""
        if name not in self._stempelbilder:
            stempel = Animation(name, massstab=self._massstab)
            self._stempelbilder[name] = tk.PhotoImage(
                master=self, file=str(stempel.ordner / stempel.hintergrund))
        return self._stempelbilder[name]

    def stempel_zeichnen(self, name, x, y, tags=()):
        """Setzt einen Stempel mit seiner Mitte auf ``x, y``."""
        return self.create_image(x, y, image=self.stempelbild(name), anchor="center",
                                 tags=tuple(tags) + ("stempel",))

    # ── Lesen (für Tests und Screens) ──────────────────────────────────────

    def texte(self, seite=None):
        """Die Texte, die gerade im Buch stehen – auf einer Seite oder auf beiden."""
        auswahl = f"text&&{seite}" if seite else "text"
        return [self.itemcget(element, "text") for element in self.find_withtag(auswahl)]

    def quadratfeld(self, schluesselbuchstabe, nachrichtenbuchstabe):
        """Was im gezeichneten Quadrat in dieser Zeile und Spalte steht (es muss aufgeschlagen sein)."""
        zeile, spalte = ALPHABET.index(schluesselbuchstabe), ALPHABET.index(nachrichtenbuchstabe)
        (element,) = self.find_withtag(f"feld&&z{zeile}&&s{spalte}")
        return self.itemcget(element, "text")

    # ── Zeichnen ───────────────────────────────────────────────────────────

    def seite_zeichnen(self, seite, stuecke, tags=()):
        """Zeichnet eine Seite neu: erst das Alte weg, dann die ``stuecke`` hin."""
        self.delete(seite)
        x0, y0, _, _ = self.flaeche(seite)
        marken = ("seite", seite) + tuple(tags)
        for stueck in stuecke:
            self.stueck_zeichnen(stueck, x0, y0, marken)

    def stueck_zeichnen(self, stueck, x0, y0, tags):
        """Zeichnet ein Stück aus :mod:`ui.buchsatz` mit der Ecke (``x0``, ``y0``) als Ursprung."""
        if isinstance(stueck, buchsatz.Zeile):
            ausrichtung = {"n": "center", "ne": "right"}.get(stueck.anker, "left")
            self.create_text(x0 + stueck.x, y0 + stueck.y, text=stueck.text, anchor=stueck.anker,
                             justify=ausrichtung, angle=stueck.winkel, fill=stueck.farbe,
                             font=getattr(self.schriften, stueck.schrift), tags=tags + ("text", stueck.art))
        elif isinstance(stueck, buchsatz.Karte):
            self._karte_zeichnen(stueck, x0, y0, tags)
        elif isinstance(stueck, buchsatz.Raster):
            self._raster_zeichnen(stueck, x0, y0, tags)
        elif isinstance(stueck, buchsatz.Quadrat):
            self._quadrat_zeichnen(stueck, x0, y0, tags)
        elif isinstance(stueck, buchsatz.Verzierung):
            self.verzierung_zeichnen(stueck, x0, y0, tags)
        elif isinstance(stueck, buchsatz.Punktlinie):
            # Einzelne Pünktchen statt einer gestrichelten Linie: Striche mit
            # eigenem Muster zeichnet Tk unter Windows nur ungefähr.
            schritt, groesse = self.px(5), max(1, self.px(1))
            for x in range(x0 + stueck.x0, x0 + stueck.x1, schritt):
                self.create_rectangle(x, y0 + stueck.y - groesse, x + groesse, y0 + stueck.y,
                                      fill=stil.FARBE_TINTE, outline="", tags=tags)
        elif isinstance(stueck, buchsatz.Stempel):
            self.create_image(x0 + stueck.x, y0 + stueck.y, image=self.stempelbild(stueck.name), anchor="nw",
                              tags=tags + ("stempel",))
        else:
            raise TypeError(f"Dieses Stück kennt das Buch nicht: {stueck!r}")

    def _karte_zeichnen(self, karte, x0, y0, tags):
        """Die Merksatz-Karte: ein Stück Papier, oben mit Klebeband ins Buch geklebt."""
        px = self.px
        x, y = x0 + karte.x, y0 + karte.y
        schatten = px(buchsatz.KARTENSCHATTEN)
        self.create_rectangle(x + schatten, y + schatten, x + karte.breite + schatten,
                              y + karte.hoehe + schatten, fill=stil.FARBE_PAPIERLINIE, outline="", tags=tags)
        self.create_rectangle(x, y, x + karte.breite, y + karte.hoehe, fill=stil.FARBE_MERKSATZ,
                              outline=stil.FARBE_KARTENKANTE, tags=tags + ("karte",))
        # Das Klebeband: etwas schief über der Oberkante – so weit, wie der Satz Platz gelassen hat.
        schief = px(3)
        mitte, halb_b, halb_h = x + karte.breite / 2, px(34), px(buchsatz.KLEBEBAND_UEBERSTAND) - schief
        self.create_polygon(mitte - halb_b, y - halb_h + schief, mitte + halb_b, y - halb_h - schief,
                            mitte + halb_b, y + halb_h - schief, mitte - halb_b, y + halb_h + schief,
                            fill=stil.FARBE_KLEBEBAND, outline=stil.FARBE_PAPIERLINIE, tags=tags)

    def _raster_zeichnen(self, raster, x0, y0, tags):
        """Eine Tabelle: vorne die Beschriftung auf dunklerem Grund, dahinter die Buchstaben."""
        px = self.px
        x, y = x0 + raster.x, y0 + raster.y
        breite, hoehe = raster.breite, raster.hoehe
        if raster.beschriftungsbreite:
            self.create_rectangle(x, y, x + raster.beschriftungsbreite, y + hoehe,
                                  fill=stil.FARBE_PAPIER_DUNKEL, outline="", tags=tags)
        for nr, (beschriftung, *zellen) in enumerate(raster.zeilen):
            mitte = y + raster.oben(nr) + raster.zeilenhoehen[nr] / 2
            if beschriftung:
                self.create_text(x + px(buchsatz.ZELLRAND + 2), mitte, text=beschriftung, anchor="w",
                                 font=self.schriften.text, fill=stil.FARBE_TINTE,
                                 tags=tags + ("text", "beschriftung"))
            for spalte, zelle in enumerate(zellen):
                self.create_text(x + raster.beschriftungsbreite + (spalte + .5) * raster.zellbreite, mitte,
                                 text=zelle, font=self.schriften.text, fill=stil.FARBE_TINTE,
                                 tags=tags + ("text", "zelle"))
        for nr in range(len(raster.zeilen) + 1):
            self.create_line(x, y + raster.oben(nr), x + breite, y + raster.oben(nr),
                             fill=stil.FARBE_BUCHLINIE, tags=tags)
        for spalte in range(len(raster.zeilen[0])):
            if spalte == 1 and not raster.beschriftungsbreite:
                continue                      # ohne Beschriftungsspalte gibt es dort keine Linie
            links = x + (raster.beschriftungsbreite + (spalte - 1) * raster.zellbreite if spalte else 0)
            self.create_line(links, y, links, y + hoehe, fill=stil.FARBE_BUCHLINIE, tags=tags)
        self.create_line(x + breite, y, x + breite, y + hoehe, fill=stil.FARBE_BUCHLINIE, tags=tags)

    def quadratschrift(self, feld, fett=False):
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
        feld = quadrat.feld
        x, y = x0 + quadrat.x, y0 + quadrat.y
        kante = quadrat.kante
        normal, fett = self.quadratschrift(feld), self.quadratschrift(feld, fett=True)
        self.create_rectangle(x, y, x + kante, y + feld, fill=stil.FARBE_PAPIER_DUNKEL, width=0, tags=tags)
        self.create_rectangle(x, y, x + feld, y + kante, fill=stil.FARBE_PAPIER_DUNKEL, width=0, tags=tags)
        mitte = feld / 2
        for nr, buchstabe in enumerate(ALPHABET, 1):
            self.create_text(x + nr * feld + mitte, y + mitte, text=buchstabe, font=fett,
                             fill=stil.FARBE_ROTSTIFT, tags=tags + ("kopfzeile", f"s{nr - 1}"))
            self.create_text(x + mitte, y + nr * feld + mitte, text=buchstabe, font=fett,
                             fill=stil.FARBE_ROTSTIFT, tags=tags + ("kopfspalte", f"z{nr - 1}"))
        for zeile, reihe in enumerate(erzeuge_quadrat()):
            for spalte, buchstabe in enumerate(reihe):
                self.create_text(x + (spalte + 1) * feld + mitte, y + (zeile + 1) * feld + mitte,
                                 text=buchstabe, font=normal, fill=stil.FARBE_TINTE,
                                 tags=tags + ("feld", f"z{zeile}", f"s{spalte}"))
        for nr in range(28):
            staerke = 2 if nr in (0, 1, 27) else 1
            self.create_line(x + nr * feld, y, x + nr * feld, y + kante, fill=stil.FARBE_BUCHLINIE,
                             width=staerke, tags=tags)
            self.create_line(x, y + nr * feld, x + kante, y + nr * feld, fill=stil.FARBE_BUCHLINIE,
                             width=staerke, tags=tags)

    # ── Markieren ──────────────────────────────────────────────────────────

    def schrittflaechen(self, seite, stuecke):
        """Wo die Schritte eines Beispiels auf der Seite stehen: je Schrittmarke ihre Rechtecke (x0, y0, x1, y1).

        Eine Textzeile gibt ein Rechteck so breit wie ihr Text – die Nummer
        davor eingeschlossen – und so hoch wie ihre Schrift. In einer
        Beispieltabelle ist es die ganze Spalte des Schritts.
        """
        x0, y0, x1, _ = self.flaeche(seite)
        rand = self.px(MARKERRAND)
        zeilen, flaechen = {}, {}
        for stueck in stuecke:
            if isinstance(stueck, buchsatz.Zeile) and stueck.schritt is not None:
                schrift = getattr(self.schriften, stueck.schrift)
                # Über den Rand der Textfläche hinaus malt der Marker nicht.
                links, oben = max(x0, x0 + stueck.x - rand), y0 + stueck.y
                rechts = min(x1, x0 + stueck.x + schrift.measure(stueck.text) + rand)
                unten = oben + schrift.metrics("linespace")
                # Nummer und Text einer Zeile bekommen einen Strich, nicht zwei.
                bisher = zeilen.get((stueck.schritt, oben))
                if bisher is not None:
                    links, rechts = min(links, bisher[0]), max(rechts, bisher[2])
                zeilen[(stueck.schritt, oben)] = (links, oben, rechts, unten)
            elif isinstance(stueck, buchsatz.Raster):
                for spalte, marke in enumerate(stueck.schritte):
                    links = x0 + stueck.x + stueck.beschriftungsbreite + spalte * stueck.zellbreite
                    oben = y0 + stueck.y
                    flaechen.setdefault(marke, []).append(
                        (links, oben, links + stueck.zellbreite, oben + stueck.hoehe))
        for (marke, _), flaeche in zeilen.items():
            flaechen.setdefault(marke, []).append(flaeche)
        return flaechen

    def markieren(self, seite, flaechen):
        """Zieht Textmarker über die ``flaechen`` – unter die Schrift der Seite."""
        self.unterlegen(seite, "text", [
            self.create_rectangle(*flaeche, fill=stil.FARBE_MARKIERUNG, width=0, tags=(seite, "markierung"))
            for flaeche in flaechen])

    def werkzeug_markieren(self, seite, stuecke, schritt):
        """Markiert im Werkzeug auf der Seite, wo ein Schritt sucht und was er findet.

        Im Quadrat die Zeile des Schlüsselbuchstabens und die Spalte des
        Nachrichtenbuchstabens, jeweils vom Kopf bis zum Kreuzungspunkt; in
        einer Tabelle die Spalte bis zu dem Feld, in dem die ``kreuzung``
        steht. Das Feld selbst wird kräftiger markiert und rot umrandet.
        """
        x0, y0, _, _ = self.flaeche(seite)
        for stueck in stuecke:
            if isinstance(stueck, buchsatz.Quadrat) and schritt.zeile:
                feld = stueck.feld
                x, y = x0 + stueck.x, y0 + stueck.y
                zeile, spalte = ALPHABET.index(schritt.zeile) + 1, ALPHABET.index(schritt.spalte) + 1
                kreuzung = (x + spalte * feld, y + zeile * feld, x + (spalte + 1) * feld, y + (zeile + 1) * feld)
                baender = ((x, kreuzung[1], kreuzung[2], kreuzung[3]), (kreuzung[0], y, kreuzung[2], kreuzung[3]))
                # Über den dunkleren Grund von Kopfzeile und Kopfspalte, unter die Buchstaben.
                self._kreuzung_zeichnen(seite, "kopfzeile", baender, kreuzung)
            elif isinstance(stueck, buchsatz.Raster) and schritt.spalte in stueck.zeilen[0][1:]:
                spalte = stueck.zeilen[0][1:].index(schritt.spalte)
                treffer = [nr for nr, zeile in enumerate(stueck.zeilen)
                           if nr and zeile[1 + spalte] == schritt.kreuzung]
                if not treffer:
                    continue
                links = x0 + stueck.x + stueck.beschriftungsbreite + spalte * stueck.zellbreite
                oben = y0 + stueck.y
                kreuzung = (links, oben + stueck.oben(treffer[0]), links + stueck.zellbreite,
                            oben + stueck.oben(treffer[0] + 1))
                self._kreuzung_zeichnen(seite, "text", ((links, oben, kreuzung[2], kreuzung[3]),), kreuzung)

    def _kreuzung_zeichnen(self, seite, unter, baender, kreuzung):
        marken = (seite, "markierung")
        elemente = [self.create_rectangle(*band, fill=stil.FARBE_MARKIERUNG, width=0, tags=marken)
                    for band in baender]
        elemente.append(self.create_rectangle(*kreuzung, fill=stil.FARBE_KREUZUNG, width=0,
                                              tags=marken + ("kreuzung",)))
        self.unterlegen(seite, unter, elemente)
        # Der Rand obenauf, sonst verschwände er unter den Linien der Tabelle.
        self.create_rectangle(*kreuzung, outline=stil.FARBE_ROTSTIFT, width=max(2, self.px(2)),
                              tags=marken + ("kreuzungsrand",))

    def unterlegen(self, seite, unter, elemente):
        """Legt die ``elemente`` direkt unter das unterste Element der Seite mit dem Tag ``unter``."""
        ziel = self.find_withtag(f"{unter}&&{seite}")
        if ziel:
            for element in elemente:
                self.tag_lower(element, ziel[0])

    def verzierung_zeichnen(self, verzierung, x0, y0, tags):
        """Eine feine Linie mit einem kleinen Diamanten in der Mitte."""
        px = self.px
        x, y = x0 + verzierung.x, y0 + verzierung.y
        mitte, r = x + verzierung.breite / 2, px(5)
        self.create_line(x, y, mitte - 2 * r, y, fill=stil.FARBE_BUCHLINIE, tags=tags)
        self.create_line(mitte + 2 * r, y, x + verzierung.breite, y, fill=stil.FARBE_BUCHLINIE, tags=tags)
        self.create_polygon(mitte, y - 1.4 * r, mitte + r, y, mitte, y + 1.4 * r, mitte - r, y,
                            fill=stil.FARBE_ROTSTIFT, outline="", tags=tags + ("diamant",))
