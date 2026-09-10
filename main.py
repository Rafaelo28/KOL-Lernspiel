"""Einstiegspunkt für das Lernspiel "Der Diamantenraub".

Aufruf:  python main.py

main.py öffnet nur das Hauptfenster und fängt die zwei Startfehler ab
(Tkinter fehlt, keine Bildschirmanzeige). Alles Weitere steht in ``ui/`` –
welcher Screen wann kommt, in ``ui/ablauf.py``.
"""

import sys
from pathlib import Path

#: Hierhin schreibt das Spiel die Messdaten: neben main.py, nicht in das
#: Verzeichnis, aus dem gestartet wurde. Wer das Spiel per Doppelklick oder aus
#: einem anderen Ordner startet, fände die Logs sonst an einem zufälligen Ort.
PROTOKOLLORDNER = Path(__file__).resolve().parent / "logs"


def starte_spiel():
    """Baut das Hauptfenster auf und startet die Tkinter-Ereignisschleife."""
    try:
        import tkinter as tk
    except ImportError:
        print(
            "Fehler: Das Modul 'tkinter' fehlt.\n"
            "Unter Debian/Ubuntu installieren mit:\n"
            "    sudo apt install python3-tk\n"
            "Danach main.py erneut starten (die virtuelle Umgebung greift auf\n"
            "die System-Standardbibliothek zu und findet tkinter dann).",
            file=sys.stderr,
        )
        return 1

    # Erst nach der Prüfung oben: ui/ braucht Tkinter schon beim Import.
    from ui import ablauf

    try:
        wurzel = tk.Tk()
    except tk.TclError as fehler:
        # Tritt auf, wenn kein Bildschirm zur Verfuegung steht, etwa bei einer
        # SSH-Sitzung ohne Weiterleitung oder auf einem Server. Ohne diesen
        # Zweig endet der Start mit einem englischen Stacktrace.
        print(
            "Fehler: Es ist keine Bildschirmanzeige verfügbar.\n"
            f"Meldung des Systems: {fehler}\n"
            "Starte das Spiel direkt am Rechner und nicht über eine\n"
            "Fernverbindung ohne Grafikweiterleitung.",
            file=sys.stderr,
        )
        return 1

    ablauf.oeffnen(wurzel, protokollordner=PROTOKOLLORDNER)
    wurzel.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(starte_spiel())
