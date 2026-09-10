# Commit-Regeln

Die Git-Historie ist Prozessnachweis – sie zählt 60 % der Bewertung (siehe
`CLAUDE.md`). Wer sie später liest, soll sehen, **in welchen Schritten** das
Spiel entstanden ist, nicht nur, dass es irgendwann fertig war. Ein einzelner
Commit mit 3600 Zeilen erzählt davon nichts.

Die Regeln gelten für jeden Commit – egal ob von Hand oder von Claude.

---

## Wer macht was

- **Claude committet selbst**, sobald ein Schritt abgeschlossen ist, ohne
  vorher nachzufragen – nach denselben Regeln wie unten.
- **Claude pusht nie.** `git push` bleibt Handarbeit.
- Gearbeitet wird direkt auf `main`, ohne Branches.

## Wann committet wird

Nach **jedem abgeschlossenen Schritt**. Ein Schritt ist:

- **eine Aufgabe aus dem Arbeitsplan** (6.1, 6.2, …) – nicht erst die ganze
  Phase,
- **eine Fehleranalyse** samt ihrer Korrekturen – als eigener Commit, nicht mit
  der Aufgabe davor vermischt,
- **eine andere abgeschlossene Änderung**, um die gebeten wurde
  (Textkorrektur, Umbenennung, Doku).

Beispiel: Der Auftrag "erledige 6.2 und 6.3 und prüfe dann auf Fehler" ergibt
drei Commits – `6.2 …`, `6.3 …` und `Fehleranalyse 6.2–6.3`.

**Nicht** committet wird:

- wenn ein Test rot ist – dann erst reparieren oder den Fehler melden,
- mitten in einem Schritt, der noch nicht funktioniert.

Fällt nach einem Commit beim Durchklicken ein Fehler auf, wird er mit einem
**neuen** Commit behoben. Auch das ist Prozess und darf in der Historie
stehen.

## Vor jedem Commit

1. **`pytest`** – alles grün.
2. **`git status`** – stehen dort nur Dateien, die zu diesem Schritt gehören?
   Nie ins Repository gehören:
   - der Inhalt von `logs/` (Messdaten, Projektregel 7),
   - `resume.txt` und Gesprächsmitschnitte aus `/export` (der Dateiname
     beginnt mit dem Datum),
   - `.idea/`, `.venv/`, `__pycache__/`.

   Die `.gitignore` fängt all das ab. Steht trotzdem etwas Unerwartetes da:
   erst klären, dann committen.
3. **Hinzufügen:** `git add .` ist in Ordnung, wenn `git status` sauber
   aussah. Claude fügt die Dateien einzeln beim Namen hinzu.

## Die Commit-Nachricht

Deutsch, wie alles im Projekt.

- **Erste Zeile:** die Nummer aus dem Arbeitsplan und worum es geht,
  höchstens etwa 70 Zeichen. Zum Beispiel:
  - `6.1 Fenstergerüst und Screen-Wechsel`
  - `Fehleranalyse 6.1–6.3`
  - `Handbuchseite 3: Merksatz korrigiert`
- **Darunter, nach einer Leerzeile:** was gemacht wurde und **warum** – vor
  allem Entscheidungen, die man dem Code nicht ansieht. Bei einer
  Fehleranalyse: die gefundenen Fehler als Liste.
- **Zum Schluss:** der Stand der Tests, etwa `Tests: 4115 grün`.

Von Hand geht das mit mehreren `-m` – jedes wird ein eigener Absatz:

```
git commit -m "6.1 Fenstergerüst und Screen-Wechsel" \
           -m "Hauptfenster tauscht die Screens aus; ein Takt über after() ruft pruefe_zeitfenster() auf." \
           -m "Tests: 4115 grün"
```

Ohne `-m` öffnet `git commit` einen Editor. Im Commit-Fenster von PyCharm
lassen sich ebenfalls mehrere Zeilen schreiben.

Commits von Claude enden mit den Zeilen `Co-Authored-By:` und
`Claude-Session:`. So bleibt sichtbar, welche Commits mit Claude entstanden
sind; auf GitHub erscheint Claude dort als Mitautor.

## Was nicht gemacht wird

- **Einen schon gepushten Commit ändern** – kein `git commit --amend`, kein
  `git rebase`, kein `git push --force`. Das schreibt die Historie auf GitHub
  um. Ein Fehler wird mit einem neuen Commit behoben.
- Einen Commit, der **noch nicht gepusht** ist, kann man dagegen jederzeit
  zurücknehmen: `git reset --soft HEAD~1`. Die Änderungen bleiben dabei
  erhalten und lassen sich neu committen.
