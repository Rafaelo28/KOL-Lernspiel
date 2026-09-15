"""Die Grundform aller Screens (Arbeitsplan 6.1).

Ein Screen ist ein Rahmen, den das Hauptfenster in seine Mitte setzt. Beim
Wechsel wird der alte abgerissen und der neue frisch gebaut – warum, steht in
:mod:`ui.hauptfenster`.

Was ein Screen wissen muss
──────────────────────────
* Im Konstruktor wird **nur gebaut**. Was eine Uhr in Gang setzt – eine
  Aufgabe stellen –, gehört nach :meth:`Screen.beim_anzeigen`. Die Uhr einer
  Aufgabe beginnt, wenn sie gestellt wird, und das soll erst geschehen, wenn
  sie auch auf dem Bildschirm steht.
* ``self.durchlauf.naechste_uebung()`` kann ``None`` liefern: Die Zeit war um,
  und das Hauptfenster hat schon zum nächsten Level umgeschaltet. Dieser
  Screen ist dann abgerissen – sofort zurückkehren und nichts mehr anfassen.
  :attr:`Screen.ist_angezeigt` sagt im Zweifel, ob er noch steht.
* Verzögerte Aufrufe über :meth:`Screen.spaeter` statt ``after()`` anmelden.
  Der Wechsel meldet sie ab. Ohne das blieben sie nach dem Abriss bei Tcl
  angemeldet und liefen ins Leere – und ein ``after()`` am Hauptfenster statt
  am Screen griffe dann auf Bedienelemente zu, die es nicht mehr gibt.
"""

import tkinter as tk

from ui.stil import ABSTAND


class Screen(tk.Frame):
    """Ein Screen im Hauptfenster.

    Unterklassen bauen ihre Bedienelemente im Konstruktor und rufen dabei
    zuerst ``super().__init__(fenster)`` auf. Was sie darüber hinaus brauchen,
    nehmen sie als eigene Schlüsselwortargumente entgegen – das Hauptfenster
    reicht sie aus ``zeige(Klasse, ...)`` weiter.
    """

    #: Steht links in der Kopfzeile. Darf je Screen im Konstruktor gesetzt
    #: werden, etwa "Handbuch – Level 2".
    titel = ""

    #: Soll der Screen den ganzen Platz im Fenster einnehmen – etwa ein
    #: Handbuch mit langem Text, das nach unten wachsen darf? Sonst steht er
    #: in seiner eigenen Grösse in der Mitte des Fensters.
    fuellt_fenster = False

    def __init__(self, fenster):
        # Oben und unten nur der halbe Abstand: Der Screen steht ohnehin in der
        # Mitte des Fensters, und auf einem 1080p-Monitor zählt im grossen
        # Maßstab jede Zeile (siehe tests/test_startbildschirm.py).
        super().__init__(fenster.inhalt, padx=fenster.px(ABSTAND), pady=fenster.px(ABSTAND // 2))
        self.fenster = fenster
        self._auftraege = set()

    def px(self, wert):
        """Eine Pixelangabe im Maßstab des Fensters (siehe :mod:`ui.stil`).

        Alle festen Grössen eines Screens – Abstände, Textbreiten, Positionen
        über einer Szene – sind für den Maßstab 1 angegeben und gehen hier
        hindurch. Auf einem 1080p-Monitor werden sie 1,5-mal so gross.
        """
        return self.fenster.px(wert)

    @property
    def massstab(self):
        """Der Maßstab des Fensters – für :class:`ui.animation.Animation`."""
        return self.fenster.massstab

    @property
    def durchlauf(self):
        """Der laufende Durchlauf, oder ``None`` vor der Figurwahl."""
        return self.fenster.durchlauf

    @property
    def ist_angezeigt(self):
        """Steht dieser Screen noch im Fenster?"""
        return self.fenster.aktueller_screen is self

    def beim_anzeigen(self):
        """Der Screen steht jetzt im Fenster – hier Aufgaben stellen."""

    def beim_verlassen(self):
        """Gleich wird der Screen abgerissen."""

    def spaeter(self, millisekunden, funktion):
        """Wie ``after()``, aber beim Wechsel automatisch abgemeldet."""

        def ausfuehren():
            self._auftraege.discard(auftrag)
            funktion()

        auftrag = self.after(millisekunden, ausfuehren)
        self._auftraege.add(auftrag)
        return auftrag

    def abraeumen(self):
        """Meldet alle noch offenen :meth:`spaeter`-Aufträge ab.

        Ruft das Hauptfenster vor dem Abriss selbst auf – eine Unterklasse,
        die :meth:`beim_verlassen` überschreibt, muss daran nicht denken.
        """
        for auftrag in list(self._auftraege):
            self.after_cancel(auftrag)
        self._auftraege.clear()
