"""Der Testmodus: die Geschichte durchklicken, ohne 15/20/25 Minuten zu warten.

Start::

    python3 main.py --testmodus

Gedacht ist er für den Entwicklungsrechner – um Stichproben zu machen, ohne
jedes Mal ein ganzes Level zu spielen. Wie man ihn bedient, steht kurz und
ohne Code in ``dokumentation/Testmodus.md``. Im Unterricht läuft das Spiel ohne
diesen Schalter, und dann gibt es hier nichts: Kein Screen des Spiels weiss
von diesem Modul, und keine Spielregel ändert sich.

Was anders ist
──────────────
* Unten im Fenster liegt eine rote Leiste (:class:`Testleiste`) mit vier
  Knöpfen: Lösung eintragen, Level beenden, Zeit ablaufen lassen, Springe zu.
* Die Uhr des Spiels ist eine :class:`Uhr`, die sich vorstellen lässt. Das
  Spiel merkt davon nichts – ein Zeitfenster endet auf Knopfdruck genau so,
  wie es nach 15 Minuten enden würde, mitsamt allem, was daran hängt.
* Die Messdaten landen in ``logs/testmodus/``, nicht bei den echten, und das
  Pseudonym bekommt ``TEST-`` davor. Eine Testdatei ist damit auch dann noch
  als solche zu erkennen, wenn sie einmal im falschen Ordner liegt.
* In der Titelzeile des Fensters steht "TESTMODUS".

Was **nicht** anders ist: die Zeitfenster (15/20/25 Minuten laufen normal,
sie lassen sich nur überspringen), die 3-Versuche-Regel, die Aufgaben, die
Reihenfolge der Screens. Wer im Testmodus etwas sieht, sieht es im Spiel
genauso – sonst wären die Stichproben wertlos.

Die Leiste braucht Platz
────────────────────────
Sie liegt unter dem Spiel und nimmt etwa 30 Pixel Höhe (im grossen Maßstab
45). Auf einem knappen 1080p-Bildschirm kann dem höchsten Screen dadurch
unten etwas fehlen. Zum Prüfen der Bildaufteilung deshalb die Leiste mit "✕"
ausblenden – mit F9 kommt sie zurück.
"""

import time
import tkinter as tk
from functools import partial
from pathlib import Path
from tkinter import font as tkfont

from content import charaktere, story
from ui import ablauf, abschluss, erzaehlszene, funk, startbildschirm, stil, uebung
from ui.hauptfenster import Hauptfenster

#: Hier landen die Messdaten des Testmodus – ein Unterordner des Logordners,
#: damit sie beim Einsammeln der echten Daten nicht dazwischenliegen.
PROTOKOLL_UNTERORDNER = "testmodus"

#: Steht vor dem Pseudonym jedes Testlaufs.
PSEUDONYM_PRAEFIX = "TEST-"

#: Womit ein Sprung anfängt, wenn noch kein Durchlauf läuft. Die ID hat die
#: Form der echten (:mod:`game.spieler_id`), gehört aber keiner Klasse.
TEST_ID = "9-99"
TEST_FIGUR = charaktere.VIC_MORENO

#: Steht in der Titelzeile des Fensters.
FENSTER_TITEL = "Der Diamantenraub – TESTMODUS"

# Die Leiste ist bewusst nicht im Nachthimmel des Spiels gehalten: Man soll
# auf einem Bildschirmfoto sofort sehen, dass das nicht das echte Spiel ist.
FARBE_LEISTE = "#3a1218"
FARBE_RAND = "#8a2d1b"
FARBE_SCHRIFT = "#ffd9c4"
FARBE_MARKE = "#ff6b4a"
FARBE_KNOPF = "#5a1c22"

#: Schriftgrösse der Leiste in Punkt (im Maßstab 1) – kleiner als im Spiel,
#: damit sie wenig Höhe braucht.
SCHRIFTGROESSE = 10

#: So oft frischt die Leiste Level und Restzeit auf.
TAKT_MS = 500

#: Damit kommt die ausgeblendete Leiste zurück.
TASTE_EINBLENDEN = "<F9>"

#: Aufschriften der Knöpfe.
KNOPF_LOESUNG = "Lösung eintragen"
KNOPF_LEVELENDE = "Level beenden"
KNOPF_ZEITABLAUF = "Zeit ablaufen lassen"
KNOPF_SPRUNG = "Springe zu ▾"
KNOPF_AUSBLENDEN = "✕"


class Uhr:
    """Die Systemuhr plus einen Versatz, den die Leiste vorstellen kann.

    Das Spiel bekommt sie als ``zeitgeber`` – genau an der Stelle, an der in
    den Tests eine gestellte Uhr steht. Es merkt davon nichts: Springt die
    Uhr über das Ende eines Zeitfensters, endet das Level auf dem normalen
    Weg, mit allem, was daran hängt (verpasste Funksprüche zum Mitlesen, der
    Hinweis über der nächsten Handbuchseite, "zeitablauf" im Log).

    >>> uhr = Uhr(lambda: 100.0)
    >>> uhr(), uhr.versatz
    (100.0, 0.0)
    >>> uhr.vorstellen(60)
    >>> uhr()
    160.0
    """

    def __init__(self, zeitgeber=time.monotonic):
        """Beginnt ohne Versatz – die Uhr geht zunächst wie die Systemuhr."""
        self._zeitgeber = zeitgeber
        self.versatz = 0.0

    def __call__(self):
        """Das Spiel fragt die Uhr wie eine Funktion: ``zeitgeber()``."""
        return self._zeitgeber() + self.versatz

    def vorstellen(self, sekunden):
        """Stellt die Uhr um so viele Sekunden vor. Zurück geht sie nie."""
        self.versatz += max(0.0, sekunden)


# ── Sprünge in die Geschichte ──────────────────────────────────────────────


def _durchlauf_sicherstellen(fenster):
    """Sorgt dafür, dass ein Durchlauf mit laufendem Level da ist – und die Bahn frei ist.

    Im Spiel entsteht der Durchlauf aus ID und Figurwahl. Für eine Stichprobe
    wäre das jedes Mal derselbe Weg über zwei Screens – deshalb übernimmt der
    Testmodus das hier mit fester Figur und fester ID.

    Läuft gerade eine Aufgabe, wird sie **abgeschlossen**, bevor irgendwohin
    gesprungen wird – genau das tut auch ``naechstes_level()``. Bliebe sie
    offen, stünde sie beim Zurückkommen noch im Spielstand: Die nächste
    Aufgabe liesse sich nicht stellen (``_verlange_freie_bahn``), und der
    Screen bliebe leer zurück. Im Log steht sie danach als abgebrochen –
    Testläufe schreiben ohnehin in ihren eigenen Ordner.
    """
    if fenster.durchlauf is None:
        fenster.starte_durchlauf(TEST_FIGUR, pseudonym=PSEUDONYM_PRAEFIX + TEST_ID)
    durchlauf = fenster.durchlauf
    stand = durchlauf.spielstand
    if stand.aktuelle_aufgabe is not None:
        durchlauf.aufgabe_abschliessen()
    if stand.aktuelles_level is None and not stand.ist_durchgespielt:
        durchlauf.starte_level()
    return durchlauf


def _zurueck(fenster):
    """Wohin es nach einer angesehenen Szene weitergeht: zurück in den Ablauf des Levels.

    Ist das Spiel schon durch, führt der Weg zum Abschluss – irgendwohin muss
    der Knopf ja führen.
    """
    stand = fenster.durchlauf.spielstand if fenster.durchlauf is not None else None
    if stand is not None and stand.aktuelles_level is not None:
        ablauf.weiter_im_level(fenster)
    else:
        ablauf.abschluss_zeigen(fenster)


def _szene(erzaehltext, titel, **optionen):
    """Baut den Sprung zu einer Erzählszene – am Level und an der Uhr ändert sie nichts.

    Eine Aufgabe, die gerade läuft, wird davor abgeschlossen
    (:func:`_durchlauf_sicherstellen`).
    """

    def springen(fenster):
        _durchlauf_sicherstellen(fenster)
        ablauf.erzaehlszene_zeigen(fenster, erzaehltext, titel, danach=_zurueck, **optionen)

    return springen


def _funkspruch(funkspruch):
    """Baut den Sprung zu einem Funkspruch – zum Mitlesen, mit Lösung und ohne Uhr.

    Das ist derselbe Screen, den das Spiel zeigt, wenn die Zeit für einen
    Funkspruch nicht mehr gereicht hat (``nur_lesen``). Er verlangt nichts
    und schreibt nichts ins Log – zum Nachsehen, wie die Nachricht aussieht,
    ist er genau richtig.
    """

    def springen(fenster):
        _durchlauf_sicherstellen(fenster)
        ablauf.funkspruch_nachlesen(fenster, funkspruch, danach=_zurueck)

    return springen


def _level(ziel):
    """Baut den Sprung an den Anfang eines Levels."""

    def springen(fenster):
        return _bis_level(fenster, ziel)

    return springen


def _bis_level(fenster, ziel):
    """Schaltet den Spielstand bis zu diesem Level weiter und schlägt sein Handbuch auf.

    Anders als der Knopf "Level beenden" läuft dabei nichts von der
    Geschichte ab: Hier zählt das Ziel, nicht der Weg dorthin. Zurück geht es
    nicht – ein Spielstand kennt nur vorwärts; dafür das Spiel neu starten.

    Aufgeschlagen wird über :func:`ui.ablauf.level_beginnen`, nicht direkt
    über die Handbuchseite: Damit startet die Uhr des Levels, so wie im Spiel.
    Sonst liefe im Sprungziel kein Zeitfenster, und alles, was daran hängt –
    "Zeit ablaufen lassen", die Restzeit in der Leiste, die Vorrang-Regel –,
    wäre im Testmodus wirkungslos.
    """
    durchlauf = _durchlauf_sicherstellen(fenster)
    stand = durchlauf.spielstand
    if stand.ist_durchgespielt:
        return "Das Spiel ist vorbei – für einen neuen Durchlauf das Spiel neu starten."
    if stand.aktuelles_level is not None and stand.aktuelles_level > ziel:
        return f"Zurück zu Level {ziel} geht nicht – dafür das Spiel neu starten."
    while stand.aktuelles_level is not None and stand.aktuelles_level < ziel:
        stand.naechstes_level()
    durchlauf.sichern()
    ablauf.level_beginnen(fenster, stand.aktuelles_level)
    return ""


def _abschluss(fenster):
    """Springt ans Ende: das Nachtlager mit dem Knopf "Warten".

    Der Spielstand wird dabei bis hinter Level 3 geschaltet. Sonst stünde in
    der Kopfzeile noch ein Level, das zu diesem Bild längst vorbei sein
    müsste – und das Bildschirmfoto zeigte etwas, das es im Spiel nie gibt.
    """
    durchlauf = _durchlauf_sicherstellen(fenster)
    stand = durchlauf.spielstand
    while stand.aktuelles_level is not None:
        stand.naechstes_level()
    durchlauf.sichern()
    ablauf.abschluss_zeigen(fenster)


#: Was im Menü "Springe zu" steht: je (Aufschrift, Sprung). Ein Sprung von
#: ``None`` ist eine Zwischenüberschrift, eine Aufschrift von ``None`` ein
#: Trennstrich.
SPRUNGZIELE = (
    ("Geschichte ansehen (Level und Uhr bleiben)", None),
    ("Intro: der Absturz", _szene(story.INTRO, ablauf.TITEL_INTRO,
                                  szene=erzaehlszene.SZENE_WRACK,
                                  letzter_knopf=ablauf.KNOPF_HANDBUCH)),
    ("Level 1: der erste Ruf", _funkspruch(story.FUNKSPRUCH_ERSTER_RUF)),
    ("Level 1: Bobs erste Antwort", _funkspruch(story.FUNKSPRUCH_BOB_ERSTE_ANTWORT)),
    ("Level 2: der abgefangene Funkspruch", _funkspruch(story.FUNKSPRUCH_VERFOLGER)),
    ("Übergang zu Level 3", _szene(story.UEBERGANG_ZU_LEVEL_3, ablauf.TITEL_UEBERGANG)),
    ("Level 3: die Reflexionsfrage", _szene(story.REFLEXIONSFRAGE_LEVEL_3, ablauf.TITEL_REFLEXION)),
    ("Level 3: der eigene Standort", _funkspruch(story.FUNKSPRUCH_STANDORT)),
    ("Level 3: Bobs zweite Antwort", _funkspruch(story.FUNKSPRUCH_BOB_ZWEITE_ANTWORT)),
    (None, None),
    ("Ins Level springen (schaltet weiter)", None),
    ("Level 1 – Caesar", _level(1)),
    ("Level 2 – Substitution", _level(2)),
    ("Level 3 – Vigenère", _level(3)),
    ("Abschluss: Nachtlager und Rettung", _abschluss),
)


# ── Die Leiste ─────────────────────────────────────────────────────────────


class Testleiste(tk.Frame):
    """Die rote Leiste unter dem Spiel.

    Sie greift auf den Screen zu, der gerade im Fenster steht – so, wie es
    die Tests des Projekts auch tun. Deshalb steht sie hier und nicht in den
    Screens: Vom Testmodus soll im Spiel nichts zu finden sein.
    """

    def __init__(self, fenster, uhr):
        """Baut die Leiste für dieses Fenster; gezeigt wird sie erst mit :meth:`einblenden`."""
        super().__init__(fenster.wurzel, bg=FARBE_LEISTE,
                         padx=fenster.px(stil.ABSTAND // 2), pady=fenster.px(3),
                         highlightthickness=fenster.px(1), highlightbackground=FARBE_RAND)
        self.fenster = fenster
        self.uhr = uhr
        # Die Schrift muss festgehalten werden: Tkinter löscht eine Schrift,
        # sobald niemand mehr auf sie zeigt.
        self._schrift = tkfont.Font(
            root=fenster.wurzel,
            family=tkfont.nametofont("TkDefaultFont", root=fenster.wurzel).actual("family"),
            size=stil.skaliert(SCHRIFTGROESSE, fenster.massstab),
        )

        tk.Label(self, text="● TESTMODUS", font=self._schrift, bg=FARBE_LEISTE,
                 fg=FARBE_MARKE).pack(side="left", padx=(0, fenster.px(stil.ABSTAND // 2)))
        self._knopf(KNOPF_LOESUNG, self.loesung_eintragen)
        self._knopf(KNOPF_LEVELENDE, self.level_beenden)
        self._knopf(KNOPF_ZEITABLAUF, self.zeit_ablaufen_lassen)
        self._sprungknopf()

        self._knopf(KNOPF_AUSBLENDEN, self.ausblenden, seite="right")
        self._standanzeige = tk.Label(self, font=self._schrift, bg=FARBE_LEISTE, fg=FARBE_SCHRIFT)
        self._standanzeige.pack(side="right", padx=fenster.px(stil.ABSTAND // 2))
        self._hinweis = tk.Label(self, font=self._schrift, bg=FARBE_LEISTE, fg=FARBE_SCHRIFT,
                                 anchor="w")
        self._hinweis.pack(side="left", fill="x", expand=True, padx=fenster.px(stil.ABSTAND // 2))

        fenster.wurzel.bind(TASTE_EINBLENDEN, lambda _ereignis: self.einblenden())
        self._takt()

    # ── Aufbau ─────────────────────────────────────────────────────────────

    def _knopf(self, text, befehl, seite="left"):
        """Ein Knopf im Stil der Leiste."""
        knopf = tk.Button(self, text=text, command=befehl, font=self._schrift,
                          bg=FARBE_KNOPF, fg=FARBE_SCHRIFT, activebackground=FARBE_RAND,
                          activeforeground=FARBE_SCHRIFT, highlightbackground=FARBE_LEISTE,
                          relief="flat", padx=self.fenster.px(6), pady=0)
        knopf.pack(side=seite, padx=self.fenster.px(2))
        return knopf

    def _sprungknopf(self):
        """Der Knopf "Springe zu" und sein Menü aus :data:`SPRUNGZIELE`."""
        knopf = tk.Menubutton(self, text=KNOPF_SPRUNG, font=self._schrift, bg=FARBE_KNOPF,
                              fg=FARBE_SCHRIFT, activebackground=FARBE_RAND,
                              activeforeground=FARBE_SCHRIFT, highlightbackground=FARBE_LEISTE,
                              relief="flat", padx=self.fenster.px(6), pady=0)
        self.sprungmenue = tk.Menu(knopf, tearoff=0, font=self._schrift, bg=FARBE_LEISTE,
                                   fg=FARBE_SCHRIFT, activebackground=FARBE_RAND,
                                   activeforeground=FARBE_SCHRIFT)
        for text, sprung in SPRUNGZIELE:
            if text is None:
                self.sprungmenue.add_separator()
            elif sprung is None:
                self.sprungmenue.add_command(label=text, state="disabled")
            else:
                self.sprungmenue.add_command(label=text, command=partial(self.springen, sprung))
        knopf.configure(menu=self.sprungmenue)
        knopf.pack(side="left", padx=self.fenster.px(2))
        return knopf

    # ── Was die Knöpfe tun ─────────────────────────────────────────────────

    def loesung_eintragen(self):
        """Trägt die richtige Antwort in die laufende Aufgabe ein und prüft sie.

        Damit lässt sich die Geschichte durchklicken, ohne jeden Funkspruch
        von Hand zu rechnen. Wartet danach der Knopf für den Rest einer
        langen Nachricht, wird auch der gedrückt. Ist die Aufgabe schon
        entschieden, geht es mit demselben Knopf weiter.
        """
        screen = self.fenster.aktueller_screen
        if not isinstance(screen, (uebung.Uebung, funk.Funk)):
            self.melden("Hier gibt es keine Aufgabe.")
            return
        if isinstance(screen, funk.Funk) and screen.nur_lesen:
            self.melden("Dieser Funkspruch steht nur zum Mitlesen da.")
            return
        if screen.ist_beendet:
            screen.pruefen()          # der Knopf heisst jetzt "Weiter"
            return
        if isinstance(screen, funk.Funk):
            # Sonst tippt sich die Nachricht noch Zeichen für Zeichen ein.
            screen.anzeige_vervollstaendigen()
        if screen.aufgabe is None:
            self.melden("Es läuft gerade keine Aufgabe.")
            return
        # Wie die Tests des Projekts: ins Eingabefeld schreiben und prüfen.
        screen._feld.delete(0, "end")
        screen._feld.insert(0, screen.aufgabe.loesung)
        screen.pruefen()
        if getattr(screen, "restknopf_sichtbar", False):
            screen.rest_freigeben()
        self.melden("Lösung eingetragen.")

    def level_beenden(self):
        """Beendet das Level, als wären alle Aufgaben erledigt.

        Das ist der normale Weg: Was danach kommt, entscheidet
        :func:`ui.ablauf.nach_levelwechsel` – bei Level 3 also der Abschluss.
        Im Log steht "vorzeitig".
        """
        durchlauf = self.fenster.durchlauf
        if durchlauf is None or durchlauf.spielstand.aktuelles_level is None:
            self.melden("Es läuft kein Level.")
            return
        level = durchlauf.spielstand.aktuelles_level
        durchlauf.naechstes_level()
        self.melden(f"Level {level} beendet.")

    def zeit_ablaufen_lassen(self):
        """Stellt die Uhr vor, bis das Zeitfenster um ist – oder springt zur Rettung.

        Im Level heisst das: Das Level endet wie am Timer, mit "zeitablauf"
        im Log und den verpassten Funksprüchen zum Mitlesen. Steht der
        Abschluss da, wird stattdessen die Nacht übersprungen, bis der
        Hubschrauber gelandet ist.
        """
        screen = self.fenster.aktueller_screen
        if isinstance(screen, abschluss.Abschluss):
            if screen.phase == "abend":
                screen.warten()
            self.uhr.vorstellen(abschluss.GELANDET / 1000)
            self.melden("Nacht übersprungen.")
            return
        durchlauf = self.fenster.durchlauf
        if durchlauf is None or durchlauf.spielstand.aktuelles_level is None:
            self.melden("Es läuft kein Level.")
            return
        if not durchlauf.spielstand.zeitfenster_laeuft:
            # Zwischen zwei Leveln wird gelesen; die Uhr des neuen Levels
            # beginnt erst mit seiner Handbuchseite. Vorstellen brächte hier
            # nichts – die Meldung sagt das, statt Erfolg zu behaupten.
            self.melden("Hier läuft noch keine Uhr – erst die Handbuchseite öffnen.")
            return
        level = durchlauf.spielstand.aktuelles_level
        self.uhr.vorstellen(durchlauf.spielstand.verbleibende_sekunden + 1)
        durchlauf.takt()
        self.melden(f"Zeit von Level {level} abgelaufen.")

    def springen(self, sprung):
        """Führt einen Eintrag aus dem Menü "Springe zu" aus."""
        self.melden(sprung(self.fenster) or "")

    # ── Anzeige ────────────────────────────────────────────────────────────

    def melden(self, text):
        """Schreibt eine Zeile in die Leiste – was zuletzt passiert ist."""
        self._hinweis.configure(text=text)

    def einblenden(self):
        """Hängt die Leiste unten ans Fenster (oder holt sie zurück)."""
        if not self.winfo_manager():
            self.pack(side="bottom", fill="x")

    def ausblenden(self):
        """Nimmt die Leiste weg – für ein Bildschirmfoto oder um die Höhe zu prüfen.

        Mit F9 kommt sie zurück.
        """
        self.pack_forget()

    def standtext(self):
        """Was rechts in der Leiste steht: Level und Restzeit."""
        durchlauf = self.fenster.durchlauf
        if durchlauf is None:
            return "kein Durchlauf"
        stand = durchlauf.spielstand
        if stand.aktuelles_level is None:
            return "Spiel vorbei" if stand.ist_durchgespielt else "kein Level"
        return f"Level {stand.aktuelles_level} · Rest {stand.restzeit_text}"

    def _takt(self):
        """Frischt Level und Restzeit auf und meldet sich gleich wieder an."""
        if self.fenster.ist_geschlossen or not self.winfo_exists():
            return
        self._standanzeige.configure(text=self.standtext())
        self.after(TAKT_MS, self._takt)


# ── Start ──────────────────────────────────────────────────────────────────


def _figurwahl_zeigen(fenster, spieler_id):
    """Wie im Spiel weiter zur Figurwahl – nur mit ``TEST-`` vor der ID."""
    ablauf.figurwahl_zeigen(fenster, PSEUDONYM_PRAEFIX + spieler_id)


def protokollordner(ordner):
    """Der Unterordner, in den der Testmodus schreibt – ``None`` bleibt ``None``.

    >>> protokollordner("/pfad/logs").name
    'testmodus'
    >>> protokollordner(None) is None
    True
    """
    return None if ordner is None else Path(ordner) / PROTOKOLL_UNTERORDNER


def oeffnen(wurzel, protokollordner_des_spiels=None, massstab=None):
    """Öffnet das Spiel im Testmodus und hängt die Leiste darunter.

    Rückgabe ist die :class:`Testleiste`; über ``leiste.fenster`` kommt man
    ans Hauptfenster.
    """
    uhr = Uhr()
    fenster = Hauptfenster(
        wurzel,
        partial(startbildschirm.Startbildschirm, danach=_figurwahl_zeigen),
        ablauf.nach_levelwechsel,
        zeitgeber=uhr,
        protokollordner=protokollordner(protokollordner_des_spiels),
        massstab=massstab,
    )
    wurzel.title(FENSTER_TITEL)
    leiste = Testleiste(fenster, uhr)
    leiste.einblenden()
    return leiste
