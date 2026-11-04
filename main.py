"""Einstiegspunkt für das Lernspiel "Der Diamantenraub".

Aufruf:  python main.py            – das Spiel
         python main.py --testmodus – zum Durchklicken (siehe ui/testmodus.py)

Für Schulrechner ohne Python lässt sich daraus mit ``bauen.py`` eine einzelne
ausführbare Datei bauen (Arbeitsplan 8.3).

main.py öffnet nur das Hauptfenster und fängt die zwei Startfehler ab
(Tkinter fehlt, keine Bildschirmanzeige). Alles Weitere steht in ``ui/`` –
welcher Screen wann kommt, in ``ui/ablauf.py``.

Der Testmodus ist für den Entwicklungsrechner: Er hängt eine Leiste unter
das Spiel, mit der sich Aufgaben lösen, Level überspringen und einzelne
Stellen der Geschichte anspringen lassen. Am Spiel selbst ändert er nichts –
im Unterricht wird es ohne diesen Schalter gestartet.
"""

import sys
from pathlib import Path


def programmordner():
    """Der Ordner, in dem das Spiel liegt – auch als gebaute Einzeldatei.

    Normalerweise ist das der Ordner von ``main.py``. In einem Build von
    PyInstaller (``bauen.py``) zeigt ``__file__`` dagegen in das temporäre
    Entpackverzeichnis, das beim Beenden **gelöscht** wird. Die Messdaten
    landeten dort und wären nach dem Unterricht weg (Arbeitsplan 8.3).
    Deshalb zählt im Build der Ordner der ausführbaren Datei: Dort liegt
    ``Diamantenraub.exe``, und daneben entsteht ``logs/``.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


#: Hierhin schreibt das Spiel die Messdaten: neben das Programm, nicht in das
#: Verzeichnis, aus dem gestartet wurde. Wer das Spiel per Doppelklick oder aus
#: einem anderen Ordner startet, fände die Logs sonst an einem zufälligen Ort.
PROTOKOLLORDNER = programmordner() / "logs"


def melden(text, fehler=False):
    """Schreibt eine Startmeldung – und schweigt, wenn es keine Konsole gibt.

    Ein ohne Konsolenfenster gebautes Spiel hat keine: ``sys.stdout`` und
    ``sys.stderr`` sind dann ``None``, und ein ``print`` dorthin bricht mit
    einem ``AttributeError`` ab. Ausgerechnet die Fehlermeldungen brächten das
    Spiel also zum Absturz – und zwar wortlos.
    """
    strom = sys.stderr if fehler else sys.stdout
    if strom is not None:
        print(text, file=strom)


#: Damit startet der Testmodus.
SCHALTER_TESTMODUS = "--testmodus"

#: Damit wird nur der Aufruf erklärt.
SCHALTER_HILFE = ("--hilfe", "--help", "-h")

#: Was bei ``--hilfe`` und bei einem unbekannten Aufruf auf dem Bildschirm steht.
HILFE = (
    "Aufruf:\n"
    "    python3 main.py                – das Spiel\n"
    f"    python3 main.py {SCHALTER_TESTMODUS}   – Testmodus zum Durchklicken "
    "(Level überspringen, Story-Stellen anspringen)\n"
)


def starte_spiel(argumente=()):
    """Baut das Hauptfenster auf und startet die Tkinter-Ereignisschleife.

    ``argumente`` sind die Angaben von der Kommandozeile – die reicht ganz
    unten der Programmstart herein. Rückgabewert ist der Rückgabecode des
    Programms: 0, wenn alles lief, sonst 1 (der Start misslang) oder 2 (der
    Aufruf war nicht zu verstehen).
    """
    argumente = list(argumente)
    if any(angabe in SCHALTER_HILFE for angabe in argumente):
        melden(HILFE)
        return 0
    testmodus = SCHALTER_TESTMODUS in argumente
    unbekannt = [angabe for angabe in argumente if angabe != SCHALTER_TESTMODUS]
    if unbekannt:
        melden(f"Unbekannte Angabe: {' '.join(unbekannt)}\n\n{HILFE}", fehler=True)
        return 2

    try:
        import tkinter as tk
    except ImportError:
        melden(
            "Fehler: Das Modul 'tkinter' fehlt.\n"
            "Unter Debian/Ubuntu installieren mit:\n"
            "    sudo apt install python3-tk\n"
            "Danach main.py erneut starten (die virtuelle Umgebung greift auf\n"
            "die System-Standardbibliothek zu und findet tkinter dann).",
            fehler=True,
        )
        return 1

    # Erst nach der Prüfung oben: ui/ braucht Tkinter schon beim Import.
    from ui import ablauf, testmodus as testmodus_ui

    try:
        wurzel = tk.Tk()
    except tk.TclError as fehler:
        # Tritt auf, wenn kein Bildschirm zur Verfuegung steht, etwa bei einer
        # SSH-Sitzung ohne Weiterleitung oder auf einem Server. Ohne diesen
        # Zweig endet der Start mit einem englischen Stacktrace.
        melden(
            "Fehler: Es ist keine Bildschirmanzeige verfügbar.\n"
            f"Meldung des Systems: {fehler}\n"
            "Starte das Spiel direkt am Rechner und nicht über eine\n"
            "Fernverbindung ohne Grafikweiterleitung.",
            fehler=True,
        )
        return 1

    if testmodus:
        testmodus_ui.oeffnen(wurzel, protokollordner_des_spiels=PROTOKOLLORDNER)
    else:
        ablauf.oeffnen(wurzel, protokollordner=PROTOKOLLORDNER)
    wurzel.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(starte_spiel(sys.argv[1:]))
