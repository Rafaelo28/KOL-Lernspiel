"""Die fünf wählbaren Figuren und Bob (Arbeitsplan 2.4).

Quelle ist ``dokumentation/Konzept_Spiel.md``, Abschnitt "Charaktere".

Wozu die Initialen dienen
─────────────────────────
Jede gesendete Funkmeldung wird mit den Initialen der gewählten Figur
unterschrieben – im Konzept ausdrücklich so vorgesehen. In
``content/story.py`` steht dafür der Platzhalter ``{initialen}``::

    text = FUNKSPRUCH_ERSTER_RUF.klartext.format(initialen=figur.initialen)

Daraus folgen zwei Anforderungen, die ``tests/test_charaktere.py`` nachhält:

* Die Initialen bestehen nur aus A–Z. Sie werden mitverschlüsselt und müssen
  deshalb der Textkonvention genügen (siehe :mod:`crypto.normalize`).
* Keine zwei Figuren haben dieselben Initialen. Sonst wäre der Absender einer
  Meldung nicht mehr eindeutig – und in den Messdaten liesse sich später nicht
  mehr zuordnen, wer was gefunkt hat.

Zu "Théo Lambert"
─────────────────
Der Name enthält ein é. Die Textkonvention macht daraus "THEO LAMBERT" – der
Grundbuchstabe bleibt also erhalten, und die Initialen lauten "TL". Vor der
Unicode-Korrektur in ``crypto/normalize.py`` wäre daraus "THO LAMBERT"
geworden; ein Test hält diesen Fall deshalb ausdrücklich fest.

Bob ist keine wählbare Figur
────────────────────────────
Er steht hier trotzdem, weil die Oberfläche seinen Namen und seine Rolle
anzeigt, wenn einer seiner beiden Funksprüche eintrifft. Er taucht nicht in
:data:`SPIELBARE_CHARAKTERE` auf.
"""

from typing import NamedTuple


class Charakter(NamedTuple):
    """Eine Figur der Geschichte.

    ``kennung`` ist der maschinenlesbare Name (klein, mit Unterstrich). Er
    landet später im Log, damit dort nicht der Anzeigename steht.
    """

    kennung: str
    name: str
    rolle: str
    initialen: str


# ───────────────────────────────────────────────────────────────────────────
# Die fünf wählbaren Crewmitglieder
# ───────────────────────────────────────────────────────────────────────────

VIC_MORENO = Charakter(
    kennung="vic_moreno",
    name="Vic Moreno",
    rolle="Tresorknacker",
    initialen="VM",
)

ELENA_DUARTE = Charakter(
    kennung="elena_duarte",
    name="Elena Duarte",
    rolle="ehemalige Diamantenhändlerin",
    initialen="ED",
)

JONAS_BERG = Charakter(
    kennung="jonas_berg",
    name="Jonas Berg",
    rolle="Technik-Experte",
    initialen="JB",
)

AMARA_NWOSU = Charakter(
    kennung="amara_nwosu",
    name="Amara Nwosu",
    rolle="Fluchtplanerin",
    initialen="AN",
)

THEO_LAMBERT = Charakter(
    kennung="theo_lambert",
    name="Théo Lambert",
    rolle="Fälscher und Tarnungsspezialist",
    initialen="TL",
)


#: Die Auswahl auf dem Startbildschirm (Arbeitsplan 6.2), in der Reihenfolge
#: des Konzepts.
SPIELBARE_CHARAKTERE = (
    VIC_MORENO,
    ELENA_DUARTE,
    JONAS_BERG,
    AMARA_NWOSU,
    THEO_LAMBERT,
)

#: Nachschlagetabelle für die Oberfläche und das Logging.
CHARAKTER_NACH_KENNUNG = {figur.kennung: figur for figur in SPIELBARE_CHARAKTERE}


# ───────────────────────────────────────────────────────────────────────────
# Bob – nicht wählbar, aber Absender zweier Funksprüche
# ───────────────────────────────────────────────────────────────────────────

BOB = Charakter(
    kennung="bob",
    name="Bob",
    rolle="dein alter Ausbilder, Crew-Zentrale in Singapur",
    initialen="B",
)
