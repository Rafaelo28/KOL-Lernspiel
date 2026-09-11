"""Der Startbildschirm (Arbeitsplan 6.2).

Das Titelbild läuft als Animation (siehe :mod:`ui.animation`): ein großer
Diamant im Nachthimmel über der Wüste, Lichtreflexe wandern über seine
Facetten, danach glänzt der Schriftzug auf. Darunter tragen die Spielenden
ihre ID ein und klicken "Spiel starten". Die Geschichte beginnt erst auf dem
nächsten Screen, der Figurwahl.

Die ID
──────
Die Lehrkraft verteilt IDs der Form ``1-12`` – Klasse, Strich, Nummer (siehe
:mod:`game.spieler_id`). Unter dieser ID steht der Durchlauf im Log; einen
Namen sieht das Spiel nie (Projektregel 7). Das Feld nimmt nur Ziffern und den
Strich an seiner Stelle an, einen Namen kann man also gar nicht erst
eintippen. Wer nach der Klasse gleich die Nummer tippt, bekommt den Strich
dazu. Fehlt beim Start noch etwas, steht über dem Feld genau, was.

Löschen ist dagegen immer erlaubt – sonst liesse sich eine vertippte Ziffer
nicht mehr korrigieren. Was dabei an Unfertigem entsteht, fängt die Prüfung
beim Start ab.

Der Schriftzug steckt im Bild (``grafik/titel.svg``), der Untertitel nicht:
Er wird im Spiel über die Dünen gelegt und lässt sich hier ändern, ohne neu
zu rendern.

Was nach dem Start kommt, gibt der Aufrufer als ``danach(fenster, id)`` mit
(siehe :mod:`ui.ablauf`) – wie beim Story-Intro weiss der Screen nichts vom
Ablauf.
"""

import tkinter as tk

from game import spieler_id
from ui import stil
from ui.animation import Animation, Buehne
from ui.screen import Screen

#: Die Animation – content/animationen/titel.
ANIMATION = "titel"

#: Steht unter dem Schriftzug, über den Dünen.
UNTERTITEL = "Ein Lernspiel über Verschlüsselung"

#: Höhe des Untertitels in der Szene (Pixel von oben) – unter dem Schriftzug,
#: der bei 444 endet.
UNTERTITEL_Y = 478

#: Höhe der Hinweiszeile zur ID, ebenfalls über den Dünen. Sie steht im Bild
#: statt unter dem Feld: Darunter wäre kein Platz mehr – das Fenster ist in
#: der Standardgrösse 700 Pixel hoch.
HINWEIS_Y = 512

#: Aufschrift des Knopfes.
KNOPF = "Spiel starten"

#: Steht vor dem Eingabefeld.
BESCHRIFTUNG_ID = "Deine ID:"

#: Steht in der Hinweiszeile, solange an der ID nichts fehlt.
HINWEIS_ID = f"Deine ID bekommst du von deiner Lehrkraft – zum Beispiel {spieler_id.BEISPIEL}."


class Startbildschirm(Screen):
    titel = "Willkommen"

    def __init__(self, fenster, danach):
        super().__init__(fenster)
        self.configure(bg=stil.FARBE_NACHT)
        self._danach = danach

        self.buehne = Buehne(self, Animation(ANIMATION), bg=stil.FARBE_NACHT)
        self.buehne.pack()
        mitte = self.buehne.animation.breite // 2
        schrift = dict(text=UNTERTITEL, font=stil.SCHRIFT_ERZAEHLUNG)
        self.buehne.create_text(mitte + 2, UNTERTITEL_Y + 2, fill=stil.FARBE_SCHATTEN, **schrift)
        self._untertitel = self.buehne.create_text(mitte, UNTERTITEL_Y, fill=stil.FARBE_SAND, **schrift)
        self._hinweis_schatten = self.buehne.create_text(mitte + 1, HINWEIS_Y + 1, text=HINWEIS_ID,
                                                         fill=stil.FARBE_SCHATTEN)
        self._hinweis = self.buehne.create_text(mitte, HINWEIS_Y, text=HINWEIS_ID, fill=stil.FARBE_DUENE)

        formular = tk.Frame(self, bg=stil.FARBE_NACHT)
        formular.pack(pady=(stil.ABSTAND // 2, 0))
        tk.Label(formular, text=BESCHRIFTUNG_ID, font=stil.SCHRIFT_FETT, bg=stil.FARBE_NACHT,
                 fg=stil.FARBE_SAND).pack(side="left")
        self._feld = tk.Entry(
            formular,
            width=5,
            justify="center",
            font=stil.SCHRIFT_TITEL,
            bg=stil.FARBE_SAND,
            fg=stil.FARBE_NACHT,
            insertbackground=stil.FARBE_NACHT,
            relief="flat",
            highlightthickness=2,
            highlightbackground=stil.FARBE_KARTENRAND,
            highlightcolor=stil.FARBE_GOLD,
            validate="key",
        )
        # Tk fragt vor jeder Änderung am Feld nach: %d ist die Art (1 = Einfügen,
        # 0 = Löschen), %P der Inhalt danach.
        self._feld.config(validatecommand=(self.register(self._darf_rein), "%d", "%P"))
        self._feld.pack(side="left", padx=(stil.ABSTAND // 2, stil.ABSTAND))
        self._feld.bind("<KeyPress>", self._taste)
        self._feld.bind("<Return>", lambda _ereignis: self.starten())

        self._knopf = tk.Button(formular, text=KNOPF, command=self.starten, font=stil.SCHRIFT_FETT,
                                padx=stil.ABSTAND, highlightbackground=stil.FARBE_NACHT)
        self._knopf.pack(side="left")
        self._knopf.bind("<Return>", lambda _ereignis: self._knopf.invoke())

    @property
    def untertitel(self):
        """Der Text unter dem Schriftzug."""
        return self.buehne.itemcget(self._untertitel, "text")

    @property
    def eingabe(self):
        """Was gerade im ID-Feld steht."""
        return self._feld.get()

    @property
    def hinweis(self):
        """Die Hinweiszeile – was eine ID ist, oder das, was an der Eingabe noch fehlt."""
        return self.buehne.itemcget(self._hinweis, "text")

    @property
    def hinweis_ist_warnung(self):
        """Steht in der Hinweiszeile gerade, was an der ID noch fehlt?"""
        return self.buehne.itemcget(self._hinweis, "fill") == stil.FARBE_WARNUNG

    def _hinweis_setzen(self, text, farbe):
        self.buehne.itemconfigure(self._hinweis_schatten, text=text)
        self.buehne.itemconfigure(self._hinweis, text=text, fill=farbe)

    def beim_anzeigen(self):
        self.buehne.starten()
        self._feld.focus_set()

    def _darf_rein(self, art, danach):
        """Lässt eine Änderung am Feld zu oder weist sie ab."""
        if art == "1" and not spieler_id.ist_anfang(danach):
            return False
        # Wer tippt oder löscht, bessert gerade aus – die alte Meldung stimmt
        # dann nicht mehr.
        self._hinweis_setzen(HINWEIS_ID, stil.FARBE_DUENE)
        return True

    def _taste(self, ereignis):
        """Fehlt nach der Klasse der Strich, setzt das Feld ihn vor die Ziffer.

        Läuft vor Tks eigener Bindung, die die Ziffer danach einfügt: Aus "1"
        und "2" wird so "1-2". Ist die Klasse markiert, ersetzt die neue Ziffer
        sie – dann kein Strich. Steht die Schreibmarke vor der Klasse, weist die
        Prüfung des Feldes den Strich ohnehin ab.
        """
        feld = self._feld
        if not feld.selection_present() and spieler_id.strich_fehlt(feld.get(), ereignis.char):
            feld.insert("insert", "-")

    def starten(self):
        """Mit gültiger ID weiter zur Figurwahl – sonst steht über dem Feld, was fehlt."""
        eingabe = self.eingabe
        meldung = spieler_id.fehler(eingabe)
        if meldung:
            self._hinweis_setzen(meldung, stil.FARBE_WARNUNG)
            self._feld.focus_set()
            self._feld.icursor("end")
            return
        self._danach(self.fenster, eingabe)
