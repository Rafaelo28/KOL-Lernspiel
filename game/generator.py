"""Der Aufgaben-Generator (Arbeitsplan 3.2).

Er baut aus dem Material in ``content/`` fertige :class:`game.aufgabe.Aufgabe`
-Objekte: für die Handbuch-Übungen zufällig, für die echten Funksprüche fest
nach Vorlage.

Was der Arbeitsplan verlangt
────────────────────────────
* zufälliger Satz aus dem Übungspool – alle drei Level teilen sich einen
  (``content/uebungen.py``),
* zufällige Richtung (ver- oder entschlüsseln), aber nie zweimal dieselbe
  hintereinander – siehe unten,
* bei "entschlüsseln" wird der Text vorher selbst verschlüsselt und **der**
  angezeigt,
* bei Level 3 zusätzlich ein zufälliges Schlüsselwort,
* kein Text zweimal hintereinander im selben Level.

Wie der Pool auf die Level verteilt wird
────────────────────────────────────────
Alle drei Level üben mit denselben achtzehn Sätzen. Zöge jedes Level frei daraus,
käme ein Satz, den jemand in Level 1 verschlüsselt hat, in Level 2 womöglich
zum Entschlüsseln wieder – und liesse sich aus dem Gedächtnis eintippen. Die
Zeit dafür stünde im Log, als wäre gerechnet worden.

Deshalb wird der Pool einmal je Durchlauf gemischt und in drei Abschnitte
geteilt – bei achtzehn Sätzen je sechs. Jedes Level beginnt am Anfang seines
Abschnitts und geht von dort der Reihe nach weiter, am Ende des Pools wieder
von vorn. Die sechs Übungen eines Levels kommen so in keinem anderen Level
vor, und sechs sind genau so viele, wie ein Level überhaupt stellen kann
(zwei Pflichtübungen und alle Zusatzaufgaben). Zweimal hintereinander kommt
derselbe Satz nie.

Warum der Zufall von aussen kommt
─────────────────────────────────
:class:`Aufgabengenerator` bekommt seine Zufallsquelle übergeben, statt das
globale ``random`` zu benutzen. Zwei Gründe:

* Aufgabe 3.3 verlangt einen protokollierbaren Seed – nur so lässt sich später
  rekonstruieren, wer welche Aufgaben bekommen hat.
* Tests werden dadurch wiederholbar, ohne am globalen Zustand zu drehen.

Im Spiel wird eine :class:`game.zufallsquelle.Zufallsquelle` übergeben. Sie
führt je Level einen eigenen Zufallsstrom, damit zur Rekonstruktion einer
Übung der Seed und ihre Nummer *unter den Übungen dieses Levels* genügen –
unabhängig davon, wie viele Zusatzaufgaben in den Leveln davor angefallen
sind. Auch die Mischung des Pools hängt nur am Seed. Diese Nummer steht in der Kennung (``uebung_l2_3`` ist die dritte Übung
in Level 2); :func:`uebung_nachbauen` liest sie dort heraus.

Für kleine Prüfungen genügt auch eine schlichte ``random.Random``-Instanz;
dann teilen sich alle Level einen Strom, und aus ihm wird auch der Pool
gemischt.

Warum die Richtung nicht frei gewürfelt wird
────────────────────────────────────────────
Die Unterlagen widersprechen sich an dieser Stelle. ``Konzept_Spiel.md`` und
die Zusammenfassung verlangen pro Level ausdrücklich "2 Aufgaben
(1× verschlüsseln, 1× entschlüsseln)"; ``Handbuchtexte.md`` und der
Arbeitsplan sagen nur "zufällig entscheiden". Frei gewürfelt kämen in einem
von vier Fällen zweimal dieselbe Richtung heraus – dann hätten die Kinder das
Entschlüsseln in diesem Level nie geübt, und das ist ein Lernziel aus
Anhang A1.

Aufgelöst wird das wie bei den Übungstexten: Welche Richtung zuerst kommt,
entscheidet der Zufall, aber zweimal hintereinander dieselbe gibt es nicht.
Bei den vorgesehenen zwei Übungen pro Level ergibt das genau einmal jede
Richtung, in zufälliger Reihenfolge.

Warum Level 1 einen Schlüssel gezogen bekommt und Level 2 nicht
───────────────────────────────────────────────────────────────
Bei Caesar ist der Schlüssel eine Zahl, bei Vigenère ein Wort – beide wechseln,
damit die Aufgabe nicht vorhersehbar wird. Bei der monoalphabetischen
Substitution ist die Zuordnungstabelle der Schlüssel, und die ist im Handbuch
fest vorgegeben (der Tastatur-Trick). Dort gibt es also nichts zu ziehen.

Jede erzeugte Aufgabe läuft durch :func:`game.aufgabe.pruefe_aufgabe`. Das
kostet nichts und schliesst aus, dass eine Aufgabe ins Spiel gelangt, deren
Lösung nicht aus ihrem Anzeigetext folgt.
"""

import random

from content import story as _story
from content import uebungen, verfahren as _verfahren
from crypto.normalize import LEERZEICHEN, ohne_leerzeichen as _ohne_leerzeichen
from game.aufgabe import (
    ENTSCHLUESSELN,
    QUELLE_FUNKSPRUCH,
    QUELLE_UEBUNG,
    VERSCHLUESSELN,
    Aufgabe,
    anwenden,
    pruefe_aufgabe,
)
from game.zufallsquelle import Zufallsquelle

#: Beide Richtungen sind gleich wahrscheinlich. Das Handbuch verlangt
#: ausdrücklich, dass pro Aufgabe einmal ver- und einmal entschlüsselt wird –
#: welche Richtung wann drankommt, entscheidet der Zufall.
RICHTUNGEN = (VERSCHLUESSELN, ENTSCHLUESSELN)


def _schluessel_ziehen(level, zufall):
    """Zieht den Schlüssel für ein Level, oder ``None`` bei der Substitution."""
    if level == 1:
        return zufall.choice(uebungen.CAESAR_SCHLUESSEL)
    if level == 3:
        return zufall.choice(uebungen.VIGENERE_SCHLUESSELWOERTER)
    return None


class Aufgabengenerator:
    """Erzeugt Übungsaufgaben und merkt sich, was zuletzt drankam.

    >>> generator = Aufgabengenerator(random.Random(42))
    >>> aufgabe = generator.naechste_uebung(1)
    >>> aufgabe.level, aufgabe.verfahren
    (1, 'caesar')
    >>> aufgabe.richtung in RICHTUNGEN
    True

    Derselbe Seed ergibt denselben Ablauf – das ist die Grundlage für
    Aufgabe 3.3:

    >>> erste = Aufgabengenerator(random.Random(1)).naechste_uebung(2)
    >>> zweite = Aufgabengenerator(random.Random(1)).naechste_uebung(2)
    >>> erste == zweite
    True
    """

    def __init__(self, zufall=None):
        """Nimmt die Zufallsquelle entgegen, aus der später alle Aufgaben gezogen werden.

        Erlaubt ist eine :class:`~game.zufallsquelle.Zufallsquelle` – so
        läuft es im Spiel, damit sich jede Aufgabe aus dem Seed
        rekonstruieren lässt – oder ein einfaches ``random.Random``, das
        ältere Tests benutzen. Ohne Angabe wird eine neue Zufallsquelle
        gezogen.

        Gemischt wird hier noch nichts: Die Reihenfolge des Übungspools
        entsteht erst, wenn die erste Übung gebraucht wird.
        """
        if zufall is None:
            zufall = Zufallsquelle.neu()
        self._quelle = zufall if isinstance(zufall, Zufallsquelle) else None
        self._gemeinsamer_strom = None if self._quelle else zufall
        self._reihenfolge = None
        # Zuletzt gestellte Richtung je Level – für "nicht zweimal
        # hintereinander dieselbe".
        self._zuletzt_richtung = {}
        self._zaehler = {}

    def naechste_uebung(self, level, zusatzaufgabe=False):
        """Baut die nächste Übungsaufgabe für ``level``.

        ``zusatzaufgabe`` markiert Aufgaben, die aus dem adaptiven Timer
        entstanden sind (Arbeitsplan 5.4). Für den Inhalt macht es keinen
        Unterschied – die Extraaufgabe kommt aus demselben Pool –, aber im Log
        müssen sich beide unterscheiden lassen.
        """
        if level not in _verfahren.VERFAHREN_NACH_LEVEL:
            raise ValueError(f"Level {level!r} gibt es nicht; erlaubt sind 1, 2, 3.")

        zufall = self._strom(level)
        text = self._text_ziehen(level)
        richtung = self._richtung_ziehen(level, zufall)
        schluessel = _schluessel_ziehen(level, zufall)
        verfahren = _verfahren.VERFAHREN_NACH_LEVEL[level]

        # Bei "entschlüsseln" ist der Geheimtext das, was angezeigt wird –
        # der Klartext ist dann die Lösung.
        if richtung == ENTSCHLUESSELN:
            anzeigetext = anwenden(verfahren, VERSCHLUESSELN, text, schluessel)
        else:
            anzeigetext = text
        loesung = anwenden(verfahren, richtung, anzeigetext, schluessel)

        self._zaehler[level] = self._zaehler.get(level, 0) + 1
        aufgabe = Aufgabe(
            kennung=f"uebung_l{level}_{self._zaehler[level]}",
            level=level,
            verfahren=verfahren,
            richtung=richtung,
            schluessel=schluessel,
            anzeigetext=anzeigetext,
            loesung=loesung,
            quelle=QUELLE_UEBUNG,
            zusatzaufgabe=zusatzaufgabe,
        )
        pruefe_aufgabe(aufgabe)
        return aufgabe

    def _strom(self, level):
        """Der Zufallsstrom für dieses Level."""
        if self._quelle is not None:
            return self._quelle.fuer_level(level)
        return self._gemeinsamer_strom

    def _text_ziehen(self, level):
        """Der Text der nächsten Übung dieses Levels: der nächste in seinem Abschnitt des gemischten Pools."""
        if self._reihenfolge is None:
            if self._quelle is not None:
                self._reihenfolge = self._quelle.gemischt(uebungen.UEBUNGSTEXTE)
            else:
                self._reihenfolge = tuple(self._gemeinsamer_strom.sample(uebungen.UEBUNGSTEXTE,
                                                                         len(uebungen.UEBUNGSTEXTE)))
        stelle = abschnittsanfang(level, len(self._reihenfolge)) + self._zaehler.get(level, 0)
        return self._reihenfolge[stelle % len(self._reihenfolge)]

    def _richtung_ziehen(self, level, zufall):
        """Zieht die Richtung, aber nie zweimal hintereinander dieselbe."""
        zuletzt = self._zuletzt_richtung.get(level)
        moeglich = [r for r in RICHTUNGEN if r != zuletzt] or list(RICHTUNGEN)
        gezogen = zufall.choice(moeglich)
        self._zuletzt_richtung[level] = gezogen
        return gezogen



def abschnittsanfang(level, poolgroesse):
    """Wo im gemischten Pool der Abschnitt dieses Levels beginnt.

    Der Pool wird so gleichmässig wie möglich auf die Level verteilt; was
    übrig bleibt, bekommen die ersten Level – dort gibt es die meisten
    Zusatzaufgaben, weil die Verfahren noch schnell gehen.

    >>> [abschnittsanfang(level, 10) for level in (1, 2, 3)]
    [0, 4, 7]
    """
    groesse, rest = divmod(poolgroesse, len(_verfahren.VERFAHREN_NACH_LEVEL))
    return (level - 1) * groesse + min(level - 1, rest)


def aufgabe_aus_funkspruch(funkspruch, initialen):
    """Baut die Aufgabe zu einem echten Funkspruch (für Phase 7).

    Kein Zufall im Spiel: Wortlaut, Schlüssel und Teilaufgabe stehen fest in
    ``content/story.py``. Zu tun ist nur, die Richtung zu übersetzen und den
    Anzeigetext auf die richtige Seite zu stellen.

    * **Senden** – angezeigt wird der Klartext, eingegeben der Geheimtext.
      Der Geheimtext darf dabei nirgends zu sehen sein, er ist die Lösung.
    * **Empfangen** – angezeigt wird der Geheimtext, eingegeben der Klartext.

    ``initialen`` wird nach der Textkonvention aufbereitet und von Leerzeichen
    befreit – aus "v. m." wird also "VM". Sie stehen im Funkspruch und werden
    mitverschlüsselt; eine unsaubere Schreibweise soll dort nicht
    durchschlagen.

    >>> from content import story
    >>> a = aufgabe_aus_funkspruch(story.FUNKSPRUCH_BOB_ZWEITE_ANTWORT, "VM")
    >>> a.richtung, a.loesung
    ('entschluesseln', 'VERSTANDEN HILFE IST UNTERWEGS')
    >>> a.quelle
    'funkspruch'
    """
    # ohne_leerzeichen statt normalisieren: Initialen sind ein einzelnes
    # Kürzel, "v. m." soll zu "VM" werden und nicht zu "V M".
    initialen = _ohne_leerzeichen(initialen)
    if not initialen:
        raise ValueError(
            "Die Initialen dürfen nicht leer sein – sie unterschreiben den "
            "Funkspruch und werden mitverschlüsselt."
        )
    klartext = funkspruch.klartext.format(initialen=initialen)
    richtung = (
        VERSCHLUESSELN if funkspruch.richtung == _story.SENDEN else ENTSCHLUESSELN
    )
    verfahren = funkspruch.verfahren
    schluessel = funkspruch.schluessel

    if richtung == ENTSCHLUESSELN:
        anzeigetext = anwenden(verfahren, VERSCHLUESSELN, klartext, schluessel)
    else:
        anzeigetext = klartext
    ganze_loesung = anwenden(verfahren, richtung, anzeigetext, schluessel)

    if funkspruch.selbst_zu_loesen:
        # Beim Entschlüsseln ist der selbst zu lösende Anfang schon Klartext,
        # beim Verschlüsseln muss er erst in den Geheimtext übersetzt werden.
        if richtung == ENTSCHLUESSELN:
            teil = funkspruch.selbst_zu_loesen
        else:
            teil = anwenden(
                verfahren, VERSCHLUESSELN, funkspruch.selbst_zu_loesen, schluessel
            )
        rest = ganze_loesung[len(teil):].lstrip(LEERZEICHEN)
        beschriftung = _story.BESCHRIFTUNG_REST[funkspruch.richtung]
        weiterrechnen_text = funkspruch.weiterrechnen
    else:
        teil, rest = ganze_loesung, ""
        beschriftung, weiterrechnen_text = "", ""

    aufgabe = Aufgabe(
        kennung=funkspruch.kennung,
        level=funkspruch.level,
        verfahren=verfahren,
        richtung=richtung,
        schluessel=schluessel,
        anzeigetext=anzeigetext,
        loesung=teil,
        quelle=QUELLE_FUNKSPRUCH,
        rest_der_loesung=rest,
        knopf_beschriftung=beschriftung,
        weiterrechnen_text=weiterrechnen_text,
    )
    pruefe_aufgabe(aufgabe)
    return aufgabe


def wiederhole_uebungen(seed, level, anzahl):
    """Baut die ersten ``anzahl`` Übungsaufgaben eines Levels noch einmal nach.

    Das ist der eigentliche Zweck von Aufgabe 3.3: Aus dem Seed im Log und der
    Übungsnummer lässt sich später feststellen, welches Wort jemand bekommen
    hat – ohne den ganzen Durchlauf nachzuspielen. Gezählt werden dabei nur
    die Übungen; Funksprüche ziehen keinen Zufall. Für eine einzelne Logzeile
    ist :func:`uebung_nachbauen` bequemer.

    >>> aufgaben = wiederhole_uebungen(4711, 1, 2)
    >>> [a.anzeigetext for a in aufgaben] == [
    ...     a.anzeigetext for a in wiederhole_uebungen(4711, 1, 2)
    ... ]
    True
    """
    generator = Aufgabengenerator(Zufallsquelle(seed))
    return [generator.naechste_uebung(level) for _ in range(anzahl)]


def uebung_nachbauen(seed, kennung):
    """Baut die Übung zu einer Logzeile nach – aus Seed und Kennung.

    Die Kennung einer Übung trägt Level und Übungsnummer (``uebung_l2_3``).
    Die Spalte ``aufgabennummer`` im Log taugt dafür **nicht**: Sie zählt die
    Funksprüche mit, der Zufallsstrom aber nicht.

    Zusatzaufgaben lassen sich genauso nachbauen – sie kommen aus demselben
    Strom, das Merkmal selbst zieht keinen Zufall. Nur ``zusatzaufgabe``
    steht in der nachgebauten Aufgabe immer auf ``False``; das steht ja
    ohnehin in der Logzeile.

    >>> a = uebung_nachbauen(4711, "uebung_l1_2")
    >>> a.kennung == "uebung_l1_2", a == wiederhole_uebungen(4711, 1, 2)[1]
    (True, True)
    """
    teile = str(kennung).split("_")
    if (
        len(teile) != 3
        or teile[0] != "uebung"
        or not teile[1].startswith("l")
        or not teile[1][1:].isdecimal()
        or not teile[2].isdecimal()
        or int(teile[2]) < 1
    ):
        raise ValueError(
            f"{kennung!r} ist keine Übungskennung wie 'uebung_l2_3'. "
            "Funksprüche stehen fest in content/story.py und brauchen keinen Seed."
        )
    level, nummer = int(teile[1][1:]), int(teile[2])
    return wiederhole_uebungen(seed, level, nummer)[-1]
