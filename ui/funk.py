"""Der Funk-Screen (Arbeitsplan 6.6): die echten Funksprüche am Funkgerät.

Übungen stehen im Buch, Funksprüche kommen über das Kurzwellen-Funkgerät. Es
steht rechts auf dem aufgeschlagenen Handbuch (``grafik/funkgeraet.svg``);
links liegt wie bei den Übungen das Werkzeug zum Rechnen, in Level 3 mit dem
Lineal. Schon am Bild ist zu sehen, ob geübt wird oder ob es ernst ist: Papier
gegen olivgrünes Blech und leuchtende Schrift auf dunklem Glas.

Was auf dem Glas steht
──────────────────────
Oben, woher der Funkspruch kommt oder dass gesendet wird, und womit gerechnet
wird ("Caesar · Schlüssel 3"). Darunter der Auftrag, die Nachricht selbst,
die Eingabezeile und die Rückmeldung. Eine empfangene Nachricht kommt Zeichen
für Zeichen herein, und das Empfangslämpchen flackert dazu; eine gesendete
lässt am Ende das Sendelämpchen leuchten.

Die Regel für lange Funksprüche (CLAUDE.md)
───────────────────────────────────────────
Von drei langen Funksprüchen rechnen die Spielenden nur den Anfang
(``selbst_zu_loesen``). Welcher Text dabei sichtbar bleibt, hängt an der
Richtung – und genau dort darf nichts verwechselt werden:

* **Empfangen:** Der vollständige Geheimtext steht da. Der Anfang, der
  entschlüsselt werden soll, leuchtet hell und ist unterstrichen, der Rest
  matt. Ohne den langen Geheimtext ginge der Grund verloren, warum er nicht
  gekürzt wird (Häufigkeitsanalyse, Handbuchseite 2).
* **Senden:** Der vollständige **Klartext** steht da, sein Anfang ist
  hervorgehoben. Der Geheimtext steht **nie** auf dem Glas – er ist genau das,
  was eingetippt werden soll. Auch nach dem Senden erscheint nur "GESENDET".
  (Die Lösungsanzeige nach drei Versuchen ohne Fortschritt ist die einzige
  Ausnahme; dann ist die Aufgabe vorbei.)

Ist der Anfang gelöst – oder nach drei Versuchen ohne Fortschritt aufgelöst –,
kommt der Knopf für den Rest (``story.BESCHRIFTUNG_REST``). Er setzt über das
Gerät den Erzähltext ("Zwanzig Minuten später …") und gibt die ganze Nachricht
frei: Beim Empfangen steht dann der ganze Klartext auf dem Glas, beim Senden
leuchtet das Sendelämpchen. Die Erzählzeit ist Fiktion – die Uhr des Levels
läuft weiter (Projektregel 1).

Die Regeln kommen aus der Spiellogik
────────────────────────────────────
Wie bei den Übungen (:mod:`ui.uebung`): Der Screen reicht die Eingabe an den
Spielstand weiter und zeigt, was zurückkommt – die konkrete Fehlermeldung,
deren Stelle in der Nachricht unterwellt wird, den Hinweis auf Fortschritt,
die verbleibenden Versuche und nach dreien ohne Fortschritt die Lösung. Eine
falsch verschlüsselte Nachricht wird nicht gesendet (Projektregel 6): Der
Knopf heisst beim Senden "Senden", und gesendet ist erst, was stimmt.

Nachschlagen im Handbuch geht auch hier, und man kommt zu demselben Funkspruch
zurück – samt dem, was schon eingetippt war.

Wann welcher Funkspruch kommt
─────────────────────────────
Das entscheidet die Spiellogik (:mod:`game.levelablauf`): Nach den Übungen
eines Levels kommen seine Funksprüche der Reihe nach – und wenn die Zeit knapp
wird, schon vorher. :mod:`ui.ablauf` zeigt sie dann hier.
"""

import tkinter as tk
from tkinter import font as tkfont

from content import story, verfahren
from game.aufgabe import ENTSCHLUESSELN
from game.generator import aufgabe_aus_funkspruch
from game.rueckmeldung import bezugsloesung, erste_abweichung
from ui import handbuch, lineal, stil, uebung
from ui.animation import Animation
from ui.buchleinwand import Buchleinwand
from ui.buchsatz import umbrechen
from ui.screen import Screen

#: Aufschriften der Knöpfe unter dem Gerät.
KNOPF_PRUEFEN = uebung.KNOPF_PRUEFEN
KNOPF_SENDEN = "Senden"
KNOPF_WEITER = uebung.KNOPF_WEITER
KNOPF_NACHSCHLAGEN = uebung.KNOPF_NACHSCHLAGEN

#: Die erste Zeile auf dem Glas: woher der Funkspruch kommt – oder dass gesendet wird.
KOPF = {story.EMPFANGEN: "EMPFANG · {absender}", story.SENDEN: "SENDEN"}
#: Die zweite: womit gerechnet wird.
VERFAHRENSANGABE = {
    verfahren.CAESAR: "Caesar · Schlüssel {schluessel}",
    verfahren.SUBSTITUTION: "Substitution · deine Geheimtabelle",
    verfahren.VIGENERE: "Vigenère · Schlüsselwort {schluessel}",
}
#: Der Auftrag – je nach Richtung und danach, ob nur der Anfang zu rechnen ist.
AUFTRAG = {
    (story.EMPFANGEN, True): "Entschlüssele den hellen Anfang:",
    (story.EMPFANGEN, False): "Entschlüssele den Funkspruch:",
    (story.SENDEN, True): "Verschlüssele den hellen Anfang:",
    (story.SENDEN, False): "Verschlüssele den Funkspruch:",
}
#: Auf dem Glas, wenn die Zeit für diese Nachricht nicht mehr reichte und sie
#: nur noch zum Mitlesen dasteht (Arbeitsplan Phase 7).
AUFTRAG_NACHGELESEN = {
    story.EMPFANGEN: "Die Zeit war zu knapp – hier zum Mitlesen:",
    story.SENDEN: "Die Zeit war zu knapp – deine Figur hat selbst verschlüsselt:",
}
#: Vor dem Eingabefeld.
EINGABEZEICHEN = "▸"
#: Nach dem Senden – mehr steht nicht da; der Geheimtext bleibt ungezeigt.
GESENDET = "GESENDET."
#: Über dem ganzen Klartext, sobald der Rest frei ist.
GANZE_NACHRICHT = "Die ganze Nachricht:"

#: Wo das Funkgerät auf dem Buch steht: die linke obere Ecke seines Bilds, in
#: Pixeln im Maßstab 1 (wie alle festen Grössen, siehe ui/stil.py).
GERAET = (492, 6)
#: Das Glas der Anzeige und die Lämpchen im Bild des Geräts – dieselben Maße wie
#: in ``grafik/funkgeraet_zeichnen.py``, dort in SVG-Einheiten und doppelt so groß.
GLAS = (46, 85, 414, 349)
LAMPE_EMPFANG = (325, 385, 11)
LAMPE_SENDEN = (382, 385, 11)
#: So weit bleibt die Schrift vom Rand des Glases weg.
GLASRAND = 8
#: Schriftgrösse der Anzeige in Punkt (Maßstab 1).
ANZEIGEGROESSE = 9
#: Abstände auf dem Glas.
ABSTAND_KOPF = 4
ABSTAND_NACHRICHT = 4
#: Höhe der Eingabezeile, in Zeilen der Anzeigeschrift.
FELDHOEHE = 1.4
#: So kommt eine empfangene Nachricht herein: Zeichen je Takt, Takt in Millisekunden.
ZEICHEN_JE_TAKT = 2
TAKT_MS = 30


class Funk(Screen):
    """Ein Funkspruch am Funkgerät. ``danach(fenster)`` ist, was nach ihm kommt.

    ``fortsetzen`` setzt den offenen Funkspruch fort, statt ihn neu zu stellen –
    so kommt man vom Nachschlagen zurück; ``entwurf`` ist, was dabei schon in
    der Eingabezeile stand.

    ``nur_lesen`` zeigt den Funkspruch, ohne ihn zu stellen: Für ihn hat die
    Zeit des Levels nicht mehr gereicht, und er steht nur noch da, damit die
    Geschichte weitergeht (Arbeitsplan Phase 7). Es gibt dann keine Eingabe,
    keine Uhr und keine Zeile im Log – nur die ganze Nachricht und "Weiter".

    ``hinweis`` ist ein Satz, der über dem Gerät erscheint, **sobald die
    Nachricht ganz da ist** – beim abgefangenen Funkspruch der zur
    Häufigkeitsanalyse (Arbeitsplan 7.2). Er tritt an die Stelle der
    Einleitung, statt eine Zeile mehr zu brauchen: Der Platz über dem Gerät
    ist knapp, und genau dann steht der lange Geheimtext vollständig auf dem
    Glas – darauf zielt der Satz.
    """

    def __init__(self, fenster, funkspruch, danach, fortsetzen=False, entwurf="", hinweis="",
                 nur_lesen=False):
        """Baut das Funkgerät: Einleitung, Gerät mit Glas, Eingabezeile und Knopfleiste.

        Die Aufgabe wird hier noch **nicht** gestellt – erst in
        :meth:`beim_anzeigen`, denn mit ihr beginnt ihre Uhr. Was die
        einzelnen Schalter bedeuten, steht oben bei der Klasse.
        """
        super().__init__(fenster)
        self.configure(bg=stil.FARBE_NACHT, pady=self.px(handbuch.ABSTAND_KNAPP))
        self.funkspruch = funkspruch
        self.titel = f"Funkgerät – Level {funkspruch.level}"
        self._danach = danach
        self._fortsetzen = fortsetzen
        self._entwurf = entwurf
        self._nur_lesen = nur_lesen
        #: Der laufende Funkspruch als Aufgabe – gestellt beim Anzeigen, dann beginnt seine Uhr.
        self.aufgabe = None
        self.lineal = None
        self._beendet = False
        self._rest_frei = False
        self._antwort = None
        self._zeilen = ()
        self._getippt = 0
        self._nachricht_oben = 0
        self._rueckmeldung_oben = 0
        self._rueckmeldung = []

        # Über dem Gerät: die Einleitung aus der Geschichte, dann der Hinweis,
        # später der Erzähltext zum Rest – immer in derselben Zeile.
        self._hinweis = hinweis
        breite = handbuch.textbreite(self)
        erzaehlschrift = tkfont.nametofont(stil.SCHRIFT_ERZAEHLUNG)
        hoehe = max(len(umbrechen(text, erzaehlschrift, breite)) or 1
                    for text in (funkspruch.einleitung, funkspruch.weiterrechnen, hinweis))
        self._erzaehlung = tk.Label(self, text=funkspruch.einleitung, bg=stil.FARBE_NACHT, fg=stil.FARBE_SAND,
                                    font=stil.SCHRIFT_ERZAEHLUNG, anchor="nw", justify="left", wraplength=breite,
                                    height=hoehe)
        self._erzaehlung.pack(side="top", fill="x")

        #: Die Leinwand: das Buch, darauf das Gerät.
        self.buch = Buchleinwand(self, self.massstab, self.px)
        self.buch.pack(side="top")
        bild = Animation("funkgeraet", massstab=self.massstab)
        self._geraetebild = tk.PhotoImage(master=self.buch, file=str(bild.ordner / bild.hintergrund))
        self.buch.create_image(self.px(GERAET[0]), self.px(GERAET[1]), image=self._geraetebild, anchor="nw",
                               tags=("geraet",))
        familie = stil.erste_schrift(self, stil.ANZEIGESCHRIFTEN) or tkfont.nametofont(
            "TkFixedFont", root=self).actual("family")
        groesse = stil.skaliert(ANZEIGEGROESSE, self.massstab)
        self.schrift = tkfont.Font(root=self, family=familie, size=groesse)
        self._fett = tkfont.Font(root=self, family=familie, size=groesse, weight="bold")
        self._unterstrichen = tkfont.Font(root=self, family=familie, size=groesse, underline=True)
        self._lampen_zeichnen()

        self._feld = tk.Entry(self.buch, font=self.schrift, bg=stil.FARBE_GLAS, fg=stil.FARBE_LEUCHTSCHRIFT_HELL,
                              insertbackground=stil.FARBE_LEUCHTSCHRIFT_HELL, relief="flat", highlightthickness=1,
                              highlightbackground=stil.FARBE_LEUCHTSCHRIFT_MATT,
                              highlightcolor=stil.FARBE_LEUCHTSCHRIFT)
        self._feld.bind("<Return>", lambda _ereignis: self.pruefen())
        self._leiste_bauen()

    # ── Was dasteht ────────────────────────────────────────────────────────

    @property
    def eingabe(self):
        """Was in der Eingabezeile steht – nach dem Ende der Aufgabe, was dort stand."""
        return self._antwort if self._antwort is not None else self._feld.get()

    @property
    def knopftext(self):
        """Was auf dem grossen Knopf rechts steht: "Senden", "Prüfen" oder "Weiter"."""
        return self._knopf.cget("text")

    @property
    def restknopf_sichtbar(self):
        """Steht der Knopf für den Rest der Nachricht gerade in der Leiste?"""
        return bool(self._restknopf.winfo_manager())

    @property
    def erzaehlung(self):
        """Der Text über dem Gerät."""
        return self._erzaehlung.cget("text")

    @property
    def hinweis(self):
        """Der Satz, der über dem Gerät steht, sobald die Nachricht ganz da ist – meist leer."""
        return self._hinweis

    @property
    def nur_lesen(self):
        """Steht der Funkspruch nur zum Mitlesen da, weil die Zeit nicht reichte?"""
        return self._nur_lesen

    @property
    def ist_beendet(self):
        """Ist der geprüfte Teil entschieden – gelöst oder aufgelöst?"""
        return self._beendet

    @property
    def eingetippt(self):
        """Ist die Nachricht ganz auf dem Glas?"""
        return self._getippt >= len(self.aufgabe.anzeigetext) if self.aufgabe is not None else False

    def glastexte(self, tag="anzeige"):
        """Die Texte auf dem Glas – alle oder die mit einem Tag ("nachricht", "rueckmeldung" …)."""
        return [self.buch.itemcget(element, "text") for element in self.buch.find_withtag(tag)
                if self.buch.type(element) == "text"]

    def lampe_leuchtet(self, name):
        """Leuchtet das Lämpchen "empfang" oder "senden"?"""
        (element,) = self.buch.find_withtag(f"lampe_{name}")
        return self.buch.itemcget(element, "fill") != stil.FARBE_LAMPE_AUS

    # ── Bauen ──────────────────────────────────────────────────────────────

    def _leiste_bauen(self):
        """Baut die Knopfleiste unter dem Gerät: Nachschlagen, der grosse Knopf, der für den Rest."""
        leiste = tk.Frame(self, bg=stil.FARBE_NACHT)
        leiste.pack(side="top", fill="x", pady=(self.px(handbuch.ABSTAND_KNAPP), 0))
        knopfart = dict(font=stil.SCHRIFT_FETT, highlightbackground=stil.FARBE_NACHT)
        self._nachschlagen_knopf = tk.Button(leiste, text=KNOPF_NACHSCHLAGEN, command=self._nachschlagen,
                                             **knopfart)
        if not self._nur_lesen:
            # Beim Mitlesen gibt es nichts zu rechnen – also auch nichts nachzuschlagen.
            self._nachschlagen_knopf.pack(side="left")
        senden = self.funkspruch.richtung == story.SENDEN
        aufschrift = KNOPF_WEITER if self._nur_lesen else (KNOPF_SENDEN if senden else KNOPF_PRUEFEN)
        self._knopf = tk.Button(leiste, text=aufschrift,
                                command=self.weiter if self._nur_lesen else self.pruefen,
                                padx=self.px(stil.ABSTAND), **knopfart)
        self._knopf.pack(side="right")
        self._knopf.bind("<Return>", lambda _ereignis: self._knopf.invoke())
        self._restknopf = tk.Button(leiste, command=self.rest_freigeben, padx=self.px(stil.ABSTAND), **knopfart)
        self._restknopf.bind("<Return>", lambda _ereignis: self._restknopf.invoke())

    def _glas(self):
        """Die Fläche auf dem Glas, auf der geschrieben wird: (x0, y0, x1, y1) auf der Leinwand."""
        gx, gy = self.px(GERAET[0]), self.px(GERAET[1])
        rand = self.px(GLASRAND)
        return (gx + self.px(GLAS[0]) + rand, gy + self.px(GLAS[1]) + rand,
                gx + self.px(GLAS[2]) - rand, gy + self.px(GLAS[3]) - rand)

    def _lampen_zeichnen(self):
        """Malt die beiden Kontrolllampen auf das Gerät – dunkel; angehen tun sie im Betrieb."""
        gx, gy = self.px(GERAET[0]), self.px(GERAET[1])
        for name, (x, y, r) in (("empfang", LAMPE_EMPFANG), ("senden", LAMPE_SENDEN)):
            x, y, r = gx + self.px(x), gy + self.px(y), self.px(r)
            self.buch.create_oval(x - r, y - r, x + r, y + r, fill=stil.FARBE_LAMPE_AUS, outline="",
                                  tags=("lampe", f"lampe_{name}"))

    def lampe(self, name, an):
        """Lässt ein Lämpchen leuchten oder löscht es."""
        farbe = {"empfang": stil.FARBE_LAMPE_EMPFANG, "senden": stil.FARBE_LAMPE_SENDEN}[name]
        self.buch.itemconfigure(f"lampe_{name}", fill=farbe if an else stil.FARBE_LAMPE_AUS)

    # ── Anzeigen ───────────────────────────────────────────────────────────

    def beim_anzeigen(self):
        """Hier wird der Funkspruch gestellt – mit ihm beginnt seine Uhr.

        Beim Mitlesen wird nichts gestellt: Die Zeit dafür ist vorbei, es gibt
        keine Uhr und keine Zeile im Log.
        """
        if self._nur_lesen:
            self._nachlesen_zeigen()
            return
        stand = self.durchlauf.spielstand
        # Zurück vom Nachschlagen: derselbe Funkspruch, seine Uhr lief weiter.
        aufgabe = stand.aktuelle_aufgabe if self._fortsetzen else self.durchlauf.stelle_funkspruch(self.funkspruch)
        if aufgabe is None:
            return  # Die Zeit war um – der Levelwechsel hat schon umgeschaltet.
        self.aufgabe = aufgabe
        seite = self.buch.werkzeug_zeichnen(aufgabe.level)
        self.lineal = lineal.anlegen(self.buch, "links", seite.stuecke, bei_benutzung=self._lineal_benutzt)
        self._anzeige_zeichnen()
        self._feld.insert(0, self._entwurf)
        self._feld.focus_set()
        empfangen = self.funkspruch.richtung == story.EMPFANGEN
        if empfangen and not self._fortsetzen:
            self._eintippen()
        else:
            self.anzeige_vervollstaendigen()
        self._stand_zeigen(stand.aktuelle_bearbeitung)

    def _nachlesen_zeigen(self):
        """Die ganze Nachricht zum Mitlesen – ohne Eingabe, ohne Uhr, ohne Log."""
        self.aufgabe = aufgabe_aus_funkspruch(self.funkspruch, self.durchlauf.spielstand.figur.initialen)
        seite = self.buch.werkzeug_zeichnen(self.funkspruch.level)
        self.lineal = lineal.anlegen(self.buch, "links", seite.stuecke)
        self._anzeige_zeichnen()
        self.anzeige_vervollstaendigen()
        self._rest_zeigen(self.aufgabe.vollstaendige_loesung, self.erzaehlung)
        self._knopf.focus_set()

    def _anzeige_zeichnen(self):
        """Schreibt Kopf, Auftrag und den Platz für Nachricht und Eingabe aufs Glas."""
        leinwand, s, px = self.buch, self.schrift, self.px
        x0, y0, x1, _ = self._glas()
        zeile = s.metrics("linespace")
        aufgabe, funkspruch = self.aufgabe, self.funkspruch
        y = y0
        kopf = KOPF[funkspruch.richtung].format(absender=funkspruch.absender.upper())
        leinwand.create_text(x0, y, text=kopf, anchor="nw", font=self._fett, fill=stil.FARBE_LEUCHTSCHRIFT_HELL,
                             tags=("anzeige", "kopf"))
        y += zeile
        angabe = VERFAHRENSANGABE[aufgabe.verfahren].format(schluessel=aufgabe.schluessel)
        leinwand.create_text(x0, y, text=angabe, anchor="nw", font=s, fill=stil.FARBE_LEUCHTSCHRIFT,
                             tags=("anzeige", "verfahren"))
        y += zeile + px(ABSTAND_KOPF)
        leinwand.create_line(x0, y, x1, y, fill=stil.FARBE_LEUCHTSCHRIFT_MATT, tags=("anzeige",))
        y += px(ABSTAND_KOPF)
        auftrag = (AUFTRAG_NACHGELESEN[funkspruch.richtung] if self._nur_lesen
                   else AUFTRAG[(funkspruch.richtung, aufgabe.hat_teilaufgabe)])
        for text in umbrechen(auftrag, s, x1 - x0):
            leinwand.create_text(x0, y, text=text, anchor="nw", font=s, fill=stil.FARBE_LEUCHTSCHRIFT,
                                 tags=("anzeige", "auftrag"))
            y += zeile
        y += px(ABSTAND_NACHRICHT // 2)
        self._nachricht_oben = y
        self._zeilen = tuple(umbrechen(aufgabe.anzeigetext, s, x1 - x0))
        y += len(self._zeilen) * zeile + px(ABSTAND_NACHRICHT)

        if self._nur_lesen:
            # Kein Eingabefeld – der Platz gehört der Nachricht.
            self._rueckmeldung_oben = y
            return
        feldhoehe = round(zeile * FELDHOEHE)
        leinwand.create_text(x0, y + feldhoehe // 2, text=EINGABEZEICHEN, anchor="w", font=self._fett,
                             fill=stil.FARBE_LEUCHTSCHRIFT_HELL, tags=("anzeige", "eingabezeichen"))
        feld_x = x0 + s.measure(EINGABEZEICHEN + " ")
        self._feldkasten = (feld_x, y, x1 - feld_x, feldhoehe)
        leinwand.create_window(feld_x, y, window=self._feld, anchor="nw", width=x1 - feld_x, height=feldhoehe,
                               tags=("eingabe",))
        self._rueckmeldung_oben = y + feldhoehe + px(ABSTAND_NACHRICHT)

    def _eintippen(self):
        """Die Nachricht kommt Zeichen für Zeichen herein – das Empfangslämpchen flackert dazu.

        Der nächste Takt wird auch dann angemeldet, wenn das Zeichnen stolpert
        (wie beim Takt des Hauptfensters): Sonst bliebe die Nachricht auf
        halber Strecke stehen. Weil jeder Takt ein Stück weiterrückt, endet das
        Eintippen so oder so.
        """
        try:
            self._getippt = min(len(self.aufgabe.anzeigetext), self._getippt + ZEICHEN_JE_TAKT)
            self._nachricht_zeichnen()
            self.lampe("empfang", True if self.eingetippt else self._getippt // ZEICHEN_JE_TAKT % 4 < 2)
            if self.eingetippt:
                self._hinweis_zeigen()
        finally:
            if not self.eingetippt:
                self.spaeter(TAKT_MS, self._eintippen)

    def anzeige_vervollstaendigen(self):
        """Die ganze Nachricht steht sofort da – etwa nach dem Nachschlagen."""
        self._getippt = len(self.aufgabe.anzeigetext)
        self._nachricht_zeichnen()
        self.lampe("empfang", self.funkspruch.richtung == story.EMPFANGEN)
        self._hinweis_zeigen()

    def _hinweis_zeigen(self):
        """Der Hinweis tritt über dem Gerät an die Stelle der Einleitung.

        Erst jetzt: Er spricht von dem Geheimtext, der nun ganz auf dem Glas
        steht. Wurde der Rest schon aufgelöst, schreibt :meth:`_stand_zeigen`
        gleich danach den Erzähltext dazu darüber.
        """
        if self._hinweis:
            self._erzaehlung.configure(text=self._hinweis)

    def _nachricht_zeichnen(self):
        """Die Nachricht, soweit sie da ist: der zu rechnende Anfang hell und unterstrichen, der Rest matt."""
        leinwand, s = self.buch, self.schrift
        leinwand.delete("nachricht")
        x0 = self._glas()[0]
        # So lang wie die Lösung ist der Anfang, der gerechnet wird – ohne
        # Teilaufgabe die ganze Nachricht (Geheim- und Klartext sind gleich lang).
        teil = len(self.aufgabe.loesung)
        stelle = 0
        for nr, zeile in enumerate(self._zeilen):
            sichtbar = zeile[:max(0, min(len(zeile), self._getippt - stelle))]
            hell = sichtbar[:max(0, teil - stelle)]
            matt = sichtbar[len(hell):]
            y = self._nachricht_oben + nr * s.metrics("linespace")
            if hell:
                leinwand.create_text(x0, y, text=hell, anchor="nw", font=self._unterstrichen,
                                     fill=stil.FARBE_LEUCHTSCHRIFT_HELL, tags=("anzeige", "nachricht", "anfang"))
            if matt:
                leinwand.create_text(x0 + s.measure(hell), y, text=matt, anchor="nw", font=s,
                                     fill=stil.FARBE_LEUCHTSCHRIFT_MATT, tags=("anzeige", "nachricht", "rest"))
            stelle += len(zeile) + 1          # das Leerzeichen, an dem umbrochen wurde

    # ── Prüfen und Rückmeldung ─────────────────────────────────────────────

    def pruefen(self):
        """Der Knopf unten rechts: erst prüfen (oder senden), nach dem Ende weiter."""
        if self._beendet:
            if not self._restknopf_wartet():
                self.weiter()
            return
        stand = self.durchlauf.spielstand
        if stand.aktuelle_aufgabe is None:
            return  # Die Zeit ist abgelaufen; der Levelwechsel räumt gleich ab.
        self._ergebnis_zeigen(stand.versuchen(self.eingabe))

    def _ergebnis_zeigen(self, ergebnis):
        """Schreibt die Rückmeldung zu einem Versuch auf das Glas und markiert die Fehlerstelle.

        Was dort steht, hängt am Ergebnis: Lob, eine Meldung mit der ersten
        falschen Stelle, der Hinweis auf Fortschritt – und, wenn die drei
        Versuche ohne Fortschritt aufgebraucht sind, die Lösung selbst.
        """
        self.buch.delete("fehlerstelle")
        zeilen = []
        if ergebnis.richtig:
            zeilen.append((uebung.LOB, stil.FARBE_LEUCHTSCHRIFT_HELL))
        elif ergebnis.loesung_angezeigt:
            # Auf dem Glas ist wenig Platz: Wenn die Lösung dasteht, genügt sie.
            self._fehlerstelle_markieren(self.eingabe)
        else:
            if ergebnis.meldung:
                zeilen.append((ergebnis.meldung, stil.FARBE_LEUCHTSCHRIFT_WARNUNG))
            if ergebnis.hinweis_fortschritt:
                zeilen.append((ergebnis.hinweis_fortschritt, stil.FARBE_LEUCHTSCHRIFT))
            self._fehlerstelle_markieren(self.eingabe)
        if ergebnis.loesung_angezeigt:
            zeilen.append((uebung.LOESUNGSZEILE.format(loesung=ergebnis.angezeigte_loesung),
                           stil.FARBE_LEUCHTSCHRIFT_HELL))
        elif not ergebnis.richtig and ergebnis.zaehlte_als_versuch:
            zeilen.append((uebung.versuchstext(ergebnis.verbleibende_versuche), stil.FARBE_LEUCHTSCHRIFT))
        self._rueckmeldung_setzen(zeilen)
        if ergebnis.ist_beendet:
            self._beenden()

    def _stand_zeigen(self, bearbeitung):
        """Zeigt beim Fortsetzen, wo der Funkspruch steht."""
        if bearbeitung is None or bearbeitung.aufgabe is not self.aufgabe:
            return
        zeilen = []
        if bearbeitung.loesung_angezeigt:
            zeilen.append((uebung.LOESUNGSZEILE.format(loesung=bearbeitung.angezeigte_loesung),
                           stil.FARBE_LEUCHTSCHRIFT_HELL))
        elif bearbeitung.geloest:
            zeilen.append((uebung.LOB, stil.FARBE_LEUCHTSCHRIFT_HELL))
        elif bearbeitung.versuche:
            zeilen.append((uebung.versuchstext(bearbeitung.verbleibende_versuche), stil.FARBE_LEUCHTSCHRIFT))
        self._rueckmeldung_setzen(zeilen)
        if bearbeitung.ist_beendet:
            self._beenden()
            if self.aufgabe.hat_teilaufgabe and not bearbeitung.darf_weiterrechnen:
                # Der Rest war schon freigegeben, bevor nachgeschlagen wurde.
                self._rest_zeigen(bearbeitung.aufgabe.vollstaendige_loesung, self.funkspruch.weiterrechnen)

    def _rueckmeldung_setzen(self, zeilen):
        """Schreibt die Zeilen unter die Eingabe – die alten kommen weg."""
        self._rueckmeldung = list(zeilen)
        leinwand, s = self.buch, self.schrift
        leinwand.delete("rueckmeldung")
        x0, _, x1, _ = self._glas()
        y = self._rueckmeldung_oben
        for text, farbe in zeilen:
            for zeile in umbrechen(text, s, x1 - x0):
                leinwand.create_text(x0, y, text=zeile, anchor="nw", font=s, fill=farbe,
                                     tags=("anzeige", "rueckmeldung"))
                y += s.metrics("linespace")

    def _fehlerstelle_markieren(self, eingabe):
        """Unterwellt in der Nachricht den Buchstaben, an dem es kippt – dieselbe Auskunft wie die Meldung."""
        abweichung = erste_abweichung(eingabe, bezugsloesung(self.aufgabe, eingabe))
        if abweichung is None:
            return
        stelle = abweichung.anzeigeposition - 1
        for nr, zeile in enumerate(self._zeilen):
            if stelle < len(zeile):
                break
            stelle -= len(zeile) + 1
        else:
            return
        if not 0 <= stelle < len(zeile) or zeile[stelle] == " ":
            return
        s = self.schrift
        staerke = max(1, self.px(2))
        links = self._glas()[0] + s.measure(zeile[:stelle]) + staerke
        breite = max(s.measure(zeile[stelle]) - 2 * staerke, self.px(4))
        unten = self._nachricht_oben + nr * s.metrics("linespace") + s.metrics("ascent") + self.px(3)
        self.buch.create_line(*uebung.welle(self.px, links, links + breite, unten),
                              fill=stil.FARBE_LEUCHTSCHRIFT_WARNUNG, width=staerke, tags=("anzeige", "fehlerstelle"))

    # ── Ende des Funkspruchs ───────────────────────────────────────────────

    def _restknopf_wartet(self):
        """Wartet gerade der Knopf für den Rest der Nachricht?

        Dann geht es nicht sofort weiter: Erst muss der Rest aufgelöst
        werden, sonst verschwände die halbe Nachricht aus der Geschichte.
        """
        return self.restknopf_sichtbar

    def _beenden(self):
        """Der Anfang ist entschieden – gelöst oder aufgelöst."""
        self._beendet = True
        self._antwort_festhalten()
        bearbeitung = self.durchlauf.spielstand.aktuelle_bearbeitung
        if bearbeitung is not None and bearbeitung.darf_weiterrechnen:
            # Erst der Rest, dann geht es weiter.
            self._knopf.pack_forget()
            self._restknopf.configure(text=self.aufgabe.knopf_beschriftung)
            self._restknopf.pack(side="right")
            self._restknopf.focus_set()
            return
        if self.funkspruch.richtung == story.SENDEN and not self._rest_frei:
            self._gesendet()
        self._knopf.configure(text=KNOPF_WEITER)
        self._knopf.focus_set()

    def rest_freigeben(self):
        """Der Knopf für den Rest: Erzähltext über dem Gerät, die ganze Nachricht auf dem Glas."""
        stand = self.durchlauf.spielstand
        if stand.aktuelle_bearbeitung is None or not stand.aktuelle_bearbeitung.darf_weiterrechnen:
            return
        rest = stand.weiterrechnen()
        self._restknopf.pack_forget()
        self._rest_zeigen(rest.vollstaendige_nachricht, rest.erzaehltext)
        self._knopf.configure(text=KNOPF_WEITER)
        self._knopf.pack(side="right")
        self._knopf.focus_set()

    def _rest_zeigen(self, vollstaendige_nachricht, erzaehltext):
        """Zeigt, was der Knopf aufgelöst hat: den Erzähltext über dem Gerät, die Nachricht auf dem Glas.

        Beim Empfangen steht die ganze entschlüsselte Nachricht da. Beim
        Senden nicht – dort ist sie der Geheimtext, den man selbst hätte
        tippen sollen; sichtbar wird nur, dass sie abgegangen ist.
        """
        self._rest_frei = True
        self._erzaehlung.configure(text=erzaehltext)
        if self.funkspruch.richtung == story.EMPFANGEN:
            self._rueckmeldung_setzen([(GANZE_NACHRICHT, stil.FARBE_LEUCHTSCHRIFT),
                                       (vollstaendige_nachricht, stil.FARBE_LEUCHTSCHRIFT_HELL)])
        else:
            self._gesendet()

    def _gesendet(self):
        """Das Sendelämpchen leuchtet, und auf dem Glas steht, dass gesendet ist – nicht, was."""
        self.lampe("senden", True)
        zeilen = [zeile for zeile in self._rueckmeldung if zeile[0] != GESENDET]
        self._rueckmeldung_setzen(zeilen + [(GESENDET, stil.FARBE_LEUCHTSCHRIFT_HELL)])

    def _antwort_festhalten(self):
        """Schreibt, was in der Eingabezeile stand, aufs Glas – und räumt das Feld weg."""
        if self._antwort is not None:
            return
        self._antwort = self._feld.get()
        self.buch.delete("eingabe")
        self._feld.destroy()
        x, y, _, hoehe = self._feldkasten
        self.buch.create_text(x, y + hoehe // 2, text=self._antwort, anchor="w", font=self.schrift,
                              fill=stil.FARBE_LEUCHTSCHRIFT_HELL, tags=("anzeige", "antwort"))

    def weiter(self):
        """Legt den Funkspruch ab – was danach kommt, entscheidet :mod:`ui.ablauf`."""
        if self.durchlauf.spielstand.aktuelle_aufgabe is not None:
            self.durchlauf.aufgabe_abschliessen()
        self._danach(self.fenster)

    # ── Nachschlagen und Lineal ────────────────────────────────────────────

    def _nachschlagen(self):
        """Ins Handbuch – und zurück zu demselben Funkspruch, mit dem, was schon dasteht."""
        danach, entwurf, funkspruch = self._danach, self.eingabe, self.funkspruch
        handbuch.nachschlagen(
            self.fenster,
            funkspruch.level,
            zurueck=lambda fenster: fenster.zeige(Funk, funkspruch=funkspruch, danach=danach, fortsetzen=True,
                                                  entwurf=entwurf),
        )

    def _lineal_benutzt(self):
        """Zählt fürs Log, dass das Lineal bewegt wurde."""
        bearbeitung = self.durchlauf.spielstand.aktuelle_bearbeitung
        if bearbeitung is not None:
            bearbeitung.lineal_benutzt()
