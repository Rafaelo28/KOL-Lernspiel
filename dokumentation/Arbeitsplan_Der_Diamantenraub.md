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

### 5.1 `game/spielstand.py`
- Gewählte Figur, aktuelles Level, aktuelle Aufgabe, Versuchszähler
- Zentral, nicht über die UI verstreut
- *(Im Plan stand ursprünglich `game/state.py`. Umbenannt, weil das Projekt
  laut CLAUDE.md durchgehend deutsche Namen benutzt und alle übrigen Module in
  `game/` deutsch heissen.)*
- Dazu gehören: die Pseudonym-ID des Durchlaufs (Projektregel 7) und die
  Liste der erledigten Bearbeitungen – die Grundlage des Logs aus 5.5
- Der Levelwechsel schliesst eine offene Aufgabe **ab**, statt sie zu
  verwerfen: Projektregel 1 sagt "weiter, egal was offen ist", aber die
  Aufgabe muss im Log stehen bleiben, sonst lässt sich "nicht bearbeitet"
  nicht von "Zeit war um" unterscheiden. Im Log steht sie als `abgebrochen`
- **Sperren gegen Oberflächenfehler** – ein Screen, der in Phase 6 neu
  aufgebaut wird, soll die Messdaten nicht verfälschen können:
  - `starte_level()` gibt es **einmal je Durchlauf**, danach nur
    `naechstes_level()`. Sonst begänne ein Zeitfenster von vorn oder ein Level
    fiele aus. Ein Durchlauf, der nicht bei Level 1 begann, gilt nie als
    durchgespielt
  - Nach dem Zeitablauf wird keine Aufgabe mehr gestellt (`ZeitIstUm`); die
    Oberfläche fängt das und ruft `pruefe_zeitfenster()`
  - Jeder Funkspruch kommt nur einmal (sonst drei frische Versuche und eine
    doppelte Kennung im Log)
- Die automatisch erzeugte Pseudonym-ID ist `P` plus der vollständige,
  neunstellige Seed – gekürzt hätten zwei Durchläufe dieselbe ID bekommen
  können
- Die **Levelzeit** wird festgehalten (`level_sekunden()`, `levelende()`):
  CLAUDE.md verlangt die Zeitmessung pro Level *und* pro Aufgabe

### 5.2 Level-Timer — `game/zeitfenster.py`
- 15 / 20 / 25 Minuten pro Level
- Bei Ablauf: automatisch weiter zum nächsten Level, unabhängig davon, was
  gerade offen ist
- Sichtbare Restzeit für die Spielenden (`spielstand.restzeit_text`, "MM:SS")
- **Die Uhr wird eingespeist** (`zeitgeber`), sonst liessen sich fünfzehn
  Minuten nur durch fünfzehn Minuten Warten prüfen
- **`time.monotonic`, nicht `time.time`:** Ein Zeitserverabgleich oder ein
  Sommerzeitwechsel würde sonst mitten im Level das Fenster verfälschen
- **Das Fenster hält nie an** – es gibt bewusst kein `anhalten()`
  (Projektregel 1)
- Der Ablauf wirkt erst, wenn die Oberfläche `spielstand.pruefe_zeitfenster()`
  aufruft (in Tkinter über `after`). So baut kein Nebenläufigkeitsfaden mitten
  in einer Eingabe den Zustand um

### 5.3 Aufgaben-Timer — in `game/bearbeitung.py`
- Misst Zeit **pro Aufgabe**, nicht die Gesamtdauer des offenen Fensters
- Die Uhr hält an, sobald die Aufgabe **entschieden** ist. Das Lesen der
  Lösung und der Weiterrechnen-Knopf zählen nicht mehr mit – sonst hinge die
  gemessene Zeit davon ab, wie lange jemand danach noch herumklickt
- Dieselbe eingespeiste Uhr wie beim Zeitfenster (`time.monotonic`)

### 5.4 Adaptive Zusatzaufgaben — `game/zusatzaufgaben.py`
- Wer deutlich unter dem Schwellenwert liegt, bekommt eine Extra-Aufgabe aus
  demselben Wortpool
- Schwellenwerte stehen **an einer Stelle**, damit sie nach dem
  Pilotdurchlauf mit einem Handgriff angepasst werden können
- **Nicht Sekunden je Buchstabe, sondern eine Gerade:**
  `erwartet = GRUNDZEIT + BUCHSTABEN * SEKUNDEN_JE_BUCHSTABE`. Jede Aufgabe hat
  eine feste Grundzeit (lesen, Schlüssel nachschlagen, tippen), die nichts mit
  ihrer Länge zu tun hat. Ein reines "Sekunden je Buchstabe" würde am Ende die
  Länge der gezogenen Aufgabe messen statt das Tempo der Person
- **Obergrenze je Level** (`HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL`): Der Pool hat
  zehn Texte, danach wiederholen sie sich – und eine versehentlich zu
  grosszügige Schwelle liefe sonst bis zum Zeitablauf durch, ohne dass die
  Person je zum Funkspruch käme
- Eine Zusatzaufgabe kurz vor Schluss wird nicht gestellt (Projektregel 1: sie
  würde nur unfertig abgebrochen)
- **Im Pilotdurchlauf nachmessen:** die Spalten `sekunden` und
  `gerechnete_buchstaben` aus dem Log gegeneinander auftragen und die Gerade
  daran anpassen – Zeilen mit `abgebrochen = ja` vorher herausfiltern, dort
  ist die Zeit keine Rechenzeit
- **Nur Übungen lösen eine Zusatzaufgabe aus.** Die Zusammenfassung legt den
  Ablauf fest: "Übungsaufgaben (+ ggf. Zusatzaufgaben) → echte Sendeaufgabe
  → Bobs Antwort". Nach einem Funkspruch hat die Geschichte begonnen
- **Die Restzeit wird am längsten Text im Pool gemessen**, nicht an der eben
  gelösten Aufgabe – welcher Text als Nächstes kommt, steht nicht fest, und in
  Level 2 liegen 7 gegen 18 Buchstaben dazwischen
- Die Obergrenze gilt im Spielstand selbst: `naechste_uebung(zusatzaufgabe=True)`
  wird darüber hinaus abgewiesen, auch wenn die Oberfläche nicht vorher fragt

### 5.5 CSV-Logging
Pro Aufgabe eine Zeile: Pseudonym-ID, Level, Aufgabennummer, Richtung, Anzahl
Versuche, Lösung angezeigt (ja/nein), benötigte Sekunden, Zusatzaufgabe (ja/nein).
- **Zusätzlich: Versuche ohne Fortschritt**, getrennt von der Gesamtzahl der
  falschen Eingaben (siehe 4.3).
- **Zusätzlich: Länge des tatsächlich geprüften Textes in Buchstaben.** Bei
  Funksprüchen mit Teilaufgabe wird nicht die ganze Nachricht gerechnet – ohne
  diese Spalte sind die Bearbeitungszeiten später nicht vergleichbar.
- **Der Seed des Durchlaufs gehört einmal pro Logdatei hinein**
  (`game/zufallsquelle.py`, Feld `protokollwert`). Zusammen mit der
  **Kennung** (`uebung_l2_3` = dritte Übung in Level 2) lässt sich damit
  später nachbauen, welches Wort jemand bekommen hat – siehe
  `game.generator.uebung_nachbauen(seed, kennung)`. Ohne ihn ist eine lange
  Bearbeitungszeit nicht davon zu unterscheiden, dass jemand den längsten
  Übungssatz erwischt hat.
  *(Ursprünglich stand hier "Level und Aufgabennummer". Das stimmt nicht: Die
  Aufgabennummer zählt die Funksprüche mit, der Zufallsstrom nur die Übungen.
  Kommt ein Funkspruch vor einer Übung, liefert das alte Rezept
  stillschweigend das falsche Wort.)*
- **Zusätzlich: `abgebrochen`** – das Level endete mitten in der Aufgabe. Dann
  steht in `sekunden` die Zeit bis zum Levelwechsel, keine Rechenzeit; ohne
  diese Spalte wanderte sie in jeden Mittelwert
- **Zusätzlich: `gerechnete_buchstaben`** – wer bei einem langen Funkspruch
  von sich aus die ganze Nachricht rechnet, hat 78 statt 15 Buchstaben
  gerechnet
- **Zusätzlich: `levelende` und `level_sekunden`** – die Zeitmessung pro
  Level. Ohne sie lässt sich aus der Datei nicht sagen, ob ein Level am Timer
  endete oder früher fertig war
- **Zusätzlich: `figur`** (nur die Kennung) – die gesendeten Funksprüche
  tragen die Initialen der Figur, ihr Wortlaut hängt also an ihr
- Dateiname mit Zeitstempel, damit nichts überschrieben wird
- **Semikolon und `utf-8-sig`:** Die Datei wird auf einem deutschen Rechner in
  Excel geöffnet; mit einem Komma landete die ganze Zeile in einer Spalte.
  Für pandas: `read_csv(datei, sep=";", encoding="utf-8-sig")`
- **`sekunden` als ganze Zahl** – sonst käme das Dezimaltrennzeichen ins Spiel
  ("16.2" liest deutsches Excel nicht als Zahl, "16,2" kollidiert mit dem
  Semikolon). Eine Zehntelsekunde sagt bei einer halbminütigen Aufgabe nichts
- Der Seed steht als **Spalte in jeder Zeile**, nicht als Kommentarzeile über
  der Tabelle – sonst stolpert jedes Auswertungsskript darüber
- Wird nach jeder Aufgabe **und nach jedem Levelwechsel** geschrieben (immer
  dieselbe Datei), damit nach einem Absturz alles bis zur letzten erledigten
  Aufgabe gesichert ist
- **Erst in eine Nebendatei, dann in einem Schritt ersetzen.** Die Datei direkt
  zu überschreiben kürzt sie sofort auf null – bricht das Schreiben dann ab,
  bleibt nur die Kopfzeile, und ausgerechnet beim Absturz ist der ganze
  Durchlauf weg. Scheitert das Schreiben (etwa weil die Datei unter Windows in
  Excel offen ist), bleibt die alte Fassung stehen; die Oberfläche meldet es
  und versucht es nach der nächsten Aufgabe wieder
- Ein sehr langes Pseudonym wird **im Dateinamen** auf 40 Zeichen gekürzt
  (in der Spalte steht es vollständig) – sonst sprengt es die 255-Byte-Grenze
  des Dateisystems
- **Kein Klarname** – nur eine ID, die du separat zuordnest (Datenschutz)

---

## Phase 6 – Oberfläche

### 6.1 Fenstergerüst und Screen-Wechsel
- Ein Hauptfenster, Screens werden ausgetauscht
- Erst das Wechsel-Gerüst bauen, dann die einzelnen Screens füllen
- **Anschluss an Phase 5** – das Gerüst übernimmt, was der Spielstand bewusst
  der Oberfläche überlässt:
  - `spielstand.pruefe_zeitfenster()` über `after()` regelmässig aufrufen
    (mindestens einmal pro Sekunde – die Restzeitanzeige braucht den Takt
    ohnehin) und bei `True` zum nächsten Level wechseln. Ohne diesen Takt
    läuft kein Zeitfenster ab (Projektregel 1)
  - `ZeitIstUm` abfangen, wenn eine Aufgabe gestellt werden soll, und dann
    ebenfalls `pruefe_zeitfenster()` aufrufen
  - `Protokoll.schreiben()` nach jeder abgeschlossenen Aufgabe, nach jedem
    Levelwechsel und am Spielende. Einen `OSError` (etwa: Datei unter Windows
    in Excel offen) melden, nicht verschlucken – beim nächsten Schreiben wird
    alles nachgeholt
  - `naechste_uebung()` / `stelle_funkspruch()` erst aufrufen, wenn die
    Aufgabe auf dem Bildschirm steht – dort beginnt ihre Uhr

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
