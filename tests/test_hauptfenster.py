"""Tests für das Fenstergerüst (Arbeitsplan 6.1): ui/hauptfenster.py,
ui/screen.py, ui/ablauf.py, die Platzhalter und main.py.

Diese Tests brauchen eine Bildschirmanzeige. Ohne eine (etwa auf einem Server)
werden sie übersprungen statt rot – die Logik dahinter prüft
``tests/test_durchlauf.py`` auch ohne Bildschirm.

Die Fenster werden versteckt (``withdraw``), damit beim Testlauf nichts über
den Bildschirm flackert. Dialoge sind durch Attrappen ersetzt – ein echter
Dialog hielte den Testlauf an, bis jemand klickt.
"""

import csv
import sys
import time
from pathlib import Path

import pytest

# Ohne Tkinter wird die ganze Datei übersprungen – deshalb stehen die
# übrigen Importe erst hier unten.
tk = pytest.importorskip("tkinter")
from tkinter import font as tkfont  # noqa: E402

import main  # noqa: E402
from game.protokoll import KODIERUNG, TRENNZEICHEN  # noqa: E402
from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN  # noqa: E402
from ui import ablauf, hauptfenster, platzhalter, stil  # noqa: E402
from ui.hauptfenster import Hauptfenster  # noqa: E402
from ui.screen import Screen  # noqa: E402


class Uhr:
    def __init__(self):
        self.jetzt = 0.0

    def __call__(self):
        return self.jetzt

    def weiter(self, sekunden):
        self.jetzt += sekunden


class Rueckfrage:
    """Ersetzt einen Dialog und gibt vorbereitete Antworten der Reihe nach zurück.

    Ohne vorbereitete Antwort schlägt der Test fehl: Eine Rückfrage, mit der
    niemand gerechnet hat, ist selbst ein Befund.
    """

    def __init__(self, *antworten, vorher=None):
        self.antworten = list(antworten)
        self.fragen = []
        self.vorher = vorher

    def __call__(self, titel, text, **_):
        self.fragen.append((titel, text))
        if self.vorher is not None:
            self.vorher()
        if not self.antworten:
            raise AssertionError(f"Unerwartete Rückfrage: {titel!r}")
        return self.antworten.pop(0)


class Speicher:
    """Ersetzt Protokoll.schreiben: scheitert, solange ``gesperrt`` ist."""

    def __init__(self, protokoll):
        self._echt = protokoll.schreiben
        self.gesperrt = True

    def __call__(self):
        if self.gesperrt:
            raise PermissionError(13, "Zugriff verweigert")
        return self._echt()


@pytest.fixture
def wurzel():
    try:
        wurzel = tk.Tk()
    except tk.TclError as fehler:
        pytest.skip(f"Keine Bildschirmanzeige: {fehler}")
    wurzel.withdraw()
    yield wurzel
    try:
        wurzel.destroy()
    except tk.TclError:
        pass  # schon vom Test geschlossen


@pytest.fixture
def uhr():
    return Uhr()


@pytest.fixture
def fenster(wurzel, uhr, tmp_path):
    fenster = ablauf.oeffnen(wurzel, zeitgeber=uhr, protokollordner=tmp_path)
    fenster.frage_ja_nein = Rueckfrage()
    fenster.frage_nochmal = Rueckfrage()
    return fenster


def _knopf(widget, anfang):
    """Sucht im Screen den Knopf, dessen Aufschrift so beginnt."""
    for kind in widget.winfo_children():
        if isinstance(kind, tk.Button) and kind.cget("text").startswith(anfang):
            return kind
        try:
            return _knopf(kind, anfang)
        except LookupError:
            pass
    raise LookupError(f"Kein Knopf '{anfang}…' in {widget}")


def _klick(fenster, anfang):
    _knopf(fenster.aktueller_screen, anfang).invoke()


def _bis_zum_handbuch(fenster):
    _klick(fenster, "Spiel starten")
    _klick(fenster, "Vic Moreno")
    _klick(fenster, "Weiter")


def _bis_zur_uebung(fenster):
    _bis_zum_handbuch(fenster)
    _klick(fenster, "Zu den Übungen")


def _zeilen(fenster):
    with open(fenster.durchlauf.protokoll.pfad, newline="", encoding=KODIERUNG) as datei:
        return list(csv.DictReader(datei, delimiter=TRENNZEICHEN))


class Probe(Screen):
    """Ein Screen, der mitschreibt, was mit ihm geschieht."""

    titel = "Probe"

    def __init__(self, fenster, name="probe", ereignisse=None):
        super().__init__(fenster)
        self.name = name
        self.ereignisse = ereignisse if ereignisse is not None else []
        self.ereignisse.append(("gebaut", name))

    def beim_anzeigen(self):
        self.ereignisse.append(("angezeigt", self.name))

    def beim_verlassen(self):
        self.ereignisse.append(("verlassen", self.name))


def _probefenster(wurzel, ereignisse, uhr=None, tmp_path=None):
    return Hauptfenster(
        wurzel,
        lambda fenster: Probe(fenster, "start", ereignisse),
        lambda fenster, wechsel: ereignisse.append(("levelwechsel", wechsel)),
        zeitgeber=uhr,
        protokollordner=tmp_path,
    )


# ───────────────────────────────────────────────────────────────────────────
# 1. Das Fenster
# ───────────────────────────────────────────────────────────────────────────

def test_das_fenster_traegt_titel_und_mindestgroesse(fenster, wurzel):
    assert wurzel.title() == hauptfenster.FENSTER_TITEL
    assert wurzel.minsize() == (hauptfenster.MIN_BREITE, hauptfenster.MIN_HOEHE)


def test_es_beginnt_mit_dem_startscreen(fenster):
    assert isinstance(fenster.aktueller_screen, ablauf.STARTSCREEN)
    assert fenster.kopfzeile == ("Der Diamantenraub", "", "")
    assert fenster.durchlauf is None


def test_die_schriften_sind_eingerichtet(fenster, wurzel):
    """Die Screens nennen die Überschrift beim Namen – es muss sie also geben."""
    assert stil.SCHRIFT_TITEL in tkfont.names(wurzel)
    titel = tkfont.nametofont(stil.SCHRIFT_TITEL, root=wurzel)
    assert titel.cget("size") == stil.TITELGROESSE
    assert tkfont.nametofont("TkDefaultFont", root=wurzel).cget("size") == stil.SCHRIFTGROESSE


# ───────────────────────────────────────────────────────────────────────────
# 2. Der Screen-Wechsel
# ───────────────────────────────────────────────────────────────────────────

def test_zeige_tauscht_den_screen_aus(wurzel):
    ereignisse = []
    fenster = _probefenster(wurzel, ereignisse)
    alt = fenster.aktueller_screen
    neu = fenster.zeige(Probe, name="zwei", ereignisse=ereignisse)
    assert ereignisse == [
        ("gebaut", "start"),
        ("angezeigt", "start"),
        ("verlassen", "start"),
        ("gebaut", "zwei"),
        ("angezeigt", "zwei"),
    ]
    assert fenster.aktueller_screen is neu
    assert not alt.winfo_exists()


def test_im_inhalt_steht_immer_nur_ein_screen(fenster):
    for _ in range(5):
        fenster.zeige(Probe)
    assert len(fenster.inhalt.winfo_children()) == 1


def test_ein_unbekanntes_datum_fuer_den_screen_ist_ein_fehler(fenster):
    """Ein Tippfehler im Namen soll auffallen, nicht still ignoriert werden."""
    with pytest.raises(TypeError):
        fenster.zeige(Probe, gibts_nicht=1)


def test_die_kopfzeile_zeigt_den_titel_des_screens(fenster):
    fenster.zeige(Probe)
    assert fenster.kopfzeile[0] == "Probe"


def test_ein_screen_weiss_ob_er_noch_angezeigt_wird(fenster):
    erster = fenster.zeige(Probe)
    assert erster.ist_angezeigt
    fenster.zeige(Probe)
    assert not erster.ist_angezeigt


def _warten(wurzel, sekunden):
    ende = time.monotonic() + sekunden
    while time.monotonic() < ende:
        wurzel.update()
        time.sleep(0.005)


def test_ein_spaeter_auftrag_feuert_wenn_der_screen_bleibt(fenster, wurzel):
    """Die Gegenprobe zum nächsten Test – sonst bewiese der nichts."""
    gefeuert = []
    fenster.zeige(Probe).spaeter(10, lambda: gefeuert.append(True))
    _warten(wurzel, 0.15)
    assert gefeuert == [True]


def _angemeldete_auftraege(wurzel):
    return set(wurzel.tk.splitlist(wurzel.tk.call("after", "info")))


def test_ein_spaeter_auftrag_wird_beim_wechsel_abgemeldet(fenster, wurzel):
    """Geprüft an Tcl selbst: Nach dem Wechsel darf er dort nicht mehr stehen.

    Dass er nicht mehr läuft, genügte als Nachweis nicht – Tkinter löscht
    beim Abriss eines Screens dessen Rückrufe, der Auftrag bliebe aber bei
    Tcl angemeldet und liefe ins Leere.
    """
    gefeuert = []
    auftrag = fenster.zeige(Probe).spaeter(10_000, lambda: gefeuert.append(True))
    assert auftrag in _angemeldete_auftraege(wurzel)
    fenster.zeige(Probe)
    assert auftrag not in _angemeldete_auftraege(wurzel)
    assert gefeuert == []


def test_ein_ausgefuehrter_auftrag_wird_vergessen(fenster, wurzel):
    screen = fenster.zeige(Probe)
    screen.spaeter(5, lambda: None)
    _warten(wurzel, 0.1)
    assert screen._auftraege == set()


# ───────────────────────────────────────────────────────────────────────────
# 3. Takt und Kopfzeile
# ───────────────────────────────────────────────────────────────────────────

def test_der_takt_ist_von_anfang_an_angemeldet(fenster):
    assert fenster._takt_auftrag is not None


def test_level_und_restzeit_stehen_in_der_kopfzeile(fenster, uhr):
    _bis_zum_handbuch(fenster)
    assert fenster.kopfzeile == ("Handbuch – Level 1", "Level 1 · Caesar-Verschlüsselung", "15:00")
    uhr.weiter(60.5)
    fenster._takt()
    assert fenster.kopfzeile[2] == "14:00"


def test_der_takt_schaltet_nach_ablauf_weiter(fenster, uhr):
    _bis_zum_handbuch(fenster)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    fenster._takt()
    assert fenster.durchlauf.spielstand.aktuelles_level == 2
    assert fenster.kopfzeile == (
        "Handbuch – Level 2", "Level 2 · monoalphabetische Substitution", "20:00",
    )


def test_der_takt_laeuft_wirklich_ueber_after(fenster, wurzel, uhr, monkeypatch):
    """Ohne Aufruf von Hand: Nur die Ereignisschleife läuft, und das Level wechselt."""
    monkeypatch.setattr(hauptfenster, "TAKT_MILLISEKUNDEN", 5)
    _bis_zum_handbuch(fenster)
    fenster._takt()  # meldet den nächsten Takt mit 5 ms an
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    ende = time.monotonic() + 2
    while fenster.durchlauf.spielstand.aktuelles_level == 1 and time.monotonic() < ende:
        wurzel.update()
        time.sleep(0.005)
    assert fenster.durchlauf.spielstand.aktuelles_level == 2


def test_ein_fehler_im_takt_haelt_die_uhr_nicht_an(fenster, monkeypatch):
    """Sonst liefe nach einem einzigen Fehler kein Zeitfenster mehr ab."""
    _bis_zum_handbuch(fenster)

    def kaputt():
        raise RuntimeError("Fehler im Takt")

    monkeypatch.setattr(fenster.durchlauf, "takt", kaputt)
    with pytest.raises(RuntimeError):
        fenster._takt()
    assert fenster._takt_auftrag is not None


def test_ein_direkter_takt_startet_keinen_zweiten_daneben(fenster, wurzel):
    for _ in range(5):
        fenster._takt()
    angemeldet = wurzel.tk.splitlist(wurzel.tk.call("after", "info"))
    assert len(angemeldet) == 1


# ───────────────────────────────────────────────────────────────────────────
# 4. Eine Aufgabe, die zu spät kommt
# ───────────────────────────────────────────────────────────────────────────

def test_eine_zu_spaet_gestellte_uebung_schaltet_sofort_weiter(fenster, uhr):
    """Zwischen Ablauf und nächstem Takt: kein Absturz, sondern das nächste Level."""
    _bis_zum_handbuch(fenster)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] + 0.1)
    _klick(fenster, "Zu den Übungen")
    screen = fenster.aktueller_screen
    assert isinstance(screen, platzhalter.Handbuch)
    assert screen.titel == "Handbuch – Level 2"
    assert fenster.durchlauf.spielstand.aktuelle_aufgabe is None
    assert fenster.meldung == ""


class StelltImKonstruktor(Screen):
    """Hält sich nicht an die Regel und stellt schon beim Bauen eine Aufgabe."""

    def __init__(self, fenster):
        super().__init__(fenster)
        fenster.durchlauf.naechste_uebung()


def test_ein_screen_der_zu_frueh_stellt_verdeckt_den_levelwechsel_nicht(fenster, uhr):
    """Sonst stünden zwei Screens übereinander, und der richtige läge unten."""
    _bis_zum_handbuch(fenster)
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] + 0.1)
    fenster.zeige(StelltImKonstruktor)
    assert isinstance(fenster.aktueller_screen, platzhalter.Handbuch)
    assert fenster.aktueller_screen.titel == "Handbuch – Level 2"
    assert len(fenster.inhalt.winfo_children()) == 1


def test_die_uebung_wird_erst_beim_anzeigen_gestellt(fenster, monkeypatch):
    """Mit dem Stellen beginnt die Uhr der Aufgabe – beim Bauen steht sie noch nicht da.

    Geprüft wird die Reihenfolge: Als der Screen angezeigt wird, darf noch
    keine Aufgabe laufen. Am Ergebnis allein sähe man den Unterschied nicht,
    weil ``zeige()`` auch einen zu früh stellenden Screen auffängt.
    """
    beobachtet = []
    echt = platzhalter.Uebung.beim_anzeigen

    def beobachten(screen):
        beobachtet.append(screen.durchlauf.spielstand.aktuelle_aufgabe)
        echt(screen)

    monkeypatch.setattr(platzhalter.Uebung, "beim_anzeigen", beobachten)
    _bis_zur_uebung(fenster)
    assert beobachtet == [None]
    assert fenster.durchlauf.spielstand.aktuelle_aufgabe is not None


# ───────────────────────────────────────────────────────────────────────────
# 5. Meldungen
# ───────────────────────────────────────────────────────────────────────────

def test_ohne_meldung_nimmt_die_zeile_keinen_platz_weg(fenster):
    assert fenster.meldung == ""
    assert fenster._meldungszeile.winfo_manager() == ""


def test_ein_speicherfehler_steht_in_der_meldungszeile(fenster, monkeypatch):
    _bis_zur_uebung(fenster)
    speicher = Speicher(fenster.durchlauf.protokoll)
    monkeypatch.setattr(fenster.durchlauf.protokoll, "schreiben", speicher)
    _klick(fenster, "Musterlösung")
    assert "nicht gespeichert" in fenster.meldung
    assert "erneut versucht" in fenster.meldung
    assert fenster._meldungszeile.winfo_manager() == "pack"

    speicher.gesperrt = False
    _klick(fenster, "Musterlösung")
    assert fenster.meldung == ""
    assert fenster._meldungszeile.winfo_manager() == ""
    assert len(_zeilen(fenster)) == 2


def test_ein_fehler_in_einem_knopf_wird_angezeigt(fenster, capsys):
    """Tkinter schriebe ihn nur auf die Konsole – die sieht im Klassenzimmer keiner."""

    def kaputt():
        raise RuntimeError("Probefehler")

    knopf = tk.Button(fenster.aktueller_screen, command=kaputt)
    knopf.invoke()
    assert "Unerwarteter Fehler" in fenster.meldung
    assert "Probefehler" in fenster.meldung
    assert "Probefehler" in capsys.readouterr().err
    assert fenster._takt_auftrag is not None


def test_ein_fehler_ohne_text_nennt_wenigstens_seine_art(fenster):
    def kaputt():
        raise RuntimeError()

    tk.Button(fenster.aktueller_screen, command=kaputt).invoke()
    assert "RuntimeError" in fenster.meldung


# ───────────────────────────────────────────────────────────────────────────
# 6. Schliessen
# ───────────────────────────────────────────────────────────────────────────

def test_waehrend_eines_levels_wird_vor_dem_schliessen_gefragt(fenster, wurzel):
    _bis_zur_uebung(fenster)
    fenster.frage_ja_nein = Rueckfrage(False)
    fenster.schliessen_anfragen()
    assert not fenster.ist_geschlossen
    assert wurzel.winfo_exists()
    assert fenster.durchlauf.spielstand.aktuelle_aufgabe is not None


def test_wer_bestaetigt_beendet_und_die_offene_aufgabe_steht_im_log(fenster, uhr):
    _bis_zur_uebung(fenster)
    uhr.weiter(33)
    fenster.frage_ja_nein = Rueckfrage(True)
    fenster.schliessen_anfragen()
    assert fenster.ist_geschlossen
    zeile = _zeilen(fenster)[0]
    assert zeile["abgebrochen"] == "ja"
    assert zeile["sekunden"] == "33"


def test_das_kreuz_am_fensterrand_ist_angeschlossen(fenster, wurzel):
    _bis_zur_uebung(fenster)
    fenster.frage_ja_nein = Rueckfrage(False)
    wurzel.tk.call(wurzel.protocol("WM_DELETE_WINDOW"))
    assert len(fenster.frage_ja_nein.fragen) == 1


def test_vor_dem_ersten_level_wird_nicht_gefragt(fenster, tmp_path):
    fenster.schliessen_anfragen()  # Rueckfrage() ohne Antwort schlüge fehl
    assert fenster.ist_geschlossen
    assert list(tmp_path.iterdir()) == []


def test_nach_dem_spielende_wird_nicht_gefragt(fenster):
    _bis_zur_uebung(fenster)
    for _ in range(3):
        _klick(fenster, "Level vorzeitig")
        if not isinstance(fenster.aktueller_screen, platzhalter.Abschluss):
            _klick(fenster, "Zu den Übungen")
    assert isinstance(fenster.aktueller_screen, platzhalter.Abschluss)
    fenster.schliessen_anfragen()
    assert fenster.ist_geschlossen


def test_scheitert_das_speichern_beim_schliessen_wird_nachgefragt(fenster, monkeypatch):
    _bis_zur_uebung(fenster)
    monkeypatch.setattr(
        fenster.durchlauf.protokoll, "schreiben", Speicher(fenster.durchlauf.protokoll)
    )
    fenster.frage_ja_nein = Rueckfrage(True)
    fenster.frage_nochmal = Rueckfrage(True, False)  # einmal nochmal, dann aufgeben
    fenster.schliessen_anfragen()
    assert len(fenster.frage_nochmal.fragen) == 2
    titel, text = fenster.frage_nochmal.fragen[0]
    assert "nicht gespeichert" in titel
    assert "Excel" in text
    assert fenster.ist_geschlossen


def test_ein_erneuter_versuch_beim_schliessen_rettet_die_daten(fenster, monkeypatch):
    _bis_zur_uebung(fenster)
    speicher = Speicher(fenster.durchlauf.protokoll)
    monkeypatch.setattr(fenster.durchlauf.protokoll, "schreiben", speicher)

    def datei_in_excel_geschlossen():
        speicher.gesperrt = False

    fenster.frage_ja_nein = Rueckfrage(True)
    fenster.frage_nochmal = Rueckfrage(True, vorher=datei_in_excel_geschlossen)
    fenster.schliessen_anfragen()
    assert fenster.ist_geschlossen
    assert _zeilen(fenster)[0]["abgebrochen"] == "ja"


def test_nach_dem_schliessen_laeuft_kein_takt_mehr(fenster):
    fenster.schliessen()
    assert fenster.ist_geschlossen
    assert fenster._takt_auftrag is None


class StolpertBeimVerlassen(Screen):
    def beim_verlassen(self):
        raise RuntimeError("Fehler beim Abräumen")


def test_das_fenster_geht_zu_auch_wenn_ein_screen_beim_abraeumen_stolpert(fenster, wurzel):
    fenster.zeige(StolpertBeimVerlassen)
    with pytest.raises(RuntimeError):
        fenster.schliessen()
    assert fenster.ist_geschlossen
    with pytest.raises(tk.TclError):
        wurzel.winfo_exists()


def test_zweimal_schliessen_schadet_nicht(fenster):
    fenster.schliessen()
    fenster.schliessen()
    assert fenster.ist_geschlossen


# ───────────────────────────────────────────────────────────────────────────
# 7. Ein Fenster, ein Durchlauf
# ───────────────────────────────────────────────────────────────────────────

def test_ein_zweiter_durchlauf_im_selben_fenster_ist_verboten(fenster):
    """Sonst mischten sich beim Wechsel die Messdaten zweier Personen."""
    _bis_zum_handbuch(fenster)
    with pytest.raises(ValueError) as fehler:
        fenster.starte_durchlauf(fenster.durchlauf.spielstand.figur)
    assert "neu starten" in str(fehler.value)


# ───────────────────────────────────────────────────────────────────────────
# 8. Der ganze Weg durch die Platzhalter
# ───────────────────────────────────────────────────────────────────────────

def _text_mit(fenster, wort):
    """Der Text des ersten Bedienelements im Screen, das ``wort`` enthält."""
    for kind in fenster.aktueller_screen.winfo_children():
        text = kind.cget("text")
        if wort in text:
            return text
    return ""


def test_der_platzhalterweg_laesst_sich_bis_zum_abschluss_durchklicken(fenster, uhr, tmp_path):
    _bis_zur_uebung(fenster)
    uhr.weiter(12)
    _klick(fenster, "Musterlösung")
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1])
    fenster._takt()                                   # Level 1 endet am Timer
    assert "Level 1 ist abgelaufen" in _text_mit(fenster, "abgelaufen")
    _klick(fenster, "Zu den Übungen")
    _klick(fenster, "Level vorzeitig")                # Level 2 endet vorzeitig
    _klick(fenster, "Zu den Übungen")
    _klick(fenster, "Level vorzeitig")                # Level 3 ebenso
    assert isinstance(fenster.aktueller_screen, platzhalter.Abschluss)
    assert fenster.durchlauf.spielstand.ist_durchgespielt
    assert fenster.kopfzeile == ("Geschafft", "", "")

    zeilen = _zeilen(fenster)
    assert [z["level"] for z in zeilen] == ["1", "1", "2", "3"]
    assert [z["levelende"] for z in zeilen] == ["zeitablauf", "zeitablauf", "vorzeitig", "vorzeitig"]
    assert [z["geloest"] for z in zeilen] == ["ja", "nein", "nein", "nein"]
    assert [z["abgebrochen"] for z in zeilen] == ["nein", "ja", "ja", "ja"]
    assert [p.name for p in tmp_path.iterdir()] == [fenster.durchlauf.protokoll.dateiname]

    _klick(fenster, "Spiel beenden")
    assert fenster.ist_geschlossen


# ───────────────────────────────────────────────────────────────────────────
# 9. main.py
# ───────────────────────────────────────────────────────────────────────────

def test_die_messdaten_landen_neben_main_py():
    """Nicht im Arbeitsverzeichnis – sonst hinge der Ort davon ab, wie gestartet wurde."""
    assert main.PROTOKOLLORDNER.is_absolute()
    assert main.PROTOKOLLORDNER == Path(main.__file__).resolve().parent / "logs"


def test_ohne_bildschirm_meldet_main_das_verstaendlich(monkeypatch, capsys):
    def ohne_anzeige(*_, **__):
        raise tk.TclError("no display name and no $DISPLAY environment variable")

    monkeypatch.setattr(tk, "Tk", ohne_anzeige)
    assert main.starte_spiel() == 1
    assert "keine Bildschirmanzeige" in capsys.readouterr().err


def test_ohne_tkinter_meldet_main_das_verstaendlich(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "tkinter", None)
    assert main.starte_spiel() == 1
    assert "tkinter" in capsys.readouterr().err


def test_main_oeffnet_das_spiel_mit_dem_startscreen(wurzel, monkeypatch):
    """Der echte Einstieg: Fenster auf, erster Screen da, Schleife zu."""
    geoeffnet = []
    echt_oeffnen = ablauf.oeffnen

    def oeffnen_und_merken(neue_wurzel, **kwargs):
        fenster = echt_oeffnen(neue_wurzel, **kwargs)
        geoeffnet.append((fenster, kwargs))
        return fenster

    monkeypatch.setattr(ablauf, "oeffnen", oeffnen_und_merken)
    monkeypatch.setattr(tk.Tk, "mainloop", lambda self, n=0: self.destroy())
    assert main.starte_spiel() == 0
    fenster, kwargs = geoeffnet[0]
    assert isinstance(fenster.aktueller_screen, ablauf.STARTSCREEN)
    assert kwargs["protokollordner"] == main.PROTOKOLLORDNER
