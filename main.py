"""Einstiegspunkt für das Lernspiel "Der Diamantenraub".

Aufruf:  python main.py

Stand Phase 0: öffnet nur das leere Hauptfenster. Die Screens
(Charakterauswahl, Handbuch, Aufgaben, Funk) kommen in Phase 6 dazu und
werden dann aus dem Paket ``ui`` heraus in dieses Fenster gehängt.
"""

import sys

FENSTER_TITEL = "Der Diamantenraub"
FENSTER_BREITE = 1000
FENSTER_HOEHE = 700
# Untergrenze: auf kleinen Schulmonitoren muss das Vigenère-Quadrat (26x26)
# noch vollständig lesbar sein – siehe Arbeitsplan 6.7.
MIN_BREITE = 800
MIN_HOEHE = 600


def _zentriere(fenster, breite, hoehe):
    """Setzt das Fenster mittig auf den Bildschirm."""
    bildschirm_breite = fenster.winfo_screenwidth()
    bildschirm_hoehe = fenster.winfo_screenheight()
    x = max(0, (bildschirm_breite - breite) // 2)
    y = max(0, (bildschirm_hoehe - hoehe) // 3)
    fenster.geometry(f"{breite}x{hoehe}+{x}+{y}")


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

    fenster = tk.Tk()
    fenster.title(FENSTER_TITEL)
    fenster.minsize(MIN_BREITE, MIN_HOEHE)
    _zentriere(fenster, FENSTER_BREITE, FENSTER_HOEHE)
    fenster.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(starte_spiel())
