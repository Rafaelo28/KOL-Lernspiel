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
from pathlib import Path

import pytest

import crypto
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

@pytest.mark.parametrize("text", ALLE_UEBUNGSTEXTE)
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

def _crypto_quelldateien():
    ordner = Path(crypto.__file__).parent
    return sorted(pfad for pfad in ordner.glob("*.py"))


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


def test_es_gibt_ueberhaupt_crypto_module_zu_pruefen():
    """Schutz davor, dass die folgenden Tests durch eine leere Liste grün werden."""
    namen = {pfad.name for pfad in _crypto_quelldateien()}
    assert {
        "normalize.py",
        "caesar.py",
        "substitution.py",
        "vigenere.py",
        "vigenere_quadrat.py",
    } <= namen


@pytest.mark.parametrize(
    "quelldatei", _crypto_quelldateien(), ids=lambda pfad: pfad.name
)
def test_kein_gui_import_in_crypto(quelldatei):
    """CLAUDE.md, Regel 5: crypto/ ist rein – Text rein, Text raus."""
    verboten = ("tkinter", "ui", "game")
    for name in _importierte_module(quelldatei):
        wurzel = name.lstrip(".").split(".")[0]
        assert wurzel not in verboten, (
            f"{quelldatei.name} importiert '{name}' – crypto/ darf weder GUI-Code "
            "noch Spiellogik kennen."
        )


@pytest.mark.parametrize(
    "quelldatei", _crypto_quelldateien(), ids=lambda pfad: pfad.name
)
def test_crypto_module_brauchen_keine_fremdpakete(quelldatei):
    """Nur Standardbibliothek und crypto selbst – Schulrechner haben kein pip."""
    for name in _importierte_module(quelldatei):
        assert name.startswith(".") or name.split(".")[0] == "crypto", (
            f"{quelldatei.name} importiert das Fremdpaket '{name}'."
        )
