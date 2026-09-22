"""Was im Level als Nächstes drankommt (Arbeitsplan Phase 7).

Ein Level läuft nach diesem Muster: die Handbuchseite, zwei Übungen, dann die
Funksprüche, die die Geschichte tragen. Wer schnell ist, bekommt zwischen den
Übungen Zusatzaufgaben (:mod:`game.zusatzaufgaben`), wer langsam ist, nicht.

Diese Entscheidung steht hier und nicht in der Oberfläche: Sie hängt an der
Restzeit, am Tempo und daran, was im Level schon gelaufen ist – lauter Dinge,
die der Spielstand kennt und ein Screen nur vom Hörensagen. Hier lässt sie
sich ohne Bildschirm testen, und kein Screen kann sie später anders auslegen.
Die Oberfläche fragt :attr:`game.spielstand.Spielstand.naechster_schritt` und
zeigt, was zurückkommt.

Die Vorrang-Regel
─────────────────
Zwei Projektregeln beissen sich: Regel 1 wechselt starr zum nächsten Level,
egal was offen ist; Regel 2 begrenzt eine einzelne Aufgabe nicht über die
Zeit. Ein langsames Kind kann also an den Übungen so viel Zeit verlieren, dass
die Funksprüche nie drankommen – und ab da ergibt die Geschichte keinen Sinn
mehr.

Deshalb wird vor jeder weiteren Übung geschätzt, wie lange die noch offenen
Funksprüche des Levels dauern werden (``zusatzaufgaben.zeit_reicht_noch``, das
dafür dieselbe Gerade benutzt wie für die Zusatzaufgaben). Reicht die Restzeit
dafür nicht mehr, kommt keine Übung mehr, sondern der nächste Funkspruch –
auch wenn dafür die zweite Basis-Übung ausfällt.

Das verlängert kein Zeitfenster und ändert am Ablauf schneller Kinder nichts;
es sortiert nur um, was in der verbleibenden Zeit zuerst drankommt. Eine schon
laufende Aufgabe bricht es nie ab – gefragt wird erst, wenn eine Aufgabe
fertig ist. Läuft die Zeit trotzdem ab, während noch gerechnet wird, greift
weiter Regel 1: Das Level endet sofort. Der Funkspruch fällt deshalb nicht
aus – nach dem Wechsel steht er zum Mitlesen da (Regel 1, "Kein Funkspruch
geht verloren"); gerechnet hat ihn dann aber niemand.

Und wenn nichts mehr ansteht
────────────────────────────
Ist der letzte Funkspruch eines Levels erzählt, hat die Vorrang-Regel nichts
mehr zu reservieren. Dann füllen weitere Übungen die Restzeit, solange die
Mindestrestzeit bleibt und die Obergrenze der Zusatzaufgaben es zulässt.
Sonst endete das Level in dem Moment, in dem die Geschichte durch ist – und
wer langsam gerechnet hat, sässe die letzten Minuten ab, während die
Kontrollgruppe weiterarbeitet. Eine dabei angefangene Übung wird am Levelende
abgebrochen und steht so im Log; die Auswertung filtert solche Zeilen ohnehin
heraus.

Warum zwei Basis-Übungen
────────────────────────
So steht es im Konzept: "Übung im Buch: 2 Aufgaben (verschlüsseln/
entschlüsseln)". Der Generator sorgt dafür, dass nicht zweimal dieselbe
Richtung kommt – man übt also beide Wege, bevor es ernst wird.
"""

from typing import NamedTuple

from game import zusatzaufgaben as _zusatzaufgaben

#: So viele Übungen gehören zu jedem Level, bevor gefunkt wird –
#: Zusatzaufgaben kommen obendrauf.
BASIS_UEBUNGEN_JE_LEVEL = 2

#: Die möglichen Schritte.
SCHRITT_UEBUNG = "uebung"
SCHRITT_ZUSATZAUFGABE = "zusatzaufgabe"
SCHRITT_FUNKSPRUCH = "funkspruch"
SCHRITT_LEVELENDE = "levelende"


class Schritt(NamedTuple):
    """Was als Nächstes kommt. ``funkspruch`` nur bei :data:`SCHRITT_FUNKSPRUCH`.

    >>> Schritt(SCHRITT_LEVELENDE).art
    'levelende'
    """

    art: str
    funkspruch: object = None


def naechster_schritt(erledigte_uebungen, offene_funksprueche, verbleibende_sekunden,
                      zusatzaufgabe_faellig=False, tempo=1.0):
    """Was im laufenden Level auf die eben abgeschlossene Aufgabe folgt.

    ``erledigte_uebungen`` zählt nur die Basis-Übungen des Levels, nicht die
    Zusatzaufgaben. ``offene_funksprueche`` sind die des Levels, in
    Spielreihenfolge. ``tempo`` ist der Faktor aus
    :func:`game.zusatzaufgaben.tempofaktor` – mit ihm rechnet die Vorrang-Regel
    nicht im Mittel, sondern im Tempo dieses Kindes.

    Zuerst die Übungen, dann die Funksprüche – ausser die Zeit wird knapp:

    >>> from content import story
    >>> naechster_schritt(0, story.FUNKSPRUECHE_NACH_LEVEL[1], 900).art
    'uebung'
    >>> naechster_schritt(2, story.FUNKSPRUECHE_NACH_LEVEL[1], 900).funkspruch.kennung
    'erster_ruf'
    >>> naechster_schritt(0, story.FUNKSPRUECHE_NACH_LEVEL[1], 300).funkspruch.kennung
    'erster_ruf'
    >>> naechster_schritt(2, (), 900).art
    'levelende'
    """
    zeit_fuer_uebung = _zusatzaufgaben.zeit_reicht_noch(verbleibende_sekunden, offene_funksprueche, tempo)
    if zeit_fuer_uebung and erledigte_uebungen < BASIS_UEBUNGEN_JE_LEVEL:
        return Schritt(SCHRITT_UEBUNG)
    # Ob eine Zusatzaufgabe fällig ist, hat die Spiellogik schon entschieden –
    # samt Restzeit und Obergrenze (game/zusatzaufgaben.py).
    if zeit_fuer_uebung and zusatzaufgabe_faellig:
        return Schritt(SCHRITT_ZUSATZAUFGABE)
    if offene_funksprueche:
        return Schritt(SCHRITT_FUNKSPRUCH, offene_funksprueche[0])
    return Schritt(SCHRITT_LEVELENDE)
