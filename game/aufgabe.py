"""Das Aufgabenobjekt (Arbeitsplan 3.1).

Eine :class:`Aufgabe` ist alles, was das Spiel braucht, um eine einzelne
Ver- oder Entschlüsselungsaufgabe zu stellen und zu bewerten: Richtung,
Anzeigetext, Schlüssel, erwartete Lösung und Level.

Warum auch die echten Funksprüche hier hineinpassen
───────────────────────────────────────────────────
Der Arbeitsplan beschreibt unter 3.1 die *Übungs*aufgabe. Phase 4 sagt aber
ausdrücklich: "Gilt einheitlich für Handbuch-Übungen **und** echte
Funksprüche" – dieselbe 3-Versuche-Regel, dieselbe Prüfung, dieselbe
Fehlermeldung. Gäbe es zwei verschiedene Objekte, bräuchte das Fehlerhandling
zwei Wege, und die 3-Versuche-Regel könnte auf einem davon vergessen werden.
Genau dort blockiert das Spiel dann an den story-tragenden Stellen.

Deshalb trägt :class:`Aufgabe` beides. Das Feld :attr:`Aufgabe.quelle`
unterscheidet die Herkunft – die UI setzt den Funk-Screen optisch ab
(Arbeitsplan 6.6) und das Log kann später Übungen von Ernstfällen trennen.

Was der Anzeigetext ist, hängt an der Richtung
──────────────────────────────────────────────
* **Verschlüsseln:** Angezeigt wird der Klartext, eingegeben der Geheimtext.
* **Entschlüsseln:** Angezeigt wird der Geheimtext, eingegeben der Klartext.

Beim Senden darf der Geheimtext deshalb nie mit angezeigt werden – er ist die
Lösung (siehe CLAUDE.md, "Lange Funksprüche: Teilaufgabe statt Kürzen").

Teilaufgaben
────────────
Bei den drei langen Funksprüchen wird nur der Anfang von Hand gerechnet.
:attr:`Aufgabe.loesung` ist dann **nur dieser Anfang** – geprüft wird immer
gegen ``loesung``, ohne Sonderfall. Was der Knopf danach auflöst, steht in
:attr:`Aufgabe.rest_der_loesung`.
"""

from typing import NamedTuple

from content import verfahren as _verfahren
from crypto import caesar, substitution, vigenere
from crypto.normalize import LEERZEICHEN, normalisieren, vergleiche_tolerant

# Richtungen einer Aufgabe.
VERSCHLUESSELN = "verschluesseln"
ENTSCHLUESSELN = "entschluesseln"
RICHTUNGEN = (VERSCHLUESSELN, ENTSCHLUESSELN)

# Herkunft einer Aufgabe.
QUELLE_UEBUNG = "uebung"
QUELLE_FUNKSPRUCH = "funkspruch"
QUELLEN = (QUELLE_UEBUNG, QUELLE_FUNKSPRUCH)


def _substitution_verschluesseln(text, schluessel):
    return substitution.verschluesseln(text, schluessel)


def _substitution_entschluesseln(text, schluessel):
    return substitution.entschluesseln(text, schluessel)


#: Ordnet jeder Verfahrenskennung aus :mod:`content.verfahren` die beiden
#: Funktionen aus ``crypto/`` zu. Das ist die einzige Stelle im Projekt, an
#: der aus der Kennung "caesar" das Modul ``crypto.caesar`` wird.
VERFAHRENSFUNKTIONEN = {
    _verfahren.CAESAR: (caesar.verschluesseln, caesar.entschluesseln),
    _verfahren.SUBSTITUTION: (_substitution_verschluesseln, _substitution_entschluesseln),
    _verfahren.VIGENERE: (vigenere.verschluesseln, vigenere.entschluesseln),
}


def anwenden(verfahren_kennung, richtung, text, schluessel):
    """Wendet ein Verfahren in der gewünschten Richtung auf ``text`` an.

    >>> anwenden("caesar", VERSCHLUESSELN, "HUND", 3)
    'KXQG'
    >>> anwenden("vigenere", ENTSCHLUESSELN, "YIGU", "ROT")
    'HUND'
    >>> anwenden("substitution", VERSCHLUESSELN, "HUND", None)
    'IXFR'
    """
    if verfahren_kennung not in VERFAHRENSFUNKTIONEN:
        raise ValueError(
            f"Unbekanntes Verfahren {verfahren_kennung!r}; bekannt sind "
            f"{sorted(VERFAHRENSFUNKTIONEN)}."
        )
    if richtung not in RICHTUNGEN:
        raise ValueError(
            f"Unbekannte Richtung {richtung!r}; erlaubt sind {list(RICHTUNGEN)}."
        )
    hin, zurueck = VERFAHRENSFUNKTIONEN[verfahren_kennung]
    funktion = hin if richtung == VERSCHLUESSELN else zurueck
    return funktion(text, schluessel)


def gegenrichtung(richtung):
    """Macht aus "verschluesseln" ein "entschluesseln" und umgekehrt.

    >>> gegenrichtung(VERSCHLUESSELN), gegenrichtung(ENTSCHLUESSELN)
    ('entschluesseln', 'verschluesseln')
    """
    if richtung not in RICHTUNGEN:
        raise ValueError(
            f"Unbekannte Richtung {richtung!r}; erlaubt sind {list(RICHTUNGEN)}."
        )
    return ENTSCHLUESSELN if richtung == VERSCHLUESSELN else VERSCHLUESSELN


class Aufgabe(NamedTuple):
    """Eine einzelne Ver- oder Entschlüsselungsaufgabe.

    ``kennung``          eindeutiger Name für das Log (Arbeitsplan 5.5)
    ``level``            1, 2 oder 3
    ``verfahren``        Kennung aus :mod:`content.verfahren`
    ``richtung``         :data:`VERSCHLUESSELN` oder :data:`ENTSCHLUESSELN`
    ``schluessel``       ganze Zahl bei Caesar, Wort bei Vigenère,
                         ``None`` bei der Substitution
    ``anzeigetext``      was auf dem Bildschirm steht
    ``loesung``          was eingegeben werden muss; bei einer Teilaufgabe
                         nur deren Anfang
    ``quelle``           Übung oder echter Funkspruch
    ``rest_der_loesung`` was der Weiterrechnen-Knopf auflöst, sonst leer
    ``knopf_beschriftung`` Aufschrift dieses Knopfes
    ``weiterrechnen_text`` Erzähltext, der nach dem Knopf erscheint
    ``zusatzaufgabe``    aus dem adaptiven Timer entstanden (Arbeitsplan 5.4)

    Die drei Felder zur Teilaufgabe gehören zusammen: Entweder sind alle drei
    gesetzt oder keines. ``pruefe_aufgabe()`` hält das nach – ein Knopf ohne
    Aufschrift oder ohne Erzähltext wäre im Spiel eine leere Fläche.
    """

    kennung: str
    level: int
    verfahren: str
    richtung: str
    schluessel: object
    anzeigetext: str
    loesung: str
    quelle: str = QUELLE_UEBUNG
    rest_der_loesung: str = ""
    knopf_beschriftung: str = ""
    weiterrechnen_text: str = ""
    zusatzaufgabe: bool = False

    @property
    def hat_teilaufgabe(self):
        """Wird nur ein Anfang von Hand gerechnet?"""
        return bool(self.rest_der_loesung)

    @property
    def vollstaendige_loesung(self):
        """Die ganze Lösung – nach dem Weiterrechnen-Knopf.

        Ohne Teilaufgabe ist das dasselbe wie :attr:`loesung`.
        """
        if not self.rest_der_loesung:
            return self.loesung
        return f"{self.loesung}{LEERZEICHEN}{self.rest_der_loesung}"

    @property
    def laenge_in_buchstaben(self):
        """Wie viele Buchstaben tatsächlich von Hand zu rechnen sind.

        Genau diese Zahl gehört ins Log (Arbeitsplan 5.5): Ohne sie sind die
        Bearbeitungszeiten von Teilaufgaben und ganzen Nachrichten nicht
        vergleichbar.
        """
        return len(self.loesung.replace(LEERZEICHEN, ""))

    def ist_geloest(self, eingabe):
        """Prüft eine Eingabe tolerant nach Textkonvention Regel 4.

        Groß-/Kleinschreibung und Leerzeichen spielen keine Rolle – ein
        vergessenes Leerzeichen darf keinen der drei Versuche kosten.

        Bei einer Teilaufgabe gilt **auch die vollständige Nachricht** als
        gelöst. Die Teilaufgabe ist eine Erleichterung, keine Vorschrift: Wer
        von sich aus weiterrechnet, hat mehr geleistet und darf dafür nicht
        als falsch gewertet werden – nach drei solchen "Fehlversuchen"
        bekäme ausgerechnet das fleissigste Kind die Lösung vorgesetzt.

        Die ausführliche Rückmeldung ("Stelle 3 stimmt nicht") kommt in
        Aufgabe 4.2 dazu; hier steht nur die Ja-Nein-Entscheidung.
        """
        return vergleiche_tolerant(eingabe, self.loesung) or (
            self.hat_teilaufgabe
            and vergleiche_tolerant(eingabe, self.vollstaendige_loesung)
        )

    def ist_vollstaendig_geloest(self, eingabe):
        """Wurde die ganze Nachricht gerechnet, nicht nur die Teilaufgabe?

        Für das Log (Arbeitsplan 5.5) ein Unterschied: Diese Person hat mehr
        Buchstaben von Hand gerechnet, als die Aufgabe verlangt hat.
        """
        return vergleiche_tolerant(eingabe, self.vollstaendige_loesung)


def pruefe_aufgabe(aufgabe):
    """Prüft eine Aufgabe auf Widerspruchsfreiheit; wirft sonst ``ValueError``.

    Das ist keine Nutzereingabe-Prüfung, sondern ein Selbsttest für den
    Generator aus Aufgabe 3.2: Eine Aufgabe, deren Lösung nicht wirklich aus
    ihrem Anzeigetext folgt, würde im Spiel jede richtige Eingabe als falsch
    werten – und die Spielenden hätten keine Chance, das zu merken.

    >>> a = Aufgabe("probe", 1, "caesar", VERSCHLUESSELN, 3, "HUND", "KXQG")
    >>> pruefe_aufgabe(a)
    >>> pruefe_aufgabe(a._replace(loesung="FALSCH"))
    Traceback (most recent call last):
        ...
    ValueError: Aufgabe 'probe': Aus dem Anzeigetext 'HUND' folgt 'KXQG', als Lösung steht dort aber 'FALSCH'.
    """
    if aufgabe.level not in (1, 2, 3):
        raise ValueError(f"Aufgabe {aufgabe.kennung!r}: Level {aufgabe.level} gibt es nicht.")
    if aufgabe.richtung not in RICHTUNGEN:
        raise ValueError(
            f"Aufgabe {aufgabe.kennung!r}: Richtung {aufgabe.richtung!r} ist unbekannt."
        )
    if aufgabe.quelle not in QUELLEN:
        raise ValueError(
            f"Aufgabe {aufgabe.kennung!r}: Quelle {aufgabe.quelle!r} ist unbekannt."
        )
    if aufgabe.verfahren != _verfahren.VERFAHREN_NACH_LEVEL[aufgabe.level]:
        raise ValueError(
            f"Aufgabe {aufgabe.kennung!r}: Level {aufgabe.level} benutzt "
            f"{_verfahren.VERFAHREN_NACH_LEVEL[aufgabe.level]!r}, hier steht "
            f"{aufgabe.verfahren!r}."
        )

    for feld in ("anzeigetext", "loesung"):
        wert = getattr(aufgabe, feld)
        if not wert:
            raise ValueError(f"Aufgabe {aufgabe.kennung!r}: {feld} ist leer.")
        if normalisieren(wert) != wert:
            raise ValueError(
                f"Aufgabe {aufgabe.kennung!r}: {feld} ist nicht normalisiert "
                f"({wert!r} wird zu {normalisieren(wert)!r})."
            )

    # Der Kern: Folgt die Lösung wirklich aus dem Anzeigetext?
    erwartet = anwenden(
        aufgabe.verfahren, aufgabe.richtung, aufgabe.anzeigetext, aufgabe.schluessel
    )
    if not erwartet.startswith(aufgabe.loesung):
        raise ValueError(
            f"Aufgabe {aufgabe.kennung!r}: Aus dem Anzeigetext "
            f"{aufgabe.anzeigetext!r} folgt {erwartet!r}, als Lösung steht "
            f"dort aber {aufgabe.loesung!r}."
        )
    if erwartet != aufgabe.vollstaendige_loesung:
        raise ValueError(
            f"Aufgabe {aufgabe.kennung!r}: Lösung und Rest ergeben zusammen "
            f"{aufgabe.vollstaendige_loesung!r}, aus dem Anzeigetext folgt "
            f"aber {erwartet!r}."
        )
    if aufgabe.rest_der_loesung and aufgabe.quelle != QUELLE_FUNKSPRUCH:
        raise ValueError(
            f"Aufgabe {aufgabe.kennung!r}: Teilaufgaben gibt es nur bei echten "
            "Funksprüchen, nicht bei Handbuch-Übungen."
        )

    teilaufgabe_felder = {
        "rest_der_loesung": aufgabe.rest_der_loesung,
        "knopf_beschriftung": aufgabe.knopf_beschriftung,
        "weiterrechnen_text": aufgabe.weiterrechnen_text,
    }
    gesetzt = {name for name, wert in teilaufgabe_felder.items() if wert}
    if gesetzt and len(gesetzt) != len(teilaufgabe_felder):
        fehlend = sorted(set(teilaufgabe_felder) - gesetzt)
        raise ValueError(
            f"Aufgabe {aufgabe.kennung!r}: Zur Teilaufgabe fehlt "
            f"{', '.join(fehlend)}. Ein Knopf ohne Aufschrift oder ohne "
            "Erzähltext wäre im Spiel eine leere Fläche."
        )
