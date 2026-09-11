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
wie beim Story-Intro.

### 3. Rendern

```bash
python3 grafik/rendern.py grafik/<name>.svg
```

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
        self.buehne = Buehne(self, Animation("<name>"))
        self.buehne.pack()

    def beim_anzeigen(self):
        self.buehne.starten()
```

Die Bühne hält beim Screen-Wechsel von selbst an. Text lässt sich mit
`self.buehne.create_text(...)` über die Szene legen – so macht es
`ui/intro.py`.

---

## Größe im Blick behalten

Jedes Einzelbild kostet im Arbeitsspeicher Breite × Höhe × 4 Byte. Ein Test
(`tests/test_animation.py`) schlägt Alarm, wenn eine Animation mehr als 40 MB
Arbeitsspeicher oder 8 MB auf der Platte braucht. Stellschrauben, falls es zu
viel wird:

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
