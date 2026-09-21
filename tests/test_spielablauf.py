"""Tests für den Weg durch ein Level (Arbeitsplan Phase 7): ui/ablauf.py.

Die Regeln dahinter prüft ``tests/test_levelablauf.py`` ohne Bildschirm. Hier
geht es darum, dass die Oberfläche sie auch befolgt: dass nach dem Handbuch
geübt wird, dass danach das Funkgerät kommt, dass eine Zusatzaufgabe als
solche gestellt wird – und dass die Funksprüche auch dann drankommen, wenn
jemand bei den Übungen trödelt.

Braucht eine Bildschirmanzeige, sonst übersprungen.
"""

import time

import pytest

tk = pytest.importorskip("tkinter")

from content import charaktere, story  # noqa: E402
from game import levelablauf, zusatzaufgaben  # noqa: E402
from game.aufgabe import QUELLE_FUNKSPRUCH  # noqa: E402
from game.spielstand import LEVELENDE_VORZEITIG  # noqa: E402
from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN  # noqa: E402
from ui import abschluss, ablauf, erzaehlszene, funk, handbuch, uebung  # noqa: E402

FIGUR = charaktere.VIC_MORENO


class Uhr:
    def __init__(self):
        self.jetzt = 0.0

    def __call__(self):
        return self.jetzt

    def weiter(self, sekunden):
        self.jetzt += sekunden


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
        pass


@pytest.fixture
def uhr():
    return Uhr()


@pytest.fixture
def fenster(wurzel, tmp_path, massstab, uhr):
    fenster = ablauf.oeffnen(wurzel, zeitgeber=uhr, protokollordner=tmp_path, massstab=massstab)
    fenster.frage_ja_nein = lambda *_, **__: True
    return fenster


@pytest.fixture
def bei_der_uebung(fenster):
    """Level 1 läuft, die erste Übung steht da."""
    fenster.aktueller_screen._feld.insert(0, "1-12")
    fenster.aktueller_screen.starten()
    fenster.aktueller_screen.waehle(FIGUR)
    fenster.aktueller_screen.bestaetigen()
    for _ in story.INTRO.absaetze:
        fenster.aktueller_screen.weiter()
    assert isinstance(fenster.aktueller_screen, handbuch.Handbuch)
    fenster.aktueller_screen.weiter()
    return fenster.aktueller_screen


def _loesen(fenster, sekunden=0.0, uhr=None):
    """Löst die laufende Aufgabe – Übung oder Funkspruch – und geht weiter."""
    if uhr is not None:
        uhr.weiter(sekunden)
    screen = fenster.aktueller_screen
    if hasattr(screen, "anzeige_vervollstaendigen"):
        screen.anzeige_vervollstaendigen()
    screen._feld.delete(0, "end")
    screen._feld.insert(0, screen.aufgabe.loesung)
    screen.pruefen()
    if getattr(screen, "restknopf_sichtbar", False):
        screen.rest_freigeben()
    screen.weiter()
    return fenster.aktueller_screen


#: So lange dauert eine Aufgabe, ohne dass sie als "schnell gelöst" gilt.
NORMALTEMPO = 60.0


def _eine_zeile(texte):
    """Texte zu einer Zeile zusammengezogen – egal, wo umbrochen wurde."""
    return " ".join(" ".join(texte).split())


def _spielen_bis(fenster, uhr, bedingung, hoechstens=40):
    """Löst Aufgabe um Aufgabe, bis ein Screen die Bedingung erfüllt."""
    for _ in range(hoechstens):
        screen = fenster.aktueller_screen
        if bedingung(screen):
            return screen
        if getattr(screen, "aufgabe", None) is None:
            screen.weiter()                              # Handbuch
        else:
            _loesen(fenster, NORMALTEMPO, uhr)
    raise AssertionError("Der gesuchte Screen kam nie.")


def _level_ablaufen_lassen(fenster, uhr, level):
    """Lässt das Zeitfenster eines Levels ablaufen, ohne etwas zu lösen."""
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[level])
    fenster._takt()


# ───────────────────────────────────────────────────────────────────────────
# 1. Die Reihenfolge im Level
# ───────────────────────────────────────────────────────────────────────────

def test_nach_dem_handbuch_kommt_die_erste_uebung(bei_der_uebung):
    screen = bei_der_uebung
    assert isinstance(screen, uebung.Uebung)
    assert screen.aufgabe.level == 1 and not screen.aufgabe.zusatzaufgabe


def test_nach_den_uebungen_kommt_das_funkgeraet(fenster, bei_der_uebung, uhr):
    """Erst die Pflichtübungen, dann Zusatzaufgaben, solange Zeit ist – dann das Gerät."""
    for _ in range(levelablauf.BASIS_UEBUNGEN_JE_LEVEL):
        assert isinstance(fenster.aktueller_screen, uebung.Uebung)
        assert not fenster.aktueller_screen.aufgabe.zusatzaufgabe
        _loesen(fenster, NORMALTEMPO, uhr)
    screen = _spielen_bis(fenster, uhr, lambda s: isinstance(s, funk.Funk))
    assert screen.funkspruch is story.FUNKSPRUCH_ERSTER_RUF
    stand = fenster.durchlauf.spielstand
    assert stand.uebungen_im_level(1) == levelablauf.BASIS_UEBUNGEN_JE_LEVEL
    assert stand.zusatzaufgaben_im_level(1) > 0, "Die Restzeit wurde mit Übungen gefüllt."


def test_nach_dem_letzten_funkspruch_beginnt_das_naechste_level(fenster, bei_der_uebung, uhr):
    while not isinstance(fenster.aktueller_screen, handbuch.Handbuch):
        _loesen(fenster, NORMALTEMPO, uhr)
    assert fenster.aktueller_screen.seite.level == 2
    assert fenster.durchlauf.spielstand.aktuelles_level == 2
    kennungen = [b.aufgabe.kennung for b in fenster.durchlauf.spielstand.erledigte_aufgaben]
    assert kennungen[-2:] == ["erster_ruf", "bob_erste_antwort"]


# ───────────────────────────────────────────────────────────────────────────
# 2. Zusatzaufgaben für die Schnellen
# ───────────────────────────────────────────────────────────────────────────

def test_wer_schnell_ist_bekommt_eine_zusatzaufgabe(fenster, bei_der_uebung):
    """Die Uhr steht still – schneller geht es nicht."""
    for _ in range(levelablauf.BASIS_UEBUNGEN_JE_LEVEL):
        _loesen(fenster)
    screen = fenster.aktueller_screen
    assert isinstance(screen, uebung.Uebung)
    assert screen.aufgabe.zusatzaufgabe, "Sie muss im Log als Zusatzaufgabe stehen."
    _loesen(fenster)
    assert fenster.durchlauf.spielstand.zusatzaufgaben_im_level() == 1
    assert fenster.durchlauf.spielstand.uebungen_im_level() == levelablauf.BASIS_UEBUNGEN_JE_LEVEL


def test_nach_den_zusatzaufgaben_kommt_trotzdem_das_funkgeraet(fenster, bei_der_uebung):
    """Die Obergrenze des Levels gilt – sonst käme man nie zur Geschichte."""
    for _ in range(levelablauf.BASIS_UEBUNGEN_JE_LEVEL
                   + zusatzaufgaben.HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL):
        _loesen(fenster)
    assert isinstance(fenster.aktueller_screen, funk.Funk)


# ───────────────────────────────────────────────────────────────────────────
# 3. Die Vorrang-Regel
# ───────────────────────────────────────────────────────────────────────────

def test_wer_troedelt_kommt_trotzdem_zum_funkspruch(fenster, bei_der_uebung, uhr):
    """Auch wenn die zweite Übung dafür ausfällt (Arbeitsplan Phase 7)."""
    noetig = zusatzaufgaben.erwartete_dauer_funksprueche(story.FUNKSPRUECHE_NACH_LEVEL[1])
    _loesen(fenster, DAUER_JE_LEVEL_SEKUNDEN[1] - noetig - zusatzaufgaben.MINDESTRESTZEIT_SEKUNDEN, uhr)
    screen = fenster.aktueller_screen
    assert isinstance(screen, funk.Funk), "Die zweite Übung fällt aus, der Funkspruch nicht."
    assert fenster.durchlauf.spielstand.uebungen_im_level() == 1
    assert screen.funkspruch is story.FUNKSPRUCH_ERSTER_RUF


def test_eine_laufende_uebung_wird_nicht_abgebrochen(fenster, bei_der_uebung, uhr):
    """Die Vorrang-Regel greift erst zwischen zwei Aufgaben, nie mitten in einer."""
    screen = bei_der_uebung
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] - 1)
    assert fenster.aktueller_screen is screen
    assert screen.aufgabe is fenster.durchlauf.spielstand.aktuelle_aufgabe


# ───────────────────────────────────────────────────────────────────────────
# 4. Die Erzähltexte an ihrem Platz (7.2)
# ───────────────────────────────────────────────────────────────────────────

def test_beim_abgefangenen_funkspruch_kommt_der_hinweis_zur_haeufigkeitsanalyse(fenster, bei_der_uebung, uhr):
    """Er gehört dorthin, wo ein sichtbar langer Geheimtext dasteht (Arbeitsplan 7.2)."""
    screen = _spielen_bis(fenster, uhr,
                          lambda s: isinstance(s, funk.Funk) and s.funkspruch is story.FUNKSPRUCH_VERFOLGER)
    assert screen.hinweis == " ".join(story.HINWEIS_HAEUFIGKEITSANALYSE.absaetze)
    assert screen.erzaehlung == story.FUNKSPRUCH_VERFOLGER.einleitung, "Zuerst die Einleitung …"
    screen.anzeige_vervollstaendigen()
    assert screen.erzaehlung == screen.hinweis, "… und dann, wenn alles dasteht, der Hinweis."


def test_der_hinweis_kommt_auch_wenn_die_nachricht_von_selbst_fertig_wird(fenster, bei_der_uebung,
                                                                            uhr, wurzel):
    """Im Spiel tippt sich die Nachricht Zeichen für Zeichen aufs Glas – kein Test drückt dabei etwas."""
    screen = _spielen_bis(fenster, uhr,
                          lambda s: isinstance(s, funk.Funk) and s.funkspruch is story.FUNKSPRUCH_VERFOLGER)
    ende = time.monotonic() + 5
    while not screen.eingetippt and time.monotonic() < ende:
        wurzel.update()
        time.sleep(0.005)
    assert screen.eingetippt, "Die Nachricht kam nicht ganz herein."
    assert screen.erzaehlung == screen.hinweis


def test_die_anderen_funksprueche_haben_keinen_hinweis(fenster, bei_der_uebung, uhr):
    screen = _spielen_bis(fenster, uhr, lambda s: isinstance(s, funk.Funk))
    assert screen.funkspruch is story.FUNKSPRUCH_ERSTER_RUF
    assert screen.hinweis == ""
    screen.anzeige_vervollstaendigen()
    assert screen.erzaehlung == story.FUNKSPRUCH_ERSTER_RUF.einleitung


def test_nach_dem_abgefangenen_funkspruch_kommt_der_uebergang_zu_level_3(fenster, bei_der_uebung, uhr):
    """Er ist der Wendepunkt der Geschichte und bekommt deshalb eine eigene Szene."""
    screen = _spielen_bis(fenster, uhr, lambda s: isinstance(s, erzaehlszene.Erzaehlszene))
    assert screen.text == story.UEBERGANG_ZU_LEVEL_3.absaetze[0]
    stand = fenster.durchlauf.spielstand
    assert stand.aktuelles_level == 3, "Gelesen wird schon in der Zeit von Level 3 …"
    assert stand.levelende(2) == LEVELENDE_VORZEITIG, (
        "… sonst kippte Level 2 vom Lesen aus auf 'zeitablauf', obwohl alles erledigt war."
    )
    for _ in story.UEBERGANG_ZU_LEVEL_3.absaetze:
        screen.weiter()
    handbuchseite = fenster.aktueller_screen
    assert isinstance(handbuchseite, handbuch.Handbuch) and handbuchseite.seite.level == 3
    assert handbuchseite.einleitung == story.EINSTIEG_LEVEL_3.absaetze


def test_verpasste_funksprueche_kann_man_hinterher_mitlesen(fenster, bei_der_uebung, uhr):
    """Die Zeitfenster sind fix – aber die Geschichte soll nicht an der Uhr scheitern.

    Wessen Zeit ablief, bevor die Funksprüche drankamen, bekommt sie danach
    mit Lösung zu sehen: ohne Eingabe, ohne Uhr, ohne Zeile im Log.
    """
    _level_ablaufen_lassen(fenster, uhr, 1)
    gelesen = []
    while isinstance(fenster.aktueller_screen, funk.Funk):
        screen = fenster.aktueller_screen
        assert screen.nur_lesen
        gelesen.append(screen.funkspruch)
        loesung = screen.aufgabe.vollstaendige_loesung
        if screen.funkspruch.richtung == story.EMPFANGEN:
            assert loesung in _eine_zeile(screen.glastexte("rueckmeldung")), "Die Lösung steht da."
        screen.weiter()
    assert gelesen == list(story.FUNKSPRUECHE_NACH_LEVEL[1])
    stand = fenster.durchlauf.spielstand
    assert not [b for b in stand.erledigte_aufgaben if b.aufgabe.level == 1
                and b.aufgabe.quelle == QUELLE_FUNKSPRUCH], "Im Log steht dafür nichts."
    assert isinstance(fenster.aktueller_screen, handbuch.Handbuch)


def test_beim_mitlesen_gibt_es_nichts_einzutippen(fenster, bei_der_uebung, uhr):
    _level_ablaufen_lassen(fenster, uhr, 1)
    screen = fenster.aktueller_screen
    assert isinstance(screen, funk.Funk) and screen.nur_lesen
    assert screen.knopftext == funk.KNOPF_WEITER
    assert not screen.buch.find_withtag("eingabe"), "Kein Eingabefeld."
    assert not screen.buch.find_withtag("eingabezeichen")
    assert funk.AUFTRAG_NACHGELESEN[screen.funkspruch.richtung] in _eine_zeile(screen.glastexte("auftrag"))


def test_auch_nach_zeitablauf_kommt_der_uebergang_wenn_der_funkspruch_dran_war(fenster, bei_der_uebung, uhr):
    """Gesehen hat man ihn – dann gehört der Satz dazu, der davon spricht.

    Gewechselt wird trotzdem sofort (Projektregel 1); gelesen wird danach, in
    der Zeit von Level 3.
    """
    _spielen_bis(fenster, uhr, lambda s: isinstance(s, funk.Funk)
                 and s.funkspruch is story.FUNKSPRUCH_VERFOLGER)
    _level_ablaufen_lassen(fenster, uhr, 2)
    screen = fenster.aktueller_screen
    assert isinstance(screen, erzaehlszene.Erzaehlszene)
    assert screen.text == story.UEBERGANG_ZU_LEVEL_3.absaetze[0]
    for _ in story.UEBERGANG_ZU_LEVEL_3.absaetze:
        screen.weiter()
    handbuchseite = fenster.aktueller_screen
    assert isinstance(handbuchseite, handbuch.Handbuch) and handbuchseite.seite.level == 3
    assert handbuchseite.hinweis, "Der Hinweis auf den Zeitablauf steht danach über dem Buch."


# ───────────────────────────────────────────────────────────────────────────
# 5. Level 3: die Reflexionsfrage vor dem Standort (7.3)
# ───────────────────────────────────────────────────────────────────────────

def test_vor_dem_standort_kommt_die_reflexionsfrage(fenster, bei_der_uebung, uhr):
    """Erst die Frage allein, dann die Antwort – und dann erst das Funkgerät."""
    frage, antwort = story.REFLEXIONSFRAGE_LEVEL_3.absaetze
    screen = _spielen_bis(fenster, uhr,
                          lambda s: isinstance(s, erzaehlszene.Erzaehlszene) and s.text == frage)
    assert fenster.durchlauf.spielstand.aktuelles_level == 3
    screen.weiter()
    assert screen.text == antwort, "Die Antwort kommt erst auf Klick – vorher denkt man selbst nach."
    screen.weiter()
    funkgeraet = fenster.aktueller_screen
    assert isinstance(funkgeraet, funk.Funk)
    assert funkgeraet.funkspruch is story.FUNKSPRUCH_STANDORT


def test_nach_dem_letzten_funkspruch_kommt_der_abschluss(fenster, bei_der_uebung, uhr):
    screen = _spielen_bis(fenster, uhr, lambda s: isinstance(s, abschluss.Abschluss), hoechstens=60)
    assert fenster.durchlauf.spielstand.ist_durchgespielt
    assert screen.hinweis == "", "Kein Level endete am Timer."
    kennungen = [b.aufgabe.kennung for b in fenster.durchlauf.spielstand.erledigte_aufgaben]
    assert kennungen[-2:] == ["standort", "bob_zweite_antwort"]


# ───────────────────────────────────────────────────────────────────────────
# 6. Der ganze Durchlauf (7.4)
# ───────────────────────────────────────────────────────────────────────────

def _gestellte_funksprueche(fenster):
    return [b.aufgabe.kennung for b in fenster.durchlauf.spielstand.erledigte_aufgaben
            if b.aufgabe.quelle == QUELLE_FUNKSPRUCH]


def _durchspielen(fenster, uhr, vor_der_uebung=None, hoechstens=80):
    """Spielt bis zum Abschluss. ``vor_der_uebung`` darf vorher noch etwas tun."""
    for _ in range(hoechstens):
        screen = fenster.aktueller_screen
        if isinstance(screen, abschluss.Abschluss):
            return screen
        if getattr(screen, "aufgabe", None) is None:
            screen.weiter()                       # Handbuchseite oder Erzähltext
            continue
        if vor_der_uebung is not None and isinstance(screen, uebung.Uebung):
            vor_der_uebung(fenster, uhr)
        _loesen(fenster, NORMALTEMPO, uhr)
    raise AssertionError("Der Abschluss kam nie.")


def _herumrechnen(fenster, uhr, versuche=3, sekunden=30.0):
    """Falsche Eingaben, die jedes Mal einen Buchstaben näher an die Lösung kommen.

    Solche Versuche zählen nicht gegen die Drei (Projektregel 2) – sie kosten
    nur Zeit, und genau darum geht es hier.
    """
    screen = fenster.aktueller_screen
    loesung = screen.aufgabe.loesung
    falsch = "".join(z if z == " " else ("Q" if z != "Q" else "Z") for z in loesung)
    for nr in range(1, versuche + 1):
        uhr.weiter(sekunden)
        screen._feld.delete(0, "end")
        screen._feld.insert(0, loesung[:nr] + falsch[nr:])
        screen.pruefen()
    assert not fenster.durchlauf.spielstand.aktuelle_bearbeitung.loesung_angezeigt, (
        "Wer Fortschritt macht, bekommt die Lösung nicht vorgesetzt."
    )


def test_ein_ganzer_durchlauf_kommt_bei_allen_funkspruechen_an(fenster, bei_der_uebung, uhr):
    """Vom Start bis zur Rettung, jede Aufgabe gelöst – nirgends bleibt man hängen."""
    _durchspielen(fenster, uhr)
    stand = fenster.durchlauf.spielstand
    assert stand.ist_durchgespielt
    assert _gestellte_funksprueche(fenster) == [f.kennung for f in story.FUNKSPRUECHE]
    assert all(not b.abgebrochen for b in stand.erledigte_aufgaben)
    assert [stand.levelende(level) for level in (1, 2, 3)] == ["vorzeitig"] * 3


def test_ein_troedel_durchlauf_kommt_trotzdem_bei_allen_funkspruechen_an(fenster, bei_der_uebung, uhr):
    """Der Fall aus dem Arbeitsplan (7.4): an den Übungen wird getrödelt, bis die Zeit knapp wird.

    Die Funksprüche tragen die Geschichte – sie müssen trotzdem alle drankommen.
    """
    def troedeln(fenster, uhr):
        _herumrechnen(fenster, uhr)
        stand = fenster.durchlauf.spielstand
        grenze = (zusatzaufgaben.erwartete_dauer_funksprueche(stand.offene_funksprueche)
                  + zusatzaufgaben.erwartete_dauer(zusatzaufgaben.laengste_uebung())
                  + zusatzaufgaben.MINDESTRESTZEIT_SEKUNDEN)
        uhr.weiter(max(0.0, stand.verbleibende_sekunden - grenze + 1))   # gerade so unter die Grenze

    _durchspielen(fenster, uhr, vor_der_uebung=troedeln)
    stand = fenster.durchlauf.spielstand
    assert _gestellte_funksprueche(fenster) == [f.kennung for f in story.FUNKSPRUECHE]
    assert stand.uebungen_im_level(1) == 1, "Für die zweite Übung war die Zeit zu knapp …"
    assert stand.zusatzaufgaben_im_level(1) == 0, "… und für eine Zusatzaufgabe erst recht."
    assert all(not b.abgebrochen for b in stand.erledigte_aufgaben)
