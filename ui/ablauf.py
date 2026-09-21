"""Welcher Screen wann kommt (Arbeitsplan 6.1 – ausgebaut in Phase 7).

Das Hauptfenster weiss nur, *wie* umgeschaltet wird. *Was* als Nächstes
kommt – der erste Screen und das, was auf ein Level folgt –, steht hier.
Die Screens selbst bekommen ihr "danach" von hier mitgegeben; so bleibt der
ganze Weg an einer Stelle lesbar:

    Startbildschirm (ID) → Figurwahl → Story-Intro → Level 1 → Level 2 → Level 3 → Abschluss

Jedes Level beginnt mit seiner Handbuchseite. Danach fragt :func:`weiter_im_level`
nach jeder Aufgabe, was als Nächstes kommt:

    Handbuchseite → Übung → (Zusatzaufgabe) → Funksprüche → nächstes Level

Entschieden wird das nicht hier, sondern in :mod:`game.levelablauf`: Es hängt
an der Restzeit, am Tempo und daran, was im Level schon gelaufen ist – das
weiss der Spielstand. Wird die Zeit knapp, fallen Übungen aus, damit die
Funksprüche noch drankommen (Vorrang-Regel, Arbeitsplan Phase 7). Dieses Modul
übersetzt die Antwort nur in den passenden Screen.

Die ID vom Startbildschirm reist bis zur Figurwahl mit; mit der Figur beginnt
der Durchlauf, und die ID wird sein Pseudonym.

Nach einem Levelwechsel wird sofort umgeschaltet, egal was gerade offen ist
(Projektregel 1). Eine offene Aufgabe hat der Spielstand da schon als
abgebrochen abgelegt und der Durchlauf gespeichert.
"""

from functools import partial

from content import story
from game import levelablauf
from ui import abschluss, erzaehlszene, figurwahl, funk, handbuch, startbildschirm, uebung
from ui.hauptfenster import Hauptfenster

#: Mit diesem Screen beginnt das Spiel.
STARTSCREEN = startbildschirm.Startbildschirm

#: Ein Satz aus der Geschichte, der über dem Funkgerät steht, sobald die
#: Nachricht ganz da ist. Beim abgefangenen Funkspruch liegt dann ein sichtbar
#: langer Geheimtext vor einem – dorthin gehört der Hinweis auf die
#: Häufigkeitsanalyse (Arbeitsplan 7.2).
HINWEIS_ZUM_FUNKSPRUCH = {
    story.FUNKSPRUCH_VERFOLGER.kennung: " ".join(story.HINWEIS_HAEUFIGKEITSANALYSE.absaetze),
}

#: Die Erzählszenen und ihre Titel in der Kopfzeile.
TITEL_INTRO = "Der Absturz"
TITEL_UEBERGANG = "Zeit für etwas Stärkeres"
TITEL_REFLEXION = "Kurz nachgedacht"
#: Der letzte Knopf des Intros – danach beginnt die Uhr von Level 1.
KNOPF_HANDBUCH = "Handbuch aufschlagen"

#: Erzähltexte, die vor einem Funkspruch eingeblendet werden: vor dem eigenen
#: Standort die Reflexionsfrage zu Level 3 (Arbeitsplan 7.3).
ERZAEHLUNG_VOR_FUNKSPRUCH = {
    story.FUNKSPRUCH_STANDORT.kennung: (story.REFLEXIONSFRAGE_LEVEL_3, TITEL_REFLEXION),
}

#: Erzähltexte zwischen zwei Leveln, als (Text, Titel, Funkspruch): Nach
#: Level 2 kommt der Übergang zu Vigenère – aber nur, wenn der abgefangene
#: Funkspruch dran war, denn er spricht von ihm (Arbeitsplan 7.2).
ERZAEHLUNG_NACH_LEVEL = {
    2: (story.UEBERGANG_ZU_LEVEL_3, TITEL_UEBERGANG, story.FUNKSPRUCH_VERFOLGER),
}


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
    erzaehlszene_zeigen(fenster, story.INTRO, TITEL_INTRO, danach=level_1_beginnen,
                        szene=erzaehlszene.SZENE_WRACK, letzter_knopf=KNOPF_HANDBUCH)


def erzaehlszene_zeigen(fenster, erzaehltext, titel, danach,
                        szene=erzaehlszene.SZENE_LAGER, letzter_knopf=erzaehlszene.KNOPF_WEITER):
    """Ein Erzähltext vor einer Szene – Absatz für Absatz (:mod:`ui.erzaehlszene`)."""
    fenster.zeige(erzaehlszene.Erzaehlszene, absaetze=erzaehltext.absaetze, danach=danach,
                  titel=titel, szene=szene, letzter_knopf=letzter_knopf)


def level_1_beginnen(fenster):
    """Nach dem Intro: Level 1 beginnt, ab jetzt läuft die Uhr."""
    fenster.durchlauf.starte_level()
    handbuch_aufschlagen(fenster, fenster.durchlauf.spielstand.aktuelles_level)


def handbuch_aufschlagen(fenster, level, hinweis=""):
    """Zu Beginn eines Levels: der Einstieg aus der Geschichte und die Handbuchseite."""
    fenster.zeige(
        handbuch.Handbuch,
        level=level,
        danach=weiter_im_level,
        hinweis=hinweis,
        einleitung=story.EINSTIEG_NACH_LEVEL[level].absaetze,
    )


def weiter_im_level(fenster):
    """Zeigt, was im Level als Nächstes drankommt – nach dem Handbuch und nach jeder Aufgabe.

    Gefragt wird der Spielstand (:mod:`game.levelablauf`); hier wird nur
    ausgeführt, was er sagt.
    """
    schritt = fenster.durchlauf.spielstand.naechster_schritt
    if schritt.art in (levelablauf.SCHRITT_UEBUNG, levelablauf.SCHRITT_ZUSATZAUFGABE):
        uebung_zeigen(fenster, zusatzaufgabe=schritt.art == levelablauf.SCHRITT_ZUSATZAUFGABE)
    elif schritt.art == levelablauf.SCHRITT_FUNKSPRUCH:
        funkspruch_zeigen(fenster, schritt.funkspruch)
    else:
        level_beenden(fenster)


def uebung_zeigen(fenster, zusatzaufgabe=False):
    """Eine Übung aus dem Handbuch – oder eine Zusatzaufgabe für die Schnellen (5.4)."""
    fenster.zeige(uebung.Uebung, danach=weiter_im_level, zusatzaufgabe=zusatzaufgabe)


def funkspruch_zeigen(fenster, funkspruch):
    """Ein echter Funkspruch am Funkgerät – der nächste, der in diesem Level ansteht.

    Führt ein Erzähltext dorthin, kommt er davor: vor dem eigenen Standort die
    Reflexionsfrage, mit der Level 3 aus den Übungen herausführt.
    """
    vorher = ERZAEHLUNG_VOR_FUNKSPRUCH.get(funkspruch.kennung)
    if vorher is not None:
        erzaehltext, titel = vorher
        erzaehlszene_zeigen(fenster, erzaehltext, titel,
                            danach=partial(funkgeraet_zeigen, funkspruch=funkspruch))
        return
    funkgeraet_zeigen(fenster, funkspruch)


def funkgeraet_zeigen(fenster, funkspruch):
    """Der Funkspruch am Gerät, ohne Vorrede."""
    fenster.zeige(funk.Funk, funkspruch=funkspruch, danach=weiter_im_level,
                  hinweis=HINWEIS_ZUM_FUNKSPRUCH.get(funkspruch.kennung, ""))


def level_beenden(fenster):
    """Das Level ist durch – weiter zum nächsten (oder zum Abschluss)."""
    fenster.durchlauf.naechstes_level()


def nach_levelwechsel(fenster, wechsel):
    """Zeigt, was auf ein Level folgt: der Übergang, das nächste Handbuch oder der Abschluss.

    Der Übergang steht **nach** dem Wechsel und damit im Zeitfenster des neuen
    Levels. Vor dem Wechsel gezeigt, liefe er noch in der Zeit des alten: Wer
    ihn langsam liest, hätte sein Level von "vorzeitig" auf "zeitablauf"
    gekippt, obwohl alle Aufgaben erledigt waren – und beim Zeitablauf fiele er
    ganz aus, obwohl der Funkspruch dran war, von dem er spricht.
    """
    if wechsel.spielende:
        fenster.zeige(abschluss.Abschluss, durch_zeitablauf=wechsel.durch_zeitablauf)
        return
    hinweis = (
        f"Die Zeit für Level {wechsel.altes_level} ist abgelaufen – weiter geht es "
        f"mit Level {wechsel.neues_level}."
        if wechsel.durch_zeitablauf
        else ""
    )
    weiter = partial(handbuch_aufschlagen, level=wechsel.neues_level, hinweis=hinweis)
    uebergang = ERZAEHLUNG_NACH_LEVEL.get(wechsel.altes_level)
    if uebergang is not None and fenster.durchlauf.spielstand.wurde_gestellt(uebergang[2]):
        erzaehltext, titel, _ = uebergang
        erzaehlszene_zeigen(fenster, erzaehltext, titel, danach=weiter)
        return
    weiter(fenster)


def oeffnen(wurzel, zeitgeber=None, protokollordner=None, massstab=None):
    """Baut das Hauptfenster in ``wurzel`` und zeigt den ersten Screen.

    Ohne ``massstab`` richtet sich die Grösse nach dem Bildschirm (siehe
    :mod:`ui.stil`); Tests geben ihn vor, damit sie überall gleich laufen.
    """
    return Hauptfenster(
        wurzel,
        partial(STARTSCREEN, danach=figurwahl_zeigen),
        nach_levelwechsel,
        zeitgeber=zeitgeber,
        protokollordner=protokollordner,
        massstab=massstab,
    )
