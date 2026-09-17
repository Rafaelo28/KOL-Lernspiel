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
- **Nachtrag – ein Pool für alle Level:** Mit eigenen Listen je Seite wäre
  eine Übung in Level 3 schon wegen ihres Textes länger gewesen als eine in
  Level 1 (4–5 Buchstaben gegen 12–18), und in den Messdaten liesse sich nicht
  trennen, was am Verfahren liegt und was an der Länge. Jetzt üben alle drei
  Level mit denselben zehn Sätzen (`UEBUNGSTEXTE`), alle 10 bis 14 Buchstaben
  lang – übernommen aus den früheren Listen. `Handbuchtexte.md` führt sie als
  eine Liste für alle drei Seiten

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
- **Nachtrag – der gemeinsame Pool wird verteilt** (siehe 2.2): Zöge jedes
  Level frei aus denselben zehn Sätzen, käme ein Satz, den jemand in Level 1
  verschlüsselt hat, in Level 2 womöglich zum Entschlüsseln wieder – und
  liesse sich aus dem Gedächtnis eintippen. Deshalb wird der Pool einmal je
  Durchlauf aus dem Seed gemischt und in drei Abschnitte geteilt (4, 3, 3
  Sätze); jedes Level beginnt an seinem Abschnitt und geht der Reihe nach
  weiter. Die ersten drei Übungen eines Levels kommen in keinem anderen vor,
  zweimal hintereinander kommt kein Satz. Rekonstruieren lässt sich eine
  Übung weiterhin aus Seed und Kennung (`uebung_nachbauen`)

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
- `spielstand.restzeit_text` liefert die Restzeit als "MM:SS" – **wird aber
  bewusst nicht angezeigt** (Entscheidung bei 6.1, siehe dort): Ein
  mitzählender Countdown erzeugt Zeitdruck-Stress. Das Feld bleibt für Log
  und Tests nützlich
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
  gelösten Aufgabe – welcher Text als Nächstes kommt, steht nicht fest. (Seit
  alle Level einen Pool haben, liegen nur noch 10 gegen 14 Buchstaben
  dazwischen.)
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
- **Zusätzlich: `lineal_klicks`** (seit 6.7) – wie oft beim Lösen das Lineal
  im Vigenère-Quadrat bewegt wurde. Eine Zeit mit Lineal ist nicht ohne
  Weiteres mit einer ohne vergleichbar
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
- **Kein Klarname** – nur eine ID, die du separat zuordnest (Datenschutz).
  Seit 6.2 ist das die ID der Lehrkraft (`1-12`); in der Spalte steht sie als
  `ID 1-12`, damit Excel kein Datum daraus macht

---

## Phase 6 – Oberfläche

### 6.1 Fenstergerüst und Screen-Wechsel
- Ein Hauptfenster, Screens werden ausgetauscht
- Erst das Wechsel-Gerüst bauen, dann die einzelnen Screens füllen
- **Anschluss an Phase 5** – das Gerüst übernimmt, was der Spielstand bewusst
  der Oberfläche überlässt:
  - `spielstand.pruefe_zeitfenster()` über `after()` regelmässig aufrufen
    (mehrmals pro Sekunde) und bei `True` zum nächsten Level wechseln. Ohne
    diesen Takt läuft kein Zeitfenster ab (Projektregel 1) – auch ohne
    sichtbare Uhr im Fenster
  - `ZeitIstUm` abfangen, wenn eine Aufgabe gestellt werden soll, und dann
    ebenfalls `pruefe_zeitfenster()` aufrufen
  - `Protokoll.schreiben()` nach jeder abgeschlossenen Aufgabe, nach jedem
    Levelwechsel und am Spielende. Einen `OSError` (etwa: Datei unter Windows
    in Excel offen) melden, nicht verschlucken – beim nächsten Schreiben wird
    alles nachgeholt
  - `naechste_uebung()` / `stelle_funkspruch()` erst aufrufen, wenn die
    Aufgabe auf dem Bildschirm steht – dort beginnt ihre Uhr
- **Umgesetzt:**
  - `ui/hauptfenster.py` – das eine Fenster: Kopfzeile (Titel, Level),
    Meldungszeile, dazwischen der Screen. `zeige(Klasse, …)` baut den neuen
    Screen **frisch** auf und reisst den alten ab. Kein `tkraise`: Sonst
    stünde eine alte Eingabe oder Rückmeldung plötzlich bei der nächsten
    Aufgabe
  - **Kein Countdown im Fenster** (nachträgliche Entscheidung, nach 6.1):
    Ein sichtbar mitzählender Timer erzeugt Zeitdruck-Stress, besonders in
    der letzten Minute – und genau das braucht eine Verschlüsselungsaufgabe
    nicht. Das Zeitfenster läuft unverändert im Hintergrund (Projektregel 1
    ist nicht verhandelbar); läuft die Zeit ab, schaltet das Spiel weiter
    und zeigt einen Hinweistext ("Die Zeit für Level X ist abgelaufen …").
    Wie viel Zeit ein Level wirklich brauchte, steht im Log
    (`level_sekunden`, `levelende`), nicht im Fenster
  - `ui/screen.py` – Grundform der Screens. Aufgaben erst in
    `beim_anzeigen()` stellen; verzögerte Aufrufe über `spaeter()` statt
    `after()`, dann meldet der Wechsel sie ab
  - `game/durchlauf.py` – Spielstand und Protokoll in einer Hand, ohne
    Tkinter und deshalb ohne Bildschirm testbar. Was eine Aufgabe stellt,
    abschliesst oder das Level wechselt, geht hier durch, und gespeichert wird
    dabei von selbst. So kann kein Screen das Speichern vergessen
  - `ui/ablauf.py` – welcher Screen wann kommt; hier setzt Phase 7 die Level
    zusammen. Die Platzhalter-Screens, die dort anfangs standen
    (`ui/platzhalter.py`), sind mit 6.2–6.8 wieder verschwunden
  - Der Takt wird im `finally` neu angemeldet – ein Fehler im Takt hält die
    Uhr nicht an
  - Fehler in Knöpfen erscheinen in der Meldungszeile. Tkinter schriebe sie
    nur auf die Konsole, und die sieht im Klassenzimmer niemand
  - Das Kreuz am Fenster fragt während eines Levels nach. Beim Schliessen wird
    die offene Aufgabe als abgebrochen gespeichert; scheitert das Speichern,
    lässt es sich wiederholen
  - Ein Fenster, ein Durchlauf – für die nächste Person wird neu gestartet
  - Die Logs landen neben `main.py` (`main.PROTOKOLLORDNER`), nicht im
    Verzeichnis, aus dem gestartet wurde
  - **Bildschirmgrösse** (nachträglich, nach 6.2 – aufgefallen auf den
    1080p-Schulmonitoren: maximiert stand das Spiel klein oben in der Mitte):
    - Das Fenster öffnet **maximiert**; F11 schaltet auf echtes Vollbild, Esc
      zurück
    - Die **Kopfzeile** steht im Nachthimmel des Spiels (Titel in Sand, Level
      gedämpft, darunter eine kaum sichtbare Linie). Die graue Standardleiste
      von Tk wirkte über Buch und Szenen unseriös
    - **Maßstab:** Ab 1920 × 1080 wird alles 1,5-mal so gross gezeichnet –
      Schriften, Abstände und die Bilder (`ui/stil.py`, `massstab_fuer`). Die
      Screens rechnen feste Pixelangaben mit `self.px(…)` um
    - Die Bilder gibt es dafür in einem **zweiten, schärferen Satz** (1440 ×
      810 statt 960 × 540), gerendert aus derselben SVG. Das kleine Bild im
      Spiel zu vergrössern sähe grob aus – Tkinter kann nur Pixel verdoppeln
    - Die Screens stehen **in der Mitte** des Fensters, der Rand drumherum hat
      ihre Hintergrundfarbe. Ein Screen, der den ganzen Platz braucht, setzt
      `fuellt_fenster = True`
    - Die Tests prüfen jeden Bild-Screen in beiden Maßstäben: im kleinen in
      1000 × 700, im grossen in 1920 × 980 (1080p abzüglich Titel- und
      Taskleiste, mit 20 Pixel Luft für Schriften unter Windows)

### 6.2 Startbildschirm + Charakterauswahl
- **Umgesetzt:**
  - `ui/startbildschirm.py` – Titelbild als Animation (`grafik/titel.svg`):
    ein großer Diamant im Nachthimmel über der Wüste, Lichtreflexe wandern
    über die Facetten, danach glänzt der Schriftzug auf. Darunter das Feld
    für die ID (siehe unten) und "Spiel starten" – die Geschichte beginnt
    erst auf dem nächsten Screen
  - `ui/figurwahl.py` – oben die **Vorgeschichte** (`story.VORGESCHICHTE`,
    die Prämisse aus dem Konzept: Raub in Antwerpen, Flucht, Absturz). Sie
    stand bisher in keinem Spieltext, und der Intro setzt sie voraus – er
    beginnt schon am brennenden Wrack. Darunter "Wer aus der Crew bist du?"
    und die fünf Figuren als Karten: Symbol, Initialen, Name, Rolle
  - **Rollen-Symbole statt Gesichter** (Tresor, Lupe, Chip, Landkarte, Pass):
    Ein gezeichnetes Gesicht legt Aussehen, Geschlecht und Herkunft fest und
    wirkt schnell wie ein Klischee – mit einem Symbol kann sich jedes Kind
    jede Figur aussuchen. Die Symbole sind kleine Animationen
    (`grafik/figur_<kennung>.svg`); es bewegt sich das Symbol unter dem
    Mauszeiger (so merkt man beim Drüberfahren, dass es Animationen sind) und
    das der gewählten Karte
  - **Erst wählen, dann bestätigen:** Ein Klick auf eine Karte wählt nur aus,
    erst "Als … spielen" legt die Figur fest und beginnt den Durchlauf.
    Danach lässt sie sich nicht mehr wechseln (ein Fenster, ein Durchlauf) –
    ein versehentlicher Klick soll deshalb noch nichts festlegen. Pfeiltasten
    und Enter gehen auch
  - Die Initialen stehen als Siegel auf jeder Karte, mit dem Hinweis, dass sie
    später jeden Funkspruch unterschreiben
  - Der Weg Start (mit ID) → Figurwahl → Intro → Level 1 steht jetzt
    vollständig in `ui/ablauf.py`; die Screens bekommen ihr "danach" von dort und wissen
    nichts vom Ablauf. Die Platzhalter `Start` und `Figurwahl` sind entfernt
  - **ID-Feld auf dem Startbildschirm** (nachträglich entschieden): Die
    Lehrkraft verteilt IDs der Form `X-XX` – Klasse, Strich, Nummer; `1-12`
    ist das zwölfte Kind der 7/1. Das Feld nimmt nur Ziffern und den Strich
    an seiner Stelle an (`game/spieler_id.py`), einen Namen kann man also gar
    nicht erst eintippen – auch nicht per Einfügen. Wer nach der Klasse gleich
    die Nummer tippt, bekommt den Strich dazu. Ohne vollständige ID geht es
    nicht weiter, und der Hinweis sagt genau, was fehlt ("Deine Nummer hat
    zwei Ziffern … 1-02"). Löschen bleibt immer erlaubt, sonst liesse sich
    nichts ausbessern
  - Die ID wird bis zur Figurwahl mitgereicht und beim Bestätigen zum
    Pseudonym des Durchlaufs: Dateiname `durchlauf_1-12_<Zeitstempel>.csv`
  - **In der CSV steht `ID 1-12`, nicht `1-12`:** Deutsches Excel liest `1-12`
    beim Öffnen als 1. Dezember (und `1-45` als Januar 1945); wer die Datei
    danach speichert, hat die ID verloren. Mit einem Buchstaben vorn bleibt es
    Text. Für pandas: `tabelle["pseudonym"].str.removeprefix("ID ")`
  - Alles passt ins Fenster – im kleinen Maßstab in 1000 × 700, im grossen
    auf den 1080p-Schulmonitor (siehe 6.1, "Bildschirmgrösse"); Tests prüfen
    beides. Wird das Fenster von Hand schmaler gezogen, wird die rechte Karte
    abgeschnitten – wie die Szenen in 6.3
### 6.3 Story-Intro (Absturz-Szene)
- **Umgesetzt** (vor 6.2 gezogen – die Platzhalter aus 6.1 überbrücken die
  Lücke):
  - Die Szene läuft als Animation: das brennende Wrack in den Dünen, mit
    sechs kleineren Bränden über das ganze Flugzeug verteilt, Rauchsäule,
    Funken, dem zurückgelassenen Diamantensack und Fußspuren, die vom Wrack
    wegführen (`grafik/wrack.svg`). Wie Animationen entstehen:
    `dokumentation/Animationen.md`
  - `ui/erzaehlszene.py` (bis Phase 7 `ui/intro.py`) zeigt die drei Absätze
    aus `story.INTRO` nacheinander im
    Nachthimmel oben rechts – dort bewegt sich nichts, und der Text liegt nicht
    über dem Feuer. Ein Absatz auf einmal: Neunzig Wörter am Stück über einer
    bewegten Szene wären zu viel
  - Der letzte Knopf heisst "Handbuch aufschlagen" und startet Level 1 – der
    Intro kostet keine Levelzeit (siehe 7.1)
  - Die Szene ist 960 × 540 Pixel gross, auf dem 1080p-Schulmonitor 1440 ×
    810 (siehe 6.1, "Bildschirmgrösse"). Wird das Fenster von Hand schmaler
    gezogen, wird sie rechts abgeschnitten
### 6.4 Handbuch-Screen
- Scrollbarer Text, Tabellen als Grid
- Muss während der Aufgaben erreichbar bleiben (Nachschlagen ist erlaubt)
- **Umgesetzt – als aufgeschlagenes Buch:** Statt eines Blattes zum Scrollen
  liegt Bobs Handbuch als **altes, in Leder gebundenes Buch** vor den
  Spielenden: Einband mit Goldprägung, vergilbte Seiten mit Stockflecken,
  Eselsohr, hochgebogene Ecken. Geblättert wird
  in Doppelseiten, und dabei schlägt sichtbar ein Blatt um
  - **Die Bilder** entstehen aus einem Programm, nicht von Hand:
    `grafik/buch_zeichnen.py` schreibt `grafik/buch.svg` (das Buch als
    Standbild) und `grafik/umblaettern.svg` (zwölf Bilder, durchsichtig, mit
    derselben viewBox). Beide brauchen dasselbe Blatt – sonst sprängen beim
    Umblättern die Kanten. Dazu `grafik/stempel.svg` ("STRENG GEHEIM",
    durchsichtig). Gerendert wie jede Animation (`dokumentation/Animationen.md`)
  - **Der Satz** (`ui/buchsatz.py`): Ein Buch hat feste Seiten, also muss
    vorher feststehen, was auf welche passt. Absätze werden in Zeilen
    umbrochen und die Zeilen auf Seiten verteilt – mit den Regeln aus dem
    Buchdruck: Eine Überschrift steht nie allein unten; ein geteilter Absatz
    lässt unten zwei Zeilen stehen und nimmt zwei mit; ein Absatz mit
    Doppelpunkt bleibt bei dem, was er ankündigt; Tabellen, Merksätze und
    Randnotizen werden nicht geteilt. Gemessen wird mit genau den Schriften,
    mit denen danach gezeichnet wird
  - **Beispiele mit dem Werkzeug gegenüber** (Nachtrag): Ein durchgerechnetes
    Beispiel versteht man nur mit der Tabelle daneben. Ein Abschnitt kann
    deshalb ein Werkzeug `gegenueber` nennen (`content.handbuch.Abschnitt`)
    – das verschobene Alphabet, die Geheimtabelle, das Quadrat. Solche
    Abschnitte stehen immer auf linken Seiten, und neben **jeder** ihrer
    Seiten liegt rechts das Werkzeug; folgen mehrere mit demselben Werkzeug
    aufeinander (Seite 3: Quadrat, Verschlüsseln, Entschlüsseln), laufen sie
    ineinander weiter. Wäre die erste davon eine rechte Seite, bleibt die
    leer (mit Verzierung, ohne Seitenzahl). Was danach ohne Werkzeug kommt,
    beginnt auf einer neuen Seite. Ein Beispiel, das auf eine Seite passt,
    wird nicht geteilt; bei einem längeren bleiben wenigstens die Schritte
    beisammen, und das Ergebnis bleibt bei ihnen
  - **Der Schritt ist markiert:** Die `schritte` eines Beispiels
    (`content.handbuch.Schritt`: Spalte, Kreuzung, im Quadrat auch die
    Zeile) gehören zu seinen nummerierten Punkten oder – bei Caesar und der
    Substitution – zu den Spalten seiner Beispieltabelle. Einer davon steht
    immer unter Textmarker, zu Beginn der erste; im Werkzeug ist markiert,
    wo er sucht: im Quadrat die Zeile des Schlüsselbuchstabens und die Spalte
    des Nachrichtenbuchstabens, jeweils vom Kopf bis zum Kreuzungspunkt, in
    einer Tabelle die Spalte bis zum abgelesenen Feld; der Kreuzungspunkt
    kräftiger und rot umrandet. Zeigt die Maus auf einen anderen Schritt,
    wandert die Markierung mit (und bleibt, wenn die Maus weiterzieht); ein
    Klick oder die Pfeiltasten hoch/runter tun dasselbe. Die Markierung zeigt
    nur, was im Schritt schon steht ("Zeile R, Spalte H … steht Y"), und ein
    Test prüft jeden Schritt gegen `crypto/` – die Kontrollgruppe liest
    dieselben Beispiele
  - **Titelseite:** Links auf der ersten Doppelseite stehen Titel und
    Untertitel des Handbuchs, eine Verzierung, das **Inhaltsverzeichnis des
    Kapitels mit Seitenzahlen** und der Stempel. Rechts beginnt das Kapitel
  - **Breite Tabellen** (26 Buchstaben) passen auf keine Buchseite; sie
    werden in so wenige Teile wie möglich zerlegt (A–M / N–Z), jeder Teil mit
    seiner Beschriftung. Das **Vigenère-Quadrat** bekommt eine Seite für sich
    und wird so gross gezeichnet, wie sie es erlaubt (im grossen Maßstab
    20 Pixel je Feld). Es entsteht weiterhin aus der Formel
    (`crypto/vigenere_quadrat.py`), nicht abgetippt; ein Test vergleicht alle
    676 Felder. Neben den Beispielen sind Zeile, Spalte und Kreuzungspunkt
    markiert (siehe oben)
  - Der **Merksatz** steht auf einer Karte, die mit Klebeband ins Buch
    geklebt ist; Beispiel-Überschriften und Ergebnisse ("HUND wird zu KXQG")
    sind fett (`betont` in `content/handbuch.py`)
  - **Bobs Randnotizen** (neu: `content.handbuch.Randnotiz`) stehen in
    Handschrift, blau und etwas schief am Rand. Sie **wiederholen nur**, was
    auf der Seite schon steht ("Nach Z geht's wieder bei A los – wie bei der
    Uhr!"). Grund ist der Versuchsaufbau: Die Kontrollgruppe lernt mit
    denselben Handbuchtexten; ein Tipp, der im Handbuch fehlt, vergliche
    nicht mehr Lernspiel und Unterricht, sondern zwei Erklärungen. Jede Notiz
    nennt die Stelle, die sie wiederholt – ein Test prüft, dass es sie gibt
  - **Blättern:** Knöpfe unter dem Buch, Pfeiltasten und Bild auf/ab,
    Mausrad und ein Klick auf die hochgebogenen Ecken unten außen. (Ein
    Lesezeichen-Band, das zur wichtigsten Tabelle sprang, gab es zuerst
    auch – es flackerte beim Umblättern und war unnötig, seit das Werkzeug
    in 6.5 ohnehin neben jeder Übung liegt; es ist wieder entfernt)
  - **Umblättern:** `ui.animation.Ablauf` legt die zwölf durchsichtigen
    Bilder über die Leinwand. Vorwärts liegt die neue rechte Seite schon
    unter dem Blatt und die neue linke erscheint, wenn es gelandet ist –
    rückwärts umgekehrt. Solange es umschlägt, wird nicht noch einmal
    geblättert (ein schnell gedrehtes Mausrad soll nicht fünf Seiten
    weiterspringen). Die Bilder sind gross (im grossen Maßstab rund 50 MB):
    Sie werden erst geladen, wenn das Buch schon dasteht, und bleiben im
    `zwischenspeicher` des Hauptfensters – das Handbuch wird zu Beginn jedes
    Levels und bei jedem Nachschlagen neu aufgeschlagen
  - **Schriften:** eine Buchschrift (Palatino Linotype, Georgia … je nach
    Rechner) und für die Notizen eine Handschrift (Ink Free, Segoe Print,
    Z003 …); fehlen alle, wird kursiv gesetzt (`ui/stil.py`,
    `erste_schrift`)
  - Über dem Buch steht der **Einstieg ins Level** aus der Geschichte ("Du
    schlägst das Handbuch auf …", `story.EINSTIEG_NACH_LEVEL`), nach einem
    Zeitablauf davor der Hinweis "Die Zeit für Level … ist abgelaufen". Im
    grossen Maßstab dürfen diese Zeilen breiter werden als das Buch: Auf dem
    1080p-Monitor ist neben dem Buch Platz, in der Höhe aber nicht
  - **Nachschlagen während der Aufgaben:** `handbuch.nachschlagen(fenster,
    level, zurueck)` zeigt dasselbe Buch mit "Zurück zur Aufgabe". Die
    Aufgabe bleibt offen, ihre Uhr läuft weiter – Nachschlagen gehört zum
    Lösen und zählt deshalb zur Bearbeitungszeit. Der Aufgaben-Screen baut
    sich danach frisch auf und setzt dieselbe Aufgabe fort (der Platzhalter
    der Übung macht es schon so: `Uebung(fortsetzen=True)`). Läuft die Zeit
    beim Nachschlagen ab, gilt Projektregel 1: Die Aufgabe wird abgebrochen,
    das nächste Kapitel liegt auf
  - Ein Handbuch im Spiel, kein zweites Fenster: Ein zweites Fenster verlöre
    man hinter dem maximierten Spiel, und das Spiel hat bewusst genau eines
  - **Grössen:** Das Buch ist 960 × 492 Pixel gross, auf dem
    1080p-Schulmonitor 1440 × 738. Die Textflächen der beiden Seiten stehen
    als Pixelmaße in `ui/buchleinwand.py` und in SVG-Einheiten in
    `grafik/buch_zeichnen.py`; ein Test prüft im gerenderten Bild, dass dort
    überall Papier ist – und die Layout-Tests, dass nichts darüber hinausragt
    und kein Text auf einem anderen liegt

### 6.5 Aufgaben-Screen
- Aufgabentext, Schlüsselangabe, Eingabefeld, Prüf-Button, Rückmeldung,
  Versuchszähler
- **Umgesetzt – die Übung steht im Buch** (`ui/uebung.py`): Bobs Handbuch
  liegt aufgeschlagen da; rechts die Übung, links das Werkzeug zum Lösen.
  Geschrieben wird also mitten ins Buch, wie in ein Übungsheft – gelernt und
  geübt wird an derselben Stelle
  - **Rechte Seite:** Überschrift ("Übung 3" – die wievielte im Level),
    der Auftrag mit Schlüsselangabe ("Entschlüssele mit dem Schlüssel 16:",
    "Verschlüssele mit deiner Geheimtabelle:", "… mit dem Schlüsselwort
    ROT:"), darunter der Aufgabentext gross, ein Schreibfeld und die
    Rückmeldung
  - **Linke Seite – das Werkzeug** (`content.handbuch.WERKZEUG_NACH_LEVEL`):
    bei Caesar **nur das blanke Alphabet** zum Abzählen, bei der Substitution
    die Geheimtabelle, bei Vigenère das Quadrat. Die verschobene Zeile aus dem
    Handbuch wäre für den Schlüssel der Aufgabe die halbe Lösung – im Handbuch
    steht sie nur als Beispiel mit dem Schlüssel 3. Darunter klebt in Level 1
    und 2 eine **Merkkarte** (`content.handbuch.MERKKARTE_NACH_LEVEL`), die
    sagt, wie man mit dem Werkzeug rechnet: bei Caesar der Merksatz der
    Handbuchseite, bei der Substitution die beiden Sätze, mit denen das
    Handbuch die Geheimtabelle liest ("So geht's"). Der Merksatz von Seite 2
    ("Je länger der Text, desto leichter … Häufigkeitsanalyse") erklärt,
    warum die Methode unsicher ist – beim Lösen hilft er nicht und liegt dort
    deshalb nicht. Jeder Satz der Karte steht so im Handbuch oder wiederholt
    eine Stelle daraus (Test wie bei den Randnotizen). Neben dem Quadrat ist
    für eine Karte kein Platz
  - **Die Regeln kommen aus der Spiellogik**, der Screen zeigt sie nur: die
    konkrete Fehlermeldung (Projektregel 6), der Hinweis "Du bist näher dran
    als vorher – dieser Versuch zählt nicht mit", die verbleibenden Versuche
    und nach dreien ohne Fortschritt die Lösung (Projektregel 2). Eine leere
    Eingabe kostet keinen Versuch
  - **Drei Dinge machen die Rückmeldung sichtbar statt nur lesbar:** Die
    Stelle, die die Meldung nennt, wird im Aufgabentext rot unterringelt
    (dieselbe Auskunft, nur schneller zu finden – welcher Buchstabe dort
    hingehört, verrät sie weiterhin nicht). Stimmt die Antwort, schlägt der
    Stempel "GELÖST" auf die Seite (`grafik/stempel_geloest.svg`). Und
    geschrieben wird in Handschrift, als hätte man den Bleistift selbst in
    der Hand
  - Ist die Aufgabe entschieden, weicht das Schreibfeld dem, was darin stand:
    Die Antwort steht dann als Handschrift im Buch, und der Stempel kann
    darüberliegen. (Ein eingebettetes Eingabefeld liegt in Tk immer über
    allem, was auf der Leinwand steht.) Aus "Prüfen" wird "Weiter"
  - **Nachschlagen:** "Im Handbuch nachschlagen" zeigt das ganze Handbuch und
    kommt zu **derselben** Aufgabe zurück – samt dem, was schon im
    Schreibfeld stand, und dem Stand der Versuche. Die Uhr der Aufgabe läuft
    weiter: Nachschlagen gehört zum Lösen
  - **Gemeinsam mit 6.4:** Das Buch selbst – Bild, Schriften, Stempel und das
    Zeichnen der gesetzten Stücke – steht jetzt in `ui/buchleinwand.py`;
    Handbuch und Übung benutzen dieselbe Leinwand. `buchsatz.einzelseite`
    setzt das Werkzeug auf die linke Seite
  - **Platzhalter bis 7.1:** Unter dem Buch hängt ein Knopf "Level beenden",
    mit dem sich ein Level vorzeitig beenden lässt. Ohne ihn müsste man beim
    Durchklicken jedes Zeitfenster abwarten. Was nach einer Übung kommt,
    entscheidet `ui/ablauf.py` (`uebung_beendet`) – dort setzt Phase 7 die
    Funksprüche dazwischen
- Aus 6.4: ein Knopf "Im Handbuch nachschlagen" über
  `handbuch.nachschlagen(...)`; der Screen muss eine **offene Aufgabe
  fortsetzen** können, statt eine neue zu stellen – samt dem, was schon
  eingetippt war, und dem Stand der Versuche aus dem Spielstand
- Das Werkzeug zum Lösen gehört **auf** den Aufgaben-Screen, nicht nur ins
  Handbuch: das Alphabet (Level 1), die Geheimtabelle (Level 2), das Quadrat
  (Level 3, siehe 6.7). Für jeden Buchstaben ins Handbuch zu wechseln, kostete
  Zeit, die dann in den Messdaten stünde

### 6.6 Funk-Screen
- Optisch abgesetzt vom Handbuch, damit "echte Nachricht" und "Übung"
  unterscheidbar sind
- **Als Gerät, nicht als Formular** (festgelegt nach 6.4): Die
  story-tragenden Funksprüche werden an einem **Funkgerät** ver- und
  entschlüsselt – Metallgehäuse, leuchtende Anzeige, Skala, Kippschalter,
  Kontrolllämpchen; der Text erscheint zeichenweise, als käme er gerade
  herein. Das Handbuch ist Papier, der Funk ist Technik: Schon am Bild ist zu
  sehen, ob gerade geübt wird oder ob es ernst ist. Entsteht wie das Buch als
  SVG in `grafik/` und wird vorgerendert
- **Beim Empfangen bleibt der vollständige Geheimtext sichtbar**, der selbst
  zu entschlüsselnde Anfang ist hervorgehoben. Sonst sieht man in Level 2 nicht
  mehr, dass der Geheimtext lang ist – und genau darauf beruht der Merksatz zur
  Häufigkeitsanalyse auf Handbuchseite 2
- **Beim Senden gilt das Gegenteil:** sichtbar ist der vollständige Klartext,
  der Geheimtext niemals – er ist die Lösung, die eingetippt werden soll
- Knopf "Den Rest entschlüsseln" plus Erzähltext-Einblendung (siehe 4.4)
- **Umgesetzt** (`ui/funk.py`, Bild `grafik/funkgeraet.svg` aus
  `grafik/funkgeraet_zeichnen.py`): Das olivgrüne Feldfunkgerät steht rechts
  auf dem aufgeschlagenen Handbuch; links liegt wie bei den Übungen das
  Werkzeug, in Level 3 mit dem Lineal. Über dem Gerät steht die Einleitung
  des Funkspruchs aus `content/story.py`
  - **Das Glas:** oben Richtung und Gegenüber ("EMPFANG · ZENTRALE",
    "SENDEN") und womit gerechnet wird ("Caesar · Schlüssel 3"), darunter der
    Auftrag, die Nachricht, die Eingabezeile und die Rückmeldung. Die Schrift
    hat feste Zeichenbreiten (Consolas unter Windows). Eine empfangene
    Nachricht kommt Zeichen für Zeichen herein, das Empfangslämpchen flackert
    dazu; nach dem Senden leuchtet das Sendelämpchen
  - **Die Regel aus CLAUDE.md:** Beim Empfangen steht der ganze Geheimtext da,
    der zu rechnende Anfang leuchtet hell und ist unterstrichen, der Rest ist
    matt. Beim Senden steht der ganze Klartext da – der Geheimtext nie, auch
    nach dem Senden nicht ("GESENDET."); Tests suchen ihn in jedem Text auf dem
    Bildschirm. Der Prüfknopf heisst beim Senden "Senden": Falsch
    Verschlüsseltes geht nicht raus
  - **Rückmeldung** aus der Spiellogik wie bei den Übungen: die Meldung in
    Warnfarbe, die Stelle in der Nachricht unterwellt, Fortschrittshinweis,
    Versuche. Steht nach drei Versuchen ohne Fortschritt die Lösung da, steht
    auf dem Glas nur noch sie – sonst reichte der Platz bei den langen
    Nachrichten nicht
  - **Der Rest:** Erst nach dem Anfang (gelöst oder aufgelöst) erscheint der
    Knopf aus `story.BESCHRIFTUNG_REST` – vorher und statt "Weiter". Er setzt
    den Erzähltext über das Gerät (der Platz darüber ist von Anfang an so hoch,
    dass nichts springt) und gibt die ganze Nachricht frei: beim Empfangen der
    ganze Klartext auf dem Glas, beim Senden das Sendelämpchen
  - **Nachschlagen** geht auch hier; zurück kommt man zu demselben Funkspruch,
    ohne dass er noch einmal hereinkommt, samt Eingabe und Stand
  - **Bis Phase 7** erreicht man die Funksprüche über den Platzhalter-Knopf
    "Zum Funkgerät" unter den Übungen (`ablauf.funksprueche_zeigen`: die
    offenen Funksprüche des Levels der Reihe nach, danach das nächste Level;
    neu: `Spielstand.offene_funksprueche`). Eine offene Übung wird dabei
    abgelegt
  - Nebenbei: Die Zeilen über Buch und Gerät werden im grossen Maßstab nicht
    breiter als auf einem 1080p-Monitor – auf einem noch breiteren Bildschirm
    wäre das Fenster sonst zu breit geworden

### 6.7 Vigenère-Quadrat als Anzeige
- 26×26-Grid aus Phase 1.5, mit Hervorhebung der aktiven Zeile/Spalte
- Muss auf kleinen Schulmonitoren lesbar sein – testen!
- Aus 6.4 und 6.5: Handbuch und Aufgabe zeichnen das Quadrat mit demselben
  Bauteil (`Buchleinwand._quadrat_zeichnen`, Grösse aus `buchsatz.Quadrat`);
  jedes Feld trägt die Tags `z<Zeile>` und `s<Spalte>`. Im Handbuch markiert
  `Buchleinwand.werkzeug_markieren` neben den Beispielen Zeile, Spalte und
  Kreuzungspunkt des gezeigten Schritts
- **Umgesetzt – das Lineal beim Lösen** (`ui/lineal.py`), in Level 3 von der
  ersten Übung an: Ein Klick links auf den Schlüsselbuchstaben legt es an die
  Zeile, ein Klick oben auf den Buchstaben der Nachricht an die Spalte; wo sie
  sich kreuzen, liegt der Marker dunkler. Ein Klick ins Quadrat legt beide an
  dieses Feld (beim Entschlüsseln: vom gefundenen Buchstaben hinauf zum
  Spaltenkopf), ein zweiter Klick auf denselben Kopf nimmt es wieder ab. Ein
  Satz unten auf der Übungsseite sagt, dass es das Lineal gibt
  - **Es markiert nur und liest nicht ab:** Kein Buchstabe wird ausgegeben
    (ein Test prüft, dass das Lineal keinen einzigen Text anlegt). Das Ablesen
    im Quadrat ist genau, was Level 3 misst; die Kontrollgruppe darf auf
    Papier Finger und Lineal benutzen – mehr nicht. Ein Werkzeug, das den
    Kreuzungspunkt nennt, wäre ein Rechner
  - **Im Log:** `lineal_klicks` zählt je Aufgabe, wie oft das Lineal bewegt
    wurde, solange sie lief (siehe 5.5)
  - Für die Funksprüche in Level 3 (6.6) liegt das Lineal als eigenes Bauteil
    bereit: Es braucht nur eine Buchleinwand mit dem Quadrat darauf

### 6.8 Abschluss-Screen
- Nachthimmel, Rettung, Schlusstext (Diamanten bleiben zurück)
- **Umgesetzt** (`ui/abschluss.py`, Bilder aus `grafik/abschluss_zeichnen.py`),
  mit zwei Wünschen aus der Abnahme: Nach "Warten" schläft man ein, und es muss
  klar sein, dass der Hubschrauber Freunde bringt
  - **Das Nachtlager an der Oase:** Lagerfeuer, Rucksack, Decke und das
    ausgeschaltete Funkgerät, dahinter das Wasser der Oase mit Palmen, darüber
    Mond und Sterne. Oben links der Text aus `story.NACHTHIMMEL`, unten rechts
    der Knopf "Warten". Die Oase kam nach der Abnahme dazu: Sie erklärt, warum
    das Lager nicht am Wrack steht, und sie gibt dem Standort-Funkspruch in
    Level 3 sein Geheimnis ("OASE DREI KILOMETER" wird von Hand verschlüsselt)
  - **Einschlafen:** Zwei Lider mit gebogener Kante schieben sich über das
    Bild, öffnen sich noch zweimal halb und schließen sich; auf Schwarz steht
    "Die Nacht vergeht." Hinter den geschlossenen Augen wechselt die Szene zum
    **Morgengrauen** (dieselbe Stelle, das Feuer ist aus). Das Geräusch der
    Rotorblätter weckt, noch bevor man etwas sieht; dann blinzelt man, und der
    Hubschrauber fliegt von rechts ein und landet neben dem Lager, sein
    Schatten wächst auf dem Sand. Der Erzähltext liegt über den Lidern und
    bleibt lesbar (neu in `content/story.py`: `EINSCHLAFEN`, `AUFWACHEN`,
    `RETTUNG`)
  - **Freunde, nicht Verfolger:** Der Hubschrauber ist dunkelgrün mit
    Goldstreifen statt in Polizeifarben, auf seiner Seite glänzt groß ein
    goldener Diamant – das Zeichen der Crew –, und ein grünes Licht blinkt.
    Der Text nach der Landung beginnt mit "Das ist nicht die Polizei" und
    nennt, woran man es sieht. (Eine Person, die aus der offenen Tür winkte,
    ist nach der Abnahme wieder herausgeflogen; die Tür ist jetzt zu)
  - **Die Rotoren** drehen sich sichtbar: 16 feste Stellungen statt Blättern,
    die nur in der Länge schwanken – das hatte geflackert (siehe
    `dokumentation/Animationen.md`)
  - **Das Ende:** "Weiter" zeigt den Schlusstext aus dem Konzept, unten links
    klein, wo die Messdaten liegen (ein zu langer Pfad wird vorn gekürzt,
    Ordner und Datei bleiben stehen), und "Spiel beenden". Endete Level 3 am
    Timer, steht das bis dahin unten links
  - **Eine Uhr für alles:** Lider, Szenenwechsel und Flug hängen an der Zeit
    seit dem Warten-Knopf (rund 15 Sekunden bis zur Landung). Der Takt liest
    die echte Uhr ab: Ein langsamer Schulrechner überspringt Bilder, aber die
    Rettung dauert nicht länger. `Abschluss.zu_zeit` stellt jeden Moment her –
    so prüfen die Tests jeden Augenblick einzeln
  - Neu in `ui/animation.py`: `Buehne.wechseln` tauscht die Szene unter
    allem aus, was darüber liegt, und `Figur` ist eine durchsichtige
    Animation, die sich verschieben lässt und ihre Bilder im Takt dessen
    blättert, der sie bewegt

---

## Phase 7 – Level zusammensetzen

### Vorrang: Die Funksprüche kommen auf jeden Fall dran
Zwei bereits feststehende Regeln beissen sich hier: Regel 1 wechselt starr
zum nächsten Level, egal was offen ist. Regel 2 begrenzt eine einzelne
Aufgabe **nicht** über die Zeit, nur über Versuche ohne Fortschritt – wer
sich mit echtem Fortschritt langsam herantastet, bekommt beliebig viele
Eingaben. In Kombination kann ein langsames oder unsicheres Kind schon an
den zwei Basis-Übungen eines Levels so viel Zeit verlieren, dass die
Funksprüche – Level 1 und 3 haben je zwei (`erster_ruf`/`bob_erste_antwort`
bzw. `standort`/`bob_zweite_antwort`), Level 2 einen (`verfolger`) – nie
drankommen. Ab dem Punkt ergibt die Geschichte keinen Sinn mehr.

**Entscheidung:** Innerhalb eines Levels haben die noch ausstehenden
Funksprüche Vorrang vor weiteren Übungen. Sobald die verbleibende Levelzeit
nicht mehr für **alle** noch offenen Funksprüche dieses Levels reicht
(Summe von `zusatzaufgaben.erwartete_dauer(laenge)` über deren
`selbst_zu_loesen`-Länge, plus Sicherheitspuffer – Vorbild ist
`zusatzaufgaben.zeit_reicht_noch`, das denselben Puffer heute nur für *eine*
Zusatzaufgabe reserviert):

- Es wird keine weitere Zusatzaufgabe und keine zweite Basis-Übung mehr
  angeboten.
- Eine schon laufende Übung wird nicht abgebrochen, aber danach geht es
  direkt zum nächsten fälligen Funkspruch – auch wenn dafür eine
  Basis-Übung ausfällt.

Das verlängert kein Zeitfenster (Regel 1 bleibt unangetastet) und ändert am
Ablauf schneller Kinder nichts – es sortiert nur um, was in der
verbleibenden Zeit zuerst drankommt. Ist selbst dafür keine Zeit mehr (Level
endet, während die letzte Übung noch läuft), greift weiterhin Regel 1: Die
Übung wird abgebrochen, das Level endet. Ein Funkspruch kann also immer noch
ausfallen – deutlich seltener als heute, aber nicht ausgeschlossen. Sobald
ein Funkspruch einmal begonnen hat, sorgt Regel 2 dafür, dass er auch bei
sehr wenig Restzeit meist noch zu Ende kommt: Drei falsche Eingaben reichen
für die Lösungsanzeige, unabhängig davon, wie viele Sekunden das dauert.

**Umgesetzt** in `game/levelablauf.py`: `naechster_schritt` sagt, was auf die
eben abgeschlossene Aufgabe folgt – Übung, Zusatzaufgabe, Funkspruch oder
Levelende. Der Spielstand füttert die Funktion mit seinen Zahlen
(`Spielstand.naechster_schritt`, `uebungen_im_level`, `wurde_gestellt`), die
Oberfläche fragt in `ablauf.weiter_im_level` nur noch nach. Die Schätzung
steckt in `zusatzaufgaben.zeit_reicht_noch`, das jetzt auch die offenen
Funksprüche reserviert (`erwartete_dauer_funksprueche`,
`Funkspruch.buchstaben_von_hand`).

In Zahlen: Die Funksprüche kosten voraussichtlich 180 s (Level 1), 120 s
(Level 2) und 216 s (Level 3). Eine weitere Übung gibt es, solange das plus
Übung plus Puffer noch in die Restzeit passt – in Level 1 also, bis rund zehn
der fünfzehn Minuten verbraucht sind. 7.4 prüft den Fall am ganzen Durchlauf:
Wer bei den Übungen bewusst trödelt, muss trotzdem bei allen Funksprüchen
ankommen.

### 7.1 Level 1 (Caesar)
Handbuch → Übungen → Sendeaufgabe "Hallo, hört mich jemand? [Initialen]" →
Bobs erste verschlüsselte Antwort entschlüsseln
- **Umgesetzt** (`ui/ablauf.py`): Nach dem Handbuch und nach jeder Aufgabe
  fragt `weiter_im_level`, was drankommt, und zeigt den passenden Screen –
  Übung, Zusatzaufgabe, Funkgerät oder das nächste Level. Der Weg gilt für
  alle drei Level; 7.2 und 7.3 setzen nur noch die Erzähltexte dazwischen
- Die zwei Platzhalter-Knöpfe unter den Übungen sind weg ("Level beenden",
  "Zum Funkgerät"). Ein Level endet jetzt, wenn seine Aufgaben erledigt sind –
  oder am Timer
- **Zu bestätigen: Wann beginnt die Uhr von Level 1?** Seit 6.3 startet sie
  mit dem letzten Knopf des Story-Intros ("Handbuch aufschlagen"). Dafür
  spricht: Die Kontrollgruppe hat 15 Minuten reine Caesar-Zeit, und die
  Absturz-Szene ist Geschichte, kein Unterricht. Der Ablauf dafür steht in
  `ui/ablauf.py` (`level_1_beginnen`)

### 7.2 Level 2 (Substitution)
Handbuch → Übungen → abgefangener Feind-Funkspruch (nur entschlüsseln) mit dem
Hinweis auf die Häufigkeitsanalyse → Story-Übergang ohne Bob
- **Geändert:** Ursprünglich wurden die Übungen länger (Wort → Satz → längere
  Nachricht), und die letzte trug den Hinweis. Seit alle Level aus einem Pool
  ähnlich langer Sätze üben (2.2), gibt es keine längste Übung mehr. Der
  Hinweis gehört zum Feind-Funkspruch: Dort liegt ein sichtbar langer
  Geheimtext vor den Spielenden (`story.HINWEIS_HAEUFIGKEITSANALYSE`)
- **Umgesetzt:** Der Hinweis erscheint über dem Gerät, **sobald die Nachricht
  ganz hereingekommen ist** – er tritt dort an die Stelle der Einleitung. Zwei
  Gründe: Genau dann steht der lange Geheimtext vollständig auf dem Glas,
  worauf der Satz zielt; und eine Zeile mehr passt über dem Gerät nicht mehr
  ins Fenster (`ui/funk.py`, Parameter `hinweis`)
- **Der Übergang zu Level 3** bekommt eine eigene Erzählszene am Ende von
  Level 2 (`ui/erzaehlszene.py` vor dem Nachtlager): Er ist der Wendepunkt der
  Geschichte, und über dem Handbuch von Level 3 hätte er zusammen mit dem
  Einstieg nicht mehr ins Fenster gepasst. Er kommt nur, wenn der abgefangene
  Funkspruch wirklich dran war – er spricht von ihm. Läuft die Zeit von
  Level 2 ab, wird sofort gewechselt (Projektregel 1), und er entfällt

### 7.3 Level 3 (Vigenère)
Handbuch inkl. Quadrat → Übungen → Reflexionsfrage → Standort senden →
Bobs zweite Antwort entschlüsseln → Warten-Button → Abschluss
- **Umgesetzt:** Die Reflexionsfrage läuft als Erzählszene vor dem
  Standort-Funkspruch: erst die Frage allein ("Warum hilft eine
  Häufigkeitsanalyse hier nicht mehr direkt weiter?"), auf Klick die Antwort,
  dann das Funkgerät (`ablauf.ERZAEHLUNG_VOR_FUNKSPRUCH`). Danach folgen
  Standort und Bobs zweite Antwort, und mit dem Levelende der Abschluss aus
  6.8 – dort steht der Warten-Knopf

### 7.4 Kompletter Durchlauf am Stück
- Einmal von Start bis Ende ohne Abbruch durchspielen
- Prüfen: Bleibt man nirgends hängen? Passen die Übergänge?
- **Zusätzlich ein Trödel-Durchlauf:** in jedem Level bei den Basis-Übungen
  absichtlich viele Fehlversuche mit Fortschritt eingeben, bis die Zeit
  knapp wird – alle Funksprüche des Levels müssen trotzdem drankommen (siehe
  "Vorrang" oben)

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
- **Beim PyInstaller-Build auf den Log-Ordner achten:** `main.PROTOKOLLORDNER`
  hängt an `__file__`. In einer Einzeldatei-.exe zeigt das in ein temporäres
  Entpackverzeichnis, das beim Beenden gelöscht wird – mit den Messdaten.
  Im Build muss der Ordner neben der .exe liegen (`sys.executable`)
- **Die Animationen mit einpacken:** `content/animationen/` enthält PNG- und
  JSON-Dateien, keine Python-Module. PyInstaller nimmt sie nur mit, wenn sie
  als Daten angegeben sind (`--add-data`) – den ganzen Ordner, samt der
  Unterordner `1.5x/` für die grossen Bildschirme. `grafik/` gehört nicht in
  den Build – das ist Werkzeug für den Entwicklungsrechner
- **Auf dem Schulrechner nachsehen, ob der grosse Maßstab greift:** Das Spiel
  soll maximiert öffnen und den Bildschirm füllen. Steht Windows auf 125 %
  Skalierung, meldet es Tkinter nur 1536 × 864 und vergrössert das Fenster
  selbst – dann gilt der kleine Maßstab, alles passt, wirkt aber etwas weicher.
  Bei 100 % (auf 1080p-Monitoren üblich) greift der grosse

### 8.4 Logdateien einsammeln und Auswertung vorbereiten
- Wo landen die CSVs? Wie kommst du nach dem Experiment an alle heran?
- **Stand der Klärung** (noch offen, Rafael kümmert sich):
  - Schulsystem vermutlich ein "SNV-Client" o. ä. – genauer Name noch zu
    klären. Es gibt je Schülerkonto einen Abgabe-/Einsammelordner, vermutlich
    `H:\<Nachname.Vorname>\home\ausgeteilt` (Pfad noch prüfen)
  - **Problem:** Schülerinnen und Schüler können den Ordner nicht öffnen, nur
    per Drag and Drop etwas hineinlegen
  - Ein Webserver scheidet eher aus: Die Messdaten verliessen das Schulnetz
    (Datenschutz, siehe "Offene Punkte"), Schulnetze blockieren solche
    Verbindungen oft, und ein Server auf dem Lehrer-PC bräuchte Adminrechte
- **Geplant – sobald der Pfad feststeht:**
  - Das Spiel schreibt nach jeder Aufgabe **zusätzlich** eine Kopie der CSV in
    den Abgabeordner, genau wie in `logs/`. Kein Kind muss daran denken, keine
    Datei geht verloren. Vorher prüfen: Darf ein Programm dort schreiben,
    obwohl man den Ordner nicht öffnen kann? (Solche Abgabeordner sind oft
    "nur einwerfen": schreiben ja, ansehen nein – dann klappt es.)
  - Der Pfad kommt in eine kleine Einstellungsdatei neben dem Spiel, nicht in
    den Code – so lässt er sich an der Schule anpassen. Der Ordnername enthält
    den Schülernamen; er darf deshalb nirgends ins Log oder ins Repository
  - Die lokale Kopie in `logs/` bleibt immer: Ist der Abgabeordner nicht
    erreichbar, geht nichts verloren, und die Meldungszeile sagt es
  - Notlösung, falls das Schreiben dort nicht erlaubt ist: Der
    Abschlussbildschirm zeigt die Datei und einen Knopf "Ordner öffnen", aus
    dem man sie per Drag and Drop in den Abgabeordner zieht
  - Dazu ein kleines Skript, das alle eingesammelten CSVs zu einer Tabelle
    zusammenführt
  - Vor dem Experiment mit 2–3 Rechnern ausprobieren (passt zu 8.2)

---

## Offene Punkte außerhalb des Codes

- [ ] Level-2-Zuordnungstrick (Tastatur) gegen den echten Testbogen (Anhang A2)
      gegenchecken – kollidiert er mit einer Testantwort?
- [ ] **Übungssätze der Kontrollgruppe:** Das Spiel übt in allen drei Leveln
      mit denselben zehn Sätzen (10–14 Buchstaben, `Handbuchtexte.md`). Die
      Papieraufgaben der Frontalunterrichts-Gruppe sollten aus derselben Liste
      kommen – sonst unterscheiden sich die Gruppen auch in der Textlänge.
- [ ] **Übungsumfang gegen Anhang A4 abgleichen:** Die Spielgruppe rechnet pro
      echtem Funkspruch nur den Anfang von Hand (15–25 Buchstaben). Wenn die
      Frontalunterrichts-Gruppe auf Papier deutlich längere Texte bearbeitet,
      unterscheiden sich die Gruppen nicht mehr nur in der Methode, sondern
      auch im Übungsumfang. Entweder die Papieraufgaben entsprechend
      zuschneiden oder die Abweichung in der Arbeit begründen.
- [ ] Einverständnis/Datenschutz für die Datenerhebung klären
- [x] **Wie findet die Pseudonym-ID zur Person?** Entschieden: Die
      Lehrkraft verteilt IDs der Form `X-XX` (Klasse, Strich, Nummer) auf
      Papier, die Spielenden tragen sie auf dem Startbildschirm ein. Das Spiel
      nimmt nichts anderes an – umgesetzt in 6.2. Die Liste, wer welche ID hat,
      bleibt bei der Lehrkraft und gehört nicht ins Repository
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
