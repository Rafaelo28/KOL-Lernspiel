"""Tests für content/uebungen.py (Arbeitsplan 2.2).

Der wichtigste Test steht am Ende: Die Texte im Code müssen wörtlich mit
``dokumentation/Handbuchtexte.md`` übereinstimmen. Das Handbuch ist das, was
die Spielenden lesen – steht dort ein anderes Wort als im Pool, üben sie etwas
anderes, als das Spiel abfragt.

Die übrigen Tests halten die Eigenschaften fest, auf die sich der
Aufgaben-Generator in Phase 3 verlassen darf.
"""

import re
from pathlib import Path

import pytest

from content import uebungen
from crypto import caesar, substitution, vigenere
from crypto.normalize import ALPHABET, LEERZEICHEN, normalisieren

POOLS = (
    ("Level 1 (Caesar)", 1, uebungen.UEBUNGSWOERTER_LEVEL_1),
    ("Level 2 (Substitution)", 2, uebungen.UEBUNGSSAETZE_LEVEL_2),
    ("Level 3 (Vigenère)", 3, uebungen.UEBUNGSSAETZE_LEVEL_3),
)
POOL_IDS = [name for name, _, _ in POOLS]

HANDBUCH = Path(__file__).resolve().parent.parent / "dokumentation" / "Handbuchtexte.md"


def _uebungslisten_aus_dem_handbuch():
    """Liest die drei nummerierten Übungslisten aus der Handbuch-Datei."""
    listen = []
    aktuelle = None
    for zeile in HANDBUCH.read_text(encoding="utf-8").splitlines():
        if zeile.startswith("### Übungs"):
            aktuelle = []
            listen.append(aktuelle)
            continue
        if aktuelle is None:
            continue
        eintrag = re.match(r"\s*\d+\.\s+(\S.*?)\s*$", zeile)
        if eintrag:
            aktuelle.append(eintrag.group(1))
        elif zeile.startswith("#") or zeile.startswith("---"):
            aktuelle = None
    return listen


# ───────────────────────────────────────────────────────────────────────────
# 1. Aufbau der Pools
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name, level, pool", POOLS, ids=POOL_IDS)
def test_jeder_pool_hat_zehn_texte(name, level, pool):
    """Das Handbuch verspricht "10 Stück – eins wird zufällig ausgewählt"."""
    assert len(pool) == 10, f"{name} hat {len(pool)} statt 10 Texte."


@pytest.mark.parametrize("name, level, pool", POOLS, ids=POOL_IDS)
def test_kein_text_kommt_doppelt_vor(name, level, pool):
    """Doppelte Einträge würden die Zufallsauswahl unmerklich verzerren."""
    assert len(set(pool)) == len(pool), (
        f"{name} enthält Dubletten: "
        f"{[t for t in pool if list(pool).count(t) > 1]}"
    )


@pytest.mark.parametrize("name, level, pool", POOLS, ids=POOL_IDS)
def test_die_texte_sind_schon_normalisiert(name, level, pool):
    """Sonst weicht der angezeigte Aufgabentext von der Lösung ab.

    Die Textkonvention entfernt Satzzeichen und ersetzt Umlaute. Stünde hier
    ein Text, der beim Normalisieren seine Form ändert, würde die UI etwas
    anderes anzeigen, als sie prüft (siehe Regel 6 in crypto/normalize.py).
    """
    for text in pool:
        assert normalisieren(text) == text, (
            f"{name}: {text!r} wird beim Normalisieren zu "
            f"{normalisieren(text)!r} – so darf er nicht im Pool stehen."
        )


@pytest.mark.parametrize("name, level, pool", POOLS, ids=POOL_IDS)
def test_die_texte_bestehen_nur_aus_erlaubten_zeichen(name, level, pool):
    """Nur A–Z und einfache Leerzeichen (Textkonvention Regel 2 und 3)."""
    for text in pool:
        assert text.strip() == text, f"{name}: {text!r} hat Leerzeichen am Rand."
        assert "  " not in text, f"{name}: {text!r} hat doppelte Leerzeichen."
        assert set(text) <= set(ALPHABET) | {LEERZEICHEN}, (
            f"{name}: {text!r} enthält unerlaubte Zeichen."
        )


def test_level_1_sind_einzelne_woerter_ohne_leerzeichen():
    """Handbuchseite 1 spricht von Übungs*wörtern*, nicht von Sätzen."""
    for wort in uebungen.UEBUNGSWOERTER_LEVEL_1:
        assert LEERZEICHEN not in wort, f"{wort!r} ist kein einzelnes Wort."


@pytest.mark.parametrize(
    "pool, name",
    [
        (uebungen.UEBUNGSSAETZE_LEVEL_2, "Level 2"),
        (uebungen.UEBUNGSSAETZE_LEVEL_3, "Level 3"),
    ],
)
def test_level_2_und_3_sind_mehrwortige_saetze(pool, name):
    """Erst mit Wortgrenzen wird Regel 3 und 7 im Spiel überhaupt sichtbar."""
    for satz in pool:
        assert LEERZEICHEN in satz, f"{name}: {satz!r} ist kein Satz."


def test_die_saetze_werden_von_level_zu_level_laenger():
    """Der Lernaufbau verlangt steigende Textlänge über die Level hinweg."""
    laenge = {
        level: sum(len(t) for t in pool) / len(pool)
        for _, level, pool in POOLS
    }
    assert laenge[1] < laenge[2] < laenge[3], (
        f"Durchschnittliche Textlängen: {laenge}"
    )


# ───────────────────────────────────────────────────────────────────────────
# 2. Die Sichten für den Generator
# ───────────────────────────────────────────────────────────────────────────

def test_die_nachschlagetabelle_passt_zu_den_pools():
    assert set(uebungen.UEBUNGSTEXTE_NACH_LEVEL) == {1, 2, 3}
    for _, level, pool in POOLS:
        assert uebungen.UEBUNGSTEXTE_NACH_LEVEL[level] is pool


def test_alle_uebungstexte_enthaelt_genau_die_drei_pools():
    assert len(uebungen.ALLE_UEBUNGSTEXTE) == 30
    assert uebungen.ALLE_UEBUNGSTEXTE == (
        uebungen.UEBUNGSWOERTER_LEVEL_1
        + uebungen.UEBUNGSSAETZE_LEVEL_2
        + uebungen.UEBUNGSSAETZE_LEVEL_3
    )


def test_kein_text_kommt_in_zwei_leveln_vor():
    """Sonst würde ein Wort aus Level 1 in Level 3 wieder auftauchen."""
    assert len(set(uebungen.ALLE_UEBUNGSTEXTE)) == 30


# ───────────────────────────────────────────────────────────────────────────
# 3. Die Vigenère-Schlüsselwörter
# ───────────────────────────────────────────────────────────────────────────

def test_es_gibt_mehrere_schluesselwoerter_zur_auswahl():
    """Ein einziges Schlüsselwort macht die Aufgabe vorhersehbar."""
    woerter = uebungen.VIGENERE_SCHLUESSELWOERTER
    assert len(woerter) >= 2
    assert len(set(woerter)) == len(woerter), "Dubletten in der Auswahl."


def test_das_handbuch_beispiel_rot_ist_dabei():
    """Handbuchseite 3 rechnet HUND + ROT durch – das Wort muss vorkommen."""
    assert "ROT" in uebungen.VIGENERE_SCHLUESSELWOERTER


@pytest.mark.parametrize("wort", uebungen.VIGENERE_SCHLUESSELWOERTER)
def test_jedes_schluesselwort_ist_fuer_vigenere_brauchbar(wort):
    """crypto/vigenere.py weist leere und mehrteilige Schlüsselwörter ab."""
    assert normalisieren(wort) == wort
    assert LEERZEICHEN not in wort
    assert 1 <= len(wort) <= 8, "Zu lang, um es von Hand im Quadrat zu verfolgen."
    # Muss sich tatsächlich benutzen lassen, nicht nur gültig aussehen.
    geheim = vigenere.verschluesseln("HUND", wort)
    assert vigenere.entschluesseln(geheim, wort) == "HUND"


def test_kein_schluesselwort_laesst_den_text_unveraendert():
    """Ein Schlüsselwort aus lauter A würde gar nichts verschlüsseln."""
    for wort in uebungen.VIGENERE_SCHLUESSELWOERTER:
        beispiel = uebungen.UEBUNGSSAETZE_LEVEL_3[0]
        assert vigenere.verschluesseln(beispiel, wort) != beispiel, (
            f"Mit dem Schlüsselwort {wort!r} bleibt der Text unverändert."
        )


# ───────────────────────────────────────────────────────────────────────────
# 4. Alle Texte lassen sich in allen drei Verfahren benutzen
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", uebungen.ALLE_UEBUNGSTEXTE)
def test_jeder_text_laeuft_durch_alle_drei_verfahren_und_zurueck(text):
    """Kein Pooltext darf in irgendeinem Level am Rundlauf scheitern."""
    assert caesar.entschluesseln(caesar.verschluesseln(text, 3), 3) == text
    assert substitution.entschluesseln(substitution.verschluesseln(text)) == text
    for wort in uebungen.VIGENERE_SCHLUESSELWOERTER:
        assert vigenere.entschluesseln(vigenere.verschluesseln(text, wort), wort) == text


# ───────────────────────────────────────────────────────────────────────────
# 5. Der Abgleich mit der Quelle
# ───────────────────────────────────────────────────────────────────────────

def test_das_handbuch_enthaelt_drei_uebungslisten_mit_je_zehn_eintraegen():
    """Schutz davor, dass der folgende Vergleich durch leere Listen grün wird."""
    listen = _uebungslisten_aus_dem_handbuch()
    assert len(listen) == 3, f"Erwartet 3 Übungslisten, gefunden {len(listen)}."
    for nummer, liste in enumerate(listen, start=1):
        assert len(liste) == 10, (
            f"Übungsliste {nummer} hat {len(liste)} statt 10 Einträge."
        )


@pytest.mark.parametrize("name, level, pool", POOLS, ids=POOL_IDS)
def test_die_pools_stimmen_woertlich_mit_dem_handbuch_ueberein(name, level, pool):
    """Was der Code übt, muss wörtlich im Handbuch stehen – und umgekehrt."""
    im_handbuch = _uebungslisten_aus_dem_handbuch()[level - 1]
    assert list(pool) == im_handbuch, (
        f"{name}: content/uebungen.py und dokumentation/Handbuchtexte.md "
        f"laufen auseinander.\n"
        f"  nur im Code:     {sorted(set(pool) - set(im_handbuch))}\n"
        f"  nur im Handbuch: {sorted(set(im_handbuch) - set(pool))}"
    )


# ───────────────────────────────────────────────────────────────────────────
# 6. Die Caesar-Schlüssel
# ───────────────────────────────────────────────────────────────────────────

def test_es_gibt_mehrere_caesar_schluessel_zur_auswahl():
    """Ein fester Schlüssel macht die Übungsaufgabe vorhersehbar."""
    assert len(uebungen.CAESAR_SCHLUESSEL) >= 5
    assert len(set(uebungen.CAESAR_SCHLUESSEL)) == len(uebungen.CAESAR_SCHLUESSEL)


@pytest.mark.parametrize("schluessel", uebungen.CAESAR_SCHLUESSEL)
def test_jeder_caesar_schluessel_veraendert_den_text(schluessel):
    """0 und 26 verschieben nichts – als Aufgabe wären sie sinnlos."""
    beispiel = uebungen.UEBUNGSWOERTER_LEVEL_1[0]
    assert caesar.verschluesseln(beispiel, schluessel) != beispiel, (
        f"Schlüssel {schluessel} lässt den Text unverändert."
    )


@pytest.mark.parametrize("schluessel", uebungen.CAESAR_SCHLUESSEL)
def test_ver_und_entschluesseln_sind_bei_jedem_schluessel_unterscheidbar(schluessel):
    """Bei Schlüssel 13 liefern beide Richtungen dasselbe Ergebnis.

    Level 1 soll aber genau den Unterschied vermitteln – "vorwärts" gegen
    "rückwärts" springen, siehe Merksatz auf Handbuchseite 1. Ein Schlüssel,
    bei dem beide Richtungen gleich aussehen, verwischt ihn.
    """
    beispiel = uebungen.UEBUNGSWOERTER_LEVEL_1[0]
    assert caesar.verschluesseln(beispiel, schluessel) != caesar.entschluesseln(
        beispiel, schluessel
    ), f"Schlüssel {schluessel} macht Ver- und Entschlüsseln ununterscheidbar."


@pytest.mark.parametrize("schluessel", uebungen.CAESAR_SCHLUESSEL)
def test_jeder_caesar_schluessel_liegt_im_handbuch_bereich(schluessel):
    """Handbuchseite 2 spricht von "nur 25 möglichen Schlüsseln"."""
    assert isinstance(schluessel, int) and not isinstance(schluessel, bool)
    assert 1 <= schluessel <= 25


def test_der_handbuch_schluessel_ist_der_aus_dem_durchgerechneten_beispiel():
    """Handbuchseite 1 rechnet HUND mit Schlüssel 3 zu KXQG durch."""
    assert caesar.verschluesseln("HUND", uebungen.CAESAR_SCHLUESSEL_HANDBUCH) == "KXQG"
    assert uebungen.CAESAR_SCHLUESSEL_HANDBUCH in uebungen.CAESAR_SCHLUESSEL
