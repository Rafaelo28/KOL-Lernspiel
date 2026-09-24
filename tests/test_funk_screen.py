"""Tests für den Funk-Screen (Arbeitsplan 6.6): ui/funk.py.

Geprüft wird vor allem die Regel für lange Funksprüche aus CLAUDE.md, weil
dort am leichtesten etwas verwechselt wird: Beim Empfangen bleibt der ganze
Geheimtext sichtbar, beim Senden der ganze Klartext – und der Geheimtext steht
beim Senden **nie** da. Dazu, dass der Knopf für den Rest erst nach dem Anfang
kommt, auch nach drei Versuchen ohne Fortschritt, dass die Rückmeldung der
Spiellogik ankommt, dass man nachschlagen und zurückkehren kann und dass alles
aufs Glas passt.

Die Regeln selbst prüft die Spiellogik (``tests/test_bearbeitung.py``,
``tests/test_story.py``); hier geht es darum, dass der Screen sie zeigt.

Braucht eine Bildschirmanzeige, sonst übersprungen.
"""

import importlib.util
import time
from pathlib import Path

import pytest

tk = pytest.importorskip("tkinter")

from content import charaktere, story  # noqa: E402
from game import levelablauf  # noqa: E402
from game.bearbeitung import HINWEIS_FORTSCHRITT  # noqa: E402
from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN  # noqa: E402
from ui import ablauf, animation, funk, handbuch, stil, uebung  # noqa: E402

PROJEKT = Path(__file__).resolve().parent.parent
FIGUR = charaktere.VIC_MORENO


@pytest.fixture
def wurzel():
    """Ein verstecktes Tk-Fenster für die Tests – und am Ende wieder weg.

    Gibt es keine Bildschirmanzeige, werden die Tests übersprungen statt rot.
    """
    try:
        wurzel = tk.Tk()
    except tk.TclError as fehler:
        pytest.skip(f"Keine Bildschirmanzeige: {fehler}")
    wurzel.withdraw()
    yield wurzel
    try:
        wurzel.destroy()
    except tk.TclError:
        pass


class Uhr:
    """Eine Uhr zum Stellen: Sie gibt zurück, was in ``jetzt`` steht."""

    def __init__(self):
        """Beginnt bei null Sekunden."""
        self.jetzt = 0.0

    def __call__(self):
        """Das Spiel fragt die Uhr wie eine Funktion: ``zeitgeber()``."""
        return self.jetzt


@pytest.fixture
def uhr():
    """Die stellbare Uhr – ohne sie liefe im Test die echte Zeit mit."""
    return Uhr()


@pytest.fixture
def fenster(wurzel, tmp_path, massstab, uhr):
    """Ein Hauptfenster an der stellbaren Uhr, das ins Testverzeichnis schreibt."""
    fenster = ablauf.oeffnen(wurzel, zeitgeber=uhr, protokollordner=tmp_path, massstab=massstab)
    fenster.frage_ja_nein = lambda *_, **__: True
    return fenster


def _zum_funkgeraet(fenster, level=1):
    """Spielt vom Startbildschirm bis zum ersten Funkspruch des Levels.

    Seit Phase 7 überspringt kein Knopf mehr ein Level: Der Weg dorthin führt
    über die Aufgaben, also werden sie hier gelöst – Übungen wie Funksprüche.
    Die Uhr steht dabei still, deshalb gilt jede Übung als schnell gelöst und
    es kommen alle Zusatzaufgaben des Levels dazu: achtzehn Übungen, bis der
    Abschnitt des Pools aufgebraucht ist. Die Schrittgrenze unten ist dafür
    grosszügig gewählt – sie soll nur eine Endlosschleife abfangen.
    """
    fenster.aktueller_screen._feld.insert(0, "1-12")
    fenster.aktueller_screen.starten()
    fenster.aktueller_screen.waehle(FIGUR)
    fenster.aktueller_screen.bestaetigen()
    for _ in story.INTRO.absaetze:
        fenster.aktueller_screen.weiter()
    for _ in range(200):
        screen = fenster.aktueller_screen
        if isinstance(screen, funk.Funk):
            if screen.funkspruch.level == level:
                return screen
            _loesen(screen)
        elif isinstance(screen, uebung.Uebung):
            _uebung_loesen(screen)
        else:
            screen.weiter()                                # das Handbuch des Levels
    raise AssertionError(f"Der erste Funkspruch von Level {level} kam nie.")


def _uebung_loesen(screen):
    """Löst die Übung, die gerade dasteht, richtig und geht weiter."""
    _tippen(screen, screen.aufgabe.loesung)
    screen.pruefen()
    screen.weiter()


def _funkspruch(fenster, level, kennung):
    """Geht zu den Funksprüchen des Levels und löst sie, bis der mit dieser Kennung dran ist."""
    screen = _zum_funkgeraet(fenster, level)
    while screen.funkspruch.kennung != kennung:
        _loesen(screen)
        screen = fenster.aktueller_screen
    return screen


def _loesen(screen):
    """Löst den Funkspruch am Gerät ganz: Nachricht abwarten, tippen, prüfen, Rest auflösen, weiter."""
    screen.anzeige_vervollstaendigen()
    _tippen(screen, screen.aufgabe.loesung)
    screen.pruefen()
    if screen.restknopf_sichtbar:
        screen.rest_freigeben()
    screen.pruefen()                                   # "Weiter"


def _tippen(screen, text):
    """Schreibt ``text`` in die Eingabezeile – wie von Hand eingetippt."""
    screen._feld.delete(0, "end")
    screen._feld.insert(0, text)


def _falsch(loesung):
    """Eine falsche Eingabe, die nie näher an die Lösung kommt – immer dieselbe."""
    return "".join(" " if z == " " else ("Q" if z != "Q" else "Z") for z in loesung)


def _alle_texte(screen):
    """Alles, was gerade zu lesen ist: auf der Leinwand und über dem Gerät."""
    leinwand = screen.buch
    texte = [leinwand.itemcget(e, "text") for e in leinwand.find_all() if leinwand.type(e) == "text"]
    return texte + [screen.erzaehlung]


def _eine_zeile(texte):
    """Klebt die Texte zu einer Zeile zusammen, ohne doppelte Leerzeichen."""
    return " ".join(" ".join(texte).split())


def _warten(wurzel, bedingung, sekunden=5):
    """Lässt das Fenster arbeiten, bis ``bedingung()`` stimmt – und bricht nach einer Weile ab.

    Gebraucht für alles, was im Takt passiert, etwa die eintreffende Nachricht.
    """
    ende = time.monotonic() + sekunden
    while not bedingung():
        assert time.monotonic() < ende, "Das hat zu lange gedauert."
        wurzel.update()
        time.sleep(0.005)


# ── Der Weg zum Funkgerät ──────────────────────────────────────────────────

def test_die_funksprueche_eines_levels_kommen_der_reihe_nach_danach_das_naechste_level(fenster):
    screen = _zum_funkgeraet(fenster, 1)
    assert screen.funkspruch is story.FUNKSPRUCH_ERSTER_RUF
    assert screen.titel == "Funkgerät – Level 1"
    _loesen(screen)
    assert fenster.aktueller_screen.funkspruch is story.FUNKSPRUCH_BOB_ERSTE_ANTWORT
    _loesen(fenster.aktueller_screen)
    assert isinstance(fenster.aktueller_screen, handbuch.Handbuch)
    assert fenster.aktueller_screen.seite.level == 2
    kennungen = [b.aufgabe.kennung for b in fenster.durchlauf.spielstand.erledigte_aufgaben]
    assert kennungen[-2:] == ["erster_ruf", "bob_erste_antwort"]


def test_vor_dem_funkspruch_sind_die_uebungen_des_levels_erledigt(fenster):
    """Erst üben, dann funken – so steht es im Konzept (Arbeitsplan 7.1)."""
    screen = _zum_funkgeraet(fenster, 1)
    uebungen = [b for b in fenster.durchlauf.spielstand.erledigte_aufgaben
                if b.aufgabe.quelle == "uebung"]
    assert len(uebungen) >= levelablauf.BASIS_UEBUNGEN_JE_LEVEL
    assert not any(b.abgebrochen for b in uebungen), "Keine Übung bleibt unterwegs liegen."
    assert screen.aufgabe.kennung == "erster_ruf"


# ── Empfangen: der ganze Geheimtext, der Anfang hervorgehoben ──────────────

@pytest.mark.parametrize("massstab", [1, 1.5])
def test_beim_empfangen_steht_der_ganze_geheimtext_da_und_der_anfang_leuchtet(fenster):
    screen = _funkspruch(fenster, 1, "bob_erste_antwort")
    screen.anzeige_vervollstaendigen()
    aufgabe = screen.aufgabe
    assert _eine_zeile(screen.glastexte("nachricht")) == aufgabe.anzeigetext
    assert _eine_zeile(screen.glastexte("anfang")) == aufgabe.anzeigetext[:len(aufgabe.loesung)]
    assert _eine_zeile(screen.glastexte("rest")) == aufgabe.anzeigetext[len(aufgabe.loesung):].strip()
    for element in screen.buch.find_withtag("anfang"):
        assert screen.buch.itemcget(element, "fill") == stil.FARBE_LEUCHTSCHRIFT_HELL
    for element in screen.buch.find_withtag("rest"):
        assert screen.buch.itemcget(element, "fill") == stil.FARBE_LEUCHTSCHRIFT_MATT
    assert screen.glastexte("kopf") == ["EMPFANG · ZENTRALE"]
    assert screen.glastexte("verfahren") == ["Caesar · Schlüssel 3"]
    assert screen.glastexte("auftrag") == [funk.AUFTRAG[(story.EMPFANGEN, True)]]
    assert screen.lampe_leuchtet("empfang") and not screen.lampe_leuchtet("senden")


def test_eine_empfangene_nachricht_kommt_zeichen_fuer_zeichen_herein(fenster, wurzel):
    screen = _funkspruch(fenster, 1, "bob_erste_antwort")
    assert not screen.eingetippt
    anfangs = len(_eine_zeile(screen.glastexte("nachricht")))
    assert anfangs < len(screen.aufgabe.anzeigetext)
    _warten(wurzel, lambda: screen.eingetippt)
    assert _eine_zeile(screen.glastexte("nachricht")) == screen.aufgabe.anzeigetext
    assert screen.lampe_leuchtet("empfang")


def test_auch_die_zweite_zeile_kommt_buchstabe_fuer_buchstabe(fenster):
    """Beim Umbruch fällt ein Leerzeichen weg – das darf die Zählung nicht verschieben."""
    screen = _funkspruch(fenster, 1, "bob_erste_antwort")
    text = screen.aufgabe.anzeigetext
    assert len(screen._zeilen) >= 2
    for anzahl in range(len(screen._zeilen[0]) - 2, len(text) + 1, 3):
        screen._getippt = anzahl
        screen._nachricht_zeichnen()
        assert _eine_zeile(screen.glastexte("nachricht")) == _eine_zeile([text[:anzahl]]), anzahl


def test_beim_abriss_mitten_im_hereinkommen_bleibt_nichts_zurueck(fenster, wurzel):
    screen = _funkspruch(fenster, 1, "bob_erste_antwort")
    assert screen._auftraege
    screen._nachschlagen()
    assert not screen._auftraege
    ende = time.monotonic() + 0.3
    while time.monotonic() < ende:
        wurzel.update()
    assert fenster.meldung == ""


# ── Senden: der ganze Klartext – der Geheimtext nie ────────────────────────

@pytest.mark.parametrize("kennung, level", [("erster_ruf", 1), ("standort", 3)])
def test_beim_senden_steht_der_klartext_da_und_nie_der_geheimtext(fenster, kennung, level):
    """CLAUDE.md: Der Geheimtext ist genau das, was eingetippt werden soll – wer ihn sieht, schreibt ab."""
    screen = _funkspruch(fenster, level, kennung)
    assert screen.eingetippt                                  # die eigene Nachricht muss nicht erst hereinkommen
    aufgabe = screen.aufgabe
    geheim = aufgabe.vollstaendige_loesung
    assert _eine_zeile(screen.glastexte("nachricht")) == aufgabe.anzeigetext
    assert screen.glastexte("kopf") == ["SENDEN"]
    assert screen.knopftext == funk.KNOPF_SENDEN

    def geheimtext_zu_sehen():
        """Steht der Geheimtext irgendwo auf dem Bildschirm? Beim Senden darf er das nie."""
        alles = _eine_zeile(_alle_texte(screen)).replace(" ", "")
        return geheim.replace(" ", "") in alles or aufgabe.loesung.replace(" ", "") in alles

    assert not geheimtext_zu_sehen()
    _tippen(screen, _falsch(aufgabe.loesung))
    screen.pruefen()
    assert not geheimtext_zu_sehen()
    assert not screen.lampe_leuchtet("senden")               # falsch Verschlüsseltes geht nicht raus
    _tippen(screen, aufgabe.loesung.lower())
    screen.pruefen()
    if screen.restknopf_sichtbar:
        assert not screen.lampe_leuchtet("senden")
        screen.rest_freigeben()
    assert screen.lampe_leuchtet("senden")
    assert funk.GESENDET in screen.glastexte("rueckmeldung")
    # Gesendet ist die ganze Nachricht – aber zu sehen ist nur, was selbst eingetippt wurde.
    assert geheim.replace(" ", "") not in _eine_zeile(_alle_texte(screen)).replace(" ", "")


def test_nach_drei_versuchen_steht_beim_senden_die_loesung_da(fenster):
    """Projektregel 2 gilt auch hier – die Aufgabe ist danach vorbei."""
    screen = _zum_funkgeraet(fenster, 1)
    screen.anzeige_vervollstaendigen()
    for _ in range(3):
        _tippen(screen, _falsch(screen.aufgabe.loesung))
        screen.pruefen()
    assert screen.ist_beendet
    assert screen.glastexte("rueckmeldung")[0] == uebung.LOESUNGSZEILE.format(loesung=screen.aufgabe.loesung)
    assert funk.GESENDET in screen.glastexte("rueckmeldung") and screen.lampe_leuchtet("senden")
    assert screen.knopftext == funk.KNOPF_WEITER


# ── Rückmeldung ────────────────────────────────────────────────────────────

def test_eine_falsche_eingabe_nennt_die_stelle_und_unterwellt_sie_in_der_nachricht(fenster):
    screen = _funkspruch(fenster, 1, "bob_erste_antwort")
    screen.anzeige_vervollstaendigen()
    loesung = screen.aufgabe.loesung
    falsch = loesung[:3] + ("Q" if loesung[3] != "Q" else "Z") + loesung[4:]     # im 2. Wort der 1. Buchstabe
    _tippen(screen, falsch)
    screen.pruefen()
    rueckmeldung = _eine_zeile(screen.glastexte("rueckmeldung"))
    assert "2. Wort" in rueckmeldung and uebung.versuchstext(2) in rueckmeldung
    farben = {screen.buch.itemcget(e, "fill") for e in screen.buch.find_withtag("rueckmeldung")}
    assert stil.FARBE_LEUCHTSCHRIFT_WARNUNG in farben
    # Unterwellt ist der vierte Buchstabe der ersten Zeile – der erste des zweiten Worts.
    (welle,) = screen.buch.find_withtag("fehlerstelle")
    x0, _, x1, _ = screen.buch.bbox(welle)
    links = screen._glas()[0]
    zeichenbreite = screen.schrift.measure("M")
    assert links + 3 * zeichenbreite <= (x0 + x1) / 2 <= links + 4 * zeichenbreite


def test_ein_fehler_in_der_zweiten_zeile_wird_dort_unterwellt(fenster):
    """Wer die ganze Nachricht eintippt, bekommt die Stelle auch hinter dem Umbruch gezeigt."""
    screen = _funkspruch(fenster, 1, "bob_erste_antwort")
    screen.anzeige_vervollstaendigen()
    ganz = screen.aufgabe.vollstaendige_loesung
    stelle = len(screen._zeilen[0]) + 1                     # der erste Buchstabe der zweiten Zeile
    _tippen(screen, ganz[:stelle] + ("Q" if ganz[stelle] != "Q" else "Z") + ganz[stelle + 1:])
    screen.pruefen()
    (welle,) = screen.buch.find_withtag("fehlerstelle")
    x0, y0, x1, _ = screen.buch.bbox(welle)
    zeile = screen.schrift.metrics("linespace")
    assert screen._nachricht_oben + zeile <= y0 <= screen._nachricht_oben + 2 * zeile
    assert (x0 + x1) / 2 <= screen._glas()[0] + screen.schrift.measure("M")


def test_wer_naeher_drankommt_bekommt_den_hinweis_und_behaelt_seine_versuche(fenster):
    screen = _funkspruch(fenster, 1, "bob_erste_antwort")
    screen.anzeige_vervollstaendigen()
    loesung = screen.aufgabe.loesung
    _tippen(screen, _falsch(loesung))
    screen.pruefen()
    _tippen(screen, loesung[:2] + _falsch(loesung)[2:])
    screen.pruefen()
    assert HINWEIS_FORTSCHRITT in _eine_zeile(screen.glastexte("rueckmeldung"))


# ── Der Rest einer langen Nachricht ────────────────────────────────────────

@pytest.mark.parametrize("geloest", [True, False], ids=["gelöst", "aufgelöst"])
def test_der_knopf_fuer_den_rest_kommt_nach_dem_anfang_und_gibt_die_ganze_nachricht_frei(fenster, geloest):
    screen = _funkspruch(fenster, 1, "bob_erste_antwort")
    screen.anzeige_vervollstaendigen()
    hoehe = int(screen._erzaehlung.cget("height"))
    assert not screen.restknopf_sichtbar
    for _ in range(1 if geloest else 3):
        _tippen(screen, screen.aufgabe.loesung if geloest else _falsch(screen.aufgabe.loesung))
        screen.pruefen()
    assert screen.ist_beendet and screen.restknopf_sichtbar
    assert screen._restknopf.cget("text") == story.BESCHRIFTUNG_REST[story.EMPFANGEN]
    assert not screen._knopf.winfo_manager()                # erst der Rest, dann weiter
    screen.pruefen()                                       # Return im Feld tut nichts Falsches
    assert fenster.aktueller_screen is screen
    screen.rest_freigeben()
    assert screen.erzaehlung == story.FUNKSPRUCH_BOB_ERSTE_ANTWORT.weiterrechnen
    assert int(screen._erzaehlung.cget("height")) == hoehe  # der Text darüber springt nicht
    assert screen.glastexte("rueckmeldung")[0] == funk.GANZE_NACHRICHT
    assert _eine_zeile(screen.glastexte("rueckmeldung")[1:]) == story.FUNKSPRUCH_BOB_ERSTE_ANTWORT.klartext
    assert not screen.restknopf_sichtbar and screen.knopftext == funk.KNOPF_WEITER
    assert fenster.durchlauf.spielstand.aktuelle_bearbeitung.darf_weiterrechnen is False
    screen.rest_freigeben()                                # ein zweiter Druck tut nichts
    assert screen.knopftext == funk.KNOPF_WEITER


@pytest.mark.parametrize("langer_text", ["einleitung", "weiterrechnen", "hinweis"])
def test_ueber_dem_geraet_ist_von_anfang_an_platz_fuer_den_laengsten_text(fenster, langer_text):
    """Sonst spränge das Gerät nach unten, sobald ein längerer Text darüberkommt.

    Nacheinander stehen dort die Einleitung, der Hinweis aus der Geschichte und
    der Erzähltext zum Rest – der Platz richtet sich nach dem längsten.
    """
    from tkinter import font as tkfont

    from ui.buchsatz import umbrechen

    _zum_funkgeraet(fenster, 1)
    fenster.durchlauf.aufgabe_abschliessen()                  # der erste Ruf – für den Probefunkspruch Platz machen
    lang = " ".join([story.FUNKSPRUCH_BOB_ERSTE_ANTWORT.weiterrechnen] * 3)
    kurz = "Es rauscht."
    texte = {feld: (lang if feld == langer_text else kurz) for feld in ("einleitung", "weiterrechnen")}
    funkspruch = story.FUNKSPRUCH_BOB_ERSTE_ANTWORT._replace(kennung="probe", **texte)
    screen = fenster.zeige(funk.Funk, funkspruch=funkspruch, danach=lambda f: None,
                           hinweis=lang if langer_text == "hinweis" else "")
    zeilen = len(umbrechen(lang, tkfont.nametofont(stil.SCHRIFT_ERZAEHLUNG), int(screen._erzaehlung.cget("wraplength"))))
    assert zeilen >= 2 and int(screen._erzaehlung.cget("height")) >= zeilen


def test_ohne_teilaufgabe_gibt_es_keinen_knopf_fuer_den_rest(fenster):
    screen = _funkspruch(fenster, 3, "bob_zweite_antwort")
    screen.anzeige_vervollstaendigen()
    assert screen.glastexte("auftrag") == [funk.AUFTRAG[(story.EMPFANGEN, False)]]
    assert _eine_zeile(screen.glastexte("anfang")) == screen.aufgabe.anzeigetext
    assert not screen.glastexte("rest")
    _tippen(screen, screen.aufgabe.loesung)
    screen.pruefen()
    assert not screen.restknopf_sichtbar and screen.knopftext == funk.KNOPF_WEITER
    assert screen.glastexte("rueckmeldung") == [uebung.LOB]


# ── Werkzeug, Lineal, Nachschlagen ─────────────────────────────────────────

def test_links_liegt_das_werkzeug_des_levels(fenster):
    screen = _zum_funkgeraet(fenster, 1)
    assert screen.lineal is None
    assert "Das Alphabet zum Abzählen" in screen.buch.texte("links")


def test_in_level_3_liegt_das_quadrat_mit_lineal_daneben_und_die_klicks_zaehlen(fenster, ausloesen):
    screen = _zum_funkgeraet(fenster, 3)
    assert screen.lineal is not None
    lineal = screen.lineal
    x0, y0, _, _ = screen.buch.flaeche("links")
    feld = lineal.quadrat.feld
    x, y = round(x0 + lineal.quadrat.x + 0.5 * feld), round(y0 + lineal.quadrat.y + 18.5 * feld)
    ausloesen(screen.buch, "<Button-1>", x=x, y=y)                 # links auf das R
    assert lineal.zeile == 17 and lineal.spalte is None
    assert fenster.durchlauf.spielstand.aktuelle_bearbeitung.lineal_klicks == 1


def test_nachschlagen_und_zurueck_zum_selben_funkspruch(fenster, uhr):
    screen = _funkspruch(fenster, 1, "bob_erste_antwort")
    aufgabe = screen.aufgabe
    _tippen(screen, "JA WI")
    screen._nachschlagen()
    buch = fenster.aktueller_screen
    assert isinstance(buch, handbuch.Handbuch) and buch.knopftext == handbuch.KNOPF_ZURUECK
    uhr.jetzt += 30
    buch.weiter()
    zurueck = fenster.aktueller_screen
    assert isinstance(zurueck, funk.Funk) and zurueck.aufgabe is aufgabe
    assert zurueck.eingetippt                                  # kein zweites Hereinkommen
    assert zurueck.eingabe == "JA WI"
    assert fenster.durchlauf.spielstand.aktuelle_aufgabe is aufgabe


def test_der_hinweis_ueberlebt_das_nachschlagen(fenster):
    """Beim abgefangenen Funkspruch steht der Satz zur Häufigkeitsanalyse über dem Gerät.

    Genau dort wird am ehesten nachgeschlagen (die Geheimtabelle steht im
    Handbuch) – und genau dort verschwand der Satz beim Zurückkommen, weil
    der neue Screen ohne ihn gebaut wurde.
    """
    hinweis = " ".join(story.HINWEIS_HAEUFIGKEITSANALYSE.absaetze)
    screen = _funkspruch(fenster, 2, "verfolger")
    screen.anzeige_vervollstaendigen()
    assert screen.erzaehlung == hinweis
    screen._nachschlagen()
    fenster.aktueller_screen.weiter()
    zurueck = fenster.aktueller_screen
    zurueck.anzeige_vervollstaendigen()
    assert zurueck.hinweis == hinweis
    assert zurueck.erzaehlung == hinweis


def test_auch_beim_mitlesen_steht_der_hinweis_da(fenster):
    """Wer den abgefangenen Funkspruch nur nachliest, hat denselben langen Geheimtext vor sich.

    Der Satz gehört zu diesem Bild (Arbeitsplan 7.2) – wer aus der Zeit
    lief, bekam ihn vorher nie zu sehen.
    """
    fenster.starte_durchlauf(FIGUR, pseudonym="1-12")
    ablauf.funkspruch_nachlesen(fenster, story.FUNKSPRUCH_VERFOLGER, danach=lambda _fenster: None)
    screen = fenster.aktueller_screen
    assert screen.nur_lesen
    assert screen.erzaehlung == " ".join(story.HINWEIS_HAEUFIGKEITSANALYSE.absaetze)


def test_nach_dem_rest_zeigt_das_zurueckkehren_wieder_die_ganze_nachricht(fenster):
    screen = _funkspruch(fenster, 1, "bob_erste_antwort")
    screen.anzeige_vervollstaendigen()
    _tippen(screen, screen.aufgabe.loesung)
    screen.pruefen()
    screen.rest_freigeben()
    screen._nachschlagen()
    fenster.aktueller_screen.weiter()
    zurueck = fenster.aktueller_screen
    assert zurueck.ist_beendet and not zurueck.restknopf_sichtbar
    assert zurueck.erzaehlung == story.FUNKSPRUCH_BOB_ERSTE_ANTWORT.weiterrechnen
    assert _eine_zeile(zurueck.glastexte("rueckmeldung")[1:]) == story.FUNKSPRUCH_BOB_ERSTE_ANTWORT.klartext
    assert zurueck.knopftext == funk.KNOPF_WEITER


def test_laeuft_die_zeit_am_funkgeraet_ab_kommt_das_naechste_level(fenster, uhr):
    screen = _zum_funkgeraet(fenster, 1)
    uhr.jetzt += DAUER_JE_LEVEL_SEKUNDEN[1]
    fenster._takt()
    # Was nicht mehr drankam, steht davor noch zum Mitlesen da (ui/ablauf.py).
    while isinstance(fenster.aktueller_screen, funk.Funk) and fenster.aktueller_screen.nur_lesen:
        fenster.aktueller_screen.weiter()
    assert isinstance(fenster.aktueller_screen, handbuch.Handbuch)
    assert fenster.aktueller_screen.seite.level == 2
    assert fenster.durchlauf.spielstand.erledigte_aufgaben[-1].aufgabe is screen.aufgabe


# ── Platz auf dem Glas und auf dem Bildschirm ──────────────────────────────

@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("level", [1, 2, 3])
def test_alles_passt_aufs_glas_auch_die_laengste_rueckmeldung(fenster, level):
    """Fehlermeldung, Fortschrittshinweis und Versuche auf einmal – bei jedem Funkspruch des Levels."""
    screen = _zum_funkgeraet(fenster, level)
    while isinstance(screen, funk.Funk):
        screen.anzeige_vervollstaendigen()
        loesung = screen.aufgabe.loesung
        for eingabe in (_falsch(loesung), loesung[:2] + _falsch(loesung)[2:]):
            _tippen(screen, eingabe)
            screen.pruefen()
            _pruefen_ob_alles_aufs_glas_passt(screen)
        _tippen(screen, loesung)
        screen.pruefen()
        if screen.restknopf_sichtbar:
            screen.rest_freigeben()
        _pruefen_ob_alles_aufs_glas_passt(screen)
        screen.pruefen()
        screen = fenster.aktueller_screen


def _pruefen_ob_alles_aufs_glas_passt(screen):
    """Prüft, dass kein Text über den Rand des Glases hinausragt."""
    luft = 2
    gx, gy = screen.px(funk.GERAET[0]), screen.px(funk.GERAET[1])
    x0, y0, x1, y1 = (gx + screen.px(funk.GLAS[0]), gy + screen.px(funk.GLAS[1]),
                      gx + screen.px(funk.GLAS[2]), gy + screen.px(funk.GLAS[3]))
    for element in screen.buch.find_withtag("anzeige"):
        a, b, c, d = screen.buch.bbox(element)
        assert x0 - luft <= a and c <= x1 + luft and y0 - luft <= b and d <= y1 + luft, (
            f"{screen.funkspruch.kennung}: {screen.buch.gettags(element)} liegt bei {(a, b, c, d)}, "
            f"das Glas ist {(x0, y0, x1, y1)}")


@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("level", [1, 2, 3])
def test_der_screen_passt_ins_fenster(fenster, wurzel, platz, level):
    """Bei jedem Funkspruch – auch bei dem mit der längsten Einleitung, dem Feind-Funkspruch.

    Über dem Gerät steht der längere von Einleitung und Erzähltext zum Rest;
    beide werden mitgeprüft.
    """
    screen = _zum_funkgeraet(fenster, level)
    while isinstance(screen, funk.Funk):
        for text in (screen.funkspruch.einleitung, screen.funkspruch.weiterrechnen or ""):
            screen._erzaehlung.configure(text=text)
            wurzel.update_idletasks()
            assert wurzel.winfo_reqwidth() <= platz[0], f"{screen.funkspruch.kennung}: zu breit"
            assert wurzel.winfo_reqheight() <= platz[1], f"{screen.funkspruch.kennung}: zu hoch"
        screen.anzeige_vervollstaendigen()
        _tippen(screen, screen.aufgabe.loesung)
        screen.pruefen()
        if screen.restknopf_sichtbar:
            screen.rest_freigeben()
        screen.pruefen()
        screen = fenster.aktueller_screen


def _rendern():
    """Lädt ``grafik/rendern.py`` nach – es gehört zu keinem Paket und lässt sich nicht einfach importieren."""
    spec = importlib.util.spec_from_file_location("rendern", PROJEKT / "grafik" / "rendern.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_glas_und_laempchen_liegen_im_bild_dort_wo_das_spiel_schreibt(massstab):
    """ui/funk.py und grafik/funkgeraet_zeichnen.py müssen dieselben Stellen meinen.

    Im fertigen Bild: Auf dem Glas ist es überall dunkel und deckend, in der
    Mitte der Lämpchen auch – und neben dem Gerät ist das Bild durchsichtig.
    """
    ordner = animation.ANIMATIONSORDNER / "funkgeraet" / animation.unterordner(massstab)
    bild = _rendern().png_lesen((ordner / "hintergrund.png").read_bytes())
    assert bild.kanaele == 4

    def punkt(x, y):
        """Die vier Farbwerte eines Bildpunkts (Rot, Grün, Blau, Deckkraft)."""
        return tuple(bild.zeilen[y][x * 4:x * 4 + 4])

    x0, y0, x1, y1 = (stil.skaliert(wert, massstab) for wert in funk.GLAS)
    rand = stil.skaliert(funk.GLASRAND, massstab)
    for i in range(9):
        for j in range(9):
            r, g, b, a = punkt(x0 + rand + (x1 - x0 - 2 * rand) * i // 8, y0 + rand + (y1 - y0 - 2 * rand) * j // 8)
            assert a == 255 and max(r, g, b) < 60, (i, j, r, g, b, a)
    for x, y, _ in (funk.LAMPE_EMPFANG, funk.LAMPE_SENDEN):
        r, g, b, a = punkt(stil.skaliert(x, massstab), stil.skaliert(y, massstab))
        assert a == 255 and max(r, g, b) < 70
    assert punkt(2, 2)[3] == 0


def test_die_nachricht_kommt_auch_nach_einem_fehler_zu_ende(fenster, wurzel, monkeypatch):
    """Sonst bliebe der Geheimtext auf halber Strecke stehen – und mit ihm die Aufgabe."""
    screen = _funkspruch(fenster, 1, "bob_erste_antwort")
    stolpert = [True]
    echt = funk.Funk._nachricht_zeichnen

    def einmal_stolpern(self):
        """Lässt das Zeichnen genau einmal misslingen und arbeitet danach normal weiter."""
        if stolpert:
            stolpert.clear()
            raise RuntimeError("Probe: das Zeichnen misslingt einmal")
        echt(self)

    monkeypatch.setattr(funk.Funk, "_nachricht_zeichnen", einmal_stolpern)
    _warten(wurzel, lambda: screen.eingetippt)
    assert not stolpert, "Der Fehler muss wirklich aufgetreten sein."
    assert _eine_zeile(screen.glastexte("nachricht")) == screen.aufgabe.anzeigetext
