# Code-Lesehilfe

Diese Datei erklärt die Bausteine, die im Quelltext immer wieder vorkommen –
für alle, die den Code lesen, ohne täglich mit Python zu arbeiten. Sie
erklärt **nicht**, was das Spiel tut (das steht in `README.md` und
`CLAUDE.md`), sondern *wie man liest, was dasteht*.

Jede Funktion im Projekt hat eine Beschreibung in ihrer ersten Zeile. Wer
wissen will, was eine Funktion grob tut, muss also nur ihren Kopf lesen – die
Erklärungen hier helfen beim Drumherum.

---

## Wie eine Datei aufgebaut ist

Von oben nach unten immer gleich:

1. **Der Modulkopf** – der lange Text in `"""…"""` ganz am Anfang. Er sagt,
   wofür die Datei da ist und warum sie so gebaut ist. Das ist die Stelle,
   an der man anfängt zu lesen.
2. **Die Importe** – welche anderen Dateien gebraucht werden.
3. **Die Konstanten** – festgelegte Werte in GROSSBUCHSTABEN, oft mit einem
   `#:`-Kommentar darüber, der sie erklärt.
4. **Die Funktionen und Klassen.**

```python
"""Der Modulkopf: wofür diese Datei da ist."""       ← Docstring der Datei

import tkinter as tk                                  ← Import

#: So viele Übungen gehören zu jedem Level.
BASIS_UEBUNGEN_JE_LEVEL = 2                           ← Konstante
```

## Docstring und Kommentar

* Ein **Docstring** steht in dreifachen Anführungszeichen direkt unter einem
  `def` oder `class` und beschreibt, *was* das Ding tut. Er gehört zum
  Programm: Python kann ihn anzeigen (`help(funktion)`), PyCharm zeigt ihn
  beim Darüberfahren.
* Ein **Kommentar** beginnt mit `#` und erklärt eine einzelne Stelle – meist
  *warum* sie so ist und nicht anders.

In den Docstrings stehen ein paar Schreibweisen aus der Python-Welt:
``text`` in doppelten Rückstrichen meint etwas aus dem Code (einen Wert, einen
Parameter), und `:func:`, `:meth:`, `:class:`, `:mod:`, `:attr:` sind
Verweise auf eine andere Funktion, Methode, Klasse, Datei oder Angabe.

## Funktionen

```python
def zeit_reicht_noch(verbleibende_sekunden, offene_funksprueche=(), tempo=1.0):
    """Bleibt im Level genug Zeit, damit noch eine Übung Sinn ergibt?"""
    return verbleibende_sekunden >= ...
```

* `def` beginnt eine Funktion, danach ihr Name.
* In der Klammer stehen die **Parameter** – das, was man ihr mitgibt.
* `tempo=1.0` ist ein **Standardwert**: Wer nichts angibt, bekommt 1.0.
* `return` gibt das Ergebnis zurück. Steht kein `return` da, kommt `None`
  zurück – "nichts".

Ein Aufruf sieht so aus: `zeit_reicht_noch(300, offene, tempo=1.5)`. Die
Angaben lassen sich auch beim Namen nennen, dann ist die Reihenfolge egal.

## `None`

`None` heisst "nichts da". Im Projekt steht es überall dort, wo eine Angabe
fehlen darf: `aktuelles_level` ist `None`, solange kein Level läuft;
`schluessel` ist `None` bei der Substitution, die keinen hat. Geprüft wird das
mit `if x is None:`.

## Klassen und Objekte

Eine **Klasse** ist ein Bauplan, ein **Objekt** ein danach gebautes Ding. Aus
der Klasse `Bearbeitung` entsteht mit `Bearbeitung(aufgabe)` der Verlauf genau
dieser einen Aufgabe – mit eigener Uhr und eigenem Versuchszähler. Für die
nächste Aufgabe entsteht ein neues Objekt nach demselben Bauplan.

```python
class Bearbeitung:
    """Der Verlauf einer einzelnen Aufgabe."""

    def __init__(self, aufgabe, zeitgeber=None):    ← läuft beim Anlegen
        self.aufgabe = aufgabe                      ← merkt sich etwas
        self._versuche = 0

    def versuchen(self, eingabe):                   ← eine Methode
        ...
```

* Eine **Methode** ist eine Funktion, die zu einem Objekt gehört.
* `self` ist das Objekt selbst – immer der erste Parameter, aber beim Aufruf
  schreibt man ihn nicht hin: `lauf.versuchen("KXQG")`.
* `__init__` läuft **einmal beim Anlegen** und richtet das Objekt ein.
* `__repr__` gibt die Kurzfassung, die in Fehlermeldungen und im Debugger
  erscheint. Die steht nur da, damit man beim Suchen sieht, welches Objekt
  gemeint war.
* `super().__init__(…)` ruft dasselbe in der Klasse darüber auf – jeder
  Screen tut das, weil er erst einmal ein ganz normaler Tk-Rahmen ist.

## `@property` – eine Methode, die sich liest wie eine Angabe

```python
@property
def zeit_ist_um(self):
    """Ist das Zeitfenster des laufenden Levels abgelaufen?"""
    return ...
```

Geschrieben wird sie wie eine Funktion, benutzt wie eine Angabe – also
`stand.zeit_ist_um` **ohne** Klammern. Der Vorteil: Von aussen sieht es aus
wie ein gespeicherter Wert, in Wirklichkeit wird er jedes Mal frisch
ausgerechnet. Fast alle Fragen an den Spielstand sind so gebaut.

## Der Unterstrich vor einem Namen

`_zeitfenster`, `_verlange_level`, `_Setzer`: Der Unterstrich heisst
"hausintern". Python hindert niemanden daran, es trotzdem zu benutzen, aber
gemeint ist: Das ist Innenleben, darauf sollte sich nichts von aussen
verlassen. Ohne Unterstrich ist der Name Teil dessen, was andere Dateien
benutzen dürfen.

Ein einzelner Unterstrich als Parametername (`def _maus_drauf(self,
_ereignis)`) heisst: "Diesen Wert bekomme ich zwar, brauche ihn aber nicht."

## `NamedTuple` – ein Datensatz mit festen Feldern

```python
class Aufgabe(NamedTuple):
    kennung: str
    level: int
    ...
```

Ein `NamedTuple` ist eine feste Liste von Feldern mit Namen. Man liest sie mit
`aufgabe.level`, und **ändern lässt sie sich nicht** – das ist Absicht: Eine
einmal gestellte Aufgabe soll sich nicht hinter dem Rücken der Messdaten
ändern. Wer eine leicht andere Fassung braucht, macht mit `_replace(…)` eine
Kopie:

```python
verschoben = stueck._replace(y=stueck.y + 10)    # dasselbe Stück, 10 Pixel tiefer
```

So etwas steht im Projekt für `Aufgabe`, `Versuchsergebnis`, `Levelwechsel`,
`Schritt` und die Stücke des Buchsatzes.

## Funktionen, die man weiterreicht

In Python ist eine Funktion selbst ein Wert: Man kann sie in eine Variable
legen und später aufrufen. Davon lebt der ganze Spielablauf.

* **`danach`** heisst im Projekt immer: die Funktion, die aufgerufen wird,
  wenn ein Screen fertig ist. Kein Screen weiss, was nach ihm kommt – er ruft
  nur `danach`. Was das ist, steht gesammelt in `ui/ablauf.py`.
* **Rückruf** ist dasselbe von der anderen Seite gesehen: `bei_levelwechsel`
  wird vom Durchlauf gerufen, wenn ein Level endet.
* **`lambda`** ist eine Funktion ohne Namen, für einen Einzeiler:
  `command=lambda: self.blaettern(1)` heisst "wenn geklickt wird, blättere
  vor".
* **`functools.partial`** trägt Angaben schon ein:
  `partial(handbuch_aufschlagen, level=2)` ist "die Funktion
  `handbuch_aufschlagen`, bei der `level` schon auf 2 steht". Heraus kommt
  wieder eine Funktion, die sich später mit dem Rest aufrufen lässt.

## `yield` – Werte einzeln herausgeben

Eine Funktion mit `yield` gibt ihre Ergebnisse eines nach dem anderen heraus,
statt erst alle zu sammeln. Für den Leser ist das eine Liste, die nach und
nach entsteht. Im Projekt steht das nur an wenigen Stellen in den Tests.

## Wenn etwas schiefgeht

* `raise ValueError("…")` bricht ab und sagt, was nicht stimmt.
* `try: … except Fehler: …` fängt einen Fehler ab und macht etwas anderes.
* `finally: …` läuft in jedem Fall – auch wenn es einen Fehler gab. Im Spiel
  hängt daran, dass ein Takt sich **immer** wieder anmeldet: Ein misslungenes
  Einzelbild darf die Animation nicht anhalten.

Welcher Fehler wann gemeint ist, steht im Kopf von `crypto/normalize.py`:
`TypeError` ist der falsche Typ (ein Programmierfehler), `ValueError` ein
unbrauchbarer Wert.

## Tkinter in zehn Begriffen

Tkinter ist die Oberflächen-Bibliothek von Python (in `ui/` und `main.py`,
sonst nirgends).

| Begriff | Was es ist |
|---------|------------|
| **Widget** / Bedienelement | Alles Sichtbare: Knopf, Textzeile, Rahmen |
| `tk.Frame` | Ein Rahmen, in dem andere Elemente liegen |
| `tk.Label` | Eine Textzeile |
| `tk.Button` | Ein Knopf; `command=` ist, was er tut |
| `tk.Entry` | Ein Eingabefeld |
| `tk.Canvas` / Leinwand | Eine Fläche zum Zeichnen – Linien, Rechtecke, Text, Bilder |
| `pack()` / `grid()` | Legt fest, wo ein Element sitzt: untereinander oder im Raster |
| `bind("<Return>", …)` | Verbindet eine Taste oder einen Klick mit einer Funktion |
| `after(ms, funktion)` | "Ruf das in so vielen Millisekunden auf" – so laufen alle Animationen und Uhren |
| **Tag** | Ein Namensschild an gezeichneten Stücken der Leinwand; damit lassen sich viele auf einmal ansprechen oder löschen |

Wichtig für dieses Projekt: Verzögerte Aufrufe werden nicht direkt mit
`after()` angemeldet, sondern mit `Screen.spaeter(…)` – die werden beim
Screenwechsel automatisch wieder abgemeldet.

## Die Tests lesen

* Jede Datei in `tests/` prüft eine Datei des Spiels: `tests/test_spielstand.py`
  prüft `game/spielstand.py`.
* Eine **Testfunktion** heisst `test_…` und trägt ihre Aussage im Namen:
  `test_nach_drei_versuchen_ohne_fortschritt_steht_die_loesung_da`. Der Name
  ist die Beschreibung – deshalb haben diese Funktionen oft keinen Docstring,
  sondern nur dort einen, wo die Begründung wichtig ist.
* `assert x == y` ist die Prüfung selbst: Stimmt es nicht, ist der Test rot.
* **Fixture**: eine Vorbereitung, die pytest einem Test mitgibt – siehe den
  Kopf von `tests/conftest.py`.
* `@pytest.mark.parametrize(…)` lässt denselben Test mit vielen Werten laufen;
  daher die hohe Zahl im Testbericht.
* `monkeypatch` tauscht für die Dauer eines Tests etwas aus, `tmp_path` ist
  ein Ordner, den pytest anlegt und wieder wegräumt – so schreibt kein Test
  ins echte `logs/`.
* **Doctest**: Zeilen mit `>>>` in einem Docstring sind Beispiele, die
  mitlaufen. Sie sind zugleich Erklärung und Prüfung – stimmt das Ergebnis
  nicht mehr, wird der Test rot.

## Die Begriffe dieses Projekts

| Begriff | Bedeutung |
|---------|-----------|
| **Screen** | Ein Bildschirm des Spiels (Startbildschirm, Handbuch, Übung, Funk …). Beim Wechsel wird der alte abgerissen und der neue gebaut |
| **Durchlauf** | Eine Person spielt das Spiel einmal – Spielstand plus Logdatei |
| **Spielstand** | Wo im Spiel wir stehen: Level, Zeitfenster, laufende und erledigte Aufgaben |
| **Bearbeitung** | Der Verlauf *einer* Aufgabe: Versuche, Zeit, ob gelöst |
| **Zeitfenster** | Die feste Zeit eines Levels (15/10/25 Minuten) |
| **Seed / Zufallsquelle / Strom** | Der Seed ist die Startzahl des Zufalls. Aus ihm entstehen je Level eigene Zufallsströme. Weil er im Log steht, lässt sich jede gezogene Aufgabe später rekonstruieren |
| **Teilaufgabe** | Bei langen Funksprüchen wird nur der Anfang von Hand gerechnet; ein Knopf löst den Rest auf |
| **Wächter** (`_verlange_…`) | Prüft am Anfang einer Methode, dass die Reihenfolge stimmt, und bricht sonst mit einer klaren Meldung ab |
| **Bühne, Ausschnitt, Figur, Ablauf** | Die Teile der Animationen: die Leinwand mit der Szene, der bewegte Bildbereich darin, eine bewegliche Figur darüber, ein einmaliger Ablauf |
| **Kiste, Fluss, Setzer** | Der Buchsatz: Der Setzer macht aus einer Handbuchseite unteilbare Kisten, der Fluss hält sie in Lesereihenfolge, danach werden sie auf Seiten verteilt |
| **Werkzeug, Schrittmarke** | Die Tabelle oder das Quadrat neben einem Beispiel und die Markierung, die zeigt, wo ein Rechenschritt nachschlägt |
| **Maßstab** | 1 oder 1,5 – auf 1080p-Monitoren wird alles anderthalbmal so gross gezeichnet. Feste Pixelangaben gehen immer durch `self.px(…)` |

## Ein Leseweg durch das Spiel

Wer den Ablauf einmal von vorn nachvollziehen will:

1. `main.py` – öffnet das Fenster, sonst nichts.
2. `ui/ablauf.py` – welcher Screen wann kommt. Der ganze Weg auf zwei Seiten.
3. `ui/hauptfenster.py` – wie Screens getauscht werden und wer die Uhr treibt.
4. `ui/screen.py` – die Grundform, die jeder Screen erbt.
5. `game/spielstand.py` – die Regeln des Ablaufs, ohne jede Oberfläche.
6. `game/bearbeitung.py` – die 3-Versuche-Regel und die Zeitmessung.
7. `crypto/normalize.py` – die Textkonvention, die für alles gilt.
8. `crypto/caesar.py`, `crypto/substitution.py`, `crypto/vigenere.py` – die
   drei Verfahren, jedes für sich lesbar und mit Beispielen im Docstring.
