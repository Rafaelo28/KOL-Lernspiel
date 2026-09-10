"""Adaptive Zusatzaufgaben (Arbeitsplan 5.4).

Wer eine Aufgabe deutlich schneller löst als erwartet, bekommt eine weitere
aus demselben Wortpool – damit die schnellen Kinder im festen Zeitfenster
nicht dasitzen und warten, während die langsamen noch rechnen.

Wie "erwartet" berechnet wird
─────────────────────────────
Nicht als Sekunden je Buchstabe. Jede Aufgabe hat eine **Grundzeit**, die
nichts mit ihrer Länge zu tun hat: die Aufgabe lesen, den Schlüssel
nachschlagen, das Eingabefeld anklicken, tippen, prüfen. Bei einem Wort mit
vier Buchstaben macht diese Grundzeit fast alles aus, bei einem Funkspruch mit
fünfundzwanzig fällt sie kaum ins Gewicht.

Ein reines "Sekunden je Buchstabe" würde deshalb systematisch danebenliegen:
Kurze Aufgaben sähen immer langsam aus, lange immer schnell – gemessen würde
am Ende die Länge der gezogenen Aufgabe, nicht das Tempo der Person.

Gerechnet wird darum mit einer Geraden::

    erwartet = GRUNDZEIT + BUCHSTABEN * SEKUNDEN_JE_BUCHSTABE

und "deutlich schneller" heisst: unter :data:`SCHNELL_WENN_UNTER_ANTEIL` davon.

Die Zahlen sind Schätzungen
───────────────────────────
Alle drei stehen an genau dieser Stelle und gehören im Pilotdurchlauf
(Arbeitsplan 8.2) nachgemessen: zwei, drei Personen spielen lassen, im Log die
Spalten ``sekunden`` und ``gerechnete_buchstaben`` gegeneinander auftragen und
die Gerade daran anpassen – ohne die Zeilen mit ``abgebrochen = ja``, dort ist
die Zeit keine Rechenzeit. Erst danach sind die Werte belastbar.

Warum es eine Obergrenze gibt
─────────────────────────────
:data:`HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL` begrenzt, wie viele Extraaufgaben
ein Level hergibt. Zwei Gründe:

* Der Übungspool hat zehn Texte. Nach ein paar Zusatzaufgaben wiederholen sie
  sich, und aus dem Üben wird stures Abarbeiten.
* Wäre die Schwelle nach dem Pilotdurchlauf versehentlich zu grosszügig
  gesetzt, liefe sonst eine Endlosschleife bis zum Zeitablauf – im Log stünden
  dann hundert Zeilen, die nichts aussagen, und die Person käme nie zum
  Funkspruch, der die Geschichte trägt.

Warum die Restzeit mitentscheidet
─────────────────────────────────
Projektregel 1: Zusatzaufgaben verlängern ein Zeitfenster nie. Eine Aufgabe
kurz vor Schluss zu stellen heisst, sie unfertig abzubrechen – das frustriert
und erzeugt eine Logzeile, die nur "Zeit war um" sagt.

Welcher Text als Zusatzaufgabe kommt, steht vorher nicht fest. Gerechnet wird
deshalb mit dem **längsten** Text im Pool des Levels, nicht mit der Aufgabe,
die gerade gelöst wurde: In Level 2 liegen zwischen dem kürzesten und dem
längsten Übungstext sieben gegen achtzehn Buchstaben.

Warum nur Übungen eine Zusatzaufgabe auslösen
─────────────────────────────────────────────
Die Zusammenfassung legt den Ablauf fest: "Übungsaufgaben (+ ggf.
Zusatzaufgaben) → echte Sendeaufgabe → Bobs Antwort". Zusatzaufgaben gehören
also in die Übungsphase und kommen "aus demselben Wortpool". Nach einem
Funkspruch hat die Geschichte schon begonnen – eine Handbuch-Übung zwischen
dem eigenen Ruf und Bobs Antwort risse sie auseinander.
"""

from content import uebungen as _uebungen
from crypto.normalize import ohne_leerzeichen as _ohne_leerzeichen
from game.aufgabe import QUELLE_UEBUNG

#: Feste Zeit je Aufgabe, unabhängig von ihrer Länge: lesen, Schlüssel
#: nachschlagen, Eingabefeld anklicken, tippen, prüfen. Schätzwert.
ERWARTETE_GRUNDZEIT_SEKUNDEN = 20.0

#: Zeit je Buchstabe, der von Hand gerechnet werden muss. Schätzwert.
ERWARTETE_SEKUNDEN_JE_BUCHSTABE = 4.0

#: Ab wann gilt jemand als "deutlich schneller"? Anteil der erwarteten Dauer.
SCHNELL_WENN_UNTER_ANTEIL = 0.6

#: So viele Zusatzaufgaben gibt es je Level höchstens.
HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL = 3

#: So viel Zeit muss im Level mindestens übrig sein, zusätzlich zu der Zeit,
#: die die Zusatzaufgabe voraussichtlich kostet.
MINDESTRESTZEIT_SEKUNDEN = 60.0


def erwartete_dauer(laenge_in_buchstaben):
    """Wie lange eine Aufgabe dieser Länge voraussichtlich dauert.

    >>> erwartete_dauer(4)
    36.0
    >>> erwartete_dauer(25)
    120.0
    """
    return (
        ERWARTETE_GRUNDZEIT_SEKUNDEN
        + laenge_in_buchstaben * ERWARTETE_SEKUNDEN_JE_BUCHSTABE
    )


def war_schnell(bearbeitung):
    """War diese Aufgabe deutlich schneller gelöst als erwartet?

    Nur eine wirklich **gelöste** Aufgabe zählt. Wer die Lösung angezeigt
    bekommen hat, war nicht schnell, auch wenn es kurz gedauert hat – und wer
    beim Zeitablauf abgebrochen wurde, erst recht nicht.
    """
    if bearbeitung.laeuft_noch:
        return False
    if not bearbeitung.geloest or bearbeitung.loesung_angezeigt:
        return False
    erwartet = erwartete_dauer(bearbeitung.gerechnete_buchstaben)
    return bearbeitung.benoetigte_sekunden < SCHNELL_WENN_UNTER_ANTEIL * erwartet


def laengste_uebung(level):
    """Die Buchstabenzahl des längsten Übungstextes eines Levels.

    >>> laengste_uebung(1)
    5
    """
    return max(
        len(_ohne_leerzeichen(text))
        for text in _uebungen.UEBUNGSTEXTE_NACH_LEVEL[level]
    )


def zeit_reicht_noch(level, verbleibende_sekunden):
    """Bleibt genug Zeit, damit eine Zusatzaufgabe in ``level`` noch Sinn ergibt?

    Gerechnet wird mit der **erwarteten** Dauer des längsten Textes im Pool,
    nicht mit dem eigenen Tempo: Sonst bekäme, wer besonders schnell war,
    noch kurz vor Schluss eine Aufgabe aufgedrückt. Und nicht mit der eben
    gelösten Aufgabe – welcher Text als Nächstes kommt, steht nicht fest.
    """
    noetig = erwartete_dauer(laengste_uebung(level))
    return verbleibende_sekunden >= noetig + MINDESTRESTZEIT_SEKUNDEN


def obergrenze_erreicht(bisherige_zusatzaufgaben):
    """Sind in diesem Level schon genug Extraaufgaben gestellt worden?"""
    return bisherige_zusatzaufgaben >= HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL


def ist_faellig(bearbeitung, verbleibende_sekunden, bisherige_zusatzaufgaben=0):
    """Soll nach dieser Aufgabe eine Zusatzaufgabe gestellt werden?

    Alle vier Bedingungen müssen stimmen: Es war eine Übung, sie war schnell
    genug gelöst, es bleibt genug Zeit, und die Obergrenze des Levels ist
    noch nicht erreicht.
    """
    if bearbeitung.aufgabe.quelle != QUELLE_UEBUNG:
        return False
    if obergrenze_erreicht(bisherige_zusatzaufgaben):
        return False
    return war_schnell(bearbeitung) and zeit_reicht_noch(
        bearbeitung.aufgabe.level, verbleibende_sekunden
    )
