"""Baut das Spiel zu einer ausführbaren Datei (Arbeitsplan 8.3).

    python3 bauen.py                – eine Einzeldatei zum Weitergeben
    python3 bauen.py --ordner       – ein Ordner statt einer Datei, startet schneller
    python3 bauen.py --mit-konsole  – zusätzlich ein Konsolenfenster, zum Fehlersuchen

Das Werkzeug läuft nur auf dem Entwicklungsrechner und braucht PyInstaller
(``pip install pyinstaller``). Das Spiel selbst braucht weiterhin nichts
ausser Python und Tkinter.

**PyInstaller baut nur für das System, auf dem es läuft.** Eine
``Diamantenraub.exe`` entsteht also nur unter Windows – unter Linux kommt
eine Linux-Datei heraus, und die hilft auf dem Schulrechner nicht. Wer auf
einem Rechner mit beiden Systemen arbeitet, startet dafür Windows.

Wofür das Ganze
───────────────
Auf Schulrechnern ist oft kein Python installiert, und ohne Adminrechte
lässt sich keines nachinstallieren. Die gebaute Datei bringt Python und
Tkinter mit; sie wird kopiert und doppelgeklickt, mehr nicht.

Worauf es beim Bauen ankommt
────────────────────────────
* **Die Animationen müssen mit.** ``content/animationen/`` enthält PNG- und
  JSON-Dateien, keine Python-Module – PyInstaller findet sie nur, wenn man
  sie als Daten angibt (:data:`DATEN`). Dazu gehören die Unterordner
  ``1.5x/`` jeder Szene für die grossen Bildschirme.
* **Die Messdaten dürfen nicht im Papierkorb landen.** Eine Einzeldatei
  entpackt sich beim Start in ein temporäres Verzeichnis, das beim Beenden
  gelöscht wird. Deshalb schreibt :func:`main.programmordner` die Logs
  neben die ausführbare Datei und nicht neben ``main.py``.
* **``grafik/`` gehört nicht hinein.** Das ist das Render-Werkzeug für die
  Animationen und braucht Firefox; es wird von keinem Spielmodul importiert
  und landet deshalb von selbst nicht im Build.
* **Kein Konsolenfenster**, sonst steht hinter dem Spiel ein schwarzes
  Fenster. Dann gibt es allerdings auch keine Ausgabe mehr: ``sys.stdout``
  und ``sys.stderr`` sind ``None``, worauf :func:`main.melden` Rücksicht
  nimmt. Zum Fehlersuchen baut ``--mit-konsole`` eine Fassung mit Fenster.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

#: Projektordner – hier liegt auch main.py.
WURZEL = Path(__file__).resolve().parent

#: So heisst das fertige Programm (unter Windows mit ".exe" dahinter).
NAME = "Diamantenraub"

#: Was ausser den Python-Modulen mit hinein muss: Quelle im Projekt und Ziel
#: im Build. Das Ziel muss genau so heissen wie die Quelle, denn
#: ``ui.animation`` sucht die Bilder über ``content.__file__``.
DATEN = [("content/animationen", "content/animationen")]

#: Schalter für diesen Aufruf.
SCHALTER_ORDNER = "--ordner"
SCHALTER_KONSOLE = "--mit-konsole"
SCHALTER_HILFE = ("--hilfe", "--help", "-h")


def argumente_fuer_pyinstaller(als_ordner=False, mit_konsole=False):
    """Die Befehlszeile für PyInstaller – ohne das Programm davor.

    ``--add-data`` trennt Quelle und Ziel mit dem Pfadtrenner des Systems:
    unter Windows mit ``;``, sonst mit ``:``. Wer das verwechselt, bekommt
    einen Build ohne Bilder, der erst beim ersten Funkspruch auffällt.

    >>> "--onefile" in argumente_fuer_pyinstaller()
    True
    >>> "--onefile" in argumente_fuer_pyinstaller(als_ordner=True)
    False
    >>> "--windowed" in argumente_fuer_pyinstaller(mit_konsole=True)
    False
    """
    argumente = [
        "--name", NAME,
        "--noconfirm",
        "--clean",
        # Die Spec-Datei und der Zwischenstand gehören in build/ – das ist in
        # .gitignore, der Projektordner bleibt sauber.
        "--specpath", "build",
        "--workpath", "build",
        "--distpath", "dist",
    ]
    argumente.append("--onedir" if als_ordner else "--onefile")
    if not mit_konsole:
        argumente.append("--windowed")
    for quelle, ziel in DATEN:
        argumente += ["--add-data", f"{WURZEL / quelle}{os.pathsep}{ziel}"]
    argumente.append(str(WURZEL / "main.py"))
    return argumente


def ergebnis(als_ordner=False):
    """Wo das fertige Programm nach dem Bauen liegt."""
    endung = ".exe" if os.name == "nt" else ""
    if als_ordner:
        return WURZEL / "dist" / NAME / f"{NAME}{endung}"
    return WURZEL / "dist" / f"{NAME}{endung}"


def bauen(als_ordner=False, mit_konsole=False, ausgabe=print):
    """Ruft PyInstaller auf. Rückgabe ist der Rückgabecode des Programms."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        ausgabe(
            "Fehler: PyInstaller fehlt. Installieren mit:\n"
            f"    {Path(sys.executable).name} -m pip install pyinstaller"
        )
        return 1

    for ordner in ("build", "dist"):
        shutil.rmtree(WURZEL / ordner, ignore_errors=True)

    befehl = [sys.executable, "-m", "PyInstaller"] + argumente_fuer_pyinstaller(als_ordner, mit_konsole)
    ausgabe(f"Baue {NAME} für {sys.platform} …")
    lauf = subprocess.run(befehl, cwd=WURZEL)
    if lauf.returncode:
        ausgabe("PyInstaller ist mit einem Fehler ausgestiegen – siehe Meldungen oben.")
        return lauf.returncode

    fertig = ergebnis(als_ordner)
    ausgabe(f"\nFertig: {fertig}")
    ausgabe(
        "\nZum Verteilen: "
        + ("den ganzen Ordner " + str(fertig.parent) + " kopieren.\n"
           if als_ordner else "diese eine Datei kopieren.\n")
        + "Die Messdaten entstehen beim Spielen im Ordner 'logs' **neben** dem\n"
        "Programm. Dafür muss der Ort beschreibbar sein – ein Stick oder der\n"
        "Desktop, nicht C:\\Programme."
    )
    return 0


HILFE = (
    "Aufruf:\n"
    f"    python3 bauen.py                – eine Einzeldatei\n"
    f"    python3 bauen.py {SCHALTER_ORDNER}       – ein Ordner statt einer Datei (startet schneller)\n"
    f"    python3 bauen.py {SCHALTER_KONSOLE}  – mit Konsolenfenster, zum Fehlersuchen\n"
    "\nEine Windows-.exe entsteht nur, wenn dieses Werkzeug unter Windows läuft.\n"
)


def main(argumente=()):
    """Liest die Schalter und baut. Rückgabe ist der Rückgabecode."""
    argumente = list(argumente)
    if any(angabe in SCHALTER_HILFE for angabe in argumente):
        print(HILFE)
        return 0
    unbekannt = [a for a in argumente if a not in (SCHALTER_ORDNER, SCHALTER_KONSOLE)]
    if unbekannt:
        print(f"Unbekannte Angabe: {' '.join(unbekannt)}\n\n{HILFE}", file=sys.stderr)
        return 2
    return bauen(als_ordner=SCHALTER_ORDNER in argumente,
                 mit_konsole=SCHALTER_KONSOLE in argumente)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
