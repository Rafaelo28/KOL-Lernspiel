"""Zusatzaufgaben (Arbeitsplan 5.4).

Wer mit den Pflichtaufgaben eines Levels durch ist und noch Zeit übrig hat,
bekommt weitere Übungen aus demselben Pool – damit im festen Zeitfenster
niemand dasitzt und wartet, während andere noch rechnen.

Warum nicht nach Tempo
──────────────────────
Ursprünglich bekam eine Zusatzaufgabe, wer "deutlich schneller" war als
erwartet: unter 60 % der geschätzten Zeit. Bei einer mittleren Übung
(zwölf Buchstaben) hiess das **unter 41 Sekunden** für Lesen, Rechnen, Tippen
und Prüfen. Für Sechst- bis Achtklässler, die das Verfahren gerade erst
gesehen haben, ist das sehr sportlich – die Schwelle wäre vermutlich nie
erreicht worden, und zwar **lautlos**: kein Fehler, kein Hinweis, nur eine
Funktion, die im Klassenzimmer nie greift.

Dazu kommt: Der Pflichtteil eines Levels füllt nach diesen Schätzungen nur
ein Fünftel bis ein Drittel seines Zeitfensters. Ohne Zusatzaufgaben wäre der
Rest Leerlauf – und die Spielgruppe hätte deutlich weniger Lernzeit als die
Kontrollgruppe, die ihre 15/20/25 Minuten voll nutzt. Das wäre ein
Unterschied zwischen den Gruppen, der nichts mit der Methode zu tun hat.

Deshalb entscheidet jetzt die Zeit, nicht das Tempo: Solange die Restzeit
für eine weitere Übung **und** für die noch offenen Funksprüche reicht, kommt
eine. Begrenzt wird das durch :data:`HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL` und
den Übungspool.

Wie "erwartet" berechnet wird
─────────────────────────────
Nicht als Sekunden je Buchstabe. Jede Aufgabe hat eine **Grundzeit**, die
nichts mit ihrer Länge zu tun hat: die Aufgabe lesen, den Schlüssel
nachschlagen, das Eingabefeld anklicken, tippen, prüfen. Bei einem Wort mit
vier Buchstaben macht diese Grundzeit fast alles aus, bei einem Funkspruch mit
fünfundzwanzig fällt sie kaum ins Gewicht.

Ein reines "Sekunden je Buchstabe" würde deshalb systematisch danebenliegen:
Kurze Aufgaben sähen immer langsam aus, lange immer schnell – gemessen würde
am Ende die Länge der gezogenen Aufgabe, nicht das Tempo der Person.

Gerechnet wird darum mit einer Geraden::

    erwartet = GRUNDZEIT + BUCHSTABEN * SEKUNDEN_JE_BUCHSTABE

Gebraucht wird sie zweimal: um zu sehen, ob die Restzeit noch reicht, und um
das eigene Tempo daran zu messen (:func:`tempofaktor`).

Die Zahlen sind Schätzungen
───────────────────────────
Beide stehen an genau dieser Stelle und gehören im Pilotdurchlauf
(Arbeitsplan 8.2) nachgemessen: zwei, drei Personen spielen lassen, im Log die
Spalten ``sekunden`` und ``gerechnete_buchstaben`` gegeneinander auftragen und
die Gerade daran anpassen – ohne die Zeilen mit ``abgebrochen = ja``, dort ist
die Zeit keine Rechenzeit. Erst danach sind die Werte belastbar.

Warum es eine Obergrenze gibt
─────────────────────────────
:data:`HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL` begrenzt, wie viele Extraaufgaben
ein Level hergibt. Zwei Gründe:

* Der Pool gibt je Level sechs Texte her. Danach wiederholen sie sich, und aus
  dem Üben wird stures Abarbeiten.
* Wäre die Schwelle nach dem Pilotdurchlauf versehentlich zu grosszügig
  gesetzt, liefe sonst eine Endlosschleife bis zum Zeitablauf – im Log stünden
  dann hundert Zeilen, die nichts aussagen, und die Person käme nie zum
  Funkspruch, der die Geschichte trägt.

Warum die Restzeit mitentscheidet
─────────────────────────────────
Projektregel 1: Zusatzaufgaben verlängern ein Zeitfenster nie. Eine Aufgabe
kurz vor Schluss zu stellen heisst, sie unfertig abzubrechen – das frustriert
und erzeugt eine Logzeile, die nur "Zeit war um" sagt.

Welcher Text als Zusatzaufgabe kommt, steht vorher nicht fest. Gerechnet wird
deshalb mit dem **längsten** Text im Pool, nicht mit der Aufgabe, die gerade
gelöst wurde. Seit alle Level denselben Pool mit ähnlich langen Sätzen haben,
liegen dazwischen nur noch 10 gegen 14 Buchstaben – aber auch vier Buchstaben
mehr kosten eine Viertelminute.

Reserviert wird dabei auch die Zeit für die **Funksprüche**, die im Level noch
ausstehen (Vorrang-Regel, Arbeitsplan Phase 7): Sie tragen die Geschichte und
dürfen nicht ausfallen, weil davor noch eine Übung lief. Was daraus für den
Ablauf folgt, steht in :mod:`game.levelablauf`; hier steht nur, wie lange es
voraussichtlich dauert.

Warum nur Übungen eine Zusatzaufgabe auslösen
─────────────────────────────────────────────
Die Zusammenfassung legt den Ablauf fest: "Übungsaufgaben (+ ggf.
Zusatzaufgaben) → echte Sendeaufgabe → Bobs Antwort". Zusatzaufgaben gehören
also in die Übungsphase und kommen "aus demselben Wortpool". Nach einem
Funkspruch hat die Geschichte schon begonnen – eine Handbuch-Übung zwischen
dem eigenen Ruf und Bobs Antwort risse sie auseinander.
"""

from content import uebungen as _uebungen
from crypto.normalize import ohne_leerzeichen as _ohne_leerzeichen
from game.aufgabe import QUELLE_UEBUNG

#: Feste Zeit je Aufgabe, unabhängig von ihrer Länge: lesen, Schlüssel
#: nachschlagen, Eingabefeld anklicken, tippen, prüfen. Schätzwert.
ERWARTETE_GRUNDZEIT_SEKUNDEN = 20.0

#: Zeit je Buchstabe, der von Hand gerechnet werden muss. Schätzwert.
ERWARTETE_SEKUNDEN_JE_BUCHSTABE = 4.0

#: So viele Zusatzaufgaben gibt es je Level höchstens. Zusammen mit den zwei
#: Pflichtübungen sind das sechs – genau so viele Texte, wie der Pool je Level
#: hergibt (achtzehn, gleichmässig auf drei Level verteilt). Danach würden sich
#: die Sätze wiederholen.
HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL = 4

#: So viel Zeit muss im Level mindestens übrig sein, zusätzlich zu der Zeit,
#: die die Zusatzaufgabe voraussichtlich kostet.
MINDESTRESTZEIT_SEKUNDEN = 60.0

#: In diesen Grenzen bleibt der Tempofaktor (siehe :func:`tempofaktor`). Nach
#: oben, damit eine einzelne liegengelassene Aufgabe nicht den ganzen Ablauf
#: umwirft; nach unten, damit niemand durch zwei Glückstreffer die Schätzung
#: halbiert.
TEMPO_GRENZEN = (0.5, 3.0)


def erwartete_dauer(laenge_in_buchstaben):
    """Wie lange eine Aufgabe dieser Länge voraussichtlich dauert.

    >>> erwartete_dauer(4)
    36.0
    >>> erwartete_dauer(25)
    120.0
    """
    return (
        ERWARTETE_GRUNDZEIT_SEKUNDEN
        + laenge_in_buchstaben * ERWARTETE_SEKUNDEN_JE_BUCHSTABE
    )


def erwartete_dauer_funksprueche(funksprueche):
    """Wie lange die angegebenen Funksprüche zusammen voraussichtlich dauern.

    Gerechnet wird mit dem Teil, der von Hand gelöst wird – den Rest löst ein
    Knopf auf (siehe ``content/story.py``).

    >>> from content import story
    >>> erwartete_dauer_funksprueche(story.FUNKSPRUECHE_NACH_LEVEL[1])
    180.0
    >>> erwartete_dauer_funksprueche(())
    0
    """
    return sum(erwartete_dauer(funkspruch.buchstaben_von_hand) for funkspruch in funksprueche)


def tempofaktor(bearbeitungen):
    """Wie viel langsamer oder schneller jemand rechnet, als oben geschätzt.

    Eins heisst "wie geschätzt", zwei "doppelt so lange". Gezählt werden nur
    Aufgaben, an denen wirklich gerechnet wurde: abgebrochene nicht (dort ist
    die Zeit die bis zum Levelwechsel) und solche ohne gerechnete Buchstaben
    auch nicht. Ohne solche Aufgaben ist der Faktor eins.

    Warum das nötig ist: Die Gerade oben ist ein Mittelwert für alle. Die
    Vorrang-Regel (:mod:`game.levelablauf`) soll aber gerade die Langsamen
    davor schützen, dass ihnen am Ende die Funksprüche fehlen – und genau für
    die reserviert ein Mittelwert zu wenig Zeit. Ein Kind, das dreimal so
    lange braucht, bekäme sonst noch eine Übung angeboten und verlöre dafür
    Bobs Antwort.

    >>> tempofaktor(())
    1.0
    """
    ist = soll = 0.0
    for bearbeitung in bearbeitungen:
        if bearbeitung.abgebrochen or not bearbeitung.gerechnete_buchstaben:
            continue
        ist += bearbeitung.benoetigte_sekunden
        soll += erwartete_dauer(bearbeitung.gerechnete_buchstaben)
    if not soll:
        return 1.0
    unten, oben = TEMPO_GRENZEN
    return min(oben, max(unten, ist / soll))


def laengste_uebung():
    """Die Buchstabenzahl des längsten Übungstextes – alle Level ziehen aus demselben Pool.

    >>> laengste_uebung()
    14
    """
    return max(len(_ohne_leerzeichen(text)) for text in _uebungen.UEBUNGSTEXTE)


def zeit_reicht_noch(verbleibende_sekunden, offene_funksprueche=(), tempo=1.0):
    """Bleibt im Level genug Zeit, damit noch eine Übung Sinn ergibt?

    Gerechnet wird mit dem **längsten** Text im Pool, nicht mit der eben
    gelösten Aufgabe – welcher Text als Nächstes kommt, steht nicht fest.

    ``offene_funksprueche`` sind die Funksprüche, die im Level noch anstehen;
    ihre Zeit wird mitreserviert (Vorrang-Regel, Arbeitsplan Phase 7).
    ``tempo`` ist der Faktor aus :func:`tempofaktor`: Wer langsamer rechnet,
    braucht für dieselbe Aufgabe länger, und die Grenze rückt entsprechend
    früher. Der Sicherheitspuffer bleibt davon unberührt.

    >>> zeit_reicht_noch(900)
    True
    >>> zeit_reicht_noch(100)
    False
    >>> zeit_reicht_noch(280), zeit_reicht_noch(280, tempo=3.0)
    (True, False)
    """
    noetig = erwartete_dauer(laengste_uebung()) + erwartete_dauer_funksprueche(offene_funksprueche)
    return verbleibende_sekunden >= tempo * noetig + MINDESTRESTZEIT_SEKUNDEN


def obergrenze_erreicht(bisherige_zusatzaufgaben):
    """Sind in diesem Level schon genug Extraaufgaben gestellt worden?"""
    return bisherige_zusatzaufgaben >= HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL


def ist_faellig(bearbeitung, verbleibende_sekunden, bisherige_zusatzaufgaben=0, offene_funksprueche=(),
                tempo=1.0):
    """Soll nach dieser Aufgabe eine Zusatzaufgabe gestellt werden?

    Alle drei Bedingungen müssen stimmen: Es war eine Übung, es bleibt genug
    Zeit – auch für die noch offenen Funksprüche des Levels –, und die
    Obergrenze des Levels ist noch nicht erreicht.
    """
    if bearbeitung.aufgabe.quelle != QUELLE_UEBUNG:
        return False
    if obergrenze_erreicht(bisherige_zusatzaufgaben):
        return False
    return zeit_reicht_noch(verbleibende_sekunden, offene_funksprueche, tempo)
