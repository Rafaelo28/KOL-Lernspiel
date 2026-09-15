"""Tests für den Handbuch-Screen (Arbeitsplan 6.4): ui/handbuch.py.

Geprüft wird, dass jede Seite vollständig und richtig dasteht – Text,
Tabellen, Merksatz, auf Seite 3 das Quadrat –, dass sie sich lesen und
scrollen lässt, und dass man mitten in einer Übung nachschlagen und zur
selben Übung zurückkehren kann (Arbeitsplan 6.4: "Muss während der Aufgaben
erreichbar bleiben").

Was *im* Handbuch steht, prüft ``tests/test_handbuch.py`` gegen die Quelle
und gegen ``crypto/``. Hier geht es darum, dass es auch auf dem Bildschirm
ankommt.

Braucht eine Bildschirmanzeige, sonst übersprungen. Die wenigen Tests, die
echte Grössen brauchen (scrollt die Seite? wie breit wird sie?), zeigen das
Fenster kurz an – ein verstecktes ist für Tk nur 1 × 1 Pixel gross.
"""

import pytest

tk = pytest.importorskip("tkinter")

from content import charaktere, story  # noqa: E402
from content import handbuch as buch  # noqa: E402
from crypto.normalize import ALPHABET  # noqa: E402
from crypto.vigenere_quadrat import erzeuge_quadrat  # noqa: E402
from ui import ablauf, handbuch, platzhalter  # noqa: E402

LEVEL = (1, 2, 3)


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


class Uhr:
    def __init__(self):
        self.jetzt = 0.0

    def __call__(self):
        return self.jetzt


@pytest.fixture
def uhr():
    return Uhr()


@pytest.fixture
def fenster(wurzel, tmp_path, massstab, uhr):
    fenster = ablauf.oeffnen(wurzel, zeitgeber=uhr, protokollordner=tmp_path, massstab=massstab)
    fenster.frage_ja_nein = lambda *_, **__: True
    return fenster


@pytest.fixture
def aufrufe():
    return []


@pytest.fixture
def sichtbar(wurzel):
    """Zeigt das Fenster wirklich an – nur dann hat Tk echte Grössen.

    Ein verstecktes Fenster ist für Tk 1 × 1 Pixel gross; ob die Seite scrollt
    oder wie breit sie wird, liesse sich daran nicht ablesen. Danach wird es
    gleich wieder versteckt.
    """
    def zeigen(breite, hoehe):
        wurzel.geometry(f"{breite}x{hoehe}")
        wurzel.deiconify()
        wurzel.update()

    yield zeigen
    wurzel.withdraw()


def _seite(fenster, level, aufrufe, **optionen):
    return fenster.zeige(handbuch.Handbuch, level=level, danach=aufrufe.append, **optionen)


def _texte(seite):
    """Alle Absätze, Aufzählungspunkte und Überschriften einer Handbuchseite."""
    for abschnitt in seite.abschnitte:
        yield abschnitt.ueberschrift
        for block in abschnitt.bloecke:
            if isinstance(block, buch.Absatz):
                yield block.text
            elif isinstance(block, buch.Aufzaehlung):
                yield from block.punkte
            elif isinstance(block, buch.Tabelle) and block.titel:
                yield block.titel
            elif isinstance(block, buch.VigenereQuadrat) and block.beschriftung:
                yield block.beschriftung


def _bereiche(screen, tag):
    """Die Textstücke, die ein Tag trägt."""
    bereiche = screen.text.tag_ranges(tag)
    return [screen.text.get(anfang, ende) for anfang, ende in zip(bereiche[::2], bereiche[1::2])]


# ── Was auf der Seite steht ────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
def test_die_seite_des_levels_steht_vollstaendig_da(fenster, aufrufe, level):
    screen = _seite(fenster, level, aufrufe)
    seite = buch.SEITE_NACH_LEVEL[level]
    assert screen.seite is seite
    assert seite.titel in screen.inhalt
    assert buch.HANDBUCH_TITEL.upper() in screen.inhalt
    assert buch.HANDBUCH_UNTERTITEL in screen.inhalt
    for text in _texte(seite):
        assert text in screen.inhalt, f"Auf Seite {level} fehlt: {text[:60]}…"


@pytest.mark.parametrize("level", LEVEL)
def test_die_abschnitte_stehen_in_der_richtigen_reihenfolge(fenster, aufrufe, level):
    screen = _seite(fenster, level, aufrufe)
    ueberschriften = [a.ueberschrift for a in screen.seite.abschnitte]
    stellen = [screen.inhalt.index(u) for u in ueberschriften]
    assert stellen == sorted(stellen)


def test_nummerierte_schritte_tragen_ihre_nummer(fenster, aufrufe):
    screen = _seite(fenster, 3, aufrufe)
    assert '1.\tH (Nachricht) + R (Schlüssel)' in screen.inhalt
    assert "4.\tGeheimbuchstabe U" in screen.inhalt


def test_stichpunkte_bekommen_einen_punkt(fenster, aufrufe):
    screen = _seite(fenster, 2, aufrufe)
    assert "•\tErste Zeile: Q W E R T Z U I O P" in screen.inhalt


@pytest.mark.parametrize("level", LEVEL)
def test_der_merksatz_ist_hinterlegt(fenster, aufrufe, level):
    screen = _seite(fenster, level, aufrufe)
    hinterlegt = " ".join(_bereiche(screen, "merksatz"))
    (merksatz,) = [a for a in screen.seite.abschnitte if a.hervorgehoben]
    for block in merksatz.bloecke:
        assert block.text in hinterlegt
    # … und nur der Merksatz
    for abschnitt in screen.seite.abschnitte:
        if not abschnitt.hervorgehoben:
            assert abschnitt.ueberschrift not in hinterlegt


@pytest.mark.parametrize("level", LEVEL)
def test_ergebnisse_und_beispiel_ueberschriften_sind_fett(fenster, aufrufe, level):
    screen = _seite(fenster, level, aufrufe)
    fett = _bereiche(screen, "betont")
    betonte = [block.text for a in screen.seite.abschnitte for block in a.bloecke
               if isinstance(block, buch.Absatz) and block.betont]
    assert betonte, f"Seite {level} hat keine betonte Zeile."
    assert [text.rstrip("\n") for text in fett] == betonte


def test_die_seite_laesst_sich_nicht_beschreiben(fenster, aufrufe):
    screen = _seite(fenster, 1, aufrufe)
    vorher = screen.inhalt
    screen.text.insert("1.0", "Kritzelei")
    assert screen.inhalt == vorher
    assert screen.text.cget("state") == "disabled"


# ── Tabellen und Quadrat ───────────────────────────────────────────────────

def _zellen(rahmen):
    """Die Tabelle als Zeilen von Texten, gelesen aus dem Raster."""
    zeilen = {}
    for zelle in rahmen.grid_slaves():
        info = zelle.grid_info()
        zeilen.setdefault(int(info["row"]), {})[int(info["column"])] = zelle.cget("text")
    return [tuple(spalten[s] for s in sorted(spalten)) for _, spalten in sorted(zeilen.items())]


@pytest.mark.parametrize("level", LEVEL)
def test_jede_tabelle_steht_als_raster_da(fenster, aufrufe, level):
    screen = _seite(fenster, level, aufrufe)
    tabellen = [block for a in screen.seite.abschnitte for block in a.bloecke if isinstance(block, buch.Tabelle)]
    assert len(screen.tabellen) == len(tabellen)
    for rahmen, tabelle in zip(screen.tabellen, tabellen):
        assert _zellen(rahmen) == [tuple(zeile) for zeile in tabelle.zeilen]


def test_die_tabellen_sitzen_im_text_und_scrollen_mit(fenster, aufrufe):
    screen = _seite(fenster, 2, aufrufe)
    eingebettet = {str(name) for name in screen.text.window_names()}
    assert {str(rahmen) for rahmen in screen.tabellen} <= eingebettet


def test_nur_seite_3_zeichnet_das_quadrat(fenster, aufrufe):
    assert _seite(fenster, 1, aufrufe).quadrat is None
    assert _seite(fenster, 2, aufrufe).quadrat is None
    assert _seite(fenster, 3, aufrufe).quadrat is not None


def test_das_quadrat_stimmt_in_allen_676_feldern(fenster, aufrufe):
    """Gezeichnet aus derselben Formel wie crypto/ – kein abgetipptes Feld."""
    screen = _seite(fenster, 3, aufrufe)
    quadrat = erzeuge_quadrat()
    for zeile, schluessel in enumerate(ALPHABET):
        for spalte, nachricht in enumerate(ALPHABET):
            assert screen.quadratfeld(schluessel, nachricht) == quadrat[zeile][spalte]


def test_das_quadrat_zeigt_das_beispiel_aus_dem_handbuch(fenster, aufrufe):
    screen = _seite(fenster, 3, aufrufe)
    assert [screen.quadratfeld(s, n) for s, n in zip("ROTR", "HUND")] == list("YIGU")


def test_das_quadrat_ist_beschriftet(fenster, aufrufe):
    leinwand = _seite(fenster, 3, aufrufe).quadrat
    kopfzeile = [leinwand.itemcget(e, "text") for e in leinwand.find_withtag("kopfzeile")]
    kopfspalte = [leinwand.itemcget(e, "text") for e in leinwand.find_withtag("kopfspalte")]
    assert "".join(kopfzeile) == ALPHABET == "".join(kopfspalte)
    assert len(leinwand.find_withtag("feld")) == 26 * 26


# ── Lesen und Scrollen ─────────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
def test_die_seite_ist_laenger_als_der_platz_und_scrollt(fenster, aufrufe, wurzel, sichtbar, level):
    screen = _seite(fenster, level, aufrufe)
    sichtbar(1000, 700)
    anfang, ende = screen.text.yview()
    assert anfang == 0 and ende < 1, "Die Seite passt ganz hinein – dann gäbe es nichts zu scrollen."
    screen.rollen(10)
    wurzel.update_idletasks()
    assert screen.text.yview()[0] > 0


def _rad(ausloesen, widget, delta):
    import re

    skript = widget.bind("<MouseWheel>")
    assert re.search(r"\[(\S+) %#", skript), f"{widget} leitet das Mausrad nicht weiter"
    return ausloesen(widget, "<MouseWheel>")


def test_das_mausrad_rollt_auch_ueber_einer_tabelle(fenster, aufrufe, wurzel, ausloesen, monkeypatch):
    """Über einem eingebetteten Raster käme das Rad sonst nicht beim Text an."""
    screen = _seite(fenster, 3, aufrufe)
    wurzel.geometry("1000x700")
    wurzel.update_idletasks()
    gerollt = []
    monkeypatch.setattr(screen, "rollen", gerollt.append)
    for teil in (screen.tabellen[0], *screen.tabellen[0].winfo_children(), screen.quadrat):
        assert teil.bind("<MouseWheel>"), f"{teil} leitet das Mausrad nicht weiter"
        assert teil.bind("<Button-4>") and teil.bind("<Button-5>")
    ausloesen(screen.quadrat, "<Button-5>")
    ausloesen(screen.quadrat, "<Button-4>")
    assert gerollt == [handbuch.ZEILEN_JE_RASTE, -handbuch.ZEILEN_JE_RASTE]


@pytest.mark.parametrize("delta, erwartet", [(120, -3), (-120, 3), (240, -6), (30, -1), (-10, 1)])
def test_das_mausrad_rollt_je_raste_drei_zeilen(fenster, aufrufe, monkeypatch, delta, erwartet):
    """Windows meldet 120 je Raste; kleinere Werte (Touchpad) rollen mindestens eine Zeile."""
    screen = _seite(fenster, 1, aufrufe)
    gerollt = []
    monkeypatch.setattr(screen, "rollen", gerollt.append)

    class Ereignis:
        pass

    ereignis = Ereignis()
    ereignis.delta = delta
    screen._mausrad(ereignis)
    assert gerollt == [erwartet]


def test_die_seite_hat_den_fokus_fuer_die_pfeiltasten(fenster, aufrufe):
    screen = _seite(fenster, 1, aufrufe)
    assert str(screen.text.cget("takefocus")) in ("", "1")
    assert screen.text.cget("yscrollcommand")


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_die_seite_nutzt_die_ganze_hoehe_des_fensters(fenster, aufrufe, wurzel, sichtbar, massstab):
    """Sonst stünde nur ein Streifen Papier da, und man müsste ständig scrollen."""
    screen = _seite(fenster, 1, aufrufe, einleitung=story.EINSTIEG_LEVEL_1.absaetze)
    hoehe = 700 if massstab == 1 else 1000
    sichtbar(1920, hoehe)
    assert screen.text.winfo_height() > 0.6 * hoehe
    assert screen._knopf.winfo_rooty() + screen._knopf.winfo_height() <= wurzel.winfo_rooty() + hoehe


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_die_seite_wird_nicht_breiter_als_zum_lesen_gut(fenster, aufrufe, sichtbar, massstab):
    """Auf einem 1920 Pixel breiten Monitor wären die Zeilen sonst viel zu lang."""
    screen = _seite(fenster, 1, aufrufe)
    sichtbar(1920, 1000)
    blatt = screen.text.master
    assert blatt.winfo_width() == screen.px(handbuch.SEITENBREITE)
    assert screen.winfo_width() > blatt.winfo_width()         # der Rest ist Nachthimmel


@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("level", LEVEL)
def test_die_tabellen_passen_auf_die_seite(fenster, aufrufe, wurzel, massstab, level):
    screen = _seite(fenster, level, aufrufe)
    wurzel.update_idletasks()
    platz = screen.px(handbuch.SEITENBREITE)
    for fenster_im_text in [*screen.tabellen, screen.quadrat]:
        if fenster_im_text is not None:
            assert fenster_im_text.winfo_reqwidth() <= platz


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_der_handbuch_screen_passt_ins_fenster(fenster, aufrufe, wurzel, platz):
    _seite(fenster, 2, aufrufe, einleitung=story.EINSTIEG_LEVEL_2.absaetze,
           hinweis="Die Zeit für Level 1 ist abgelaufen – weiter geht es mit Level 2.")
    wurzel.update_idletasks()
    assert wurzel.winfo_reqwidth() <= platz[0]
    assert wurzel.winfo_reqheight() <= platz[1]


# ── Knopf, Einleitung, Hinweis ─────────────────────────────────────────────

def test_der_knopf_fuehrt_weiter(fenster, aufrufe, ausloesen):
    screen = _seite(fenster, 1, aufrufe)
    assert screen.knopftext == handbuch.KNOPF_WEITER
    screen._knopf.invoke()
    ausloesen(screen._knopf, "<Return>")
    assert aufrufe == [fenster, fenster]


def test_einleitung_und_hinweis_stehen_ueber_der_seite(fenster, aufrufe):
    screen = _seite(fenster, 2, aufrufe, einleitung=story.EINSTIEG_LEVEL_2.absaetze, hinweis="Zeit um.")
    assert screen.einleitung == story.EINSTIEG_LEVEL_2.absaetze
    assert screen.hinweis == "Zeit um."


def test_ohne_einleitung_und_hinweis_steht_nichts_darueber(fenster, aufrufe):
    screen = _seite(fenster, 1, aufrufe)
    assert screen.einleitung == () and screen.hinweis == ""


def test_die_kopfzeile_nennt_das_level(fenster, aufrufe):
    assert _seite(fenster, 3, aufrufe).titel == "Handbuch – Level 3"


# ── Im Spielablauf ─────────────────────────────────────────────────────────

def _bis_zum_handbuch(fenster):
    fenster.aktueller_screen._feld.insert(0, "1-12")
    fenster.aktueller_screen.starten()
    fenster.aktueller_screen.waehle(charaktere.JONAS_BERG)
    fenster.aktueller_screen.bestaetigen()
    for _ in story.INTRO.absaetze:
        fenster.aktueller_screen.weiter()


def test_nach_dem_intro_liegt_seite_1_mit_dem_einstieg_auf(fenster):
    _bis_zum_handbuch(fenster)
    screen = fenster.aktueller_screen
    assert isinstance(screen, handbuch.Handbuch)
    assert screen.seite is buch.SEITE_CAESAR
    assert screen.einleitung == story.EINSTIEG_LEVEL_1.absaetze
    assert screen.knopftext == handbuch.KNOPF_WEITER
    assert fenster.durchlauf.spielstand.aktuelles_level == 1


def test_nach_dem_handbuch_kommen_die_uebungen(fenster):
    _bis_zum_handbuch(fenster)
    fenster.aktueller_screen.weiter()
    assert isinstance(fenster.aktueller_screen, platzhalter.Uebung)
    assert fenster.durchlauf.spielstand.aktuelle_aufgabe is not None


def test_nach_einem_levelwechsel_liegt_die_naechste_seite_auf(fenster):
    _bis_zum_handbuch(fenster)
    fenster.durchlauf.naechstes_level()
    screen = fenster.aktueller_screen
    assert isinstance(screen, handbuch.Handbuch)
    assert screen.seite is buch.SEITE_SUBSTITUTION
    assert screen.einleitung == story.EINSTIEG_LEVEL_2.absaetze
    assert screen.hinweis == ""                            # vorzeitig beendet, nicht abgelaufen


def test_ist_die_zeit_abgelaufen_sagt_die_seite_es(fenster, uhr):
    from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN

    _bis_zum_handbuch(fenster)
    uhr.jetzt += DAUER_JE_LEVEL_SEKUNDEN[1]
    fenster._takt()
    screen = fenster.aktueller_screen
    assert screen.seite is buch.SEITE_SUBSTITUTION
    assert "Level 1 ist abgelaufen" in screen.hinweis


# ── Nachschlagen während einer Übung ───────────────────────────────────────

def test_mitten_in_der_uebung_laesst_sich_nachschlagen(fenster, uhr):
    _bis_zum_handbuch(fenster)
    fenster.aktueller_screen.weiter()
    aufgabe = fenster.durchlauf.spielstand.aktuelle_aufgabe
    uebung = fenster.aktueller_screen
    uebung._nachschlagen()
    screen = fenster.aktueller_screen
    assert isinstance(screen, handbuch.Handbuch)
    assert screen.seite is buch.SEITE_CAESAR
    assert screen.knopftext == handbuch.KNOPF_ZURUECK
    assert screen.einleitung == ()                         # beim Nachschlagen keine Geschichte
    assert fenster.durchlauf.spielstand.aktuelle_aufgabe is aufgabe   # die Übung bleibt offen


def test_zurueck_vom_nachschlagen_geht_es_mit_derselben_uebung_weiter(fenster, uhr):
    """Keine neue Übung – und die Zeit zum Nachschlagen zählt mit, sie gehört zum Lösen."""
    _bis_zum_handbuch(fenster)
    fenster.aktueller_screen.weiter()
    stand = fenster.durchlauf.spielstand
    aufgabe = stand.aktuelle_aufgabe
    fenster.aktueller_screen._nachschlagen()
    uhr.jetzt += 40
    fenster.aktueller_screen.weiter()
    assert isinstance(fenster.aktueller_screen, platzhalter.Uebung)
    assert stand.aktuelle_aufgabe is aufgabe
    assert len(stand.erledigte_aufgaben) == 0
    assert aufgabe.kennung in fenster.aktueller_screen._aufgabentext.cget("text")
    stand.versuchen(aufgabe.loesung)
    fenster.durchlauf.aufgabe_abschliessen()
    assert round(stand.erledigte_aufgaben[0].benoetigte_sekunden) == 40


def test_nachschlagen_im_naechsten_level_zeigt_dessen_seite(fenster):
    _bis_zum_handbuch(fenster)
    fenster.durchlauf.naechstes_level()
    fenster.aktueller_screen.weiter()
    fenster.aktueller_screen._nachschlagen()
    assert fenster.aktueller_screen.seite is buch.SEITE_SUBSTITUTION


def test_laeuft_die_zeit_beim_nachschlagen_ab_kommt_das_naechste_level(fenster, uhr):
    """Projektregel 1 gilt auch im Handbuch: Die Übung wird abgebrochen, Level 2 beginnt."""
    from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN

    _bis_zum_handbuch(fenster)
    fenster.aktueller_screen.weiter()
    fenster.aktueller_screen._nachschlagen()
    uhr.jetzt += DAUER_JE_LEVEL_SEKUNDEN[1]
    fenster._takt()
    screen = fenster.aktueller_screen
    assert screen.seite is buch.SEITE_SUBSTITUTION
    assert screen.knopftext == handbuch.KNOPF_WEITER       # kein "Zurück zur Aufgabe" mehr
    assert fenster.durchlauf.spielstand.erledigte_aufgaben[0].abgebrochen
