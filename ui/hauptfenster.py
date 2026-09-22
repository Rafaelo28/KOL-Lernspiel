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

Grösse und Vollbild
───────────────────
Das Fenster öffnet maximiert – auf den Schulrechnern soll das Spiel den
Bildschirm füllen, nicht als kleines Fenster darauf liegen. Auf einem
1080p-Monitor wird dabei alles 1,5-mal so gross gezeichnet (siehe
:mod:`ui.stil`, "Der Maßstab"), und die Screens stehen in der Mitte des
Fensters statt oben am Rand. F11 schaltet auf echtes Vollbild ohne
Titelleiste, Esc wieder zurück.

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
#: Grösse des Fensters, wenn es nicht maximiert ist – im Maßstab 1. Im
#: grossen Maßstab wächst sie mit, höchstens bis auf die Bildschirmgrösse.
FENSTER_BREITE = 1000
FENSTER_HOEHE = 700
# Untergrenze: auf kleinen Schulmonitoren muss das Vigenère-Quadrat (26x26)
# noch vollständig lesbar sein – siehe Arbeitsplan 6.7.
MIN_BREITE = 800
MIN_HOEHE = 600
#: So viel vom Bildschirm bleibt für Titelleiste und Taskleiste frei, wenn das
#: Fenster nicht maximiert ist.
RAND_BILDSCHIRM = (40, 100)

#: So oft wird das Zeitfenster geprüft. Viermal pro Sekunde: Der Levelwechsel
#: kommt dann höchstens eine Viertelsekunde nach Ablauf – bei einem Takt pro
#: Sekunde bis zu einer ganzen, weil ``after()`` nie ganz pünktlich ist.
TAKT_MILLISEKUNDEN = 250


def _zentriere(fenster, breite, hoehe):
    """Setzt das Fenster mittig auf den Bildschirm – nie grösser als dieser."""
    bildschirm_breite = fenster.winfo_screenwidth()
    bildschirm_hoehe = fenster.winfo_screenheight()
    breite = min(breite, bildschirm_breite - RAND_BILDSCHIRM[0])
    hoehe = min(hoehe, bildschirm_hoehe - RAND_BILDSCHIRM[1])
    x = max(0, (bildschirm_breite - breite) // 2)
    y = max(0, (bildschirm_hoehe - hoehe) // 3)
    fenster.geometry(f"{breite}x{hoehe}+{x}+{y}")


def _maximieren(fenster):
    """Maximiert das Fenster. Windows und macOS kennen dafür einen Zustand, X11 ein Attribut."""
    try:
        fenster.state("zoomed")
    except tk.TclError:
        fenster.attributes("-zoomed", True)


class Hauptfenster:
    """Das eine Fenster des Spiels.

    ``wurzel``            das ``tk.Tk()``, das ``main.py`` angelegt hat
    ``startscreen``       die Screen-Klasse, mit der es losgeht – oder etwas,
                          das sie baut: ``startscreen(fenster)``, etwa ein
                          ``functools.partial`` mit weiteren Angaben
    ``bei_levelwechsel``  ``funktion(fenster, levelwechsel)`` – zeigt, was
                          nach einem Level kommt
    ``zeitgeber``         die Uhr für Zeitfenster und Aufgaben (Tests)
    ``protokollordner``   wohin die Messdaten geschrieben werden
    ``massstab``          wie gross alles gezeichnet wird; ohne Angabe nach
                          der Bildschirmgrösse (:func:`ui.stil.massstab_fuer`)
    """

    def __init__(
        self, wurzel, startscreen, bei_levelwechsel, zeitgeber=None, protokollordner=None, massstab=None
    ):
        """Richtet das Fenster ein und zeigt den ersten Screen.

        Was die einzelnen Angaben bedeuten, steht oben bei der Klasse. Hier
        entsteht der Rahmen (Kopfzeile, Meldungszeile, Inhaltsbereich), der
        Takt für die Zeitfenster wird angeworfen und der Startscreen gebaut.
        """
        self.wurzel = wurzel
        #: Der Maßstab des Fensters – siehe :mod:`ui.stil`. Er gilt für die
        #: ganze Sitzung; die Bilder dazu werden je Screen geladen.
        self.massstab = (
            massstab
            if massstab is not None
            else stil.massstab_fuer(wurzel.winfo_screenwidth(), wurzel.winfo_screenheight())
        )
        self.durchlauf = None
        self._bei_levelwechsel = bei_levelwechsel
        self._zeitgeber = zeitgeber
        self._protokollordner = protokollordner
        self._screen = None
        self._takt_auftrag = None
        self._geschlossen = False
        self._speichermeldung = ""
        self._fehlermeldung = ""
        #: Was Screens über ihren eigenen Abriss hinaus behalten wollen – etwa
        #: die Bilder des Umblätterns im Handbuch, die zu laden eine spürbare
        #: Weile dauert und die bei jedem Nachschlagen wieder gebraucht werden.
        self.zwischenspeicher = {}
        #: Rückfragen an die Spielenden. In Tests ersetzbar, damit kein Dialog
        #: den Testlauf anhält.
        self.frage_ja_nein = messagebox.askyesno
        self.frage_nochmal = messagebox.askretrycancel

        wurzel.title(FENSTER_TITEL)
        wurzel.minsize(
            min(self.px(MIN_BREITE), wurzel.winfo_screenwidth() - RAND_BILDSCHIRM[0]),
            min(self.px(MIN_HOEHE), wurzel.winfo_screenheight() - RAND_BILDSCHIRM[1]),
        )
        _zentriere(wurzel, self.px(FENSTER_BREITE), self.px(FENSTER_HOEHE))
        _maximieren(wurzel)
        self._schriften = stil.schriften_einrichten(wurzel, self.massstab)
        self._rahmen_bauen()
        wurzel.protocol("WM_DELETE_WINDOW", self.schliessen_anfragen)
        wurzel.report_callback_exception = self._unerwarteter_fehler
        wurzel.bind("<F11>", lambda _ereignis: self.vollbild_umschalten())
        wurzel.bind("<Escape>", lambda _ereignis: self.vollbild_beenden())

        self.zeige(startscreen)
        self._takt()

    def px(self, wert):
        """Eine Pixelangabe aus dem Maßstab 1 in den Maßstab dieses Fensters."""
        return stil.skaliert(wert, self.massstab)

    def _rahmen_bauen(self):
        """Baut, was in jedem Screen gleich bleibt: Kopfzeile, Trennlinie, Meldungszeile, Inhaltsbereich.

        Die Screens selbst kommen später in den Inhaltsbereich und werden
        dort ausgetauscht; dieser Rahmen bleibt stehen.
        """
        # Alles im Nachthimmel des Spiels: Eine helle Leiste in Grau oder Weiss
        # sähe über dem Buch und den Szenen aus wie ein Formular.
        self.wurzel.configure(bg=stil.FARBE_NACHT)
        kopf = tk.Frame(self.wurzel, padx=self.px(stil.ABSTAND), pady=self.px(stil.ABSTAND // 2),
                        bg=stil.FARBE_NACHT)
        kopf.pack(side="top", fill="x")
        self._titelanzeige = tk.Label(kopf, font=stil.SCHRIFT_TITEL, anchor="w", bg=stil.FARBE_NACHT,
                                      fg=stil.FARBE_SAND)
        self._titelanzeige.pack(side="left")
        self._levelanzeige = tk.Label(kopf, bg=stil.FARBE_NACHT, fg=stil.FARBE_DUENE)
        self._levelanzeige.pack(side="right", padx=self.px(stil.ABSTAND))
        tk.Frame(self.wurzel, height=1, bg=stil.FARBE_LINIE).pack(side="top", fill="x")

        # Die Meldungszeile wird erst gepackt, wenn es etwas zu melden gibt.
        self._meldungszeile = tk.Label(
            self.wurzel,
            fg=stil.FARBE_MELDUNG,
            bg=stil.FARBE_NACHT,
            anchor="w",
            justify="left",
            wraplength=self.px(MIN_BREITE - 2 * stil.ABSTAND),
            padx=self.px(stil.ABSTAND),
            pady=self.px(stil.ABSTAND // 2),
        )

        #: Hierhin bauen die Screens ihre Bedienelemente.
        self.inhalt = tk.Frame(self.wurzel, bg=stil.FARBE_NACHT)
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
        if neu.fuellt_fenster:
            neu.pack(fill="both", expand=True)
        else:
            # In der Mitte des Fensters – auf einem grossen Bildschirm stünde
            # der Screen sonst oben am Rand. Der Rand drumherum bekommt seine
            # Farbe, damit der Nachthimmel nicht an einem grauen Rand endet.
            neu.pack(expand=True)
        self.inhalt.configure(bg=neu.cget("bg"))
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
        """Meldung des Durchlaufs, dass ein Level zu Ende ist – Kopfzeile nachziehen, Ablauf fragen."""
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
        """Schreibt Titel des Screens und "Level 2 · Substitution" in die Kopfzeile."""
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
        """Meldung des Durchlaufs, dass das Speichern hakt – oder wieder klappt (dann leerer Hinweis)."""
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
        """Zeigt Speicher- und Fehlermeldung unten im Fenster – und blendet die Zeile aus, wenn nichts ansteht."""
        if self._geschlossen:
            return
        text = "\n".join(t for t in (self._speichermeldung, self._fehlermeldung) if t)
        self._meldungszeile.config(text=text)
        if not text:
            self._meldungszeile.pack_forget()
        elif not self._meldungszeile.winfo_manager():
            self._meldungszeile.pack(side="bottom", fill="x", before=self.inhalt)

    # ── Vollbild ───────────────────────────────────────────────────────────

    @property
    def vollbild(self):
        """Läuft das Spiel gerade im echten Vollbild (ohne Titelleiste)?"""
        return bool(int(self.wurzel.attributes("-fullscreen")))

    def vollbild_umschalten(self):
        """F11: echtes Vollbild an oder aus."""
        self.wurzel.attributes("-fullscreen", not self.vollbild)

    def vollbild_beenden(self):
        """Esc: zurück ins Fenster – im Vollbild fehlt sonst das Kreuz zum Schliessen."""
        if self.vollbild:
            self.wurzel.attributes("-fullscreen", False)

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
        """Wurde das Fenster schon geschlossen? Danach wird nichts mehr gezeichnet."""
        return self._geschlossen
