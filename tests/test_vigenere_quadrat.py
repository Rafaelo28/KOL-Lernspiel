"""Tests für das Vigenère-Quadrat (crypto/vigenere_quadrat.py).

Alle Erwartungswerte in dieser Datei sind aus der Spezifikation und aus
``dokumentation/Handbuchtexte.md`` von Hand hergeleitet – nie aus der
Implementierung übernommen. Die Rechenvorschrift, gegen die geprüft wird,
lautet (Handbuch Seite 3, Arbeitsplan 1.5):

    Feld in Zeile k (Schlüsselbuchstabe) und Spalte m (Nachrichtenbuchstabe)
    = Buchstabe mit dem Index (k + m) mod 26, wobei A = 0.

Die Handbuch-Referenzwerte, die immer stimmen müssen:

* Zeile A ist das normale Alphabet.
* Das Feld (Zeile R, Spalte H) ist ein Y.
* HUND + Schlüsselwort ROT ergibt YIGU.
* YIGU + Schlüsselwort ROT ergibt wieder HUND.

Damit die Prüfung unabhängig bleibt, rechnet diese Datei die Formel selbst
nach (``_erwartetes_feld``) und baut ganze Texte ausschließlich über die
drei öffentlichen Funktionen des Moduls zusammen. ``crypto/vigenere.py``
wird bewusst **nicht** importiert: Tabelle und Formel sollen zwei getrennte
Wege bleiben.
"""

import ast
import inspect

import pytest

from crypto.normalize import ALPHABET, LEERZEICHEN, normalisieren, ohne_leerzeichen
from crypto import vigenere_quadrat
from crypto.vigenere_quadrat import (
    erzeuge_quadrat,
    klarbuchstabe_finden,
    verschluesselter_buchstabe,
)

# ───────────────────────────────────────────────────────────────────────────
# Testdaten aus dokumentation/Handbuchtexte.md
# ───────────────────────────────────────────────────────────────────────────

# Seite 1, die zehn Caesar-Übungswörter – hier als kurze Klartexte benutzt.
UEBUNGSWOERTER = [
    "HUND", "KATZE", "MAUS", "BURG", "FELS",
    "WALD", "STERN", "MOND", "SAND", "TURM",
]

# Seite 3, die zehn Vigenère-Übungssätze.
UEBUNGSSAETZE = [
    "ICH BIN IN SICHERHEIT",
    "STANDORT UNBEKANNT",
    "NAHE DEM WRACK",
    "RICHTUNG NORDEN",
    "KEIN WASSER MEHR",
    "VERFOLGER SIND NAH",
    "BRAUCHE SOFORT HILFE",
    "BIN NOCH AM LEBEN",
    "WARTE AUF RETTUNG",
    "SIGNAL WIRD SCHWACH",
]

# Die Schlüsselwörter, die das Handbuch am Ende von Seite 3 vorschlägt.
SCHLUESSELWOERTER = ["ROT", "WEG", "TAG"]


# ───────────────────────────────────────────────────────────────────────────
# Unabhängige Nachrechnung und Hilfsmittel für ganze Texte
# ───────────────────────────────────────────────────────────────────────────

def _erwartetes_feld(zeile, spalte):
    """Rechnet ein Quadratfeld allein aus der Spezifikation nach.

    ``zeile`` und ``spalte`` sind Indizes von 0 bis 25. Die Funktion kennt
    das geprüfte Modul nicht – sie setzt nur die Formel (k + m) mod 26 um.
    """
    return ALPHABET[(zeile + spalte) % len(ALPHABET)]


def _mit_quadrat_verschluesseln(klartext, schluesselwort):
    """Verschlüsselt einen ganzen Text ausschließlich über die Tabelle.

    So, wie es die Spielenden auf Papier tun: Für jeden Buchstaben den
    Kreuzungspunkt aus Schlüssel- und Nachrichtenbuchstabe ablesen.
    Leerzeichen bleiben stehen (Regel 3) und schieben den Schlüsselindex
    nicht weiter (Regel 7).
    """
    text = normalisieren(klartext)
    schluessel = ohne_leerzeichen(schluesselwort)
    if not schluessel:
        raise ValueError("Das Schlüsselwort braucht mindestens einen Buchstaben.")

    ergebnis = []
    stelle = 0
    for zeichen in text:
        if zeichen == LEERZEICHEN:
            ergebnis.append(LEERZEICHEN)
            continue
        schluesselbuchstabe = schluessel[stelle % len(schluessel)]
        ergebnis.append(verschluesselter_buchstabe(schluesselbuchstabe, zeichen))
        stelle += 1
    return "".join(ergebnis)


def _mit_quadrat_entschluesseln(geheimtext, schluesselwort):
    """Entschlüsselt einen ganzen Text ausschließlich über die Tabelle.

    Gegenstück zu :func:`_mit_quadrat_verschluesseln`: In der Zeile des
    Schlüsselbuchstabens den Geheimbuchstaben suchen und den Spaltenkopf
    ablesen.
    """
    text = normalisieren(geheimtext)
    schluessel = ohne_leerzeichen(schluesselwort)
    if not schluessel:
        raise ValueError("Das Schlüsselwort braucht mindestens einen Buchstaben.")

    ergebnis = []
    stelle = 0
    for zeichen in text:
        if zeichen == LEERZEICHEN:
            ergebnis.append(LEERZEICHEN)
            continue
        schluesselbuchstabe = schluessel[stelle % len(schluessel)]
        ergebnis.append(klarbuchstabe_finden(schluesselbuchstabe, zeichen))
        stelle += 1
    return "".join(ergebnis)


def _leerzeichen_stellen(text):
    """Gibt die Positionen aller Leerzeichen eines Textes zurück."""
    return [stelle for stelle, zeichen in enumerate(text) if zeichen == LEERZEICHEN]


# ───────────────────────────────────────────────────────────────────────────
# 1. Aufbau des Quadrats
# ───────────────────────────────────────────────────────────────────────────

def test_quadrat_hat_26_zeilen_zu_je_26_feldern():
    """Das Quadrat ist ein sauberes Rechteck – die UI baut daraus ein Grid."""
    quadrat = erzeuge_quadrat()

    assert isinstance(quadrat, list)
    assert len(quadrat) == 26
    for zeile in quadrat:
        assert isinstance(zeile, list)
        assert len(zeile) == 26


def test_quadrat_enthaelt_nur_einzelne_grossbuchstaben():
    """In jedem der 676 Felder steht genau ein Buchstabe von A bis Z."""
    for zeile in erzeuge_quadrat():
        for feld in zeile:
            assert isinstance(feld, str)
            assert len(feld) == 1
            assert feld in ALPHABET


def test_zeile_a_ist_das_normale_alphabet():
    """Handbuch-Referenzwert: Zeile A steht für die Verschiebung 0."""
    assert "".join(erzeuge_quadrat()[0]) == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def test_zeile_r_laeuft_am_ende_wieder_bei_a_weiter():
    """Zeile R ist von Hand abgezählt: R S T ... Z, dann A B ... Q."""
    zeile_r = "".join(erzeuge_quadrat()[ALPHABET.index("R")])

    assert zeile_r == "RSTUVWXYZABCDEFGHIJKLMNOPQ"


def test_zeile_z_zeigt_den_umbruch_von_z_nach_a():
    """Randfall: In der letzten Zeile bricht schon nach dem ersten Feld um."""
    zeile_z = "".join(erzeuge_quadrat()[ALPHABET.index("Z")])

    assert zeile_z == "ZABCDEFGHIJKLMNOPQRSTUVWXY"
    # Das allerletzte Feld (Z, Z) ist (25 + 25) mod 26 = 24, also Y.
    assert erzeuge_quadrat()[25][25] == "Y"


@pytest.mark.parametrize("zeilenindex", range(26))
def test_jede_zeile_ist_das_um_ihren_index_gedrehte_alphabet(zeilenindex):
    """Zeile k ist das Alphabet, um k Stellen nach links gedreht."""
    erwartet = ALPHABET[zeilenindex:] + ALPHABET[:zeilenindex]

    assert "".join(erzeuge_quadrat()[zeilenindex]) == erwartet


def test_jedes_der_676_felder_entspricht_der_formel():
    """Kernprüfung: (k + m) mod 26 – unabhängig nachgerechnet."""
    quadrat = erzeuge_quadrat()

    for zeile in range(26):
        for spalte in range(26):
            assert quadrat[zeile][spalte] == _erwartetes_feld(zeile, spalte), (
                f"Feld (Zeile {ALPHABET[zeile]}, Spalte {ALPHABET[spalte]}) "
                f"ist falsch."
            )


@pytest.mark.parametrize("zeilenindex", range(26))
def test_jede_zeile_enthaelt_jeden_buchstaben_genau_einmal(zeilenindex):
    """Nur so ist das Entschlüsseln über die Zeile überhaupt eindeutig."""
    zeile = erzeuge_quadrat()[zeilenindex]

    assert sorted(zeile) == sorted(ALPHABET)


@pytest.mark.parametrize("spaltenindex", range(26))
def test_jede_spalte_enthaelt_jeden_buchstaben_genau_einmal(spaltenindex):
    """Auch spaltenweise ist das Quadrat ein lateinisches Quadrat."""
    spalte = [zeile[spaltenindex] for zeile in erzeuge_quadrat()]

    assert sorted(spalte) == sorted(ALPHABET)


def test_erste_spalte_traegt_dieselben_buchstaben_wie_die_zeilenkoepfe():
    """Spalte A gibt jeden Schlüsselbuchstaben unverändert zurück.

    Damit darf die UI schlicht ALPHABET als Zeilenbeschriftung verwenden.
    """
    erste_spalte = "".join(zeile[0] for zeile in erzeuge_quadrat())

    assert erste_spalte == ALPHABET


def test_quadrat_ist_symmetrisch():
    """(k + m) ist vertauschbar – Feld (R, H) und Feld (H, R) sind gleich."""
    quadrat = erzeuge_quadrat()

    for zeile in range(26):
        for spalte in range(26):
            assert quadrat[zeile][spalte] == quadrat[spalte][zeile]


def test_jeder_aufruf_liefert_ein_frisches_quadrat():
    """Die UI darf ihr Quadrat umbauen, ohne andere Aufrufer zu stören."""
    erstes = erzeuge_quadrat()
    erstes[0][0] = "VERAENDERT"
    erstes[5].append("ZUSATZ")

    zweites = erzeuge_quadrat()

    assert zweites[0][0] == "A"
    assert len(zweites[5]) == 26
    assert erstes is not zweites


def test_die_zeilen_sind_untereinander_eigene_listen():
    """Kein geteiltes Zeilenobjekt – sonst wirkt ein Umbau in allen Zeilen.

    Als Markierung dient bewusst kein Buchstabe: "X" käme in der ersten
    Spalte ohnehin schon vor und würde die Zählung verfälschen.
    """
    quadrat = erzeuge_quadrat()
    quadrat[3][0] = "*"

    assert [zeile[0] for zeile in quadrat].count("*") == 1
    assert quadrat[0][0] == "A"


# ───────────────────────────────────────────────────────────────────────────
# 2. Verschlüsseln: der Kreuzungspunkt
# ───────────────────────────────────────────────────────────────────────────

def test_handbuch_kreuzungspunkt_zeile_r_spalte_h_ist_y():
    """Der wörtlich im Handbuch genannte Referenzwert."""
    assert verschluesselter_buchstabe("R", "H") == "Y"


@pytest.mark.parametrize(
    "schluesselbuchstabe, klarbuchstabe, erwartet",
    [
        ("R", "H", "Y"),   # Handbuch Schritt 1
        ("O", "U", "I"),   # Handbuch Schritt 2
        ("T", "N", "G"),   # Handbuch Schritt 3
        ("R", "D", "U"),   # Handbuch Schritt 4
    ],
)
def test_handbuchbeispiel_hund_mit_rot_schritt_fuer_schritt(
    schluesselbuchstabe, klarbuchstabe, erwartet
):
    """Die vier Einzelschritte des Beispiels HUND + ROT → YIGU."""
    assert verschluesselter_buchstabe(schluesselbuchstabe, klarbuchstabe) == erwartet


def test_handbuchbeispiel_hund_mit_rot_ergibt_yigu():
    """Alle vier Schritte zusammengesetzt ergeben den Handbuch-Geheimtext."""
    geheim = "".join(
        verschluesselter_buchstabe(schluessel, klar)
        for schluessel, klar in zip("ROTR", "HUND")
    )

    assert geheim == "YIGU"


@pytest.mark.parametrize(
    "schluesselbuchstabe, klarbuchstabe",
    [("r", "h"), ("R", "h"), ("r", "H")],
)
def test_verschluesseln_akzeptiert_kleinbuchstaben(schluesselbuchstabe, klarbuchstabe):
    """Regel 1 der Textkonvention: Kleinschreibung ist nie ein Fehler."""
    assert verschluesselter_buchstabe(schluesselbuchstabe, klarbuchstabe) == "Y"


@pytest.mark.parametrize("klarbuchstabe", list(ALPHABET))
def test_schluessel_a_veraendert_den_buchstaben_nicht(klarbuchstabe):
    """A steht für die Verschiebung 0 – Zeile A ist die Identität."""
    assert verschluesselter_buchstabe("A", klarbuchstabe) == klarbuchstabe


def test_verschluesselter_buchstabe_liest_wirklich_aus_dem_quadrat():
    """Anzeige und Ergebnis müssen dieselbe Quelle haben (alle 676 Felder)."""
    quadrat = erzeuge_quadrat()

    for zeile, schluesselbuchstabe in enumerate(ALPHABET):
        for spalte, klarbuchstabe in enumerate(ALPHABET):
            assert (
                verschluesselter_buchstabe(schluesselbuchstabe, klarbuchstabe)
                == quadrat[zeile][spalte]
            )


def test_verschluesseln_ist_in_beiden_buchstaben_vertauschbar():
    """Folgt aus der Symmetrie des Quadrats – nützlich als Gegenprobe."""
    for schluesselbuchstabe in ALPHABET:
        for klarbuchstabe in ALPHABET:
            assert verschluesselter_buchstabe(
                schluesselbuchstabe, klarbuchstabe
            ) == verschluesselter_buchstabe(klarbuchstabe, schluesselbuchstabe)


def test_verschluesseln_am_alphabetrand_bricht_korrekt_um():
    """Randfälle Z→A: (B, Z) ist A, (Z, B) ist A, (Z, Z) ist Y."""
    assert verschluesselter_buchstabe("B", "Z") == "A"
    assert verschluesselter_buchstabe("Z", "B") == "A"
    assert verschluesselter_buchstabe("Z", "Z") == "Y"
    assert verschluesselter_buchstabe("A", "A") == "A"


# ───────────────────────────────────────────────────────────────────────────
# 3. Entschlüsseln: der Spaltenkopf
# ───────────────────────────────────────────────────────────────────────────

def test_handbuch_zeile_r_geheimbuchstabe_y_steht_in_spalte_h():
    """Der Rückweg aus dem Handbuch, Seite 3."""
    assert klarbuchstabe_finden("R", "Y") == "H"


@pytest.mark.parametrize(
    "schluesselbuchstabe, geheimbuchstabe, erwartet",
    [
        ("R", "Y", "H"),   # Handbuch Schritt 1
        ("O", "I", "U"),   # Handbuch Schritt 2
        ("T", "G", "N"),   # Handbuch Schritt 3
        ("R", "U", "D"),   # Handbuch Schritt 4
    ],
)
def test_handbuchbeispiel_yigu_mit_rot_schritt_fuer_schritt(
    schluesselbuchstabe, geheimbuchstabe, erwartet
):
    """Die vier Einzelschritte des Beispiels YIGU + ROT → HUND."""
    assert klarbuchstabe_finden(schluesselbuchstabe, geheimbuchstabe) == erwartet


def test_handbuchbeispiel_yigu_mit_rot_ergibt_hund():
    """Alle vier Schritte zusammengesetzt ergeben wieder den Klartext."""
    klar = "".join(
        klarbuchstabe_finden(schluessel, geheim)
        for schluessel, geheim in zip("ROTR", "YIGU")
    )

    assert klar == "HUND"


@pytest.mark.parametrize(
    "schluesselbuchstabe, geheimbuchstabe",
    [("r", "y"), ("R", "y"), ("r", "Y")],
)
def test_entschluesseln_akzeptiert_kleinbuchstaben(schluesselbuchstabe, geheimbuchstabe):
    """Regel 1 der Textkonvention gilt auch für den Rückweg."""
    assert klarbuchstabe_finden(schluesselbuchstabe, geheimbuchstabe) == "H"


@pytest.mark.parametrize("geheimbuchstabe", list(ALPHABET))
def test_schluessel_a_gibt_den_geheimbuchstaben_unveraendert_zurueck(geheimbuchstabe):
    """Zeile A ist auch beim Entschlüsseln die Identität."""
    assert klarbuchstabe_finden("A", geheimbuchstabe) == geheimbuchstabe


def test_entschluesseln_am_alphabetrand_bricht_korrekt_um():
    """Gegenprobe zu den Randfällen des Verschlüsselns."""
    assert klarbuchstabe_finden("B", "A") == "Z"
    assert klarbuchstabe_finden("Z", "A") == "B"
    assert klarbuchstabe_finden("Z", "Y") == "Z"


def test_rundlauf_ueber_alle_676_buchstabenpaare():
    """Entschlüsseln hebt Verschlüsseln für jede Kombination wieder auf."""
    for schluesselbuchstabe in ALPHABET:
        for klarbuchstabe in ALPHABET:
            geheim = verschluesselter_buchstabe(schluesselbuchstabe, klarbuchstabe)
            assert klarbuchstabe_finden(schluesselbuchstabe, geheim) == klarbuchstabe


def test_rundlauf_in_der_gegenrichtung_ueber_alle_676_paare():
    """Auch andersherum: erst Spaltenkopf suchen, dann wieder ablesen."""
    for schluesselbuchstabe in ALPHABET:
        for geheimbuchstabe in ALPHABET:
            klar = klarbuchstabe_finden(schluesselbuchstabe, geheimbuchstabe)
            assert (
                verschluesselter_buchstabe(schluesselbuchstabe, klar)
                == geheimbuchstabe
            )


# ───────────────────────────────────────────────────────────────────────────
# 4. Ganze Texte über die Tabelle (Regeln 3 und 7 der Textkonvention)
# ───────────────────────────────────────────────────────────────────────────

def test_hilfsfunktionen_reproduzieren_das_handbuchbeispiel():
    """Verankert die Testhilfen selbst am Handbuch, bevor sie benutzt werden."""
    assert _mit_quadrat_verschluesseln("HUND", "ROT") == "YIGU"
    assert _mit_quadrat_entschluesseln("YIGU", "ROT") == "HUND"


@pytest.mark.parametrize(
    "klartext, schluesselwort, erwartet",
    [
        # Jeder Wert unten wurde von Hand über (k + m) mod 26 abgezählt.
        ("HUND", "ROT", "YIGU"),
        ("NAHE DEM WRACK", "TAG", "GANX DKF WXTCQ"),
        ("WARTE AUF RETTUNG", "WEG", "SEXPI GQJ XAXZQRM"),
        ("KEIN WASSER MEHR", "ROT", "BSBE KTJGXI AXYF"),
    ],
)
def test_handbuchsaetze_von_hand_nachgerechnet(klartext, schluesselwort, erwartet):
    """Ganze Übungssätze aus dem Handbuch, Zelle für Zelle nachgezählt."""
    assert _mit_quadrat_verschluesseln(klartext, schluesselwort) == erwartet
    assert _mit_quadrat_entschluesseln(erwartet, schluesselwort) == klartext


@pytest.mark.parametrize("klartext", UEBUNGSWOERTER + UEBUNGSSAETZE)
@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_rundlauf_fuer_alle_uebungstexte(klartext, schluesselwort):
    """entschlüsseln(verschlüsseln(x)) == x für alle Texte des Handbuchs."""
    geheim = _mit_quadrat_verschluesseln(klartext, schluesselwort)

    assert _mit_quadrat_entschluesseln(geheim, schluesselwort) == klartext


@pytest.mark.parametrize("klartext", UEBUNGSSAETZE)
@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_leerzeichen_bleiben_an_genau_denselben_stellen(klartext, schluesselwort):
    """Regel 3: Die Wortgrenzen bleiben im Geheimtext sichtbar."""
    geheim = _mit_quadrat_verschluesseln(klartext, schluesselwort)

    assert _leerzeichen_stellen(geheim) == _leerzeichen_stellen(klartext)
    assert len(geheim) == len(klartext)
    assert [len(wort) for wort in geheim.split(LEERZEICHEN)] == [
        len(wort) for wort in klartext.split(LEERZEICHEN)
    ]


def test_leerzeichen_zaehlen_den_schluesselindex_nicht_weiter():
    """Regel 7: HUND und HU ND ergeben dieselben vier Geheimbuchstaben."""
    assert _mit_quadrat_verschluesseln("HU ND", "ROT") == "YI GU"
    assert _mit_quadrat_verschluesseln("H U N D", "ROT") == "Y I G U"


def test_leerer_text_bleibt_leer():
    """Randfall: Es gibt nichts abzulesen."""
    assert _mit_quadrat_verschluesseln("", "ROT") == ""
    assert _mit_quadrat_entschluesseln("", "ROT") == ""


def test_text_aus_lauter_leerzeichen_wird_zu_leerem_text():
    """Randfall: Normalisieren schneidet Rand-Leerzeichen weg (Regel 6)."""
    assert _mit_quadrat_verschluesseln("   ", "ROT") == ""
    assert _mit_quadrat_verschluesseln("\t \n", "ROT") == ""


def test_umlaute_und_satzzeichen_werden_vorher_ersetzt_und_entfernt():
    """Regeln 5 und 6: Aus "Grüße" wird GRUESSE, dann erst wird abgelesen."""
    # GRUESSE + ROT: G+R=X, R+O=F, U+T=N, E+R=V, S+O=G, S+T=L, E+R=V
    assert _mit_quadrat_verschluesseln("Grüße", "ROT") == "XFNVGLV"

    # "Hallo, hört mich jemand?" → HALLO HOERT MICH JEMAND, Schlüssel WEG.
    assert (
        _mit_quadrat_verschluesseln("Hallo, hört mich jemand?", "WEG")
        == "DERHS NKIXP QOYL PAQGJH"
    )


def test_mehrere_woerter_werden_durchgehend_weiterverschluesselt():
    """Der Schlüssel läuft über Wortgrenzen hinweg weiter, nur eben ohne
    die Leerzeichen mitzuzählen."""
    ohne_luecken = _mit_quadrat_verschluesseln("NAHEDEMWRACK", "TAG")
    mit_luecken = _mit_quadrat_verschluesseln("NAHE DEM WRACK", "TAG")

    assert mit_luecken.replace(LEERZEICHEN, "") == ohne_luecken


def test_sehr_langer_text_laeuft_sauber_durch():
    """Belastungsprobe: alle Übungssätze hintereinander, Rundlauf und Länge."""
    langer_text = normalisieren(" ".join(UEBUNGSSAETZE * 5))
    geheim = _mit_quadrat_verschluesseln(langer_text, "ROT")

    assert len(ohne_leerzeichen(langer_text)) > 750
    assert len(geheim) == len(langer_text)
    assert _leerzeichen_stellen(geheim) == _leerzeichen_stellen(langer_text)
    assert _mit_quadrat_entschluesseln(geheim, "ROT") == langer_text


def test_schluesselwort_der_laenge_eins_wirkt_wie_caesar():
    """Grenzfall: Ein einziger Schlüsselbuchstabe verschiebt überall gleich.

    Mit Schlüssel D (Index 3) muss HUND zu KXQG werden – genau der
    Caesar-Referenzwert von Seite 1 des Handbuchs.
    """
    assert _mit_quadrat_verschluesseln("HUND", "D") == "KXQG"
    assert _mit_quadrat_entschluesseln("KXQG", "D") == "HUND"


def test_schluesselwort_a_laesst_den_text_unveraendert():
    """Grenzfall: Verschiebung 0 an jeder Stelle."""
    assert _mit_quadrat_verschluesseln("ZEIT WIRD KNAPP", "A") == "ZEIT WIRD KNAPP"


def test_schluesselwort_laenger_als_der_text_ist_unproblematisch():
    """Grenzfall: Vom Schlüssel wird schlicht nur der Anfang gebraucht."""
    # HUND mit dem Schlüsselanfang R, O, T, R – das Handbuchbeispiel.
    assert _mit_quadrat_verschluesseln("HUND", "ROTROTROTROT") == "YIGU"


# ───────────────────────────────────────────────────────────────────────────
# 5. Ungültige Eingaben
# ───────────────────────────────────────────────────────────────────────────

# Texte, die kein einzelner Buchstabe von A bis Z sind: unbrauchbarer Wert
# bei richtigem Typ -> ValueError.
UNGUELTIGE_EINGABEN = [
    ("", "leerer Text"),
    (" ", "Leerzeichen"),
    ("AB", "zwei Buchstaben"),
    ("HUND", "ganzes Wort"),
    ("4", "Ziffer"),
    ("!", "Satzzeichen"),
    ("Ä", "Umlaut"),
    ("ß", "scharfes S"),
    ("é", "Buchstabe mit Akzent"),
    ("\n", "Zeilenumbruch"),
]

# Gar kein Text: Programmierfehler im aufrufenden Code -> TypeError.
# Die Trennung folgt der Fehlerart-Konvention im Kopf von crypto/normalize.py.
FALSCHE_TYPEN = [
    (3, "Zahl statt Text"),
    (None, "None"),
    (["A"], "Liste"),
    (b"A", "bytes"),
]


@pytest.mark.parametrize(
    "eingabe, beschreibung", UNGUELTIGE_EINGABEN, ids=[b for _, b in UNGUELTIGE_EINGABEN]
)
def test_verschluesseln_lehnt_ungueltigen_schluesselbuchstaben_ab(eingabe, beschreibung):
    """Als Zeile ist nur genau ein Buchstabe von A bis Z erlaubt."""
    with pytest.raises(ValueError):
        verschluesselter_buchstabe(eingabe, "H")


@pytest.mark.parametrize(
    "eingabe, beschreibung", UNGUELTIGE_EINGABEN, ids=[b for _, b in UNGUELTIGE_EINGABEN]
)
def test_verschluesseln_lehnt_ungueltigen_klarbuchstaben_ab(eingabe, beschreibung):
    """Als Spalte ist nur genau ein Buchstabe von A bis Z erlaubt."""
    with pytest.raises(ValueError):
        verschluesselter_buchstabe("R", eingabe)


@pytest.mark.parametrize(
    "eingabe, beschreibung", UNGUELTIGE_EINGABEN, ids=[b for _, b in UNGUELTIGE_EINGABEN]
)
def test_entschluesseln_lehnt_ungueltigen_schluesselbuchstaben_ab(eingabe, beschreibung):
    """Auch der Rückweg braucht eine gültige Zeile."""
    with pytest.raises(ValueError):
        klarbuchstabe_finden(eingabe, "Y")


@pytest.mark.parametrize(
    "eingabe, beschreibung", UNGUELTIGE_EINGABEN, ids=[b for _, b in UNGUELTIGE_EINGABEN]
)
def test_entschluesseln_lehnt_ungueltigen_geheimbuchstaben_ab(eingabe, beschreibung):
    """Ein Geheimbuchstabe, der im Quadrat nicht vorkommt, ist ein Fehler."""
    with pytest.raises(ValueError):
        klarbuchstabe_finden("R", eingabe)


def test_fehlermeldung_ist_deutsch_und_nennt_die_rolle_des_buchstabens():
    """Die Meldung muss zeigen, *welcher* der beiden Buchstaben falsch war."""
    with pytest.raises(ValueError) as fehler:
        verschluesselter_buchstabe("4", "H")
    assert "Schlüsselbuchstabe" in str(fehler.value)

    with pytest.raises(ValueError) as fehler:
        verschluesselter_buchstabe("R", "4")
    assert "Nachrichtenbuchstabe" in str(fehler.value)

    with pytest.raises(ValueError) as fehler:
        klarbuchstabe_finden("R", "4")
    assert "Geheimbuchstabe" in str(fehler.value)


def test_fehlermeldung_enthaelt_keine_englischen_standardtexte():
    """Fehlermeldungen sind Spieltext – sie müssen deutsch sein."""
    with pytest.raises(ValueError) as fehler:
        verschluesselter_buchstabe("R", " ")
    meldung = str(fehler.value)

    assert "Buchstabe" in meldung
    assert "substring not found" not in meldung
    assert "is not in" not in meldung


def test_leerzeichen_wird_nicht_stillschweigend_durchgereicht():
    """Regel 3 ist Sache des Aufrufers – das Quadrat kennt kein Leerzeichen."""
    with pytest.raises(ValueError):
        verschluesselter_buchstabe(" ", "H")
    with pytest.raises(ValueError):
        klarbuchstabe_finden("R", " ")


# ───────────────────────────────────────────────────────────────────────────
# 6. Bauvorschriften des Moduls
# ───────────────────────────────────────────────────────────────────────────

def _importierte_module():
    """Liest alle Import-Namen aus der Quelldatei des geprüften Moduls.

    Über den Syntaxbaum statt über eine Textsuche, damit Erwähnungen im
    Fließtext des Docstrings nicht fälschlich als Import gelten.
    """
    baum = ast.parse(inspect.getsource(vigenere_quadrat))
    namen = set()
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            namen.update(teil.name for teil in knoten.names)
        elif isinstance(knoten, ast.ImportFrom):
            # Relative Importe ("from .normalize import ...") werden auf ihren
            # vollen Namen aufgelöst. Ohne das würde "from .vigenere import"
            # als schlichtes "vigenere" hier durchrutschen und der
            # Unabhängigkeitstest darunter wäre wirkungslos.
            if knoten.level:
                namen.add("crypto." + (knoten.module or ""))
            elif knoten.module:
                namen.add(knoten.module)
    return namen


def test_modul_importiert_die_rechenvariante_nicht():
    """Tabelle und Formel müssen zwei unabhängige Wege bleiben.

    Sonst wäre der spätere Vergleichstest zwischen crypto/vigenere.py und
    diesem Modul wertlos.
    """
    assert "crypto.vigenere" not in _importierte_module()


def test_modul_enthaelt_keinen_gui_code():
    """Projektregel: crypto/ importiert weder tkinter noch ui/ oder game/."""
    for modulname in _importierte_module():
        wurzel = modulname.split(".")[0]
        assert wurzel not in {"tkinter", "ui", "game"}, (
            f"crypto/vigenere_quadrat.py darf {modulname!r} nicht importieren."
        )


def test_modul_bringt_nur_standardbibliothek_und_eigenen_code_mit():
    """Keine externen Abhängigkeiten in der Verschlüsselungslogik."""
    erlaubt = {"crypto.normalize"}
    for modulname in _importierte_module():
        assert modulname in erlaubt, f"Unerwarteter Import: {modulname!r}"


def test_das_quadrat_ist_nicht_abgetippt_sondern_erzeugt():
    """Im Quelltext darf keine fertige Buchstabenzeile stehen (Tippfehler!).

    Geprüft wird, dass keine der 26 Zeilen als Zeichenkette in der Datei
    auftaucht – ausgenommen das normale Alphabet, das aus crypto.normalize
    kommt und in den Doctests als erwartetes Ergebnis steht.
    """
    quelltext = inspect.getsource(vigenere_quadrat)

    for zeilenindex in range(1, 26):
        zeile = ALPHABET[zeilenindex:] + ALPHABET[:zeilenindex]
        if zeilenindex == ALPHABET.index("R"):
            continue  # Zeile R steht als erwartetes Doctest-Ergebnis drin.
        assert zeile not in quelltext


def test_funktionen_haben_deutsche_docstrings():
    """Dokumentationspflicht des Projekts."""
    for funktion in (erzeuge_quadrat, verschluesselter_buchstabe, klarbuchstabe_finden):
        assert funktion.__doc__, f"{funktion.__name__} hat keinen Docstring."
        assert len(funktion.__doc__.strip()) > 20


# ───────────────────────────────────────────────────────────────────────────
# Falscher Typ ergibt TypeError, nicht ValueError
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "eingabe, beschreibung", FALSCHE_TYPEN, ids=[b for _, b in FALSCHE_TYPEN]
)
def test_falscher_typ_ergibt_typeerror(eingabe, beschreibung):
    """Konvention: falscher Typ -> TypeError, unbrauchbarer Wert -> ValueError.

    Ein ``TypeError`` bedeutet, dass der aufrufende Code etwas falsch macht;
    ein ``ValueError`` bedeutet, dass der Wert nicht ins Quadrat passt. Die
    Oberfläche in Phase 6 muss die beiden unterscheiden können, und alle
    Module in ``crypto/`` müssen sich dabei gleich verhalten.
    """
    for aufruf in (
        lambda: vigenere_quadrat.verschluesselter_buchstabe(eingabe, "H"),
        lambda: vigenere_quadrat.verschluesselter_buchstabe("R", eingabe),
        lambda: vigenere_quadrat.klarbuchstabe_finden(eingabe, "Y"),
        lambda: vigenere_quadrat.klarbuchstabe_finden("R", eingabe),
    ):
        with pytest.raises(TypeError):
            aufruf()


def test_die_module_werfen_bei_falschem_typ_dieselbe_fehlerart():
    """normalize, substitution und vigenere_quadrat müssen sich gleich verhalten."""
    from crypto import normalize, substitution, vigenere

    with pytest.raises(TypeError):
        normalize.buchstabe_zu_index(3)
    with pytest.raises(TypeError):
        normalize.normalisieren(3)
    with pytest.raises(TypeError):
        substitution.verschluesseln("HUND", ["A", "Q"])
    with pytest.raises(TypeError):
        vigenere.verschluesseln("HUND", 3)
    with pytest.raises(TypeError):
        vigenere_quadrat.verschluesselter_buchstabe(3, "H")
