"""Die Story-Texte des Spiels (Arbeitsplan 2.3).

Quelle ist ``dokumentation/Konzept_Spiel.md``, Abschnitt "Der große
Diamantenraub".

Zwei Sorten Text – und der Unterschied ist wichtig
──────────────────────────────────────────────────
* :class:`Erzaehltext` wird nur **angezeigt**. Er darf Satzzeichen, Umlaute
  und Zahlen enthalten und ist ganz normal geschrieben.
* :class:`Funkspruch` geht über Funk und wird deshalb **immer** ver- oder
  entschlüsselt (Projektregel 3: kein Klartext-Funkverkehr). Sein ``klartext``
  steht schon in der Form der Textkonvention: nur A–Z und einfache
  Leerzeichen. Damit stimmt das, was die Spielenden sehen, genau mit dem
  überein, was das Spiel als Lösung erwartet.

Warum "QUADRANT VIER" und nicht "QUADRANT 4"
────────────────────────────────────────────
Regel 6 der Textkonvention entfernt Ziffern. Aus "Quadrant 4 ist durchsucht,
wir gehen jetzt auf Quadrant 7" würde "QUADRANT IST DURCHSUCHT WIR GEHEN JETZT
AUF QUADRANT" – der abgefangene Funkspruch verlöre genau die Information, um
die es geht. Zahlen in Funksprüchen sind deshalb ausgeschrieben.
``tests/test_story.py`` prüft, dass kein Funkspruch eine Ziffer enthält.

Die Initialen der Spielfigur
────────────────────────────
Gesendete Funksprüche werden mit den Initialen der gewählten Figur
unterschrieben. Im ``klartext`` steht dafür der Platzhalter ``{initialen}``.
Der Aufrufer setzt ihn ein, bevor er den Text anzeigt oder verschlüsselt::

    text = FUNKSPRUCH_ERSTER_RUF.klartext.format(initialen="VM")

Die fünf Figuren und ihre Initialen kommen in Aufgabe 2.4 nach
``content/charaktere.py``.

Teilaufgabe und Weiterrechnen
─────────────────────────────
Die Wortlaute stammen unverändert aus dem Konzept und sind entsprechend lang:
Bobs erste Antwort hat 78 Buchstaben, der abgefangene Funkspruch 76. Die alle
von Hand zu entschlüsseln, wäre in den festen Zeitfenstern (15/20/25 Minuten,
zusätzlich zu Handbuch und Übungen) nicht zu schaffen und vor allem
demotivierend – nach einem Dutzend Buchstaben ist das Verfahren verstanden,
der Rest ist Abschreibarbeit.

Gelöst wird das **nicht durch Kürzen**, sondern durch eine Teilaufgabe:

* ``selbst_zu_loesen`` ist der Anfang der Nachricht, den die Spielenden
  wirklich rechnen. Er endet immer an einer Wortgrenze – ein halbes Wort zu
  entschlüsseln fühlt sich willkürlich an.
* Ist dieser Teil richtig (oder wurde die Lösung nach drei Versuchen ohne
  Fortschritt
  angezeigt), erscheint ein Knopf, siehe :data:`BESCHRIFTUNG_REST`.
* Der Knopf zeigt ``weiterrechnen`` – einen kurzen Erzähltext, in dem die
  Figur die Arbeit zu Ende bringt – und gibt danach die vollständige
  Nachricht frei.

Warum nicht kürzen? Drei Gründe:

1. Handbuchseite 2 sagt: "Je länger der Text, desto leichter wird er über
   Häufigkeitsanalyse knackbar." Der abgefangene Funkspruch ist genau die
   Stelle, an der ein *sichtbar langer* Geheimtext vor den Spielenden liegen
   soll. Ein gekürzter Text widerspricht dem eigenen Handbuch.
2. Die Messdaten werden sauberer. Bei 78 Buchstaben und hartem Zeitfenster
   würden langsamere Kinder mitten in der Aufgabe vom Timer abgeschnitten –
   für die gäbe es keine verwertbare Bearbeitungszeit. Bei einer festen
   Teilaufgabe misst man dieselbe Arbeitsmenge für alle.
3. Der Knopf ist keine Abkürzung, sondern eine Belohnung dafür, dass man das
   Verfahren beherrscht.

Was daran hängt (in späteren Phasen umzusetzen):

* **Phase 4:** Geprüft wird ``selbst_zu_loesen``, nicht der ganze Klartext.
  Die 3-Versuche-Regel gilt für diesen Teil. Der Knopf muss auch dann
  erscheinen, wenn die Lösung angezeigt wurde – sonst blockiert das Spiel an
  genau den story-tragenden Stellen.
* **Phase 5:** Ins Log gehört die Länge des geprüften Teils, sonst sind die
  Zeiten später nicht vergleichbar.
* **Phase 6, je nach Richtung:** Beim *Empfangen* bleibt der vollständige
  Geheimtext sichtbar, der zu entschlüsselnde Anfang ist hervorgehoben – sonst
  geht Grund 1 verloren. Beim *Senden* bleibt der vollständige **Klartext**
  sichtbar; der Geheimtext darf nie angezeigt werden, denn er ist genau das,
  was eingetippt werden soll.
* Die Erzählzeit im ``weiterrechnen``-Text ("zwanzig Minuten später") ist
  reine Fiktion – der echte Level-Timer läuft unverändert weiter.

Funksprüche ohne ``selbst_zu_loesen`` werden ganz von Hand gelöst. Das sind
die beiden kurzen: der erste Ruf (22 Buchstaben) und Bobs zweite Antwort
(27 Buchstaben) – letztere ist der Zahltag des Spiels, den will man selbst
entschlüsseln.
"""

from typing import NamedTuple

from . import uebungen, verfahren

# Richtungen eines Funkspruchs.
SENDEN = "senden"
EMPFANGEN = "empfangen"

# Die Verfahrenskennungen stehen in content/verfahren.py, damit Handbuchseite
# und Funkspruch dieselben benutzen. Hier nur weitergereicht, damit
# ``story.CAESAR`` weiter funktioniert.
CAESAR = verfahren.CAESAR
SUBSTITUTION = verfahren.SUBSTITUTION
VIGENERE = verfahren.VIGENERE

#: Platzhalter für die Initialen der gewählten Figur.
PLATZHALTER_INITIALEN = "{initialen}"

#: Absenderkennung für die Meldungen, die man selbst funkt. Welche Figur das
#: ist, entscheidet sich erst bei der Charakterauswahl.
ABSENDER_SPIELFIGUR = "spielfigur"

#: Absenderkennung, wenn der Absender unbekannt bleibt (die Verfolger).
ABSENDER_UNBEKANNT = ""

#: Das Schlüsselwort, auf das sich die Crew geeinigt hat – dasselbe, mit dem
#: Handbuchseite 3 ihr Beispiel durchrechnet. Die *Übungsaufgaben* wechseln
#: das Schlüsselwort (siehe uebungen.VIGENERE_SCHLUESSELWOERTER), damit sie
#: nicht vorhersehbar werden. Der Ernstfall benutzt bewusst das aus dem
#: Handbuch: Dort soll das Verfahren geübt werden, nicht ein neues Wort.
SCHLUESSELWORT_DER_GESCHICHTE = "ROT"

#: Höchstlänge einer selbst zu lösenden Teilaufgabe, in Buchstaben ohne
#: Leerzeichen. Diese Zahl steht bewusst an genau *einer* Stelle: Nach dem
#: Pilotdurchlauf (Arbeitsplan 8.2) wird sie mit einem Handgriff angepasst,
#: und ``tests/test_story.py`` prüft danach jeden Funkspruch dagegen.
HOECHSTLAENGE_TEILAUFGABE = 25

#: Höchstlänge eines Funkspruchs, der *ganz* von Hand gelöst wird. Bewusst
#: eine zweite Zahl: Sonst liesse sich HOECHSTLAENGE_TEILAUFGABE nicht mehr
#: unter die Länge der kürzesten vollständigen Nachricht senken, und der
#: Stellknopf für den Pilotdurchlauf wäre blockiert.
HOECHSTLAENGE_GANZE_NACHRICHT = 30

#: Beschriftung des Knopfes, der den Rest der Nachricht auflöst. Welche der
#: beiden gilt, hängt an der Richtung des Funkspruchs.
BESCHRIFTUNG_REST = {
    SENDEN: "Den Rest verschlüsseln und senden",
    EMPFANGEN: "Den Rest entschlüsseln",
}


class Erzaehltext(NamedTuple):
    """Text, den das Spiel anzeigt. Wird nie verschlüsselt."""

    kennung: str
    absaetze: tuple


class Funkspruch(NamedTuple):
    """Eine Nachricht über das Kurzwellen-Funkgerät.

    ``klartext`` ist die entschlüsselte Fassung in der Form der
    Textkonvention. Beim Senden ist er die Vorlage, die verschlüsselt werden
    muss; beim Empfangen ist er die Lösung, auf die entschlüsselt wird.

    ``schluessel`` ist der Schlüssel, mit dem die Nachricht ver- bzw.
    entschlüsselt wird: eine ganze Zahl bei Caesar, das Schlüsselwort bei
    Vigenère, ``None`` bei der Substitution (dort ist die Tabelle der
    Schlüssel). Das Spiel **nennt** ihn – es geht ums Anwenden des Verfahrens,
    nicht ums Knacken.

    ``absender_kennung`` verweist auf eine Figur in :mod:`content.charaktere`
    (heute nur ``"bob"``), auf :data:`ABSENDER_SPIELFIGUR` für die selbst
    gesendeten Meldungen, oder ist leer, wenn der Absender unbekannt bleibt.

    ``selbst_zu_loesen`` ist der Anfang von ``klartext``, den die Spielenden
    von Hand rechnen – siehe "Teilaufgabe und Weiterrechnen" im Kopf dieses
    Moduls. Ein leerer Wert heisst: die ganze Nachricht wird selbst gelöst.
    ``weiterrechnen`` ist der Erzähltext, der nach dem Knopf erscheint.
    """

    kennung: str
    level: int
    richtung: str
    verfahren: str
    absender: str
    absender_kennung: str
    schluessel: object
    einleitung: str
    klartext: str
    selbst_zu_loesen: str = ""
    weiterrechnen: str = ""


# ───────────────────────────────────────────────────────────────────────────
# Vor Level 1 – der Raub und der Absturz
# ───────────────────────────────────────────────────────────────────────────

#: Die Prämisse aus dem Konzept. Steht in der Figurwahl über den fünf
#: Figuren: Erst mit ihr ergibt "Wer aus der Crew bist du?" einen Sinn, und
#: der Intro danach setzt sie voraus – er beginnt schon am brennenden Wrack.
VORGESCHICHTE = Erzaehltext(
    kennung="vorgeschichte",
    absaetze=(
        "Der Raub ist geglückt: Deine Crew hat aus einem gesicherten Tresor in "
        "Antwerpen, der Diamantenstadt Belgiens, Diamanten im Wert mehrerer "
        "Milliarden Euro erbeutet.",
        "Die Flucht per Charterflugzeug Richtung Singapur läuft zunächst glatt – "
        "bis CIA, Interpol und die belgische Polizei die Maschine auf dem Radar "
        "haben und Jäger aufsteigen lassen. Der Pilot muss ausweichen, verliert "
        "die Kontrolle – das Flugzeug stürzt über der afghanischen Wüste ab.",
    ),
)

INTRO = Erzaehltext(
    kennung="intro",
    absaetze=(
        "Das Wrack brennt. Du musst weg, bevor es jemand am Rauch findet. Der "
        "Diamantensack liegt griffbereit – aber er ist zu schwer, um ihn allein "
        "zu tragen und gleichzeitig schnell genug zu fliehen. Du lässt ihn "
        "zurück.",
        "Im Vorbeigehen greifst du zwei Dinge aus dem Gepäckfach: ein "
        "Kurzwellen-Funkgerät aus der Notausrüstung – kräftig genug, um über "
        "Kontinente hinweg Signale zu senden, aber auch leicht von jedem "
        "mitzuhören, der auf derselben Frequenz lauscht – und Bobs "
        "Verschlüsselungshandbuch, Standardausrüstung, die du dir vor der "
        "Mission nie richtig angesehen hast.",
        "In sicherer Entfernung vom Wrack bist du auf dich allein gestellt: "
        "kein Funkkontakt, nur das Handbuch. Deine Aufgabe: einen Weg finden, "
        "Kontakt zur Zentrale in Singapur aufzunehmen, ohne dass die Verfolger "
        "– die dieselbe Frequenz absuchen – deine Nachrichten mitlesen können.",
    ),
)


# ───────────────────────────────────────────────────────────────────────────
# Level 1 – Caesar
# ───────────────────────────────────────────────────────────────────────────

EINSTIEG_LEVEL_1 = Erzaehltext(
    kennung="einstieg_level_1",
    absaetze=(
        "Du schlägst das Handbuch auf. Seite 1: Grundlagen der "
        "Verschlüsselung – der Caesar-Code.",
    ),
)

FUNKSPRUCH_ERSTER_RUF = Funkspruch(
    kennung="erster_ruf",
    level=1,
    richtung=SENDEN,
    verfahren=CAESAR,
    absender="du",
    absender_kennung=ABSENDER_SPIELFIGUR,
    schluessel=uebungen.CAESAR_SCHLUESSEL_HANDBUCH,
    einleitung=(
        "Du verschlüsselst eine erste Funkmeldung, ohne zu wissen, ob "
        "überhaupt jemand zuhört."
    ),
    klartext="HALLO HOERT MICH JEMAND {initialen}",
)

FUNKSPRUCH_BOB_ERSTE_ANTWORT = Funkspruch(
    kennung="bob_erste_antwort",
    level=1,
    richtung=EMPFANGEN,
    verfahren=CAESAR,
    absender="Zentrale",
    absender_kennung="bob",
    schluessel=uebungen.CAESAR_SCHLUESSEL_HANDBUCH,
    einleitung=(
        "Kurz darauf trifft eine Antwort ein – verschlüsselt in Caesar. Du "
        "musst sie selbst entschlüsseln, um zu erfahren, was drinsteht."
    ),
    klartext=(
        "JA WIR HOEREN DICH ABER CAESAR IST IN MINUTEN ZU KNACKEN "
        "NIMM DIE NAECHSTE METHODE IM HANDBUCH"
    ),
    # Der geschnittene Anfang ist für sich eine vollständige Aussage: Erst
    # erfährst du, dass überhaupt jemand zuhört – dass Caesar unsicher ist,
    # kommt danach. Erzählerisch besser als die Nachricht am Stück.
    selbst_zu_loesen="JA WIR HOEREN DICH",
    weiterrechnen=(
        "Du rechnest weiter, Buchstabe für Buchstabe, mit dem Alphabetband "
        "aus dem Handbuch. Zwanzig Minuten später liegt der Rest der "
        "Nachricht vor dir."
    ),
)


# ───────────────────────────────────────────────────────────────────────────
# Level 2 – Monoalphabetische Substitution
# ───────────────────────────────────────────────────────────────────────────

EINSTIEG_LEVEL_2 = Erzaehltext(
    kennung="einstieg_level_2",
    absaetze=(
        "Kein Funkkontakt nötig – aus Bobs Nachricht weißt du bereits, dass du "
        "weiterblättern musst. Seite 2: die monoalphabetische Substitution.",
    ),
)

FUNKSPRUCH_VERFOLGER = Funkspruch(
    kennung="verfolger",
    level=2,
    richtung=EMPFANGEN,
    verfahren=SUBSTITUTION,
    absender="unbekannt",
    absender_kennung=ABSENDER_UNBEKANNT,
    schluessel=None,
    einleitung=(
        "Bevor du weiterfunken kannst, rauscht es im Gerät – ein fremder "
        "Funkspruch wird aufgefangen. Er ist mit derselben Substitutionsmethode "
        "verschlüsselt – der Feind benutzt dieselbe Zuordnungstabelle, die auch "
        "in deinem Handbuch steht. Damit kannst du ihn entschlüsseln."
    ),
    # "Quadrant 4" und "Quadrant 7" stehen ausgeschrieben, weil Regel 6 der
    # Textkonvention Ziffern entfernt – sonst bliebe nur "QUADRANT" übrig und
    # der Funkspruch verlöre seinen Sinn.
    klartext=(
        "QUADRANT VIER IST DURCHSUCHT WIR GEHEN JETZT AUF QUADRANT SIEBEN "
        "WIR FINDEN DEN VERRAETER"
    ),
    # Schon der Anfang setzt die Verfolger in die Nähe – der Rest verrät,
    # wohin sie als Nächstes gehen.
    selbst_zu_loesen="QUADRANT VIER IST DURCHSUCHT",
    weiterrechnen=(
        "Du bleibst dran und schlägst jeden weiteren Buchstaben in Bobs "
        "erbeuteter Tabelle nach. Eine gute halbe Stunde später ist der ganze "
        "Funkspruch entziffert."
    ),
)

#: Erscheint bei der letzten und längsten Übungsaufgabe von Level 2
#: (Arbeitsplan 7.2). Er begründet, warum Durchprobieren nicht mehr reicht –
#: eines der Lernziele aus Anhang A1.
HINWEIS_HAEUFIGKEITSANALYSE = Erzaehltext(
    kennung="hinweis_haeufigkeitsanalyse",
    absaetze=(
        "Alle Zuordnungen durchzuprobieren würde ewig dauern – hier hilft nur "
        "eine Häufigkeitsanalyse.",
    ),
)

UEBERGANG_ZU_LEVEL_3 = Erzaehltext(
    kennung="uebergang_zu_level_3",
    absaetze=(
        "Der Feind nutzt genau die Methode, die du gerade verwendest. Zeit für "
        "etwas Stärkeres.",
        "Du blätterst selbst zur letzten Seite weiter. Diesmal meldet sich "
        "niemand über Funk – du bist auf dich gestellt.",
    ),
)


# ───────────────────────────────────────────────────────────────────────────
# Level 3 – Vigenère
# ───────────────────────────────────────────────────────────────────────────

EINSTIEG_LEVEL_3 = Erzaehltext(
    kennung="einstieg_level_3",
    absaetze=(
        "Letzte Seite im Handbuch: die Vigenère-Verschlüsselung – mit einem "
        "Schlüsselwort und dem Vigenère-Quadrat.",
    ),
)

#: Kurze Reflexionsfrage nach den Übungen von Level 3 (Arbeitsplan 7.3).
#: Sie prüft nichts ab, sondern lässt die Spielenden den Unterschied zu
#: Level 2 in eigene Worte fassen.
REFLEXIONSFRAGE_LEVEL_3 = Erzaehltext(
    kennung="reflexionsfrage_level_3",
    absaetze=(
        "Kurz nachgedacht: Warum hilft eine Häufigkeitsanalyse hier nicht mehr "
        "direkt weiter?",
        "Bei der Substitution steht ein Buchstabe immer für dasselbe "
        "Geheimzeichen. Bei Vigenère hängt es davon ab, welcher "
        "Schlüsselbuchstabe gerade an der Reihe ist – dasselbe E wird mal zu "
        "dem einen, mal zu einem anderen Zeichen.",
    ),
)

FUNKSPRUCH_STANDORT = Funkspruch(
    kennung="standort",
    level=3,
    richtung=SENDEN,
    verfahren=VIGENERE,
    absender="du",
    absender_kennung=ABSENDER_SPIELFIGUR,
    schluessel=SCHLUESSELWORT_DER_GESCHICHTE,
    einleitung=(
        "Jetzt zählt es: Du verschlüsselst deinen aktuellen Standort und "
        "sendest ihn."
    ),
    # Auch hier ist die Zahl ausgeschrieben – aus demselben Grund wie beim
    # Funkspruch der Verfolger.
    klartext="STANDORT DREI KILOMETER NORDWESTLICH VOM WRACK {initialen}",
    selbst_zu_loesen="STANDORT DREI KILOMETER",
    weiterrechnen=(
        "Den Rest verschlüsselst du in Ruhe zu Ende, Zeile um Zeile mit dem "
        "Quadrat. Dann drückst du die Sendetaste."
    ),
)

FUNKSPRUCH_BOB_ZWEITE_ANTWORT = Funkspruch(
    kennung="bob_zweite_antwort",
    level=3,
    richtung=EMPFANGEN,
    verfahren=VIGENERE,
    absender="Zentrale",
    absender_kennung="bob",
    schluessel=SCHLUESSELWORT_DER_GESCHICHTE,
    einleitung=(
        "Die Antwort trifft verschlüsselt in Vigenère ein – der letzte "
        "Funkkontakt des Spiels."
    ),
    klartext="VERSTANDEN HILFE IST UNTERWEGS",
)


# ───────────────────────────────────────────────────────────────────────────
# Abschluss
# ───────────────────────────────────────────────────────────────────────────

#: Beschriftung des Buttons, der den Abschluss auslöst.
BESCHRIFTUNG_WARTEN = "Warten"

NACHTHIMMEL = Erzaehltext(
    kennung="nachthimmel",
    absaetze=(
        "Du schaltest das Funkgerät aus und wartest.",
        "Über der Wüste wird es still. Der Himmel ist klar, die Sterne stehen "
        "so dicht, wie du sie in der Stadt nie gesehen hast.",
        "Dann, weit entfernt, ein Geräusch. Rotorblätter.",
    ),
)

ABSCHLUSS = Erzaehltext(
    kennung="abschluss",
    absaetze=(
        "Du bist raus – lebend, aber mit leeren Händen. Der Diamantensack "
        "liegt noch im Wrack in der Wüste. Manchmal ist das Überleben der "
        "einzige Gewinn, den man mitnehmen kann.",
    ),
)


# ───────────────────────────────────────────────────────────────────────────
# Sichten für den Level-Zusammenbau (Phase 7)
# ───────────────────────────────────────────────────────────────────────────

#: Alle fünf Funksprüche in der Reihenfolge, in der sie im Spiel vorkommen.
FUNKSPRUECHE = (
    FUNKSPRUCH_ERSTER_RUF,
    FUNKSPRUCH_BOB_ERSTE_ANTWORT,
    FUNKSPRUCH_VERFOLGER,
    FUNKSPRUCH_STANDORT,
    FUNKSPRUCH_BOB_ZWEITE_ANTWORT,
)

#: Welche Funksprüche gehören zu welchem Level?
FUNKSPRUECHE_NACH_LEVEL = {
    1: (FUNKSPRUCH_ERSTER_RUF, FUNKSPRUCH_BOB_ERSTE_ANTWORT),
    2: (FUNKSPRUCH_VERFOLGER,),
    3: (FUNKSPRUCH_STANDORT, FUNKSPRUCH_BOB_ZWEITE_ANTWORT),
}

#: Alle Erzähltexte in Spielreihenfolge.
ERZAEHLTEXTE = (
    VORGESCHICHTE,
    INTRO,
    EINSTIEG_LEVEL_1,
    EINSTIEG_LEVEL_2,
    HINWEIS_HAEUFIGKEITSANALYSE,
    UEBERGANG_ZU_LEVEL_3,
    EINSTIEG_LEVEL_3,
    REFLEXIONSFRAGE_LEVEL_3,
    NACHTHIMMEL,
    ABSCHLUSS,
)
