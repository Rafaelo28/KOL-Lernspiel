# Das Spiel auf Schulrechner bringen (Arbeitsplan 8.3)

Auf Schulrechnern ist oft kein Python installiert, und ohne Adminrechte lässt
sich keines nachinstallieren. Deshalb wird das Spiel zu **einer ausführbaren
Datei** gebaut, die Python und Tkinter mitbringt: kopieren, doppelklicken,
fertig.

> **PyInstaller baut nur für das System, auf dem es läuft.** Eine
> `Diamantenraub.exe` entsteht **nur unter Windows**. Unter Linux kommt eine
> Linux-Datei heraus, die auf dem Schulrechner nicht startet. Auf einem
> Rechner mit beiden Systemen heisst das: für den Build nach Windows booten.

---

## 1. Vorher: Läuft dort überhaupt schon Python?

Die ehrlichste Prüfung kostet eine Minute. Auf dem Schulrechner in die
Eingabeaufforderung:

```
python --version
python -c "import tkinter; print('Tkinter ist da')"
```

Kommt eine Version ab 3.12 und die Tkinter-Zeile, reicht es, den Projektordner
zu kopieren und `python main.py` zu starten – dann braucht es gar keinen Build.
Kommt eine Fehlermeldung, geht es unten weiter.

---

## 2. Das Projekt nach Windows holen

Die Linux-Partition ist von Windows aus normalerweise nicht lesbar. Zwei Wege:

* **Über GitHub** (am saubersten, weil die Historie mitkommt):

  ```
  git clone https://github.com/Rafaelo28/KOL-Lernspiel.git
  ```

  Vorher unter Linux `git push`, sonst fehlen die letzten Commits.

* **Über einen USB-Stick oder eine NTFS-Partition:** den ganzen Projektordner
  kopieren. `logs/`, `.venv/`, `build/` und `dist/` können dabei weg.

---

## 3. Python unter Windows einrichten

1. Installer von [python.org](https://www.python.org/downloads/windows/) laden
   (3.12 oder neuer).
2. Im ersten Dialog **"Add python.exe to PATH"** ankreuzen – sonst findet die
   Eingabeaufforderung `python` nicht.
3. Tcl/Tk ist im Standardumfang dabei und muss nicht extra gewählt werden.

Danach im Projektordner:

```
pip install pyinstaller
```

---

## 4. Bauen

```
python bauen.py
```

Das Ergebnis liegt in `dist\Diamantenraub.exe` (rund 40 MB).

Zwei Schalter:

| Aufruf | Wirkung |
|---|---|
| `python bauen.py` | eine Einzeldatei – am einfachsten weiterzugeben |
| `python bauen.py --ordner` | ein Ordner statt einer Datei – **startet deutlich schneller**, weil nichts entpackt werden muss |
| `python bauen.py --mit-konsole` | zusätzlich ein Konsolenfenster, in dem Fehlermeldungen stehen |

Wenn die Einzeldatei auf dem Schulrechner zu lange zum Starten braucht (sie
entpackt bei jedem Start 27 MB Animationen in ein temporäres Verzeichnis), ist
`--ordner` die Antwort: dann wird der ganze Ordner `dist\Diamantenraub\`
kopiert.

---

## 5. Was auf dem Windows-Rechner zu prüfen ist

Der Reihe nach durchgehen – jede Zeile hat schon einmal jemandem das
Experiment zerschossen:

- [ ] **Startet das Spiel?** Doppelklick auf die Datei, Startbildschirm da.
- [ ] **Meldet sich SmartScreen oder der Virenschutz?** Eine selbst gebaute,
      nicht signierte .exe wird von Windows gern mit "Der Computer wurde durch
      Windows geschützt" angehalten (Weg: *Weitere Informationen → Trotzdem
      ausführen*). Auf einem verwalteten Schulrechner kann das **komplett
      blockiert** sein – genau deshalb gehört dieser Test früh gemacht und auf
      einem echten Schulrechner, nicht nur zu Hause.
- [ ] **Die Schriften.** Das Spiel wünscht sich Consolas (Funkanzeige),
      Palatino Linotype (Handbuch) und Ink Free oder Segoe Print (Bobs
      Randnotizen). Alle drei gibt es unter Windows, unter Linux nicht – das
      Handbuch sollte dort also **besser** aussehen. Prüfen: Sind die
      Randnotizen wirklich handschriftlich?
- [ ] **Der Maßstab.** Auf einem 1080p-Monitor mit 100 % Skalierung soll das
      Spiel maximiert öffnen und alles 1,5-mal so gross zeichnen. Steht
      Windows auf 125 %, meldet es Tkinter nur 1536 × 864 – dann greift der
      kleine Maßstab, alles passt, wirkt aber etwas weicher. Beides ist in
      Ordnung, aber man sollte wissen, was man sieht.
- [ ] **Die Messdaten.** Einen kurzen Durchlauf spielen (ID `0-99` eingeben)
      und nachsehen, ob **neben** der .exe ein Ordner `logs` mit einer
      CSV-Datei entstanden ist. Liegt die .exe in einem schreibgeschützten
      Ordner (`C:\Programme`), entsteht dort nichts – auf Desktop oder Stick
      legen.
- [ ] **Startzeit stoppen.** Mehr als ein paar Sekunden sind im Unterricht
      lästig, wenn dreissig Rechner gleichzeitig starten. Dann `--ordner`.
- [ ] **Die Animationen laufen?** Wrack, Funkgerät, Nachtlager. Fehlen sie,
      wurde `content/animationen` nicht mit eingepackt.

---

## 6. Was danach noch offen ist

Wie die CSV-Dateien nach dem Experiment eingesammelt werden, steht in
Arbeitsplan 8.4 und hängt am Abgabeordner des Schulsystems. Sobald der Pfad
feststeht, schreibt das Spiel die Kopie automatisch dorthin – der Pfad kommt
in eine Einstellungsdatei neben das Programm, nicht in den Code.
