"""Caesar-Verschiebung – das erste und einfachste Verfahren des Spiels.

Das Verfahren
─────────────
Jeder Buchstabe wandert um eine feste Anzahl Stellen im Alphabet nach vorn.
Bei Schlüssel 3 wird aus A ein D, aus H ein K und so weiter. Hinter Z geht es
wieder bei A weiter – das Alphabet ist ein geschlossener Ring. Entschlüsseln
ist dieselbe Rechnung rückwärts, also eine Verschiebung um ``-schluessel``.

Durchgerechnetes Handbuch-Beispiel (dokumentation/Handbuchtexte.md):

    Buchstabe       | H | U | N | D
    verschoben um 3 | K | X | Q | G   ->  HUND wird zu KXQG

Worauf die UI sich verlassen darf
─────────────────────────────────
* Beide Funktionen sind rein: Text rein, Text raus. Kein globaler Zustand,
  keine Ausgabe auf der Konsole, kein GUI-Code. Derselbe Aufruf liefert
  immer dasselbe Ergebnis und lässt sich beliebig oft wiederholen.
* Das Ergebnis ist immer schon normalisiert (siehe ``crypto.normalize``):
  Großbuchstaben, nur A–Z und einfache Leerzeichen. Die UI kann den
  Rückgabewert also unverändert anzeigen. Damit der Aufgabentext zum
  Ergebnis passt, sollte sie auch den Klartext über ``normalisieren()``
  schicken, bevor sie ihn anzeigt.
* Leerzeichen bleiben an Ort und Stelle stehen (Textkonvention Regel 3), sie
  werden nicht mitverschoben und nicht entfernt. Die Wortgrenzen im
  Geheimtext stimmen deshalb genau mit denen im Klartext überein.
* ``entschluesseln(verschluesseln(t, s), s)`` ergibt für jeden Text ``t``
  und jeden Schlüssel ``s`` wieder den normalisierten Text ``t``. Die UI
  kann die Musterlösung eines Rätsels also aus dem Klartext berechnen,
  statt sie fest im Inhalt zu hinterlegen.
* Der Schlüssel darf beliebig groß und auch negativ sein; 25, -1 und 51
  verhalten sich identisch. Die UI muss den Wert eines Eingabefelds also
  nicht vorher in den Bereich 0–25 zurückrechnen.
"""

from .normalize import (
    LEERZEICHEN,
    buchstabe_zu_index,
    index_zu_buchstabe,
    normalisieren,
)


def _pruefe_schluessel(schluessel):
    """Stellt sicher, dass der Schlüssel eine ganze Zahl ist.

    ``bool`` ist in Python ein Sonderfall von ``int``; ``True`` würde als
    Verschiebung um 1 durchgehen. Das ist fast immer ein Programmierfehler
    im aufrufenden Code und wird deshalb hier abgefangen.

    >>> _pruefe_schluessel(3)
    >>> _pruefe_schluessel("3")
    Traceback (most recent call last):
        ...
    TypeError: Der Caesar-Schlüssel muss eine ganze Zahl (int) sein, nicht str.
    >>> _pruefe_schluessel(True)
    Traceback (most recent call last):
        ...
    TypeError: Der Caesar-Schlüssel muss eine ganze Zahl (int) sein, nicht bool.
    """
    if isinstance(schluessel, bool) or not isinstance(schluessel, int):
        raise TypeError(
            "Der Caesar-Schlüssel muss eine ganze Zahl (int) sein, "
            f"nicht {type(schluessel).__name__}."
        )


def verschluesseln(text, schluessel):
    """Verschiebt jeden Buchstaben um ``schluessel`` Stellen nach vorn.

    Der Text wird zuerst normalisiert; Leerzeichen bleiben unverschoben
    stehen. Der Umbruch von Z nach A entsteht in ``index_zu_buchstabe()``,
    das modulo 26 rechnet.

    >>> verschluesseln("HUND", 3)
    'KXQG'
    >>> verschluesseln("Z", 1)
    'A'
    >>> verschluesseln("A", -1)
    'Z'

    Leerzeichen bleiben stehen, Satzzeichen fallen beim Normalisieren weg:

    >>> verschluesseln("Zeit wird knapp!", 3)
    'CHLW ZLUG NQDSS'

    Schlüssel 0 und 26 geben den Text unverändert zurück, ein zu großer
    Schlüssel wird automatisch umgebrochen (51 wirkt wie -1):

    >>> verschluesseln("HUND", 0), verschluesseln("HUND", 26)
    ('HUND', 'HUND')
    >>> verschluesseln("HUND", 29) == verschluesseln("HUND", 3)
    True
    >>> verschluesseln("A", 51)
    'Z'

    Ein Schlüssel, der keine ganze Zahl ist, ist ein Fehler:

    >>> verschluesseln("HUND", 3.0)
    Traceback (most recent call last):
        ...
    TypeError: Der Caesar-Schlüssel muss eine ganze Zahl (int) sein, nicht float.
    """
    _pruefe_schluessel(schluessel)

    geheimtext = []
    for zeichen in normalisieren(text):
        if zeichen == LEERZEICHEN:
            # Regel 3: Wortgrenzen bleiben sichtbar.
            geheimtext.append(LEERZEICHEN)
        else:
            verschoben = buchstabe_zu_index(zeichen) + schluessel
            geheimtext.append(index_zu_buchstabe(verschoben))
    return "".join(geheimtext)


def entschluesseln(text, schluessel):
    """Macht ``verschluesseln()`` rückgängig – dieselbe Verschiebung zurück.

    >>> entschluesseln("KXQG", 3)
    'HUND'
    >>> entschluesseln("A", 1)
    'Z'
    >>> entschluesseln("Z", -1)
    'A'

    Ver- und Entschlüsseln heben einander für jeden Schlüssel auf:

    >>> entschluesseln(verschluesseln("Zeit wird knapp!", 7), 7)
    'ZEIT WIRD KNAPP'
    """
    _pruefe_schluessel(schluessel)
    return verschluesseln(text, -schluessel)
