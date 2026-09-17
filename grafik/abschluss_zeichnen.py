"""Zeichnet die Bilder für den Abschluss (Arbeitsplan 6.8): Nachtlager, Morgen und den Hubschrauber.

Erzeugt drei SVG-Dateien in ``grafik/``, die danach wie jede Animation
vorgerendert werden (``dokumentation/Animationen.md``)::

    python3 grafik/abschluss_zeichnen.py
    python3 grafik/rendern.py grafik/nachtlager.svg
    python3 grafik/rendern.py grafik/morgen.svg
    python3 grafik/rendern.py grafik/hubschrauber.svg

Die Geschichte in Bildern
─────────────────────────
Nach Bobs letzter Antwort wartet man im **Nachtlager an der Oase**: Feuer,
Rucksack, das ausgeschaltete Funkgerät, dahinter Wasser und Palmen in einer
Mulde zwischen den Dünen, darüber der Sternenhimmel. Es ist derselbe Ort, den
man in Level 3 verschlüsselt durchgegeben hat. Man legt
sich hin, die Augen fallen zu – das Schließen der Augen zeichnet das Spiel
selbst über die Szene (``ui/abschluss.py``). Beim Aufwachen liegt dieselbe
Stelle im **Morgengrauen** da, das Feuer ist aus. Dann kommt der
**Hubschrauber** und landet.

Warum man sofort sieht, dass es Freunde sind
────────────────────────────────────────────
Gejagt wird die Crew von Polizei, CIA und Interpol (Vorgeschichte). Der
Hubschrauber darf deshalb nicht aussehen wie einer von ihnen: kein Blaulicht,
kein Schriftzug, kein Grau. Er ist dunkelgrün mit Goldstreifen, auf seiner
Seite glänzt groß ein goldener Diamant – das Zeichen aus dem Titelbild, das
Zeichen der Crew –, und ein grünes Licht blinkt. Der Text im Spiel sagt es dann
noch ausdrücklich.

Warum ein Programm
──────────────────
Nachtlager und Morgen zeigen dieselbe Stelle – dieselben Dünen, dasselbe
Lager, nur in anderem Licht. Beide entstehen hier aus denselben Formen; wer
etwas verschiebt, verschiebt es in beiden. Wo der Hubschrauber landet und wo
der Text steht, rechnet ``ui/abschluss.py`` in Pixeln – die Szenen lassen
dort Platz: Sand ohne Lager, Himmel ohne Mond.

Maße
────
Die Szenen haben eine viewBox von 1600 × 900 und sind im Spiel 960 × 540
Pixel groß (eine Einheit sind 0,6 Pixel), wie die Wrack-Szene im Intro. Der
Hubschrauber hat 680 × 320 Einheiten und ist im Spiel 340 × 160 Pixel groß.
"""

import math
import pathlib
import random

ORDNER = pathlib.Path(__file__).resolve().parent

B, H = 1600, 900
HORIZONT = 560
#: Das Lager steht links; rechts davon bleibt Sand frei, wo der Hubschrauber landet.
FEUER = (430, 792)
RUCKSACK = (215, 768)
FUNKGERAET = (620, 800)
DECKE = (250, 836)
#: Wo die Kufen des gelandeten Hubschraubers den Sand berühren (Einheiten).
LANDEPLATZ = (1066, 790)

#: Immer derselbe Zufall – sonst sähen die Sterne nach jedem Neuzeichnen anders aus.
rnd = random.Random(2031)


def punkte(liste):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in liste)


def sterne(anzahl, oben, unten, deckkraft=(0.35, 1.0), groesse=(0.7, 2.0), farbe="#fff6e6"):
    teile = []
    for _ in range(anzahl):
        x, y = rnd.uniform(0, B), rnd.uniform(oben, unten)
        teile.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rnd.uniform(*groesse):.1f}" fill="{farbe}" '
                     f'opacity="{rnd.uniform(*deckkraft):.2f}"/>')
    return "\n".join(teile)


def huegelkette(y0, huegel, spannweite, seed):
    """Ein weicher Dünenkamm quer über das Bild – als geschlossene Fläche nach unten."""
    zufall = random.Random(seed)
    x, pfad = -40, [f"M-40,{H + 10}", f"L-40,{y0}"]
    y = y0
    while x < B + 40:
        breite = zufall.uniform(*spannweite)
        hoehe = zufall.uniform(-huegel, huegel * .6)
        xm, x = x + breite / 2, x + breite
        y_neu = y0 + zufall.uniform(-huegel * .3, huegel * .3)
        pfad.append(f"Q{xm:.0f},{y0 - huegel + hoehe:.0f} {x:.0f},{y_neu:.0f}")
        y = y_neu
    pfad.append(f"L{B + 40},{H + 10} Z")
    return " ".join(pfad)


BERGE = ("M-20,600 L-20,548 L70,540 L120,508 L240,506 L280,532 L420,536 L470,512 L610,510 L650,538 "
         "L860,544 L900,522 L1010,520 L1060,546 L1260,550 L1300,518 L1440,516 L1490,544 L1620,548 L1620,600 Z")
DUENE_FERN = huegelkette(598, 26, (260, 420), 11)
DUENE_MITTE = huegelkette(662, 34, (340, 520), 23)
# Der Boden vorn: links das Lager, rechts eben – dort landet der Hubschrauber. Sein Kamm
# liegt tief genug, dass dahinter die Mulde mit dem Wasser der Oase zu sehen ist.
BODEN = ("M-40,910 L-40,748 C120,736 360,748 560,762 C760,776 900,786 1060,792 C1240,798 1420,788 1640,772 "
         "L1640,910 Z")

#: Das Ufer der Oase: der Wasserrand quer durch die Mulde, von links nach rechts.
UFER = ((20, 716), (200, 696), (420, 683), (640, 680), (860, 686), (1080, 697), (1320, 714))
#: Die Palmen am Wasser: x, Höhe, Neigung der Krone nach links oder rechts, Zufallsnummer.
PALMEN = ((150, 300, -34, 5), (330, 250, 26, 9), (520, 335, -18, 14),
          (1010, 290, 30, 21), (1215, 235, -26, 33))


def _glatter_zug(punkte_liste):
    """Ein weicher Linienzug durch die Punkte – für Ufer und Uferkanten."""
    teile = [f"M{punkte_liste[0][0]},{punkte_liste[0][1]}"]
    for (xa, ya), (xb, yb) in zip(punkte_liste, punkte_liste[1:]):
        teile.append(f"Q{xa},{ya} {(xa + xb) / 2:.0f},{(ya + yb) / 2:.0f}")
    teile.append(f"L{punkte_liste[-1][0]},{punkte_liste[-1][1]}")
    return " ".join(teile)


#: Die ganze Wasserfläche; nach unten deckt die vordere Düne sie ab. Licht und
#: Spiegelungen werden darauf beschnitten, sonst lägen sie wie Pfützen im Sand.
WASSER_FLAECHE = _glatter_zug(UFER) + f" L{UFER[-1][0]},860 L{UFER[0][0]},860 Z"


def _ufer_y(x):
    """Wie hoch das Ufer an der Stelle ``x`` liegt."""
    for (xa, ya), (xb, yb) in zip(UFER, UFER[1:]):
        if x <= xb:
            return ya + (yb - ya) * (x - xa) / (xb - xa)
    return UFER[-1][1]


def palme(x, hoehe, neigung, seed, nacht):
    """Eine Dattelpalme am Ufer: geschwungener Stamm mit Ringen, darüber ein Kranz aus Wedeln.

    Das Licht kommt in beiden Szenen von rechts – nachts vom Mond, morgens von
    der Sonne –, deshalb sind die Wedel nach rechts heller.
    """
    zufall = random.Random(seed)
    stamm, ring = ("#241d33", "#3a3050") if nacht else ("#7d5a3a", "#a07c4e")
    wedel, wedel_hell, rippe = ("#15303a", "#204b58", "#0e1f27") if nacht else ("#3d6b44", "#74a24e", "#2b4a30")
    frucht = "#2b2238" if nacht else "#c07128"
    fuss = _ufer_y(x) - 6
    kx, ky = x + neigung, fuss - hoehe
    dick, duenn = hoehe * .05, hoehe * .028
    mitte_x, mitte_y = x + neigung * .3, fuss - hoehe * .55
    teile = [f'<path d="M{x - dick:.0f},{fuss:.0f} Q{mitte_x - duenn:.0f},{mitte_y:.0f} {kx - duenn:.0f},{ky:.0f} '
             f'L{kx + duenn:.0f},{ky:.0f} Q{mitte_x + dick:.0f},{mitte_y:.0f} {x + dick:.0f},{fuss:.0f} Z" '
             f'fill="{stamm}"/>']
    for i in range(1, 8):
        s = i / 8
        px = (1 - s) ** 2 * x + 2 * (1 - s) * s * mitte_x + s ** 2 * kx
        py = (1 - s) ** 2 * fuss + 2 * (1 - s) * s * mitte_y + s ** 2 * ky
        halb = (dick + (duenn - dick) * s) * .85
        teile.append(f'<path d="M{px - halb:.0f},{py:.0f} Q{px:.0f},{py + 7:.0f} {px + halb:.0f},{py:.0f}" '
                     f'fill="none" stroke="{ring}" stroke-width="2.5" opacity=".8"/>')
    teile.append(f'<ellipse cx="{kx:.0f}" cy="{ky + 6:.0f}" rx="{duenn * 1.6:.0f}" ry="{duenn:.0f}" fill="{ring}"/>')
    for i in range(3):
        teile.append(f'<circle cx="{kx + (i - 1) * duenn * 1.3:.0f}" cy="{ky + 16 + (i % 2) * 7:.0f}" '
                     f'r="{duenn * .5:.0f}" fill="{frucht}" opacity=".9"/>')
    wedelzahl = 8
    for i in range(wedelzahl):
        grad = -168 + i * (156 / (wedelzahl - 1)) + zufall.uniform(-7, 7)
        w = math.radians(grad)
        laenge = hoehe * (.52 + zufall.uniform(-.07, .07))
        quer = math.cos(w)
        spitze = (kx + laenge * quer, ky + laenge * math.sin(w) + laenge * .45 * abs(quer))
        steuer = ((kx + spitze[0]) / 2, (ky + spitze[1]) / 2 - laenge * .17)
        laengs = (spitze[0] - kx, spitze[1] - ky)
        weite = math.hypot(*laengs) or 1
        senkrecht = (-laengs[1] / weite, laengs[0] / weite)
        bauch = laenge * .12
        teile.append(
            f'<path d="M{kx:.0f},{ky:.0f} '
            f'Q{steuer[0] + senkrecht[0] * bauch:.0f},{steuer[1] + senkrecht[1] * bauch:.0f} '
            f'{spitze[0]:.0f},{spitze[1]:.0f} '
            f'Q{steuer[0] - senkrecht[0] * bauch:.0f},{steuer[1] - senkrecht[1] * bauch:.0f} {kx:.0f},{ky:.0f} Z" '
            f'fill="{wedel_hell if quer > 0 else wedel}"/>')
        teile.append(f'<path d="M{kx:.0f},{ky:.0f} Q{steuer[0]:.0f},{steuer[1]:.0f} {spitze[0]:.0f},{spitze[1]:.0f}" '
                     f'fill="none" stroke="{rippe}" stroke-width="2.5" opacity=".7"/>')
    return "\n".join(teile)


def schilf(x, breite, hoehe, seed, nacht):
    """Ein Büschel Schilf am Wasser."""
    zufall = random.Random(seed)
    farbe = "#1a3038" if nacht else "#5c7a3e"
    halme = []
    for _ in range(7):
        x0 = x + zufall.uniform(-breite, breite)
        h = hoehe * zufall.uniform(.6, 1.2)
        neigung = zufall.uniform(-.5, .5)
        halme.append(f'<path d="M{x0:.0f},{_ufer_y(x0) + 4:.0f} Q{x0 + h * neigung * .4:.0f},'
                     f'{_ufer_y(x0) - h * .6:.0f} {x0 + h * neigung:.0f},{_ufer_y(x0) - h:.0f}" fill="none" '
                     f'stroke="{farbe}" stroke-width="3.5" stroke-linecap="round"/>')
    return "\n".join(halme)


def oase(nacht):
    """Das Wasser der Oase mit Palmen und Schilf – hinter dem Lager in der Mulde.

    Gezeichnet wird zwischen mittlerer Düne und Vordergrund: Die vordere Düne
    deckt das untere Ende des Wassers ab, dadurch liegt es in einer Mulde und
    nicht wie eine Pfütze auf dem Sand. Bewegt wird hier nichts – das Wasser
    liegt ausserhalb der Ausschnitte, in denen Feuer und Rauch spielen.
    """
    zufall = random.Random(77)
    kante = _glatter_zug(UFER)
    teile = [f'<path d="{WASSER_FLAECHE}" fill="url(#wasser)"/>', '<g clip-path="url(#wasserflaeche)">']
    # Die Spiegelung der Palmen: dunkle Streifen unter ihren Stämmen.
    for x, hoehe, neigung, seed in PALMEN:
        oben = _ufer_y(x)
        teile.append(f'<path d="M{x - 13},{oben + 2:.0f} L{x + 13},{oben + 2:.0f} L{x + 7},{oben + 80:.0f} '
                     f'L{x - 7},{oben + 80:.0f} Z" fill="{"#0b1030" if nacht else "#a06a55"}" opacity=".35" '
                     f'filter="url(#weich8)"/>')
    # Das Licht auf dem Wasser – Mond und Sonne stehen rechts.
    teile.append(f'<ellipse cx="1210" cy="{_ufer_y(1210) + 40:.0f}" rx="150" ry="52" fill="url(#wasserglanz)"/>')
    for _ in range(26):
        x = zufall.uniform(60, 1290)
        y = _ufer_y(x) + zufall.uniform(6, 78)
        laenge = zufall.uniform(14, 52)
        teile.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{laenge:.0f}" height="2.5" rx="1.2" '
                     f'fill="{"#cdd7ff" if nacht else "#fff1cd"}" opacity="{zufall.uniform(.15, .5):.2f}"/>')
    teile.append("</g>")
    teile.append(f'<path d="{kante}" fill="none" stroke="{"#7b86c9" if nacht else "#fff0cd"}" stroke-width="3" '
                 f'opacity=".45"/>')
    for x, hoehe, neigung, seed in PALMEN:
        teile.append(palme(x, hoehe, neigung, seed, nacht))
    for x, breite, hoehe, seed in ((95, 45, 60, 3), (400, 55, 52, 6), (700, 50, 46, 12), (1150, 60, 54, 18)):
        teile.append(schilf(x, breite, hoehe, seed, nacht))
    return "\n".join(teile)


def lager(nacht):
    """Rucksack, Decke, Funkgerät und die Feuerstelle – bei Nacht und am Morgen."""
    rx, ry = RUCKSACK
    fx, fy = FEUER
    gx, gy = FUNKGERAET
    dx, dy = DECKE
    stoff = "#3b4a2a" if nacht else "#6b7a45"
    stoff_dunkel = "#262f1b" if nacht else "#4a5530"
    decke = "#4a2231" if nacht else "#8f3f4a"
    decke_streifen = "#6b3346" if nacht else "#c56a6f"
    stein = "#3c3a48" if nacht else "#8d7d73"
    teile = [
        # Die Decke – nachts glatt ausgebreitet, morgens zurückgeschlagen
        (f'<path d="M{dx - 90},{dy - 8} C{dx - 20},{dy - 28} {dx + 150},{dy - 30} {dx + 230},{dy - 12} '
         f'L{dx + 250},{dy + 30} C{dx + 150},{dy + 44} {dx - 10},{dy + 46} {dx - 100},{dy + 30} Z" fill="{decke}"/>'
         if nacht else
         f'<path d="M{dx - 90},{dy - 4} C{dx - 20},{dy - 22} {dx + 90},{dy - 26} {dx + 130},{dy - 14} '
         f'C{dx + 180},{dy - 40} {dx + 250},{dy - 22} {dx + 256},{dy + 6} L{dx + 250},{dy + 30} '
         f'C{dx + 150},{dy + 44} {dx - 10},{dy + 46} {dx - 100},{dy + 30} Z" fill="{decke}"/>'),
        f'<path d="M{dx - 70},{dy + 4} L{dx + 236},{dy - 2} M{dx - 80},{dy + 20} L{dx + 244},{dy + 16}" '
        f'stroke="{decke_streifen}" stroke-width="6" opacity=".8"/>',
        # Rucksack
        f'<rect x="{rx - 48}" y="{ry - 86}" width="96" height="112" rx="26" fill="{stoff}"/>',
        f'<rect x="{rx - 40}" y="{ry - 30}" width="80" height="46" rx="12" fill="{stoff_dunkel}"/>',
        f'<path d="M{rx - 30},{ry - 84} C{rx - 26},{ry - 118} {rx + 26},{ry - 118} {rx + 30},{ry - 84}" fill="none" '
        f'stroke="{stoff_dunkel}" stroke-width="9"/>',
        f'<line x1="{rx - 20}" y1="{ry - 80}" x2="{rx - 20}" y2="{ry - 34}" stroke="{stoff_dunkel}" stroke-width="7"/>',
        f'<line x1="{rx + 20}" y1="{ry - 80}" x2="{rx + 20}" y2="{ry - 34}" stroke="{stoff_dunkel}" stroke-width="7"/>',
        # Das Funkgerät – ausgeschaltet
        f'<rect x="{gx - 44}" y="{gy - 56}" width="88" height="62" rx="10" fill="{"#3e4527" if nacht else "#5f6a38"}"/>',
        f'<rect x="{gx - 34}" y="{gy - 46}" width="68" height="30" rx="4" fill="#0b120c"/>',
        f'<circle cx="{gx - 20}" cy="{gy - 5}" r="6" fill="#15170f"/><circle cx="{gx + 18}" cy="{gy - 5}" r="6" fill="#15170f"/>',
        f'<line x1="{gx + 34}" y1="{gy - 54}" x2="{gx + 70}" y2="{gy - 150}" stroke="#9c9a90" stroke-width="3"/>',
        # Steine um die Feuerstelle
    ]
    for i in range(9):
        w = math.radians(200 + i * 18)
        teile.append(f'<ellipse cx="{fx + math.cos(w) * 64:.0f}" cy="{fy + 10 + math.sin(w) * 20:.0f}" rx="17" ry="11" '
                     f'fill="{stein}"/>')
    # Holz
    if nacht:
        teile.append(f'<path d="M{fx - 52},{fy + 8} L{fx + 40},{fy - 14}" stroke="#3a2418" stroke-width="16" '
                     f'stroke-linecap="round"/>')
        teile.append(f'<path d="M{fx - 40},{fy - 14} L{fx + 52},{fy + 10}" stroke="#4a2e1d" stroke-width="16" '
                     f'stroke-linecap="round"/>')
    else:
        teile.append(f'<ellipse cx="{fx}" cy="{fy + 4}" rx="56" ry="15" fill="#6e6a66" opacity=".85"/>')
        teile.append(f'<path d="M{fx - 48},{fy + 4} L{fx + 38},{fy - 8}" stroke="#221612" stroke-width="13" '
                     f'stroke-linecap="round"/>')
        teile.append(f'<path d="M{fx - 34},{fy - 10} L{fx + 46},{fy + 6}" stroke="#2c1d17" stroke-width="12" '
                     f'stroke-linecap="round"/>')
    for i in range(9, 12):
        w = math.radians(i * 18 - 180)
        teile.append(f'<ellipse cx="{fx + math.cos(w) * 64:.0f}" cy="{fy + 10 + math.sin(w) * 20:.0f}" rx="17" ry="11" '
                     f'fill="{stein}"/>')
    return "\n".join(teile)


def flammen():
    """Das Feuer im Nachtlager – bewegt sich nur im Ausschnitt um die Feuerstelle."""
    fx, fy = FEUER
    zungen = []
    for i, (dx, hoehe, breite, verlauf, dauer) in enumerate((
            (-24, 96, 30, "flamme-aussen", "1s"), (18, 110, 32, "flamme-aussen", ".5s"),
            (-6, 128, 34, "flamme-mitte", "1s"), (10, 88, 24, "flamme-innen", ".5s"),
            (-12, 62, 18, "flamme-kern", "1s"))):
        x0 = fx + dx
        zungen.append(
            f'<path class="zunge" style="animation-duration:{dauer};animation-delay:-{i * .13:.2f}s" '
            f'd="M{x0 - breite},{fy} C{x0 - breite},{fy - hoehe * .5} {x0 - 4},{fy - hoehe * .7} {x0},{fy - hoehe} '
            f'C{x0 + 6},{fy - hoehe * .66} {x0 + breite},{fy - hoehe * .45} {x0 + breite},{fy} Z" '
            f'fill="url(#{verlauf})"/>')
    funken = "\n".join(
        f'<circle class="funke" style="--dx:{rnd.uniform(-30, 30):.0f}px;--dy:{-rnd.uniform(90, 150):.0f}px;'
        f'animation-delay:-{rnd.uniform(0, 2):.2f}s" cx="{fx + rnd.uniform(-14, 14):.0f}" cy="{fy - 40}" r="2.4" '
        f'fill="#ffd27a"/>' for _ in range(6))
    return "\n".join(zungen) + "\n" + funken


FEUER_BEREICH = (FEUER[0] - 80, FEUER[1] - 200, 160, 230)
RAUCH_BEREICH = (FEUER[0] - 90, FEUER[1] - 330, 190, 350)

GEMEINSAME_DEFS = '''
  <filter id="weich2" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2"/></filter>
  <filter id="weich8" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>
  <filter id="weich30" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="30"/></filter>'''


def nachtlager_svg():
    fx, fy = FEUER
    bx, by, bb, bh = FEUER_BEREICH
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B} {H}"
     data-breite="960" data-schleife-ms="4000" data-bilder="40" data-bereiche="{bx} {by} {bb} {bh}">
<!--
  Das Nachtlager an der Oase – Szene für den Abschluss (Arbeitsplan 6.8).
  Entsteht mit grafik/abschluss_zeichnen.py – dort ändern, nicht hier.

  Fürs Spiel vorrendern mit:
      python3 grafik/rendern.py grafik/nachtlager.svg
  Bewegt wird nur das Feuer (data-bereiche). Oben links bleibt der Himmel ruhig: Dort steht im Spiel der Text.
-->
<title>Das Nachtlager</title>
<desc>Nacht an einer Oase: ein klarer Sternenhimmel mit Milchstraße und Mondsichel über dunklen Dünen.
Hinter dem Lager liegt das Wasser der Oase, in dem sich das Mondlicht spiegelt, dahinter stehen Palmen.
Vorn links brennt ein kleines Lagerfeuer zwischen Steinen, daneben liegen ein Rucksack, eine ausgebreitete
Decke und das ausgeschaltete Funkgerät.</desc>
<style>
  /* Alle Dauern teilen 4 s – so wiederholt die vorgerenderte Bildfolge ohne Sprung. */
  .zunge {{ transform-box: fill-box; transform-origin: 50% 100%; animation: flackern 1s ease-in-out infinite alternate; }}
  @keyframes flackern {{
    0%   {{ transform: scale(1, 1) skewX(0deg); }}
    50%  {{ transform: scale(1.1, .88) skewX(-7deg); }}
    100% {{ transform: scale(.92, 1.12) skewX(5deg); }}
  }}
  .funke {{ animation: funkenflug 2s ease-out infinite; }}
  @keyframes funkenflug {{
    0%   {{ transform: translate(0, 0); opacity: 0; }}
    15%  {{ opacity: 1; }}
    100% {{ transform: translate(var(--dx), var(--dy)); opacity: 0; }}
  }}
  .schein {{ animation: pulsieren 1s ease-in-out infinite alternate; }}
  @keyframes pulsieren {{ 0% {{ opacity: .55; }} 100% {{ opacity: 1; }} }}
</style>
<defs>
  <linearGradient id="himmel" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#03051a"/><stop offset=".35" stop-color="#0a0f2e"/>
    <stop offset=".55" stop-color="#161d46"/><stop offset=".64" stop-color="#262f5c"/>
    <stop offset="1" stop-color="#262f5c"/>
  </linearGradient>
  <linearGradient id="berge" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#151a3a"/><stop offset="1" stop-color="#0f1330"/>
  </linearGradient>
  <linearGradient id="duene-fern" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#232649"/><stop offset="1" stop-color="#181a36"/>
  </linearGradient>
  <linearGradient id="duene-mitte" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2e2d52"/><stop offset="1" stop-color="#1f1e3a"/>
  </linearGradient>
  <linearGradient id="boden" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#3a3354"/><stop offset="1" stop-color="#1c1830"/>
  </linearGradient>
  <linearGradient id="wasser" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#151d4c"/><stop offset=".5" stop-color="#1e2a66"/>
    <stop offset="1" stop-color="#2b3a7d"/>
  </linearGradient>
  <radialGradient id="wasserglanz" cx="1210" cy="740" r="170" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#dfe6ff" stop-opacity=".45"/><stop offset="1" stop-color="#dfe6ff" stop-opacity="0"/>
  </radialGradient>
  <clipPath id="wasserflaeche"><path d="{WASSER_FLAECHE}"/></clipPath>
  <radialGradient id="mondschein" cx="1360" cy="140" r="260" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#dfe6ff" stop-opacity=".22"/><stop offset="1" stop-color="#dfe6ff" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="feuerschein" cx="{fx}" cy="{fy}" r="360" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#ff9a3c" stop-opacity=".45"/><stop offset=".45" stop-color="#ff7a22" stop-opacity=".16"/>
    <stop offset="1" stop-color="#ff5a14" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="glut" cx="{fx}" cy="{fy - 30}" r="70" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#ffc46a" stop-opacity=".55"/><stop offset="1" stop-color="#ff7a22" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="flamme-aussen" x1="0" y1="1" x2="0" y2="0">
    <stop offset="0" stop-color="#ff5a14"/><stop offset=".6" stop-color="#ff3d10" stop-opacity=".8"/>
    <stop offset="1" stop-color="#c81e0a" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="flamme-mitte" x1="0" y1="1" x2="0" y2="0">
    <stop offset="0" stop-color="#ffb238"/><stop offset=".6" stop-color="#ff8a1c" stop-opacity=".9"/>
    <stop offset="1" stop-color="#ff6a14" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="flamme-innen" x1="0" y1="1" x2="0" y2="0">
    <stop offset="0" stop-color="#fff0b0"/><stop offset=".5" stop-color="#ffd45c"/>
    <stop offset="1" stop-color="#ffb030" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="flamme-kern" x1="0" y1="1" x2="0" y2="0">
    <stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#fff6d6" stop-opacity=".9"/>
    <stop offset="1" stop-color="#ffe28a" stop-opacity="0"/>
  </linearGradient>
  <mask id="sichel">
    <rect width="{B}" height="{H}" fill="#000"/>
    <circle cx="1360" cy="140" r="46" fill="#fff"/>
    <circle cx="1382" cy="126" r="42" fill="#000"/>
  </mask>{GEMEINSAME_DEFS}
</defs>

<rect width="{B}" height="{H}" fill="url(#himmel)"/>
<!-- Milchstraße: ein weiches Band schräg über den Himmel, rechts vom Text -->
<ellipse cx="1000" cy="250" rx="760" ry="70" transform="rotate(-24 1000 250)" fill="#b9c3ff" opacity=".10"
         filter="url(#weich30)"/>
<g>
{sterne(170, 0, HORIZONT - 30)}
</g>
<g>
{sterne(90, 120, 420, deckkraft=(.3, .8), groesse=(.5, 1.1), farbe="#dfe6ff")}
</g>
<!-- Mondsichel oben rechts -->
<rect width="{B}" height="{H}" fill="url(#mondschein)"/>
<rect width="{B}" height="{H}" fill="#f4ecd0" mask="url(#sichel)"/>

<path d="{BERGE}" fill="url(#berge)"/>
<path d="{DUENE_FERN}" fill="url(#duene-fern)"/>
<path d="{DUENE_MITTE}" fill="url(#duene-mitte)"/>
<!-- Die Oase in der Mulde: Wasser, Palmen, Schilf -->
{oase(nacht=True)}
<path d="{BODEN}" fill="url(#boden)"/>
<!-- Mondlicht auf den Kämmen -->
<path d="{DUENE_MITTE}" fill="none" stroke="#5a5f9a" stroke-width="2" opacity=".35"/>

<!-- Das Lager -->
<!-- Der große Feuerschein steht still; nur die Glut direkt am Feuer pulsiert – im Ausschnitt -->
<rect width="{B}" height="{H}" fill="url(#feuerschein)"/>
{lager(nacht=True)}
<circle class="schein" cx="{fx}" cy="{fy - 30}" r="70" fill="url(#glut)"/>
<g>
{flammen()}
</g>
</svg>
'''


def rauch():
    """Ein dünner Rauchfaden über der erloschenen Feuerstelle – bewegt sich nur im Ausschnitt."""
    fx, fy = FEUER
    return "\n".join(
        f'<circle class="puff" style="--px:{rnd.uniform(-40, 30):.0f}px;--py:{-rnd.uniform(220, 280):.0f}px;'
        f'animation-delay:-{i:.1f}s" cx="{fx + rnd.uniform(-6, 6):.0f}" cy="{fy - 14}" r="{rnd.uniform(12, 18):.0f}" '
        f'fill="#e9e4f0" filter="url(#weich8)"/>' for i in (0, .5, 1, 1.5, 2, 2.5, 3, 3.5))


def morgen_svg():
    bx, by, bb, bh = RAUCH_BEREICH
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B} {H}"
     data-breite="960" data-schleife-ms="4000" data-bilder="40" data-bereiche="{bx} {by} {bb} {bh}">
<!--
  Dieselbe Oase im Morgengrauen – Szene für den Abschluss (Arbeitsplan 6.8).
  Entsteht mit grafik/abschluss_zeichnen.py – dort ändern, nicht hier.

  Fürs Spiel vorrendern mit:
      python3 grafik/rendern.py grafik/morgen.svg
  Bewegt wird nur der Rauch über der Feuerstelle (data-bereiche). Rechts auf dem ebenen Sand landet im Spiel
  der Hubschrauber, oben links steht der Text.
-->
<title>Das Lager am Morgen</title>
<desc>Morgengrauen über derselben Oase: Der Himmel geht von Blau über Rosa in ein warmes Orange über, rechts
am Horizont kündigt sich die Sonne an, die letzten Sterne verblassen. Im Wasser spiegelt sich das Morgenlicht,
die Palmen sind grün. Das Feuer ist aus, ein dünner Rauchfaden steigt auf; Rucksack, zurückgeschlagene Decke
und Funkgerät liegen noch da. Rechts neben der Oase ist ebener Sand.</desc>
<style>
  /* Alle Dauern teilen 4 s. */
  .puff {{ transform-box: fill-box; transform-origin: center; opacity: 0; animation: aufsteigen 4s linear infinite; }}
  @keyframes aufsteigen {{
    0%   {{ transform: translate(0, 0) scale(.5); opacity: 0; }}
    15%  {{ opacity: .45; }}
    75%  {{ opacity: 0; }}
    100% {{ transform: translate(var(--px), var(--py)) scale(2); opacity: 0; }}
  }}
</style>
<defs>
  <linearGradient id="himmel" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#1d2a5c"/><stop offset=".3" stop-color="#4c4f8a"/>
    <stop offset=".47" stop-color="#a7728f"/><stop offset=".56" stop-color="#e8977a"/>
    <stop offset=".62" stop-color="#ffc98f"/><stop offset="1" stop-color="#ffc98f"/>
  </linearGradient>
  <radialGradient id="sonne" cx="1240" cy="{HORIZONT}" r="520" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#fff2c4" stop-opacity=".95"/><stop offset=".25" stop-color="#ffd48a" stop-opacity=".55"/>
    <stop offset="1" stop-color="#ffb070" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="berge" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#8c6788"/><stop offset="1" stop-color="#6d5176"/>
  </linearGradient>
  <linearGradient id="duene-fern" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#d59379"/><stop offset="1" stop-color="#ad7063"/>
  </linearGradient>
  <linearGradient id="duene-mitte" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#eaa77a"/><stop offset="1" stop-color="#c07f60"/>
  </linearGradient>
  <linearGradient id="boden" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#f2bf8c"/><stop offset="1" stop-color="#cf9168"/>
  </linearGradient>
  <linearGradient id="wasser" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#9ab8c4"/><stop offset=".4" stop-color="#6e97b0"/>
    <stop offset="1" stop-color="#4d7391"/>
  </linearGradient>
  <radialGradient id="wasserglanz" cx="1210" cy="740" r="190" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#fff2c4" stop-opacity=".8"/><stop offset="1" stop-color="#fff2c4" stop-opacity="0"/>
  </radialGradient>
  <clipPath id="wasserflaeche"><path d="{WASSER_FLAECHE}"/></clipPath>
{GEMEINSAME_DEFS}
</defs>

<rect width="{B}" height="{H}" fill="url(#himmel)"/>
<rect width="{B}" height="{H}" fill="url(#sonne)"/>
<g>
{sterne(22, 0, 200, deckkraft=(.15, .5), groesse=(.6, 1.4))}
</g>

<path d="{BERGE}" fill="url(#berge)"/>
<path d="{DUENE_FERN}" fill="url(#duene-fern)"/>
<path d="{DUENE_MITTE}" fill="url(#duene-mitte)"/>
<!-- Die Oase in der Mulde: Wasser, Palmen, Schilf -->
{oase(nacht=False)}
<path d="{BODEN}" fill="url(#boden)"/>
<!-- Lange Morgenschatten nach links, die Sonne steht rechts -->
<path d="{DUENE_MITTE}" fill="none" stroke="#fff0d0" stroke-width="3" opacity=".35"/>
<ellipse cx="330" cy="800" rx="420" ry="34" fill="#7f5a78" opacity=".22" filter="url(#weich30)"/>

<!-- Das Lager -->
{lager(nacht=False)}
<g>
{rauch()}
</g>
</svg>
'''


#: Der Hauptrotor, von leicht oben gesehen: Nabe, Blattlänge und wie hoch die flache Scheibe
#: erscheint, die die Blätter überstreichen (Einheiten).
NABE = (300, 54)
BLATT = 292
SCHEIBE = 18
#: Der Heckrotor dreht sich in der Ebene des Bilds – seine Scheibe ist rund.
HECKNABE = (632, 116)
HECKBLATT = 28
#: Alle 50 ms kommt ein Bild, 16 Stellungen je Schleife. Der Hauptrotor hat vier Blätter
#: und dreht sich je Bild um 22,5° – ein Viertel des Wegs zum nächsten Blatt; der Heckrotor
#: hat zwei und dreht sich um 45°, ebenfalls ein Viertel. So liest das Auge die Drehung
#: eindeutig. Vier Blätter, weil von der Seite gesehen immer eins lang quer steht; zwei
#: verschwänden jedes zweite Bild, wenn sie gerade auf einen zeigen. (Vorher schwankten
#: zwei Blätter nur in der Länge, und das Bild flackerte zwischen lang und kurz.)
SCHLEIFE_MS = 800
STELLUNGEN = 16
#: Je Rotor: Zahl der Blätter und Drehung je Bild in Grad – der Heckrotor dreht andersherum.
HAUPTROTOR = (4, 360 / STELLUNGEN)
HECKROTOR = (2, -2 * 360 / STELLUNGEN)
#: Die Unschärfe hinter einem Blatt: Tortenstücke der Scheibe, je (Winkel, Deckkraft).
WISCHER = ((40, .07), (24, .09), (10, .12))
FARBE_BLATT = "#1b1f21"


def _auf_scheibe(zentrum, rx, ry, winkel, anteil=1.0):
    w = math.radians(winkel)
    return zentrum[0] + rx * anteil * math.cos(w), zentrum[1] + ry * anteil * math.sin(w)


def _wisch(zentrum, rx, ry, von, bis, deckkraft):
    rand = [_auf_scheibe(zentrum, rx, ry, von + (bis - von) * i / 8) for i in range(9)]
    return f'<polygon points="{punkte([zentrum] + rand)}" fill="{FARBE_BLATT}" opacity="{deckkraft}"/>'


def _blatt(zentrum, rx, ry, winkel, breite, spitze=None):
    x0, y0 = zentrum
    x1, y1 = _auf_scheibe(zentrum, rx, ry, winkel)
    teile = [f'<line x1="{x0}" y1="{y0}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{FARBE_BLATT}" '
             f'stroke-width="{breite}" stroke-linecap="round"/>']
    # Zeigt das Blatt fast genau auf einen zu, wäre die Spitze nur ein goldener Punkt am Mast.
    if spitze and abs(math.cos(math.radians(winkel))) > .25:
        xs, ys = _auf_scheibe(zentrum, rx, ry, winkel, .88)
        teile.append(f'<line x1="{xs:.1f}" y1="{ys:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{spitze}" '
                     f'stroke-width="{breite}" stroke-linecap="round"/>')
    return teile


def blattwinkel(rotor, nr):
    """Wo die Blätter von ``rotor`` in Stellung ``nr`` stehen, in Grad (0° zeigt nach rechts)."""
    blaetter, schritt = rotor
    return [nr * schritt + 360 / blaetter * k for k in range(blaetter)]


def rotorstellung(nr):
    """Beide Rotoren in Stellung ``nr`` – jedes Blatt mit der Unschärfe dahinter.

    Der Hauptrotor dreht sich vorn von links nach rechts, der Heckrotor
    andersherum. Die Blattspitzen des Hauptrotors sind golden wie der Streifen.
    """
    haupt = blattwinkel(HAUPTROTOR, nr)
    heck = blattwinkel(HECKROTOR, nr)
    teile = []
    for blatt in haupt:
        teile += [_wisch(NABE, BLATT, SCHEIBE, blatt - breite, blatt, deckkraft) for breite, deckkraft in WISCHER]
    for blatt in heck:
        teile += [_wisch(HECKNABE, HECKBLATT, HECKBLATT, blatt, blatt + breite, deckkraft * 1.4)
                  for breite, deckkraft in WISCHER]
    # Die hinteren Blätter (über der Nabe) zuerst, die vorderen liegen darüber.
    for blatt in sorted(haupt, key=lambda w: math.sin(math.radians(w))):
        teile += _blatt(NABE, BLATT, SCHEIBE, blatt, 7, spitze="#e2b651")
    for blatt in heck:
        teile += _blatt(HECKNABE, HECKBLATT, HECKBLATT, blatt, 7)
    return teile


def rotoren():
    """Alle Stellungen übereinander; jede ist genau in ihrem 50-ms-Fenster zu sehen.

    Das Fenster liegt mittig um den Zeitpunkt, zu dem ``grafik/rendern.py`` das
    Bild nimmt – ein Rundungsfehler an der Kante kann so kein falsches Bild
    zeigen.
    """
    takt = SCHLEIFE_MS // STELLUNGEN
    gruppen = []
    for nr in range(STELLUNGEN):
        verzoegerung = nr * takt - takt // 2 - SCHLEIFE_MS
        inhalt = "\n  ".join(rotorstellung(nr))
        gruppen.append(f'<g class="stellung" style="animation-delay: {verzoegerung}ms">\n  {inhalt}\n</g>')
    return "\n".join(gruppen)


def hubschrauber_svg():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 320"
     data-breite="340" data-schleife-ms="800" data-bilder="16" data-bereiche="0 0 680 320" data-durchsichtig="ja">
<!--
  Der Hubschrauber der Crew – für den Abschluss (Arbeitsplan 6.8).
  Entsteht mit grafik/abschluss_zeichnen.py – dort ändern, nicht hier.

  Fürs Spiel vorrendern mit:
      python3 grafik/rendern.py grafik/hubschrauber.svg
  Durchsichtig und in Schleife: Die Rotoren drehen sich, das grüne Licht blinkt.
  Das Spiel lässt ihn über die Morgenszene fliegen und landen.
  Freund, nicht Feind: dunkelgrün mit Goldstreifen und großem goldenem Diamanten – kein Blaulicht, keine Aufschrift.
-->
<title>Der Hubschrauber der Crew</title>
<desc>Ein dunkelgrüner Hubschrauber von der Seite, nach links gewandt, mit goldenem Streifen und einem großen
goldenen Diamanten auf der Seite. Die Rotoren drehen sich, und am Heck blinkt ein grünes Licht.</desc>
<style>
  /* Alle Dauern teilen 800 ms. Von den Rotorstellungen ist immer genau eine zu sehen. */
  .stellung {{ opacity: 0; animation: stellung {SCHLEIFE_MS / 1000:g}s steps(1) infinite; }}
  @keyframes stellung {{ 0% {{ opacity: 1; }} {100 / STELLUNGEN:g}% {{ opacity: 0; }} }}
  .licht {{ animation: blinken .8s steps(1) infinite; }}
  @keyframes blinken {{ 0% {{ opacity: 1; }} 50% {{ opacity: .15; }} }}
</style>
<defs>
  <linearGradient id="lack" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#3f8a72"/><stop offset=".45" stop-color="#276552"/>
    <stop offset="1" stop-color="#173e33"/>
  </linearGradient>
  <linearGradient id="glas" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#cfe9f2"/><stop offset=".4" stop-color="#7fb0c4"/>
    <stop offset="1" stop-color="#2f5566"/>
  </linearGradient>
  <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#fff0b0"/><stop offset=".45" stop-color="#e2b651"/>
    <stop offset="1" stop-color="#9a7020"/>
  </linearGradient>
  <linearGradient id="metall" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#6d7478"/><stop offset="1" stop-color="#2e3336"/>
  </linearGradient>
  <filter id="weich" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3"/></filter>
</defs>

<!-- Kufen, hinten und vorn -->
<g stroke="#2a2f31" stroke-linecap="round" fill="none">
  <path d="M132,254 L150,212 M364,254 L352,212" stroke-width="7"/>
  <path d="M96,256 C104,244 112,244 124,246 L440,246" stroke-width="8"/>
</g>
<g stroke="url(#metall)" stroke-linecap="round" fill="none">
  <path d="M168,272 L182,214 M392,272 L376,214" stroke-width="9"/>
  <path d="M112,276 C120,262 132,262 146,264 L470,264" stroke-width="10"/>
</g>

<!-- Heckausleger und Leitwerk -->
<path d="M420,112 L640,128 L640,146 L420,176 Z" fill="url(#lack)"/>
<path d="M600,128 L626,70 L660,70 L650,148 L618,146 Z" fill="url(#lack)"/>
<path d="M430,146 L636,137" stroke="#e2b651" stroke-width="5"/>
<circle class="licht" cx="650" cy="78" r="9" fill="#5dff7a"/>
<circle class="licht" cx="650" cy="78" r="18" fill="#5dff7a" opacity=".35" filter="url(#weich)"/>
<!-- Die Scheibe des Heckrotors -->
<circle cx="{HECKNABE[0]}" cy="{HECKNABE[1]}" r="{HECKBLATT + 3}" fill="#dfe6e8" opacity=".12"/>

<!-- Die Kabine -->
<path d="M70,152 C66,112 104,88 160,84 L398,84 C430,86 446,104 446,128 L446,186 C446,210 430,224 402,226
         L150,226 C104,226 74,200 70,152 Z" fill="url(#lack)"/>
<path d="M98,112 C112,94 140,88 166,88 L396,88" fill="none" stroke="#8fd1b8" stroke-width="3" opacity=".5"/>
<!-- Das Cockpitfenster vorn -->
<path d="M78,150 C76,118 104,96 150,94 L186,94 L186,170 L84,170 C80,164 78,158 78,150 Z" fill="url(#glas)"/>
<path d="M104,110 C118,102 136,100 156,100" fill="none" stroke="#ffffff" stroke-width="5" opacity=".55"
      stroke-linecap="round"/>
<!-- Die Schiebetür mit Fenster, geschlossen -->
<rect x="210" y="98" width="100" height="124" rx="8" fill="none" stroke="#173e33" stroke-width="3"/>
<rect x="222" y="108" width="76" height="54" rx="7" fill="url(#glas)"/>
<path d="M232,118 C244,113 258,112 270,113" fill="none" stroke="#ffffff" stroke-width="4" opacity=".5"
      stroke-linecap="round"/>
<path d="M206,93 L322,93" stroke="#173e33" stroke-width="3" stroke-linecap="round"/>
<!-- Goldstreifen -->
<path d="M84,184 L446,184" stroke="#e2b651" stroke-width="9"/>
<rect x="284" y="196" width="16" height="6" rx="3" fill="url(#metall)"/>

<!-- Das Zeichen der Crew: ein großer goldener Diamant -->
<g transform="translate(392,146)">
  <polygon points="-34,-12 -18,-30 18,-30 34,-12 0,34" fill="url(#gold)" stroke="#6b4d12" stroke-width="2.5"/>
  <polyline points="-34,-12 34,-12" fill="none" stroke="#6b4d12" stroke-width="2"/>
  <polyline points="-18,-30 -10,-12 0,34 10,-12 18,-30" fill="none" stroke="#8c6818" stroke-width="1.6"/>
  <polygon points="-18,-30 -10,-12 -34,-12" fill="#fff6d0" opacity=".55"/>
</g>

<!-- Rotormast und die Scheibe des Hauptrotors -->
<rect x="{NABE[0] - 10}" y="{NABE[1] + 6}" width="20" height="{84 - NABE[1] - 4}" rx="4" fill="url(#metall)"/>
<ellipse cx="{NABE[0]}" cy="{NABE[1]}" rx="{BLATT}" ry="{SCHEIBE}" fill="{FARBE_BLATT}" opacity=".05"
         stroke="{FARBE_BLATT}" stroke-width="2" stroke-opacity=".12"/>

<!-- Die Rotoren: 16 Stellungen, je 50 ms -->
{rotoren()}

<!-- Die Naben -->
<circle cx="{NABE[0]}" cy="{NABE[1]}" r="11" fill="url(#metall)"/>
<circle cx="{HECKNABE[0]}" cy="{HECKNABE[1]}" r="6" fill="url(#metall)"/>
</svg>
"""

def main():
    for name, inhalt in (("nachtlager", nachtlager_svg()), ("morgen", morgen_svg()),
                         ("hubschrauber", hubschrauber_svg())):
        ziel = ORDNER / f"{name}.svg"
        ziel.write_text(inhalt, encoding="utf-8")
        print(f"geschrieben: {ziel}")


if __name__ == "__main__":
    main()
