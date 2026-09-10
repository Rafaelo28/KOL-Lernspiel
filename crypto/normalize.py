"""Textkonvention des Spiels – verbindlich für alle drei Verfahren.

Diese Datei ist die *eine* Stelle, an der festgelegt ist, wie Text im Spiel
aussieht. Sie entstand aus Aufgabe 0.3 des Arbeitsplans; dieselben Regeln
stehen im Abschnitt "Textkonvention" der CLAUDE.md.

Warum das so früh festgelegt wird: Wenn Normalisierung und Vergleich nicht
sauber definiert sind, meldet das Fehlerhandling "falsch", obwohl die
Schüler:innen richtig gerechnet haben. Das verfälscht die Messdaten und damit
den ganzen Methodenvergleich.

────────────────────────────────────────────────────────────────────────────
Die Regeln
────────────────────────────────────────────────────────────────────────────

1. GROSSBUCHSTABEN
   Intern wird jeder Text auf Großbuchstaben normalisiert – Klartext,
   Geheimtext, Nutzereingabe und Lösung gleichermaßen. Die Handbuchtexte
   ("HUND", "ZEIT WIRD KNAPP") sind ohnehin schon so geschrieben.
   Kleinschreibung in der Eingabe ist also erlaubt und nie ein Fehler.

2. NUR A–Z WERDEN VERSCHLÜSSELT
   Das Arbeitsalphabet ist A–Z (26 Zeichen, ohne Umlaute). Das Leerzeichen
   ist das einzige weitere zugelassene Zeichen und bleibt beim Ver- und
   Entschlüsseln unverändert stehen.

3. LEERZEICHEN BLEIBEN IM GEHEIMTEXT ERHALTEN
   Aus "ZEIT WIRD KNAPP" wird also nicht "ZEITWIRDKNAPP", sondern ein
   Geheimtext mit denselben Wortgrenzen.
   Jede Art von Weissraum gilt dabei als Wortgrenze und wird zu einem
   einfachen Leerzeichen: Tabulator, Zeilenumbruch und auch das geschuetzte
   Leerzeichen U+00A0. Das ist wichtig, weil beim Kopieren aus einem PDF
   oder einer Webseite regelmaessig geschuetzte Leerzeichen mitkommen - sie
   nach Regel 6 zu loeschen wuerde zwei Woerter unsichtbar verkleben.
   Begründung: Ohne Wortgrenzen wird das Abzählen langer Sätze von Hand für
   die Zielgruppe (Schulklasse, 20 Minuten pro Level) zu fehleranfällig.
   Sicherheitstechnisch ist das ein Nachteil – für ein Lernspiel ist die
   Nachvollziehbarkeit wichtiger.

4. BEIM VERGLEICH WERDEN LEERZEICHEN IGNORIERT
   Wer "ZEITWIRDKNAPP" oder "ZEIT  WIRD KNAPP" eingibt, hat die Aufgabe
   richtig gelöst. Ein vergessenes oder doppeltes Leerzeichen ist kein
   inhaltlicher Fehler und darf nicht als Fehlversuch zählen – sonst
   verbraucht es einen der drei Versuche aus der 3-Versuche-Regel.

5. UMLAUTE UND SS WERDEN ERSETZT, NICHT ABGEWIESEN
   Ä → AE, Ö → OE, Ü → UE, ß → SS.
   Begründung: Der erste echte Funkspruch lautet "Hallo, hört mich jemand?"
   und enthält ein ö. Eine Fehlermeldung statt einer Ersetzung würde Zeit im
   festen 15-Minuten-Fenster kosten und die Messdaten verzerren, ohne dass
   irgendetwas über Verschlüsselung gelernt wird. Die Ersetzung geschieht
   still im Hintergrund – für den Spieler ändert sich nichts, außer dass im
   Aufgabentext von vornherein "HOERT" steht.
   Das gilt unabhängig davon, wie der Umlaut in Unicode geschrieben ist: "ö"
   als ein Zeichen und "o" plus getrenntes Umlautzeichen sehen gleich aus und
   werden gleich behandelt.

   Andere Akzentbuchstaben behalten ihren Grundbuchstaben, statt ganz zu
   verschwinden: É → E, Ç → C, Å → A. Das ist keine Nebensache – "Théo
   Lambert" ist einer der fünf wählbaren Charaktere, und "THO LAMBERT" wäre
   ein sichtbarer Fehler im Spiel.

   Die Grenze dieser Regel: Sie greift nur, wenn sich das Zeichen in
   Grundbuchstabe und Akzent zerlegen lässt. Buchstaben, bei denen der Strich
   fest zum Zeichen gehört (Ø, Ł, Đ, Ħ), und Ligaturen (Æ, Œ) lassen sich
   nicht zerlegen und fallen deshalb unter Regel 6 – sie verschwinden. In den
   Handbuchtexten, den Funksprüchen und den fünf Charakternamen kommt keines
   dieser Zeichen vor; sollte je eines dazukommen, gehört es ausdrücklich in
   UMLAUT_ERSATZ.

6. ALLE ÜBRIGEN ZEICHEN WERDEN ENTFERNT
   Satzzeichen, Ziffern und Sonderzeichen fallen beim Normalisieren weg
   (aus "Hallo, hört mich jemand?" wird "HALLO HOERT MICH JEMAND").
   Wichtig für die UI: Angezeigt wird immer der bereits normalisierte Text.
   Sonst steht im Aufgabentext ein Komma, das in der Lösung fehlt – und die
   Spielenden suchen den Fehler an der falschen Stelle.

7. VIGENÈRE: LEERZEICHEN ZÄHLEN DEN SCHLÜSSELINDEX NICHT WEITER
   Das Schlüsselwort rückt nur bei Buchstaben eine Stelle vor. Andernfalls
   stimmt das durchgerechnete Handbuch-Beispiel (HUND + ROT → YIGU) nicht
   mehr mit mehrwortigen Sätzen überein.

────────────────────────────────────────────────────────────────────────────
Welche Fehlerart wann
────────────────────────────────────────────────────────────────────────────

Gilt für alle Module in ``crypto/``, damit die Oberfläche in Phase 6 nicht
je Level einen anderen Fehler abfangen muss:

* ``TypeError``  – falscher **Typ**. Das ist ein Programmierfehler im
  aufrufenden Code, zum Beispiel eine Zahl statt eines Texts. So etwas darf
  nie durch eine Spielereingabe entstehen.
* ``ValueError`` – richtiger Typ, aber unbrauchbarer **Wert**: ein
  Schlüsselwort mit Leerzeichen, eine Tabelle mit doppeltem Geheimbuchstaben,
  ein Zeichen, das kein Buchstabe von A bis Z ist.

────────────────────────────────────────────────────────────────────────────
Achtung für Aufgabe 4.2 ("Stelle 3 stimmt nicht")
────────────────────────────────────────────────────────────────────────────

Es gibt zwei verschiedene Positionen für denselben Buchstaben, und sie
stimmen nicht überein:

* die **Buchstabenposition** in ``ohne_leerzeichen(text)`` – danach wird
  verglichen (Regel 4),
* die **Anzeigeposition** im normalisierten Text mit Leerzeichen – die sehen
  die Spielenden vor sich.

Für "CHLW ZLUG NQDSS" ist der letzte Buchstabe die 13. der Buchstaben, steht
aber an 15. Stelle auf dem Bildschirm. Wer die Meldung aus der falschen Zählung
baut, schickt die Spielenden an eine Stelle, an der gar nichts falsch ist.

Die Umrechnung steht seit Aufgabe 4.2 in ``game/rueckmeldung.py``
(:func:`~game.rueckmeldung.erste_abweichung`). Sie führt beide Positionen mit
und nennt zusätzlich Wort und Buchstabe im Wort.
"""

import unicodedata

# Arbeitsalphabet (Regel 2). A = Index 0.
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Einziges zugelassenes Nicht-Buchstaben-Zeichen (Regeln 2 und 3).
LEERZEICHEN = " "

# Ersetzungen aus Regel 5. Werden angewendet, nachdem der Text auf
# Großbuchstaben gesetzt wurde – "ß".upper() ergibt in Python bereits "SS",
# der Eintrag bleibt trotzdem als Sicherheitsnetz stehen. "ẞ" ist die
# Großbuchstaben-Form von "ß" und fällt unter dieselbe Regel.
UMLAUT_ERSATZ = {
    "Ä": "AE",
    "Ö": "OE",
    "Ü": "UE",
    "ß": "SS",
    "ẞ": "SS",
}

# Dieselbe Regel für die zerlegte Schreibweise: Grundbuchstabe gefolgt vom
# Umlautzeichen U+0308. Diese Form bleibt übrig, wenn das Zeichen ein zweites
# Diakritikum trägt (etwa "ǖ" = u + Umlaut + Längsstrich) und deshalb nicht zu
# einem einzelnen "Ü" zusammengesetzt werden kann.
UMLAUT_ERSATZ_ZERLEGT = {
    "A\u0308": "AE",
    "O\u0308": "OE",
    "U\u0308": "UE",
}


def normalisieren(text):
    """Bringt beliebigen Text in die interne Form der Textkonvention.

    Ergebnis enthält ausschließlich A–Z und einfache Leerzeichen, ohne
    führende oder abschließende Leerzeichen.

    >>> normalisieren("Hallo, hört mich jemand?")
    'HALLO HOERT MICH JEMAND'
    >>> normalisieren("zeit   wird\\tknapp")
    'ZEIT WIRD KNAPP'

    Auch ein geschuetztes Leerzeichen (U+00A0, kommt beim Kopieren aus PDFs
    mit) gilt als Wortgrenze und nicht als zu loeschendes Sonderzeichen:

    >>> normalisieren("ALLES\\u00a0OK")
    'ALLES OK'

    Ein Umlaut wird auch dann ersetzt, wenn er in Unicode aus zwei Zeichen
    zusammengesetzt ist (Grundbuchstabe plus Umlautzeichen):

    >>> normalisieren("h\\u00f6rt"), normalisieren("ho\\u0308rt")
    ('HOERT', 'HOERT')

    Andere Akzentbuchstaben verlieren nur ihren Akzent, statt ganz zu
    verschwinden – wichtig fuer den Charakternamen "Th\u00e9o Lambert":

    >>> normalisieren("Th\\u00e9o Lambert")
    'THEO LAMBERT'

    Auch ein Umlaut mit zweitem Diakritikum wird noch erkannt:

    >>> normalisieren("\\u01d6ber")
    'UEBER'
    """
    if not isinstance(text, str):
        raise TypeError("normalisieren() erwartet einen Text (str).")

    # Vorbereitung: Ein "ö" kann in Unicode auf zwei Arten geschrieben sein –
    # als ein Zeichen (U+00F6) oder als "o" plus getrenntes Umlautzeichen
    # (U+006F U+0308). Beides sieht gleich aus, ist aber nicht dasselbe.
    # Die zweite Form entsteht beim Kopieren aus manchen PDFs und auf macOS.
    # Ohne dieses Zusammensetzen würde Regel 5 dort nicht greifen und "hört"
    # zu "HORT" statt "HOERT" werden – der Funkspruch wäre still verfälscht.
    text = unicodedata.normalize("NFC", text)

    # Regel 1: erst Großbuchstaben, ...
    text = text.upper()
    # ... dann Regel 5, weil die Ersatzformen selbst Großbuchstaben sind.
    for zeichen, ersatz in UMLAUT_ERSATZ.items():
        text = text.replace(zeichen, ersatz)

    # Alle übrigen Akzentbuchstaben werden jetzt in Grundbuchstabe und
    # Akzentzeichen zerlegt. Das Akzentzeichen fällt gleich unter Regel 6 weg,
    # der Grundbuchstabe bleibt stehen: aus "THÉO" wird "THEO" statt "THO".
    # Das betrifft echte Spielinhalte – "Théo Lambert" ist einer der fünf
    # wählbaren Charaktere.
    text = unicodedata.normalize("NFD", text)

    # Regel 5 noch einmal auf der zerlegten Form: Ein Umlaut, der wegen eines
    # zweiten Diakritikums nicht zusammengesetzt werden konnte, wird hier
    # eingefangen. Ohne diesen Schritt bliebe von "ǖ" nur ein "U" übrig.
    for zeichen, ersatz in UMLAUT_ERSATZ_ZERLEGT.items():
        text = text.replace(zeichen, ersatz)

    # Regel 2 und 6: A–Z behalten, jede Art von Weißraum zu einem Leerzeichen
    # machen, alles andere verwerfen.
    gefiltert = []
    for zeichen in text:
        if zeichen in ALPHABET:
            gefiltert.append(zeichen)
        elif zeichen.isspace():
            gefiltert.append(LEERZEICHEN)

    # Mehrfache Leerzeichen zusammenfassen und außen abschneiden.
    return LEERZEICHEN.join("".join(gefiltert).split())


def ohne_leerzeichen(text):
    """Normalisiert und entfernt zusätzlich alle Leerzeichen.

    Grundlage für Regel 4 (toleranter Vergleich) und für die Fehlermeldung
    "Stelle n stimmt nicht" aus Aufgabe 4.2, die auf Buchstabenpositionen
    ohne Leerzeichen zählt.

    >>> ohne_leerzeichen("Zeit wird knapp")
    'ZEITWIRDKNAPP'
    """
    return normalisieren(text).replace(LEERZEICHEN, "")


def vergleiche_tolerant(eingabe, loesung):
    """Prüft nach Regel 4, ob zwei Texte inhaltlich übereinstimmen.

    Groß-/Kleinschreibung, Leerzeichen, Umlautschreibweise und Satzzeichen
    spielen dabei keine Rolle.

    >>> vergleiche_tolerant("zeitwirdknapp", "ZEIT WIRD KNAPP")
    True
    >>> vergleiche_tolerant("ZEIT WIRD KNAP", "ZEIT WIRD KNAPP")
    False
    """
    return ohne_leerzeichen(eingabe) == ohne_leerzeichen(loesung)


def buchstabe_zu_index(buchstabe):
    """Wandelt einen Buchstaben in seinen Alphabet-Index um (A = 0, Z = 25).

    >>> buchstabe_zu_index("A"), buchstabe_zu_index("z")
    (0, 25)
    >>> buchstabe_zu_index("AB")
    Traceback (most recent call last):
    ValueError: 'AB' ist kein einzelner Buchstabe von A bis Z.
    """
    if not isinstance(buchstabe, str):
        raise TypeError("buchstabe_zu_index() erwartet einen Text (str).")
    grossbuchstabe = buchstabe.upper()
    # Die Laengenpruefung ist Pflicht: "AB" in ALPHABET waere ein Teilstring-
    # Treffer und wuerde stillschweigend den Index von "A" liefern.
    if len(grossbuchstabe) != 1 or grossbuchstabe not in ALPHABET:
        raise ValueError(
            f"'{buchstabe}' ist kein einzelner Buchstabe von A bis Z."
        )
    return ALPHABET.index(grossbuchstabe)


def index_zu_buchstabe(index):
    """Wandelt einen Alphabet-Index in den zugehörigen Buchstaben um.

    Der Index wird modulo 26 genommen – damit ist der Umbruch Z→A bzw. A→Z
    für alle Verfahren an genau dieser Stelle geregelt.

    >>> index_zu_buchstabe(0), index_zu_buchstabe(26), index_zu_buchstabe(-1)
    ('A', 'A', 'Z')
    """
    if isinstance(index, bool) or not isinstance(index, int):
        raise TypeError("index_zu_buchstabe() erwartet eine ganze Zahl (int).")
    return ALPHABET[index % len(ALPHABET)]
