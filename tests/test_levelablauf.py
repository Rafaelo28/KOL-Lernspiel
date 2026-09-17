"""Tests für game/levelablauf.py (Arbeitsplan Phase 7).

Hier steht, was in einem Level als Nächstes drankommt. Zwei Dinge sind für
den Versuchsaufbau wichtig:

* **Die Reihenfolge** aus dem Konzept: zwei Übungen, dann die Funksprüche.
* **Die Vorrang-Regel:** Wird die Zeit knapp, fallen Übungen aus, damit die
  Funksprüche noch drankommen – sie tragen die Geschichte. Kein Zeitfenster
  wird dabei länger (Projektregel 1).

Geprüft wird beides doppelt: an der reinen Funktion und am Spielstand, der
sie mit den eigenen Zahlen füttert.
"""

from content import charaktere, story
from game import zusatzaufgaben
from game.levelablauf import (
    BASIS_UEBUNGEN_JE_LEVEL,
    SCHRITT_FUNKSPRUCH,
    SCHRITT_LEVELENDE,
    SCHRITT_UEBUNG,
    SCHRITT_ZUSATZAUFGABE,
    naechster_schritt,
)
from game.spielstand import Spielstand
from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN
from game.zufallsquelle import Zufallsquelle

FIGUR = charaktere.VIC_MORENO
LEVEL_1 = story.FUNKSPRUECHE_NACH_LEVEL[1]


class Uhr:
    """Eine Uhr, die nur weitergeht, wenn ein Test sie weiterstellt."""

    def __init__(self):
        self.jetzt = 0.0

    def __call__(self):
        return self.jetzt

    def weiter(self, sekunden):
        self.jetzt += sekunden


def _stand(uhr=None, seed=4711):
    stand = Spielstand(FIGUR, Zufallsquelle(seed), "P01", zeitgeber=uhr)
    stand.starte_level(1)
    return stand


#: So lange dauert eine Aufgabe in den Tests, wenn nichts anderes dasteht:
#: lang genug, dass sie nicht als "schnell gelöst" gilt und eine Zusatzaufgabe
#: auslöst, aber kurz genug, dass die Levelzeit reicht.
NORMALTEMPO_SEKUNDEN = 90.0


def _loese(stand, sekunden=NORMALTEMPO_SEKUNDEN, uhr=None):
    """Löst die laufende Aufgabe richtig und schliesst sie ab – nach ``sekunden``."""
    if uhr is not None:
        uhr.weiter(sekunden)
    aufgabe = stand.aktuelle_aufgabe
    stand.versuchen(aufgabe.loesung)
    if stand.aktuelle_bearbeitung.darf_weiterrechnen:
        stand.weiterrechnen()
    stand.aufgabe_abschliessen()


def _knappe_zeit(funksprueche):
    """Eine Restzeit, die für die Funksprüche reicht, für eine Übung davor aber nicht mehr."""
    return zusatzaufgaben.erwartete_dauer_funksprueche(funksprueche) + zusatzaufgaben.MINDESTRESTZEIT_SEKUNDEN


# ───────────────────────────────────────────────────────────────────────────
# 1. Die Reihenfolge im Level
# ───────────────────────────────────────────────────────────────────────────

def test_zuerst_kommen_die_uebungen():
    for erledigt in range(BASIS_UEBUNGEN_JE_LEVEL):
        assert naechster_schritt(erledigt, LEVEL_1, 900).art == SCHRITT_UEBUNG


def test_nach_den_uebungen_kommen_die_funksprueche_der_reihe_nach():
    schritt = naechster_schritt(BASIS_UEBUNGEN_JE_LEVEL, LEVEL_1, 900)
    assert (schritt.art, schritt.funkspruch) == (SCHRITT_FUNKSPRUCH, LEVEL_1[0])
    weiter = naechster_schritt(BASIS_UEBUNGEN_JE_LEVEL, LEVEL_1[1:], 900)
    assert weiter.funkspruch is LEVEL_1[1]


def test_ist_nichts_mehr_offen_endet_das_level():
    schritt = naechster_schritt(BASIS_UEBUNGEN_JE_LEVEL, (), 900)
    assert (schritt.art, schritt.funkspruch) == (SCHRITT_LEVELENDE, None)


def test_eine_faellige_zusatzaufgabe_kommt_nach_den_uebungen():
    schritt = naechster_schritt(BASIS_UEBUNGEN_JE_LEVEL, LEVEL_1, 900, zusatzaufgabe_faellig=True)
    assert schritt.art == SCHRITT_ZUSATZAUFGABE


def test_die_basis_uebungen_gehen_einer_zusatzaufgabe_vor():
    """Sonst käme die Extraaufgabe, bevor beide Richtungen geübt wurden."""
    schritt = naechster_schritt(0, LEVEL_1, 900, zusatzaufgabe_faellig=True)
    assert schritt.art == SCHRITT_UEBUNG


# ───────────────────────────────────────────────────────────────────────────
# 2. Die Vorrang-Regel
# ───────────────────────────────────────────────────────────────────────────

def test_wird_die_zeit_knapp_kommt_der_funkspruch_statt_der_uebung():
    """Die Geschichte darf nicht daran scheitern, dass davor noch geübt wurde."""
    schritt = naechster_schritt(0, LEVEL_1, _knappe_zeit(LEVEL_1))
    assert (schritt.art, schritt.funkspruch) == (SCHRITT_FUNKSPRUCH, LEVEL_1[0])


def test_bei_knapper_zeit_faellt_auch_die_zusatzaufgabe_aus():
    schritt = naechster_schritt(BASIS_UEBUNGEN_JE_LEVEL, LEVEL_1, _knappe_zeit(LEVEL_1),
                                zusatzaufgabe_faellig=True)
    assert schritt.art == SCHRITT_FUNKSPRUCH


def test_reicht_die_zeit_knapp_doch_kommt_die_uebung():
    """Die Grenze gilt einschliesslich – sonst fiele eine Übung aus, für die es reicht."""
    gerade_genug = (_knappe_zeit(LEVEL_1)
                    + zusatzaufgaben.erwartete_dauer(zusatzaufgaben.laengste_uebung()))
    assert naechster_schritt(0, LEVEL_1, gerade_genug).art == SCHRITT_UEBUNG
    assert naechster_schritt(0, LEVEL_1, gerade_genug - 1).art == SCHRITT_FUNKSPRUCH


def test_ohne_funkspruch_und_ohne_zeit_endet_das_level():
    """Auch wenn noch Übungen fehlten: Für sie ist keine Zeit mehr."""
    assert naechster_schritt(0, (), 10).art == SCHRITT_LEVELENDE


def test_je_mehr_funksprueche_offen_sind_desto_frueher_greift_der_vorrang():
    zeit = _knappe_zeit(LEVEL_1) + zusatzaufgaben.erwartete_dauer(zusatzaufgaben.laengste_uebung())
    assert naechster_schritt(0, LEVEL_1, zeit).art == SCHRITT_UEBUNG
    assert naechster_schritt(0, LEVEL_1[:1], zeit).art == SCHRITT_UEBUNG, "Weniger offen, mehr Luft."
    mehr = LEVEL_1 + story.FUNKSPRUECHE_NACH_LEVEL[3]
    assert naechster_schritt(0, mehr, zeit).art == SCHRITT_FUNKSPRUCH


# ───────────────────────────────────────────────────────────────────────────
# 3. Am Spielstand
# ───────────────────────────────────────────────────────────────────────────

def test_der_spielstand_fuehrt_durch_das_ganze_level():
    """Zwei Übungen, dann beide Funksprüche von Level 1, dann ist das Level durch."""
    uhr = Uhr()
    stand = _stand(uhr)
    gesehen = []
    for _ in range(6):
        schritt = stand.naechster_schritt
        gesehen.append(schritt.art if schritt.funkspruch is None else schritt.funkspruch.kennung)
        if schritt.art == SCHRITT_LEVELENDE:
            break
        if schritt.art == SCHRITT_FUNKSPRUCH:
            stand.stelle_funkspruch(schritt.funkspruch)
        else:
            stand.naechste_uebung(zusatzaufgabe=schritt.art == SCHRITT_ZUSATZAUFGABE)
        _loese(stand, uhr=uhr)
    assert gesehen == ["uebung", "uebung", "erster_ruf", "bob_erste_antwort", "levelende"]


def test_uebungen_im_level_zaehlt_die_zusatzaufgaben_nicht_mit():
    """Sonst käme nach einer Extraaufgabe keine zweite Basis-Übung mehr."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.naechste_uebung()
    _loese(stand, uhr=uhr)
    stand.naechste_uebung(zusatzaufgabe=True)
    _loese(stand, uhr=uhr)
    assert stand.uebungen_im_level() == 1
    assert stand.zusatzaufgaben_im_level() == 1
    assert stand.naechster_schritt.art == SCHRITT_UEBUNG


def test_wer_schnell_ist_bekommt_eine_zusatzaufgabe():
    uhr = Uhr()
    stand = _stand(uhr)
    for _ in range(BASIS_UEBUNGEN_JE_LEVEL):
        stand.naechste_uebung()
        _loese(stand, sekunden=1, uhr=uhr)
    assert stand.zusatzaufgabe_faellig
    assert stand.naechster_schritt.art == SCHRITT_ZUSATZAUFGABE


def test_bei_knapper_zeit_ist_am_spielstand_keine_zusatzaufgabe_mehr_faellig():
    """Auch wer schnell war, bekommt keine Extraaufgabe mehr, wenn die Funksprüche warten."""
    uhr = Uhr()
    stand = _stand(uhr)
    for _ in range(BASIS_UEBUNGEN_JE_LEVEL):
        stand.naechste_uebung()
        _loese(stand, sekunden=1, uhr=uhr)
    assert stand.zusatzaufgabe_faellig
    uhr.weiter(stand.verbleibende_sekunden - _knappe_zeit(LEVEL_1))
    assert not stand.zusatzaufgabe_faellig
    assert stand.naechster_schritt.art == SCHRITT_FUNKSPRUCH


def test_wer_troedelt_kommt_trotzdem_zum_funkspruch():
    """Der Fall aus dem Arbeitsplan: lange an den Übungen, aber die Geschichte läuft weiter."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.naechste_uebung()
    _loese(stand, sekunden=DAUER_JE_LEVEL_SEKUNDEN[1] - _knappe_zeit(LEVEL_1), uhr=uhr)
    assert stand.uebungen_im_level() == 1, "Die zweite Basis-Übung steht noch aus …"
    schritt = stand.naechster_schritt
    assert (schritt.art, schritt.funkspruch) == (SCHRITT_FUNKSPRUCH, LEVEL_1[0]), (
        "… kommt aber nicht mehr, damit die Funksprüche noch drankommen."
    )


def test_ein_gestellter_funkspruch_ist_nicht_mehr_offen():
    uhr = Uhr()
    stand = _stand(uhr)
    assert not stand.wurde_gestellt(LEVEL_1[0])
    stand.stelle_funkspruch(LEVEL_1[0])
    assert stand.wurde_gestellt(LEVEL_1[0])
    assert not stand.wurde_gestellt(LEVEL_1[1])
    _loese(stand, uhr=uhr)
    assert stand.offene_funksprueche == (LEVEL_1[1],)


def test_ausserhalb_eines_levels_gibt_es_nichts_zu_tun():
    stand = Spielstand(FIGUR, Zufallsquelle(1), "P01")
    assert stand.naechster_schritt.art == SCHRITT_LEVELENDE
