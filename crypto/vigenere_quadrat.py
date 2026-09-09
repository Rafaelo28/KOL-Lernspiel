"""Das Vigenère-Quadrat – die Nachschlagetabelle aus dem Handbuch.

Was das Verfahren macht
───────────────────────
Das Vigenère-Quadrat ist die Papier-Variante der Vigenère-Verschlüsselung:
26 Zeilen mit je 26 Buchstaben, in denen man das Ergebnis *ablesen* kann,
statt es auszurechnen. Aufgebaut ist es so (Handbuch, Seite 3):

* **Zeile**  = Buchstabe des Schlüsselworts
* **Spalte** = Buchstabe der Nachricht (Klartext)
* Im Feld steht der Buchstabe mit dem Index ``(k + m) mod 26``, A = 0.

Verschlüsseln heißt damit: Zeile des Schlüsselbuchstabens und Spalte des
Nachrichtenbuchstabens suchen, im Kreuzungspunkt ablesen.
Entschlüsseln heißt: in der Zeile des Schlüsselbuchstabens den Geheim-
buchstaben suchen; der Spaltenkopf darüber ist der Klarbuchstabe.

Beispiel aus dem Handbuch: HUND + ROT → YIGU, weil (R, H) = Y, (O, U) = I,
(T, N) = G und (R, D) = U.

Worauf sich die UI verlassen darf
─────────────────────────────────
* :func:`erzeuge_quadrat` liefert **immer** 26 Listen zu je 26 einzelnen
  Großbuchstaben – ein sauberes Rechteck, aus dem sich in Aufgabe 6.7 ohne
  weitere Prüfungen ein Grid mit 26×26 Zellen bauen lässt.
* Zeilen und Spalten stehen in Alphabet-Reihenfolge. Die Zeilen- bzw.
  Spaltenbeschriftung ist deshalb schlicht ``ALPHABET`` aus
  :mod:`crypto.normalize`; Zeile 0 und Spalte 0 gehören zu "A".
* Der Rückgabewert ist bei jedem Aufruf frisch gebaut. Die UI darf ihn also
  gefahrlos umbauen (z. B. Beschriftungen einfügen), ohne dass ein anderer
  Aufrufer davon etwas merkt.
* Das Quadrat wird aus der Formel *erzeugt* und ist nirgends abgetippt –
  ein Tippfehler in einer der 676 Zellen ist damit ausgeschlossen.

Bewusst unabhängig von :mod:`crypto.vigenere`
─────────────────────────────────────────────
Dieses Modul importiert die Rechen-Variante **nicht**. Beide Wege – Formel
und Tabelle – stehen getrennt nebeneinander, damit ein Test in Phase 5
beweisen kann, dass sie für alle 676 Kombinationen dasselbe Ergebnis
liefern. Würde die Tabelle die Formel aufrufen, wäre dieser Test wertlos.

Leerzeichen kommen im Quadrat nicht vor: Es enthält nur A–Z. Regel 3 und
Regel 7 der Textkonvention (Leerzeichen stehen lassen, Schlüsselindex nicht
weiterzählen) sind Sache des aufrufenden Moduls.
"""

from .normalize import ALPHABET, buchstabe_zu_index, index_zu_buchstabe


def _index_pruefen(buchstabe, rolle):
    """Prüft eine Eingabe und gibt ihren Alphabet-Index zurück (A = 0).

    ``rolle`` ist die Bezeichnung für die Fehlermeldung, damit man ihr
    ansieht, *welcher* der beiden Buchstaben nicht gestimmt hat.

    Alles, was kein einzelner Buchstabe von A bis Z ist, führt zu einem
    ``ValueError`` – auch eine Zahl oder ein ganzes Wort. Das Quadrat kennt
    schlicht keine anderen Felder, deshalb ist das hier immer ein
    Wertproblem und nie eine bloße Typfrage.
    """
    if not isinstance(buchstabe, str) or len(buchstabe) != 1:
        raise ValueError(
            f"Als {rolle} wird genau ein Buchstabe von A bis Z erwartet, "
            f"nicht {buchstabe!r}."
        )
    try:
        return buchstabe_zu_index(buchstabe)
    except ValueError:
        raise ValueError(
            f"'{buchstabe}' ist als {rolle} nicht erlaubt – im Quadrat "
            f"stehen nur die Buchstaben A bis Z."
        ) from None


def erzeuge_quadrat():
    """Baut das vollständige Vigenère-Quadrat als Liste von Listen.

    Rückgabe: 26 Zeilen zu je 26 einzelnen Großbuchstaben.
    ``quadrat[k][m]`` ist das Feld in der Zeile des Schlüsselbuchstabens
    mit Index ``k`` und der Spalte des Nachrichtenbuchstabens mit Index
    ``m`` – also der Buchstabe mit dem Index ``(k + m) mod 26``.

    Zeile A (Index 0) ist das normale Alphabet, weil "A" für die
    Verschiebung 0 steht:

    >>> quadrat = erzeuge_quadrat()
    >>> "".join(quadrat[0])
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    Das Quadrat ist 26 mal 26 Felder groß:

    >>> len(quadrat), {len(zeile) for zeile in quadrat}
    (26, {26})

    Zeile R beginnt beim R und läuft hinten wieder bei A weiter; das Feld
    (Zeile R, Spalte H) aus dem Handbuch ist ein Y:

    >>> "".join(quadrat[buchstabe_zu_index("R")])
    'RSTUVWXYZABCDEFGHIJKLMNOPQ'
    >>> quadrat[buchstabe_zu_index("R")][buchstabe_zu_index("H")]
    'Y'

    Jeder Aufruf liefert ein eigenes Quadrat – die UI darf ihres umbauen:

    >>> erzeuge_quadrat() is not erzeuge_quadrat()
    True
    """
    # index_zu_buchstabe() rechnet selbst modulo 26 und regelt damit den
    # Umbruch Z→A. Deshalb steht hier nirgends eine eigene Modulo-Rechnung.
    return [
        [index_zu_buchstabe(zeile + spalte) for spalte in range(len(ALPHABET))]
        for zeile in range(len(ALPHABET))
    ]


def verschluesselter_buchstabe(schluesselbuchstabe, klarbuchstabe):
    """Liest den Kreuzungspunkt aus Zeile und Spalte ab (Verschlüsseln).

    Das ist genau der Handgriff aus dem Handbuch: Zeile des Schlüssel-
    buchstabens, Spalte des Nachrichtenbuchstabens, Feld ablesen.

    >>> verschluesselter_buchstabe("R", "H")
    'Y'

    Die weiteren Schritte des Beispiels HUND + ROT → YIGU:

    >>> "".join(verschluesselter_buchstabe(s, k)
    ...         for s, k in zip("ROTR", "HUND"))
    'YIGU'

    Klein geschriebene Eingaben sind erlaubt (Regel 1 der Textkonvention):

    >>> verschluesselter_buchstabe("r", "h")
    'Y'

    Alles andere wird abgelehnt:

    >>> verschluesselter_buchstabe("R", " ")
    Traceback (most recent call last):
        ...
    ValueError: ' ' ist als Nachrichtenbuchstabe nicht erlaubt – im Quadrat stehen nur die Buchstaben A bis Z.
    """
    zeile = _index_pruefen(schluesselbuchstabe, "Schlüsselbuchstabe")
    spalte = _index_pruefen(klarbuchstabe, "Nachrichtenbuchstabe")
    # Bewusst über das erzeugte Quadrat und nicht über die Formel: So ist
    # abgesichert, dass die Anzeige und dieses Ergebnis dieselbe Quelle haben.
    return erzeuge_quadrat()[zeile][spalte]


def klarbuchstabe_finden(schluesselbuchstabe, geheimbuchstabe):
    """Sucht den Geheimbuchstaben in einer Zeile und gibt den Spaltenkopf zurück.

    So entschlüsselt das Handbuch: In der Zeile des Schlüsselbuchstabens
    den Geheimbuchstaben suchen; die Spalte, in der er steht, nennt den
    ursprünglichen Buchstaben.

    >>> klarbuchstabe_finden("R", "Y")
    'H'

    Das ganze Beispiel YIGU + ROT → HUND:

    >>> "".join(klarbuchstabe_finden(s, g)
    ...         for s, g in zip("ROTR", "YIGU"))
    'HUND'

    Verschlüsseln und Entschlüsseln heben einander auf:

    >>> klarbuchstabe_finden("T", verschluesselter_buchstabe("T", "N"))
    'N'

    Klein geschriebene Eingaben sind erlaubt, alles andere nicht:

    >>> klarbuchstabe_finden("r", "y")
    'H'
    >>> klarbuchstabe_finden("4", "Y")
    Traceback (most recent call last):
        ...
    ValueError: '4' ist als Schlüsselbuchstabe nicht erlaubt – im Quadrat stehen nur die Buchstaben A bis Z.
    """
    zeile_index = _index_pruefen(schluesselbuchstabe, "Schlüsselbuchstabe")
    gesucht = _index_pruefen(geheimbuchstabe, "Geheimbuchstabe")

    zeile = erzeuge_quadrat()[zeile_index]
    # Jede Zeile enthält alle 26 Buchstaben genau einmal, die Suche kann
    # also nicht scheitern. Die Zeile wird trotzdem wirklich durchsucht –
    # das ist der Handgriff, den die Spielenden auf Papier machen.
    return ALPHABET[zeile.index(index_zu_buchstabe(gesucht))]
