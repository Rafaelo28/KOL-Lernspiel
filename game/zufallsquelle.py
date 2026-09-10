"""Der Zufalls-Seed eines Durchlaufs (Arbeitsplan 3.3).

Wozu das gut ist
────────────────
Die Übungsaufgaben werden zufällig gezogen – jedes Kind bekommt andere Wörter,
damit man nicht abschauen kann. Für die Auswertung muss aber rekonstruierbar
bleiben, **wer welche Aufgaben bekommen hat**: Sonst lässt sich eine lange
Bearbeitungszeit nicht danach unterscheiden, ob jemand langsam war oder einfach
den längsten Satz erwischt hat.

Dafür wird der Seed **einmal pro Durchlauf** gezogen und ins Log geschrieben.
Mit ihm lässt sich die Aufgabenfolge später Zeichen für Zeichen nachbauen.

Warum je Level ein eigener Zufallsstrom
───────────────────────────────────────
Ein einziger Strom für den ganzen Durchlauf wäre bequemer, aber schlechter zu
rekonstruieren: Wie viele Zufallszahlen bis zu einer bestimmten Aufgabe
verbraucht wurden, hinge dann davon ab, wie viele Zusatzaufgaben jemand in den
Leveln davor bekommen hat (Arbeitsplan 5.4). Man müsste den ganzen Durchlauf
nachspielen, um an Level 3 heranzukommen.

Mit einem eigenen Strom je Level genügen **Seed und die Nummer der Übung in
diesem Level** – und genau beides steht in jeder Logzeile (Arbeitsplan 5.5):
der Seed in seiner Spalte, die Übungsnummer in der Kennung (``uebung_l2_3``).
:func:`game.generator.uebung_nachbauen` erledigt den Rest. Die Spalte
``aufgabennummer`` ist dafür die falsche – sie zählt die Funksprüche mit.

Der Strom wird aus Seed und Level abgeleitet, nicht neu gewürfelt: Dieselbe
Zufallsquelle liefert für dasselbe Level immer denselben Strom, für
verschiedene Level aber verschiedene. Als Ableitung dient eine Zeichenkette,
weil ``random.Random`` Zeichenketten über SHA-512 einliest – das Ergebnis ist
damit über Prozessgrenzen und Rechner hinweg gleich. (Über ``hash()``
abgeleitete Seeds wären das wegen der Hash-Randomisierung von Python **nicht**.)

Benutzung
─────────
    quelle = Zufallsquelle.neu()          # einmal zu Beginn des Durchlaufs
    protokolliere(quelle.protokollwert)   # in die erste Logzeile
    generator = Aufgabengenerator(quelle)

Und später, zur Auswertung:

    quelle = Zufallsquelle(4711)          # der Seed aus dem Log
"""

import random

#: Der Seed ist eine Zahl von 0 bis unter dieser Grenze – neunstellig, damit
#: er in eine Logzeile passt und sich notfalls von Hand abtippen lässt.
SEED_OBERGRENZE = 1_000_000_000


def neuer_seed():
    """Zieht einen frischen Seed für einen echten Durchlauf.

    Bewusst über ``random.SystemRandom``: Ein Seed, der selbst aus dem
    normalen Zufallsgenerator käme, wäre von dessen Zustand abhängig – zwei
    gleichzeitig gestartete Schulrechner könnten denselben bekommen.
    """
    return random.SystemRandom().randrange(SEED_OBERGRENZE)


class Zufallsquelle:
    """Hält den Seed eines Durchlaufs und gibt je Level einen Zufallsstrom aus.

    >>> quelle = Zufallsquelle(4711)
    >>> quelle.seed
    4711
    >>> quelle.protokollwert
    '4711'

    Derselbe Seed ergibt denselben Strom:

    >>> Zufallsquelle(4711).fuer_level(1).random() == Zufallsquelle(4711).fuer_level(1).random()
    True

    Verschiedene Level ziehen unabhängig voneinander:

    >>> quelle = Zufallsquelle(4711)
    >>> quelle.fuer_level(1).random() == quelle.fuer_level(2).random()
    False

    Derselbe Level liefert immer denselben Strom weiter, nicht jedes Mal einen
    neuen – sonst käme in einem Level immer dieselbe Aufgabe:

    >>> quelle = Zufallsquelle(4711)
    >>> quelle.fuer_level(1) is quelle.fuer_level(1)
    True
    """

    def __init__(self, seed):
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise TypeError(
                f"Der Seed muss eine ganze Zahl (int) sein, nicht "
                f"{type(seed).__name__}."
            )
        if not 0 <= seed < SEED_OBERGRENZE:
            raise ValueError(
                f"Der Seed muss zwischen 0 und {SEED_OBERGRENZE - 1} liegen, "
                f"ist aber {seed}."
            )
        self._seed = seed
        self._stroeme = {}

    @classmethod
    def neu(cls):
        """Erzeugt eine Zufallsquelle mit frischem Seed – einmal je Durchlauf."""
        return cls(neuer_seed())

    @property
    def seed(self):
        """Der Seed dieses Durchlaufs."""
        return self._seed

    @property
    def protokollwert(self):
        """Der Seed so, wie er ins Log geschrieben wird."""
        return str(self._seed)

    def fuer_level(self, level):
        """Der Zufallsstrom dieses Levels – bei jedem Aufruf derselbe.

        Der Strom wird beim ersten Aufruf angelegt und danach weitergeführt.
        Ein neu angelegter Strom bei jedem Aufruf würde in einem Level immer
        wieder dieselbe Aufgabe ziehen.
        """
        if level not in self._stroeme:
            self._stroeme[level] = random.Random(f"{self._seed}:level{level}")
        return self._stroeme[level]

    def __repr__(self):
        return f"Zufallsquelle({self._seed})"
