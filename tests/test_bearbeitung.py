"""Tests für game/bearbeitung.py (Arbeitsplan 4.3).

Der wichtigste Test steht in Abschnitt 3: Das Spiel darf an **keiner** Aufgabe
hängen bleiben. Projektregel 2 nennt ausdrücklich Bobs zwei Funksprüche – ohne
Lösungsanzeige blockiert die Geschichte genau dort, und der Durchlauf wäre für
die Messung verloren.
"""

import pytest

from content import charaktere, story
from game.aufgabe import VERSCHLUESSELN, Aufgabe
from game.bearbeitung import (
    HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT,
    Bearbeitung,
    Versuchsergebnis,
)
from game.generator import Aufgabengenerator, aufgabe_aus_funkspruch
from game.zufallsquelle import Zufallsquelle

LEVEL = (1, 2, 3)
FUNKSPRUCH_AUFGABEN = [aufgabe_aus_funkspruch(f, "VM") for f in story.FUNKSPRUECHE]
FUNKSPRUCH_IDS = [f.kennung for f in story.FUNKSPRUECHE]


def _uebung():
    return Aufgabe("probe", 1, "caesar", VERSCHLUESSELN, 3, "HUND", "KXQG")


def _alle_uebungen(je_level=10):
    generator = Aufgabengenerator(Zufallsquelle(4711))
    return [
        generator.naechste_uebung(level) for level in LEVEL for _ in range(je_level)
    ]


def _falsche_eingabe(aufgabe, nummer=0):
    """Eine garantiert falsche, nicht leere Eingabe."""
    return "X" * (len(aufgabe.loesung.replace(" ", "")) + nummer + 1)


# ───────────────────────────────────────────────────────────────────────────
# 1. Der Zähler
# ───────────────────────────────────────────────────────────────────────────

def test_am_anfang_sind_alle_versuche_frei():
    lauf = Bearbeitung(_uebung())
    assert lauf.versuche == 0
    assert lauf.verbleibende_versuche == HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT
    assert not lauf.geloest
    assert not lauf.loesung_angezeigt
    assert not lauf.ist_beendet


def test_ein_fehlversuch_kostet_genau_einen_versuch():
    lauf = Bearbeitung(_uebung())
    ergebnis = lauf.versuchen("XXXX")
    assert ergebnis.zaehlte_als_versuch
    assert ergebnis.versuche == 1
    assert ergebnis.verbleibende_versuche == HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT - 1
    assert not ergebnis.richtig
    assert ergebnis.meldung


@pytest.mark.parametrize("leer", ["", "   ", "???", "\t", "123"])
def test_eine_leere_eingabe_kostet_nichts(leer):
    """Sonst wären nach drei Fehlklicks die Versuche verbraucht."""
    lauf = Bearbeitung(_uebung())
    for _ in range(20):
        ergebnis = lauf.versuchen(leer)
        assert not ergebnis.zaehlte_als_versuch
    assert lauf.versuche == 0
    assert not lauf.loesung_angezeigt


def test_die_richtige_loesung_kostet_keinen_versuch():
    lauf = Bearbeitung(_uebung())
    ergebnis = lauf.versuchen("KXQG")
    assert ergebnis.richtig
    assert not ergebnis.zaehlte_als_versuch
    assert lauf.versuche == 0
    assert lauf.geloest
    assert ergebnis.meldung == ""


def test_die_toleranz_gilt_auch_hier():
    """Regel 4: Kleinschreibung und Leerzeichen kosten keinen Versuch."""
    lauf = Bearbeitung(_uebung())
    assert lauf.versuchen("kxqg").richtig
    assert lauf.versuche == 0


# ───────────────────────────────────────────────────────────────────────────
# 2. Die Lösungsanzeige
# ───────────────────────────────────────────────────────────────────────────

def test_nach_drei_fehlversuchen_steht_die_loesung_da():
    lauf = Bearbeitung(_uebung())
    for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT - 1):
        assert not lauf.versuchen(f"XXX{nummer}").loesung_angezeigt
    letzter = lauf.versuchen("XXXY")
    assert letzter.loesung_angezeigt
    assert letzter.angezeigte_loesung == "KXQG"
    assert letzter.ist_beendet


def test_wer_es_im_letzten_versuch_schafft_bekommt_keine_loesung():
    """Gezählt werden Fehlversuche, nicht Eingaben."""
    lauf = Bearbeitung(_uebung())
    lauf.versuchen("XXXX")
    lauf.versuchen("YYYY")
    ergebnis = lauf.versuchen("KXQG")
    assert ergebnis.richtig
    assert not ergebnis.loesung_angezeigt
    assert lauf.versuche == 2


def test_nach_dem_ende_zaehlt_nichts_mehr():
    """Das Log soll festhalten, was bis zur Entscheidung nötig war."""
    lauf = Bearbeitung(_uebung())
    for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
        lauf.versuchen(f"XXX{nummer}")
    assert lauf.versuche == HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT
    for _ in range(10):
        ergebnis = lauf.versuchen("IMMER FALSCH")
        assert not ergebnis.zaehlte_als_versuch
    assert lauf.versuche == HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT
    assert lauf.verbleibende_versuche == 0


def test_nach_dem_loesen_zaehlt_nichts_mehr():
    lauf = Bearbeitung(_uebung())
    lauf.versuchen("KXQG")
    for _ in range(5):
        assert not lauf.versuchen("XXXX").zaehlte_als_versuch
    assert lauf.versuche == 0


def test_die_angezeigte_loesung_ist_vorher_leer():
    """Sie darf nicht durchsickern, bevor die Versuche verbraucht sind."""
    lauf = Bearbeitung(_uebung())
    assert lauf.angezeigte_loesung == ""
    assert lauf.versuchen("XXXX").angezeigte_loesung == ""
    assert lauf.versuchen("YYYY").angezeigte_loesung == ""


def test_aufgeben_blendet_die_loesung_sofort_ein():
    """Gebraucht, wenn das Zeitfenster abläuft (Projektregel 1)."""
    lauf = Bearbeitung(_uebung())
    lauf.aufgeben()
    assert lauf.loesung_angezeigt
    assert lauf.ist_beendet
    assert lauf.versuche == 0


# ───────────────────────────────────────────────────────────────────────────
# 3. Das Spiel bleibt nirgends hängen – die eigentliche Zusicherung
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("aufgabe", FUNKSPRUCH_AUFGABEN, ids=FUNKSPRUCH_IDS)
def test_kein_funkspruch_blockiert_das_spiel(aufgabe):
    """Projektregel 2: gilt ausdrücklich auch für Bobs zwei Nachrichten.

    Ohne Lösungsanzeige hängt die Geschichte an genau diesen Stellen fest, und
    der ganze Durchlauf ist für die Messung verloren.
    """
    lauf = Bearbeitung(aufgabe)
    for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
        lauf.versuchen(_falsche_eingabe(aufgabe, nummer))
    assert lauf.ist_beendet, f"{aufgabe.kennung} blockiert das Spiel."
    assert lauf.loesung_angezeigt
    assert lauf.angezeigte_loesung == aufgabe.loesung


def test_bobs_beide_funksprueche_sind_dabei():
    """Schutz davor, dass der Test oben durch eine leere Liste grün wird."""
    von_bob = [
        a for a, f in zip(FUNKSPRUCH_AUFGABEN, story.FUNKSPRUECHE)
        if f.absender_kennung == charaktere.BOB.kennung
    ]
    assert len(von_bob) == 2
    for aufgabe in von_bob:
        lauf = Bearbeitung(aufgabe)
        for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
            lauf.versuchen(_falsche_eingabe(aufgabe, nummer))
        assert lauf.ist_beendet


def test_keine_uebung_blockiert_das_spiel():
    for aufgabe in _alle_uebungen():
        lauf = Bearbeitung(aufgabe)
        for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
            lauf.versuchen(_falsche_eingabe(aufgabe, nummer))
        assert lauf.ist_beendet, f"{aufgabe.kennung} blockiert."


@pytest.mark.parametrize(
    "figur",
    charaktere.SPIELBARE_CHARAKTERE,
    ids=[f.kennung for f in charaktere.SPIELBARE_CHARAKTERE],
)
def test_das_gilt_fuer_jede_figur(figur):
    for funkspruch in story.FUNKSPRUECHE:
        aufgabe = aufgabe_aus_funkspruch(funkspruch, figur.initialen)
        lauf = Bearbeitung(aufgabe)
        for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
            lauf.versuchen(_falsche_eingabe(aufgabe, nummer))
        assert lauf.ist_beendet


# ───────────────────────────────────────────────────────────────────────────
# 4. Der Weiterrechnen-Knopf
# ───────────────────────────────────────────────────────────────────────────

MIT_TEILAUFGABE = [a for a in FUNKSPRUCH_AUFGABEN if a.hat_teilaufgabe]
OHNE_TEILAUFGABE = [a for a in FUNKSPRUCH_AUFGABEN if not a.hat_teilaufgabe]


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_der_knopf_kommt_bei_richtiger_loesung(aufgabe):
    lauf = Bearbeitung(aufgabe)
    assert not lauf.darf_weiterrechnen
    ergebnis = lauf.versuchen(aufgabe.loesung)
    assert ergebnis.richtig
    assert ergebnis.darf_weiterrechnen


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_der_knopf_kommt_auch_nach_drei_fehlversuchen(aufgabe):
    """Arbeitsplan 4.3: sonst hängt das Spiel an denselben Stellen wieder fest.

    Erschiene der Knopf nur bei richtiger Lösung, hätte die Lösungsanzeige die
    Blockade zwar aufgehoben – der Rest der Nachricht käme aber nie, und die
    Geschichte ginge nicht weiter.
    """
    lauf = Bearbeitung(aufgabe)
    for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
        ergebnis = lauf.versuchen(_falsche_eingabe(aufgabe, nummer))
    assert ergebnis.loesung_angezeigt
    assert ergebnis.darf_weiterrechnen, f"{aufgabe.kennung}: Knopf fehlt."


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_der_knopf_kommt_nicht_zu_frueh(aufgabe):
    lauf = Bearbeitung(aufgabe)
    for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT - 1):
        assert not lauf.versuchen(_falsche_eingabe(aufgabe, nummer)).darf_weiterrechnen


@pytest.mark.parametrize(
    "aufgabe", OHNE_TEILAUFGABE, ids=[a.kennung for a in OHNE_TEILAUFGABE]
)
def test_ohne_teilaufgabe_gibt_es_keinen_knopf(aufgabe):
    """Sonst stünde ein Knopf da, der nichts aufzulösen hat."""
    lauf = Bearbeitung(aufgabe)
    assert not lauf.versuchen(aufgabe.loesung).darf_weiterrechnen
    lauf2 = Bearbeitung(aufgabe)
    for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
        lauf2.versuchen(_falsche_eingabe(aufgabe, nummer))
    assert not lauf2.darf_weiterrechnen


def test_bei_uebungen_gibt_es_nie_einen_knopf():
    for aufgabe in _alle_uebungen():
        lauf = Bearbeitung(aufgabe)
        lauf.versuchen(aufgabe.loesung)
        assert not lauf.darf_weiterrechnen


# ───────────────────────────────────────────────────────────────────────────
# 5. Was ins Log gehört
# ───────────────────────────────────────────────────────────────────────────

def test_der_zaehler_liefert_die_zahlen_fuer_das_log():
    """Arbeitsplan 5.5: Anzahl Versuche und ob die Lösung angezeigt wurde."""
    lauf = Bearbeitung(_uebung())
    lauf.versuchen("XXXX")
    lauf.versuchen("")
    lauf.versuchen("KXQG")
    assert lauf.versuche == 1
    assert lauf.loesung_angezeigt is False
    assert lauf.geloest is True


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_wer_die_ganze_nachricht_rechnet_wird_als_solcher_vermerkt(aufgabe):
    """Diese Person hat mehr Buchstaben gerechnet als verlangt."""
    lauf = Bearbeitung(aufgabe)
    lauf.versuchen(aufgabe.vollstaendige_loesung)
    assert lauf.geloest
    assert lauf.vollstaendig_geloest


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_wer_nur_die_teilaufgabe_rechnet_wird_nicht_so_vermerkt(aufgabe):
    lauf = Bearbeitung(aufgabe)
    lauf.versuchen(aufgabe.loesung)
    assert lauf.geloest
    assert not lauf.vollstaendig_geloest


def test_das_ergebnis_ist_unveraenderlich():
    ergebnis = Bearbeitung(_uebung()).versuchen("XXXX")
    assert isinstance(ergebnis, Versuchsergebnis)
    with pytest.raises(AttributeError):
        ergebnis.versuche = 0


def test_die_hoechstzahl_steht_an_einer_stelle():
    """Sie ist eine Projektregel, keine Zufallszahl – und muss die 3 sein."""
    assert HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT == 3


# ───────────────────────────────────────────────────────────────────────────
# 6. Der Druck auf den Weiterrechnen-Knopf (Arbeitsplan 4.4)
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_der_knopf_gibt_die_ganze_nachricht_frei(aufgabe):
    lauf = Bearbeitung(aufgabe)
    lauf.versuchen(aufgabe.loesung)
    assert lauf.sichtbare_nachricht == aufgabe.loesung

    ergebnis = lauf.weiterrechnen()
    assert ergebnis.vollstaendige_nachricht == aufgabe.vollstaendige_loesung
    assert ergebnis.rest == aufgabe.rest_der_loesung
    assert ergebnis.erzaehltext == aufgabe.weiterrechnen_text
    assert lauf.sichtbare_nachricht == aufgabe.vollstaendige_loesung


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_der_erzaehltext_ist_da_und_nennt_keine_buchstaben(aufgabe):
    """Er soll erzählen, dass weitergerechnet wird – nicht die Lösung nennen."""
    lauf = Bearbeitung(aufgabe)
    lauf.versuchen(aufgabe.loesung)
    text = lauf.weiterrechnen().erzaehltext
    assert text.strip()
    assert text.endswith(".")
    assert aufgabe.rest_der_loesung not in text


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_der_knopf_traegt_eine_aufschrift(aufgabe):
    lauf = Bearbeitung(aufgabe)
    assert lauf.knopf_beschriftung == ""
    lauf.versuchen(aufgabe.loesung)
    assert lauf.knopf_beschriftung == aufgabe.knopf_beschriftung
    assert lauf.knopf_beschriftung.strip()


def test_die_aufschrift_passt_zur_richtung():
    """Beim Senden wird verschlüsselt, beim Empfangen entschlüsselt."""
    for funkspruch in story.FUNKSPRUECHE:
        aufgabe = aufgabe_aus_funkspruch(funkspruch, "VM")
        if not aufgabe.hat_teilaufgabe:
            continue
        assert aufgabe.knopf_beschriftung == story.BESCHRIFTUNG_REST[funkspruch.richtung]


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_der_knopf_verschwindet_nach_dem_druecken(aufgabe):
    """Zweimal drücken gäbe es nichts mehr aufzulösen."""
    lauf = Bearbeitung(aufgabe)
    lauf.versuchen(aufgabe.loesung)
    lauf.weiterrechnen()
    assert not lauf.darf_weiterrechnen
    assert lauf.knopf_beschriftung == ""
    with pytest.raises(ValueError):
        lauf.weiterrechnen()


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_der_knopf_laesst_sich_nicht_vorzeitig_druecken(aufgabe):
    """Sonst käme man an den Rest, ohne die Teilaufgabe gelöst zu haben."""
    lauf = Bearbeitung(aufgabe)
    with pytest.raises(ValueError):
        lauf.weiterrechnen()
    lauf.versuchen(_falsche_eingabe(aufgabe))
    with pytest.raises(ValueError):
        lauf.weiterrechnen()
    assert lauf.sichtbare_nachricht == ""


@pytest.mark.parametrize(
    "aufgabe", OHNE_TEILAUFGABE, ids=[a.kennung for a in OHNE_TEILAUFGABE]
)
def test_ohne_teilaufgabe_laesst_sich_nicht_weiterrechnen(aufgabe):
    lauf = Bearbeitung(aufgabe)
    lauf.versuchen(aufgabe.loesung)
    with pytest.raises(ValueError):
        lauf.weiterrechnen()


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_auch_nach_drei_fehlversuchen_geht_es_weiter(aufgabe):
    """Die Anti-Blockier-Regel bis zum Ende durchgespielt."""
    lauf = Bearbeitung(aufgabe)
    for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
        lauf.versuchen(_falsche_eingabe(aufgabe, nummer))
    assert lauf.darf_weiterrechnen
    ergebnis = lauf.weiterrechnen()
    assert ergebnis.vollstaendige_nachricht == aufgabe.vollstaendige_loesung
    assert lauf.ist_abgeschlossen


# ───────────────────────────────────────────────────────────────────────────
# 7. Beendet ist nicht dasselbe wie abgeschlossen
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_mit_teilaufgabe_endet_die_pruefung_vor_dem_abschluss(aufgabe):
    """Solange der Rest hinter dem Knopf steckt, ist die Geschichte nicht weiter."""
    lauf = Bearbeitung(aufgabe)
    lauf.versuchen(aufgabe.loesung)
    assert lauf.ist_beendet
    assert not lauf.ist_abgeschlossen
    lauf.weiterrechnen()
    assert lauf.ist_abgeschlossen


@pytest.mark.parametrize(
    "aufgabe", OHNE_TEILAUFGABE, ids=[a.kennung for a in OHNE_TEILAUFGABE]
)
def test_ohne_teilaufgabe_fallen_beide_zusammen(aufgabe):
    lauf = Bearbeitung(aufgabe)
    lauf.versuchen(aufgabe.loesung)
    assert lauf.ist_beendet and lauf.ist_abgeschlossen


def test_bei_uebungen_fallen_beide_zusammen():
    for aufgabe in _alle_uebungen():
        lauf = Bearbeitung(aufgabe)
        lauf.versuchen(aufgabe.loesung)
        assert lauf.ist_abgeschlossen


def test_die_sichtbare_nachricht_sickert_nicht_vorzeitig_durch():
    """Vor dem Ende ist gar nichts zu sehen."""
    for aufgabe in FUNKSPRUCH_AUFGABEN:
        lauf = Bearbeitung(aufgabe)
        assert lauf.sichtbare_nachricht == ""
        lauf.versuchen(_falsche_eingabe(aufgabe))
        assert lauf.sichtbare_nachricht == ""


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_wer_gleich_alles_rechnet_bekommt_trotzdem_den_knopf(aufgabe):
    """Sonst hinge die Geschichte ausgerechnet beim fleissigsten Kind fest."""
    lauf = Bearbeitung(aufgabe)
    lauf.versuchen(aufgabe.vollstaendige_loesung)
    assert lauf.darf_weiterrechnen
    lauf.weiterrechnen()
    assert lauf.ist_abgeschlossen


# ───────────────────────────────────────────────────────────────────────────
# 8. Die drei Felder zur Teilaufgabe gehören zusammen
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "weglassen", ["knopf_beschriftung", "weiterrechnen_text"]
)
def test_eine_teilaufgabe_ohne_knopftext_wird_abgewiesen(weglassen):
    """Ein Knopf ohne Aufschrift wäre im Spiel eine leere Fläche."""
    from game.aufgabe import QUELLE_FUNKSPRUCH, pruefe_aufgabe

    vorgabe = dict(
        kennung="probe",
        level=1,
        verfahren="caesar",
        richtung=VERSCHLUESSELN,
        schluessel=3,
        anzeigetext="ALLES OK",
        loesung="DOOHV",
        quelle=QUELLE_FUNKSPRUCH,
        rest_der_loesung="RN",
        knopf_beschriftung="Den Rest verschlüsseln",
        weiterrechnen_text="Du rechnest zu Ende.",
    )
    vorgabe[weglassen] = ""
    with pytest.raises(ValueError) as fehler:
        pruefe_aufgabe(Aufgabe(**vorgabe))
    assert weglassen in str(fehler.value)


def test_alle_funksprueche_mit_teilaufgabe_haben_alle_drei_felder():
    for aufgabe in MIT_TEILAUFGABE:
        assert aufgabe.rest_der_loesung
        assert aufgabe.knopf_beschriftung
        assert aufgabe.weiterrechnen_text


# ───────────────────────────────────────────────────────────────────────────
# 9. Fortschritt kostet keinen Versuch
# ───────────────────────────────────────────────────────────────────────────
#
# Ohne diese Regel bekäme jemand, der vier Buchstaben verzählt hat und sie
# einen nach dem anderen ausbessert, nach der dritten Ausbesserung die Lösung
# vorgesetzt – obwohl er die Methode verstanden hat und nur langsam war. In
# den Messdaten sähe das aus wie "nicht gekonnt".

from game.bearbeitung import HINWEIS_FORTSCHRITT  # noqa: E402
from game.rueckmeldung import fehlerzahl  # noqa: E402


def _mit_fehlern(loesung, anzahl):
    """Baut eine Eingabe mit genau ``anzahl`` falschen Buchstaben."""
    zeichen = list(loesung)
    stellen = [i for i, z in enumerate(zeichen) if z != " "]
    for i in stellen[:anzahl]:
        zeichen[i] = "A" if zeichen[i] != "A" else "B"
    ergebnis = "".join(zeichen)
    assert fehlerzahl(ergebnis, loesung) == anzahl
    return ergebnis


@pytest.mark.parametrize("aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE])
def test_wer_schritt_fuer_schritt_ausbessert_behaelt_seine_versuche(aufgabe):
    """Der Fall aus der Rückfrage: vier Fehler, einer nach dem anderen weg."""
    lauf = Bearbeitung(aufgabe)
    for anzahl in (4, 3, 2, 1):
        ergebnis = lauf.versuchen(_mit_fehlern(aufgabe.loesung, anzahl))
        assert not ergebnis.loesung_angezeigt, (
            f"Nach {ergebnis.versuche} Versuchen mit Fortschritt schon aufgelöst."
        )
    assert lauf.versuchen(aufgabe.loesung).richtig
    assert not lauf.loesung_angezeigt


def test_ein_besserer_versuch_zaehlt_nicht_gegen_das_kontingent():
    aufgabe = _uebung()
    lauf = Bearbeitung(aufgabe)
    lauf.versuchen("AAAA")             # 4 Fehler gegen KXQG
    assert lauf.versuche_ohne_fortschritt == 1
    ergebnis = lauf.versuchen("KAAA")  # 4 -> 3 Fehler
    assert ergebnis.fortschritt
    assert ergebnis.hinweis_fortschritt == HINWEIS_FORTSCHRITT
    assert lauf.versuche_ohne_fortschritt == 0
    assert lauf.verbleibende_versuche == HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT


def test_der_erste_versuch_ist_noch_kein_fortschritt():
    """Es gibt noch nichts, wogegen er besser sein könnte."""
    lauf = Bearbeitung(_uebung())
    ergebnis = lauf.versuchen("AAAA")
    assert not ergebnis.fortschritt
    assert lauf.versuche_ohne_fortschritt == 1
    assert lauf.beste_fehlerzahl == 4


def test_gleich_gut_ist_kein_fortschritt():
    """Sonst liesse sich die Strähne durch blosses Umtippen zurücksetzen."""
    lauf = Bearbeitung(_uebung())
    lauf.versuchen("AAAA")
    ergebnis = lauf.versuchen("BBBB")
    assert not ergebnis.fortschritt
    assert lauf.versuche_ohne_fortschritt == 2


def test_schlechter_werden_ist_kein_fortschritt():
    lauf = Bearbeitung(_uebung())
    lauf.versuchen("KXQA")             # 1 Fehler
    ergebnis = lauf.versuchen("AAAA")  # 4 Fehler
    assert not ergebnis.fortschritt
    assert lauf.versuche_ohne_fortschritt == 2
    assert lauf.beste_fehlerzahl == 1


def test_hin_und_herspringen_setzt_die_straehne_nicht_zurueck():
    """Verglichen wird gegen das bisherige Beste, nicht gegen den Vorgänger.

    Sonst könnte man abwechselnd verschlechtern und wieder verbessern und die
    Strähne beliebig oft auf null setzen, ohne je voranzukommen.
    """
    lauf = Bearbeitung(_uebung())
    lauf.versuchen("KXQA")   # 1 Fehler, bestes Ergebnis
    for _ in range(5):
        lauf.versuchen("AAAA")   # 4 Fehler
        lauf.versuchen("KXQA")   # wieder 1 – aber nicht besser als das Beste
    assert lauf.loesung_angezeigt


def test_drei_versuche_ohne_fortschritt_loesen_weiterhin_auf():
    lauf = Bearbeitung(_uebung())
    for nummer in range(HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT):
        ergebnis = lauf.versuchen("AAAA")
    assert ergebnis.loesung_angezeigt
    assert lauf.versuche_ohne_fortschritt == HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT


def test_nach_fortschritt_beginnt_die_straehne_von_vorn():
    lauf = Bearbeitung(_uebung())
    lauf.versuchen("AAAA")   # 4 Fehler
    lauf.versuchen("AAAA")   # nichts gewonnen
    assert lauf.versuche_ohne_fortschritt == 2
    lauf.versuchen("KAAA")   # 3 Fehler -> Fortschritt
    assert lauf.versuche_ohne_fortschritt == 0
    lauf.versuchen("KAAA")
    lauf.versuchen("KAAA")
    assert not lauf.loesung_angezeigt
    lauf.versuchen("KAAA")
    assert lauf.loesung_angezeigt


def test_die_regel_laeuft_nicht_endlos():
    """Jeder Fortschritt senkt die Fehlerzahl um mindestens eins.

    Mehr Fehler als Buchstaben kann eine Antwort nicht haben – die Zahl der
    "geschenkten" Versuche ist damit von selbst begrenzt.
    """
    aufgabe = MIT_TEILAUFGABE[0]
    hoechstens = len(aufgabe.loesung.replace(" ", ""))
    lauf = Bearbeitung(aufgabe)
    eingaben = 0
    for anzahl in range(hoechstens, 0, -1):
        lauf.versuchen(_mit_fehlern(aufgabe.loesung, anzahl))
        eingaben += 1
        if lauf.loesung_angezeigt:
            break
    assert eingaben <= hoechstens


def test_das_log_bekommt_beide_zahlen():
    """"Acht Versuche, keiner ohne Fortschritt" ist etwas anderes als
    "drei Versuche, alle ohne Fortschritt" – beides gehört ins Log."""
    lauf = Bearbeitung(_uebung())
    lauf.versuchen("AAAA")
    lauf.versuchen("KAAA")
    lauf.versuchen("KXAA")
    assert lauf.versuche == 3
    assert lauf.versuche_ohne_fortschritt == 0
    assert not lauf.loesung_angezeigt


def test_die_fehlerzahl_steht_im_ergebnis():
    """Die UI kann daraus "noch 2 Buchstaben" anzeigen, ohne neu zu rechnen."""
    lauf = Bearbeitung(_uebung())
    assert lauf.versuchen("KXAA").fehlerzahl == 2  # Q und G falsch
    assert lauf.versuchen("KXQG").fehlerzahl == 0


def test_der_fortschrittshinweis_kommt_nur_bei_fortschritt():
    lauf = Bearbeitung(_uebung())
    assert lauf.versuchen("AAAA").hinweis_fortschritt == ""
    assert lauf.versuchen("KAAA").hinweis_fortschritt == HINWEIS_FORTSCHRITT
    assert lauf.versuchen("KXQG").hinweis_fortschritt == ""


def test_eine_leere_eingabe_veraendert_den_fortschritt_nicht():
    lauf = Bearbeitung(_uebung())
    lauf.versuchen("KAAA")
    beste = lauf.beste_fehlerzahl
    for _ in range(5):
        lauf.versuchen("")
    assert lauf.beste_fehlerzahl == beste
    assert lauf.versuche_ohne_fortschritt == 1


# ───────────────────────────────────────────────────────────────────────────
# 10. Nachgereicht: Randfälle, die bei der Durchsicht auffielen
# ───────────────────────────────────────────────────────────────────────────

def test_nach_aufgeben_bleiben_keine_versuche_uebrig():
    """Sonst stünde auf einer erledigten Aufgabe "noch 3 Versuche"."""
    lauf = Bearbeitung(_uebung())
    lauf.aufgeben()
    assert lauf.ist_beendet
    assert lauf.verbleibende_versuche == 0


def test_nach_dem_loesen_bleiben_keine_versuche_uebrig():
    lauf = Bearbeitung(_uebung())
    lauf.versuchen("KXQG")
    assert lauf.verbleibende_versuche == 0


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_die_ganze_nachricht_wird_mit_null_fehlern_gemeldet(aufgabe):
    """Die Oberfläche darf nicht "richtig" und "63 Fehler" nebeneinander zeigen."""
    ergebnis = Bearbeitung(aufgabe).versuchen(aufgabe.vollstaendige_loesung)
    assert ergebnis.richtig
    assert ergebnis.fehlerzahl == 0
    assert ergebnis.meldung == ""


@pytest.mark.parametrize(
    "aufgabe", MIT_TEILAUFGABE, ids=[a.kennung for a in MIT_TEILAUFGABE]
)
def test_fortschritt_an_der_ganzen_nachricht_wird_erkannt(aufgabe):
    """Wer die ganze Nachricht rechnet, darf nicht ins Kontingent laufen."""
    ganz = aufgabe.vollstaendige_loesung
    lauf = Bearbeitung(aufgabe)
    for anzahl in (4, 3, 2, 1):
        ergebnis = lauf.versuchen(_mit_fehlern(ganz, anzahl))
        assert ergebnis.fehlerzahl == anzahl, (
            f"Gemessen gegen die falsche Bezugslösung: {ergebnis.fehlerzahl}"
        )
        assert not ergebnis.loesung_angezeigt
    assert lauf.versuchen(ganz).richtig


@pytest.mark.parametrize("initialen", ["VM", "vm", "V.M.", " v m "])
def test_die_initialen_werden_normalisiert(initialen):
    """Die Schreibweise der Initialen soll nicht in den Funkspruch durchschlagen."""
    aufgabe = aufgabe_aus_funkspruch(story.FUNKSPRUCH_ERSTER_RUF, initialen)
    assert aufgabe.loesung == aufgabe_aus_funkspruch(
        story.FUNKSPRUCH_ERSTER_RUF, "VM"
    ).loesung


@pytest.mark.parametrize("leer", ["", "   ", "???", "123"])
def test_leere_initialen_werden_abgewiesen(leer):
    """Sie unterschreiben den Funkspruch – ohne sie fehlte die Unterschrift."""
    with pytest.raises(ValueError) as fehler:
        aufgabe_aus_funkspruch(story.FUNKSPRUCH_ERSTER_RUF, leer)
    assert "Initialen" in str(fehler.value)
