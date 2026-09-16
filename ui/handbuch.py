"""Der Handbuch-Screen (Arbeitsplan 6.4): Bobs Verschlüsselungshandbuch als Buch.

Zu Beginn jedes Levels liegt Bobs Handbuch aufgeschlagen vor den Spielenden:
ein altes, in Leder gebundenes Buch mit vergilbten Seiten (``grafik/buch.svg``).
Links steht die Titelseite mit dem Inhalt des Kapitels und dem Stempel
"STRENG GEHEIM", rechts beginnt das Kapitel des Levels. Darüber steht der
Einstiegssatz aus der Geschichte ("Du schlägst das Handbuch auf …").

Was auf welcher Seite steht, rechnet :mod:`ui.buchsatz` aus; hier wird es
nur gezeichnet. Das Vigenère-Quadrat auf Seite 3 entsteht aus der Formel
(``crypto/vigenere_quadrat.py``), nicht abgetippt.

Beispiele mit dem Werkzeug daneben
──────────────────────────────────
Ein durchgerechnetes Beispiel steht links, und rechts liegt das Werkzeug, mit
dem es rechnet: das verschobene Alphabet, die Geheimtabelle, das Quadrat.
Einer seiner Schritte ist immer mit Textmarker markiert – zu Beginn der
erste –, und im Werkzeug ist markiert, wo dieser Schritt sucht: im Quadrat
die Zeile des Schlüsselbuchstabens und die Spalte des Nachrichtenbuchstabens
bis zum Kreuzungspunkt, in einer Tabelle die Spalte bis zu dem Feld, das der
Schritt abliest. Zeigt die Maus auf einen anderen Schritt, wandert die
Markierung mit; ein Klick oder die Pfeiltasten hoch und runter tun dasselbe.

Die Markierung zeigt nur, was im Beispiel schon steht ("Suche im Quadrat die
Zeile R und die Spalte H"), und rechnet nichts Neues vor – die Kontrollgruppe
liest dieselben Beispiele.

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
schräg gestellt, und darüber das Blatt, das umschlägt. Sie steht in
:mod:`ui.buchleinwand`, weil der Aufgaben-Screen (6.5) dasselbe Buch
benutzt: Dort liegt links das Werkzeug und rechts die Übung.
"""

import tkinter as tk

from content import handbuch as buch
from ui import buchleinwand, buchsatz, stil
from ui.animation import Ablauf, Animation
from ui.buchleinwand import Buchleinwand
from ui.screen import Screen

#: Aufschrift des Knopfes zu Beginn eines Levels.
KNOPF_WEITER = "Zu den Übungen"

#: Aufschrift des Knopfes beim Nachschlagen mitten in einer Aufgabe.
KNOPF_ZURUECK = "Zurück zur Aufgabe"

#: Die Knöpfe zum Blättern.
KNOPF_VORBLAETTERN = "Weiterblättern ▶"
KNOPF_ZURUECKBLAETTERN = "◀ Zurückblättern"

#: Wo man auf dem Buch klicken kann (x0, y0, x1, y1): die hochgebogenen Ecken
#: unten außen zum Blättern.
ECKE_LINKS = (18, 426, 86, 492)
ECKE_RECHTS = (874, 426, 942, 492)

#: So lange nach dem Aufschlagen werden die Bilder des Umblätterns geladen –
#: erst steht das Buch da, dann kommt, was man erst beim Blättern braucht.
VORLADEN_MS = 150

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
        #: Was gerade auf den beiden Seiten gezeichnet ist – und wo darauf die Schritte stehen.
        self._gezeichnet = {}
        self._schrittflaechen = {}
        #: Der markierte Schritt. Die Titelseite vorne hat keine.
        self._schritt = None

        self._hinweis = self._zeile(hinweis, stil.FARBE_WARNUNG, stil.SCHRIFT_FETT)
        self._einleitung = [self._zeile(absatz, stil.FARBE_SAND, stil.SCHRIFT_ERZAEHLUNG)
                            for absatz in einleitung]

        #: Die Leinwand mit dem aufgeschlagenen Buch.
        self.buch = Buchleinwand(self, self.massstab, self.px, takefocus=True)
        self.buch.pack(side="top")

        stempel = self.buch.stempelbild("stempel")
        x0, y0, x1, y1 = self.flaeche("links")
        #: Das gesetzte Kapitel: welche Stücke auf welcher Seite stehen.
        self.satz = buchsatz.setzen(self.seite, self.schriften, x1 - x0, y1 - y0, self.px,
                                    stempel=(stempel.width(), stempel.height()))

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

    @property
    def schritte(self):
        """Die Schritte des Beispiels auf der aufgeschlagenen Doppelseite – Schrittmarken in Lesereihenfolge.

        Sie stehen immer links: Beispiele haben ihr Werkzeug rechts daneben.
        """
        return self.satz.seiten[2 * self._doppelseite].schritte

    @property
    def schritt(self):
        """Der markierte Schritt (eine :class:`ui.buchsatz.Schrittmarke`) – oder ``None`` ohne Beispiel."""
        return self._schritt

    @property
    def schriften(self):
        """Die Schriften des Buchs (siehe :mod:`ui.buchleinwand`)."""
        return self.buch.schriften

    def flaeche(self, seite):
        """Die Textfläche der linken oder rechten Seite auf der Leinwand: (x0, y0, x1, y1)."""
        return self.buch.flaeche(seite)

    def texte(self, seite=None):
        """Die Texte, die gerade im Buch stehen – auf der ``seite`` "links" oder "rechts", sonst auf beiden."""
        return self.buch.texte(seite)

    def quadratfeld(self, schluesselbuchstabe, nachrichtenbuchstabe):
        """Was im gezeichneten Quadrat in dieser Zeile und Spalte steht (es muss aufgeschlagen sein)."""
        return self.buch.quadratfeld(schluesselbuchstabe, nachrichtenbuchstabe)

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
        leinwand.bind("<Up>", lambda _ereignis: self.schritt_weiter(-1))
        leinwand.bind("<Down>", lambda _ereignis: self.schritt_weiter(1))
        leinwand.bind("<MouseWheel>", self._mausrad)
        leinwand.bind("<Button-4>", lambda _ereignis: self.blaettern(-1))
        leinwand.bind("<Button-5>", lambda _ereignis: self.blaettern(1))
        leinwand.bind("<Button-1>", lambda ereignis: self.klicken(ereignis.x, ereignis.y))
        leinwand.bind("<Motion>", lambda ereignis: self._maus_ueber(self.ziel(ereignis.x, ereignis.y)))
        leinwand.bind("<Leave>", lambda _ereignis: self._maus_ueber(None))

    def _erster_schritt(self):
        schritte = self.schritte
        return schritte[0] if schritte else None

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
        """Zeichnet die linke oder rechte Seite der aufgeschlagenen Doppelseite neu – samt Markierung."""
        nr = 2 * self._doppelseite + (seite == "rechts")
        if nr < len(self.satz.seiten):
            buchseite = self.satz.seiten[nr]
        else:
            # Die letzte Seite eines Kapitels bleibt leer – bis auf eine Verzierung.
            x0, y0, x1, y1 = self.flaeche(seite)
            buchseite = buchsatz.leerseite(x1 - x0, y1 - y0, self.px)
        self.buch.seite_zeichnen(seite, buchseite.stuecke)
        self._gezeichnet[seite] = buchseite
        self._schrittflaechen[seite] = (self.buch.schrittflaechen(seite, buchseite.stuecke)
                                        if buchseite.schritte else {})
        self._markierung_zeichnen(seite)
        # Was die Maus gerade zeigt, bleibt obenauf.
        self.buch.tag_raise("maus")

    def _markierung_zeichnen(self, seite):
        """Markiert auf der Seite den Schritt, der dran ist – im Beispiel oder im Werkzeug."""
        marke, buchseite = self._schritt, self._gezeichnet.get(seite)
        if marke is None or buchseite is None:
            return
        if marke in self._schrittflaechen[seite]:
            self.buch.markieren(seite, self._schrittflaechen[seite][marke])
        if buchseite.werkzeug is not None:
            self.buch.werkzeug_markieren(seite, buchseite.stuecke, marke.schritt)

    # ── Schritte eines Beispiels ───────────────────────────────────────────

    def schritt_zeigen(self, marke):
        """Markiert einen Schritt des aufgeschlagenen Beispiels und im Werkzeug, wo er sucht.

        ``False``, wenn er schon markiert ist oder nicht auf dieser Doppelseite steht.
        """
        if marke == self._schritt or marke not in self.schritte:
            return False
        self._schritt = marke
        self.buch.delete("markierung")
        for seite in buchleinwand.SEITEN:
            self._markierung_zeichnen(seite)
        self.buch.tag_raise("maus")
        return True

    def schritt_weiter(self, richtung):
        """Markiert den nächsten (1) oder den vorigen Schritt (-1). ``False``, wenn es keinen gibt."""
        schritte = self.schritte
        if self._schritt not in schritte:
            return False
        nr = schritte.index(self._schritt) + richtung
        return 0 <= nr < len(schritte) and self.schritt_zeigen(schritte[nr])

    def schritt_bei(self, x, y):
        """Der Schritt, der auf der Leinwand bei ``x, y`` steht – oder ``None``."""
        for flaechen in self._schrittflaechen.values():
            for marke, rechtecke in flaechen.items():
                if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in rechtecke):
                    return marke
        return None

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
        self._schritt = self._erster_schritt()
        self._leiste_aktualisieren()
        self._maus_ueber(None)
        # Was auf der alten Doppelseite stand und markiert war, gilt nicht mehr –
        # auch nicht auf der Seite, die erst nach dem Umschlagen neu gezeichnet wird.
        self.buch.delete("markierung")
        self._gezeichnet.clear()
        self._schrittflaechen.clear()
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
        """Was ein Klick an dieser Stelle der Leinwand täte: "vor", "zurueck", einen Schritt markieren – oder nichts.

        Für einen Schritt ist das Ziel seine Schrittmarke, sonst ``None``.
        """
        def drin(bereich):
            x0, y0, x1, y1 = (self.px(wert) for wert in bereich)
            return x0 <= x <= x1 and y0 <= y <= y1

        if drin(ECKE_RECHTS) and self._doppelseite < self.anzahl_doppelseiten - 1:
            return "vor"
        if drin(ECKE_LINKS) and self._doppelseite > 0:
            return "zurueck"
        return self.schritt_bei(x, y)

    def klicken(self, x, y):
        """Ein Klick auf die Leinwand bei ``x, y``."""
        self.buch.focus_set()
        ziel = self.ziel(x, y)
        if ziel == "vor":
            self.blaettern(1)
        elif ziel == "zurueck":
            self.blaettern(-1)
        elif ziel is not None:
            self.schritt_zeigen(ziel)

    def _maus_ueber(self, ziel):
        """Zeigt, dass sich hier etwas tut: Hand als Zeiger und ein Pfeil an der Ecke.

        Über einem Schritt eines Beispiels wird er gleich markiert – und bleibt
        es, wenn die Maus weiterzieht.
        """
        if ziel == self._unter_maus:
            return
        self._unter_maus = ziel
        px, leinwand = self.px, self.buch
        leinwand.delete("maus")
        leinwand.configure(cursor="hand2" if ziel else "")
        if isinstance(ziel, buchsatz.Schrittmarke):
            self.schritt_zeigen(ziel)
        elif ziel in ("vor", "zurueck"):
            spitze, hinten = (px(912), px(898)) if ziel == "vor" else (px(48), px(62))
            mitte = px(420)
            leinwand.create_polygon(hinten, mitte - px(7), spitze, mitte, hinten, mitte + px(7),
                                    fill=stil.FARBE_ROTSTIFT, outline="", tags=("maus",))

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
