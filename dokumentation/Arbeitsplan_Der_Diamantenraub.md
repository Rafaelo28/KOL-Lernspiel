# Arbeitsplan: "Der Diamantenraub" – Verschlüsselungs-Lernspiel

*Aufgabenzerlegung für die Umsetzung mit Claude Code (Python/Tkinter).*
*Reihenfolge ist bewusst so gewählt, dass nach jeder Phase etwas Lauffähiges existiert.*

**Arbeitsweise:** Immer nur **eine** Aufgabe pro Claude-Code-Sitzung. Nach jeder
erledigten Aufgabe: selbst durchklicken, dann committen. So bleibt die
Git-Historie als Prozessnachweis (60 % der Bewertung) aussagekräftig.

---

## Phase 0 – Projektgerüst

### 0.1 Repository und Ordnerstruktur anlegen
- Git-Repo initialisieren, `.gitignore` für Python (`__pycache__`, `.venv`, `logs/`)
- Struktur:
  ```
  /crypto        – reine Verschlüsselungslogik, kein GUI
  /game          – Spiellogik, Zustand, Timer
  /ui            – Tkinter-Oberfläche
  /content       – Handbuchtexte, Wortlisten, Story-Texte (JSON/Python-Dicts)
  /tests         – pytest
  /logs          – Ausgabe der Messdaten (im .gitignore!)
  /dokumentation – Konzept, Arbeitsplan, Handbuchtexte, Tipps
  main.py        – Einstiegspunkt
  ```
- **Fertig, wenn:** `python main.py` startet und ein leeres Fenster zeigt.

### 0.2 CLAUDE.md mit den Projektregeln schreiben
Inhalt (Kurzfassung der unverhandelbaren Regeln):
- Zeitfenster 15/20/25 Min pro Level sind fix, Zusatzaufgaben verlängern sie nie
- 3-Versuche-Regel gilt für **alle** Aufgaben, auch für Bobs zwei Funksprüche
- Kein Klartext-Funkverkehr, auch nicht durch Bob
- Level 2 ist **monoalphabetische Substitution**, nicht Transposition
- Verschlüsselungslogik enthält niemals GUI-Code
- **Fertig, wenn:** Datei liegt im Projekt-Root.

### 0.3 Textkonvention festlegen und dokumentieren
Einmal entscheiden, überall gültig:
- Interne Normalisierung: alles auf Großbuchstaben
- Leerzeichen: bleiben im Geheimtext erhalten, werden aber beim Vergleich ignoriert
- Umlaute/Sonderzeichen: werden in Eingaben abgewiesen oder ersetzt (festlegen!)
- Nur A–Z werden verschlüsselt
- **Fertig, wenn:** Regeln stehen in `CLAUDE.md` und als Kommentar in `crypto/normalize.py`.

---

## Phase 1 – Verschlüsselungslogik (ohne Oberfläche)

*Diese Phase ist die wichtigste. Alles hier ist testbar und damit ein starker
Beleg für die Prozessdokumentation.*

### 1.1 `crypto/normalize.py`
- Funktion, die Nutzereingaben nach der Konvention aus 0.3 vereinheitlicht
- Funktion, die zwei Texte "tolerant" vergleicht (Groß/Klein, Leerzeichen)

### 1.2 `crypto/caesar.py`
- `verschluesseln(text, schluessel)` und `entschluesseln(text, schluessel)`
- Korrekter Umbruch Z→A und A→Z

### 1.3 `crypto/substitution.py`
- Tabelle aus dem Tastatur-Trick generieren (QWERTZUIOP / ASDFGHJKL / YXCVBNM)
- `verschluesseln` / `entschluesseln` gegen eine beliebige Zuordnungstabelle
- Rückgabe der Tabelle als Dict, damit die UI sie anzeigen kann

### 1.4 `crypto/vigenere.py`
- `verschluesseln(text, schluesselwort)` / `entschluesseln(...)`
- Schlüsselwort wird über die Nachrichtenlänge wiederholt
- **Wichtig:** Leerzeichen dürfen den Schlüssel-Index nicht weiterzählen (sonst
  passt das Ergebnis nicht zum Handbuch-Beispiel)

### 1.5 `crypto/vigenere_quadrat.py`
- 26×26-Quadrat automatisch generieren: Zeile *k*, Spalte *m* → Buchstabe mit
  Index `(k+m) mod 26`, A=0
- Rückgabe als Liste von Listen, damit die UI daraus ein Grid bauen kann

### 1.6 Tests schreiben (`/tests`)
- Caesar: `HUND` + Schlüssel 3 → `KXQG`; `Z` + 1 → `A`
- Substitution: `HUND` → `IXFR`
- Vigenère: `HUND` mit `ROT` → `YIGU`
- Rundlauf-Test für alle drei: entschlüsseln(verschlüsseln(x)) == x
- Quadrat: Zeile A ist das normale Alphabet; Feld (R, H) ist Y
- **Fertig, wenn:** `pytest` läuft grün durch.

---

## Phase 2 – Inhalte als Daten

### 2.1 `content/handbuch.py`
- Die drei Handbuchseiten als Text (aus `dokumentation/Handbuchtexte.md` übernehmen)
- Getrennt nach Abschnitten (Was ist das? / Beispiel / Merksatz), damit die UI
  sie einzeln layouten kann

### 2.2 `content/uebungen.py`
- Die 10 Caesar-Wörter, 10 Substitutionssätze, 10 Vigenère-Sätze
- Liste der Vigenère-Schlüsselwörter (ROT, WEG, TAG, …)

### 2.3 `content/story.py`
- Intro-Text (Absturz), Bobs zwei Funksprüche, der abgefangene Feind-Funkspruch,
  Story-Übergang Level 2→3, Abschlusstext
- Platzhalter für die Initialen der gewählten Figur
- **Achtung, aus Phase 1 aufgefallen:** Ziffern fallen nach Textkonvention
  Regel 6 weg. Aus "Quadrant 4 ist durchsucht … auf Quadrant 7" wird
  "QUADRANT IST DURCHSUCHT … AUF QUADRANT" – der Funkspruch verliert seinen
  Sinn. Zahlen in Story-Texten deshalb **ausschreiben** ("QUADRANT VIER").
  Gilt genauso für Standortangaben in Level 3.

### 2.4 `content/charaktere.py`
- Die fünf Figuren mit Name, Rolle, Initialen

---

## Phase 3 – Aufgaben-Generator

### 3.1 Aufgabenobjekt definieren
Eine Übungsaufgabe besteht aus: Richtung (ver-/entschlüsseln), Anzeigetext,
Schlüssel, erwartete Lösung, Level.

### 3.2 Generator schreiben
- Wählt zufällig ein Wort/einen Satz aus dem Pool des Levels
- Wählt zufällig die Richtung
- Bei "entschlüsseln": Text vorher selbst verschlüsseln und **den** anzeigen
- Bei Level 3 zusätzlich zufälliges Schlüsselwort
- Kein Wort zweimal hintereinander im selben Level

### 3.3 Zufalls-Seed protokollierbar machen
- Seed einmal pro Durchlauf setzen und ins Log schreiben, damit später
  rekonstruierbar ist, wer welche Aufgaben bekommen hat

---

## Phase 4 – Prüfung und Fehlerhandling

*Gilt einheitlich für Handbuch-Übungen **und** echte Funksprüche.*

### 4.1 Prüf-Funktion
- Vergleicht Eingabe mit Lösung (tolerant nach 0.3)
- Falsche Eingabe kann nicht abgeschickt werden
- **Bei echten Funksprüchen wird `selbst_zu_loesen` geprüft, nicht der ganze
  Klartext** – die langen Nachrichten werden nur zum Teil von Hand gerechnet
  (siehe CLAUDE.md, "Lange Funksprüche: Teilaufgabe statt Kürzen")

### 4.2 Konkrete Fehlermeldung statt "falsch"
- Rückmeldung, an welcher Stelle es kippt, z. B. "Stelle 3 stimmt nicht – prüf
  nochmal die Verschiebung"

### 4.3 Versuchszähler und Lösungsanzeige
- Nach 3 erfolglosen Versuchen **ohne Fortschritt** wird die Lösung
  eingeblendet. Eine Eingabe mit weniger falschen Buchstaben als die beste
  bisher kostet keinen Versuch – sonst bekommt jemand, der vier Verzähler
  einzeln ausbessert, nach der dritten Ausbesserung die Lösung vorgesetzt
  (siehe CLAUDE.md, Regel 2)
- Ins Log gehören beide Zahlen: alle falschen Eingaben und davon die ohne
  Fortschritt
- **Auch bei Bobs beiden Funksprüchen** – sonst blockiert das Spiel dort
- Bei Funksprüchen mit Teilaufgabe: Der Knopf "Den Rest entschlüsseln"
  erscheint, sobald der geprüfte Teil richtig ist **oder** die Lösung
  angezeigt wurde. Erscheint er nur bei richtiger Lösung, blockiert das Spiel
  an genau denselben Stellen wieder.

### 4.4 Teilaufgabe und Weiterrechnen-Knopf
Gilt für die drei langen Funksprüche (Bobs erste Antwort, Feind-Funkspruch,
Standort senden). Die Aufteilung steht fertig in `content/story.py`.
- Aufgabe ist `funkspruch.selbst_zu_loesen`, der Rest ist
  `klartext[len(selbst_zu_loesen):]`
- Nach Lösen (oder Anzeigen) der Teilaufgabe: Knopf mit der Beschriftung aus
  `story.BESCHRIFTUNG_REST[funkspruch.richtung]`
- Knopf zeigt `funkspruch.weiterrechnen` als Erzähltext und gibt danach die
  vollständige Nachricht frei
- Die Erzählzeit darin ist Fiktion – der Level-Timer läuft weiter

### 4.5 Optional: "Fast richtig"-Markierung — *zurückgestellt*
- Falsche Buchstaben farblich hervorheben
- Bewusst als *letzte* Aufgabe eingeplant, weil Zusatzaufwand
- **Entscheidung: wird vorerst nicht gebaut.** Die Rückmeldung aus 4.2 nennt
  bereits Stelle, Anzahl und Verfahrenshinweis; Projektregel 6 ist damit
  erfüllt. Alle falschen Stellen zu markieren würde verraten, welche
  Buchstaben stimmen, und aus dem Nachrechnen ein mechanisches Ausbessern
  machen. Ausserdem änderte es die Bedeutung der Versuchszahl in den
  Messdaten – wenn überhaupt, dann vor dem Pilotdurchlauf und begründet.

---

## Phase 5 – Zustand, Timer, Logging

### 5.1 `game/state.py`
- Gewählte Figur, aktuelles Level, aktuelle Aufgabe, Versuchszähler
- Zentral, nicht über die UI verstreut

### 5.2 Level-Timer
- 15 / 20 / 25 Minuten pro Level
- Bei Ablauf: automatisch weiter zum nächsten Level, unabhängig davon, was
  gerade offen ist
- Sichtbare Restzeit für die Spielenden

### 5.3 Aufgaben-Timer
- Misst Zeit **pro Aufgabe**, nicht die Gesamtdauer des offenen Fensters

### 5.4 Adaptive Zusatzaufgaben
- Wer deutlich unter dem Schwellenwert liegt, bekommt eine Extra-Aufgabe aus
  demselben Wortpool
- Schwellenwert als **eine Konstante an einer Stelle**, damit sie nach dem
  Pilotdurchlauf mit einem Handgriff angepasst werden kann

### 5.5 CSV-Logging
Pro Aufgabe eine Zeile: Pseudonym-ID, Level, Aufgabennummer, Richtung, Anzahl
Versuche, Lösung angezeigt (ja/nein), benötigte Sekunden, Zusatzaufgabe (ja/nein).
- **Zusätzlich: Versuche ohne Fortschritt**, getrennt von der Gesamtzahl der
  falschen Eingaben (siehe 4.3).
- **Zusätzlich: Länge des tatsächlich geprüften Textes in Buchstaben.** Bei
  Funksprüchen mit Teilaufgabe wird nicht die ganze Nachricht gerechnet – ohne
  diese Spalte sind die Bearbeitungszeiten später nicht vergleichbar.
- **Der Seed des Durchlaufs gehört einmal pro Logdatei hinein**
  (`game/zufallsquelle.py`, Feld `protokollwert`). Zusammen mit Level und
  Aufgabennummer lässt sich damit später nachbauen, welches Wort jemand
  bekommen hat – siehe `game.generator.wiederhole_uebungen()`. Ohne ihn ist
  eine lange Bearbeitungszeit nicht davon zu unterscheiden, dass jemand den
  längsten Übungssatz erwischt hat.
- Dateiname mit Zeitstempel, damit nichts überschrieben wird
- **Kein Klarname** – nur eine ID, die du separat zuordnest (Datenschutz)

---

## Phase 6 – Oberfläche

### 6.1 Fenstergerüst und Screen-Wechsel
- Ein Hauptfenster, Screens werden ausgetauscht
- Erst das Wechsel-Gerüst bauen, dann die einzelnen Screens füllen

### 6.2 Startbildschirm + Charakterauswahl
### 6.3 Story-Intro (Absturz-Szene)
### 6.4 Handbuch-Screen
- Scrollbarer Text, Tabellen als Grid
- Muss während der Aufgaben erreichbar bleiben (Nachschlagen ist erlaubt)

### 6.5 Aufgaben-Screen
- Aufgabentext, Schlüsselangabe, Eingabefeld, Prüf-Button, Rückmeldung,
  Versuchszähler

### 6.6 Funk-Screen
- Optisch abgesetzt vom Handbuch, damit "echte Nachricht" und "Übung"
  unterscheidbar sind
- **Beim Empfangen bleibt der vollständige Geheimtext sichtbar**, der selbst
  zu entschlüsselnde Anfang ist hervorgehoben. Sonst sieht man in Level 2 nicht
  mehr, dass der Geheimtext lang ist – und genau darauf beruht der Merksatz zur
  Häufigkeitsanalyse auf Handbuchseite 2
- **Beim Senden gilt das Gegenteil:** sichtbar ist der vollständige Klartext,
  der Geheimtext niemals – er ist die Lösung, die eingetippt werden soll
- Knopf "Den Rest entschlüsseln" plus Erzähltext-Einblendung (siehe 4.4)

### 6.7 Vigenère-Quadrat als Anzeige
- 26×26-Grid aus Phase 1.5, mit Hervorhebung der aktiven Zeile/Spalte
- Muss auf kleinen Schulmonitoren lesbar sein – testen!

### 6.8 Abschluss-Screen
- Nachthimmel, Rettung, Schlusstext (Diamanten bleiben zurück)

---

## Phase 7 – Level zusammensetzen

### 7.1 Level 1 (Caesar)
Handbuch → Übungen → Sendeaufgabe "Hallo, hört mich jemand? [Initialen]" →
Bobs erste verschlüsselte Antwort entschlüsseln

### 7.2 Level 2 (Substitution)
Handbuch → Übungen mit steigender Textlänge → Hinweis auf Häufigkeitsanalyse →
abgefangener Feind-Funkspruch (nur entschlüsseln) → Story-Übergang ohne Bob

### 7.3 Level 3 (Vigenère)
Handbuch inkl. Quadrat → Übungen → Reflexionsfrage → Standort senden →
Bobs zweite Antwort entschlüsseln → Warten-Button → Abschluss

### 7.4 Kompletter Durchlauf am Stück
- Einmal von Start bis Ende ohne Abbruch durchspielen
- Prüfen: Bleibt man nirgends hängen? Passen die Übergänge?

---

## Phase 8 – Test und Verteilung

### 8.1 Zeitmessung im Selbsttest
- Selbst durchspielen und stoppen: Sind 15/20/25 Min realistisch?

### 8.2 Pilotdurchlauf mit 2–3 Personen
- Ziel: Schwellenwert für Zusatzaufgaben kalibrieren (Aufgabe 5.4)
- Zweites Ziel: Verständlichkeit der Handbuchtexte prüfen

### 8.3 Verteilung auf Schulrechner testen
- Läuft Python dort? Ist Tkinter vorhanden?
- Falls nein: PyInstaller-Build erstellen und **auf einem echten Schulrechner**
  testen, nicht nur auf dem eigenen
- **Früh machen** – das ist das größte Ausfallrisiko

### 8.4 Logdateien einsammeln und Auswertung vorbereiten
- Wo landen die CSVs? Wie kommst du nach dem Experiment an alle heran?

---

## Offene Punkte außerhalb des Codes

- [ ] Level-2-Zuordnungstrick (Tastatur) gegen den echten Testbogen (Anhang A2)
      gegenchecken – kollidiert er mit einer Testantwort?
- [ ] **Übungsumfang gegen Anhang A4 abgleichen:** Die Spielgruppe rechnet pro
      echtem Funkspruch nur den Anfang von Hand (15–25 Buchstaben). Wenn die
      Frontalunterrichts-Gruppe auf Papier deutlich längere Texte bearbeitet,
      unterscheiden sich die Gruppen nicht mehr nur in der Methode, sondern
      auch im Übungsumfang. Entweder die Papieraufgaben entsprechend
      zuschneiden oder die Abweichung in der Arbeit begründen.
- [ ] Einverständnis/Datenschutz für die Datenerhebung klären
- [ ] Ablauf für den Vortest/Nachtest festlegen: im Spiel integriert oder auf
      Papier? (Muss identisch zur Kontrollgruppe sein.)

---

## Vorschlag für den Einstieg mit Claude Code

Formuliere Aufgaben klein und mit Abnahmekriterium, zum Beispiel:

> Lies CLAUDE.md und `dokumentation/Zusammenfassung_fuer_Development.md`.
> Setze Aufgabe 1.2 um:
> crypto/caesar.py mit verschluesseln() und entschluesseln(). Reine Funktionen,
> kein GUI-Code. Schreib dazu die Tests aus Aufgabe 1.6, die Caesar betreffen.

Nach jedem Schritt selbst prüfen und committen.
