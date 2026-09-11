"""Tests für die Figurwahl (Arbeitsplan 6.2): ui/figurwahl.py.

Geprüft wird, was die Spielenden erleben: die Vorgeschichte, fünf Karten in
der Reihenfolge des Konzepts, erst wählen und dann bestätigen – und dass erst
das Bestätigen den Durchlauf beginnt.

Mausklicks lassen sich in einem versteckten Fenster nicht auslösen. Die Tests
rufen deshalb die Tcl-Befehle auf, die Tkinter für die Bindungen angelegt hat
(Fixture ``ausloesen`` aus ``tests/conftest.py``) – dieselben, die Tk bei
einem echten Klick aufriefe.

Die ersten Tests brauchen keinen Bildschirm, die übrigen werden ohne einen
übersprungen.
"""

import importlib.util
from pathlib import Path

import pytest

tk = pytest.importorskip("tkinter")
from tkinter import font as tkfont  # noqa: E402

from content import charaktere, story  # noqa: E402
from ui import ablauf, figurwahl, hauptfenster, intro, stil  # noqa: E402
from ui.animation import ANIMATIONSORDNER  # noqa: E402

PROJEKT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("rendern", PROJEKT / "grafik" / "rendern.py")
rendern = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rendern)

FIGUREN = charaktere.SPIELBARE_CHARAKTERE
IDS = [figur.kennung for figur in FIGUREN]


# ───────────────────────────────────────────────────────────────────────────
# 1. Die Rollen-Symbole (ohne Bildschirm)
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("figur", FIGUREN, ids=IDS)
def test_jede_figur_hat_ihr_symbol(figur):
    name = figurwahl.animation_fuer(figur)
    assert (ANIMATIONSORDNER / name / "animation.json").exists(), (
        f"Das Symbol für {figur.name} ist nicht gerendert: python3 grafik/rendern.py grafik/{name}.svg")
    assert (PROJEKT / "grafik" / f"{name}.svg").exists()


@pytest.mark.parametrize("figur", FIGUREN, ids=IDS)
def test_die_symbole_sind_auf_die_kartenfarbe_gemalt(figur):
    """Sonst stünde auf jeder Karte ein Rechteck in einer anderen Farbe."""
    bild = rendern.png_lesen((ANIMATIONSORDNER / figurwahl.animation_fuer(figur) / "hintergrund.png").read_bytes())
    erwartet = bytes.fromhex(stil.FARBE_KARTE[1:])
    for x, y in ((0, 0), (bild.breite - 1, 0), (0, bild.hoehe - 1), (bild.breite - 1, bild.hoehe - 1)):
        ecke = rendern.ausschneiden(bild, x, y, 1, 1)[0]
        assert ecke == erwartet, f"Ecke ({x}, {y}) hat #{ecke.hex()}, die Karte {stil.FARBE_KARTE}."


# ───────────────────────────────────────────────────────────────────────────
# 2. Der Screen
# ───────────────────────────────────────────────────────────────────────────

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
def gewaehlt():
    return []


@pytest.fixture
def screen(fenster, gewaehlt):
    return fenster.zeige(figurwahl.Figurwahl, danach=lambda _fenster, figur: gewaehlt.append(figur))


def _texte(widget):
    """Alle Beschriftungen im Screen, der Reihe nach."""
    texte = []
    for kind in widget.winfo_children():
        if isinstance(kind, (tk.Label, tk.Button)):
            texte.append(kind.cget("text"))
        texte.extend(_texte(kind))
    return texte


def test_die_vorgeschichte_steht_ueber_der_frage(screen):
    texte = _texte(screen)
    for absatz in story.VORGESCHICHTE.absaetze:
        assert absatz in texte
    assert texte.index(story.VORGESCHICHTE.absaetze[-1]) < texte.index(figurwahl.FRAGE)
    assert screen.titel == "Wähle deine Figur"


def test_fuenf_karten_in_der_reihenfolge_des_konzepts(screen):
    assert [karte.figur for karte in screen.karten] == list(FIGUREN)


def test_jede_karte_zeigt_symbol_initialen_name_und_rolle(screen):
    for karte in screen.karten:
        figur = karte.figur
        assert karte.buehne.animation.name == figurwahl.animation_fuer(figur)
        assert karte.initialen == figur.initialen
        assert karte._name.cget("text") == figur.name
        assert karte._rolle.cget("text") == figur.rolle


def test_der_hinweis_erklaert_die_initialen(screen):
    assert figurwahl.HINWEIS_INITIALEN in _texte(screen)
    assert "Initialen" in figurwahl.HINWEIS_INITIALEN


def test_am_anfang_ist_nichts_gewaehlt(screen):
    assert screen.gewaehlt is None
    assert not any(karte.gewaehlt for karte in screen.karten)
    assert not any(karte.buehne.laeuft for karte in screen.karten)
    assert screen.knopftext == figurwahl.KNOPF_OHNE_WAHL
    assert screen._knopf.cget("state") == "disabled"


def test_ohne_wahl_bestaetigt_der_knopf_nichts(screen, gewaehlt):
    screen._knopf.invoke()
    screen.bestaetigen()
    assert gewaehlt == []


def test_ein_klick_auf_eine_karte_waehlt_nur_aus(screen, gewaehlt, fenster, ausloesen):
    """Festgelegt ist noch nichts – ein versehentlicher Klick lässt sich korrigieren."""
    ausloesen(screen.karten[3], "<Button-1>")
    assert screen.gewaehlt == charaktere.AMARA_NWOSU
    assert gewaehlt == []
    assert fenster.durchlauf is None
    assert screen.knopftext == "Als Amara Nwosu spielen"
    assert screen._knopf.cget("state") == "normal"


def _mit_allen_kindern(widget):
    yield widget
    for kind in widget.winfo_children():
        yield from _mit_allen_kindern(kind)


def test_jeder_teil_einer_karte_nimmt_den_klick_an(screen, ausloesen):
    """Symbol, Name und Rolle – nicht nur der schmale Rand um sie herum.

    Die Teile werden hier selbst eingesammelt, nicht aus ``karte.teile``
    übernommen: Vergässe die Karte dort einen, vergässe ihn sonst auch der Test.
    """
    for nr, karte in enumerate(screen.karten):
        andere = screen.karten[(nr + 1) % len(screen.karten)].figur
        teile = list(_mit_allen_kindern(karte))
        assert len(teile) >= 4                       # Karte, Symbol, Name, Rolle
        for teil in teile:
            screen.waehle(andere)
            ausloesen(teil, "<Button-1>")
            assert screen.gewaehlt == karte.figur, f"Klick auf {teil} wählt nicht {karte.figur.name}"


def test_eine_neue_wahl_loest_die_alte_ab(screen):
    screen.waehle(charaktere.VIC_MORENO)
    screen.waehle(charaktere.THEO_LAMBERT)
    assert [karte.gewaehlt for karte in screen.karten] == [False, False, False, False, True]
    assert screen.knopftext == "Als Théo Lambert spielen"


def test_die_gewaehlte_karte_ist_golden_umrandet(screen):
    screen.waehle(charaktere.ELENA_DUARTE)
    raender = [karte.cget("highlightbackground") for karte in screen.karten]
    assert raender == [stil.FARBE_KARTENRAND, stil.FARBE_GOLD] + [stil.FARBE_KARTENRAND] * 3


def test_nur_das_symbol_der_gewaehlten_karte_bewegt_sich(screen):
    screen.waehle(charaktere.JONAS_BERG)
    assert [karte.buehne.laeuft for karte in screen.karten] == [False, False, True, False, False]
    jonas = screen.karten[2]
    jonas.buehne.zeige_bild(17)
    screen.waehle(charaktere.ELENA_DUARTE)
    assert [karte.buehne.laeuft for karte in screen.karten] == [False, True, False, False, False]
    assert jonas.buehne.bild_nr == 0, "Die abgewählte Karte soll wieder wie die anderen aussehen."


def test_nach_dem_wechsel_laeuft_kein_symbol_weiter(screen, fenster, wurzel):
    """Sonst liefe ein after() ins Leere."""
    screen.waehle(charaktere.JONAS_BERG)
    auftrag = screen.karten[2].buehne._auftrag
    fenster.zeige(figurwahl.Figurwahl, danach=lambda *_: None)
    assert auftrag not in wurzel.tk.splitlist(wurzel.tk.call("after", "info"))


def test_der_mauszeiger_hellt_den_rand_auf(screen, ausloesen):
    karte = screen.karten[1]
    ausloesen(karte._name, "<Enter>")
    assert karte.cget("highlightbackground") == stil.FARBE_KARTENRAND_HELL
    ausloesen(karte._name, "<Leave>", x_root=-50, y_root=-50)
    assert karte.cget("highlightbackground") == stil.FARBE_KARTENRAND


def test_der_mauszeiger_nimmt_der_gewaehlten_karte_nicht_das_gold(screen, ausloesen):
    screen.waehle(charaktere.ELENA_DUARTE)
    karte = screen.karten[1]
    ausloesen(karte.buehne, "<Enter>")
    ausloesen(karte.buehne, "<Leave>", x_root=-50, y_root=-50)
    assert karte.cget("highlightbackground") == stil.FARBE_GOLD


def test_eine_karte_kennt_nur_ihre_eigenen_teile(screen):
    """Die zweite Karte heisst im Tk-Pfad "…!karte2" – das ist kein Teil der ersten."""
    erste, zweite = screen.karten[0], screen.karten[1]
    assert erste.enthaelt(erste._rolle)
    assert not erste.enthaelt(zweite)
    assert not erste.enthaelt(zweite._name)


def test_die_pfeiltasten_blaettern_im_kreis(screen, ausloesen):
    ausloesen(screen._knopf, "<Right>")
    assert screen.gewaehlt == FIGUREN[0]
    ausloesen(screen._knopf, "<Left>")
    assert screen.gewaehlt == FIGUREN[-1]
    ausloesen(screen._knopf, "<Right>")
    assert screen.gewaehlt == FIGUREN[0]


def test_ohne_wahl_beginnt_pfeil_links_bei_der_letzten_karte(screen):
    screen.blaettern(-1)
    assert screen.gewaehlt == FIGUREN[-1]


def test_enter_bestaetigt(screen, gewaehlt, ausloesen):
    screen.waehle(charaktere.JONAS_BERG)
    ausloesen(screen._knopf, "<Return>")
    assert gewaehlt == [charaktere.JONAS_BERG]


def test_bestaetigen_gibt_die_gewaehlte_figur_weiter(screen, gewaehlt):
    screen.waehle(charaktere.THEO_LAMBERT)
    screen._knopf.invoke()
    assert gewaehlt == [charaktere.THEO_LAMBERT]


# ── Platz auf dem Bildschirm ───────────────────────────────────────────────

def test_kein_wort_wird_mitten_im_wort_umbrochen(screen, wurzel):
    """"Diamantenhändlerin" ist breiter als das Symbol – Tk bräche es sonst mitten im Wort um."""
    grundschrift = tkfont.nametofont("TkDefaultFont", root=wurzel)
    fett = tkfont.nametofont(stil.SCHRIFT_FETT, root=wurzel)
    for karte in screen.karten:
        for wort in karte.figur.rolle.split():
            assert grundschrift.measure(wort) <= int(karte._rolle.cget("wraplength")), wort
        for wort in karte.figur.name.split():
            assert fett.measure(wort) <= int(karte._name.cget("wraplength")), wort


def test_die_zeilen_einer_karte_bleiben_in_der_karte(screen):
    for karte in screen.karten:
        assert int(karte._rolle.cget("wraplength")) <= figurwahl.KARTENBREITE


def test_alle_karten_sind_gleich_breit(screen):
    screen.update_idletasks()
    assert len({karte.winfo_width() for karte in screen.karten}) == 1
    assert screen.karten[0].winfo_width() == figurwahl.KARTENBREITE + 2 * figurwahl.RAHMEN


def test_die_figurwahl_passt_ins_fenster(screen, wurzel):
    """In der Standardgrösse muss alles zu sehen sein – auch der Knopf ganz unten."""
    wurzel.update_idletasks()
    assert wurzel.winfo_reqwidth() <= hauptfenster.FENSTER_BREITE
    assert wurzel.winfo_reqheight() <= hauptfenster.FENSTER_HOEHE


# ───────────────────────────────────────────────────────────────────────────
# 3. Im Ablauf: erst das Bestätigen beginnt den Durchlauf
# ───────────────────────────────────────────────────────────────────────────

def test_der_startbildschirm_fuehrt_zur_figurwahl(fenster):
    fenster.aktueller_screen.starten()
    assert isinstance(fenster.aktueller_screen, figurwahl.Figurwahl)


def test_mit_der_bestaetigung_beginnt_der_durchlauf(fenster):
    fenster.aktueller_screen.starten()
    screen = fenster.aktueller_screen
    screen.waehle(charaktere.AMARA_NWOSU)
    assert fenster.durchlauf is None
    screen.bestaetigen()
    assert fenster.durchlauf.spielstand.figur == charaktere.AMARA_NWOSU
    assert isinstance(fenster.aktueller_screen, intro.Intro)
    assert fenster.durchlauf.spielstand.aktuelles_level is None   # die Uhr läuft noch nicht


def test_ein_zweites_bestaetigen_startet_keinen_zweiten_durchlauf(fenster):
    """Ein Doppelklick darf nicht als Fehler in der Meldungszeile landen."""
    fenster.aktueller_screen.starten()
    screen = fenster.aktueller_screen
    screen.waehle(charaktere.VIC_MORENO)
    screen.bestaetigen()
    screen.bestaetigen()                       # der alte Screen ist schon abgerissen
    assert fenster.durchlauf.spielstand.figur == charaktere.VIC_MORENO
    assert isinstance(fenster.aktueller_screen, intro.Intro)
