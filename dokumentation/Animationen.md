# Animationen im Spiel

Tkinter kann weder SVG noch CSS-Animationen abspielen, und das Spiel darf
keine Zusatzpakete brauchen – Schulrechner haben keine Adminrechte. Deshalb
kommt eine Animation über drei Stationen ins Spiel:

1. **Die Szene als SVG** mit CSS-Animationen, in `grafik/<name>.svg`. Zum
   Ansehen einfach in Firefox öffnen.
2. **Vorrendern:** `python3 grafik/rendern.py grafik/<name>.svg`. Firefox
   rechnet die Animation einmal in Bilder um – nur auf dem
   Entwicklungsrechner, nie auf den Schulrechnern.
3. **Abspielen** mit `ui/animation.py`: Das Spiel blättert die Bilder im
   Takt durch. Das kann Tkinter von Haus aus.

Heraus kommen drei Dateien in `content/animationen/<name>/`:

| Datei | Inhalt |
|-------|--------|
| `hintergrund.png` | die ganze Szene als Standbild |
| `bereich_1.png` | alle Einzelbilder des bewegten Ausschnitts auf einem Blatt |
| `animation.json` | Größe, Lage des Ausschnitts, Takt |

Gespeichert wird also nicht die ganze Szene für jedes Bild, sondern nur der
Ausschnitt, in dem sich etwas bewegt. Beim Wrack sind das 377 × 330 Pixel
statt 960 × 540 – rund 20 MB Arbeitsspeicher statt 80.

**Zwei Größen.** Dieselben drei Dateien entstehen noch einmal 1,5-mal so groß
im Unterordner `1.5x/` (beim Wrack 1440 × 810 statt 960 × 540). Auf einem
1080p-Schulmonitor zeichnet das Spiel alles 1,5-mal so groß und lädt diesen
Satz; auf kleineren Bildschirmen den kleinen (siehe `ui/stil.py`, „Der
Maßstab“). Vergrößern ließe sich das kleine Bild im Spiel nicht sauber –
Tkinter kann nur Pixel verdoppeln, das sähe grob aus. Deshalb rechnet Firefox
beide Größen direkt aus der SVG.

## Was es schon gibt

Gute Vorlagen für neue Animationen:

| Quelle | Wo im Spiel | Besonderheit |
|--------|-------------|--------------|
| `grafik/wrack.svg` | Story-Intro (6.3) | eine große Szene, ein Ausschnitt; der Text liegt im Spiel darüber |
| `grafik/titel.svg` | Startbildschirm (6.2) | **zwei** Ausschnitte (Diamant, Schriftzug); der Schriftzug steckt im Bild |
| `grafik/figur_<kennung>.svg` | Figurwahl (6.2) | fünf kleine Symbole, 150 × 150 Pixel; der Grund ist die Kartenfarbe |
| `grafik/buch.svg` | Handbuch (6.4) | ein **Standbild**: das aufgeschlagene Buch, auf das das Spiel den Text setzt |
| `grafik/umblaettern.svg` | Handbuch (6.4) | **einmalig und durchsichtig**: zwölf Bilder, in denen ein Blatt umschlägt |
| `grafik/stempel.svg` | Handbuch (6.4) | ein **durchsichtiges Standbild**: "STRENG GEHEIM" auf der Titelseite |
| `grafik/stempel_geloest.svg` | Übung (6.5) | derselbe Bau in Grün: "GELÖST", sobald die Antwort stimmt |
| `grafik/funkgeraet.svg` | Funkgerät (6.6) | ein **durchsichtiges Standbild**, das auf dem Buch steht; auf sein leeres Glas schreibt das Spiel |
| `grafik/nachtlager.svg` | Abschluss (6.8) | eine große Szene wie das Wrack: das Lager an der Oase, der Ausschnitt ist das Feuer; Wasser, Palmen, Mond und Sterne stehen still |
| `grafik/morgen.svg` | Abschluss (6.8) | **dieselbe Oase** im Morgengrauen – das Spiel wechselt hinter geschlossenen Augen von der einen Szene zur anderen (`Buehne.wechseln`) |
| `grafik/hubschrauber.svg` | Abschluss (6.8) | eine **durchsichtige Figur**: Rotoren und Licht in einer Schleife, der Ausschnitt ist das ganze Bild. Das Spiel schiebt sie mit `ui.animation.Figur` über die Szene und blättert ihre Bilder selbst weiter. Die Rotoren sind **feste Stellungen**, von denen immer genau eine zu sehen ist (siehe unten) |

Die Symbole der Figurwahl sind auf `FARBE_KARTE` aus `ui/stil.py` gemalt,
sonst stünde auf jeder Karte ein Rechteck in einer anderen Farbe. Wer die
Farbe ändert, muss die SVGs mitziehen und neu rendern – ein Test in
`tests/test_figurwahl.py` prüft die Ecken.

**Buch und Umblättern werden gezeichnet, nicht getippt.** Beide SVGs entstehen
aus `grafik/buch_zeichnen.py`:

```bash
python3 grafik/buch_zeichnen.py          # schreibt buch.svg und umblaettern.svg
python3 grafik/rendern.py grafik/buch.svg
python3 grafik/rendern.py grafik/umblaettern.svg
```

Das Funkgerät entsteht genauso aus einem Programm, `grafik/funkgeraet_zeichnen.py`:
Glas und Lämpchen stehen dort in SVG-Einheiten und in `ui/funk.py` in Pixeln,
und ein Test prüft im gerenderten Bild, dass das Spiel dort schreibt, wo Glas ist.

Nachtlager, Morgen und Hubschrauber kommen aus `grafik/abschluss_zeichnen.py`
(`python3 grafik/abschluss_zeichnen.py` schreibt alle drei). Die beiden Szenen
entstehen aus denselben Formen – Dünen, Oase und Lager dürfen beim Wechsel
nicht springen. Das Wasser liegt in einer Mulde hinter der vordersten Düne:
Erst dadurch wirkt es wie ein See und nicht wie eine Pfütze auf dem Sand – und
der Platz vorn bleibt für Lager und Landung frei. Licht und Spiegelungen
darauf werden mit einem `clipPath` an der Wasserkante beschnitten. Wo der Hubschrauber landet und wo der Text steht, rechnet
`ui/abschluss.py` in Pixeln; ein Test prüft, dass er rechts neben dem Lager
aufsetzt.

**Was sich schnell dreht, zeichnet man in Stellungen.** Ein Rotor dreht sich
schneller, als 20 Bilder in der Sekunde zeigen können. Blätter, die nur in der
Länge schwanken, flackerten deshalb zwischen lang und kurz hin und her.
`grafik/abschluss_zeichnen.py` rechnet stattdessen für jedes der 16 Bilder
aus, wo die Blätter stehen – von leicht oben gesehen, auf einer flachen
Ellipse, mit einer Unschärfe hinter jedem Blatt –, und eine CSS-Animation zeigt
immer genau eine Stellung. Zwei Regeln dabei:

- Je Bild rückt ein Blatt höchstens ein Viertel des Wegs zum nächsten Blatt
  vor. Bei der Hälfte weiß das Auge nicht mehr, in welche Richtung es sich
  dreht; bei einem ganzen Abstand steht der Rotor scheinbar still.
- Das Fenster einer Stellung liegt mittig um den Zeitpunkt, zu dem das Bild
  genommen wird – eine Stellung genau auf der Kante könnte sonst durch einen
  Rundungsfehler danebenliegen.

Buch und Umblättern brauchen dasselbe Blatt – denselben ausgefransten Umriss, dieselbe
viewBox –, sonst springt beim Umblättern die Kante. Wer am Buch etwas ändern
will, ändert es dort und lässt beide neu entstehen. Die Textflächen der
Buchseiten stehen in beiden Dateien: in SVG-Einheiten in
`grafik/buch_zeichnen.py`, in Pixeln in `ui/handbuch.py`. Ein Test prüft im
gerenderten Bild, dass dort überall Papier ist.

---

## Eine neue Animation anlegen

### 1. Die SVG

Am `<svg>`-Element stehen vier Angaben fürs Rendern:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900"
     data-breite="960" data-schleife-ms="4000" data-bilder="40"
     data-bereiche="526 280 627 549">
```

| Attribut | Bedeutung |
|----------|-----------|
| `data-breite` | Breite im Spiel in Pixeln. Die Höhe folgt aus der `viewBox` und muss eine ganze Zahl ergeben (1600 × 900 → 960 × 540). |
| `data-schleife-ms` | Wie lange die Schleife dauert, bis sie von vorn beginnt. |
| `data-bilder` | Einzelbilder je Schleife. 40 Bilder in 4 s sind 10 pro Sekunde – für Feuer und Rauch genug. |
| `data-bereiche` | Der bewegte Ausschnitt in SVG-Einheiten: `x y Breite Höhe`. Mehrere Ausschnitte mit `;` trennen. |

Die Animationen selbst stehen als CSS in einem `<style>` innerhalb der SVG
(SMIL mit `<animate>` geht auch). `grafik/wrack.svg` ist ein vollständiges
Beispiel.

### 2. Die drei Regeln

**Jede Dauer teilt die Schleife.** Bei einer Schleife von 4 s gehen Dauern von
0,5 s, 1 s, 2 s und 4 s – aber keine 0,7 s oder 3 s. Mit `alternate` zählt die
doppelte Dauer: `1s … alternate` braucht 2 s für Hin und Zurück. Eine negative
`animation-delay` ist erlaubt und macht die Bewegung abwechslungsreicher.
Warum: Das Spiel wiederholt die Bildfolge endlos. Passt eine Dauer nicht,
springt das Bild an der Nahtstelle.

**Bewegt wird nur im Ausschnitt.** Was sich außerhalb von `data-bereiche`
bewegt, steht im Spiel still – und an der Kante des Ausschnitts entstünde ein
sichtbarer Sprung. Großflächiges wie ein pulsierendes Leuchten über die ganze
Szene oder funkelnde Sterne im ganzen Himmel deshalb stillhalten.

**Keine Schriften aus dem Netz.** Firefox rendert mit den Schriften, die auf
dem Rechner installiert sind. Für Text in der Szene eine verbreitete Schrift
angeben (etwa `DejaVu Sans`) – oder Text lieber im Spiel über die Szene legen,
wie beim Story-Intro. Der Schriftzug im Titelbild nennt zuerst
`Noto Serif Display` und dann `DejaVu Serif` als Ersatz. Das betrifft nur
das Rendern: Im Spiel steht er schon als Bild, die Schulrechner brauchen die
Schrift nicht.

### Wann Bild 0 kommt

Das Werkzeug rendert ab der **10. Sekunde** (`T0_MS` in `grafik/rendern.py`),
damit alles eingeschwungen ist. Bild 0 im Spiel ist also der Zeitpunkt 10 s
der Animation – bei einer Schleife von 4 s die Mitte der Schleife
(10 s = 2 × 4 s + 2 s). Für Feuer und Rauch spielt das keine Rolle.

Soll eine Bewegung aber genau mit Bild 0 anfangen, etwa ein Lichtstreifen,
der gleich beim Erscheinen des Screens über den Titel läuft, verzögert man
sie um den Rest, der bei 10 s geteilt durch die Schleifenlänge bleibt: bei
4 s Schleife `animation-delay: 2s` (gleichwertig `-2s`, so steht es in
`grafik/titel.svg`), bei 3 s Schleife `1s`.

### 3. Rendern

```bash
python3 grafik/rendern.py grafik/<name>.svg
```

Das rendert beide Größen. Nur eine davon: `--massstab 1.5` (oder `1`). Damit
die große Größe aufgeht, muss `data-breite` × 1,5 eine ganze Zahl ergeben –
also eine gerade Breite wählen.

Bevor das Werkzeug etwas schreibt, prüft es die Regeln an echten Bildern:

| Meldung | Was zu tun ist |
|---------|----------------|
| *fehlt data-bereiche. Vorschlag …* | Den vorgeschlagenen Ausschnitt übernehmen – er umfasst alles, was sich bewegt. |
| *Außerhalb der Ausschnitte bewegt sich etwas: bei x=… y=…* | Den Ausschnitt dorthin vergrößern oder die Bewegung an der Stelle anhalten. |
| *wiederholt sich nach … ms nicht genau* | Eine Dauer teilt die Schleife nicht – siehe Regel 1. |
| *passt nicht zur viewBox* | `data-breite` so wählen, dass die Höhe eine ganze Zahl wird. |

Das Rendern dauert wenige Sekunden. Firefox ist als Snap installiert und darf
nicht in `/tmp` lesen – das Werkzeug arbeitet deshalb in
`~/snap/firefox/common` und räumt dort hinterher auf.

Die fertigen Dateien werden mit committet: Die Schulrechner haben kein
Firefox-Werkzeug dabei, sie brauchen die Bilder.

### 4. Im Spiel zeigen

```python
from ui.animation import Animation, Buehne

class MeinScreen(Screen):
    def __init__(self, fenster):
        super().__init__(fenster)
        self.buehne = Buehne(self, Animation("<name>", massstab=self.massstab))
        self.buehne.pack()
        # Positionen über der Szene im Maßstab 1 angeben und durch px() schicken:
        self.buehne.create_text(self.px(480), self.px(30), text="…")

    def beim_anzeigen(self):
        self.buehne.starten()
```

`massstab=self.massstab` wählt den Bildsatz, der zum Fenster passt. Ohne ihn
käme auf dem Schulmonitor das kleine Bild in ein großes Fenster. Alle festen
Pixelangaben – Positionen von Text über der Szene, Abstände, Textbreiten –
gelten für den Maßstab 1 und gehen durch `self.px(…)`.

Die Bühne hält beim Screen-Wechsel von selbst an und gibt ihre Bilder frei.
Text lässt sich mit `self.buehne.create_text(...)` über die Szene legen – so
macht es `ui/erzaehlszene.py`. Eine Bühne, die erst auf einen Klick hin laufen soll, zeigt
bis dahin Bild 0; `anhalten()` und `zeige_bild(0)` setzen sie wieder zurück
(so die Karten in `ui/figurwahl.py`).

### 5. Standbilder, Durchsichtiges, einmalige Abläufe

Nicht alles ist eine Schleife. Drei Schalter am `<svg>`-Element (Wert `"ja"`):

| Schalter | Wofür | Was entsteht |
|----------|-------|--------------|
| `data-standbild` | ein Bild, das sich nicht bewegt (das Buch im Handbuch) | nur `hintergrund.png`; `data-schleife-ms`, `data-bilder` und `data-bereiche` entfallen |
| `data-durchsichtig` | ein Bild, unter dem etwas durchscheinen soll (ein Stempel über Text) | PNGs mit Alphakanal |
| `data-einmalig` | ein Ablauf, der einmal abläuft statt sich zu wiederholen (das Umblättern) | Bilder ab 0 ms, keine Prüfung der Nahtstelle |

Durchsichtig wird es, indem Firefox jede Seite zweimal fotografiert – auf
schwarzem und auf weissem Grund. Wo die SVG nichts malt, unterscheiden sich
die beiden Fotos, und genau das wird zur Durchsichtigkeit. Die SVG darf
deshalb **keinen eigenen Hintergrund** malen. Das Umrechnen läuft in reinem
Python und dauert bei großen Bildern ein paar Sekunden.

Ist ein einmaliger Ablauf zugleich durchsichtig, bekommt er keinen
Hintergrund: Er wird über etwas gelegt, das schon dasteht. Im Spiel spielt
ihn `Ablauf` ab:

```python
from ui.animation import Ablauf, Animation

umblaettern = Ablauf(leinwand, Animation("umblaettern", massstab=self.massstab), x, y)
umblaettern.abspielen(rueckwaerts=False, bei_bild=..., danach=...)
```

`bei_bild(nr, anzahl)` kommt nach jedem Bild – beim Umblättern wird damit in
der Mitte der Text darunter ausgetauscht.

---

## Größe im Blick behalten

Jedes Einzelbild kostet im Arbeitsspeicher Breite × Höhe × 4 Byte. Ein Test
(`tests/test_animation.py`) schlägt Alarm, wenn eine Animation mehr als 40 MB
Arbeitsspeicher oder 8 MB auf der Platte braucht – in der großen Größe das
2,25-Fache, weil jedes Bild 1,5 × 1,5-mal so viele Pixel hat (das Wrack
braucht dort rund 50 MB). Stellschrauben, falls es zu viel wird:

* den Ausschnitt enger fassen oder in zwei kleinere teilen,
* weniger Bilder je Sekunde (`data-bilder` kleiner),
* eine kürzere Schleife.

Derselbe Test prüft auch, dass die gerenderten Dateien zu ihrer SVG passen.
Wer die SVG ändert und das Rendern vergisst, sieht es dort.

---

## Warum nicht einfacher?

* **SVG direkt im Spiel anzeigen:** Dafür bräuchte Tkinter ein Zusatzpaket –
  genau das, was auf den Schulrechnern nicht geht.
* **Ein animiertes GIF:** GIF kennt nur 256 Farben. Die weichen Verläufe von
  Himmel, Glut und Rauch würden streifig.
* **Die ganze Szene für jedes Bild:** 40 Bilder mit 960 × 540 Pixeln wären
  rund 80 MB Arbeitsspeicher – für einen Schulrechner zu viel, und fast alles
  davon wäre 40-mal dasselbe Standbild.
