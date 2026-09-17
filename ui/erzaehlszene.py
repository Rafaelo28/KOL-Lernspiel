"""Ein Erzähltext über einer Szene (Arbeitsplan 6.3 und Phase 7).

So läuft der Story-Intro mit der Absturz-Szene – und ebenso die kurzen
Erzähltexte zwischen den Aufgaben: der Übergang zu Level 3 und die
Reflexionsfrage davor. Die Absätze kommen einzeln, "Weiter" blättert; im
Hintergrund läuft eine Szene aus ``content/animationen``.

Warum Absatz für Absatz
───────────────────────
Der ganze Intro-Text am Stück wären rund neunzig Wörter über einer bewegten
Szene. Einzeln bleibt jeder Absatz kurz genug, um ihn neben dem Bild zu lesen –
und wer schnell liest, klickt einfach weiter. Bei der Reflexionsfrage kommt
noch etwas dazu: Zuerst steht die Frage allein da, und erst der nächste Klick
zeigt die Antwort. So denkt man einen Moment selbst nach.

Wo der Text steht
─────────────────
Je Szene woanders, nämlich dort, wo sich nichts bewegt: Beim Wrack brennt es
unten links, also steht der Text oben rechts im Nachthimmel; am Nachtlager
steht der Mond oben rechts, also steht er oben links. Das hält
:data:`TEXTSTELLE_NACH_SZENE` fest.

Und die Levelzeit?
──────────────────
Der Intro kostet keine: Die Uhr von Level 1 beginnt erst mit seinem letzten
Klick (Entscheidung in Arbeitsplan 7.1). Die Zwischentexte in einem Level
laufen dagegen in dessen Zeitfenster – sie gehören zum Level, und die
Zeitfenster sind fix (Projektregel 1). Beide sind kurz.
"""

import tkinter as tk

from ui import stil
from ui.animation import Animation, Buehne
from ui.screen import Screen

#: Die Szenen, vor denen erzählt wird – content/animationen/.
SZENE_WRACK = "wrack"
SZENE_LAGER = "nachtlager"

#: Wo der Text in einer Szene steht: (x, y, Breite) in Pixeln im Maßstab 1,
#: wie alle festen Grössen der Screens (siehe ui/stil.py).
TEXTSTELLE_NACH_SZENE = {
    SZENE_WRACK: (584, 24, 356),
    SZENE_LAGER: (24, 20, 400),
}

#: Aufschrift des Knopfs, solange noch ein Absatz folgt.
KNOPF_WEITER = "Weiter"


class Erzaehlszene(Screen):
    """Erzähltext vor einer Szene. ``danach(fenster)`` ist, was der letzte Knopf tut.

    ``absaetze`` kommen nacheinander, ``titel`` steht in der Kopfzeile,
    ``letzter_knopf`` ist die Aufschrift beim letzten Absatz.
    """

    def __init__(self, fenster, absaetze, danach, titel, szene=SZENE_WRACK, letzter_knopf=KNOPF_WEITER):
        super().__init__(fenster)
        self.configure(bg=stil.FARBE_NACHT)
        self.titel = titel
        self.szene = szene
        self._danach = danach
        self._absaetze = tuple(absaetze)
        self._letzter_knopf = letzter_knopf
        self._nr = 0

        self.buehne = Buehne(self, Animation(szene, massstab=self.massstab), bg=stil.FARBE_NACHT)
        self.buehne.pack()
        x, y, breite = (self.px(wert) for wert in TEXTSTELLE_NACH_SZENE[szene])
        versatz = self.px(2)
        schrift = dict(anchor="nw", width=breite, font=stil.SCHRIFT_ERZAEHLUNG)
        self._schatten = self.buehne.create_text(x + versatz, y + versatz, fill=stil.FARBE_SCHATTEN, **schrift)
        self._text = self.buehne.create_text(x, y, fill=stil.FARBE_SAND, **schrift)

        leiste = tk.Frame(self, bg=stil.FARBE_NACHT)
        leiste.pack(fill="x", pady=(self.px(stil.ABSTAND // 2), 0))
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

    @property
    def knopftext(self):
        return self._knopf.cget("text")

    def _absatz_zeigen(self):
        absatz = self._absaetze[self._nr]
        self.buehne.itemconfigure(self._schatten, text=absatz)
        self.buehne.itemconfigure(self._text, text=absatz)
        self._zaehler.config(text=f"{self._nr + 1} / {len(self._absaetze)}")
        letzter = self._nr == len(self._absaetze) - 1
        self._knopf.config(text=self._letzter_knopf if letzter else KNOPF_WEITER)

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
