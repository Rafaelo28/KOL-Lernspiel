"""Tests über Modulgrenzen hinweg (Arbeitsplan 1.6, Rundlauf-Teil).

Die Einzeltests prüfen jedes Verfahren für sich. Hier steht das, was kein
einzelnes Modul prüfen kann:

* Rechnen und Nachschlagen müssen dasselbe ergeben – sonst widerspricht das
  Handbuch dem Spiel und die Schülerinnen und Schüler rechnen "falsch"
  richtig.
* Die Textkonvention muss in allen drei Verfahren gleich wirken, sonst
  verhält sich das Fehlerhandling aus Phase 4 je Level anders.
* Die Projektregel "crypto/ enthält niemals GUI-Code" wird hier maschinell
  nachgehalten, statt sie nur in CLAUDE.md zu behaupten.
"""

import ast
import re
import sys
from pathlib import Path

import pytest

import content
import crypto
import game
from crypto import caesar, substitution, vigenere, vigenere_quadrat
from crypto.normalize import (
    ALPHABET,
    LEERZEICHEN,
    normalisieren,
    vergleiche_tolerant,
)

# Die Übungswörter und -sätze aus dokumentation/Handbuchtexte.md.
# Ab Aufgabe 2.2 leben sie in content/uebungen.py; bis dahin stehen sie hier,
# damit die Rundlauf-Tests schon jetzt auf dem echten Material laufen.
UEBUNGSWOERTER_LEVEL1 = (
    "HUND", "KATZE", "MAUS", "BURG", "FELS",
    "WALD", "STERN", "MOND", "SAND", "TURM",
)
UEBUNGSSAETZE_LEVEL2 = (
    "ALLES OK", "ICH BIN HIER", "KOMM SCHNELL", "WO BIST DU", "BLEIB RUHIG",
    "WEG IST FREI", "GEFAHR NAH", "ZEIT WIRD KNAPP", "PLAN WIRD NEU",
    "HILFE WIRD GEBRAUCHT",
)
UEBUNGSSAETZE_LEVEL3 = (
    "ICH BIN IN SICHERHEIT", "STANDORT UNBEKANNT", "NAHE DEM WRACK",
    "RICHTUNG NORDEN", "KEIN WASSER MEHR", "VERFOLGER SIND NAH",
    "BRAUCHE SOFORT HILFE", "BIN NOCH AM LEBEN", "WARTE AUF RETTUNG",
    "SIGNAL WIRD SCHWACH",
)
ALLE_UEBUNGSTEXTE = (
    UEBUNGSWOERTER_LEVEL1 + UEBUNGSSAETZE_LEVEL2 + UEBUNGSSAETZE_LEVEL3
)

# Aus dem Handbuch: das Schlüsselwort für Level 3 wird zufällig aus mehreren
# Wörtern gezogen, damit die Aufgabe nicht vorhersehbar wird.
SCHLUESSELWOERTER = ("ROT", "WEG", "TAG")
CAESAR_SCHLUESSEL = (0, 1, 3, 7, 13, 25, 26, -1, -3, 51)


def _positionen_der_leerzeichen(text):
    """Liste der Stellen, an denen im Text ein Leerzeichen steht."""
    return [i for i, zeichen in enumerate(text) if zeichen == LEERZEICHEN]


# ───────────────────────────────────────────────────────────────────────────
# 1. Der Kernnachweis: Formel (vigenere) == Nachschlagetabelle (Quadrat)
# ───────────────────────────────────────────────────────────────────────────

def test_formel_und_quadrat_stimmen_in_allen_676_feldern_ueberein():
    """Rechenweg und Handbuch-Quadrat müssen identisch verschlüsseln.

    Das ist der wichtigste Test der ganzen Phase 1: Das Handbuch erklärt
    Vigenère über das Quadrat, das Spiel prüft die Eingabe über die Formel.
    Wären die beiden auch nur in einem Feld verschieden, würde eine korrekt
    abgelesene Lösung als Fehlversuch gewertet.
    """
    abweichungen = []
    for schluesselbuchstabe in ALPHABET:
        for klarbuchstabe in ALPHABET:
            gerechnet = vigenere.verschluesseln(klarbuchstabe, schluesselbuchstabe)
            abgelesen = vigenere_quadrat.verschluesselter_buchstabe(
                schluesselbuchstabe, klarbuchstabe
            )
            if gerechnet != abgelesen:
                abweichungen.append(
                    f"Zeile {schluesselbuchstabe}, Spalte {klarbuchstabe}: "
                    f"gerechnet {gerechnet}, abgelesen {abgelesen}"
                )

    assert not abweichungen, (
        "Formel und Quadrat sind nicht deckungsgleich:\n"
        + "\n".join(abweichungen[:10])
    )


def test_formel_und_quadrat_stimmen_auch_beim_entschluesseln_ueberein():
    """Auch rückwärts muss Ablesen dasselbe ergeben wie Rechnen."""
    for schluesselbuchstabe in ALPHABET:
        for geheimbuchstabe in ALPHABET:
            gerechnet = vigenere.entschluesseln(geheimbuchstabe, schluesselbuchstabe)
            abgelesen = vigenere_quadrat.klarbuchstabe_finden(
                schluesselbuchstabe, geheimbuchstabe
            )
            assert gerechnet == abgelesen, (
                f"Zeile {schluesselbuchstabe}, Geheimbuchstabe {geheimbuchstabe}: "
                f"gerechnet {gerechnet}, abgelesen {abgelesen}"
            )


@pytest.mark.parametrize("text", UEBUNGSSAETZE_LEVEL3)
@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_ganze_saetze_lassen_sich_mit_dem_quadrat_nachvollziehen(text, schluesselwort):
    """Ein ganzer Übungssatz, Buchstabe für Buchstabe im Quadrat abgelesen.

    Das ahmt genau nach, was die Spielenden auf Papier tun: Schlüssel über
    den Text legen (Regel 7), dann Feld für Feld nachschlagen.
    """
    klartext = normalisieren(text)
    schluesselzeile = vigenere.schluessel_ausrichten(text, schluesselwort)

    von_hand = "".join(
        LEERZEICHEN
        if klarzeichen == LEERZEICHEN
        else vigenere_quadrat.verschluesselter_buchstabe(schluesselzeichen, klarzeichen)
        for klarzeichen, schluesselzeichen in zip(klartext, schluesselzeile)
    )

    assert von_hand == vigenere.verschluesseln(text, schluesselwort)


# ───────────────────────────────────────────────────────────────────────────
# 2. Rundlauf über das echte Handbuch-Material, alle drei Verfahren
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE)
@pytest.mark.parametrize("schluessel", CAESAR_SCHLUESSEL)
def test_rundlauf_caesar(text, schluessel):
    """entschluesseln(verschluesseln(x)) == x für alle Übungstexte."""
    geheim = caesar.verschluesseln(text, schluessel)
    assert caesar.entschluesseln(geheim, schluessel) == normalisieren(text)


@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE)
def test_rundlauf_substitution(text):
    """entschluesseln(verschluesseln(x)) == x für alle Übungstexte."""
    geheim = substitution.verschluesseln(text)
    assert substitution.entschluesseln(geheim) == normalisieren(text)


@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE)
@pytest.mark.parametrize("schluesselwort", SCHLUESSELWOERTER)
def test_rundlauf_vigenere(text, schluesselwort):
    """entschluesseln(verschluesseln(x)) == x für alle Übungstexte."""
    geheim = vigenere.verschluesseln(text, schluesselwort)
    assert vigenere.entschluesseln(geheim, schluesselwort) == normalisieren(text)


# ───────────────────────────────────────────────────────────────────────────
# 3. Die Textkonvention wirkt in allen drei Verfahren gleich
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE)
def test_alle_verfahren_lassen_die_leerzeichen_an_ort_und_stelle(text):
    """Regel 3 muss in allen drei Verfahren identisch gelten."""
    klartext = normalisieren(text)
    erwartete_stellen = _positionen_der_leerzeichen(klartext)

    for geheimtext in (
        caesar.verschluesseln(text, 5),
        substitution.verschluesseln(text),
        vigenere.verschluesseln(text, "ROT"),
    ):
        assert len(geheimtext) == len(klartext)
        assert _positionen_der_leerzeichen(geheimtext) == erwartete_stellen


@pytest.mark.parametrize(
    "roh",
    [
        "Hallo, hört mich jemand?",
        "zeit   wird\tknapp",
        "Straße 42!",
        "Übung macht den Meister",
    ],
)
def test_alle_verfahren_normalisieren_ihre_eingabe_selbst(roh):
    """Roher Text und vornormalisierter Text müssen dasselbe ergeben.

    Die UI darf den Spielertext also unverändert durchreichen.
    """
    sauber = normalisieren(roh)
    assert caesar.verschluesseln(roh, 4) == caesar.verschluesseln(sauber, 4)
    assert substitution.verschluesseln(roh) == substitution.verschluesseln(sauber)
    assert vigenere.verschluesseln(roh, "WEG") == vigenere.verschluesseln(sauber, "WEG")


@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE)
def test_jedes_ergebnis_ist_selbst_schon_normalisiert(text):
    """Der Geheimtext darf direkt angezeigt werden – ohne Nachbearbeitung."""
    for geheimtext in (
        caesar.verschluesseln(text, 11),
        substitution.verschluesseln(text),
        vigenere.verschluesseln(text, "TAG"),
    ):
        assert normalisieren(geheimtext) == geheimtext
        assert set(geheimtext) <= set(ALPHABET) | {LEERZEICHEN}


@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE)
def test_die_pruefung_aus_phase_4_akzeptiert_die_musterloesung(text):
    """vergleiche_tolerant() muss die richtige Lösung auch zerschrieben annehmen.

    Vorgriff auf Aufgabe 4.1: Wer die Leerzeichen weglässt oder alles klein
    schreibt, hat die Aufgabe trotzdem gelöst und darf keinen Fehlversuch
    verbrauchen.
    """
    loesung = vigenere.verschluesseln(text, "ROT")
    assert vergleiche_tolerant(loesung, loesung)
    assert vergleiche_tolerant(loesung.replace(LEERZEICHEN, ""), loesung)
    assert vergleiche_tolerant(loesung.lower(), loesung)


# ───────────────────────────────────────────────────────────────────────────
# 4. Verhältnis der Verfahren zueinander
# ───────────────────────────────────────────────────────────────────────────

# Für die Gleichheit von Caesar und Vigenère kommt es auf die Verschiebung an,
# nicht auf den Text. Alle 30 Übungstexte durchzuprobieren ergäbe 780 Fälle,
# die dieselbe Aussage 30-mal wiederholen.
#
# Auf den Text kommt es aber in einer Hinsicht doch an: Jeder Buchstabe sollte
# mindestens einmal vorkommen. Die 30 Übungstexte decken zusammen nur 22 der
# 26 Buchstaben ab – J, Q, X und Y kommen im Handbuch überhaupt nicht vor.
# Deshalb steht das vollständige Alphabet als erste Probe hier: Damit deckt
# der gekürzte Test 26 von 26 Buchstaben ab und damit mehr als die 780 Fälle
# vorher. Die drei weiteren Proben bringen die Wortgrenzen ein, die dem
# Alphabet fehlen.
TEXTPROBEN = (
    ALPHABET,
    "HUND",
    "ALLES OK",
    "ICH BIN IN SICHERHEIT",
)


@pytest.mark.parametrize("text", TEXTPROBEN)
@pytest.mark.parametrize("verschiebung", range(26))
def test_caesar_ist_vigenere_mit_einbuchstabigem_schluessel(text, verschiebung):
    """Caesar ist der Sonderfall von Vigenère mit Schlüssellänge 1.

    Genau das erklärt Handbuchseite 3 ("Bei Caesar hast du immer um dieselbe
    Zahl verschoben"). Stimmt es nicht, widersprechen sich die Level.
    """
    schluesselbuchstabe = ALPHABET[verschiebung]
    assert caesar.verschluesseln(text, verschiebung) == vigenere.verschluesseln(
        text, schluesselbuchstabe
    )


def test_substitution_ist_keine_verschiebung():
    """Level 2 muss sich nachweisbar von Level 1 unterscheiden.

    Die Tastatur-Tabelle darf zu keinem Caesar-Schlüssel äquivalent sein –
    sonst wäre der Lernschritt von Level 1 zu Level 2 keiner.
    """
    beispiel = "HILFE WIRD GEBRAUCHT"
    mit_substitution = substitution.verschluesseln(beispiel)
    for schluessel in range(26):
        assert mit_substitution != caesar.verschluesseln(beispiel, schluessel)


# ───────────────────────────────────────────────────────────────────────────
# 5. Projektregel: crypto/ enthält niemals GUI-Code
# ───────────────────────────────────────────────────────────────────────────
#
# Geprüft wird über den Syntaxbaum, nicht über Textsuche: Das Wort "tkinter"
# darf in einem Docstring durchaus vorkommen ("dieses Modul benutzt kein
# tkinter"). Verboten ist der Import, nicht die Erwähnung.

# Geprüft werden alle drei Schichten, die keine Oberfläche kennen dürfen.
# game/ und content/ sind heute noch fast leer – gerade deshalb steht die
# Prüfung schon hier: Sie greift ab der ersten Datei, die dort entsteht.
GEPRUEFTE_PAKETE = (crypto, game, content)


def _logik_quelldateien():
    dateien = []
    for paket in GEPRUEFTE_PAKETE:
        dateien.extend(Path(paket.__file__).parent.glob("*.py"))
    return sorted(dateien)


def _paketname(pfad):
    """crypto/caesar.py -> "crypto/caesar.py" (für lesbare Test-IDs)."""
    return f"{pfad.parent.name}/{pfad.name}"


def _importierte_module(quelldatei):
    """Alle Modulnamen, die eine Datei importiert.

    Ein relativer Import (``from .normalize import ...``) wird als
    ``".normalize"`` zurückgegeben, damit er sich von einem Fremdpaket
    unterscheiden lässt.
    """
    baum = ast.parse(quelldatei.read_text(encoding="utf-8"), filename=str(quelldatei))
    namen = []
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            namen.extend(alias.name for alias in knoten.names)
        elif isinstance(knoten, ast.ImportFrom):
            namen.append("." * knoten.level + (knoten.module or ""))
    return namen


def test_es_gibt_ueberhaupt_module_zu_pruefen():
    """Schutz davor, dass die folgenden Tests durch eine leere Liste grün werden."""
    namen = {_paketname(pfad) for pfad in _logik_quelldateien()}
    assert {
        "crypto/normalize.py",
        "crypto/caesar.py",
        "crypto/substitution.py",
        "crypto/vigenere.py",
        "crypto/vigenere_quadrat.py",
        "game/__init__.py",
        "content/__init__.py",
    } <= namen


@pytest.mark.parametrize(
    "quelldatei", _logik_quelldateien(), ids=_paketname
)
def test_kein_gui_import_in_der_logik(quelldatei):
    """CLAUDE.md, Regel 5: crypto/, game/ und content/ kennen keine Oberfläche."""
    verboten = ("tkinter", "ui", "game")
    for name in _importierte_module(quelldatei):
        wurzel = name.lstrip(".").split(".")[0]
        assert wurzel not in verboten, (
            f"{_paketname(quelldatei)} importiert '{name}' – nur ui/ und main.py "
            "dürfen Tkinter benutzen."
        )


@pytest.mark.parametrize(
    "quelldatei", _logik_quelldateien(), ids=_paketname
)
def test_module_brauchen_keine_fremdpakete(quelldatei):
    """Nur Standardbibliothek und crypto selbst – Schulrechner haben kein pip.

    Geprüft wird gegen ``sys.stdlib_module_names``, nicht gegen eine eigene
    Liste erlaubter Namen: Die Zusage lautet "keine Fremdpakete", nicht "keine
    Importe". Ein Test, der jeden Import verbietet, würde schon beim ersten
    berechtigten ``import unicodedata`` fehlschlagen und dann eher entschärft
    als ernst genommen.
    """
    for name in _importierte_module(quelldatei):
        wurzel = name.lstrip(".").split(".")[0]
        erlaubt = (
            name.startswith(".")
            or wurzel == "crypto"
            or wurzel in sys.stdlib_module_names
        )
        assert erlaubt, (
            f"{_paketname(quelldatei)} importiert das Fremdpaket '{name}'."
        )


@pytest.mark.parametrize(
    "quelldatei", _logik_quelldateien(), ids=_paketname
)
def test_keine_konsolenausgabe_in_der_logik(quelldatei):
    """Reine Funktionen: Text rein, Text raus – kein print(), kein input().

    Auch das über den Syntaxbaum: Gesucht wird der tatsächliche Aufruf, nicht
    das Wort. Ein Docstring darf erklären, dass ein Modul nichts ausgibt,
    ohne dass ein Test deswegen rot wird.
    """
    baum = ast.parse(quelldatei.read_text(encoding="utf-8"))
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Call) and isinstance(knoten.func, ast.Name):
            assert knoten.func.id not in {"print", "input"}, (
                f"{_paketname(quelldatei)} ruft {knoten.func.id}() auf – die "
                "Logik gibt nichts aus und fragt nichts ab, das macht ui/."
            )


# ───────────────────────────────────────────────────────────────────────────
# Die Übungstexte im Code müssen zum Handbuch passen
# ───────────────────────────────────────────────────────────────────────────
#
# Die 30 Übungswörter und -sätze stehen bislang doppelt: einmal als Quelle in
# dokumentation/Handbuchtexte.md, einmal hart in den Testdateien. Ab Aufgabe
# 2.2 kommt mit content/uebungen.py eine dritte Kopie dazu. Wer eine
# Handbuchseite ändert, würde das sonst nirgends merken – die Spielenden
# bekämen ein Wort zu sehen, das im Handbuch gar nicht steht.

HANDBUCH = Path(__file__).resolve().parent.parent / "dokumentation" / "Handbuchtexte.md"


def _uebungslisten_aus_dem_handbuch():
    """Liest die drei nummerierten Übungslisten aus der Handbuch-Datei.

    Rückgabe: Liste mit drei Listen, in der Reihenfolge der Seiten
    (Caesar, Substitution, Vigenère).
    """
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


def test_das_handbuch_enthaelt_drei_uebungslisten_mit_je_zehn_eintraegen():
    """Schutz davor, dass der folgende Vergleich durch leere Listen grün wird."""
    listen = _uebungslisten_aus_dem_handbuch()
    assert len(listen) == 3, f"Erwartet 3 Übungslisten, gefunden {len(listen)}."
    for nummer, liste in enumerate(listen, start=1):
        assert len(liste) == 10, (
            f"Übungsliste {nummer} hat {len(liste)} statt 10 Einträge."
        )


@pytest.mark.parametrize(
    "level, im_code",
    [
        (1, UEBUNGSWOERTER_LEVEL1),
        (2, UEBUNGSSAETZE_LEVEL2),
        (3, UEBUNGSSAETZE_LEVEL3),
    ],
)
def test_uebungstexte_stimmen_mit_dem_handbuch_ueberein(level, im_code):
    """Was der Code übt, muss wörtlich im Handbuch stehen – und umgekehrt."""
    im_handbuch = _uebungslisten_aus_dem_handbuch()[level - 1]
    assert list(im_code) == im_handbuch, (
        f"Level {level}: Übungstexte im Code und in "
        f"dokumentation/Handbuchtexte.md laufen auseinander.\n"
        f"  nur im Code:     {sorted(set(im_code) - set(im_handbuch))}\n"
        f"  nur im Handbuch: {sorted(set(im_handbuch) - set(im_code))}"
    )
