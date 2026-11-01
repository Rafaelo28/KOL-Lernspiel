"""Bobs Verschlüsselungshandbuch – die drei Seiten als Daten (Arbeitsplan 2.1).

Quelle ist ``dokumentation/Handbuchtexte.md``. Hier steht derselbe Text noch
einmal, aber in Stücke zerlegt, die die Oberfläche einzeln setzen kann
(Arbeitsplan 6.4: "Scrollbarer Text, Tabellen als Grid").

Aufbau
──────
Eine :class:`Handbuchseite` besteht aus :class:`Abschnitt`-Objekten
("Was ist das?", "Beispiel", "Merksatz"). Jeder Abschnitt enthält Blöcke, und
zwar nur wenige Sorten, damit die UI mit einer einfachen Fallunterscheidung
auskommt:

* :class:`Absatz`      – Fließtext, wird umgebrochen
* :class:`Aufzaehlung` – Punkte oder nummerierte Schritte
* :class:`Tabelle`     – Zeilen für ein Grid; die **erste Spalte ist immer die
  Beschriftung der Zeile**, danach folgen die Zellen
* :class:`VigenereQuadrat` – Platzhalter: hier gehört das 26x26-Raster hin,
  das ``crypto.vigenere_quadrat`` zur Laufzeit erzeugt
* :class:`Randnotiz`   – eine handschriftliche Notiz von Bob; sie wiederholt
  nur, was auf der Seite schon steht (siehe dort)

Ein durchgerechnetes Beispiel versteht man nur mit der Tabelle daneben. Ein
Abschnitt kann deshalb ein Werkzeug ``gegenueber`` nennen – das Buch zeigt es
auf der Seite gegenüber – und die ``schritte`` des Beispiels. Zeigt man auf
einen Schritt, markiert das Buch im Werkzeug, wo gesucht wird: Zeile, Spalte
und Kreuzungspunkt.

Warum der Text hier ohne Fettschrift steht
──────────────────────────────────────────
Im Markdown der Quelle sind Schlüsselwörter mit ``**`` hervorgehoben. Tkinter
kennt kein Markdown, und ein Text-Widget würde die Sternchen wörtlich anzeigen.
Der Text ist deshalb reiner Fließtext. Hervorgehoben werden nur ganze Zeilen:
``Absatz(..., betont=True)`` für die Beispiel-Überschriften und Ergebnisse,
``Abschnitt(..., hervorgehoben=True)`` für die Merksätze. Wie das aussieht,
entscheidet die Oberfläche (6.4) – hier steht nur, *was* wichtig ist.

Warum die Beispielwerte hier abgeschrieben stehen
─────────────────────────────────────────────────
``content/`` importiert bewusst nichts aus ``crypto/`` – die Schichten sind
getrennt, und das Handbuch ist reiner Text. Damit die abgeschriebenen Werte
(``KXQG``, ``IXFR``, ``YIGU``, die Geheimtabelle, das verschobene Alphabet)
nicht still von der Verschlüsselungslogik abweichen, vergleicht
``tests/test_handbuch.py`` jede einzelne Angabe mit dem, was ``crypto/``
tatsächlich berechnet. Läuft eines der beiden auseinander, wird ein Test rot –
und nicht erst eine Schülerin im Unterricht stutzig.

Die Übungssätze stehen nicht hier, sondern in ``content/uebungen.py`` – ein
Pool für alle drei Seiten.
"""

from typing import NamedTuple, Union

from . import verfahren as _verfahren


class Absatz(NamedTuple):
    """Ein Fließtextabsatz. Die UI bricht ihn auf die Fensterbreite um.

    ``betont`` markiert die Zeilen, die in der Quelle fett stehen und für sich
    wichtig sind: die Überschrift eines durchgerechneten Beispiels und sein
    Ergebnis ("HUND wird zu KXQG"). Die UI setzt sie fett.
    """

    text: str
    betont: bool = False


class Aufzaehlung(NamedTuple):
    """Mehrere Punkte. ``nummeriert`` unterscheidet Schritte von Stichpunkten."""

    punkte: tuple
    nummeriert: bool = False


class Tabelle(NamedTuple):
    """Zeilen für ein Grid. Die erste Spalte jeder Zeile ist ihre Beschriftung.

    Alle Zeilen einer Tabelle sind gleich lang; ``tests/test_handbuch.py``
    hält das nach, damit die UI kein Sonderfall-Layout braucht.
    """

    zeilen: tuple
    titel: str = ""


class VigenereQuadrat(NamedTuple):
    """Platzhalter für das 26x26-Quadrat an genau dieser Stelle der Seite.

    Der Block trägt selbst keine Buchstaben. Das Quadrat wird zur Laufzeit von
    ``crypto.vigenere_quadrat.erzeuge_quadrat()`` erzeugt – abgetippt stünde es
    zweimal im Projekt und könnte auseinanderlaufen. Der Block sagt der
    Oberfläche nur: *hier* gehört das Raster hin, mit dieser Beschriftung.
    """

    beschriftung: str = ""


class Randnotiz(NamedTuple):
    """Eine handschriftliche Notiz von Bob, direkt unter dem, was sie betrifft.

    Randnotizen bringen **nichts Neues**. Sie wiederholen in Bobs Worten, was
    auf der Seite schon steht – sie machen das Buch lebendig, nicht klüger.
    Der Grund ist der Versuchsaufbau: Die Kontrollgruppe lernt mit denselben
    Handbuchtexten, aber ohne Notizen. Hülfe eine Notiz mit einem Tipp, der im
    Handbuch fehlt, verglichen die Messdaten nicht mehr Lernspiel und
    Unterricht, sondern zwei verschiedene Erklärungen.

    ``bezug`` ist die Stelle der Seite, die die Notiz wiederholt – wörtlich,
    ``tests/test_handbuch.py`` prüft, dass sie dort steht.
    """

    text: str
    bezug: str


Block = Union[Absatz, Aufzaehlung, Tabelle, VigenereQuadrat, Randnotiz]


class Schritt(NamedTuple):
    """Ein Schritt eines durchgerechneten Beispiels – was dabei im Werkzeug markiert wird.

    ``spalte`` ist der Buchstabe, von dem man in der Kopfzeile ausgeht,
    ``kreuzung`` der, der im markierten Feld steht. ``zeile`` gibt es nur im
    Vigenère-Quadrat: der Schlüsselbuchstabe. Beim Entschlüsseln sind es
    dieselben drei Buchstaben, nur andersherum gelesen – gesucht wird die
    Kreuzung in der Zeile, abgelesen die Spalte.
    """

    spalte: str
    kreuzung: str
    zeile: str = ""


class Abschnitt(NamedTuple):
    """Ein Abschnitt einer Handbuchseite, zum Beispiel "Was ist das?".

    ``hervorgehoben`` markiert den Merksatz. Die UI soll ihn absetzen können,
    ohne die Überschrift auf ihren Wortlaut prüfen zu müssen.

    ``gegenueber`` ist das Werkzeug (eine :class:`Tabelle` oder das
    :class:`VigenereQuadrat`), das beim Lesen dieses Abschnitts auf der Seite
    gegenüber liegt. ``schritte`` sind die Schritte seines Beispiels, in der
    Reihenfolge der nummerierten Punkte des Abschnitts – oder, wo es keine
    gibt, der Spalten seiner Beispieltabelle.
    """

    ueberschrift: str
    bloecke: tuple
    hervorgehoben: bool = False
    gegenueber: object = None
    schritte: tuple = ()


class Handbuchseite(NamedTuple):
    """Eine der drei Seiten, zugeordnet zu genau einem Level.

    ``verfahren`` ist die Kennung aus :mod:`content.verfahren` – dieselbe, die
    auch die Funksprüche in :mod:`content.story` benutzen. So lässt sich in
    Phase 7 eine Seite ihren Funksprüchen zuordnen. Den ausgeschriebenen Namen
    für die Anzeige liefert ``verfahren.BEZEICHNUNG[seite.verfahren]``.
    """

    level: int
    titel: str
    verfahren: str
    abschnitte: tuple


#: Die Buchstaben des Alphabets – hier einmal aufgeschrieben, damit dieselbe
#: Reihe nicht an mehreren Stellen steht.
ALPHABET_ZEILE = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
                  "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z")

#: Die Geheimtabelle aus dem Tastatur-Trick (Handbuchseite 2). Sie steht hier
#: für sich, weil sie zweimal gebraucht wird: im Handbuch und beim Lösen der
#: Übungen von Level 2 (siehe :data:`WERKZEUG_NACH_LEVEL`).
GEHEIMTABELLE = Tabelle(
    titel="Deine Geheimtabelle",
    zeilen=(
        ("Original", *ALPHABET_ZEILE),
        ("Geheim", "Q", "W", "E", "R", "T", "Z", "U", "I", "O", "P", "A", "S", "D", "F", "G", "H", "J", "K", "L", "Y", "X", "C", "V", "B", "N", "M"),
    ),
)

#: Das Alphabet, einmal ohne und einmal mit der Verschiebung um 3
#: (Handbuchseite 1). Es liegt dem Caesar-Beispiel gegenüber.
ALPHABET_UM_3 = Tabelle(
    titel="Das Alphabet, einmal ohne und einmal mit Verschiebung",
    zeilen=(
        ("ohne Verschiebung", *ALPHABET_ZEILE),
        ("um 3 verschoben", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "A", "B", "C"),
    ),
)

#: Das Vigenère-Quadrat (Handbuchseite 3). Es liegt der Erklärung des Quadrats
#: und beiden Beispielen gegenüber – so ist es beim Lesen immer zu sehen.
QUADRAT = VigenereQuadrat(
    beschriftung="Das Vigenère-Quadrat – Zeile: Schlüssel, Spalte: Nachricht",
)

HANDBUCH_TITEL = "Bobs Verschlüsselungshandbuch"
HANDBUCH_UNTERTITEL = (
    "Notfall-Ausgabe – lies das genau durch, bevor du irgendwas funkst."
)


# ───────────────────────────────────────────────────────────────────────────
# Seite 1 – Caesar-Verschlüsselung (Level 1)
# ───────────────────────────────────────────────────────────────────────────

SEITE_CAESAR = Handbuchseite(
    level=1,
    titel="Seite 1: Die Caesar-Verschlüsselung",
    verfahren=_verfahren.CAESAR,
    abschnitte=(
        Abschnitt(
            ueberschrift="Was ist das?",
            bloecke=(
                Absatz(
                    "Stell dir das Alphabet als einen Kreis vor, der sich drehen "
                    "lässt – wie ein Glücksrad mit 26 Feldern (A bis Z). Bei der "
                    "Caesar-Verschlüsselung drehst du das Rad um eine bestimmte "
                    "Anzahl Stellen weiter. Diese Zahl nennt man den Schlüssel."
                ),
                Absatz(
                    "Jeder Buchstabe deiner Nachricht wird um genau diese Anzahl "
                    "Stellen im Alphabet nach vorne verschoben. Kommst du am Ende "
                    "des Alphabets an (bei Z), geht es einfach wieder bei A weiter "
                    "– wie bei einer Uhr, die nach 12 wieder bei 1 anfängt."
                ),
                Randnotiz(
                    "Nach Z geht's wieder bei A los – wie bei der Uhr!",
                    bezug="wie bei einer Uhr, die nach 12 wieder bei 1 anfängt",
                ),
            ),
        ),
        Abschnitt(
            ueberschrift="Beispiel: Schlüssel 3",
            gegenueber=ALPHABET_UM_3,
            schritte=(
                Schritt(spalte="H", kreuzung="K"),
                Schritt(spalte="U", kreuzung="X"),
                Schritt(spalte="N", kreuzung="Q"),
                Schritt(spalte="D", kreuzung="G"),
            ),
            bloecke=(
                Absatz(
                    "Das heißt: Aus A wird D, aus B wird E, aus H wird K und so "
                    "weiter."
                ),
                Randnotiz(
                    "Aus A wird D, aus B wird E – immer 3 weiter!",
                    bezug="Aus A wird D, aus B wird E",
                ),
                Absatz('Verschlüsseln des Wortes "HUND" mit Schlüssel 3:', betont=True),
                Tabelle(
                    zeilen=(
                        ("Buchstabe", "H", "U", "N", "D"),
                        ("verschoben um 3", "K", "X", "Q", "G"),
                    ),
                ),
                Absatz("Ergebnis: HUND wird zu KXQG", betont=True),
                Absatz(
                    "Entschlüsseln funktioniert genau umgekehrt: Du gehst dieselbe "
                    "Anzahl Stellen im Alphabet zurück. Aus KXQG wird also wieder "
                    "HUND."
                ),
            ),
        ),
        Abschnitt(
            ueberschrift="Merksatz",
            hervorgehoben=True,
            bloecke=(
                Absatz("Verschlüsseln = im Alphabet vorwärts springen."),
                Absatz("Entschlüsseln = im Alphabet rückwärts springen."),
                Absatz(
                    "Am Rand des Alphabets (Z bzw. A) einfach am anderen Ende "
                    "weitermachen."
                ),
            ),
        ),
    ),
)


# ───────────────────────────────────────────────────────────────────────────
# Seite 2 – Monoalphabetische Substitution (Level 2)
# ───────────────────────────────────────────────────────────────────────────

SEITE_SUBSTITUTION = Handbuchseite(
    level=2,
    titel="Seite 2: Die monoalphabetische Substitution",
    verfahren=_verfahren.SUBSTITUTION,
    abschnitte=(
        Abschnitt(
            ueberschrift="Was ist das?",
            bloecke=(
                Absatz(
                    "Bei Caesar hast du das ganze Alphabet um eine feste Zahl "
                    "verschoben – das Muster ist also leicht zu erkennen, sobald "
                    "man es einmal weiß. Bei der Substitution machst du es "
                    "cleverer: Jeder Buchstabe bekommt einen völlig frei "
                    'gewählten Ersatzbuchstaben, nicht einfach "3 weiter". Es '
                    "gibt kein festes Verschiebungsmuster mehr."
                ),
            ),
        ),
        Abschnitt(
            ueberschrift="Ein Trick, um dir die Zuordnung zu merken",
            bloecke=(
                Absatz(
                    "Nimm eine Computertastatur. Lies die Buchstaben einfach der "
                    "Reihe nach ab, Zeile für Zeile:"
                ),
                Aufzaehlung(
                    punkte=(
                        "Erste Zeile: Q W E R T Z U I O P",
                        "Zweite Zeile: A S D F G H J K L",
                        "Dritte Zeile: Y X C V B N M",
                    ),
                ),
                Randnotiz(
                    "Einfach die Tastatur abschreiben – Zeile für Zeile!",
                    bezug="Lies die Buchstaben einfach der Reihe nach ab, Zeile für Zeile",
                ),
                Absatz(
                    "Hintereinander ergibt das eine komplette neue "
                    "Buchstaben-Reihenfolge mit 26 Zeichen. Ordnest du sie dem "
                    "normalen Alphabet zu, bekommst du deine Geheimtabelle:"
                ),
                GEHEIMTABELLE,
            ),
        ),
        Abschnitt(
            ueberschrift='Beispiel: Das Wort "HUND"',
            gegenueber=GEHEIMTABELLE,
            schritte=(
                Schritt(spalte="H", kreuzung="I"),
                Schritt(spalte="U", kreuzung="X"),
                Schritt(spalte="N", kreuzung="F"),
                Schritt(spalte="D", kreuzung="R"),
            ),
            bloecke=(
                Absatz('Verschlüsseln des Wortes "HUND":', betont=True),
                Tabelle(
                    zeilen=(
                        ("Buchstabe", "H", "U", "N", "D"),
                        ("Geheimzeichen", "I", "X", "F", "R"),
                    ),
                ),
                Absatz("Ergebnis: HUND wird zu IXFR", betont=True),
                Absatz(
                    "Entschlüsseln: Du suchst den Geheimbuchstaben in der unteren "
                    "Zeile und liest ab, welcher Originalbuchstabe darüber steht."
                ),
            ),
        ),
        Abschnitt(
            ueberschrift="Warum ist das schwerer zu knacken?",
            bloecke=(
                Absatz(
                    "Bei Caesar gibt es nur 25 mögliche Schlüssel – die kann man "
                    "in ein paar Minuten alle durchprobieren. Bei der Substitution "
                    "kann jeder Buchstabe zu jedem anderen werden. Das ergibt "
                    "Millionen und Millionen möglicher Zuordnungen – zu viele zum "
                    "Durchprobieren."
                ),
                Absatz(
                    "Trotzdem ist die Methode nicht unknackbar: In jeder Sprache "
                    "kommen manche Buchstaben viel häufiger vor als andere. Im "
                    'Deutschen ist zum Beispiel das "E" der häufigste Buchstabe. '
                    "Wer einen langen Geheimtext hat, kann zählen, welches "
                    "Geheimzeichen am öftesten vorkommt – das ist dann sehr "
                    'wahrscheinlich das "E". So lässt sich die Zuordnung Stück '
                    "für Stück knacken. Das nennt man Häufigkeitsanalyse."
                ),
                Randnotiz(
                    'Das "E" ist im Deutschen der häufigste Buchstabe!',
                    bezug='Im Deutschen ist zum Beispiel das "E" der häufigste Buchstabe.',
                ),
            ),
        ),
        Abschnitt(
            ueberschrift="Merksatz",
            hervorgehoben=True,
            bloecke=(
                Absatz(
                    "Je länger der Text, desto leichter wird er über "
                    "Häufigkeitsanalyse knackbar – kurze Nachrichten sind sicherer "
                    "als lange."
                ),
            ),
        ),
    ),
)


# ───────────────────────────────────────────────────────────────────────────
# Seite 3 – Vigenère-Verschlüsselung (Level 3)
# ───────────────────────────────────────────────────────────────────────────

SEITE_VIGENERE = Handbuchseite(
    level=3,
    titel="Seite 3: Die Vigenère-Verschlüsselung (mit dem Vigenère-Quadrat)",
    verfahren=_verfahren.VIGENERE,
    abschnitte=(
        Abschnitt(
            ueberschrift="Was ist das?",
            bloecke=(
                Absatz(
                    "Bei Caesar hast du immer um dieselbe Zahl verschoben. Das "
                    "Problem: Sobald jemand die eine Verschiebung errät, ist die "
                    "ganze Nachricht offen. Die Vigenère-Verschlüsselung löst das "
                    "clever: Du benutzt nicht nur eine Verschiebung, sondern ein "
                    "ganzes Schlüsselwort. Jeder Buchstabe dieses Wortes sorgt "
                    "für eine eigene, andere Verschiebung."
                ),
                Absatz(
                    "Das Schlüsselwort wird so oft wiederholt, bis es genauso "
                    "lang ist wie deine Nachricht."
                ),
                Randnotiz(
                    "ROT ROT ROT … bis es so lang ist wie die Nachricht!",
                    bezug="Das Schlüsselwort wird so oft wiederholt, bis es genauso lang ist wie deine Nachricht.",
                ),
                Absatz(
                    "Du schreibst es also immer wieder hintereinander, bis "
                    "unter jedem Buchstaben einer steht – egal, wie oft:"
                ),
                # Das lange Beispiel steht hier und nicht erst beim Rechnen:
                # Bei "HUND" mit "ROT" wird aus dem Schlüssel nur "ROTR", und
                # daran ist nicht zu sehen, dass das Wort immer weiterläuft.
                # Eine Pilotperson hat genau das nicht erkannt. "TREFFPUNKT"
                # zeigt ROT dreimal ganz und einmal angefangen.
                Tabelle(
                    zeilen=(
                        ("Nachricht", *"TREFFPUNKT"),
                        ("Schlüssel", *"ROTROTROTR"),
                    ),
                ),
            ),
        ),
        Abschnitt(
            ueberschrift="Das Vigenère-Quadrat",
            gegenueber=QUADRAT,
            bloecke=(
                Absatz(
                    "Damit du nicht rechnen musst, gibt es eine fertige Tabelle: "
                    "das Vigenère-Quadrat. Es sieht aus wie ein riesiges "
                    "Kreuzworträtsel:"
                ),
                Aufzaehlung(
                    punkte=(
                        "Oben in der Kopfzeile stehen die Buchstaben deiner "
                        "Nachricht (Klartext), A bis Z.",
                        "Links in der ersten Spalte stehen die Buchstaben deines "
                        "Schlüsselworts, A bis Z.",
                        "In jedem Feld der Tabelle steht ein Buchstabe. Um zu "
                        "verschlüsseln, gehst du einfach zur richtigen Zeile und "
                        "Spalte und liest ab, was am Kreuzungspunkt steht.",
                    ),
                ),
            ),
        ),
        Abschnitt(
            ueberschrift="Verschlüsseln – Schritt für Schritt",
            gegenueber=QUADRAT,
            schritte=(
                Schritt(zeile="R", spalte="H", kreuzung="Y"),
                Schritt(zeile="O", spalte="U", kreuzung="I"),
                Schritt(zeile="T", spalte="N", kreuzung="G"),
                Schritt(zeile="R", spalte="D", kreuzung="U"),
            ),
            bloecke=(
                Absatz('Beispiel: Nachricht "HUND", Schlüsselwort "ROT"', betont=True),
                Absatz(
                    "Zuerst schreibst du das Schlüsselwort so oft untereinander, "
                    "bis es genauso lang ist wie deine Nachricht:"
                ),
                Tabelle(
                    zeilen=(
                        ("Nachricht", "H", "U", "N", "D"),
                        ("Schlüssel", "R", "O", "T", "R"),
                    ),
                ),
                Absatz("Jetzt gehst du Buchstabe für Buchstabe vor:"),
                Aufzaehlung(
                    nummeriert=True,
                    punkte=(
                        'H (Nachricht) + R (Schlüssel): Suche im Quadrat die Zeile '
                        '"R" und die Spalte "H". Am Kreuzungspunkt steht Y.',
                        'U + O: Zeile "O", Spalte "U" ergibt I.',
                        'N + T: Zeile "T", Spalte "N" ergibt G.',
                        'D + R: Zeile "R", Spalte "D" ergibt U.',
                    ),
                ),
                Absatz("Ergebnis: HUND wird zu YIGU", betont=True),
            ),
        ),
        Abschnitt(
            ueberschrift="Entschlüsseln – Schritt für Schritt",
            gegenueber=QUADRAT,
            schritte=(
                Schritt(zeile="R", spalte="H", kreuzung="Y"),
                Schritt(zeile="O", spalte="U", kreuzung="I"),
                Schritt(zeile="T", spalte="N", kreuzung="G"),
                Schritt(zeile="R", spalte="D", kreuzung="U"),
            ),
            bloecke=(
                Absatz(
                    "Jetzt hast du den Geheimtext YIGU und das Schlüsselwort ROT "
                    "– und willst wissen, was ursprünglich dastand."
                ),
                Absatz(
                    "Diesmal machst du es andersherum: Du suchst zuerst die Zeile "
                    "deines Schlüsselbuchstabens, und darin den Geheimbuchstaben. "
                    "Die Spalte, in der du ihn findest, verrät dir den "
                    "Original-Buchstaben."
                ),
                Randnotiz(
                    "Erst die Zeile, dann den Buchstaben darin suchen!",
                    bezug="Du suchst zuerst die Zeile deines Schlüsselbuchstabens, und darin den Geheimbuchstaben.",
                ),
                Aufzaehlung(
                    nummeriert=True,
                    punkte=(
                        'Geheimbuchstabe Y, Schlüssel R: Gehe zur Zeile "R" und '
                        'suche darin das "Y". Es steht in der Spalte H.',
                        'Geheimbuchstabe I, Schlüssel O: Zeile "O", suche "I" '
                        "ergibt Spalte U.",
                        'Geheimbuchstabe G, Schlüssel T: Zeile "T", suche "G" '
                        "ergibt Spalte N.",
                        'Geheimbuchstabe U, Schlüssel R: Zeile "R", suche "U" '
                        "ergibt Spalte D.",
                    ),
                ),
                Absatz("Ergebnis: YIGU wird zu HUND", betont=True),
            ),
        ),
        Abschnitt(
            ueberschrift="Warum ist das noch sicherer?",
            bloecke=(
                Absatz(
                    "Bei der einfachen Substitution steht jeder Buchstabe der "
                    "Nachricht immer für dasselbe Geheimzeichen – deshalb "
                    "funktioniert Häufigkeitsanalyse so gut. Bei Vigenère wird zum "
                    'Beispiel das "N" aus HUND einmal zu "G", könnte an anderer '
                    "Stelle aber zu einem ganz anderen Buchstaben werden – je "
                    "nachdem, welcher Schlüsselbuchstabe gerade dran ist. Dadurch "
                    "verschwimmt das Muster: Einfaches Zählen der häufigsten "
                    "Zeichen hilft hier nicht mehr direkt weiter."
                ),
            ),
        ),
        Abschnitt(
            ueberschrift="Merksatz",
            hervorgehoben=True,
            bloecke=(
                Absatz(
                    "Verschlüsseln = Nachrichtenbuchstabe (Spalte) und "
                    "Schlüsselbuchstabe (Zeile) im Quadrat zusammenführen – der "
                    "Kreuzpunkt ist der verschlüsselte Buchstabe."
                ),
                Absatz(
                    "Entschlüsseln = In der Zeile des Schlüsselbuchstabens den "
                    "Geheimbuchstaben suchen – der Spaltenkopf darüber ist der "
                    "entschlüsselte Buchstabe."
                ),
            ),
        ),
    ),
)


# Alle Seiten in Lesereihenfolge – so blättert man im Spiel durch das Handbuch.
SEITEN = (SEITE_CAESAR, SEITE_SUBSTITUTION, SEITE_VIGENERE)

# Nachschlagetabelle für die UI: Welches Level zeigt welche Seite?
# Bewusst ein Dict und keine Funktion – content/ enthält nur Daten.
SEITE_NACH_LEVEL = {seite.level: seite for seite in SEITEN}

#: Was beim Lösen einer Übung neben der Aufgabe liegt (Arbeitsplan 6.5).
#:
#: Bei der Substitution und bei Vigenère ist das Werkzeug die Tabelle selbst –
#: ohne sie lässt sich das Verfahren gar nicht rechnen, und genau so steht es
#: im Handbuch.
#:
#: Bei Caesar ist es dagegen **nur das blanke Alphabet**. Die verschobene
#: Zeile stünde für den Schlüssel der Aufgabe da wie die halbe Lösung: Man
#: bräuchte bloss abzulesen, statt zu zählen. Im Handbuch gibt es sie nur als
#: Beispiel mit dem Schlüssel 3, die Übungen benutzen andere Schlüssel.
WERKZEUG_NACH_LEVEL = {
    1: Tabelle(
        titel="Das Alphabet zum Abzählen",
        # Ohne Zeilenbeschriftung: Das Band besteht nur aus den Buchstaben.
        zeilen=(("", *ALPHABET_ZEILE),),
    ),
    2: GEHEIMTABELLE,
    3: VigenereQuadrat(beschriftung="Zeile: Schlüssel, Spalte: Nachricht"),
}


class Merksatz(NamedTuple):
    """Ein Satz auf der Merkkarte. ``bezug`` ist die Stelle der Handbuchseite,
    die er wiederholt – leer, wenn er dort wörtlich so steht."""

    text: str
    bezug: str = ""


class Merkkarte(NamedTuple):
    """Die Karte, die beim Lösen unter dem Werkzeug liegt (Arbeitsplan 6.5).

    Sie sagt in wenigen Sätzen, wie man mit dem Werkzeug rechnet. Wie die
    Randnotizen bringt sie nichts Neues: Jeder Satz steht so im Handbuch oder
    wiederholt eine Stelle daraus, und ``tests/test_handbuch.py`` prüft das.
    """

    ueberschrift: str
    saetze: tuple


#: Was beim Lösen unter dem Werkzeug liegt.
#:
#: Bei Caesar ist es der Merksatz der Handbuchseite – er sagt genau, wie man
#: rechnet. Der Merksatz der Substitution taugt dafür nicht: "Je länger der
#: Text, desto leichter …" erklärt, warum die Methode unsicher ist, nicht, wie
#: man die Tabelle liest. Dort stehen deshalb die beiden Sätze, mit denen das
#: Handbuch die Tabelle benutzt. Bei Vigenère füllt das Quadrat die Seite;
#: seine Beschriftung sagt, was Zeile und Spalte sind.
MERKKARTE_NACH_LEVEL = {
    1: Merkkarte(
        ueberschrift="Merksatz",
        saetze=(
            Merksatz("Verschlüsseln = im Alphabet vorwärts springen."),
            Merksatz("Entschlüsseln = im Alphabet rückwärts springen."),
            Merksatz("Am Rand des Alphabets (Z bzw. A) einfach am anderen Ende weitermachen."),
        ),
    ),
    2: Merkkarte(
        ueberschrift="So geht's",
        saetze=(
            Merksatz(
                "Verschlüsseln: Du suchst deinen Buchstaben in der oberen Zeile und liest ab, "
                "welches Geheimzeichen darunter steht.",
                bezug="Ordnest du sie dem normalen Alphabet zu, bekommst du deine Geheimtabelle",
            ),
            Merksatz(
                "Entschlüsseln: Du suchst den Geheimbuchstaben in der unteren Zeile und liest ab, "
                "welcher Originalbuchstabe darüber steht."
            ),
        ),
    ),
    3: None,
}
