"""Tests für game/generator.py (Arbeitsplan 3.2).

Geprüft werden die vier Zusagen des Arbeitsplans – zufälliger Text, zufällige
Richtung, bei "entschlüsseln" wird der Geheimtext angezeigt, kein Text zweimal
hintereinander – und die Eigenschaft, an der Aufgabe 3.3 hängt: Derselbe Seed
muss denselben Ablauf ergeben, sonst lässt sich später nicht rekonstruieren,
wer welche Aufgaben bekommen hat.

Die Zufallstests laufen über viele Ziehungen mit festen Seeds. Ein einzelner
Durchlauf beweist bei einem Generator nichts.
"""

import random

import pytest

from content import charaktere, story, uebungen, verfahren
from crypto.normalize import LEERZEICHEN, normalisieren
from game.aufgabe import (
    ENTSCHLUESSELN,
    QUELLE_FUNKSPRUCH,
    QUELLE_UEBUNG,
    VERSCHLUESSELN,
    anwenden,
    pruefe_aufgabe,
)
from game.generator import Aufgabengenerator, aufgabe_aus_funkspruch

LEVEL = (1, 2, 3)


def _ziehungen(level, anzahl=200, seed=0):
    generator = Aufgabengenerator(random.Random(seed))
    return [generator.naechste_uebung(level) for _ in range(anzahl)]


# ───────────────────────────────────────────────────────────────────────────
# 1. Der Text kommt aus dem Pool des Levels
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
def test_der_klartext_stammt_immer_aus_dem_pool_des_levels(level):
    pool = set(uebungen.UEBUNGSTEXTE_NACH_LEVEL[level])
    for aufgabe in _ziehungen(level):
        klartext = (
            aufgabe.anzeigetext
            if aufgabe.richtung == VERSCHLUESSELN
            else aufgabe.loesung
        )
        assert klartext in pool, f"{klartext!r} steht nicht im Pool von Level {level}."


@pytest.mark.parametrize("level", LEVEL)
def test_auf_dauer_kommt_jeder_text_des_pools_dran(level):
    """Sonst bekämen manche Übungswörter nie eine Chance."""
    gezogen = set()
    for aufgabe in _ziehungen(level, anzahl=400):
        gezogen.add(
            aufgabe.anzeigetext
            if aufgabe.richtung == VERSCHLUESSELN
            else aufgabe.loesung
        )
    assert gezogen == set(uebungen.UEBUNGSTEXTE_NACH_LEVEL[level])


@pytest.mark.parametrize("level", LEVEL)
@pytest.mark.parametrize("seed", range(5))
def test_kein_text_kommt_zweimal_hintereinander(level, seed):
    """Ausdrückliche Forderung des Arbeitsplans (3.2).

    Zweimal dasselbe Wort hintereinander wirkt wie ein Fehler im Spiel und
    verschenkt eine der wenigen Übungen im Zeitfenster.
    """
    texte = []
    for aufgabe in _ziehungen(level, anzahl=200, seed=seed):
        texte.append(
            aufgabe.anzeigetext
            if aufgabe.richtung == VERSCHLUESSELN
            else aufgabe.loesung
        )
    wiederholungen = [
        (a, b) for a, b in zip(texte, texte[1:]) if a == b
    ]
    assert not wiederholungen, f"Direkt wiederholt: {wiederholungen[:3]}"


def test_die_level_kommen_sich_nicht_in_die_quere():
    """Der Merker für "kein Text zweimal" gilt je Level, nicht global."""
    generator = Aufgabengenerator(random.Random(3))
    texte = {level: [] for level in LEVEL}
    for _ in range(60):
        for level in LEVEL:
            aufgabe = generator.naechste_uebung(level)
            texte[level].append(
                aufgabe.anzeigetext
                if aufgabe.richtung == VERSCHLUESSELN
                else aufgabe.loesung
            )
    for level in LEVEL:
        folge = texte[level]
        assert not any(a == b for a, b in zip(folge, folge[1:]))


# ───────────────────────────────────────────────────────────────────────────
# 2. Richtung und Anzeigetext
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
def test_beide_richtungen_kommen_vor(level):
    """Das Handbuch verlangt pro Aufgabe einmal ver- und einmal entschlüsseln."""
    richtungen = {aufgabe.richtung for aufgabe in _ziehungen(level)}
    assert richtungen == {VERSCHLUESSELN, ENTSCHLUESSELN}


@pytest.mark.parametrize("level", LEVEL)
def test_beim_entschluesseln_wird_der_geheimtext_angezeigt(level):
    """3.2: "Text vorher selbst verschlüsseln und den anzeigen"."""
    pool = set(uebungen.UEBUNGSTEXTE_NACH_LEVEL[level])
    geprueft = 0
    for aufgabe in _ziehungen(level):
        if aufgabe.richtung != ENTSCHLUESSELN:
            continue
        geprueft += 1
        assert aufgabe.loesung in pool, "Die Lösung ist der Klartext."
        assert aufgabe.anzeigetext not in pool or aufgabe.anzeigetext == aufgabe.loesung
        # Der Anzeigetext muss wirklich der verschlüsselte Klartext sein.
        assert aufgabe.anzeigetext == anwenden(
            aufgabe.verfahren, VERSCHLUESSELN, aufgabe.loesung, aufgabe.schluessel
        )
    assert geprueft > 0


@pytest.mark.parametrize("level", LEVEL)
def test_beim_verschluesseln_wird_der_klartext_angezeigt(level):
    pool = set(uebungen.UEBUNGSTEXTE_NACH_LEVEL[level])
    for aufgabe in _ziehungen(level):
        if aufgabe.richtung == VERSCHLUESSELN:
            assert aufgabe.anzeigetext in pool


# ───────────────────────────────────────────────────────────────────────────
# 3. Die Schlüssel
# ───────────────────────────────────────────────────────────────────────────

def test_level_1_zieht_einen_caesar_schluessel_aus_dem_vorrat():
    schluessel = {aufgabe.schluessel for aufgabe in _ziehungen(1, anzahl=400)}
    assert schluessel <= set(uebungen.CAESAR_SCHLUESSEL)
    assert len(schluessel) > 5, "Der Schlüssel wechselt zu selten."


def test_level_2_hat_keinen_schluessel():
    """Bei der Substitution ist die Tabelle der Schlüssel, und die steht fest."""
    assert {aufgabe.schluessel for aufgabe in _ziehungen(2)} == {None}


def test_level_3_zieht_ein_schluesselwort_aus_dem_vorrat():
    """Immer dasselbe Wort würde die Aufgabe vorhersehbar machen."""
    woerter = {aufgabe.schluessel for aufgabe in _ziehungen(3, anzahl=200)}
    assert woerter == set(uebungen.VIGENERE_SCHLUESSELWOERTER)


# ───────────────────────────────────────────────────────────────────────────
# 4. Jede erzeugte Aufgabe ist in sich stimmig
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
def test_jede_erzeugte_aufgabe_ist_widerspruchsfrei(level):
    """Der Generator prüft sich selbst – hier noch einmal von aussen."""
    for aufgabe in _ziehungen(level):
        pruefe_aufgabe(aufgabe)
        assert aufgabe.level == level
        assert aufgabe.verfahren == verfahren.VERFAHREN_NACH_LEVEL[level]
        assert aufgabe.quelle == QUELLE_UEBUNG
        assert aufgabe.hat_teilaufgabe is False
        assert aufgabe.ist_geloest(aufgabe.loesung)
        assert normalisieren(aufgabe.anzeigetext) == aufgabe.anzeigetext
        assert aufgabe.laenge_in_buchstaben > 0


@pytest.mark.parametrize("level", LEVEL)
def test_die_kennungen_sind_eindeutig(level):
    """Sie landen im Log – doppelte Kennungen wären dort nicht zuzuordnen."""
    kennungen = [aufgabe.kennung for aufgabe in _ziehungen(level, anzahl=50)]
    assert len(set(kennungen)) == len(kennungen)
    assert all(kennung.startswith(f"uebung_l{level}_") for kennung in kennungen)


def test_zusatzaufgaben_sind_als_solche_markiert():
    """Arbeitsplan 5.5: Im Log müssen sich Pflicht- und Zusatzaufgabe trennen lassen."""
    generator = Aufgabengenerator(random.Random(11))
    assert generator.naechste_uebung(1).zusatzaufgabe is False
    assert generator.naechste_uebung(1, zusatzaufgabe=True).zusatzaufgabe is True


@pytest.mark.parametrize("level", [0, 4, -1, "1", None])
def test_ein_unbekanntes_level_wird_abgewiesen(level):
    with pytest.raises(ValueError):
        Aufgabengenerator(random.Random(0)).naechste_uebung(level)


# ───────────────────────────────────────────────────────────────────────────
# 5. Wiederholbarkeit – die Grundlage für Aufgabe 3.3
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
def test_derselbe_seed_ergibt_denselben_ablauf(level):
    """Ohne das lässt sich später nicht rekonstruieren, wer was bekommen hat."""
    erster = _ziehungen(level, anzahl=30, seed=1234)
    zweiter = _ziehungen(level, anzahl=30, seed=1234)
    assert [a._replace(kennung="") for a in erster] == [
        a._replace(kennung="") for a in zweiter
    ]


@pytest.mark.parametrize("level", LEVEL)
def test_verschiedene_seeds_ergeben_verschiedene_ablaeufe(level):
    """Sonst bekämen alle Kinder dieselbe Aufgabenfolge und könnten abschauen."""
    erster = [a.anzeigetext for a in _ziehungen(level, anzahl=30, seed=1)]
    zweiter = [a.anzeigetext for a in _ziehungen(level, anzahl=30, seed=2)]
    assert erster != zweiter


def test_der_generator_benutzt_nicht_den_globalen_zufall():
    """Sonst würde ein random.seed() irgendwo im Spiel den Ablauf verbiegen."""
    random.seed(999)
    erster = [a.anzeigetext for a in _ziehungen(1, anzahl=20, seed=5)]
    random.seed(1)
    zweiter = [a.anzeigetext for a in _ziehungen(1, anzahl=20, seed=5)]
    assert erster == zweiter


# ───────────────────────────────────────────────────────────────────────────
# 6. Die echten Funksprüche
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "funkspruch", story.FUNKSPRUECHE, ids=[f.kennung for f in story.FUNKSPRUECHE]
)
@pytest.mark.parametrize(
    "figur",
    charaktere.SPIELBARE_CHARAKTERE,
    ids=[f.kennung for f in charaktere.SPIELBARE_CHARAKTERE],
)
def test_jeder_funkspruch_wird_zu_einer_stimmigen_aufgabe(funkspruch, figur):
    aufgabe = aufgabe_aus_funkspruch(funkspruch, figur.initialen)
    pruefe_aufgabe(aufgabe)
    assert aufgabe.quelle == QUELLE_FUNKSPRUCH
    assert aufgabe.kennung == funkspruch.kennung
    assert aufgabe.ist_geloest(aufgabe.loesung)


def test_die_drei_langen_funksprueche_werden_zu_teilaufgaben():
    mit_rest = {
        f.kennung
        for f in story.FUNKSPRUECHE
        if aufgabe_aus_funkspruch(f, "VM").hat_teilaufgabe
    }
    assert mit_rest == {"bob_erste_antwort", "verfolger", "standort"}


@pytest.mark.parametrize(
    "funkspruch", story.FUNKSPRUECHE, ids=[f.kennung for f in story.FUNKSPRUECHE]
)
def test_der_rest_beginnt_nicht_mit_einem_leerzeichen(funkspruch):
    """Sonst stünde in der Anzeige eine Lücke, die dort nicht hingehört."""
    aufgabe = aufgabe_aus_funkspruch(funkspruch, "VM")
    assert not aufgabe.rest_der_loesung.startswith(LEERZEICHEN)


@pytest.mark.parametrize(
    "funkspruch", story.FUNKSPRUECHE, ids=[f.kennung for f in story.FUNKSPRUECHE]
)
def test_die_vollstaendige_loesung_ergibt_wieder_die_nachricht(funkspruch):
    """Lösung und Rest zusammen müssen die ganze Nachricht ergeben."""
    aufgabe = aufgabe_aus_funkspruch(funkspruch, "VM")
    klartext = funkspruch.klartext.format(initialen="VM")
    if aufgabe.richtung == ENTSCHLUESSELN:
        assert aufgabe.vollstaendige_loesung == klartext
    else:
        assert aufgabe.vollstaendige_loesung == anwenden(
            funkspruch.verfahren, VERSCHLUESSELN, klartext, funkspruch.schluessel
        )


def test_beim_senden_steht_die_loesung_nicht_im_anzeigetext():
    """Sonst wäre die Aufgabe durch Abschreiben lösbar."""
    for funkspruch in story.FUNKSPRUECHE:
        aufgabe = aufgabe_aus_funkspruch(funkspruch, "VM")
        if aufgabe.richtung == VERSCHLUESSELN:
            assert aufgabe.loesung not in aufgabe.anzeigetext
            assert aufgabe.vollstaendige_loesung not in aufgabe.anzeigetext


def test_die_teilaufgabe_haengt_nicht_von_der_figur_ab():
    """Dieselbe Arbeitsmenge für alle – Voraussetzung für die Auswertung."""
    for funkspruch in story.FUNKSPRUECHE:
        laengen = {
            aufgabe_aus_funkspruch(funkspruch, figur.initialen).laenge_in_buchstaben
            for figur in charaktere.SPIELBARE_CHARAKTERE
        }
        assert len(laengen) == 1, f"{funkspruch.kennung}: {sorted(laengen)}"


def test_der_generator_prueft_seine_eigenen_aufgaben(monkeypatch):
    """Die Selbstprüfung muss wirklich verdrahtet sein, nicht nur dastehen.

    Sie ändert im Normalfall nichts – der Generator baut ja stimmige Aufgaben.
    Ihr Wert liegt darin, dass eine spätere Änderung am Generator nicht
    unbemerkt eine Aufgabe ins Spiel lässt, deren Lösung nicht aus ihrem
    Anzeigetext folgt. Damit dieser Wert nicht nur behauptet ist, wird hier
    absichtlich Unsinn untergeschoben.
    """
    import game.generator as generatormodul

    monkeypatch.setattr(generatormodul, "anwenden", lambda *args, **kwargs: "FALSCH")
    with pytest.raises(ValueError) as fehler:
        Aufgabengenerator(random.Random(0)).naechste_uebung(1)
    assert "folgt" in str(fehler.value)


def test_auch_die_funkspruch_aufgaben_werden_geprueft(monkeypatch):
    import game.generator as generatormodul

    monkeypatch.setattr(generatormodul, "anwenden", lambda *args, **kwargs: "FALSCH")
    with pytest.raises(ValueError):
        aufgabe_aus_funkspruch(story.FUNKSPRUCH_BOB_ZWEITE_ANTWORT, "VM")


# ───────────────────────────────────────────────────────────────────────────
# 7. Beide Richtungen kommen in jedem Level wirklich dran
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
@pytest.mark.parametrize("seed", range(10))
def test_keine_richtung_kommt_zweimal_hintereinander(level, seed):
    """Konzept: "2 Aufgaben (1× verschlüsseln, 1× entschlüsseln)" pro Level.

    Frei gewürfelt käme in einem von vier Fällen zweimal dieselbe Richtung –
    dann hätten die Kinder das Entschlüsseln in diesem Level nie geübt, und
    das ist ein Lernziel aus Anhang A1.
    """
    richtungen = [a.richtung for a in _ziehungen(level, anzahl=100, seed=seed)]
    doppelt = [(a, b) for a, b in zip(richtungen, richtungen[1:]) if a == b]
    assert not doppelt, f"Richtung wiederholt sich: {doppelt[:3]}"


@pytest.mark.parametrize("level", LEVEL)
@pytest.mark.parametrize("seed", range(10))
def test_zwei_uebungen_ergeben_immer_beide_richtungen(level, seed):
    """Genau der Fall, den das Konzept beschreibt."""
    generator = Aufgabengenerator(random.Random(seed))
    richtungen = {generator.naechste_uebung(level).richtung for _ in range(2)}
    assert richtungen == {VERSCHLUESSELN, ENTSCHLUESSELN}


def test_die_richtung_wird_je_level_getrennt_gemerkt():
    """Ein Levelwechsel darf die Abwechslung im anderen Level nicht stören."""
    generator = Aufgabengenerator(random.Random(17))
    folgen = {level: [] for level in LEVEL}
    for _ in range(30):
        for level in LEVEL:
            folgen[level].append(generator.naechste_uebung(level).richtung)
    for level in LEVEL:
        f = folgen[level]
        assert not any(a == b for a, b in zip(f, f[1:]))


def test_die_richtung_ist_trotzdem_nicht_vorhersehbar():
    """Nur der Wechsel ist erzwungen, nicht welche Richtung zuerst kommt."""
    erste = {
        Aufgabengenerator(random.Random(seed)).naechste_uebung(1).richtung
        for seed in range(20)
    }
    assert erste == {VERSCHLUESSELN, ENTSCHLUESSELN}
