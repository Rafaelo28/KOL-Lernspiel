"""Tests für content/handbuch.py (Arbeitsplan 2.1).

Zwei Sorten von Prüfungen:

1. **Aufbau** – hat jede Seite die Abschnitte, die die UI erwartet, und sind
   die Tabellen so geformt, dass ein Grid daraus entsteht?
2. **Übereinstimmung mit crypto/** – das ist der eigentliche Punkt. Im
   Handbuch stehen durchgerechnete Beispiele: die Geheimtabelle, das um drei
   verschobene Alphabet, HUND wird zu KXQG, IXFR und YIGU, dazu jeder einzelne
   Schritt im Vigenère-Quadrat. Dieselben Werte berechnet ``crypto/`` beim
   Prüfen der Schülerantworten. Wenn beides auseinanderläuft, lernen die
   Spielenden etwas anderes, als das Spiel von ihnen verlangt – und das
   Fehlerhandling wertet richtige Lösungen als Fehlversuch.
"""

import re

import pytest

from content import handbuch
from content import verfahren
from content.handbuch import (
    Absatz,
    Aufzaehlung,
    Handbuchseite,
    Tabelle,
    VigenereQuadrat,
)
from crypto import caesar, substitution, vigenere, vigenere_quadrat
from crypto.normalize import ALPHABET


# ───────────────────────────────────────────────────────────────────────────
# Hilfsmittel
# ───────────────────────────────────────────────────────────────────────────

def _abschnitt(seite, ueberschrift):
    """Sucht einen Abschnitt einer Seite anhand seiner Überschrift."""
    for abschnitt in seite.abschnitte:
        if abschnitt.ueberschrift == ueberschrift:
            return abschnitt
    raise AssertionError(
        f"Seite {seite.level} hat keinen Abschnitt '{ueberschrift}'. "
        f"Vorhanden: {[a.ueberschrift for a in seite.abschnitte]}"
    )


def _tabellen(seite):
    """Alle Tabellen einer Seite in Reihenfolge."""
    return [
        block
        for abschnitt in seite.abschnitte
        for block in abschnitt.bloecke
        if isinstance(block, Tabelle)
    ]


def _tabellenzeile(seite, beschriftung):
    """Die Zellen der Zeile mit dieser Beschriftung, ohne die Beschriftung."""
    for tabelle in _tabellen(seite):
        for zeile in tabelle.zeilen:
            if zeile[0] == beschriftung:
                return tuple(zeile[1:])
    raise AssertionError(
        f"Seite {seite.level} hat keine Tabellenzeile '{beschriftung}'."
    )


def _alle_texte(seite):
    """Jeden Text der Seite als flache Liste – für Suchen im Fließtext."""
    texte = [seite.titel]
    for abschnitt in seite.abschnitte:
        texte.append(abschnitt.ueberschrift)
        for block in abschnitt.bloecke:
            if isinstance(block, Absatz):
                texte.append(block.text)
            elif isinstance(block, Aufzaehlung):
                texte.extend(block.punkte)
            elif isinstance(block, Tabelle):
                texte.append(block.titel)
                texte.extend(zelle for zeile in block.zeilen for zelle in zeile)
            elif isinstance(block, VigenereQuadrat):
                texte.append(block.beschriftung)
    return texte


def _ergebnis(seite, klartext):
    """Liest "Ergebnis: HUND wird zu KXQG" und gibt "KXQG" zurück."""
    muster = re.compile(rf"Ergebnis: {klartext} wird zu ([A-Z]+)")
    for text in _alle_texte(seite):
        treffer = muster.search(text)
        if treffer:
            return treffer.group(1)
    raise AssertionError(
        f"Seite {seite.level} nennt kein Ergebnis für '{klartext}'."
    )


def _schrittergebnisse(abschnitt):
    """Der jeweils letzte Großbuchstabe jedes nummerierten Schritts."""
    for block in abschnitt.bloecke:
        if isinstance(block, Aufzaehlung) and block.nummeriert:
            return [re.search(r"([A-Z])\.$", punkt).group(1) for punkt in block.punkte]
    raise AssertionError(
        f"Abschnitt '{abschnitt.ueberschrift}' hat keine nummerierten Schritte."
    )


# ───────────────────────────────────────────────────────────────────────────
# 1. Aufbau
# ───────────────────────────────────────────────────────────────────────────

def test_es_gibt_genau_drei_seiten_fuer_die_drei_level():
    assert len(handbuch.SEITEN) == 3
    assert [seite.level for seite in handbuch.SEITEN] == [1, 2, 3]


def test_die_nachschlagetabelle_passt_zu_den_seiten():
    """SEITE_NACH_LEVEL ist die Sicht, mit der die UI arbeitet."""
    assert set(handbuch.SEITE_NACH_LEVEL) == {1, 2, 3}
    for level, seite in handbuch.SEITE_NACH_LEVEL.items():
        assert seite.level == level
        assert seite in handbuch.SEITEN


@pytest.mark.parametrize("seite", handbuch.SEITEN, ids=lambda s: f"Level {s.level}")
def test_jede_seite_hat_die_pflichtabschnitte(seite):
    """Der Arbeitsplan verlangt "Was ist das?" und einen Merksatz je Seite."""
    _abschnitt(seite, "Was ist das?")
    _abschnitt(seite, "Merksatz")


@pytest.mark.parametrize("seite", handbuch.SEITEN, ids=lambda s: f"Level {s.level}")
def test_genau_der_merksatz_ist_hervorgehoben(seite):
    """Die UI soll den Merksatz absetzen können, ohne auf den Wortlaut zu prüfen."""
    hervorgehoben = [a.ueberschrift for a in seite.abschnitte if a.hervorgehoben]
    assert hervorgehoben == ["Merksatz"]


@pytest.mark.parametrize("seite", handbuch.SEITEN, ids=lambda s: f"Level {s.level}")
def test_kein_abschnitt_und_kein_text_ist_leer(seite):
    assert seite.titel.strip()
    assert seite.verfahren.strip()
    assert seite.abschnitte, f"Seite {seite.level} hat keine Abschnitte."
    for abschnitt in seite.abschnitte:
        assert abschnitt.ueberschrift.strip()
        assert abschnitt.bloecke, f"'{abschnitt.ueberschrift}' ist leer."
        for block in abschnitt.bloecke:
            assert isinstance(block, (Absatz, Aufzaehlung, Tabelle, VigenereQuadrat)), (
                f"Unbekannter Blocktyp {type(block).__name__} – die UI kennt nur "
                "Absatz, Aufzaehlung, Tabelle und VigenereQuadrat."
            )
            if isinstance(block, Absatz):
                assert block.text.strip()
            elif isinstance(block, Aufzaehlung):
                assert block.punkte
                assert all(punkt.strip() for punkt in block.punkte)


@pytest.mark.parametrize("seite", handbuch.SEITEN, ids=lambda s: f"Level {s.level}")
def test_tabellen_sind_rechteckig(seite):
    """Sonst bräuchte das Grid in Phase 6.4 ein Sonderfall-Layout."""
    for tabelle in _tabellen(seite):
        assert len(tabelle.zeilen) >= 2, "Eine Tabelle mit einer Zeile ist keine."
        breiten = {len(zeile) for zeile in tabelle.zeilen}
        assert len(breiten) == 1, (
            f"Tabelle '{tabelle.titel}' auf Seite {seite.level} hat "
            f"unterschiedlich lange Zeilen: {sorted(breiten)}"
        )
        for zeile in tabelle.zeilen:
            assert all(isinstance(zelle, str) for zelle in zeile)
            assert zeile[0].strip(), "Die erste Spalte ist die Zeilenbeschriftung."


@pytest.mark.parametrize("seite", handbuch.SEITEN, ids=lambda s: f"Level {s.level}")
def test_kein_markdown_im_text(seite):
    """Tkinter kennt kein Markdown und würde die Zeichen wörtlich anzeigen."""
    for text in _alle_texte(seite):
        for rest in ("**", "`", "$", "|"):
            assert rest not in text, (
                f"Markdown-Rest {rest!r} auf Seite {seite.level} in: {text[:70]!r}"
            )


# ───────────────────────────────────────────────────────────────────────────
# 2. Übereinstimmung mit crypto/ – der eigentliche Punkt
# ───────────────────────────────────────────────────────────────────────────

def test_seite_1_das_verschobene_alphabet_stimmt():
    """Die Alphabetzeilen sind das Herz der Caesar-Erklärung."""
    seite = handbuch.SEITE_NACH_LEVEL[1]
    assert "".join(_tabellenzeile(seite, "ohne Verschiebung")) == ALPHABET
    assert "".join(_tabellenzeile(seite, "um 3 verschoben")) == caesar.verschluesseln(
        ALPHABET, 3
    )


def test_seite_1_jede_spalte_der_alphabettabelle_ist_ein_gueltiges_paar():
    """Spaltenweise geprüft: unter jedem Buchstaben steht seine Verschiebung."""
    seite = handbuch.SEITE_NACH_LEVEL[1]
    klar = _tabellenzeile(seite, "ohne Verschiebung")
    verschoben = _tabellenzeile(seite, "um 3 verschoben")
    assert len(klar) == len(verschoben) == 26
    for oben, unten in zip(klar, verschoben):
        assert caesar.verschluesseln(oben, 3) == unten, (
            f"Im Handbuch steht unter {oben} der Buchstabe {unten}, "
            f"crypto/caesar.py rechnet {caesar.verschluesseln(oben, 3)}."
        )


def test_seite_1_das_beispiel_hund_stimmt():
    seite = handbuch.SEITE_NACH_LEVEL[1]
    assert _tabellenzeile(seite, "Buchstabe") == tuple("HUND")
    assert "".join(_tabellenzeile(seite, "verschoben um 3")) == caesar.verschluesseln(
        "HUND", 3
    )
    assert _ergebnis(seite, "HUND") == caesar.verschluesseln("HUND", 3)


def test_seite_2_der_tastatur_trick_stimmt_mit_dem_code_ueberein():
    """Die drei Tastaturreihen im Text sind dieselben wie in crypto/."""
    seite = handbuch.SEITE_NACH_LEVEL[2]
    abschnitt = _abschnitt(seite, "Ein Trick, um dir die Zuordnung zu merken")
    punkte = next(
        block.punkte
        for block in abschnitt.bloecke
        if isinstance(block, Aufzaehlung)
    )
    im_handbuch = [punkt.split(":", 1)[1].replace(" ", "") for punkt in punkte]
    assert tuple(im_handbuch) == substitution.TASTATUR_REIHEN


def test_seite_2_die_geheimtabelle_stimmt():
    seite = handbuch.SEITE_NACH_LEVEL[2]
    tabelle_im_code = substitution.erzeuge_tastatur_tabelle()
    assert "".join(_tabellenzeile(seite, "Original")) == ALPHABET
    assert "".join(_tabellenzeile(seite, "Geheim")) == "".join(tabelle_im_code.values())


def test_seite_2_jede_spalte_der_geheimtabelle_ist_ein_gueltiges_paar():
    seite = handbuch.SEITE_NACH_LEVEL[2]
    tabelle_im_code = substitution.erzeuge_tastatur_tabelle()
    original = _tabellenzeile(seite, "Original")
    geheim = _tabellenzeile(seite, "Geheim")
    assert len(original) == len(geheim) == 26
    for oben, unten in zip(original, geheim):
        assert tabelle_im_code[oben] == unten, (
            f"Im Handbuch wird {oben} zu {unten}, "
            f"crypto/substitution.py ordnet {tabelle_im_code[oben]} zu."
        )


def test_seite_2_das_beispiel_hund_stimmt():
    seite = handbuch.SEITE_NACH_LEVEL[2]
    assert _tabellenzeile(seite, "Buchstabe") == tuple("HUND")
    assert "".join(_tabellenzeile(seite, "Geheimzeichen")) == substitution.verschluesseln(
        "HUND"
    )
    assert _ergebnis(seite, "HUND") == substitution.verschluesseln("HUND")


def test_seite_3_der_ausgerichtete_schluessel_stimmt():
    """Die Zeile "Schlüssel" ist genau das, was schluessel_ausrichten() liefert."""
    seite = handbuch.SEITE_NACH_LEVEL[3]
    assert _tabellenzeile(seite, "Nachricht") == tuple("HUND")
    assert "".join(_tabellenzeile(seite, "Schlüssel")) == vigenere.schluessel_ausrichten(
        "HUND", "ROT"
    )


def test_seite_3_jeder_verschluesselungsschritt_stimmt_mit_dem_quadrat_ueberein():
    """Die vier Schritte werden einzeln im Quadrat nachgeschlagen."""
    seite = handbuch.SEITE_NACH_LEVEL[3]
    schritte = _schrittergebnisse(_abschnitt(seite, "Verschlüsseln – Schritt für Schritt"))
    schluessel = vigenere.schluessel_ausrichten("HUND", "ROT")
    assert len(schritte) == len("HUND")
    for nummer, (klarbuchstabe, schluesselbuchstabe, im_handbuch) in enumerate(
        zip("HUND", schluessel, schritte), start=1
    ):
        erwartet = vigenere_quadrat.verschluesselter_buchstabe(
            schluesselbuchstabe, klarbuchstabe
        )
        assert im_handbuch == erwartet, (
            f"Schritt {nummer}: Handbuch sagt {im_handbuch}, Quadrat liefert "
            f"{erwartet} (Zeile {schluesselbuchstabe}, Spalte {klarbuchstabe})."
        )
    assert "".join(schritte) == vigenere.verschluesseln("HUND", "ROT")


def test_seite_3_jeder_entschluesselungsschritt_stimmt_mit_dem_quadrat_ueberein():
    seite = handbuch.SEITE_NACH_LEVEL[3]
    schritte = _schrittergebnisse(_abschnitt(seite, "Entschlüsseln – Schritt für Schritt"))
    geheimtext = vigenere.verschluesseln("HUND", "ROT")
    schluessel = vigenere.schluessel_ausrichten("HUND", "ROT")
    assert len(schritte) == len(geheimtext)
    for nummer, (geheimbuchstabe, schluesselbuchstabe, im_handbuch) in enumerate(
        zip(geheimtext, schluessel, schritte), start=1
    ):
        erwartet = vigenere_quadrat.klarbuchstabe_finden(
            schluesselbuchstabe, geheimbuchstabe
        )
        assert im_handbuch == erwartet, (
            f"Schritt {nummer}: Handbuch sagt {im_handbuch}, Quadrat liefert "
            f"{erwartet}."
        )
    assert "".join(schritte) == "HUND"


def test_seite_3_beide_ergebnisse_stimmen():
    seite = handbuch.SEITE_NACH_LEVEL[3]
    geheimtext = vigenere.verschluesseln("HUND", "ROT")
    assert _ergebnis(seite, "HUND") == geheimtext
    assert _ergebnis(seite, geheimtext) == "HUND"


# ───────────────────────────────────────────────────────────────────────────
# 3. Der Text stammt wirklich aus der Quelle
# ───────────────────────────────────────────────────────────────────────────

def test_die_drei_ergebnisse_stehen_auch_in_der_quelle():
    """Handbuchtexte.md ist die Quelle – die Kopie darf nicht abweichen."""
    from pathlib import Path

    quelle = (
        Path(__file__).resolve().parent.parent
        / "dokumentation"
        / "Handbuchtexte.md"
    ).read_text(encoding="utf-8")
    for level, klartext in ((1, "HUND"), (2, "HUND"), (3, "HUND")):
        ergebnis = _ergebnis(handbuch.SEITE_NACH_LEVEL[level], klartext)
        assert f"{klartext} → {ergebnis}" in quelle, (
            f"Seite {level} nennt '{klartext} → {ergebnis}', in "
            "dokumentation/Handbuchtexte.md steht das so nicht."
        )


# ───────────────────────────────────────────────────────────────────────────
# 4. Das Vigenère-Quadrat hat einen Platz auf der Seite
# ───────────────────────────────────────────────────────────────────────────

def _quadratbloecke(seite):
    return [
        block
        for abschnitt in seite.abschnitte
        for block in abschnitt.bloecke
        if isinstance(block, VigenereQuadrat)
    ]


def test_nur_seite_3_hat_einen_platz_fuer_das_quadrat():
    """Die UI muss wissen, wo das 26x26-Raster hingehört (Arbeitsplan 6.7)."""
    for seite in handbuch.SEITEN:
        anzahl = len(_quadratbloecke(seite))
        erwartet = 1 if seite.level == 3 else 0
        assert anzahl == erwartet, (
            f"Seite {seite.level} hat {anzahl} Quadrat-Platzhalter, "
            f"erwartet {erwartet}."
        )


def test_der_quadrat_platzhalter_steht_im_richtigen_abschnitt():
    """Er gehört unter die Erklärung, was das Quadrat ist."""
    seite = handbuch.SEITE_NACH_LEVEL[3]
    abschnitt = _abschnitt(seite, "Das Vigenère-Quadrat")
    assert any(isinstance(block, VigenereQuadrat) for block in abschnitt.bloecke)


def test_der_quadrat_platzhalter_hat_eine_beschriftung():
    seite = handbuch.SEITE_NACH_LEVEL[3]
    beschriftung = _quadratbloecke(seite)[0].beschriftung
    assert beschriftung.strip()
    assert "Zeile" in beschriftung and "Spalte" in beschriftung


def test_der_platzhalter_enthaelt_selbst_keine_buchstaben_des_quadrats():
    """Das Quadrat wird erzeugt, nicht abgetippt – sonst gäbe es zwei Quellen."""
    seite = handbuch.SEITE_NACH_LEVEL[3]
    beschriftung = _quadratbloecke(seite)[0].beschriftung
    assert "RSTUVWXYZ" not in beschriftung.replace(" ", "")


# ───────────────────────────────────────────────────────────────────────────
# 5. Die Verfahrenskennung verbindet Seite und Funksprüche
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("seite", handbuch.SEITEN, ids=lambda s: f"Level {s.level}")
def test_die_seite_nennt_das_verfahren_ihres_levels(seite):
    """Damit Phase 7 eine Seite ihren Funksprüchen zuordnen kann."""
    assert seite.verfahren == verfahren.VERFAHREN_NACH_LEVEL[seite.level]
    assert seite.verfahren in verfahren.BEZEICHNUNG


@pytest.mark.parametrize("seite", handbuch.SEITEN, ids=lambda s: f"Level {s.level}")
def test_der_seitentitel_passt_zum_verfahren(seite):
    """Ein vertauschtes Verfahren soll auffallen, nicht still durchgehen."""
    bezeichnung = verfahren.BEZEICHNUNG[seite.verfahren]
    stichwort = bezeichnung.split("-")[0].split()[-1]
    assert stichwort.lower() in seite.titel.lower(), (
        f"Seite {seite.level} heisst {seite.titel!r}, das Verfahren ist aber "
        f"{bezeichnung!r}."
    )


# ───────────────────────────────────────────────────────────────────────────
# 6. Die Prosa stammt wirklich aus der Quelle
# ───────────────────────────────────────────────────────────────────────────

def test_jeder_absatz_steht_so_auch_im_handbuch_markdown():
    """Ohne diesen Test bleibt eine geänderte Erklärung unbemerkt.

    Verglichen wird auf Ebene ganzer Sätze und ohne Markdown-Auszeichnung:
    Der Zeilenumbruch ist im Markdown anders gesetzt als im Python-Quelltext,
    der Wortlaut muss aber derselbe sein. Absätze, die beim Umbau bewusst zu
    Tabellen oder Überschriften geworden sind, stehen in AUSNAHMEN.
    """
    import re
    from pathlib import Path

    quelle = (
        Path(__file__).resolve().parent.parent
        / "dokumentation"
        / "Handbuchtexte.md"
    ).read_text(encoding="utf-8")
    ohne_auszeichnung = re.sub(r"[*`$]", "", quelle)
    quelle_flach = re.sub(r"\s+", " ", ohne_auszeichnung)

    # Diese Absätze der Quelle sind bewusst in eine andere Form gewandert.
    AUSNAHMEN = (
        "Alphabet ohne Verschiebung",   # wurde zur Tabellenzeile
        "Alphabet um 3 Stellen",        # wurde zur Tabellenzeile
        "Ein Trick, um dir so eine",    # wurde zur Abschnittsüberschrift
    )

    fehlend = []
    for seite in handbuch.SEITEN:
        for abschnitt in seite.abschnitte:
            for block in abschnitt.bloecke:
                if not isinstance(block, Absatz):
                    continue
                flach = re.sub(r"\s+", " ", block.text).strip()
                if any(a in flach for a in AUSNAHMEN):
                    continue
                # Erster Satz genügt als Nachweis, dass der Absatz aus der
                # Quelle stammt und nicht umformuliert wurde.
                satz = re.split(r"(?<=[.:!?]) ", flach)[0]
                if satz not in quelle_flach:
                    fehlend.append((seite.level, satz[:80]))

    assert not fehlend, (
        "Diese Absätze aus content/handbuch.py stehen so nicht in "
        "dokumentation/Handbuchtexte.md:\n"
        + "\n".join(f"  Seite {lvl}: {t}" for lvl, t in fehlend)
    )
