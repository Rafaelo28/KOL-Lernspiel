"""Die Figurwahl (Arbeitsplan 6.2): Wer aus der Crew bist du?

Oben steht die Vorgeschichte aus ``content/story.py`` – der Raub, die Flucht,
der Absturz. Darunter liegen die fünf Figuren aus ``content/charaktere.py``
als Karten: Symbol, Initialen, Name, Rolle.

Rollen-Symbole statt Gesichter
──────────────────────────────
Jede Karte zeigt ein Symbol für die Rolle – Tresor, Lupe, Chip, Landkarte,
Pass – statt eines Porträts. Ein gezeichnetes Gesicht legt Aussehen,
Geschlecht und Herkunft fest und wirkt schnell wie ein Klischee; mit einem
Symbol kann sich jedes Kind jede Figur aussuchen. Die Symbole sind kleine
Animationen (``grafik/figur_<kennung>.svg``), aber es bewegt sich nur das der
gewählten Karte – fünf gleichzeitig wären Unruhe.

Erst wählen, dann bestätigen
────────────────────────────
Ein Klick auf eine Karte wählt die Figur nur aus. Erst der Knopf darunter
("Als … spielen") legt sie fest, und damit beginnt der Durchlauf. Danach lässt
sich die Figur nicht mehr wechseln – ein Fenster, ein Durchlauf (siehe
:meth:`ui.hauptfenster.Hauptfenster.starte_durchlauf`). Ein versehentlicher
Klick soll deshalb noch nichts festlegen.

Mit der Tastatur geht es auch: Pfeil links/rechts wechselt die Karte, Enter
bestätigt.

Die Initialen stehen als Siegel auf jeder Karte, weil mit ihnen später jeder
gesendete Funkspruch unterschrieben wird.

Was nach der Wahl geschieht, gibt der Aufrufer als ``danach(fenster, figur)``
mit (siehe :mod:`ui.ablauf`).
"""

import tkinter as tk

from content import charaktere, story
from ui import stil
from ui.animation import Animation, Buehne
from ui.screen import Screen

#: Die Frage über den Karten.
FRAGE = "Wer aus der Crew bist du?"

#: Steht neben dem Knopf – wozu die Initialen auf den Karten da sind.
HINWEIS_INITIALEN = "Mit deinen Initialen unterschreibst du später jeden Funkspruch."

#: Aufschrift des Knopfes, solange keine Karte gewählt ist.
KNOPF_OHNE_WAHL = "Wähle zuerst eine Figur"

#: So breit darf die Vorgeschichte werden, in Pixeln.
TEXTBREITE = 920

#: Innenbreite einer Karte in Pixeln – alle Karten gleich breit. Fünf müssen
#: nebeneinander in das Fenster in Standardgrösse passen (1000 Pixel abzüglich
#: Rand), und das längste Wort einer Rolle ("Diamantenhändlerin") muss in eine
#: Zeile passen: Tk bräche es sonst mitten im Wort um.
KARTENBREITE = 176

#: Stärke des Rahmens um eine Karte – gold, sobald sie gewählt ist.
RAHMEN = 3

#: Lücke links und rechts neben jeder Karte.
LUECKE = 3


def animation_fuer(figur):
    """Name der Animation mit dem Rollen-Symbol einer Figur."""
    return f"figur_{figur.kennung}"


def knopftext(figur):
    """Die Aufschrift des Knopfes, sobald ``figur`` gewählt ist."""
    return f"Als {figur.name} spielen"


class Karte(tk.Frame):
    """Eine Figur zum Anklicken: Symbol mit Initialen, Name, Rolle."""

    def __init__(self, master, figur, beim_klick):
        super().__init__(
            master,
            bg=stil.FARBE_KARTE,
            pady=stil.ABSTAND // 2,
            highlightthickness=RAHMEN,
            highlightbackground=stil.FARBE_KARTENRAND,
            highlightcolor=stil.FARBE_KARTENRAND,
            cursor="hand2",
        )
        self.figur = figur
        self._gewaehlt = False

        self.buehne = Buehne(self, Animation(animation_fuer(figur)), bg=stil.FARBE_KARTE)
        self.buehne.pack()
        # Die Initialen als Siegel unten rechts auf dem Symbol.
        x = self.buehne.animation.breite - 22
        y = self.buehne.animation.hoehe - 22
        self.buehne.create_oval(x - 18, y - 18, x + 18, y + 18, fill=stil.FARBE_NACHT,
                                outline=stil.FARBE_GOLD, width=2)
        self._siegel = self.buehne.create_text(x, y, text=figur.initialen, fill=stil.FARBE_GOLD,
                                               font=stil.SCHRIFT_FETT)

        zeile = KARTENBREITE - stil.ABSTAND // 2
        self._name = tk.Label(self, text=figur.name, font=stil.SCHRIFT_FETT, bg=stil.FARBE_KARTE,
                              fg=stil.FARBE_SAND, wraplength=zeile)
        self._name.pack(pady=(stil.ABSTAND // 2, 0))
        self._rolle = tk.Label(self, text=figur.rolle, bg=stil.FARBE_KARTE, fg=stil.FARBE_DUENE,
                               wraplength=zeile, justify="center")
        self._rolle.pack()

        for teil in self.teile:
            teil.bind("<Button-1>", lambda _ereignis: beim_klick(figur))
            teil.bind("<Enter>", self._maus_drauf)
            teil.bind("<Leave>", self._maus_weg)

    @property
    def teile(self):
        """Die Karte und alles darauf – ein Klick irgendwo darauf wählt die Figur."""
        return (self, self.buehne, self._name, self._rolle)

    @property
    def initialen(self):
        """Was im Siegel steht."""
        return self.buehne.itemcget(self._siegel, "text")

    @property
    def gewaehlt(self):
        return self._gewaehlt

    def markieren(self, gewaehlt):
        """Hebt die Karte als gewählt hervor und lässt ihr Symbol laufen – oder nicht."""
        self._gewaehlt = gewaehlt
        self._rand(stil.FARBE_GOLD if gewaehlt else stil.FARBE_KARTENRAND)
        self._name.config(fg=stil.FARBE_GOLD if gewaehlt else stil.FARBE_SAND)
        if gewaehlt:
            self.buehne.starten()
        else:
            self.buehne.anhalten()
            self.buehne.zeige_bild(0)

    def _rand(self, farbe):
        self.config(highlightbackground=farbe, highlightcolor=farbe)

    def _maus_drauf(self, _ereignis):
        if not self._gewaehlt:
            self._rand(stil.FARBE_KARTENRAND_HELL)

    def enthaelt(self, widget):
        """Gehört ``widget`` zu dieser Karte?

        Verglichen wird der Tk-Pfad. Ein blosses ``startswith`` genügte nicht:
        Die zweite Karte heisst ``….!karte2`` und finge mit dem Namen der
        ersten an.
        """
        pfad = str(widget)
        return pfad == str(self) or pfad.startswith(str(self) + ".")

    def _maus_weg(self, ereignis):
        # Beim Wechsel von der Karte auf ihren Namen meldet Tk ebenfalls ein
        # Verlassen – dann steht der Zeiger aber noch auf der Karte.
        drunter = self.winfo_containing(ereignis.x_root, ereignis.y_root)
        if drunter is not None and self.enthaelt(drunter):
            return
        if not self._gewaehlt:
            self._rand(stil.FARBE_KARTENRAND)


class Figurwahl(Screen):
    titel = "Wähle deine Figur"

    def __init__(self, fenster, danach, figuren=charaktere.SPIELBARE_CHARAKTERE):
        super().__init__(fenster)
        self.configure(bg=stil.FARBE_NACHT)
        self._danach = danach
        self._gewaehlt = None

        for absatz in story.VORGESCHICHTE.absaetze:
            tk.Label(self, text=absatz, font=stil.SCHRIFT_ERZAEHLUNG, bg=stil.FARBE_NACHT, fg=stil.FARBE_SAND,
                     wraplength=TEXTBREITE, justify="left", anchor="w").pack(fill="x", pady=(0, stil.ABSTAND // 2))
        tk.Label(self, text=FRAGE, font=stil.SCHRIFT_TITEL, bg=stil.FARBE_NACHT, fg=stil.FARBE_SAND,
                 anchor="w").pack(fill="x", pady=(stil.ABSTAND // 2, stil.ABSTAND))

        reihe = tk.Frame(self, bg=stil.FARBE_NACHT)
        reihe.pack()
        self.karten = []
        for spalte, figur in enumerate(figuren):
            karte = Karte(reihe, figur, self.waehle)
            karte.grid(row=0, column=spalte, padx=LUECKE, sticky="nsew")
            # Die Spaltenbreite zählt Rahmen und Lücke mit.
            reihe.grid_columnconfigure(spalte, uniform="karte", minsize=KARTENBREITE + 2 * (RAHMEN + LUECKE))
            self.karten.append(karte)

        leiste = tk.Frame(self, bg=stil.FARBE_NACHT)
        leiste.pack(fill="x", pady=(stil.ABSTAND, 0))
        tk.Label(leiste, text=HINWEIS_INITIALEN, bg=stil.FARBE_NACHT, fg=stil.FARBE_DUENE).pack(side="left")
        self._knopf = tk.Button(leiste, command=self.bestaetigen, font=stil.SCHRIFT_FETT, padx=stil.ABSTAND,
                                highlightbackground=stil.FARBE_NACHT)
        self._knopf.pack(side="right")
        self._knopf.bind("<Return>", lambda _ereignis: self._knopf.invoke())
        self._knopf.bind("<Left>", lambda _ereignis: self.blaettern(-1))
        self._knopf.bind("<Right>", lambda _ereignis: self.blaettern(1))
        self._knopf_beschriften()

    @property
    def gewaehlt(self):
        """Die ausgewählte Figur – oder ``None``, solange keine Karte angeklickt ist."""
        return self._gewaehlt

    @property
    def knopftext(self):
        return self._knopf.cget("text")

    def beim_anzeigen(self):
        # Auf dem Knopf liegen Enter und die Pfeiltasten.
        self._knopf.focus_set()

    def waehle(self, figur):
        """Wählt eine Figur aus – festgelegt ist sie erst mit :meth:`bestaetigen`."""
        self._gewaehlt = figur
        for karte in self.karten:
            karte.markieren(karte.figur == figur)
        self._knopf_beschriften()
        self._knopf.focus_set()

    def blaettern(self, schritt):
        """Wählt die Karte ``schritt`` Plätze weiter (Pfeiltasten), im Kreis."""
        figuren = [karte.figur for karte in self.karten]
        if self._gewaehlt is None:
            nr = 0 if schritt > 0 else len(figuren) - 1
        else:
            nr = (figuren.index(self._gewaehlt) + schritt) % len(figuren)
        self.waehle(figuren[nr])

    def bestaetigen(self):
        """Legt die gewählte Figur fest; ohne Wahl geschieht nichts."""
        if self._gewaehlt is None or not self.ist_angezeigt:
            return
        self._danach(self.fenster, self._gewaehlt)

    def _knopf_beschriften(self):
        if self._gewaehlt is None:
            self._knopf.config(text=KNOPF_OHNE_WAHL, state="disabled")
        else:
            self._knopf.config(text=knopftext(self._gewaehlt), state="normal")
