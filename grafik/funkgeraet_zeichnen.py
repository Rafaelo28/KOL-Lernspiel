"""Zeichnet das Kurzwellen-Funkgerät für den Funk-Screen (Arbeitsplan 6.6).

Erzeugt ``grafik/funkgeraet.svg``, das danach wie jede Animation vorgerendert
wird (``dokumentation/Animationen.md``)::

    python3 grafik/funkgeraet_zeichnen.py
    python3 grafik/rendern.py grafik/funkgeraet.svg

Das Gerät ist ein durchsichtiges Standbild. Im Spiel steht es rechts auf dem
aufgeschlagenen Handbuch: Links bleibt die Seite mit dem Werkzeug frei, wie
bei den Übungen – rechts ist Technik statt Papier. So sieht man schon am
Bild, ob geübt wird oder ob es ernst ist.

Was nicht im Bild steht
───────────────────────
Die Anzeige ist leeres, dunkles Glas: Nachricht, Eingabe und Rückmeldung
schreibt das Spiel darauf (``ui/funk.py``), Zeichen für Zeichen, als kämen
sie gerade herein. Auch die beiden Lämpchen sind hier aus – das Spiel lässt
sie leuchten. Ihre Lage steht deshalb an zwei Stellen: hier in SVG-Einheiten,
in ``ui/funk.py`` in Pixeln (halb so groß). Ein Test prüft im gerenderten
Bild, dass dort Glas und Fassungen sind.

Maße
────
In SVG-Einheiten, gezählt ab der linken oberen Ecke des Bilds; im Spiel ist
eine Einheit ein halber Pixel (Maßstab 1).
"""

import math
import pathlib
import random

ORDNER = pathlib.Path(__file__).resolve().parent

B, H = 920, 960                    # das Bild; im Spiel 460 × 480 Pixel

# Das Gehäuse
GX0, GY0, GX1, GY1 = 24, 96, 896, 940
# Die Frontplatte darin
PX0, PY0, PX1, PY1 = 56, 132, 864, 912
#: Das Glas der Anzeige (x0, y0, x1, y1) – dort schreibt das Spiel.
GLAS = (92, 170, 828, 698)
# Der Rahmen um das Glas
RAHMEN = (72, 150, 848, 718)
# Die Frequenzskala
SKALA = (96, 744, 430, 850)
# Der große Abstimmknopf
KNOPF = (528, 800, 54)
#: Die Fassungen der Lämpchen (x, y, r): links Empfang, rechts Senden.
LAMPE_EMPFANG = (650, 770, 22)
LAMPE_SENDEN = (764, 770, 22)
# Die Kippschalter darunter
SCHALTER = ((650, 870), (764, 870))
# Der Lautsprecher
LAUTSPRECHER = (808, 744, 846, 872)
# Henkel und Antenne
HENKEL_X = (262, 658)
ANTENNE_FUSS, ANTENNE_SPITZE = (812, 126), (884, 10)

#: Immer derselbe Zufall – sonst sähe das Gerät nach jedem Neuzeichnen anders aus.
rnd = random.Random(1947)


def schraube(x, y, r=10):
    """Eine Kreuzschlitzschraube in der Ecke."""
    winkel = rnd.uniform(0, 90)
    dx, dy = math.cos(math.radians(winkel)) * r * .62, math.sin(math.radians(winkel)) * r * .62
    return (f'<circle cx="{x}" cy="{y}" r="{r + 2}" fill="#20251a" opacity=".55"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#schraube)"/>'
            f'<path d="M{x - dx:.1f},{y - dy:.1f} L{x + dx:.1f},{y + dy:.1f} M{x + dy:.1f},{y - dx:.1f} '
            f'L{x - dy:.1f},{y + dx:.1f}" stroke="#2b2f24" stroke-width="2.4" stroke-linecap="round"/>')


def skala():
    """Die Frequenzskala: ein Fenster mit Strichen, Bereichsmarken und einem roten Zeiger."""
    x0, y0, x1, y1 = SKALA
    teile = [f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="10" fill="#1b1d15" '
             f'stroke="#0b0c08" stroke-width="3"/>',
             f'<rect x="{x0 + 8}" y="{y0 + 8}" width="{x1 - x0 - 16}" height="{y1 - y0 - 16}" rx="6" '
             f'fill="url(#skalenglas)"/>']
    links, rechts = x0 + 28, x1 - 28
    for i in range(41):
        x = links + (rechts - links) * i / 40
        lang = 26 if i % 10 == 0 else (18 if i % 5 == 0 else 10)
        teile.append(f'<line x1="{x:.1f}" y1="{y0 + 22}" x2="{x:.1f}" y2="{y0 + 22 + lang}" '
                     f'stroke="#e8dcc0" stroke-width="{2.2 if i % 10 == 0 else 1.4}" opacity=".85"/>')
    for i, zahl in enumerate(("3", "6", "9", "12", "15")):
        x = links + (rechts - links) * i / 4
        teile.append(f'<text x="{x:.1f}" y="{y1 - 22}" text-anchor="middle" font-family="DejaVu Sans" '
                     f'font-size="22" fill="#e8dcc0" opacity=".8">{zahl}</text>')
    zeiger = links + (rechts - links) * .43
    teile.append(f'<line x1="{zeiger:.1f}" y1="{y0 + 14}" x2="{zeiger:.1f}" y2="{y1 - 14}" stroke="#d8452e" '
                 f'stroke-width="3.2"/>')
    teile.append(f'<rect x="{x0 + 8}" y="{y0 + 8}" width="{x1 - x0 - 16}" height="{(y1 - y0 - 16) / 2:.0f}" '
                 f'rx="6" fill="#ffffff" opacity=".06"/>')
    return "\n  ".join(teile)


def abstimmknopf():
    """Der große Knopf mit Riffelung und Markierung."""
    x, y, r = KNOPF
    teile = [f'<circle cx="{x + 4}" cy="{y + 7}" r="{r + 4}" fill="#000" opacity=".45" filter="url(#weich)"/>',
             f'<circle cx="{x}" cy="{y}" r="{r + 3}" fill="#101109"/>']
    for i in range(48):
        w = math.radians(i * 7.5)
        teile.append(f'<line x1="{x + math.cos(w) * (r - 7):.1f}" y1="{y + math.sin(w) * (r - 7):.1f}" '
                     f'x2="{x + math.cos(w) * r:.1f}" y2="{y + math.sin(w) * r:.1f}" stroke="#3a3d33" '
                     f'stroke-width="3"/>')
    teile.append(f'<circle cx="{x}" cy="{y}" r="{r - 8}" fill="url(#knopf)"/>')
    teile.append(f'<circle cx="{x}" cy="{y}" r="{r - 24}" fill="none" stroke="#565a4b" stroke-width="2" opacity=".6"/>')
    teile.append(f'<line x1="{x}" y1="{y - r + 14}" x2="{x}" y2="{y - r + 34}" stroke="#e8dcc0" stroke-width="5" '
                 f'stroke-linecap="round" transform="rotate(38 {x} {y})"/>')
    return "\n  ".join(teile)


def lampe(x, y, r, beschriftung):
    """Die Fassung eines Lämpchens – das Glas bleibt dunkel, leuchten lässt es das Spiel."""
    return (f'<circle cx="{x}" cy="{y}" r="{r + 9}" fill="url(#chrom)"/>'
            f'<circle cx="{x}" cy="{y}" r="{r + 3}" fill="#0c0d09"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#lampenglas)"/>'
            f'<text x="{x}" y="{y + r + 26}" text-anchor="middle" font-family="DejaVu Sans" font-size="15" '
            f'font-weight="bold" letter-spacing=".5" fill="#d9ceb2" opacity=".75">{beschriftung}</text>')


def kippschalter(x, y, oben=True):
    """Ein Kippschalter mit Sechskantmutter; der Hebel steht nach oben oder unten."""
    richtung = -1 if oben else 1
    mutter = " ".join(f"{x + math.cos(math.radians(60 * i + 30)) * 20:.1f},"
                      f"{y + math.sin(math.radians(60 * i + 30)) * 20:.1f}" for i in range(6))
    return (f'<circle cx="{x}" cy="{y}" r="27" fill="#141510"/>'
            f'<polygon points="{mutter}" fill="url(#chrom)" stroke="#2a2c22" stroke-width="1.5"/>'
            f'<line x1="{x}" y1="{y}" x2="{x + 6}" y2="{y + richtung * 34}" stroke="#1a1b14" stroke-width="13" '
            f'stroke-linecap="round" opacity=".5" transform="translate(3,4)"/>'
            f'<line x1="{x}" y1="{y}" x2="{x + 6}" y2="{y + richtung * 34}" stroke="url(#hebel)" stroke-width="11" '
            f'stroke-linecap="round"/>'
            f'<circle cx="{x}" cy="{y}" r="7" fill="#c9c6b8"/>')


def lautsprecher():
    """Schlitze für den Lautsprecher."""
    x0, y0, x1, y1 = LAUTSPRECHER
    teile = []
    for i in range(3):
        x = x0 + 6 + i * (x1 - x0 - 12) / 2
        teile.append(f'<rect x="{x - 4:.1f}" y="{y0}" width="8" height="{y1 - y0}" rx="4" fill="#0a0b07"/>')
        teile.append(f'<rect x="{x - 4:.1f}" y="{y0}" width="8" height="{y1 - y0}" rx="4" fill="none" '
                     f'stroke="#5b6147" stroke-width="1.2" opacity=".5"/>')
    return "\n  ".join(teile)


def kratzer():
    """Ein paar Gebrauchsspuren auf dem Gehäuse – nur am Rand, nie auf dem Glas."""
    teile = []
    for _ in range(26):
        seite = rnd.choice("olur")
        if seite == "o":
            x, y = rnd.uniform(GX0 + 40, GX1 - 40), rnd.uniform(GY0 + 8, PY0 - 8)
        elif seite == "u":
            x, y = rnd.uniform(GX0 + 40, GX1 - 40), rnd.uniform(PY1 + 6, GY1 - 8)
        elif seite == "l":
            x, y = rnd.uniform(GX0 + 6, PX0 - 6), rnd.uniform(GY0 + 40, GY1 - 40)
        else:
            x, y = rnd.uniform(PX1 + 6, GX1 - 6), rnd.uniform(GY0 + 40, GY1 - 40)
        w, l = rnd.uniform(0, math.pi), rnd.uniform(6, 22)
        teile.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x + math.cos(w) * l:.0f}" y2="{y + math.sin(w) * l:.0f}" '
                     f'stroke="#cfd3b8" stroke-width="1.2" opacity="{rnd.uniform(.15, .35):.2f}"/>')
    return "\n  ".join(teile)


def funkgeraet_svg():
    """Die SVG-Datei des Funkgeräts – ein Standbild, auf dessen Glas das Spiel später schreibt."""
    gx0, gy0, gx1, gy1 = GX0, GY0, GX1, GY1
    px0, py0, px1, py1 = PX0, PY0, PX1, PY1
    rx0, ry0, rx1, ry1 = RAHMEN
    sx0, sy0, sx1, sy1 = GLAS
    hl, hr = HENKEL_X
    ax, ay = ANTENNE_FUSS
    tx, ty = ANTENNE_SPITZE
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B} {H}"
     data-breite="{B // 2}" data-standbild="ja" data-durchsichtig="ja">
<!--
  Das Kurzwellen-Funkgerät für den Funk-Screen (Arbeitsplan 6.6).
  Entsteht mit grafik/funkgeraet_zeichnen.py – dort ändern, nicht hier.

  Fürs Spiel vorrendern mit:
      python3 grafik/rendern.py grafik/funkgeraet.svg
  Auf das Glas (x {sx0}–{sx1}, y {sy0}–{sy1}) schreibt das Spiel, und die Lämpchen bei
  ({LAMPE_EMPFANG[0]}, {LAMPE_EMPFANG[1]}) und ({LAMPE_SENDEN[0]}, {LAMPE_SENDEN[1]}) lässt es leuchten –
  ui/funk.py rechnet mit genau diesen Maßen, dort in Pixeln und halb so groß.
-->
<title>Kurzwellen-Funkgerät</title>
<desc>Ein olivgrünes Feldfunkgerät mit Tragegriff und Antenne. Auf der dunklen Frontplatte liegen
eine große Glasanzeige, darunter eine Frequenzskala mit rotem Zeiger, ein geriffelter Abstimmknopf,
zwei Lämpchen für Empfang und Senden mit Kippschaltern und die Schlitze des Lautsprechers.</desc>
<defs>
  <linearGradient id="oliv" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#6b7449"/><stop offset=".45" stop-color="#565e39"/>
    <stop offset="1" stop-color="#3d4328"/>
  </linearGradient>
  <filter id="lack" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="5" result="koernung"/>
    <feColorMatrix in="koernung" type="matrix"
      values="0 0 0 0 .12  0 0 0 0 .13  0 0 0 0 .08  0 0 0 .35 -.08" result="koernfarbe"/>
    <feMerge result="beides"><feMergeNode in="SourceGraphic"/><feMergeNode in="koernfarbe"/></feMerge>
    <feComposite in="beides" in2="SourceGraphic" operator="in"/>
  </filter>
  <linearGradient id="platte" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2f3327"/><stop offset="1" stop-color="#23261d"/>
  </linearGradient>
  <linearGradient id="rahmen" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#15160f"/><stop offset=".5" stop-color="#2a2c22"/>
    <stop offset="1" stop-color="#3b3e32"/>
  </linearGradient>
  <radialGradient id="glas" cx=".5" cy=".45" r=".7">
    <stop offset="0" stop-color="#0d2416"/><stop offset=".65" stop-color="#08170e"/>
    <stop offset="1" stop-color="#040a06"/>
  </radialGradient>
  <linearGradient id="spiegelung" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity=".07"/><stop offset=".35" stop-color="#ffffff" stop-opacity=".02"/>
    <stop offset=".36" stop-color="#ffffff" stop-opacity="0"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <pattern id="zeilen" width="4" height="6" patternUnits="userSpaceOnUse">
    <rect width="4" height="2" fill="#000" opacity=".22"/>
  </pattern>
  <linearGradient id="skalenglas" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#3a3018"/><stop offset="1" stop-color="#231c0d"/>
  </linearGradient>
  <radialGradient id="knopf" cx=".38" cy=".32" r=".8">
    <stop offset="0" stop-color="#4a4d42"/><stop offset=".6" stop-color="#26281f"/>
    <stop offset="1" stop-color="#15160f"/>
  </radialGradient>
  <linearGradient id="chrom" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#e3e1d6"/><stop offset=".45" stop-color="#8f8e84"/>
    <stop offset=".55" stop-color="#b9b7ab"/><stop offset="1" stop-color="#55544b"/>
  </linearGradient>
  <radialGradient id="lampenglas" cx=".4" cy=".35" r=".7">
    <stop offset="0" stop-color="#3a3a33"/><stop offset="1" stop-color="#121210"/>
  </radialGradient>
  <linearGradient id="hebel" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#8e8c81"/><stop offset=".5" stop-color="#f1efe6"/>
    <stop offset="1" stop-color="#77756b"/>
  </linearGradient>
  <radialGradient id="schraube" cx=".35" cy=".3" r=".8">
    <stop offset="0" stop-color="#d6d4c8"/><stop offset="1" stop-color="#6d6c62"/>
  </radialGradient>
  <linearGradient id="griff" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#3a3a33"/><stop offset="1" stop-color="#15150f"/>
  </linearGradient>
  <filter id="weich" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>
  <filter id="schatten" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="12"/></filter>
</defs>

<!-- Schatten auf dem Buch -->
<rect x="{gx0 + 10}" y="{gy0 + 26}" width="{gx1 - gx0 - 6}" height="{gy1 - gy0 - 22}" rx="40" fill="#000"
      opacity=".55" filter="url(#schatten)"/>

<!-- Antenne: Fuß am Gehäuse, Stab schräg nach oben, Kugel an der Spitze -->
<line x1="{ax}" y1="{ay}" x2="{tx}" y2="{ty + 8}" stroke="#121310" stroke-width="10" stroke-linecap="round"/>
<line x1="{ax}" y1="{ay}" x2="{tx}" y2="{ty + 8}" stroke="url(#chrom)" stroke-width="6" stroke-linecap="round"/>
<circle cx="{tx}" cy="{ty + 6}" r="8" fill="url(#schraube)"/>

<!-- Tragegriff -->
<path d="M{hl},{gy0 + 6} C{hl},{gy0 - 70} {hr},{gy0 - 70} {hr},{gy0 + 6}" fill="none" stroke="#0e0e0a"
      stroke-width="34" stroke-linecap="round"/>
<path d="M{hl},{gy0 + 6} C{hl},{gy0 - 70} {hr},{gy0 - 70} {hr},{gy0 + 6}" fill="none" stroke="url(#griff)"
      stroke-width="26" stroke-linecap="round"/>
<path d="M{hl + 20},{gy0 - 30} C{hl + 90},{gy0 - 62} {hr - 90},{gy0 - 62} {hr - 20},{gy0 - 30}" fill="none"
      stroke="#6a6a5c" stroke-width="3" opacity=".45"/>
<rect x="{hl - 30}" y="{gy0 - 12}" width="60" height="26" rx="6" fill="url(#chrom)"/>
<rect x="{hr - 30}" y="{gy0 - 12}" width="60" height="26" rx="6" fill="url(#chrom)"/>

<!-- Gehäuse: oliv lackiertes Blech -->
<rect x="{gx0}" y="{gy0}" width="{gx1 - gx0}" height="{gy1 - gy0}" rx="38" fill="url(#oliv)" filter="url(#lack)"/>
<rect x="{gx0 + 3}" y="{gy0 + 3}" width="{gx1 - gx0 - 6}" height="{gy1 - gy0 - 6}" rx="35" fill="none"
      stroke="#9aa376" stroke-opacity=".45" stroke-width="3"/>
<rect x="{gx0}" y="{gy0}" width="{gx1 - gx0}" height="{gy1 - gy0}" rx="38" fill="none" stroke="#1d2014"
      stroke-width="4"/>
<!-- Antennenbuchse -->
<circle cx="{ax}" cy="{ay}" r="18" fill="url(#chrom)" stroke="#1d2014" stroke-width="3"/>
<circle cx="{ax}" cy="{ay}" r="7" fill="#1d2014"/>
<!-- Gebrauchsspuren -->
<g>
  {kratzer()}
</g>
<!-- Namensschild -->
<rect x="{gx0 + 60}" y="{gy0 + 6}" width="176" height="24" rx="5" fill="#1d2014" opacity=".75"/>
<text x="{gx0 + 148}" y="{gy0 + 25}" text-anchor="middle" font-family="DejaVu Sans" font-size="17"
      font-weight="bold" letter-spacing="3" fill="#cfc6a4" opacity=".85">KW-FUNK</text>

<!-- Frontplatte -->
<rect x="{px0}" y="{py0}" width="{px1 - px0}" height="{py1 - py0}" rx="20" fill="url(#platte)"/>
<rect x="{px0}" y="{py0}" width="{px1 - px0}" height="{py1 - py0}" rx="20" fill="none" stroke="#0f110b"
      stroke-width="3"/>
<rect x="{px0 + 3}" y="{py0 + 3}" width="{px1 - px0 - 6}" height="{py1 - py0 - 6}" rx="18" fill="none"
      stroke="#50563f" stroke-width="1.5" opacity=".6"/>
{schraube(px0 + 22, py0 + 22)}
{schraube(px1 - 22, py0 + 22)}
{schraube(px0 + 22, py1 - 22)}
{schraube(px1 - 22, py1 - 22)}

<!-- Die Anzeige: Rahmen und dunkles Glas -->
<rect x="{rx0}" y="{ry0}" width="{rx1 - rx0}" height="{ry1 - ry0}" rx="16" fill="url(#rahmen)"/>
<rect x="{rx0}" y="{ry0}" width="{rx1 - rx0}" height="{ry1 - ry0}" rx="16" fill="none" stroke="#070806"
      stroke-width="3"/>
<rect x="{sx0}" y="{sy0}" width="{sx1 - sx0}" height="{sy1 - sy0}" rx="10" fill="url(#glas)"/>
<rect x="{sx0}" y="{sy0}" width="{sx1 - sx0}" height="{sy1 - sy0}" rx="10" fill="url(#zeilen)"/>
<rect x="{sx0}" y="{sy0}" width="{sx1 - sx0}" height="{sy1 - sy0}" rx="10" fill="url(#spiegelung)"/>
<rect x="{sx0}" y="{sy0}" width="{sx1 - sx0}" height="{sy1 - sy0}" rx="10" fill="none" stroke="#000"
      stroke-width="5" opacity=".7"/>

<!-- Bedienelemente -->
<g>
  {skala()}
</g>
<text x="{(SKALA[0] + SKALA[2]) / 2:.0f}" y="{SKALA[3] + 30}" text-anchor="middle" font-family="DejaVu Sans"
      font-size="17" font-weight="bold" letter-spacing="1" fill="#d9ceb2" opacity=".75">FREQUENZ MHz</text>
<g>
  {abstimmknopf()}
</g>
{lampe(*LAMPE_EMPFANG, "EMPFANG")}
{lampe(*LAMPE_SENDEN, "SENDEN")}
{kippschalter(*SCHALTER[0], oben=True)}
{kippschalter(*SCHALTER[1], oben=False)}
<g>
  {lautsprecher()}
</g>
</svg>
'''


def main():
    """Schreibt die SVG-Datei nach ``grafik/`` – das tut ein Aufruf dieser Datei."""
    ziel = ORDNER / "funkgeraet.svg"
    ziel.write_text(funkgeraet_svg(), encoding="utf-8")
    print(f"geschrieben: {ziel}")


if __name__ == "__main__":
    main()
