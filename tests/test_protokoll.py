"""Tests für game/protokoll.py (Arbeitsplan 5.5).

Die CSV-Dateien sind das eigentliche Ergebnis des Experiments – das Spiel ist
nur der Weg dorthin. Zwei Dinge werden deshalb besonders geprüft:

* **Datenschutz (Projektregel 7):** kein Klarname in der Datei, weder als
  Spalte noch im Dateinamen.
* **Vollständigkeit:** jede gestellte Aufgabe steht genau einmal drin, auch
  die, die beim Zeitablauf abgebrochen wurde. Sonst kann die Auswertung
  "nicht bearbeitet" nicht von "Zeit war um" unterscheiden.
"""

import csv
from datetime import datetime

import pytest

from content import charaktere, story
from game import protokoll as protokollmodul
from game.generator import uebung_nachbauen
from game.protokoll import KODIERUNG, SPALTEN, TRENNZEICHEN, Protokoll, dateiname, zeilen
from game.spielstand import (
    LEVEL,
    LEVELENDE_LAEUFT,
    LEVELENDE_VORZEITIG,
    LEVELENDE_ZEITABLAUF,
    Spielstand,
)
from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN
from game.zufallsquelle import Zufallsquelle

ZEITPUNKT = datetime(2026, 9, 10, 14, 5, 30)


class Uhr:
    def __init__(self):
        self.jetzt = 0.0

    def __call__(self):
        return self.jetzt

    def weiter(self, sekunden):
        self.jetzt += sekunden


def _durchlauf(uhr=None, figur=charaktere.ELENA_DUARTE, pseudonym="P07", seed=20260910):
    """Ein kleiner, vollständiger Durchlauf.

    Die Uhr springt um krumme Werte – sonst liesse sich nicht prüfen, dass im
    Log wirklich auf ganze Sekunden gerundet wird.
    """
    uhr = uhr if uhr is not None else Uhr()
    stand = Spielstand(figur, Zufallsquelle(seed), pseudonym, zeitgeber=uhr)
    stand.starte_level(LEVEL[0])
    for level in LEVEL:
        assert stand.aktuelles_level == level
        aufgabe = stand.naechste_uebung()
        uhr.weiter(30.4)
        stand.versuchen("XXXXX")
        stand.versuchen(aufgabe.loesung)
        stand.aufgabe_abschliessen()
        for funkspruch in story.FUNKSPRUECHE_NACH_LEVEL[level]:
            aufgabe = stand.stelle_funkspruch(funkspruch)
            uhr.weiter(44.6)
            stand.versuchen(aufgabe.loesung)
            if stand.aktuelle_bearbeitung.darf_weiterrechnen:
                stand.weiterrechnen()
            stand.aufgabe_abschliessen()
        stand.naechstes_level()
    return stand


def _gelesen(pfad):
    with open(pfad, newline="", encoding=KODIERUNG) as datei:
        return list(csv.DictReader(datei, delimiter=TRENNZEICHEN))


# ───────────────────────────────────────────────────────────────────────────
# 1. Datenschutz
# ───────────────────────────────────────────────────────────────────────────

def test_kein_klarname_steht_in_der_datei(tmp_path):
    """Projektregel 7: nur die Pseudonym-ID."""
    stand = _durchlauf(figur=charaktere.THEO_LAMBERT)
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    inhalt = pfad.read_text(encoding=KODIERUNG)
    for figur in charaktere.SPIELBARE_CHARAKTERE:
        assert figur.name not in inhalt, f"Der Name {figur.name} steht in der Datei."
        for teil in figur.name.split():
            assert teil not in inhalt


def test_auch_der_dateiname_traegt_keinen_klarnamen():
    stand = _durchlauf(figur=charaktere.THEO_LAMBERT, pseudonym="P07")
    name = dateiname(stand, ZEITPUNKT)
    assert "P07" in name
    for figur in charaktere.SPIELBARE_CHARAKTERE:
        for teil in figur.name.split():
            assert teil not in name


def test_ein_pseudonym_mit_sonderzeichen_wird_entschaerft():
    """Der Name landet in einem Dateipfad – Schrägstriche wären fatal."""
    stand = _durchlauf(pseudonym="Klasse 8b/Gruppe 3")
    name = dateiname(stand, ZEITPUNKT)
    assert "/" not in name
    assert " " not in name
    assert name.endswith(".csv")


def test_der_dateiname_traegt_einen_zeitstempel():
    """Sonst überschriebe ein zweiter Durchlauf den ersten."""
    stand = _durchlauf()
    frueh = dateiname(stand, datetime(2026, 9, 10, 8, 0, 0))
    spaet = dateiname(stand, datetime(2026, 9, 10, 10, 30, 0))
    assert frueh != spaet
    assert "2026-09-10" in frueh


# ───────────────────────────────────────────────────────────────────────────
# 2. Der Inhalt
# ───────────────────────────────────────────────────────────────────────────

def test_jede_gestellte_aufgabe_steht_genau_einmal_drin(tmp_path):
    stand = _durchlauf()
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    reihen = _gelesen(pfad)
    assert len(reihen) == len(stand.erledigte_aufgaben)
    kennungen = [r["kennung"] for r in reihen]
    assert kennungen == [b.aufgabe.kennung for b in stand.erledigte_aufgaben]


def test_die_spalten_stimmen_mit_der_kopfzeile_ueberein(tmp_path):
    stand = _durchlauf()
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    with open(pfad, newline="", encoding=KODIERUNG) as datei:
        kopf = next(csv.reader(datei, delimiter=TRENNZEICHEN))
    assert kopf == list(SPALTEN)


def test_alle_vom_arbeitsplan_verlangten_spalten_sind_da():
    """5.5 nennt sie wörtlich."""
    verlangt = {
        "pseudonym", "level", "aufgabennummer", "richtung", "versuche",
        "loesung_angezeigt", "sekunden", "zusatzaufgabe",
        "versuche_ohne_fortschritt", "laenge_in_buchstaben", "seed",
    }
    assert verlangt <= set(SPALTEN)


def test_der_seed_steht_in_jeder_zeile(tmp_path):
    """Als Spalte statt als Kommentarzeile – sonst stolpert jedes Auswertungsskript."""
    stand = _durchlauf(seed=4711)
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    for reihe in _gelesen(pfad):
        assert reihe["seed"] == "4711"


def test_die_aufgabennummer_zaehlt_je_level_ab_eins(tmp_path):
    """Zusammen mit dem Seed macht sie die Aufgabe rekonstruierbar (3.3)."""
    stand = _durchlauf()
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    gesehen = {}
    for reihe in _gelesen(pfad):
        level = int(reihe["level"])
        gesehen[level] = gesehen.get(level, 0) + 1
        assert int(reihe["aufgabennummer"]) == gesehen[level]


def test_wahrheitswerte_stehen_als_ja_und_nein(tmp_path):
    """Lesbarer als True/False, wenn die Datei in Excel geöffnet wird."""
    stand = _durchlauf()
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    for reihe in _gelesen(pfad):
        for spalte in (
            "zusatzaufgabe", "loesung_angezeigt", "abgebrochen", "geloest",
            "vollstaendig_geloest",
        ):
            assert reihe[spalte] in ("ja", "nein"), f"{spalte}={reihe[spalte]!r}"


def test_die_zahlen_sind_zahlen(tmp_path):
    stand = _durchlauf()
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    for reihe in _gelesen(pfad):
        assert int(reihe["level"]) in LEVEL
        assert int(reihe["versuche"]) >= 0
        assert int(reihe["versuche_ohne_fortschritt"]) >= 0
        assert int(reihe["laenge_in_buchstaben"]) > 0
        assert int(reihe["gerechnete_buchstaben"]) >= int(reihe["laenge_in_buchstaben"])
        assert int(reihe["sekunden"]) >= 0
        assert int(reihe["level_sekunden"]) >= int(reihe["sekunden"])


def test_die_gemessene_zeit_landet_gerundet_in_der_datei(tmp_path):
    """Auf ganze Sekunden – siehe Modulkopf von game/protokoll.py."""
    stand = _durchlauf()
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    gemessen = [b.benoetigte_sekunden for b in stand.erledigte_aufgaben]
    assert any(s != int(s) for s in gemessen), "Die Uhr muss krumme Werte liefern."
    aus_datei = [int(r["sekunden"]) for r in _gelesen(pfad)]
    assert aus_datei == [round(s) for s in gemessen]


def test_eine_beim_zeitablauf_abgebrochene_aufgabe_steht_im_log(tmp_path):
    """Sonst liesse sich "nicht bearbeitet" nicht von "Zeit war um" trennen."""
    uhr = Uhr()
    stand = Spielstand(charaktere.VIC_MORENO, Zufallsquelle(1), "P01", zeitgeber=uhr)
    stand.starte_level(1)
    stand.naechste_uebung()
    stand.versuchen("XXXXX")
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    stand.pruefe_zeitfenster()
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    reihen = _gelesen(pfad)
    assert len(reihen) == 1
    assert reihen[0]["loesung_angezeigt"] == "ja"
    assert reihen[0]["geloest"] == "nein"
    assert reihen[0]["versuche"] == "1"
    assert reihen[0]["abgebrochen"] == "ja"
    assert reihen[0]["levelende"] == LEVELENDE_ZEITABLAUF
    assert reihen[0]["level_sekunden"] == str(DAUER_JE_LEVEL_SEKUNDEN[1])


def test_eine_abgebrochene_zeile_ist_von_drei_fehlversuchen_zu_unterscheiden(tmp_path):
    """Beide haben "Lösung angezeigt", aber nur bei einer ist die Zeit Rechenzeit.

    Ohne diese Spalte wanderten die Wartezeiten bis zum Timer in jeden
    Mittelwert – und in die Gerade, mit der nach dem Pilotdurchlauf die
    Zusatzaufgaben kalibriert werden.
    """
    uhr = Uhr()
    stand = Spielstand(charaktere.VIC_MORENO, Zufallsquelle(99), "P10", zeitgeber=uhr)
    stand.starte_level(1)
    stand.naechste_uebung()
    for nummer in range(3):
        uhr.weiter(10)
        stand.versuchen("X" * (nummer + 2))
    stand.aufgabe_abschliessen()
    stand.naechste_uebung()
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    stand.pruefe_zeitfenster()
    reihen = _gelesen(Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben())
    assert [r["loesung_angezeigt"] for r in reihen] == ["ja", "ja"]
    assert [r["abgebrochen"] for r in reihen] == ["nein", "ja"]


# ───────────────────────────────────────────────────────────────────────────
# 3. Die Datei selbst
# ───────────────────────────────────────────────────────────────────────────

def test_die_datei_landet_im_angegebenen_ordner(tmp_path):
    stand = _durchlauf()
    protokoll = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT)
    pfad = protokoll.schreiben()
    assert pfad == protokoll.pfad
    assert pfad.parent == tmp_path
    assert pfad.exists()


def test_der_ordner_wird_bei_bedarf_angelegt(tmp_path):
    """Auf einem frischen Schulrechner gibt es logs/ noch nicht."""
    ziel = tmp_path / "tief" / "logs"
    assert not ziel.exists()
    Protokoll(_durchlauf(), ordner=ziel, zeitpunkt=ZEITPUNKT).schreiben()
    assert ziel.exists()


def test_der_standardordner_ist_logs():
    """Er steht in .gitignore – die Messdaten dürfen nie ins Repository."""
    assert protokollmodul.STANDARDORDNER == "logs"


def test_mehrfaches_schreiben_erzeugt_nur_eine_datei(tmp_path):
    """Damit nach einem Absturz alles bis zur letzten Aufgabe gesichert ist,
    wird nach jeder Aufgabe geschrieben – aber immer in dieselbe Datei."""
    uhr = Uhr()
    stand = Spielstand(charaktere.VIC_MORENO, Zufallsquelle(1), "P01", zeitgeber=uhr)
    protokoll = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT)
    stand.starte_level(1)
    for _ in range(3):
        aufgabe = stand.naechste_uebung()
        uhr.weiter(20)
        stand.versuchen(aufgabe.loesung)
        stand.aufgabe_abschliessen()
        protokoll.schreiben()
    assert len(list(tmp_path.glob("*.csv"))) == 1
    assert len(_gelesen(protokoll.pfad)) == 3


def test_ein_leerer_durchlauf_ergibt_eine_datei_mit_kopfzeile(tmp_path):
    """Auch wenn jemand sofort abbricht, soll die Datei lesbar sein."""
    stand = Spielstand(charaktere.VIC_MORENO, Zufallsquelle(1), "P01")
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    assert _gelesen(pfad) == []
    assert pfad.read_text(encoding=KODIERUNG).strip().startswith("pseudonym")


def test_die_datei_laesst_sich_in_deutschem_excel_oeffnen(tmp_path):
    """Semikolon als Trennzeichen, utf-8 mit Byte-Order-Mark.

    Mit einem Komma landet in deutschem Excel die ganze Zeile in einer
    einzigen Spalte; ohne das Vorzeichen der Kodierung werden Umlaute falsch
    dargestellt.
    """
    stand = _durchlauf()
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    rohbytes = pfad.read_bytes()
    assert rohbytes.startswith(b"\xef\xbb\xbf"), "Byte-Order-Mark fehlt"
    kopfzeile = rohbytes.decode("utf-8-sig").splitlines()[0]
    assert ";" in kopfzeile
    assert "," not in kopfzeile


def test_die_zeilen_funktionieren_auch_ohne_datei():
    """Für Auswertungen, die nichts schreiben wollen."""
    stand = _durchlauf()
    reihen = zeilen(stand)
    assert len(reihen) == len(stand.erledigte_aufgaben)
    assert set(reihen[0]) == set(SPALTEN)


def test_die_sekunden_sind_ganze_zahlen(tmp_path):
    """Kein Dezimaltrennzeichen, keine Locale-Falle.

    Ein "16.2" liest deutsches Excel nicht als Zahl, ein "16,2" kollidiert
    mit dem Semikolon in naiven Lesern. Eine Zehntelsekunde sagt bei einer
    halbminütigen Aufgabe ohnehin nichts.
    """
    uhr = Uhr()
    stand = Spielstand(charaktere.VIC_MORENO, Zufallsquelle(1), "P01", zeitgeber=uhr)
    stand.starte_level(1)
    aufgabe = stand.naechste_uebung()
    uhr.weiter(16.23)
    stand.versuchen(aufgabe.loesung)
    stand.aufgabe_abschliessen()
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    for reihe in _gelesen(pfad):
        assert "." not in reihe["sekunden"]
        assert "," not in reihe["sekunden"]
        assert reihe["sekunden"] == str(int(reihe["sekunden"]))


def test_keine_spalte_enthaelt_ein_dezimaltrennzeichen(tmp_path):
    """Über alle Zeilen eines echten Durchlaufs."""
    stand = _durchlauf()
    pfad = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()
    for reihe in _gelesen(pfad):
        for spalte, wert in reihe.items():
            assert "," not in wert, f"{spalte}={wert!r} enthält ein Komma"
            assert "." not in wert, f"{spalte}={wert!r} enthält einen Punkt"


# ───────────────────────────────────────────────────────────────────────────
# 4. Figur, gerechnete Buchstaben, Levelzeit
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("figur", charaktere.SPIELBARE_CHARAKTERE, ids=lambda f: f.kennung)
def test_die_figur_steht_als_kennung_drin(tmp_path, figur):
    """Die gesendeten Funksprüche tragen ihre Initialen – ohne sie ist ihr
    Wortlaut nicht nachzubauen. Der Anzeigename bleibt draussen."""
    stand = _durchlauf(figur=figur)
    for reihe in _gelesen(Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben()):
        assert reihe["figur"] == figur.kennung
        assert reihe["figur"] != figur.name


def test_wer_die_ganze_nachricht_rechnet_bekommt_die_ganze_laenge(tmp_path):
    """Sonst stünden die Sekunden für 78 Buchstaben neben einer 15."""
    uhr = Uhr()
    stand = Spielstand(charaktere.VIC_MORENO, Zufallsquelle(99), "P10", zeitgeber=uhr)
    stand.starte_level(1)
    aufgabe = stand.stelle_funkspruch(story.FUNKSPRUCH_BOB_ERSTE_ANTWORT)
    uhr.weiter(312)
    stand.versuchen(aufgabe.vollstaendige_loesung)
    stand.aufgabe_abschliessen()
    reihe = _gelesen(Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben())[0]
    assert reihe["laenge_in_buchstaben"] == str(aufgabe.laenge_in_buchstaben)
    assert reihe["gerechnete_buchstaben"] == str(aufgabe.laenge_vollstaendig_in_buchstaben)
    assert reihe["vollstaendig_geloest"] == "ja"
    assert int(reihe["gerechnete_buchstaben"]) > int(reihe["laenge_in_buchstaben"])


def test_die_levelzeit_steht_in_jeder_zeile_ihres_levels(tmp_path):
    uhr = Uhr()
    stand = _durchlauf(uhr=uhr)
    reihen = _gelesen(Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben())
    for level in LEVEL:
        eigene = [r for r in reihen if int(r["level"]) == level]
        assert eigene
        assert {r["levelende"] for r in eigene} == {LEVELENDE_VORZEITIG}
        assert {r["level_sekunden"] for r in eigene} == {
            str(round(stand.level_sekunden(level)))
        }


def test_die_levelzeit_umfasst_auch_die_zeit_zwischen_den_aufgaben(tmp_path):
    """Handbuch lesen, Geschichte lesen – das zählt zum Level, nicht zur Aufgabe."""
    uhr = Uhr()
    stand = Spielstand(charaktere.VIC_MORENO, Zufallsquelle(1), "P01", zeitgeber=uhr)
    stand.starte_level(1)
    uhr.weiter(240)                       # Handbuchseite lesen
    aufgabe = stand.naechste_uebung()
    uhr.weiter(30)
    stand.versuchen(aufgabe.loesung)
    stand.aufgabe_abschliessen()
    uhr.weiter(60)
    stand.naechstes_level()
    reihe = _gelesen(Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben())[0]
    assert reihe["sekunden"] == "30"
    assert reihe["level_sekunden"] == "330"
    assert reihe["levelende"] == LEVELENDE_VORZEITIG


def test_ein_laufendes_level_steht_als_laufend_drin(tmp_path):
    """Zwischenstand – nach dem nächsten Schreiben steht dort das Ende."""
    uhr = Uhr()
    stand = Spielstand(charaktere.VIC_MORENO, Zufallsquelle(1), "P01", zeitgeber=uhr)
    protokoll = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT)
    stand.starte_level(1)
    aufgabe = stand.naechste_uebung()
    uhr.weiter(20)
    stand.versuchen(aufgabe.loesung)
    stand.aufgabe_abschliessen()
    assert _gelesen(protokoll.schreiben())[0]["levelende"] == LEVELENDE_LAEUFT
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    stand.pruefe_zeitfenster()
    reihe = _gelesen(protokoll.schreiben())[0]
    assert reihe["levelende"] == LEVELENDE_ZEITABLAUF
    assert reihe["level_sekunden"] == str(DAUER_JE_LEVEL_SEKUNDEN[1] + 20)


# ───────────────────────────────────────────────────────────────────────────
# 5. Aus der Datei zurück zur Aufgabe (Aufgabe 3.3)
# ───────────────────────────────────────────────────────────────────────────
#
# Der Fall, an dem das alte Rezept "Seed + Aufgabennummer" scheiterte: ein
# Funkspruch vor den Übungen und Zusatzaufgaben mittendrin. Funksprüche
# ziehen keinen Zufall, zählen aber in der Aufgabennummer mit.

def _gemischter_durchlauf(uhr, seed):
    stand = Spielstand(charaktere.AMARA_NWOSU, Zufallsquelle(seed), "P42", zeitgeber=uhr)
    stand.starte_level(LEVEL[0])
    for level in LEVEL:
        for funkspruch in story.FUNKSPRUECHE_NACH_LEVEL[level][:1]:
            aufgabe = stand.stelle_funkspruch(funkspruch)
            uhr.weiter(50)
            stand.versuchen(aufgabe.loesung)
            stand.aufgabe_abschliessen()
        for nummer in range(4):
            aufgabe = stand.naechste_uebung(zusatzaufgabe=nummer % 2 == 1)
            uhr.weiter(5)
            stand.versuchen(aufgabe.loesung)
            stand.aufgabe_abschliessen()
        stand.naechstes_level()
    return stand


@pytest.mark.parametrize("seed", [5, 4711, 20260910, 999999999])
def test_jede_uebung_laesst_sich_aus_seed_und_kennung_nachbauen(tmp_path, seed):
    stand = _gemischter_durchlauf(Uhr(), seed)
    reihen = _gelesen(Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben())
    gespielt = {b.aufgabe.kennung: b.aufgabe for b in stand.erledigte_aufgaben}
    uebungen = [r for r in reihen if r["quelle"] == "uebung"]
    assert len(uebungen) == 4 * len(LEVEL)
    for reihe in uebungen:
        nachgebaut = uebung_nachbauen(int(reihe["seed"]), reihe["kennung"])
        original = gespielt[reihe["kennung"]]
        assert nachgebaut.anzeigetext == original.anzeigetext
        assert nachgebaut.loesung == original.loesung
        assert nachgebaut.richtung == original.richtung
        assert nachgebaut.schluessel == original.schluessel


def test_die_aufgabennummer_ist_nicht_die_uebungsnummer(tmp_path):
    """Warum das Rezept über die Kennung geht – festgehalten, damit es niemand
    "vereinfacht"."""
    stand = _gemischter_durchlauf(Uhr(), 5)
    reihen = _gelesen(Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT).schreiben())
    erste_uebung = next(r for r in reihen if r["quelle"] == "uebung")
    assert erste_uebung["aufgabennummer"] == "2"
    assert erste_uebung["kennung"] == "uebung_l1_1"


@pytest.mark.parametrize(
    "kennung",
    ["erster_ruf", "bob_erste_antwort", "uebung_l1", "uebung_l1_0", "uebung_lx_2",
     "uebung_l1_²", "uebung_1_2", "", None],
)
def test_nur_uebungskennungen_lassen_sich_nachbauen(kennung):
    with pytest.raises(ValueError):
        uebung_nachbauen(4711, kennung)


def test_eine_uebungskennung_eines_unbekannten_levels_wird_abgewiesen():
    with pytest.raises(ValueError):
        uebung_nachbauen(4711, "uebung_l7_1")


# ───────────────────────────────────────────────────────────────────────────
# 6. Absturzsicher schreiben
# ───────────────────────────────────────────────────────────────────────────
#
# Die Datei wird nach jeder Aufgabe vollständig neu geschrieben. Bricht das
# mittendrin ab, darf nicht eine Datei mit blosser Kopfzeile zurückbleiben –
# sonst wäre ausgerechnet dann der ganze Durchlauf weg.

class Stromausfall(BaseException):
    """Stellvertretend für Absturz, zugeklappten Deckel, Stromausfall."""


def _drei_aufgaben(tmp_path):
    uhr = Uhr()
    stand = Spielstand(charaktere.VIC_MORENO, Zufallsquelle(1), "P01", zeitgeber=uhr)
    protokoll = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT)
    stand.starte_level(1)
    for _ in range(3):
        aufgabe = stand.naechste_uebung()
        uhr.weiter(10)
        stand.versuchen(aufgabe.loesung)
        stand.aufgabe_abschliessen()
        protokoll.schreiben()
    aufgabe = stand.naechste_uebung()
    stand.versuchen(aufgabe.loesung)
    stand.aufgabe_abschliessen()
    return stand, protokoll


def test_ein_abbruch_mitten_im_schreiben_laesst_die_alte_fassung_stehen(tmp_path, monkeypatch):
    stand, protokoll = _drei_aufgaben(tmp_path)
    vorher = protokoll.pfad.read_bytes()

    class AbbruchNachEinerZeile(csv.DictWriter):
        def writerows(self, reihen):
            self.writerow(list(reihen)[0])
            raise Stromausfall

    monkeypatch.setattr(protokollmodul.csv, "DictWriter", AbbruchNachEinerZeile)
    with pytest.raises(Stromausfall):
        protokoll.schreiben()
    assert protokoll.pfad.read_bytes() == vorher
    assert len(_gelesen(protokoll.pfad)) == 3
    assert not protokoll.zwischendatei.exists()


def test_scheitert_das_ersetzen_bleibt_die_alte_fassung_stehen(tmp_path, monkeypatch):
    """Etwa unter Windows, wenn die Datei gerade in Excel offen ist."""
    stand, protokoll = _drei_aufgaben(tmp_path)
    vorher = protokoll.pfad.read_bytes()

    def gesperrt(quelle, ziel):
        raise PermissionError("Die Datei ist in einem anderen Programm geöffnet.")

    monkeypatch.setattr(protokollmodul.os, "replace", gesperrt)
    with pytest.raises(PermissionError):
        protokoll.schreiben()
    assert protokoll.pfad.read_bytes() == vorher
    assert not protokoll.zwischendatei.exists()


def test_nach_einem_fehlschlag_holt_das_naechste_schreiben_alles_nach(tmp_path, monkeypatch):
    """Verloren geht nichts – jedes Mal wird alles geschrieben."""
    stand, protokoll = _drei_aufgaben(tmp_path)

    def gesperrt(quelle, ziel):
        raise PermissionError("Die Datei ist in einem anderen Programm geöffnet.")

    with monkeypatch.context() as m:
        m.setattr(protokollmodul.os, "replace", gesperrt)
        with pytest.raises(PermissionError):
            protokoll.schreiben()
    protokoll.schreiben()
    assert len(_gelesen(protokoll.pfad)) == len(stand.erledigte_aufgaben) == 4


def test_nach_dem_schreiben_bleibt_keine_nebendatei_liegen(tmp_path):
    stand, protokoll = _drei_aufgaben(tmp_path)
    protokoll.schreiben()
    assert sorted(p.name for p in tmp_path.iterdir()) == [protokoll.dateiname]


# ───────────────────────────────────────────────────────────────────────────
# 7. Sehr lange Pseudonyme
# ───────────────────────────────────────────────────────────────────────────

def test_ein_sehr_langes_pseudonym_verhindert_das_schreiben_nicht(tmp_path):
    """Die Grenze des Dateisystems (255 Bytes) darf den Durchlauf nicht kosten."""
    lang = "Klasse-9b-Gruppe-A-" + "x" * 250
    stand = _durchlauf(pseudonym=lang)
    protokoll = Protokoll(stand, ordner=tmp_path, zeitpunkt=ZEITPUNKT)
    pfad = protokoll.schreiben()
    assert len(pfad.name.encode("utf-8")) < 255
    assert all(r["pseudonym"] == lang for r in _gelesen(pfad))


def test_im_dateinamen_wird_das_pseudonym_gekuerzt():
    class Probe:
        pseudonym = "ä" * 500

    name = dateiname(Probe(), ZEITPUNKT)
    teil = name.removeprefix("durchlauf_").removesuffix("_2026-09-10_140530.csv")
    assert len(teil) == protokollmodul.HOECHSTLAENGE_PSEUDONYM_IM_DATEINAMEN
    assert len(name.encode("utf-8")) < 255
