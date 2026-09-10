"""Tests für content/charaktere.py (Arbeitsplan 2.4).

Der Schwerpunkt liegt auf den Initialen: Sie unterschreiben jede gesendete
Funkmeldung, werden also mitverschlüsselt und müssen der Textkonvention
genügen. Und sie müssen eindeutig sein – sonst lässt sich später weder im
Spiel noch in den Messdaten sagen, wer gefunkt hat.
"""

from pathlib import Path

import pytest

from content import charaktere, story
from content.charaktere import BOB, SPIELBARE_CHARAKTERE
from crypto import caesar, substitution, vigenere
from crypto.normalize import ALPHABET, LEERZEICHEN, normalisieren

FIGUR_IDS = [figur.kennung for figur in SPIELBARE_CHARAKTERE]
KONZEPT = Path(__file__).resolve().parent.parent / "dokumentation" / "Konzept_Spiel.md"


# ───────────────────────────────────────────────────────────────────────────
# 1. Die Besetzung
# ───────────────────────────────────────────────────────────────────────────

def test_es_gibt_genau_fuenf_waehlbare_figuren():
    """Konzept: "wählbar zu Beginn aus fünf Crewmitgliedern"."""
    assert len(SPIELBARE_CHARAKTERE) == 5


def test_bob_ist_nicht_waehlbar():
    """Bob ist Gegenüber, nicht Spielfigur."""
    assert BOB not in SPIELBARE_CHARAKTERE
    assert BOB.kennung not in charaktere.CHARAKTER_NACH_KENNUNG


def test_die_nachschlagetabelle_passt_zur_auswahl():
    assert set(charaktere.CHARAKTER_NACH_KENNUNG) == {
        figur.kennung for figur in SPIELBARE_CHARAKTERE
    }
    for kennung, figur in charaktere.CHARAKTER_NACH_KENNUNG.items():
        assert figur.kennung == kennung


@pytest.mark.parametrize("figur", SPIELBARE_CHARAKTERE, ids=FIGUR_IDS)
def test_kein_feld_ist_leer(figur):
    assert figur.kennung.strip()
    assert figur.name.strip()
    assert figur.rolle.strip()
    assert figur.initialen.strip()


def test_namen_kennungen_und_rollen_sind_eindeutig():
    for feld in ("name", "kennung", "rolle"):
        werte = [getattr(figur, feld) for figur in SPIELBARE_CHARAKTERE]
        assert len(set(werte)) == len(werte), f"Doppelte Werte im Feld {feld}."


@pytest.mark.parametrize("figur", SPIELBARE_CHARAKTERE, ids=FIGUR_IDS)
def test_die_kennung_ist_maschinenlesbar(figur):
    """Sie landet im Log und in Dateinamen – dort stören Umlaute und Leerzeichen."""
    assert figur.kennung == figur.kennung.lower()
    assert all(zeichen.isalnum() or zeichen == "_" for zeichen in figur.kennung)
    assert figur.kennung.isascii()


# ───────────────────────────────────────────────────────────────────────────
# 2. Die Initialen – sie werden mitverschlüsselt
# ───────────────────────────────────────────────────────────────────────────

def test_keine_zwei_figuren_haben_dieselben_initialen():
    """Sonst ist der Absender einer Funkmeldung nicht mehr eindeutig."""
    initialen = [figur.initialen for figur in SPIELBARE_CHARAKTERE]
    assert len(set(initialen)) == len(initialen), (
        f"Doppelte Initialen: "
        f"{[i for i in initialen if initialen.count(i) > 1]}"
    )


@pytest.mark.parametrize("figur", SPIELBARE_CHARAKTERE, ids=FIGUR_IDS)
def test_die_initialen_genuegen_der_textkonvention(figur):
    """Sie werden mitverschlüsselt, dürfen also nur A–Z enthalten."""
    assert set(figur.initialen) <= set(ALPHABET), (
        f"{figur.name}: {figur.initialen!r} enthält Zeichen ausserhalb von A–Z."
    )
    assert normalisieren(figur.initialen) == figur.initialen


@pytest.mark.parametrize("figur", SPIELBARE_CHARAKTERE, ids=FIGUR_IDS)
def test_die_initialen_folgen_wirklich_aus_dem_namen(figur):
    """Schutz vor Tippfehlern – und ein Test für den Umlaut-Fall.

    "Théo Lambert" wird nach der Textkonvention zu "THEO LAMBERT", die
    Initialen lauten also "TL". Vor der Unicode-Korrektur in
    crypto/normalize.py wäre daraus "THO LAMBERT" geworden – die Initialen
    hätten trotzdem gestimmt, aber der angezeigte Name nicht.
    """
    abgeleitet = "".join(wort[0] for wort in normalisieren(figur.name).split())
    assert figur.initialen == abgeleitet, (
        f"{figur.name}: Initialen {figur.initialen!r}, aus dem Namen folgt "
        f"{abgeleitet!r} (normalisiert: {normalisieren(figur.name)!r})."
    )


def test_theo_lambert_behaelt_seinen_grundbuchstaben():
    """Der Akzent darf den Buchstaben nicht verschlucken."""
    assert normalisieren(charaktere.THEO_LAMBERT.name) == "THEO LAMBERT"


@pytest.mark.parametrize("figur", SPIELBARE_CHARAKTERE, ids=FIGUR_IDS)
def test_der_name_ueberlebt_die_normalisierung_als_ganzes(figur):
    """Kein Buchstabe darf ersatzlos verschwinden.

    Geprüft wird die Wortzahl, nicht die Zeichenzahl – "Théo" wird zu "THEO"
    (gleich lang), aus einem "ß" würde "SS" (länger). Verschwände ein ganzes
    Wort, wäre der Name im Spiel entstellt.
    """
    assert len(normalisieren(figur.name).split()) == len(figur.name.split())
    assert set(normalisieren(figur.name)) <= set(ALPHABET) | {LEERZEICHEN}


# ───────────────────────────────────────────────────────────────────────────
# 3. Zusammenspiel mit den Funksprüchen
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("figur", SPIELBARE_CHARAKTERE, ids=FIGUR_IDS)
def test_jede_figur_kann_jeden_funkspruch_unterschreiben(figur):
    """Der Platzhalter aus content/story.py muss mit jeder Figur aufgehen."""
    for funkspruch in story.FUNKSPRUECHE:
        fertig = funkspruch.klartext.format(initialen=figur.initialen)
        assert "{" not in fertig and "}" not in fertig
        assert normalisieren(fertig) == fertig, (
            f"{figur.name} in {funkspruch.kennung}: {fertig!r} ist nicht "
            "normalisiert."
        )
        if funkspruch.richtung == story.SENDEN:
            assert fertig.endswith(figur.initialen)


VERFAHREN = {
    story.CAESAR: (lambda t: caesar.verschluesseln(t, 3), lambda t: caesar.entschluesseln(t, 3)),
    story.SUBSTITUTION: (substitution.verschluesseln, substitution.entschluesseln),
    story.VIGENERE: (
        lambda t: vigenere.verschluesseln(t, "ROT"),
        lambda t: vigenere.entschluesseln(t, "ROT"),
    ),
}


@pytest.mark.parametrize("figur", SPIELBARE_CHARAKTERE, ids=FIGUR_IDS)
def test_die_unterschrift_uebersteht_das_verschluesseln(figur):
    """Rundlauf mit echter Unterschrift – das ist der Ernstfall im Spiel."""
    for funkspruch in story.FUNKSPRUECHE:
        fertig = funkspruch.klartext.format(initialen=figur.initialen)
        hin, zurueck = VERFAHREN[funkspruch.verfahren]
        assert zurueck(hin(fertig)) == fertig


@pytest.mark.parametrize("figur", SPIELBARE_CHARAKTERE, ids=FIGUR_IDS)
def test_die_unterschrift_liegt_nie_in_der_teilaufgabe(figur):
    """Der selbst zu lösende Anfang darf nicht von der Figurwahl abhängen.

    Sonst wäre die Aufgabe für die eine Figur länger als für die andere – und
    die Bearbeitungszeiten liessen sich nicht mehr vergleichen.
    """
    for funkspruch in story.FUNKSPRUECHE:
        if not funkspruch.selbst_zu_loesen:
            continue
        assert figur.initialen not in funkspruch.selbst_zu_loesen.split()


def test_die_teilaufgaben_sind_fuer_alle_figuren_gleich_lang():
    """Dieselbe Arbeitsmenge für alle – Voraussetzung für die Auswertung."""
    for funkspruch in story.FUNKSPRUECHE:
        laengen = {
            len(
                (funkspruch.selbst_zu_loesen or
                 funkspruch.klartext.format(initialen=figur.initialen))
                .replace(LEERZEICHEN, "")
            )
            for figur in SPIELBARE_CHARAKTERE
        }
        assert len(laengen) == 1, (
            f"{funkspruch.kennung}: unterschiedlich lange Teilaufgaben je "
            f"nach Figur ({sorted(laengen)})."
        )


# ───────────────────────────────────────────────────────────────────────────
# 4. Abgleich mit dem Konzept
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("figur", SPIELBARE_CHARAKTERE, ids=FIGUR_IDS)
def test_name_und_rolle_stehen_so_im_konzept(figur):
    """Quelle ist dokumentation/Konzept_Spiel.md."""
    quelle = KONZEPT.read_text(encoding="utf-8")
    assert f"{figur.name} – {figur.rolle}" in quelle, (
        f'"{figur.name} – {figur.rolle}" steht so nicht im Konzept.'
    )


def test_das_konzept_nennt_genau_diese_fuenf():
    """Schutz davor, dass jemand eine Figur ergänzt, ohne die Quelle zu pflegen."""
    quelle = KONZEPT.read_text(encoding="utf-8")
    zeilen = [
        zeile.strip("- ").strip()
        for zeile in quelle.splitlines()
        if zeile.startswith("- ") and " – " in zeile
    ]
    im_konzept = {
        zeile.split(" – ")[0]
        for zeile in zeilen
        if zeile.split(" – ")[0] in {f.name for f in SPIELBARE_CHARAKTERE}
    }
    assert im_konzept == {figur.name for figur in SPIELBARE_CHARAKTERE}
