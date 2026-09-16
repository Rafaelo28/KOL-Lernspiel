"""Tests für den Handbuch-Screen (Arbeitsplan 6.4): ui/handbuch.py.

Das Handbuch ist ein aufgeschlagenes Buch. Geprüft wird, dass jedes Kapitel
vollständig und in der richtigen Reihenfolge im Buch steht – Text,
Tabellen, Merksatz, Randnotizen, auf Seite 3 das Quadrat –, dass nichts über
die Seiten hinausragt, dass sich blättern lässt (Knöpfe, Tasten, Mausrad,
Ecken), dass dabei ein Blatt umschlägt, und dass man mitten in
einer Übung nachschlagen und zur selben Übung zurückkehren kann
(Arbeitsplan 6.4: "Muss während der Aufgaben erreichbar bleiben").

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
from ui import ablauf, animation, buchleinwand, buchsatz, handbuch, stil, uebung  # noqa: E402

LEVEL = (1, 2, 3)
PROJEKT = Path(__file__).resolve().parent.parent


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


def _buch(fenster, level, aufrufe, **optionen):
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
    return next((tag for tag in screen.buch.gettags(element) if tag in FLIESSTEXT), None)


def _gelesen(screen):
    """Der Fließtext des Kapitels, wie er im Buch steht – Doppelseite für Doppelseite, links vor rechts."""
    teile = []
    for _ in _alle_doppelseiten(screen):
        teile.extend(screen.buch.itemcget(element, "text") for element in screen.buch.find_withtag("text")
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
    return any(isinstance(s, buchsatz.Quadrat) for s in buchseite.stuecke)


def _hat_geheimtabelle(buchseite):
    zellen = {z for s in buchseite.stuecke if isinstance(s, buchsatz.Raster) for zeile in s.zeilen for z in zeile}
    return "Geheim" in zellen


def _aufschlagen_bei(screen, bedingung):
    """Schlägt die Doppelseite mit der ersten Seite auf, für die ``bedingung`` stimmt; gibt deren Nummer."""
    nummer = next(nr for nr, seite in enumerate(screen.satz.seiten) if bedingung(seite))
    screen.aufschlagen(nummer // 2, animiert=False)
    return nummer


def _zeilen_im_satz(screen, seite, *arten):
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
        assert zahlen == [f"– {n} –" for n in (2 * nr, 2 * nr + 1) if 0 < n < len(screen.satz.seiten)]


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

@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("level", LEVEL)
def test_jede_tabelle_steht_vollstaendig_da_auch_wenn_sie_geteilt_ist(fenster, aufrufe, level):
    """Die Teile einer Tabelle ergeben zusammen genau ihre Zeilen – und jeder Teil ist beschriftet."""
    screen = _buch(fenster, level, aufrufe)
    tabellen = [block for a in screen.seite.abschnitte for block in a.bloecke if isinstance(block, buch.Tabelle)]
    teile = [s for seite in screen.satz.seiten for s in seite.stuecke if isinstance(s, buchsatz.Raster)]
    for tabelle in tabellen:
        zusammen = [[zeile[0]] for zeile in tabelle.zeilen]
        while len(zusammen[0]) < len(tabelle.zeilen[0]):
            teil = teile.pop(0)
            assert [_eine_zeile([z[0]]) for z in teil.zeilen] == [z[0] for z in tabelle.zeilen]
            for bisher, zeile in zip(zusammen, teil.zeilen):
                bisher.extend(zeile[1:])
        assert [tuple(z) for z in zusammen] == [tuple(z) for z in tabelle.zeilen]
    assert teile == []


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


def test_das_quadrat_steht_nur_in_level_3_und_dort_auf_einer_seite_fuer_sich(fenster, aufrufe):
    for level in (1, 2):
        screen = _buch(fenster, level, aufrufe)
        assert not any(isinstance(s, buchsatz.Quadrat) for seite in screen.satz.seiten for s in seite.stuecke)
    screen = _buch(fenster, 3, aufrufe)
    (quadratseite,) = [s for s in screen.satz.seiten if any(isinstance(t, buchsatz.Quadrat) for t in s.stuecke)]
    assert {s.art for s in quadratseite.stuecke if isinstance(s, buchsatz.Zeile)} == {"tabellentitel", "seitenzahl"}


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
    (quadrat,) = [s for seite in screen.satz.seiten for s in seite.stuecke if isinstance(s, buchsatz.Quadrat)]
    for element in screen.buch.find_withtag("feld") + screen.buch.find_withtag("kopfzeile"):
        x0, y0, x1, y1 = screen.buch.bbox(element)
        assert x1 - x0 <= quadrat.feld and y1 - y0 <= quadrat.feld, screen.buch.itemcget(element, "text")


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_die_felder_des_quadrats_sind_gross_genug_zum_lesen(fenster, aufrufe, massstab):
    """Auf dem 1080p-Schulmonitor mindestens 18 Pixel – mit diesem Quadrat wird gerechnet."""
    screen = _buch(fenster, 3, aufrufe)
    (quadrat,) = [s for seite in screen.satz.seiten for s in seite.stuecke if isinstance(s, buchsatz.Quadrat)]
    assert quadrat.feld >= (12 if massstab == 1 else 18)


# ── Alles auf dem Papier ───────────────────────────────────────────────────

def _ueberlappen(a, b, luft=1):
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
    assert isinstance(fenster.aktueller_screen, uebung.Uebung)
    assert fenster.durchlauf.spielstand.aktuelle_aufgabe is not None


def test_nach_einem_levelwechsel_liegt_die_naechste_seite_auf(fenster):
    _bis_zum_handbuch(fenster)
    fenster.durchlauf.naechstes_level()
    screen = fenster.aktueller_screen
    assert isinstance(screen, handbuch.Handbuch)
    assert screen.seite is buch.SEITE_SUBSTITUTION
    assert screen.einleitung == story.EINSTIEG_LEVEL_2.absaetze
    assert screen.hinweis == ""                            # vorzeitig beendet, nicht abgelaufen


def test_ist_die_zeit_abgelaufen_sagt_das_buch_es(fenster, uhr):
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
