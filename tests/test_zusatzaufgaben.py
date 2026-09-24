"""Tests für die Bearbeitungszeit und die Zusatzaufgaben (Arbeitsplan 5.3/5.4).

Die Bearbeitungszeit ist der zentrale Messwert des Experiments. Zwei Dinge
dürfen sie nicht verfälschen: die Zeit *zwischen* den Aufgaben und die Zeit
*nach* der Entscheidung (Lösung lesen, Weiterrechnen-Knopf).

Bei den Zusatzaufgaben geht es darum, dass die Restzeit richtig geschätzt wird:
mit dem längsten Text aus dem Pool, mit den noch offenen Funksprüchen und mit
dem Tempo dieses Kindes (:func:`game.zusatzaufgaben.tempofaktor`).
"""

import pytest

from content import charaktere, story
from game import zusatzaufgaben as zusatz
from game.aufgabe import VERSCHLUESSELN, Aufgabe
from game.bearbeitung import HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT, Bearbeitung
from game.spielstand import LEVEL, Spielstand
from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN
from game.zufallsquelle import Zufallsquelle


class Uhr:
    """Eine Uhr zum Stellen: Sie gibt zurück, was in ``jetzt`` steht, und lässt sich vorspulen."""

    def __init__(self, start=0.0):
        """Beginnt bei ``start`` Sekunden."""
        self.jetzt = float(start)

    def __call__(self):
        """Die Bearbeitung fragt die Uhr wie eine Funktion: ``zeitgeber()``."""
        return self.jetzt

    def weiter(self, sekunden):
        """Spult um so viele Sekunden vor."""
        self.jetzt += sekunden


def _uebung():
    """Eine feste Übung zum Durchspielen: HUND mit Caesar und Schlüssel 3."""
    return Aufgabe("probe", 1, "caesar", VERSCHLUESSELN, 3, "HUND", "KXQG")


def _stand(uhr, seed=4711):
    """Ein Spielstand, dessen Zeitfenster an der stellbaren Uhr hängen."""
    return Spielstand(charaktere.VIC_MORENO, Zufallsquelle(seed), "P01", zeitgeber=uhr)


# ───────────────────────────────────────────────────────────────────────────
# 1. Die Bearbeitungszeit (5.3)
# ───────────────────────────────────────────────────────────────────────────

def test_die_uhr_beginnt_mit_der_aufgabe():
    uhr = Uhr()
    lauf = Bearbeitung(_uebung(), uhr)
    assert lauf.benoetigte_sekunden == 0
    assert lauf.laeuft_noch
    uhr.weiter(12)
    assert lauf.benoetigte_sekunden == 12


def test_die_uhr_haelt_beim_loesen_an():
    uhr = Uhr()
    lauf = Bearbeitung(_uebung(), uhr)
    uhr.weiter(30)
    lauf.versuchen("KXQG")
    uhr.weiter(500)
    assert lauf.benoetigte_sekunden == 30
    assert not lauf.laeuft_noch


def test_das_lesen_der_loesung_zaehlt_nicht_mehr_mit():
    """Sonst hinge die Zeit davon ab, wie lange jemand danach herumklickt."""
    uhr = Uhr()
    lauf = Bearbeitung(_uebung(), uhr)
    for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
        uhr.weiter(10)
        lauf.versuchen("AAAA")
    assert lauf.loesung_angezeigt
    gemessen = lauf.benoetigte_sekunden
    uhr.weiter(300)
    assert lauf.benoetigte_sekunden == gemessen


def test_der_weiterrechnen_knopf_zaehlt_nicht_mehr_mit():
    """Der Erzähltext danach ist keine Rechenarbeit."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    aufgabe = stand.stelle_funkspruch(story.FUNKSPRUCH_BOB_ERSTE_ANTWORT)
    uhr.weiter(40)
    stand.versuchen(aufgabe.loesung)
    gemessen = stand.aktuelle_bearbeitung.benoetigte_sekunden
    uhr.weiter(120)
    stand.weiterrechnen()
    uhr.weiter(60)
    assert stand.aktuelle_bearbeitung.benoetigte_sekunden == gemessen


def test_beim_zeitablauf_haelt_die_uhr_ebenfalls_an():
    uhr = Uhr()
    lauf = Bearbeitung(_uebung(), uhr)
    uhr.weiter(45)
    lauf.aufgeben()
    uhr.weiter(200)
    assert lauf.benoetigte_sekunden == 45


def test_die_zeit_zwischen_den_aufgaben_zaehlt_nicht_mit():
    """Gemessen wird pro Aufgabe, nicht die Gesamtdauer des Fensters."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    aufgabe = stand.naechste_uebung()
    uhr.weiter(20)
    stand.versuchen(aufgabe.loesung)
    stand.aufgabe_abschliessen()
    uhr.weiter(600)                     # Pause, Ablenkung, Nachbarn fragen
    zweite = stand.naechste_uebung()
    uhr.weiter(25)
    stand.versuchen(zweite.loesung)
    stand.aufgabe_abschliessen()
    zeiten = [b.benoetigte_sekunden for b in stand.erledigte_aufgaben]
    assert zeiten == [20, 25]


def test_die_sekunden_je_buchstabe_stimmen():
    uhr = Uhr()
    lauf = Bearbeitung(_uebung(), uhr)
    uhr.weiter(20)
    lauf.versuchen("KXQG")
    assert lauf.aufgabe.laenge_in_buchstaben == 4
    assert lauf.sekunden_je_buchstabe == 5.0


def test_die_zeit_steht_auch_im_versuchsergebnis():
    uhr = Uhr()
    lauf = Bearbeitung(_uebung(), uhr)
    uhr.weiter(7)
    assert lauf.versuchen("AAAA").benoetigte_sekunden == 7


# Abgebrochen oder entschieden? Im Log muss sich das trennen lassen: Bei einer
# abgebrochenen Aufgabe ist die gemessene Zeit die bis zum Levelwechsel.

def test_eine_beim_levelwechsel_beendete_aufgabe_gilt_als_abgebrochen():
    uhr = Uhr()
    lauf = Bearbeitung(_uebung(), uhr)
    uhr.weiter(880)
    lauf.aufgeben()
    assert lauf.abgebrochen
    assert lauf.loesung_angezeigt
    assert not lauf.geloest


def test_nach_drei_versuchen_ohne_fortschritt_ist_nichts_abgebrochen():
    """Das ist eine echte Entscheidung – die Zeit ist Rechenzeit."""
    lauf = Bearbeitung(_uebung(), Uhr())
    for _ in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
        lauf.versuchen("AAAA")
    assert lauf.loesung_angezeigt
    assert not lauf.abgebrochen
    lauf.aufgeben()
    assert not lauf.abgebrochen


def test_aufgeben_veraendert_eine_geloeste_aufgabe_nicht():
    """Sonst stünde sie im Log als "gelöst" und "Lösung angezeigt" zugleich."""
    uhr = Uhr()
    lauf = Bearbeitung(_uebung(), uhr)
    uhr.weiter(12)
    lauf.versuchen("KXQG")
    uhr.weiter(100)
    lauf.aufgeben()
    assert lauf.geloest
    assert not lauf.loesung_angezeigt
    assert not lauf.abgebrochen
    assert lauf.benoetigte_sekunden == 12


def test_eine_frische_aufgabe_ist_nicht_abgebrochen():
    assert not Bearbeitung(_uebung(), Uhr()).abgebrochen


# Wer bei einer Teilaufgabe von sich aus die ganze Nachricht rechnet, hat mehr
# Buchstaben gerechnet – seine Zeit gehört zu dieser Zahl.

def _bob(uhr):
    """Die Bearbeitung von Bobs erster Antwort – eine lange Aufgabe mit Teilaufgabe."""
    from game.generator import aufgabe_aus_funkspruch

    return Bearbeitung(aufgabe_aus_funkspruch(story.FUNKSPRUCH_BOB_ERSTE_ANTWORT, "VM"), uhr)


def test_ohne_teilaufgabe_sind_die_gerechneten_buchstaben_die_laenge():
    lauf = Bearbeitung(_uebung(), Uhr())
    lauf.versuchen("KXQG")
    assert lauf.gerechnete_buchstaben == lauf.aufgabe.laenge_in_buchstaben == 4


def test_wer_nur_den_anfang_rechnet_hat_den_anfang_gerechnet():
    lauf = _bob(Uhr())
    lauf.versuchen(lauf.aufgabe.loesung)
    assert lauf.aufgabe.hat_teilaufgabe
    assert lauf.gerechnete_buchstaben == lauf.aufgabe.laenge_in_buchstaben


def test_wer_die_ganze_nachricht_rechnet_hat_alle_buchstaben_gerechnet():
    lauf = _bob(Uhr())
    lauf.versuchen(lauf.aufgabe.vollstaendige_loesung)
    assert lauf.vollstaendig_geloest
    assert lauf.gerechnete_buchstaben == lauf.aufgabe.laenge_vollstaendig_in_buchstaben
    assert lauf.gerechnete_buchstaben > lauf.aufgabe.laenge_in_buchstaben


def test_die_ganze_nachricht_nach_der_loesungsanzeige_zaehlt_nicht():
    """Abgeschrieben ist nicht gerechnet – und die Uhr stand da schon."""
    lauf = _bob(Uhr())
    for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
        lauf.versuchen("X" * (nummer + 2))
    lauf.versuchen(lauf.aufgabe.vollstaendige_loesung)
    assert lauf.gerechnete_buchstaben == lauf.aufgabe.laenge_in_buchstaben


def test_die_sekunden_je_buchstabe_beziehen_sich_auf_die_gerechneten():
    uhr = Uhr()
    lauf = _bob(uhr)
    uhr.weiter(312)
    lauf.versuchen(lauf.aufgabe.vollstaendige_loesung)
    assert lauf.sekunden_je_buchstabe == 312 / lauf.aufgabe.laenge_vollstaendig_in_buchstaben


# ───────────────────────────────────────────────────────────────────────────
# 2. Das Erwartungsmodell (5.4)
# ───────────────────────────────────────────────────────────────────────────

def test_die_erwartete_dauer_hat_eine_grundzeit():
    """Ohne sie sähen kurze Aufgaben immer langsam aus.

    Lesen, Schlüssel nachschlagen, tippen und prüfen kosten Zeit, die nichts
    mit der Länge zu tun hat. Ein reines "Sekunden je Buchstabe" würde am Ende
    die Länge der gezogenen Aufgabe messen, nicht das Tempo der Person.
    """
    assert zusatz.erwartete_dauer(0) == zusatz.ERWARTETE_GRUNDZEIT_SEKUNDEN
    assert zusatz.ERWARTETE_GRUNDZEIT_SEKUNDEN > 0


def test_die_erwartete_dauer_waechst_mit_der_laenge():
    dauern = [zusatz.erwartete_dauer(n) for n in (4, 9, 15, 25)]
    assert dauern == sorted(dauern)
    assert len(set(dauern)) == len(dauern)


def _geloeste_bearbeitung(uhr, sekunden, text="HUND", loesung="KXQG"):
    """Eine gelöste Übung, die ``sekunden`` gedauert hat."""
    aufgabe = Aufgabe("probe", 1, "caesar", VERSCHLUESSELN, 3, text, loesung)
    uhr.jetzt = 0
    lauf = Bearbeitung(aufgabe, uhr)
    uhr.weiter(sekunden)
    lauf.versuchen(loesung)
    return lauf


def test_ohne_erledigte_aufgaben_ist_der_tempofaktor_eins():
    assert zusatz.tempofaktor(()) == 1.0


def test_wer_doppelt_so_lange_braucht_hat_den_faktor_zwei():
    """Der Faktor misst das Tempo, nicht die Länge der gezogenen Aufgabe."""
    uhr = Uhr()
    for text, loesung in [("HUND", "KXQG"), ("ZEIT WIRD KNAPP", "CHLW ZLUG NQDSS")]:
        laenge = len(text.replace(" ", ""))
        lauf = _geloeste_bearbeitung(uhr, zusatz.erwartete_dauer(laenge) * 2, text, loesung)
        assert zusatz.tempofaktor([lauf]) == pytest.approx(2.0), text


def test_der_faktor_bleibt_in_seinen_grenzen():
    """Eine liegengelassene Aufgabe soll nicht den ganzen Ablauf umwerfen."""
    uhr = Uhr()
    unten, oben = zusatz.TEMPO_GRENZEN
    assert zusatz.tempofaktor([_geloeste_bearbeitung(uhr, 3600)]) == oben
    assert zusatz.tempofaktor([_geloeste_bearbeitung(uhr, 0.5)]) == unten


def test_abgebrochene_aufgaben_zaehlen_beim_tempo_nicht_mit():
    """Dort ist die Zeit die bis zum Levelwechsel, keine Rechenzeit."""
    uhr = Uhr()
    lauf = Bearbeitung(_uebung(), uhr)
    uhr.weiter(600)
    lauf.aufgeben()
    assert lauf.abgebrochen
    assert zusatz.tempofaktor([lauf]) == 1.0


def test_lange_aufgaben_wiegen_beim_tempo_schwerer():
    """Gerechnet wird Summe durch Summe – sonst zöge eine kurze Aufgabe alles mit."""
    uhr = Uhr()
    kurz = _geloeste_bearbeitung(uhr, zusatz.erwartete_dauer(4) * 3, "HUND", "KXQG")
    lang = _geloeste_bearbeitung(uhr, zusatz.erwartete_dauer(13), "ZEIT WIRD KNAPP", "CHLW ZLUG NQDSS")
    faktor = zusatz.tempofaktor([kurz, lang])
    assert 1.0 < faktor < 2.0, faktor


# ───────────────────────────────────────────────────────────────────────────
# 3. Restzeit und Obergrenze
# ───────────────────────────────────────────────────────────────────────────

def _erledigte_uebung(uhr, sekunden=1):
    """Eine Übung, die nach ``sekunden`` richtig gelöst wurde."""
    lauf = Bearbeitung(_uebung(), uhr)
    uhr.weiter(sekunden)
    lauf.versuchen("KXQG")
    return lauf


def test_kurz_vor_schluss_gibt_es_keine_zusatzaufgabe():
    """Projektregel 1: Sie würde nur unfertig abgebrochen."""
    uhr = Uhr()
    lauf = _erledigte_uebung(uhr)
    assert not zusatz.zeit_reicht_noch(30)
    assert not zusatz.ist_faellig(lauf, 30)


def test_mit_genug_restzeit_gibt_es_eine():
    uhr = Uhr()
    lauf = _erledigte_uebung(uhr)
    assert zusatz.ist_faellig(lauf, 600)


def test_auch_wer_langsam_war_bekommt_eine_solange_die_zeit_reicht():
    """Seit Phase 7 entscheidet die Zeit, nicht das Tempo (siehe Modulkopf)."""
    uhr = Uhr()
    langsam = _erledigte_uebung(uhr, sekunden=zusatz.erwartete_dauer(4) * 2)
    assert zusatz.ist_faellig(langsam, 600)


def test_wer_langsam_rechnet_braucht_mehr_restzeit():
    """Der Tempofaktor verschiebt die Grenze – für Langsame früher."""
    offen = story.FUNKSPRUECHE_NACH_LEVEL[1]
    noetig = zusatz.erwartete_dauer(zusatz.laengste_uebung()) + zusatz.erwartete_dauer_funksprueche(offen)
    knapp = 2 * noetig + zusatz.MINDESTRESTZEIT_SEKUNDEN
    assert zusatz.zeit_reicht_noch(knapp, offen, tempo=2.0)
    assert not zusatz.zeit_reicht_noch(knapp - 1, offen, tempo=2.0)
    assert zusatz.zeit_reicht_noch(knapp - 1, offen, tempo=1.0), "Wer schneller rechnet, hat länger Luft."


def test_die_obergrenze_je_level_greift():
    """Sonst liefe eine Endlosschleife, solange noch Zeit ist."""
    uhr = Uhr()
    lauf = _erledigte_uebung(uhr)
    grenze = zusatz.HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL
    assert zusatz.ist_faellig(lauf, 600, grenze - 1)
    assert not zusatz.ist_faellig(lauf, 600, grenze)
    assert not zusatz.ist_faellig(lauf, 600, grenze + 5)


def test_die_laengste_uebung_stimmt_mit_dem_pool_ueberein():
    from content import uebungen
    from crypto.normalize import ohne_leerzeichen

    laengen = [len(ohne_leerzeichen(t)) for t in uebungen.UEBUNGSTEXTE]
    assert zusatz.laengste_uebung() == max(laengen)


def test_die_restzeit_reicht_genau_ab_der_schwelle():
    """Solange ein Funkspruch aussteht, wird seine Zeit mitreserviert."""
    offen = story.FUNKSPRUECHE_NACH_LEVEL[2]
    noetig = (zusatz.erwartete_dauer(zusatz.laengste_uebung())
              + zusatz.erwartete_dauer_funksprueche(offen)
              + zusatz.MINDESTRESTZEIT_SEKUNDEN)
    assert zusatz.zeit_reicht_noch(noetig, offen)
    assert not zusatz.zeit_reicht_noch(noetig - 1, offen)


def test_ohne_offene_funksprueche_zaehlt_nur_die_mindestrestzeit():
    """Dann gibt es nichts mehr zu reservieren – geübt wird bis zum Schluss.

    Sonst sässe ausgerechnet das langsame Kind die letzten Minuten seines
    Zeitfensters ab: Die Schätzung für eine ganze Übung fällt bei dreifacher
    Rechenzeit über vier Minuten lang aus.
    """
    assert zusatz.zeit_reicht_noch(zusatz.MINDESTRESTZEIT_SEKUNDEN)
    assert not zusatz.zeit_reicht_noch(zusatz.MINDESTRESTZEIT_SEKUNDEN - 1)
    assert zusatz.zeit_reicht_noch(zusatz.MINDESTRESTZEIT_SEKUNDEN, tempo=3.0), (
        "ohne Funkspruch spielt das Tempo keine Rolle mehr"
    )


def test_die_restzeit_richtet_sich_nach_dem_laengsten_text_nicht_nach_dem_letzten():
    """Nach einem kurzen Satz kann ein längerer kommen.

    Wer "HUND" schnell gelöst hat und gerade genug Zeit für ein zweites
    kurzes Wort hätte, bekäme sonst womöglich einen Satz mit 14 Buchstaben –
    und der würde unfertig abgebrochen.
    """
    uhr = Uhr()
    offen = story.FUNKSPRUECHE_NACH_LEVEL[2]
    kurz = Aufgabe("probe", 2, "substitution", VERSCHLUESSELN, None, "HUND", "IXFR")
    lauf = Bearbeitung(kurz, uhr)
    uhr.weiter(1)
    lauf.versuchen("IXFR")
    knapp = (zusatz.erwartete_dauer(4) + zusatz.erwartete_dauer_funksprueche(offen)
             + zusatz.MINDESTRESTZEIT_SEKUNDEN + 1)
    assert zusatz.laengste_uebung() > 4
    assert not zusatz.ist_faellig(lauf, knapp, offene_funksprueche=offen)


def test_die_obergrenze_passt_zum_abschnitt_des_pools():
    """Jedes Level hat nur seinen Abschnitt des Pools – danach wiederholen sich die Texte.

    Die Grenze darf also nicht grösser sein als "Abschnitt minus zwei
    Pflichtübungen", und kleiner sollte sie auch nicht sein: Sonst läuft das
    Level leer, bevor sein Zeitfenster um ist.
    """
    from content import uebungen
    from game.levelablauf import BASIS_UEBUNGEN_JE_LEVEL

    je_level = len(uebungen.UEBUNGSTEXTE) // 3
    assert zusatz.HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL == je_level - BASIS_UEBUNGEN_JE_LEVEL


def test_die_tempogrenzen_umschliessen_die_eins():
    """Sonst wäre schon ein Kind im geschätzten Tempo aussergewöhnlich."""
    unten, oben = zusatz.TEMPO_GRENZEN
    assert 0 < unten < 1 < oben


# ───────────────────────────────────────────────────────────────────────────
# 4. Zusammenspiel mit dem Spielstand
# ───────────────────────────────────────────────────────────────────────────

def test_der_spielstand_bietet_nach_einer_uebung_eine_zusatzaufgabe_an():
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    aufgabe = stand.naechste_uebung()
    uhr.weiter(5)
    stand.versuchen(aufgabe.loesung)
    stand.aufgabe_abschliessen()
    assert stand.zusatzaufgabe_faellig


def test_nach_einer_sehr_langsamen_aufgabe_nicht():
    """Nicht wegen des Tempos an sich, sondern weil die Zeit dann nicht mehr reicht."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    aufgabe = stand.naechste_uebung()
    uhr.weiter(DAUER_JE_LEVEL_SEKUNDEN[1] * 0.75)
    stand.versuchen(aufgabe.loesung)
    stand.aufgabe_abschliessen()
    assert stand.tempofaktor > 1
    assert not stand.zusatzaufgabe_faellig


def test_ohne_erledigte_aufgabe_gibt_es_nichts_anzubieten():
    stand = _stand(Uhr())
    assert not stand.zusatzaufgabe_faellig
    stand.starte_level(1)
    assert not stand.zusatzaufgabe_faellig


def test_der_strom_an_zusatzaufgaben_reisst_nach_der_obergrenze_ab():
    """Der Fall, der ohne Obergrenze in eine Endlosschleife lief."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    gestellt = 0
    aufgabe = stand.naechste_uebung()
    uhr.weiter(3)
    stand.versuchen(aufgabe.loesung)
    stand.aufgabe_abschliessen()
    while stand.zusatzaufgabe_faellig:
        gestellt += 1
        assert gestellt <= 20, "Endlosschleife"
        zusatzaufgabe = stand.naechste_uebung(zusatzaufgabe=True)
        uhr.weiter(3)
        stand.versuchen(zusatzaufgabe.loesung)
        stand.aufgabe_abschliessen()
    assert gestellt == zusatz.HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL
    assert stand.zusatzaufgaben_im_level(1) == gestellt


def test_die_obergrenze_gilt_je_level_neu():
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(LEVEL[0])
    for level in LEVEL:
        aufgabe = stand.naechste_uebung()
        uhr.weiter(3)
        stand.versuchen(aufgabe.loesung)
        stand.aufgabe_abschliessen()
        assert stand.zusatzaufgabe_faellig, f"Level {level}"
        stand.naechstes_level()


def test_zusatzaufgaben_verlaengern_das_zeitfenster_nicht():
    """Projektregel 1, noch einmal von der anderen Seite."""
    uhr = Uhr()
    stand = _stand(uhr)
    stand.starte_level(1)
    aufgabe = stand.naechste_uebung()
    uhr.weiter(3)
    stand.versuchen(aufgabe.loesung)
    stand.aufgabe_abschliessen()
    while stand.zusatzaufgabe_faellig:
        zusatzaufgabe = stand.naechste_uebung(zusatzaufgabe=True)
        uhr.weiter(3)
        stand.versuchen(zusatzaufgabe.loesung)
        stand.aufgabe_abschliessen()
    verbraucht = DAUER_JE_LEVEL_SEKUNDEN[1] - stand.verbleibende_sekunden
    assert verbraucht == uhr.jetzt


def test_eine_eingabe_nach_dem_ende_stempelt_die_zeit_nicht_neu():
    """Wer nach der angezeigten Lösung noch herumtippt, verlängert nichts.

    Die Uhr hält beim **ersten** Erreichen des Endes an. Ohne diese
    Bedingung würde jede weitere Eingabe den Endzeitpunkt nach hinten
    schieben – und im Log stünde die Zeit bis zum letzten Klick statt bis zur
    Entscheidung.
    """
    uhr = Uhr()
    lauf = Bearbeitung(_uebung(), uhr)
    for _ in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
        uhr.weiter(10)
        lauf.versuchen("AAAA")
    gemessen = lauf.benoetigte_sekunden
    assert lauf.loesung_angezeigt
    for _ in range(5):
        uhr.weiter(60)
        lauf.versuchen("BBBB")
    assert lauf.benoetigte_sekunden == gemessen
    uhr.weiter(60)
    lauf.versuchen("KXQG")
    assert lauf.benoetigte_sekunden == gemessen


# ───────────────────────────────────────────────────────────────────────────
# 5. Nur Übungen lösen eine Zusatzaufgabe aus
# ───────────────────────────────────────────────────────────────────────────
#
# Die Zusammenfassung legt den Ablauf fest: "Übungsaufgaben (+ ggf.
# Zusatzaufgaben) → echte Sendeaufgabe → Bobs Antwort". Nach einem Funkspruch
# hat die Geschichte begonnen; eine Handbuch-Übung dazwischen risse sie
# auseinander.

@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=lambda f: f.kennung)
def test_ein_funkspruch_loest_keine_zusatzaufgabe_aus_solange_einer_aussteht(funkspruch):
    from game.generator import aufgabe_aus_funkspruch

    uhr = Uhr()
    lauf = Bearbeitung(aufgabe_aus_funkspruch(funkspruch, "VM"), uhr)
    uhr.weiter(1)
    lauf.versuchen(lauf.aufgabe.loesung)
    assert not zusatz.ist_faellig(lauf, 10_000, offene_funksprueche=(funkspruch,))


@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=lambda f: f.kennung)
def test_nach_dem_letzten_funkspruch_wird_weiter_geuebt(funkspruch):
    """Ist die Geschichte des Levels erzählt, darf die Restzeit nicht verfallen.

    Dann reisst eine Übung nichts mehr auseinander – es kommt ja nichts
    mehr, dem sie den Vortritt lassen müsste.
    """
    from game.generator import aufgabe_aus_funkspruch

    uhr = Uhr()
    lauf = Bearbeitung(aufgabe_aus_funkspruch(funkspruch, "VM"), uhr)
    uhr.weiter(1)
    lauf.versuchen(lauf.aufgabe.loesung)
    assert zusatz.ist_faellig(lauf, 10_000)


def test_wer_die_ganze_nachricht_rechnet_wird_an_ihr_gemessen():
    """Gemessen an der ganzen Nachricht, nicht am Anfang.

    100 Sekunden für 15 Buchstaben sind langsam, für 78 sehr schnell – der
    Tempofaktor muss das auseinanderhalten.
    """
    uhr = Uhr()
    ganz = _bob(uhr)
    uhr.weiter(100)
    ganz.versuchen(ganz.aufgabe.vollstaendige_loesung)

    uhr = Uhr()
    anfang = _bob(uhr)
    uhr.weiter(100)
    anfang.versuchen(anfang.aufgabe.loesung)

    assert zusatz.tempofaktor([ganz]) < 1 < zusatz.tempofaktor([anfang])
