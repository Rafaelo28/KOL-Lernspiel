# Projektregeln: "Der Diamantenraub" (Verschlüsselungs-Lernspiel)

## Vor der Arbeit lesen

Alle Konzeptdokumente liegen im Ordner `dokumentation/`. Immer zuerst
durchlesen:

- `dokumentation/Zusammenfassung_fuer_Development.md` – Konzeptentscheidungen, Zeitrahmen, Lernziele
- `dokumentation/Konzept_Spiel.md` – Rahmengeschichte und Level-Ablauf
- `dokumentation/Handbuchtexte.md` – die fertigen Handbuchtexte, Übungswörter und -sätze
- `dokumentation/Arbeitsplan_Der_Diamantenraub.md` – Aufgabenzerlegung, Phasen 0–8
- `dokumentation/Tipps-und-Tricks.md` – Hinweise zu Tkinter, Normalisierung, Logging

## Sprache

Das Projekt ist durchgehend deutsch: Funktions- und Variablennamen, Kommentare,
Docstrings, Commit-Messages und alle Texte im Spiel.

---

## Unverhandelbare Regeln

Diese Punkte stammen aus dem Versuchsaufbau (Methodenvergleich Lernspiel vs.
Frontalunterricht). Sie sind keine Geschmacksfrage – wer sie bricht, macht die
Messdaten unbrauchbar oder blockiert das Spiel.

### 1. Die Zeitfenster sind fix

15 Min (Level 1) / 20 Min (Level 2) / 25 Min (Level 3). Die Kontrollgruppe hat
exakt dieselben Zeiten. Zusatzaufgaben verlängern ein Zeitfenster **nie**.
Läuft die Zeit ab, wird sofort zum nächsten Level gewechselt – egal, wie viele
Aufgaben noch offen sind.

### 2. 3-Versuche-Regel gilt für **alle** Aufgaben

Nach drei erfolglosen Versuchen **ohne Fortschritt** wird die Lösung
angezeigt. Das gilt für Handbuch-Übungen **und** für die echten Funksprüche,
insbesondere für Bobs zwei Nachrichten (Ende Level 1, Ende Level 3). Ohne
diese Regel blockiert das Spiel genau an den zwei story-tragenden Stellen.

**Was "ohne Fortschritt" heisst:** Eine Eingabe, die weniger falsche
Buchstaben hat als die beste bisher, kostet keinen Versuch – die Strähne
beginnt von vorn. Wer bei einem 25-Buchstaben-Funkspruch vier Stellen
verzählt hat und sie einzeln ausbessert, braucht vier Eingaben; mit einem
harten Limit von drei bekäme ausgerechnet diese Person die Lösung vorgesetzt,
obwohl sie die Methode verstanden hat. In den Messdaten sähe das aus wie
"nicht gekonnt".

Verglichen wird gegen das bisher beste Ergebnis, nicht gegen den letzten
Versuch – sonst liesse sich die Strähne durch abwechselndes Verschlechtern und
Verbessern beliebig zurücksetzen. Endlos läuft das nicht: Jeder Fortschritt
senkt die Fehlerzahl um mindestens eins, und mehr Fehler als Buchstaben kann
eine Antwort nicht haben.

Der Schwellenwert steht als `HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT` an genau
einer Stelle in `game/bearbeitung.py`.

**Fürs Log (5.5) gehören beide Zahlen hinein:** alle falschen Eingaben *und*
davon die ohne Fortschritt. "Acht Eingaben, keine ohne Fortschritt" ist etwas
ganz anderes als "drei Eingaben, alle ohne Fortschritt".

### 3. Kein Klartext-Funkverkehr

Jede gesendete Nachricht wird verschlüsselt, jede empfangene muss entschlüsselt
werden. Auch Bob funkt niemals im Klartext.

### 4. Level 2 ist monoalphabetische Substitution

**Nicht** Transposition. (Die alte Konzeptversion V1 in
`dokumentation/Konzept_Spiel.md`
spricht noch von Transposition – das ist überholt.) Die Zuordnungstabelle
entsteht aus dem Tastatur-Trick: `QWERTZUIOP` / `ASDFGHJKL` / `YXCVBNM`.

### 5. Verschlüsselungslogik enthält niemals GUI-Code

`crypto/` ist rein: Text rein, Text raus. Keine Tkinter-Importe, keine
Importe aus `ui/` oder `game/`. Nur so bleibt alles mit pytest testbar – und
die Testdatei ist ein starker Beleg für die Prozessnote.

### 6. Fehlermeldungen sind konkret

Nie nur "falsch", sondern ein Hinweis, wo es kippt (z. B. "Stelle 3 stimmt
nicht – prüf nochmal die Verschiebung"). Eine falsch ver-/entschlüsselte
Nachricht lässt sich nicht abschicken.

### 7. Datenschutz beim Logging

In den CSV-Logs steht **kein Klarname**, nur eine Pseudonym-ID. Der Ordner
`logs/` ist in `.gitignore` und darf nie eingecheckt werden.

---

## Lange Funksprüche: Teilaufgabe statt Kürzen

Die echten Funksprüche sind lang (Bobs erste Antwort 78 Buchstaben, der
abgefangene Feind-Funkspruch 76). Sie werden **nicht gekürzt**. Stattdessen
rechnen die Spielenden nur den Anfang von Hand; ein Knopf löst den Rest auf,
begleitet von einem kurzen Erzähltext ("zwanzig Minuten später …").

Die Aufteilung steht als `selbst_zu_loesen` in `content/story.py`.

**Warum nicht kürzen:**

1. Handbuchseite 2 sagt "Je länger der Text, desto leichter wird er über
   Häufigkeitsanalyse knackbar". Der abgefangene Funkspruch ist die Stelle,
   an der ein *sichtbar langer* Geheimtext vor den Spielenden liegen soll –
   ein gekürzter Text widerspricht dem eigenen Handbuch.
2. Die Messdaten werden sauberer: Bei 78 Buchstaben würden langsamere Kinder
   vom Level-Timer mitten in der Aufgabe abgeschnitten, und für die gäbe es
   keine verwertbare Bearbeitungszeit. Eine feste Teilaufgabe misst für alle
   dieselbe Arbeitsmenge.
3. Der Knopf ist keine Abkürzung, sondern die Belohnung dafür, dass man das
   Verfahren beherrscht.

**Was daran hängt – bitte in den jeweiligen Phasen beachten:**

- **Phase 4:** Geprüft wird `selbst_zu_loesen`, nicht der ganze Klartext. Die
  3-Versuche-Regel gilt für diesen Teil. Der Knopf muss **auch dann**
  erscheinen, wenn die Lösung nach drei Versuchen ohne Fortschritt
  angezeigt wurde – sonst
  blockiert das Spiel genau an den story-tragenden Stellen (siehe Regel 2).
- **Phase 5:** Die Länge des geprüften Teils gehört ins Log, sonst sind die
  Bearbeitungszeiten später nicht vergleichbar.
- **Phase 6 – und hier hängt es an der Richtung:**
  - **Empfangen:** Der **vollständige Geheimtext** bleibt sichtbar, nur der zu
    entschlüsselnde Anfang ist hervorgehoben. Sonst geht Grund 1 verloren.
  - **Senden:** Sichtbar bleibt der vollständige **Klartext**, hervorgehoben
    ist der zu verschlüsselnde Anfang. Der Geheimtext darf dort **nie**
    angezeigt werden – er ist genau das, was eingetippt werden soll. Wer die
    Empfangen-Regel versehentlich auch beim Senden anwendet, macht die Aufgabe
    durch Abschreiben lösbar und die gemessene Zeit für Level 3 wertlos.
- Der Schwellenwert `HOECHSTLAENGE_TEILAUFGABE` in `content/story.py` steht an
  genau einer Stelle und wird nach dem Pilotdurchlauf angepasst – genau wie
  der Schwellenwert für die Zusatzaufgaben.
- Die Erzählzeit ("zwanzig Minuten später") ist reine Fiktion. Der echte
  Level-Timer läuft unverändert weiter; Zeitfenster bleiben fix (Regel 1).

---

## Technische Vorgaben

- **Python 3.12 + Tkinter** (nicht Pygame). Tkinter gehört zur
  Standardbibliothek – keine pip-Abhängigkeiten für das Spiel selbst, das ist
  auf Schulrechnern ohne Adminrechte entscheidend. Einzige Dev-Abhängigkeit:
  `pytest`.
- **Zeitmessung pro Level und pro Aufgabe**, nicht über die gesamte
  Fensteröffnungsdauer (sonst verfälschen Pausen die Daten).
- **Schwellenwert für Zusatzaufgaben** ist genau *eine* Konstante an *einer*
  Stelle – er wird nach dem Pilotdurchlauf angepasst.
- **Zufalls-Seed** einmal pro Durchlauf setzen und ins Log schreiben, damit
  rekonstruierbar bleibt, wer welche Aufgaben bekommen hat.
- **Vigenère-Quadrat** wird generiert, nicht abgetippt: Zeile *k*, Spalte *m*
  → Buchstabe mit Index `(k + m) mod 26`, A = 0.
- **Vigenère-Schlüsselwort** variiert zufällig (ROT, WEG, TAG, …) – nicht
  immer dasselbe, sonst wird die Aufgabe vorhersehbar.

### Textkonvention (Aufgabe 0.3 – festgelegt)

Gilt für Klartext, Geheimtext, Nutzereingabe und Lösung gleichermaßen.
Ausführliche Begründungen stehen im Kopf von `crypto/normalize.py`.

1. **Großbuchstaben intern.** Kleinschreibung in der Eingabe ist erlaubt und
   nie ein Fehler.
2. **Nur A–Z werden verschlüsselt.** Arbeitsalphabet sind 26 Zeichen ohne
   Umlaute; das Leerzeichen ist das einzige weitere zugelassene Zeichen und
   bleibt unverändert stehen.
3. **Leerzeichen bleiben im Geheimtext erhalten** – Wortgrenzen bleiben also
   sichtbar. Kryptografisch ein Nachteil, für die Nachvollziehbarkeit von Hand
   in der Schulklasse aber notwendig. Jede Art von Weißraum zählt als
   Wortgrenze, auch das geschützte Leerzeichen U+00A0 aus PDF-Kopien.
4. **Beim Vergleich werden Leerzeichen ignoriert.** Ein vergessenes oder
   doppeltes Leerzeichen darf keinen der drei Versuche verbrauchen.
5. **Umlaute werden ersetzt, nicht abgewiesen:** Ä→AE, Ö→OE, Ü→UE, ß→SS.
   (Bobs erster Funkspruch enthält "hört" – eine Fehlermeldung würde nur Zeit
   im festen Zeitfenster kosten.) Die Schreibweise in Unicode spielt keine
   Rolle – zusammengesetzte und zerlegte Umlaute werden gleich behandelt.
   Andere Akzentbuchstaben behalten ihren Grundbuchstaben: É→E, Ç→C. Sonst
   würde aus dem Charakter "Théo Lambert" im Spiel "THO LAMBERT". Nicht
   zerlegbare Zeichen (Ø, Ł, Æ) fallen dagegen unter Regel 6 und verschwinden;
   in den Spieltexten kommt keines davon vor.
6. **Alle übrigen Zeichen werden entfernt** (Satzzeichen, Ziffern). Die UI
   zeigt deshalb **immer den bereits normalisierten Text** an, sonst steht im
   Aufgabentext ein Komma, das in der Lösung fehlt.
7. **Vigenère: Leerzeichen zählen den Schlüsselindex nicht weiter.**

---

## Projektstruktur

```
crypto/        – reine Verschlüsselungslogik, kein GUI
game/          – Spiellogik, Zustand, Timer, Logging
ui/            – Tkinter-Oberfläche (baut als einzige Schicht Bedienelemente)
content/       – Handbuchtexte, Wortlisten, Story-Texte, Charaktere (als Python-Daten)
tests/         – pytest
logs/          – Messdaten der Durchläufe (Inhalt in .gitignore!)
dokumentation/ – Konzept, Arbeitsplan, Handbuchtexte, Tipps (keine Programmdateien)
main.py        – Einstiegspunkt
```

Erlaubte Abhängigkeitsrichtung: `ui` → `game` → `crypto` / `content`.
Niemals umgekehrt.

Tkinter darf nur in `ui/` und in `main.py` vorkommen. `main.py` öffnet das
Hauptfenster und fängt die zwei Startfehler ab (Tkinter fehlt, keine
Bildschirmanzeige); alles Weitere gehört nach `ui/`. In `crypto/`, `game/`
und `content/` sind Tkinter-Importe verboten, ebenso `print()` und `input()` –
`tests/test_zusammenspiel.py` prüft beides für alle drei Pakete über den
Syntaxbaum.

---

## Arbeitsweise

- **Eine Aufgabe aus dem Arbeitsplan pro Sitzung.** Danach selbst durchklicken
  und committen. Die Git-Historie ist Prozessnachweis (60 % der Bewertung).
- Referenzwerte, die immer stimmen müssen (aus den Handbuchtexten):
  - Caesar: `HUND` + Schlüssel 3 → `KXQG`
  - Substitution: `HUND` → `IXFR`
  - Vigenère: `HUND` mit `ROT` → `YIGU`
- Nach jeder Änderung an `crypto/`: `pytest` laufen lassen.
