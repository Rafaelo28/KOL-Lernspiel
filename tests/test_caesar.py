"""Tests für ``crypto/caesar.py`` – Level 1 des Lernspiels "Der Diamantenraub".

Alle Erwartungswerte in dieser Datei sind **von Hand** aus zwei Quellen
hergeleitet und nicht aus der Implementierung übernommen:

* ``dokumentation/Handbuchtexte.md``, Seite 1 – dort steht die verschobene
  Alphabet-Zeile für Schlüssel 3 und das durchgerechnete Beispiel
  ``HUND -> KXQG``.
* Die Textkonvention aus ``crypto/normalize.py`` (Aufgabe 0.3), insbesondere
  Regel 3: Leerzeichen bleiben im Geheimtext an Ort und Stelle stehen.

Als zweites Standbein enthält die Datei mit ``_caesar_von_hand()`` eine
bewusst *anders* gebaute Referenz: Sie schlägt in der verschobenen
Alphabet-Zeile des Handbuchs nach (Tabellen-Lookup), statt wie das Modul mit
Indizes modulo 26 zu rechnen. Stimmen beide Wege überein, ist ein gemeinsamer
Denkfehler unwahrscheinlich.
"""

import doctest

from pathlib import Path

import pytest

from content import uebungen

from crypto import caesar
from crypto.normalize import (
    ALPHABET,
    LEERZEICHEN,
    normalisieren,
    vergleiche_tolerant,
)

# ---------------------------------------------------------------------------
# Übungsmaterial aus dokumentation/Handbuchtexte.md
# ---------------------------------------------------------------------------

# Das Übungsmaterial kommt seit Aufgabe 2.2 aus content/uebungen.py.
UEBUNGSWOERTER = list(uebungen.UEBUNGSWOERTER_LEVEL_1)

# Level 2 und 3 zusammen – hier nur als mehrwortiges Testmaterial, um Regel 3
# (Leerzeichen bleiben stehen) an echten Sätzen zu prüfen.
UEBUNGSSAETZE_MIT_LEERZEICHEN = list(
    uebungen.UEBUNGSSAETZE_LEVEL_2 + uebungen.UEBUNGSSAETZE_LEVEL_3
)


# ---------------------------------------------------------------------------
# Unabhängige Referenz: das Nachschlage-Verfahren aus dem Handbuch
# ---------------------------------------------------------------------------

def _verschobenes_alphabet(schluessel):
    """Baut die verschobene Alphabet-Zeile aus dem Handbuch nach.

    Für Schlüssel 3 muss genau die Zeile von Seite 1 herauskommen:
    ``DEFGHIJKLMNOPQRSTUVWXYZABC``.
    """
    versatz = schluessel % len(ALPHABET)
    return ALPHABET[versatz:] + ALPHABET[:versatz]


def _caesar_von_hand(text, schluessel):
    """Verschlüsselt per Tabellen-Lookup statt per Modulo-Rechnung.

    Bewusst anders gebaut als ``crypto/caesar.py``, damit die Tests nicht
    denselben Rechenweg noch einmal nachbeten.
    """
    zeile = _verschobenes_alphabet(schluessel)
    ergebnis = []
    for zeichen in normalisieren(text):
        if zeichen == LEERZEICHEN:
            ergebnis.append(LEERZEICHEN)
        else:
            ergebnis.append(zeile[ALPHABET.index(zeichen)])
    return "".join(ergebnis)


# ---------------------------------------------------------------------------
# 1. Referenzwerte aus dem Handbuch
# ---------------------------------------------------------------------------

def test_handbuch_beispiel_hund_wird_zu_kxqg():
    """Das durchgerechnete Beispiel von Seite 1: HUND + Schlüssel 3 -> KXQG."""
    assert caesar.verschluesseln("HUND", 3) == "KXQG"


def test_handbuch_beispiel_kxqg_wird_wieder_zu_hund():
    """Rückrichtung desselben Beispiels: KXQG + Schlüssel 3 -> HUND."""
    assert caesar.entschluesseln("KXQG", 3) == "HUND"


def test_handbuch_alphabetzeile_fuer_schluessel_drei():
    """Das ganze Alphabet um 3 verschoben ergibt die Zeile aus dem Handbuch."""
    assert caesar.verschluesseln(ALPHABET, 3) == "DEFGHIJKLMNOPQRSTUVWXYZABC"


@pytest.mark.parametrize(
    "klartext, geheimtext",
    [
        ("HUND", "KXQG"),
        ("KATZE", "NDWCH"),
        ("MAUS", "PDXV"),
        ("BURG", "EXUJ"),
        ("FELS", "IHOV"),
        ("WALD", "ZDOG"),
        ("STERN", "VWHUQ"),
        ("MOND", "PRQG"),
        ("SAND", "VDQG"),
        ("TURM", "WXUP"),
    ],
)
def test_alle_uebungswoerter_mit_schluessel_drei(klartext, geheimtext):
    """Alle 10 Übungswörter von Seite 1, von Hand mit Schlüssel 3 gerechnet."""
    assert caesar.verschluesseln(klartext, 3) == geheimtext
    assert caesar.entschluesseln(geheimtext, 3) == klartext


@pytest.mark.parametrize(
    "klartext, schluessel, geheimtext",
    [
        ("HUND", 5, "MZSI"),
        ("KATZE", 13, "XNGMR"),
        ("MAUS", 25, "LZTR"),
        ("BURG", 17, "SLIX"),
        ("FELS", 23, "CBIP"),
        ("WALD", 1, "XBME"),
        ("STERN", 20, "MNYLH"),
        ("MOND", 12, "YAZP"),
        ("SAND", 8, "AIVL"),
        ("TURM", 7, "ABYT"),
    ],
)
def test_uebungswoerter_mit_verschiedenen_schluesseln(
    klartext, schluessel, geheimtext
):
    """Dieselben Wörter mit anderen Schlüsseln, ebenfalls von Hand gerechnet."""
    assert caesar.verschluesseln(klartext, schluessel) == geheimtext
    assert caesar.entschluesseln(geheimtext, schluessel) == klartext


# ---------------------------------------------------------------------------
# 2. Umbruch Z->A und A->Z (Kernlernziel von Level 1)
# ---------------------------------------------------------------------------

def test_umbruch_z_nach_a():
    """Am Ende des Alphabets geht es wieder bei A weiter (Merksatz Seite 1)."""
    assert caesar.verschluesseln("Z", 1) == "A"


def test_umbruch_a_nach_z_bei_negativem_schluessel():
    """Ein negativer Schlüssel schiebt rückwärts über den Alphabetanfang."""
    assert caesar.verschluesseln("A", -1) == "Z"


def test_umbruch_a_nach_z_beim_entschluesseln():
    """Entschlüsseln geht rückwärts – aus A wird mit Schlüssel 1 wieder Z."""
    assert caesar.entschluesseln("A", 1) == "Z"


@pytest.mark.parametrize(
    "buchstabe, schluessel, erwartet",
    [
        ("Z", 1, "A"),
        ("Z", 2, "B"),
        ("Z", 27, "A"),
        ("A", -1, "Z"),
        ("A", -2, "Y"),
        ("A", 25, "Z"),
        ("Y", 3, "B"),
        ("X", 5, "C"),
        ("M", 13, "Z"),
        ("N", 13, "A"),
    ],
)
def test_einzelne_grenzbuchstaben(buchstabe, schluessel, erwartet):
    """Von Hand abgezählte Sprünge über die Alphabetgrenze hinweg."""
    assert caesar.verschluesseln(buchstabe, schluessel) == erwartet


def test_vollstaendige_tabelle_gegen_handbuch_lookup():
    """Jeder Buchstabe mit jedem Schlüssel 0–25 gegen das Nachschlageverfahren."""
    for schluessel in range(len(ALPHABET)):
        zeile = _verschobenes_alphabet(schluessel)
        for position, buchstabe in enumerate(ALPHABET):
            assert caesar.verschluesseln(buchstabe, schluessel) == zeile[position]


# ---------------------------------------------------------------------------
# 3. Leerzeichen (Regel 3 der Textkonvention)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "klartext, schluessel, geheimtext",
    [
        ("ALLES OK", 3, "DOOHV RN"),
        ("WO BIST DU", 5, "BT GNXY IZ"),
        ("ZEIT WIRD KNAPP", 1, "AFJU XJSE LOBQQ"),
        ("NAHE DEM WRACK", 4, "RELI HIQ AVEGO"),
        ("ICH BIN HIER", 2, "KEJ DKP JKGT"),
        ("WARTE AUF RETTUNG", 3, "ZDUWH DXI UHWWXQJ"),
    ],
)
def test_mehrere_woerter_von_hand_gerechnet(klartext, schluessel, geheimtext):
    """Mehrwortige Sätze: Leerzeichen bleiben stehen, Buchstaben wandern."""
    assert caesar.verschluesseln(klartext, schluessel) == geheimtext
    assert caesar.entschluesseln(geheimtext, schluessel) == klartext


@pytest.mark.parametrize("satz", UEBUNGSSAETZE_MIT_LEERZEICHEN)
@pytest.mark.parametrize("schluessel", [1, 3, 7, 13, 25])
def test_leerzeichen_bleiben_an_derselben_stelle(satz, schluessel):
    """Regel 3: Die Wortgrenzen liegen im Geheimtext an denselben Positionen."""
    normalisiert = normalisieren(satz)
    geheim = caesar.verschluesseln(satz, schluessel)

    positionen_klar = [
        i for i, z in enumerate(normalisiert) if z == LEERZEICHEN
    ]
    positionen_geheim = [
        i for i, z in enumerate(geheim) if z == LEERZEICHEN
    ]

    assert positionen_geheim == positionen_klar
    assert len(geheim) == len(normalisiert)


def test_leerzeichen_wird_nicht_mitverschoben():
    """Ein Leerzeichen bleibt Leerzeichen und wird nie zu einem Buchstaben."""
    ergebnis = caesar.verschluesseln("A A", 1)
    assert ergebnis == "B B"


def test_nur_leerzeichen_ergibt_leeren_text():
    """Reiner Weißraum bleibt nach dem Normalisieren nichts übrig."""
    assert caesar.verschluesseln("   ", 5) == ""
    assert caesar.entschluesseln("   ", 5) == ""


def test_mehrfache_leerzeichen_werden_zusammengefasst():
    """Normalisierung vor der Verschlüsselung: doppelte Lücken verschwinden."""
    assert caesar.verschluesseln("ALLES   OK", 3) == "DOOHV RN"


# ---------------------------------------------------------------------------
# 4. Normalisierung der Eingabe (Regeln 1, 5 und 6)
# ---------------------------------------------------------------------------

def test_kleinbuchstaben_werden_akzeptiert():
    """Regel 1: Kleinschreibung ist erlaubt und nie ein Fehler."""
    assert caesar.verschluesseln("hund", 3) == "KXQG"
    assert caesar.entschluesseln("kxqg", 3) == "HUND"


def test_umlaute_werden_ersetzt_und_dann_verschluesselt():
    """Regel 5: Aus "hört" wird HOERT, erst danach wird verschoben."""
    # HALLO HOERT MICH JEMAND, jeder Buchstabe von Hand um 3 verschoben.
    assert (
        caesar.verschluesseln("Hallo, hört mich jemand?", 3)
        == "KDOOR KRHUW PLFK MHPDQG"
    )


def test_scharfes_s_wird_zu_doppel_s():
    """Regel 5: ß -> SS. GRUSS mit Schlüssel 1 ergibt HSVTT."""
    assert caesar.verschluesseln("Gruß", 1) == "HSVTT"


def test_satzzeichen_und_ziffern_fallen_weg():
    """Regel 6: Alles außer A–Z und Leerzeichen verschwindet vor dem Rechnen."""
    assert caesar.verschluesseln("H.U-N,D!", 3) == "KXQG"
    assert caesar.verschluesseln("HUND 2024", 3) == "KXQG"


def test_text_ohne_buchstaben_ergibt_leeren_text():
    """Ein Text nur aus Satzzeichen oder Ziffern bleibt leer."""
    assert caesar.verschluesseln("!?,.-", 4) == ""
    assert caesar.verschluesseln("12345", 4) == ""


def test_ergebnis_ist_selbst_schon_normalisiert():
    """Der Geheimtext erfüllt dieselbe Textkonvention wie der Klartext."""
    for satz in UEBUNGSSAETZE_MIT_LEERZEICHEN:
        geheim = caesar.verschluesseln(satz, 11)
        assert normalisieren(geheim) == geheim
        assert set(geheim) <= set(ALPHABET + LEERZEICHEN)


# ---------------------------------------------------------------------------
# 5. Rundlauf: entschluesseln(verschluesseln(x)) == x
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text", UEBUNGSWOERTER + UEBUNGSSAETZE_MIT_LEERZEICHEN
)
@pytest.mark.parametrize("schluessel", [1, 3, 5, 13, 25, 26, 0, -3, 42])
def test_rundlauf_ver_und_entschluesseln(text, schluessel):
    """Jede Übungsaufgabe muss sich sauber hin- und zurückrechnen lassen."""
    geheim = caesar.verschluesseln(text, schluessel)
    assert caesar.entschluesseln(geheim, schluessel) == normalisieren(text)


@pytest.mark.parametrize(
    "text", UEBUNGSWOERTER + UEBUNGSSAETZE_MIT_LEERZEICHEN
)
@pytest.mark.parametrize("schluessel", [2, 9, 17, -7])
def test_rundlauf_in_der_gegenrichtung(text, schluessel):
    """Auch entschlüsseln-dann-verschlüsseln muss den Ausgangstext liefern.

    Wichtig für den Aufgaben-Generator aus Phase 3: Bei der Richtung
    "entschlüsseln" wird der Klartext zuerst verschlüsselt angezeigt.
    """
    zwischenschritt = caesar.entschluesseln(text, schluessel)
    assert caesar.verschluesseln(zwischenschritt, schluessel) == normalisieren(text)


@pytest.mark.parametrize(
    "text", UEBUNGSWOERTER + UEBUNGSSAETZE_MIT_LEERZEICHEN
)
def test_gegen_die_unabhaengige_handbuch_referenz(text):
    """Modul und Nachschlage-Verfahren aus dem Handbuch müssen übereinstimmen."""
    for schluessel in (1, 3, 8, 13, 19, 25):
        assert caesar.verschluesseln(text, schluessel) == _caesar_von_hand(
            text, schluessel
        )


def test_toleranter_vergleich_akzeptiert_schuelereingabe():
    """Zusammenspiel mit Regel 4: getippte Lösung ohne Leerzeichen zählt."""
    loesung = caesar.verschluesseln("ZEIT WIRD KNAPP", 1)
    assert vergleiche_tolerant("afjuxjselobqq", loesung)


# ---------------------------------------------------------------------------
# 6. Schlüssel: Wertebereich, Äquivalenz, Nullschlüssel
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("schluessel", [0, 26, 52, -26, 260])
def test_nullschluessel_laesst_den_text_unveraendert(schluessel):
    """Schlüssel 0 und jedes Vielfache von 26 geben den Klartext zurück."""
    text = "ZEIT WIRD KNAPP"
    assert caesar.verschluesseln(text, schluessel) == normalisieren(text)
    assert caesar.entschluesseln(text, schluessel) == normalisieren(text)


@pytest.mark.parametrize(
    "schluessel_a, schluessel_b",
    [
        (3, 29),
        (3, -23),
        (25, -1),
        (25, 51),
        (-1, 51),
        (13, 39),
        (0, 26),
        (7, -19),
    ],
)
def test_schluessel_modulo_26_verhalten_sich_gleich(schluessel_a, schluessel_b):
    """25, -1 und 51 sind derselbe Schlüssel – der Umbruch regelt das."""
    text = "HILFE WIRD GEBRAUCHT"
    assert caesar.verschluesseln(text, schluessel_a) == caesar.verschluesseln(
        text, schluessel_b
    )
    assert caesar.entschluesseln(text, schluessel_a) == caesar.entschluesseln(
        text, schluessel_b
    )


def test_sehr_grosser_und_sehr_kleiner_schluessel():
    """Auch absurde Schlüssel dürfen nicht abstürzen (Eingabefeld der UI)."""
    assert caesar.verschluesseln("HUND", 1_000_003) == caesar.verschluesseln(
        "HUND", 1_000_003 % 26
    )
    assert caesar.verschluesseln("HUND", -1_000_003) == caesar.verschluesseln(
        "HUND", -1_000_003 % 26
    )


def test_entschluesseln_ist_verschluesseln_mit_negativem_schluessel():
    """Spezifikation: entschluesseln(x, k) == verschluesseln(x, -k)."""
    for satz in UEBUNGSSAETZE_MIT_LEERZEICHEN:
        for schluessel in (0, 1, 4, 13, 25, -6):
            assert caesar.entschluesseln(satz, schluessel) == caesar.verschluesseln(
                satz, -schluessel
            )


def test_verschiebungen_addieren_sich():
    """Zweimal verschieben ist dasselbe wie einmal um die Summe verschieben."""
    text = "BRAUCHE SOFORT HILFE"
    for erster, zweiter in ((3, 4), (10, 20), (25, 1), (-5, 12)):
        doppelt = caesar.verschluesseln(caesar.verschluesseln(text, erster), zweiter)
        assert doppelt == caesar.verschluesseln(text, erster + zweiter)


def test_die_25_schluessel_ergeben_25_verschiedene_geheimtexte():
    """Handbuch Seite 2: "Bei Caesar gibt es nur 25 mögliche Schlüssel".

    Gezählt werden die Schlüssel 1 bis 25 – Schlüssel 0 verschiebt nichts und
    ist deshalb kein Schlüssel im Sinne des Handbuchs. Genau darauf beruht das
    Argument von Handbuchseite 2, dass Caesar in Minuten zu knacken ist.
    """
    text = "STANDORT UNBEKANNT"
    ergebnisse = {caesar.verschluesseln(text, k) for k in range(1, 26)}
    assert len(ergebnisse) == 25
    assert normalisieren(text) not in ergebnisse
    assert caesar.verschluesseln(text, 0) == normalisieren(text)


# ---------------------------------------------------------------------------
# 7. Randfälle: leerer und sehr langer Text
# ---------------------------------------------------------------------------

def test_leerer_text():
    """Der leere Text bleibt leer – die UI darf hier nicht abstürzen."""
    assert caesar.verschluesseln("", 3) == ""
    assert caesar.entschluesseln("", 3) == ""


def test_einzelner_buchstabe():
    """Kürzestmögliche echte Aufgabe."""
    assert caesar.verschluesseln("A", 3) == "D"
    assert caesar.entschluesseln("D", 3) == "A"


def test_sehr_langer_text():
    """Ein sehr langer Funkspruch muss Länge, Lücken und Rundlauf behalten."""
    satz = "SIGNAL WIRD SCHWACH"
    langer_text = " ".join([satz] * 500)
    normalisiert = normalisieren(langer_text)

    geheim = caesar.verschluesseln(langer_text, 17)

    assert len(geheim) == len(normalisiert)
    assert geheim.count(LEERZEICHEN) == normalisiert.count(LEERZEICHEN)
    assert caesar.entschluesseln(geheim, 17) == normalisiert


# ---------------------------------------------------------------------------
# 8. Ungültige Eingaben
# ---------------------------------------------------------------------------

DEUTSCHE_MELDUNGSTEILE = (
    "zahl",
    "schluessel",
    "schlüssel",
    "erwartet",
    "ganze",
)


@pytest.mark.parametrize(
    "ungueltiger_schluessel",
    ["3", 3.0, None, [3], (3,), {"k": 3}, 3.5, complex(3, 0)],
)
def test_nicht_ganzzahliger_schluessel_wirft_typeerror(ungueltiger_schluessel):
    """Ein Schlüssel, der keine ganze Zahl ist, muss abgelehnt werden."""
    with pytest.raises(TypeError) as fehler_ver:
        caesar.verschluesseln("HUND", ungueltiger_schluessel)
    with pytest.raises(TypeError) as fehler_ent:
        caesar.entschluesseln("HUND", ungueltiger_schluessel)

    for fehler in (fehler_ver, fehler_ent):
        meldung = str(fehler.value).lower()
        assert meldung, "Die Fehlermeldung darf nicht leer sein."
        assert any(teil in meldung for teil in DEUTSCHE_MELDUNGSTEILE), (
            f"Fehlermeldung wirkt nicht deutsch: {meldung!r}"
        )


@pytest.mark.parametrize("wahrheitswert", [True, False])
def test_bool_ist_kein_gueltiger_schluessel(wahrheitswert):
    """bool ist zwar technisch ein int, hier aber ausdrücklich verboten."""
    with pytest.raises(TypeError):
        caesar.verschluesseln("HUND", wahrheitswert)
    with pytest.raises(TypeError):
        caesar.entschluesseln("HUND", wahrheitswert)


@pytest.mark.parametrize("ungueltiger_text", [None, 123, ["H", "U"], 4.5])
def test_nicht_text_als_nachricht_wirft_typeerror(ungueltiger_text):
    """Die Nachricht muss ein str sein – normalisieren() lehnt alles andere ab."""
    with pytest.raises(TypeError):
        caesar.verschluesseln(ungueltiger_text, 3)
    with pytest.raises(TypeError):
        caesar.entschluesseln(ungueltiger_text, 3)


def test_reihenfolge_der_pruefungen_ist_egal():
    """Sind Text *und* Schlüssel falsch, kommt trotzdem ein TypeError."""
    with pytest.raises(TypeError):
        caesar.verschluesseln(None, "drei")


# ---------------------------------------------------------------------------
# 9. Doctests und Modulhygiene
# ---------------------------------------------------------------------------

def test_doctests_im_modul_laufen_durch():
    """Die Pflicht-Doctests müssen vorhanden sein und stimmen."""
    ergebnis = doctest.testmod(caesar, verbose=False)
    assert ergebnis.attempted > 0, "Im Modul steht kein einziger Doctest."
    assert ergebnis.failed == 0


def test_pflicht_doctests_enthalten_die_referenzwerte():
    """HUND -> KXQG, KXQG -> HUND, Z + 1 -> A, A + (-1) -> Z."""
    doku = " ".join(
        text or ""
        for text in (
            caesar.__doc__,
            caesar.verschluesseln.__doc__,
            caesar.entschluesseln.__doc__,
        )
    )
    for referenzwert in ("HUND", "KXQG", "'A'", "'Z'"):
        assert referenzwert in doku, f"{referenzwert} fehlt in den Doctests."


# Die Projektregel "kein GUI-Code in crypto/" wird zentral in
# tests/test_zusammenspiel.py über den Syntaxbaum geprüft – für alle Module
# auf einmal, statt in jeder Testdatei erneut.


