"""Rendert eine SVG-Animation für das Spiel vor.

    python3 grafik/rendern.py grafik/wrack.svg

Das Werkzeug läuft nur auf dem Entwicklungsrechner. Das Spiel braucht es
nicht – es liest nur, was hier herauskommt:

    content/animationen/<name>/hintergrund.png   die ganze Szene als Standbild
    content/animationen/<name>/bereich_1.png     Bildfolge des bewegten Ausschnitts
    content/animationen/<name>/animation.json    Größen, Positionen, Takt

Warum vorrendern
────────────────
Tkinter kann weder SVG noch CSS-Animationen abspielen, und das Spiel darf
keine Zusatzpakete brauchen – Schulrechner haben keine Adminrechte. Firefox
kann beides. Also rechnet Firefox die Animation einmal in Einzelbilder um, und
das Spiel blättert sie nur noch durch (``ui/animation.py``).

Damit das klein bleibt, wird nicht die ganze Szene für jedes Bild gespeichert,
sondern nur der Ausschnitt, in dem sich etwas bewegt. Der Rest ist ein
einziges Standbild.

Was die SVG mitbringen muss – Attribute am <svg>-Element
────────────────────────────────────────────────────────
    viewBox            wie immer
    data-breite        Breite im Spiel in Pixeln; die Höhe folgt aus der viewBox
    data-schleife-ms   Länge der Schleife; jede Animationsdauer muss sie teilen
    data-bilder        Einzelbilder je Schleife (data-schleife-ms muss teilbar sein)
    data-bereiche      bewegte Ausschnitte in SVG-Einheiten: "x y b h" oder
                       mehrere, getrennt durch ";"

Fehlt data-bereiche, schlägt das Werkzeug einen Ausschnitt vor.

Was es prüft, bevor es etwas schreibt
─────────────────────────────────────
* Wiederholt sich die Animation nach data-schleife-ms genau? Sonst springt das
  Bild im Spiel an der Nahtstelle.
* Bewegt sich etwas außerhalb der Ausschnitte? Das bliebe im Spiel stehen,
  und an der Kante des Ausschnitts entstünde ein Sprung.

Mehr dazu in dokumentation/Animationen.md.
"""

import argparse
import json
import math
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from typing import NamedTuple

PROJEKT = pathlib.Path(__file__).resolve().parent.parent
ZIELORDNER = PROJEKT / "content" / "animationen"

#: Die Animation wird erst nach dieser Zeit angehalten – dann ist alles
#: eingeschwungen, auch was mit negativer Verzögerung beginnt.
T0_MS = 10_000

#: So viele Zeitpunkte werden auf Bewegung außerhalb der Ausschnitte geprüft.
PRUEFBILDER = 12
#: Geprüft wird in halber Größe – das genügt und spart Zeit.
PRUEFMASSSTAB = 0.5
#: Ab diesem Farbabstand (0–255) gilt ein Pixel als verändert.
RAUSCHEN = 14
#: So viele veränderte Prüfpixel gelten noch als Rundungsrauschen.
ERLAUBTE_AUSREISSER = 6
#: Breiter wird ein Bildblatt nicht – danach beginnt eine neue Zeile.
MAX_BLATTBREITE = 4096


class Bereich(NamedTuple):
    """Ein bewegter Ausschnitt in Pixeln des fertigen Bildes."""

    x: int
    y: int
    breite: int
    hoehe: int


class Einstellungen(NamedTuple):
    name: str
    viewbox: tuple
    breite: int
    hoehe: int
    schleife_ms: int
    bilder: int
    takt_ms: int
    bereiche: tuple

    @property
    def massstab(self):
        """Pixel je SVG-Einheit."""
        return self.breite / self.viewbox[2]


class Bild(NamedTuple):
    """Ein entpacktes PNG: Zeilen mit je ``breite * kanaele`` Bytes."""

    breite: int
    hoehe: int
    kanaele: int
    zeilen: list


# ── Einstellungen aus der SVG ──────────────────────────────────────────────

def _kopf(svg_text):
    treffer = re.search(r"<svg\b[^>]*>", svg_text)
    if not treffer:
        raise ValueError("In der Datei steht kein <svg>-Element.")
    return treffer


def _attribut(kopf, name, pflicht=True):
    treffer = re.search(rf'\s{re.escape(name)}\s*=\s*"([^"]*)"', kopf)
    if treffer:
        return treffer.group(1).strip()
    if pflicht:
        raise ValueError(f'Am <svg>-Element fehlt {name}="…" – siehe dokumentation/Animationen.md.')
    return None


def _ganze_zahl(kopf, name):
    wert = _attribut(kopf, name)
    try:
        zahl = int(wert)
    except ValueError:
        raise ValueError(f'{name}="{wert}" ist keine ganze Zahl.') from None
    if zahl <= 0:
        raise ValueError(f'{name} muss grösser als null sein, ist aber {zahl}.')
    return zahl


def bereich_in_pixeln(werte, viewbox, massstab, breite, hoehe):
    """Ein Ausschnitt in SVG-Einheiten → ganze Pixel, nach außen gerundet.

    Nach außen, damit der Ausschnitt nur wachsen und nie etwas Bewegtes
    abschneiden kann.

    >>> bereich_in_pixeln((570, 290, 450, 460), (0, 0, 1600, 900), .6, 960, 540)
    Bereich(x=342, y=174, breite=270, hoehe=276)
    """
    x, y, b, h = werte
    if b <= 0 or h <= 0:
        raise ValueError(f"Ausschnitt {werte}: Breite und Höhe müssen grösser als null sein.")
    vx, vy = viewbox[0], viewbox[1]
    x0 = max(0, math.floor(round((x - vx) * massstab, 6)))
    y0 = max(0, math.floor(round((y - vy) * massstab, 6)))
    x1 = min(breite, math.ceil(round((x + b - vx) * massstab, 6)))
    y1 = min(hoehe, math.ceil(round((y + h - vy) * massstab, 6)))
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"Ausschnitt {werte} liegt ganz außerhalb der viewBox.")
    return Bereich(x0, y0, x1 - x0, y1 - y0)


def einstellungen_lesen(svg_text, name):
    """Liest die data-Attribute am <svg>-Element und prüft sie."""
    kopf = _kopf(svg_text).group(0)
    try:
        viewbox = tuple(float(v) for v in _attribut(kopf, "viewBox").replace(",", " ").split())
    except ValueError:
        raise ValueError("Die viewBox muss aus vier Zahlen bestehen.") from None
    if len(viewbox) != 4 or viewbox[2] <= 0 or viewbox[3] <= 0:
        raise ValueError("Die viewBox muss aus vier Zahlen bestehen, Breite und Höhe grösser null.")
    breite = _ganze_zahl(kopf, "data-breite")
    massstab = breite / viewbox[2]
    hoehe_genau = viewbox[3] * massstab
    hoehe = round(hoehe_genau)
    if abs(hoehe_genau - hoehe) > 1e-6:
        raise ValueError(
            f"data-breite={breite} passt nicht zur viewBox: Die Höhe wäre {hoehe_genau:.3f} Pixel. "
            "Wähle eine Breite, bei der eine ganze Zahl herauskommt."
        )
    schleife_ms = _ganze_zahl(kopf, "data-schleife-ms")
    bilder = _ganze_zahl(kopf, "data-bilder")
    if schleife_ms % bilder:
        raise ValueError(
            f"data-schleife-ms={schleife_ms} ist nicht durch data-bilder={bilder} teilbar – "
            "jedes Bild muss gleich lange stehen."
        )
    bereiche = []
    for teil in (_attribut(kopf, "data-bereiche", pflicht=False) or "").split(";"):
        if not teil.strip():
            continue
        try:
            werte = tuple(float(v) for v in teil.replace(",", " ").split())
        except ValueError:
            raise ValueError(f'data-bereiche: "{teil.strip()}" sind keine vier Zahlen.') from None
        if len(werte) != 4:
            raise ValueError(f'data-bereiche: "{teil.strip()}" braucht genau vier Zahlen: x y b h.')
        bereiche.append(bereich_in_pixeln(werte, viewbox, massstab, breite, hoehe))
    return Einstellungen(name, viewbox, breite, hoehe, schleife_ms, bilder,
                         schleife_ms // bilder, tuple(bereiche))


# ── Die Seite, die Firefox abfotografiert ─────────────────────────────────

#: Hält jede Kopie der Szene an ihrem Zeitpunkt an – CSS-Animationen über die
#: Web-Animations-API, SMIL-Animationen (<animate>) über setCurrentTime.
ANHALTEN = """
document.querySelectorAll("svg.kopie").forEach(svg => {
  const t = Number(svg.dataset.t);
  svg.getAnimations({subtree: true}).forEach(a => { a.pause(); a.currentTime = t; });
  if (svg.pauseAnimations) { svg.pauseAnimations(); svg.setCurrentTime(t / 1000); }
});
"""


def svg_innen(svg_text):
    """Alles zwischen <svg …> und </svg>."""
    anfang = _kopf(svg_text).end()
    ende = svg_text.rfind("</svg>")
    if ende < anfang:
        raise ValueError("Das schliessende </svg> fehlt.")
    return svg_text[anfang:ende]


def kopie(innen, einstellungen, t_ms, bereich=None, faktor=1.0):
    """Eine angehaltene Kopie der Szene – ganz oder als Ausschnitt."""
    vx, vy, vb, vh = einstellungen.viewbox
    s = einstellungen.massstab
    if bereich is None:
        ansicht, breite, hoehe = (vx, vy, vb, vh), einstellungen.breite, einstellungen.hoehe
    else:
        ansicht = (vx + bereich.x / s, vy + bereich.y / s, bereich.breite / s, bereich.hoehe / s)
        breite, hoehe = bereich.breite, bereich.hoehe
    zahlen = " ".join(f"{v:.6f}".rstrip("0").rstrip(".") for v in ansicht)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="kopie" data-t="{t_ms}" '
            f'viewBox="{zahlen}" width="{round(breite * faktor)}" height="{round(hoehe * faktor)}" '
            f'preserveAspectRatio="none">{innen}</svg>')


def seite(kopien, spalten):
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
        "html, body { margin: 0; padding: 0; overflow: hidden; background: #000; }"
        f".raster {{ display: grid; grid-template-columns: repeat({spalten}, max-content); }}"
        "svg.kopie { display: block; }"
        f'</style></head><body><div class="raster">{"".join(kopien)}</div>'
        f"<script>{ANHALTEN}</script></body></html>"
    )


def blattmasse(bereich, bilder):
    """Spalten und Zeilen des Bildblatts für einen Ausschnitt.

    >>> blattmasse(Bereich(0, 0, 270, 276), 40)
    (8, 5)
    """
    spalten = max(1, min(bilder, MAX_BLATTBREITE // bereich.breite))
    return spalten, math.ceil(bilder / spalten)


# ── Firefox ────────────────────────────────────────────────────────────────

def firefox_bild(html, breite, hoehe):
    """Lässt Firefox (headless) die Seite in genau dieser Fenstergröße fotografieren."""
    programm = os.environ.get("FIREFOX") or shutil.which("firefox")
    if not programm:
        raise RuntimeError(
            "Firefox wurde nicht gefunden. Das Werkzeug braucht Firefox – nur auf dem "
            "Entwicklungsrechner, nicht im Spiel. (Anderer Pfad: Umgebungsvariable FIREFOX.)"
        )
    # Firefox als Snap darf nicht in /tmp lesen, wohl aber in seinem eigenen Ordner.
    snap = pathlib.Path.home() / "snap" / "firefox" / "common"
    arbeitsordner = pathlib.Path(tempfile.mkdtemp(prefix="animation-", dir=snap if snap.is_dir() else None))
    try:
        (arbeitsordner / "profil").mkdir()
        seite_datei = arbeitsordner / "seite.html"
        seite_datei.write_text(html, encoding="utf-8")
        bild = arbeitsordner / "bild.png"
        ergebnis = subprocess.run(
            [programm, "--headless", "--no-remote", "--profile", str(arbeitsordner / "profil"),
             f"--window-size={breite},{hoehe}", "--screenshot", str(bild), seite_datei.as_uri()],
            capture_output=True, text=True, timeout=300,
        )
        if not bild.exists():
            raise RuntimeError("Firefox hat kein Bild geschrieben:\n" + ergebnis.stderr[-1500:])
        return bild.read_bytes()
    finally:
        shutil.rmtree(arbeitsordner, ignore_errors=True)


# ── PNG lesen (nur fürs Prüfen) ────────────────────────────────────────────

def png_lesen(daten):
    """Entpackt ein 8-Bit-PNG ohne Zeilensprung (RGB oder RGBA)."""
    if daten[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Das ist keine PNG-Datei.")
    position, idat = 8, []
    breite = hoehe = kanaele = None
    while position < len(daten):
        laenge, art = struct.unpack(">I4s", daten[position:position + 8])
        inhalt = daten[position + 8:position + 8 + laenge]
        position += 12 + laenge
        if art == b"IHDR":
            breite, hoehe, tiefe, farbtyp, _, _, zeilensprung = struct.unpack(">IIBBBBB", inhalt)
            if tiefe != 8 or farbtyp not in (2, 6) or zeilensprung:
                raise ValueError("Nur 8-Bit-PNGs in RGB oder RGBA ohne Zeilensprung werden gelesen.")
            kanaele = 3 if farbtyp == 2 else 4
        elif art == b"IDAT":
            idat.append(inhalt)
        elif art == b"IEND":
            break
    if kanaele is None:
        raise ValueError("Dem PNG fehlt der Kopf (IHDR).")
    roh = zlib.decompress(b"".join(idat))
    laenge = breite * kanaele
    vorher = bytearray(laenge)
    zeilen = []
    for y in range(hoehe):
        start = y * (laenge + 1)
        art, zeile = roh[start], bytearray(roh[start + 1:start + 1 + laenge])
        if art == 1:
            for i in range(kanaele, laenge):
                zeile[i] = (zeile[i] + zeile[i - kanaele]) & 255
        elif art == 2:
            zeile = bytearray((a + b) & 255 for a, b in zip(zeile, vorher))
        elif art == 3:
            for i in range(laenge):
                links = zeile[i - kanaele] if i >= kanaele else 0
                zeile[i] = (zeile[i] + ((links + vorher[i]) >> 1)) & 255
        elif art == 4:
            for i in range(laenge):
                a = zeile[i - kanaele] if i >= kanaele else 0
                b = vorher[i]
                c = vorher[i - kanaele] if i >= kanaele else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                vorhersage = a if pa <= pb and pa <= pc else b if pb <= pc else c
                zeile[i] = (zeile[i] + vorhersage) & 255
        elif art != 0:
            raise ValueError(f"Unbekannter PNG-Zeilenfilter {art}.")
        zeilen.append(bytes(zeile))
        vorher = zeile
    return Bild(breite, hoehe, kanaele, zeilen)


def ausschneiden(bild, x, y, breite, hoehe):
    """Ein Rechteck aus einem entpackten Bild, als Liste von RGB-Zeilen."""
    k = bild.kanaele
    teil = []
    for zeile in bild.zeilen[y:y + hoehe]:
        stueck = zeile[x * k:(x + breite) * k]
        if k == 4:
            stueck = bytes(b for i, b in enumerate(stueck) if i % 4 != 3)
        teil.append(stueck)
    return teil


# ── Prüfen ─────────────────────────────────────────────────────────────────

def veraenderte_pixel(a, b):
    """Positionen (x, y), an denen sich zwei gleich große RGB-Bilder unterscheiden."""
    treffer = []
    for y, (za, zb) in enumerate(zip(a, b)):
        if za == zb:
            continue
        for x in range(len(za) // 3):
            i = 3 * x
            if (abs(za[i] - zb[i]) > RAUSCHEN or abs(za[i + 1] - zb[i + 1]) > RAUSCHEN
                    or abs(za[i + 2] - zb[i + 2]) > RAUSCHEN):
                treffer.append((x, y))
    return treffer


def umriss(pixel):
    """Das kleinste Rechteck (x, y, b, h) um eine Menge von Pixeln."""
    xs = [x for x, _ in pixel]
    ys = [y for _, y in pixel]
    return min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def in_svg_einheiten(rechteck, einstellungen, faktor, rand=0):
    """Pixel-Rechteck (im Prüfbild) → SVG-Einheiten, mit Rand, auf ganze Zahlen."""
    s = einstellungen.massstab * faktor
    x, y, b, h = rechteck
    vx, vy = einstellungen.viewbox[:2]
    return (math.floor(vx + x / s - rand), math.floor(vy + y / s - rand),
            math.ceil(b / s + 2 * rand), math.ceil(h / s + 2 * rand))


def pruefen(svg_text, einstellungen, bild_machen=firefox_bild):
    """Prüft Nahtstelle und Bewegung außerhalb der Ausschnitte.

    Rückgabe: Liste von Fehlermeldungen (leer, wenn alles passt) und – falls
    keine Ausschnitte angegeben sind – ein Vorschlag für data-bereiche.
    """
    innen = svg_innen(svg_text)
    zeiten = [T0_MS, T0_MS + einstellungen.schleife_ms]
    zeiten += [T0_MS + i * einstellungen.schleife_ms // PRUEFBILDER for i in range(1, PRUEFBILDER)]
    spalten = 4
    pb = round(einstellungen.breite * PRUEFMASSSTAB)
    ph = round(einstellungen.hoehe * PRUEFMASSSTAB)
    kopien = [kopie(innen, einstellungen, t, faktor=PRUEFMASSSTAB) for t in zeiten]
    zeilen_zahl = math.ceil(len(kopien) / spalten)
    blatt = png_lesen(bild_machen(seite(kopien, spalten), pb * spalten, ph * zeilen_zahl))
    bilder = [ausschneiden(blatt, (i % spalten) * pb, (i // spalten) * ph, pb, ph) for i in range(len(zeiten))]

    fehler, vorschlag = [], None
    naht = veraenderte_pixel(bilder[0], bilder[1])
    if len(naht) > ERLAUBTE_AUSREISSER:
        x, y, b, h = in_svg_einheiten(umriss(naht), einstellungen, PRUEFMASSSTAB)
        fehler.append(
            f"Die Animation wiederholt sich nach {einstellungen.schleife_ms} ms nicht genau – "
            f"Unterschiede bei x={x} y={y} (Breite {b}, Höhe {h}). Jede Animationsdauer muss "
            "data-schleife-ms teilen (bei alternate: die doppelte Dauer)."
        )

    bewegt = set()
    for anderes in bilder[2:]:
        bewegt.update(veraenderte_pixel(bilder[0], anderes))
    bewegt.update(naht)
    if not einstellungen.bereiche:
        if bewegt:
            vorschlag = in_svg_einheiten(umriss(bewegt), einstellungen, PRUEFMASSSTAB, rand=12)
        return fehler, vorschlag

    halb = [Bereich(math.floor(b.x * PRUEFMASSSTAB) - 1, math.floor(b.y * PRUEFMASSSTAB) - 1,
                    math.ceil(b.breite * PRUEFMASSSTAB) + 2, math.ceil(b.hoehe * PRUEFMASSSTAB) + 2)
            for b in einstellungen.bereiche]
    draussen = [(x, y) for x, y in bewegt
                if not any(b.x <= x < b.x + b.breite and b.y <= y < b.y + b.hoehe for b in halb)]
    if len(draussen) > ERLAUBTE_AUSREISSER:
        x, y, b, h = in_svg_einheiten(umriss(draussen), einstellungen, PRUEFMASSSTAB, rand=8)
        fehler.append(
            f"Außerhalb der Ausschnitte bewegt sich etwas: bei x={x} y={y} (Breite {b}, Höhe {h}). "
            "Vergrößere data-bereiche oder halte die Bewegung dort an."
        )
    return fehler, vorschlag


# ── Schreiben ──────────────────────────────────────────────────────────────

def rendern(svg_datei, zielordner=ZIELORDNER, pruefung=True, bild_machen=firefox_bild, ausgabe=print):
    """Rendert eine Animation. Rückgabe: der Ordner mit den fertigen Dateien."""
    svg_datei = pathlib.Path(svg_datei)
    svg_text = svg_datei.read_text(encoding="utf-8")
    einstellungen = einstellungen_lesen(svg_text, svg_datei.stem)

    if pruefung or not einstellungen.bereiche:
        ausgabe("Prüfe Nahtstelle und Bewegung …")
        fehler, vorschlag = pruefen(svg_text, einstellungen, bild_machen)
        if vorschlag:
            raise ValueError(
                "Am <svg>-Element fehlt data-bereiche. Vorschlag nach der Prüfung:\n"
                f'    data-bereiche="{" ".join(str(v) for v in vorschlag)}"'
            )
        if not einstellungen.bereiche:
            raise ValueError("Am <svg>-Element fehlt data-bereiche, und es bewegt sich nichts.")
        if fehler:
            raise ValueError("\n".join(fehler))

    ziel = pathlib.Path(zielordner) / einstellungen.name
    ziel.mkdir(parents=True, exist_ok=True)
    for alt in ziel.glob("bereich_*.png"):
        alt.unlink()

    innen = svg_innen(svg_text)
    ausgabe(f"Hintergrund {einstellungen.breite}×{einstellungen.hoehe} …")
    (ziel / "hintergrund.png").write_bytes(
        bild_machen(seite([kopie(innen, einstellungen, T0_MS)], 1), einstellungen.breite, einstellungen.hoehe)
    )
    bereiche = []
    for nr, bereich in enumerate(einstellungen.bereiche, 1):
        spalten, zeilen = blattmasse(bereich, einstellungen.bilder)
        ausgabe(f"Ausschnitt {nr}: {einstellungen.bilder} Bilder à {bereich.breite}×{bereich.hoehe} …")
        kopien = [kopie(innen, einstellungen, T0_MS + i * einstellungen.takt_ms, bereich)
                  for i in range(einstellungen.bilder)]
        datei = f"bereich_{nr}.png"
        (ziel / datei).write_bytes(
            bild_machen(seite(kopien, spalten), bereich.breite * spalten, bereich.hoehe * zeilen)
        )
        bereiche.append({"datei": datei, "x": bereich.x, "y": bereich.y, "breite": bereich.breite,
                         "hoehe": bereich.hoehe, "spalten": spalten})

    try:
        quelle = svg_datei.resolve().relative_to(PROJEKT).as_posix()
    except ValueError:
        quelle = svg_datei.name
    beschreibung = {
        "quelle": quelle,
        "breite": einstellungen.breite,
        "hoehe": einstellungen.hoehe,
        "bilder": einstellungen.bilder,
        "takt_ms": einstellungen.takt_ms,
        "hintergrund": "hintergrund.png",
        "bereiche": bereiche,
    }
    (ziel / "animation.json").write_text(json.dumps(beschreibung, indent=2, ensure_ascii=False) + "\n",
                                         encoding="utf-8")
    return ziel


def main(argumente=None):
    parser = argparse.ArgumentParser(description="Rendert eine SVG-Animation für das Spiel vor.")
    parser.add_argument("svg", type=pathlib.Path, help="die SVG-Datei, z. B. grafik/wrack.svg")
    parser.add_argument("--ohne-pruefung", action="store_true",
                        help="Nahtstelle und Ausschnitte nicht prüfen (schneller, riskanter)")
    argumente = parser.parse_args(argumente)
    try:
        ziel = rendern(argumente.svg, pruefung=not argumente.ohne_pruefung)
    except (ValueError, RuntimeError, OSError) as fehler:
        print(f"Fehler: {fehler}", file=sys.stderr)
        return 1
    groesse = sum(datei.stat().st_size for datei in ziel.iterdir()) / 1024
    print(f"Fertig: {ziel.relative_to(PROJEKT) if ziel.is_relative_to(PROJEKT) else ziel} ({groesse:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
