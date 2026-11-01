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
from game.aufgabe import QUELLE_FUNKSPRUCH, QUELLE_UEBUNG  # noqa: E402
from game.spielstand import LEVELENDE_VORZEITIG  # noqa: E402
from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN  # noqa: E402
from ui import abschluss, ablauf, erzaehlszene, funk, handbuch, uebung  # noqa: E402

FIGUR = charaktere.VIC_MORENO


class Uhr:
    """Eine Uhr zum Stellen: Sie gibt zurück, was in ``jetzt`` steht, und lässt sich vorspulen."""

    def __init__(self):
        """Beginnt bei null Sekunden."""
        self.jetzt = 0.0

    def __call__(self):
        """Das Spiel fragt die Uhr wie eine Funktion: ``zeitgeber()``."""
        return self.jetzt

    def weiter(self, sekunden):
        """Spult um so viele Sekunden vor."""
        self.jetzt += sekunden


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


def _spielen_bis(fenster, uhr, bedingung, hoechstens=300):
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
    """Erst die Pflichtübungen, dann gleich das Gerät – Zusatzaufgaben kommen danach.

    Bis zum Pilotdurchlauf schoben sie sich davor; in Level 2 lagen dadurch
    bis zu fünfzehn Übungen zwischen der Handbuchseite und der Geschichte.
    """
    for _ in range(levelablauf.BASIS_UEBUNGEN_JE_LEVEL):
        assert isinstance(fenster.aktueller_screen, uebung.Uebung)
        assert not fenster.aktueller_screen.aufgabe.zusatzaufgabe
        _loesen(fenster, NORMALTEMPO, uhr)
    screen = _spielen_bis(fenster, uhr, lambda s: isinstance(s, funk.Funk))
    assert screen.funkspruch is story.FUNKSPRUCH_ERSTER_RUF
    stand = fenster.durchlauf.spielstand
    assert stand.uebungen_im_level(1) == levelablauf.BASIS_UEBUNGEN_JE_LEVEL
    assert stand.zusatzaufgaben_im_level(1) == 0, "Vor der Geschichte wird nicht gefüllt."


def test_nach_dem_letzten_funkspruch_beginnt_das_naechste_level(fenster, bei_der_uebung, uhr):
    """Die Funksprüche kommen in ihrer Reihenfolge – danach füllen Übungen die Restzeit."""
    while not isinstance(fenster.aktueller_screen, handbuch.Handbuch):
        _loesen(fenster, NORMALTEMPO, uhr)
    assert fenster.aktueller_screen.seite.level == 2
    assert fenster.durchlauf.spielstand.aktuelles_level == 2
    assert _gestellte_funksprueche(fenster) == ["erster_ruf", "bob_erste_antwort"]
    danach = [b.aufgabe.quelle for b in fenster.durchlauf.spielstand.erledigte_aufgaben_im_level(1)]
    assert danach[-1] == QUELLE_UEBUNG, "nach dem letzten Funkspruch wird weitergeübt"


# ───────────────────────────────────────────────────────────────────────────
# 2. Zusatzaufgaben für die Schnellen
# ───────────────────────────────────────────────────────────────────────────

def test_wer_schnell_ist_bekommt_eine_zusatzaufgabe(fenster, bei_der_uebung):
    """Die Uhr steht still – schneller geht es nicht. Gefüllt wird nach der Geschichte."""
    screen = _spielen_bis(fenster, None,
                          lambda s: getattr(getattr(s, "aufgabe", None), "zusatzaufgabe", False))
    assert isinstance(screen, uebung.Uebung)
    assert screen.aufgabe.zusatzaufgabe, "Sie muss im Log als Zusatzaufgabe stehen."
    assert _gestellte_funksprueche(fenster) == ["erster_ruf", "bob_erste_antwort"], (
        "Die Funksprüche waren vorher dran.")
    _loesen(fenster)
    assert fenster.durchlauf.spielstand.zusatzaufgaben_im_level() == 1
    assert fenster.durchlauf.spielstand.uebungen_im_level() == levelablauf.BASIS_UEBUNGEN_JE_LEVEL


def test_die_zusatzaufgaben_hoeren_an_der_obergrenze_auf(fenster, bei_der_uebung):
    """Sonst liefen sie bis zum Zeitablauf weiter.

    Die Uhr steht still, das Zeitfenster begrenzt hier also nichts – was das
    Level beendet, ist allein die Obergrenze aus game/zusatzaufgaben.py.
    (Vor dem Pilotdurchlauf sicherte dieser Test, dass man über die
    Zusatzaufgaben überhaupt zur Geschichte kommt. Die kommt jetzt vorher.)
    """
    _spielen_bis(fenster, None, lambda s: isinstance(s, handbuch.Handbuch) and s.seite.level == 2)
    stand = fenster.durchlauf.spielstand
    assert stand.zusatzaufgaben_im_level(1) == zusatzaufgaben.HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL


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


def test_waehrend_des_mitlesens_laeuft_die_uhr_des_neuen_levels_nicht(fenster, bei_der_uebung, uhr):
    """Lesen ist keine Arbeitszeit – sonst zahlt das langsame Kind zweimal.

    Wer die Funksprüche des alten Levels verpasst hat, liest sie nach dem
    Wechsel. Liefe dabei schon die Uhr von Level 2, ginge ihm ausgerechnet
    dafür die Rechenzeit verloren, die er ohnehin knapp hat.
    """
    _level_ablaufen_lassen(fenster, uhr, 1)
    stand = fenster.durchlauf.spielstand
    assert stand.aktuelles_level == 2 and not stand.zeitfenster_laeuft
    uhr.weiter(300)                                   # in Ruhe gelesen
    while isinstance(fenster.aktueller_screen, funk.Funk):
        fenster.aktueller_screen.weiter()
    assert isinstance(fenster.aktueller_screen, handbuch.Handbuch)
    assert stand.zeitfenster_laeuft, "Mit der Handbuchseite beginnt Level 2."
    assert stand.verbleibende_sekunden == DAUER_JE_LEVEL_SEKUNDEN[2], "und zwar ganz von vorn"
    assert stand.level_sekunden(1) == DAUER_JE_LEVEL_SEKUNDEN[1], "Level 1 bleibt bei seinen Minuten."


def test_beim_mitlesen_nennt_die_kopfzeile_das_level_der_nachricht(fenster, bei_der_uebung, uhr):
    """Sonst widerspricht sich der Balken selbst.

    Nach dem Wechsel steht der Spielstand schon im neuen Level, die
    nachzulesende Nachricht aber im alten. Rechts stand deshalb "Level 2 ·
    monoalphabetische Substitution", während links "Funkgerät – Level 1" und
    auf dem Glas "Caesar · Schlüssel 3" zu lesen war.
    """
    _level_ablaufen_lassen(fenster, uhr, 1)
    screen = fenster.aktueller_screen
    assert isinstance(screen, funk.Funk) and screen.nur_lesen
    titel, levelzeile = fenster.kopfzeile
    assert titel == "Funkgerät – Level 1"
    assert levelzeile.startswith("Level 1 ·")
    assert screen.glastexte("verfahren") == ["Caesar · Schlüssel 3"]

    while isinstance(fenster.aktueller_screen, funk.Funk):
        fenster.aktueller_screen.weiter()
    assert fenster.kopfzeile[1].startswith("Level 2 ·"), "mit der Handbuchseite wechselt sie"


def test_beim_mitlesen_gibt_es_nichts_einzutippen(fenster, bei_der_uebung, uhr):
    _level_ablaufen_lassen(fenster, uhr, 1)
    screen = fenster.aktueller_screen
    assert isinstance(screen, funk.Funk) and screen.nur_lesen
    assert screen.knopftext == funk.KNOPF_WEITER
    assert not screen.buch.find_withtag("eingabe"), "Kein Eingabefeld."
    assert not screen.buch.find_withtag("eingabezeichen")
    assert funk.AUFTRAG_NACHGELESEN[screen.funkspruch.richtung] in _eine_zeile(screen.glastexte("auftrag"))


def test_ein_abgebrochener_funkspruch_wird_danach_zum_mitlesen_gezeigt(fenster, bei_der_uebung, uhr):
    """Wer mitten im Funkspruch vom Timer abgeschnitten wird, erfährt trotzdem, was drinstand.

    Gewechselt wird sofort (Projektregel 1) – die angefangene Aufgabe steht
    als abgebrochen im Log. Danach liegt dieselbe Nachricht noch einmal da,
    diesmal mit Lösung und ohne Uhr.
    """
    _spielen_bis(fenster, uhr, lambda s: isinstance(s, funk.Funk)
                 and s.funkspruch is story.FUNKSPRUCH_VERFOLGER)
    _level_ablaufen_lassen(fenster, uhr, 2)
    screen = fenster.aktueller_screen
    assert isinstance(screen, funk.Funk) and screen.nur_lesen
    assert screen.funkspruch is story.FUNKSPRUCH_VERFOLGER
    abgebrochen = [b for b in fenster.durchlauf.spielstand.erledigte_aufgaben
                   if b.aufgabe.kennung == story.FUNKSPRUCH_VERFOLGER.kennung]
    assert [b.abgebrochen for b in abgebrochen] == [True], "genau eine Zeile, und die als abgebrochen"
    screen.weiter()
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


def test_auch_die_reflexionsfrage_kommt_beim_nachlesen_mit(fenster, bei_der_uebung, uhr):
    """Sonst verliert ausgerechnet das langsame Kind den Gedanken hinter Level 3.

    Der Erzähltext führt zum eigenen Standort: Warum hilft eine
    Häufigkeitsanalyse bei Vigenère nicht mehr weiter? Kam der Funkspruch
    nie dran, stand die Frage nie da – die Funksprüche wurden nachgereicht,
    der Text davor nicht.
    """
    frage = story.REFLEXIONSFRAGE_LEVEL_3.absaetze[0]
    _spielen_bis(fenster, uhr, lambda s: isinstance(s, handbuch.Handbuch) and s.seite.level == 3)
    _level_ablaufen_lassen(fenster, uhr, 3)

    szene = fenster.aktueller_screen
    assert isinstance(szene, erzaehlszene.Erzaehlszene) and szene.text == frage
    for _ in story.REFLEXIONSFRAGE_LEVEL_3.absaetze:
        szene.weiter()
    gelesen = []
    while isinstance(fenster.aktueller_screen, funk.Funk):
        screen = fenster.aktueller_screen
        assert screen.nur_lesen
        gelesen.append(screen.funkspruch)
        screen.weiter()
    assert gelesen == list(story.FUNKSPRUECHE_NACH_LEVEL[3])
    assert isinstance(fenster.aktueller_screen, abschluss.Abschluss)


def test_ein_schon_gesehener_erzaehltext_kommt_nicht_zweimal(fenster, bei_der_uebung, uhr):
    """Wer den Standort angefangen hat, kennt die Frage – dann nur die Nachricht nachreichen."""
    frage = story.REFLEXIONSFRAGE_LEVEL_3.absaetze[0]
    szene = _spielen_bis(fenster, uhr,
                         lambda s: isinstance(s, erzaehlszene.Erzaehlszene) and s.text == frage)
    for _ in story.REFLEXIONSFRAGE_LEVEL_3.absaetze:
        szene.weiter()
    assert isinstance(fenster.aktueller_screen, funk.Funk)          # der Standort läuft
    _level_ablaufen_lassen(fenster, uhr, 3)
    assert isinstance(fenster.aktueller_screen, funk.Funk), "gleich der Funkspruch, ohne die Frage"
    assert fenster.aktueller_screen.nur_lesen


def test_nach_dem_letzten_funkspruch_kommt_der_abschluss(fenster, bei_der_uebung, uhr):
    """Auch Level 3 läuft nach Bobs zweiter Antwort weiter – bis die Zeit um ist."""
    _spielen_bis(fenster, uhr, lambda s: isinstance(s, abschluss.Abschluss), hoechstens=300)
    stand = fenster.durchlauf.spielstand
    assert stand.ist_durchgespielt
    assert _gestellte_funksprueche(fenster) == [f.kennung for f in story.FUNKSPRUECHE]


# ───────────────────────────────────────────────────────────────────────────
# 6. Der ganze Durchlauf (7.4)
# ───────────────────────────────────────────────────────────────────────────

def uebungen_texte(stand, level):
    """Die Aufgabentexte der Übungen eines Levels – für die Frage, ob sich einer wiederholt."""
    return {b.aufgabe.anzeigetext for b in stand.erledigte_aufgaben_im_level(level)
            if b.aufgabe.quelle == QUELLE_UEBUNG}


def _gestellte_funksprueche(fenster):
    """Die Kennungen aller Funksprüche, die im Durchlauf wirklich gestellt wurden."""
    return [b.aufgabe.kennung for b in fenster.durchlauf.spielstand.erledigte_aufgaben
            if b.aufgabe.quelle == QUELLE_FUNKSPRUCH]


def _durchspielen(fenster, uhr, vor_der_uebung=None, hoechstens=300):
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
    """Vom Start bis zur Rettung, jede Aufgabe gelöst – nirgends bleibt man hängen.

    Wer im geschätzten Tempo arbeitet, füllt sein Zeitfenster: Jedes Level
    endet am Timer, und die Übung, die dabei gerade lief, steht als
    abgebrochen im Log. Genau ein solcher Abbruch je Level ist richtig – mehr
    wäre ein Fehler, keiner hiesse, dass jemand untätig gewartet hat.
    """
    _durchspielen(fenster, uhr)
    stand = fenster.durchlauf.spielstand
    assert stand.ist_durchgespielt
    assert _gestellte_funksprueche(fenster) == [f.kennung for f in story.FUNKSPRUECHE]
    for level in (1, 2, 3):
        erledigt = stand.erledigte_aufgaben_im_level(level)
        abgebrochen = [b for b in erledigt if b.abgebrochen]
        uebungen = [b for b in erledigt if b.aufgabe.quelle == QUELLE_UEBUNG]
        if stand.levelende(level) == "zeitablauf":
            # Höchstens eine: die Übung, die beim Ablauf gerade lief. Lief
            # gerade keine (die Zeit ging zwischen zwei Aufgaben zu Ende),
            # ist es keine.
            assert len(abgebrochen) <= 1, f"Level {level}"
            assert all(b.aufgabe.quelle == QUELLE_UEBUNG for b in abgebrochen), f"Level {level}"
        else:
            # Vorzeitig endet ein Level nur noch, wenn ihm die eigenen Texte
            # ausgehen – nicht, weil es niemandem mehr etwas zu tun gäbe.
            assert not abgebrochen, f"Level {level}"
            assert len(uebungen) == len(uebungen_texte(stand, level)), f"Level {level}"
            assert len(uebungen) == (levelablauf.BASIS_UEBUNGEN_JE_LEVEL
                                     + zusatzaufgaben.HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL)


def test_ein_troedel_durchlauf_kommt_trotzdem_bei_allen_funkspruechen_an(fenster, bei_der_uebung, uhr):
    """Der Fall aus dem Arbeitsplan (7.4): an den Übungen wird getrödelt, bis die Zeit knapp wird.

    Die Funksprüche tragen die Geschichte – sie müssen trotzdem alle drankommen.
    """
    def troedeln(fenster, uhr):
        """Lässt so viel Zeit verstreichen, dass gerade keine weitere Übung mehr hineinpasst."""
        _herumrechnen(fenster, uhr)
        stand = fenster.durchlauf.spielstand
        grenze = (zusatzaufgaben.erwartete_dauer_funksprueche(stand.offene_funksprueche)
                  + zusatzaufgaben.erwartete_dauer(zusatzaufgaben.laengste_uebung())
                  + zusatzaufgaben.MINDESTRESTZEIT_SEKUNDEN)
        uhr.weiter(max(0.0, stand.verbleibende_sekunden - grenze + 1))   # gerade so unter die Grenze

    _durchspielen(fenster, uhr, vor_der_uebung=troedeln)
    stand = fenster.durchlauf.spielstand
    assert _gestellte_funksprueche(fenster) == [f.kennung for f in story.FUNKSPRUECHE]
    assert all(not b.abgebrochen for b in stand.erledigte_aufgaben)

    # Die Funksprüche bekommen den Vortritt: Als die Zeit knapp wurde, kam
    # keine Übung mehr dazwischen.
    reihenfolge = [b.aufgabe.quelle for b in stand.erledigte_aufgaben_im_level(1)]
    assert reihenfolge[:3] == [QUELLE_UEBUNG, QUELLE_FUNKSPRUCH, QUELLE_FUNKSPRUCH]
    # Danach steht nichts mehr an – die Restzeit füllt wieder eine Übung.
    assert reihenfolge[3:] and set(reihenfolge[3:]) == {QUELLE_UEBUNG}
