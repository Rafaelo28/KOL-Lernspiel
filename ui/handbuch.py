"""Der Handbuch-Screen (Arbeitsplan 6.4): Bobs Verschlüsselungshandbuch.

Zu Beginn jedes Levels liegt die Seite dieses Levels aufgeschlagen vor den
Spielenden: oben der Einstiegssatz aus der Geschichte ("Du schlägst das
Handbuch auf …"), darunter die Seite selbst – ein Blatt Papier auf dem
Nachthimmel, das sich scrollen lässt. Der Inhalt kommt aus
``content/handbuch.py``: Überschriften, Absätze, Aufzählungen, Tabellen als
Raster, die Merksätze farbig hinterlegt. Das Vigenère-Quadrat auf Seite 3
wird aus der Formel gezeichnet (``crypto/vigenere_quadrat.py``), nicht
abgetippt. Hervorheben, welche Zeile und Spalte gerade gebraucht wird, kommt
mit Aufgabe 6.7 dazu.

Nachschlagen während der Aufgaben
─────────────────────────────────
Das Handbuch muss während der Übungen und Funksprüche erreichbar bleiben –
Nachschlagen ist erlaubt. :func:`nachschlagen` zeigt dieselbe Seite mit dem
Knopf "Zurück zur Aufgabe". Die Aufgabe bleibt dabei offen, und ihre Uhr
läuft weiter: Nachschlagen gehört zum Lösen. Den Rückweg gibt der Aufgaben-
Screen als ``zurueck(fenster)`` mit; er baut sich frisch auf und setzt
dieselbe Aufgabe fort, statt eine neue zu stellen – so macht es schon der
Platzhalter der Übung in :mod:`ui.platzhalter`.

Warum ein Textfeld
──────────────────
``tk.Text`` bricht den Fließtext von selbst um, scrollt mit Mausrad und
Tasten und kennt hängende Einzüge für Aufzählungen. Tabellen und das Quadrat
sitzen als eingebettete Fenster im Text und scrollen mit. Nur das Mausrad
käme über ihnen nicht beim Text an – deshalb leiten sie es weiter.

Die Seite ist höchstens :data:`SEITENBREITE` breit: Auf einem 1920 Pixel
breiten Monitor wären die Zeilen sonst viel zu lang zum Lesen.
"""

import tkinter as tk
from tkinter import ttk

from content import handbuch as buch
from crypto.normalize import ALPHABET
from crypto.vigenere_quadrat import erzeuge_quadrat
from ui import stil
from ui.screen import Screen

#: Aufschrift des Knopfes zu Beginn eines Levels.
KNOPF_WEITER = "Zu den Übungen"

#: Aufschrift des Knopfes beim Nachschlagen mitten in einer Aufgabe.
KNOPF_ZURUECK = "Zurück zur Aufgabe"

#: So breit wird die Seite höchstens – in Pixeln im Maßstab 1, wie alle
#: festen Grössen hier (siehe ui/stil.py, "Der Maßstab"). Die Tabellen mit
#: 26 Buchstaben müssen hineinpassen.
SEITENBREITE = 860

#: Rand zwischen Papierkante und Text.
SEITENRAND = 28

#: Kantenlänge eines Feldes im Vigenère-Quadrat.
QUADRATFELD = 22

#: Wie weit eine Raste am Mausrad rollt, in Zeilen – über Tabellen und Quadrat.
ZEILEN_JE_RASTE = 3


def nachschlagen(fenster, level, zurueck):
    """Schlägt die Handbuchseite mitten in einer Aufgabe auf.

    ``zurueck(fenster)`` ist der Weg zurück zur Aufgabe. Die Aufgabe bleibt
    offen, ihre Uhr läuft weiter – Nachschlagen gehört zum Lösen.
    """
    return fenster.zeige(Handbuch, level=level, danach=zurueck, knopf=KNOPF_ZURUECK)


class Handbuch(Screen):
    """Eine Handbuchseite. ``danach(fenster)`` ist, was der Knopf unten tut.

    ``einleitung`` sind Absätze über der Seite (der Einstieg ins Level),
    ``hinweis`` eine Zeile davor – etwa, dass die Zeit des letzten Levels
    abgelaufen ist.
    """

    fuellt_fenster = True

    def __init__(self, fenster, level, danach, knopf=KNOPF_WEITER, hinweis="", einleitung=()):
        super().__init__(fenster)
        self.configure(bg=stil.FARBE_NACHT)
        self.titel = f"Handbuch – Level {level}"
        self.seite = buch.SEITE_NACH_LEVEL[level]
        self._danach = danach
        self.tabellen = []
        self.quadrat = None

        spalte = tk.Frame(self, bg=stil.FARBE_NACHT, width=self.px(SEITENBREITE))
        spalte.pack(fill="y", expand=True)
        # Die Spalte behält ihre Breite, statt sich nach dem Inhalt zu richten.
        spalte.pack_propagate(False)

        self._hinweis = self._zeile(spalte, hinweis, stil.FARBE_WARNUNG, stil.SCHRIFT_FETT)
        self._einleitung = [self._zeile(spalte, absatz, stil.FARBE_SAND, stil.SCHRIFT_ERZAEHLUNG)
                            for absatz in einleitung]

        leiste = tk.Frame(spalte, bg=stil.FARBE_NACHT)
        leiste.pack(side="bottom", fill="x", pady=(self.px(stil.ABSTAND // 2), 0))
        self._knopf = tk.Button(leiste, text=knopf, command=self.weiter, font=stil.SCHRIFT_FETT,
                                padx=self.px(stil.ABSTAND), highlightbackground=stil.FARBE_NACHT)
        self._knopf.pack(side="right")
        self._knopf.bind("<Return>", lambda _ereignis: self._knopf.invoke())

        blatt = tk.Frame(spalte, bg=stil.FARBE_PAPIER)
        blatt.pack(side="top", fill="both", expand=True)
        self.text = tk.Text(
            blatt,
            wrap="word",
            width=1,
            height=1,
            bg=stil.FARBE_PAPIER,
            fg=stil.FARBE_TINTE,
            font=stil.SCHRIFT_ERZAEHLUNG,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=self.px(SEITENRAND),
            pady=self.px(SEITENRAND * 3 // 4),
            cursor="arrow",
            insertwidth=0,
        )
        rollbalken = ttk.Scrollbar(blatt, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=rollbalken.set)
        rollbalken.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        self._tags_einrichten()
        self._seite_setzen()
        # Lesen ja, schreiben nein.
        self.text.configure(state="disabled")

    # ── Was darauf steht ───────────────────────────────────────────────────

    @property
    def inhalt(self):
        """Der Text der Seite, wie er dasteht (ohne Tabellen und Quadrat)."""
        return self.text.get("1.0", "end-1c")

    @property
    def hinweis(self):
        return self._hinweis.cget("text") if self._hinweis else ""

    @property
    def einleitung(self):
        return tuple(zeile.cget("text") for zeile in self._einleitung)

    @property
    def knopftext(self):
        return self._knopf.cget("text")

    def quadratfeld(self, schluesselbuchstabe, nachrichtenbuchstabe):
        """Was im gezeichneten Quadrat in dieser Zeile und Spalte steht."""
        zeile, spalte = ALPHABET.index(schluesselbuchstabe), ALPHABET.index(nachrichtenbuchstabe)
        (element,) = self.quadrat.find_withtag(f"z{zeile}&&s{spalte}")
        return self.quadrat.itemcget(element, "text")

    # ── Bauen ──────────────────────────────────────────────────────────────

    def _zeile(self, spalte, text, farbe, schrift):
        if not text:
            return None
        zeile = tk.Label(spalte, text=text, bg=stil.FARBE_NACHT, fg=farbe, font=schrift, anchor="w",
                         justify="left", wraplength=self.px(SEITENBREITE))
        zeile.pack(side="top", fill="x", pady=(0, self.px(stil.ABSTAND // 2)))
        return zeile

    def _tags_einrichten(self):
        px, text = self.px, self.text
        text.tag_configure("kopf", font=stil.SCHRIFT_FETT, foreground=stil.FARBE_ROTSTIFT, justify="center")
        text.tag_configure("untertitel", font=stil.SCHRIFT_KURSIV, justify="center", spacing3=px(18))
        text.tag_configure("seitentitel", font=stil.SCHRIFT_TITEL, spacing3=px(4))
        text.tag_configure("abschnitt", font=stil.SCHRIFT_ABSCHNITT, foreground=stil.FARBE_ROTSTIFT,
                           spacing1=px(18), spacing3=px(6))
        text.tag_configure("absatz", spacing3=px(8))
        text.tag_configure("betont", font=stil.SCHRIFT_BETONT)
        einzug = px(30)
        text.tag_configure("punkt", lmargin1=px(8), lmargin2=einzug, tabs=(einzug,), spacing3=px(5))
        text.tag_configure("tabellentitel", font=stil.SCHRIFT_KURSIV, justify="center", spacing1=px(4),
                           spacing3=px(4))
        text.tag_configure("tabelle", justify="center", spacing3=px(12))
        rand = px(14)
        text.tag_configure("merksatz", background=stil.FARBE_MERKSATZ, lmargin1=rand, lmargin2=rand,
                           rmargin=rand, lmargincolor=stil.FARBE_MERKSATZ, rmargincolor=stil.FARBE_MERKSATZ)
        # Der Merksatz-Kasten beginnt mit seiner Überschrift und endet mit einer
        # leeren, ebenfalls hinterlegten Zeile – so hat er oben und unten Luft.
        text.tag_configure("kastenende", spacing3=px(2))
        # Tags, die später dazukommen, gewinnen – der Merksatz soll über "absatz" liegen.
        text.tag_raise("merksatz")

    def _seite_setzen(self):
        text = self.text
        text.insert("end", buch.HANDBUCH_TITEL.upper() + "\n", "kopf")
        text.insert("end", buch.HANDBUCH_UNTERTITEL + "\n", "untertitel")
        text.insert("end", self.seite.titel + "\n", "seitentitel")
        for abschnitt in self.seite.abschnitte:
            kasten = ("merksatz",) if abschnitt.hervorgehoben else ()
            text.insert("end", abschnitt.ueberschrift + "\n", ("abschnitt",) + kasten)
            for block in abschnitt.bloecke:
                self._block_setzen(block, kasten)
            if kasten:
                text.insert("end", "\n", ("kastenende",) + kasten)

    def _block_setzen(self, block, kasten):
        text = self.text
        if isinstance(block, buch.Absatz):
            text.insert("end", block.text + "\n", ("absatz",) + (("betont",) if block.betont else ()) + kasten)
        elif isinstance(block, buch.Aufzaehlung):
            for nr, punkt in enumerate(block.punkte, 1):
                zeichen = f"{nr}." if block.nummeriert else "•"
                text.insert("end", f"{zeichen}\t{punkt}\n", ("punkt",) + kasten)
        elif isinstance(block, buch.Tabelle):
            if block.titel:
                text.insert("end", block.titel + "\n", ("tabellentitel",) + kasten)
            tabelle = self._tabelle_bauen(block)
            self.tabellen.append(tabelle)
            self._einbetten(tabelle, kasten)
        elif isinstance(block, buch.VigenereQuadrat):
            if block.beschriftung:
                text.insert("end", block.beschriftung + "\n", ("tabellentitel",) + kasten)
            self.quadrat = self._quadrat_bauen()
            self._einbetten(self.quadrat, kasten)
        else:
            raise TypeError(f"Diesen Block kennt das Handbuch nicht: {block!r}")

    def _einbetten(self, fenster, kasten):
        """Setzt eine Tabelle oder das Quadrat mittig in eine eigene Zeile."""
        anfang = self.text.index("end-1c")
        self.text.window_create("end", window=fenster)
        self.text.insert("end", "\n")
        self.text.tag_add("tabelle", anfang, "end-1c")
        for tag in kasten:
            self.text.tag_add(tag, anfang, "end-1c")
        self._mausrad_weiterleiten(fenster)

    def _tabelle_bauen(self, tabelle):
        """Ein Raster: erste Spalte die Beschriftung, dahinter die Buchstaben.

        Die Linien sind der Grund des Rahmens, der zwischen den Zellen
        durchscheint.
        """
        rahmen = tk.Frame(self.text, bg=stil.FARBE_PAPIERLINIE, padx=1, pady=1)
        letzte = len(tabelle.zeilen) - 1
        for nr, (beschriftung, *zellen) in enumerate(tabelle.zeilen):
            unten = 0 if nr == letzte else 1
            tk.Label(rahmen, text=beschriftung, font=stil.SCHRIFT_FETT, bg=stil.FARBE_PAPIER_DUNKEL,
                     fg=stil.FARBE_TINTE, anchor="w", padx=self.px(8), pady=self.px(3)).grid(
                row=nr, column=0, sticky="nsew", padx=(0, 1), pady=(0, unten))
            for spalte, zelle in enumerate(zellen, 1):
                tk.Label(rahmen, text=zelle, font="TkFixedFont", width=2, bg=stil.FARBE_PAPIER,
                         fg=stil.FARBE_TINTE, pady=self.px(3)).grid(
                    row=nr, column=spalte, sticky="nsew", padx=(0, 0 if spalte == len(zellen) else 1),
                    pady=(0, unten))
        return rahmen

    def _quadrat_bauen(self):
        """Das Vigenère-Quadrat: Kopfzeile Nachricht, Kopfspalte Schlüssel, 26 × 26 Felder.

        Jedes Feld trägt die Tags ``z<Zeile>`` und ``s<Spalte>`` (ab 0) – damit
        lässt es sich finden und später hervorheben (Aufgabe 6.7).
        """
        feld = self.px(QUADRATFELD)
        anzahl = len(ALPHABET) + 1
        kante = anzahl * feld
        leinwand = tk.Canvas(self.text, width=kante + 1, height=kante + 1, bg=stil.FARBE_PAPIER,
                             highlightthickness=0)
        leinwand.create_rectangle(0, 0, kante, feld, fill=stil.FARBE_PAPIER_DUNKEL, width=0)
        leinwand.create_rectangle(0, 0, feld, kante, fill=stil.FARBE_PAPIER_DUNKEL, width=0)
        mitte = feld / 2
        for nr, buchstabe in enumerate(ALPHABET, 1):
            leinwand.create_text(nr * feld + mitte, mitte, text=buchstabe, font=stil.SCHRIFT_FETT,
                                 fill=stil.FARBE_ROTSTIFT, tags=("kopfzeile", f"s{nr - 1}"))
            leinwand.create_text(mitte, nr * feld + mitte, text=buchstabe, font=stil.SCHRIFT_FETT,
                                 fill=stil.FARBE_ROTSTIFT, tags=("kopfspalte", f"z{nr - 1}"))
        for zeile, reihe in enumerate(erzeuge_quadrat()):
            for spalte, buchstabe in enumerate(reihe):
                leinwand.create_text((spalte + 1) * feld + mitte, (zeile + 1) * feld + mitte, text=buchstabe,
                                     font="TkFixedFont", fill=stil.FARBE_TINTE,
                                     tags=("feld", f"z{zeile}", f"s{spalte}"))
        for nr in range(anzahl + 1):
            staerke = 2 if nr in (0, 1, anzahl) else 1
            leinwand.create_line(nr * feld, 0, nr * feld, kante, fill=stil.FARBE_PAPIERLINIE, width=staerke)
            leinwand.create_line(0, nr * feld, kante, nr * feld, fill=stil.FARBE_PAPIERLINIE, width=staerke)
        return leinwand

    # ── Bedienen ───────────────────────────────────────────────────────────

    def _mausrad_weiterleiten(self, fenster):
        """Über Tabellen und dem Quadrat rollt das Mausrad die Seite – wie überall sonst."""
        for teil in (fenster, *fenster.winfo_children()):
            teil.bind("<MouseWheel>", self._mausrad)
            teil.bind("<Button-4>", lambda _ereignis: self.rollen(-ZEILEN_JE_RASTE))
            teil.bind("<Button-5>", lambda _ereignis: self.rollen(ZEILEN_JE_RASTE))

    def _mausrad(self, ereignis):
        # Windows meldet je Raste 120, macOS und Touchpads kleinere Werte –
        # dann rollt es wenigstens eine Zeile.
        zeilen = round(-ereignis.delta / 120 * ZEILEN_JE_RASTE)
        self.rollen(zeilen or (-1 if ereignis.delta > 0 else 1))

    def rollen(self, zeilen):
        """Rollt die Seite um ``zeilen`` Zeilen, nach unten positiv."""
        self.text.yview_scroll(zeilen, "units")

    def beim_anzeigen(self):
        # Mit dem Fokus auf der Seite rollen auch Pfeiltasten und Bild auf/ab.
        self.text.focus_set()

    def weiter(self):
        """Zu den Übungen – oder zurück zur Aufgabe, wenn nachgeschlagen wurde."""
        self._danach(self.fenster)
