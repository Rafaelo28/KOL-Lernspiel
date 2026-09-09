"""Tests für :mod:`crypto.vigenere` – Level 3 des Spiels (Arbeitsplan 1.6).

Alle Erwartungswerte in dieser Datei sind von Hand aus der Textkonvention
(``crypto/normalize.py``, Regeln 1–7) und aus ``dokumentation/Handbuchtexte.md``
hergeleitet worden, **nicht** aus der Implementierung abgeschrieben. Die
Rechnung steht jeweils als Kommentar über dem Wert, damit sie nachprüfbar
bleibt: Geheimbuchstabe = ``(Klartext-Index + Schlüssel-Index) % 26`` mit
``A = 0`` – das ist genau das, was das Vigenère-Quadrat des Handbuchs in
Zeile *Schlüssel* und Spalte *Nachricht* stehen hat.

Das Pflicht-Beispiel des Handbuchs (Seite 3, "HUND" mit "ROT"):

>>> verschluesseln("HUND", "ROT")
'YIGU'
>>> entschluesseln("YIGU", "ROT")
'HUND'

Und ein selbst durchgerechneter **mehrwortiger** Fall – daran hängt Regel 7.
Übungssatz 3 von Handbuchseite 3 mit dem Schlüsselwort "TAG"::

    Nachricht  N A H E   D E M   W R A C K
    Schlüssel  T A G T   A G T   A G T A G
    Ergebnis   G A N X   D K F   W X T C Q

Der Schlüssel rückt über dem Leerzeichen *nicht* vor: auf das T über dem "E"
von NAHE folgt das A über dem "D" von DEM, nicht das G.

>>> verschluesseln("NAHE DEM WRACK", "TAG")
'GANX DKF WXTCQ'
>>> entschluesseln("GANX DKF WXTCQ", "TAG")
'NAHE DEM WRACK'
>>> schluessel_ausrichten("NAHE DEM WRACK", "TAG")
'TAGT AGT AGTAG'
"""

import re
from pathlib import Path

import pytest

import crypto.vigenere as vigenere_modul
from crypto.normalize import (
    ALPHABET,
    LEERZEICHEN,
    buchstabe_zu_index,
    normalisieren,
    ohne_leerzeichen,
)
from crypto.vigenere import entschluesseln, schluessel_ausrichten, verschluesseln

# ───────────────────────────────────────────────────────────────────────────
# Material aus dokumentation/Handbuchtexte.md
# ───────────────────────────────────────────────────────────────────────────

# Seite 3, die 10 Übungssätze für Level 3.
UEBUNGSSAETZE_LEVEL3 = (
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
)

# Seite 1, die 10 Caesar-Übungswörter – als kurze, einwortige Gegenprobe.
UEBUNGSWOERTER_LEVEL1 = (
    "HUND",
    "KATZE",
    "MAUS",
    "BURG",
    "FELS",
    "WALD",
    "STERN",
    "MOND",
    "SAND",
    "TURM",
)

# Seite 2, die 10 Substitutions-Übungssätze – zusätzliches mehrwortiges Material.
UEBUNGSSAETZE_LEVEL2 = (
    "ALLES OK",
    "ICH BIN HIER",
    "KOMM SCHNELL",
    "WO BIST DU",
    "BLEIB RUHIG",
    "WEG IST FREI",
    "GEFAHR NAH",
    "ZEIT WIRD KNAPP",
    "PLAN WIRD NEU",
    "HILFE WIRD GEBRAUCHT",
)

# Die im Handbuch-Hinweis vorgeschlagenen Schlüsselwörter für Level 3.
SCHLUESSELWOERTER = ("ROT", "WEG", "TAG")

# ───────────────────────────────────────────────────────────────────────────
# Von Hand durchgerechnete Referenzwerte
# ───────────────────────────────────────────────────────────────────────────

# Jede Zeile: (Klartext, Schlüsselwort, erwarteter Geheimtext).
# Die Rechnung steht jeweils darüber, Index A = 0.
HANDBERECHNETE_PAARE = (
    # Handbuch Seite 3, Pflicht-Beispiel:
    #   H(7)+R(17)=24 -> Y | U(20)+O(14)=34%26=8 -> I
    #   N(13)+T(19)=32%26=6 -> G | D(3)+R(17)=20 -> U
    ("HUND", "ROT", "YIGU"),
    # Übungssatz Seite 2 Nr. 1, Schlüssel ROT. Schlüsselfolge R O T R O (Leer) T R:
    #   A(0)+R(17)=17 -> R | L(11)+O(14)=25 -> Z | L(11)+T(19)=30%26=4 -> E
    #   E(4)+R(17)=21 -> V | S(18)+O(14)=32%26=6 -> G | " "
    #   O(14)+T(19)=33%26=7 -> H | K(10)+R(17)=27%26=1 -> B
    ("ALLES OK", "ROT", "RZEVG HB"),
    # Übungssatz Seite 3 Nr. 3, Schlüssel TAG (Schlüsselfolge TAGT AGT AGTAG):
    #   N+T=13+19=32%26=6 -> G | A+A=0 -> A | H+G=7+6=13 -> N | E+T=4+19=23 -> X
    #   D+A=3 -> D | E+G=4+6=10 -> K | M+T=12+19=31%26=5 -> F
    #   W+A=22 -> W | R+G=17+6=23 -> X | A+T=0+19=19 -> T
    #   C+A=2 -> C | K+G=10+6=16 -> Q
    ("NAHE DEM WRACK", "TAG", "GANX DKF WXTCQ"),
    # Übungssatz Seite 3 Nr. 2, Schlüssel WEG (W=22, E=4, G=6):
    #   S+W=18+22=40%26=14 -> O | T+E=19+4=23 -> X | A+G=0+6=6 -> G
    #   N+W=13+22=35%26=9 -> J | D+E=3+4=7 -> H | O+G=14+6=20 -> U
    #   R+W=17+22=39%26=13 -> N | T+E=19+4=23 -> X | " "
    #   U+G=20+6=26%26=0 -> A | N+W=9 -> J | B+E=1+4=5 -> F | E+G=4+6=10 -> K
    #   K+W=10+22=32%26=6 -> G | A+E=0+4=4 -> E | N+G=13+6=19 -> T
    #   N+W=9 -> J | T+E=23 -> X
    ("STANDORT UNBEKANNT", "WEG", "OXGJHUNX AJFKGETJX"),
    # Übungssatz Seite 3 Nr. 1, Schlüssel ROT (Schlüsselfolge ROT ROT RO TROTROTROT):
    #   I+R=8+17=25 -> Z | C+O=2+14=16 -> Q | H+T=7+19=26%26=0 -> A
    #   B+R=1+17=18 -> S | I+O=8+14=22 -> W | N+T=13+19=32%26=6 -> G
    #   I+R=25 -> Z | N+O=13+14=27%26=1 -> B
    #   S+T=18+19=37%26=11 -> L | I+R=25 -> Z | C+O=16 -> Q | H+T=0 -> A
    #   E+R=4+17=21 -> V | R+O=17+14=31%26=5 -> F | H+T=0 -> A | E+R=21 -> V
    #   I+O=22 -> W | T+T=19+19=38%26=12 -> M
    ("ICH BIN IN SICHERHEIT", "ROT", "ZQA SWG ZB LZQAVFAVWM"),
    # Übungssatz Seite 3 Nr. 9, Schlüssel TAG (Schlüsselfolge TAGTA GTA GTAGTAG):
    #   W+T=22+19=41%26=15 -> P | A+A=0 -> A | R+G=17+6=23 -> X
    #   T+T=38%26=12 -> M | E+A=4 -> E
    #   A+G=6 -> G | U+T=20+19=39%26=13 -> N | F+A=5 -> F
    #   R+G=23 -> X | E+T=4+19=23 -> X | T+A=19 -> T | T+G=19+6=25 -> Z
    #   U+T=13 -> N | N+A=13 -> N | G+G=6+6=12 -> M
    ("WARTE AUF RETTUNG", "TAG", "PAXME GNF XXTZNNM"),
)

# Von Hand gelegte Schlüsselzeilen (untere Zeile der Handbuch-Tabelle).
HANDBERECHNETE_SCHLUESSELZEILEN = (
    ("HUND", "ROT", "ROTR"),
    ("ALLES OK", "ROT", "ROTRO TR"),
    ("NAHE DEM WRACK", "TAG", "TAGT AGT AGTAG"),
    ("STANDORT UNBEKANNT", "WEG", "WEGWEGWE GWEGWEGWE"),
    ("ICH BIN IN SICHERHEIT", "ROT", "ROT ROT RO TROTROTROT"),
    ("WARTE AUF RETTUNG", "TAG", "TAGTA GTA GTAGTAG"),
)


def _positionen_der_leerzeichen(text):
    """Hilfsfunktion: Indizes aller Leerzeichen in ``text`` als Tupel."""
    return tuple(i for i, zeichen in enumerate(text) if zeichen == LEERZEICHEN)


# ───────────────────────────────────────────────────────────────────────────
# 1. Die Referenzwerte aus dem Handbuch
# ───────────────────────────────────────────────────────────────────────────


def test_handbuch_beispiel_hund_wird_mit_rot_zu_yigu():
    """Seite 3 des Handbuchs: HUND + ROT ergibt YIGU (Zeile R, Spalte H = Y)."""
    assert verschluesseln("HUND", "ROT") == "YIGU"


def test_handbuch_beispiel_yigu_wird_mit_rot_wieder_zu_hund():
    """Der Entschlüsselungsteil desselben Handbuch-Beispiels: YIGU -> HUND."""
    assert entschluesseln("YIGU", "ROT") == "HUND"


def test_handbuch_tabelle_schluesselzeile_zu_hund():
    """Die Tabelle "Nachricht H U N D / Schlüssel R O T R" aus dem Handbuch."""
    assert schluessel_ausrichten("HUND", "ROT") == "ROTR"


@pytest.mark.parametrize("klartext, schluesselwort, geheimtext", HANDBERECHNETE_PAARE)
def test_handberechnete_werte_werden_verschluesselt(klartext, schluesselwort, geheimtext):
    """Alle von Hand durchgerechneten Klartext/Geheimtext-Paare stimmen."""
    assert verschluesseln(klartext, schluesselwort) == geheimtext


@pytest.mark.parametrize("klartext, schluesselwort, geheimtext", HANDBERECHNETE_PAARE)
def test_handberechnete_werte_werden_entschluesselt(klartext, schluesselwort, geheimtext):
    """Dieselben Paare rückwärts – Entschlüsseln ist die Umkehrung."""
    assert entschluesseln(geheimtext, schluesselwort) == klartext


@pytest.mark.parametrize(
    "klartext, schluesselwort, schluesselzeile", HANDBERECHNETE_SCHLUESSELZEILEN
)
def test_handberechnete_schluesselzeilen(klartext, schluesselwort, schluesselzeile):
    """Der ausgerichtete Schlüssel entspricht der von Hand gelegten Zeile."""
    assert schluessel_ausrichten(klartext, schluesselwort) == schluesselzeile


# ───────────────────────────────────────────────────────────────────────────
# 2. Regel 7 – das Leerzeichen zählt den Schlüsselindex nicht weiter
# ───────────────────────────────────────────────────────────────────────────


def test_regel7_leerzeichen_ruecken_den_schluessel_nicht_vor():
    """"ALLES OK" mit ROT: die Schlüsselfolge ist R O T R O (Leer) T R.

    Würde das Leerzeichen mitzählen, stünde über dem "O" von OK ein R und
    über dem "K" ein O – das Ergebnis wäre "RZEVG FY" statt "RZEVG HB".
    Genau diesen Unterschied hält Regel 7 fest.
    """
    assert verschluesseln("ALLES OK", "ROT") == "RZEVG HB"
    assert verschluesseln("ALLES OK", "ROT") != "RZEVG FY"


def test_regel7_schluesselzeile_ueberspringt_das_leerzeichen():
    """In "ROTRO TR" folgt auf das O direkt das T – das Leerzeichen zählt nicht."""
    assert schluessel_ausrichten("ALLES OK", "ROT") == "ROTRO TR"


@pytest.mark.parametrize("satz", UEBUNGSSAETZE_LEVEL3 + UEBUNGSSAETZE_LEVEL2)
@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_regel7_geheimtext_ohne_leerzeichen_gleicht_zusammengeschriebenem_text(
    satz, schluesselwort
):
    """Regel 7 präzise formuliert: Leerzeichen ändern die Buchstabenfolge nicht.

    Verschlüsselt man denselben Satz einmal mit und einmal ohne Leerzeichen,
    muss – nach Entfernen der Leerzeichen – dieselbe Buchstabenkette
    herauskommen. Nur dann rückt der Schlüssel wirklich ausschließlich bei
    Buchstaben vor.
    """
    mit_leerzeichen = verschluesseln(satz, schluesselwort)
    ohne = verschluesseln(satz.replace(LEERZEICHEN, ""), schluesselwort)
    assert ohne_leerzeichen(mit_leerzeichen) == ohne


@pytest.mark.parametrize("satz", UEBUNGSSAETZE_LEVEL3)
@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_regel7_gilt_auch_beim_entschluesseln(satz, schluesselwort):
    """Auch rückwärts darf das Leerzeichen den Schlüsselindex nicht weiterzählen."""
    mit_leerzeichen = entschluesseln(satz, schluesselwort)
    ohne = entschluesseln(satz.replace(LEERZEICHEN, ""), schluesselwort)
    assert ohne_leerzeichen(mit_leerzeichen) == ohne


# ───────────────────────────────────────────────────────────────────────────
# 3. Regel 3 – Leerzeichen bleiben an genau denselben Stellen stehen
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("satz", UEBUNGSSAETZE_LEVEL3 + UEBUNGSSAETZE_LEVEL2)
@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_regel3_leerzeichen_bleiben_an_denselben_stellen(satz, schluesselwort):
    """Geheimtext, Klartext und Schlüsselzeile haben dieselben Wortgrenzen."""
    erwartete_positionen = _positionen_der_leerzeichen(normalisieren(satz))

    geheim = verschluesseln(satz, schluesselwort)
    klar_zurueck = entschluesseln(geheim, schluesselwort)
    schluesselzeile = schluessel_ausrichten(satz, schluesselwort)

    assert _positionen_der_leerzeichen(geheim) == erwartete_positionen
    assert _positionen_der_leerzeichen(klar_zurueck) == erwartete_positionen
    assert _positionen_der_leerzeichen(schluesselzeile) == erwartete_positionen


@pytest.mark.parametrize("satz", UEBUNGSSAETZE_LEVEL3)
def test_regel3_laenge_bleibt_erhalten(satz):
    """Klartext und Geheimtext sind gleich lang – sonst passt die Tabelle nicht."""
    normalisiert = normalisieren(satz)
    assert len(verschluesseln(satz, "ROT")) == len(normalisiert)
    assert len(schluessel_ausrichten(satz, "ROT")) == len(normalisiert)


def test_wortgrenzen_bleiben_wortweise_sichtbar():
    """Aus drei Wörtern werden drei Wörter mit denselben Längen."""
    geheim = verschluesseln("NAHE DEM WRACK", "TAG")
    assert [len(wort) for wort in geheim.split(LEERZEICHEN)] == [4, 3, 5]


# ───────────────────────────────────────────────────────────────────────────
# 4. Rundlauf: entschluesseln(verschluesseln(x)) == x
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("satz", UEBUNGSSAETZE_LEVEL3)
@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_rundlauf_uebungssaetze_level3(satz, schluesselwort):
    """Alle 10 Übungssätze von Handbuchseite 3, mit jedem Schlüsselwort."""
    assert entschluesseln(verschluesseln(satz, schluesselwort), schluesselwort) == satz


@pytest.mark.parametrize("wort", UEBUNGSWOERTER_LEVEL1)
@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_rundlauf_uebungswoerter_level1(wort, schluesselwort):
    """Die kurzen Einzelwörter von Seite 1 als Gegenprobe ohne Leerzeichen."""
    assert entschluesseln(verschluesseln(wort, schluesselwort), schluesselwort) == wort


@pytest.mark.parametrize("satz", UEBUNGSSAETZE_LEVEL2)
@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_rundlauf_uebungssaetze_level2(satz, schluesselwort):
    """Auch das mehrwortige Material von Seite 2 läuft sauber hin und zurück."""
    assert entschluesseln(verschluesseln(satz, schluesselwort), schluesselwort) == satz


@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_rundlauf_in_der_anderen_reihenfolge(schluesselwort):
    """Auch verschluesseln(entschluesseln(x)) muss wieder x ergeben."""
    text = "SIGNAL WIRD SCHWACH"
    assert verschluesseln(entschluesseln(text, schluesselwort), schluesselwort) == text


@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_rundlauf_sehr_langer_text(schluesselwort):
    """Sehr langer Text: 40 Wiederholungen aller 10 Übungssätze (über 7000 Zeichen)."""
    langer_text = LEERZEICHEN.join(UEBUNGSSAETZE_LEVEL3 * 40)
    geheim = verschluesseln(langer_text, schluesselwort)

    assert len(geheim) == len(langer_text) > 7000
    assert _positionen_der_leerzeichen(geheim) == _positionen_der_leerzeichen(langer_text)
    assert entschluesseln(geheim, schluesselwort) == langer_text


def test_rundlauf_mit_langem_schluesselwort():
    """Ein Schlüsselwort, das länger ist als der übliche Dreier, stört nicht."""
    text = "BRAUCHE SOFORT HILFE"
    lang = "DIAMANTENRAUB"
    assert entschluesseln(verschluesseln(text, lang), lang) == text


# ───────────────────────────────────────────────────────────────────────────
# 5. Zusammenspiel von schluessel_ausrichten() und verschluesseln()
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("satz", UEBUNGSSAETZE_LEVEL3)
@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_schluesselzeile_erklaert_den_geheimtext(satz, schluesselwort):
    """Handbuch-Formel Zeichen für Zeichen nachgerechnet.

    Für jede Stelle muss gelten: Geheimbuchstabe = (Klartext + Schlüssel) % 26.
    Damit ist die angezeigte Tabelle "Nachricht / Schlüssel" garantiert
    dieselbe Rechnung wie der ausgegebene Geheimtext – sonst würden die
    Schülerinnen und Schüler von Hand etwas anderes herausbekommen als das
    Programm.
    """
    klartext = normalisieren(satz)
    schluesselzeile = schluessel_ausrichten(satz, schluesselwort)
    geheimtext = verschluesseln(satz, schluesselwort)

    assert len(schluesselzeile) == len(klartext) == len(geheimtext)

    for klar_zeichen, schluessel_zeichen, geheim_zeichen in zip(
        klartext, schluesselzeile, geheimtext
    ):
        if klar_zeichen == LEERZEICHEN:
            assert schluessel_zeichen == LEERZEICHEN
            assert geheim_zeichen == LEERZEICHEN
            continue
        erwartet = ALPHABET[
            (buchstabe_zu_index(klar_zeichen) + buchstabe_zu_index(schluessel_zeichen)) % 26
        ]
        assert geheim_zeichen == erwartet


def test_schluesselzeile_enthaelt_nur_buchstaben_des_schluesselworts():
    """In der Schlüsselzeile dürfen nur Zeichen des Schlüsselworts vorkommen."""
    zeile = schluessel_ausrichten("HILFE WIRD GEBRAUCHT", "WEG")
    assert set(zeile) <= set("WEG" + LEERZEICHEN)


def test_schluesselzeile_wiederholt_das_schluesselwort_lueckenlos():
    """Ohne Leerzeichen gelesen ist die Zeile das mehrfach wiederholte Wort."""
    zeile = ohne_leerzeichen(schluessel_ausrichten("ICH BIN IN SICHERHEIT", "ROT"))
    assert zeile == ("ROT" * 6)[: len(zeile)]


# ───────────────────────────────────────────────────────────────────────────
# 6. Randfälle beim Text
# ───────────────────────────────────────────────────────────────────────────


def test_leerer_text_ergibt_leeren_text():
    """Ein leerer Text ist kein Fehler, sondern liefert einen leeren Text."""
    assert verschluesseln("", "ROT") == ""
    assert entschluesseln("", "ROT") == ""
    assert schluessel_ausrichten("", "ROT") == ""


def test_text_nur_aus_leerzeichen_wird_zu_leerem_text():
    """Reine Leerzeichen fallen beim Normalisieren weg (Regel 6 bzw. trim)."""
    assert verschluesseln("     ", "ROT") == ""
    assert entschluesseln("\t\n  ", "ROT") == ""
    assert schluessel_ausrichten("   ", "ROT") == ""


def test_text_ganz_ohne_buchstaben_wird_zu_leerem_text():
    """Nur Satzzeichen und Ziffern: nach Regel 6 bleibt nichts übrig."""
    assert verschluesseln("123 !?-,.", "ROT") == ""
    assert schluessel_ausrichten("123 !?-,.", "ROT") == ""


def test_einzelner_buchstabe():
    """Kürzestmöglicher Fall: A + R = R (Zeile R, Spalte A im Quadrat)."""
    assert verschluesseln("A", "ROT") == "R"
    assert entschluesseln("R", "ROT") == "A"
    assert schluessel_ausrichten("A", "ROT") == "R"


def test_kleinschreibung_wird_still_normalisiert():
    """Regel 1: Kleinschreibung ist erlaubt und nie ein Fehler."""
    assert verschluesseln("hund", "ROT") == "YIGU"
    assert verschluesseln("HuNd", "ROT") == "YIGU"
    assert entschluesseln("yigu", "ROT") == "HUND"


def test_umlaute_und_satzzeichen_im_text():
    """Der erste Funkspruch des Spiels, von Hand durchgerechnet.

    "Hallo, hört mich jemand?" wird nach den Regeln 5 und 6 zuerst zu
    "HALLO HOERT MICH JEMAND" (20 Buchstaben). Mit ROT ergibt das::

        H A L L O   H O E R T   M I C H   J E M A N D
        R O T R O   T R O T R   O T R O   T R O T R O
        Y O E C C   A F S K K   A B T V   C V A T E R
    """
    assert normalisieren("Hallo, hört mich jemand?") == "HALLO HOERT MICH JEMAND"
    assert verschluesseln("Hallo, hört mich jemand?", "ROT") == "YOECC AFSKK ABTV CVATER"
    assert entschluesseln("YOECC AFSKK ABTV CVATER", "ROT") == "HALLO HOERT MICH JEMAND"


def test_scharfes_s_wird_zu_ss():
    """Regel 5 auch für ß: "Größe" wird zu GROESSE (7 Buchstaben)."""
    assert normalisieren("Größe") == "GROESSE"
    assert verschluesseln("Größe", "A") == "GROESSE"


def test_mehrfache_leerzeichen_werden_zusammengefasst():
    """Doppelte Leerzeichen und Ränder verschwinden schon beim Normalisieren."""
    assert verschluesseln("  ALLES   OK  ", "ROT") == "RZEVG HB"
    assert schluessel_ausrichten("  ALLES   OK  ", "ROT") == "ROTRO TR"


def test_satzzeichen_verschieben_den_schluessel_nicht():
    """Entfernte Satzzeichen dürfen den Schlüsselindex nicht weiterzählen."""
    assert verschluesseln("ALLES, OK!", "ROT") == "RZEVG HB"


# ───────────────────────────────────────────────────────────────────────────
# 7. Randfälle beim Schlüsselwort
# ───────────────────────────────────────────────────────────────────────────


def test_schluesselwort_wird_normalisiert():
    """Klein geschrieben, mit Satzzeichen – das Ergebnis bleibt dasselbe."""
    assert verschluesseln("HUND", "rot") == "YIGU"
    assert verschluesseln("HUND", "Rot!") == "YIGU"
    assert verschluesseln("HUND", "  ROT  ") == "YIGU"


def test_schluesselwort_mit_umlaut_wird_ersetzt():
    """Regel 5 gilt auch für das Schlüsselwort: "RÖT" wird zu ROET.

    Damit sind es vier Schlüsselbuchstaben, nicht drei::

        H U N D
        R O E T
        Y I R W
    """
    assert verschluesseln("HUND", "RÖT") == "YIRW"
    assert schluessel_ausrichten("HUND", "RÖT") == "ROET"


def test_schluesselwort_a_veraendert_nichts():
    """A steht für die Verschiebung 0 – der Text bleibt, wie er ist."""
    text = "ZEIT WIRD KNAPP"
    assert verschluesseln(text, "A") == text
    assert entschluesseln(text, "A") == text
    assert verschluesseln(text, "AAAA") == text


def test_einbuchstabiges_schluesselwort_wirkt_wie_caesar():
    """Mit einem einzigen Schlüsselbuchstaben ist Vigenère genau Caesar.

    B verschiebt um 1, also auch Z -> A (Alphabetumbruch aus Lernziel 1).
    """
    assert verschluesseln("HUND", "B") == "IVOE"
    assert verschluesseln("Z", "B") == "A"
    assert verschluesseln("XYZ", "B") == "YZA"


def test_alphabetumbruch_beim_entschluesseln():
    """Rückwärts über den Rand: A - 1 ergibt Z."""
    assert entschluesseln("A", "B") == "Z"
    assert entschluesseln("ABC", "B") == "ZAB"


def test_wiederholtes_schluesselwort_aendert_nichts():
    """"ROT" und "ROTROT" beschreiben dieselbe Schlüsselfolge."""
    for satz in UEBUNGSSAETZE_LEVEL3:
        assert verschluesseln(satz, "ROT") == verschluesseln(satz, "ROTROT")


def test_schluesselwort_laenger_als_der_text():
    """Ist der Schlüssel länger als der Text, wird nur sein Anfang benutzt.

    H(7)+R(17)=24 -> Y, I(8)+O(14)=22 -> W.
    """
    assert verschluesseln("HI", "ROTATION") == "YW"
    assert schluessel_ausrichten("HI", "ROTATION") == "RO"


def test_schluesselwort_aus_dem_ganzen_alphabet():
    """Ein 26 Zeichen langes Schlüsselwort läuft genau einmal durch."""
    text = "STANDORT UNBEKANNT"
    assert entschluesseln(verschluesseln(text, ALPHABET), ALPHABET) == text


# ───────────────────────────────────────────────────────────────────────────
# 8. Fehlerfälle
# ───────────────────────────────────────────────────────────────────────────

UNBRAUCHBARE_SCHLUESSELWOERTER = (
    "",              # gar nichts
    "   ",           # nur Leerzeichen
    "123",           # nur Ziffern
    "!?-,.",         # nur Satzzeichen
    "RO T",          # zwei Wörter
    "ROT WEG",       # zwei Wörter
    " ROT TAG ",     # zwei Wörter mit Rändern
)


@pytest.mark.parametrize("schluesselwort", UNBRAUCHBARE_SCHLUESSELWOERTER)
@pytest.mark.parametrize(
    "funktion", (verschluesseln, entschluesseln, schluessel_ausrichten)
)
def test_unbrauchbares_schluesselwort_wirft_valueerror(funktion, schluesselwort):
    """Alle drei öffentlichen Funktionen prüfen das Schlüsselwort gleich streng."""
    with pytest.raises(ValueError):
        funktion("HUND", schluesselwort)


def test_fehlermeldung_bei_leerem_schluesselwort_ist_deutsch_und_erklaert_das_problem():
    """Die Meldung muss auf Deutsch sagen, was fehlt – nicht nur "invalid"."""
    with pytest.raises(ValueError) as fehler:
        verschluesseln("HUND", "")
    meldung = str(fehler.value)
    assert "Schlüsselwort" in meldung
    assert "Buchstaben" in meldung


def test_fehlermeldung_bei_leerzeichen_im_schluesselwort_nennt_das_leerzeichen():
    """Bei "RO T" muss die Meldung das Leerzeichen als Ursache benennen."""
    with pytest.raises(ValueError) as fehler:
        verschluesseln("HUND", "RO T")
    meldung = str(fehler.value)
    assert "Schlüsselwort" in meldung
    assert "Leerzeichen" in meldung


def test_leeres_schluesselwort_wird_auch_bei_leerem_text_bemerkt():
    """Der Schlüssel wird geprüft, bevor der (leere) Text abgearbeitet wird."""
    with pytest.raises(ValueError):
        verschluesseln("", "")


@pytest.mark.parametrize("schluesselwort", (None, 3, ["R", "O", "T"]))
def test_schluesselwort_ohne_text_typ_wirft_typeerror(schluesselwort):
    """Ein Schlüsselwort, das kein str ist, ist ein Typfehler.

    Das entspricht der Zusage von :func:`crypto.normalize.normalisieren`,
    die bei Nicht-Texten ebenfalls ``TypeError`` meldet.
    """
    with pytest.raises(TypeError):
        verschluesseln("HUND", schluesselwort)


@pytest.mark.parametrize("text", (None, 42, ["H", "U"]))
def test_text_ohne_text_typ_wirft_typeerror(text):
    """Auch der Text selbst muss ein str sein."""
    with pytest.raises(TypeError):
        verschluesseln(text, "ROT")


# ───────────────────────────────────────────────────────────────────────────
# 9. Lernziel-Eigenschaften und Modulhygiene
# ───────────────────────────────────────────────────────────────────────────


def test_gleiche_buchstaben_werden_verschieden_verschluesselt():
    """Kernaussage des Handbuchs: Vigenère verwischt das Häufigkeitsmuster.

    Zwei benachbarte N werden zu zwei verschiedenen Buchstaben::

        N(13)+R(17)=30%26=4 -> E,  N(13)+O(14)=27%26=1 -> B
    """
    assert verschluesseln("NN", "ROT") == "EB"
    geheim = verschluesseln("AAAAAA", "ROT")
    assert geheim == "ROTROT"
    assert len(set(geheim)) == 3


def test_verschiedene_schluesselwoerter_liefern_verschiedene_geheimtexte():
    """Sonst wäre die Zufallsauswahl ROT/WEG/TAG wirkungslos."""
    text = "WARTE AUF RETTUNG"
    ergebnisse = {verschluesseln(text, wort) for wort in SCHLUESSELWOERTER}
    assert len(ergebnisse) == len(SCHLUESSELWOERTER)


def test_funktionen_sind_rein_und_ohne_zustand():
    """Mehrfacher Aufruf mit denselben Argumenten liefert dasselbe Ergebnis."""
    ergebnisse = {verschluesseln("ALLES OK", "ROT") for _ in range(5)}
    assert ergebnisse == {"RZEVG HB"}


def test_modul_enthaelt_keinen_gui_code():
    """Projektregel: crypto/ importiert weder tkinter noch ui/ oder game/."""
    quelltext = Path(vigenere_modul.__file__).read_text(encoding="utf-8")
    verbotener_import = re.search(
        r"^\s*(?:import|from)\s+(tkinter|ui|game)\b", quelltext, re.MULTILINE
    )
    assert verbotener_import is None
    assert "print(" not in quelltext
    assert "input(" not in quelltext
