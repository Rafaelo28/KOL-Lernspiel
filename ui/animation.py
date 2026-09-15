"""Vorgerenderte Animationen abspielen (Arbeitsplan 6.3).

Tkinter kann keine SVG-Animation abspielen. Deshalb rechnet
``grafik/rendern.py`` jede Animation vorher in Bilder um (siehe
dokumentation/Animationen.md), und hier werden sie nur noch durchgeblättert:

    content/animationen/<name>/hintergrund.png   die Szene als Standbild
    content/animationen/<name>/bereich_1.png     Bildfolge des bewegten Ausschnitts,
                                                 als ein Blatt mit allen Bildern
    content/animationen/<name>/animation.json    Größen, Positionen, Takt
    content/animationen/<name>/1.5x/…            derselbe Satz 1,5-mal so groß

Welcher Satz geladen wird, entscheidet der Maßstab des Fensters (siehe
:func:`ui.stil.massstab_fuer`): Auf einem 1080p-Schulmonitor ist es der
grosse, sonst der kleine.

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

Standbilder und einmalige Abläufe
─────────────────────────────────
Ein Standbild (``data-standbild`` in der SVG) ist eine :class:`Buehne` ohne
bewegte Ausschnitte – etwa das aufgeschlagene Buch im Handbuch. Ein
einmaliger, durchsichtiger Ablauf (``data-einmalig``, ``data-durchsichtig``)
hat keinen eigenen Hintergrund: :class:`Ablauf` legt seine Bilder über eine
Leinwand, die schon dasteht, spielt sie einmal ab und räumt sie wieder weg –
so blättert die Seite um, während darunter der Text der Buchseiten liegt.
"""

import json
import tkinter as tk
from pathlib import Path
from typing import NamedTuple

import content

#: Hier liegen die fertig gerenderten Animationen.
ANIMATIONSORDNER = Path(content.__file__).resolve().parent / "animationen"


def unterordner(massstab):
    """Wo der Bildsatz eines Maßstabs liegt – wie in grafik/rendern.py.

    Maßstab 1 direkt im Ordner der Animation, die anderen etwa in "1.5x".
    """
    return "" if massstab == 1 else f"{massstab:g}x"


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

    def __init__(self, name, ordner=None, massstab=1):
        self.name = name
        self.massstab = massstab
        self.ordner = Path(ordner if ordner is not None else ANIMATIONSORDNER) / name / unterordner(massstab)
        beschreibung = self.ordner / "animation.json"
        if not beschreibung.exists():
            groesse = "" if massstab == 1 else f" im Maßstab {massstab:g}"
            raise FileNotFoundError(
                f"Die Animation '{name}' ist{groesse} nicht gerendert ({beschreibung} fehlt). "
                f"Erzeugen mit: python3 grafik/rendern.py grafik/{name}.svg"
            )
        daten = json.loads(beschreibung.read_text(encoding="utf-8"))
        try:
            self.breite = int(daten["breite"])
            self.hoehe = int(daten["hoehe"])
            self.bilder = int(daten["bilder"])
            self.takt_ms = int(daten["takt_ms"])
            # Ein durchsichtiger einmaliger Ablauf hat keinen eigenen Hintergrund.
            self.hintergrund = None if daten["hintergrund"] is None else str(daten["hintergrund"])
            self.standbild = bool(daten.get("standbild", False))
            self.durchsichtig = bool(daten.get("durchsichtig", False))
            self.einmalig = bool(daten.get("einmalig", False))
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


def _folge_laden(master, animation, ausschnitt):
    """Lädt das Bildblatt eines Ausschnitts und schneidet es in seine Einzelbilder."""
    blatt = tk.PhotoImage(master=master, file=str(animation.ordner / ausschnitt.datei))
    erwartet = (ausschnitt.spalten * ausschnitt.breite,
                -(-animation.bilder // ausschnitt.spalten) * ausschnitt.hoehe)
    if (blatt.width(), blatt.height()) != erwartet:
        raise ValueError(
            f"{ausschnitt.datei} ist {blatt.width()}×{blatt.height()} Pixel gross, "
            f"erwartet sind {erwartet[0]}×{erwartet[1]} – neu rendern mit grafik/rendern.py."
        )
    return _zerschneiden(master, blatt, ausschnitt, animation.bilder)


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
        self._hintergrund = None
        if animation.hintergrund is not None:
            self._hintergrund = tk.PhotoImage(master=self, file=str(animation.ordner / animation.hintergrund))
            self.create_image(0, 0, image=self._hintergrund, anchor="nw")
        for ausschnitt in animation.ausschnitte:
            folge = _folge_laden(self, animation, ausschnitt)
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
        """Spielt die Animation in Schleife ab. Ein zweiter Aufruf ändert nichts.

        Bei einem Standbild gibt es nichts abzuspielen – dann auch keinen Takt.
        """
        if self._auftrag is None and self._folgen:
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
        # Die Bilder gleich freigeben, nicht erst, wenn Python aufräumt: Im
        # grossen Maßstab belegt eine Szene um die 50 MB.
        self._folgen = []
        self._hintergrund = None


class Ablauf:
    """Spielt eine einmalige Animation einmal über einer vorhandenen Leinwand ab.

    Gedacht für durchsichtige Abläufe ohne Hintergrund (``data-einmalig`` und
    ``data-durchsichtig``): Die Bilder liegen über allem, was auf der Leinwand
    steht, und verschwinden am Ende wieder. ``x`` und ``y`` sind die Stelle
    der linken oberen Ecke der Animation auf der Leinwand.

    Die Bilder werden beim Bauen geladen. Wer das nicht beim Öffnen eines
    Screens bezahlen will, baut den Ablauf etwas später (siehe das Handbuch).
    """

    TAG = "ablauf"

    def __init__(self, leinwand, animation, x=0, y=0):
        self.leinwand = leinwand
        self.animation = animation
        self._x, self._y = x, y
        self._auftrag = None
        self._elemente = []
        self._folgen = [(ausschnitt, _folge_laden(leinwand, animation, ausschnitt))
                        for ausschnitt in animation.ausschnitte]

    @property
    def laeuft(self):
        return self._auftrag is not None or bool(self._elemente)

    def abspielen(self, rueckwaerts=False, bei_bild=None, danach=None):
        """Zeigt die Bilder nacheinander im Takt, rückwärts auf Wunsch.

        ``bei_bild(i, anzahl)`` kommt nach jedem Bild – etwa um in der Mitte
        des Umblätterns den Text darunter auszutauschen. ``danach()`` kommt,
        wenn das letzte Bild wieder weg ist. Läuft schon ein Ablauf, geschieht
        nichts: Zweimal übereinander sähe wirr aus.
        """
        if self.laeuft:
            return False
        reihenfolge = list(range(self.animation.bilder))
        if rueckwaerts:
            reihenfolge.reverse()
        for ausschnitt, folge in self._folgen:
            self._elemente.append(self.leinwand.create_image(
                self._x + ausschnitt.x, self._y + ausschnitt.y, image=folge[reihenfolge[0]], anchor="nw",
                tags=(self.TAG,)))
        self._schritt(reihenfolge, 0, bei_bild, danach)
        return True

    def _schritt(self, reihenfolge, i, bei_bild, danach):
        self._auftrag = None
        if i >= len(reihenfolge):
            self.abbrechen()
            if danach is not None:
                danach()
            return
        for element, (_, folge) in zip(self._elemente, self._folgen):
            self.leinwand.itemconfigure(element, image=folge[reihenfolge[i]])
        self.leinwand.tag_raise(self.TAG)
        if bei_bild is not None:
            bei_bild(i, len(reihenfolge))
        self._auftrag = self.leinwand.after(
            self.animation.takt_ms, lambda: self._schritt(reihenfolge, i + 1, bei_bild, danach))

    def abbrechen(self):
        """Hält an und räumt die Bilder von der Leinwand."""
        if self._auftrag is not None:
            self.leinwand.after_cancel(self._auftrag)
            self._auftrag = None
        for element in self._elemente:
            self.leinwand.delete(element)
        self._elemente = []
