"""Tests für game/spieler_id.py – die ID der Lehrkraft in der Form X-XX.

Die Lehrkraft verteilt IDs wie ``1-12`` (Klasse 1, zwölftes Kind). Das Spiel
nimmt nur genau diese Form an – einen Namen soll man gar nicht erst
eintragen können (Projektregel 7).
"""

import pytest

from game import spieler_id
from game.protokoll import pseudonym_fuer_tabelle

GUELTIG = ["1-12", "0-00", "9-99", "7-05", "3-40"]

UNGUELTIG = [
    "", "1", "1-", "1-1", "1-123", "12-12", "112", "-12", "1_12", "1 12", " 1-12", "1-12 ",
    "1–12",                  # Gedankenstrich statt Bindestrich
    "A-12", "1-1a", "Max", "max-12", "Moritz 1-12",
    "١-١٢",                  # arabisch-indische Ziffern: \d fände sie gut, die Lehrkraft nicht
]


@pytest.mark.parametrize("text", GUELTIG)
def test_gueltige_ids(text):
    assert spieler_id.ist_gueltig(text)
    assert spieler_id.fehler(text) == ""


@pytest.mark.parametrize("text", UNGUELTIG)
def test_alles_andere_ist_keine_id(text):
    assert not spieler_id.ist_gueltig(text)
    assert spieler_id.fehler(text), f"Für {text!r} fehlt eine Meldung."


def test_das_beispiel_ist_selbst_eine_gueltige_id():
    assert spieler_id.ist_gueltig(spieler_id.BEISPIEL)


# ── Beim Tippen ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", ["", "1", "1-", "1-1", "1-12"])
def test_jeder_anfang_einer_id_darf_ins_feld(text):
    assert spieler_id.ist_anfang(text)


@pytest.mark.parametrize("text", ["a", "M", "-", " ", "11", "1a", "1 ", "1--", "1-a", "1-123", "12-", "Max"])
def test_was_keine_id_mehr_werden_kann_kommt_nicht_ins_feld(text):
    assert not spieler_id.ist_anfang(text)


def test_ein_name_laesst_sich_nicht_eintippen():
    """Buchstabe für Buchstabe: Schon der erste wird abgewiesen."""
    for name in ("Max", "Lea", "Moritz", "Ömer", "Zoë"):
        assert not spieler_id.ist_anfang(name[0])


def test_jede_gueltige_id_laesst_sich_zeichenweise_eintippen():
    for text in GUELTIG:
        for ende in range(len(text) + 1):
            assert spieler_id.ist_anfang(text[:ende]), text[:ende]


def test_nach_der_klasse_setzt_das_feld_den_strich_selbst():
    assert spieler_id.strich_fehlt("1", "2")
    assert not spieler_id.strich_fehlt("1", "-")      # der Strich kommt ja gerade
    assert not spieler_id.strich_fehlt("", "1")       # erst die Klasse
    assert not spieler_id.strich_fehlt("1-", "2")     # der Strich ist schon da
    assert not spieler_id.strich_fehlt("1", "a")


# ── Konkrete Meldungen (Projektregel 6: nie nur "falsch") ─────────────────

@pytest.mark.parametrize(
    "text, steht_drin",
    [
        ("", "Trag zuerst deine ID ein"),
        ("1", "fehlen noch der Strich und deine Nummer"),
        ("1-", "Nach dem Strich fehlt noch deine Nummer"),
        ("1-2", "1-02"),                   # sagt, wie es richtig heisst
        ("112", "1-12"),                   # der Strich fehlt – und wohin er gehört
        ("-12", "Vor dem Strich fehlt noch deine Klasse"),
        ("Max", "Klasse, Strich, Nummer"),
    ],
)
def test_die_meldung_sagt_was_fehlt(text, steht_drin):
    assert steht_drin in spieler_id.fehler(text)


# ── Im Log ─────────────────────────────────────────────────────────────────

def test_im_log_macht_excel_aus_der_id_kein_datum():
    """Deutsches Excel läse 1-12 als 1. Dezember – mit "ID " davor bleibt es Text."""
    assert pseudonym_fuer_tabelle("1-12") == "ID 1-12"
    for text in GUELTIG:
        assert not pseudonym_fuer_tabelle(text)[0].isdigit()


def test_andere_pseudonyme_bleiben_wie_sie_sind():
    assert pseudonym_fuer_tabelle("P004711000") == "P004711000"
    assert pseudonym_fuer_tabelle("Gruppe-A-03") == "Gruppe-A-03"
