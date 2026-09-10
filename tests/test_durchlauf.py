"""Tests für game/durchlauf.py (Arbeitsplan 6.1).

Der Durchlauf ist die Stelle, an der die Oberfläche an Phase 5 anschliesst.
Geprüft wird, was dort nie vergessen werden darf:

* **Der Takt schaltet weiter**, wenn die Zeit um ist – und nur dann.
* **Eine zu spät gestellte Aufgabe** wird nicht zum Absturz, sondern zum
  Levelwechsel.
* **Gespeichert wird** beim Start, nach jeder Aufgabe, nach jedem
  Levelwechsel und beim Beenden. Ein Speicherfehler wird gemeldet, nicht
  verschluckt – und kostet keine Daten.
"""

import csv

import pytest

from content import charaktere, story
from game.durchlauf import Durchlauf, Levelwechsel
from game.protokoll import KODIERUNG, TRENNZEICHEN
from game.spielstand import LEVEL
from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN

FIGUR = charaktere.JONAS_BERG


class Uhr:
    def __init__(self):
        self.jetzt = 0.0

    def __call__(self):
        return self.jetzt

    def weiter(self, sekunden):
        self.jetzt += sekunden


class Mitschrift:
    """Sammelt, was der Durchlauf über seine Rückrufe meldet."""

    def __init__(self):
        self.levelwechsel = []
        self.speicherprobleme = []

    def rueckrufe(self):
        return {
            "bei_levelwechsel": self.levelwechsel.append,
            "bei_speicherproblem": self.speicherprobleme.append,
        }


@pytest.fixture
def uhr():
    return Uhr()


@pytest.fixture
def mitschrift():
    return Mitschrift()


@pytest.fixture
def durchlauf(tmp_path, uhr, mitschrift):
    return Durchlauf.neu(
        FIGUR, pseudonym="P03", zeitgeber=uhr, protokollordner=tmp_path, **mitschrift.rueckrufe()
    )


def _zeilen(durchlauf):
    with open(durchlauf.protokoll.pfad, newline="", encoding=KODIERUNG) as datei:
        return list(csv.DictReader(datei, delimiter=TRENNZEICHEN))


def _loesen(durchlauf):
    stand = durchlauf.spielstand
    stand.versuchen(stand.aktuelle_aufgabe.loesung)
    durchlauf.aufgabe_abschliessen()


class Speicher:
    """Ersetzt Protokoll.schreiben: scheitert, solange ``gesperrt`` ist."""

    def __init__(self, protokoll):
        self._echt = protokoll.schreiben
        self.gesperrt = True

    def __call__(self):
        if self.gesperrt:
            raise PermissionError(13, "Zugriff verweigert")
        return self._echt()


# ───────────────────────────────────────────────────────────────────────────
# 1. Aufbau
# ───────────────────────────────────────────────────────────────────────────

def test_ein_neuer_durchlauf_traegt_figur_pseudonym_und_ordner(tmp_path, durchlauf):
    assert durchlauf.spielstand.figur is FIGUR
    assert durchlauf.spielstand.pseudonym == "P03"
    assert durchlauf.protokoll.pfad.parent == tmp_path
    assert durchlauf.protokoll.spielstand is durchlauf.spielstand


def test_vor_dem_ersten_level_ist_noch_nichts_geschrieben(durchlauf):
    assert not durchlauf.hat_begonnen
    assert not durchlauf.protokoll.pfad.exists()


def test_der_start_des_ersten_levels_legt_die_datei_an(durchlauf):
    """Ein nicht beschreibbarer Log-Ordner zeigt sich so nach Sekunden."""
    durchlauf.starte_level()
    assert durchlauf.hat_begonnen
    assert durchlauf.spielstand.aktuelles_level == LEVEL[0]
    assert durchlauf.protokoll.pfad.exists()
    assert _zeilen(durchlauf) == []


# ───────────────────────────────────────────────────────────────────────────
# 2. Der Takt
# ───────────────────────────────────────────────────────────────────────────

def test_solange_zeit_bleibt_passiert_beim_takt_nichts(durchlauf, uhr, mitschrift):
    durchlauf.starte_level()
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] - 0.5)
    assert durchlauf.takt() is None
    assert mitschrift.levelwechsel == []
    assert durchlauf.spielstand.aktuelles_level == 1


def test_vor_dem_start_passiert_beim_takt_nichts(durchlauf, mitschrift):
    assert durchlauf.takt() is None
    assert mitschrift.levelwechsel == []


def test_ist_die_zeit_um_schaltet_der_takt_weiter(durchlauf, uhr, mitschrift):
    durchlauf.starte_level()
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    wechsel = durchlauf.takt()
    assert wechsel == Levelwechsel(altes_level=1, neues_level=2, durch_zeitablauf=True)
    assert mitschrift.levelwechsel == [wechsel]
    assert durchlauf.spielstand.aktuelles_level == 2


def test_der_takt_schaltet_nur_einmal_weiter(durchlauf, uhr, mitschrift):
    durchlauf.starte_level()
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    for _ in range(10):
        durchlauf.takt()
    assert len(mitschrift.levelwechsel) == 1


def test_der_zeitablauf_wird_gespeichert(durchlauf, uhr):
    """Nach dem Wechsel steht im Log "zeitablauf", nicht mehr "laeuft"."""
    durchlauf.starte_level()
    durchlauf.naechste_uebung()
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    durchlauf.takt()
    zeile = _zeilen(durchlauf)[0]
    assert zeile["levelende"] == "zeitablauf"
    assert zeile["abgebrochen"] == "ja"


def test_nach_dem_letzten_level_meldet_der_takt_das_spielende(durchlauf, uhr, mitschrift):
    durchlauf.starte_level(3)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[3])
    wechsel = durchlauf.takt()
    assert wechsel.spielende
    assert wechsel.neues_level is None
    assert durchlauf.takt() is None


# ───────────────────────────────────────────────────────────────────────────
# 3. Vorzeitig weiter, weil die Geschichte weitergeht
# ───────────────────────────────────────────────────────────────────────────

def test_ein_vorzeitiger_wechsel_meldet_sich_wie_ein_zeitablauf(durchlauf, uhr, mitschrift):
    """Beide Wege laufen über denselben Rückruf – eine Stelle entscheidet."""
    durchlauf.starte_level()
    uhr.weiter(300)
    wechsel = durchlauf.naechstes_level()
    assert wechsel == Levelwechsel(altes_level=1, neues_level=2, durch_zeitablauf=False)
    assert mitschrift.levelwechsel == [wechsel]


def test_wer_erst_nach_ablauf_weiterschaltet_bekommt_trotzdem_den_zeitablauf(durchlauf, uhr):
    """So steht es auch im Log – Rückmeldung und Datei widersprechen sich nicht."""
    durchlauf.starte_level()
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] + 1)
    assert durchlauf.naechstes_level().durch_zeitablauf


def test_ein_vorzeitiger_wechsel_wird_gespeichert(durchlauf, uhr):
    durchlauf.starte_level()
    durchlauf.naechste_uebung()
    _loesen(durchlauf)
    uhr.weiter(200)
    durchlauf.naechstes_level()
    assert _zeilen(durchlauf)[0]["levelende"] == "vorzeitig"


def test_der_ganze_weg_bis_zum_spielende(durchlauf, mitschrift):
    durchlauf.starte_level()
    for _ in LEVEL:
        durchlauf.naechstes_level()
    assert [w.neues_level for w in mitschrift.levelwechsel] == [2, 3, None]
    assert mitschrift.levelwechsel[-1].spielende
    assert durchlauf.spielstand.ist_durchgespielt


# ───────────────────────────────────────────────────────────────────────────
# 4. Aufgaben stellen – auch zu spät
# ───────────────────────────────────────────────────────────────────────────

def test_eine_uebung_wird_gestellt(durchlauf):
    durchlauf.starte_level()
    aufgabe = durchlauf.naechste_uebung()
    assert aufgabe is durchlauf.spielstand.aktuelle_aufgabe
    assert aufgabe.level == 1


def test_ein_funkspruch_wird_gestellt(durchlauf):
    durchlauf.starte_level()
    aufgabe = durchlauf.stelle_funkspruch(story.FUNKSPRUCH_ERSTER_RUF)
    assert aufgabe.kennung == "erster_ruf"


@pytest.mark.parametrize("stellen", ["uebung", "funkspruch"])
def test_zu_spaet_gestellt_wird_zum_levelwechsel(durchlauf, uhr, mitschrift, stellen):
    """Zwischen Ablauf und nächstem Takt: kein Absturz, sondern sofort weiter."""
    durchlauf.starte_level()
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] + 0.1)
    if stellen == "uebung":
        ergebnis = durchlauf.naechste_uebung()
    else:
        ergebnis = durchlauf.stelle_funkspruch(story.FUNKSPRUCH_BOB_ERSTE_ANTWORT)
    assert ergebnis is None
    assert durchlauf.spielstand.aktuelle_aufgabe is None
    assert durchlauf.spielstand.aktuelles_level == 2
    assert mitschrift.levelwechsel == [Levelwechsel(1, 2, True)]


def test_andere_fehler_beim_stellen_kommen_durch(durchlauf):
    """Nur der Zeitablauf wird abgefangen – ein Programmierfehler nicht."""
    durchlauf.starte_level()
    durchlauf.naechste_uebung()
    with pytest.raises(ValueError):
        durchlauf.naechste_uebung()


def test_nach_jeder_abgeschlossenen_aufgabe_wird_gespeichert(durchlauf, uhr):
    durchlauf.starte_level()
    for anzahl in range(1, 4):
        durchlauf.naechste_uebung()
        uhr.weiter(10)
        _loesen(durchlauf)
        assert len(_zeilen(durchlauf)) == anzahl


# ───────────────────────────────────────────────────────────────────────────
# 5. Speicherfehler: melden, nicht verschlucken, nichts verlieren
# ───────────────────────────────────────────────────────────────────────────

def test_ein_speicherfehler_wird_gemeldet(durchlauf, mitschrift, monkeypatch):
    durchlauf.starte_level()
    monkeypatch.setattr(durchlauf.protokoll, "schreiben", Speicher(durchlauf.protokoll))
    assert durchlauf.sichern() is False
    assert isinstance(durchlauf.speicherfehler, PermissionError)
    assert mitschrift.speicherprobleme == [durchlauf.speicherhinweis]
    assert "Zugriff verweigert" in durchlauf.speicherhinweis
    assert durchlauf.protokoll.dateiname in durchlauf.speicherhinweis
    assert "Excel" in durchlauf.speicherhinweis


def test_klappt_es_wieder_verschwindet_die_meldung(durchlauf, mitschrift, monkeypatch):
    durchlauf.starte_level()
    speicher = Speicher(durchlauf.protokoll)
    monkeypatch.setattr(durchlauf.protokoll, "schreiben", speicher)
    durchlauf.sichern()
    speicher.gesperrt = False
    assert durchlauf.sichern() is True
    assert durchlauf.speicherfehler is None
    assert durchlauf.speicherhinweis == ""
    assert mitschrift.speicherprobleme[-1] == ""


def test_ohne_fehler_wird_auch_nichts_gemeldet(durchlauf, mitschrift):
    durchlauf.starte_level()
    durchlauf.sichern()
    assert mitschrift.speicherprobleme == []


def test_ein_speicherfehler_kostet_keine_daten(durchlauf, uhr, monkeypatch):
    """Solange die Datei gesperrt ist, gehen die Aufgaben nicht verloren."""
    durchlauf.starte_level()
    speicher = Speicher(durchlauf.protokoll)
    monkeypatch.setattr(durchlauf.protokoll, "schreiben", speicher)
    for _ in range(3):
        durchlauf.naechste_uebung()
        uhr.weiter(5)
        _loesen(durchlauf)
    assert _zeilen(durchlauf) == []
    speicher.gesperrt = False
    durchlauf.naechste_uebung()
    _loesen(durchlauf)
    assert len(_zeilen(durchlauf)) == 4


def test_ein_speicherfehler_haelt_das_spiel_nicht_an(durchlauf, uhr, monkeypatch):
    """Weiterspielen geht – auch der Levelwechsel."""
    durchlauf.starte_level()
    monkeypatch.setattr(durchlauf.protokoll, "schreiben", Speicher(durchlauf.protokoll))
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    assert durchlauf.takt() is not None
    assert durchlauf.spielstand.aktuelles_level == 2


def test_andere_fehler_beim_speichern_kommen_durch(durchlauf, monkeypatch):
    """Abgefangen wird nur, was das Dateisystem meldet."""
    durchlauf.starte_level()

    def kaputt():
        raise KeyError("Programmierfehler")

    monkeypatch.setattr(durchlauf.protokoll, "schreiben", kaputt)
    with pytest.raises(KeyError):
        durchlauf.sichern()


# ───────────────────────────────────────────────────────────────────────────
# 6. Beenden
# ───────────────────────────────────────────────────────────────────────────

def test_beim_beenden_wird_die_offene_aufgabe_festgehalten(durchlauf, uhr):
    """Sonst fehlte im Log genau die Stelle, an der jemand aufgehört hat."""
    durchlauf.starte_level()
    durchlauf.naechste_uebung()
    uhr.weiter(42)
    assert durchlauf.beenden() is True
    zeile = _zeilen(durchlauf)[0]
    assert zeile["abgebrochen"] == "ja"
    assert zeile["sekunden"] == "42"
    assert zeile["levelende"] == "laeuft"


def test_beenden_ohne_offene_aufgabe_speichert_nur(durchlauf):
    durchlauf.starte_level()
    durchlauf.naechste_uebung()
    _loesen(durchlauf)
    assert durchlauf.beenden() is True
    assert len(_zeilen(durchlauf)) == 1


def test_beenden_vor_dem_ersten_level_hinterlaesst_keine_datei(durchlauf):
    assert durchlauf.beenden() is True
    assert not durchlauf.protokoll.pfad.exists()


def test_beenden_meldet_einen_speicherfehler(durchlauf, monkeypatch):
    durchlauf.starte_level()
    monkeypatch.setattr(durchlauf.protokoll, "schreiben", Speicher(durchlauf.protokoll))
    assert durchlauf.beenden() is False
    assert durchlauf.speicherfehler is not None


def test_beenden_laesst_sich_wiederholen(durchlauf, uhr, monkeypatch):
    """Das Hauptfenster versucht es nach einem Fehler noch einmal."""
    durchlauf.starte_level()
    durchlauf.naechste_uebung()
    speicher = Speicher(durchlauf.protokoll)
    monkeypatch.setattr(durchlauf.protokoll, "schreiben", speicher)
    assert durchlauf.beenden() is False
    speicher.gesperrt = False
    assert durchlauf.beenden() is True
    assert len(_zeilen(durchlauf)) == 1
