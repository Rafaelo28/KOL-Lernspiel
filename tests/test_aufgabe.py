"""Tests für game/aufgabe.py (Arbeitsplan 3.1).

Zwei Schwerpunkte:

1. **Widerspruchsfreiheit.** ``pruefe_aufgabe()`` muss jede Aufgabe abweisen,
   deren Lösung nicht wirklich aus ihrem Anzeigetext folgt. Eine solche
   Aufgabe würde im Spiel jede richtige Eingabe als falsch werten, und nach
   drei Versuchen bekämen die Spielenden eine "Lösung" gezeigt, die gar keine
   ist.
2. **Das Objekt trägt auch die echten Funksprüche.** Phase 4 behandelt
   Handbuch-Übungen und Funksprüche gleich. Wenn sich die fünf Funksprüche aus
   ``content/story.py`` nicht als :class:`Aufgabe` ausdrücken lassen, bräuchte
   das Fehlerhandling zwei Wege – und die 3-Versuche-Regel könnte auf einem
   davon fehlen.
"""

import pytest

from content import charaktere, story, uebungen, verfahren
from crypto import caesar, substitution, vigenere
from crypto.normalize import LEERZEICHEN, normalisieren
from game import aufgabe as aufgabenmodul
from game.generator import aufgabe_aus_funkspruch
from game.aufgabe import (
    ENTSCHLUESSELN,
    QUELLE_FUNKSPRUCH,
    QUELLE_UEBUNG,
    VERSCHLUESSELN,
    Aufgabe,
    anwenden,
    gegenrichtung,
    pruefe_aufgabe,
)


def _uebungsaufgabe(**abweichend):
    """Eine gültige Beispielaufgabe, die einzelne Tests gezielt verbiegen."""
    vorgabe = dict(
        kennung="probe",
        level=1,
        verfahren=verfahren.CAESAR,
        richtung=VERSCHLUESSELN,
        schluessel=3,
        anzeigetext="HUND",
        loesung="KXQG",
    )
    vorgabe.update(abweichend)
    return Aufgabe(**vorgabe)


# ───────────────────────────────────────────────────────────────────────────
# 1. anwenden() – die Brücke von der Kennung zum crypto-Modul
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "kennung, schluessel, klartext, geheimtext",
    [
        (verfahren.CAESAR, 3, "HUND", "KXQG"),
        (verfahren.SUBSTITUTION, None, "HUND", "IXFR"),
        (verfahren.VIGENERE, "ROT", "HUND", "YIGU"),
    ],
)
def test_anwenden_trifft_die_referenzwerte_des_handbuchs(
    kennung, schluessel, klartext, geheimtext
):
    """Die Zuordnung Kennung -> Modul muss stimmen, sonst rechnet das Spiel falsch."""
    assert anwenden(kennung, VERSCHLUESSELN, klartext, schluessel) == geheimtext
    assert anwenden(kennung, ENTSCHLUESSELN, geheimtext, schluessel) == klartext


def test_anwenden_deckt_alle_verfahren_ab():
    """Kommt ein viertes Verfahren dazu, soll dieser Test daran erinnern."""
    assert set(aufgabenmodul.VERFAHRENSFUNKTIONEN) == set(verfahren.ALLE)


@pytest.mark.parametrize("unsinn", ["rot13", "", None, 3])
def test_anwenden_weist_unbekannte_verfahren_ab(unsinn):
    with pytest.raises(ValueError):
        anwenden(unsinn, VERSCHLUESSELN, "HUND", 3)


@pytest.mark.parametrize("unsinn", ["knacken", "", None])
def test_anwenden_weist_unbekannte_richtungen_ab(unsinn):
    with pytest.raises(ValueError):
        anwenden(verfahren.CAESAR, unsinn, "HUND", 3)


def test_gegenrichtung_dreht_die_richtung_um():
    assert gegenrichtung(VERSCHLUESSELN) == ENTSCHLUESSELN
    assert gegenrichtung(gegenrichtung(VERSCHLUESSELN)) == VERSCHLUESSELN
    with pytest.raises(ValueError):
        gegenrichtung("seitwaerts")


# ───────────────────────────────────────────────────────────────────────────
# 2. Die Felder des Aufgabenobjekts
# ───────────────────────────────────────────────────────────────────────────

def test_das_objekt_hat_die_vom_arbeitsplan_verlangten_felder():
    """3.1: Richtung, Anzeigetext, Schlüssel, erwartete Lösung, Level."""
    assert {"richtung", "anzeigetext", "schluessel", "loesung", "level"} <= set(
        Aufgabe._fields
    )


def test_eine_uebungsaufgabe_kommt_ohne_zusatzangaben_aus():
    """Die Vorgabewerte sollen den häufigen Fall abdecken."""
    a = _uebungsaufgabe()
    assert a.quelle == QUELLE_UEBUNG
    assert a.rest_der_loesung == ""
    assert a.zusatzaufgabe is False
    assert a.hat_teilaufgabe is False
    assert a.vollstaendige_loesung == a.loesung


def test_die_geloest_pruefung_ist_tolerant():
    """Textkonvention Regel 4: Leerzeichen und Kleinschreibung zählen nicht."""
    a = _uebungsaufgabe(anzeigetext="ALLES OK", loesung="DOOHV RN")
    assert a.ist_geloest("DOOHV RN")
    assert a.ist_geloest("doohv rn")
    assert a.ist_geloest("DOOHVRN")
    assert not a.ist_geloest("DOOHV RM")


def test_die_laenge_zaehlt_nur_buchstaben():
    """Diese Zahl gehört ins Log (Arbeitsplan 5.5)."""
    a = _uebungsaufgabe(anzeigetext="ALLES OK", loesung="DOOHV RN")
    assert a.laenge_in_buchstaben == 7


def test_bei_einer_teilaufgabe_zaehlt_nur_der_selbst_geloeste_teil():
    """Sonst wären Teilaufgaben und ganze Nachrichten im Log nicht vergleichbar."""
    a = _uebungsaufgabe(
        quelle=QUELLE_FUNKSPRUCH,
        anzeigetext="ALLES OK",
        loesung="DOOHV",
        rest_der_loesung="RN",
    )
    assert a.hat_teilaufgabe is True
    assert a.laenge_in_buchstaben == 5
    assert a.vollstaendige_loesung == "DOOHV RN"


# ───────────────────────────────────────────────────────────────────────────
# 3. pruefe_aufgabe() – der Selbsttest für den Generator aus 3.2
# ───────────────────────────────────────────────────────────────────────────

def test_eine_stimmige_aufgabe_wird_angenommen():
    pruefe_aufgabe(_uebungsaufgabe())


@pytest.mark.parametrize(
    "abweichend, stichwort",
    [
        ({"loesung": "FALSCH"}, "folgt"),
        ({"schluessel": 4}, "folgt"),
        ({"anzeigetext": "KATZE"}, "folgt"),
        ({"richtung": ENTSCHLUESSELN}, "folgt"),
        ({"level": 9}, "Level"),
        ({"level": 2}, "benutzt"),
        ({"richtung": "seitwaerts"}, "Richtung"),
        ({"quelle": "irgendwoher"}, "Quelle"),
        ({"loesung": ""}, "leer"),
        ({"anzeigetext": ""}, "leer"),
        ({"anzeigetext": "Hund!"}, "normalisiert"),
        ({"loesung": "kxqg"}, "normalisiert"),
        # Inhaltlich stimmig, aber eine Handbuch-Übung darf keinen Rest haben.
        (
            {
                "anzeigetext": "ALLES OK",
                "loesung": "DOOHV",
                "rest_der_loesung": "RN",
            },
            "Funksprüchen",
        ),
    ],
)
def test_widerspruechliche_aufgaben_werden_abgewiesen(abweichend, stichwort):
    """Jeder dieser Fälle würde im Spiel richtige Eingaben als falsch werten."""
    with pytest.raises(ValueError) as fehler:
        pruefe_aufgabe(_uebungsaufgabe(**abweichend))
    assert stichwort in str(fehler.value)


def test_ein_falscher_rest_faellt_auf():
    """Lösung und Rest müssen zusammen wirklich den ganzen Geheimtext ergeben."""
    with pytest.raises(ValueError) as fehler:
        pruefe_aufgabe(
            _uebungsaufgabe(
                quelle=QUELLE_FUNKSPRUCH,
                anzeigetext="ALLES OK",
                loesung="DOOHV",
                rest_der_loesung="XX",
            )
        )
    assert "zusammen" in str(fehler.value)


# ───────────────────────────────────────────────────────────────────────────
# 4. Das Objekt trägt jede Übung aus dem Pool
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", uebungen.UEBUNGSWOERTER_LEVEL_1, ids=lambda t: t)
@pytest.mark.parametrize("richtung", [VERSCHLUESSELN, ENTSCHLUESSELN])
def test_jede_caesar_uebung_laesst_sich_als_aufgabe_ausdruecken(text, richtung):
    """Vorgriff auf 3.2: Bei "entschlüsseln" wird der Geheimtext angezeigt."""
    schluessel = uebungen.CAESAR_SCHLUESSEL_HANDBUCH
    anzeige = text if richtung == VERSCHLUESSELN else caesar.verschluesseln(text, schluessel)
    a = Aufgabe(
        kennung=f"l1_{text}_{richtung}",
        level=1,
        verfahren=verfahren.CAESAR,
        richtung=richtung,
        schluessel=schluessel,
        anzeigetext=anzeige,
        loesung=anwenden(verfahren.CAESAR, richtung, anzeige, schluessel),
    )
    pruefe_aufgabe(a)
    assert a.ist_geloest(a.loesung)


@pytest.mark.parametrize("text", uebungen.UEBUNGSSAETZE_LEVEL_3, ids=lambda t: t[:12])
@pytest.mark.parametrize("wort", uebungen.VIGENERE_SCHLUESSELWOERTER)
def test_jede_vigenere_uebung_laesst_sich_als_aufgabe_ausdruecken(text, wort):
    anzeige = vigenere.verschluesseln(text, wort)
    a = Aufgabe(
        kennung=f"l3_{wort}",
        level=3,
        verfahren=verfahren.VIGENERE,
        richtung=ENTSCHLUESSELN,
        schluessel=wort,
        anzeigetext=anzeige,
        loesung=text,
    )
    pruefe_aufgabe(a)


@pytest.mark.parametrize("text", uebungen.UEBUNGSSAETZE_LEVEL_2, ids=lambda t: t[:12])
def test_jede_substitutions_uebung_laesst_sich_als_aufgabe_ausdruecken(text):
    a = Aufgabe(
        kennung="l2",
        level=2,
        verfahren=verfahren.SUBSTITUTION,
        richtung=VERSCHLUESSELN,
        schluessel=None,
        anzeigetext=text,
        loesung=substitution.verschluesseln(text),
    )
    pruefe_aufgabe(a)


# ───────────────────────────────────────────────────────────────────────────
# 5. Das Objekt trägt auch die fünf echten Funksprüche
# ───────────────────────────────────────────────────────────────────────────

# Die Umrechnung Funkspruch -> Aufgabe steht seit 3.2 in game/generator.py.
# Hier wird sie nur benutzt, damit die Logik nicht zweimal im Projekt liegt
# und die beiden Fassungen auseinanderlaufen können. Die Vorgabe für die
# Initialen ist Testbequemlichkeit und gehört bewusst nicht in den Generator:
# Im Spiel steht die gewählte Figur immer fest.
def _aus_funkspruch(funkspruch, initialen="VM"):
    return aufgabe_aus_funkspruch(funkspruch, initialen)


@pytest.mark.parametrize(
    "funkspruch", story.FUNKSPRUECHE, ids=[f.kennung for f in story.FUNKSPRUECHE]
)
def test_jeder_funkspruch_laesst_sich_als_aufgabe_ausdruecken(funkspruch):
    a = _aus_funkspruch(funkspruch)
    pruefe_aufgabe(a)
    assert a.quelle == QUELLE_FUNKSPRUCH
    assert a.ist_geloest(a.loesung)


@pytest.mark.parametrize(
    "funkspruch", story.FUNKSPRUECHE, ids=[f.kennung for f in story.FUNKSPRUECHE]
)
@pytest.mark.parametrize(
    "figur", charaktere.SPIELBARE_CHARAKTERE, ids=[f.kennung for f in charaktere.SPIELBARE_CHARAKTERE]
)
def test_der_funkspruch_bleibt_stimmig_egal_welche_figur_unterschreibt(funkspruch, figur):
    pruefe_aufgabe(_aus_funkspruch(funkspruch, figur.initialen))


def test_die_teilaufgaben_landen_als_solche_im_objekt():
    """Genau die drei langen Funksprüche haben einen Rest."""
    mit_rest = {
        f.kennung for f in story.FUNKSPRUECHE if _aus_funkspruch(f).hat_teilaufgabe
    }
    assert mit_rest == {"bob_erste_antwort", "verfolger", "standort"}


def test_beim_senden_ist_der_angezeigte_text_der_klartext():
    """Der Geheimtext ist die Lösung und darf nirgends abzulesen sein."""
    a = _aus_funkspruch(story.FUNKSPRUCH_STANDORT)
    assert a.richtung == VERSCHLUESSELN
    assert a.anzeigetext == normalisieren(
        story.FUNKSPRUCH_STANDORT.klartext.format(initialen="VM")
    )
    assert a.loesung not in a.anzeigetext


def test_beim_empfangen_ist_der_angezeigte_text_der_geheimtext():
    a = _aus_funkspruch(story.FUNKSPRUCH_BOB_ERSTE_ANTWORT)
    assert a.richtung == ENTSCHLUESSELN
    assert a.anzeigetext != a.vollstaendige_loesung
    assert a.vollstaendige_loesung == story.FUNKSPRUCH_BOB_ERSTE_ANTWORT.klartext
