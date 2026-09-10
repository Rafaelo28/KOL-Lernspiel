"""Konkrete Fehlermeldungen statt "falsch" (Arbeitsplan 4.2).

Projektregel 6 verlangt: nie nur "falsch", sondern ein Hinweis, wo es kippt.
Dieses Modul baut aus Aufgabe und Eingabe einen deutschen Satz, den die
Oberfläche unverändert anzeigen kann.

Was die Meldung verrät – und was nicht
──────────────────────────────────────
Sie sagt **wo** der Fehler steckt und **womit** man ihn findet, nie **welcher
Buchstabe richtig wäre**. Sonst könnte man sich die Lösung Versuch für Versuch
zusammensetzen lassen, und die drei Versuche aus Regel 2 wären wertlos. Die
Lösung erscheint erst nach drei Fehlversuchen (Aufgabe 4.3).

Die Zählbasis-Falle
───────────────────
Für denselben Buchstaben gibt es zwei Positionen, und sie stimmen nicht
überein (siehe Kopf von :mod:`crypto.normalize`):

* die **Buchstabenposition** – ohne Leerzeichen gezählt, danach wird
  verglichen,
* die **Anzeigeposition** – mit Leerzeichen, so wie der Text auf dem
  Bildschirm steht.

In "CHLW ZLUG NQDSS" ist das letzte S der 13. Buchstabe, steht aber an
15. Stelle. Wer die Meldung aus der falschen Zahl baut, schickt die Spielenden
an eine Stelle, an der gar nichts falsch ist. :class:`Abweichung` führt beide
mit, und die Meldung nennt zusätzlich Wort und Buchstabe im Wort – das ist am
leichtesten wiederzufinden.

Dass das überhaupt geht, liegt an Textkonvention Regel 3: Alle drei Verfahren
lassen die Leerzeichen stehen. Aufgabentext und Lösung haben deshalb dieselbe
Wortstruktur, und "im 2. Wort der 3. Buchstabe" lässt sich in beiden abzählen.

Zwei Fehler, die keine Buchstabenfehler sind
────────────────────────────────────────────
* **Der Aufgabentext, unverändert abgeschrieben.** Hier hat niemand einen
  Buchstaben verwechselt, sondern gar nicht gerechnet.
* **In die falsche Richtung gerechnet** – verschlüsselt, wo entschlüsselt
  werden sollte.

Beide werden gesondert erkannt und beim Namen genannt, statt die Person an den
ersten abweichenden Buchstaben zu schicken. Dort ist nämlich nicht ein
Buchstabe falsch, sondern das Vorgehen – und "der 1. Buchstabe stimmt nicht"
würde in die Irre führen.
"""

from typing import NamedTuple

from crypto.normalize import LEERZEICHEN, normalisieren, ohne_leerzeichen
from game.aufgabe import ENTSCHLUESSELN, VERSCHLUESSELN, anwenden, gegenrichtung
from game.pruefung import pruefe

#: Hinweis je Verfahren – er sagt, *womit* man den Fehler findet. Die Wortwahl
#: folgt dem Handbuch, damit die Spielenden dieselben Begriffe wiedersehen.
HINWEIS_JE_VERFAHREN = {
    "caesar": "Prüf noch einmal, um wie viele Stellen du verschieben musst.",
    "substitution": "Schau noch einmal in der Zuordnungstabelle nach.",
    "vigenere": (
        "Prüf noch einmal, welcher Schlüsselbuchstabe an dieser Stelle dran ist."
    ),
}

#: Wie die beiden Richtungen im Fliesstext heissen.
RICHTUNG_IM_TEXT = {
    VERSCHLUESSELN: "verschlüsseln",
    ENTSCHLUESSELN: "entschlüsseln",
}


class Abweichung(NamedTuple):
    """Die erste Stelle, an der Eingabe und Lösung auseinandergehen.

    ``buchstabenposition``  ohne Leerzeichen gezählt, ab 1
    ``anzeigeposition``     mit Leerzeichen gezählt, ab 1
    ``wortnummer``          das wievielte Wort, ab 1
    ``position_im_wort``    der wievielte Buchstabe darin, ab 1
    ``eingegeben``          der Buchstabe, der dort steht
    ``anzahl``              wie viele Buchstaben insgesamt nicht stimmen

    ``anzahl`` steht dabei, weil die 3-Versuche-Regel sonst gegen die Meldung
    arbeitet: Wer nur die erste falsche Stelle erfährt, braucht so viele
    Versuche, wie er Fehler gemacht hat – bei drei Verzählern wären die drei
    Versuche aufgebraucht, obwohl die Methode verstanden war. Die blosse
    Anzahl verrät nichts darüber, *welche* Buchstaben stimmen, bringt aber
    dazu, die ganze Rechnung noch einmal durchzugehen statt nur eine Stelle
    zu flicken.
    """

    buchstabenposition: int
    anzeigeposition: int
    wortnummer: int
    position_im_wort: int
    eingegeben: str
    anzahl: int


def erste_abweichung(eingabe, loesung):
    """Findet die erste abweichende Stelle, oder ``None``.

    Verglichen wird ohne Leerzeichen (Textkonvention Regel 4); die Positionen
    werden anschliessend auf den Text **mit** Leerzeichen umgerechnet, weil
    die Spielenden den vor sich haben.

    Ist die Eingabe nur zu kurz oder zu lang, gibt es keine Abweichung – das
    ist ein Längenproblem und wird in :func:`rueckmeldung` gesondert gemeldet.

    >>> erste_abweichung("CHLW ZLUG NQDSR", "CHLW ZLUG NQDSS").buchstabenposition
    13
    >>> erste_abweichung("CHLW ZLUG NQDRR", "CHLW ZLUG NQDSS").anzahl
    2
    >>> erste_abweichung("CHLW", "CHLW ZLUG") is None
    True
    """
    eingabe_buchstaben = ohne_leerzeichen(eingabe)
    loesung_buchstaben = ohne_leerzeichen(loesung)

    falsche_stellen = [
        (stelle, dort)
        for stelle, (dort, soll) in enumerate(
            zip(eingabe_buchstaben, loesung_buchstaben), start=1
        )
        if dort != soll
    ]
    if not falsche_stellen:
        return None

    stelle, eingegeben = falsche_stellen[0]
    anzeige, wort, im_wort = _umrechnen(normalisieren(loesung), stelle)
    return Abweichung(
        buchstabenposition=stelle,
        anzeigeposition=anzeige,
        wortnummer=wort,
        position_im_wort=im_wort,
        eingegeben=eingegeben,
        anzahl=len(falsche_stellen),
    )


def fehlerzahl(eingabe, loesung):
    """Wie weit ist die Eingabe von der Lösung entfernt?

    Gezählt werden die Buchstaben, die nicht stimmen, plus die Buchstaben, die
    zu viel oder zu wenig sind. Leerzeichen und Schreibweise spielen keine
    Rolle (Textkonvention Regel 4).

    Die Zahl dient zwei Zwecken: Sie steht in der Rückmeldung ("Noch 3
    Buchstaben stimmen nicht") und sie sagt dem Versuchszähler, ob jemand
    seit dem letzten Mal vorangekommen ist.

    >>> fehlerzahl("CHLW ZLUG NQDSS", "CHLW ZLUG NQDSS")
    0
    >>> fehlerzahl("CHLW ZLUG NQDSR", "CHLW ZLUG NQDSS")
    1
    >>> fehlerzahl("CHLW ZLUG", "CHLW ZLUG NQDSS")
    5
    >>> fehlerzahl("chlwzlugnqdsr", "CHLW ZLUG NQDSS")
    1
    """
    dort = ohne_leerzeichen(eingabe)
    soll = ohne_leerzeichen(loesung)
    falsch = sum(1 for a, b in zip(dort, soll) if a != b)
    return falsch + abs(len(dort) - len(soll))


def bezugsloesung(aufgabe, eingabe):
    """Gegen welche Lösung wird diese Eingabe gemessen?

    Bei einer Teilaufgabe zählen **zwei** Antworten als richtig: der geforderte
    Anfang und die ganze Nachricht (siehe :meth:`game.aufgabe.Aufgabe.ist_geloest`).
    Wer sich für die ganze Nachricht entschieden hat, muss auch eine
    Rückmeldung bekommen, die sich darauf bezieht – sonst hört jemand, der
    zwei Buchstaben von der vollständigen Lösung entfernt ist, seine Antwort
    sei dreiundsechzig Buchstaben zu lang.

    Gemessen wird deshalb gegen die **nähere** der beiden. Bei Gleichstand
    gewinnt die Teilaufgabe – sie ist das, was verlangt war.
    """
    if not aufgabe.hat_teilaufgabe:
        return aufgabe.loesung
    if fehlerzahl(eingabe, aufgabe.vollstaendige_loesung) < fehlerzahl(
        eingabe, aufgabe.loesung
    ):
        return aufgabe.vollstaendige_loesung
    return aufgabe.loesung


def fehlerzahl_der_aufgabe(aufgabe, eingabe):
    """Wie viele Buchstaben fehlen dieser Eingabe zur nächstliegenden Lösung.

    Anders als :func:`fehlerzahl` weiss diese Funktion von Teilaufgaben. Sie
    ist die Zahl, die im Spiel angezeigt wird und über Fortschritt entscheidet.
    """
    return fehlerzahl(eingabe, bezugsloesung(aufgabe, eingabe))


def _umrechnen(loesung_mit_leerzeichen, buchstabenposition):
    """Rechnet eine Buchstabenposition auf Anzeige, Wort und Wortposition um."""
    gezaehlt = 0
    wortnummer = 1
    im_wort = 0
    for anzeige, zeichen in enumerate(loesung_mit_leerzeichen, start=1):
        if zeichen == LEERZEICHEN:
            wortnummer += 1
            im_wort = 0
            continue
        gezaehlt += 1
        im_wort += 1
        if gezaehlt == buchstabenposition:
            return anzeige, wortnummer, im_wort
    raise ValueError(
        f"Stelle {buchstabenposition} liegt hinter dem Ende von "
        f"{loesung_mit_leerzeichen!r}."
    )


def _hat_falsche_richtung_gerechnet(aufgabe, eingabe):
    """Wurde ver- statt entschlüsselt (oder umgekehrt)?"""
    try:
        andersherum = anwenden(
            aufgabe.verfahren,
            gegenrichtung(aufgabe.richtung),
            aufgabe.anzeigetext,
            aufgabe.schluessel,
        )
    except (ValueError, TypeError):
        return False
    return ohne_leerzeichen(eingabe) == ohne_leerzeichen(andersherum)


def rueckmeldung(aufgabe, eingabe):
    """Baut die Rückmeldung zu einer Eingabe.

    Rückgabe ist ein anzeigefertiger deutscher Satz. Bei einer richtigen
    Lösung ist er leer – dann gibt es nichts zu meckern.

    >>> from game.aufgabe import Aufgabe, VERSCHLUESSELN
    >>> a = Aufgabe("probe", 1, "caesar", VERSCHLUESSELN, 3, "ZEIT WIRD KNAPP",
    ...             "CHLW ZLUG NQDSS")
    >>> rueckmeldung(a, "CHLW ZLUG NQDSS")
    ''
    >>> rueckmeldung(a, "")
    'Du hast noch nichts eingegeben.'
    >>> print(rueckmeldung(a, "CHLW ZLUG NQDSR"))
    Der 13. Buchstabe stimmt noch nicht – im 3. Wort der 5. Buchstabe. Prüf noch einmal, um wie viele Stellen du verschieben musst.
    >>> print(rueckmeldung(a, "CHLW ZLUG"))
    Deine Antwort ist noch zu kurz: es fehlen 5 Buchstaben.
    >>> print(rueckmeldung(a, "ZEIT WIRD KNAPP"))
    Das ist der Aufgabentext, unverändert abgeschrieben. Du musst ihn erst verschlüsseln.

    Falscher Buchstabe **und** zu kurz – beides wird gesagt:

    >>> print(rueckmeldung(a, "CHLA ZLUG"))
    Der 4. Buchstabe stimmt noch nicht – im 1. Wort der 4. Buchstabe. Ausserdem fehlen noch 5 Buchstaben. Prüf noch einmal, um wie viele Stellen du verschieben musst.
    """
    ergebnis = pruefe(aufgabe, eingabe)
    if ergebnis.richtig:
        return ""
    if ergebnis.ist_leer:
        return "Du hast noch nichts eingegeben."

    if ohne_leerzeichen(eingabe) == ohne_leerzeichen(aufgabe.anzeigetext):
        soll = RICHTUNG_IM_TEXT[aufgabe.richtung]
        return (
            f"Das ist der Aufgabentext, unverändert abgeschrieben. Du musst "
            f"ihn erst {soll}."
        )

    if _hat_falsche_richtung_gerechnet(aufgabe, eingabe):
        soll = RICHTUNG_IM_TEXT[aufgabe.richtung]
        statt = RICHTUNG_IM_TEXT[gegenrichtung(aufgabe.richtung)]
        return (
            f"Du hast in die falsche Richtung gerechnet: Hier musst du {soll}, "
            f"nicht {statt}."
        )

    bezug = bezugsloesung(aufgabe, eingabe)
    abweichung = erste_abweichung(eingabe, bezug)
    fehlend = len(ohne_leerzeichen(bezug)) - len(ohne_leerzeichen(eingabe))

    saetze = []
    if abweichung is not None:
        mehrwortig = LEERZEICHEN in normalisieren(bezug)
        stelle_im_wort = (
            f"im {abweichung.wortnummer}. Wort der "
            f"{abweichung.position_im_wort}. Buchstabe"
        )
        if abweichung.anzahl == 1:
            satz = f"Der {abweichung.buchstabenposition}. Buchstabe stimmt noch nicht"
            if mehrwortig:
                satz += f" – {stelle_im_wort}"
        else:
            satz = (
                f"Noch {abweichung.anzahl} Buchstaben stimmen nicht – der erste "
                f"davon ist der {abweichung.buchstabenposition}"
            )
            if mehrwortig:
                satz += f"., {stelle_im_wort}"
        saetze.append(satz + ".")

    if fehlend:
        # Steht schon ein Satz davor, wird die Länge angehängt statt allein
        # genannt. Sonst korrigiert jemand den einen Buchstaben und erfährt
        # erst im nächsten Versuch, dass die Antwort ausserdem zu kurz ist.
        angehaengt = bool(saetze)
        saetze.append(_laengensatz(fehlend, angehaengt))

    # Der Verfahrenshinweis gehört nur dort hin, wo wirklich ein Buchstabe
    # falsch gerechnet wurde. Bei einer bloss zu kurzen Antwort wäre "prüf die
    # Verschiebung" irreführend – da wurde nur nicht zu Ende gerechnet.
    if abweichung is not None:
        saetze.append(HINWEIS_JE_VERFAHREN.get(aufgabe.verfahren, ""))
    return " ".join(satz for satz in saetze if satz).strip()


def _laengensatz(fehlend, angehaengt):
    """Der Satz zur Längenabweichung, allein stehend oder angehängt."""
    if fehlend > 0:
        buchstaben = "Buchstabe" if fehlend == 1 else "Buchstaben"
        verb = "fehlt" if fehlend == 1 else "fehlen"
        if angehaengt:
            return f"Ausserdem {verb} noch {fehlend} {buchstaben}."
        return f"Deine Antwort ist noch zu kurz: es {verb} {fehlend} {buchstaben}."
    zuviel = -fehlend
    buchstaben = "Buchstabe" if zuviel == 1 else "Buchstaben"
    if angehaengt:
        return f"Ausserdem {'ist' if zuviel == 1 else 'sind'} {zuviel} {buchstaben} zu viel."
    return f"Deine Antwort ist zu lang: {zuviel} {buchstaben} zu viel."
