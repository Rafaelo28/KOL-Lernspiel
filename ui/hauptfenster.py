"""Das Hauptfenster und der Wechsel zwischen den Screens (Arbeitsplan 6.1).

Ein Fenster, darin wechselnde Screens
─────────────────────────────────────
Das Spiel hat genau ein Fenster. Oben steht die Kopfzeile (Titel des Screens,
Level), unten erscheint bei Bedarf eine Meldungszeile, dazwischen steht der
Screen, der gerade dran ist. :meth:`Hauptfenster.zeige` baut den neuen Screen
frisch auf und reisst den alten ab.

Keine sichtbare Restzeit
────────────────────────
Absichtlich: Ein mitzählender Countdown erzeugt Zeitdruck-Stress, gerade in
der letzten Minute, und genau das soll eine Verschlüsselungsaufgabe nicht
brauchen. Das Zeitfenster läuft trotzdem exakt wie in Projektregel 1
verlangt – es wird nur nicht vorgeführt. Läuft die Zeit ab, schaltet
:mod:`ui.ablauf` automatisch weiter und zeigt einen Hinweistext ("Die Zeit
für Level X ist abgelaufen – weiter geht es mit …"). Wer wissen will, wie
viel Zeit ein Level tatsächlich brauchte, findet es im Log
(``level_sekunden``, ``levelende``), nicht im Fenster.

Warum neu aufbauen statt verstecken
───────────────────────────────────
Die Alternative wäre, alle Screens einmal zu bauen und nur nach vorn zu holen
(``tkraise``). Dann müsste jeder Screen beim Hervorholen seinen Inhalt selbst
auffrischen – und ein vergessener Rest vom letzten Mal, eine alte Eingabe
oder eine alte Rückmeldung, stünde plötzlich bei der nächsten Aufgabe. Frisch
gebaut kann das nicht passieren. Was über einen Screen hinaus gilt, steht
ohnehin im Spielstand.

Der Takt
────────
Der Spielstand prüft sein Zeitfenster nicht selbst (siehe
:mod:`game.spielstand`). Das Hauptfenster ruft deshalb viermal pro Sekunde
:meth:`game.durchlauf.Durchlauf.takt` auf. Ohne diesen Takt liefe kein
Zeitfenster ab – Projektregel 1 hinge dann an nichts, auch ohne sichtbare Uhr.

Der nächste Takt wird im ``finally`` angemeldet. Wirft ein Takt einen Fehler,
läuft die Uhr trotzdem weiter; sonst stünde nach einem einzigen Fehler die
Zeit still, und niemand merkte es.

Was nach einem Levelwechsel kommt, entscheidet nicht das Hauptfenster, sondern
der Rückruf ``bei_levelwechsel`` – siehe :mod:`ui.ablauf`.

Fehler, die niemand sieht
─────────────────────────
Tkinter schreibt Fehler in Bedienelementen nur auf die Konsole, und die sieht
im Klassenzimmer keiner: Ein Knopf täte dann einfach nichts. Das Hauptfenster
zeigt solche Fehler deshalb zusätzlich in der Meldungszeile – ebenso, wenn
das Speichern der Messdaten scheitert.

Schliessen
──────────
Wer das Fenster während eines Levels schliesst, wird erst gefragt – ein
versehentlicher Klick aufs Kreuz soll keinen Durchlauf beenden. Beim
Schliessen wird eine offene Aufgabe als abgebrochen festgehalten und ein
letztes Mal gespeichert. Klappt das nicht, wird angeboten, es noch einmal zu
versuchen.
"""

import sys
import tkinter as tk
import traceback
from tkinter import messagebox

from content import verfahren as _verfahren
from game.durchlauf import Durchlauf
from ui import stil

FENSTER_TITEL = "Der Diamantenraub"
FENSTER_BREITE = 1000
FENSTER_HOEHE = 700
# Untergrenze: auf kleinen Schulmonitoren muss das Vigenère-Quadrat (26x26)
# noch vollständig lesbar sein – siehe Arbeitsplan 6.7.
MIN_BREITE = 800
MIN_HOEHE = 600

#: So oft wird das Zeitfenster geprüft und die Restzeit aufgefrischt. Viermal
#: pro Sekunde: Bei einem Takt pro Sekunde übersprünge die Anzeige ab und zu
#: eine Sekunde, weil ``after()`` nie ganz pünktlich ist.
TAKT_MILLISEKUNDEN = 250


def _zentriere(fenster, breite, hoehe):
    """Setzt das Fenster mittig auf den Bildschirm."""
    bildschirm_breite = fenster.winfo_screenwidth()
    bildschirm_hoehe = fenster.winfo_screenheight()
    x = max(0, (bildschirm_breite - breite) // 2)
    y = max(0, (bildschirm_hoehe - hoehe) // 3)
    fenster.geometry(f"{breite}x{hoehe}+{x}+{y}")


class Hauptfenster:
    """Das eine Fenster des Spiels.

    ``wurzel``            das ``tk.Tk()``, das ``main.py`` angelegt hat
    ``startscreen``       die Screen-Klasse, mit der es losgeht
    ``bei_levelwechsel``  ``funktion(fenster, levelwechsel)`` – zeigt, was
                          nach einem Level kommt
    ``zeitgeber``         die Uhr für Zeitfenster und Aufgaben (Tests)
    ``protokollordner``   wohin die Messdaten geschrieben werden
    """

    def __init__(
        self, wurzel, startscreen, bei_levelwechsel, zeitgeber=None, protokollordner=None
    ):
        self.wurzel = wurzel
        self.durchlauf = None
        self._bei_levelwechsel = bei_levelwechsel
        self._zeitgeber = zeitgeber
        self._protokollordner = protokollordner
        self._screen = None
        self._takt_auftrag = None
        self._geschlossen = False
        self._speichermeldung = ""
        self._fehlermeldung = ""
        #: Rückfragen an die Spielenden. In Tests ersetzbar, damit kein Dialog
        #: den Testlauf anhält.
        self.frage_ja_nein = messagebox.askyesno
        self.frage_nochmal = messagebox.askretrycancel

        wurzel.title(FENSTER_TITEL)
        wurzel.minsize(MIN_BREITE, MIN_HOEHE)
        _zentriere(wurzel, FENSTER_BREITE, FENSTER_HOEHE)
        self._titelschrift = stil.schriften_einrichten(wurzel)
        self._rahmen_bauen()
        wurzel.protocol("WM_DELETE_WINDOW", self.schliessen_anfragen)
        wurzel.report_callback_exception = self._unerwarteter_fehler

        self.zeige(startscreen)
        self._takt()

    def _rahmen_bauen(self):
        kopf = tk.Frame(self.wurzel, padx=stil.ABSTAND, pady=stil.ABSTAND // 2)
        kopf.pack(side="top", fill="x")
        self._titelanzeige = tk.Label(kopf, font=stil.SCHRIFT_TITEL, anchor="w")
        self._titelanzeige.pack(side="left")
        self._levelanzeige = tk.Label(kopf)
        self._levelanzeige.pack(side="right", padx=stil.ABSTAND)
        tk.Frame(self.wurzel, height=1, bg=stil.FARBE_LINIE).pack(side="top", fill="x")

        # Die Meldungszeile wird erst gepackt, wenn es etwas zu melden gibt.
        self._meldungszeile = tk.Label(
            self.wurzel,
            fg=stil.FARBE_MELDUNG,
            anchor="w",
            justify="left",
            wraplength=MIN_BREITE - 2 * stil.ABSTAND,
            padx=stil.ABSTAND,
            pady=stil.ABSTAND // 2,
        )

        #: Hierhin bauen die Screens ihre Bedienelemente.
        self.inhalt = tk.Frame(self.wurzel)
        self.inhalt.pack(side="top", fill="both", expand=True)

    # ── Screens ────────────────────────────────────────────────────────────

    @property
    def aktueller_screen(self):
        """Der Screen, der gerade im Fenster steht."""
        return self._screen

    def zeige(self, screen_klasse, **daten):
        """Tauscht den Screen aus. ``daten`` gehen an den Konstruktor des neuen.

        Rückgabe ist der Screen, der danach im Fenster steht. Das ist nicht
        immer der neue: Stellt er in :meth:`~ui.screen.Screen.beim_anzeigen`
        eine Aufgabe, obwohl die Zeit schon um war, hat der Levelwechsel ihn
        gleich wieder ersetzt.
        """
        alt, self._screen = self._screen, None
        if alt is not None:
            try:
                alt.abraeumen()
                alt.beim_verlassen()
            finally:
                alt.destroy()
        neu = screen_klasse(self, **daten)
        if self._screen is not None:
            # Der neue Screen hat schon beim Bauen umgeschaltet – etwa weil er
            # entgegen der Regel im Konstruktor eine Aufgabe gestellt hat und
            # die Zeit um war. Dann gilt der Screen des Levelwechsels; der
            # halb gebaute darf ihn nicht überdecken.
            neu.destroy()
            return self._screen
        neu.pack(fill="both", expand=True)
        self._screen = neu
        self._kopfzeile_aktualisieren()
        neu.beim_anzeigen()
        return self._screen

    # ── Durchlauf ──────────────────────────────────────────────────────────

    def starte_durchlauf(self, figur, pseudonym=None):
        """Beginnt den Durchlauf, sobald die Figur gewählt ist.

        Ein Fenster, ein Durchlauf: Für die nächste Person wird das Spiel neu
        gestartet. Sonst landeten zwei Personen in einer Sitzung, und ein
        Versehen beim Wechsel mischte ihre Messdaten.
        """
        if self.durchlauf is not None:
            raise ValueError(
                "In diesem Fenster läuft schon ein Durchlauf. Für die nächste "
                "Person das Spiel neu starten."
            )
        self.durchlauf = Durchlauf.neu(
            figur,
            pseudonym=pseudonym,
            zeitgeber=self._zeitgeber,
            protokollordner=self._protokollordner,
            bei_levelwechsel=self._levelwechsel,
            bei_speicherproblem=self._speicherproblem,
        )
        return self.durchlauf

    def _levelwechsel(self, wechsel):
        self._kopfzeile_aktualisieren()
        self._bei_levelwechsel(self, wechsel)

    # ── Takt und Kopfzeile ─────────────────────────────────────────────────

    def _takt(self):
        """Prüft das Zeitfenster und meldet den nächsten Takt an.

        Ein direkter Aufruf ersetzt den angemeldeten Takt, statt einen
        zweiten daneben zu starten.
        """
        if self._takt_auftrag is not None:
            self.wurzel.after_cancel(self._takt_auftrag)
            self._takt_auftrag = None
        try:
            if self.durchlauf is not None:
                self.durchlauf.takt()
            self._kopfzeile_aktualisieren()
        finally:
            if not self._geschlossen:
                self._takt_auftrag = self.wurzel.after(TAKT_MILLISEKUNDEN, self._takt)

    def _kopfzeile_aktualisieren(self):
        if self._geschlossen:
            return
        self._titelanzeige.config(text=self._screen.titel if self._screen else "")
        stand = self.durchlauf.spielstand if self.durchlauf else None
        if stand is None or stand.aktuelles_level is None:
            leveltext = ""
        else:
            bezeichnung = _verfahren.BEZEICHNUNG[stand.aktuelles_verfahren]
            leveltext = f"Level {stand.aktuelles_level} · {bezeichnung}"
        self._levelanzeige.config(text=leveltext)

    @property
    def kopfzeile(self):
        """Was in der Kopfzeile steht: (Titel, Level). Keine Restzeit – siehe Modulkopf."""
        return (
            self._titelanzeige.cget("text"),
            self._levelanzeige.cget("text"),
        )

    # ── Meldungen ──────────────────────────────────────────────────────────

    @property
    def meldung(self):
        """Was gerade in der Meldungszeile steht – leer, wenn nichts."""
        return self._meldungszeile.cget("text")

    def _speicherproblem(self, hinweis):
        self._speichermeldung = (
            f"{hinweis} Beim nächsten Speichern wird es erneut versucht." if hinweis else ""
        )
        self._meldungen_zeigen()

    def _unerwarteter_fehler(self, art, fehler, verlauf):
        """Ersetzt Tkinters ``report_callback_exception``."""
        traceback.print_exception(art, fehler, verlauf, file=sys.stderr)
        self._fehlermeldung = (
            f"Unerwarteter Fehler: {str(fehler) or art.__name__}. Bitte der "
            "Lehrkraft Bescheid geben."
        )
        self._meldungen_zeigen()

    def _meldungen_zeigen(self):
        if self._geschlossen:
            return
        text = "\n".join(t for t in (self._speichermeldung, self._fehlermeldung) if t)
        self._meldungszeile.config(text=text)
        if not text:
            self._meldungszeile.pack_forget()
        elif not self._meldungszeile.winfo_manager():
            self._meldungszeile.pack(side="bottom", fill="x", before=self.inhalt)

    # ── Schliessen ─────────────────────────────────────────────────────────

    def schliessen_anfragen(self):
        """Das Kreuz am Fensterrand. Während eines Levels wird erst gefragt."""
        stand = self.durchlauf.spielstand if self.durchlauf else None
        if stand is not None and stand.aktuelles_level is not None:
            if not self.frage_ja_nein(
                "Spiel beenden?",
                "Das Spiel läuft noch. Wenn du jetzt beendest, kannst du nicht "
                "an dieser Stelle weiterspielen.\n\nWirklich beenden?",
                parent=self.wurzel,
            ):
                return
        self.schliessen()

    def schliessen(self):
        """Speichert ein letztes Mal und schliesst das Fenster.

        Scheitert das Speichern, wird angeboten, es noch einmal zu versuchen –
        etwa nachdem die Datei in Excel geschlossen wurde.
        """
        if self._geschlossen:
            return
        if self.durchlauf is not None:
            while not self.durchlauf.beenden():
                if not self.frage_nochmal(
                    "Messdaten nicht gespeichert",
                    f"{self.durchlauf.speicherhinweis}\n\nNoch einmal versuchen? "
                    "Mit „Abbrechen“ wird das Spiel trotzdem beendet – was seit "
                    "dem letzten Speichern passiert ist, fehlt dann in den "
                    "Messdaten.",
                    parent=self.wurzel,
                ):
                    break
        self._geschlossen = True
        if self._takt_auftrag is not None:
            self.wurzel.after_cancel(self._takt_auftrag)
            self._takt_auftrag = None
        try:
            if self._screen is not None:
                self._screen.abraeumen()
                self._screen.beim_verlassen()
        finally:
            # Auch wenn ein Screen beim Abräumen stolpert: Das Fenster geht zu.
            self.wurzel.destroy()

    @property
    def ist_geschlossen(self):
        return self._geschlossen
