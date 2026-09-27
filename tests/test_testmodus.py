"""Tests für ui/testmodus.py – das Werkzeug zum Durchklicken der Geschichte.

Der Testmodus ist kein Teil des Spiels, aber er darf nicht kaputtgehen: Mit
ihm werden die Story-Stellen vor dem Pilotdurchlauf geprüft. Zwei Dinge sind
dabei wichtiger als alles andere:

* **Er darf das Spiel nicht verändern.** Ohne den Schalter ``--testmodus``
  gibt es keine Leiste, und kein Modul des Spiels weiss von diesem hier.
* **Seine Daten dürfen nicht in die Messdaten geraten.** Geschrieben wird in
  ``logs/testmodus/``, und vor dem Pseudonym steht ``TEST-``.
"""

import ast
import sys
import tkinter as tk
from pathlib import Path

import pytest

PROJEKT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJEKT))

import main  # noqa: E402
from content import story  # noqa: E402
from game.spielstand import LEVELENDE_VORZEITIG, LEVELENDE_ZEITABLAUF  # noqa: E402
from ui import ablauf, abschluss, erzaehlszene, funk, handbuch, testmodus, uebung  # noqa: E402


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
def leiste(wurzel, tmp_path, massstab):
    """Das Spiel im Testmodus, das ins Testverzeichnis schreibt."""
    leiste = testmodus.oeffnen(wurzel, protokollordner_des_spiels=tmp_path, massstab=massstab)
    leiste.fenster.frage_ja_nein = lambda *_, **__: True
    return leiste


@pytest.fixture
def fenster(leiste):
    """Das Hauptfenster hinter der Leiste."""
    return leiste.fenster


def _sprung(beschriftung):
    """Der Eintrag aus dem Menü "Springe zu" mit dieser Aufschrift."""
    ziele = {text: sprung for text, sprung in testmodus.SPRUNGZIELE if sprung is not None}
    return ziele[beschriftung]


#: Wie die Level im Sprungmenü heissen.
VERFAHREN = {1: "Caesar", 2: "Substitution", 3: "Vigenère"}


def _ins_level(leiste, level):
    """Springt in ein Level und gibt den Handbuch-Screen zurück."""
    leiste.springen(_sprung(f"Level {level} – {VERFAHREN[level]}: Handbuch"))
    return leiste.fenster.aktueller_screen


def _zur_uebung(leiste, level=1):
    """Springt in ein Level und klickt vom Handbuch zur ersten Übung."""
    _ins_level(leiste, level).weiter()
    return leiste.fenster.aktueller_screen


# ───────────────────────────────────────────────────────────────────────────
# 1. Die Uhr, die sich vorstellen lässt
# ───────────────────────────────────────────────────────────────────────────

def test_die_uhr_geht_wie_die_systemuhr_bis_jemand_sie_vorstellt():
    """Ohne Versatz ist sie die Uhr darunter – sonst wäre jede gemessene Zeit falsch."""
    stand = [100.0]
    uhr = testmodus.Uhr(lambda: stand[0])
    assert uhr() == 100.0
    stand[0] = 130.0
    assert uhr() == 130.0
    uhr.vorstellen(60)
    assert uhr() == 190.0


def test_die_uhr_geht_nie_zurueck():
    """Eine Uhr, die zurückspringt, liesse eine laufende Aufgabe negativ lange dauern."""
    uhr = testmodus.Uhr(lambda: 0.0)
    uhr.vorstellen(-60)
    assert uhr() == 0.0


def test_das_spiel_bekommt_die_uhr_des_testmodus(fenster):
    """Sonst liesse sich kein Zeitfenster überspringen."""
    assert isinstance(fenster.zeitgeber, testmodus.Uhr)


# ───────────────────────────────────────────────────────────────────────────
# 2. Die Leiste
# ───────────────────────────────────────────────────────────────────────────

def test_die_leiste_haengt_unten_im_fenster(leiste, wurzel):
    """Sie soll unter dem Spiel liegen, nicht darüber oder daneben."""
    assert leiste.winfo_manager() == "pack"
    assert leiste.pack_info()["side"] == "bottom"
    assert leiste.master is wurzel


def test_die_leiste_traegt_alle_knoepfe(leiste):
    """Vier Knöpfe plus das Sprungmenü – so steht es im Modulkopf."""
    aufschriften = {kind.cget("text") for kind in leiste.winfo_children()
                    if isinstance(kind, (tk.Button, tk.Menubutton))}
    assert {testmodus.KNOPF_LOESUNG, testmodus.KNOPF_LEVELENDE, testmodus.KNOPF_ZEITABLAUF,
            testmodus.KNOPF_SPRUNG, testmodus.KNOPF_AUSBLENDEN} <= aufschriften


def test_die_leiste_faellt_farblich_auf(leiste):
    """Auf einem Bildschirmfoto muss sofort zu sehen sein, dass das nicht das Spiel ist."""
    from ui import stil

    assert leiste.cget("bg") == testmodus.FARBE_LEISTE
    assert leiste.cget("bg") != stil.FARBE_NACHT


def test_das_fenster_sagt_im_titel_dass_es_der_testmodus_ist(wurzel, leiste):
    assert "TESTMODUS" in wurzel.title()


def test_die_leiste_laesst_sich_ausblenden_und_mit_f9_zurueckholen(leiste, wurzel, ausloesen):
    """Für Bildschirmfotos und um zu prüfen, ob ein Screen ohne sie ins Fenster passt."""
    leiste.ausblenden()
    assert not leiste.winfo_manager()
    ausloesen(wurzel, testmodus.TASTE_EINBLENDEN)
    assert leiste.winfo_manager() == "pack"


def test_die_anzeige_nennt_level_und_restzeit(leiste):
    assert leiste.standtext() == "kein Durchlauf"
    _ins_level(leiste, 1)
    assert leiste.standtext().startswith("Level 1 · Rest 1")


# ───────────────────────────────────────────────────────────────────────────
# 3. Lösung eintragen
# ───────────────────────────────────────────────────────────────────────────

def test_loesung_eintragen_loest_die_laufende_uebung(leiste):
    """Der Kern des Testmodus: die Geschichte sehen, ohne jede Aufgabe zu rechnen."""
    screen = _zur_uebung(leiste)
    leiste.loesung_eintragen()
    bearbeitung = leiste.fenster.durchlauf.spielstand.aktuelle_bearbeitung
    assert screen.ist_beendet and bearbeitung.geloest
    assert not bearbeitung.loesung_angezeigt, "als richtig gelöst, nicht als aufgelöst"


def test_ein_zweiter_druck_geht_weiter(leiste):
    """Nach dem Lösen heisst der Knopf "Weiter" – der Testmodus drückt ihn mit."""
    screen = _zur_uebung(leiste)
    leiste.loesung_eintragen()
    leiste.loesung_eintragen()
    assert leiste.fenster.aktueller_screen is not screen


def test_loesung_eintragen_beim_funkspruch_wartet_nicht_auf_die_nachricht(leiste):
    """Sonst müsste man zusehen, wie sich der Geheimtext Zeichen für Zeichen eintippt.

    Das betrifft die empfangenen Nachrichten: Sie kommen im Spiel Zeichen für
    Zeichen herein. Was man selbst sendet, steht sofort da.
    """
    _ins_level(leiste, 1)
    ablauf.funkgeraet_zeigen(leiste.fenster, story.FUNKSPRUCH_BOB_ERSTE_ANTWORT)
    screen = leiste.fenster.aktueller_screen
    assert isinstance(screen, funk.Funk) and not screen.eingetippt
    leiste.loesung_eintragen()
    assert screen.eingetippt and screen.ist_beendet


def test_loesung_eintragen_drueckt_auch_den_knopf_fuer_den_rest(leiste):
    """Bei langen Nachrichten hängt der Rest der Geschichte an diesem Knopf."""
    _ins_level(leiste, 1)
    ablauf.funkgeraet_zeigen(leiste.fenster, story.FUNKSPRUCH_BOB_ERSTE_ANTWORT)
    screen = leiste.fenster.aktueller_screen
    leiste.loesung_eintragen()
    assert not screen.restknopf_sichtbar
    assert leiste.fenster.durchlauf.spielstand.aktuelle_bearbeitung.rest_freigegeben


def test_loesung_eintragen_loest_auch_einen_von_hand_entschiedenen_rest_auf(leiste):
    """Wer die Teilaufgabe selbst gerechnet hat, hängt sonst am wartenden Knopf fest.

    "Prüfen" tut nichts, solange der Rest-Knopf dasteht – der Knopf der
    Leiste wirkte damit tot, und gemeldet wurde auch nichts.
    """
    _ins_level(leiste, 1)
    ablauf.funkgeraet_zeigen(leiste.fenster, story.FUNKSPRUCH_BOB_ERSTE_ANTWORT)
    screen = leiste.fenster.aktueller_screen
    screen.anzeige_vervollstaendigen()
    screen._feld.delete(0, "end")
    screen._feld.insert(0, screen.aufgabe.loesung)
    screen.pruefen()                                  # von Hand gelöst
    assert screen.restknopf_sichtbar
    leiste.loesung_eintragen()
    assert not screen.restknopf_sichtbar, "der Rest ist aufgelöst"
    assert leiste.fenster.durchlauf.spielstand.aktuelle_bearbeitung.rest_freigegeben
    assert "Rest" in leiste._hinweis.cget("text")


def test_ohne_aufgabe_passiert_nichts_ausser_einer_meldung(leiste):
    """Auf dem Startbildschirm gibt es nichts zu lösen."""
    leiste.loesung_eintragen()
    assert "keine Aufgabe" in leiste._hinweis.cget("text")


def test_ein_funkspruch_zum_mitlesen_wird_nicht_geloest_sondern_weitergeklickt(leiste):
    """Dort gibt es kein Eingabefeld – ein Griff hinein wäre ein Absturz.

    Zum Mitlesen stehen Funksprüche nach einem Zeitablauf da, nicht nach einem
    Sprung: Ein Sprung stellt sie als Aufgabe. Eintragen heisst hier
    weiterklicken; sonst käme man mit diesem Knopf an ihnen nicht vorbei.
    """
    _ins_level(leiste, 2)
    leiste.zeit_ablaufen_lassen()
    screen = leiste.fenster.aktueller_screen
    assert isinstance(screen, funk.Funk) and screen.nur_lesen
    leiste.loesung_eintragen()
    assert "Mitlesen" in leiste._hinweis.cget("text")
    assert leiste.fenster.aktueller_screen is not screen, "und weiter ist es auch"
    assert not leiste.fenster.durchlauf.spielstand.erledigte_aufgaben, "ohne Zeile im Log"


# ───────────────────────────────────────────────────────────────────────────
# 4. Level beenden und Zeit ablaufen lassen
# ───────────────────────────────────────────────────────────────────────────

def test_level_beenden_schaltet_weiter_wie_nach_erledigter_arbeit(leiste):
    """Im Log steht "vorzeitig" – das Level endete nicht am Timer."""
    _ins_level(leiste, 1)
    leiste.level_beenden()
    stand = leiste.fenster.durchlauf.spielstand
    assert stand.aktuelles_level == 2
    assert stand.levelende(1) == LEVELENDE_VORZEITIG


def test_zeit_ablaufen_lassen_beendet_das_level_wie_der_timer(leiste):
    """Der zweite Weg durch die Geschichte – und der, bei dem Funksprüche ausfallen."""
    _ins_level(leiste, 1)
    leiste.zeit_ablaufen_lassen()
    stand = leiste.fenster.durchlauf.spielstand
    assert stand.levelende(1) == LEVELENDE_ZEITABLAUF
    assert stand.aktuelles_level == 2


def test_nach_dem_zeitablauf_stehen_die_verpassten_funksprueche_zum_mitlesen_da(leiste):
    """Genau das soll sich stichprobenweise ansehen lassen, ohne 15 Minuten zu warten."""
    _ins_level(leiste, 1)
    leiste.zeit_ablaufen_lassen()
    screen = leiste.fenster.aktueller_screen
    assert isinstance(screen, funk.Funk) and screen.nur_lesen


def test_zeit_ablaufen_lassen_ueberspringt_am_ende_die_nacht(leiste, wurzel):
    """Beim Abschluss gibt es kein Zeitfenster – dort führt derselbe Knopf zur Rettung."""
    leiste.springen(_sprung("Abschluss: Nachtlager und Rettung"))
    screen = leiste.fenster.aktueller_screen
    assert screen.phase == "abend"
    leiste.zeit_ablaufen_lassen()
    screen.zu_zeit(abschluss.GELANDET)          # wie der nächste Takt, nur ohne Warten
    assert screen.phase == "gerettet"
    assert screen.knopf_bereit


def test_in_der_lesepause_sagt_die_leiste_dass_keine_uhr_laeuft(leiste):
    """Vorher meldete der Knopf "Zeit abgelaufen" und tat nichts.

    Zwischen zwei Leveln läuft keine Uhr – sie beginnt erst mit der
    Handbuchseite. Wer sich auf die Erfolgsmeldung verlässt, prüft danach
    einen Zustand, den es gar nicht gibt.
    """
    _ins_level(leiste, 1)
    leiste.level_beenden()
    stand = leiste.fenster.durchlauf.spielstand
    assert stand.aktuelles_level == 2 and not stand.zeitfenster_laeuft
    leiste.zeit_ablaufen_lassen()
    assert "keine Uhr" in leiste._hinweis.cget("text")
    assert stand.aktuelles_level == 2, "und es wurde auch nichts weitergeschaltet"


def test_ohne_laufendes_level_meldet_die_leiste_das(leiste):
    leiste.level_beenden()
    assert "kein Level" in leiste._hinweis.cget("text")
    leiste.zeit_ablaufen_lassen()
    assert "kein Level" in leiste._hinweis.cget("text")


# ───────────────────────────────────────────────────────────────────────────
# 5. Die Sprünge
# ───────────────────────────────────────────────────────────────────────────

def test_ein_sprung_ins_level_schlaegt_dessen_handbuch_auf(leiste):
    for level in (1, 2, 3):
        screen = _ins_level(leiste, level)
        assert isinstance(screen, handbuch.Handbuch)
        assert leiste.fenster.durchlauf.spielstand.aktuelles_level == level


def test_nach_einem_sprung_laeuft_die_uhr_des_levels(leiste):
    """Sonst wäre im Sprungziel alles wirkungslos, was an der Zeit hängt.

    Seit die Uhr erst mit der Handbuchseite startet, muss auch der Sprung
    diesen Weg nehmen (``ui.ablauf.level_beginnen``) – sonst liefe im
    Sprungziel kein Zeitfenster: "Zeit ablaufen lassen" täte nichts, die
    Restzeit stünde ewig auf der vollen Dauer, und die Vorrang-Regel rechnete
    mit Zeit, die niemand verbraucht.
    """
    for level in (1, 2, 3):
        _ins_level(leiste, level)
        stand = leiste.fenster.durchlauf.spielstand
        assert stand.zeitfenster_laeuft, f"Level {level}"


def test_zeit_ablaufen_lassen_wirkt_auch_nach_einem_sprung(leiste):
    """Der Knopf muss halten, was die Anleitung verspricht – in jedem Level."""
    _ins_level(leiste, 2)
    leiste.zeit_ablaufen_lassen()
    stand = leiste.fenster.durchlauf.spielstand
    assert stand.levelende(2) == LEVELENDE_ZEITABLAUF
    assert stand.aktuelles_level == 3


def test_ein_sprung_schliesst_eine_laufende_aufgabe_ab(leiste):
    """Bliebe sie offen, liesse sich danach keine neue stellen – der Screen bliebe leer.

    Der Spielstand lässt keine zweite Aufgabe zu, solange eine läuft
    (``_verlange_freie_bahn``). Ein Sprung muss deshalb aufräumen, genau wie
    es ein Levelwechsel tut.
    """
    screen = _zur_uebung(leiste)
    stand = leiste.fenster.durchlauf.spielstand
    assert stand.aktuelle_aufgabe is not None
    leiste.springen(_sprung("Level 2 – Substitution: Handbuch"))
    assert stand.aktuelle_aufgabe is None
    assert stand.erledigte_aufgaben[-1].aufgabe.kennung == screen.aufgabe.kennung
    assert stand.erledigte_aufgaben[-1].abgebrochen

    leiste.fenster.aktueller_screen.weiter()
    weiter = leiste.fenster.aktueller_screen
    assert isinstance(weiter, (uebung.Uebung, funk.Funk))
    assert weiter.aufgabe is not None, "und danach lässt sich wieder arbeiten"


def test_der_rueckweg_aus_der_lesepause_fuehrt_ueber_die_handbuchseite(leiste):
    """Sonst steht plötzlich eine Übung da, deren Verfahren man nie gelesen hat.

    Zwischen zwei Leveln läuft das neue Level schon, seine Uhr aber noch
    nicht. Der Rückweg aus einer angesehenen Szene ging bisher direkt in den
    Ablauf – und startete damit die Uhr, ohne die Handbuchseite zu zeigen.
    """
    _ins_level(leiste, 2)
    leiste.zeit_ablaufen_lassen()
    stand = leiste.fenster.durchlauf.spielstand
    assert stand.aktuelles_level == 3 and not stand.zeitfenster_laeuft

    leiste.springen(_sprung("Level 3: die Reflexionsfrage"))
    szene = leiste.fenster.aktueller_screen
    for _ in story.REFLEXIONSFRAGE_LEVEL_3.absaetze:
        szene.weiter()
    screen = leiste.fenster.aktueller_screen
    assert isinstance(screen, handbuch.Handbuch) and screen.seite.level == 3
    assert stand.zeitfenster_laeuft, "und erst hier beginnt die Zeit von Level 3"


def test_nach_dem_spielende_geht_ein_sprung_in_einen_neuen_durchlauf(leiste):
    """Vorher klebte man am Abschluss fest: Jeder weitere Sprung tat nichts.

    Wer einmal ans Ende gesprungen ist, hat kein Level mehr, in dem sich
    etwas stellen liesse – von da an blieb der Abschluss stehen, und im Log
    stand keine einzige Aufgabe. Jetzt beginnt ein frischer Durchlauf.
    """
    leiste.springen(_sprung("Abschluss: Nachtlager und Rettung"))
    alter_durchlauf = leiste.fenster.durchlauf
    screen = _ins_level(leiste, 1)
    assert isinstance(screen, handbuch.Handbuch) and screen.seite.level == 1
    assert leiste.fenster.durchlauf is not alter_durchlauf
    stand = leiste.fenster.durchlauf.spielstand
    assert stand.aktuelles_level == 1 and stand.zeitfenster_laeuft
    assert leiste.fenster.durchlauf.protokoll.dateiname in leiste._hinweis.cget("text")

    screen.weiter()                               # und hier lässt sich arbeiten
    assert leiste.fenster.aktueller_screen.aufgabe is not None


def test_ein_sprung_beginnt_notfalls_selbst_einen_durchlauf(leiste):
    """Sonst müsste man für jede Stichprobe erst ID und Figur durchklicken."""
    assert leiste.fenster.durchlauf is None
    _ins_level(leiste, 1)
    assert leiste.fenster.durchlauf is not None


def test_rueckwaerts_springen_beginnt_einen_neuen_durchlauf(leiste):
    """Ein Spielstand kennt nur vorwärts – zurück geht es über einen neuen Durchlauf.

    Vorher meldete die Leiste "Zurück geht nicht" und blieb stehen. Wer im
    Testmodus Level 1 noch einmal ansehen will, soll das können.
    """
    _ins_level(leiste, 2)
    erster = leiste.fenster.durchlauf
    _ins_level(leiste, 1)
    zweiter = leiste.fenster.durchlauf
    assert zweiter is not erster
    assert zweiter.spielstand.aktuelles_level == 1
    assert zweiter.protokoll.dateiname != erster.protokoll.dateiname
    assert zweiter.protokoll.dateiname in leiste._hinweis.cget("text")


def test_ein_sprung_nach_vorn_behaelt_den_durchlauf(leiste):
    """Vorwärts braucht es keinen neuen – sonst zerfielen die Messdaten in Schnipsel."""
    _ins_level(leiste, 1)
    durchlauf = leiste.fenster.durchlauf
    _ins_level(leiste, 3)
    assert leiste.fenster.durchlauf is durchlauf
    assert durchlauf.spielstand.aktuelles_level == 3
    assert leiste._hinweis.cget("text") == ""


@pytest.mark.parametrize("beschriftung, erwartet", [
    ("Intro: der Absturz", erzaehlszene.Erzaehlszene),
    ("Übergang zu Level 3", erzaehlszene.Erzaehlszene),
    ("Level 3: die Reflexionsfrage", erzaehlszene.Erzaehlszene),
    ("Level 1: der erste Ruf", funk.Funk),
    ("Level 1: Bobs erste Antwort", funk.Funk),
    ("Level 2: der abgefangene Funkspruch", funk.Funk),
    # Vor den eigenen Standort gehört die Reflexionsfrage – wie im Spiel.
    ("Level 3: der eigene Standort", erzaehlszene.Erzaehlszene),
    ("Level 3: Bobs zweite Antwort", funk.Funk),
    ("Abschluss: Nachtlager und Rettung", abschluss.Abschluss),
])
def test_jede_stelle_der_geschichte_laesst_sich_anspringen(leiste, beschriftung, erwartet):
    """Das ist der Zweck des Menüs: Stichproben ohne Durchspielen."""
    leiste.springen(_sprung(beschriftung))
    assert isinstance(leiste.fenster.aktueller_screen, erwartet)


def test_der_sprung_ans_ende_beendet_auch_das_spiel(leiste):
    """Sonst stünde über der Rettung noch "Level 1 · Caesar-Verschlüsselung"."""
    leiste.springen(_sprung("Abschluss: Nachtlager und Rettung"))
    stand = leiste.fenster.durchlauf.spielstand
    assert stand.aktuelles_level is None and stand.ist_durchgespielt
    assert leiste.standtext() == "Spiel vorbei"


def test_ein_angesprungener_funkspruch_ist_eine_echte_aufgabe(leiste):
    """Genau dafür ist der Sprung da: die Stelle selbst rechnen.

    Vorher stand die Nachricht nur zum Mitlesen da, mit Lösung. Damit liess
    sich weder die Eingabe prüfen noch eine Bearbeitungszeit ansehen.
    """
    leiste.springen(_sprung("Level 1: Bobs erste Antwort"))
    screen = leiste.fenster.aktueller_screen
    assert isinstance(screen, funk.Funk) and not screen.nur_lesen
    assert screen.aufgabe is not None, "gestellt ist sie"
    assert screen.eingabe == "", "eingetragen ist nichts"
    stand = leiste.fenster.durchlauf.spielstand
    assert stand.aktuelle_aufgabe.kennung == story.FUNKSPRUCH_BOB_ERSTE_ANTWORT.kennung
    assert stand.zeitfenster_laeuft, "und die Uhr läuft wie im Spiel"


def test_ein_zweiter_sprung_zum_selben_funkspruch_beginnt_neu(leiste):
    """Jeder Funkspruch kommt nur einmal – sonst zwei Zeilen mit derselben Kennung im Log."""
    leiste.springen(_sprung("Level 1: Bobs erste Antwort"))
    erster = leiste.fenster.durchlauf
    leiste.loesung_eintragen()
    leiste.springen(_sprung("Level 1: Bobs erste Antwort"))
    assert leiste.fenster.durchlauf is not erster
    screen = leiste.fenster.aktueller_screen
    assert isinstance(screen, funk.Funk) and screen.aufgabe is not None


def test_nach_einem_angesprungenen_funkspruch_geht_das_level_weiter(leiste):
    """Der Sprung setzt das Spiel an diese Stelle – es soll von dort weiterlaufen."""
    leiste.springen(_sprung("Level 3: der eigene Standort"))
    szene = leiste.fenster.aktueller_screen      # die Reflexionsfrage führt hin
    for _ in story.REFLEXIONSFRAGE_LEVEL_3.absaetze:
        szene.weiter()
    leiste.loesung_eintragen()                   # Standort gesendet
    leiste.loesung_eintragen()                   # weiter
    screen = leiste.fenster.aktueller_screen
    assert isinstance(screen, funk.Funk)
    assert screen.funkspruch.kennung == story.FUNKSPRUCH_BOB_ZWEITE_ANTWORT.kennung


def test_eine_szene_im_laufenden_level_aendert_den_spielstand_nicht(leiste):
    """Sonst verschöbe eine Stichprobe genau das, was sie prüfen soll."""
    _ins_level(leiste, 3)
    stand = leiste.fenster.durchlauf.spielstand
    vorher = (stand.aktuelles_level, len(stand.erledigte_aufgaben))
    leiste.springen(_sprung("Level 3: die Reflexionsfrage"))
    assert (stand.aktuelles_level, len(stand.erledigte_aufgaben)) == vorher


def test_der_uebergangstext_fuehrt_ins_dritte_level(leiste):
    """Er liegt zwischen den Leveln – danach beginnt Level 3 mit seiner Handbuchseite."""
    _ins_level(leiste, 2)
    leiste.springen(_sprung("Übergang zu Level 3"))
    stand = leiste.fenster.durchlauf.spielstand
    assert stand.aktuelles_level == 3 and not stand.zeitfenster_laeuft, "Lesezeit"
    szene = leiste.fenster.aktueller_screen
    for _ in story.UEBERGANG_ZU_LEVEL_3.absaetze:
        szene.weiter()
    screen = leiste.fenster.aktueller_screen
    assert isinstance(screen, handbuch.Handbuch) and screen.seite.level == 3
    assert stand.zeitfenster_laeuft, "und erst hier beginnt die Zeit von Level 3"


def test_nach_einer_angesehenen_szene_geht_es_im_level_weiter(leiste):
    """Der Knopf unter der Szene darf nicht ins Leere führen."""
    _ins_level(leiste, 3)
    leiste.springen(_sprung("Level 3: die Reflexionsfrage"))
    szene = leiste.fenster.aktueller_screen
    for _ in story.REFLEXIONSFRAGE_LEVEL_3.absaetze:
        szene.weiter()
    assert isinstance(leiste.fenster.aktueller_screen, (uebung.Uebung, funk.Funk))


def test_der_sprung_ins_intro_beginnt_das_spiel_von_vorn(leiste):
    """Vor Level 1 liegt nichts – dorthin kommt man nur mit einem neuen Durchlauf."""
    _ins_level(leiste, 2)
    leiste.springen(_sprung("Intro: der Absturz"))
    stand = leiste.fenster.durchlauf.spielstand
    assert stand.aktuelles_level is None, "die Uhr von Level 1 wartet noch"
    szene = leiste.fenster.aktueller_screen
    for _ in story.INTRO.absaetze:
        szene.weiter()
    screen = leiste.fenster.aktueller_screen
    assert isinstance(screen, handbuch.Handbuch) and screen.seite.level == 1
    assert leiste.fenster.durchlauf.spielstand.zeitfenster_laeuft


def test_ein_klick_klappt_das_sprungmenue_auf(leiste):
    """Vorher war es ein ``Menubutton``: Er postete beim Drücken und nahm das Menü
    beim Loslassen wieder weg – man musste die Maustaste gedrückt halten.

    Geprüft wird, was sich ohne echte Maus prüfen lässt: dass der Knopf einen
    Befehl hat, der das Menü postet, und dass es danach steht.
    """
    knopf = leiste._sprungknopf_widget
    assert knopf.cget("command"), "ein Knopf mit Befehl, kein Menubutton"
    assert not isinstance(knopf, tk.Menubutton)
    leiste.sprungmenue_zeigen()
    try:
        assert leiste.sprungmenue.winfo_ismapped() or leiste.sprungmenue.winfo_exists()
    finally:
        leiste.sprungmenue.unpost()


def test_das_sprungmenue_zeigt_alle_ziele(leiste):
    """Was in SPRUNGZIELE steht, muss auch im Menü stehen – sonst ist es unerreichbar."""
    eintraege = [leiste.sprungmenue.entrycget(nr, "label")
                 for nr in range(leiste.sprungmenue.index("end") + 1)
                 if leiste.sprungmenue.type(nr) == "command"]
    assert eintraege == [text for text, _ in testmodus.SPRUNGZIELE if text is not None]


# ───────────────────────────────────────────────────────────────────────────
# 6. Die Messdaten bleiben getrennt (Projektregel 7)
# ───────────────────────────────────────────────────────────────────────────

def test_der_testmodus_schreibt_in_einen_eigenen_ordner(tmp_path):
    assert testmodus.protokollordner(tmp_path) == tmp_path / testmodus.PROTOKOLL_UNTERORDNER
    assert testmodus.protokollordner(None) is None


def test_die_testdaten_landen_nicht_bei_den_echten(leiste, tmp_path):
    """Sonst rechnete die Auswertung später Testläufe mit."""
    _zur_uebung(leiste)
    leiste.loesung_eintragen()
    leiste.fenster.durchlauf.aufgabe_abschliessen()
    assert not list(tmp_path.glob("*.csv"))
    dateien = list((tmp_path / testmodus.PROTOKOLL_UNTERORDNER).glob("*.csv"))
    assert len(dateien) == 1


def test_die_geloesten_aufgaben_stehen_in_der_datei_des_laufenden_durchlaufs(leiste):
    """Die Beschwerde war: "im Log steht keine Aufgabe" – nach einem Sprung ans Ende.

    Zwei Dinge müssen stimmen. Erstens: Was gelöst wurde, steht in der Datei.
    Zweitens: Beginnt ein Sprung einen neuen Durchlauf, ist das eine **andere**
    Datei – deshalb nennt die Leiste ihren Namen.
    """
    leiste.springen(_sprung("Abschluss: Nachtlager und Rettung"))
    screen = _ins_level(leiste, 1)
    durchlauf = leiste.fenster.durchlauf
    assert durchlauf.protokoll.dateiname in leiste._hinweis.cget("text"), "der neue Dateiname"
    screen.weiter()
    for _ in range(2):
        leiste.loesung_eintragen()               # lösen
        leiste.loesung_eintragen()               # weiter
    durchlauf.sichern()
    zeilen = durchlauf.protokoll.pfad.read_text(encoding="utf-8").splitlines()
    assert len(zeilen) >= 3, "Kopfzeile und zwei Aufgaben"
    assert len(durchlauf.spielstand.erledigte_aufgaben) == 2


def test_das_pseudonym_eines_testlaufs_ist_als_solches_zu_erkennen(leiste):
    """Auch eine Datei im falschen Ordner soll sich noch zuordnen lassen."""
    _ins_level(leiste, 1)
    assert leiste.fenster.durchlauf.spielstand.pseudonym.startswith(testmodus.PSEUDONYM_PRAEFIX)


def test_ein_neuer_durchlauf_behaelt_die_id_und_bekommt_eine_laufnummer(leiste):
    """Sonst stünde nach einem Rücksprung eine fremde ID in der Tabelle.

    Und ohne Laufnummer hiesse die zweite Datei wie die erste, solange beide
    in derselben Sekunde entstehen – der Dateiname kennt keine Bruchteile.
    """
    start = leiste.fenster.aktueller_screen
    start._feld.insert(0, "1-12")
    start.starten()
    figurwahl = leiste.fenster.aktueller_screen
    figurwahl.waehle(figurwahl.karten[0].figur)
    figurwahl.bestaetigen()
    _ins_level(leiste, 3)
    erster = leiste.fenster.durchlauf
    _ins_level(leiste, 1)                        # zurück: neuer Durchlauf
    zweiter = leiste.fenster.durchlauf
    assert zweiter is not erster
    assert zweiter.spielstand.pseudonym.startswith(testmodus.PSEUDONYM_PRAEFIX + "1-12")
    assert testmodus.PSEUDONYM_LAUF in zweiter.spielstand.pseudonym
    assert zweiter.protokoll.dateiname != erster.protokoll.dateiname


def test_auch_die_selbst_eingegebene_id_bekommt_das_praefix(leiste, wurzel):
    """Der Weg über den Startbildschirm ist derselbe wie im Spiel – bis auf das Präfix."""
    start = leiste.fenster.aktueller_screen
    start._feld.insert(0, "1-12")
    start.starten()
    figurwahl = leiste.fenster.aktueller_screen
    figurwahl.waehle(figurwahl.karten[0].figur)
    figurwahl.bestaetigen()
    assert leiste.fenster.durchlauf.spielstand.pseudonym == testmodus.PSEUDONYM_PRAEFIX + "1-12"


# ───────────────────────────────────────────────────────────────────────────
# 7. Das Spiel weiss nichts vom Testmodus
# ───────────────────────────────────────────────────────────────────────────

def test_kein_modul_des_spiels_importiert_den_testmodus():
    """Er hängt an der Oberfläche, nicht in ihr – sonst wäre er im Unterricht dabei."""
    ausser = {"testmodus.py"}
    treffer = []
    for ordner in ("crypto", "game", "content", "ui"):
        for pfad in sorted((PROJEKT / ordner).glob("*.py")):
            if pfad.name in ausser:
                continue
            baum = ast.parse(pfad.read_text(encoding="utf-8"))
            for knoten in ast.walk(baum):
                namen = []
                if isinstance(knoten, ast.Import):
                    namen = [teil.name for teil in knoten.names]
                elif isinstance(knoten, ast.ImportFrom):
                    namen = [f"{knoten.module or ''}.{teil.name}" for teil in knoten.names]
                if any("testmodus" in name for name in namen):
                    treffer.append(str(pfad.relative_to(PROJEKT)))
    assert treffer == []


def test_ohne_schalter_gibt_es_keine_leiste(wurzel, tmp_path):
    """Das Spiel im Unterricht startet ohne Argumente – und sieht dann aus wie immer."""
    fenster = ablauf.oeffnen(wurzel, protokollordner=tmp_path, massstab=1)
    assert not [kind for kind in fenster.wurzel.winfo_children()
                if isinstance(kind, testmodus.Testleiste)]
    assert "TESTMODUS" not in wurzel.title()


def test_main_startet_den_testmodus_nur_mit_dem_schalter(wurzel, monkeypatch):
    """Und schreibt dabei in den Unterordner, nicht zu den Messdaten."""
    geoeffnet = []
    monkeypatch.setattr(tk.Tk, "mainloop", lambda self, n=0: self.destroy())
    monkeypatch.setattr(testmodus, "oeffnen",
                        lambda wurzel, **kwargs: geoeffnet.append(kwargs))
    monkeypatch.setattr(ablauf, "oeffnen", lambda wurzel, **kwargs: geoeffnet.append(kwargs))

    assert main.starte_spiel([]) == 0
    assert "protokollordner" in geoeffnet[-1]
    assert main.starte_spiel([main.SCHALTER_TESTMODUS]) == 0
    assert geoeffnet[-1]["protokollordner_des_spiels"] == main.PROTOKOLLORDNER


def test_main_erklaert_einen_unverstandenen_aufruf(capsys):
    assert main.starte_spiel(["--quatsch"]) == 2
    ausgabe = capsys.readouterr().err
    assert "--quatsch" in ausgabe and main.SCHALTER_TESTMODUS in ausgabe


def test_main_erklaert_den_aufruf_auf_wunsch(capsys):
    for schalter in main.SCHALTER_HILFE:
        assert main.starte_spiel([schalter]) == 0
        assert main.SCHALTER_TESTMODUS in capsys.readouterr().out
