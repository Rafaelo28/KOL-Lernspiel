"""Tests für game/zufallsquelle.py und die Rekonstruktion (Arbeitsplan 3.3).

Der Seed hat genau einen Zweck: Nach dem Experiment muss feststellbar sein,
welche Aufgaben eine bestimmte Person bekommen hat. Sonst lässt sich eine
lange Bearbeitungszeit nicht danach unterscheiden, ob jemand langsam war oder
den längsten Übungssatz erwischt hat.

Die Tests prüfen deshalb weniger die Zufälligkeit als die **Wiederholbarkeit**
– und zwar bis über Prozessgrenzen hinweg, weil die Auswertung später auf
einem anderen Rechner läuft als das Spiel.
"""

import random
import subprocess
import sys
from pathlib import Path

import pytest

from game.generator import Aufgabengenerator, wiederhole_uebungen
from game.zufallsquelle import SEED_OBERGRENZE, Zufallsquelle, neuer_seed

LEVEL = (1, 2, 3)
WURZEL = Path(__file__).resolve().parent.parent


# ───────────────────────────────────────────────────────────────────────────
# 1. Der Seed selbst
# ───────────────────────────────────────────────────────────────────────────

def test_ein_frischer_seed_liegt_im_erlaubten_bereich():
    for _ in range(200):
        seed = neuer_seed()
        assert isinstance(seed, int)
        assert 0 <= seed < SEED_OBERGRENZE


def test_frische_seeds_wiederholen_sich_nicht_staendig():
    """Zwei gleichzeitig gestartete Schulrechner sollen nicht dasselbe ziehen."""
    seeds = {neuer_seed() for _ in range(200)}
    assert len(seeds) > 190


def test_der_seed_haengt_nicht_am_globalen_zufallsgenerator():
    """Er kommt aus SystemRandom – ein random.seed() darf ihn nicht festlegen."""
    random.seed(1)
    erster = [neuer_seed() for _ in range(5)]
    random.seed(1)
    zweiter = [neuer_seed() for _ in range(5)]
    assert erster != zweiter


def test_der_seed_passt_in_eine_logzeile():
    """Er soll sich notfalls von Hand abtippen lassen."""
    assert len(str(SEED_OBERGRENZE - 1)) <= 10
    assert Zufallsquelle(SEED_OBERGRENZE - 1).protokollwert.isdigit()


@pytest.mark.parametrize(
    "unsinn", [-1, SEED_OBERGRENZE, SEED_OBERGRENZE + 1, 10**12]
)
def test_ein_seed_ausserhalb_des_bereichs_wird_abgewiesen(unsinn):
    with pytest.raises(ValueError):
        Zufallsquelle(unsinn)


@pytest.mark.parametrize("unsinn", ["4711", 4.0, None, True, [1]])
def test_ein_seed_vom_falschen_typ_wird_abgewiesen(unsinn):
    """Fehlerart-Konvention: falscher Typ ergibt TypeError."""
    with pytest.raises(TypeError):
        Zufallsquelle(unsinn)


# ───────────────────────────────────────────────────────────────────────────
# 2. Die Zufallsströme je Level
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
def test_derselbe_level_liefert_denselben_strom_weiter(level):
    """Sonst käme in einem Level immer wieder dieselbe Aufgabe."""
    quelle = Zufallsquelle(4711)
    assert quelle.fuer_level(level) is quelle.fuer_level(level)
    erste = quelle.fuer_level(level).random()
    zweite = quelle.fuer_level(level).random()
    assert erste != zweite


def test_die_level_ziehen_unabhaengig_voneinander():
    """Grund für getrennte Ströme: Level 3 soll nicht davon abhängen, wie
    viele Zusatzaufgaben in Level 1 angefallen sind."""
    quelle = Zufallsquelle(4711)
    for _ in range(20):
        quelle.fuer_level(1).random()
    vergleich = Zufallsquelle(4711)
    assert quelle.fuer_level(3).random() == vergleich.fuer_level(3).random()


@pytest.mark.parametrize("level", LEVEL)
def test_verschiedene_seeds_ergeben_verschiedene_stroeme(level):
    werte = {
        Zufallsquelle(seed).fuer_level(level).random() for seed in range(50)
    }
    assert len(werte) == 50


def test_verschiedene_level_ergeben_verschiedene_stroeme():
    quelle = Zufallsquelle(4711)
    werte = {quelle.fuer_level(level).random() for level in LEVEL}
    assert len(werte) == len(LEVEL)


# ───────────────────────────────────────────────────────────────────────────
# 3. Rekonstruktion – der eigentliche Zweck
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
@pytest.mark.parametrize("seed", [0, 1, 4711, SEED_OBERGRENZE - 1])
def test_derselbe_seed_ergibt_dieselben_aufgaben(level, seed):
    erste = wiederhole_uebungen(seed, level, 12)
    zweite = wiederhole_uebungen(seed, level, 12)
    assert [a._replace(kennung="") for a in erste] == [
        a._replace(kennung="") for a in zweite
    ]


@pytest.mark.parametrize("level", LEVEL)
def test_verschiedene_seeds_ergeben_verschiedene_aufgabenfolgen(level):
    """Sonst bekämen alle Kinder dieselbe Folge und könnten abschauen."""
    folgen = {
        tuple(a.anzeigetext for a in wiederhole_uebungen(seed, level, 8))
        for seed in range(30)
    }
    assert len(folgen) > 25


def test_die_aufgabe_eines_levels_haengt_nicht_am_verlauf_der_anderen():
    """Das ist der Grund für die getrennten Ströme.

    Wer in Level 1 fünf Zusatzaufgaben bekommen hat, soll in Level 3 trotzdem
    dieselben Aufgaben sehen wie jemand ohne Zusatzaufgaben – sonst müsste die
    Auswertung den ganzen Durchlauf nachspielen, um an Level 3 heranzukommen.
    """
    fleissig = Aufgabengenerator(Zufallsquelle(4711))
    for _ in range(5):
        fleissig.naechste_uebung(1, zusatzaufgabe=True)
    for _ in range(3):
        fleissig.naechste_uebung(2)

    langsam = Aufgabengenerator(Zufallsquelle(4711))

    assert (
        fleissig.naechste_uebung(3).anzeigetext
        == langsam.naechste_uebung(3).anzeigetext
    )


def test_die_rekonstruktion_findet_die_richtige_aufgabennummer():
    """Aus Seed und Aufgabennummer im Log folgt genau eine Aufgabe."""
    generator = Aufgabengenerator(Zufallsquelle(2024))
    im_spiel = [generator.naechste_uebung(2) for _ in range(6)]
    nachgebaut = wiederhole_uebungen(2024, 2, 6)
    for gespielt, rekonstruiert in zip(im_spiel, nachgebaut):
        assert gespielt.anzeigetext == rekonstruiert.anzeigetext
        assert gespielt.loesung == rekonstruiert.loesung
        assert gespielt.richtung == rekonstruiert.richtung
        assert gespielt.schluessel == rekonstruiert.schluessel


@pytest.mark.parametrize("level", LEVEL)
def test_die_rekonstruktion_funktioniert_auch_in_einem_anderen_prozess(level):
    """Die Auswertung läuft später auf einem anderen Rechner.

    Python würfelt seine Hash-Werte pro Prozess neu. Ein Zufallsstrom, der
    über ``hash()`` abgeleitet wäre, ergäbe dort andere Aufgaben – und der
    Seed im Log wäre wertlos. Deshalb wird hier wirklich ein zweiter Prozess
    gestartet, mit abweichendem PYTHONHASHSEED.
    """
    programm = (
        "from game.generator import wiederhole_uebungen;"
        f"print([a.anzeigetext for a in wiederhole_uebungen(4711, {level}, 5)])"
    )
    ergebnisse = set()
    for hashseed in ("0", "1", "12345"):
        lauf = subprocess.run(
            [sys.executable, "-c", programm],
            cwd=WURZEL,
            env={"PYTHONHASHSEED": hashseed, "PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
            check=True,
        )
        ergebnisse.add(lauf.stdout.strip())
    assert len(ergebnisse) == 1, (
        f"Der Zufallsstrom hängt vom Prozess ab: {ergebnisse}"
    )
    im_test = str([a.anzeigetext for a in wiederhole_uebungen(4711, level, 5)])
    assert ergebnisse == {im_test}


# ───────────────────────────────────────────────────────────────────────────
# 4. Zusammenspiel mit dem Generator
# ───────────────────────────────────────────────────────────────────────────

def test_der_generator_nimmt_eine_zufallsquelle_entgegen():
    generator = Aufgabengenerator(Zufallsquelle(1))
    aufgabe = generator.naechste_uebung(1)
    assert aufgabe.level == 1


def test_der_generator_nimmt_auch_eine_schlichte_random_instanz():
    """Für kleine Prüfungen genügt ein gemeinsamer Strom."""
    generator = Aufgabengenerator(random.Random(1))
    assert generator.naechste_uebung(2).level == 2


def test_ohne_angabe_zieht_der_generator_selbst_einen_seed():
    """Ein Spiel, das ohne Zufallsquelle gestartet wird, darf nicht abstürzen."""
    erster = Aufgabengenerator().naechste_uebung(1)
    zweiter = Aufgabengenerator().naechste_uebung(1)
    assert erster.level == zweiter.level == 1
