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
| 1     | Caesar                        | 15 Min      | Handbuch → Übungen → Funkspruch senden → Bobs Antwort entschlüsseln |
| 2     | Monoalphabetische Substitution| 20 Min      | Handbuch → Übungen → abgefangenen Feind-Funkspruch entschlüsseln |
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
Arbeitsverzeichnis heraus.

Fehlt Tkinter, meldet `main.py` das im Klartext mit Installationshinweis,
statt mit einem Stacktrace abzubrechen.

### Tests

Einzige Entwicklungsabhängigkeit ist `pytest`:

```bash
sudo apt install python3-venv     # nur unter Debian/Ubuntu nötig
python3 -m venv .venv
.venv/bin/pip install pytest
.venv/bin/python -m pytest
```

Mitgeprüft werden auch die Doctests in `crypto/`, in denen die
durchgerechneten Beispiele des Handbuchs stehen (`HUND` + Schlüssel 3 →
`KXQG` und so weiter). Ein weiterer Test liest `dokumentation/Handbuchtexte.md`
ein und vergleicht die 30 Übungswörter und -sätze mit denen im Code – wer eine
Handbuchseite ändert, sieht am roten Test sofort, wo Text und Code
auseinanderlaufen.

---

## Projektstruktur

```
crypto/          Verschlüsselungslogik – reine Funktionen, kein GUI
game/            Spiellogik, Zustand, Timer, Logging
ui/              Tkinter-Oberfläche (baut als einzige Schicht Bedienelemente)
content/         Handbuchtexte, Wortlisten, Story-Texte als Python-Daten
tests/           pytest
logs/            Messdaten der Durchläufe (Inhalt steht in .gitignore)
dokumentation/   Konzept, Arbeitsplan, Handbuchtexte
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
| `handbuch.py` | Die drei Handbuchseiten, zerlegt in Absätze, Aufzählungen und Tabellen |
| `uebungen.py` | Die 30 Übungstexte, die Vigenère-Schlüsselwörter, die Caesar-Schlüssel |
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

Der Seed wird einmal je Durchlauf gezogen und ins Log geschrieben. Damit lässt
sich nach dem Experiment rekonstruieren, welche Übungswörter eine bestimmte
Person bekommen hat – sonst wäre eine lange Bearbeitungszeit nicht davon zu
unterscheiden, dass jemand zufällig den längsten Satz erwischt hat.

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
  Frontalunterrichts-Gruppe nicht mehr sauber.
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

## Datenschutz

Das Spiel protokolliert pro Aufgabe Versuchszahl, benötigte Zeit und ob die
Lösung angezeigt wurde. In den CSV-Dateien steht **kein Klarname**, nur eine
Pseudonym-ID. Der Ordner `logs/` ist in `.gitignore`; die Messdaten der
Teilnehmenden dürfen nicht im Repository landen.

---

## Entwicklungsstand

| Phase | Inhalt                                       | Stand   |
|-------|----------------------------------------------|---------|
| 0     | Projektgerüst, Textkonvention                | fertig  |
| 1     | Verschlüsselungslogik samt Tests             | fertig  |
| 2     | Inhalte als Daten (Handbuch, Wortlisten, Story, Figuren) | fertig |
| 3     | Aufgaben-Generator                           | fertig  |
| 4     | Prüfung und Fehlerhandling                   | fertig  |
| 5     | Zustand, Timer, CSV-Logging                  | offen   |
| 6     | Tkinter-Oberfläche                           | offen   |
| 7     | Level zusammensetzen                         | offen   |
| 8     | Test und Verteilung auf Schulrechner         | offen   |

`main.py` öffnet derzeit ein leeres Fenster; die Screens entstehen in Phase 6.

Die vollständige Aufgabenzerlegung steht in
[dokumentation/Arbeitsplan_Der_Diamantenraub.md](dokumentation/Arbeitsplan_Der_Diamantenraub.md).

---

## Dokumentation

| Datei | Inhalt |
|-------|--------|
| [CLAUDE.md](CLAUDE.md) | Verbindliche Projektregeln und Textkonvention |
| [dokumentation/Zusammenfassung_fuer_Development.md](dokumentation/Zusammenfassung_fuer_Development.md) | Konzeptentscheidungen, Zeitrahmen, Lernziele |
| [dokumentation/Konzept_Spiel.md](dokumentation/Konzept_Spiel.md) | Rahmengeschichte und Level-Ablauf |
| [dokumentation/Handbuchtexte.md](dokumentation/Handbuchtexte.md) | Die drei Handbuchseiten, Übungswörter und -sätze |
| [dokumentation/Arbeitsplan_Der_Diamantenraub.md](dokumentation/Arbeitsplan_Der_Diamantenraub.md) | Aufgabenzerlegung, Phasen 0–8 |
| [dokumentation/Tipps-und-Tricks.md](dokumentation/Tipps-und-Tricks.md) | Hinweise zu Tkinter, Normalisierung, Logging |
