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
import sys
from pathlib import Path

import pytest

import content
import crypto
import game
import ui
from content import uebungen
from crypto import caesar, substitution, vigenere, vigenere_quadrat
from crypto.normalize import (
    ALPHABET,
    LEERZEICHEN,
    normalisieren,
    vergleiche_tolerant,
)

# Das Übungsmaterial kommt seit Aufgabe 2.2 aus content/uebungen.py – dort
# steht es einmal, und tests/test_uebungen.py hält es gegen das Markdown des
# Handbuchs. Hier wird es nur noch benutzt, nicht mehr wiederholt.
UEBUNGSWOERTER_LEVEL1 = uebungen.UEBUNGSWOERTER_LEVEL_1
UEBUNGSSAETZE_LEVEL2 = uebungen.UEBUNGSSAETZE_LEVEL_2
UEBUNGSSAETZE_LEVEL3 = uebungen.UEBUNGSSAETZE_LEVEL_3
ALLE_UEBUNGSTEXTE = uebungen.ALLE_UEBUNGSTEXTE
SCHLUESSELWOERTER = uebungen.VIGENERE_SCHLUESSELWOERTER

# Die Caesar-Schlüssel sind kein Handbuch-Material, sondern bewusst gewählte
# Prüfwerte: 0 und 26 als Nullverschiebung, 25 und -1 als Randfall, 51 als
# Beleg dafür, dass sehr grosse Schlüssel umgebrochen werden.
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
# 5. Projektregeln: Schichten, Tkinter, Fremdpakete
# ───────────────────────────────────────────────────────────────────────────
#
# Geprüft wird über den Syntaxbaum, nicht über Textsuche: Das Wort "tkinter"
# darf in einem Docstring stehen ("dieses Modul benutzt kein tkinter").
# Verboten ist der Import, nicht die Erwähnung.

#: Welche Projektpakete darf ein Paket importieren? Bildet die erlaubte
#: Abhängigkeitsrichtung aus CLAUDE.md ab: ui -> game -> crypto / content.
#: Ein Paket darf sich immer selbst importieren.
ERLAUBTE_ABHAENGIGKEITEN = {
    "crypto": {"crypto"},
    "content": {"content"},
    "game": {"game", "crypto", "content"},
    "ui": {"ui", "game", "crypto", "content"},
}

#: Nur diese Pakete dürfen Tkinter anfassen. main.py steht ausserhalb der
#: Pakete und wird gesondert geprüft.
PAKETE_MIT_TKINTER = {"ui"}

PROJEKTPAKETE = set(ERLAUBTE_ABHAENGIGKEITEN)

# Pakete ohne Oberfläche – dort ist zusätzlich print()/input() verboten.
LOGIKPAKETE = (crypto, game, content)


def _quelldateien(*pakete):
    dateien = []
    for paket in pakete:
        dateien.extend(Path(paket.__file__).parent.glob("*.py"))
    return sorted(dateien)


def _logik_quelldateien():
    return _quelldateien(*LOGIKPAKETE)


def _alle_paket_quelldateien():
    return _quelldateien(crypto, game, content, ui)


def _paketname(pfad):
    """crypto/caesar.py -> "crypto/caesar.py" (für lesbare Test-IDs)."""
    return f"{pfad.parent.name}/{pfad.name}"


def _importierte_module(quelldatei):
    """Alle Modulnamen, die eine Datei importiert.

    Relative Importe werden auf ihren vollen Namen aufgelöst, damit
    ``from .normalize import ...`` als ``crypto.normalize`` erscheint und
    nicht als das viel harmlosere ``normalize``.
    """
    baum = ast.parse(quelldatei.read_text(encoding="utf-8"), filename=str(quelldatei))
    namen = []
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            namen.extend(alias.name for alias in knoten.names)
        elif isinstance(knoten, ast.ImportFrom):
            if knoten.level:
                namen.append(f"{quelldatei.parent.name}.{knoten.module or ''}")
            elif knoten.module:
                namen.append(knoten.module)
    return namen


def test_es_gibt_ueberhaupt_module_zu_pruefen():
    """Schutz davor, dass die folgenden Tests durch eine leere Liste grün werden."""
    namen = {_paketname(pfad) for pfad in _alle_paket_quelldateien()}
    assert {
        "crypto/normalize.py",
        "crypto/caesar.py",
        "crypto/substitution.py",
        "crypto/vigenere.py",
        "crypto/vigenere_quadrat.py",
        "content/handbuch.py",
        "content/uebungen.py",
        "content/story.py",
        "content/charaktere.py",
        "game/__init__.py",
        "game/durchlauf.py",
        "ui/__init__.py",
        "ui/hauptfenster.py",
        "ui/screen.py",
        "ui/animation.py",
        "ui/intro.py",
    } <= namen


@pytest.mark.parametrize("paket", [crypto, game, content, ui], ids=lambda p: p.__name__)
def test_die_pakete_haben_keine_unterordner_mit_quelltext(paket):
    """Die Prüfungen hier lesen nur die oberste Ebene jedes Pakets.

    Ein Unterordner wie ``ui/screens/`` würde deshalb stillschweigend nicht
    geprüft – ein Tkinter-Import in ``game/irgendwas/`` fiele niemandem auf.
    Wer einen Unterordner braucht, muss vorher ``_quelldateien`` erweitern.
    """
    wurzel = Path(paket.__file__).parent
    unterordner = sorted(
        str(ordner.relative_to(wurzel))
        for ordner in wurzel.iterdir()
        if ordner.is_dir() and any(ordner.rglob("*.py"))
    )
    assert unterordner == [], (
        f"{paket.__name__}/ hat Unterordner mit Python-Dateien: {unterordner}"
    )


@pytest.mark.parametrize(
    "quelldatei", _alle_paket_quelldateien(), ids=_paketname
)
def test_die_schichten_halten_ihre_abhaengigkeitsrichtung_ein(quelldatei):
    """CLAUDE.md: ui -> game -> crypto / content, niemals umgekehrt.

    Geprüft wird nur die Richtung zwischen den Projektpaketen. Dass ein Paket
    sich selbst importiert, ist erlaubt und normal – ``crypto/caesar.py``
    holt sich seine Textkonvention aus ``crypto/normalize.py``.
    """
    paket = quelldatei.parent.name
    erlaubt = ERLAUBTE_ABHAENGIGKEITEN[paket]
    for name in _importierte_module(quelldatei):
        wurzel = name.split(".")[0]
        if wurzel not in PROJEKTPAKETE:
            continue
        assert wurzel in erlaubt, (
            f"{_paketname(quelldatei)} importiert '{name}'. {paket}/ darf nur "
            f"{sorted(erlaubt)} benutzen – sonst dreht sich die "
            "Abhängigkeitsrichtung um."
        )


@pytest.mark.parametrize(
    "quelldatei", _alle_paket_quelldateien(), ids=_paketname
)
def test_tkinter_nur_in_der_oberflaeche(quelldatei):
    """CLAUDE.md, Regel 5: crypto/, game/ und content/ kennen keine Oberfläche."""
    paket = quelldatei.parent.name
    for name in _importierte_module(quelldatei):
        if name.split(".")[0] != "tkinter":
            continue
        assert paket in PAKETE_MIT_TKINTER, (
            f"{_paketname(quelldatei)} importiert '{name}' – Tkinter gehört "
            "nach ui/ (und in main.py, das den Startfehler abfängt)."
        )


def test_main_py_ist_die_einzige_datei_ausserhalb_von_ui_mit_tkinter():
    """main.py darf Tkinter benutzen, sonst niemand ausserhalb von ui/."""
    wurzel = Path(crypto.__file__).resolve().parent.parent
    with_tkinter = []
    for pfad in wurzel.glob("*.py"):
        if "tkinter" in {n.split(".")[0] for n in _importierte_module(pfad)}:
            with_tkinter.append(pfad.name)
    assert with_tkinter == ["main.py"], (
        f"Tkinter im Projekt-Root nur in main.py erwartet, gefunden: {with_tkinter}"
    )


@pytest.mark.parametrize(
    "quelldatei", _alle_paket_quelldateien(), ids=_paketname
)
def test_module_brauchen_keine_fremdpakete(quelldatei):
    """Nur Standardbibliothek und eigene Pakete – Schulrechner haben kein pip.

    Geprüft wird gegen ``sys.stdlib_module_names``, nicht gegen eine eigene
    Liste erlaubter Namen: Die Zusage lautet "keine Fremdpakete", nicht "keine
    Importe". Ein Test, der jeden Import verbietet, würde schon beim ersten
    berechtigten ``import unicodedata`` fehlschlagen und dann eher entschärft
    als ernst genommen.
    """
    for name in _importierte_module(quelldatei):
        wurzel = name.split(".")[0]
        erlaubt = wurzel in PROJEKTPAKETE or wurzel in sys.stdlib_module_names
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


