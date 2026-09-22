"""Tests für den Handbuch-Screen (Arbeitsplan 6.4): ui/handbuch.py.

Das Handbuch ist ein aufgeschlagenes Buch. Geprüft wird, dass jedes Kapitel
vollständig und in der richtigen Reihenfolge im Buch steht – Text,
Tabellen, Merksatz, Randnotizen, auf Seite 3 das Quadrat –, dass neben jedem
Beispiel sein Werkzeug liegt und darin markiert ist, wo der gerade gezeigte
Schritt sucht, dass nichts über die Seiten hinausragt, dass sich blättern
lässt (Knöpfe, Tasten, Mausrad, Ecken), dass dabei ein Blatt umschlägt, und
dass man mitten in einer Übung nachschlagen und zur selben Übung
zurückkehren kann (Arbeitsplan 6.4: "Muss während der Aufgaben erreichbar
bleiben").

Was *im* Handbuch steht, prüft ``tests/test_handbuch.py`` gegen die Quelle
und gegen ``crypto/``; nach welchen Regeln es auf die Seiten verteilt wird,
``tests/test_buchsatz.py``. Hier geht es darum, dass es auch auf dem
Bildschirm ankommt.

Braucht eine Bildschirmanzeige, sonst übersprungen.
"""

import importlib.util
import time
from pathlib import Path

import pytest

tk = pytest.importorskip("tkinter")

from content import charaktere, story  # noqa: E402
from content import handbuch as buch  # noqa: E402
from crypto.normalize import ALPHABET  # noqa: E402
from crypto.vigenere_quadrat import erzeuge_quadrat  # noqa: E402
from ui import ablauf, animation, buchleinwand, buchsatz, funk, handbuch, stil, uebung  # noqa: E402

LEVEL = (1, 2, 3)
PROJEKT = Path(__file__).resolve().parent.parent


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
        pass


class Uhr:
    """Eine Uhr zum Stellen: Sie gibt zurück, was in ``jetzt`` steht."""

    def __init__(self):
        """Beginnt bei null Sekunden."""
        self.jetzt = 0.0

    def __call__(self):
        """Das Spiel fragt die Uhr wie eine Funktion: ``zeitgeber()``."""
        return self.jetzt


@pytest.fixture
def uhr():
    """Die stellbare Uhr – ohne sie liefe im Test die echte Zeit mit."""
    return Uhr()


@pytest.fixture
def fenster(wurzel, tmp_path, massstab, uhr):
    """Ein Hauptfenster an der stellbaren Uhr, das ins Testverzeichnis schreibt."""
    fenster = ablauf.oeffnen(wurzel, zeitgeber=uhr, protokollordner=tmp_path, massstab=massstab)
    fenster.frage_ja_nein = lambda *_, **__: True
    return fenster


@pytest.fixture
def aufrufe():
    """Eine leere Liste, in der landet, was nach dem Handbuch aufgerufen wird."""
    return []


def _buch(fenster, level, aufrufe, **optionen):
    """Zeigt die Handbuchseite eines Levels und gibt den Screen zurück."""
    return fenster.zeige(handbuch.Handbuch, level=level, danach=aufrufe.append, **optionen)


def _alle_doppelseiten(screen):
    """Schlägt eine Doppelseite nach der anderen auf (ohne Umblättern) und gibt dabei ihre Nummer."""
    for nr in range(screen.anzahl_doppelseiten):
        screen.aufschlagen(nr, animiert=False)
        yield nr


def _warten(wurzel, bedingung, sekunden=3):
    """Lässt Tk arbeiten, bis ``bedingung()`` stimmt – etwa bis das Blatt umgeschlagen ist."""
    ende = time.monotonic() + sekunden
    while not bedingung():
        assert time.monotonic() < ende, "Das hat zu lange gedauert."
        wurzel.update()
        time.sleep(0.005)


def _eine_zeile(texte):
    """Texte zu einer Zeile zusammengezogen – so, wie man sie liest, egal wo umbrochen ist."""
    return " ".join(" ".join(texte).split())


#: Die Arten von Zeilen, die zum Fließtext des Kapitels gehören.
FLIESSTEXT = {"kapitel", "abschnitt", "absatz", "betont", "punkt", "tabellentitel", "merksatz_titel",
              "merksatz", "notiz"}


def _art(screen, element):
    """Die Textart eines Elements auf der Leinwand (Absatz, Überschrift …), sonst ``None``."""
    return next((tag for tag in screen.buch.gettags(element) if tag in FLIESSTEXT), None)


def _gelesen(screen):
    """Der Fließtext des Kapitels, wie er im Buch steht – Doppelseite für Doppelseite, links vor rechts.

    Die Seiten mit dem Werkzeug neben einem Beispiel zählen nicht mit: Das
    Werkzeug liegt dort neben jeder Seite des Beispiels noch einmal.
    """
    teile = []
    for nr in _alle_doppelseiten(screen):
        for seite, index in (("links", 2 * nr), ("rechts", 2 * nr + 1)):
            if index < len(screen.satz.seiten) and screen.satz.seiten[index].werkzeug is not None:
                continue
            teile.extend(screen.buch.itemcget(element, "text") for element in screen.buch.find_withtag(f"text&&{seite}")
                         if _art(screen, element))
    return _eine_zeile(teile)


def _erwartet(seite):
    """Der Fließtext eines Kapitels aus content/handbuch.py, in Lesereihenfolge."""
    teile = [seite.titel]
    for abschnitt in seite.abschnitte:
        teile.append(abschnitt.ueberschrift)
        for block in abschnitt.bloecke:
            if isinstance(block, buch.Absatz):
                teile.append(block.text)
            elif isinstance(block, buch.Aufzaehlung):
                teile.extend(block.punkte)
            elif isinstance(block, buch.Tabelle) and block.titel:
                teile.append(block.titel)
            elif isinstance(block, buch.VigenereQuadrat) and block.beschriftung:
                teile.append(block.beschriftung)
            elif isinstance(block, buch.Randnotiz):
                teile.append(block.text)
    return _eine_zeile(teile)


def _hat_quadrat(buchseite):
    """Steht auf dieser gesetzten Seite das Vigenère-Quadrat?"""
    return any(isinstance(s, buchsatz.Quadrat) for s in buchseite.stuecke)


def _quadrat(screen):
    """Das gesetzte Quadrat – es liegt neben mehreren Seiten, ist aber überall dasselbe."""
    (quadrat,) = {s for seite in screen.satz.seiten for s in seite.stuecke if isinstance(s, buchsatz.Quadrat)}
    return quadrat


def _hat_geheimtabelle(buchseite):
    """Steht auf dieser Seite die Tabelle mit der Zeile "Geheim"?"""
    zellen = {z for s in buchseite.stuecke if isinstance(s, buchsatz.Raster) for zeile in s.zeilen for z in zeile}
    return "Geheim" in zellen


def _aufschlagen_bei(screen, bedingung):
    """Schlägt die Doppelseite mit der ersten Seite auf, für die ``bedingung`` stimmt; gibt deren Nummer."""
    nummer = next(nr for nr, seite in enumerate(screen.satz.seiten) if bedingung(seite))
    screen.aufschlagen(nummer // 2, animiert=False)
    return nummer


def _zeilen_im_satz(screen, seite, *arten):
    """Die Texte bestimmter Art auf einer gesetzten Seite."""
    return [z.text for z in screen.satz.seiten[seite].stuecke if isinstance(z, buchsatz.Zeile) and z.art in arten]


# ── Was im Buch steht ──────────────────────────────────────────────────────

@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("level", LEVEL)
def test_das_kapitel_steht_vollstaendig_und_in_der_richtigen_reihenfolge_im_buch(fenster, aufrufe, level):
    """Jeder Absatz, jeder Punkt, jede Überschrift und Notiz – nichts fehlt, nichts doppelt, nichts vertauscht."""
    screen = _buch(fenster, level, aufrufe)
    assert _gelesen(screen) == _erwartet(screen.seite)


def test_das_buch_beginnt_mit_der_titelseite_und_dem_anfang_des_kapitels(fenster, aufrufe):
    screen = _buch(fenster, 1, aufrufe)
    assert screen.doppelseite == 0
    links = _eine_zeile(screen.texte("links"))
    assert _eine_zeile([buch.HANDBUCH_TITEL]) in links and "Inhalt" in links
    assert _eine_zeile(screen.texte("rechts")).startswith(buch.SEITE_CAESAR.titel)


@pytest.mark.parametrize("level", LEVEL)
def test_die_titelseite_nennt_zu_jedem_abschnitt_seine_seite(fenster, aufrufe, level):
    screen = _buch(fenster, level, aufrufe)
    eintraege = [screen.buch.itemcget(e, "text") for e in screen.buch.find_withtag("inhalt")]
    zahlen = [screen.buch.itemcget(e, "text") for e in screen.buch.find_withtag("inhalt_seite")]
    assert len(eintraege) == len(screen.seite.abschnitte) == len(zahlen)
    for (ueberschrift, nummer), eintrag, zahl in zip(screen.satz.inhalt, eintraege, zahlen):
        assert ueberschrift.startswith(eintrag.removesuffix(" …")) and zahl == str(nummer)
        screen.aufschlagen(nummer // 2, animiert=False)
        assert ueberschrift in _eine_zeile(screen.texte("links" if nummer % 2 == 0 else "rechts"))
        screen.aufschlagen(0, animiert=False)


@pytest.mark.parametrize("level", LEVEL)
def test_auf_der_titelseite_steht_der_stempel(fenster, aufrufe, level):
    screen = _buch(fenster, level, aufrufe)
    (stempel,) = screen.buch.find_withtag("stempel&&links")
    assert screen.buch.itemcget(stempel, "image") == str(screen.buch.stempelbild("stempel"))
    screen.aufschlagen(1, animiert=False)
    assert not screen.buch.find_withtag("stempel")


def test_die_seiten_sind_nummeriert(fenster, aufrufe):
    screen = _buch(fenster, 3, aufrufe)
    for nr in _alle_doppelseiten(screen):
        zahlen = [screen.buch.itemcget(e, "text") for e in screen.buch.find_withtag("seitenzahl")]
        assert zahlen == [f"– {n} –" for n in (2 * nr, 2 * nr + 1)
                          if 0 < n < len(screen.satz.seiten) and screen.satz.seiten[n].stuecke != _leer(screen)]


def _leer(screen):
    """Wie eine leere Seite aussieht – zum Vergleich mit dem, was im Buch steht."""
    x0, y0, x1, y1 = screen.flaeche("links")
    return buchsatz.leerseite(x1 - x0, y1 - y0, screen.px).stuecke


def test_eine_leere_letzte_seite_bekommt_eine_verzierung(fenster, aufrufe):
    screen = _buch(fenster, 1, aufrufe)
    screen.aufschlagen(screen.anzahl_doppelseiten - 1, animiert=False)
    ungerade = len(screen.satz.seiten) % 2
    assert bool(screen.buch.find_withtag("diamant&&rechts")) == bool(ungerade)
    assert bool(screen.texte("rechts")) != bool(ungerade)


def test_nummerierte_schritte_tragen_ihre_nummer(fenster, aufrufe):
    screen = _buch(fenster, 3, aufrufe)
    zeichen = [screen.buch.itemcget(e, "text") for _ in _alle_doppelseiten(screen)
               for e in screen.buch.find_withtag("zeichen")]
    assert zeichen == ["•", "•", "•", "1.", "2.", "3.", "4.", "1.", "2.", "3.", "4."]


def test_stichpunkte_bekommen_einen_punkt(fenster, aufrufe):
    screen = _buch(fenster, 2, aufrufe)
    zeichen = [screen.buch.itemcget(e, "text") for _ in _alle_doppelseiten(screen)
               for e in screen.buch.find_withtag("zeichen")]
    assert zeichen == ["•", "•", "•"]


@pytest.mark.parametrize("level", LEVEL)
def test_ergebnisse_und_beispiel_ueberschriften_sind_fett(fenster, aufrufe, level):
    screen = _buch(fenster, level, aufrufe)
    fett = []
    for _ in _alle_doppelseiten(screen):
        for element in screen.buch.find_withtag("betont"):
            assert screen.buch.itemcget(element, "font") == str(screen.schriften.betont)
            fett.append(screen.buch.itemcget(element, "text"))
    betonte = [block.text for a in screen.seite.abschnitte for block in a.bloecke
               if isinstance(block, buch.Absatz) and block.betont]
    assert betonte, f"Seite {level} hat keine betonte Zeile."
    assert _eine_zeile(fett) == _eine_zeile(betonte)


@pytest.mark.parametrize("level", LEVEL)
def test_der_merksatz_steht_auf_einer_karte(fenster, aufrufe, level):
    screen = _buch(fenster, level, aufrufe)
    karten = ()
    for _ in _alle_doppelseiten(screen):
        karten = screen.buch.find_withtag("karte")
        if karten:
            break
    (karte,) = karten
    assert screen.buch.itemcget(karte, "fill") == stil.FARBE_MERKSATZ
    x0, y0, x1, y1 = screen.buch.bbox(karte)
    zeilen = screen.buch.find_withtag("merksatz") + screen.buch.find_withtag("merksatz_titel")
    assert len(zeilen) >= 2
    for element in zeilen:
        a, b, c, d = screen.buch.bbox(element)
        assert x0 <= a and c <= x1 and y0 <= b and d <= y1


@pytest.mark.parametrize("level", LEVEL)
def test_bobs_randnotizen_stehen_in_handschrift_blau_und_etwas_schief(fenster, aufrufe, level):
    screen = _buch(fenster, level, aufrufe)
    notizen = []
    for _ in _alle_doppelseiten(screen):
        for element in screen.buch.find_withtag("notiz"):
            assert screen.buch.itemcget(element, "font") == str(screen.schriften.notiz)
            assert float(screen.buch.itemcget(element, "angle")) == buchsatz.NOTIZWINKEL
            assert screen.buch.itemcget(element, "fill") == stil.FARBE_KULI
            notizen.append(_eine_zeile([screen.buch.itemcget(element, "text")]))
    assert notizen == [block.text for a in screen.seite.abschnitte for block in a.bloecke
                       if isinstance(block, buch.Randnotiz)]


def test_die_notizen_stehen_in_einer_handschrift_wenn_der_rechner_eine_kennt(wurzel):
    familie = stil.erste_schrift(wurzel, stil.HANDSCHRIFTEN)
    schriften = buchsatz.schriften(wurzel, 1)
    if familie is None:
        assert schriften.notiz.actual("slant") == "italic"
    else:
        assert schriften.notiz.actual("family") == familie


def test_erste_schrift_nimmt_die_erste_die_es_gibt(wurzel):
    from tkinter import font as tkfont

    vorhanden = tkfont.families(wurzel)[0]
    assert stil.erste_schrift(wurzel, ("Gibt es nicht 1", vorhanden, "Gibt es nicht 2")) == vorhanden
    assert stil.erste_schrift(wurzel, ("Gibt es nicht",)) is None


# ── Tabellen und Quadrat ───────────────────────────────────────────────────

def _tabellen_pruefen(tabellen, teile):
    """Die Teile ergeben der Reihe nach genau die Tabellen – und jeder Teil ist beschriftet."""
    teile = list(teile)
    for tabelle in tabellen:
        zusammen = [[zeile[0]] for zeile in tabelle.zeilen]
        while len(zusammen[0]) < len(tabelle.zeilen[0]):
            teil = teile.pop(0)
            assert [_eine_zeile([z[0]]) for z in teil.zeilen] == [z[0] for z in tabelle.zeilen]
            for bisher, zeile in zip(zusammen, teil.zeilen):
                bisher.extend(zeile[1:])
        assert [tuple(z) for z in zusammen] == [tuple(z) for z in tabelle.zeilen]
    assert teile == []


@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("level", LEVEL)
def test_jede_tabelle_steht_vollstaendig_da_auch_wenn_sie_geteilt_ist(fenster, aufrufe, level):
    """Die Teile einer Tabelle ergeben zusammen genau ihre Zeilen – im Text und auf jeder Werkzeugseite."""
    screen = _buch(fenster, level, aufrufe)
    tabellen = [block for a in screen.seite.abschnitte for block in a.bloecke if isinstance(block, buch.Tabelle)]
    _tabellen_pruefen(tabellen, [s for seite in screen.satz.seiten if seite.werkzeug is None
                                 for s in seite.stuecke if isinstance(s, buchsatz.Raster)])
    for seite in screen.satz.seiten:
        if isinstance(seite.werkzeug, buch.Tabelle):
            _tabellen_pruefen([seite.werkzeug], [s for s in seite.stuecke if isinstance(s, buchsatz.Raster)])


def test_die_zellen_stehen_auch_auf_der_leinwand(fenster, aufrufe):
    """Der Satz kennt die Zellen – hier steht, dass sie auch gezeichnet werden, jede genau einmal."""
    screen = _buch(fenster, 2, aufrufe)
    nummer = _aufschlagen_bei(screen, _hat_geheimtabelle)
    seite = "links" if nummer % 2 == 0 else "rechts"
    gezeichnet = [screen.buch.itemcget(e, "text") for e in screen.buch.find_withtag(f"zelle&&{seite}")]
    erwartet = [zelle for stueck in screen.satz.seiten[nummer].stuecke
                if isinstance(stueck, buchsatz.Raster)
                for zeile in stueck.zeilen for zelle in zeile[1:]]
    assert sorted(gezeichnet) == sorted(erwartet)
    for zeile in buch.GEHEIMTABELLE.zeilen:
        for zelle in zeile[1:]:
            assert zelle in gezeichnet


def test_das_quadrat_steht_nur_in_level_3_und_dort_auf_seiten_fuer_sich(fenster, aufrufe):
    for level in (1, 2):
        screen = _buch(fenster, level, aufrufe)
        assert not any(isinstance(s, buchsatz.Quadrat) for seite in screen.satz.seiten for s in seite.stuecke)
    screen = _buch(fenster, 3, aufrufe)
    quadratseiten = [s for s in screen.satz.seiten if _hat_quadrat(s)]
    assert quadratseiten
    for quadratseite in quadratseiten:
        assert quadratseite.werkzeug is buch.QUADRAT
        assert {s.art for s in quadratseite.stuecke if isinstance(s, buchsatz.Zeile)} == {"tabellentitel",
                                                                                          "seitenzahl"}


def test_das_quadrat_stimmt_in_allen_676_feldern(fenster, aufrufe):
    """Gezeichnet aus derselben Formel wie crypto/ – kein abgetipptes Feld."""
    screen = _buch(fenster, 3, aufrufe)
    _aufschlagen_bei(screen, _hat_quadrat)
    quadrat = erzeuge_quadrat()
    for zeile, schluessel in enumerate(ALPHABET):
        for spalte, nachricht in enumerate(ALPHABET):
            assert screen.quadratfeld(schluessel, nachricht) == quadrat[zeile][spalte]


def test_das_quadrat_zeigt_das_beispiel_aus_dem_handbuch(fenster, aufrufe):
    screen = _buch(fenster, 3, aufrufe)
    _aufschlagen_bei(screen, _hat_quadrat)
    assert [screen.quadratfeld(s, n) for s, n in zip("ROTR", "HUND")] == list("YIGU")


def test_das_quadrat_ist_beschriftet(fenster, aufrufe):
    screen = _buch(fenster, 3, aufrufe)
    _aufschlagen_bei(screen, _hat_quadrat)
    leinwand = screen.buch
    kopfzeile = [leinwand.itemcget(e, "text") for e in leinwand.find_withtag("kopfzeile")]
    kopfspalte = [leinwand.itemcget(e, "text") for e in leinwand.find_withtag("kopfspalte")]
    assert "".join(kopfzeile) == ALPHABET == "".join(kopfspalte)
    assert len(leinwand.find_withtag("feld")) == 26 * 26


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_die_buchstaben_des_quadrats_passen_in_ihre_felder(fenster, aufrufe, massstab):
    """Sonst klebten die 676 Buchstaben aneinander – und niemand fände den Kreuzungspunkt."""
    screen = _buch(fenster, 3, aufrufe)
    _aufschlagen_bei(screen, _hat_quadrat)
    quadrat = _quadrat(screen)
    for element in screen.buch.find_withtag("feld") + screen.buch.find_withtag("kopfzeile"):
        x0, y0, x1, y1 = screen.buch.bbox(element)
        assert x1 - x0 <= quadrat.feld and y1 - y0 <= quadrat.feld, screen.buch.itemcget(element, "text")


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_die_felder_des_quadrats_sind_gross_genug_zum_lesen(fenster, aufrufe, massstab):
    """Auf dem 1080p-Schulmonitor mindestens 18 Pixel – mit diesem Quadrat wird gerechnet."""
    screen = _buch(fenster, 3, aufrufe)
    assert _quadrat(screen).feld >= (12 if massstab == 1 else 18)


# ── Beispiele: das Werkzeug gegenüber, der Schritt markiert ────────────────

def _beispiele(seite):
    """Die Abschnitte einer Handbuchseite, die ein Werkzeug daneben haben – mit ihrer Nummer."""
    return [(nr, a) for nr, a in enumerate(seite.abschnitte) if a.gegenueber is not None]


@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("level", LEVEL)
def test_neben_jedem_beispiel_liegt_sein_werkzeug(fenster, aufrufe, level):
    """Links das Beispiel, rechts die Tabelle oder das Quadrat – auf jeder Doppelseite, über die es läuft."""
    screen = _buch(fenster, level, aufrufe)
    seiten = screen.satz.seiten
    inhalt = dict(screen.satz.inhalt)
    for _, abschnitt in _beispiele(screen.seite):
        nummer = inhalt[abschnitt.ueberschrift]
        assert nummer % 2 == 0, f"{abschnitt.ueberschrift!r} beginnt auf einer rechten Seite"
        assert seiten[nummer + 1].werkzeug == abschnitt.gegenueber
    for nummer, seite in enumerate(seiten):
        if seite.schritte:
            assert nummer % 2 == 0 and seiten[nummer + 1].werkzeug is not None
        if seite.werkzeug is not None:
            assert nummer % 2 == 1 and seiten[nummer - 1].werkzeug is None
    # Alle Schritte stehen im Buch, jeder genau einmal.
    marken = [marke for seite in seiten for marke in seite.schritte]
    assert marken == [buchsatz.Schrittmarke(nr, i, schritt) for nr, a in _beispiele(screen.seite)
                      for i, schritt in enumerate(a.schritte)]


def test_auf_der_leinwand_liegt_das_werkzeug_rechts(fenster, aufrufe):
    for level, zellen in ((1, buch.ALPHABET_UM_3), (2, buch.GEHEIMTABELLE), (3, None)):
        screen = _buch(fenster, level, aufrufe)
        nummer = _aufschlagen_bei(screen, lambda seite: seite.schritte)
        assert nummer % 2 == 0
        if zellen is None:
            assert len(screen.buch.find_withtag("feld&&rechts")) == 26 * 26
        else:
            gezeichnet = [screen.buch.itemcget(e, "text") for e in screen.buch.find_withtag("zelle&&rechts")]
            assert sorted(gezeichnet) == sorted(z for zeile in zellen.zeilen for z in zeile[1:])


def _texte_in(leinwand, seite, rechtecke, waagrecht=False):
    """Die Texte auf der Seite, deren Mitte in einem der ``rechtecke`` liegt.

    Sortiert von oben nach unten – oder, ``waagrecht``, von links nach rechts:
    In einer Zeile des Quadrats steht der fette Kopfbuchstabe ein halbes
    Pixel anders als die übrigen.
    """
    gefunden = []
    for element in leinwand.find_withtag(seite):
        if leinwand.type(element) != "text":          # die Buchstaben des Quadrats sind auch Text
            continue
        a, b, c, d = leinwand.bbox(element)
        x, y = (a + c) / 2, (b + d) / 2
        if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in rechtecke):
            gefunden.append(((x, y) if waagrecht else (y, x), leinwand.itemcget(element, "text")))
    return [text for _, text in sorted(gefunden)]


def _schritttexte(buchseite, marke):
    """Was im Satz zu einem Schritt gehört: seine Zeilen – oder seine Spalte der Beispieltabelle."""
    texte = []
    for stueck in buchseite.stuecke:
        if isinstance(stueck, buchsatz.Zeile) and stueck.schritt == marke:
            texte.append(stueck.text)
        elif isinstance(stueck, buchsatz.Raster) and marke in stueck.schritte:
            texte.extend(zeile[1 + stueck.schritte.index(marke)] for zeile in stueck.zeilen)
    return texte


def _markierung_pruefen(screen, marke):
    """Links steht der Schritt unter Textmarker, rechts im Werkzeug ist markiert, wo er sucht und was er findet."""
    leinwand, schritt = screen.buch, marke.schritt
    werkzeug = screen.satz.seiten[2 * screen.doppelseite + 1].werkzeug
    (kreuzung,) = leinwand.find_withtag("kreuzung&&rechts")
    (rand,) = leinwand.find_withtag("kreuzungsrand&&rechts")
    feld = leinwand.coords(kreuzung)
    assert leinwand.coords(rand) == feld
    assert leinwand.itemcget(kreuzung, "fill") == stil.FARBE_KREUZUNG
    assert leinwand.itemcget(rand, "outline") == stil.FARBE_ROTSTIFT
    assert _texte_in(leinwand, "rechts", [feld]) == [schritt.kreuzung]
    baender = [e for e in leinwand.find_withtag("markierung&&rechts") if e not in (kreuzung, rand)]
    assert all(leinwand.itemcget(e, "fill") == stil.FARBE_MARKIERUNG for e in baender)
    baender = [leinwand.coords(e) for e in baender]
    # Markiert ist vom Kopf bis zum Kreuzungspunkt – und nicht weiter.
    (spalte,) = [band for band in baender if band[0] == feld[0] and band[2] == feld[2]]
    # Der Kreuzungspunkt ist genau ein Feld gross.
    rechts = screen.satz.seiten[2 * screen.doppelseite + 1]
    if isinstance(werkzeug, buch.VigenereQuadrat):
        assert feld[2] - feld[0] == feld[3] - feld[1] == _quadrat(screen).feld
    else:
        (teil,) = [s for s in rechts.stuecke if isinstance(s, buchsatz.Raster) and schritt.spalte in s.zeilen[0][1:]]
        zeile = next(nr for nr, reihe in enumerate(teil.zeilen)
                     if nr and reihe[1 + teil.zeilen[0][1:].index(schritt.spalte)] == schritt.kreuzung)
        assert (feld[2] - feld[0], feld[3] - feld[1]) == (teil.zellbreite, teil.zeilenhoehen[zeile])
    if isinstance(werkzeug, buch.VigenereQuadrat):
        quadrat = erzeuge_quadrat()
        z, s = ALPHABET.index(schritt.zeile), ALPHABET.index(schritt.spalte)
        assert _texte_in(leinwand, "rechts", [spalte]) == [schritt.spalte] + [quadrat[r][s] for r in range(z + 1)]
        (zeile,) = [band for band in baender if band is not spalte]
        assert _texte_in(leinwand, "rechts", [zeile], waagrecht=True) == [schritt.zeile] + list(quadrat[z][:s + 1])
    else:
        s = werkzeug.zeilen[0].index(schritt.spalte)
        z = next(nr for nr, reihe in enumerate(werkzeug.zeilen) if nr and reihe[s] == schritt.kreuzung)
        assert baender == [spalte]
        assert _texte_in(leinwand, "rechts", [spalte]) == [reihe[s] for reihe in werkzeug.zeilen[:z + 1]]
    # Links: der Textmarker liegt unter genau dem, was zu diesem Schritt gehört.
    buchseite = screen.satz.seiten[2 * screen.doppelseite]
    marker = [leinwand.coords(e) for e in leinwand.find_withtag("markierung&&links")]
    assert all(leinwand.itemcget(e, "fill") == stil.FARBE_MARKIERUNG for e in leinwand.find_withtag("markierung&&links"))
    assert sorted(_texte_in(leinwand, "links", marker)) == sorted(_schritttexte(buchseite, marke))


@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("level", LEVEL)
def test_jeder_schritt_markiert_im_werkzeug_zeile_spalte_und_kreuzungspunkt(fenster, aufrufe, level):
    screen = _buch(fenster, level, aufrufe)
    for _ in _alle_doppelseiten(screen):
        if not screen.schritte:
            assert screen.schritt is None and not screen.buch.find_withtag("markierung")
            continue
        assert screen.schritt == screen.schritte[0]                 # zu Beginn der erste
        for marke in screen.schritte:
            screen.schritt_zeigen(marke)
            assert screen.schritt == marke
            _markierung_pruefen(screen, marke)


def _schrittmitte(screen, marke):
    """Eine Stelle auf der Leinwand, an der der Schritt steht."""
    x0, y0, x1, y1 = screen._schrittflaechen["links"][marke][0]
    return (x0 + x1) // 2, (y0 + y1) // 2


@pytest.mark.parametrize("level", LEVEL)
def test_zeigt_die_maus_auf_einen_schritt_wird_er_markiert_und_bleibt_es(fenster, aufrufe, ausloesen, level):
    screen = _buch(fenster, level, aufrufe)
    nummer = _aufschlagen_bei(screen, lambda seite: len(seite.schritte) > 1)
    erster, letzter = screen.schritte[0], screen.schritte[-1]
    x, y = _schrittmitte(screen, letzter)
    assert screen.ziel(x, y) == letzter
    ausloesen(screen.buch, "<Motion>", x=x, y=y)
    assert screen.schritt == letzter and screen.buch.cget("cursor") == "hand2"
    _markierung_pruefen(screen, letzter)
    ausloesen(screen.buch, "<Leave>")
    assert screen.schritt == letzter and screen.buch.cget("cursor") == ""
    _markierung_pruefen(screen, letzter)
    # Ein Klick tut dasselbe – geblättert wird davon nicht.
    x, y = _schrittmitte(screen, erster)
    ausloesen(screen.buch, "<Button-1>", x=x, y=y)
    assert screen.schritt == erster and screen.doppelseite == nummer // 2
    _markierung_pruefen(screen, erster)


def test_neben_einem_schritt_ist_kein_schritt(fenster, aufrufe):
    screen = _buch(fenster, 3, aufrufe)
    _aufschlagen_bei(screen, lambda seite: seite.schritte)
    x0, y0, x1, y1 = screen.flaeche("links")
    assert screen.ziel(x0 + 1, y0 + 1) is None                      # die Überschrift oben ist kein Schritt
    assert screen.ziel(*_mitte(buchleinwand.TEXT_RECHTS, screen)) is None
    screen.schritt_zeigen(screen.schritte[1])
    screen._maus_ueber(None)
    assert screen.schritt == screen.schritte[1]


@pytest.mark.parametrize("level", LEVEL)
def test_die_pfeiltasten_hoch_und_runter_gehen_die_schritte_durch(fenster, aufrufe, ausloesen, level):
    screen = _buch(fenster, level, aufrufe)
    nummer = _aufschlagen_bei(screen, lambda seite: seite.schritte)
    schritte = screen.schritte
    for erwartet in schritte[1:]:
        ausloesen(screen.buch, "<Down>")
        assert screen.schritt == erwartet
    assert screen.schritt_weiter(1) is False and screen.schritt == schritte[-1]
    ausloesen(screen.buch, "<Up>")
    assert screen.schritt == schritte[-2]
    screen.schritt_zeigen(schritte[0])
    assert screen.schritt_weiter(-1) is False and screen.schritt == schritte[0]
    assert screen.doppelseite == nummer // 2                        # geblättert wird davon nicht
    _markierung_pruefen(screen, schritte[0])


def test_ein_schritt_von_einer_anderen_doppelseite_wird_nicht_markiert(fenster, aufrufe):
    screen = _buch(fenster, 3, aufrufe)
    alle = [marke for seite in screen.satz.seiten for marke in seite.schritte]
    _aufschlagen_bei(screen, lambda seite: seite.schritte)
    fremd = next(marke for marke in alle if marke not in screen.schritte)
    assert screen.schritt_zeigen(fremd) is False
    assert screen.schritt == screen.schritte[0]
    assert screen.schritt_zeigen(screen.schritte[0]) is False           # schon markiert


def test_ohne_beispiel_gibt_es_nichts_zu_markieren(fenster, aufrufe, ausloesen):
    screen = _buch(fenster, 1, aufrufe)
    assert screen.schritte == () and screen.schritt is None
    ausloesen(screen.buch, "<Down>")
    assert screen.schritt_weiter(1) is False
    assert not screen.buch.find_withtag("markierung")


def _markierung_der_doppelseite_pruefen(screen):
    """Prüft, dass auf der offenen Doppelseite der erste Schritt markiert ist – und sonst nichts."""
    if screen.schritte:
        assert screen.schritt == screen.schritte[0]
        _markierung_pruefen(screen, screen.schritt)
    else:
        assert screen.schritt is None and not screen.buch.find_withtag("markierung")


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_nach_dem_umblaettern_ist_der_erste_schritt_der_neuen_seite_markiert(fenster, aufrufe, wurzel):
    screen = _buch(fenster, 3, aufrufe)
    nummer = _aufschlagen_bei(screen, lambda seite: seite.schritte)
    screen.schritt_zeigen(screen.schritte[-1])
    screen.aufschlagen(nummer // 2 - 1, animiert=False)
    _markierung_der_doppelseite_pruefen(screen)
    screen.aufschlagen(nummer // 2, animiert=False)
    _markierung_der_doppelseite_pruefen(screen)
    # Mit Umschlagen: Links liegt noch die alte Seite, aber ihre Schritte zählen nicht mehr.
    x, y = _schrittmitte(screen, screen.schritte[0])
    assert screen.blaettern(1) is True and screen.blaettert
    assert screen.ziel(x, y) is None
    assert not screen.buch.find_withtag("markierung&&links")
    _warten(wurzel, lambda: not screen.blaettert)
    _markierung_der_doppelseite_pruefen(screen)
    assert screen.blaettern(-1) is True
    _warten(wurzel, lambda: not screen.blaettert)
    _markierung_der_doppelseite_pruefen(screen)


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_die_pfeiltasten_hoch_und_runter_gehen_auch_waehrend_das_blatt_umschlaegt(fenster, aufrufe, wurzel,
                                                                                  ausloesen):
    """Links liegt dann noch die alte Seite – markiert wird trotzdem nur, was auf die neue gehört."""
    screen = _buch(fenster, 3, aufrufe)
    mit_schritten = [nr // 2 for nr, seite in enumerate(screen.satz.seiten) if seite.schritte]
    screen.aufschlagen(mit_schritten[-1] - 1, animiert=False)
    assert screen.blaettern(1) is True and screen.blaettert
    ausloesen(screen.buch, "<Down>")
    assert screen.schritt == screen.schritte[1]
    assert not screen.buch.find_withtag("markierung&&links")
    _warten(wurzel, lambda: not screen.blaettert)
    _markierung_pruefen(screen, screen.schritte[1])


@pytest.mark.parametrize("level", LEVEL)
def test_der_textmarker_liegt_unter_der_schrift_und_auf_dem_papier(fenster, aufrufe, level):
    screen = _buch(fenster, level, aufrufe)
    _aufschlagen_bei(screen, lambda seite: seite.schritte)
    leinwand = screen.buch
    stapel = leinwand.find_all()

    def lage(auswahl):
        """Die Plätze der ausgewählten Elemente im Stapel der Leinwand – wer liegt über wem?"""
        return [stapel.index(e) for e in leinwand.find_withtag(auswahl)]

    assert leinwand.type(stapel[0]) == "image"                                  # ganz unten das Buch
    links = lage("markierung&&links")
    assert links and 0 < min(links) and max(links) < min(lage("text&&links"))
    rechts = [i for i in lage("markierung&&rechts") if "kreuzungsrand" not in leinwand.gettags(stapel[i])]
    buchstaben = "(kopfzeile||kopfspalte||feld)&&rechts" if level == 3 else "text&&rechts"
    assert rechts and max(rechts) < min(lage(buchstaben))
    if level == 3:
        # Über dem dunkleren Grund von Kopfzeile und Kopfspalte – der Kopf ist mit markiert.
        kopfgrund = [i for i in lage("rechts") if leinwand.type(stapel[i]) == "rectangle"
                     and leinwand.itemcget(stapel[i], "fill") == stil.FARBE_PAPIER_DUNKEL]
        assert kopfgrund and max(kopfgrund) < min(rechts)
    # Der rote Rand des Kreuzungspunkts liegt obenauf, über den Linien.
    (rand,) = lage("kreuzungsrand")
    assert rand > max(i for i in lage("rechts") if leinwand.type(stapel[i]) == "line")


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_der_textmarker_steht_nicht_ueber_die_textflaeche_hinaus(fenster, aufrufe):
    """Eine Zeile, die vom linken bis zum rechten Rand reicht, wird nur bis zum Rand markiert."""
    screen = _buch(fenster, 1, aufrufe)
    x0, y0, x1, y1 = screen.flaeche("links")
    schrift = screen.schriften.text
    marke = buchsatz.Schrittmarke(0, 0, buch.Schritt(spalte="A", kreuzung="B"))
    ganz_links = buchsatz.Zeile(0, 0, "Wort", "text", stil.FARBE_TINTE, "punkt", schritt=marke)
    ganz_rechts = buchsatz.Zeile(x1 - x0 - schrift.measure("Wort"), 40, "Wort", "text", stil.FARBE_TINTE, "punkt",
                                 schritt=marke)
    ((links, _, _, _), (_, _, rechts, _)) = screen.buch.schrittflaechen("links", (ganz_links, ganz_rechts))[marke]
    assert links == x0 and rechts == x1


# ── Alles auf dem Papier ───────────────────────────────────────────────────

def _ueberlappen(a, b, luft=1):
    """Überschneiden sich zwei Rechtecke (x0, y0, x1, y1)? Eine Linie Luft zählt nicht."""
    return a[0] + luft < b[2] and b[0] + luft < a[2] and a[1] + luft < b[3] and b[1] + luft < a[3]


@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("level", LEVEL)
def test_nichts_ragt_ueber_die_textflaeche_und_kein_text_liegt_auf_einem_anderen(fenster, aufrufe, level):
    screen = _buch(fenster, level, aufrufe)
    luft = 2          # um Text rechnet Tk einen Pixel Rand
    for nr in _alle_doppelseiten(screen):
        for seite in ("links", "rechts"):
            x0, y0, x1, y1 = screen.flaeche(seite)
            texte = []
            for element in screen.buch.find_withtag(seite):
                tags = screen.buch.gettags(element)
                if "seitenzahl" in tags:
                    continue
                a, b, c, d = screen.buch.bbox(element)
                text = screen.buch.itemcget(element, "text") if "text" in tags else ""
                assert x0 - luft <= a and c <= x1 + luft and y0 - luft <= b and d <= y1 + luft, (
                    f"Doppelseite {nr}, {seite}: {tags} {text!r} liegt bei {(a, b, c, d)}, "
                    f"die Textfläche ist {(x0, y0, x1, y1)}")
                if _art(screen, element) or {"beschriftung", "zelle"} & set(tags):
                    texte.append((text, (a, b, c, d)))
            for i, (text_a, kasten_a) in enumerate(texte):
                for text_b, kasten_b in texte[i + 1:]:
                    assert not _ueberlappen(kasten_a, kasten_b), f"{text_a!r} liegt auf {text_b!r}"


def _rendern():
    """Lädt ``grafik/rendern.py`` nach – es gehört zu keinem Paket und lässt sich nicht einfach importieren."""
    spec = importlib.util.spec_from_file_location("rendern", PROJEKT / "grafik" / "rendern.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_die_textflaechen_liegen_auf_dem_papier_des_buchbilds(massstab):
    """ui/handbuch.py und grafik/buch_zeichnen.py müssen dieselben Flächen meinen.

    Geprüft wird im fertigen Bild: Überall auf den Textflächen ist helles,
    gelbliches Papier – keine Kante, kein Fleck, kein Einband. Links neben dem
    Buch ist Nachthimmel.
    """
    ordner = animation.ANIMATIONSORDNER / "buch" / animation.unterordner(massstab)
    bild = _rendern().png_lesen((ordner / "hintergrund.png").read_bytes())

    def farbe(x, y):
        """Die Farbe eines Bildpunkts im gerenderten Bild (Rot, Grün, Blau)."""
        return tuple(bild.zeilen[y][x * bild.kanaele:x * bild.kanaele + 3])

    for flaeche in (buchleinwand.TEXT_LINKS, buchleinwand.TEXT_RECHTS):
        x0, y0, x1, y1 = (stil.skaliert(wert, massstab) for wert in flaeche)
        for i in range(11):
            for j in range(11):
                r, g, b = farbe(x0 + (x1 - 1 - x0) * i // 10, y0 + (y1 - 1 - y0) * j // 10)
                assert r >= 200 and g >= 180 and b >= 140 and r - b >= 25, (r, g, b)
    assert max(farbe(stil.skaliert(5, massstab), stil.skaliert(240, massstab))) < 60


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_das_buch_passt_ins_fenster_auch_mit_hinweis_und_langem_einstieg(fenster, aufrufe, wurzel, platz):
    _buch(fenster, 2, aufrufe, einleitung=story.EINSTIEG_LEVEL_2.absaetze,
          hinweis="Die Zeit für Level 1 ist abgelaufen – weiter geht es mit Level 2.")
    wurzel.update_idletasks()
    assert wurzel.winfo_reqwidth() <= platz[0]
    assert wurzel.winfo_reqheight() <= platz[1]


def test_im_kleinen_massstab_ist_der_text_darueber_so_breit_wie_das_buch(fenster, aufrufe):
    screen = _buch(fenster, 2, aufrufe, einleitung=story.EINSTIEG_LEVEL_2.absaetze)
    (zeile,) = screen._einleitung
    assert int(zeile.cget("wraplength")) == screen.buch.winfo_reqwidth()


@pytest.mark.parametrize("massstab", [1.5])
def test_im_grossen_massstab_darf_der_text_darueber_breiter_werden(fenster, aufrufe):
    """Auf dem 1080p-Monitor ist neben dem Buch Platz – und in der Höhe zählt jede Zeile."""
    screen = _buch(fenster, 2, aufrufe, einleitung=story.EINSTIEG_LEVEL_2.absaetze)
    (zeile,) = screen._einleitung
    assert int(zeile.cget("wraplength")) > screen.buch.winfo_reqwidth()


# ── Blättern ───────────────────────────────────────────────────────────────

def _mitte(bereich, screen):
    """Der Mittelpunkt eines Bereichs, schon im Maßstab des Screens."""
    x0, y0, x1, y1 = (screen.px(wert) for wert in bereich)
    return (x0 + x1) // 2, (y0 + y1) // 2


def test_die_knoepfe_blaettern_und_sind_am_ende_gesperrt(fenster, aufrufe, wurzel):
    screen = _buch(fenster, 3, aufrufe)
    letzte = screen.anzahl_doppelseiten - 1
    assert screen._zurueckblaettern.cget("state") == "disabled"
    assert screen.seitenanzeige == f"Doppelseite 1 von {letzte + 1}"
    screen._vorblaettern.invoke()
    assert screen.doppelseite == 1 and screen.seitenanzeige == f"Doppelseite 2 von {letzte + 1}"
    assert screen._zurueckblaettern.cget("state") == "normal"
    _warten(wurzel, lambda: not screen.blaettert)
    screen.aufschlagen(letzte, animiert=False)
    assert screen._vorblaettern.cget("state") == "disabled"
    assert screen.blaettern(1) is False and screen.doppelseite == letzte
    screen._zurueckblaettern.invoke()
    assert screen.doppelseite == letzte - 1
    assert screen.blaettern(-99) is False


@pytest.mark.parametrize("taste, richtung", [("<Right>", 1), ("<Next>", 1), ("<Left>", -1), ("<Prior>", -1)])
def test_die_pfeiltasten_und_bild_auf_ab_blaettern(fenster, aufrufe, ausloesen, taste, richtung):
    screen = _buch(fenster, 3, aufrufe)
    screen.aufschlagen(1, animiert=False)
    ausloesen(screen.buch, taste)
    assert screen.doppelseite == 1 + richtung


@pytest.mark.parametrize("sequenz, delta, richtung",
                         [("<MouseWheel>", -120, 1), ("<MouseWheel>", 120, -1), ("<MouseWheel>", -3, 1),
                          ("<Button-5>", 0, 1), ("<Button-4>", 0, -1)])
def test_das_mausrad_blaettert(fenster, aufrufe, ausloesen, sequenz, delta, richtung):
    screen = _buch(fenster, 3, aufrufe)
    screen.aufschlagen(1, animiert=False)
    ausloesen(screen.buch, sequenz, delta=delta)
    assert screen.doppelseite == 1 + richtung


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_ein_klick_auf_die_hochgebogenen_ecken_blaettert(fenster, aufrufe, ausloesen, wurzel):
    screen = _buch(fenster, 3, aufrufe)
    x, y = _mitte(handbuch.ECKE_RECHTS, screen)
    ausloesen(screen.buch, "<Button-1>", x=x, y=y)
    assert screen.doppelseite == 1
    _warten(wurzel, lambda: not screen.blaettert)
    x, y = _mitte(handbuch.ECKE_LINKS, screen)
    ausloesen(screen.buch, "<Button-1>", x=x, y=y)
    assert screen.doppelseite == 0


def test_ein_klick_mitten_auf_die_seite_blaettert_nicht(fenster, aufrufe):
    screen = _buch(fenster, 3, aufrufe)
    screen.klicken(*_mitte(buchleinwand.TEXT_RECHTS, screen))
    assert screen.doppelseite == 0


def test_der_zeiger_zeigt_wo_man_klicken_kann(fenster, aufrufe):
    screen = _buch(fenster, 3, aufrufe)
    assert screen.ziel(*_mitte(handbuch.ECKE_RECHTS, screen)) == "vor"
    assert screen.ziel(*_mitte(handbuch.ECKE_LINKS, screen)) is None       # vor der Titelseite ist nichts
    screen.aufschlagen(screen.anzahl_doppelseiten - 1, animiert=False)
    assert screen.ziel(*_mitte(handbuch.ECKE_RECHTS, screen)) is None      # hinter der letzten auch nicht
    assert screen.ziel(*_mitte(handbuch.ECKE_LINKS, screen)) == "zurueck"
    screen.aufschlagen(0, animiert=False)
    assert screen.ziel(*_mitte(buchleinwand.TEXT_LINKS, screen)) is None
    screen._maus_ueber("vor")
    assert screen.buch.cget("cursor") == "hand2" and screen.buch.find_withtag("maus")
    screen._maus_ueber(None)
    assert screen.buch.cget("cursor") == "" and not screen.buch.find_withtag("maus")


def test_das_buch_bekommt_den_fokus_fuer_die_pfeiltasten(fenster, aufrufe, monkeypatch):
    """Ein verstecktes Fenster bekommt von Tk keinen Fokus – deshalb wird nachgesehen, wem er gegeben wird."""
    bekommen = []
    monkeypatch.setattr(animation.Buehne, "focus_set", lambda leinwand: bekommen.append(leinwand))
    screen = _buch(fenster, 1, aufrufe)
    assert bekommen == [screen.buch]
    screen._vorblaettern.invoke()                  # nach einem Knopf gleich wieder
    assert bekommen == [screen.buch, screen.buch]
    assert str(screen.buch.cget("takefocus")) == "1"


# ── Umblättern ─────────────────────────────────────────────────────────────

def test_die_bilder_des_umblaetterns_werden_erst_nach_dem_aufschlagen_geladen(fenster, aufrufe, wurzel):
    screen = _buch(fenster, 1, aufrufe)
    assert screen._ablauf is None
    _warten(wurzel, lambda: screen._ablauf is not None)


def test_vorwaerts_liegt_die_neue_rechte_seite_unter_dem_blatt_das_umschlaegt(fenster, aufrufe, wurzel):
    screen = _buch(fenster, 1, aufrufe)
    alt_links = screen.texte("links")
    assert screen.blaettern(1) is True
    assert screen.blaettert
    (blatt,) = screen.buch.find_withtag(animation.Ablauf.TAG)
    assert screen.buch.find_all()[-1] == blatt                       # das Blatt liegt über allem
    ((_, folge),) = screen._ablauf.bilder
    assert screen.buch.itemcget(blatt, "image") == str(folge[0])     # es liegt noch flach auf der rechten Seite
    assert screen.aufschlagen(0, animiert=False) is False           # kein zweites Mal, solange es umschlägt
    assert screen.doppelseite == 1
    assert screen.texte("links") == alt_links                       # links noch die alte Seite …
    assert _zeilen_im_satz(screen, 3, *FLIESSTEXT)[0] in screen.texte("rechts")   # … rechts schon die neue
    _warten(wurzel, lambda: not screen.blaettert)
    assert not screen.buch.find_withtag(animation.Ablauf.TAG)
    assert _zeilen_im_satz(screen, 2, *FLIESSTEXT)[0] in screen.texte("links")


def test_rueckwaerts_liegt_die_neue_linke_seite_zuerst_darunter(fenster, aufrufe, wurzel):
    screen = _buch(fenster, 1, aufrufe)
    screen.aufschlagen(1, animiert=False)
    alt_rechts = screen.texte("rechts")
    assert screen.blaettern(-1) is True
    (blatt,) = screen.buch.find_withtag(animation.Ablauf.TAG)
    ((_, folge),) = screen._ablauf.bilder
    assert screen.buch.itemcget(blatt, "image") == str(folge[-1])    # rückwärts: erst liegt es links
    assert screen.texte("rechts") == alt_rechts
    assert _eine_zeile([buch.HANDBUCH_TITEL]) in _eine_zeile(screen.texte("links"))
    _warten(wurzel, lambda: not screen.blaettert)
    assert _eine_zeile(screen.texte("rechts")).startswith(buch.SEITE_CAESAR.titel)


def test_waehrend_es_umschlaegt_wird_nicht_noch_einmal_geblaettert(fenster, aufrufe, wurzel, ausloesen):
    """Ein schnell gedrehtes Mausrad blättert nicht fünf Seiten auf einmal."""
    screen = _buch(fenster, 3, aufrufe)
    screen.blaettern(1)
    for _ in range(4):
        ausloesen(screen.buch, "<MouseWheel>", delta=-120)
    assert screen.doppelseite == 1
    _warten(wurzel, lambda: not screen.blaettert)
    assert screen.blaettern(1) and screen.doppelseite == 2


def test_die_bilder_werden_nur_einmal_geladen(fenster, aufrufe, monkeypatch):
    """Das Handbuch wird oft aufgeschlagen – die grossen Bilder bleiben im Fenster."""
    geladen = []
    original = animation._folge_laden
    monkeypatch.setattr(animation, "_folge_laden", lambda *werte: geladen.append(1) or original(*werte))
    erstes = _buch(fenster, 1, aufrufe)._umblaettern()
    zweites = _buch(fenster, 2, aufrufe)._umblaettern()
    assert len(geladen) == 1
    assert zweites.bilder is erstes.bilder


def test_ohne_bilder_wird_eben_ohne_umschlagen_geblaettert(fenster, aufrufe, monkeypatch):
    def laden(name, **optionen):
        """Lädt Animationen wie sonst – nur die Umblätter-Bilder gibt es hier nicht."""
        if name == "umblaettern":
            raise FileNotFoundError(name)
        return animation.Animation(name, **optionen)

    monkeypatch.setattr(handbuch, "Animation", laden)
    screen = _buch(fenster, 1, aufrufe)
    assert screen.blaettern(1) is True
    assert not screen.blaettert and screen.doppelseite == 1
    assert _zeilen_im_satz(screen, 2, *FLIESSTEXT)[0] in screen.texte("links")


def test_wer_mitten_im_umblaettern_weitergeht_hinterlaesst_nichts(fenster, aufrufe, wurzel):
    """Sonst liefe der Takt des Umblätterns nach dem Abriss ins Leere – mitten in der nächsten Aufgabe."""
    screen = _buch(fenster, 1, aufrufe)
    screen.blaettern(1)
    blatt = screen._ablauf
    auftrag = blatt._auftrag
    assert auftrag in wurzel.tk.call("after", "info")
    _buch(fenster, 2, aufrufe)                          # der alte Screen wird abgerissen
    assert not blatt.laeuft and blatt._auftrag is None
    assert auftrag not in wurzel.tk.call("after", "info")
    ende = time.monotonic() + 0.4
    while time.monotonic() < ende:
        wurzel.update()
        time.sleep(0.01)
    assert fenster.meldung == ""


# ── Knopf, Einleitung, Hinweis ─────────────────────────────────────────────

def test_der_knopf_fuehrt_weiter(fenster, aufrufe, ausloesen):
    screen = _buch(fenster, 1, aufrufe)
    assert screen.knopftext == handbuch.KNOPF_WEITER
    screen._knopf.invoke()
    ausloesen(screen._knopf, "<Return>")
    assert aufrufe == [fenster, fenster]


def test_einleitung_und_hinweis_stehen_ueber_dem_buch(fenster, aufrufe):
    screen = _buch(fenster, 2, aufrufe, einleitung=story.EINSTIEG_LEVEL_2.absaetze, hinweis="Zeit um.")
    assert screen.einleitung == story.EINSTIEG_LEVEL_2.absaetze
    assert screen.hinweis == "Zeit um."
    reihenfolge = screen.pack_slaves()
    assert (reihenfolge.index(screen._hinweis) < reihenfolge.index(screen._einleitung[0])
            < reihenfolge.index(screen.buch))


def test_ohne_einleitung_und_hinweis_steht_nichts_darueber(fenster, aufrufe):
    screen = _buch(fenster, 1, aufrufe)
    assert screen.einleitung == () and screen.hinweis == ""
    assert screen.pack_slaves()[0] is screen.buch


def test_die_kopfzeile_nennt_das_level(fenster, aufrufe):
    assert _buch(fenster, 3, aufrufe).titel == "Handbuch – Level 3"


# ── Im Spielablauf ─────────────────────────────────────────────────────────

def _nachlese_durchklicken(fenster):
    """Klickt die Funksprüche weg, die nach einem Zeitablauf zum Mitlesen dastehen (ui/ablauf.py)."""
    while isinstance(fenster.aktueller_screen, funk.Funk) and fenster.aktueller_screen.nur_lesen:
        fenster.aktueller_screen.weiter()
    return fenster.aktueller_screen


def _bis_zum_handbuch(fenster):
    """Klickt sich vom Startbildschirm bis zur Handbuchseite von Level 1 durch."""
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
    assert isinstance(fenster.aktueller_screen, uebung.Uebung)
    assert fenster.durchlauf.spielstand.aktuelle_aufgabe is not None


def test_nach_einem_levelwechsel_liegt_die_naechste_seite_auf(fenster):
    _bis_zum_handbuch(fenster)
    fenster.durchlauf.naechstes_level()
    screen = _nachlese_durchklicken(fenster)
    assert isinstance(screen, handbuch.Handbuch)
    assert screen.seite is buch.SEITE_SUBSTITUTION
    assert screen.einleitung == story.EINSTIEG_LEVEL_2.absaetze
    assert screen.hinweis == ""                            # vorzeitig beendet, nicht abgelaufen


def test_ist_die_zeit_abgelaufen_sagt_das_buch_es(fenster, uhr):
    from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN

    _bis_zum_handbuch(fenster)
    uhr.jetzt += DAUER_JE_LEVEL_SEKUNDEN[1]
    fenster._takt()
    screen = _nachlese_durchklicken(fenster)
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
    assert isinstance(fenster.aktueller_screen, uebung.Uebung)
    assert stand.aktuelle_aufgabe is aufgabe
    assert len(stand.erledigte_aufgaben) == 0
    assert fenster.aktueller_screen.aufgabe is aufgabe
    stand.versuchen(aufgabe.loesung)
    fenster.durchlauf.aufgabe_abschliessen()
    assert round(stand.erledigte_aufgaben[0].benoetigte_sekunden) == 40


def test_nachschlagen_im_naechsten_level_zeigt_dessen_seite(fenster):
    _bis_zum_handbuch(fenster)
    fenster.durchlauf.naechstes_level()
    _nachlese_durchklicken(fenster)
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
    screen = _nachlese_durchklicken(fenster)
    assert screen.seite is buch.SEITE_SUBSTITUTION
    assert screen.knopftext == handbuch.KNOPF_WEITER       # kein "Zurück zur Aufgabe" mehr
    assert fenster.durchlauf.spielstand.erledigte_aufgaben[0].abgebrochen
