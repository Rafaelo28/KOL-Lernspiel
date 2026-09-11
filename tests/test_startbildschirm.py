"""Tests für den Startbildschirm (Arbeitsplan 6.2): ui/startbildschirm.py.

Neben dem Titelbild geht es um das ID-Feld: Es nimmt nur IDs der Form X-XX an
(siehe game/spieler_id.py), einen Namen kann man gar nicht erst eintippen,
und ohne vollständige ID geht es nicht weiter.

Braucht eine Bildschirmanzeige, sonst übersprungen.
"""

import pytest

tk = pytest.importorskip("tkinter")

from game import spieler_id  # noqa: E402
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


@pytest.fixture
def screen(fenster):
    return fenster.aktueller_screen


@pytest.fixture
def tippen(screen, ausloesen):
    """Tippt Zeichen für Zeichen ins ID-Feld – wie es eine Tastatur täte.

    Erst die Bindung des Feldes (sie setzt den fehlenden Strich), dann Tks
    eigene, die das Zeichen an der Schreibmarke einfügt.
    """
    def tippen(text):
        for zeichen in text:
            ausloesen(screen._feld, "<KeyPress>", zeichen=zeichen)
            screen._feld.insert("insert", zeichen)
    return tippen


# ── Das Titelbild ──────────────────────────────────────────────────────────

def test_das_spiel_beginnt_mit_dem_titelbild(fenster, screen):
    assert isinstance(screen, startbildschirm.Startbildschirm)
    assert screen.buehne.animation.name == startbildschirm.ANIMATION
    assert fenster.kopfzeile == ("Willkommen", "")


def test_das_titelbild_laeuft_sobald_es_zu_sehen_ist(screen):
    assert screen.buehne.laeuft


def _rahmen(screen, element):
    screen.update_idletasks()
    return screen.buehne.bbox(element)


def test_untertitel_und_hinweis_stehen_unter_dem_schriftzug(screen):
    """Nicht über dem glänzenden Schriftzug, nicht übereinander, nicht über den Rand."""
    assert screen.untertitel == startbildschirm.UNTERTITEL
    animation = screen.buehne.animation
    schriftzug_unten = max(a.y + a.hoehe for a in animation.ausschnitte)
    _, u_oben, _, u_unten = _rahmen(screen, screen._untertitel)
    _, h_oben, _, h_unten = _rahmen(screen, screen._hinweis)
    assert schriftzug_unten <= u_oben < u_unten <= h_oben < h_unten <= animation.hoehe


def test_jede_meldung_passt_in_die_zeile(screen):
    """Die Meldungen sind unterschiedlich lang – keine darf über den Bildrand laufen."""
    breite = screen.buehne.animation.breite
    for eingabe in ("", "1", "1-", "1-2", "112", "-12", "Max"):
        screen._hinweis_setzen(spieler_id.fehler(eingabe), "#fff")
        links, _, rechts, _ = _rahmen(screen, screen._hinweis)
        assert 0 <= links and rechts <= breite, eingabe


def test_der_startbildschirm_passt_ins_fenster(screen, wurzel):
    wurzel.update_idletasks()
    assert wurzel.winfo_reqwidth() <= hauptfenster.FENSTER_BREITE
    assert wurzel.winfo_reqheight() <= hauptfenster.FENSTER_HOEHE


# ── Das ID-Feld ────────────────────────────────────────────────────────────

def test_am_anfang_ist_das_feld_leer_und_der_hinweis_erklaert_es(screen):
    assert screen.eingabe == ""
    assert screen.hinweis == startbildschirm.HINWEIS_ID
    assert spieler_id.BEISPIEL in screen.hinweis
    assert not screen.hinweis_ist_warnung


def test_eine_id_laesst_sich_eintippen(screen, tippen):
    tippen("1-12")
    assert screen.eingabe == "1-12"


def test_ein_name_kommt_nicht_ins_feld(screen, tippen):
    tippen("Max Mustermann")
    assert screen.eingabe == ""


def test_buchstaben_zwischen_den_ziffern_werden_abgewiesen(screen, tippen):
    tippen("1a-b1c2")
    assert screen.eingabe == "1-12"


def test_auch_eingefuegter_text_muss_eine_id_sein(screen):
    """Wer einen Namen aus der Zwischenablage einfügt, kommt damit nicht durch."""
    screen._feld.insert(0, "Lea")
    assert screen.eingabe == ""
    screen._feld.insert(0, "3-07")
    assert screen.eingabe == "3-07"


def test_eine_zu_lange_nummer_wird_abgewiesen(screen, tippen):
    tippen("1-123")
    assert screen.eingabe == "1-12"


def test_der_strich_kommt_von_selbst(screen, tippen):
    """Wer nach der Klasse gleich die Nummer tippt, bekommt den Strich dazu."""
    tippen("112")
    assert screen.eingabe == "1-12"


def test_eine_markierte_klasse_wird_ersetzt_und_nicht_ergaenzt(screen, tippen, ausloesen):
    """Wer die Klasse markiert und überschreibt, will sie tauschen – kein Strich dazu."""
    tippen("1")
    feld = screen._feld
    feld.selection_range(0, "end")
    feld.icursor("end")
    ausloesen(feld, "<KeyPress>", zeichen="2")
    # Tks eigene Bindung ersetzt beim Tippen die Markierung: erst löschen, dann einfügen.
    feld.delete("sel.first", "sel.last")
    feld.insert("insert", "2")
    assert screen.eingabe == "2"


def test_vor_der_klasse_kommt_kein_strich_hinein(screen, tippen, ausloesen):
    tippen("1")
    screen._feld.icursor(0)
    ausloesen(screen._feld, "<KeyPress>", zeichen="2")
    screen._feld.insert("insert", "2")
    assert screen.eingabe == "1"                 # "21" ist kein Anfang einer ID


def test_loeschen_ist_immer_erlaubt(screen, tippen):
    """Sonst liesse sich eine vertippte Klasse nicht mehr ausbessern."""
    tippen("1-12")
    screen._feld.delete(0)
    assert screen.eingabe == "-12"
    screen._feld.insert(0, "2")
    assert screen.eingabe == "2-12"


# ── Starten ────────────────────────────────────────────────────────────────

def test_ohne_id_geht_es_nicht_weiter(fenster, screen):
    screen._knopf.invoke()
    assert fenster.aktueller_screen is screen
    assert fenster.durchlauf is None
    assert screen.hinweis == spieler_id.fehler("")
    assert screen.hinweis_ist_warnung


def test_eine_halbe_id_sagt_was_fehlt(fenster, screen, tippen):
    tippen("1-2")
    screen.starten()
    assert fenster.aktueller_screen is screen
    assert "1-02" in screen.hinweis


def test_wer_ausbessert_sieht_wieder_den_hinweis(screen, tippen):
    screen.starten()
    assert screen.hinweis_ist_warnung
    tippen("1")
    assert screen.hinweis == startbildschirm.HINWEIS_ID
    assert not screen.hinweis_ist_warnung


def test_mit_gueltiger_id_geht_es_zur_figurwahl(fenster, screen, tippen):
    tippen("1-12")
    screen._knopf.invoke()
    assert isinstance(fenster.aktueller_screen, figurwahl.Figurwahl)
    assert fenster.durchlauf is None                      # noch keine Figur – noch kein Durchlauf


def test_enter_im_feld_startet(fenster, screen, tippen, ausloesen):
    tippen("4-01")
    ausloesen(screen._feld, "<Return>")
    assert isinstance(fenster.aktueller_screen, figurwahl.Figurwahl)


def test_enter_auf_dem_knopf_startet(fenster, screen, tippen, ausloesen):
    tippen("4-01")
    ausloesen(screen._knopf, "<Return>")
    assert isinstance(fenster.aktueller_screen, figurwahl.Figurwahl)


def test_der_screen_gibt_die_id_weiter_und_weiss_sonst_nichts_vom_ablauf(fenster):
    """Was nach dem Knopf kommt, gibt ui/ablauf.py vor."""
    aufrufe = []
    screen = fenster.zeige(startbildschirm.Startbildschirm,
                           danach=lambda *argumente: aufrufe.append(argumente))
    screen._feld.insert(0, "2-30")
    screen.starten()
    assert aufrufe == [(fenster, "2-30")]


def test_nach_dem_wechsel_steht_das_titelbild_still(fenster, screen, wurzel, tippen):
    """Sonst liefe ein after() ins Leere."""
    auftrag = screen.buehne._auftrag
    tippen("1-12")
    screen.starten()
    assert auftrag not in wurzel.tk.splitlist(wurzel.tk.call("after", "info"))


# ── Die ID im Durchlauf ────────────────────────────────────────────────────

def test_die_id_wird_zum_pseudonym_des_durchlaufs(fenster, screen, tippen):
    tippen("5-17")
    screen.starten()
    wahl = fenster.aktueller_screen
    wahl.waehle(wahl.karten[0].figur)
    wahl.bestaetigen()
    assert fenster.durchlauf.spielstand.pseudonym == "5-17"
    assert "_5-17_" in fenster.durchlauf.protokoll.dateiname
