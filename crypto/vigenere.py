"""Vigenère-Verschlüsselung – Level 3 des Spiels.

Was das Verfahren macht
───────────────────────
Caesar verschiebt jeden Buchstaben um *dieselbe* Zahl. Vigenère verschiebt
jeden Buchstaben um eine *andere* Zahl: Über die Nachricht wird ein
**Schlüsselwort** gelegt und so oft wiederholt, bis es genauso lang ist wie
die Nachricht. Jeder Schlüsselbuchstabe liefert die Verschiebung für genau
den Buchstaben, der unter ihm steht (A = 0 Stellen, B = 1 Stelle, … Z = 25).

    Nachricht  H   U   N   D
    Schlüssel  R   O   T   R
    Ergebnis   Y   I   G   U

Im Handbuch wird das nicht als Rechnung, sondern über das Vigenère-Quadrat
erklärt: Zeile = Schlüsselbuchstabe, Spalte = Nachrichtenbuchstabe. Beides
ist dasselbe, denn im Quadrat steht in Zeile *k* und Spalte *m* der Buchstabe
mit dem Index ``(k + m) % 26``. Dieses Modul rechnet, ``crypto.vigenere_quadrat``
baut die zugehörige Nachschlagetabelle für die Anzeige – beide müssen
zwangsläufig dieselben Ergebnisse liefern.

Worauf die UI sich verlassen darf
─────────────────────────────────
* Reine Funktionen: Text rein, Text raus. Kein Zustand, keine Ausgabe, kein
  ``tkinter``. Der Rückgabewert hängt nur von den Argumenten ab.
* Ein- und Ausgabe folgen der Textkonvention aus :mod:`crypto.normalize`.
  Eingaben werden selbst normalisiert – die UI darf also ruhig "hund" oder
  "Hallo, hört mich jemand?" hereinreichen.
* **Leerzeichen bleiben an derselben Stelle stehen** (Regel 3). Klartext und
  Geheimtext haben deshalb dieselbe Länge und dieselben Wortgrenzen.
* **Regel 7 – der kritische Punkt:** Ein Leerzeichen zählt den Schlüsselindex
  *nicht* weiter. Der Schlüssel rückt ausschließlich bei Buchstaben eine
  Stelle vor. Ohne diese Regel würde ein mehrwortiger Satz anders
  verschlüsselt, als die Schülerinnen und Schüler ihn von Hand mit der
  Handbuch-Tabelle "Nachricht / Schlüssel" ausrechnen – und das
  Fehlerhandling würde eine richtige Lösung als Fehlversuch werten.
* :func:`schluessel_ausrichten` liefert genau die zweite Zeile jener
  Handbuch-Tabelle. Die UI kann Nachricht und ausgerichteten Schlüssel Zeichen
  für Zeichen untereinander setzen, ohne die Wiederhol-Logik nachzubauen.
* :func:`entschluesseln` ist die exakte Umkehrung von :func:`verschluesseln`
  (Rundlauf), solange derselbe Schlüssel benutzt wird.

Fehlerfälle: Ein unbrauchbares Schlüsselwort (leer, ohne Buchstaben oder
mehrteilig) löst einen ``ValueError`` mit deutscher Meldung aus. Das ist ein
Programmierfehler beim Zusammenstellen der Aufgabe, kein Spielerfehler – die
Schlüsselwörter kommen aus einer festen Liste (ROT, WEG, TAG).
"""

from .normalize import (
    LEERZEICHEN,
    buchstabe_zu_index,
    index_zu_buchstabe,
    normalisieren,
)

# Vorzeichen der Verschiebung. Verschlüsseln geht im Alphabet vorwärts,
# Entschlüsseln denselben Weg zurück – mehr Unterschied gibt es nicht,
# deshalb teilen sich beide Richtungen die Funktion _anwenden().
_VORWAERTS = +1
_RUECKWAERTS = -1


def _schluessel_pruefen(schluesselwort):
    """Normalisiert das Schlüsselwort und prüft es auf Brauchbarkeit.

    Rückgabe ist das normalisierte Schlüsselwort in Großbuchstaben.

    >>> _schluessel_pruefen("rot")
    'ROT'
    >>> _schluessel_pruefen("Weg!")
    'WEG'
    """
    if not isinstance(schluesselwort, str):
        raise TypeError(
            "Das Schlüsselwort muss ein Text (str) sein, "
            f"nicht {type(schluesselwort).__name__}."
        )

    sauber = normalisieren(schluesselwort)

    if not sauber:
        raise ValueError(
            "Das Schlüsselwort enthält keinen einzigen Buchstaben von A bis Z."
        )
    if LEERZEICHEN in sauber:
        raise ValueError(
            f"Das Schlüsselwort darf keine Leerzeichen enthalten: '{sauber}'. "
            "Erlaubt ist ein einzelnes Wort aus A bis Z, zum Beispiel 'ROT'."
        )
    return sauber


def _anwenden(text, schluesselwort, vorzeichen):
    """Verschiebt jeden Buchstaben um seinen Schlüsselbuchstaben.

    ``vorzeichen`` ist ``+1`` zum Verschlüsseln und ``-1`` zum Entschlüsseln.
    Hier steckt Regel 7: ``schluessel_stelle`` wird nur dann erhöht, wenn
    tatsächlich ein Buchstabe verarbeitet wurde.
    """
    schluessel = _schluessel_pruefen(schluesselwort)
    klartext = normalisieren(text)

    ergebnis = []
    schluessel_stelle = 0

    for zeichen in klartext:
        if zeichen == LEERZEICHEN:
            # Regel 3: das Leerzeichen bleibt stehen.
            # Regel 7: der Schlüsselindex rückt dabei NICHT vor.
            ergebnis.append(LEERZEICHEN)
            continue

        verschiebung = buchstabe_zu_index(
            schluessel[schluessel_stelle % len(schluessel)]
        )
        neuer_index = buchstabe_zu_index(zeichen) + vorzeichen * verschiebung
        # index_zu_buchstabe() rechnet modulo 26 und regelt damit Z→A und A→Z.
        ergebnis.append(index_zu_buchstabe(neuer_index))
        schluessel_stelle += 1

    return "".join(ergebnis)


def verschluesseln(text, schluesselwort):
    """Verschlüsselt ``text`` mit dem ``schluesselwort`` nach Vigenère.

    Das Handbuch-Beispiel von Seite 3 (Zeile "R", Spalte "H" → "Y" usw.):

    >>> verschluesseln("HUND", "ROT")
    'YIGU'

    Kleinschreibung, Satzzeichen und Umlaute werden vorher still normalisiert:

    >>> verschluesseln("hund", "rot")
    'YIGU'

    Mehrwortiger Fall – der Prüfstein für Regel 7. Das Leerzeichen zählt den
    Schlüssel nicht weiter, die Schlüsselfolge lautet also R O T R O (Leer) T R:

    >>> verschluesseln("ALLES OK", "ROT")
    'RZEVG HB'

    Ein unbrauchbares Schlüsselwort ist ein Fehler, kein stiller Sonderfall:

    >>> verschluesseln("HUND", "RO T")
    Traceback (most recent call last):
        ...
    ValueError: Das Schlüsselwort darf keine Leerzeichen enthalten: 'RO T'. Erlaubt ist ein einzelnes Wort aus A bis Z, zum Beispiel 'ROT'.
    """
    return _anwenden(text, schluesselwort, _VORWAERTS)


def entschluesseln(text, schluesselwort):
    """Entschlüsselt ``text`` mit dem ``schluesselwort`` nach Vigenère.

    Genaue Umkehrung von :func:`verschluesseln` – dieselbe Verschiebung, nur
    im Alphabet rückwärts.

    >>> entschluesseln("YIGU", "ROT")
    'HUND'

    Auch der mehrwortige Fall läuft sauber zurück:

    >>> entschluesseln("RZEVG HB", "ROT")
    'ALLES OK'

    Rundlauf über einen längeren Übungssatz aus dem Handbuch:

    >>> geheim = verschluesseln("BRAUCHE SOFORT HILFE", "WEG")
    >>> geheim
    'XVGQGNA WUBSXP LOHJK'
    >>> entschluesseln(geheim, "WEG")
    'BRAUCHE SOFORT HILFE'
    """
    return _anwenden(text, schluesselwort, _RUECKWAERTS)


def schluessel_ausrichten(text, schluesselwort):
    """Legt das Schlüsselwort über den Text und gibt diese Zeile zurück.

    Das ist die untere Zeile der Handbuch-Tabelle "Nachricht / Schlüssel".
    Das Ergebnis ist genauso lang wie der normalisierte Text und hat die
    Leerzeichen an denselben Stellen – die UI (Phase 6) kann beide Zeilen
    also einfach untereinander setzen.

    >>> schluessel_ausrichten("HUND", "ROT")
    'ROTR'

    Nach Regel 7 überspringt der Schlüssel das Leerzeichen, statt es
    mitzuzählen – hier folgt auf das O also das T und nicht das R:

    >>> schluessel_ausrichten("ALLES OK", "ROT")
    'ROTRO TR'

    Zusammen mit dem normalisierten Text ergibt das die Handbuch-Tabelle:

    >>> normalisieren("Alles ok!")
    'ALLES OK'
    >>> schluessel_ausrichten("Alles ok!", "ROT")
    'ROTRO TR'
    """
    schluessel = _schluessel_pruefen(schluesselwort)
    klartext = normalisieren(text)

    ergebnis = []
    schluessel_stelle = 0

    for zeichen in klartext:
        if zeichen == LEERZEICHEN:
            ergebnis.append(LEERZEICHEN)
            continue
        ergebnis.append(schluessel[schluessel_stelle % len(schluessel)])
        schluessel_stelle += 1

    return "".join(ergebnis)
