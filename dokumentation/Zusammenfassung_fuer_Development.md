# Übergabedokument: Verschlüsselungs-Lernspiel "Der Antwerpen-Raub"

*Zusammenfassung aller Konzept-Entscheidungen für den Einstieg in die
Entwicklung. Grundlage: Projektplan_KOL_Informatik (Anhänge A1–A5).*

---

## 1. Ausgangslage & Ziel des Projekts

Das Spiel ist Teil eines Methodenvergleichs: Eine Gruppe lernt Verschlüsselung
per Frontalunterricht, eine andere per Lernspiel. Beide Gruppen durchlaufen
**exakt dieselben Lernziele** (Anhang A1) und denselben **Vor-/Nachtest**
(Anhang A2), in **derselben Gesamtzeit**.

**Wichtige Konsequenz für die Entwicklung:** 60 % der Bewertung entfallen auf
den *Prozess*, nicht nur auf das fertige Produkt. Design-Entscheidungen sollten
dokumentiert und begründbar sein. Das Spiel darf bewusst schlank bleiben –
Priorität liegt auf sauberer Vergleichbarkeit mit dem Frontalunterricht, nicht
auf aufwendiger Grafik.

---

## 2. Zeitrahmen (fix, identisch zur Kontrollgruppe – Anhang A4)

| Abschnitt              | Dauer  |
|------------------------|--------|
| Vortest                | 10 Min |
| Level 1 – Caesar       | 15 Min |
| Level 2 – Substitution | 20 Min |
| Level 3 – Vigenère     | 25 Min |
| Nachtest               | 10 Min |
| Puffer                 | 5 Min  |

**Kritisch:** Die drei Level-Zeitfenster (15/20/25 Min) dürfen durch
Zusatzaufgaben (siehe Punkt 6) **nicht verlängert** werden – sonst ist der
Vergleich mit der Frontalunterrichts-Gruppe nicht mehr sauber. Wenn das
Zeitfenster endet, wird zum nächsten Level weitergeschaltet, unabhängig davon,
wie viele Zusatzaufgaben gerade offen sind.

---

## 3. Lerninhalte pro Level (müssen exakt zu Anhang A1/A2 passen)

| Level | Methode                                               | Kernlernziele                                                                                                                                                      |
|-------|-------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1     | Caesar-Verschlüsselung                                | Prinzip fester Verschiebe-Schlüssel; Ver-/Entschlüsseln inkl. Sprung Z→A                                                                                           |
| 2     | **Monoalphabetische Substitution** (nicht Transposition!) | Unterschied zu Caesar; Ver-/Entschlüsseln mit freier Zuordnungstabelle; Begründen, warum Durchprobieren nicht mehr praktikabel ist; Hinweis auf Häufigkeitsanalyse |
| 3     | Vigenère-Verschlüsselung                              | Schlüsselwort-Prinzip; Ver-/Entschlüsseln mit kurzem Schlüsselwort; erklären, warum Häufigkeitsanalyse hier nicht direkt greift                                    |

**Offener Prüfpunkt:** Der Handbuch-Erklärtrick für Level 2 (Tastatur-Zeilen
als Zuordnungsmuster) wurde bewusst **anders** gewählt als eine mögliche
Zuordnung im echten Testbogen (Anhang A2), damit das Handbuch nicht versehentlich
die Testantwort vorwegnimmt. Bitte einmal gegenchecken, ob das mit dem
tatsächlichen Testbogen kollidiert oder nicht.

---

## 4. Rahmengeschichte – nur Verweis

Die vollständige Story ("**Der große Diamantenraub")**

- 5 wählbare Charaktere: Vic Moreno, Elena Duarte, Jonas Berg, Amara Nwosu, Théo Lambert
- Ausgangssituation: Flugzeugabsturz nach Diamantenraub in Antwerpen, Diamanten müssen am Wrack zurückgelassen werden (Fluchtgewicht), kein reiches Ende
- Kommunikationsmittel: **Kurzwellen-Funkgerät** (nicht "Transmitter") – erklärt plausibel, warum Nachrichten Singapur erreichen können, aber auch, warum sie abhörbar sind
- Bob (Kontakt in der Zentrale) meldet sich **nur zweimal** im ganzen Spiel (Ende Level 1, Ende Level 3), **ausschließlich verschlüsselt**
- Strikte Regel: Jede gesendete Nachricht wird verschlüsselt, jede empfangene muss entschlüsselt werden – kein Klartext-Funkverkehr, auch nicht durch Bob
- Level-2-Spannungsmoment: abgefangener Funkspruch der Verfolger, der mit Bobs erbeuteter Tabelle entschlüsselt werden kann
- Übergang Level 2 → 3 verläuft **ohne** zusätzlichen Bob-Dialog/Funkspruch

---

## 5. Handbuchtexte – nur Verweis

Die vollständigen, kindgerecht formulierten Handbuchtexte für alle drei Level
(inkl. Merksätze, durchgerechneten Beispielen und je 10 Übungswörtern/-sätzen
pro Level zur Zufallsauswahl) sind ebenfalls bereits separat gespeichert.
Wichtige technische Punkte daraus, die beim Bau zu beachten sind:

- **Level 1 (Caesar):** 10 Übungswörter, Schlüssel wird vorgegeben.
- **Level 2 (Substitution):** 10 Übungssätze, Zuordnungstabelle nach Tastatur-Trick (Q-W-E-R-T-Z-U-I-O-P / A-S-D-F-G-H-J-K-L / Y-X-C-V-B-N-M).
- **Level 3 (Vigenère):** Erklärung erfolgt über das **Vigenère-Quadrat** (Nachschlagetabelle), nicht über Zahlenrechnung. 10 Übungssätze. Schlüsselwort **muss zufällig aus mehreren Optionen** gewählt werden (z. B. ROT, WEG, TAG) – nicht immer dasselbe Wort, sonst wird die Aufgabe vorhersehbar.
- **Für jede Übungsaufgabe in allen drei Leveln** muss einmal ver- und entschlüsselt werden
- **Vollständiges Vigenère-Quadrat (26×26):** kann automatisch generiert werden, keine manuelle Eingabe nötig. Formel: In Zeile $k$ (Schlüsselbuchstabe) und Spalte $m$ (Nachrichtenbuchstabe) steht der Buchstabe mit Index $(k+m) \\bmod 26$, wobei $A=0$.

---

## 6. Zusatzaufgaben-System (adaptiver Timer)

Statt fester Bonusaufgaben: ein Timer pro Level/Aufgabe erkennt, wenn
Spieler:innen ungewöhnlich schnell fertig sind, und schlägt dann zusätzliche
Ver-/Entschlüsselungsaufgaben aus dem Handbuch-Wortpool vor.

**Wichtige Regeln dafür:**

- Zeit **pro Level bzw. pro Aufgabe** messen, **nicht** die gesamte Spielöffnungsdauer (sonst verfälscht durch Pausen/Ablenkung).
- Zusatzaufgaben dürfen die festen Zeitfenster (15/20/25 Min) **nicht verlängern** – sobald das Zeitfenster endet, wird trotzdem zum nächsten Level gewechselt.
- Der Schwellenwert ("ab wann gilt jemand als zu schnell?") sollte **vor dem eigentlichen Experiment mit einem kleinen Pilotdurchlauf kalibriert** werden, statt geschätzt zu werden.

---

## 7. Fehlerhandling & Lösungsanzeige

Gilt einheitlich für **alle** Aufgaben – Handbuch-Übungen **und** echte
Funksprüche im Spiel (inkl. Bobs zwei Nachrichten, die story-kritisch sind):

- Eine falsch ver-/entschlüsselte Nachricht kann **nicht abgeschickt/bestätigt** werden. Rückmeldung: konkreter Hinweis, was falsch ist (nicht nur "falsch"), z. B. an welcher Stelle die Verschiebung/Zuordnung nicht stimmt.
- Nach **3 erfolglosen Versuchen** wird die Lösung angezeigt.
- Optionale Zusatzfunktion: "Fast richtig"-Erkennung, die markiert, welche Buchstaben/Stellen konkret falsch sind (Zusatzaufwand, aber sinnvoll).
- **Besonders wichtig:** Auch Bobs beiden Funksprüche (Ende Level 1, Ende Level 3) müssen dieselbe 3-Versuche-Regel nutzen, sonst kann das Spiel an genau diesen zwei story-tragenden Stellen komplett blockieren.

---

## 8. Logging / Datenerfassung (für die spätere Prozessauswertung)

Da 60 % der Bewertung auf dem Prozess liegt, sollten mindestens folgende Daten
pro Aufgabe/Spieler:in protokolliert werden:

- Anzahl Versuche pro Aufgabe
- Ob die Lösung angezeigt wurde (ja/nein)
- Benötigte Zeit pro Aufgabe/Level
- Ob und wie oft Zusatzaufgaben genutzt wurden

---

## 9. Technik-Empfehlung

| Option                | Bewertung                                                                                                                                                                                      |
|-----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| *Browser (HTML/CSS/JS)* | *Läuft per Link ohne Login, leicht an mehrere Klassen/Schulrechner verteilbar, keine Serverabhängigkeit nötig (rein clientseitig, z. B. eine einzelne HTML-Datei mit eingebettetem JavaScript).* |
| **Python (z. B. Pygame)** | **Machbar, aber Verteilung an viele Schulrechner umständlicher.**                                                                                                                                  |
| *Scratch*               | *Schnell teilbar, aber Texteingabe/Verschlüsselung über drei Ebenen eher unhandlich.*                                                                                                            |

---

## 10. Grober Bildschirm-/Screen-Ablauf (Vorschlag, ggf. anzupassen)

1. Startbildschirm mit Titel + Charakterauswahl
2. Story-Intro (Absturz-Szene, kein Funkkontakt)
3. Level 1: Handbuch-Erklärung → Übungsaufgaben (+ ggf. Zusatzaufgaben) → echte Sendeaufgabe → Bobs erste (verschlüsselte) Antwort
4. Level 2: Handbuch-Erklärung → Übungsaufgaben → abgefangener Feind-Funkspruch (nur Entschlüsseln) → Story-Übergang ohne Bob-Dialog
5. Level 3: Handbuch-Erklärung (inkl. Vigenère-Quadrat) → Übungsaufgaben → echte Standort-Sendeaufgabe → Bobs zweite (verschlüsselte) Antwort
6. Abschluss-Screen: Rettung, Diamanten bleiben zurück

---

## 11. Offene Punkte / To-dos für den Projektstart

- [x] Titel final festlegen (4 Alternativen stehen zur Auswahl, siehe Punkt 4) ---> entschieden: Der Diamanten Raub
- [ ] Level-2-Zuordnungstrick gegen den echten Testbogen (Anhang A2) prüfen
- [ ] Pilotdurchlauf einplanen, um den Zusatzaufgaben-Schwellenwert zu kalibrieren
- [ ] Entwicklungsaufwand für Timer-Logik, Versuchszähler und Logging realistisch in die Zeitplanung einkalkulieren (im ursprünglichen Projektplan nicht explizit vorgesehen)
- [ ] Vollständiges 26×26-Vigenère-Quadrat automatisch generieren (Formel siehe Punkt 5), nicht manuell eintippen