"""Tests für das Fenstergerüst (Arbeitsplan 6.1): ui/hauptfenster.py,
ui/screen.py, ui/ablauf.py, die Platzhalter und main.py.

Diese Tests brauchen eine Bildschirmanzeige. Ohne eine (etwa auf einem Server)
werden sie übersprungen statt rot – die Logik dahinter prüft
``tests/test_durchlauf.py`` auch ohne Bildschirm.

Die Fenster werden versteckt (``withdraw``), damit beim Testlauf nichts über
den Bildschirm flackert. Dialoge sind durch Attrappen ersetzt – ein echter
Dialog hielte den Testlauf an, bis jemand klickt.
"""

import csv
import sys
import time
from pathlib import Path

import pytest

# Ohne Tkinter wird die ganze Datei übersprungen – deshalb stehen die
# übrigen Importe erst hier unten.
tk = pytest.importorskip("tkinter")
from tkinter import font as tkfont  # noqa: E402

import main  # noqa: E402
from content import charaktere  # noqa: E402
from game.protokoll import KODIERUNG, TRENNZEICHEN  # noqa: E402
from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN  # noqa: E402
from ui import abschluss, ablauf, funk, handbuch, hauptfenster, stil, uebung  # noqa: E402
from ui.hauptfenster import Hauptfenster  # noqa: E402
from ui.screen import Screen  # noqa: E402


class Uhr:
    """Eine Uhr zum Stellen: Sie gibt zurück, was in ``jetzt`` steht, und lässt sich vorspulen."""

    def __init__(self):
        """Beginnt bei null Sekunden."""
        self.jetzt = 0.0

    def __call__(self):
        """Das Spiel fragt die Uhr wie eine Funktion: ``zeitgeber()``."""
        return self.jetzt

    def weiter(self, sekunden):
        """Spult um so viele Sekunden vor."""
        self.jetzt += sekunden


class Rueckfrage:
    """Ersetzt einen Dialog und gibt vorbereitete Antworten der Reihe nach zurück.

    Ohne vorbereitete Antwort schlägt der Test fehl: Eine Rückfrage, mit der
    niemand gerechnet hat, ist selbst ein Befund.
    """

    def __init__(self, *antworten, vorher=None):
        """Nimmt die Antworten entgegen, die der Reihe nach gegeben werden sollen."""
        self.antworten = list(antworten)
        self.fragen = []
        self.vorher = vorher

    def __call__(self, titel, text, **_):
        """Der Dialog wird gestellt: Frage mitschreiben und die nächste Antwort zurückgeben."""
        self.fragen.append((titel, text))
        if self.vorher is not None:
            self.vorher()
        if not self.antworten:
            raise AssertionError(f"Unerwartete Rückfrage: {titel!r}")
        return self.antworten.pop(0)


class Speicher:
    """Ersetzt Protokoll.schreiben: scheitert, solange ``gesperrt`` ist."""

    def __init__(self, protokoll):
        """Merkt sich das echte Schreiben und beginnt gesperrt."""
        self._echt = protokoll.schreiben
        self.gesperrt = True

    def __call__(self):
        """Scheitert wie eine schreibgeschützte Datei – oder schreibt doch, wenn die Sperre weg ist."""
        if self.gesperrt:
            raise PermissionError(13, "Zugriff verweigert")
        return self._echt()


@pytest.fixture
def wurzel():
    """Ein verstecktes Tk-Fenster für die Tests – und am Ende wieder weg.

    Gibt es keine Bildschirmanzeige, werden die Tests übersprungen statt rot.
    """
    try:
        wurzel = tk.Tk()
    except tk.TclError as fehler:
        pytest.skip(f"Keine Bildschirmanzeige: {fehler}")
    wurzel.withdraw()
    yield wurzel
    try:
        wurzel.destroy()
    except tk.TclError:
        pass  # schon vom Test geschlossen


@pytest.fixture
def uhr():
    """Die stellbare Uhr – ohne sie liefe im Test die echte Zeit mit."""
    return Uhr()


@pytest.fixture
def fenster(wurzel, uhr, tmp_path, massstab):
    """Ein Hauptfenster an der stellbaren Uhr; seine Rückfragen beantworten Attrappen."""
    fenster = ablauf.oeffnen(wurzel, zeitgeber=uhr, protokollordner=tmp_path, massstab=massstab)
    fenster.frage_ja_nein = Rueckfrage()
    fenster.frage_nochmal = Rueckfrage()
    return fenster


def _knopf(widget, anfang):
    """Sucht im Screen den Knopf, dessen Aufschrift so beginnt."""
    for kind in widget.winfo_children():
        if isinstance(kind, tk.Button) and kind.cget("text").startswith(anfang):
            return kind
        try:
            return _knopf(kind, anfang)
        except LookupError:
            pass
    raise LookupError(f"Kein Knopf '{anfang}…' in {widget}")


def _klick(fenster, anfang):
    """Drückt den Knopf, dessen Aufschrift so beginnt – wie ein Klick mit der Maus."""
    _knopf(fenster.aktueller_screen, anfang).invoke()


def _bis_zum_handbuch(fenster):
    """Klickt sich vom Startbildschirm bis zur Handbuchseite von Level 1 durch."""
    fenster.aktueller_screen._feld.insert(0, "1-12")          # die ID von der Lehrkraft
    _klick(fenster, "Spiel starten")
    fenster.aktueller_screen.waehle(charaktere.VIC_MORENO)   # was ein Klick auf die Karte tut
    _klick(fenster, "Als Vic Moreno")          # Figur bestätigen, der Durchlauf beginnt
    _klick(fenster, "Weiter")                 # Intro, Absatz 1 → 2
    _klick(fenster, "Weiter")                 # Absatz 2 → 3
    _klick(fenster, "Handbuch aufschlagen")   # Level 1 beginnt


def _bis_zur_uebung(fenster):
    """Klickt weiter bis zur ersten Übung von Level 1."""
    _bis_zum_handbuch(fenster)
    _klick(fenster, "Zu den Übungen")


def _loesen(fenster):
    """Löst die laufende Aufgabe mit ihrer Musterlösung und schliesst sie ab.

    Geht für Übungen wie für Funksprüche: Beim Funkgerät wird die Anzeige
    vorher fertig getippt und danach der Rest der Nachricht freigegeben.
    """
    screen = fenster.aktueller_screen
    if hasattr(screen, "anzeige_vervollstaendigen"):
        screen.anzeige_vervollstaendigen()
    screen._feld.delete(0, "end")
    screen._feld.insert(0, fenster.durchlauf.spielstand.aktuelle_aufgabe.loesung)
    screen.pruefen()
    if getattr(screen, "restknopf_sichtbar", False):
        screen.rest_freigeben()
    screen.weiter()


def _nachlese_durchklicken(fenster):
    """Klickt die Funksprüche weg, die nach einem Zeitablauf zum Mitlesen dastehen.

    Seit Phase 7 bekommt man sie beim Levelwechsel mit Lösung zu sehen, damit
    die Geschichte nicht an der Uhr scheitert (ui/ablauf.py).
    """
    while isinstance(fenster.aktueller_screen, funk.Funk) and fenster.aktueller_screen.nur_lesen:
        fenster.aktueller_screen.weiter()
    return fenster.aktueller_screen


def _alle_level_ablaufen_lassen(fenster, uhr):
    """Lässt die Zeitfenster aller Level ablaufen – der schnellste Weg zum Abschluss.

    Zwischen zwei Leveln steht, was die Uhr abgeschnitten hat: die
    Funksprüche zum Mitlesen, der Erzähltext, der zu einem von ihnen
    hinführt, und der Übergang zu Level 3. Sie kommen gemischt, deshalb wird
    geklickt, bis nichts davon mehr dasteht.
    """
    for level in sorted(DAUER_JE_LEVEL_SEKUNDEN):
        uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[level])
        fenster._takt()
        while True:
            screen = fenster.aktueller_screen
            zum_lesen = (isinstance(screen, ablauf.erzaehlszene.Erzaehlszene)
                         or (isinstance(screen, funk.Funk) and screen.nur_lesen))
            if not zum_lesen:
                break
            screen.weiter()


def _zeilen(fenster):
    """Die geschriebene CSV-Datei, Zeile für Zeile als Wörterbuch."""
    with open(fenster.durchlauf.protokoll.pfad, newline="", encoding=KODIERUNG) as datei:
        return list(csv.DictReader(datei, delimiter=TRENNZEICHEN))


class Probe(Screen):
    """Ein Screen, der mitschreibt, was mit ihm geschieht."""

    titel = "Probe"

    def __init__(self, fenster, name="probe", ereignisse=None):
        """Baut den Probe-Screen und schreibt gleich mit, dass er gebaut wurde."""
        super().__init__(fenster)
        self.name = name
        self.ereignisse = ereignisse if ereignisse is not None else []
        self.ereignisse.append(("gebaut", name))

    def beim_anzeigen(self):
        """Schreibt mit, dass der Screen jetzt zu sehen ist."""
        self.ereignisse.append(("angezeigt", self.name))

    def beim_verlassen(self):
        """Schreibt mit, dass der Screen gleich abgerissen wird."""
        self.ereignisse.append(("verlassen", self.name))


def _probefenster(wurzel, ereignisse, uhr=None, tmp_path=None):
    """Ein Hauptfenster, das statt des Spiels nur Probe-Screens zeigt und alles mitschreibt."""
    return Hauptfenster(
        wurzel,
        lambda fenster: Probe(fenster, "start", ereignisse),
        lambda fenster, wechsel: ereignisse.append(("levelwechsel", wechsel)),
        zeitgeber=uhr,
        protokollordner=tmp_path,
        massstab=1,
    )


# ───────────────────────────────────────────────────────────────────────────
# 1. Das Fenster
# ───────────────────────────────────────────────────────────────────────────

def test_das_fenster_traegt_titel_und_mindestgroesse(fenster, wurzel):
    assert wurzel.title() == hauptfenster.FENSTER_TITEL
    assert wurzel.minsize() == (hauptfenster.MIN_BREITE, hauptfenster.MIN_HOEHE)


def test_es_beginnt_mit_dem_startscreen(fenster):
    assert isinstance(fenster.aktueller_screen, ablauf.STARTSCREEN)
    assert fenster.kopfzeile == ("Willkommen", "")
    assert fenster.durchlauf is None


def test_die_schriften_sind_eingerichtet(fenster, wurzel):
    """Die Screens nennen die Überschrift beim Namen – es muss sie also geben."""
    assert stil.SCHRIFT_TITEL in tkfont.names(wurzel)
    titel = tkfont.nametofont(stil.SCHRIFT_TITEL, root=wurzel)
    assert titel.cget("size") == stil.TITELGROESSE
    assert tkfont.nametofont("TkDefaultFont", root=wurzel).cget("size") == stil.SCHRIFTGROESSE
    erzaehlung = tkfont.nametofont(stil.SCHRIFT_ERZAEHLUNG, root=wurzel)
    assert erzaehlung.cget("size") == stil.ERZAEHLGROESSE
    fett = tkfont.nametofont(stil.SCHRIFT_FETT, root=wurzel)
    assert (fett.cget("size"), fett.cget("weight")) == (stil.SCHRIFTGROESSE, "bold")
    abschnitt = tkfont.nametofont(stil.SCHRIFT_ABSCHNITT, root=wurzel)
    assert (abschnitt.cget("size"), abschnitt.cget("weight")) == (stil.ABSCHNITTGROESSE, "bold")
    betont = tkfont.nametofont(stil.SCHRIFT_BETONT, root=wurzel)
    assert (betont.cget("size"), betont.cget("weight")) == (stil.ERZAEHLGROESSE, "bold")
    kursiv = tkfont.nametofont(stil.SCHRIFT_KURSIV, root=wurzel)
    assert (kursiv.cget("size"), kursiv.cget("slant")) == (stil.SCHRIFTGROESSE, "italic")


# ── Grösse, Maßstab und Vollbild ───────────────────────────────────────────

class Fensterzustand:
    """Ersetzt state() und attributes() eines versteckten Fensters.

    Unter X11 bleiben Maximieren und Vollbild bei einem versteckten Fenster
    wirkungslos – Tk meldet danach weiter 0. Die Attrappe merkt sich, was
    das Hauptfenster verlangt hat.
    """

    def __init__(self, kennt_zoomed_zustand):
        """Beginnt im Zustand "normal", ohne gesetzte Attribute."""
        self.kennt_zoomed_zustand = kennt_zoomed_zustand
        self.werte = {}
        self.zustand = "normal"

    def state(self, neu=None):
        """Fragt den Fensterzustand ab oder setzt ihn – "zoomed" kennt nicht jedes System."""
        if neu is None:
            return self.zustand
        if neu == "zoomed" and not self.kennt_zoomed_zustand:
            raise tk.TclError('bad argument "zoomed": must be normal, iconic, or withdrawn')
        self.zustand = neu

    def attributes(self, name, *wert):
        """Fragt ein Fensterattribut ab oder setzt es, wie Tk es täte."""
        if not wert:
            return self.werte.get(name, 0)
        self.werte[name] = int(bool(wert[0]))


def _bildschirm(monkeypatch, wurzel, breite, hoehe):
    """Tut so, als hätte der Bildschirm diese Größe – ohne einen solchen zu brauchen."""
    monkeypatch.setattr(wurzel, "winfo_screenwidth", lambda: breite)
    monkeypatch.setattr(wurzel, "winfo_screenheight", lambda: hoehe)


@pytest.mark.parametrize("breite, hoehe, erwartet", [(1920, 1080, 1.5), (1366, 768, 1), (1680, 1050, 1)])
def test_der_massstab_richtet_sich_nach_dem_bildschirm(wurzel, monkeypatch, tmp_path, breite, hoehe, erwartet):
    """Ein 1080p-Schulmonitor bekommt alles 1,5-mal so gross, ein Laptop nicht."""
    _bildschirm(monkeypatch, wurzel, breite, hoehe)
    fenster = ablauf.oeffnen(wurzel, zeitgeber=lambda: 0.0, protokollordner=tmp_path)
    assert fenster.massstab == erwartet


@pytest.mark.parametrize("massstab", [1.5])
def test_im_grossen_massstab_wachsen_schriften_und_abstaende(fenster, wurzel):
    assert tkfont.nametofont("TkDefaultFont", root=wurzel).cget("size") == 18
    assert tkfont.nametofont(stil.SCHRIFT_TITEL, root=wurzel).cget("size") == 27
    assert tkfont.nametofont(stil.SCHRIFT_ERZAEHLUNG, root=wurzel).cget("size") == 21
    assert fenster.px(stil.ABSTAND) == 24
    assert fenster.aktueller_screen.px(stil.ABSTAND) == 24
    assert fenster.aktueller_screen.buehne.animation.massstab == 1.5


@pytest.mark.parametrize("kennt_zoomed_zustand, wie", [(True, "state"), (False, "attributes")])
def test_das_fenster_oeffnet_maximiert(wurzel, monkeypatch, tmp_path, kennt_zoomed_zustand, wie):
    """Windows kennt dafür den Zustand "zoomed", X11 nur das Attribut -zoomed."""
    zustand = Fensterzustand(kennt_zoomed_zustand)
    monkeypatch.setattr(wurzel, "state", zustand.state)
    monkeypatch.setattr(wurzel, "attributes", zustand.attributes)
    ablauf.oeffnen(wurzel, zeitgeber=lambda: 0.0, protokollordner=tmp_path, massstab=1)
    if wie == "state":
        assert zustand.zustand == "zoomed"
    else:
        assert zustand.werte["-zoomed"] == 1


def test_f11_schaltet_ins_vollbild_und_esc_zurueck(wurzel, monkeypatch, tmp_path, ausloesen):
    zustand = Fensterzustand(kennt_zoomed_zustand=True)
    monkeypatch.setattr(wurzel, "attributes", zustand.attributes)
    fenster = ablauf.oeffnen(wurzel, zeitgeber=lambda: 0.0, protokollordner=tmp_path, massstab=1)
    assert not fenster.vollbild
    ausloesen(wurzel, "<F11>")
    assert fenster.vollbild
    ausloesen(wurzel, "<Escape>")
    assert not fenster.vollbild
    ausloesen(wurzel, "<Escape>")                # Esc ohne Vollbild schadet nicht
    assert not fenster.vollbild
    ausloesen(wurzel, "<F11>")
    ausloesen(wurzel, "<F11>")                   # F11 schaltet auch wieder zurück
    assert not fenster.vollbild


@pytest.mark.parametrize("bildschirm", [(1920, 1080), (900, 650)], ids=["1080p", "winzig"])
def test_nicht_maximiert_wird_das_fenster_nie_groesser_als_der_bildschirm(wurzel, monkeypatch, tmp_path, bildschirm):
    """Die Grösse, auf die das Fenster beim Verkleinern zurückspringt – und die Mindestgrösse."""
    _bildschirm(monkeypatch, wurzel, *bildschirm)
    verlangt = []
    monkeypatch.setattr(wurzel, "geometry", lambda neu=None: verlangt.append(neu))
    fenster = ablauf.oeffnen(wurzel, zeitgeber=lambda: 0.0, protokollordner=tmp_path)
    breite, hoehe = (int(zahl) for zahl in verlangt[-1].split("+")[0].split("x"))
    assert breite <= bildschirm[0] - hauptfenster.RAND_BILDSCHIRM[0]
    assert hoehe <= bildschirm[1] - hauptfenster.RAND_BILDSCHIRM[1]
    min_breite, min_hoehe = wurzel.minsize()
    assert min_breite <= breite and min_hoehe <= hoehe
    assert min_breite <= fenster.px(hauptfenster.MIN_BREITE) and min_hoehe <= fenster.px(hauptfenster.MIN_HOEHE)


class Fuellend(Screen):
    """Ein Screen, der den ganzen Platz im Fenster einnehmen will – wie das Handbuch."""

    fuellt_fenster = True


def test_ein_screen_steht_in_der_mitte_des_fensters(fenster):
    """Auf einem grossen Bildschirm stünde er sonst oben am Rand."""
    info = fenster.aktueller_screen.pack_info()
    assert int(info["expand"]) == 1 and info["fill"] == "none"


def test_ein_fuellender_screen_nimmt_den_ganzen_platz(fenster):
    info = fenster.zeige(Fuellend).pack_info()
    assert int(info["expand"]) == 1 and info["fill"] == "both"


def test_der_rand_um_den_screen_hat_dessen_farbe(fenster):
    """Sonst endete der Nachthimmel an einem grauen Rand."""
    assert fenster.inhalt.cget("bg") == stil.FARBE_NACHT
    probe = fenster.zeige(Probe)
    assert fenster.inhalt.cget("bg") == probe.cget("bg")


# ───────────────────────────────────────────────────────────────────────────
# 2. Der Screen-Wechsel
# ───────────────────────────────────────────────────────────────────────────

def test_zeige_tauscht_den_screen_aus(wurzel):
    ereignisse = []
    fenster = _probefenster(wurzel, ereignisse)
    alt = fenster.aktueller_screen
    neu = fenster.zeige(Probe, name="zwei", ereignisse=ereignisse)
    assert ereignisse == [
        ("gebaut", "start"),
        ("angezeigt", "start"),
        ("verlassen", "start"),
        ("gebaut", "zwei"),
        ("angezeigt", "zwei"),
    ]
    assert fenster.aktueller_screen is neu
    assert not alt.winfo_exists()


def test_im_inhalt_steht_immer_nur_ein_screen(fenster):
    for _ in range(5):
        fenster.zeige(Probe)
    assert len(fenster.inhalt.winfo_children()) == 1


def test_ein_unbekanntes_datum_fuer_den_screen_ist_ein_fehler(fenster):
    """Ein Tippfehler im Namen soll auffallen, nicht still ignoriert werden."""
    with pytest.raises(TypeError):
        fenster.zeige(Probe, gibts_nicht=1)


def test_die_kopfzeile_zeigt_den_titel_des_screens(fenster):
    fenster.zeige(Probe)
    assert fenster.kopfzeile[0] == "Probe"


def test_ein_screen_weiss_ob_er_noch_angezeigt_wird(fenster):
    erster = fenster.zeige(Probe)
    assert erster.ist_angezeigt
    fenster.zeige(Probe)
    assert not erster.ist_angezeigt


def _warten(wurzel, sekunden):
    """Lässt das Fenster so viele Sekunden lang arbeiten, damit angemeldete Aufträge laufen."""
    ende = time.monotonic() + sekunden
    while time.monotonic() < ende:
        wurzel.update()
        time.sleep(0.005)


def test_ein_spaeter_auftrag_feuert_wenn_der_screen_bleibt(fenster, wurzel):
    """Die Gegenprobe zum nächsten Test – sonst bewiese der nichts."""
    gefeuert = []
    fenster.zeige(Probe).spaeter(10, lambda: gefeuert.append(True))
    _warten(wurzel, 0.15)
    assert gefeuert == [True]


def _angemeldete_auftraege(wurzel):
    """Alle Aufträge, die gerade bei Tk für später angemeldet sind (``after``)."""
    return set(wurzel.tk.splitlist(wurzel.tk.call("after", "info")))


def test_ein_spaeter_auftrag_wird_beim_wechsel_abgemeldet(fenster, wurzel):
    """Geprüft an Tcl selbst: Nach dem Wechsel darf er dort nicht mehr stehen.

    Dass er nicht mehr läuft, genügte als Nachweis nicht – Tkinter löscht
    beim Abriss eines Screens dessen Rückrufe, der Auftrag bliebe aber bei
    Tcl angemeldet und liefe ins Leere.
    """
    gefeuert = []
    auftrag = fenster.zeige(Probe).spaeter(10_000, lambda: gefeuert.append(True))
    assert auftrag in _angemeldete_auftraege(wurzel)
    fenster.zeige(Probe)
    assert auftrag not in _angemeldete_auftraege(wurzel)
    assert gefeuert == []


def test_ein_ausgefuehrter_auftrag_wird_vergessen(fenster, wurzel):
    screen = fenster.zeige(Probe)
    screen.spaeter(5, lambda: None)
    _warten(wurzel, 0.1)
    assert screen._auftraege == set()


# ───────────────────────────────────────────────────────────────────────────
# 3. Takt und Kopfzeile
# ───────────────────────────────────────────────────────────────────────────

def test_der_takt_ist_von_anfang_an_angemeldet(fenster):
    assert fenster._takt_auftrag is not None


def test_das_level_steht_in_der_kopfzeile(fenster):
    _bis_zum_handbuch(fenster)
    assert fenster.kopfzeile == ("Handbuch – Level 1", "Level 1 · Caesar-Verschlüsselung")


def test_es_gibt_keine_sichtbare_restzeit(fenster, uhr):
    """Ein mitzählender Countdown erzeugt Zeitdruck – bewusst nicht gezeigt.

    Die Uhr läuft trotzdem im Hintergrund weiter: Projektregel 1 gilt auch
    ohne sichtbare Anzeige.
    """
    _bis_zum_handbuch(fenster)
    assert not hasattr(fenster, "_zeitanzeige")
    vorher = fenster.kopfzeile
    uhr.weiter(60.5)
    fenster._takt()
    assert fenster.kopfzeile == vorher                     # unverändert sichtbar
    assert fenster.durchlauf.spielstand.verbleibende_sekunden == pytest.approx(
        DAUER_JE_LEVEL_SEKUNDEN[1] - 60.5
    )


def test_der_takt_schaltet_nach_ablauf_weiter(fenster, uhr):
    _bis_zum_handbuch(fenster)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    fenster._takt()
    _nachlese_durchklicken(fenster)                 # die verpassten Funksprüche zum Mitlesen
    assert fenster.durchlauf.spielstand.aktuelles_level == 2
    assert fenster.kopfzeile == ("Handbuch – Level 2", "Level 2 · monoalphabetische Substitution")


def test_der_takt_laeuft_wirklich_ueber_after(fenster, wurzel, uhr, monkeypatch):
    """Ohne Aufruf von Hand: Nur die Ereignisschleife läuft, und das Level wechselt."""
    monkeypatch.setattr(hauptfenster, "TAKT_MILLISEKUNDEN", 5)
    _bis_zum_handbuch(fenster)
    fenster._takt()  # meldet den nächsten Takt mit 5 ms an
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    ende = time.monotonic() + 2
    while fenster.durchlauf.spielstand.aktuelles_level == 1 and time.monotonic() < ende:
        wurzel.update()
        time.sleep(0.005)
    assert fenster.durchlauf.spielstand.aktuelles_level == 2


def test_ein_fehler_im_takt_haelt_die_uhr_nicht_an(fenster, monkeypatch):
    """Sonst liefe nach einem einzigen Fehler kein Zeitfenster mehr ab."""
    _bis_zum_handbuch(fenster)

    def kaputt():
        """Scheitert – für die Frage, ob ein Fehler im Takt die Uhr anhält."""
        raise RuntimeError("Fehler im Takt")

    monkeypatch.setattr(fenster.durchlauf, "takt", kaputt)
    with pytest.raises(RuntimeError):
        fenster._takt()
    assert fenster._takt_auftrag is not None


def test_ein_direkter_takt_startet_keinen_zweiten_daneben(fenster, wurzel):
    fenster.zeige(Probe)   # ein Screen ohne Animation – sonst zählte deren Takt mit
    for _ in range(5):
        fenster._takt()
    angemeldet = wurzel.tk.splitlist(wurzel.tk.call("after", "info"))
    assert len(angemeldet) == 1


# ───────────────────────────────────────────────────────────────────────────
# 4. Eine Aufgabe, die zu spät kommt
# ───────────────────────────────────────────────────────────────────────────

def test_eine_zu_spaet_gestellte_uebung_schaltet_sofort_weiter(fenster, uhr):
    """Zwischen Ablauf und nächstem Takt: kein Absturz, sondern das nächste Level."""
    _bis_zum_handbuch(fenster)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] + 0.1)
    _klick(fenster, "Zu den Übungen")
    screen = _nachlese_durchklicken(fenster)
    assert isinstance(screen, handbuch.Handbuch)
    assert screen.titel == "Handbuch – Level 2"
    assert fenster.durchlauf.spielstand.aktuelle_aufgabe is None
    assert fenster.meldung == ""


class StelltImKonstruktor(Screen):
    """Hält sich nicht an die Regel und stellt schon beim Bauen eine Aufgabe."""

    def __init__(self, fenster):
        """Ein Screen, der schon im Konstruktor eine Übung stellt – genau das soll auffallen."""
        super().__init__(fenster)
        fenster.durchlauf.naechste_uebung()


def test_ein_screen_der_zu_frueh_stellt_verdeckt_den_levelwechsel_nicht(fenster, uhr):
    """Sonst stünden zwei Screens übereinander, und der richtige läge unten."""
    _bis_zum_handbuch(fenster)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] + 0.1)
    fenster.zeige(StelltImKonstruktor)
    assert len(fenster.inhalt.winfo_children()) == 1, "Kein halb gebauter Screen bleibt liegen."
    assert isinstance(_nachlese_durchklicken(fenster), handbuch.Handbuch)
    assert fenster.aktueller_screen.titel == "Handbuch – Level 2"


def test_die_uebung_wird_erst_beim_anzeigen_gestellt(fenster, monkeypatch):
    """Mit dem Stellen beginnt die Uhr der Aufgabe – beim Bauen steht sie noch nicht da.

    Geprüft wird die Reihenfolge: Als der Screen angezeigt wird, darf noch
    keine Aufgabe laufen. Am Ergebnis allein sähe man den Unterschied nicht,
    weil ``zeige()`` auch einen zu früh stellenden Screen auffängt.
    """
    beobachtet = []
    echt = uebung.Uebung.beim_anzeigen

    def beobachten(screen):
        """Schreibt mit, welche Aufgabe beim Anzeigen schon gestellt war."""
        beobachtet.append(screen.durchlauf.spielstand.aktuelle_aufgabe)
        echt(screen)

    monkeypatch.setattr(uebung.Uebung, "beim_anzeigen", beobachten)
    _bis_zur_uebung(fenster)
    assert beobachtet == [None]
    assert fenster.durchlauf.spielstand.aktuelle_aufgabe is not None


# ───────────────────────────────────────────────────────────────────────────
# 5. Meldungen
# ───────────────────────────────────────────────────────────────────────────

def test_ohne_meldung_nimmt_die_zeile_keinen_platz_weg(fenster):
    assert fenster.meldung == ""
    assert fenster._meldungszeile.winfo_manager() == ""


def test_ein_speicherfehler_steht_in_der_meldungszeile(fenster, monkeypatch):
    _bis_zur_uebung(fenster)
    speicher = Speicher(fenster.durchlauf.protokoll)
    monkeypatch.setattr(fenster.durchlauf.protokoll, "schreiben", speicher)
    _loesen(fenster)
    assert "nicht gespeichert" in fenster.meldung
    assert "erneut versucht" in fenster.meldung
    assert fenster._meldungszeile.winfo_manager() == "pack"

    speicher.gesperrt = False
    _loesen(fenster)
    assert fenster.meldung == ""
    assert fenster._meldungszeile.winfo_manager() == ""
    assert len(_zeilen(fenster)) == 2


def test_ein_fehler_in_einem_knopf_wird_angezeigt(fenster, capsys):
    """Tkinter schriebe ihn nur auf die Konsole – die sieht im Klassenzimmer keiner."""

    def kaputt():
        """Scheitert mit einer Meldung – für die Frage, ob ein Knopffehler angezeigt wird."""
        raise RuntimeError("Probefehler")

    knopf = tk.Button(fenster.aktueller_screen, command=kaputt)
    knopf.invoke()
    assert "Unerwarteter Fehler" in fenster.meldung
    assert "Probefehler" in fenster.meldung
    assert "Probefehler" in capsys.readouterr().err
    assert fenster._takt_auftrag is not None


def test_ein_fehler_ohne_text_nennt_wenigstens_seine_art(fenster):
    def kaputt():
        """Scheitert ohne Meldung – dann muss wenigstens die Fehlerart dastehen."""
        raise RuntimeError()

    tk.Button(fenster.aktueller_screen, command=kaputt).invoke()
    assert "RuntimeError" in fenster.meldung


# ───────────────────────────────────────────────────────────────────────────
# 6. Schliessen
# ───────────────────────────────────────────────────────────────────────────

def test_waehrend_eines_levels_wird_vor_dem_schliessen_gefragt(fenster, wurzel):
    _bis_zur_uebung(fenster)
    fenster.frage_ja_nein = Rueckfrage(False)
    fenster.schliessen_anfragen()
    assert not fenster.ist_geschlossen
    assert wurzel.winfo_exists()
    assert fenster.durchlauf.spielstand.aktuelle_aufgabe is not None


def test_wer_bestaetigt_beendet_und_die_offene_aufgabe_steht_im_log(fenster, uhr):
    _bis_zur_uebung(fenster)
    uhr.weiter(33)
    fenster.frage_ja_nein = Rueckfrage(True)
    fenster.schliessen_anfragen()
    assert fenster.ist_geschlossen
    zeile = _zeilen(fenster)[0]
    assert zeile["abgebrochen"] == "ja"
    assert zeile["sekunden"] == "33"


def test_das_kreuz_am_fensterrand_ist_angeschlossen(fenster, wurzel):
    _bis_zur_uebung(fenster)
    fenster.frage_ja_nein = Rueckfrage(False)
    wurzel.tk.call(wurzel.protocol("WM_DELETE_WINDOW"))
    assert len(fenster.frage_ja_nein.fragen) == 1


def test_vor_dem_ersten_level_wird_nicht_gefragt(fenster, tmp_path):
    fenster.schliessen_anfragen()  # Rueckfrage() ohne Antwort schlüge fehl
    assert fenster.ist_geschlossen
    assert list(tmp_path.iterdir()) == []


def test_nach_dem_spielende_wird_nicht_gefragt(fenster, uhr):
    _bis_zur_uebung(fenster)
    _alle_level_ablaufen_lassen(fenster, uhr)
    assert isinstance(fenster.aktueller_screen, abschluss.Abschluss)
    fenster.schliessen_anfragen()
    assert fenster.ist_geschlossen


def test_scheitert_das_speichern_beim_schliessen_wird_nachgefragt(fenster, monkeypatch):
    _bis_zur_uebung(fenster)
    monkeypatch.setattr(
        fenster.durchlauf.protokoll, "schreiben", Speicher(fenster.durchlauf.protokoll)
    )
    fenster.frage_ja_nein = Rueckfrage(True)
    fenster.frage_nochmal = Rueckfrage(True, False)  # einmal nochmal, dann aufgeben
    fenster.schliessen_anfragen()
    assert len(fenster.frage_nochmal.fragen) == 2
    titel, text = fenster.frage_nochmal.fragen[0]
    assert "nicht gespeichert" in titel
    assert "Excel" in text
    assert fenster.ist_geschlossen


def test_ein_erneuter_versuch_beim_schliessen_rettet_die_daten(fenster, monkeypatch):
    _bis_zur_uebung(fenster)
    speicher = Speicher(fenster.durchlauf.protokoll)
    monkeypatch.setattr(fenster.durchlauf.protokoll, "schreiben", speicher)

    def datei_in_excel_geschlossen():
        """Gibt die Datei wieder frei – als hätte jemand Excel geschlossen."""
        speicher.gesperrt = False

    fenster.frage_ja_nein = Rueckfrage(True)
    fenster.frage_nochmal = Rueckfrage(True, vorher=datei_in_excel_geschlossen)
    fenster.schliessen_anfragen()
    assert fenster.ist_geschlossen
    assert _zeilen(fenster)[0]["abgebrochen"] == "ja"


def test_nach_dem_schliessen_laeuft_kein_takt_mehr(fenster):
    fenster.schliessen()
    assert fenster.ist_geschlossen
    assert fenster._takt_auftrag is None


class StolpertBeimVerlassen(Screen):
    """Ein Screen, bei dem das Abräumen scheitert."""

    def beim_verlassen(self):
        """Scheitert beim Abräumen – der Wechsel muss trotzdem klappen."""
        raise RuntimeError("Fehler beim Abräumen")


def test_das_fenster_geht_zu_auch_wenn_ein_screen_beim_abraeumen_stolpert(fenster, wurzel):
    fenster.zeige(StolpertBeimVerlassen)
    with pytest.raises(RuntimeError):
        fenster.schliessen()
    assert fenster.ist_geschlossen
    with pytest.raises(tk.TclError):
        wurzel.winfo_exists()


def test_zweimal_schliessen_schadet_nicht(fenster):
    fenster.schliessen()
    fenster.schliessen()
    assert fenster.ist_geschlossen


# ───────────────────────────────────────────────────────────────────────────
# 7. Ein Fenster, ein Durchlauf
# ───────────────────────────────────────────────────────────────────────────

def test_ein_zweiter_durchlauf_im_selben_fenster_ist_verboten(fenster):
    """Sonst mischten sich beim Wechsel die Messdaten zweier Personen."""
    _bis_zum_handbuch(fenster)
    with pytest.raises(ValueError) as fehler:
        fenster.starte_durchlauf(fenster.durchlauf.spielstand.figur)
    assert "neu starten" in str(fehler.value)


# ───────────────────────────────────────────────────────────────────────────
# 8. Der ganze Weg bis zum Abschluss
# ───────────────────────────────────────────────────────────────────────────

def test_der_ganze_weg_laesst_sich_bis_zum_abschluss_durchklicken(fenster, uhr, tmp_path):
    """Ein Durchlauf, bei dem jede Aufgabe gelöst wird – vom Titel bis zur Rettung.

    Die Schrittgrenze ist grosszügig: Seit ein Level seine Restzeit mit
    Übungen füllt, sind es je Level bis zu achtzehn davon.
    """
    _bis_zur_uebung(fenster)
    for _ in range(300):
        screen = fenster.aktueller_screen
        if isinstance(screen, abschluss.Abschluss):
            break
        if getattr(screen, "aufgabe", None) is None:
            screen.weiter()                           # Handbuchseite oder Erzähltext
        else:
            uhr.weiter(60)
            _loesen(fenster)
    assert isinstance(fenster.aktueller_screen, abschluss.Abschluss)
    assert fenster.durchlauf.spielstand.ist_durchgespielt
    assert fenster.kopfzeile == ("Die Rettung", "")

    zeilen = _zeilen(fenster)
    assert {z["pseudonym"] for z in zeilen} == {"ID 1-12"}   # so macht Excel kein Datum daraus
    assert fenster.durchlauf.protokoll.dateiname.startswith("durchlauf_1-12_")
    level = [z["level"] for z in zeilen]
    assert level == sorted(level), "Die Zeilen stehen in der Reihenfolge des Spiels."
    for nummer, funksprueche in ((1, ["erster_ruf", "bob_erste_antwort"]),
                                 (2, ["verfolger"]),
                                 (3, ["standort", "bob_zweite_antwort"])):
        im_level = [z for z in zeilen if z["level"] == str(nummer)]
        # Erst die Pflichtübungen, dann die Funksprüche in ihrer Reihenfolge –
        # und danach füllen weitere Übungen die Restzeit des Levels.
        assert [z["kennung"] for z in im_level if z["quelle"] == "funkspruch"] == funksprueche, (
            f"Level {nummer}: die Funksprüche in der Reihenfolge der Geschichte."
        )
        uebungen = [z for z in im_level if z["quelle"] == "uebung"]
        assert len(uebungen) >= 2, f"Level {nummer}: mindestens die zwei Pflichtübungen."
        assert len({z["kennung"] for z in uebungen}) == len(uebungen), "Keine Übung doppelt."
    # Ein Level endet entweder am Timer (dann steht die Übung, die dabei lief,
    # als abgebrochen im Log) oder vorzeitig, wenn ihm die eigenen Texte
    # ausgehen. Untätig gewartet hat in beiden Fällen niemand.
    assert {z["levelende"] for z in zeilen} <= {"vorzeitig", "zeitablauf"}
    for zeile in zeilen:
        assert zeile["geloest"] == "ja" or zeile["abgebrochen"] == "ja"
    assert len([z for z in zeilen if z["abgebrochen"] == "ja"]) <= 3, "höchstens eine je Level"
    assert [p.name for p in tmp_path.iterdir()] == [fenster.durchlauf.protokoll.dateiname]

    _klick(fenster, "Warten")                                  # die Augen fallen zu …
    fenster.aktueller_screen.zu_zeit(abschluss.GELANDET)       # … bis der Hubschrauber gelandet ist
    _klick(fenster, "Weiter")
    _klick(fenster, "Spiel beenden")
    assert fenster.ist_geschlossen


def test_endet_level_3_am_timer_steht_es_im_abschluss(fenster, uhr):
    _bis_zur_uebung(fenster)
    _alle_level_ablaufen_lassen(fenster, uhr)
    assert isinstance(fenster.aktueller_screen, abschluss.Abschluss)
    assert fenster.aktueller_screen.hinweis == abschluss.HINWEIS_ZEITABLAUF


# ───────────────────────────────────────────────────────────────────────────
# 9. main.py
# ───────────────────────────────────────────────────────────────────────────

def test_die_messdaten_landen_neben_main_py():
    """Nicht im Arbeitsverzeichnis – sonst hinge der Ort davon ab, wie gestartet wurde."""
    assert main.PROTOKOLLORDNER.is_absolute()
    assert main.PROTOKOLLORDNER == Path(main.__file__).resolve().parent / "logs"


def test_ohne_bildschirm_meldet_main_das_verstaendlich(monkeypatch, capsys):
    def ohne_anzeige(*_, **__):
        """Tut so, als gäbe es keine Bildschirmanzeige."""
        raise tk.TclError("no display name and no $DISPLAY environment variable")

    monkeypatch.setattr(tk, "Tk", ohne_anzeige)
    assert main.starte_spiel() == 1
    assert "keine Bildschirmanzeige" in capsys.readouterr().err


def test_ohne_tkinter_meldet_main_das_verstaendlich(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "tkinter", None)
    assert main.starte_spiel() == 1
    assert "tkinter" in capsys.readouterr().err


def test_main_oeffnet_das_spiel_mit_dem_startscreen(wurzel, monkeypatch):
    """Der echte Einstieg: Fenster auf, erster Screen da, Schleife zu."""
    geoeffnet = []
    echt_oeffnen = ablauf.oeffnen

    def oeffnen_und_merken(neue_wurzel, **kwargs):
        """Öffnet das Spiel wie sonst und merkt sich, womit."""
        fenster = echt_oeffnen(neue_wurzel, **kwargs)
        geoeffnet.append((fenster, kwargs))
        return fenster

    monkeypatch.setattr(ablauf, "oeffnen", oeffnen_und_merken)
    monkeypatch.setattr(tk.Tk, "mainloop", lambda self, n=0: self.destroy())
    assert main.starte_spiel() == 0
    fenster, kwargs = geoeffnet[0]
    assert isinstance(fenster.aktueller_screen, ablauf.STARTSCREEN)
    assert kwargs["protokollordner"] == main.PROTOKOLLORDNER


def test_die_kopfzeile_steht_im_nachthimmel_statt_in_einer_hellen_leiste(fenster):
    """Eine graue oder weisse Leiste über Buch und Szenen wirkte wie ein Formular."""
    teile = [fenster.wurzel, fenster.inhalt, fenster._titelanzeige, fenster._levelanzeige,
             fenster._titelanzeige.master, fenster._meldungszeile]
    assert {teil.cget("bg") for teil in teile} == {stil.FARBE_NACHT}
    assert fenster._titelanzeige.cget("fg") == stil.FARBE_SAND
