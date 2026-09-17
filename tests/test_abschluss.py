"""Tests für den Abschluss (Arbeitsplan 6.8): ui/abschluss.py.

Geprüft wird, was die Spielenden erleben: das Nachtlager mit dem Knopf
"Warten", die Augen, die zufallen, "Die Nacht vergeht." auf Schwarz, der
Morgen, der Hubschrauber, der landet – und am Ende der Schlusstext mit dem
Weg zu den Messdaten. Die Zeit nach dem Warten-Knopf wird direkt angesteuert
(``zu_zeit``); der Takt liest nur die Uhr ab.

Braucht eine Bildschirmanzeige, sonst übersprungen.
"""

import importlib.util
from pathlib import Path

import pytest

tk = pytest.importorskip("tkinter")

from content import charaktere, story  # noqa: E402
from ui import abschluss, ablauf  # noqa: E402
from ui.abschluss import FLUG, GELANDET, GERAEUSCH, LIDER, MORGEN_BEGINNT, NACHT  # noqa: E402

PROJEKT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("abschluss_zeichnen", PROJEKT / "grafik" / "abschluss_zeichnen.py")
zeichnung = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(zeichnung)


class Uhr:
    def __init__(self):
        self.jetzt = 100.0

    def __call__(self):
        return self.jetzt


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
def fenster(wurzel, tmp_path, massstab):
    fenster = ablauf.oeffnen(wurzel, zeitgeber=lambda: 0.0, protokollordner=tmp_path, massstab=massstab)
    fenster.frage_ja_nein = lambda *_, **__: True
    fenster.starte_durchlauf(charaktere.VIC_MORENO, pseudonym="1-12")
    return fenster


@pytest.fixture
def uhr():
    return Uhr()


@pytest.fixture
def screen(fenster, uhr):
    return fenster.zeige(abschluss.Abschluss, zeitgeber=uhr)


def _gelandet(screen):
    screen.warten()
    screen.zu_zeit(GELANDET)


def _angemeldet(wurzel):
    return wurzel.tk.splitlist(wurzel.tk.call("after", "info"))


# ───────────────────────────────────────────────────────────────────────────
# 1. Das Nachtlager
# ───────────────────────────────────────────────────────────────────────────

def test_zuerst_das_nachtlager_mit_dem_knopf_warten(screen):
    assert screen.titel == "Die Rettung"
    assert screen.buehne.animation.name == abschluss.ABEND
    assert screen.text == "\n\n".join(story.NACHTHIMMEL.absaetze)
    assert screen.knopftext == story.BESCHRIFTUNG_WARTEN
    assert screen.knopf_bereit
    assert screen.hinweis == ""
    assert screen.phase == "abend"


def test_die_szene_laeuft(screen):
    assert screen.buehne.laeuft


def test_der_knopf_bekommt_den_fokus_wann_immer_er_etwas_neues_kann(fenster, uhr, monkeypatch):
    """Mit Return geht es weiter – wie im Intro. Im versteckten Testfenster
    vergibt Tk keinen Fokus, deshalb wird der Aufruf mitgeschrieben."""
    bekommen = []
    monkeypatch.setattr(tk.Button, "focus_set", lambda knopf: bekommen.append(knopf.cget("text")))
    screen = fenster.zeige(abschluss.Abschluss, zeitgeber=uhr)
    assert bekommen == ["Warten"]
    _gelandet(screen)
    assert bekommen == ["Warten", "Weiter"]
    screen.weiter()
    assert bekommen == ["Warten", "Weiter", "Spiel beenden"]


def test_der_schatten_zeigt_denselben_text(screen):
    screen.warten()
    assert screen.buehne.itemcget(screen._schatten, "text") == screen.text


def test_nach_zeitablauf_steht_es_unten_links(fenster, uhr):
    screen = fenster.zeige(abschluss.Abschluss, durch_zeitablauf=True, zeitgeber=uhr)
    assert screen.hinweis == "Die Zeit für Level 3 ist abgelaufen."
    screen.warten()
    screen.zu_zeit(GELANDET - 1)
    assert screen.hinweis == "Die Zeit für Level 3 ist abgelaufen."


def test_offen_liegt_kein_lid_ueber_dem_bild(screen):
    oben, unten = screen.lidkanten()
    assert max(y for _, y in oben) <= 0
    assert min(y for _, y in unten) >= screen.buehne.animation.hoehe


def test_return_drueckt_den_knopf(screen, ausloesen):
    ausloesen(screen._knopf, "<Return>")
    assert screen.phase == "nacht"


# ───────────────────────────────────────────────────────────────────────────
# 2. Die Augen fallen zu
# ───────────────────────────────────────────────────────────────────────────

def test_warten_laesst_die_augen_zufallen(screen):
    screen.warten()
    assert screen.phase == "nacht"
    assert not screen.knopf_bereit
    assert screen.text == story.EINSCHLAFEN.absaetze[0]
    assert not screen.nachttext_sichtbar


def test_ein_zweites_warten_startet_nichts_neu(screen, uhr):
    screen.warten()
    uhr.jetzt += 3
    screen.warten()
    screen._takt()
    assert screen.zeit_ms == 3000


def test_die_augen_kaempfen_zweimal_gegen_den_schlaf(screen):
    """Halb zu, wieder auf, weiter zu, wieder auf – dann ganz zu."""
    werte = [wert for zeit, wert in LIDER if zeit <= NACHT]
    richtungen = [b > a for a, b in zip(werte, werte[1:])]
    assert richtungen == [True, False, True, False, True]
    assert werte[-1] == 1.0


def _mitte_der_kanten(screen):
    oben, unten = screen.lidkanten()
    return oben[len(oben) // 2][1], unten[len(unten) // 2][1]


def test_die_lider_folgen_der_uhr(screen):
    screen.warten()
    hoehe = screen.buehne.animation.hoehe
    offen = []
    for zeit in (0, 1200, 1900, 3000, 3800):
        screen.zu_zeit(zeit)
        oben, unten = _mitte_der_kanten(screen)
        offen.append(unten - oben)
    assert offen[0] > hoehe
    assert offen[1] < offen[0] and offen[2] > offen[1] and offen[3] < offen[2] and offen[4] > offen[3]


def test_geschlossen_bleibt_keine_ritze(screen):
    screen.warten()
    screen.zu_zeit(NACHT)
    oben, unten = screen.lidkanten()
    assert all(y_oben > y_unten for (_, y_oben), (_, y_unten) in zip(oben, unten))
    assert oben[0][0] < 0 and oben[-1][0] > screen.buehne.animation.breite


def test_geschlossen_ist_das_ganze_bild_bedeckt(screen):
    """Auch die Ecken – dort sieht man sonst noch Sterne."""
    screen.warten()
    screen.zu_zeit(NACHT)
    breite, hoehe = screen.buehne.animation.breite, screen.buehne.animation.hoehe
    for x in (1, breite // 2, breite - 2):
        for y, lid in ((1, screen._lid_oben), (hoehe // 2 - 2, screen._lid_oben),
                       (hoehe // 2 + 2, screen._lid_unten), (hoehe - 2, screen._lid_unten)):
            assert lid in screen.buehne.find_overlapping(x, y, x + 1, y + 1), f"Bei ({x}, {y}) ist offen."


def test_halb_zu_ist_die_oeffnung_wie_ein_auge(screen):
    """In der Mitte am weitesten offen, zu den Seiten hin enger."""
    screen.warten()
    screen.zu_zeit(1200)
    oben, unten = screen.lidkanten()
    weiten = [u - o for (_, o), (_, u) in zip(oben, unten)]
    mitte = len(weiten) // 2
    assert weiten[:mitte + 1] == sorted(weiten[:mitte + 1])
    assert weiten[mitte:] == sorted(weiten[mitte:], reverse=True)
    assert weiten[0] < weiten[mitte] * .6 and weiten[-1] < weiten[mitte] * .6


def test_die_lider_decken_die_szene_und_der_text_liegt_darueber(screen):
    screen.warten()
    screen.zu_zeit(GELANDET)
    stapel = screen.buehne.find_all()
    lid = stapel.index(screen._lid_oben)
    assert stapel.index(screen._lid_unten) > lid
    assert all(stapel.index(element) < lid for element in screen.hubschrauber.elemente)
    assert stapel.index(screen._bodenschatten) < min(stapel.index(e) for e in screen.hubschrauber.elemente)
    assert stapel.index(screen._text) > stapel.index(screen._lid_unten)
    assert stapel.index(screen._schatten) < stapel.index(screen._text)
    assert stapel.index(screen._nachttext) == len(stapel) - 1
    assert stapel.index(screen.buehne._hintergrund_element) == 0


def test_auf_schwarz_vergeht_die_nacht(screen):
    screen.warten()
    screen.zu_zeit(NACHT - 1)
    assert not screen.nachttext_sichtbar
    screen.zu_zeit(NACHT)
    assert screen.nachttext_sichtbar
    assert screen.buehne.itemcget(screen._nachttext, "text") == story.EINSCHLAFEN.absaetze[1]
    assert screen.text == ""


# ───────────────────────────────────────────────────────────────────────────
# 3. Der Morgen und der Hubschrauber
# ───────────────────────────────────────────────────────────────────────────

def test_hinter_geschlossenen_augen_wird_es_morgen(screen):
    screen.warten()
    screen.zu_zeit(MORGEN_BEGINNT - 1)
    assert screen.buehne.animation.name == abschluss.ABEND
    screen.zu_zeit(MORGEN_BEGINNT)
    assert screen.buehne.animation.name == abschluss.MORGEN
    assert not screen.nachttext_sichtbar
    assert zwischenwert_lider(MORGEN_BEGINNT) == 1.0
    assert screen.buehne.laeuft


def zwischenwert_lider(zeit):
    return abschluss.zwischenwert(LIDER, zeit)


def test_ein_geraeusch_weckt(screen):
    screen.warten()
    screen.zu_zeit(GERAEUSCH - 1)
    assert screen.text == ""
    screen.zu_zeit(GERAEUSCH)
    assert screen.text == story.AUFWACHEN.absaetze[0]
    assert zwischenwert_lider(GERAEUSCH) == 1.0, "Das Geräusch kommt, bevor man etwas sieht."


def test_der_hubschrauber_kommt_erst_wenn_die_augen_aufgehen(screen):
    screen.warten()
    screen.zu_zeit(FLUG[0][0] - 1)
    assert screen.hubschrauber is None
    assert zwischenwert_lider(FLUG[0][0]) < 1.0
    screen.zu_zeit(FLUG[0][0])
    assert screen.hubschrauber.animation.name == abschluss.HUBSCHRAUBER


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_er_fliegt_von_rechts_ausserhalb_herein_und_landet_auf_dem_sand(screen):
    screen.warten()
    breite = screen.buehne.animation.breite
    screen.zu_zeit(FLUG[0][0])
    assert screen.hubschrauber.x >= breite, "Er erscheint nicht mitten im Bild."
    screen.zu_zeit(FLUG[1][0])
    assert (screen.hubschrauber.x, screen.hubschrauber.y) == (screen.px(FLUG[1][1][0]), screen.px(FLUG[1][1][1]))
    screen.zu_zeit(GELANDET)
    x, y = screen.hubschrauber.x, screen.hubschrauber.y
    assert (x, y) == (screen.px(FLUG[-1][1][0]), screen.px(FLUG[-1][1][1]))
    assert 0 <= x and x + screen.hubschrauber.animation.breite <= breite
    assert y + screen.hubschrauber.animation.hoehe <= screen.buehne.animation.hoehe
    screen.zu_zeit(GELANDET + 5000)
    assert (screen.hubschrauber.x, screen.hubschrauber.y) == (x, y)


def test_er_landet_neben_dem_lager_und_nicht_darauf(screen):
    """Links liegen Rucksack, Feuer und Funkgerät – rechts davon ist Platz."""
    _gelandet(screen)
    rechts_vom_lager = zeichnung.FUNKGERAET[0] / zeichnung.B * screen.buehne.animation.breite
    assert screen.hubschrauber.x > rechts_vom_lager


def test_der_rotor_dreht_sich_im_takt_der_uhr(screen):
    screen.warten()
    screen.zu_zeit(FLUG[0][0])
    takt_ms = screen.hubschrauber.animation.takt_ms
    bilder = screen.hubschrauber.animation.bilder
    for schritt in range(bilder + 2):
        zeit = FLUG[0][0] + schritt * takt_ms
        screen.zu_zeit(zeit)
        assert screen.hubschrauber.bild_nr == (zeit // takt_ms) % bilder
    screen.zu_zeit(GELANDET + 7 * takt_ms)
    assert screen.hubschrauber.bild_nr == ((GELANDET + 7 * takt_ms) // takt_ms) % bilder


def test_der_schatten_waechst_beim_landen(screen):
    screen.warten()
    screen.zu_zeit(FLUG[1][0])
    assert screen.bodenschatten is None, "Hoch oben fällt noch kein Schatten neben das Lager."
    breiten = []
    for zeit in (FLUG[1][0] + 1000, FLUG[1][0] + 1500, GELANDET):
        screen.zu_zeit(zeit)
        links, oben, rechts, unten = screen.bodenschatten
        breiten.append(rechts - links)
    assert breiten == sorted(breiten) and breiten[0] < breiten[-1]
    boden = screen.hubschrauber.y + screen.px(abschluss.KUFEN)
    assert oben < boden < unten
    assert abs((links + rechts) / 2 - (screen.hubschrauber.x + screen.hubschrauber.animation.breite / 2)) <= 1
    screen.zu_zeit(FLUG[1][0])
    assert screen.bodenschatten is None, "Beim Zurückspulen verschwindet er wieder."


# ───────────────────────────────────────────────────────────────────────────
# 4. Gerettet – und das Ende
# ───────────────────────────────────────────────────────────────────────────

def test_nach_der_landung_sagt_der_text_dass_es_freunde_sind(screen):
    screen.warten()
    screen.zu_zeit(GELANDET - 1)
    assert not screen.knopf_bereit
    assert screen.phase == "nacht"
    screen.zu_zeit(GELANDET)
    assert screen.phase == "gerettet"
    assert screen.text == story.RETTUNG.absaetze[0]
    assert screen.knopftext == "Weiter"
    assert screen.knopf_bereit


def test_ein_sprung_ans_ende_holt_alles_nach(screen):
    """Auch ein langsamer Rechner, der Takte verschluckt, landet richtig."""
    screen.warten()
    screen.zu_zeit(GELANDET + 40)
    assert screen.buehne.animation.name == abschluss.MORGEN
    assert not screen.nachttext_sichtbar
    assert screen.text == story.RETTUNG.absaetze[0]
    assert screen.hubschrauber is not None
    assert screen.phase == "gerettet"


def test_jedes_ereignis_passiert_nur_einmal(screen, monkeypatch):
    screen.warten()
    screen.zu_zeit(MORGEN_BEGINNT)
    wechsel = []
    monkeypatch.setattr(screen.buehne, "wechseln", wechsel.append)
    screen.zu_zeit(MORGEN_BEGINNT + 30)
    screen.zu_zeit(GELANDET)
    screen.weiter()
    screen.zu_zeit(GELANDET + 30)
    assert wechsel == []
    assert screen.text == "\n\n".join(story.ABSCHLUSS.absaetze)
    assert screen.knopftext == "Spiel beenden"


def test_weiter_zeigt_den_schlusstext_und_die_messdaten(screen, fenster):
    _gelandet(screen)
    screen.weiter()
    assert screen.phase == "ende"
    assert screen.text == "\n\n".join(story.ABSCHLUSS.absaetze)
    assert screen.knopftext == "Spiel beenden"
    pfad = str(fenster.durchlauf.protokoll.pfad)
    assert screen.hinweis.startswith("Die Messdaten sind gespeichert: ")
    rest = screen.hinweis.removeprefix("Die Messdaten sind gespeichert: ")
    assert pfad.endswith(rest.removeprefix("…"))
    assert rest.endswith(fenster.durchlauf.protokoll.dateiname)


def test_weiter_geht_erst_nach_der_landung(screen):
    screen.weiter()
    assert screen.phase == "abend"
    screen.warten()
    screen.zu_zeit(GELANDET - 1)
    screen.weiter()
    assert screen.phase == "nacht"
    assert screen.text != "\n\n".join(story.ABSCHLUSS.absaetze)


def test_spiel_beenden_schliesst_das_fenster(screen, fenster):
    _gelandet(screen)
    screen.weiter()
    screen._knopf.invoke()
    assert fenster.ist_geschlossen


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_ein_langer_pfad_verdraengt_den_knopf_nicht(screen, fenster, wurzel, monkeypatch, tmp_path, platz):
    lang = tmp_path.joinpath(*["ein_sehr_langer_ordnername"] * 12, "durchlauf_1-12.csv")
    monkeypatch.setattr(type(fenster.durchlauf.protokoll), "pfad", property(lambda _: lang))
    _gelandet(screen)
    screen.weiter()
    wurzel.update_idletasks()
    assert screen.hinweis.endswith(str(Path("ein_sehr_langer_ordnername", "durchlauf_1-12.csv")))
    assert "…" in screen.hinweis
    assert screen._knopf.winfo_reqwidth() + screen._hinweis.winfo_reqwidth() <= screen.buehne.animation.breite
    assert wurzel.winfo_reqwidth() <= platz[0]


# ───────────────────────────────────────────────────────────────────────────
# 5. Uhr, Takt und Fenster
# ───────────────────────────────────────────────────────────────────────────

def test_der_takt_liest_die_uhr_ab(screen, uhr, wurzel):
    screen.warten()
    assert screen.zeit_ms == 0
    assert len(_angemeldet(wurzel)) >= 1
    uhr.jetzt += 1.25
    angemeldet = len(screen._auftraege)
    screen._takt()
    assert screen.zeit_ms == 1250
    assert len(screen._auftraege) == angemeldet + 1, "Der Takt meldet sich wieder an."
    uhr.jetzt += 20
    screen._takt()
    assert screen.phase == "gerettet"


def test_vor_dem_warten_laeuft_keine_uhr(screen):
    assert screen.zeit_ms is None
    assert not screen._auftraege


def test_nach_dem_wechsel_laeuft_kein_takt_mehr(screen, fenster, wurzel):
    screen.warten()
    auftraege = set(screen._auftraege)
    assert auftraege
    fenster.zeige(ablauf.STARTSCREEN, danach=lambda _fenster: None)
    assert not auftraege & set(_angemeldet(wurzel))


@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("zeit", [None, 0, NACHT, GERAEUSCH, GELANDET, "ende"])
def test_der_abschluss_passt_ins_fenster(screen, wurzel, platz, zeit):
    if zeit is not None:
        screen.warten()
        screen.zu_zeit(GELANDET if zeit == "ende" else zeit)
    if zeit == "ende":
        screen.weiter()
    wurzel.update_idletasks()
    assert wurzel.winfo_reqwidth() <= platz[0]
    assert wurzel.winfo_reqheight() <= platz[1]


@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("zeit", [None, 0, GERAEUSCH, GELANDET, "ende"])
def test_der_text_bleibt_im_himmel_links(screen, zeit):
    """Rechts fliegt der Hubschrauber ein, unten liegt das Lager."""
    if zeit is not None:
        screen.warten()
        screen.zu_zeit(GELANDET if zeit == "ende" else zeit)
    if zeit == "ende":
        screen.weiter()
    screen.update_idletasks()
    x0, y0, x1, y1 = screen.buehne.bbox(screen._text)
    breite, hoehe = screen.buehne.animation.breite, screen.buehne.animation.hoehe
    assert x0 >= 0 and y0 >= 0
    assert x1 <= breite / 2 and y1 <= hoehe * .45


# ───────────────────────────────────────────────────────────────────────────
# 6. Die Hilfen
# ───────────────────────────────────────────────────────────────────────────

def test_zwischenwert_faehrt_weich_an_und_bremst():
    stellen = ((0, 0.0), (100, 1.0), (300, 0.0))
    assert abschluss.zwischenwert(stellen, -5) == 0.0
    assert abschluss.zwischenwert(stellen, 0) == 0.0
    assert abschluss.zwischenwert(stellen, 25) == 0.15625
    assert abschluss.zwischenwert(stellen, 50) == 0.5
    assert abschluss.zwischenwert(stellen, 100) == 1.0
    assert abschluss.zwischenwert(stellen, 200) == 0.5
    assert abschluss.zwischenwert(stellen, 400) == 0.0


def test_zwischenwert_kann_auch_punkte():
    assert abschluss.zwischenwert(((0, (0, 10)), (10, (20, 30))), 5) == (10.0, 20.0)
    assert abschluss.zwischenwert(((0, (0, 10)), (10, (20, 30))), 11) == (20, 30)


def test_vorne_kuerzen_behaelt_das_ende():
    passt = lambda text: len(text) <= 12  # noqa: E731
    assert abschluss.vorne_kuerzen("C:/Spiel/logs/datei.csv", passt) == "…s/datei.csv"
    assert abschluss.vorne_kuerzen("kurz.csv", passt) == "kurz.csv"
    assert abschluss.vorne_kuerzen("genau zwölf!", passt) == "genau zwölf!"
    assert abschluss.vorne_kuerzen("abcdef", lambda text: False) == "…f"
