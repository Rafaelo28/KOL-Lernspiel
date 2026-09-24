"""Tests für content/uebungen.py (Arbeitsplan 2.2).

Der wichtigste Test steht am Ende: Die Texte im Code müssen wörtlich mit
``dokumentation/Handbuchtexte.md`` übereinstimmen. Das Handbuch ist das, was
die Spielenden lesen – steht dort ein anderer Satz als im Pool, üben sie etwas
anderes, als das Spiel abfragt.

Die übrigen Tests halten die Eigenschaften fest, auf die sich der
Aufgaben-Generator in Phase 3 verlassen darf – vor allem, dass alle Sätze
ähnlich lang sind: Alle drei Level üben mit demselben Pool.
"""

import re
from pathlib import Path

import pytest

from content import uebungen
from crypto import caesar, substitution, vigenere
from crypto.normalize import ALPHABET, LEERZEICHEN, normalisieren, ohne_leerzeichen

POOL = uebungen.UEBUNGSTEXTE

HANDBUCH = Path(__file__).resolve().parent.parent / "dokumentation" / "Handbuchtexte.md"


def _uebungslisten_aus_dem_handbuch():
    """Liest die nummerierten Übungslisten aus der Handbuch-Datei."""
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
# 1. Aufbau des Pools
# ───────────────────────────────────────────────────────────────────────────

def test_der_pool_hat_vierundfuenfzig_texte():
    """Das Handbuch verspricht "18 Stück – einer wird zufällig ausgewählt".

    Achtzehn je Level: zwei Pflichtübungen und bis zu sechzehn Zusatzaufgaben, alle
    verschieden (siehe game/zusatzaufgaben.py).
    """
    assert len(POOL) == 54, f"Der Pool hat {len(POOL)} statt 54 Texte."


def test_kein_text_kommt_doppelt_vor():
    """Doppelte Einträge würden die Zufallsauswahl unmerklich verzerren."""
    assert len(set(POOL)) == len(POOL), (
        f"Dubletten: {[t for t in POOL if list(POOL).count(t) > 1]}"
    )


def test_die_texte_sind_schon_normalisiert():
    """Sonst weicht der angezeigte Aufgabentext von der Lösung ab.

    Die Textkonvention entfernt Satzzeichen und ersetzt Umlaute. Stünde hier
    ein Text, der beim Normalisieren seine Form ändert, würde die UI etwas
    anderes anzeigen, als sie prüft (siehe Regel 6 in crypto/normalize.py).
    """
    for text in POOL:
        assert normalisieren(text) == text, (
            f"{text!r} wird beim Normalisieren zu {normalisieren(text)!r} – "
            "so darf er nicht im Pool stehen."
        )


def test_die_texte_bestehen_nur_aus_erlaubten_zeichen():
    """Nur A–Z und einfache Leerzeichen (Textkonvention Regel 2 und 3)."""
    for text in POOL:
        assert text.strip() == text, f"{text!r} hat Leerzeichen am Rand."
        assert "  " not in text, f"{text!r} hat doppelte Leerzeichen."
        assert set(text) <= set(ALPHABET) | {LEERZEICHEN}, f"{text!r} enthält unerlaubte Zeichen."


def test_alle_texte_sind_mehrwortige_saetze():
    """Erst mit Wortgrenzen werden Regel 3 und 7 im Spiel überhaupt sichtbar."""
    for satz in POOL:
        assert LEERZEICHEN in satz, f"{satz!r} ist kein Satz."


def test_die_saetze_sind_aehnlich_lang():
    """Alle Level üben mit demselben Pool – schwerer werden sie durch das Verfahren, nicht durch die Länge.

    Der längste Satz ist höchstens anderthalbmal so lang wie der kürzeste.
    Sonst hinge die Bearbeitungszeit einer Übung wieder stark davon ab,
    welchen Satz jemand gezogen hat.
    """
    laengen = [len(ohne_leerzeichen(text)) for text in POOL]
    assert max(laengen) <= 1.5 * min(laengen), sorted(laengen)


def test_die_alten_levellisten_gibt_es_nicht_mehr():
    """Ein vergessener Rest würde still weiter benutzt – etwa von einem Test."""
    for name in ("UEBUNGSWOERTER_LEVEL_1", "UEBUNGSSAETZE_LEVEL_2", "UEBUNGSSAETZE_LEVEL_3",
                 "UEBUNGSTEXTE_NACH_LEVEL", "ALLE_UEBUNGSTEXTE"):
        assert not hasattr(uebungen, name), name


# ───────────────────────────────────────────────────────────────────────────
# 2. Die Vigenère-Schlüsselwörter
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
        beispiel = POOL[0]
        assert vigenere.verschluesseln(beispiel, wort) != beispiel, (
            f"Mit dem Schlüsselwort {wort!r} bleibt der Text unverändert."
        )


# ───────────────────────────────────────────────────────────────────────────
# 3. Alle Texte lassen sich in allen drei Verfahren benutzen
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", POOL)
def test_jeder_text_laeuft_durch_alle_drei_verfahren_und_zurueck(text):
    """Kein Pooltext darf in irgendeinem Level am Rundlauf scheitern."""
    assert caesar.entschluesseln(caesar.verschluesseln(text, 3), 3) == text
    assert substitution.entschluesseln(substitution.verschluesseln(text)) == text
    for wort in uebungen.VIGENERE_SCHLUESSELWOERTER:
        assert vigenere.entschluesseln(vigenere.verschluesseln(text, wort), wort) == text


# ───────────────────────────────────────────────────────────────────────────
# 4. Der Abgleich mit der Quelle
# ───────────────────────────────────────────────────────────────────────────

def test_das_handbuch_enthaelt_genau_eine_uebungsliste_mit_vierundfuenfzig_eintraegen():
    """Eine für alle drei Seiten – und nicht leer, sonst würde der folgende Vergleich trivial grün."""
    listen = _uebungslisten_aus_dem_handbuch()
    assert len(listen) == 1, f"Erwartet eine Übungsliste, gefunden {len(listen)}."
    assert len(listen[0]) == 54, f"Die Übungsliste hat {len(listen[0])} statt 54 Einträge."


def test_der_pool_stimmt_woertlich_mit_dem_handbuch_ueberein():
    """Was der Code übt, muss wörtlich im Handbuch stehen – und umgekehrt."""
    (im_handbuch,) = _uebungslisten_aus_dem_handbuch()
    assert list(POOL) == im_handbuch, (
        "content/uebungen.py und dokumentation/Handbuchtexte.md laufen auseinander.\n"
        f"  nur im Code:     {sorted(set(POOL) - set(im_handbuch))}\n"
        f"  nur im Handbuch: {sorted(set(im_handbuch) - set(POOL))}"
    )


# ───────────────────────────────────────────────────────────────────────────
# 5. Die Caesar-Schlüssel
# ───────────────────────────────────────────────────────────────────────────

def test_es_gibt_mehrere_caesar_schluessel_zur_auswahl():
    """Ein fester Schlüssel macht die Übungsaufgabe vorhersehbar."""
    assert len(uebungen.CAESAR_SCHLUESSEL) >= 5
    assert len(set(uebungen.CAESAR_SCHLUESSEL)) == len(uebungen.CAESAR_SCHLUESSEL)


@pytest.mark.parametrize("schluessel", uebungen.CAESAR_SCHLUESSEL)
def test_jeder_caesar_schluessel_veraendert_den_text(schluessel):
    """0 und 26 verschieben nichts – als Aufgabe wären sie sinnlos."""
    beispiel = POOL[0]
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
    beispiel = POOL[0]
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
