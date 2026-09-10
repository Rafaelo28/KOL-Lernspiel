"""Tests für game/rueckmeldung.py (Arbeitsplan 4.2).

Projektregel 6: nie nur "falsch", sondern ein Hinweis, wo es kippt. Zwei
Anforderungen stehen dabei gegeneinander und werden beide geprüft:

* Die Meldung muss **konkret genug** sein, damit man den Fehler findet.
* Sie darf die Lösung **nicht verraten** – sonst liesse sich der Text Versuch
  für Versuch zusammensetzen und die 3-Versuche-Regel wäre wertlos.

Dazu kommt die Zählbasis-Falle aus Phase 1: Buchstabenposition und
Anzeigeposition sind nicht dasselbe.
"""

import pytest

from content import charaktere, story, uebungen
from crypto.normalize import LEERZEICHEN, ohne_leerzeichen
from game.aufgabe import ENTSCHLUESSELN, VERSCHLUESSELN, Aufgabe, anwenden, gegenrichtung
from game.generator import Aufgabengenerator, aufgabe_aus_funkspruch
from game.rueckmeldung import (
    HINWEIS_JE_VERFAHREN,
    Abweichung,
    erste_abweichung,
    rueckmeldung,
)
from game.zufallsquelle import Zufallsquelle

LEVEL = (1, 2, 3)

# Handbuch-Beispiel: ZEIT WIRD KNAPP mit Schlüssel 3.
CAESAR_AUFGABE = Aufgabe(
    "probe", 1, "caesar", VERSCHLUESSELN, 3, "ZEIT WIRD KNAPP", "CHLW ZLUG NQDSS"
)

FUNKSPRUCH_AUFGABEN = [aufgabe_aus_funkspruch(f, "VM") for f in story.FUNKSPRUECHE]
FUNKSPRUCH_IDS = [f.kennung for f in story.FUNKSPRUECHE]


def _alle_uebungen(je_level=15):
    generator = Aufgabengenerator(Zufallsquelle(4711))
    return [
        generator.naechste_uebung(level)
        for level in LEVEL
        for _ in range(je_level)
    ]


def _ein_buchstabe_falsch(loesung, stelle=0):
    """Verfälscht genau einen Buchstaben, ohne die Länge zu ändern."""
    zeichen = list(loesung)
    buchstaben = [i for i, z in enumerate(zeichen) if z != LEERZEICHEN]
    i = buchstaben[stelle]
    zeichen[i] = "A" if zeichen[i] != "A" else "B"
    return "".join(zeichen)


# ───────────────────────────────────────────────────────────────────────────
# 1. Die Zählbasis-Falle
# ───────────────────────────────────────────────────────────────────────────

def test_die_beiden_positionen_werden_getrennt_gefuehrt():
    """Der 13. Buchstabe steht an 15. Stelle – beides muss stimmen."""
    abweichung = erste_abweichung("CHLW ZLUG NQDSR", "CHLW ZLUG NQDSS")
    assert abweichung.buchstabenposition == 13
    assert abweichung.anzeigeposition == 15
    assert abweichung.wortnummer == 3
    assert abweichung.position_im_wort == 5
    assert abweichung.eingegeben == "R"


@pytest.mark.parametrize("stelle", range(13))
def test_die_umrechnung_stimmt_fuer_jede_stelle(stelle):
    """Gegenprobe von Hand: die Anzeigeposition zeigt auf denselben Buchstaben."""
    loesung = "CHLW ZLUG NQDSS"
    falsch = _ein_buchstabe_falsch(loesung, stelle)
    abweichung = erste_abweichung(falsch, loesung)
    assert abweichung.buchstabenposition == stelle + 1
    # Die Anzeigeposition muss im Text mit Leerzeichen denselben Buchstaben treffen.
    assert loesung[abweichung.anzeigeposition - 1] == ohne_leerzeichen(loesung)[stelle]
    # Und Wort/Position im Wort ebenfalls.
    wort = loesung.split()[abweichung.wortnummer - 1]
    assert wort[abweichung.position_im_wort - 1] == ohne_leerzeichen(loesung)[stelle]


def test_bei_einem_einzelnen_wort_ist_beides_gleich():
    abweichung = erste_abweichung("KXQF", "KXQG")
    assert abweichung.buchstabenposition == abweichung.anzeigeposition == 4
    assert abweichung.wortnummer == 1
    assert abweichung.position_im_wort == 4


def test_die_zaehlung_ist_unabhaengig_von_der_schreibweise_der_eingabe():
    """Regel 4: Leerzeichen in der Eingabe zählen nicht mit."""
    for eingabe in ["CHLWZLUGNQDSR", "chlw zlug nqdsr", "CHLW  ZLUG  NQDSR"]:
        abweichung = erste_abweichung(eingabe, "CHLW ZLUG NQDSS")
        assert abweichung.buchstabenposition == 13
        assert abweichung.anzeigeposition == 15


def test_ohne_abweichung_gibt_es_keine():
    assert erste_abweichung("CHLW ZLUG NQDSS", "CHLW ZLUG NQDSS") is None
    assert erste_abweichung("CHLW", "CHLW ZLUG") is None
    assert erste_abweichung("CHLW ZLUG NQDSSX", "CHLW ZLUG NQDSS") is None


# ───────────────────────────────────────────────────────────────────────────
# 2. Die Meldungen
# ───────────────────────────────────────────────────────────────────────────

def test_eine_richtige_loesung_bekommt_keine_meldung():
    assert rueckmeldung(CAESAR_AUFGABE, "CHLW ZLUG NQDSS") == ""
    assert rueckmeldung(CAESAR_AUFGABE, "chlwzlugnqdss") == ""


def test_eine_leere_eingabe_bekommt_keine_fehlermeldung():
    """Wer nichts eingegeben hat, hat nichts falsch gemacht."""
    for eingabe in ["", "   ", "???"]:
        assert rueckmeldung(CAESAR_AUFGABE, eingabe) == "Du hast noch nichts eingegeben."


def test_die_meldung_nennt_die_stelle_und_einen_hinweis():
    meldung = rueckmeldung(CAESAR_AUFGABE, "CHLW ZLUG NQDSR")
    assert "13." in meldung
    assert "3. Wort" in meldung and "5. Buchstabe" in meldung
    assert HINWEIS_JE_VERFAHREN["caesar"] in meldung


def test_zu_kurz_und_zu_lang_werden_benannt():
    assert rueckmeldung(CAESAR_AUFGABE, "CHLW ZLUG") == (
        "Deine Antwort ist noch zu kurz: es fehlen 5 Buchstaben."
    )
    assert rueckmeldung(CAESAR_AUFGABE, "CHLW ZLUG NQDS") == (
        "Deine Antwort ist noch zu kurz: es fehlt 1 Buchstabe."
    )
    assert rueckmeldung(CAESAR_AUFGABE, "CHLW ZLUG NQDSSX") == (
        "Deine Antwort ist zu lang: 1 Buchstabe zu viel."
    )
    assert rueckmeldung(CAESAR_AUFGABE, "CHLW ZLUG NQDSSXYZ") == (
        "Deine Antwort ist zu lang: 3 Buchstaben zu viel."
    )


def test_der_abgeschriebene_aufgabentext_wird_erkannt():
    """Hier ist kein Buchstabe falsch – es wurde gar nicht gerechnet."""
    meldung = rueckmeldung(CAESAR_AUFGABE, "ZEIT WIRD KNAPP")
    assert "abgeschrieben" in meldung
    assert "verschlüsseln" in meldung
    assert "Buchstabe" not in meldung


@pytest.mark.parametrize("level", LEVEL)
def test_die_falsche_richtung_wird_erkannt(level):
    """Der häufigste Anfängerfehler bekommt einen eigenen Satz."""
    generator = Aufgabengenerator(Zufallsquelle(99))
    for _ in range(10):
        aufgabe = generator.naechste_uebung(level)
        andersherum = anwenden(
            aufgabe.verfahren,
            gegenrichtung(aufgabe.richtung),
            aufgabe.anzeigetext,
            aufgabe.schluessel,
        )
        if andersherum == aufgabe.loesung:
            continue  # kann bei manchen Schlüsseln zusammenfallen
        meldung = rueckmeldung(aufgabe, andersherum)
        assert "falsche Richtung" in meldung, meldung


@pytest.mark.parametrize("verfahren, level", [("caesar", 1), ("substitution", 2), ("vigenere", 3)])
def test_jedes_verfahren_bekommt_seinen_eigenen_hinweis(verfahren, level):
    """Der Hinweis soll sagen, *womit* man den Fehler findet."""
    generator = Aufgabengenerator(Zufallsquelle(5))
    aufgabe = generator.naechste_uebung(level)
    meldung = rueckmeldung(aufgabe, _ein_buchstabe_falsch(aufgabe.loesung))
    assert HINWEIS_JE_VERFAHREN[verfahren] in meldung


def test_es_gibt_fuer_jedes_verfahren_einen_hinweis():
    from content import verfahren as verfahrensmodul

    assert set(HINWEIS_JE_VERFAHREN) == set(verfahrensmodul.ALLE)
    assert all(hinweis.strip() for hinweis in HINWEIS_JE_VERFAHREN.values())


# ───────────────────────────────────────────────────────────────────────────
# 3. Die Meldung verrät die Lösung nicht
# ───────────────────────────────────────────────────────────────────────────

def _meldungen_zu_falschen_eingaben():
    aufgaben = _alle_uebungen() + FUNKSPRUCH_AUFGABEN
    for aufgabe in aufgaben:
        for eingabe in (
            _ein_buchstabe_falsch(aufgabe.loesung),
            _ein_buchstabe_falsch(aufgabe.loesung, stelle=1)
            if len(ohne_leerzeichen(aufgabe.loesung)) > 1
            else _ein_buchstabe_falsch(aufgabe.loesung),
            ohne_leerzeichen(aufgabe.loesung)[:-1],
            aufgabe.anzeigetext,
        ):
            yield aufgabe, eingabe, rueckmeldung(aufgabe, eingabe)


def test_keine_meldung_enthaelt_die_loesung():
    """Sonst liesse sich die Lösung Versuch für Versuch zusammensetzen."""
    for aufgabe, eingabe, meldung in _meldungen_zu_falschen_eingaben():
        assert meldung, "Eine falsche Eingabe muss eine Meldung bekommen."
        assert ohne_leerzeichen(aufgabe.loesung) not in ohne_leerzeichen(meldung), (
            f"{aufgabe.kennung}: Die Meldung verrät die Lösung: {meldung}"
        )


def test_keine_meldung_nennt_ueberhaupt_einen_einzelnen_buchstaben():
    """Auch einzeln darf kein Buchstabe der Lösung dastehen.

    Sonst genügten so viele Versuche wie Buchstaben, um die Lösung
    abzufragen – und die 3-Versuche-Regel wäre umgangen.

    Geprüft wird auf einzeln stehende Grossbuchstaben. Deutsche Wörter fangen
    zwar gross an, aber ein Wort aus genau einem Grossbuchstaben kommt im
    Fliesstext nicht vor – wohl aber in einer Meldung wie "erwartet wird ein
    R". Genau die soll es hier nicht geben.
    """
    import re

    for aufgabe, eingabe, meldung in _meldungen_zu_falschen_eingaben():
        einzelne = re.findall(r"(?<![A-Za-zÄÖÜäöü])([A-Z])(?![A-Za-zÄÖÜäöüß])", meldung)
        assert not einzelne, (
            f"{aufgabe.kennung}: Die Meldung nennt einzelne Buchstaben "
            f"{einzelne}: {meldung}"
        )


# ───────────────────────────────────────────────────────────────────────────
# 4. Die Meldung passt zu jeder Aufgabe im Spiel
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
def test_jede_uebung_bekommt_eine_brauchbare_meldung(level):
    generator = Aufgabengenerator(Zufallsquelle(2024))
    for _ in range(30):
        aufgabe = generator.naechste_uebung(level)
        meldung = rueckmeldung(aufgabe, _ein_buchstabe_falsch(aufgabe.loesung))
        assert meldung.endswith(".")
        assert len(meldung) > 20


@pytest.mark.parametrize("aufgabe", FUNKSPRUCH_AUFGABEN, ids=FUNKSPRUCH_IDS)
def test_jeder_funkspruch_bekommt_eine_brauchbare_meldung(aufgabe):
    """Regel: gilt einheitlich für Übungen und echte Funksprüche."""
    meldung = rueckmeldung(aufgabe, _ein_buchstabe_falsch(aufgabe.loesung))
    assert "stimmt noch nicht" in meldung
    assert meldung.endswith(".")


MIT_TEILAUFGABE = [a for a in FUNKSPRUCH_AUFGABEN if a.hat_teilaufgabe]


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_bei_teilaufgaben_zaehlt_die_meldung_innerhalb_der_teilaufgabe(aufgabe):
    """Die Stelle darf sich nie auf den noch verdeckten Rest beziehen."""
    meldung = rueckmeldung(aufgabe, _ein_buchstabe_falsch(aufgabe.loesung))
    abweichung = erste_abweichung(_ein_buchstabe_falsch(aufgabe.loesung), aufgabe.loesung)
    assert abweichung.buchstabenposition <= aufgabe.laenge_in_buchstaben
    assert str(abweichung.buchstabenposition) in meldung


@pytest.mark.parametrize(
    "figur",
    charaktere.SPIELBARE_CHARAKTERE,
    ids=[f.kennung for f in charaktere.SPIELBARE_CHARAKTERE],
)
def test_die_meldung_haengt_nicht_von_der_figur_ab(figur):
    """Alle bekommen dieselbe Rückmeldung an derselben Stelle."""
    for funkspruch in story.FUNKSPRUECHE:
        aufgabe = aufgabe_aus_funkspruch(funkspruch, figur.initialen)
        meldung = rueckmeldung(aufgabe, _ein_buchstabe_falsch(aufgabe.loesung))
        assert "1. Buchstabe" in meldung


@pytest.mark.parametrize("unsinn", [None, 3, ["A"]])
def test_eine_eingabe_vom_falschen_typ_wird_abgewiesen(unsinn):
    with pytest.raises(TypeError):
        rueckmeldung(CAESAR_AUFGABE, unsinn)


# ───────────────────────────────────────────────────────────────────────────
# 5. Die Anzahl der Fehler
# ───────────────────────────────────────────────────────────────────────────
#
# Ohne sie arbeitet die 3-Versuche-Regel gegen die Meldung: Wer nur die erste
# falsche Stelle erfährt, braucht so viele Versuche, wie er Fehler gemacht
# hat. Bei drei Verzählern wären die drei Versuche aufgebraucht, obwohl die
# Methode verstanden war – in den Messdaten sähe das aus wie "nicht gekonnt".

@pytest.mark.parametrize(
    "eingabe, erwartet",
    [
        ("CHLW ZLUG NQDSS", 0),
        ("CHLW ZLUG NQDSR", 1),
        ("CHLW ZLUG NQDRR", 2),
        ("CHLA ZLUG NQDRR", 3),
        ("AAAA AAAA AAAAA", 13),
    ],
)
def test_die_anzahl_der_falschen_buchstaben_stimmt(eingabe, erwartet):
    abweichung = erste_abweichung(eingabe, CAESAR_AUFGABE.loesung)
    if erwartet == 0:
        assert abweichung is None
    else:
        assert abweichung.anzahl == erwartet


def test_die_anzahl_zaehlt_unabhaengig_von_der_schreibweise():
    """Regel 4: Leerzeichen und Kleinschreibung ändern nichts."""
    for eingabe in ["CHLW ZLUG NQDRR", "chlwzlugnqdrr", "CHLW  ZLUG  NQDRR"]:
        assert erste_abweichung(eingabe, CAESAR_AUFGABE.loesung).anzahl == 2


def test_bei_einem_einzigen_fehler_bleibt_die_meldung_wie_bisher():
    """Der häufige Fall soll nicht umständlicher werden."""
    meldung = rueckmeldung(CAESAR_AUFGABE, "CHLW ZLUG NQDSR")
    assert meldung.startswith("Der 13. Buchstabe stimmt noch nicht")
    assert "Noch" not in meldung


def test_bei_mehreren_fehlern_nennt_die_meldung_die_anzahl():
    meldung = rueckmeldung(CAESAR_AUFGABE, "CHLA ZLUG NQDRR")
    assert meldung.startswith("Noch 3 Buchstaben stimmen nicht")
    assert "der erste davon ist der 4." in meldung
    assert "im 1. Wort der 4. Buchstabe" in meldung


def test_die_meldung_ist_auch_bei_einem_einzelnen_wort_sauber_gebaut():
    """Ohne Wortangabe darf kein doppelter Punkt entstehen."""
    einwortig = Aufgabe("probe", 1, "caesar", VERSCHLUESSELN, 3, "HUND", "KXQG")
    assert rueckmeldung(einwortig, "KXQF") == (
        "Der 4. Buchstabe stimmt noch nicht. "
        + HINWEIS_JE_VERFAHREN["caesar"]
    )
    assert rueckmeldung(einwortig, "KAQF") == (
        "Noch 2 Buchstaben stimmen nicht – der erste davon ist der 2. "
        + HINWEIS_JE_VERFAHREN["caesar"]
    )


def test_keine_meldung_enthaelt_einen_doppelten_punkt_oder_ein_komma_vor_dem_punkt():
    """Rein sprachliche Kontrolle über alle Aufgaben und Fehlerzahlen."""
    for aufgabe in _alle_uebungen() + FUNKSPRUCH_AUFGABEN:
        for anzahl in (1, 2, 3):
            buchstaben = ohne_leerzeichen(aufgabe.loesung)
            if len(buchstaben) < anzahl:
                continue
            falsch = aufgabe.loesung
            for stelle in range(anzahl):
                falsch = _ein_buchstabe_falsch(falsch, stelle)
            meldung = rueckmeldung(aufgabe, falsch)
            assert ".." not in meldung, meldung
            assert ",." not in meldung, meldung
            assert " ." not in meldung, meldung
            assert meldung.endswith("."), meldung


def test_die_anzahl_verraet_nicht_welche_buchstaben_stimmen():
    """Sie ist eine Zahl, keine Liste von Stellen.

    Alle Positionen zu nennen würde verraten, welche Buchstaben richtig sind,
    und aus dem Nachrechnen ein mechanisches Ausbessern machen. Das ist
    ausdrücklich für Aufgabe 4.5 vorgesehen, nicht für 4.2.
    """
    meldung = rueckmeldung(CAESAR_AUFGABE, "CHLA ZLUG NQDRR")
    # Genannt wird nur die erste Stelle (4), nicht 12 und 13.
    assert "12." not in meldung
    assert "13." not in meldung


# ───────────────────────────────────────────────────────────────────────────
# 6. Wer die ganze Nachricht rechnet, bekommt passende Rückmeldung
# ───────────────────────────────────────────────────────────────────────────
#
# Bei einer Teilaufgabe zählen zwei Antworten als richtig: der geforderte
# Anfang und die ganze Nachricht. Wird immer gegen den Anfang gemessen, hört
# jemand, der zwei Buchstaben von der vollständigen Lösung entfernt ist, seine
# Antwort sei dreiundsechzig Buchstaben zu lang.

from game.rueckmeldung import bezugsloesung, fehlerzahl_der_aufgabe  # noqa: E402


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_die_richtige_ganze_nachricht_hat_null_fehler(aufgabe):
    """Sonst zeigt die Oberfläche "richtig" und "63 Fehler" nebeneinander."""
    assert fehlerzahl_der_aufgabe(aufgabe, aufgabe.vollstaendige_loesung) == 0
    assert rueckmeldung(aufgabe, aufgabe.vollstaendige_loesung) == ""


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_fehler_am_ende_der_ganzen_nachricht_werden_richtig_gezaehlt(aufgabe):
    """Zwei Buchstaben daneben sollen als zwei gemeldet werden, nicht als 63."""
    fast = _ein_buchstabe_falsch(aufgabe.vollstaendige_loesung, stelle=-1)
    assert fehlerzahl_der_aufgabe(aufgabe, fast) == 1
    meldung = rueckmeldung(aufgabe, fast)
    assert "zu lang" not in meldung
    assert "stimmt noch nicht" in meldung


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_kurze_eingaben_werden_weiter_an_der_teilaufgabe_gemessen(aufgabe):
    """Wer den geforderten Anfang bearbeitet, bekommt dazu die Rückmeldung."""
    assert bezugsloesung(aufgabe, aufgabe.loesung) == aufgabe.loesung
    fast = _ein_buchstabe_falsch(aufgabe.loesung)
    assert bezugsloesung(aufgabe, fast) == aufgabe.loesung
    abweichung = erste_abweichung(fast, aufgabe.loesung)
    assert str(abweichung.buchstabenposition) in rueckmeldung(aufgabe, fast)


def test_ohne_teilaufgabe_gibt_es_nur_eine_bezugsloesung():
    for aufgabe in _alle_uebungen():
        assert bezugsloesung(aufgabe, "IRGENDWAS") == aufgabe.loesung


# ───────────────────────────────────────────────────────────────────────────
# 7. Falscher Buchstabe und falsche Länge zugleich
# ───────────────────────────────────────────────────────────────────────────

def test_beides_wird_gesagt_wenn_beides_falsch_ist():
    """Sonst bessert jemand den Buchstaben aus und erfährt erst danach,
    dass die Antwort ausserdem zu kurz war – ein Versuch für nichts."""
    meldung = rueckmeldung(CAESAR_AUFGABE, "CHLA ZLUG")
    assert "4. Buchstabe stimmt noch nicht" in meldung
    assert "Ausserdem fehlen noch 5 Buchstaben." in meldung


def test_zu_viel_wird_ebenfalls_angehaengt():
    meldung = rueckmeldung(CAESAR_AUFGABE, "CHLA ZLUG NQDSSXX")
    assert "stimmt noch nicht" in meldung
    assert "Ausserdem sind 2 Buchstaben zu viel." in meldung


def test_ein_einzelner_fehlender_buchstabe_wird_richtig_gebeugt():
    meldung = rueckmeldung(CAESAR_AUFGABE, "CHLA ZLUG NQDS")
    assert "Ausserdem fehlt noch 1 Buchstabe." in meldung


def test_bei_reiner_laengenabweichung_gibt_es_keinen_verfahrenshinweis():
    """"Prüf die Verschiebung" wäre falsch – da wurde nur nicht fertig gerechnet."""
    meldung = rueckmeldung(CAESAR_AUFGABE, "CHLW ZLUG")
    assert meldung == "Deine Antwort ist noch zu kurz: es fehlen 5 Buchstaben."
    assert HINWEIS_JE_VERFAHREN["caesar"] not in meldung


def test_bei_einem_buchstabenfehler_gibt_es_ihn_weiterhin():
    assert HINWEIS_JE_VERFAHREN["caesar"] in rueckmeldung(CAESAR_AUFGABE, "CHLA ZLUG NQDSS")
