"""Vorgerenderte Animationen abspielen (Arbeitsplan 6.3).

Tkinter kann keine SVG-Animation abspielen. Deshalb rechnet
``grafik/rendern.py`` jede Animation vorher in Bilder um (siehe
dokumentation/Animationen.md), und hier werden sie nur noch durchgeblättert:

    content/animationen/<name>/hintergrund.png   die Szene als Standbild
    content/animationen/<name>/bereich_1.png     Bildfolge des bewegten Ausschnitts,
                                                 als ein Blatt mit allen Bildern
    content/animationen/<name>/animation.json    Größen, Positionen, Takt

Eine :class:`Buehne` legt den Hintergrund auf eine Leinwand und darüber für
jeden Ausschnitt ein Bild, das im Takt ausgetauscht wird. Das kostet fast
nichts: Ein Wechsel dauert unter einer Millisekunde, weil Tkinter nur ein
fertiges Bild an eine Stelle kopiert.

Das Blatt zerschneidet Tkinter beim Laden selbst (``photo copy -from``) – ohne
Zusatzpaket, wie es die Projektregeln für die Schulrechner verlangen.

Benutzung in einem Screen::

    self.buehne = Buehne(self, Animation("wrack"))
    self.buehne.pack()
    ...
    def beim_anzeigen(self):
        self.buehne.starten()

Die Bühne hält beim Abriss selbst an – ein Screen muss daran nicht denken.
"""

import json
import tkinter as tk
from pathlib import Path
from typing import NamedTuple

import content

#: Hier liegen die fertig gerenderten Animationen.
ANIMATIONSORDNER = Path(content.__file__).resolve().parent / "animationen"


class Ausschnitt(NamedTuple):
    """Ein bewegter Ausschnitt: wo er liegt und woher seine Bilder kommen."""

    datei: str
    x: int
    y: int
    breite: int
    hoehe: int
    spalten: int


class Animation:
    """Die Beschreibung einer gerenderten Animation – ohne die Bilder selbst.

    Die Bilder lädt erst die :class:`Buehne`: Tkinter braucht dafür ein
    geöffnetes Fenster.
    """

    def __init__(self, name, ordner=None):
        self.name = name
        self.ordner = Path(ordner if ordner is not None else ANIMATIONSORDNER) / name
        beschreibung = self.ordner / "animation.json"
        if not beschreibung.exists():
            raise FileNotFoundError(
                f"Die Animation '{name}' ist nicht gerendert ({beschreibung} fehlt). "
                f"Erzeugen mit: python3 grafik/rendern.py grafik/{name}.svg"
            )
        daten = json.loads(beschreibung.read_text(encoding="utf-8"))
        try:
            self.breite = int(daten["breite"])
            self.hoehe = int(daten["hoehe"])
            self.bilder = int(daten["bilder"])
            self.takt_ms = int(daten["takt_ms"])
            self.hintergrund = str(daten["hintergrund"])
            self.ausschnitte = tuple(
                Ausschnitt(str(a["datei"]), int(a["x"]), int(a["y"]), int(a["breite"]),
                           int(a["hoehe"]), int(a["spalten"]))
                for a in daten["bereiche"]
            )
        except (KeyError, TypeError, ValueError) as fehler:
            raise ValueError(f"{beschreibung} ist unvollständig oder beschädigt: {fehler!r}") from None
        if self.bilder < 1 or self.takt_ms < 1:
            raise ValueError(f"{beschreibung}: 'bilder' und 'takt_ms' müssen grösser als null sein.")

    @property
    def dauer_ms(self):
        """Wie lange eine Schleife dauert."""
        return self.bilder * self.takt_ms

    def __repr__(self):
        return f"Animation({self.name!r}, {self.breite}×{self.hoehe}, {self.bilder} Bilder)"


def _zerschneiden(master, blatt, ausschnitt, anzahl):
    """Schneidet ein Bildblatt in Einzelbilder – der Reihe nach, Zeile für Zeile."""
    bilder = []
    for nr in range(anzahl):
        x = (nr % ausschnitt.spalten) * ausschnitt.breite
        y = (nr // ausschnitt.spalten) * ausschnitt.hoehe
        bild = tk.PhotoImage(master=master, width=ausschnitt.breite, height=ausschnitt.hoehe)
        bild.tk.call(bild, "copy", blatt, "-from", x, y, x + ausschnitt.breite, y + ausschnitt.hoehe,
                     "-to", 0, 0)
        bilder.append(bild)
    return bilder


class Buehne(tk.Canvas):
    """Eine Leinwand, auf der eine :class:`Animation` läuft."""

    def __init__(self, master, animation, **optionen):
        # Zuerst, damit destroy() auch nach einem Ladefehler funktioniert.
        self.animation = animation
        self._auftrag = None
        self._bild_nr = 0
        self._folgen = []
        self._elemente = []
        optionen.setdefault("highlightthickness", 0)
        optionen.setdefault("borderwidth", 0)
        super().__init__(master, width=animation.breite, height=animation.hoehe, **optionen)
        try:
            self._laden()
        except BaseException:
            # Keine halb gebaute Leinwand im Fenster zurücklassen.
            self.destroy()
            raise

    def _laden(self):
        animation = self.animation
        self._hintergrund = tk.PhotoImage(master=self, file=str(animation.ordner / animation.hintergrund))
        self.create_image(0, 0, image=self._hintergrund, anchor="nw")
        for ausschnitt in animation.ausschnitte:
            blatt = tk.PhotoImage(master=self, file=str(animation.ordner / ausschnitt.datei))
            erwartet = (ausschnitt.spalten * ausschnitt.breite,
                        -(-animation.bilder // ausschnitt.spalten) * ausschnitt.hoehe)
            if (blatt.width(), blatt.height()) != erwartet:
                raise ValueError(
                    f"{ausschnitt.datei} ist {blatt.width()}×{blatt.height()} Pixel gross, "
                    f"erwartet sind {erwartet[0]}×{erwartet[1]} – neu rendern mit grafik/rendern.py."
                )
            folge = _zerschneiden(self, blatt, ausschnitt, animation.bilder)
            self._folgen.append(folge)
            self._elemente.append(self.create_image(ausschnitt.x, ausschnitt.y, image=folge[0], anchor="nw"))

    @property
    def bild_nr(self):
        """Welches Bild der Schleife gerade zu sehen ist."""
        return self._bild_nr

    @property
    def laeuft(self):
        return self._auftrag is not None

    def starten(self):
        """Spielt die Animation in Schleife ab. Ein zweiter Aufruf ändert nichts."""
        if self._auftrag is None:
            self._auftrag = self.after(self.animation.takt_ms, self._weiter)

    def anhalten(self):
        """Hält die Animation beim aktuellen Bild an."""
        if self._auftrag is not None:
            self.after_cancel(self._auftrag)
            self._auftrag = None

    def zeige_bild(self, nr):
        """Zeigt ein bestimmtes Bild der Schleife."""
        self._bild_nr = nr % self.animation.bilder
        for element, folge in zip(self._elemente, self._folgen):
            self.itemconfigure(element, image=folge[self._bild_nr])

    def _weiter(self):
        self.zeige_bild(self._bild_nr + 1)
        self._auftrag = self.after(self.animation.takt_ms, self._weiter)

    def destroy(self):
        # Beim Abriss des Screens mit abräumen – sonst liefe ein after() ins Leere.
        self.anhalten()
        super().destroy()
