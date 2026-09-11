"""Tests für grafik/rendern.py – das Werkzeug, das Animationen vorrendert.

Firefox wird hier nicht gestartet. An seine Stelle tritt ein nachgebauter
"Firefox", der die Seite liest, die das Werkzeug ihm gibt, und dafür ein
Testbild malt: je Kopie der Szene ein Hintergrund und ein gelber Punkt, der
sich mit der Zeit bewegt. So lässt sich prüfen, ob das Werkzeug

* die Einstellungen aus der SVG richtig liest,
* eine Schleife erkennt, die nicht nahtlos ist,
* Bewegung außerhalb der Ausschnitte findet und
* die richtigen Dateien schreibt –

in Sekundenbruchteilen und ohne Bildschirm.
"""

import importlib.util
import json
import re
import struct
import zlib
from pathlib import Path

import pytest

PROJEKT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("rendern", PROJEKT / "grafik" / "rendern.py")
rendern = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rendern)


def _svg(bereiche="80 20 60 40", schleife=800, bilder=8, breite=200, viewbox="0 0 200 100"):
    teile = [f'viewBox="{viewbox}"', f'data-breite="{breite}"',
             f'data-schleife-ms="{schleife}"', f'data-bilder="{bilder}"']
    if bereiche is not None:
        teile.append(f'data-bereiche="{bereiche}"')
    return f'<svg xmlns="http://www.w3.org/2000/svg" {" ".join(teile)}><rect width="200" height="100"/></svg>'


# ── Ein kleiner PNG-Schreiber für die Tests – mit allen fünf Zeilenfiltern ───

def _png(breite, hoehe, zeilen, kanaele=3, filter_je_zeile=None):
    """Baut ein PNG. ``zeilen``: Liste von bytes je Zeile (breite * kanaele)."""
    roh = bytearray()
    vorher = bytes(breite * kanaele)
    for y, zeile in enumerate(zeilen):
        art = filter_je_zeile[y % len(filter_je_zeile)] if filter_je_zeile else 0
        gefiltert = bytearray()
        for i, wert in enumerate(zeile):
            a = zeile[i - kanaele] if i >= kanaele else 0
            b = vorher[i]
            c = vorher[i - kanaele] if i >= kanaele else 0
            if art == 0:
                vorhersage = 0
            elif art == 1:
                vorhersage = a
            elif art == 2:
                vorhersage = b
            elif art == 3:
                vorhersage = (a + b) >> 1
            else:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                vorhersage = a if pa <= pb and pa <= pc else b if pb <= pc else c
            gefiltert.append((wert - vorhersage) & 255)
        roh += bytes([art]) + gefiltert
        vorher = zeile

    def stueck(art, inhalt):
        return struct.pack(">I", len(inhalt)) + art + inhalt + struct.pack(">I", zlib.crc32(art + inhalt))

    farbtyp = 2 if kanaele == 3 else 6
    return (b"\x89PNG\r\n\x1a\n" + stueck(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, farbtyp, 0, 0, 0))
            + stueck(b"IDAT", zlib.compress(bytes(roh))) + stueck(b"IEND", b""))


class FalscherFirefox:
    """Malt statt Firefox ein Testbild zu der Seite, die das Werkzeug erzeugt.

    ``bewegung(t_ms)`` liefert die Position des Punktes in SVG-Einheiten.
    """

    HINTERGRUND = (40, 60, 90)
    PUNKT = (250, 200, 50)

    def __init__(self, bewegung):
        self.bewegung = bewegung
        self.aufrufe = []

    def __call__(self, html, breite, hoehe):
        self.aufrufe.append((breite, hoehe, html.count('class="kopie"')))
        spalten = int(re.search(r"repeat\((\d+), max-content\)", html).group(1))
        kopien = re.findall(
            r'class="kopie" data-t="(\d+)" viewBox="([^"]+)" width="(\d+)" height="(\d+)"', html)
        bild = [bytearray(breite * 3) for _ in range(hoehe)]
        x0 = y0 = zeilenhoehe = 0
        for nr, (t, ansicht, w, h) in enumerate(kopien):
            w, h = int(w), int(h)
            if nr and nr % spalten == 0:
                x0, y0, zeilenhoehe = 0, y0 + zeilenhoehe, 0
            vx, vy, vb, vh = (float(v) for v in ansicht.split())
            px, py = self.bewegung(int(t))
            mx, my = (px - vx) * w / vb, (py - vy) * h / vh
            for y in range(h):
                for x in range(w):
                    farbe = self.PUNKT if abs(x + .5 - mx) <= 3 and abs(y + .5 - my) <= 3 else self.HINTERGRUND
                    if y0 + y < hoehe and x0 + x < breite:
                        bild[y0 + y][3 * (x0 + x):3 * (x0 + x) + 3] = bytes(farbe)
            x0 += w
            zeilenhoehe = max(zeilenhoehe, h)
        return _png(breite, hoehe, [bytes(z) for z in bild])


def im_kreis(t_ms, schleife=800):
    """Ein Punkt, der nahtlos im Kreis läuft – um (110, 40), Radius 15."""
    import math
    winkel = 2 * math.pi * ((t_ms - rendern.T0_MS) % schleife) / schleife
    return 110 + 15 * math.cos(winkel), 40 + 15 * math.sin(winkel)


# ───────────────────────────────────────────────────────────────────────────
# 1. Einstellungen aus der SVG
# ───────────────────────────────────────────────────────────────────────────

def test_die_einstellungen_werden_gelesen():
    e = rendern.einstellungen_lesen(_svg(), "probe")
    assert (e.name, e.breite, e.hoehe, e.schleife_ms, e.bilder, e.takt_ms) == ("probe", 200, 100, 800, 8, 100)
    assert e.viewbox == (0, 0, 200, 100)
    assert e.bereiche == (rendern.Bereich(80, 20, 60, 40),)


def test_die_hoehe_folgt_aus_der_viewbox():
    e = rendern.einstellungen_lesen(_svg(breite=960, viewbox="0 0 1600 900"), "probe")
    assert (e.breite, e.hoehe) == (960, 540)
    assert e.massstab == pytest.approx(.6)


def test_mehrere_bereiche_getrennt_durch_semikolon():
    e = rendern.einstellungen_lesen(_svg(bereiche="10 10 20 20; 100 50 30 30"), "probe")
    assert len(e.bereiche) == 2


def test_ein_bereich_wird_nach_aussen_auf_ganze_pixel_gerundet():
    """Er darf wachsen, aber nie etwas Bewegtes abschneiden."""
    b = rendern.bereich_in_pixeln((10.4, 20.6, 30.2, 5.1), (0, 0, 200, 100), 1.0, 200, 100)
    assert b == rendern.Bereich(10, 20, 31, 6)


def test_ein_bereich_wird_an_der_bildkante_gekappt():
    b = rendern.bereich_in_pixeln((180, -10, 50, 40), (0, 0, 200, 100), 1.0, 200, 100)
    assert b == rendern.Bereich(180, 0, 20, 30)


@pytest.mark.parametrize("svg, fehlerwort", [
    ('<rect/>', "<svg>"),
    ('<svg data-breite="200" data-schleife-ms="800" data-bilder="8"></svg>', "viewBox"),
    ('<svg viewBox="0 0 200 100" data-schleife-ms="800" data-bilder="8"></svg>', "data-breite"),
    ('<svg viewBox="0 0 200 100" data-breite="200" data-bilder="8"></svg>', "data-schleife-ms"),
    ('<svg viewBox="0 0 200 100" data-breite="abc" data-schleife-ms="800" data-bilder="8"></svg>', "ganze Zahl"),
    ('<svg viewBox="0 0 200 100" data-breite="200" data-schleife-ms="800" data-bilder="7"></svg>', "teilbar"),
    ('<svg viewBox="0 0 300 100" data-breite="200" data-schleife-ms="800" data-bilder="8"></svg>', "passt nicht"),
    ('<svg viewBox="0 0 200 100" data-breite="200" data-schleife-ms="800" data-bilder="8" '
     'data-bereiche="1 2 3"></svg>', "vier Zahlen"),
    ('<svg viewBox="0 0 200 100" data-breite="200" data-schleife-ms="800" data-bilder="8" '
     'data-bereiche="500 500 10 10"></svg>', "ausserhalb"),
])
def test_fehlerhafte_einstellungen_werden_verstaendlich_abgewiesen(svg, fehlerwort):
    with pytest.raises(ValueError) as fehler:
        rendern.einstellungen_lesen(svg, "probe")
    assert fehlerwort.lower() in str(fehler.value).lower().replace("ß", "ss")


def test_das_blatt_wird_nicht_breiter_als_erlaubt():
    spalten, zeilen = rendern.blattmasse(rendern.Bereich(0, 0, 1000, 100), 40)
    assert spalten * 1000 <= rendern.MAX_BLATTBREITE
    assert spalten * zeilen >= 40


# ───────────────────────────────────────────────────────────────────────────
# 2. Die Seite für Firefox
# ───────────────────────────────────────────────────────────────────────────

def test_eine_ausschnitt_kopie_zeigt_genau_den_ausschnitt():
    e = rendern.einstellungen_lesen(_svg(breite=960, viewbox="0 0 1600 900", bereiche="570 290 450 460"), "p")
    kopie = rendern.kopie("<g/>", e, 12345, e.bereiche[0])
    assert 'viewBox="570 290 450 460"' in kopie
    assert 'width="270" height="276"' in kopie
    assert 'data-t="12345"' in kopie
    assert 'preserveAspectRatio="none"' in kopie


def test_die_seite_haelt_css_und_smil_animationen_an():
    html = rendern.seite(["<svg class=\"kopie\"></svg>"] * 3, 2)
    assert "getAnimations" in html and "setCurrentTime" in html
    assert "repeat(2, max-content)" in html


# ───────────────────────────────────────────────────────────────────────────
# 3. PNG lesen
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("kanaele", [3, 4])
def test_png_lesen_versteht_alle_fuenf_zeilenfilter(kanaele):
    breite, hoehe = 7, 10
    zeilen = [bytes((x * 37 + y * 11 + k * 5) % 256 for x in range(breite) for k in range(kanaele))
              for y in range(hoehe)]
    daten = _png(breite, hoehe, zeilen, kanaele, filter_je_zeile=[0, 1, 2, 3, 4])
    bild = rendern.png_lesen(daten)
    assert (bild.breite, bild.hoehe, bild.kanaele) == (breite, hoehe, kanaele)
    assert bild.zeilen == zeilen


def test_ausschneiden_liefert_rgb_auch_aus_rgba():
    zeilen = [bytes([1, 2, 3, 255, 4, 5, 6, 255])] * 2
    bild = rendern.png_lesen(_png(2, 2, zeilen, kanaele=4))
    assert rendern.ausschneiden(bild, 1, 0, 1, 2) == [bytes([4, 5, 6])] * 2


def test_kein_png_wird_abgewiesen():
    with pytest.raises(ValueError):
        rendern.png_lesen(b"GIF89a")


# ───────────────────────────────────────────────────────────────────────────
# 4. Prüfen – mit dem nachgebauten Firefox
# ───────────────────────────────────────────────────────────────────────────

def test_eine_nahtlose_animation_im_ausschnitt_besteht_die_pruefung():
    svg = _svg(bereiche="85 15 50 50")
    fehler, vorschlag = rendern.pruefen(svg, rendern.einstellungen_lesen(svg, "p"), FalscherFirefox(im_kreis))
    assert fehler == [] and vorschlag is None


def test_bewegung_ausserhalb_des_ausschnitts_wird_gemeldet():
    svg = _svg(bereiche="10 10 20 20")
    fehler, _ = rendern.pruefen(svg, rendern.einstellungen_lesen(svg, "p"), FalscherFirefox(im_kreis))
    assert len(fehler) == 1
    assert "Außerhalb der Ausschnitte" in fehler[0]


def test_eine_schleife_die_nicht_nahtlos_ist_wird_gemeldet():
    """Der Punkt läuft einfach weiter – nach 800 ms steht er woanders."""
    def geradeaus(t_ms):
        return 20 + (t_ms - rendern.T0_MS) * .1, 50

    svg = _svg(bereiche="0 0 200 100")
    fehler, _ = rendern.pruefen(svg, rendern.einstellungen_lesen(svg, "p"), FalscherFirefox(geradeaus))
    assert any("wiederholt sich" in f for f in fehler)


def test_ohne_ausschnitt_schlaegt_die_pruefung_einen_vor():
    svg = _svg(bereiche=None)
    _, vorschlag = rendern.pruefen(svg, rendern.einstellungen_lesen(svg, "p"), FalscherFirefox(im_kreis))
    x, y, b, h = vorschlag
    assert x <= 95 and y <= 25 and x + b >= 125 and y + h >= 55    # umfasst den Kreis


def test_eine_stehende_szene_braucht_keinen_ausschnitt_und_meldet_nichts():
    svg = _svg(bereiche=None)
    fehler, vorschlag = rendern.pruefen(svg, rendern.einstellungen_lesen(svg, "p"),
                                        FalscherFirefox(lambda t: (50, 50)))
    assert fehler == [] and vorschlag is None


# ───────────────────────────────────────────────────────────────────────────
# 5. Schreiben
# ───────────────────────────────────────────────────────────────────────────

def _svg_datei(tmp_path, **einstellungen):
    datei = tmp_path / "probe.svg"
    datei.write_text(_svg(**einstellungen), encoding="utf-8")
    return datei


def test_rendern_schreibt_hintergrund_blatt_und_beschreibung(tmp_path):
    firefox = FalscherFirefox(im_kreis)
    ziel = rendern.rendern(_svg_datei(tmp_path, bereiche="85 15 50 50"), tmp_path / "aus",
                           bild_machen=firefox, ausgabe=lambda *_: None)
    assert sorted(p.name for p in ziel.iterdir()) == ["animation.json", "bereich_1.png", "hintergrund.png"]
    beschreibung = json.loads((ziel / "animation.json").read_text(encoding="utf-8"))
    assert beschreibung["breite"] == 200 and beschreibung["hoehe"] == 100
    assert beschreibung["bilder"] == 8 and beschreibung["takt_ms"] == 100
    assert beschreibung["bereiche"] == [
        {"datei": "bereich_1.png", "x": 85, "y": 15, "breite": 50, "hoehe": 50, "spalten": 8}]
    blatt = rendern.png_lesen((ziel / "bereich_1.png").read_bytes())
    assert (blatt.breite, blatt.hoehe) == (8 * 50, 50)
    hintergrund = rendern.png_lesen((ziel / "hintergrund.png").read_bytes())
    assert (hintergrund.breite, hintergrund.hoehe) == (200, 100)


def test_die_einzelbilder_zeigen_die_zeitpunkte_der_reihe_nach(tmp_path):
    zeiten = []

    def merken(t_ms):
        zeiten.append(t_ms)
        return im_kreis(t_ms)

    rendern.rendern(_svg_datei(tmp_path, bereiche="85 15 50 50"), tmp_path / "aus", pruefung=False,
                    bild_machen=FalscherFirefox(merken), ausgabe=lambda *_: None)
    blattzeiten = zeiten[-8:]                      # die letzte Seite ist das Blatt
    assert blattzeiten == [rendern.T0_MS + i * 100 for i in range(8)]


def test_bei_einem_pruefungsfehler_wird_nichts_geschrieben(tmp_path):
    with pytest.raises(ValueError):
        rendern.rendern(_svg_datei(tmp_path, bereiche="10 10 20 20"), tmp_path / "aus",
                        bild_machen=FalscherFirefox(im_kreis), ausgabe=lambda *_: None)
    assert not (tmp_path / "aus").exists()


def test_alte_ausschnitte_werden_entfernt(tmp_path):
    """Wer von zwei Ausschnitten auf einen umstellt, behält keine Leiche."""
    ziel = tmp_path / "aus" / "probe"
    ziel.mkdir(parents=True)
    (ziel / "bereich_2.png").write_bytes(b"alt")
    rendern.rendern(_svg_datei(tmp_path, bereiche="85 15 50 50"), tmp_path / "aus",
                    bild_machen=FalscherFirefox(im_kreis), ausgabe=lambda *_: None)
    assert not (ziel / "bereich_2.png").exists()


def test_main_meldet_fehler_und_gibt_eins_zurueck(tmp_path, capsys):
    datei = tmp_path / "kaputt.svg"
    datei.write_text("<svg></svg>", encoding="utf-8")
    assert rendern.main([str(datei)]) == 1
    assert "Fehler:" in capsys.readouterr().err
