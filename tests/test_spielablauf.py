"""Tests für den Weg durch ein Level (Arbeitsplan Phase 7): ui/ablauf.py.

Die Regeln dahinter prüft ``tests/test_levelablauf.py`` ohne Bildschirm. Hier
geht es darum, dass die Oberfläche sie auch befolgt: dass nach dem Handbuch
geübt wird, dass danach das Funkgerät kommt, dass eine Zusatzaufgabe als
solche gestellt wird – und dass die Funksprüche auch dann drankommen, wenn
jemand bei den Übungen trödelt.

Braucht eine Bildschirmanzeige, sonst übersprungen.
"""

import pytest

tk = pytest.importorskip("tkinter")

from content import charaktere, story  # noqa: E402
from game import levelablauf, zusatzaufgaben  # noqa: E402
from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN  # noqa: E402
from ui import ablauf, funk, handbuch, uebung  # noqa: E402

FIGUR = charaktere.VIC_MORENO


class Uhr:
    def __init__(self):
        self.jetzt = 0.0

    def __call__(self):
        return self.jetzt

    def weiter(self, sekunden):
        self.jetzt += sekunden


@pytest.fixture
def wurzel():
    try:
        wurzel = tk.Tk()
    except tk.TclError as fehler:
        pytest.skip(f"Keine Bildschirmanzeige: {fehler}")
    wurzel.withdraw()
    yield wurzel
    try:
        wurzel.destroy()
    except tk.TclError:
        pass


@pytest.fixture
def uhr():
    return Uhr()


@pytest.fixture
def fenster(wurzel, tmp_path, massstab, uhr):
    fenster = ablauf.oeffnen(wurzel, zeitgeber=uhr, protokollordner=tmp_path, massstab=massstab)
    fenster.frage_ja_nein = lambda *_, **__: True
    return fenster


@pytest.fixture
def bei_der_uebung(fenster):
    """Level 1 läuft, die erste Übung steht da."""
    fenster.aktueller_screen._feld.insert(0, "1-12")
    fenster.aktueller_screen.starten()
    fenster.aktueller_screen.waehle(FIGUR)
    fenster.aktueller_screen.bestaetigen()
    for _ in story.INTRO.absaetze:
        fenster.aktueller_screen.weiter()
    assert isinstance(fenster.aktueller_screen, handbuch.Handbuch)
    fenster.aktueller_screen.weiter()
    return fenster.aktueller_screen


def _loesen(fenster, sekunden=0.0, uhr=None):
    """Löst die laufende Aufgabe – Übung oder Funkspruch – und geht weiter."""
    if uhr is not None:
        uhr.weiter(sekunden)
    screen = fenster.aktueller_screen
    if hasattr(screen, "anzeige_vervollstaendigen"):
        screen.anzeige_vervollstaendigen()
    screen._feld.delete(0, "end")
    screen._feld.insert(0, screen.aufgabe.loesung)
    screen.pruefen()
    if getattr(screen, "restknopf_sichtbar", False):
        screen.rest_freigeben()
    screen.weiter()
    return fenster.aktueller_screen


#: So lange dauert eine Aufgabe, ohne dass sie als "schnell gelöst" gilt.
NORMALTEMPO = 60.0


# ───────────────────────────────────────────────────────────────────────────
# 1. Die Reihenfolge im Level
# ───────────────────────────────────────────────────────────────────────────

def test_nach_dem_handbuch_kommt_die_erste_uebung(bei_der_uebung):
    screen = bei_der_uebung
    assert isinstance(screen, uebung.Uebung)
    assert screen.aufgabe.level == 1 and not screen.aufgabe.zusatzaufgabe


def test_nach_den_uebungen_kommt_das_funkgeraet(fenster, bei_der_uebung, uhr):
    for _ in range(levelablauf.BASIS_UEBUNGEN_JE_LEVEL):
        assert isinstance(fenster.aktueller_screen, uebung.Uebung)
        _loesen(fenster, NORMALTEMPO, uhr)
    screen = fenster.aktueller_screen
    assert isinstance(screen, funk.Funk)
    assert screen.funkspruch is story.FUNKSPRUCH_ERSTER_RUF


def test_nach_dem_letzten_funkspruch_beginnt_das_naechste_level(fenster, bei_der_uebung, uhr):
    while not isinstance(fenster.aktueller_screen, handbuch.Handbuch):
        _loesen(fenster, NORMALTEMPO, uhr)
    assert fenster.aktueller_screen.seite.level == 2
    assert fenster.durchlauf.spielstand.aktuelles_level == 2
    kennungen = [b.aufgabe.kennung for b in fenster.durchlauf.spielstand.erledigte_aufgaben]
    assert kennungen[-2:] == ["erster_ruf", "bob_erste_antwort"]


# ───────────────────────────────────────────────────────────────────────────
# 2. Zusatzaufgaben für die Schnellen
# ───────────────────────────────────────────────────────────────────────────

def test_wer_schnell_ist_bekommt_eine_zusatzaufgabe(fenster, bei_der_uebung):
    """Die Uhr steht still – schneller geht es nicht."""
    for _ in range(levelablauf.BASIS_UEBUNGEN_JE_LEVEL):
        _loesen(fenster)
    screen = fenster.aktueller_screen
    assert isinstance(screen, uebung.Uebung)
    assert screen.aufgabe.zusatzaufgabe, "Sie muss im Log als Zusatzaufgabe stehen."
    _loesen(fenster)
    assert fenster.durchlauf.spielstand.zusatzaufgaben_im_level() == 1
    assert fenster.durchlauf.spielstand.uebungen_im_level() == levelablauf.BASIS_UEBUNGEN_JE_LEVEL


def test_nach_den_zusatzaufgaben_kommt_trotzdem_das_funkgeraet(fenster, bei_der_uebung):
    """Die Obergrenze des Levels gilt – sonst käme man nie zur Geschichte."""
    for _ in range(levelablauf.BASIS_UEBUNGEN_JE_LEVEL
                   + zusatzaufgaben.HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL):
        _loesen(fenster)
    assert isinstance(fenster.aktueller_screen, funk.Funk)


# ───────────────────────────────────────────────────────────────────────────
# 3. Die Vorrang-Regel
# ───────────────────────────────────────────────────────────────────────────

def test_wer_troedelt_kommt_trotzdem_zum_funkspruch(fenster, bei_der_uebung, uhr):
    """Auch wenn die zweite Übung dafür ausfällt (Arbeitsplan Phase 7)."""
    noetig = zusatzaufgaben.erwartete_dauer_funksprueche(story.FUNKSPRUECHE_NACH_LEVEL[1])
    _loesen(fenster, DAUER_JE_LEVEL_SEKUNDEN[1] - noetig - zusatzaufgaben.MINDESTRESTZEIT_SEKUNDEN, uhr)
    screen = fenster.aktueller_screen
    assert isinstance(screen, funk.Funk), "Die zweite Übung fällt aus, der Funkspruch nicht."
    assert fenster.durchlauf.spielstand.uebungen_im_level() == 1
    assert screen.funkspruch is story.FUNKSPRUCH_ERSTER_RUF


def test_eine_laufende_uebung_wird_nicht_abgebrochen(fenster, bei_der_uebung, uhr):
    """Die Vorrang-Regel greift erst zwischen zwei Aufgaben, nie mitten in einer."""
    screen = bei_der_uebung
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] - 1)
    assert fenster.aktueller_screen is screen
    assert screen.aufgabe is fenster.durchlauf.spielstand.aktuelle_aufgabe
