"""Der Story-Intro: die Absturz-Szene (Arbeitsplan 6.3).

Die Wüstenszene läuft als Animation (siehe :mod:`ui.animation`), und die drei
Absätze des Intro-Textes aus ``content/story.py`` erscheinen nacheinander im
Nachthimmel oben rechts – dort bewegt sich nichts, und der Text liegt nicht
über dem Feuer. "Weiter" blättert zum nächsten Absatz; am Ende steht
"Handbuch aufschlagen", und erst damit geht es weiter.

Warum Absatz für Absatz
───────────────────────
Der ganze Text am Stück wären rund neunzig Wörter über einer bewegten Szene.
Einzeln bleibt jeder Absatz kurz genug, um ihn neben dem Bild zu lesen – und
wer schnell liest, klickt einfach weiter.

Der Intro kostet keine Levelzeit: Die Uhr von Level 1 beginnt erst mit dem
letzten Klick (Entscheidung in Arbeitsplan 7.1). Was danach kommt, gibt der
Aufrufer als ``danach`` mit – der Screen weiss nichts vom Ablauf.
"""

import tkinter as tk

from content import story
from ui import stil
from ui.animation import Animation, Buehne
from ui.screen import Screen

#: Die Animation hinter dem Text – content/animationen/wrack.
ANIMATION = "wrack"

#: Wo der Erzähltext steht: im Nachthimmel oben rechts der Szene.
TEXT_X, TEXT_Y, TEXT_BREITE = 584, 24, 356

#: Aufschrift auf dem letzten Knopf – danach liegt das Handbuch vor einem.
LETZTER_KNOPF = "Handbuch aufschlagen"


class Intro(Screen):
    titel = "Der Absturz"

    def __init__(self, fenster, danach, absaetze=story.INTRO.absaetze):
        super().__init__(fenster)
        self.configure(bg=stil.FARBE_NACHT)
        self._danach = danach
        self._absaetze = tuple(absaetze)
        self._nr = 0

        self.buehne = Buehne(self, Animation(ANIMATION), bg=stil.FARBE_NACHT)
        self.buehne.pack()
        schrift = dict(anchor="nw", width=TEXT_BREITE, font=stil.SCHRIFT_ERZAEHLUNG)
        self._schatten = self.buehne.create_text(TEXT_X + 2, TEXT_Y + 2, fill=stil.FARBE_SCHATTEN, **schrift)
        self._text = self.buehne.create_text(TEXT_X, TEXT_Y, fill=stil.FARBE_SAND, **schrift)

        leiste = tk.Frame(self, bg=stil.FARBE_NACHT)
        leiste.pack(fill="x", pady=(stil.ABSTAND // 2, 0))
        self._zaehler = tk.Label(leiste, bg=stil.FARBE_NACHT, fg=stil.FARBE_DUENE)
        self._zaehler.pack(side="left")
        self._knopf = tk.Button(leiste, command=self.weiter, highlightbackground=stil.FARBE_NACHT)
        self._knopf.pack(side="right")
        self._knopf.bind("<Return>", lambda _ereignis: self._knopf.invoke())
        self._absatz_zeigen()

    @property
    def absatz_nr(self):
        """Der Absatz, der gerade zu lesen ist – ab null gezählt."""
        return self._nr

    @property
    def text(self):
        """Der Erzähltext, der gerade über der Szene steht."""
        return self.buehne.itemcget(self._text, "text")

    def _absatz_zeigen(self):
        absatz = self._absaetze[self._nr]
        self.buehne.itemconfigure(self._schatten, text=absatz)
        self.buehne.itemconfigure(self._text, text=absatz)
        self._zaehler.config(text=f"{self._nr + 1} / {len(self._absaetze)}")
        letzter = self._nr == len(self._absaetze) - 1
        self._knopf.config(text=LETZTER_KNOPF if letzter else "Weiter")

    def beim_anzeigen(self):
        self.buehne.starten()
        self._knopf.focus_set()

    def weiter(self):
        """Nächster Absatz – oder nach dem letzten weiter im Spiel."""
        if self._nr < len(self._absaetze) - 1:
            self._nr += 1
            self._absatz_zeigen()
        else:
            self._danach(self.fenster)
