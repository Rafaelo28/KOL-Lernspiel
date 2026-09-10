"""Welcher Screen wann kommt (Arbeitsplan 6.1 – ausgebaut in Phase 7).

Das Hauptfenster weiss nur, *wie* umgeschaltet wird. *Was* als Nächstes
kommt – der erste Screen und das, was auf ein Level folgt –, steht hier.
Solange die echten Screens fehlen, sind es die Platzhalter aus
:mod:`ui.platzhalter`; in Phase 7 werden hier die Level zusammengesetzt.

Nach einem Levelwechsel wird sofort umgeschaltet, egal was gerade offen ist
(Projektregel 1). Eine offene Aufgabe hat der Spielstand da schon als
abgebrochen abgelegt und der Durchlauf gespeichert.
"""

from ui import platzhalter
from ui.hauptfenster import Hauptfenster

#: Mit diesem Screen beginnt das Spiel.
STARTSCREEN = platzhalter.Start


def nach_levelwechsel(fenster, wechsel):
    """Zeigt, was auf ein Level folgt – das nächste Handbuch oder den Abschluss."""
    if wechsel.spielende:
        fenster.zeige(platzhalter.Abschluss, durch_zeitablauf=wechsel.durch_zeitablauf)
        return
    hinweis = (
        f"Die Zeit für Level {wechsel.altes_level} ist abgelaufen – weiter geht es "
        f"mit Level {wechsel.neues_level}."
        if wechsel.durch_zeitablauf
        else ""
    )
    fenster.zeige(platzhalter.Handbuch, level=wechsel.neues_level, hinweis=hinweis)


def oeffnen(wurzel, zeitgeber=None, protokollordner=None):
    """Baut das Hauptfenster in ``wurzel`` und zeigt den ersten Screen."""
    return Hauptfenster(
        wurzel,
        STARTSCREEN,
        nach_levelwechsel,
        zeitgeber=zeitgeber,
        protokollordner=protokollordner,
    )
