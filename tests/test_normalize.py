"""Tests fuer crypto/normalize.py – die Textkonvention des Spiels.

Grundlage der Erwartungswerte sind ausschliesslich
  * die sieben Regeln im Docstring-Kopf von crypto/normalize.py und
  * dokumentation/Handbuchtexte.md (Referenzwerte, Uebungswoerter, Uebungssaetze).

Alle Erwartungswerte in dieser Datei wurden von Hand hergeleitet, nicht aus
einem Funktionsaufruf uebernommen. Wo eine Herleitung nicht offensichtlich ist,
steht sie als Kommentar oder im Docstring des jeweiligen Tests.

Warum das Modul so gruendlich geprueft wird: normalize.py entscheidet, ob eine
richtig gerechnete Schuelerloesung als richtig erkannt wird. Ein Fehler hier
kostet Versuche aus der 3-Versuche-Regel und verfaelscht damit die Messdaten
des Methodenvergleichs.
"""

import pytest
from content import uebungen

from crypto.normalize import (
    ALPHABET,
    LEERZEICHEN,
    UMLAUT_ERSATZ,
    buchstabe_zu_index,
    index_zu_buchstabe,
    normalisieren,
    ohne_leerzeichen,
    vergleiche_tolerant,
)

# ───────────────────────────────────────────────────────────────────────────
# Testdaten aus dokumentation/Handbuchtexte.md
# ───────────────────────────────────────────────────────────────────────────

# Das Uebungsmaterial des Handbuchs kommt seit Aufgabe 2.2 aus
# content/uebungen.py. tests/test_uebungen.py haelt es gegen das Markdown der
# Quelle; hier wird es nur benutzt.
UEBUNGSWOERTER_CAESAR = list(uebungen.UEBUNGSWOERTER_LEVEL_1)
UEBUNGSSAETZE_SUBSTITUTION = list(uebungen.UEBUNGSSAETZE_LEVEL_2)
UEBUNGSSAETZE_VIGENERE = list(uebungen.UEBUNGSSAETZE_LEVEL_3)
ALLE_UEBUNGSTEXTE = list(uebungen.ALLE_UEBUNGSTEXTE)

# Seite 2: Tastatur-Trick als Geheimalphabet
# Q W E R T Z U I O P / A S D F G H J K L / Y X C V B N M
TASTATUR_GEHEIMALPHABET = "QWERTZUIOP" "ASDFGHJKL" "YXCVBNM"

# Die drei echten Funksprueche aus dokumentation/Konzept_Spiel.md. Sie sind
# im Rohzustand geschrieben (Umlaute, Satzzeichen, Ziffern) und damit der
# eigentliche Anwendungsfall der Regeln 5 und 6.
FUNKSPRUCH_ERSTKONTAKT = "Hallo, hört mich jemand?"
FUNKSPRUCH_BOB = (
    "Ja, wir hören dich. Aber Caesar ist in Minuten zu knacken – "
    "nimm die nächste Methode im Handbuch."
)
FUNKSPRUCH_VERFOLGER = (
    "Quadrant 4 ist durchsucht, wir gehen jetzt auf Quadrant 7 – "
    "wir finden den Verräter."
)


# ───────────────────────────────────────────────────────────────────────────
# 1. Die Konstanten
# ───────────────────────────────────────────────────────────────────────────

def test_alphabet_ist_das_arbeitsalphabet_a_bis_z():
    """Regel 2: Das Arbeitsalphabet sind genau die 26 Buchstaben A bis Z."""
    assert ALPHABET == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    assert len(ALPHABET) == 26
    assert len(set(ALPHABET)) == 26


def test_alphabet_enthaelt_keine_umlaute():
    """Regel 2 und 5: Umlaute gehoeren nicht ins Arbeitsalphabet."""
    for umlaut in ("Ä", "Ö", "Ü", "ß"):
        assert umlaut not in ALPHABET


def test_leerzeichen_ist_ein_einfaches_leerzeichen():
    """Regel 2: Das Leerzeichen ist das einzige weitere zugelassene Zeichen."""
    assert LEERZEICHEN == " "
    assert len(LEERZEICHEN) == 1


@pytest.mark.parametrize(
    "umlaut, erwartet",
    [("Ä", "AE"), ("Ö", "OE"), ("Ü", "UE"), ("ß", "SS")],
)
def test_umlaut_ersatz_deckt_regel_5_ab(umlaut, erwartet):
    """Regel 5 nennt genau diese vier Ersetzungen."""
    assert UMLAUT_ERSATZ[umlaut] == erwartet


def test_umlaut_ersatz_ergibt_nur_alphabetbuchstaben():
    """Ein Ersatz, der selbst kein A-Z waere, wuerde spaeter still wegfallen."""
    for ersatz in UMLAUT_ERSATZ.values():
        assert ersatz != ""
        for zeichen in ersatz:
            assert zeichen in ALPHABET


# ───────────────────────────────────────────────────────────────────────────
# 2. normalisieren()
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "eingabe, erwartet",
    [
        ("hund", "HUND"),
        ("Hund", "HUND"),
        ("HUND", "HUND"),
        ("hUnD", "HUND"),
        ("zeit wird knapp", "ZEIT WIRD KNAPP"),
    ],
)
def test_normalisieren_macht_grossbuchstaben(eingabe, erwartet):
    """Regel 1: Intern ist alles gross; Kleinschreibung ist nie ein Fehler."""
    assert normalisieren(eingabe) == erwartet


@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE)
def test_normalisieren_laesst_handbuchtexte_unveraendert(text):
    """Die Handbuchtexte stehen schon in der internen Form (Regeln 1 bis 3)."""
    assert normalisieren(text) == text


@pytest.mark.parametrize(
    "eingabe, erwartet",
    [
        # Regel 5: Ä->AE, Ö->OE, Ü->UE, ß->SS.
        ("Ärger", "AERGER"),
        ("Öl", "OEL"),
        ("über", "UEBER"),
        ("Straße", "STRASSE"),
        ("Fußball", "FUSSBALL"),
        ("ÄÖÜ", "AEOEUE"),
        ("äöü", "AEOEUE"),
        ("GRÜSSE", "GRUESSE"),
        ("hört", "HOERT"),
        # "ẞ" ist die Grossbuchstabenform von "ß" und faellt unter dieselbe Regel.
        ("ẞ", "SS"),
        # Ein Umlaut wird zu zwei Buchstaben, der Text wird also laenger.
        ("MÜDE", "MUEDE"),
    ],
)
def test_normalisieren_ersetzt_umlaute(eingabe, erwartet):
    """Regel 5: Umlaute werden ersetzt, nicht abgewiesen."""
    assert normalisieren(eingabe) == erwartet


@pytest.mark.parametrize(
    "eingabe, erwartet",
    [
        # Regel 6: Satzzeichen, Ziffern und Sonderzeichen fallen weg.
        ("HUND!", "HUND"),
        ("H.U.N.D.", "HUND"),
        ("A1B2C3", "ABC"),
        ("2024", ""),
        ("HUND (3)", "HUND"),
        ("ZEIT-WIRD-KNAPP", "ZEITWIRDKNAPP"),
        ("@#$%&", ""),
        ("[Initialen]", "INITIALEN"),
        # Akzentbuchstaben verlieren nach Regel 5 nur ihren Akzent, der
        # Grundbuchstabe bleibt stehen. Andernfalls wuerde aus dem Charakter
        # "Théo Lambert" im Spiel "THO LAMBERT".
        ("Café", "CAFE"),
        ("Théo Lambert", "THEO LAMBERT"),
        ("Curaçao", "CURACAO"),
    ],
)
def test_normalisieren_entfernt_satzzeichen_und_ziffern(eingabe, erwartet):
    """Regel 6: Alles ausser A-Z und Leerzeichen wird entfernt."""
    assert normalisieren(eingabe) == erwartet


def test_normalisieren_entfernt_zeichen_ohne_ersatzleerzeichen():
    """Regel 6 fuegt kein Leerzeichen ein, wo ein Zeichen verschwindet.

    Aus "ALLES,OK" wird deshalb "ALLESOK" und nicht "ALLES OK". Das ist
    unkritisch, weil beim Vergleich nach Regel 4 ohnehin ohne Leerzeichen
    geprueft wird.
    """
    assert normalisieren("ALLES,OK") == "ALLESOK"
    assert vergleiche_tolerant("ALLES,OK", "ALLES OK") is True


@pytest.mark.parametrize(
    "eingabe, erwartet",
    [
        (FUNKSPRUCH_ERSTKONTAKT, "HALLO HOERT MICH JEMAND"),
        (
            FUNKSPRUCH_BOB,
            "JA WIR HOEREN DICH ABER CAESAR IST IN MINUTEN ZU KNACKEN "
            "NIMM DIE NAECHSTE METHODE IM HANDBUCH",
        ),
        (
            FUNKSPRUCH_VERFOLGER,
            "QUADRANT IST DURCHSUCHT WIR GEHEN JETZT AUF QUADRANT "
            "WIR FINDEN DEN VERRAETER",
        ),
    ],
)
def test_normalisieren_verarbeitet_die_echten_funksprueche(eingabe, erwartet):
    """Regeln 1, 5 und 6 am eigentlichen Anwendungsfall.

    Von Hand hergeleitet, z. B. fuer den Erstkontakt:
    "Hallo, hört mich jemand?" -> gross -> "HALLO, HÖRT MICH JEMAND?"
    -> Ö wird OE -> "HALLO, HOERT MICH JEMAND?"
    -> Komma und Fragezeichen fallen weg -> "HALLO HOERT MICH JEMAND".
    Der Gedankenstrich in den beiden langen Funkspruechen verschwindet
    zwischen zwei Leerzeichen; die bleiben als ein Leerzeichen uebrig.
    """
    assert normalisieren(eingabe) == erwartet


@pytest.mark.parametrize(
    "eingabe, erwartet",
    [
        ("ZEIT  WIRD KNAPP", "ZEIT WIRD KNAPP"),
        ("ZEIT     WIRD     KNAPP", "ZEIT WIRD KNAPP"),
        ("A  B  C", "A B C"),
    ],
)
def test_normalisieren_fasst_mehrfache_leerzeichen_zusammen(eingabe, erwartet):
    """Doppelte Leerzeichen sind kein inhaltlicher Unterschied (Regel 4)."""
    assert normalisieren(eingabe) == erwartet


@pytest.mark.parametrize(
    "eingabe",
    ["  HUND", "HUND  ", "   HUND   ", "\tHUND\n"],
)
def test_normalisieren_entfernt_aeussere_leerzeichen(eingabe):
    """Fuehrende und abschliessende Leerzeichen gehoeren nicht zum Text."""
    assert normalisieren(eingabe) == "HUND"


@pytest.mark.parametrize(
    "eingabe",
    ["ZEIT\tWIRD\tKNAPP", "ZEIT\nWIRD\nKNAPP", "ZEIT \t WIRD \n KNAPP"],
)
def test_normalisieren_wandelt_weissraum_in_leerzeichen(eingabe):
    """Tabulator und Zeilenumbruch sind Wortgrenzen wie das Leerzeichen."""
    assert normalisieren(eingabe) == "ZEIT WIRD KNAPP"


@pytest.mark.parametrize(
    "eingabe",
    ["", " ", "   ", "\t", "\n", " \t \n ", ",.-!?", "1234", "   ,   "],
)
def test_normalisieren_gibt_leeren_text_zurueck(eingabe):
    """Randfall: Bleibt kein Buchstabe uebrig, ist das Ergebnis leer."""
    assert normalisieren(eingabe) == ""


@pytest.mark.parametrize(
    "eingabe",
    ALLE_UEBUNGSTEXTE
    + [FUNKSPRUCH_ERSTKONTAKT, FUNKSPRUCH_BOB, FUNKSPRUCH_VERFOLGER,
       "", "   ", "Straße 7!", "  hund  "],
)
def test_normalisieren_erzeugt_nur_erlaubte_zeichen(eingabe):
    """Regeln 2, 3 und 6: Das Ergebnis enthaelt nur A-Z und einfache Leerzeichen."""
    ergebnis = normalisieren(eingabe)
    for zeichen in ergebnis:
        assert zeichen in ALPHABET or zeichen == LEERZEICHEN
    assert LEERZEICHEN * 2 not in ergebnis
    assert ergebnis == ergebnis.strip()


@pytest.mark.parametrize(
    "eingabe",
    ALLE_UEBUNGSTEXTE
    + [FUNKSPRUCH_ERSTKONTAKT, FUNKSPRUCH_BOB, FUNKSPRUCH_VERFOLGER,
       "", "   ", "Straße 7!"],
)
def test_normalisieren_ist_idempotent(eingabe):
    """Rundlauf: Bereits normalisierter Text darf sich nicht mehr aendern.

    Das ist die Rundlauf-Eigenschaft dieses Moduls: Die UI zeigt nach Regel 6
    den bereits normalisierten Text an, und der muss ein zweites Mal
    durchgereicht identisch bleiben.
    """
    einmal = normalisieren(eingabe)
    assert normalisieren(einmal) == einmal


@pytest.mark.parametrize("satz", UEBUNGSSAETZE_SUBSTITUTION + UEBUNGSSAETZE_VIGENERE)
def test_normalisieren_erhaelt_leerzeichenpositionen(satz):
    """Regel 3: Leerzeichen bleiben an genau denselben Stellen stehen."""
    positionen_vorher = [i for i, z in enumerate(satz) if z == LEERZEICHEN]
    ergebnis = normalisieren(satz)
    positionen_nachher = [i for i, z in enumerate(ergebnis) if z == LEERZEICHEN]
    assert positionen_nachher == positionen_vorher
    assert len(ergebnis) == len(satz)


@pytest.mark.parametrize("satz", UEBUNGSSAETZE_SUBSTITUTION + UEBUNGSSAETZE_VIGENERE)
def test_normalisieren_erhaelt_leerzeichenpositionen_bei_kleinschreibung(satz):
    """Regel 3 gilt auch, wenn die Eingabe klein geschrieben wurde (Regel 1)."""
    ergebnis = normalisieren(satz.lower())
    assert ergebnis == satz
    assert ergebnis.count(LEERZEICHEN) == satz.count(LEERZEICHEN)


def test_normalisieren_erhaelt_wortgrenzen_trotz_satzzeichen():
    """Regel 3 und 6: Wortgrenzen bleiben sichtbar, Satzzeichen verschwinden."""
    ergebnis = normalisieren("Zeit wird knapp, Bob!")
    assert ergebnis == "ZEIT WIRD KNAPP BOB"
    assert ergebnis.count(LEERZEICHEN) == 3
    assert len(ergebnis.split(LEERZEICHEN)) == 4


def test_normalisieren_bewaeltigt_sehr_langen_text():
    """Randfall: sehr langer Text – die Zusatzaufgaben haengen mehrere Saetze an."""
    langer_text = LEERZEICHEN.join(ALLE_UEBUNGSTEXTE * 200)
    ergebnis = normalisieren(langer_text)
    assert ergebnis == langer_text
    assert len(ergebnis) > 10000


def test_normalisieren_bewaeltigt_sehr_langen_rohtext():
    """Randfall: langer Text mit Umlauten und Satzzeichen (500 Funksprueche)."""
    ergebnis = normalisieren((FUNKSPRUCH_ERSTKONTAKT + " ") * 500)
    assert ergebnis == LEERZEICHEN.join(["HALLO HOERT MICH JEMAND"] * 500)


@pytest.mark.parametrize("eingabe", [None, 42, 3.5, ["HUND"], ("HUND",), b"HUND"])
def test_normalisieren_lehnt_nicht_text_ab(eingabe):
    """Dokumentierte Ausnahme: normalisieren() erwartet einen str."""
    with pytest.raises(TypeError):
        normalisieren(eingabe)


# ───────────────────────────────────────────────────────────────────────────
# 3. ohne_leerzeichen()
# ───────────────────────────────────────────────────────────────────────────

def test_ohne_leerzeichen_beispiel_aus_der_spezifikation():
    """Beispiel aus dem Modul-Docstring: "Zeit wird knapp" -> "ZEITWIRDKNAPP"."""
    assert ohne_leerzeichen("Zeit wird knapp") == "ZEITWIRDKNAPP"


def test_ohne_leerzeichen_normalisiert_ebenfalls():
    """Umlaute und Satzzeichen werden mitbehandelt (Regeln 5 und 6)."""
    assert ohne_leerzeichen(FUNKSPRUCH_ERSTKONTAKT) == "HALLOHOERTMICHJEMAND"


@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE)
def test_ohne_leerzeichen_entfernt_alle_leerzeichen(text):
    """Grundlage von Regel 4: Im Ergebnis steht kein Leerzeichen mehr."""
    ergebnis = ohne_leerzeichen(text)
    assert LEERZEICHEN not in ergebnis
    assert ergebnis == text.replace(LEERZEICHEN, "")


@pytest.mark.parametrize("eingabe", ["", " ", "    ", "\t\n", "!?"])
def test_ohne_leerzeichen_bei_leerem_text(eingabe):
    """Randfall: leerer Text und reine Leerzeichen ergeben den leeren Text."""
    assert ohne_leerzeichen(eingabe) == ""


@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE)
def test_ohne_leerzeichen_zaehlt_die_buchstaben(text):
    """Die Laenge entspricht der Buchstabenzahl – Grundlage fuer "Stelle n"."""
    ergebnis = ohne_leerzeichen(text)
    anzahl_buchstaben = sum(1 for z in normalisieren(text) if z in ALPHABET)
    assert len(ergebnis) == anzahl_buchstaben
    for zeichen in ergebnis:
        assert zeichen in ALPHABET


@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE + [FUNKSPRUCH_BOB, ""])
def test_ohne_leerzeichen_ist_idempotent(text):
    """Rundlauf: ein zweiter Durchlauf aendert nichts mehr."""
    einmal = ohne_leerzeichen(text)
    assert ohne_leerzeichen(einmal) == einmal


@pytest.mark.parametrize("eingabe", [None, 42, ["HUND"]])
def test_ohne_leerzeichen_lehnt_nicht_text_ab(eingabe):
    """Dokumentierte Ausnahme: der TypeError aus normalisieren() reicht durch."""
    with pytest.raises(TypeError):
        ohne_leerzeichen(eingabe)


# ───────────────────────────────────────────────────────────────────────────
# 4. vergleiche_tolerant()
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "eingabe, loesung",
    [
        # Regel 4: fehlende, doppelte und aeussere Leerzeichen sind egal.
        ("ZEITWIRDKNAPP", "ZEIT WIRD KNAPP"),
        ("ZEIT  WIRD KNAPP", "ZEIT WIRD KNAPP"),
        ("  ZEIT WIRD KNAPP  ", "ZEIT WIRD KNAPP"),
        ("ZEIT\tWIRD\nKNAPP", "ZEIT WIRD KNAPP"),
        # Regel 1: Kleinschreibung ist nie ein Fehler.
        ("zeitwirdknapp", "ZEIT WIRD KNAPP"),
        ("Zeit Wird Knapp", "ZEIT WIRD KNAPP"),
        # Regeln 5 und 6: Umlautschreibweise und Satzzeichen sind egal.
        ("hört mich jemand", "HOERT MICH JEMAND"),
        ("Hallo, hört mich jemand?", "HALLO HOERT MICH JEMAND"),
        ("HALLOHOERTMICHJEMAND", "Hallo, hört mich jemand?"),
        ("Straße", "STRASSE"),
        # Randfall: zwei leere Texte gelten als gleich.
        ("", ""),
        ("   ", ""),
    ],
)
def test_vergleiche_tolerant_akzeptiert_gleichwertige_schreibweisen(eingabe, loesung):
    """Regel 4: Ein vergessenes Leerzeichen darf keinen Versuch kosten."""
    assert vergleiche_tolerant(eingabe, loesung) is True


@pytest.mark.parametrize(
    "eingabe, loesung",
    [
        # Ein fehlender Buchstabe ist ein echter Fehler.
        ("ZEIT WIRD KNAP", "ZEIT WIRD KNAPP"),
        ("ZEIT WIRD KNAPPP", "ZEIT WIRD KNAPP"),
        # Ein falscher Buchstabe ebenso – typischer Caesar-Verzaehler.
        ("HAND", "HUND"),
        ("KXQF", "KXQG"),
        ("IXFS", "IXFR"),
        ("YIGV", "YIGU"),
        # Vertauschte Buchstaben sind nicht dasselbe Wort.
        ("HUDN", "HUND"),
        # Leere Eingabe gegen echte Loesung.
        ("", "HUND"),
        ("HUND", ""),
        ("   ", "HUND"),
    ],
)
def test_vergleiche_tolerant_erkennt_echte_fehler(eingabe, loesung):
    """Inhaltliche Abweichungen muessen als falsch erkannt werden."""
    assert vergleiche_tolerant(eingabe, loesung) is False


@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE)
def test_vergleiche_tolerant_ist_reflexiv(text):
    """Ein Text ist immer gleich zu sich selbst und zu seiner Kurzform."""
    assert vergleiche_tolerant(text, text) is True
    assert vergleiche_tolerant(ohne_leerzeichen(text), text) is True
    assert vergleiche_tolerant(text.lower(), text) is True


@pytest.mark.parametrize(
    "eingabe, loesung",
    [
        ("ZEITWIRDKNAPP", "ZEIT WIRD KNAPP"),
        ("ZEIT WIRD KNAP", "ZEIT WIRD KNAPP"),
        ("Hallo, hört mich jemand?", "HALLO HOERT MICH JEMAND"),
        ("", "HUND"),
    ],
)
def test_vergleiche_tolerant_ist_symmetrisch(eingabe, loesung):
    """Die Reihenfolge der Argumente darf das Ergebnis nicht aendern."""
    assert vergleiche_tolerant(eingabe, loesung) == vergleiche_tolerant(loesung, eingabe)


def test_vergleiche_tolerant_akzeptiert_verschobene_wortgrenzen():
    """Grenzfall und bewusster Kompromiss aus Regel 4.

    Weil beim Vergleich alle Leerzeichen wegfallen, gilt eine falsch gesetzte
    Wortgrenze als richtig. Das ist gewollt: eine verrutschte Wortgrenze ist
    kein Fehler beim Ver- oder Entschluesseln und darf keinen der drei
    Versuche verbrauchen.
    """
    assert vergleiche_tolerant("ALLE SOK", "ALLES OK") is True
    assert vergleiche_tolerant("ALLESOK", "ALLES OK") is True
    # Ein echter Buchstabenfehler bleibt trotzdem ein Fehler.
    assert vergleiche_tolerant("ALLE SOKK", "ALLES OK") is False


def test_vergleiche_tolerant_unterscheidet_die_uebungstexte_voneinander():
    """Verschiedene Handbuchtexte duerfen nicht als gleich durchgehen."""
    for i, erster in enumerate(ALLE_UEBUNGSTEXTE):
        for zweiter in ALLE_UEBUNGSTEXTE[i + 1:]:
            assert vergleiche_tolerant(erster, zweiter) is False


@pytest.mark.parametrize(
    "eingabe, loesung",
    [(None, "HUND"), ("HUND", None), (42, "HUND"), ("HUND", ["HUND"])],
)
def test_vergleiche_tolerant_lehnt_nicht_text_ab(eingabe, loesung):
    """Dokumentierte Ausnahme: der TypeError reicht bis nach oben durch."""
    with pytest.raises(TypeError):
        vergleiche_tolerant(eingabe, loesung)


# ───────────────────────────────────────────────────────────────────────────
# 5. buchstabe_zu_index()
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "buchstabe, erwartet",
    [
        # Von Hand abgezaehlt: A0 B1 C2 D3 E4 F5 G6 H7 I8 J9 K10 L11 M12
        # N13 O14 P15 Q16 R17 S18 T19 U20 V21 W22 X23 Y24 Z25.
        ("A", 0), ("B", 1), ("D", 3), ("H", 7), ("M", 12),
        ("N", 13), ("O", 14), ("R", 17), ("T", 19), ("U", 20), ("Z", 25),
    ],
)
def test_buchstabe_zu_index_liefert_die_alphabetposition(buchstabe, erwartet):
    """A = 0 bis Z = 25, wie in der Spezifikation festgelegt."""
    assert buchstabe_zu_index(buchstabe) == erwartet


@pytest.mark.parametrize("position", range(26))
def test_buchstabe_zu_index_passt_zum_alphabet(position):
    """Jeder Buchstabe des Arbeitsalphabets liefert seine eigene Position."""
    assert buchstabe_zu_index(ALPHABET[position]) == position


@pytest.mark.parametrize(
    "buchstabe, erwartet",
    [("a", 0), ("h", 7), ("z", 25), ("u", 20)],
)
def test_buchstabe_zu_index_akzeptiert_kleinbuchstaben(buchstabe, erwartet):
    """Regel 1: Kleinschreibung ist erlaubt und nie ein Fehler."""
    assert buchstabe_zu_index(buchstabe) == erwartet


@pytest.mark.parametrize(
    "eingabe",
    ["Ä", "Ö", "Ü", "ß", "É", " ", "1", "?", "-", "\n", "€"],
)
def test_buchstabe_zu_index_lehnt_nichtbuchstaben_ab(eingabe):
    """Dokumentierte Ausnahme: ValueError bei allem ausser A-Z."""
    with pytest.raises(ValueError):
        buchstabe_zu_index(eingabe)


def test_buchstabe_zu_index_lehnt_leeren_text_ab():
    """Der leere Text ist kein Buchstabe von A bis Z und muss abgelehnt werden."""
    with pytest.raises(ValueError):
        buchstabe_zu_index("")


@pytest.mark.parametrize("eingabe", ["AB", "ABC", "XYZ", "HUND", "AA"])
def test_buchstabe_zu_index_lehnt_mehrere_buchstaben_ab(eingabe):
    """Ein ganzes Wort ist kein einzelner Buchstabe und muss abgelehnt werden.

    Sonst bekaeme der Aufrufer stillschweigend die Position der ersten
    Fundstelle zurueck, statt einen Fehler zu sehen.
    """
    with pytest.raises(ValueError):
        buchstabe_zu_index(eingabe)


@pytest.mark.parametrize("eingabe", [None, 1, 3.5, ["A"], ("A",), b"A"])
def test_buchstabe_zu_index_lehnt_nicht_text_ab(eingabe):
    """Dokumentierte Ausnahme: TypeError, wenn kein str uebergeben wird."""
    with pytest.raises(TypeError):
        buchstabe_zu_index(eingabe)


# ───────────────────────────────────────────────────────────────────────────
# 6. index_zu_buchstabe()
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "index, erwartet",
    [(0, "A"), (1, "B"), (3, "D"), (7, "H"), (17, "R"), (20, "U"), (25, "Z")],
)
def test_index_zu_buchstabe_liefert_den_alphabetbuchstaben(index, erwartet):
    """Umkehrung von buchstabe_zu_index(): A = 0 bis Z = 25."""
    assert index_zu_buchstabe(index) == erwartet


@pytest.mark.parametrize(
    "index, erwartet",
    [
        # 26 % 26 = 0 -> A, 27 % 26 = 1 -> B, 51 % 26 = 25 -> Z,
        # 52 % 26 = 0 -> A, 260 % 26 = 0 -> A.
        (26, "A"), (27, "B"), (51, "Z"), (52, "A"), (260, "A"),
        # Negative Werte: -1 % 26 = 25 -> Z, -26 % 26 = 0 -> A,
        # -27 % 26 = 25 -> Z, -3 % 26 = 23 -> X.
        (-1, "Z"), (-2, "Y"), (-3, "X"), (-26, "A"), (-27, "Z"),
    ],
)
def test_index_zu_buchstabe_rechnet_modulo_26(index, erwartet):
    """Hier ist der Alphabet-Umbruch Z->A und A->Z geregelt."""
    assert index_zu_buchstabe(index) == erwartet


@pytest.mark.parametrize("eingabe", [None, "A", 1.0, 3.5, ["A"]])
def test_index_zu_buchstabe_lehnt_nicht_ganze_zahlen_ab(eingabe):
    """Dokumentierte Ausnahme: TypeError, wenn kein int uebergeben wird."""
    with pytest.raises(TypeError):
        index_zu_buchstabe(eingabe)


@pytest.mark.parametrize("eingabe", [True, False])
def test_index_zu_buchstabe_lehnt_wahrheitswerte_ab(eingabe):
    """Grenzfall: True/False sind in Python zwar ints, aber keine Indizes.

    Ohne diese Pruefung wuerde ein versehentlich uebergebenes True still zu
    "B" werden – ein Fehler, den niemand mehr findet.
    """
    with pytest.raises(TypeError):
        index_zu_buchstabe(eingabe)


# ───────────────────────────────────────────────────────────────────────────
# 7. Rundlauf: hin und wieder zurueck
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("buchstabe", list(ALPHABET))
def test_rundlauf_buchstabe_index_buchstabe(buchstabe):
    """Rundlauf: index_zu_buchstabe(buchstabe_zu_index(x)) == x."""
    assert index_zu_buchstabe(buchstabe_zu_index(buchstabe)) == buchstabe


@pytest.mark.parametrize("index", list(range(-30, 60)))
def test_rundlauf_index_buchstabe_index(index):
    """Rundlauf: nach dem Umweg ueber den Buchstaben bleibt index % 26 uebrig."""
    assert buchstabe_zu_index(index_zu_buchstabe(index)) == index % 26


@pytest.mark.parametrize(
    "text",
    ALLE_UEBUNGSTEXTE
    + [FUNKSPRUCH_ERSTKONTAKT, FUNKSPRUCH_BOB, FUNKSPRUCH_VERFOLGER],
)
def test_rundlauf_vergleich_akzeptiert_die_normalisierte_form(text):
    """Rundlauf ueber alle Uebungstexte: normalisierte Form gilt als richtig.

    Genau das braucht das Fehlerhandling: Der angezeigte Aufgabentext ist
    bereits normalisiert, die Schuelereingabe ist es nicht – beide muessen
    als gleich gelten.
    """
    assert vergleiche_tolerant(normalisieren(text), text) is True
    assert vergleiche_tolerant(ohne_leerzeichen(text), text) is True
    assert vergleiche_tolerant(text.lower(), text) is True


@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE)
def test_rundlauf_buchstabenweise_ueber_die_uebungstexte(text):
    """Rundlauf Buchstabe fuer Buchstabe ueber jeden Handbuchtext.

    Jeder Buchstabe wird in seinen Index und zurueck verwandelt; am Ende muss
    derselbe Text herauskommen. Das ist die Schleife, die alle drei
    Verschluesselungsverfahren spaeter benutzen.
    """
    zurueck = "".join(
        index_zu_buchstabe(buchstabe_zu_index(z)) if z != LEERZEICHEN else LEERZEICHEN
        for z in normalisieren(text)
    )
    assert zurueck == normalisieren(text)


# ───────────────────────────────────────────────────────────────────────────
# 8. Referenzwerte aus dokumentation/Handbuchtexte.md
#
# Die drei Verfahren liegen in eigenen Modulen. Geprueft wird hier, dass die
# Bausteine aus normalize.py ausreichen, um die Handbuch-Referenzwerte
# herzuleiten – wenn das hier schon nicht stimmt, kann kein Verfahren stimmen.
# ───────────────────────────────────────────────────────────────────────────

def test_referenz_caesar_hund_wird_kxqg():
    """Handbuch Seite 1: HUND + Schluessel 3 -> KXQG.

    Von Hand: H(7)+3 = 10 -> K, U(20)+3 = 23 -> X,
    N(13)+3 = 16 -> Q, D(3)+3 = 6 -> G.
    """
    geheim = "".join(
        index_zu_buchstabe(buchstabe_zu_index(z) + 3) for z in "HUND"
    )
    assert geheim == "KXQG"


def test_referenz_caesar_entschluesselt_kxqg_wieder_zu_hund():
    """Handbuch Seite 1: Entschluesseln heisst dieselbe Zahl zurueckgehen."""
    klar = "".join(
        index_zu_buchstabe(buchstabe_zu_index(z) - 3) for z in "KXQG"
    )
    assert klar == "HUND"


def test_referenz_caesar_z_plus_eins_wird_a():
    """Arbeitsplan 1.6: Z + 1 -> A. Von Hand: Z(25)+1 = 26, 26 % 26 = 0 -> A."""
    assert index_zu_buchstabe(buchstabe_zu_index("Z") + 1) == "A"
    # Und die Gegenrichtung: A - 1 -> Z, weil -1 % 26 = 25.
    assert index_zu_buchstabe(buchstabe_zu_index("A") - 1) == "Z"


def test_referenz_tastatur_geheimalphabet_ist_vollstaendig():
    """Handbuch Seite 2: Die drei Tastaturzeilen ergeben 26 verschiedene Zeichen."""
    assert len(TASTATUR_GEHEIMALPHABET) == 26
    assert sorted(TASTATUR_GEHEIMALPHABET) == sorted(ALPHABET)


def test_referenz_substitution_hund_wird_ixfr():
    """Handbuch Seite 2: HUND mit der Tastatur-Tabelle -> IXFR.

    Von Hand abgezaehlt in QWERTZUIOPASDFGHJKLYXCVBNM:
    H = Position 7 -> I, U = Position 20 -> X,
    N = Position 13 -> F, D = Position 3 -> R.
    """
    geheim = "".join(
        TASTATUR_GEHEIMALPHABET[buchstabe_zu_index(z)] for z in "HUND"
    )
    assert geheim == "IXFR"


def test_referenz_vigenere_hund_mit_rot_wird_yigu():
    """Handbuch Seite 3: HUND + Schluesselwort ROT -> YIGU.

    Von Hand mit (Zeile + Spalte) mod 26:
    H(7)+R(17) = 24 -> Y, U(20)+O(14) = 34, 34-26 = 8 -> I,
    N(13)+T(19) = 32, 32-26 = 6 -> G, D(3)+R(17) = 20 -> U.
    """
    nachricht = "HUND"
    schluessel = "ROTR"  # ROT auf Nachrichtenlaenge wiederholt
    geheim = "".join(
        index_zu_buchstabe(buchstabe_zu_index(n) + buchstabe_zu_index(s))
        for n, s in zip(nachricht, schluessel)
    )
    assert geheim == "YIGU"


def test_referenz_vigenere_entschluesselt_yigu_wieder_zu_hund():
    """Handbuch Seite 3: YIGU mit ROT -> HUND (Geheim minus Schluessel)."""
    klar = "".join(
        index_zu_buchstabe(buchstabe_zu_index(g) - buchstabe_zu_index(s))
        for g, s in zip("YIGU", "ROTR")
    )
    assert klar == "HUND"


def test_referenz_vigenere_quadrat_zeile_a_ist_das_normale_alphabet():
    """Handbuch Seite 3: In Zeile A steht das unveraenderte Alphabet.

    Von Hand: A hat den Index 0, also ist (0 + Spalte) mod 26 = Spalte.
    """
    zeile_a = "".join(
        index_zu_buchstabe(buchstabe_zu_index("A") + spalte)
        for spalte in range(26)
    )
    assert zeile_a == ALPHABET


def test_referenz_vigenere_quadrat_feld_zeile_r_spalte_h_ist_y():
    """Handbuch Seite 3: Das Feld (Zeile R, Spalte H) enthaelt Y.

    Von Hand: R = 17, H = 7, 17 + 7 = 24 -> Y.
    """
    feld = index_zu_buchstabe(buchstabe_zu_index("R") + buchstabe_zu_index("H"))
    assert feld == "Y"


def test_regel_7_leerzeichen_zaehlt_den_schluesselindex_nicht_weiter():
    """Regel 7 am Beispiel "HUND HUND" mit dem Schluesselwort ROT.

    Das Schluesselwort rueckt nur bei Buchstaben eine Stelle vor. Die acht
    Buchstaben bekommen also der Reihe nach R O T R O T R O:
    H(7)+R(17) = 24 -> Y, U(20)+O(14) = 8 -> I, N(13)+T(19) = 6 -> G,
    D(3)+R(17) = 20 -> U, dann das Leerzeichen unveraendert,
    H(7)+O(14) = 21 -> V, U(20)+T(19) = 13 -> N, N(13)+R(17) = 4 -> E,
    D(3)+O(14) = 17 -> R.
    Erwartet: "YIGU VNER".
    """
    nachricht = normalisieren("hund hund")
    assert nachricht == "HUND HUND"

    schluesselwort = "ROT"
    schluesselindex = 0
    geheim = []
    for zeichen in nachricht:
        if zeichen == LEERZEICHEN:
            # Regel 3 und 7: Leerzeichen bleibt stehen und zaehlt nicht mit.
            geheim.append(LEERZEICHEN)
            continue
        schluesselbuchstabe = schluesselwort[schluesselindex % len(schluesselwort)]
        geheim.append(
            index_zu_buchstabe(
                buchstabe_zu_index(zeichen) + buchstabe_zu_index(schluesselbuchstabe)
            )
        )
        schluesselindex += 1

    ergebnis = "".join(geheim)
    assert ergebnis == "YIGU VNER"
    # Regel 3: Das Leerzeichen steht an genau derselben Stelle wie vorher.
    assert ergebnis.index(LEERZEICHEN) == nachricht.index(LEERZEICHEN)
