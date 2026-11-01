# Testmodus – Kurzanleitung

Zum Durchklicken der Geschichte, ohne 12/10/25 Minuten zu warten und ohne
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
| **Lösung eintragen** | Schreibt die richtige Antwort in das Feld und prüft sie. Bei den langen Funksprüchen drückt er auch den Knopf, der den Rest der Nachricht auflöst. Noch einmal drücken = "Weiter". Bei einem Funkspruch, der nur zum Mitlesen dasteht, gibt es nichts einzutragen – dort klickt er weiter. |
| **Level beenden** | Beendet das Level, als wären alle Aufgaben erledigt. Im Log steht dann "vorzeitig". |
| **Zeit ablaufen lassen** | Stellt die Uhr ans Ende des Zeitfensters. Das Level endet wie am Timer – mit "zeitablauf" im Log und den verpassten Funksprüchen zum Mitlesen. Steht der Abschluss da, überspringt derselbe Knopf die Nacht bis zur Landung. |
| **Springe zu ▾** | Führt direkt an eine Stelle der Geschichte (siehe unten). |

Dazu: **✕** blendet die Leiste aus, **F9** holt sie zurück. (Im Spiel
ausserdem: **F11** Vollbild, **Esc** zurück.)

## Das Sprungmenü

Ein Klick auf **Springe zu ▾** klappt das Menü auf; es bleibt offen, bis du
etwas auswählst oder daneben klickst.

Jeder Eintrag setzt das Spiel an diese Stelle und lässt es **von dort
weiterlaufen** – du spielst also ganz normal weiter:

* Intro: der Absturz
* Level 1 – Caesar: Handbuch · der erste Ruf · Bobs erste Antwort
* Level 2 – Substitution: Handbuch · der abgefangene Funkspruch · Übergang
  zu Level 3
* Level 3 – Vigenère: Handbuch · die Reflexionsfrage · der eigene Standort ·
  Bobs zweite Antwort
* Abschluss: Nachtlager und Rettung

**Funksprüche sind echte Aufgaben.** Springst du zu "Bobs erste Antwort",
steht die Nachricht mit leerem Eingabefeld da: Du kannst sie selbst rechnen,
mit laufender Uhr, mit der 3-Versuche-Regel und mit einer Zeile im Log. Wer
nicht rechnen will, drückt **Lösung eintragen**. Der Erzähltext, der im Spiel
zu einem Funkspruch hinführt (vor dem eigenen Standort die Reflexionsfrage),
kommt auch beim Sprung davor.

**Rückwärts geht es auch** – mit einem neuen Durchlauf. Ein Spielstand kennt
nur vorwärts (ein Level darf nicht zweimal beginnen, sonst würden aus 15
Minuten 30). Wer also von Level 3 zurück nach Level 1 springt, ins Intro, zu
einem Funkspruch, der schon dran war, oder nach dem Abschluss noch irgendwo
hin, bekommt einen frischen Durchlauf. Die Leiste sagt das und nennt den
**neuen Dateinamen**:

```
Neuer Durchlauf – Messdaten jetzt in durchlauf_TEST-9-99-lauf2_2026-09-27_153628.csv
```

Das ist wichtig, wenn du ins Log schaust: Die Aufgaben von vorher stehen in
der **alten** Datei, die neuen in der neuen. Ein Testlauf mit vielen Sprüngen
hinterlässt deshalb mehrere Tabellen in `logs/testmodus/` – die Nummer im
Pseudonym (`TEST-9-99-lauf2`, `-lauf3`, …) sagt, in welcher Reihenfolge sie
entstanden sind. Hast du am Anfang eine eigene ID eingetippt, bleibt sie
erhalten (`TEST-1-12-lauf2`). Vorwärts springen behält den Durchlauf.

Läuft noch kein Durchlauf, beginnt ein Sprung selbst einen (Figur Vic
Moreno, ID `9-99`) – ID und Figur musst du also nicht jedes Mal
durchklicken.

Läuft gerade eine Aufgabe, wird sie vor dem Sprung abgeschlossen und steht
danach als abgebrochen im Testlog. Das muss so sein: Bliebe sie offen,
liesse sich danach keine neue Aufgabe stellen.

Übersprungene Level stehen im Log mit 0 Sekunden und "vorzeitig" – beim
Sprung zählt das Ziel, nicht der Weg dorthin. Die Funksprüche, die **vor**
dem Sprungziel liegen, kommen im Level noch dran.

---

## Typische Handgriffe

**Eine einzelne Szene ansehen**
Springe zu → die Stelle anklicken. Fertig. Der Knopf unter der Szene führt
zurück in den Ablauf.

**Ein Level durchspielen, ohne zu rechnen**
Springe zu → "Level 2 – Substitution: Handbuch". Dann bei jeder Aufgabe
zweimal **Lösung eintragen** (einmal lösen, einmal weiter).

**Einen Funkspruch selbst rechnen**
Springe zu → den Funkspruch. Das Feld ist leer, die Uhr läuft, drei Versuche
ohne Fortschritt – wie im Unterricht. Danach geht das Level normal weiter.

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

* **Die Zeitfenster sind echt.** 12/10/25 Minuten laufen wie im Spiel, sie
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
