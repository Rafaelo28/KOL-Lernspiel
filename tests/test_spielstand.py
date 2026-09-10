"""Tests für game/spielstand.py (Arbeitsplan 5.1).

Der Spielstand ist die Stelle, an der die Regeln des Ablaufs stehen. Zwei
davon sind für den Versuchsaufbau kritisch:

* **Projektregel 1** – läuft das Zeitfenster ab, wird gewechselt, egal was
  offen ist. Die offene Aufgabe darf dabei nicht verlorengehen, sonst kann die
  Auswertung "nicht bearbeitet" nicht von "Zeit war um" unterscheiden.
* **Projektregel 7** – im Log steht ein Pseudonym, nie ein Klarname.

Dazu die Zusicherung, dass jede gestellte Aufgabe am Ende genau einmal in der
Liste der erledigten steht – das ist die Grundlage des CSV-Logs aus 5.5.
"""

import pytest

from content import charaktere, story, verfahren
from game.aufgabe import QUELLE_FUNKSPRUCH, QUELLE_UEBUNG
from game.bearbeitung import HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT, Bearbeitung
from game.spielstand import (
    LEVEL,
    LEVELENDE_LAEUFT,
    LEVELENDE_VORZEITIG,
    LEVELENDE_ZEITABLAUF,
    Spielstand,
    ZeitIstUm,
)
from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN
from game.zufallsquelle import SEED_OBERGRENZE, Zufallsquelle

FIGUR = charaktere.VIC_MORENO


def _stand(seed=4711, figur=FIGUR, pseudonym="P01"):
    return Spielstand(figur, Zufallsquelle(seed), pseudonym)


def _loese(stand):
    """Löst die laufende Aufgabe richtig und schliesst sie ab."""
    aufgabe = stand.aktuelle_aufgabe
    stand.versuchen(aufgabe.loesung)
    if stand.aktuelle_bearbeitung.darf_weiterrechnen:
        stand.weiterrechnen()
    stand.aufgabe_abschliessen()


# ───────────────────────────────────────────────────────────────────────────
# 1. Der Anfangszustand
# ───────────────────────────────────────────────────────────────────────────

def test_ein_frischer_spielstand_hat_noch_nichts_laufen():
    stand = _stand()
    assert stand.aktuelles_level is None
    assert stand.aktuelles_verfahren is None
    assert stand.aktuelle_aufgabe is None
    assert stand.aktuelle_bearbeitung is None
    assert stand.versuche == 0
    assert stand.erledigte_aufgaben == ()
    assert not stand.ist_durchgespielt


def test_die_figur_gehoert_zum_spielstand():
    """Ihre Initialen unterschreiben jeden gesendeten Funkspruch."""
    stand = _stand(figur=charaktere.THEO_LAMBERT)
    assert stand.figur is charaktere.THEO_LAMBERT


def test_ohne_figur_geht_es_nicht():
    with pytest.raises(ValueError) as fehler:
        Spielstand(None)
    assert "Figur" in str(fehler.value)


def test_der_seed_gehoert_zum_durchlauf():
    """Er wird einmal je Durchlauf gezogen und ins Log geschrieben (3.3)."""
    quelle = Zufallsquelle(1234)
    assert _stand().zufallsquelle is not None
    assert Spielstand(FIGUR, quelle).zufallsquelle is quelle


def test_ohne_angabe_zieht_der_spielstand_selbst_einen_seed():
    erster = Spielstand(FIGUR)
    zweiter = Spielstand(FIGUR)
    assert erster.zufallsquelle.seed != zweiter.zufallsquelle.seed


# ───────────────────────────────────────────────────────────────────────────
# 2. Datenschutz: Pseudonym statt Klarname
# ───────────────────────────────────────────────────────────────────────────

def test_das_pseudonym_laesst_sich_vorgeben():
    """Die Lehrkraft ordnet die IDs getrennt zu (Projektregel 7)."""
    assert _stand(pseudonym="Gruppe-A-03").pseudonym == "Gruppe-A-03"


def test_ohne_vorgabe_entsteht_ein_pseudonym_ohne_klarnamen():
    stand = Spielstand(charaktere.ELENA_DUARTE)
    assert stand.pseudonym
    assert charaktere.ELENA_DUARTE.name.lower() not in stand.pseudonym.lower()
    assert "elena" not in stand.pseudonym.lower()
    assert "duarte" not in stand.pseudonym.lower()


def test_das_erzeugte_pseudonym_ist_kurz_und_maschinenlesbar():
    """Es landet in einer CSV-Spalte und in einem Dateinamen."""
    for seed in (0, 1, SEED_OBERGRENZE - 1):
        stand = Spielstand(FIGUR, Zufallsquelle(seed))
        assert stand.pseudonym.isascii()
        assert stand.pseudonym.isalnum()
        assert 2 <= len(stand.pseudonym) <= 12


@pytest.mark.parametrize(
    "seed_a, seed_b",
    [
        (999999999, 999990000),   # gleicher Anfang – früher beide "P99999"
        (123456789, 123450000),
        (100000, 1000000),
        (0, SEED_OBERGRENZE - 1),
        (1, 10),
    ],
)
def test_verschiedene_seeds_ergeben_verschiedene_pseudonyme(seed_a, seed_b):
    """Sonst liefen zwei Durchläufe im Log unter derselben ID."""
    a = Spielstand(FIGUR, Zufallsquelle(seed_a)).pseudonym
    b = Spielstand(FIGUR, Zufallsquelle(seed_b)).pseudonym
    assert a != b


def test_viele_seeds_ergeben_lauter_verschiedene_pseudonyme():
    seeds = list(range(0, SEED_OBERGRENZE, SEED_OBERGRENZE // 997))
    pseudonyme = {Spielstand(FIGUR, Zufallsquelle(s)).pseudonym for s in seeds}
    assert len(pseudonyme) == len(seeds)


@pytest.mark.parametrize("seed", [0, 7, 4711, 999990000, SEED_OBERGRENZE - 1])
def test_aus_dem_erzeugten_pseudonym_geht_der_seed_hervor(seed):
    """Die Ziffern sind der Seed – nichts wird abgeschnitten."""
    assert int(Spielstand(FIGUR, Zufallsquelle(seed)).pseudonym[1:]) == seed


@pytest.mark.parametrize("leer", ["", "   ", "\t\n", None])
def test_ein_leeres_pseudonym_gilt_als_keins(leer):
    """Sonst stünde im Log eine Zelle aus lauter Leerzeichen."""
    stand = Spielstand(FIGUR, Zufallsquelle(4711), leer)
    assert stand.pseudonym == Spielstand(FIGUR, Zufallsquelle(4711)).pseudonym
    assert stand.pseudonym.strip() == stand.pseudonym


def test_ein_vorgegebenes_pseudonym_verliert_nur_den_rand():
    assert _stand(pseudonym="  G-07 ").pseudonym == "G-07"


# ───────────────────────────────────────────────────────────────────────────
# 3. Level
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
def test_ein_level_laesst_sich_starten(level):
    stand = _stand()
    stand.starte_level(level)
    assert stand.aktuelles_level == level
    assert stand.aktuelles_verfahren == verfahren.VERFAHREN_NACH_LEVEL[level]


@pytest.mark.parametrize("unsinn", [0, 4, -1, "1", None])
def test_ein_unbekanntes_level_wird_abgewiesen(unsinn):
    with pytest.raises(ValueError):
        _stand().starte_level(unsinn)


def test_ohne_level_gibt_es_keine_aufgabe():
    stand = _stand()
    with pytest.raises(ValueError) as fehler:
        stand.naechste_uebung()
    assert "Level" in str(fehler.value)


def test_die_level_folgen_aufeinander():
    stand = _stand()
    stand.starte_level(1)
    assert stand.naechstes_level() == 2
    assert stand.naechstes_level() == 3
    assert stand.naechstes_level() is None
    assert stand.aktuelles_level is None


def test_ohne_laufendes_level_gibt_es_kein_naechstes():
    with pytest.raises(ValueError):
        _stand().naechstes_level()


# ───────────────────────────────────────────────────────────────────────────
# 4. Aufgaben stellen und abschliessen
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
def test_eine_uebung_passt_zum_laufenden_level(level):
    stand = _stand()
    stand.starte_level(level)
    aufgabe = stand.naechste_uebung()
    assert aufgabe.level == level
    assert aufgabe.quelle == QUELLE_UEBUNG
    assert stand.aktuelle_aufgabe is aufgabe
    assert isinstance(stand.aktuelle_bearbeitung, Bearbeitung)


def test_zwei_aufgaben_gleichzeitig_gibt_es_nicht():
    """Sonst fiele die erste aus dem Log heraus."""
    stand = _stand()
    stand.starte_level(1)
    stand.naechste_uebung()
    with pytest.raises(ValueError) as fehler:
        stand.naechste_uebung()
    assert "läuft noch" in str(fehler.value)


def test_ohne_laufende_aufgabe_gibt_es_nichts_zu_versuchen():
    stand = _stand()
    stand.starte_level(1)
    with pytest.raises(ValueError):
        stand.versuchen("XXXX")
    with pytest.raises(ValueError):
        stand.weiterrechnen()
    with pytest.raises(ValueError):
        stand.aufgabe_abschliessen()


def test_der_versuchszaehler_gehoert_zum_zustand():
    """Arbeitsplan 5.1 nennt ihn ausdrücklich."""
    stand = _stand()
    stand.starte_level(1)
    stand.naechste_uebung()
    assert stand.versuche == 0
    stand.versuchen("XXXXX")
    assert stand.versuche == 1
    stand.aufgabe_abschliessen()
    assert stand.versuche == 0


def test_eine_abgeschlossene_aufgabe_landet_bei_den_erledigten():
    stand = _stand()
    stand.starte_level(1)
    aufgabe = stand.naechste_uebung()
    _loese(stand)
    assert stand.aktuelle_aufgabe is None
    assert [b.aufgabe for b in stand.erledigte_aufgaben] == [aufgabe]


def test_jede_gestellte_aufgabe_steht_genau_einmal_im_log():
    """Grundlage des CSV-Logs aus 5.5."""
    stand = _stand()
    gestellt = []
    stand.starte_level(LEVEL[0])
    for level in LEVEL:
        for _ in range(3):
            gestellt.append(stand.naechste_uebung())
            _loese(stand)
        for funkspruch in story.FUNKSPRUECHE_NACH_LEVEL[level]:
            gestellt.append(stand.stelle_funkspruch(funkspruch))
            _loese(stand)
        stand.naechstes_level()
    kennungen = [b.aufgabe.kennung for b in stand.erledigte_aufgaben]
    assert kennungen == [a.kennung for a in gestellt]
    assert len(kennungen) == len(set(kennungen))


def test_die_erledigten_lassen_sich_nach_level_abfragen():
    stand = _stand()
    stand.starte_level(LEVEL[0])
    for level in LEVEL:
        for _ in range(2):
            stand.naechste_uebung()
            _loese(stand)
        stand.naechstes_level()
    for level in LEVEL:
        im_level = stand.erledigte_aufgaben_im_level(level)
        assert len(im_level) == 2
        assert all(b.aufgabe.level == level for b in im_level)


def test_die_liste_der_erledigten_laesst_sich_nicht_von_aussen_veraendern():
    """Sie ist die Grundlage des Logs – niemand soll darin herumschreiben."""
    stand = _stand()
    stand.starte_level(1)
    stand.naechste_uebung()
    _loese(stand)
    assert isinstance(stand.erledigte_aufgaben, tuple)


# ───────────────────────────────────────────────────────────────────────────
# 5. Funksprüche
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "funkspruch", story.FUNKSPRUECHE, ids=[f.kennung for f in story.FUNKSPRUECHE]
)
def test_jeder_funkspruch_laesst_sich_in_seinem_level_stellen(funkspruch):
    stand = _stand()
    stand.starte_level(funkspruch.level)
    aufgabe = stand.stelle_funkspruch(funkspruch)
    assert aufgabe.quelle == QUELLE_FUNKSPRUCH
    assert aufgabe.kennung == funkspruch.kennung
    stand.versuchen(aufgabe.loesung)
    assert stand.aktuelle_bearbeitung.geloest


@pytest.mark.parametrize(
    "funkspruch", story.FUNKSPRUECHE, ids=[f.kennung for f in story.FUNKSPRUECHE]
)
def test_ein_funkspruch_aus_dem_falschen_level_wird_abgewiesen(funkspruch):
    """Sonst käme Bobs Antwort mitten in Level 2."""
    falsches_level = next(l for l in LEVEL if l != funkspruch.level)
    stand = _stand()
    stand.starte_level(falsches_level)
    with pytest.raises(ValueError) as fehler:
        stand.stelle_funkspruch(funkspruch)
    assert str(funkspruch.level) in str(fehler.value)


@pytest.mark.parametrize(
    "figur",
    charaktere.SPIELBARE_CHARAKTERE,
    ids=[f.kennung for f in charaktere.SPIELBARE_CHARAKTERE],
)
def test_der_funkspruch_traegt_die_initialen_der_gewaehlten_figur(figur):
    """Der Spielstand muss *seine* Figur einsetzen, nicht irgendeine.

    Geprüft wird am angezeigten Klartext der Sendeaufgabe: Dort steht die
    Unterschrift sichtbar am Ende. Verglichen wird gegen den Charakter, nicht
    gegen die Aufgabe selbst – sonst prüfte der Test sich selbst.
    """
    stand = _stand(figur=figur)
    stand.starte_level(1)
    aufgabe = stand.stelle_funkspruch(story.FUNKSPRUCH_ERSTER_RUF)
    assert aufgabe.richtung == "verschluesseln", "Sendeaufgabe erwartet."
    assert aufgabe.anzeigetext.endswith(f" {figur.initialen}"), (
        f"{aufgabe.anzeigetext!r} endet nicht auf die Initialen von {figur.name}."
    )
    andere = [f for f in charaktere.SPIELBARE_CHARAKTERE if f is not figur]
    for fremde in andere:
        assert not aufgabe.anzeigetext.endswith(f" {fremde.initialen}")
    stand.versuchen(aufgabe.loesung)
    assert stand.aktuelle_bearbeitung.geloest


# ───────────────────────────────────────────────────────────────────────────
# 6. Projektregel 1: Zeitfenster aus, weiter – aber nichts geht verloren
# ───────────────────────────────────────────────────────────────────────────

def test_der_levelwechsel_schliesst_eine_offene_aufgabe_ab():
    """Sonst fehlte sie im Log, und die Auswertung könnte "nicht bearbeitet"
    nicht von "Zeit war um" unterscheiden."""
    stand = _stand()
    stand.starte_level(1)
    aufgabe = stand.naechste_uebung()
    stand.versuchen("XXXXX")
    stand.naechstes_level()
    assert stand.aktuelles_level == 2
    assert stand.aktuelle_aufgabe is None
    assert len(stand.erledigte_aufgaben) == 1
    bearbeitung = stand.erledigte_aufgaben[0]
    assert bearbeitung.aufgabe is aufgabe
    assert bearbeitung.loesung_angezeigt, "Die Lösung muss eingeblendet worden sein."
    assert bearbeitung.ist_beendet


def test_eine_abgebrochene_aufgabe_behaelt_ihre_versuchszahl():
    """Die Zahl ist der Datenpunkt – sie darf beim Abbruch nicht verfälscht werden."""
    stand = _stand()
    stand.starte_level(1)
    stand.naechste_uebung()
    stand.versuchen("XXXXX")
    stand.versuchen("YYYYY")
    stand.naechstes_level()
    assert stand.erledigte_aufgaben[0].versuche == 2


def test_ein_zweites_starte_level_laesst_die_offene_aufgabe_in_ruhe():
    """Der verbotene Aufruf darf nichts nebenbei verändern."""
    stand = _stand()
    stand.starte_level(1)
    aufgabe = stand.naechste_uebung()
    stand.versuchen("XXXXX")
    with pytest.raises(ValueError):
        stand.starte_level(2)
    assert stand.aktuelle_aufgabe is aufgabe
    assert stand.aktuelle_bearbeitung.versuche == 1
    assert stand.erledigte_aufgaben == ()
    assert stand.aktuelles_level == 1


def test_eine_bereits_geloeste_aufgabe_wird_beim_wechsel_nicht_verfaelscht():
    """aufgeben() darf nur greifen, wenn wirklich nichts entschieden war."""
    stand = _stand()
    stand.starte_level(1)
    aufgabe = stand.naechste_uebung()
    stand.versuchen(aufgabe.loesung)
    stand.naechstes_level()
    bearbeitung = stand.erledigte_aufgaben[0]
    assert bearbeitung.geloest
    assert not bearbeitung.loesung_angezeigt


def test_ein_kompletter_durchlauf_laeuft_ohne_fehler_durch():
    """Von der Figurwahl bis zum Ende, nur über den Spielstand."""
    stand = _stand(seed=20260910)
    stand.starte_level(LEVEL[0])
    for level in LEVEL:
        for _ in range(2):
            stand.naechste_uebung()
            _loese(stand)
        for funkspruch in story.FUNKSPRUECHE_NACH_LEVEL[level]:
            stand.stelle_funkspruch(funkspruch)
            _loese(stand)
        stand.naechstes_level()
    assert stand.ist_durchgespielt
    assert stand.aktuelles_level is None
    assert len(stand.erledigte_aufgaben) == 6 + len(story.FUNKSPRUECHE)
    assert all(b.ist_abgeschlossen for b in stand.erledigte_aufgaben)


def test_auch_ein_durchlauf_ohne_eine_einzige_richtige_loesung_endet():
    """Projektregel 2 bis zum Ende: das Spiel bleibt nirgends hängen."""
    stand = _stand()
    stand.starte_level(LEVEL[0])
    for level in LEVEL:
        for funkspruch in story.FUNKSPRUECHE_NACH_LEVEL[level]:
            stand.stelle_funkspruch(funkspruch)
            for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
                stand.versuchen("X" * (nummer + 2))
            assert stand.aktuelle_bearbeitung.ist_beendet
            if stand.aktuelle_bearbeitung.darf_weiterrechnen:
                stand.weiterrechnen()
            stand.aufgabe_abschliessen()
        stand.naechstes_level()
    assert len(stand.erledigte_aufgaben) == len(story.FUNKSPRUECHE)
    assert all(b.loesung_angezeigt for b in stand.erledigte_aufgaben)


# ───────────────────────────────────────────────────────────────────────────
# 7. Wiederholbarkeit
# ───────────────────────────────────────────────────────────────────────────

def test_derselbe_seed_ergibt_denselben_ablauf():
    """Grundlage der Rekonstruktion aus Aufgabe 3.3."""
    def ablauf(seed):
        stand = _stand(seed=seed)
        texte = []
        stand.starte_level(LEVEL[0])
        for level in LEVEL:
            for _ in range(3):
                texte.append(stand.naechste_uebung().anzeigetext)
                _loese(stand)
            stand.naechstes_level()
        return texte

    assert ablauf(2024) == ablauf(2024)
    assert ablauf(2024) != ablauf(2025)


def test_zusatzaufgaben_werden_als_solche_weitergereicht():
    """Arbeitsplan 5.4 markiert sie, 5.5 loggt sie."""
    stand = _stand()
    stand.starte_level(1)
    assert stand.naechste_uebung().zusatzaufgabe is False
    _loese(stand)
    assert stand.naechste_uebung(zusatzaufgabe=True).zusatzaufgabe is True


# ───────────────────────────────────────────────────────────────────────────
# 8. Jedes Level genau einmal, und nur vorwärts
# ───────────────────────────────────────────────────────────────────────────
#
# Ein zweiter starte_level() für dasselbe Level würde sein Zeitfenster von
# vorn beginnen lassen – aus fünfzehn Minuten würden dreissig, ohne dass es
# auffiele. In Phase 6 passiert so etwas leicht, wenn ein Screen neu aufgebaut
# wird; Projektregel 1 hinge dann an einer Zeile Oberflächencode.

def test_dasselbe_level_laesst_sich_nicht_zweimal_starten():
    stand = _stand()
    stand.starte_level(1)
    with pytest.raises(ValueError) as fehler:
        stand.starte_level(1)
    assert "Zeitfenster" in str(fehler.value)


def test_ein_zweiter_start_wuerde_die_uhr_zuruecksetzen():
    """Der Grund für die Sperre, direkt geprüft."""
    from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN

    uhr = [0.0]
    stand = Spielstand(
        FIGUR, Zufallsquelle(1), "P01", zeitgeber=lambda: uhr[0]
    )
    stand.starte_level(1)
    uhr[0] = DAUER_JE_LEVEL_SEKUNDEN[1] - 60
    verbleibend = stand.verbleibende_sekunden
    with pytest.raises(ValueError):
        stand.starte_level(1)
    assert stand.verbleibende_sekunden == verbleibend


def test_ein_schon_gespieltes_level_laesst_sich_nicht_neu_starten():
    stand = _stand()
    stand.starte_level(1)
    stand.naechstes_level()
    with pytest.raises(ValueError):
        stand.starte_level(1)


def test_ein_frueheres_level_laesst_sich_nicht_starten():
    stand = _stand()
    stand.starte_level(2)
    with pytest.raises(ValueError) as fehler:
        stand.starte_level(1)
    assert "Reihe nach" in str(fehler.value)


def test_ein_level_ueberspringen_ist_verboten():
    """Sonst fiele Level 2 aus, und der Durchlauf gälte trotzdem als fertig."""
    stand = _stand()
    stand.starte_level(1)
    with pytest.raises(ValueError) as fehler:
        stand.starte_level(3)
    assert "naechstes_level" in str(fehler.value)
    assert stand.aktuelles_level == 1


def test_nach_dem_spielende_laesst_sich_nichts_mehr_starten():
    stand = _stand()
    stand.starte_level(2)
    stand.naechstes_level()
    stand.naechstes_level()
    assert stand.aktuelles_level is None
    for level in LEVEL:
        with pytest.raises(ValueError):
            stand.starte_level(level)


@pytest.mark.parametrize("startlevel", LEVEL[1:])
def test_ein_spaeteres_startlevel_geht_zaehlt_aber_nicht_als_durchgespielt(startlevel):
    """Für Tests und einen Wiedereinstieg – im Versuch fehlt dann ein Level."""
    stand = _stand()
    stand.starte_level(startlevel)
    while stand.naechstes_level() is not None:
        pass
    assert stand.aktuelles_level is None
    assert not stand.ist_durchgespielt


def test_naechstes_level_bleibt_der_normale_weg():
    stand = _stand()
    stand.starte_level(1)
    assert stand.naechstes_level() == 2
    assert stand.naechstes_level() == 3
    assert stand.naechstes_level() is None


def test_durchgespielt_gilt_auch_ohne_eine_einzige_aufgabe():
    """Wer nur zusieht, bis überall die Zeit abläuft, hat trotzdem durchgespielt."""
    stand = _stand()
    stand.starte_level(1)
    for _ in LEVEL:
        stand.naechstes_level()
    assert stand.erledigte_aufgaben == ()
    assert stand.ist_durchgespielt


def test_mitten_im_spiel_gilt_es_noch_nicht_als_durchgespielt():
    stand = _stand()
    stand.starte_level(1)
    stand.naechstes_level()
    assert not stand.ist_durchgespielt


# ───────────────────────────────────────────────────────────────────────────
# 9. Nach dem Zeitablauf wird keine Aufgabe mehr gestellt
# ───────────────────────────────────────────────────────────────────────────
#
# Zwischen dem Ablauf und dem nächsten pruefe_zeitfenster() liegt ein kurzer
# Moment. Eine Aufgabe, die dort gestellt würde, räumte der nächste Aufruf
# sofort wieder ab – übrig bliebe eine Logzeile ohne jede Bearbeitung.

class Uhr:
    def __init__(self):
        self.jetzt = 0.0

    def __call__(self):
        return self.jetzt

    def weiter(self, sekunden):
        self.jetzt += sekunden


def _stand_mit_uhr(uhr, seed=4711):
    return Spielstand(FIGUR, Zufallsquelle(seed), "P01", zeitgeber=uhr)


@pytest.mark.parametrize("nach_ablauf", [0.0, 0.5, 30.0])
def test_nach_ablauf_gibt_es_keine_neue_uebung(nach_ablauf):
    uhr = Uhr()
    stand = _stand_mit_uhr(uhr)
    stand.starte_level(1)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] + nach_ablauf)
    with pytest.raises(ZeitIstUm):
        stand.naechste_uebung()
    assert stand.aktuelle_aufgabe is None
    assert stand.erledigte_aufgaben == ()


def test_nach_ablauf_gibt_es_keinen_funkspruch():
    uhr = Uhr()
    stand = _stand_mit_uhr(uhr)
    stand.starte_level(1)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    with pytest.raises(ZeitIstUm):
        stand.stelle_funkspruch(story.FUNKSPRUCH_BOB_ERSTE_ANTWORT)
    assert stand.aktuelle_aufgabe is None


def test_zeit_ist_um_ist_ein_valueerror():
    """Code, der nur den allgemeinen Fall abfängt, bemerkt ihn trotzdem."""
    assert issubclass(ZeitIstUm, ValueError)


def test_kurz_vor_ablauf_geht_es_noch():
    """Solange eine Sekunde bleibt, gilt das Level – Projektregel 1 gilt beidseitig."""
    uhr = Uhr()
    stand = _stand_mit_uhr(uhr)
    stand.starte_level(1)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] - 0.5)
    assert stand.naechste_uebung() is not None


def test_nach_dem_weiterschalten_geht_es_im_neuen_level_weiter():
    """Der Weg, den die Oberfläche nach ZeitIstUm geht."""
    uhr = Uhr()
    stand = _stand_mit_uhr(uhr)
    stand.starte_level(1)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    with pytest.raises(ZeitIstUm):
        stand.naechste_uebung()
    assert stand.pruefe_zeitfenster()
    assert stand.naechste_uebung().level == 2


def test_eine_kurz_vor_ablauf_gestellte_aufgabe_gilt_als_abgebrochen():
    """Der Fall aus dem Review: gestellt bei 899,5 s, abgeräumt bei 900,5 s."""
    uhr = Uhr()
    stand = _stand_mit_uhr(uhr)
    stand.starte_level(1)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] - 0.5)
    stand.stelle_funkspruch(story.FUNKSPRUCH_BOB_ERSTE_ANTWORT)
    uhr.weiter(1.0)
    assert stand.pruefe_zeitfenster()
    bearbeitung = stand.erledigte_aufgaben[-1]
    assert bearbeitung.abgebrochen
    assert bearbeitung.loesung_angezeigt
    assert not bearbeitung.geloest


# ───────────────────────────────────────────────────────────────────────────
# 10. Jeder Funkspruch kommt nur einmal
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=lambda f: f.kennung)
def test_ein_funkspruch_laesst_sich_nicht_zweimal_stellen(funkspruch):
    """Sonst gäbe es drei frische Versuche und eine doppelte Kennung im Log."""
    stand = _stand()
    stand.starte_level(LEVEL[0])
    while stand.aktuelles_level != funkspruch.level:
        stand.naechstes_level()
    stand.stelle_funkspruch(funkspruch)
    _loese(stand)
    with pytest.raises(ValueError) as fehler:
        stand.stelle_funkspruch(funkspruch)
    assert "schon gestellt" in str(fehler.value)
    assert stand.aktuelle_aufgabe is None
    kennungen = [b.aufgabe.kennung for b in stand.erledigte_aufgaben]
    assert kennungen.count(funkspruch.kennung) == 1


def test_ein_abgewiesener_funkspruch_gilt_nicht_als_gestellt():
    """Wer ihn im falschen Level stellen wollte, bekommt ihn später trotzdem."""
    stand = _stand()
    stand.starte_level(1)
    with pytest.raises(ValueError):
        stand.stelle_funkspruch(story.FUNKSPRUCH_VERFOLGER)
    stand.naechstes_level()
    assert stand.stelle_funkspruch(story.FUNKSPRUCH_VERFOLGER).kennung == "verfolger"


# ───────────────────────────────────────────────────────────────────────────
# 11. Die Levelzeit
# ───────────────────────────────────────────────────────────────────────────
#
# Die Projektregeln verlangen die Zeitmessung pro Level *und* pro Aufgabe. Aus
# den Aufgabenzeiten allein lässt sich nicht sagen, ob ein Level am Timer
# endete oder früher fertig war.

def test_ein_laufendes_level_meldet_seine_bisherige_zeit():
    uhr = Uhr()
    stand = _stand_mit_uhr(uhr)
    stand.starte_level(1)
    uhr.weiter(123)
    assert stand.level_sekunden(1) == 123
    assert stand.levelende(1) == LEVELENDE_LAEUFT


def test_ein_level_am_timer_endet_mit_der_vollen_zeit():
    uhr = Uhr()
    stand = _stand_mit_uhr(uhr)
    stand.starte_level(1)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    stand.pruefe_zeitfenster()
    uhr.weiter(500)
    assert stand.level_sekunden(1) == DAUER_JE_LEVEL_SEKUNDEN[1]
    assert stand.levelende(1) == LEVELENDE_ZEITABLAUF


def test_ein_vorzeitig_beendetes_level_behaelt_seine_zeit():
    uhr = Uhr()
    stand = _stand_mit_uhr(uhr)
    stand.starte_level(1)
    uhr.weiter(400)
    stand.naechstes_level()
    uhr.weiter(700)
    assert stand.level_sekunden(1) == 400
    assert stand.levelende(1) == LEVELENDE_VORZEITIG
    assert stand.level_sekunden(2) == 700
    assert stand.levelende(2) == LEVELENDE_LAEUFT


def test_ein_nie_gestartetes_level_hat_keine_zeit():
    stand = _stand_mit_uhr(Uhr())
    stand.starte_level(2)
    assert stand.level_sekunden(1) is None
    assert stand.levelende(1) is None
    assert stand.level_sekunden(3) is None


def test_alle_drei_levelzeiten_nach_einem_durchlauf():
    uhr = Uhr()
    stand = _stand_mit_uhr(uhr)
    stand.starte_level(1)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    stand.pruefe_zeitfenster()
    uhr.weiter(300)
    stand.naechstes_level()
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[3] + 2)
    stand.pruefe_zeitfenster()
    assert stand.ist_durchgespielt
    assert [stand.levelende(level) for level in LEVEL] == [
        LEVELENDE_ZEITABLAUF, LEVELENDE_VORZEITIG, LEVELENDE_ZEITABLAUF,
    ]
    assert [stand.level_sekunden(level) for level in LEVEL] == [
        DAUER_JE_LEVEL_SEKUNDEN[1], 300, DAUER_JE_LEVEL_SEKUNDEN[3] + 2,
    ]


# ───────────────────────────────────────────────────────────────────────────
# 12. Zusatzaufgaben: die Grenzen gelten hier, nicht erst in der Oberfläche
# ───────────────────────────────────────────────────────────────────────────

def test_ueber_die_obergrenze_hinaus_gibt_es_keine_zusatzaufgabe():
    """Auch wenn die Oberfläche nicht vorher fragt."""
    from game.zusatzaufgaben import HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL

    stand = _stand()
    stand.starte_level(1)
    for _ in range(HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL):
        stand.naechste_uebung(zusatzaufgabe=True)
        _loese(stand)
    with pytest.raises(ValueError) as fehler:
        stand.naechste_uebung(zusatzaufgabe=True)
    assert "Zusatzaufgaben" in str(fehler.value)
    assert stand.aktuelle_aufgabe is None
    # Normale Übungen gehen weiter – die Grenze gilt nur für Extraaufgaben.
    assert stand.naechste_uebung().zusatzaufgabe is False


def test_die_obergrenze_beginnt_im_naechsten_level_neu():
    from game.zusatzaufgaben import HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL

    stand = _stand()
    stand.starte_level(1)
    for _ in range(HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL):
        stand.naechste_uebung(zusatzaufgabe=True)
        _loese(stand)
    stand.naechstes_level()
    assert stand.naechste_uebung(zusatzaufgabe=True).zusatzaufgabe is True


def test_waehrend_eine_aufgabe_laeuft_ist_nichts_faellig():
    """Gefragt wird nach dem Abschliessen – nicht mittendrin."""
    uhr = Uhr()
    stand = _stand_mit_uhr(uhr)
    stand.starte_level(1)
    stand.naechste_uebung()
    uhr.weiter(3)
    _loese(stand)
    assert stand.zusatzaufgabe_faellig
    stand.naechste_uebung()
    assert not stand.zusatzaufgabe_faellig


@pytest.mark.parametrize(
    "funkspruch",
    [f for f in story.FUNKSPRUECHE],
    ids=lambda f: f.kennung,
)
def test_nach_einem_funkspruch_ist_keine_zusatzaufgabe_faellig(funkspruch):
    """Zusatzaufgaben gehören in die Übungsphase, nicht zwischen Ruf und Antwort."""
    uhr = Uhr()
    stand = _stand_mit_uhr(uhr)
    stand.starte_level(LEVEL[0])
    while stand.aktuelles_level != funkspruch.level:
        stand.naechstes_level()
    stand.stelle_funkspruch(funkspruch)
    uhr.weiter(1)
    _loese(stand)
    assert stand.erledigte_aufgaben[-1].geloest
    assert not stand.zusatzaufgabe_faellig
