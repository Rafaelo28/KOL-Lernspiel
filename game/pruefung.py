"""Die Prüf-Funktion (Arbeitsplan 4.1).

Sie beantwortet genau eine Frage: Ist diese Eingabe die Lösung dieser Aufgabe?
Und sie gilt **einheitlich für Handbuch-Übungen und echte Funksprüche** – der
Unterschied steckt schon in der :class:`game.aufgabe.Aufgabe`, nicht hier.

Was sie tolerant hinnimmt (Textkonvention Regel 4)
─────────────────────────────────────────────────
Kleinschreibung, fehlende, doppelte oder verrutschte Leerzeichen, Satzzeichen
und Umlautschreibweisen. Ein vergessenes Leerzeichen ist kein inhaltlicher
Fehler und darf keinen der drei Versuche kosten – sonst misst das Spiel
Tippgenauigkeit statt Verständnis.

Zwei Fälle, die leicht übersehen werden
───────────────────────────────────────
* **Die leere Eingabe.** Wer auf "Prüfen" drückt, ohne etwas eingegeben zu
  haben, hat es nicht versucht. Das Ergebnis meldet das als
  :attr:`Pruefergebnis.ist_leer`; Aufgabe 4.3 darf so etwas nicht als
  Fehlversuch zählen. Dazu gehört auch eine Eingabe, von der nach der
  Normalisierung nichts übrig bleibt – "???" ist so gut wie nichts.
* **Die zu fleissige Eingabe.** Bei einer Teilaufgabe gilt auch die
  vollständige Nachricht als gelöst. Wer von sich aus weiterrechnet, hat mehr
  geleistet; ihn dafür als falsch zu werten wäre verkehrt herum.

Warum "nicht abschicken" hier entschieden wird
──────────────────────────────────────────────
Der Arbeitsplan verlangt: "Falsche Eingabe kann nicht abgeschickt werden."
Ob die Oberfläche den Senden-Knopf sperrt oder eine Meldung zeigt, ist ihre
Sache – die Entscheidung selbst gehört in die Logik und steht als
:attr:`Pruefergebnis.darf_abgeschickt_werden` bereit. So kann sie in Phase 6
nicht versehentlich anders getroffen werden als hier.

Die konkrete Fehlermeldung ("Stelle 3 stimmt nicht") kommt in Aufgabe 4.2
dazu, der Versuchszähler in 4.3.
"""

from typing import NamedTuple

from crypto.normalize import normalisieren


class Pruefergebnis(NamedTuple):
    """Das Urteil über eine Eingabe.

    ``richtig``                 Die Aufgabe ist gelöst.
    ``ist_leer``                Es wurde nichts eingegeben – kein Fehlversuch.
    ``vollstaendig_geloest``    Die ganze Nachricht wurde gerechnet, nicht nur
                                die Teilaufgabe.
    ``eingabe``                 Die Eingabe in normalisierter Form, so wie
                                verglichen wurde.
    ``erwartet``               Die Lösung, gegen die geprüft wurde.
    """

    richtig: bool
    ist_leer: bool
    vollstaendig_geloest: bool
    eingabe: str
    erwartet: str

    @property
    def darf_abgeschickt_werden(self):
        """Arbeitsplan 4.1: Eine falsche Eingabe lässt sich nicht abschicken."""
        return self.richtig

    @property
    def zaehlt_als_versuch(self):
        """Zählt diese Eingabe gegen die drei Versuche aus Regel 2?

        Eine leere Eingabe nicht – wer nichts eingibt, hat es nicht versucht.
        Eine richtige Lösung beendet die Aufgabe und wird von Aufgabe 4.3
        ohnehin nicht mehr gegen das Kontingent gerechnet.
        """
        return not self.ist_leer and not self.richtig


def pruefe(aufgabe, eingabe):
    """Prüft ``eingabe`` gegen die Lösung von ``aufgabe``.

    >>> from game.aufgabe import Aufgabe, VERSCHLUESSELN
    >>> a = Aufgabe("probe", 1, "caesar", VERSCHLUESSELN, 3, "HUND", "KXQG")
    >>> pruefe(a, "KXQG").richtig
    True
    >>> pruefe(a, "kxqg").richtig
    True
    >>> pruefe(a, "KXQF").richtig
    False
    >>> pruefe(a, "KXQF").darf_abgeschickt_werden
    False

    Leerzeichen spielen keine Rolle, eine leere Eingabe ist kein Fehlversuch:

    >>> b = Aufgabe("probe2", 1, "caesar", VERSCHLUESSELN, 3, "ALLES OK", "DOOHV RN")
    >>> pruefe(b, "doohvrn").richtig
    True
    >>> ergebnis = pruefe(b, "   ")
    >>> ergebnis.richtig, ergebnis.ist_leer, ergebnis.zaehlt_als_versuch
    (False, True, False)
    """
    if not isinstance(eingabe, str):
        raise TypeError(
            f"Die Eingabe muss ein Text (str) sein, nicht {type(eingabe).__name__}."
        )

    sauber = normalisieren(eingabe)
    richtig = aufgabe.ist_geloest(eingabe)
    return Pruefergebnis(
        richtig=richtig,
        ist_leer=not sauber,
        vollstaendig_geloest=richtig and aufgabe.ist_vollstaendig_geloest(eingabe),
        eingabe=sauber,
        erwartet=aufgabe.loesung,
    )
