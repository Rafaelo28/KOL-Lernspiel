"""Tests für den Story-Intro (Arbeitsplan 6.3): ui/intro.py.

Geprüft wird, was die Spielenden erleben: die drei Absätze nacheinander, die
laufende Szene dahinter, und dass die Uhr von Level 1 erst mit dem letzten
Klick beginnt – der Intro kostet keine Levelzeit.

Braucht eine Bildschirmanzeige, sonst übersprungen.
"""

import pytest

tk = pytest.importorskip("tkinter")

from content import charaktere, story  # noqa: E402
from ui import ablauf, figurwahl, intro, platzhalter  # noqa: E402


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
def fenster(wurzel, tmp_path):
    fenster = ablauf.oeffnen(wurzel, zeitgeber=lambda: 0.0, protokollordner=tmp_path)
    fenster.frage_ja_nein = lambda *_, **__: True
    return fenster


@pytest.fixture
def aufrufe():
    return []


@pytest.fixture
def screen(fenster, aufrufe):
    fenster.starte_durchlauf(charaktere.VIC_MORENO)
    return fenster.zeige(intro.Intro, danach=aufrufe.append)


def _knopftext(screen):
    return screen._knopf.cget("text")


def test_der_erste_absatz_steht_zuerst_da(screen):
    assert screen.text == story.INTRO.absaetze[0]
    assert screen._zaehler.cget("text") == f"1 / {len(story.INTRO.absaetze)}"
    assert _knopftext(screen) == "Weiter"
    assert screen.titel == "Der Absturz"


def test_weiter_blaettert_absatz_fuer_absatz(screen):
    for nr in range(1, len(story.INTRO.absaetze)):
        screen.weiter()
        assert screen.absatz_nr == nr
        assert screen.text == story.INTRO.absaetze[nr]


def test_der_letzte_knopf_schlaegt_das_handbuch_auf(screen, aufrufe, fenster):
    for _ in range(len(story.INTRO.absaetze) - 1):
        screen.weiter()
    assert _knopftext(screen) == intro.LETZTER_KNOPF
    assert aufrufe == []
    screen.weiter()
    assert aufrufe == [fenster]


def test_die_szene_laeuft_sobald_der_intro_zu_sehen_ist(screen):
    assert screen.buehne.laeuft


def test_der_schatten_zeigt_denselben_text(screen):
    """Er macht den Text vor den Sternen lesbar – und muss mitblättern."""
    screen.weiter()
    assert screen.buehne.itemcget(screen._schatten, "text") == screen.text


def test_nach_dem_wechsel_laeuft_die_szene_nicht_weiter(screen, fenster, wurzel):
    """Sonst liefe ein after() ins Leere."""
    auftrag = screen.buehne._auftrag
    fenster.zeige(ablauf.STARTSCREEN, danach=lambda _fenster: None)
    assert auftrag not in wurzel.tk.splitlist(wurzel.tk.call("after", "info"))


@pytest.mark.parametrize("nr", range(len(story.INTRO.absaetze)))
def test_jeder_absatz_passt_in_den_nachthimmel(screen, nr):
    """Der Text darf nicht über das brennende Wrack laufen und nicht über den Rand."""
    for _ in range(nr):
        screen.weiter()
    screen.update_idletasks()
    x0, y0, x1, y1 = screen.buehne.bbox(screen._text)
    breite, hoehe = screen.buehne.animation.breite, screen.buehne.animation.hoehe
    assert x1 <= breite and y0 >= 0
    assert y1 < hoehe * .62, f"Absatz {nr + 1} reicht bis y={y1} – in die brennende Szene."


def test_der_intro_kostet_keine_levelzeit(fenster):
    """Die Uhr von Level 1 beginnt erst mit dem letzten Klick (Arbeitsplan 7.1)."""
    fenster.zeige(figurwahl.Figurwahl, danach=ablauf.figur_gewaehlt)
    fenster.aktueller_screen.waehle(charaktere.ELENA_DUARTE)
    fenster.aktueller_screen.bestaetigen()
    assert isinstance(fenster.aktueller_screen, intro.Intro)
    assert fenster.durchlauf.spielstand.aktuelles_level is None
    for _ in story.INTRO.absaetze:
        fenster.aktueller_screen.weiter()
    assert fenster.durchlauf.spielstand.aktuelles_level == 1
    assert isinstance(fenster.aktueller_screen, platzhalter.Handbuch)
