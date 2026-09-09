"""Monoalphabetische Substitution – das Verfahren von Level 2.

Bei Cäsar wird das ganze Alphabet um dieselbe Zahl verschoben; das Muster ist
damit leicht zu durchschauen. Bei der Substitution bekommt stattdessen jeder
Buchstabe einen frei gewählten Ersatzbuchstaben. Es gibt kein
Verschiebungsmuster mehr, sondern nur noch eine Tabelle mit 26 Einträgen.
Weil ein Buchstabe dabei *immer* auf dasselbe Geheimzeichen abgebildet wird
(daher "mono-alphabetisch"), bleibt das Verfahren durch Häufigkeitsanalyse
knackbar – genau der Merksatz von Handbuchseite 2.

Die Standardtabelle des Spiels ist der Tastatur-Trick aus dem Handbuch: Man
liest die drei Buchstabenreihen einer Computertastatur der Reihe nach ab und
ordnet sie dem normalen Alphabet zu. Das ergibt genau 26 verschiedene
Buchstaben und muss deshalb nicht auswendig gelernt werden.

    Original  A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
    Geheim    Q W E R T Z U I O P A S D F G H J K L Y X C V B N M

Worauf die UI sich verlassen darf (Arbeitsplan 1.3 und 6.4)
-----------------------------------------------------------
* ``erzeuge_tastatur_tabelle()`` liefert ein ``dict`` mit genau 26 Einträgen,
  in der Reihenfolge des Originalalphabets A..Z. Es kann also unverändert
  Spalte für Spalte als Tabelle angezeigt werden.
* Jeder Aufruf liefert eine *neue* Kopie. Die UI darf das Ergebnis verändern,
  ohne dass ein anderer Teil des Spiels davon betroffen ist; einen geteilten
  Zustand gibt es in diesem Modul nicht.
* ``tabelle=None`` bedeutet überall "die Tastatur-Tabelle verwenden".
* Eine selbst übergebene Tabelle wird geprüft. Ist sie unbrauchbar, gibt es
  einen ``ValueError`` mit einer deutschen Meldung, die konkret benennt, was
  fehlt – die kann die UI direkt anzeigen.
* Leerzeichen bleiben stehen (Textkonvention Regel 3); alle übrigen Zeichen
  entfernt vorher :func:`crypto.normalize.normalisieren` (Regeln 1, 5, 6).
"""

from .normalize import ALPHABET, LEERZEICHEN, normalisieren

# Der Merk-Trick aus dem Handbuch: die drei Buchstabenreihen einer deutschen
# Computertastatur. Zusammengesetzt ergeben sie das Geheimalphabet.
TASTATUR_REIHEN = ("QWERTZUIOP", "ASDFGHJKL", "YXCVBNM")


def _pruefe_tabelle(tabelle):
    """Prüft eine Zuordnungstabelle und gibt sie als sortierte Kopie zurück.

    Verlangt wird genau das, was eine monoalphabetische Substitution
    umkehrbar macht: 26 Einträge, die Schlüssel sind die Buchstaben A–Z, die
    Werte sind 26 *verschiedene* Buchstaben A–Z. Wäre ein Geheimbuchstabe
    doppelt vergeben, ließe sich der Text nicht mehr eindeutig entschlüsseln.

    Die zurückgegebene Kopie ist nach A..Z sortiert; die Aufrufer arbeiten
    danach nie auf dem dict der UI weiter.
    """
    if not isinstance(tabelle, dict):
        raise TypeError(
            "Die Tabelle muss ein dict sein, das jedem Buchstaben A bis Z "
            "genau einen Geheimbuchstaben zuordnet."
        )

    # 1. Schlüsselseite: nur Buchstaben A–Z, und zwar alle 26.
    for schluessel in tabelle:
        if not isinstance(schluessel, str) or schluessel not in ALPHABET:
            raise ValueError(
                f"{schluessel!r} ist kein gültiger Tabellen-Eintrag; "
                "erlaubt sind nur die Buchstaben A bis Z."
            )
    fehlend = [buchstabe for buchstabe in ALPHABET if buchstabe not in tabelle]
    if fehlend:
        raise ValueError(
            f"Die Tabelle hat {len(tabelle)} statt 26 Einträge. "
            f"Es fehlen: {', '.join(fehlend)}."
        )

    # 2. Werteseite: einzelne Buchstaben A–Z, jeder nur einmal.
    belegt = {}
    for original in ALPHABET:
        geheim = tabelle[original]
        if not isinstance(geheim, str) or geheim not in ALPHABET:
            raise ValueError(
                f"Die Tabelle ordnet '{original}' den Wert {geheim!r} zu; "
                "erlaubt ist genau ein Buchstabe von A bis Z."
            )
        if geheim in belegt:
            raise ValueError(
                f"Der Geheimbuchstabe '{geheim}' ist doppelt vergeben "
                f"(an '{belegt[geheim]}' und '{original}')."
            )
        belegt[geheim] = original

    # 26 Schlüssel mit 26 verschiedenen Werten aus einem 26-Buchstaben-
    # Alphabet: damit ist die Tabelle automatisch vollständig umkehrbar.
    return {original: tabelle[original] for original in ALPHABET}


def erzeuge_tastatur_tabelle():
    """Baut die Tastatur-Tabelle aus :data:`TASTATUR_REIHEN`.

    Ergebnis ist ein neues ``dict`` mit 26 Einträgen in der Reihenfolge
    A..Z, also ``{"A": "Q", "B": "W", ...}``.

    >>> tabelle = erzeuge_tastatur_tabelle()
    >>> len(tabelle)
    26
    >>> "".join(tabelle[b] for b in ALPHABET)
    'QWERTZUIOPASDFGHJKLYXCVBNM'

    Die Handkontrolle aus dem Handbuch:

    >>> tabelle["A"], tabelle["B"], tabelle["H"], tabelle["U"]
    ('Q', 'W', 'I', 'X')
    >>> tabelle["N"], tabelle["D"], tabelle["Z"]
    ('F', 'R', 'M')
    """
    geheimalphabet = "".join(TASTATUR_REIHEN)
    # Diese Prüfung steht bewusst im Code und nicht nur im Test: Ein
    # Tippfehler in TASTATUR_REIHEN soll sofort auffallen und nicht erst
    # dadurch, dass ein Level unlösbare Aufgaben stellt.
    if len(geheimalphabet) != len(ALPHABET):
        raise ValueError(
            "TASTATUR_REIHEN muss zusammengesetzt genau 26 Buchstaben "
            f"ergeben, ergibt aber {len(geheimalphabet)}."
        )
    return _pruefe_tabelle(dict(zip(ALPHABET, geheimalphabet)))


def umkehren(tabelle):
    """Dreht eine Zuordnungstabelle um: Geheimbuchstabe -> Originalbuchstabe.

    Das ist die untere Zeile der Handbuch-Tabelle, von links nach rechts
    gelesen. Das Ergebnis ist nach dem Geheimbuchstaben A..Z sortiert, damit
    die UI auch diese Richtung ordentlich anzeigen kann.

    >>> rueckwaerts = umkehren(erzeuge_tastatur_tabelle())
    >>> rueckwaerts["I"], rueckwaerts["X"], rueckwaerts["F"], rueckwaerts["R"]
    ('H', 'U', 'N', 'D')
    >>> len(rueckwaerts)
    26

    Eine unbrauchbare Tabelle wird abgewiesen, und die Meldung sagt, woran
    es liegt:

    >>> kaputt = erzeuge_tastatur_tabelle()
    >>> kaputt["A"] = "W"          # 'W' gehört schon zu 'B'
    >>> try:
    ...     umkehren(kaputt)
    ... except ValueError as fehler:
    ...     print(fehler)
    Der Geheimbuchstabe 'W' ist doppelt vergeben (an 'A' und 'B').
    """
    geprueft = _pruefe_tabelle(tabelle)
    rueckwaerts = {geheim: original for original, geheim in geprueft.items()}
    return {geheim: rueckwaerts[geheim] for geheim in ALPHABET}


def _tabelle_oder_standard(tabelle):
    """Liefert die geprüfte Arbeitstabelle; ``None`` heißt Tastatur-Tabelle."""
    if tabelle is None:
        return erzeuge_tastatur_tabelle()
    return _pruefe_tabelle(tabelle)


def _ersetzen(text, geprueft):
    """Ersetzt jeden Buchstaben nach der Tabelle, Leerzeichen bleiben stehen."""
    ergebnis = []
    for zeichen in normalisieren(text):
        if zeichen == LEERZEICHEN:
            ergebnis.append(LEERZEICHEN)
        else:
            ergebnis.append(geprueft[zeichen])
    return "".join(ergebnis)


def verschluesseln(text, tabelle=None):
    """Verschlüsselt Text, indem jeder Buchstabe durch sein Geheimzeichen ersetzt wird.

    Ohne ``tabelle`` wird die Tastatur-Tabelle des Handbuchs verwendet.

    >>> verschluesseln("HUND")
    'IXFR'
    >>> verschluesseln("Hund")
    'IXFR'

    Leerzeichen bleiben als Wortgrenze stehen, Satzzeichen fallen weg:

    >>> verschluesseln("Zeit wird knapp!")
    'MTOY VOKR AFQHH'

    Eine eigene Tabelle wird genauso benutzt:

    >>> eigene = erzeuge_tastatur_tabelle()
    >>> verschluesseln("HUND", eigene)
    'IXFR'
    """
    return _ersetzen(text, _tabelle_oder_standard(tabelle))


def entschluesseln(text, tabelle=None):
    """Entschlüsselt Text, indem die Tabelle rückwärts gelesen wird.

    ``tabelle`` ist dieselbe Original -> Geheim-Tabelle wie beim
    Verschlüsseln; das Umdrehen erledigt diese Funktion selbst.

    >>> entschluesseln("IXFR")
    'HUND'
    >>> entschluesseln("MTOY VOKR AFQHH")
    'ZEIT WIRD KNAPP'
    >>> entschluesseln(verschluesseln("ALLES OK"))
    'ALLES OK'
    """
    return _ersetzen(text, umkehren(_tabelle_oder_standard(tabelle)))


# Beim Import einmal durchrechnen: Sind die drei Tastaturreihen nicht genau
# 26 verschiedene Buchstaben A–Z, scheitert das Spiel sofort beim Start und
# nicht erst mitten in Level 2.
erzeuge_tastatur_tabelle()
