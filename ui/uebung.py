"""Der Aufgaben-Screen (Arbeitsplan 6.5): die Übungen stehen im Buch.

Geübt wird da, wo auch erklärt wird: Bobs Handbuch liegt aufgeschlagen da,
links das Werkzeug zum Lösen, rechts die Übung – Auftrag, der Text, ein
Schreibfeld und darunter die Rückmeldung. Aufgeschrieben wird also mitten im
Buch, wie in einem Übungsheft.

Warum das Werkzeug mit auf den Tisch gehört
───────────────────────────────────────────
Ohne Alphabet, Geheimtabelle oder Quadrat lässt sich keine der drei Methoden
von Hand rechnen. Läge das nur im Handbuch, müsste man für jeden Buchstaben
hin- und herblättern – und diese Zeit stünde hinterher in den Messdaten, ohne
etwas über das Verständnis zu sagen. Was je Level danebenliegt, steht in
``content.handbuch.WERKZEUG_NACH_LEVEL``: bei Caesar bewusst nur das blanke
Alphabet zum Abzählen, denn eine verschobene Zeile wäre für den Schlüssel der
Aufgabe die halbe Lösung. Darunter klebt, wo Platz ist, eine Karte mit den
Sätzen aus dem Handbuch, die sagen, wie man mit dem Werkzeug rechnet
(``content.handbuch.MERKKARTE_NACH_LEVEL``).

Die Regeln kommen aus der Spiellogik
────────────────────────────────────
Dieser Screen rechnet nichts und entscheidet nichts. Er reicht die Eingabe an
:meth:`game.spielstand.Spielstand.versuchen` weiter und zeigt an, was
zurückkommt: die konkrete Fehlermeldung (Projektregel 6), den Hinweis, dass
ein Versuch wegen Fortschritts nicht zählte, die verbleibenden Versuche und
nach dreien ohne Fortschritt die Lösung (Projektregel 2). Auch das Ende der
Aufgabe meldet die Logik, nicht die Anzeige.

Drei Dinge machen die Rückmeldung sichtbar statt nur lesbar:

* Die Stelle, die die Meldung nennt ("im 2. Wort der 5. Buchstabe"), wird im
  Aufgabentext rot unterringelt. Das ist dieselbe Auskunft, nur schneller zu
  finden – welcher Buchstabe dort richtig wäre, verrät sie weiterhin nicht.
* Stimmt die Antwort, schlägt der Stempel "GELÖST" auf die Seite.
* Geschrieben wird in Handschrift, als hätte man den Bleistift selbst in der
  Hand.

Nachschlagen mitten in der Aufgabe
──────────────────────────────────
"Im Handbuch nachschlagen" zeigt das ganze Handbuch (:mod:`ui.handbuch`) und
kommt danach zu **derselben** Aufgabe zurück – samt dem, was schon im
Schreibfeld stand, und dem Stand der Versuche. Die Uhr der Aufgabe läuft
dabei weiter: Nachschlagen gehört zum Lösen.

Was hier noch fehlt
───────────────────
Welche Aufgabe nach der Übung kommt, entscheidet nicht dieser Screen, sondern
:mod:`ui.ablauf` – dort werden in Phase 7 die Funksprüche dazwischen gesetzt.
Bis dahin hängt am unteren Rand ein Platzhalter-Knopf, mit dem sich ein Level
vorzeitig beenden lässt; sonst müsste man beim Durchklicken jedes Zeitfenster
abwarten.
"""

import tkinter as tk

from content import handbuch as buch
from content import verfahren
from game.aufgabe import ENTSCHLUESSELN, QUELLE_UEBUNG, VERSCHLUESSELN
from game.rueckmeldung import bezugsloesung, erste_abweichung
from ui import buchsatz, handbuch, stil
from ui.buchleinwand import Buchleinwand
from ui.screen import Screen

#: Aufschriften der Knöpfe unter dem Buch.
KNOPF_PRUEFEN = "Prüfen"
KNOPF_WEITER = "Weiter"
KNOPF_NACHSCHLAGEN = "Im Handbuch nachschlagen"
#: Platzhalter bis Phase 7 – siehe Modulkopf.
KNOPF_LEVELENDE = "Level beenden (Platzhalter)"

#: Die Überschrift der Übungsseite.
UEBERSCHRIFT = "Übung {nummer}"

#: Der Auftrag über dem Aufgabentext: Richtung und Schlüssel.
RICHTUNGSWORT = {VERSCHLUESSELN: "Verschlüssele", ENTSCHLUESSELN: "Entschlüssele"}
SCHLUESSELANGABE = {
    verfahren.CAESAR: "mit dem Schlüssel {schluessel}",
    verfahren.SUBSTITUTION: "mit deiner Geheimtabelle",
    verfahren.VIGENERE: "mit dem Schlüsselwort {schluessel}",
}

BESCHRIFTUNG_ANTWORT = "Deine Antwort:"
LOB = "Richtig! Genau so stimmt es."
LOESUNGSZEILE = "Die Lösung: {loesung}"
LOESUNGSHINWEIS = "Schau sie dir in Ruhe an – dann geht es weiter."
VERSUCHE_UEBRIG = "Noch {anzahl} Versuche."
LETZTER_VERSUCH = "Noch ein Versuch – danach zeige ich dir die Lösung."

#: Abstände auf der Übungsseite – Pixel im Maßstab 1, wie überall in ui/.
ABSTAND_AUFTRAG = 8
ABSTAND_TEXT = 12
ABSTAND_FELD = 5
ABSTAND_RUECKMELDUNG = 14
#: Höhe des Schreibfelds, in Zeilen der Handschrift.
FELDHOEHE = 1.9
#: Innenabstand im Schreibfeld.
FELDRAND = 6
#: Wo der Stempel "GELÖST" landet – Anteil der Seitenbreite, gemessen an der
#: Mitte des Stempels. Etwas rechts, damit er kurze Antworten nicht zudeckt.
STEMPELSTELLE = 0.62


class Uebung(Screen):
    """Eine Übung im Buch. ``danach(fenster)`` ist, was nach ihr kommt.

    ``fortsetzen`` setzt die offene Aufgabe fort, statt eine neue zu stellen –
    so kommt man vom Nachschlagen zurück; ``entwurf`` ist, was dabei schon im
    Schreibfeld stand.
    """

    def __init__(self, fenster, danach, fortsetzen=False, entwurf=""):
        super().__init__(fenster)
        self.configure(bg=stil.FARBE_NACHT, pady=self.px(handbuch.ABSTAND_KNAPP))
        self.titel = f"Übung – Level {fenster.durchlauf.spielstand.aktuelles_level}"
        self._danach = danach
        self._fortsetzen = fortsetzen
        self._entwurf = entwurf
        #: Die laufende Aufgabe – erst beim Anzeigen gestellt, dann beginnt ihre Uhr.
        self.aufgabe = None
        self._beendet = False
        self._antwort = None
        self._ursprung = (0, 0)
        self._textzeilen = ()
        self._text_oben = 0
        self._feldkasten = (0, 0, 0, 0)
        self._rueckmeldung_oben = 0

        #: Die Leinwand mit dem aufgeschlagenen Buch.
        self.buch = Buchleinwand(self, self.massstab, self.px)
        self.buch.pack(side="top")
        self._feld = tk.Entry(self.buch, font=self.buch.schriften.notiz, bg=stil.FARBE_PAPIER,
                              fg=stil.FARBE_BLEISTIFT, insertbackground=stil.FARBE_BLEISTIFT,
                              relief="flat", highlightthickness=0)
        self._feld.bind("<Return>", lambda _ereignis: self.pruefen())
        self._leiste_bauen()

    # ── Was dasteht ────────────────────────────────────────────────────────

    @property
    def eingabe(self):
        """Was im Schreibfeld steht – nach dem Ende der Aufgabe, was dort stand."""
        return self._antwort if self._antwort is not None else self._feld.get()

    @property
    def knopftext(self):
        return self._knopf.cget("text")

    @property
    def ist_beendet(self):
        """Ist die Aufgabe entschieden – gelöst oder aufgelöst?"""
        return self._beendet

    def texte(self, seite=None):
        """Die Texte, die gerade im Buch stehen (siehe :mod:`ui.buchleinwand`)."""
        return self.buch.texte(seite)

    def rueckmeldung(self):
        """Die Zeilen, die gerade unter dem Schreibfeld stehen."""
        return [self.buch.itemcget(element, "text") for element in self.buch.find_withtag("rueckmeldung")]

    # ── Bauen ──────────────────────────────────────────────────────────────

    def _leiste_bauen(self):
        leiste = tk.Frame(self, bg=stil.FARBE_NACHT)
        leiste.pack(side="top", fill="x", pady=(self.px(handbuch.ABSTAND_KNAPP), 0))
        knopfart = dict(font=stil.SCHRIFT_FETT, highlightbackground=stil.FARBE_NACHT)
        self._nachschlagen_knopf = tk.Button(leiste, text=KNOPF_NACHSCHLAGEN, command=self._nachschlagen,
                                             **knopfart)
        self._nachschlagen_knopf.pack(side="left")
        self._levelknopf = tk.Button(leiste, text=KNOPF_LEVELENDE, command=self._level_beenden,
                                     font=stil.SCHRIFT_KURSIV, highlightbackground=stil.FARBE_NACHT)
        self._levelknopf.pack(side="left", padx=(self.px(stil.ABSTAND), 0))
        self._knopf = tk.Button(leiste, text=KNOPF_PRUEFEN, command=self.pruefen,
                                padx=self.px(stil.ABSTAND), **knopfart)
        self._knopf.pack(side="right")
        self._knopf.bind("<Return>", lambda _ereignis: self._knopf.invoke())

    def beim_anzeigen(self):
        """Hier wird die Aufgabe gestellt – mit ihr beginnt die Uhr."""
        stand = self.durchlauf.spielstand
        if self._fortsetzen and stand.aktuelle_aufgabe is not None:
            # Zurück vom Nachschlagen: dieselbe Aufgabe, ihre Uhr lief weiter.
            aufgabe = stand.aktuelle_aufgabe
        else:
            aufgabe = self.durchlauf.naechste_uebung()
            if aufgabe is None:
                return  # Die Zeit war um – der Levelwechsel hat schon umgeschaltet.
        self.aufgabe = aufgabe
        self._werkzeug_zeichnen()
        self._aufgabe_zeichnen(aufgabe)
        self._feld.insert(0, self._entwurf)
        self._feld.focus_set()
        self._stand_zeigen(stand.aktuelle_bearbeitung)

    def _werkzeug_zeichnen(self):
        """Die linke Seite: womit sich diese Aufgabe von Hand rechnen lässt – und wie."""
        level = self.durchlauf.spielstand.aktuelles_level
        teile = [buch.WERKZEUG_NACH_LEVEL[level]]
        karte = buch.MERKKARTE_NACH_LEVEL[level]
        if karte is not None:
            # Gesetzt wie der Merksatz im Handbuch: als eingeklebte Karte.
            teile.append(buch.Abschnitt(karte.ueberschrift, tuple(buch.Absatz(satz.text) for satz in karte.saetze),
                                        hervorgehoben=True))
        x0, y0, x1, y1 = self.buch.flaeche("links")
        seite = buchsatz.einzelseite(teile, self.buch.schriften, x1 - x0, y1 - y0, self.px)
        self.buch.seite_zeichnen("links", seite.stuecke)

    def auftrag(self, aufgabe):
        """Der Satz über dem Aufgabentext: Richtung und Schlüssel."""
        angabe = SCHLUESSELANGABE[aufgabe.verfahren].format(schluessel=aufgabe.schluessel)
        return f"{RICHTUNGSWORT[aufgabe.richtung]} {angabe}:"

    def _nummer(self, aufgabe):
        """Die wievielte Übung dieses Levels das ist."""
        stand = self.durchlauf.spielstand
        erledigt = [b for b in stand.erledigte_aufgaben_im_level(aufgabe.level)
                    if b.aufgabe.quelle == QUELLE_UEBUNG]
        return len(erledigt) + 1

    def _aufgabe_zeichnen(self, aufgabe):
        """Die rechte Seite: Überschrift, Auftrag, Aufgabentext, Schreibfeld."""
        s, px = self.buch.schriften, self.px
        x0, y0, x1, _ = self.buch.flaeche("rechts")
        self._ursprung = (x0, y0)
        breite = x1 - x0
        stuecke, y = [], 0

        stuecke.append(buchsatz.Zeile(0, y, UEBERSCHRIFT.format(nummer=self._nummer(aufgabe)),
                                      "abschnitt", stil.FARBE_ROTSTIFT, "uebungstitel"))
        y += s.abschnitt.metrics("linespace") + px(ABSTAND_AUFTRAG)
        for zeile in buchsatz.umbrechen(self.auftrag(aufgabe), s.betont, breite):
            stuecke.append(buchsatz.Zeile(0, y, zeile, "betont", stil.FARBE_TINTE, "auftrag"))
            y += s.betont.metrics("linespace")
        y += px(ABSTAND_TEXT)

        # Der Aufgabentext gross: An ihm wird Buchstabe für Buchstabe gerechnet.
        self._textzeilen = tuple(buchsatz.umbrechen(aufgabe.anzeigetext, s.kapitel, breite))
        self._text_oben = y
        for zeile in self._textzeilen:
            stuecke.append(buchsatz.Zeile(0, y, zeile, "kapitel", stil.FARBE_TINTE, "aufgabentext"))
            y += s.kapitel.metrics("linespace")
        y += px(ABSTAND_TEXT)

        stuecke.append(buchsatz.Zeile(0, y, BESCHRIFTUNG_ANTWORT, "klein", stil.FARBE_TINTE, "beschriftung"))
        y += s.klein.metrics("linespace") + px(ABSTAND_FELD)
        feldhoehe = round(s.notiz.metrics("linespace") * FELDHOEHE)
        self._feldkasten = (0, y, breite, feldhoehe)
        y += feldhoehe + px(ABSTAND_RUECKMELDUNG)
        self._rueckmeldung_oben = y

        self.buch.seite_zeichnen("rechts", stuecke)
        self._schreibfeld_zeichnen()

    def _schreibfeld_zeichnen(self):
        """Das Feld, in das geschrieben wird – ein Kasten auf dem Papier."""
        x0, y0 = self._ursprung
        x, y, breite, hoehe = self._feldkasten
        rand = self.px(FELDRAND)
        self.buch.create_rectangle(x0 + x, y0 + y, x0 + x + breite, y0 + y + hoehe,
                                   fill=stil.FARBE_PAPIER, outline=stil.FARBE_BUCHLINIE,
                                   tags=("rechts", "schreibfeld"))
        self.buch.create_window(x0 + x + rand, y0 + y + rand, window=self._feld, anchor="nw",
                                width=breite - 2 * rand, height=hoehe - 2 * rand, tags=("eingabe",))

    # ── Prüfen und Rückmeldung ─────────────────────────────────────────────

    def pruefen(self):
        """Der Knopf unten rechts: erst prüfen, nach dem Ende weiter."""
        if self._beendet:
            self.weiter()
            return
        stand = self.durchlauf.spielstand
        if stand.aktuelle_aufgabe is None:
            return  # Die Zeit ist abgelaufen; der Levelwechsel räumt gleich ab.
        self._ergebnis_zeigen(stand.versuchen(self.eingabe))

    def _ergebnis_zeigen(self, ergebnis):
        zeilen = []
        self.buch.delete("fehlerstelle", "stempel")
        if ergebnis.richtig:
            zeilen.append((LOB, "betont", stil.FARBE_HAKEN))
        else:
            if ergebnis.meldung:
                zeilen.append((ergebnis.meldung, "text", stil.FARBE_ROTSTIFT))
            if ergebnis.hinweis_fortschritt:
                zeilen.append((ergebnis.hinweis_fortschritt, "kursiv", stil.FARBE_TINTE))
            self._fehlerstelle_markieren(self.eingabe)
        if ergebnis.loesung_angezeigt:
            zeilen.append((LOESUNGSZEILE.format(loesung=ergebnis.angezeigte_loesung), "betont",
                           stil.FARBE_TINTE))
            zeilen.append((LOESUNGSHINWEIS, "kursiv", stil.FARBE_TINTE))
        elif not ergebnis.richtig and ergebnis.zaehlte_als_versuch:
            zeilen.append((self._versuchstext(ergebnis.verbleibende_versuche), "klein", stil.FARBE_TINTE))
        self._rueckmeldung_setzen(zeilen)
        if ergebnis.ist_beendet:
            self._beenden(geloest=ergebnis.richtig)

    def _versuchstext(self, verbleibend):
        return LETZTER_VERSUCH if verbleibend == 1 else VERSUCHE_UEBRIG.format(anzahl=verbleibend)

    def _stand_zeigen(self, bearbeitung):
        """Zeigt beim Fortsetzen, wo die Aufgabe steht – Versuche, Lösung, Ende."""
        if bearbeitung is None:
            return
        zeilen = []
        if bearbeitung.loesung_angezeigt:
            zeilen.append((LOESUNGSZEILE.format(loesung=bearbeitung.angezeigte_loesung), "betont",
                           stil.FARBE_TINTE))
            zeilen.append((LOESUNGSHINWEIS, "kursiv", stil.FARBE_TINTE))
        elif bearbeitung.geloest:
            zeilen.append((LOB, "betont", stil.FARBE_HAKEN))
        elif bearbeitung.versuche:
            zeilen.append((self._versuchstext(bearbeitung.verbleibende_versuche), "klein", stil.FARBE_TINTE))
        self._rueckmeldung_setzen(zeilen)
        if bearbeitung.ist_beendet:
            self._beenden(geloest=bearbeitung.geloest)

    def _rueckmeldung_setzen(self, zeilen):
        """Schreibt die Zeilen unter das Schreibfeld – die alten kommen weg."""
        self.buch.delete("rueckmeldung")
        x0, y0 = self._ursprung
        breite = self._feldkasten[2]
        y = self._rueckmeldung_oben
        for text, schrift, farbe in zeilen:
            font = getattr(self.buch.schriften, schrift)
            for zeile in buchsatz.umbrechen(text, font, breite):
                self.buch.create_text(x0, y0 + y, text=zeile, anchor="nw", font=font, fill=farbe,
                                      tags=("rechts", "rueckmeldung", "text", "rueckmeldungszeile"))
                y += font.metrics("linespace")
            y += self.px(4)

    def _stempeln(self):
        """Der Stempel "GELÖST" – schräg auf die Antwort."""
        x0, y0 = self._ursprung
        _, y, breite, hoehe = self._feldkasten
        self.buch.stempel_zeichnen("stempel_geloest", x0 + round(breite * STEMPELSTELLE),
                                   y0 + y + hoehe // 2, tags=("rechts",))

    def _fehlerstelle_markieren(self, eingabe):
        """Unterringelt im Aufgabentext den Buchstaben, an dem es kippt.

        Dieselbe Auskunft, die auch in der Meldung steht ("im 2. Wort der 5.
        Buchstabe") – nur gleich an der richtigen Stelle. Welcher Buchstabe
        dort hingehört, verrät sie nicht.
        """
        abweichung = erste_abweichung(eingabe, bezugsloesung(self.aufgabe, eingabe))
        if abweichung is None:
            return
        stelle = abweichung.anzeigeposition - 1
        for nr, zeile in enumerate(self._textzeilen):
            if stelle < len(zeile):
                break
            stelle -= len(zeile) + 1        # das Leerzeichen, an dem umbrochen wurde
        else:
            return
        if not 0 <= stelle < len(zeile) or zeile[stelle] == " ":
            return
        schrift = self.buch.schriften.kapitel
        x0, y0 = self._ursprung
        staerke = max(1, self.px(2))
        # Um den halben Strich eingerückt: Sonst ragte die Welle unter dem
        # ersten Buchstaben einer Zeile über den Rand der Textfläche hinaus.
        links = x0 + schrift.measure(zeile[:stelle]) + staerke
        breite = max(schrift.measure(zeile[stelle]) - 2 * staerke, self.px(4))
        unten = (y0 + self._text_oben + nr * schrift.metrics("linespace")
                 + schrift.metrics("ascent") + self.px(3))
        self.buch.create_line(*self._welle(links, links + breite, unten), fill=stil.FARBE_ROTSTIFT,
                              width=staerke, tags=("rechts", "fehlerstelle"))

    def _welle(self, von, bis, y):
        """Die Punkte einer kleinen Wellenlinie – wie mit dem Rotstift gezogen."""
        schritt, hub = max(2, self.px(3)), self.px(2)
        punkte = []
        for nr, x in enumerate(range(von, bis + schritt, schritt)):
            punkte += [min(x, bis), y + (hub if nr % 2 else 0)]
        return punkte

    # ── Ende der Aufgabe ───────────────────────────────────────────────────

    def _beenden(self, geloest):
        """Die Aufgabe ist entschieden: Aus "Prüfen" wird "Weiter".

        Das Schreibfeld weicht dabei dem, was darin stand: Die Antwort steht
        jetzt im Buch, und auf ihr kann der Stempel liegen. Ein eingebettetes
        Eingabefeld liegt in Tk immer über allem, was auf der Leinwand steht –
        der Stempel wäre sonst halb dahinter verschwunden.
        """
        self._beendet = True
        self._knopf.configure(text=KNOPF_WEITER)
        self._antwort_festhalten()
        if geloest:
            self._stempeln()
        self._knopf.focus_set()

    def _antwort_festhalten(self):
        """Schreibt, was im Feld stand, als Handschrift ins Buch – und räumt das Feld weg."""
        if self._antwort is not None:
            return
        self._antwort = self._feld.get()
        self.buch.delete("eingabe")
        self._feld.destroy()
        x0, y0 = self._ursprung
        _, y, _, hoehe = self._feldkasten
        self.buch.create_text(x0 + self.px(FELDRAND * 2), y0 + y + hoehe // 2, text=self._antwort,
                              anchor="w", font=self.buch.schriften.notiz, fill=stil.FARBE_BLEISTIFT,
                              tags=("rechts", "text", "antwort"))

    def weiter(self):
        """Schliesst die Aufgabe ab – was danach kommt, entscheidet :mod:`ui.ablauf`."""
        if self.durchlauf.spielstand.aktuelle_aufgabe is not None:
            self.durchlauf.aufgabe_abschliessen()
        self._danach(self.fenster)

    def _nachschlagen(self):
        """Ins Handbuch – und zurück zu derselben Aufgabe, mit dem, was schon dasteht."""
        danach, entwurf = self._danach, self.eingabe
        handbuch.nachschlagen(
            self.fenster,
            self.durchlauf.spielstand.aktuelles_level,
            zurueck=lambda fenster: fenster.zeige(Uebung, danach=danach, fortsetzen=True, entwurf=entwurf),
        )

    def _level_beenden(self):
        """Platzhalter bis Phase 7: das Level vorzeitig beenden."""
        self.durchlauf.naechstes_level()
