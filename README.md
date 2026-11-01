# Der Diamantenraub

Ein Lernspiel, das Verschlüsselung erklärt: Caesar, monoalphabetische
Substitution und Vigenère – eingebettet in eine Agentengeschichte, die nach
einem Flugzeugabsturz in der Wüste spielt.

Das Spiel ist Teil eines **Methodenvergleichs für den Informatikunterricht**:
Eine Gruppe lernt dieselben Inhalte per Frontalunterricht, die andere mit
diesem Spiel. Beide durchlaufen dieselben Lernziele, denselben Vor- und
Nachtest und dieselbe Gesamtzeit. Daraus ergeben sich die Regeln, die im
Code an vielen Stellen auftauchen – siehe [Warum das Spiel so gebaut
ist](#warum-das-spiel-so-gebaut-ist).

---

## Spielablauf

| Level | Verfahren                     | Zeitfenster | Ablauf                                                          |
|-------|-------------------------------|-------------|-----------------------------------------------------------------|
| 1     | Caesar                        | 12 Min      | Handbuch → Übungen → Funkspruch senden → Bobs Antwort entschlüsseln |
| 2     | Monoalphabetische Substitution| 10 Min      | Handbuch → Übungen → abgefangenen Feind-Funkspruch entschlüsseln |
| 3     | Vigenère (mit Quadrat)        | 25 Min      | Handbuch → Übungen → Standort senden → Bobs zweite Antwort       |

Dazu je 10 Minuten Vor- und Nachtest sowie 5 Minuten Puffer.

Die echten Funksprüche sind bis zu 78 Buchstaben lang. Die werden nicht
gekürzt – stattdessen rechnen die Spielenden nur den Anfang von Hand, dann
löst ein Knopf den Rest auf („zwanzig Minuten später …"). So bleibt die
Nachricht vollständig, ohne dass Abschreibarbeit die Zeitfenster sprengt.
Die Begründung und was daran hängt, steht in [CLAUDE.md](CLAUDE.md).

---

## Schnellstart

Voraussetzung ist Python 3 mit Tkinter. Tkinter gehört zur
Standardbibliothek, wird unter Debian und Ubuntu aber separat verteilt:

```bash
sudo apt install python3-tk        # nur unter Debian/Ubuntu nötig
python3 main.py
```

Das Spiel braucht **keine** externen Pakete – wichtig für Schulrechner ohne
Internetzugang oder Administratorrechte. Der Aufruf funktioniert aus jedem
Arbeitsverzeichnis heraus; die Messdaten landen immer in `logs/` neben
`main.py`.

Fehlt Tkinter, meldet `main.py` das im Klartext mit Installationshinweis,
statt mit einem Stacktrace abzubrechen.

### Testmodus

Zum Durchklicken der Geschichte – nicht für den Unterricht:

```bash
python3 main.py --testmodus
```

Unter dem Spiel erscheint dann eine rote Leiste: **Lösung eintragen** füllt
die richtige Antwort ein und prüft sie, **Level beenden** schaltet weiter wie
nach erledigter Arbeit, **Zeit ablaufen lassen** lässt das Zeitfenster
sofort enden (und überspringt am Ende die Nacht bis zur Rettung), und
**Springe zu** setzt das Spiel an eine Stelle der Geschichte – vom Intro bis
zur Rettung – und lässt es von dort weiterlaufen; Funksprüche sind dort echte
Aufgaben zum Selberrechnen. Auch nach hinten: Dafür beginnt ein neuer
Durchlauf mit eigener Logdatei, deren Namen die Leiste nennt. Mit `✕`
verschwindet die Leiste, mit `F9` kommt sie zurück.

Am Spiel ändert der Schalter nichts: dieselben Screens, dieselben Regeln,
dieselben Zeitfenster – sie lassen sich nur überspringen. Die Messdaten der
Testläufe landen in `logs/testmodus/`, und vor ihrem Pseudonym steht
`TEST-`; sie können also nicht mit den echten durcheinandergeraten.

Die Kurzanleitung mit allen Sprungzielen steht in
[dokumentation/Testmodus.md](dokumentation/Testmodus.md).

### Tests

Einzige Entwicklungsabhängigkeit ist `pytest`. Die Fenstertests in
`tests/test_hauptfenster.py` brauchen eine Bildschirmanzeige; ohne eine
werden sie übersprungen.

```bash
sudo apt install python3-venv     # nur unter Debian/Ubuntu nötig
python3 -m venv .venv
.venv/bin/pip install pytest
.venv/bin/python -m pytest
```

Mitgeprüft werden auch die Doctests in `crypto/`, in denen die
durchgerechneten Beispiele des Handbuchs stehen (`HUND` + Schlüssel 3 →
`KXQG` und so weiter). Ein weiterer Test liest `dokumentation/Handbuchtexte.md`
ein und vergleicht die 54 Übungssätze mit denen im Code – wer eine
Handbuchseite ändert, sieht am roten Test sofort, wo Text und Code
auseinanderlaufen.

---

## Projektstruktur

```
crypto/          Verschlüsselungslogik – reine Funktionen, kein GUI
game/            Spiellogik, Zustand, Timer, Logging
ui/              Tkinter-Oberfläche (baut als einzige Schicht Bedienelemente)
content/         Handbuchtexte, Wortlisten, Story-Texte als Python-Daten, fertige Animationen
grafik/          Quellen der Animationen (SVG) und die Werkzeuge, die sie zeichnen und vorrendern
tests/           pytest
logs/            Messdaten der Durchläufe (Inhalt steht in .gitignore)
dokumentation/   Konzept, Arbeitsplan, Handbuchtexte, Commit-Regeln
main.py          Einstiegspunkt
```

Erlaubte Abhängigkeitsrichtung: `ui` → `game` → `crypto` / `content`, niemals
umgekehrt. Ein Test in `tests/test_zusammenspiel.py` hält das maschinell nach:
Er liest den Syntaxbaum jeder Datei in `crypto/`, `game/`, `content/` und `ui/`
und prüft, welche Projektpakete sie importiert. Derselbe Test stellt sicher,
dass Tkinter nur in `ui/` und `main.py` vorkommt, dass kein Fremdpaket
hereinrutscht und dass die Logik weder `print()` noch `input()` aufruft.

### Was in `content/` steckt

| Modul | Inhalt |
|-------|--------|
| `handbuch.py` | Die drei Handbuchseiten, zerlegt in Absätze, Aufzählungen, Tabellen und Bobs Randnotizen; dazu die Schritte der Beispiele, das Werkzeug gegenüber und die Merkkarten zum Lösen |
| `uebungen.py` | Die 54 Übungssätze (ein Pool für alle drei Level, je 18 eigene), die Vigenère-Schlüsselwörter, die Caesar-Schlüssel |
| `story.py` | Erzähltexte und die fünf Funksprüche samt Teilaufgaben |
| `charaktere.py` | Die fünf wählbaren Figuren und Bob |
| `verfahren.py` | Die drei Verfahrenskennungen, gemeinsam für Handbuch und Story |

Alle Texte stammen aus `dokumentation/`, und Tests vergleichen sie Zeile für
Zeile mit der Quelle – wer eine Handbuchseite ändert, sieht am roten Test
sofort, wo Text und Code auseinanderlaufen.

### Was in `game/` steckt

| Modul | Inhalt |
|-------|--------|
| `aufgabe.py` | Das Aufgabenobjekt – trägt Übungen und echte Funksprüche gleichermaßen |
| `generator.py` | Zieht Übungsaufgaben aus dem Pool, baut Funksprüche zu Aufgaben um |
| `zufallsquelle.py` | Der Seed des Durchlaufs, je Level ein eigener Zufallsstrom |
| `pruefung.py` | Vergleicht Eingabe und Lösung, tolerant nach der Textkonvention |
| `rueckmeldung.py` | Baut die konkrete Fehlermeldung statt eines blossen „falsch" |
| `bearbeitung.py` | Versuchszähler, Lösungsanzeige, Weiterrechnen-Knopf |
| `spielstand.py` | Der zentrale Zustand eines Durchlaufs: Figur, Level, laufende Aufgabe |
| `zeitfenster.py` | Die 12/10/25-Minuten-Fenster der drei Level (Level 2 ist das kürzeste – siehe Modulkopf) |
| `zusatzaufgaben.py` | Entscheidet, wann noch eine Extraaufgabe in die Restzeit passt – im Tempo des Kindes gerechnet |
| `levelablauf.py` | Was im Level als Nächstes drankommt: Übung, Zusatzaufgabe, Funkspruch – oder Levelende |
| `protokoll.py` | Schreibt das CSV eines Durchlaufs |
| `durchlauf.py` | Spielstand und Protokoll in einer Hand – speichert von selbst, fängt den Zeitablauf ab |
| `spieler_id.py` | Die ID der Lehrkraft (`1-12`): prüft die Form X-XX und sagt genau, was fehlt |

Der Seed wird einmal je Durchlauf gezogen und ins Log geschrieben. Damit lässt
sich nach dem Experiment rekonstruieren, welche Übungssätze eine bestimmte
Person bekommen hat – sonst wäre eine lange Bearbeitungszeit nicht davon zu
unterscheiden, dass jemand zufällig den längsten Satz erwischt hat.

### Was in `ui/` steckt

| Modul | Inhalt |
|-------|--------|
| `hauptfenster.py` | Das eine Fenster: öffnet maximiert (F11 Vollbild), Kopfzeile mit Level, Screen-Wechsel, Takt. Zeigt bewusst keinen Countdown (Zeitdruck-Stress) |
| `screen.py` | Die Grundform aller Screens |
| `ablauf.py` | Welcher Screen wann kommt – hier setzt Phase 7 die Level zusammen |
| `stil.py` | Schriften, Farben und Abstände an einer Stelle – und der Maßstab: auf 1080p-Monitoren alles 1,5-mal so groß |
| `animation.py` | Spielt vorgerenderte Animationen ab |
| `startbildschirm.py` | Der Startbildschirm: Titelbild mit funkelndem Diamanten, Feld für die ID, „Spiel starten“ |
| `figurwahl.py` | Die Figurwahl: Vorgeschichte und fünf Karten mit Rollen-Symbol; erst wählen, dann bestätigen |
| `erzaehlszene.py` | Erzähltext vor einer Szene, Absatz für Absatz: der Story-Intro und die kurzen Texte zwischen den Aufgaben |
| `handbuch.py` | Bobs Handbuch als aufgeschlagenes Buch: Doppelseiten zum Blättern (Knöpfe, Tasten, Mausrad, Seitenecken), umschlagende Blätter, das Vigenère-Quadrat; neben jedem Beispiel das Werkzeug mit markiertem Schritt; auch mitten in einer Aufgabe zum Nachschlagen |
| `buchsatz.py` | Der Satz des Handbuchs: welcher Text auf welche Buchseite kommt – mit den Regeln aus dem Buchdruck |
| `buchleinwand.py` | Das aufgeschlagene Buch als Leinwand – Bild, Schriften, Stempel, Zeichnen; Handbuch und Übung teilen es sich |
| `uebung.py` | Die Übungen im Buch: Aufgabe rechts, Werkzeug links, Rückmeldung mit Fehlerstelle, Stempel und Versuchszähler |
| `lineal.py` | Das Lineal im Vigenère-Quadrat: Zeile und Spalte per Klick markieren, damit beim Nachschlagen niemand verrutscht |
| `funk.py` | Die echten Funksprüche am Funkgerät: leuchtende Anzeige, Nachricht Zeichen für Zeichen, beim Empfangen der ganze Geheimtext, beim Senden nie; der Knopf für den Rest einer langen Nachricht |
| `abschluss.py` | Das Ende: Nachtlager mit dem Knopf „Warten“, die Augen fallen zu, am Morgen landet der Hubschrauber der Crew; dann der Schlusstext und wo die Messdaten liegen |
| `testmodus.py` | Kein Teil des Spiels: die Leiste für `--testmodus`, mit der sich Aufgaben lösen, Level überspringen und Story-Stellen anspringen lassen |

### Animationen

Tkinter kann keine SVG-Animationen abspielen. Die Szenen entstehen deshalb als SVG in
`grafik/` und werden einmal vorgerendert:

```bash
python3 grafik/rendern.py grafik/wrack.svg
```

Firefox rechnet dabei die Animation in Bilder um (nur auf dem Entwicklungsrechner),
das Spiel blättert die fertigen Bilder aus `content/animationen/` nur noch durch – ohne
Zusatzpaket. Jede Animation gibt es in zwei Größen: 960 × 540 für kleine Bildschirme und
1440 × 810 für die 1080p-Schulmonitore. Die große Fassung liegt je Szene in einem eigenen
Unterordner `1.5x/` – also `content/animationen/wrack/1.5x/`, nicht in einem gemeinsamen
Ordner für alle. Das Buch des Handbuchs und das Umblättern darin sind selbst gezeichnete
SVGs: `python3 grafik/buch_zeichnen.py` schreibt beide, danach werden sie wie jede
Animation vorgerendert. Genauso entstehen das Funkgerät (`grafik/funkgeraet_zeichnen.py`)
und die Bilder des Abschlusses (`grafik/abschluss_zeichnen.py`). Wie man eine neue
Animation anlegt und welche Regeln sie einhalten muss, steht in
[dokumentation/Animationen.md](dokumentation/Animationen.md).

| Animation | Wo | Was sich bewegt |
|-----------|----|-----------------|
| `titel` | Startbildschirm | Lichtreflexe und Funkeln auf dem Diamanten, Glanz über dem Schriftzug |
| `figur_<kennung>` (5×) | Figurwahl | das Rollen-Symbol unter der Maus und das der gewählten Karte: Zahlenschloss, Lupe, Chip, Landkarte, Füller |
| `wrack` | Story-Intro | Feuer, Rauch und Funken am Wrack |
| `umblaettern` | Handbuch | ein Blatt, das sich umschlägt – läuft einmal ab, nicht in einer Schleife |
| `nachtlager` | Abschluss | das Lagerfeuer an der Oase mit Flammen, Funken und Glut unter dem Sternenhimmel |
| `morgen` | Abschluss | dieselbe Oase im Morgengrauen: Rauch über der erloschenen Glut |
| `hubschrauber` | Abschluss | Haupt- und Heckrotor und das grüne Licht – das Spiel lässt ihn einfliegen und landen |

### Was in `crypto/` steckt

| Modul                  | Inhalt                                                              |
|------------------------|---------------------------------------------------------------------|
| `normalize.py`         | Die Textkonvention – wie Text im ganzen Spiel aussieht              |
| `caesar.py`            | Verschiebung um einen festen Schlüssel                              |
| `substitution.py`      | Freie Zuordnungstabelle, Standard ist der Tastatur-Trick des Handbuchs |
| `vigenere.py`          | Schlüsselwort-Verfahren, Rechenweg                                  |
| `vigenere_quadrat.py`  | Dasselbe als 26×26-Nachschlagetabelle für die Anzeige               |

Die letzten beiden sind bewusst voneinander unabhängig: Das Handbuch erklärt
Vigenère über das Quadrat, das Spiel prüft die Eingabe über die Formel. Ein
Test vergleicht deshalb **alle 676 Felder** beider Wege miteinander – wären
sie auch nur in einem Feld verschieden, würde eine korrekt abgelesene Lösung
als Fehlversuch gewertet.

---

## Textkonvention

Ausführlich begründet im Docstring-Kopf von `crypto/normalize.py`, kurz:

1. Intern alles Großbuchstaben; Kleinschreibung in der Eingabe ist nie ein Fehler.
2. Verschlüsselt werden nur A–Z; das Leerzeichen ist das einzige weitere erlaubte Zeichen.
3. Leerzeichen bleiben im Geheimtext stehen – Wortgrenzen bleiben sichtbar.
4. Beim Vergleich werden Leerzeichen ignoriert.
5. Umlaute werden ersetzt: Ä→AE, Ö→OE, Ü→UE, ß→SS – unabhängig davon, wie sie
   in Unicode geschrieben sind. Andere Akzentbuchstaben behalten ihren
   Grundbuchstaben (É→E), damit aus „Théo Lambert" nicht „THO LAMBERT" wird.
6. Alle übrigen Zeichen (Satzzeichen, Ziffern) werden entfernt.
7. Bei Vigenère zählen Leerzeichen den Schlüsselindex nicht weiter.

Punkt 6 hat eine Nebenwirkung, die beim Schreiben von Story-Texten zählt:
Zahlen verschwinden. „Quadrant 4" wird zu „QUADRANT" – Zahlen gehören
deshalb ausgeschrieben.

---

## Warum das Spiel so gebaut ist

Diese Regeln stammen aus dem Versuchsaufbau, nicht aus Geschmack. Sie stehen
vollständig in [CLAUDE.md](CLAUDE.md):

- **Die Zeitfenster sind fix.** Zusatzaufgaben verlängern ein Level nie. Läuft
  die Zeit ab, geht es weiter – sonst ist der Vergleich mit der
  Frontalunterrichts-Gruppe nicht mehr sauber. Gemeint ist Arbeitszeit: Was
  zwischen zwei Leveln nur gelesen wird – die verpassten Funksprüche, der
  Übergangstext –, läuft in keinem Zeitfenster; die Uhr des neuen Levels
  beginnt erst mit seiner Handbuchseite.
- **Kein Funkspruch geht verloren.** Was niemand ganz gesehen hat – nie
  drangewesen, am Timer abgebrochen oder mit unaufgelöstem Rest –, steht nach
  dem Levelwechsel zum Mitlesen da: mit Lösung, ohne Eingabe, ohne Uhr. Die
  Geschichte darf nicht an der Uhr scheitern.
- **Solange das Fenster läuft, gibt es Arbeit.** Sind die Funksprüche eines
  Levels erzählt, füllen weitere Übungen die Restzeit. Sonst sässe
  ausgerechnet das langsame Kind die letzten Minuten ab.
- **Nach drei Fehlversuchen ohne Fortschritt wird die Lösung gezeigt** – auch
  bei den beiden Funksprüchen, die die Geschichte tragen. Ohne diese Regel
  bliebe das Spiel genau dort hängen. Eine Eingabe mit weniger Fehlern als
  zuvor kostet keinen Versuch: Wer sich Buchstabe für Buchstabe herantastet,
  soll nicht dafür bestraft werden.
- **Kein Klartext-Funkverkehr.** Jede gesendete Nachricht wird verschlüsselt,
  jede empfangene muss entschlüsselt werden.
- **Level 2 ist monoalphabetische Substitution**, nicht Transposition.
- **`crypto/` enthält niemals GUI-Code.** Text rein, Text raus – nur so bleibt
  die Logik testbar.

---

## Die Messdaten

Pro Aufgabe entsteht eine Zeile in `logs/durchlauf_<ID>_<Zeitstempel>.csv`, etwa
`durchlauf_1-12_2026-09-14_101500.csv`:

| Spalte | Bedeutung |
|--------|-----------|
| `pseudonym`, `seed`, `figur` | Wer (die ID mit „ID “ davor, etwa `ID 1-12` – siehe unten), mit welcher Zufallsfolge und mit welcher Spielfigur (nur deren Kennung, z. B. `vic_moreno`) |
| `level`, `levelende`, `level_sekunden` | Wie lange das Level lief und ob es am Timer endete (`zeitablauf`), vorher (`vorzeitig`) oder noch läuft (`laeuft`) – gleich in jeder Zeile des Levels |
| `aufgabennummer`, `kennung`, `quelle` | Welche Aufgabe, in welcher Reihenfolge |
| `verfahren`, `richtung`, `zusatzaufgabe` | Was verlangt war |
| `laenge_in_buchstaben`, `gerechnete_buchstaben`, `sekunden` | Wie viel Arbeit und wie lange – erst zusammen vergleichbar. `gerechnete_buchstaben` ist grösser, wenn jemand von sich aus die ganze Nachricht gerechnet hat |
| `versuche`, `versuche_ohne_fortschritt` | „Acht Eingaben, keine ohne Fortschritt" ist etwas anderes als „drei Eingaben, alle ohne Fortschritt" |
| `loesung_angezeigt`, `abgebrochen`, `geloest`, `vollstaendig_geloest` | Wie es ausging |

Gelesen wird sie mit `pandas.read_csv(datei, sep=";", encoding="utf-8-sig")` –
oder per Doppelklick in Excel.

Drei Dinge sind bei der Auswertung wichtig:

- **Zeilen mit `abgebrochen = ja` gehören in keine Zeitauswertung.** Dort
  endete das Level mitten in der Aufgabe; in `sekunden` steht die Zeit bis
  zum Levelwechsel, keine Rechenzeit.
- **Welches Wort jemand bekommen hat,** baut
  `game.generator.uebung_nachbauen(seed, kennung)` aus einer Übungszeile
  nach. Die Übungsnummer steckt in der Kennung (`uebung_l2_3`). Die Spalte
  `aufgabennummer` taugt dafür nicht – sie zählt die Funksprüche mit.
- **Vor der ID steht „ID “.** Deutsches Excel machte aus `1-12` beim Öffnen
  sonst den 1. Dezember, und nach dem Speichern wäre die ID verloren. Die reine
  ID liefert `tabelle["pseudonym"].str.removeprefix("ID ")`.

## Datenschutz

Das Spiel protokolliert pro Aufgabe Versuchszahl, benötigte Zeit und ob die
Lösung angezeigt wurde. In den CSV-Dateien steht **kein Klarname**, nur eine
ID. Die IDs verteilt die Lehrkraft auf Papier, in der Form `X-XX`: Klasse,
Strich, Nummer – `1-12` ist das zwölfte Kind der 7/1. Das Feld auf dem
Startbildschirm nimmt nur genau diese Form an; einen Namen kann man dort gar
nicht erst eintippen. Wer hinter einer ID steckt, weiss nur die Lehrkraft.
Der Ordner `logs/` ist in `.gitignore`; die Messdaten der Teilnehmenden
dürfen nicht im Repository landen.

---

## Entwicklungsstand

| Phase | Inhalt                                       | Stand   |
|-------|----------------------------------------------|---------|
| 0     | Projektgerüst, Textkonvention                | fertig  |
| 1     | Verschlüsselungslogik samt Tests             | fertig  |
| 2     | Inhalte als Daten (Handbuch, Wortlisten, Story, Figuren) | fertig |
| 3     | Aufgaben-Generator                           | fertig  |
| 4     | Prüfung und Fehlerhandling                   | fertig  |
| 5     | Zustand, Timer, CSV-Logging                  | fertig  |
| 6     | Tkinter-Oberfläche                           | fertig  |
| 7     | Level zusammensetzen                         | fertig  |
| 8     | Test und Verteilung auf Schulrechner         | offen   |

Die vollständige Aufgabenzerlegung steht in
[dokumentation/Arbeitsplan_Der_Diamantenraub.md](dokumentation/Arbeitsplan_Der_Diamantenraub.md).

---

## Dokumentation

| Datei | Inhalt |
|-------|--------|
| [CLAUDE.md](CLAUDE.md) | Verbindliche Projektregeln und Textkonvention |
| [dokumentation/Zusammenfassung_fuer_Development.md](dokumentation/Zusammenfassung_fuer_Development.md) | Konzeptentscheidungen, Zeitrahmen, Lernziele |
| [dokumentation/Konzept_Spiel.md](dokumentation/Konzept_Spiel.md) | Rahmengeschichte und Level-Ablauf |
| [dokumentation/Handbuchtexte.md](dokumentation/Handbuchtexte.md) | Die drei Handbuchseiten und die Übungssätze |
| [dokumentation/Arbeitsplan_Der_Diamantenraub.md](dokumentation/Arbeitsplan_Der_Diamantenraub.md) | Aufgabenzerlegung, Phasen 0–8 |
| [dokumentation/Code_Lesehilfe.md](dokumentation/Code_Lesehilfe.md) | Die Bausteine im Quelltext – für alle, die nicht täglich Python schreiben |
| [dokumentation/Tipps-und-Tricks.md](dokumentation/Tipps-und-Tricks.md) | Hinweise zu Tkinter, Normalisierung, Logging |
| [dokumentation/Commit_Regeln.md](dokumentation/Commit_Regeln.md) | Wann und wie committet wird |
| [dokumentation/Animationen.md](dokumentation/Animationen.md) | Wie Animationen entstehen und ins Spiel kommen |
| [dokumentation/Testmodus.md](dokumentation/Testmodus.md) | Kurzanleitung für `main.py --testmodus` |
