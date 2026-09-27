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
* Jeder Eintrag im Sprungmenü setzt das Spiel an eine Stelle der Geschichte
  und lässt es von dort weiterlaufen – Funksprüche sind dort echte Aufgaben.
  Nach hinten geht es auch: Ein Spielstand kennt nur vorwärts, deshalb
  beginnt so ein Sprung einen **neuen Durchlauf** mit eigener Logdatei
  (:func:`_neuer_durchlauf`). Im Spiel gibt es das nicht.
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
from game.spielstand import LEVEL
from ui import ablauf, abschluss, erzaehlszene, funk, startbildschirm, stil, uebung
from ui.hauptfenster import Hauptfenster

#: Hier landen die Messdaten des Testmodus – ein Unterordner des Logordners,
#: damit sie beim Einsammeln der echten Daten nicht dazwischenliegen.
PROTOKOLL_UNTERORDNER = "testmodus"

#: Steht vor dem Pseudonym jedes Testlaufs.
PSEUDONYM_PRAEFIX = "TEST-"

#: Trennt das Pseudonym von der Nummer des Durchlaufs: ``TEST-9-99-lauf2``.
PSEUDONYM_LAUF = "-lauf"

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


#: Der wievielte Durchlauf dieses Testlaufs gerade läuft. Jeder Sprung nach
#: hinten beginnt einen neuen (:func:`_neuer_durchlauf`), und die Nummer hängt
#: sich ab dem zweiten ans Pseudonym: Der Dateiname des Protokolls kennt nur
#: Sekunden – zwei Durchläufe in derselben Sekunde schrieben sonst in dieselbe
#: Datei, und die Aufgaben des ersten wären weg.
_durchlaufnummer = 0


def _pseudonym(alter_durchlauf, nummer):
    """Das Pseudonym des nächsten Durchlaufs – mit der Nummer des Laufs dahinter.

    Die ID des vorigen Durchlaufs bleibt stehen: Wer sie im Startbildschirm
    eingetippt hat, findet sie auch in der zweiten Tabelle wieder, dann als
    ``TEST-1-12-lauf2``. Ohne den Zusatz ``-lauf`` wäre ``TEST-1-12-2`` nicht
    von einer ID zu unterscheiden – ein Strich steht schon zwischen Klasse und
    Nummer.
    """
    basis = PSEUDONYM_PRAEFIX + TEST_ID
    if alter_durchlauf is not None:
        basis = alter_durchlauf.spielstand.pseudonym.split(PSEUDONYM_LAUF)[0]
    return basis if nummer <= 1 else f"{basis}{PSEUDONYM_LAUF}{nummer}"


def _neuer_durchlauf(fenster, mit_level=True):
    """Beginnt einen frischen Durchlauf – das darf nur der Testmodus.

    Im Spiel gilt: ein Fenster, ein Durchlauf (sonst mischten sich zwei
    Personen in den Messdaten). Beim Springen braucht es beides, und ein
    Spielstand kennt nur vorwärts: Wer von Level 3 zurück nach Level 1 will
    oder nach dem Abschluss noch etwas ansehen, bekommt deshalb einen neuen
    Durchlauf. Seine Messdaten landen ohnehin in ``logs/testmodus/``.

    Der alte wird davor ordentlich beendet – eine laufende Aufgabe kommt als
    abgebrochen ins Log, und geschrieben ist es auch. Ein Durchlauf, in dem
    noch gar nichts passiert ist, wird stattdessen weiterbenutzt; sonst
    entstünde bei jedem Sprung an den Anfang eine Nummer mehr.

    ``mit_level=False`` lässt Level 1 noch ungestartet – für den Sprung ins
    Intro, nach dem die Uhr wie im Spiel erst mit der Handbuchseite beginnt.
    """
    global _durchlaufnummer
    alt = fenster.durchlauf
    if alt is not None and (alt.hat_begonnen or alt.spielstand.aktuelles_level is not None):
        alt.beenden()
        fenster.durchlauf = None
    if fenster.durchlauf is None:
        # Kam der erste Durchlauf über den Startbildschirm, hat ihn niemand
        # gezählt – er war der erste. Sonst bekäme der zweite dieselbe Nummer
        # und damit denselben Dateinamen (der kennt nur Sekunden).
        if alt is not None and _durchlaufnummer == 0:
            _durchlaufnummer = 1
        _durchlaufnummer += 1
        fenster.starte_durchlauf(TEST_FIGUR, pseudonym=_pseudonym(alt, _durchlaufnummer))
    durchlauf = fenster.durchlauf
    if mit_level and durchlauf.spielstand.aktuelles_level is None:
        durchlauf.starte_level()
    return durchlauf


def _stand_fuer(fenster, level, neu_noetig=None):
    """Bringt den Durchlauf dorthin, wo in ``level`` gespielt werden kann.

    Rückgabe ist ``(durchlauf, neu)`` – ``neu`` sagt, ob dafür ein frischer
    Durchlauf nötig war. Fünf Fälle führen dazu:

    * Es läuft noch keiner (der Sprung kam vom Startbildschirm).
    * Das Spiel ist vorbei – nach dem Abschluss gibt es kein Level mehr, in
      dem sich etwas stellen liesse.
    * Das Ziel liegt hinter dem laufenden Level. Zurück kann ein Spielstand
      nicht, und ein zweites Mal beginnen darf ein Level nicht (aus fünfzehn
      Minuten würden dreissig).
    * Die Zeit des laufenden Levels ist schon um. Dann liesse sich darin
      nichts mehr stellen (``_verlange_restzeit``) – der Levelwechsel steht
      nur noch nicht im Bild.
    * ``neu_noetig`` sagt es: Für einen Funkspruch etwa, der in diesem
      Durchlauf schon gestellt wurde – ein zweites Mal gibt es ihn nicht.

    Läuft gerade eine Aufgabe, wird sie **abgeschlossen**, bevor irgendwohin
    gesprungen wird – genau das tut auch ``naechstes_level()``. Bliebe sie
    offen, liesse sich die nächste nicht stellen (``_verlange_freie_bahn``),
    und der Screen bliebe leer zurück.

    Vorwärts geht es über den **Spielstand**, nicht über den Durchlauf: Sonst
    liefe bei jedem übersprungenen Level der Levelwechsel des Spiels mit
    Funksprüchen zum Mitlesen und Übergangstext ab – hier zählt das Ziel,
    nicht der Weg dorthin.
    """
    vorher = fenster.durchlauf
    durchlauf = vorher
    stand = durchlauf.spielstand if durchlauf is not None else None
    if stand is not None and stand.aktuelle_aufgabe is not None:
        durchlauf.aufgabe_abschliessen()
    if (stand is None
            or stand.aktuelles_level is None
            or stand.aktuelles_level > level
            or stand.zeit_ist_um
            or (neu_noetig is not None and neu_noetig(stand))):
        durchlauf = _neuer_durchlauf(fenster)
        stand = durchlauf.spielstand
    # Gemeldet wird nur ein wirklich neuer Durchlauf: Ein Spielstand, in dem
    # noch nichts passiert ist, wird weiterbenutzt (etwa gleich nach der
    # Figurwahl) – dann bleibt die Logdatei dieselbe, und ein Hinweis auf eine
    # neue Datei wäre falsch.
    neu = durchlauf is not vorher
    while stand.aktuelles_level < level:
        stand.naechstes_level()
    durchlauf.sichern()
    return durchlauf, neu


def _meldung(durchlauf, neu):
    """Was nach einem Sprung in der Leiste steht.

    Bei einem frischen Durchlauf der Dateiname: Von hier an stehen die
    Aufgaben in einer **anderen** Tabelle, und wer danach im alten Log sucht,
    findet nichts.
    """
    if not neu:
        return ""
    return f"Neuer Durchlauf – Messdaten jetzt in {durchlauf.protokoll.dateiname}"


def _zurueck(fenster):
    """Wohin es nach einer angesehenen Szene weitergeht: zurück in den Ablauf des Levels.

    Drei Fälle:

    * Das Level läuft samt Uhr – dann weiter wie im Spiel
      (:func:`ui.ablauf.weiter_im_level`).
    * Die Uhr des Levels wartet noch (Lesepause nach einem Levelwechsel).
      Dann führt der Weg über seine Handbuchseite, so wie im Spiel auch –
      sonst stünde plötzlich eine Übung da, deren Verfahren man nie gelesen
      hat.
    * Das Spiel ist durch – dann der Abschluss; irgendwohin muss der Knopf ja
      führen.
    """
    stand = fenster.durchlauf.spielstand if fenster.durchlauf is not None else None
    if stand is None or stand.aktuelles_level is None:
        ablauf.abschluss_zeigen(fenster)
    elif stand.zeitfenster_laeuft:
        ablauf.weiter_im_level(fenster)
    else:
        ablauf.level_beginnen(fenster, stand.aktuelles_level)


def _intro(fenster):
    """Springt an den Anfang: der Absturz, danach Level 1 wie im Spiel.

    Das ist immer ein frischer Durchlauf – vor Level 1 gibt es nichts, wohin
    man sonst zurückkönnte. Die Uhr beginnt erst mit der Handbuchseite
    (:func:`ui.ablauf.level_1_beginnen`), das Intro ist Lesezeit.
    """
    vorher = fenster.durchlauf
    durchlauf = _neuer_durchlauf(fenster, mit_level=False)
    ablauf.erzaehlszene_zeigen(fenster, story.INTRO, ablauf.TITEL_INTRO,
                               danach=ablauf.level_1_beginnen,
                               szene=erzaehlszene.SZENE_WRACK,
                               letzter_knopf=ablauf.KNOPF_HANDBUCH)
    return _meldung(durchlauf, durchlauf is not vorher)


def _szene(erzaehltext, titel, level, **optionen):
    """Baut den Sprung zu einer Erzählszene; danach geht es im Level weiter.

    ``level`` ist das Level, in dem die Szene im Spiel steht. Der Übergang zu
    Level 3 gehört schon zu Level 3: Er liegt zwischen den Leveln, und danach
    beginnt die Uhr von Level 3 mit der Handbuchseite – genau wie im Spiel
    (:func:`_zurueck`).
    """

    def springen(fenster):
        durchlauf, neu = _stand_fuer(fenster, level)
        ablauf.erzaehlszene_zeigen(fenster, erzaehltext, titel, danach=_zurueck, **optionen)
        return _meldung(durchlauf, neu)

    return springen


def _funkspruch(funkspruch):
    """Baut den Sprung zu einem Funkspruch – als **echte Aufgabe**, zum Selberrechnen.

    Gestellt wird er über den normalen Weg des Spiels
    (:func:`ui.ablauf.funkspruch_zeigen`): mit dem Erzähltext davor, wo einer
    hingehört, mit laufender Uhr, mit der 3-Versuche-Regel und mit einer Zeile
    im Log. Eingetragen ist nichts – dafür gibt es den Knopf "Lösung
    eintragen", wenn man nur weiterklicken will.

    War der Funkspruch in diesem Durchlauf schon dran, beginnt ein neuer:
    Jeder Funkspruch kommt nur einmal (sonst drei frische Versuche und zwei
    Zeilen mit derselben Kennung im Log).

    Danach läuft das Level normal weiter – die Funksprüche, die vor dem
    Sprungziel liegen, kommen also noch.
    """

    def schon_gestellt(stand):
        """Wurde dieser Funkspruch in diesem Durchlauf schon gestellt?"""
        return funkspruch not in stand.nicht_gestellte_funksprueche(funkspruch.level)

    def springen(fenster):
        durchlauf, neu = _stand_fuer(fenster, funkspruch.level, neu_noetig=schon_gestellt)
        ablauf.funkspruch_zeigen(fenster, funkspruch)
        return _meldung(durchlauf, neu)

    return springen


def _level(ziel):
    """Baut den Sprung an den Anfang eines Levels: seine Handbuchseite.

    Aufgeschlagen wird über :func:`ui.ablauf.level_beginnen`, nicht direkt
    über die Handbuchseite: Damit startet die Uhr des Levels, so wie im Spiel.
    Sonst liefe im Sprungziel kein Zeitfenster, und alles, was daran hängt –
    "Zeit ablaufen lassen", die Restzeit in der Leiste, die Vorrang-Regel –,
    wäre wirkungslos.
    """

    def springen(fenster):
        durchlauf, neu = _stand_fuer(fenster, ziel)
        ablauf.level_beginnen(fenster, ziel)
        return _meldung(durchlauf, neu)

    return springen


def _abschluss(fenster):
    """Springt ans Ende: das Nachtlager mit dem Knopf "Warten".

    Der Spielstand wird bis hinter Level 3 geschaltet. Sonst stünde in der
    Kopfzeile noch ein Level, das zu diesem Bild längst vorbei sein müsste –
    und das Bildschirmfoto zeigte etwas, das es im Spiel nie gibt.

    Steht das Ende schon, wird nur noch einmal hingeschaut: Ein zweiter
    Durchlauf bloss fürs Wiederansehen wäre eine Logdatei für nichts.
    """
    durchlauf = fenster.durchlauf
    if durchlauf is not None and durchlauf.spielstand.ist_durchgespielt:
        ablauf.abschluss_zeigen(fenster)
        return ""
    durchlauf, neu = _stand_fuer(fenster, LEVEL[-1])
    stand = durchlauf.spielstand
    while stand.aktuelles_level is not None:
        stand.naechstes_level()
    durchlauf.sichern()
    ablauf.abschluss_zeigen(fenster)
    return _meldung(durchlauf, neu)


#: Was im Menü "Springe zu" steht: je (Aufschrift, Sprung), in der Reihenfolge
#: der Geschichte. Eine Aufschrift von ``None`` ist ein Trennstrich.
#:
#: Jeder Eintrag setzt das Spiel an diese Stelle und lässt es **von dort
#: weiterlaufen**: Funksprüche sind Aufgaben zum Selberrechnen, das Level
#: läuft danach normal weiter. Nach hinten geht es auch – dann beginnt ein
#: neuer Durchlauf (:func:`_neuer_durchlauf`), der Leiste steht der neue
#: Dateiname.
SPRUNGZIELE = (
    ("Intro: der Absturz", _intro),
    (None, None),
    ("Level 1 – Caesar: Handbuch", _level(1)),
    ("Level 1: der erste Ruf", _funkspruch(story.FUNKSPRUCH_ERSTER_RUF)),
    ("Level 1: Bobs erste Antwort", _funkspruch(story.FUNKSPRUCH_BOB_ERSTE_ANTWORT)),
    (None, None),
    ("Level 2 – Substitution: Handbuch", _level(2)),
    ("Level 2: der abgefangene Funkspruch", _funkspruch(story.FUNKSPRUCH_VERFOLGER)),
    ("Übergang zu Level 3", _szene(story.UEBERGANG_ZU_LEVEL_3, ablauf.TITEL_UEBERGANG, level=3)),
    (None, None),
    ("Level 3 – Vigenère: Handbuch", _level(3)),
    ("Level 3: die Reflexionsfrage", _szene(story.REFLEXIONSFRAGE_LEVEL_3, ablauf.TITEL_REFLEXION,
                                           level=3)),
    ("Level 3: der eigene Standort", _funkspruch(story.FUNKSPRUCH_STANDORT)),
    ("Level 3: Bobs zweite Antwort", _funkspruch(story.FUNKSPRUCH_BOB_ZWEITE_ANTWORT)),
    (None, None),
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
        """Der Knopf "Springe zu" und sein Menü aus :data:`SPRUNGZIELE`.

        Ein gewöhnlicher Knopf, kein ``Menubutton``: Der postet sein Menü
        beim **Drücken** und nimmt es beim Loslassen wieder weg – man müsste
        die Maustaste gedrückt halten, um etwas auszuwählen. Hier klappt das
        Menü auf Klick auf und bleibt offen (:meth:`sprungmenue_zeigen`).
        """
        self._sprungknopf_widget = self._knopf(KNOPF_SPRUNG, self.sprungmenue_zeigen)
        self.sprungmenue = tk.Menu(self._sprungknopf_widget, tearoff=0, font=self._schrift,
                                   bg=FARBE_LEISTE, fg=FARBE_SCHRIFT, activebackground=FARBE_RAND,
                                   activeforeground=FARBE_SCHRIFT)
        for text, sprung in SPRUNGZIELE:
            if text is None:
                self.sprungmenue.add_separator()
            else:
                self.sprungmenue.add_command(label=text, command=partial(self.springen, sprung))
        return self._sprungknopf_widget

    def sprungmenue_zeigen(self):
        """Klappt das Sprungmenü unter dem Knopf auf – ein Klick genügt.

        ``tk_popup`` stellt das Menü an eine Bildschirmposition und hält es
        offen, bis etwas gewählt oder daneben geklickt ist. Der
        ``grab_release()`` danach gehört dazu: Ohne ihn behielte das Menü die
        Maus auch dann, wenn es schon wieder weg ist, und die Knöpfe der
        Leiste reagierten nicht mehr.
        """
        knopf = self._sprungknopf_widget
        try:
            self.sprungmenue.tk_popup(knopf.winfo_rootx(),
                                      knopf.winfo_rooty() + knopf.winfo_height())
        finally:
            self.sprungmenue.grab_release()

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
            # Hier gibt es nichts einzutragen: Die Nachricht steht mit Lösung
            # da, ein Eingabefeld hat sie nicht. Eintragen heisst dann
            # weiterklicken – sonst blieben nach einem Zeitablauf mehrere
            # solche Screens hintereinander liegen, und der Knopf, mit dem man
            # sich durch die Geschichte klickt, käme an ihnen nicht vorbei.
            screen.weiter()
            self.melden("Nur zum Mitlesen – weiter.")
            return
        if screen.ist_beendet:
            # Wartet der Knopf für den Rest, tut "Prüfen" nichts – dann erst
            # den Rest auflösen. Das trifft jede Teilaufgabe, die von Hand
            # entschieden wurde; ohne diesen Zweig wirkte der Knopf tot.
            if getattr(screen, "restknopf_sichtbar", False):
                screen.rest_freigeben()
                self.melden("Rest aufgelöst.")
                return
            screen.pruefen()          # der Knopf heisst jetzt "Weiter"
            self.melden("Weiter.")
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
