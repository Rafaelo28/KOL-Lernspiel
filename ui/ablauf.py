"""Welcher Screen wann kommt (Arbeitsplan 6.1 – ausgebaut in Phase 7).

Das Hauptfenster weiss nur, *wie* umgeschaltet wird. *Was* als Nächstes
kommt – der erste Screen und das, was auf ein Level folgt –, steht hier.
Die Screens selbst bekommen ihr "danach" von hier mitgegeben; so bleibt der
ganze Weg an einer Stelle lesbar:

    Startbildschirm (ID) → Figurwahl → Story-Intro → Level 1 → Level 2 → Level 3 → Abschluss

Die ID vom Startbildschirm reist bis zur Figurwahl mit; mit der Figur beginnt
der Durchlauf, und die ID wird sein Pseudonym.

Wo die echten Screens noch fehlen, stehen die Platzhalter aus
:mod:`ui.platzhalter`; in Phase 7 werden hier die Level zusammengesetzt.

Nach einem Levelwechsel wird sofort umgeschaltet, egal was gerade offen ist
(Projektregel 1). Eine offene Aufgabe hat der Spielstand da schon als
abgebrochen abgelegt und der Durchlauf gespeichert.
"""

from functools import partial

from ui import figurwahl, intro, platzhalter, startbildschirm
from ui.hauptfenster import Hauptfenster

#: Mit diesem Screen beginnt das Spiel.
STARTSCREEN = startbildschirm.Startbildschirm


def figurwahl_zeigen(fenster, spieler_id):
    """Nach dem Startbildschirm: Wer aus der Crew bist du?

    ``spieler_id`` ist die ID vom Startbildschirm. Sie wird bis zur Wahl der
    Figur mitgereicht – erst dann beginnt der Durchlauf, der sie braucht.
    """
    fenster.zeige(figurwahl.Figurwahl, danach=partial(figur_gewaehlt, spieler_id=spieler_id))


def figur_gewaehlt(fenster, figur, spieler_id=None):
    """Mit der Figur beginnt der Durchlauf – dann kommt der Absturz.

    Unter ``spieler_id`` steht der Durchlauf im Log. Ohne sie erzeugt der
    Spielstand selbst eine (``P`` und der Seed) – das kommt nur in Tests vor,
    im Spiel verlangt der Startbildschirm eine ID.
    """
    fenster.starte_durchlauf(figur, pseudonym=spieler_id)
    fenster.zeige(intro.Intro, danach=level_1_beginnen)


def level_1_beginnen(fenster):
    """Nach dem Intro: Level 1 beginnt, ab jetzt läuft die Uhr."""
    fenster.durchlauf.starte_level()
    fenster.zeige(platzhalter.Handbuch, level=fenster.durchlauf.spielstand.aktuelles_level)


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
        partial(STARTSCREEN, danach=figurwahl_zeigen),
        nach_levelwechsel,
        zeitgeber=zeitgeber,
        protokollordner=protokollordner,
    )
