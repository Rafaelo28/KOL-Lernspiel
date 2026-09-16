"""Zeichnet Bobs Handbuch: das aufgeschlagene Buch und das Umblättern.

Erzeugt zwei SVG-Dateien in ``grafik/``, die danach wie jede Animation
vorgerendert werden (``dokumentation/Animationen.md``)::

    python3 grafik/buch_zeichnen.py
    python3 grafik/rendern.py grafik/buch.svg
    python3 grafik/rendern.py grafik/umblaettern.svg

Warum ein Programm statt einer gezeichneten SVG
───────────────────────────────────────────────
Beide Bilder brauchen dasselbe Blatt – denselben ausgefransten Umriss,
dieselben Maße –, sonst springt beim Umblättern die Kante. Und die sieben
Blätter des Seitenstapels, die unregelmäßigen Ränder und die Knicklinie in
jedem Bild des Umblätterns sind Rechenarbeit. Wer das Buch ändern will,
ändert es hier und lässt beide SVGs neu entstehen.

Maße
────
In SVG-Einheiten; im Spiel ist eine Einheit ein halber Pixel (Maßstab 1),
gezählt ab der linken oberen Ecke der :data:`VIEWBOX`. ``ui/handbuch.py``
setzt den Text auf die Flächen :data:`TEXT_LINKS` und :data:`TEXT_RECHTS` –
dort in Pixeln, also halb so groß und 4 Pixel höher. Diese Flächen bleiben
frei von Flecken und Schäden, damit alles lesbar ist; ein Test prüft im
gerenderten Bild, dass dort Papier ist.
"""

import math
import pathlib
import random

ORDNER = pathlib.Path(__file__).resolve().parent

B, H = 1920, 1000                  # die Zeichenfläche
#: Der Ausschnitt, der ins Bild kommt (viewBox beider Bilder): oben und unten
#: nur ein schmaler Rand Nachthimmel – im grossen Maßstab zählt jede Zeile.
VIEWBOX = (0, 8, 1920, 984)
NACHT = "#11132a"                  # der Nachthimmel des Spiels (stil.FARBE_NACHT)

# Einband
EX0, EY0, EX1, EY1 = 22, 12, 1898, 988
# Die beiden obersten Seiten
LX0, LX1 = 74, 960                 # links
RX0, RX1 = 960, 1846               # rechts
SY0, SY1 = 40, 960                 # oben, unten
MITTE = 960
#: Textflächen (x0, y0, x1, y1) – im Spiel: Pixel = Einheit / 2.
TEXT_LINKS = (136, 104, 868, 874)
TEXT_RECHTS = (1052, 104, 1784, 874)

#: Immer derselbe Zufall – sonst sähe das Buch nach jedem Neuzeichnen anders aus.
rnd = random.Random(1904)


def pfad(punkte, zu=True):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in punkte) + (" Z" if zu else "")


def kante(x0, y0, x1, y1, schritte, zittern, kerben=()):
    """Punkte einer leicht unregelmäßigen Papierkante von (x0, y0) nach (x1, y1).

    ``kerben`` sind kleine Einrisse: (Stelle 0–1 entlang der Kante, Tiefe).
    """
    punkte = []
    for i in range(schritte + 1):
        f = i / schritte
        x = x0 + (x1 - x0) * f
        y = y0 + (y1 - y0) * f
        if 0 < i < schritte:
            nx, ny = -(y1 - y0), (x1 - x0)
            laenge = math.hypot(nx, ny)
            versatz = rnd.uniform(-zittern, zittern)
            for stelle, tiefe in kerben:
                if abs(f - stelle) < 0.012:
                    versatz -= tiefe * (1 - abs(f - stelle) / 0.012)
            x += nx / laenge * versatz
            y += ny / laenge * versatz
        punkte.append((x, y))
    return punkte


def linke_seite(dx=0, dy=0, schaeden=True):
    """Umriss der linken Seite; oben und unten zur Mitte hin leicht eingezogen."""
    z = 2.2 if schaeden else 0
    oben = [(LX0 + dx + 14, SY0 + dy)] + [(x, SY0 + dy + 7 * ((x - LX0) / (LX1 - LX0)) ** 3)
                                          for x in range(LX0 + 60, LX1, 60)] + [(LX1 + dx, SY0 + dy + 10)]
    rechts = [(LX1 + dx, SY1 + dy - 10)]
    unten = [(x, SY1 + dy - 7 * ((x - LX0) / (LX1 - LX0)) ** 3) for x in range(LX1 - 60, LX0 + 30, -60)]
    links = kante(LX0 + dx, SY1 + dy - 14, LX0 + dx, SY0 + dy + 14, 46, z,
                  kerben=((0.63, 11), (0.2, 5)) if schaeden else ())
    return [(LX0 + dx, SY0 + dy + 14)] + oben + rechts + unten + [(LX0 + dx + 14, SY1 + dy)] + links


def rechte_seite(dx=0, dy=0, schaeden=True, eselsohr=True):
    """Umriss der rechten Seite, oben rechts auf Wunsch mit Eselsohr."""
    z = 2.2 if schaeden else 0
    ohr = 58 if eselsohr else 0
    oben = [(RX0 + dx, SY0 + dy + 10)] + [(x, SY0 + dy + 7 * ((RX1 - x) / (RX1 - RX0)) ** 3)
                                          for x in range(RX0 + 60, RX1 - ohr - 20, 60)]
    oben += [(RX1 + dx - ohr, SY0 + dy)]
    rechts = kante(RX1 + dx, SY0 + dy + ohr, RX1 + dx, SY1 + dy - 14, 46, z,
                   kerben=((0.8, 7),) if schaeden else ())
    unten = [(RX1 + dx - 14, SY1 + dy)] + kante(RX1 + dx - 30, SY1 + dy, RX0 + 80 + dx, SY1 + dy - 2, 30,
                                                z * 0.8, kerben=((0.35, 8),) if schaeden else ())
    unten += [(RX0 + dx, SY1 + dy - 10)]
    return oben + rechts + unten


def stockflecken(seite_x0, seite_x1):
    """Kleine braune Punkte, nur am Rand – nie auf der Textfläche."""
    teile = []
    for _ in range(38):
        wo = rnd.choice("olur")
        if wo == "o":
            x, y = rnd.uniform(seite_x0 + 20, seite_x1 - 20), rnd.uniform(SY0 + 8, SY0 + 55)
        elif wo == "u":
            x, y = rnd.uniform(seite_x0 + 20, seite_x1 - 20), rnd.uniform(SY1 - 70, SY1 - 10)
        elif wo == "l":
            x, y = rnd.uniform(seite_x0 + 6, seite_x0 + 50), rnd.uniform(SY0 + 20, SY1 - 20)
        else:
            x, y = rnd.uniform(seite_x1 - 60, seite_x1 - 8), rnd.uniform(SY0 + 20, SY1 - 20)
        r = rnd.choice([1.4, 2, 2.6, 3.4, 4.5])
        teile.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" opacity="{rnd.uniform(.12, .34):.2f}"/>')
    return "\n    ".join(teile)


def ecken_ornament(x, y, sx, sy):
    """Goldene Eckverzierung des Einbands (gespiegelt über sx, sy)."""
    return (f'<g transform="translate({x},{y}) scale({sx},{sy})" fill="none" stroke="url(#gold)" '
            f'stroke-width="3" stroke-linecap="round">'
            f'<path d="M0,40 C0,16 16,0 40,0"/><path d="M8,62 C8,30 30,8 62,8"/>'
            f'<path d="M14,14 L34,34"/><circle cx="38" cy="38" r="5" fill="url(#gold)" stroke="none"/>'
            f'<path d="M0,70 L0,110 M70,0 L110,0" stroke-width="2"/></g>')


def ecke_angehoben(x, y, richtung):
    """Eine Seitenecke, die sich unten außen hochbiegt – hier lässt sich blättern.

    ``richtung`` 1 für die linke Seite (Ecke links unten), -1 für die rechte.
    Hinter der Ecke sieht man das nächste Blatt, davor die umgebogene Ecke.
    """
    r = richtung
    a = (x + r * 78, y)            # Knick auf der Unterkante
    b = (x, y - 78)                # Knick auf der Außenkante
    spitze = (x + r * 40, y - 40)  # die hochgebogene Spitze
    darunter = f"M{a[0]},{a[1]} L{x},{y} L{b[0]},{b[1]} Q{x + r * 24},{y - 30} {a[0]},{a[1]} Z"
    knick = f"M{a[0]},{a[1]} Q{x + r * 24},{y - 30} {b[0]},{b[1]}"
    ecke = (f"M{a[0]},{a[1]} Q{x + r * 24},{y - 30} {b[0]},{b[1]} "
            f"Q{x + r * 22},{y - 50} {spitze[0]},{spitze[1]} Q{x + r * 52},{y - 22} {a[0]},{a[1]} Z")
    return (f'<path d="{darunter}" fill="#d9c8a0"/>'
            f'<path d="{knick}" fill="none" stroke="#3a2a14" stroke-opacity=".35" stroke-width="6" '
            f'filter="url(#weich)"/>'
            f'<path d="{ecke}" fill="#000" opacity=".2" filter="url(#weich)" transform="translate({-r * 3},-4)"/>'
            f'<path d="{ecke}" fill="url(#rueckseite{"L" if r > 0 else "R"})" stroke="#a58c5c" stroke-width="1.2"/>')


# Die Reihenfolge hier legt fest, welche Zufallszahlen wohin fallen – erst die
# Blätter des Stapels, dann die beiden obersten Seiten.
STAPELFARBEN = ((7, "#bda877"), (6, "#c6b284"), (5, "#cfbd92"), (4, "#d6c59c"), (3, "#dccca6"),
                (2, "#e2d3ae"), (1, "#e7d9b6"))
STAPEL_LINKS = [(pfad(linke_seite(-k * 4.2, k * 2.8, schaeden=False)), farbe) for k, farbe in STAPELFARBEN]
STAPEL_RECHTS = [(pfad(rechte_seite(k * 4.2, k * 2.8, schaeden=False, eselsohr=False)), farbe)
                 for k, farbe in STAPELFARBEN]
LINKS_PUNKTE = linke_seite()
RECHTS_PUNKTE = rechte_seite()
LINKS = pfad(LINKS_PUNKTE)
RECHTS = pfad(RECHTS_PUNKTE)

# Eselsohr oben rechts: die umgeknickte Ecke
OHR = [(RX1 - 58, SY0), (RX1, SY0 + 58), (RX1 - 50, SY0 + 50)]

#: Das Papier – auf dem Buch und auf dem Blatt, das umgeblättert wird.
PAPIER_DEFS = '''
  <radialGradient id="papier" cx=".5" cy=".45" r=".75">
    <stop offset="0" stop-color="#f6ecd2"/><stop offset=".7" stop-color="#efe1bd"/>
    <stop offset="1" stop-color="#dcc493"/>
  </radialGradient>
  <filter id="randbraun" x="-5%" y="-5%" width="110%" height="110%">
    <feGaussianBlur stdDeviation="16"/>
  </filter>
  <filter id="weich" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>'''


def buch_svg():
    """Das aufgeschlagene Buch – ein Standbild, auf das das Spiel den Text setzt."""
    stapel = "\n".join(f'<path d="{d}" fill="{farbe}" stroke="#a8936a" stroke-width="1"/>'
                       for d, farbe in STAPEL_LINKS + STAPEL_RECHTS)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{' '.join(map(str, VIEWBOX))}"
     data-breite="960" data-standbild="ja">
<!--
  Bobs Verschlüsselungshandbuch, aufgeschlagen – Standbild für den Handbuch-Screen (Arbeitsplan 6.4).
  Entsteht mit grafik/buch_zeichnen.py – dort ändern, nicht hier.

  Fürs Spiel vorrendern mit:
      python3 grafik/rendern.py grafik/buch.svg
  Der Text der Seiten kommt nicht aus diesem Bild: Das Spiel setzt ihn auf die
  Textflächen links (x {TEXT_LINKS[0]}–{TEXT_LINKS[2]}, y {TEXT_LINKS[1]}–{TEXT_LINKS[3]}) und rechts (x {TEXT_RECHTS[0]}–{TEXT_RECHTS[2]}, y {TEXT_RECHTS[1]}–{TEXT_RECHTS[3]}).
  Diese Flächen bleiben frei von Flecken und Beschädigungen – ui/handbuch.py
  rechnet mit genau diesen Maßen (dort in Pixeln ab der Oberkante der viewBox, halb so groß).
  Das rote Lesezeichen-Band unten in der Mitte und die hochgebogenen Ecken
  unten außen sind im Spiel anklickbar.
-->
<title>Bobs Handbuch, aufgeschlagen</title>
<desc>Ein altes, in dunkelrotes Leder gebundenes Buch liegt aufgeschlagen auf dem Nachthimmel. Die
Seiten sind vergilbt, an den Rändern fleckig und etwas beschädigt, oben rechts ist ein Eselsohr, die
unteren Ecken biegen sich hoch. Aus dem Falz hängt ein rotes Lesezeichen-Band.</desc>
<defs>
  <linearGradient id="leder" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#6b2a22"/><stop offset=".5" stop-color="#57201b"/>
    <stop offset="1" stop-color="#3f1612"/>
  </linearGradient>
  <filter id="lederstruktur" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="4" seed="7" result="rauschen"/>
    <feDiffuseLighting in="rauschen" surfaceScale="2.2" lighting-color="#ffffff" result="licht">
      <feDistantLight azimuth="225" elevation="52"/>
    </feDiffuseLighting>
    <feComposite in="SourceGraphic" in2="licht" operator="arithmetic" k1="1.15" k2="0" k3="0" k4="0"/>
  </filter>
  <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#f3d98c"/><stop offset=".5" stop-color="#c9a24a"/>
    <stop offset="1" stop-color="#8f6b22"/>
  </linearGradient>{PAPIER_DEFS}
  <filter id="papierstruktur" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="3" result="fasern"/>
    <feColorMatrix in="fasern" type="matrix"
      values="0 0 0 0 .45  0 0 0 0 .33  0 0 0 0 .18  0 0 0 .22 -.03" result="faserfarbe"/>
    <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="3" seed="11" result="wolken"/>
    <feColorMatrix in="wolken" type="matrix"
      values="0 0 0 0 .55  0 0 0 0 .40  0 0 0 0 .20  0 0 0 .5 -.18" result="wolkenfarbe"/>
    <feMerge result="alt"><feMergeNode in="SourceGraphic"/><feMergeNode in="wolkenfarbe"/>
      <feMergeNode in="faserfarbe"/></feMerge>
    <feComposite in="alt" in2="SourceGraphic" operator="in"/>
  </filter>
  <filter id="schatten" x="-10%" y="-10%" width="120%" height="130%"><feGaussianBlur stdDeviation="14"/></filter>
  <linearGradient id="falz" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#3b2a16" stop-opacity="0"/>
    <stop offset=".40" stop-color="#3b2a16" stop-opacity=".10"/>
    <stop offset=".49" stop-color="#2a1d0e" stop-opacity=".42"/>
    <stop offset=".51" stop-color="#2a1d0e" stop-opacity=".42"/>
    <stop offset=".60" stop-color="#3b2a16" stop-opacity=".10"/>
    <stop offset="1" stop-color="#3b2a16" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="band" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#6d0f16"/><stop offset=".35" stop-color="#b3212b"/>
    <stop offset=".55" stop-color="#d23a42"/><stop offset="1" stop-color="#7a1219"/>
  </linearGradient>
  <linearGradient id="rueckseiteL" x1="0" y1="1" x2="1" y2="0">
    <stop offset="0" stop-color="#fbf4e2"/><stop offset=".55" stop-color="#ead9b2"/>
    <stop offset="1" stop-color="#cbb07a"/>
  </linearGradient>
  <linearGradient id="rueckseiteR" x1="1" y1="1" x2="0" y2="0">
    <stop offset="0" stop-color="#fbf4e2"/><stop offset=".55" stop-color="#ead9b2"/>
    <stop offset="1" stop-color="#cbb07a"/>
  </linearGradient>
  <linearGradient id="ohr" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#e9d9b0"/><stop offset="1" stop-color="#cdb582"/>
  </linearGradient>
  <clipPath id="links"><path d="{LINKS}"/></clipPath>
  <clipPath id="rechts"><path d="{RECHTS}"/></clipPath>
</defs>

<!-- Grund: der Nachthimmel des Spiels -->
<rect width="{B}" height="{H}" fill="{NACHT}"/>

<!-- Schatten unter dem Buch -->
<rect x="{EX0 + 16}" y="{EY0 + 26}" width="{EX1 - EX0 - 20}" height="{EY1 - EY0 - 20}" rx="30" fill="#000"
      opacity=".6" filter="url(#schatten)"/>

<!-- Einband: Leder mit Goldprägung -->
<rect x="{EX0}" y="{EY0}" width="{EX1 - EX0}" height="{EY1 - EY0}" rx="26" fill="url(#leder)"
      filter="url(#lederstruktur)"/>
<rect x="{EX0 + 3}" y="{EY0 + 3}" width="{EX1 - EX0 - 6}" height="{EY1 - EY0 - 6}" rx="24" fill="none"
      stroke="#8a4034" stroke-opacity=".6" stroke-width="2"/>
<rect x="{EX0 + 12}" y="{EY0 + 10}" width="{EX1 - EX0 - 24}" height="{EY1 - EY0 - 20}" rx="18" fill="none"
      stroke="url(#gold)" stroke-width="2.5" opacity=".85"/>
{ecken_ornament(EX0 + 16, EY0 + 14, 1, 1)}
{ecken_ornament(EX1 - 16, EY0 + 14, -1, 1)}
{ecken_ornament(EX0 + 16, EY1 - 14, 1, -1)}
{ecken_ornament(EX1 - 16, EY1 - 14, -1, -1)}
<!-- abgeschabte Stellen am Leder -->
<g fill="#c9906e" opacity=".22" filter="url(#weich)">
  <ellipse cx="{EX0 + 40}" cy="{EY1 - 30}" rx="30" ry="12"/>
  <ellipse cx="{EX1 - 60}" cy="{EY0 + 22}" rx="26" ry="9"/>
  <ellipse cx="{MITTE + 380}" cy="{EY1 - 8}" rx="40" ry="6"/>
</g>

<!-- Seitenstapel: die Blätter darunter -->
{stapel}

<!-- Die beiden obersten Seiten -->
<g filter="url(#papierstruktur)">
  <path d="{LINKS}" fill="url(#papier)"/>
  <path d="{RECHTS}" fill="url(#papier)"/>
</g>
<!-- vergilbte, gebräunte Ränder – nach innen verlaufend -->
<g clip-path="url(#links)"><path d="{LINKS}" fill="none" stroke="#8a6232" stroke-width="44" opacity=".42"
   filter="url(#randbraun)"/></g>
<g clip-path="url(#rechts)"><path d="{RECHTS}" fill="none" stroke="#8a6232" stroke-width="44" opacity=".42"
   filter="url(#randbraun)"/></g>
<g clip-path="url(#links)"><path d="{LINKS}" fill="none" stroke="#5e3f1c" stroke-width="7" opacity=".35"
   filter="url(#weich)"/></g>
<g clip-path="url(#rechts)"><path d="{RECHTS}" fill="none" stroke="#5e3f1c" stroke-width="7" opacity=".35"
   filter="url(#weich)"/></g>
<g fill="none" stroke="#8c7247" stroke-width="1.3" opacity=".7">
  <path d="{LINKS}"/><path d="{RECHTS}"/>
</g>

<!-- Stockflecken am Rand -->
<g fill="#8a5a2b" filter="url(#weich)">
  <g clip-path="url(#links)">
    {stockflecken(LX0, LX1)}
  </g>
  <g clip-path="url(#rechts)">
    {stockflecken(RX0, RX1)}
  </g>
</g>

<!-- Kaffeerand oben links: die Tasse stand halb neben dem Buch – der Rand bleibt vor der Textfläche -->
<g clip-path="url(#links)" opacity=".55">
  <ellipse cx="{LX0 - 4}" cy="{SY0 + 24}" rx="62" ry="56" fill="none" stroke="#8a5a2b" stroke-width="6"
           opacity=".4" filter="url(#weich)"/>
  <ellipse cx="{LX0 - 4}" cy="{SY0 + 24}" rx="60" ry="54" fill="none" stroke="#6e4520" stroke-width="1.6"
           opacity=".45"/>
</g>
<!-- ein Wasserfleck oben auf der rechten Seite, im Rand -->
<g clip-path="url(#rechts)">
  <path d="M{RX1 - 190},{SY0 + 4} C{RX1 - 150},{SY0 + 44} {RX1 - 70},{SY0 + 52} {RX1 - 40},{SY0 + 20} L{RX1 - 60},{SY0} Z"
        fill="#b08a52" opacity=".16" filter="url(#weich)"/>
</g>

<!-- Der Falz in der Mitte -->
<rect x="{MITTE - 130}" y="{SY0}" width="260" height="{SY1 - SY0}" fill="url(#falz)"/>
<path d="M{MITTE},{SY0 + 6} L{MITTE},{SY1 - 6}" stroke="#4a3418" stroke-opacity=".55" stroke-width="2"/>
<path d="M{MITTE - 16},{SY0 + 14} L{MITTE - 16},{SY1 - 14} M{MITTE + 16},{SY0 + 14} L{MITTE + 16},{SY1 - 14}"
      stroke="#fff6dc" stroke-opacity=".25" stroke-width="3"/>

<!-- Eselsohr oben rechts -->
<path d="M{RX1 - 58},{SY0} L{RX1 - 52},{SY0 + 58} L{RX1},{SY0 + 58}" fill="#000" opacity=".18" filter="url(#weich)"/>
<path d="{pfad(OHR)}" fill="url(#ohr)" stroke="#9c8558" stroke-width="1.3"/>

<!-- Hochgebogene Ecken unten außen: hier lässt sich blättern -->
{ecke_angehoben(RX1, SY1, -1)}
{ecke_angehoben(LX0, SY1, 1)}

<!-- Lesezeichen-Band -->
<path d="M{MITTE - 14},{SY1 - 116} C{MITTE - 8},{SY1 - 60} {MITTE - 14},{SY1 - 20} {MITTE - 6},{H} L{MITTE + 30},{H}
         C{MITTE + 22},{SY1 - 20} {MITTE + 28},{SY1 - 60} {MITTE + 20},{SY1 - 116} Z" fill="#000" opacity=".25"
      filter="url(#weich)" transform="translate(5,4)"/>
<path d="M{MITTE - 14},{SY1 - 116} C{MITTE - 8},{SY1 - 60} {MITTE - 14},{SY1 - 20} {MITTE - 6},{H + 10}
         L{MITTE + 7},{H - 8} L{MITTE + 30},{H + 10} C{MITTE + 22},{SY1 - 20} {MITTE + 28},{SY1 - 60}
         {MITTE + 20},{SY1 - 116} Z" fill="url(#band)"/>
<path d="M{MITTE + 2},{SY1 - 110} C{MITTE + 8},{SY1 - 60} {MITTE + 2},{SY1 - 20} {MITTE + 10},{H}"
      fill="none" stroke="#ff8a8f" stroke-opacity=".35" stroke-width="2"/>
</svg>
'''


# ── Das Umblättern ─────────────────────────────────────────────────────────

#: Wo die untere Außenecke der rechten Seite in jedem Bild liegt – als
#: Versatz von ihrem Platz (dx nach links, dy nach oben), in Einheiten.
#: Vor dem ersten Eintrag liegt das Blatt noch flach (Bild 0), mit dem
#: letzten liegt es links. Erst hebt sich die Ecke schräg, dann richtet sich
#: der Knick auf und wandert zum Falz. Früher aufrichten muss er sich, weil
#: die umgeschlagene Seite sonst oben aus dem Bild ragte – das rechnet
#: :func:`umblaettern_pruefen` nach.
ECKE_UNTERWEGS = ((40, 40), (130, 100), (260, 120), (430, 70), (650, 36), (880, 30), (1100, 28),
                  (1300, 26), (1480, 22), (1630, 16), (RX1 - LX0, 0))

#: So lange steht jedes Bild – zwölf Bilder, gut eine Drittelsekunde.
TAKT_MS = 30

#: Der Ausschnitt, in dem sich das Blatt bewegt (x y b h) – beide Seiten samt Schatten.
UMBLAETTERN_BEREICH = (40, VIEWBOX[1], 1832, VIEWBOX[3])


def knick(dx, dy):
    """Die Knicklinie, wenn die Ecke um (dx, dy) versetzt liegt: Fußpunkt und Normale.

    Gefaltet wird so, dass die Ecke genau dort landet – die Knicklinie ist
    also die Mittelsenkrechte zwischen ihrem Platz und ihrer neuen Lage. Die
    Normale zeigt zur Ecke hin, auf den Teil, der umgeschlagen wird.
    """
    laenge = math.hypot(dx, dy)
    return (RX1 - dx / 2, SY1 - dy / 2), (dx / laenge, dy / laenge)


def abstand(punkt, fuss, normale):
    """Wie weit ``punkt`` auf der Seite der Ecke von der Knicklinie liegt (negativ: auf der anderen)."""
    return (punkt[0] - fuss[0]) * normale[0] + (punkt[1] - fuss[1]) * normale[1]


def gespiegelt(punkt, fuss, normale):
    d = abstand(punkt, fuss, normale)
    return punkt[0] - 2 * d * normale[0], punkt[1] - 2 * d * normale[1]


def spiegelung(fuss, normale):
    """Die SVG-Matrix der Spiegelung an der Knicklinie."""
    nx, ny = normale
    c = fuss[0] * nx + fuss[1] * ny
    werte = (1 - 2 * nx * nx, -2 * nx * ny, -2 * nx * ny, 1 - 2 * ny * ny, 2 * c * nx, 2 * c * ny)
    return "matrix(" + " ".join(f"{w:.6f}" for w in werte) + ")"


def streifen(fuss, normale, von, bis):
    """Ein Streifen parallel zur Knicklinie, von ``von`` bis ``bis`` Einheiten zur Ecke hin."""
    nx, ny = normale
    ux, uy = -ny, nx
    w = 5000
    fx, fy = fuss
    return [(fx + nx * von - ux * w, fy + ny * von - uy * w), (fx + nx * von + ux * w, fy + ny * von + uy * w),
            (fx + nx * bis + ux * w, fy + ny * bis + uy * w), (fx + nx * bis - ux * w, fy + ny * bis - uy * w)]


def umblaettern_pruefen():
    """Reißt das Blatt nicht am Falz ab, und bleibt es im Bild?"""
    for dx, dy in ECKE_UNTERWEGS:
        fuss, normale = knick(dx, dy)
        for punkt in RECHTS_PUNKTE:
            if abstand(punkt, fuss, normale) <= 0:
                continue
            if punkt[0] <= RX0 + 0.5 and (dx, dy) != ECKE_UNTERWEGS[-1]:
                raise ValueError(f"Bei {dx, dy} knickt das Blatt schon am Falz – es risse ab.")
            x, y = gespiegelt(punkt, fuss, normale)
            bx, by, bb, bh = UMBLAETTERN_BEREICH
            if not (bx + 10 <= x <= bx + bb - 10 and by + 1 <= y <= by + bh - 1):
                raise ValueError(f"Bei {dx, dy} ragt die umgeschlagene Seite aus dem Bild: {x:.0f}, {y:.0f}")


def _verlauf(name, fuss, normale, laenge, stopps):
    """Ein Verlauf quer zur Knicklinie; ``stopps`` sind (Abstand in Einheiten, Farbe, Deckkraft)."""
    x1, y1 = fuss
    x2, y2 = fuss[0] + normale[0] * laenge, fuss[1] + normale[1] * laenge
    teile, zuletzt = [], 0.0
    for weg, farbe, deckkraft in stopps:
        stelle = max(zuletzt, min(1.0, weg / laenge))
        zuletzt = stelle
        teile.append(f'<stop offset="{stelle:.4f}" stop-color="{farbe}" stop-opacity="{deckkraft}"/>')
    return (f'<linearGradient id="{name}" gradientUnits="userSpaceOnUse" x1="{x1:.1f}" y1="{y1:.1f}" '
            f'x2="{x2:.1f}" y2="{y2:.1f}">{"".join(teile)}</linearGradient>')


def umblaettern_bild(nr, dx, dy):
    """Definitionen und Zeichnung eines Bildes: das Blatt, geknickt bei (dx, dy)."""
    fuss, normale = knick(dx, dy)
    spiegel = spiegelung(fuss, normale)
    # So weit reicht der umgeschlagene Teil von der Knicklinie aus.
    weite = max(abstand(p, fuss, normale) for p in RECHTS_PUNKTE)
    defs = (
        f'<clipPath id="liegt{nr}"><path d="{pfad(streifen(fuss, normale, -5000, 0))}"/></clipPath>'
        f'<clipPath id="klappe{nr}"><path d="{pfad(streifen(fuss, normale, 0, 5000))}"/></clipPath>'
        # Auf der Seite darunter: dunkel dicht am Knick, wo sich das Blatt hebt.
        + _verlauf(f"darunter{nr}", fuss, normale, 90,
                   ((0, "#231405", .45), (30, "#231405", .16), (90, "#231405", 0)))
        # Auf der Rückseite des Blatts: die Wölbung am Knick, ein Glanz, dann Papier.
        + _verlauf(f"woelbung{nr}", fuss, normale, weite,
                   ((0, "#3c2a10", .42), (10, "#3c2a10", .16), (26, "#fff8e6", .34), (70, "#fff8e6", 0),
                    (weite * .75, "#5a4018", 0), (weite, "#5a4018", .12)))
    )
    zeichnung = f'''<g class="bild" id="bild_{nr}">
  <g clip-path="url(#rechts)"><path d="{pfad(streifen(fuss, normale, 0, 90))}" fill="url(#darunter{nr})"/></g>
  <g clip-path="url(#liegt{nr})"><use href="#blatt"/></g>
  <g transform="translate({-normale[0] * 10:.1f},{6 - normale[1] * 10:.1f})" opacity=".35" filter="url(#klappenschatten)">
    <g transform="{spiegel}"><g clip-path="url(#klappe{nr})"><path d="{RECHTS}" fill="#000"/></g></g>
  </g>
  <g transform="{spiegel}"><g clip-path="url(#klappe{nr})">
    <use href="#blatt"/>
    <g clip-path="url(#rechts)"><path d="{pfad(streifen(fuss, normale, 0, weite + 20))}" fill="url(#woelbung{nr})"/></g>
  </g></g>
</g>'''
    return defs, zeichnung


def umblaettern_svg():
    """Das Blatt, das von rechts nach links umschlägt – durchsichtig, einmal abgespielt.

    Rückwärts abgespielt blättert es zurück. Text steht auf dem Blatt nicht:
    Das Spiel tauscht den Text darunter aus (siehe ui/handbuch.py).
    """
    umblaettern_pruefen()
    bilder = [("", '<g class="bild" id="bild_0"><use href="#blatt"/></g>')]
    bilder += [umblaettern_bild(nr, dx, dy) for nr, (dx, dy) in enumerate(ECKE_UNTERWEGS, 1)]
    anzahl = len(bilder)
    # Jedes Bild ist eine halbe Taktlänge vor und nach seinem Zeitpunkt zu
    # sehen – so fällt kein Zeitpunkt auf eine Kante.
    zeiten = "\n".join(f"  #bild_{nr} {{ animation: zeigen {TAKT_MS}ms linear {nr * TAKT_MS - TAKT_MS // 2}ms; }}"
                       for nr in range(anzahl))
    bereich = " ".join(str(v) for v in UMBLAETTERN_BEREICH)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{' '.join(map(str, VIEWBOX))}"
     data-breite="960" data-schleife-ms="{anzahl * TAKT_MS}" data-bilder="{anzahl}" data-bereiche="{bereich}"
     data-einmalig="ja" data-durchsichtig="ja">
<!--
  Umblättern in Bobs Handbuch (Arbeitsplan 6.4): das rechte Blatt schlägt nach links um.
  Liegt genau über grafik/buch.svg (gleiche viewBox) und entsteht mit
  grafik/buch_zeichnen.py – dort ändern, nicht hier.

  Fürs Spiel vorrendern mit:
      python3 grafik/rendern.py grafik/umblaettern.svg
  Jedes Bild ist eine eigene Gruppe, die nur zu ihrem Zeitpunkt sichtbar ist.
-->
<title>Umblättern</title>
<style>
  .bild {{ opacity: 0; }}
  @keyframes zeigen {{ from, to {{ opacity: 1; }} }}
{zeiten}
</style>
<defs>{PAPIER_DEFS}
  <filter id="papierwolken" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="3" seed="11" result="wolken"/>
    <feColorMatrix in="wolken" type="matrix"
      values="0 0 0 0 .55  0 0 0 0 .40  0 0 0 0 .20  0 0 0 .5 -.18" result="wolkenfarbe"/>
    <feMerge result="alt"><feMergeNode in="SourceGraphic"/><feMergeNode in="wolkenfarbe"/></feMerge>
    <feComposite in="alt" in2="SourceGraphic" operator="in"/>
  </filter>
  <filter id="klappenschatten" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="9"/>
  </filter>
  <linearGradient id="falzrechts" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#2a1d0e" stop-opacity=".42"/>
    <stop offset=".02" stop-color="#2a1d0e" stop-opacity=".42"/>
    <stop offset=".2" stop-color="#3b2a16" stop-opacity=".10"/>
    <stop offset="1" stop-color="#3b2a16" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="rechts"><path d="{RECHTS}"/></clipPath>
  <!-- Das Blatt: dieselbe rechte Seite wie im Buch, nur ohne Fasern und Flecken -->
  <g id="blatt">
    <path d="{RECHTS}" fill="url(#papier)" filter="url(#papierwolken)"/>
    <g clip-path="url(#rechts)">
      <path d="{RECHTS}" fill="none" stroke="#8a6232" stroke-width="44" opacity=".42" filter="url(#randbraun)"/>
      <path d="{RECHTS}" fill="none" stroke="#5e3f1c" stroke-width="7" opacity=".35" filter="url(#weich)"/>
      <rect x="{MITTE}" y="{SY0}" width="130" height="{SY1 - SY0}" fill="url(#falzrechts)"/>
    </g>
    <path d="M{MITTE},{SY0 + 6} L{MITTE},{SY1 - 6}" stroke="#4a3418" stroke-opacity=".55" stroke-width="2"/>
    <path d="M{MITTE + 16},{SY0 + 14} L{MITTE + 16},{SY1 - 14}" stroke="#fff6dc" stroke-opacity=".25"
          stroke-width="3"/>
    <path d="{RECHTS}" fill="none" stroke="#8c7247" stroke-width="1.3" opacity=".7"/>
  </g>
  {"".join(defs for defs, _ in bilder)}
</defs>
{chr(10).join(zeichnung for _, zeichnung in bilder)}
</svg>
'''


def main():
    for name, svg in (("buch.svg", buch_svg()), ("umblaettern.svg", umblaettern_svg())):
        (ORDNER / name).write_text(svg, encoding="utf-8")
        print("geschrieben:", ORDNER / name)


if __name__ == "__main__":
    main()
