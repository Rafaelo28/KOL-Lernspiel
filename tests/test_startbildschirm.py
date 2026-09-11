"""Tests für den Startbildschirm (Arbeitsplan 6.2): ui/startbildschirm.py.

Braucht eine Bildschirmanzeige, sonst übersprungen.
"""

import pytest

tk = pytest.importorskip("tkinter")

from ui import ablauf, figurwahl, hauptfenster, startbildschirm  # noqa: E402


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
    return ablauf.oeffnen(wurzel, zeitgeber=lambda: 0.0, protokollordner=tmp_path)


def test_das_spiel_beginnt_mit_dem_titelbild(fenster):
    screen = fenster.aktueller_screen
    assert isinstance(screen, startbildschirm.Startbildschirm)
    assert screen.buehne.animation.name == startbildschirm.ANIMATION
    assert fenster.kopfzeile == ("Willkommen", "")


def test_das_titelbild_laeuft_sobald_es_zu_sehen_ist(fenster):
    assert fenster.aktueller_screen.buehne.laeuft


def test_der_untertitel_steht_unter_dem_schriftzug(fenster):
    """Nicht über dem glänzenden Schriftzug und nicht über den Bildrand hinaus."""
    screen = fenster.aktueller_screen
    assert screen.untertitel == startbildschirm.UNTERTITEL
    screen.update_idletasks()
    x0, y0, x1, y1 = screen.buehne.bbox(screen._untertitel)
    animation = screen.buehne.animation
    schriftzug_unten = max(a.y + a.hoehe for a in animation.ausschnitte)
    assert y0 >= schriftzug_unten
    assert x0 >= 0 and x1 <= animation.breite and y1 <= animation.hoehe


def test_spiel_starten_fuehrt_zur_figurwahl(fenster):
    fenster.aktueller_screen._knopf.invoke()
    assert isinstance(fenster.aktueller_screen, figurwahl.Figurwahl)
    assert fenster.durchlauf is None                      # noch keine Figur – noch kein Durchlauf


def test_enter_startet_das_spiel(fenster, ausloesen):
    ausloesen(fenster.aktueller_screen._knopf, "<Return>")
    assert isinstance(fenster.aktueller_screen, figurwahl.Figurwahl)


def test_der_screen_weiss_nichts_vom_ablauf(fenster):
    """Was nach dem Knopf kommt, gibt ui/ablauf.py vor."""
    aufrufe = []
    screen = fenster.zeige(startbildschirm.Startbildschirm, danach=aufrufe.append)
    screen.starten()
    assert aufrufe == [fenster]


def test_nach_dem_wechsel_steht_das_titelbild_still(fenster, wurzel):
    """Sonst liefe ein after() ins Leere."""
    auftrag = fenster.aktueller_screen.buehne._auftrag
    fenster.aktueller_screen.starten()
    assert auftrag not in wurzel.tk.splitlist(wurzel.tk.call("after", "info"))


def test_der_startbildschirm_passt_ins_fenster(fenster, wurzel):
    wurzel.update_idletasks()
    assert wurzel.winfo_reqwidth() <= hauptfenster.FENSTER_BREITE
    assert wurzel.winfo_reqheight() <= hauptfenster.FENSTER_HOEHE
