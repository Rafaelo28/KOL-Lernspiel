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

Das Lineal in Level 3
─────────────────────
Neben einer Vigenère-Übung liegt das Quadrat mit 676 Feldern. Damit beim
Nachschlagen niemand um eine Zeile verrutscht, lässt sich ein Lineal anlegen
(:mod:`ui.lineal`): ein Klick auf den Schlüsselbuchstaben links, einer auf den
Buchstaben der Nachricht oben. Abgelesen wird weiter selbst; wie oft es bewegt
wurde, zählt die Spiellogik fürs Log mit.

Dass es das Lineal gibt, sagt der Tipp über dem Schreibfeld – in Rotstift und
Handschrift, schief wie hingekritzelt. Bei der ersten Aufgabe des Levels legt
sich das Lineal zusätzlich von selbst an, auf einem Feld weit weg von dem, mit
dem die Aufgabe anfängt (:func:`ui.lineal.vorzeigefeld`). Beides kam nach dem
Pilotdurchlauf dazu: Am unteren Seitenrand, wo der Satz vorher stand, hat ihn
die erste Testperson nicht gesehen.

Nachschlagen mitten in der Aufgabe
──────────────────────────────────
"Im Handbuch nachschlagen" zeigt das ganze Handbuch (:mod:`ui.handbuch`) und
kommt danach zu **derselben** Aufgabe zurück – samt dem, was schon im
Schreibfeld stand, und dem Stand der Versuche. Die Uhr der Aufgabe läuft
dabei weiter: Nachschlagen gehört zum Lösen.

Was nach der Übung kommt
────────────────────────
Das entscheidet nicht dieser Screen, sondern die Spiellogik
(:mod:`game.levelablauf`): die nächste Übung, eine Zusatzaufgabe, der nächste
Funkspruch oder das Ende des Levels. Hier wird nur ``danach(fenster)``
gerufen, und :mod:`ui.ablauf` zeigt, was drankommt.

``zusatzaufgabe`` sagt, ob diese Übung eine Extraaufgabe für die Schnellen ist
(Arbeitsplan 5.4). Für die Aufgabe selbst macht es keinen Unterschied – sie
kommt aus demselben Pool –, aber im Log stehen beide getrennt.
"""

import math
import tkinter as tk

from content import verfahren
from game.aufgabe import ENTSCHLUESSELN, QUELLE_UEBUNG, VERSCHLUESSELN
from game.rueckmeldung import bezugsloesung, erste_abweichung
from ui import buchsatz, handbuch, lineal, stil
from ui.buchleinwand import Buchleinwand
from ui.screen import Screen

#: Aufschriften der Knöpfe unter dem Buch.
KNOPF_PRUEFEN = "Prüfen"
KNOPF_WEITER = "Weiter"
KNOPF_NACHSCHLAGEN = "Im Handbuch nachschlagen"

#: Die Überschrift der Übungsseite.
UEBERSCHRIFT = "Übung {nummer}"

#: Der Auftrag über dem Aufgabentext: Richtung und Schlüssel.
#:
#: Das Richtungswort steht in Großbuchstaben, weil "Verschlüssele" und
#: "Entschlüssele" sich nur in der Vorsilbe unterscheiden – zwölf gleiche
#: Buchstaben am Ende, drei am Anfang. Im Pilotdurchlauf hat deshalb jemand
#: einen Geheimtext ein zweites Mal verschlüsselt. Gesetzt wird es ausserdem
#: in Rotstift (:meth:`Uebung._auftrag_setzen`): zwei Unterscheidungen statt
#: einer, falls jemand die Farben schlecht auseinanderhält.
RICHTUNGSWORT = {VERSCHLUESSELN: "VERSCHLÜSSELN", ENTSCHLUESSELN: "ENTSCHLÜSSELN"}
#: Kurz gehalten, damit sie neben dem grossen Richtungswort auf dieselbe
#: Zeile passt, auf der vorher der ganze Satz stand – in beiden Maßstäben.
SCHLUESSELANGABE = {
    verfahren.CAESAR: "– Schlüssel {schluessel}",
    verfahren.SUBSTITUTION: "– deine Geheimtabelle",
    verfahren.VIGENERE: "– Schlüsselwort {schluessel}",
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


def versuchstext(verbleibend):
    """Wie viele Versuche noch bleiben – beim letzten deutlich."""
    return LETZTER_VERSUCH if verbleibend == 1 else VERSUCHE_UEBRIG.format(anzahl=verbleibend)


def welle(px, von, bis, y):
    """Die Punkte einer kleinen Wellenlinie – wie mit dem Rotstift gezogen."""
    schritt, hub = max(2, px(3)), px(2)
    punkte = []
    for nr, x in enumerate(range(von, bis + schritt, schritt)):
        punkte += [min(x, bis), y + (hub if nr % 2 else 0)]
    return punkte


class Uebung(Screen):
    """Eine Übung im Buch. ``danach(fenster)`` ist, was nach ihr kommt.

    ``fortsetzen`` setzt die offene Aufgabe fort, statt eine neue zu stellen –
    so kommt man vom Nachschlagen zurück; ``entwurf`` ist, was dabei schon im
    Schreibfeld stand. ``zusatzaufgabe`` stellt eine Extraaufgabe (5.4).
    """

    def __init__(self, fenster, danach, fortsetzen=False, entwurf="", zusatzaufgabe=False):
        """Baut die Übungsseite: das Buch als Leinwand, darunter die Knopfleiste.

        Die Aufgabe wird hier noch **nicht** gezogen – das geschieht in
        :meth:`beim_anzeigen`, weil mit ihr die Uhr der Aufgabe beginnt.
        """
        super().__init__(fenster)
        self.configure(bg=stil.FARBE_NACHT, pady=self.px(handbuch.ABSTAND_KNAPP))
        self.titel = f"Übung – Level {fenster.durchlauf.spielstand.aktuelles_level}"
        self._danach = danach
        self._fortsetzen = fortsetzen
        self._entwurf = entwurf
        self._zusatzaufgabe = zusatzaufgabe
        #: Die laufende Aufgabe – erst beim Anzeigen gestellt, dann beginnt ihre Uhr.
        self.aufgabe = None
        self._beendet = False
        self._antwort = None
        self._ursprung = (0, 0)
        self._textzeilen = ()
        self._text_oben = 0
        self._feldkasten = (0, 0, 0, 0)
        self._rueckmeldung_oben = 0
        #: Das Lineal im Quadrat – nur, wenn links das Quadrat liegt (Level 3).
        self.lineal = None

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
        """Was auf dem grossen Knopf rechts steht: "Prüfen" oder "Weiter"."""
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
        """Baut die Knopfleiste unter dem Buch: links Nachschlagen, rechts Prüfen."""
        leiste = tk.Frame(self, bg=stil.FARBE_NACHT)
        leiste.pack(side="top", fill="x", pady=(self.px(handbuch.ABSTAND_KNAPP), 0))
        knopfart = dict(font=stil.SCHRIFT_FETT, highlightbackground=stil.FARBE_NACHT)
        self._nachschlagen_knopf = tk.Button(leiste, text=KNOPF_NACHSCHLAGEN, command=self._nachschlagen,
                                             **knopfart)
        self._nachschlagen_knopf.pack(side="left")
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
            aufgabe = self.durchlauf.naechste_uebung(zusatzaufgabe=self._zusatzaufgabe)
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
        seite = self.buch.werkzeug_zeichnen(self.durchlauf.spielstand.aktuelles_level)
        if self.lineal is None:
            self.lineal = lineal.anlegen(self.buch, "links", seite.stuecke, bei_benutzung=self._lineal_benutzt)
            if self.lineal is not None and self._erste_aufgabe_im_level():
                self.lineal.vorzeigen(lineal.vorzeigefeld(lineal.erster_schritt(self.aufgabe)))

    def _erste_aufgabe_im_level(self):
        """Ist das die erste Aufgabe dieses Levels?

        Dann zeigt sich das Lineal von selbst. Später nicht mehr: Wer schon
        eine Aufgabe hinter sich hat, weiss davon – und ein Lineal, das bei
        jeder Übung von vorn an fremder Stelle liegt, wäre nur im Weg.
        """
        stand = self.durchlauf.spielstand
        return not stand.erledigte_aufgaben_im_level(stand.aktuelles_level)

    def _lineal_benutzt(self):
        """Zählt fürs Log, dass das Lineal bewegt wurde."""
        bearbeitung = self.durchlauf.spielstand.aktuelle_bearbeitung
        if bearbeitung is not None:
            bearbeitung.lineal_benutzt()

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
        y = self._auftrag_setzen(stuecke, y, breite, aufgabe)
        y += px(ABSTAND_TEXT)

        # Der Aufgabentext gross: An ihm wird Buchstabe für Buchstabe gerechnet.
        self._textzeilen = tuple(buchsatz.umbrechen(aufgabe.anzeigetext, s.kapitel, breite))
        self._text_oben = y
        for zeile in self._textzeilen:
            stuecke.append(buchsatz.Zeile(0, y, zeile, "kapitel", stil.FARBE_TINTE, "aufgabentext"))
            y += s.kapitel.metrics("linespace")
        y += px(ABSTAND_TEXT)

        if self.lineal is not None:
            y += self._lineal_tipp_setzen(stuecke, y, breite)

        stuecke.append(buchsatz.Zeile(0, y, BESCHRIFTUNG_ANTWORT, "klein", stil.FARBE_TINTE, "beschriftung"))
        y += s.klein.metrics("linespace") + px(ABSTAND_FELD)
        feldhoehe = round(s.notiz.metrics("linespace") * FELDHOEHE)
        self._feldkasten = (0, y, breite, feldhoehe)
        y += feldhoehe + px(ABSTAND_RUECKMELDUNG)
        self._rueckmeldung_oben = y

        self.buch.seite_zeichnen("rechts", stuecke)
        self._schreibfeld_zeichnen()

    def _auftrag_setzen(self, stuecke, y, breite, aufgabe):
        """Setzt den Auftrag: das Richtungswort in Rotstift, die Schlüsselangabe daneben.

        Beides bleibt auf einer Zeile, solange die Angabe neben das Wort passt
        – so rutscht auf der Seite nichts nach unten. Nur wenn sie das nicht
        tut, steht sie darunter. Warum das Wort auffallen muss, steht bei
        :data:`RICHTUNGSWORT`.
        """
        s = self.buch.schriften
        zeilenhoehe = s.betont.metrics("linespace")
        wort = RICHTUNGSWORT[aufgabe.richtung]
        angabe = SCHLUESSELANGABE[aufgabe.verfahren].format(schluessel=aufgabe.schluessel) + ":"
        stuecke.append(buchsatz.Zeile(0, y, wort, "betont", stil.FARBE_ROTSTIFT, "auftrag"))
        neben = s.betont.measure(wort + " ")
        zeilen = buchsatz.umbrechen(angabe, s.betont, max(breite - neben, 1))
        if len(zeilen) > 1 or s.betont.measure(zeilen[0]) > breite - neben:
            # Passt sie nicht ganz daneben, steht sie ganz darunter: ein halb
            # umbrochener Auftrag neben dem Wort sähe aus wie ein Satzfehler.
            y += zeilenhoehe
            neben, zeilen = 0, buchsatz.umbrechen(angabe, s.betont, breite)
        for nummer, text in enumerate(zeilen):
            stuecke.append(buchsatz.Zeile(neben if nummer == 0 else 0, y, text, "betont",
                                          stil.FARBE_TINTE, "auftrag"))
            y += zeilenhoehe
        return y

    def _lineal_tipp_setzen(self, stuecke, y, breite):
        """Schreibt den Tipp auf das Lineal zwischen Aufgabentext und Schreibfeld.

        Rotstift, Handschrift und derselbe kleine Winkel wie bei Bobs
        Randnotizen im Handbuch (:data:`ui.buchsatz.NOTIZWINKEL`) – so liest
        es sich wie mit der Hand dazugeschrieben und nicht wie gedruckter Text,
        den man überblättert. Rückgabe ist die Höhe, die er braucht.

        Schief gestellt steigt das rechte Ende nach oben; deshalb beginnt der
        Text um genau diese Höhe tiefer, sonst ragte er in den Aufgabentext.
        """
        s, px = self.buch.schriften, self.px
        zeilen = buchsatz.umbrechen(lineal.HINWEIS, s.notiz, breite)
        schraeg = math.ceil(breite * math.sin(math.radians(buchsatz.NOTIZWINKEL)))
        stuecke.append(buchsatz.Zeile(0, y + schraeg, "\n".join(zeilen), "notiz", stil.FARBE_ROTSTIFT,
                                      "linealhinweis", winkel=buchsatz.NOTIZWINKEL))
        return schraeg + len(zeilen) * s.notiz.metrics("linespace") + px(ABSTAND_TEXT)

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
        """Schreibt die Rückmeldung zu einem Versuch auf die Buchseite und markiert die Fehlerstelle.

        Je nach Ergebnis steht dort Lob und ein Stempel, eine Meldung mit der
        ersten falschen Stelle, der Hinweis auf Fortschritt, die Zahl der
        übrigen Versuche – oder die Lösung, wenn drei Versuche ohne
        Fortschritt vorbei sind.
        """
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
            zeilen.append((versuchstext(ergebnis.verbleibende_versuche), "klein", stil.FARBE_TINTE))
        self._rueckmeldung_setzen(zeilen)
        if ergebnis.ist_beendet:
            self._beenden(geloest=ergebnis.richtig)

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
            zeilen.append((versuchstext(bearbeitung.verbleibende_versuche), "klein", stil.FARBE_TINTE))
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
        self.buch.create_line(*welle(self.px, links, links + breite, unten), fill=stil.FARBE_ROTSTIFT,
                              width=staerke, tags=("rechts", "fehlerstelle"))

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

