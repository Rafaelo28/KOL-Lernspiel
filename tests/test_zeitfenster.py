"""Tests für game/zeitfenster.py und den Level-Timer (Arbeitsplan 5.2).

Die drei Zeitfenster sind der Kern des Versuchsaufbaus: Die
Frontalunterrichts-Gruppe bekommt exakt dieselben 15, 20 und 25 Minuten. Wären
sie hier anders, liesse sich am Ende nicht sagen, ob eine Gruppe mehr gelernt
hat oder nur mehr Zeit hatte.

Getestet wird mit einer Uhr-Attrappe. Fünfzehn Minuten lassen sich sonst nur
durch fünfzehn Minuten Warten prüfen.
"""

import time

import pytest

from content import charaktere, story
from game import zeitfenster as zeitmodul
from game.bearbeitung import HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT
from game.spielstand import LEVEL, Spielstand
from game.zeitfenster import (
    DAUER_JE_LEVEL_MINUTEN,
    DAUER_JE_LEVEL_SEKUNDEN,
    Zeitfenster,
    fuer_level,
)
from game.zufallsquelle import Zufallsquelle


class Uhr:
    """Eine Uhr, die man vorstellen kann."""

    def __init__(self, start=0.0):
        self.jetzt = float(start)

    def __call__(self):
        return self.jetzt

    def weiter(self, sekunden):
        self.jetzt += sekunden


def _stand(uhr, seed=4711):
    return Spielstand(
        charaktere.VIC_MORENO, Zufallsquelle(seed), "P01", zeitgeber=uhr
    )


# ───────────────────────────────────────────────────────────────────────────
# 1. Die Zeiten selbst – sie sind Teil des Versuchsaufbaus
# ───────────────────────────────────────────────────────────────────────────

def test_die_zeitfenster_sind_genau_die_aus_dem_versuchsaufbau():
    """15 / 20 / 25 Minuten, wie bei der Kontrollgruppe (Anhang A4).

    Diese Zahlen sind keine Einstellung. Wer sie ändert, ändert den Vergleich
    zwischen den beiden Gruppen – und dieser Test soll dabei auffallen.
    """
    assert DAUER_JE_LEVEL_MINUTEN == {1: 15, 2: 20, 3: 25}


def test_sekunden_und_minuten_passen_zusammen():
    for level, minuten in DAUER_JE_LEVEL_MINUTEN.items():
        assert DAUER_JE_LEVEL_SEKUNDEN[level] == minuten * 60


def test_es_gibt_fuer_jedes_level_ein_zeitfenster():
    assert set(DAUER_JE_LEVEL_MINUTEN) == set(LEVEL)


def test_die_gesamtzeit_der_drei_level_ist_eine_stunde():
    """Der Zeitplan der Arbeit rechnet mit 60 Minuten für die drei Level."""
    assert sum(DAUER_JE_LEVEL_MINUTEN.values()) == 60


def test_die_fenster_werden_von_level_zu_level_laenger():
    """Die Verfahren werden aufwendiger, die Texte länger."""
    dauern = [DAUER_JE_LEVEL_MINUTEN[level] for level in sorted(LEVEL)]
    assert dauern == sorted(dauern)
    assert len(set(dauern)) == len(dauern)


@pytest.mark.parametrize("unsinn", [0, 4, -1, "1", None])
def test_fuer_ein_unbekanntes_level_gibt_es_kein_fenster(unsinn):
    with pytest.raises(ValueError):
        fuer_level(unsinn)


# ───────────────────────────────────────────────────────────────────────────
# 2. Der Ablauf eines Fensters
# ───────────────────────────────────────────────────────────────────────────

def test_ein_frisches_fenster_hat_die_volle_zeit():
    uhr = Uhr()
    fenster = Zeitfenster(900, zeitgeber=uhr)
    assert fenster.verbleibende_sekunden == 900
    assert fenster.verstrichene_sekunden == 0
    assert not fenster.ist_abgelaufen
    assert fenster.anteil_verbraucht == 0


def test_die_zeit_laeuft_ab():
    uhr = Uhr()
    fenster = Zeitfenster(900, zeitgeber=uhr)
    uhr.weiter(300)
    assert fenster.verstrichene_sekunden == 300
    assert fenster.verbleibende_sekunden == 600
    assert fenster.anteil_verbraucht == pytest.approx(1 / 3)
    assert not fenster.ist_abgelaufen


def test_genau_am_ende_ist_die_zeit_um():
    """Die Grenze gehört zum Ende, nicht zum Fenster."""
    uhr = Uhr()
    fenster = Zeitfenster(900, zeitgeber=uhr)
    uhr.weiter(899.9)
    assert not fenster.ist_abgelaufen
    uhr.weiter(0.1)
    assert fenster.ist_abgelaufen


def test_ueber_das_ende_hinaus_wird_nicht_ins_minus_gezaehlt():
    uhr = Uhr()
    fenster = Zeitfenster(900, zeitgeber=uhr)
    uhr.weiter(5000)
    assert fenster.verbleibende_sekunden == 0
    assert fenster.anteil_verbraucht == 1.0
    assert fenster.restzeit_text == "00:00"


@pytest.mark.parametrize(
    "verbleibend, text",
    [(900, "15:00"), (899.5, "15:00"), (61, "01:01"), (60, "01:00"),
     (59.4, "01:00"), (1, "00:01"), (0.4, "00:01"), (0, "00:00")],
)
def test_die_restzeit_wird_lesbar_angezeigt(verbleibend, text):
    """Aufgerundet: Solange Zeit bleibt, steht dort nicht "00:00"."""
    uhr = Uhr()
    fenster = Zeitfenster(900, zeitgeber=uhr)
    uhr.weiter(900 - verbleibend)
    assert fenster.restzeit_text == text


def test_solange_zeit_bleibt_steht_dort_nie_null():
    """Sonst zeigte die Anzeige das Ende an, während noch gerechnet werden darf."""
    uhr = Uhr()
    fenster = Zeitfenster(60, zeitgeber=uhr)
    for zehntel in range(600):
        uhr.jetzt = zehntel / 10
        if fenster.ist_abgelaufen:
            break
        assert fenster.restzeit_text != "00:00", f"bei {uhr.jetzt}s"


@pytest.mark.parametrize("unsinn", [0, -1, -900])
def test_eine_dauer_von_null_oder_weniger_wird_abgewiesen(unsinn):
    with pytest.raises(ValueError):
        Zeitfenster(unsinn)


@pytest.mark.parametrize("unsinn", ["900", None, [900], True])
def test_eine_dauer_vom_falschen_typ_wird_abgewiesen(unsinn):
    with pytest.raises(TypeError):
        Zeitfenster(unsinn)


def test_die_uhr_ist_standardmaessig_monoton():
    """time.time kann springen – ein Zeitserverabgleich mitten im Level würde
    das Fenster verfälschen, ein Sommerzeitwechsel erst recht."""
    fenster = Zeitfenster(900)
    assert fenster._zeitgeber is time.monotonic


def test_das_fenster_laesst_sich_nicht_anhalten():
    """Projektregel 1: Zusatzaufgaben verlängern ein Zeitfenster nie."""
    assert not hasattr(Zeitfenster(900), "anhalten")
    assert not hasattr(Zeitfenster(900), "pausieren")


# ───────────────────────────────────────────────────────────────────────────
# 3. Der Anschluss an den Spielstand
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
def test_mit_dem_level_beginnt_sein_zeitfenster(level):
    uhr = Uhr()
    stand = _stand(uhr)
    assert stand.zeitfenster is None
    stand.starte_level(level)
    assert stand.zeitfenster is not None
    assert stand.verbleibende_sekunden == DAUER_JE_LEVEL_SEKUNDEN[level]
    assert stand.restzeit_text == f"{DAUER_JE_LEVEL_MINUTEN[level]:02d}:00"


def test_ausserhalb_eines_levels_gibt_es_keine_restzeit():
    stand = _stand(Uhr())
    assert stand.restzeit_text == ""
    assert stand.verbleibende_sekunden == 0
    assert not stand.zeit_ist_um


def test_solange_zeit_bleibt_wird_nicht_gewechselt():
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    for minute in range(15):
        uhr.jetzt = minute * 60
        assert not stand.pruefe_zeitfenster()
        assert stand.aktuelles_level == 1


def test_bei_ablauf_wird_automatisch_weitergeschaltet():
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    assert stand.zeit_ist_um
    assert stand.pruefe_zeitfenster() is True
    assert stand.aktuelles_level == 2


def test_das_neue_level_bekommt_ein_frisches_fenster():
    """Sonst würde die Verspätung aus Level 1 in Level 2 weiterlaufen."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] + 120)
    stand.pruefe_zeitfenster()
    assert stand.verbleibende_sekunden == DAUER_JE_LEVEL_SEKUNDEN[2]


def test_nach_level_3_endet_das_spiel():
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(3)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[3])
    assert stand.pruefe_zeitfenster() is True
    assert stand.aktuelles_level is None
    assert stand.zeitfenster is None
    assert stand.restzeit_text == ""


def test_der_ablauf_schliesst_eine_offene_aufgabe_ab():
    """Projektregel 1: weiter, egal was offen ist – aber nichts geht verloren."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    aufgabe = stand.naechste_uebung()
    stand.versuchen("XXXXX")
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    stand.pruefe_zeitfenster()
    assert stand.aktuelle_aufgabe is None
    assert len(stand.erledigte_aufgaben) == 1
    bearbeitung = stand.erledigte_aufgaben[0]
    assert bearbeitung.aufgabe is aufgabe
    assert bearbeitung.versuche == 1
    assert bearbeitung.loesung_angezeigt


def test_mehrfaches_pruefen_schaltet_nicht_mehrfach_weiter():
    """Die Oberfläche ruft das im Sekundentakt auf."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    assert stand.pruefe_zeitfenster() is True
    for _ in range(10):
        assert stand.pruefe_zeitfenster() is False
    assert stand.aktuelles_level == 2


def test_ohne_laufendes_level_passiert_beim_pruefen_nichts():
    stand = _stand(Uhr())
    assert stand.pruefe_zeitfenster() is False


# ───────────────────────────────────────────────────────────────────────────
# 4. Nichts verlängert das Fenster (Projektregel 1)
# ───────────────────────────────────────────────────────────────────────────

def test_zusatzaufgaben_verlaengern_das_fenster_nicht():
    from game.zusatzaufgaben import HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL as GRENZE

    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    for _ in range(GRENZE):
        aufgabe = stand.naechste_uebung(zusatzaufgabe=True)
        stand.versuchen(aufgabe.loesung)
        stand.aufgabe_abschliessen()
        uhr.weiter(60)
    assert stand.verbleibende_sekunden == DAUER_JE_LEVEL_SEKUNDEN[1] - GRENZE * 60


def test_der_weiterrechnen_knopf_haelt_die_uhr_nicht_an():
    """Die "zwanzig Minuten später" im Erzähltext sind reine Fiktion."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    aufgabe = stand.stelle_funkspruch(story.FUNKSPRUCH_BOB_ERSTE_ANTWORT)
    uhr.weiter(120)
    vorher = stand.verbleibende_sekunden
    stand.versuchen(aufgabe.loesung)
    stand.weiterrechnen()
    assert stand.verbleibende_sekunden == vorher


def test_fehlversuche_verlaengern_das_fenster_nicht():
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    stand.naechste_uebung()
    for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
        stand.versuchen("X" * (nummer + 2))
        uhr.weiter(30)
    assert stand.verbleibende_sekunden == DAUER_JE_LEVEL_SEKUNDEN[1] - 90


def test_die_uhr_laeuft_auch_zwischen_den_aufgaben_weiter():
    """Gemessen wird das Zeitfenster, nicht die Summe der Bearbeitungszeiten."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(2)
    uhr.weiter(400)
    assert stand.verbleibende_sekunden == DAUER_JE_LEVEL_SEKUNDEN[2] - 400


# ───────────────────────────────────────────────────────────────────────────
# 5. Ein Durchlauf, in dem jedes Level an der Zeit endet
# ───────────────────────────────────────────────────────────────────────────

def test_ein_durchlauf_endet_auch_wenn_ueberall_die_zeit_ablaeuft():
    """Der ungünstigste Fall: niemand wird fertig, das Spiel läuft trotzdem durch."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    for level in LEVEL:
        assert stand.aktuelles_level == level
        stand.naechste_uebung()
        stand.versuchen("XXXXX")
        uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[level])
        stand.pruefe_zeitfenster()
    assert stand.aktuelles_level is None
    assert stand.ist_durchgespielt
    assert len(stand.erledigte_aufgaben) == len(LEVEL)
    assert all(b.loesung_angezeigt for b in stand.erledigte_aufgaben)


def test_die_gesamtdauer_eines_solchen_durchlaufs_ist_genau_eine_stunde():
    """Kein Level kann sich Zeit vom nächsten borgen."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    beginn = uhr.jetzt
    for level in LEVEL:
        uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[level])
        stand.pruefe_zeitfenster()
    assert uhr.jetzt - beginn == 60 * 60
