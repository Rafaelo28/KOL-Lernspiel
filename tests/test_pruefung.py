"""Tests für game/pruefung.py (Arbeitsplan 4.1).

Die Prüf-Funktion entscheidet, ob eine Aufgabe gelöst ist – und damit auch, ob
einer der drei Versuche verbraucht wird. Sie zu streng zu bauen ist genauso
schädlich wie zu lasch: Wer richtig gerechnet und ein Leerzeichen vergessen
hat, würde sonst bestraft, und das Spiel misst am Ende Tippgenauigkeit statt
Verständnis.
"""

import random

import pytest

from content import charaktere, story, uebungen
from crypto.normalize import LEERZEICHEN
from game.aufgabe import ENTSCHLUESSELN, VERSCHLUESSELN, Aufgabe, anwenden
from game.generator import Aufgabengenerator, aufgabe_aus_funkspruch
from game.pruefung import Pruefergebnis, pruefe
from game.zufallsquelle import Zufallsquelle

LEVEL = (1, 2, 3)


def _uebung(anzeigetext="HUND", loesung="KXQG"):
    return Aufgabe("probe", 1, "caesar", VERSCHLUESSELN, 3, anzeigetext, loesung)


def _alle_uebungen(anzahl=60):
    generator = Aufgabengenerator(Zufallsquelle(4711))
    return [
        generator.naechste_uebung(level)
        for level in LEVEL
        for _ in range(anzahl // len(LEVEL))
    ]


FUNKSPRUCH_AUFGABEN = [
    aufgabe_aus_funkspruch(f, "VM") for f in story.FUNKSPRUECHE
]
FUNKSPRUCH_IDS = [f.kennung for f in story.FUNKSPRUECHE]


# ───────────────────────────────────────────────────────────────────────────
# 1. Die richtige Lösung wird angenommen
# ───────────────────────────────────────────────────────────────────────────

def test_die_richtige_loesung_ist_richtig():
    ergebnis = pruefe(_uebung(), "KXQG")
    assert ergebnis.richtig
    assert ergebnis.darf_abgeschickt_werden
    assert not ergebnis.zaehlt_als_versuch


def test_jede_erzeugte_uebung_erkennt_ihre_eigene_loesung():
    for aufgabe in _alle_uebungen():
        assert pruefe(aufgabe, aufgabe.loesung).richtig


@pytest.mark.parametrize("aufgabe", FUNKSPRUCH_AUFGABEN, ids=FUNKSPRUCH_IDS)
def test_jeder_funkspruch_erkennt_seine_eigene_loesung(aufgabe):
    """Regel 4.1 gilt einheitlich für Übungen und echte Funksprüche."""
    assert pruefe(aufgabe, aufgabe.loesung).richtig


# ───────────────────────────────────────────────────────────────────────────
# 2. Toleranz nach Textkonvention Regel 4
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "eingabe, beschreibung",
    [
        ("DOOHV RN", "genau so"),
        ("doohv rn", "klein geschrieben"),
        ("DoOhV rN", "gemischt"),
        ("DOOHVRN", "ohne Leerzeichen"),
        ("DOOHV  RN", "doppeltes Leerzeichen"),
        ("  DOOHV RN  ", "Leerzeichen aussen"),
        ("DOO HVRN", "Leerzeichen verrutscht"),
        ("DOOHV, RN!", "mit Satzzeichen"),
        ("DOOHV\tRN", "Tabulator"),
    ],
)
def test_die_pruefung_ist_tolerant(eingabe, beschreibung):
    """Ein Tippdetail darf keinen der drei Versuche kosten."""
    aufgabe = _uebung("ALLES OK", "DOOHV RN")
    assert pruefe(aufgabe, eingabe).richtig, f"abgelehnt: {beschreibung}"


@pytest.mark.parametrize("eingabe", ["DOOHV RM", "DOOH RN", "DOOHV RNX", "XOOHV RN"])
def test_ein_falscher_buchstabe_bleibt_falsch(eingabe):
    """Toleranz gilt für Schreibweise, nicht für den Inhalt."""
    aufgabe = _uebung("ALLES OK", "DOOHV RN")
    ergebnis = pruefe(aufgabe, eingabe)
    assert not ergebnis.richtig
    assert not ergebnis.darf_abgeschickt_werden
    assert ergebnis.zaehlt_als_versuch


def test_die_eingabe_wird_normalisiert_zurueckgemeldet():
    """Phase 4.2 und die UI arbeiten mit derselben Form, die verglichen wurde."""
    ergebnis = pruefe(_uebung("ALLES OK", "DOOHV RN"), "  doohv,  rn!  ")
    assert ergebnis.eingabe == "DOOHV RN"
    assert ergebnis.erwartet == "DOOHV RN"


# ───────────────────────────────────────────────────────────────────────────
# 3. Die leere Eingabe ist kein Fehlversuch
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("eingabe", ["", "   ", "\t", "???", "123", "!!!", " . , "])
def test_eine_leere_eingabe_zaehlt_nicht_als_versuch(eingabe):
    """Wer nichts eingibt, hat es nicht versucht.

    Auch eine Eingabe, von der nach der Normalisierung nichts übrig bleibt,
    ist keine – "???" ist so gut wie nichts. Zählte sie mit, wären nach drei
    Fehlklicks die drei Versuche verbraucht und die Lösung stünde da.
    """
    ergebnis = pruefe(_uebung(), eingabe)
    assert ergebnis.ist_leer
    assert not ergebnis.richtig
    assert not ergebnis.zaehlt_als_versuch
    assert not ergebnis.darf_abgeschickt_werden


def test_eine_nichtleere_falsche_eingabe_zaehlt_sehr_wohl():
    ergebnis = pruefe(_uebung(), "XXXX")
    assert not ergebnis.ist_leer
    assert ergebnis.zaehlt_als_versuch


# ───────────────────────────────────────────────────────────────────────────
# 4. Teilaufgaben – wer mehr rechnet, wird nicht bestraft
# ───────────────────────────────────────────────────────────────────────────

MIT_TEILAUFGABE = [a for a in FUNKSPRUCH_AUFGABEN if a.hat_teilaufgabe]
OHNE_TEILAUFGABE = [a for a in FUNKSPRUCH_AUFGABEN if not a.hat_teilaufgabe]


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_bei_einer_teilaufgabe_genuegt_der_anfang(aufgabe):
    """Arbeitsplan 4.1: Geprüft wird selbst_zu_loesen, nicht der ganze Text."""
    ergebnis = pruefe(aufgabe, aufgabe.loesung)
    assert ergebnis.richtig
    assert not ergebnis.vollstaendig_geloest


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_wer_die_ganze_nachricht_rechnet_hat_auch_recht(aufgabe):
    """Die Teilaufgabe ist eine Erleichterung, keine Vorschrift.

    Ohne diese Regel bekäme ausgerechnet das fleissigste Kind nach drei
    "Fehlversuchen" die Lösung vorgesetzt.
    """
    ergebnis = pruefe(aufgabe, aufgabe.vollstaendige_loesung)
    assert ergebnis.richtig
    assert ergebnis.vollstaendig_geloest
    assert not ergebnis.zaehlt_als_versuch


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_etwas_dazwischen_ist_trotzdem_falsch(aufgabe):
    """Mehr als die Teilaufgabe, aber nicht alles – das ist keine Lösung."""
    zuviel = aufgabe.loesung + LEERZEICHEN + aufgabe.rest_der_loesung.split()[0]
    if zuviel == aufgabe.vollstaendige_loesung:
        pytest.skip("Der Rest besteht nur aus einem Wort.")
    assert not pruefe(aufgabe, zuviel).richtig


@pytest.mark.parametrize(
    "aufgabe", OHNE_TEILAUFGABE, ids=[a.kennung for a in OHNE_TEILAUFGABE]
)
def test_ohne_teilaufgabe_ist_die_loesung_immer_die_ganze(aufgabe):
    ergebnis = pruefe(aufgabe, aufgabe.loesung)
    assert ergebnis.richtig
    assert ergebnis.vollstaendig_geloest


def test_bei_uebungen_gibt_es_keine_teilaufgabe():
    """Handbuch-Übungen sind kurz genug, um sie ganz zu rechnen."""
    for aufgabe in _alle_uebungen():
        ergebnis = pruefe(aufgabe, aufgabe.loesung)
        assert ergebnis.vollstaendig_geloest


# ───────────────────────────────────────────────────────────────────────────
# 5. Die Prüfung passt zu jeder Figur und jedem Verfahren
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "funkspruch", story.FUNKSPRUECHE, ids=FUNKSPRUCH_IDS
)
@pytest.mark.parametrize(
    "figur",
    charaktere.SPIELBARE_CHARAKTERE,
    ids=[f.kennung for f in charaktere.SPIELBARE_CHARAKTERE],
)
def test_die_pruefung_gilt_fuer_jede_figur(funkspruch, figur):
    aufgabe = aufgabe_aus_funkspruch(funkspruch, figur.initialen)
    assert pruefe(aufgabe, aufgabe.loesung).richtig
    assert not pruefe(aufgabe, aufgabe.anzeigetext).richtig


def test_der_angezeigte_text_ist_nie_die_loesung():
    """Sonst wäre die Aufgabe durch Abschreiben lösbar."""
    for aufgabe in _alle_uebungen() + FUNKSPRUCH_AUFGABEN:
        assert not pruefe(aufgabe, aufgabe.anzeigetext).richtig


def test_die_loesung_der_gegenrichtung_wird_nicht_angenommen():
    """Wer in die falsche Richtung rechnet, hat die Aufgabe nicht gelöst."""
    aufgabe = Aufgabe(
        "probe", 1, "caesar", ENTSCHLUESSELN, 3, "KXQG", "HUND"
    )
    falsch = anwenden("caesar", VERSCHLUESSELN, "KXQG", 3)
    assert not pruefe(aufgabe, falsch).richtig


# ───────────────────────────────────────────────────────────────────────────
# 6. Fehlerarten
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("unsinn", [None, 3, ["KXQG"], b"KXQG", 4.0])
def test_eine_eingabe_vom_falschen_typ_wird_abgewiesen(unsinn):
    """Fehlerart-Konvention: falscher Typ ergibt TypeError.

    Die Meldung muss von der *Eingabe* sprechen. Ohne die eigene Prüfung in
    pruefe() käme der TypeError aus normalisieren() durch, und die Meldung
    ("normalisieren() erwartet einen Text") würde beim Suchen in die falsche
    Richtung zeigen – der Fehler steckt im aufrufenden Code, nicht in der
    Textkonvention.
    """
    with pytest.raises(TypeError) as fehler:
        pruefe(_uebung(), unsinn)
    assert "Eingabe" in str(fehler.value)
    assert type(unsinn).__name__ in str(fehler.value)


def test_das_ergebnis_ist_unveraenderlich():
    """Es wandert durch UI und Log – niemand soll es unterwegs umschreiben."""
    ergebnis = pruefe(_uebung(), "KXQG")
    assert isinstance(ergebnis, Pruefergebnis)
    with pytest.raises(AttributeError):
        ergebnis.richtig = False
