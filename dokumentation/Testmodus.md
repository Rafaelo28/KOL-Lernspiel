# Testmodus – Kurzanleitung

Zum Durchklicken der Geschichte, ohne 15/20/25 Minuten zu warten und ohne
jede Aufgabe von Hand zu rechnen. **Nicht** für den Unterricht.

```bash
python3 main.py --testmodus     # Testmodus
python3 main.py                 # das echte Spiel, unverändert
```

Im Testmodus steht "TESTMODUS" in der Titelzeile des Fensters, und unten
liegt eine rote Leiste:

```
● TESTMODUS  [Lösung eintragen] [Level beenden] [Zeit ablaufen lassen] [Springe zu ▾]   Level 1 · Rest 14:45  [✕]
```

Rechts steht immer, in welchem Level du bist und wie viel Zeit das Level
noch hat. Links neben dieser Anzeige erscheint, was der letzte Knopfdruck
bewirkt hat.

---

## Die vier Knöpfe

| Knopf | Was er tut |
|-------|------------|
| **Lösung eintragen** | Schreibt die richtige Antwort in das Feld und prüft sie. Bei den langen Funksprüchen drückt er auch den Knopf, der den Rest der Nachricht auflöst. Noch einmal drücken = "Weiter". |
| **Level beenden** | Beendet das Level, als wären alle Aufgaben erledigt. Im Log steht dann "vorzeitig". |
| **Zeit ablaufen lassen** | Stellt die Uhr ans Ende des Zeitfensters. Das Level endet wie am Timer – mit "zeitablauf" im Log und den verpassten Funksprüchen zum Mitlesen. Steht der Abschluss da, überspringt derselbe Knopf die Nacht bis zur Landung. |
| **Springe zu ▾** | Führt direkt an eine Stelle der Geschichte (siehe unten). |

Dazu: **✕** blendet die Leiste aus, **F9** holt sie zurück. (Im Spiel
ausserdem: **F11** Vollbild, **Esc** zurück.)

## Das Sprungmenü

**Geschichte ansehen** – Level und Uhr bleiben, wo sie sind. Funksprüche
stehen dort zum Mitlesen da: mit Lösung, ohne Eingabe, ohne Uhr, ohne
Logzeile.

* Intro: der Absturz
* Level 1: der erste Ruf · Bobs erste Antwort
* Level 2: der abgefangene Funkspruch
* Übergang zu Level 3
* Level 3: die Reflexionsfrage · der eigene Standort · Bobs zweite Antwort

**Ins Level springen** – schaltet den Spielstand wirklich weiter, damit du
von dort normal weiterspielen kannst.

* Level 1 – Caesar · Level 2 – Substitution · Level 3 – Vigenère
* Abschluss: Nachtlager und Rettung

Läuft noch kein Durchlauf, beginnt ein Sprung selbst einen (Figur Vic
Moreno, ID `9-99`) – ID und Figur musst du also nicht jedes Mal
durchklicken. **Rückwärts** geht es nicht: Von Level 2 nach Level 1 kommt
man nur, indem man das Spiel neu startet; nach dem Abschluss ebenso.

Läuft gerade eine Aufgabe, wird sie vor dem Sprung abgeschlossen und steht
danach als abgebrochen im Testlog. Das muss so sein: Bliebe sie offen,
liesse sich beim Zurückkommen keine neue Aufgabe stellen.

---

## Drei typische Handgriffe

**Eine einzelne Szene ansehen**
Springe zu → die Stelle anklicken. Fertig. Der Knopf unter der Szene führt
zurück in den Ablauf.

**Ein Level durchspielen, ohne zu rechnen**
Springe zu → "Level 2 – Substitution". Dann bei jeder Aufgabe zweimal
**Lösung eintragen** (einmal lösen, einmal weiter).

**Sehen, was passiert, wenn die Zeit ausgeht**
Springe zu → das Level. Dann **Zeit ablaufen lassen**: Das Level wechselt
sofort, und die Funksprüche, die nicht mehr drankamen, erscheinen zum
Mitlesen – genau so, wie es einem langsamen Kind im Unterricht ginge.

**Das Ende ansehen**
Springe zu → "Abschluss: Nachtlager und Rettung". Entweder auf "Warten"
drücken und die Nacht ansehen (gut 15 Sekunden), oder **Zeit ablaufen
lassen** und gleich bei der Landung sein.

---

## Wichtig

* **Die Zeitfenster sind echt.** 15/20/25 Minuten laufen wie im Spiel, sie
  lassen sich nur überspringen. Für die Frage, ob die Zeiten reichen
  (Arbeitsplan 8.1), deshalb **ohne** Schalter starten und richtig spielen.
* **Testdaten sind keine Messdaten.** Sie landen in `logs/testmodus/`, und
  ihr Pseudonym beginnt mit `TEST-`. Beim Einsammeln der echten Daten
  bleibt dieser Ordner liegen.
* **Die Leiste braucht Platz** (etwa 30 Pixel, im grossen Maßstab 45). Auf
  einem knappen 1080p-Bildschirm kann dem höchsten Screen unten deshalb
  etwas fehlen. Zum Prüfen der Bildaufteilung die Leiste mit **✕**
  ausblenden.
* Am Spiel ändert der Testmodus nichts: dieselben Screens, dieselben
  Regeln, dieselben Aufgaben. Was du hier siehst, sehen die Kinder auch.

Der Code steht in [`ui/testmodus.py`](../ui/testmodus.py); in seinem Kopf
steht ausführlicher, warum er so gebaut ist.
