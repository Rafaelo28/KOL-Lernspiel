"""Der Startbildschirm (Arbeitsplan 6.2).

Das Titelbild läuft als Animation (siehe :mod:`ui.animation`): ein großer
Diamant im Nachthimmel über der Wüste, Lichtreflexe wandern über seine
Facetten, danach glänzt der Schriftzug auf. Darunter steht nur ein Knopf,
"Spiel starten". Die Geschichte beginnt erst auf dem nächsten Screen, der
Figurwahl – hier soll nichts zu lesen sein, bevor jemand bereit ist.

Der Schriftzug steckt im Bild (``grafik/titel.svg``), der Untertitel nicht:
Er wird im Spiel über die Dünen gelegt und lässt sich hier ändern, ohne neu
zu rendern.

Was nach dem Knopf kommt, gibt der Aufrufer als ``danach`` mit (siehe
:mod:`ui.ablauf`) – wie beim Story-Intro weiss der Screen nichts vom Ablauf.
"""

import tkinter as tk

from ui import stil
from ui.animation import Animation, Buehne
from ui.screen import Screen

#: Die Animation – content/animationen/titel.
ANIMATION = "titel"

#: Steht unter dem Schriftzug, über den Dünen.
UNTERTITEL = "Ein Lernspiel über Verschlüsselung"

#: Höhe des Untertitels in der Szene (Pixel von oben) – unter dem Schriftzug,
#: der bei 444 endet.
UNTERTITEL_Y = 486

#: Aufschrift des Knopfes.
KNOPF = "Spiel starten"


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

        leiste = tk.Frame(self, bg=stil.FARBE_NACHT)
        leiste.pack(fill="x", pady=(stil.ABSTAND // 2, 0))
        self._knopf = tk.Button(leiste, text=KNOPF, command=self.starten, font=stil.SCHRIFT_FETT,
                                padx=stil.ABSTAND, highlightbackground=stil.FARBE_NACHT)
        self._knopf.pack()
        self._knopf.bind("<Return>", lambda _ereignis: self._knopf.invoke())

    @property
    def untertitel(self):
        """Der Text unter dem Schriftzug."""
        return self.buehne.itemcget(self._untertitel, "text")

    def beim_anzeigen(self):
        self.buehne.starten()
        self._knopf.focus_set()

    def starten(self):
        """Weiter zur Figurwahl – oder was der Aufrufer als ``danach`` vorsieht."""
        self._danach(self.fenster)
