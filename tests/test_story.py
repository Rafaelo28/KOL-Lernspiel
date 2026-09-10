"""Tests für content/story.py (Arbeitsplan 2.3).

Der Schwerpunkt liegt auf den Funksprüchen. Sie sind der einzige Story-Text,
den die Spielenden nicht nur lesen, sondern selbst ver- und entschlüsseln
müssen – und an ihnen hängen zwei Projektregeln:

* Regel 3: kein Klartext-Funkverkehr. Jeder Funkspruch muss sich tatsächlich
  mit dem Verfahren seines Levels verschlüsseln lassen.
* Regel 2 der Textkonvention: Was angezeigt wird, muss der Lösung entsprechen.
  Ein Funkspruch, der beim Normalisieren seine Form ändert, würde die
  Spielenden an einer Stelle suchen lassen, die gar nicht falsch ist.

Dazu kommt die Falle, die in Phase 1 aufgefallen ist: Ziffern verschwinden
beim Normalisieren. "Quadrant 4" würde zu "QUADRANT" – der abgefangene
Funkspruch verlöre genau seine Aussage.
"""

import pytest

from content import story
from content.story import Erzaehltext, Funkspruch
from crypto import caesar, substitution, vigenere
from crypto.normalize import ALPHABET, LEERZEICHEN, normalisieren, vergleiche_tolerant

BEISPIEL_INITIALEN = "VM"

#: Ein Funkspruch, wie ihn das Spiel anzeigt: Platzhalter schon ersetzt.
def _fertiger_klartext(funkspruch, initialen=BEISPIEL_INITIALEN):
    return funkspruch.klartext.format(initialen=initialen)


FUNKSPRUCH_IDS = [f.kennung for f in story.FUNKSPRUECHE]
ERZAEHL_IDS = [e.kennung for e in story.ERZAEHLTEXTE]
MIT_TEILAUFGABE = [f for f in story.FUNKSPRUECHE if f.selbst_zu_loesen]
OHNE_TEILAUFGABE = [f for f in story.FUNKSPRUECHE if not f.selbst_zu_loesen]


# ───────────────────────────────────────────────────────────────────────────
# 1. Vollständigkeit – alles, was der Arbeitsplan verlangt
# ───────────────────────────────────────────────────────────────────────────

def test_alle_vom_arbeitsplan_verlangten_texte_sind_da():
    """2.3: Intro, Bobs zwei Funksprüche, Feind-Funkspruch, Übergang, Abschluss."""
    assert story.INTRO.absaetze
    assert story.FUNKSPRUCH_BOB_ERSTE_ANTWORT.klartext
    assert story.FUNKSPRUCH_BOB_ZWEITE_ANTWORT.klartext
    assert story.FUNKSPRUCH_VERFOLGER.klartext
    assert story.UEBERGANG_ZU_LEVEL_3.absaetze
    assert story.ABSCHLUSS.absaetze


def test_bob_meldet_sich_genau_zweimal():
    """Konzept: Bob funkt im ganzen Spiel nur zweimal – Ende Level 1 und 3."""
    von_bob = [f for f in story.FUNKSPRUECHE if f.absender == "Zentrale"]
    assert len(von_bob) == 2
    assert [f.level for f in von_bob] == [1, 3]


def test_in_level_2_meldet_sich_bob_nicht():
    """Der Übergang Level 2 zu 3 läuft ausdrücklich ohne Bob-Dialog."""
    absender = {f.absender for f in story.FUNKSPRUECHE_NACH_LEVEL[2]}
    assert "Zentrale" not in absender


def test_jedes_level_hat_die_funksprueche_aus_dem_konzept():
    assert set(story.FUNKSPRUECHE_NACH_LEVEL) == {1, 2, 3}
    # Level 1: senden und empfangen, Level 2: nur empfangen, Level 3: beides.
    richtungen = {
        level: [f.richtung for f in funksprueche]
        for level, funksprueche in story.FUNKSPRUECHE_NACH_LEVEL.items()
    }
    assert richtungen[1] == [story.SENDEN, story.EMPFANGEN]
    assert richtungen[2] == [story.EMPFANGEN]
    assert richtungen[3] == [story.SENDEN, story.EMPFANGEN]


def test_die_sichten_passen_zueinander():
    aus_der_tabelle = [
        f for level in sorted(story.FUNKSPRUECHE_NACH_LEVEL)
        for f in story.FUNKSPRUECHE_NACH_LEVEL[level]
    ]
    assert aus_der_tabelle == list(story.FUNKSPRUECHE)
    assert len({f.kennung for f in story.FUNKSPRUECHE}) == len(story.FUNKSPRUECHE)
    assert len({e.kennung for e in story.ERZAEHLTEXTE}) == len(story.ERZAEHLTEXTE)


# ───────────────────────────────────────────────────────────────────────────
# 2. Die Funksprüche folgen der Textkonvention
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=FUNKSPRUCH_IDS)
def test_der_klartext_ist_schon_normalisiert(funkspruch):
    """Sonst weicht der angezeigte Text von der geprüften Lösung ab."""
    fertig = _fertiger_klartext(funkspruch)
    assert normalisieren(fertig) == fertig, (
        f"{funkspruch.kennung}: wird beim Normalisieren zu "
        f"{normalisieren(fertig)!r}"
    )


@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=FUNKSPRUCH_IDS)
def test_kein_funkspruch_enthaelt_eine_ziffer(funkspruch):
    """Der Fallstrick aus Phase 1: Ziffern fallen nach Regel 6 ersatzlos weg.

    Aus "Quadrant 4 ist durchsucht" würde "QUADRANT IST DURCHSUCHT" – die
    Spielenden bekämen einen Funkspruch, der seine Aussage verloren hat.
    Zahlen gehören deshalb ausgeschrieben.
    """
    assert not any(zeichen.isdigit() for zeichen in funkspruch.klartext), (
        f"{funkspruch.kennung} enthält eine Ziffer – bitte ausschreiben "
        f'("QUADRANT VIER" statt "QUADRANT 4").'
    )


@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=FUNKSPRUCH_IDS)
def test_der_klartext_besteht_nur_aus_erlaubten_zeichen(funkspruch):
    fertig = _fertiger_klartext(funkspruch)
    assert set(fertig) <= set(ALPHABET) | {LEERZEICHEN}
    assert fertig.strip() == fertig
    assert "  " not in fertig


def test_der_verfolger_funkspruch_nennt_beide_quadranten():
    """Die Aussage des Funkspruchs hängt an genau diesen zwei Zahlwörtern."""
    text = story.FUNKSPRUCH_VERFOLGER.klartext
    assert "QUADRANT VIER" in text
    assert "QUADRANT SIEBEN" in text


# ───────────────────────────────────────────────────────────────────────────
# 3. Die Initialen der Spielfigur
# ───────────────────────────────────────────────────────────────────────────

def test_gesendete_funksprueche_werden_unterschrieben():
    """Konzept: Der Spieler signiert seine Meldungen mit seinen Initialen."""
    for funkspruch in story.FUNKSPRUECHE:
        if funkspruch.richtung == story.SENDEN:
            assert story.PLATZHALTER_INITIALEN in funkspruch.klartext, (
                f"{funkspruch.kennung} wird gesendet, trägt aber keine Initialen."
            )


def test_empfangene_funksprueche_tragen_keinen_platzhalter():
    """Bob und die Verfolger unterschreiben nicht mit deinen Initialen."""
    for funkspruch in story.FUNKSPRUECHE:
        if funkspruch.richtung == story.EMPFANGEN:
            assert story.PLATZHALTER_INITIALEN not in funkspruch.klartext


@pytest.mark.parametrize("initialen", ["VM", "ED", "JB", "AN", "TL"])
def test_der_platzhalter_laesst_sich_mit_jeder_figur_fuellen(initialen):
    """Die fünf Figuren aus dem Konzept – ihre Initialen kommen in 2.4."""
    for funkspruch in story.FUNKSPRUECHE:
        fertig = _fertiger_klartext(funkspruch, initialen)
        assert "{" not in fertig and "}" not in fertig
        assert normalisieren(fertig) == fertig
        if funkspruch.richtung == story.SENDEN:
            assert fertig.endswith(initialen)


# ───────────────────────────────────────────────────────────────────────────
# 4. Jeder Funkspruch ist mit dem Verfahren seines Levels wirklich lösbar
# ───────────────────────────────────────────────────────────────────────────

VERFAHREN = {
    story.CAESAR: lambda text: caesar.verschluesseln(text, 3),
    story.SUBSTITUTION: substitution.verschluesseln,
    story.VIGENERE: lambda text: vigenere.verschluesseln(text, "ROT"),
}
RUECKWEG = {
    story.CAESAR: lambda text: caesar.entschluesseln(text, 3),
    story.SUBSTITUTION: substitution.entschluesseln,
    story.VIGENERE: lambda text: vigenere.entschluesseln(text, "ROT"),
}


@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=FUNKSPRUCH_IDS)
def test_jeder_funkspruch_laesst_sich_ver_und_entschluesseln(funkspruch):
    """Projektregel 3: Jede Nachricht geht verschlüsselt über den Funk."""
    fertig = _fertiger_klartext(funkspruch)
    geheim = VERFAHREN[funkspruch.verfahren](fertig)
    assert geheim != fertig, "Der Geheimtext ist mit dem Klartext identisch."
    assert RUECKWEG[funkspruch.verfahren](geheim) == fertig
    assert vergleiche_tolerant(RUECKWEG[funkspruch.verfahren](geheim), fertig)


@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=FUNKSPRUCH_IDS)
def test_das_verfahren_passt_zum_level(funkspruch):
    """Level 1 Caesar, Level 2 Substitution, Level 3 Vigenère – sonst nichts."""
    erwartet = {1: story.CAESAR, 2: story.SUBSTITUTION, 3: story.VIGENERE}
    assert funkspruch.verfahren == erwartet[funkspruch.level]


@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=FUNKSPRUCH_IDS)
def test_der_geheimtext_behaelt_die_wortgrenzen(funkspruch):
    """Regel 3: Die Spielenden zählen die Wörter beim Rechnen von Hand mit."""
    fertig = _fertiger_klartext(funkspruch)
    geheim = VERFAHREN[funkspruch.verfahren](fertig)
    stellen = lambda text: [i for i, z in enumerate(text) if z == LEERZEICHEN]
    assert stellen(geheim) == stellen(fertig)


# ───────────────────────────────────────────────────────────────────────────
# 5. Erzähltexte
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("erzaehltext", story.ERZAEHLTEXTE, ids=ERZAEHL_IDS)
def test_kein_erzaehltext_ist_leer(erzaehltext):
    assert erzaehltext.kennung.strip()
    assert erzaehltext.absaetze
    for absatz in erzaehltext.absaetze:
        assert absatz.strip()
        assert absatz == absatz.strip()


@pytest.mark.parametrize("erzaehltext", story.ERZAEHLTEXTE, ids=ERZAEHL_IDS)
def test_erzaehltexte_enthalten_keinen_offenen_platzhalter(erzaehltext):
    """Ein vergessenes {initialen} würde im Spiel wörtlich auf dem Schirm stehen."""
    for absatz in erzaehltext.absaetze:
        assert "{" not in absatz and "}" not in absatz


def test_erzaehltexte_sind_normale_sprache_und_keine_funksprueche():
    """Sie werden angezeigt, nicht verschlüsselt – Satzzeichen sind erlaubt.

    Umgekehrt formuliert: Stünde ein Erzähltext versehentlich in
    Grossbuchstaben ohne Satzzeichen, wäre das ein Zeichen dafür, dass er
    eigentlich ein Funkspruch sein sollte.
    """
    for erzaehltext in story.ERZAEHLTEXTE:
        gesamt = " ".join(erzaehltext.absaetze)
        assert gesamt != gesamt.upper(), (
            f"{erzaehltext.kennung} ist durchgehend gross geschrieben."
        )
        assert any(zeichen in gesamt for zeichen in ".!?")


def test_der_abschluss_laesst_die_diamanten_zurueck():
    """Die Kernaussage des Endes – kein reiches Ende (Konzept, Punkt 4)."""
    text = " ".join(story.ABSCHLUSS.absaetze).lower()
    assert "leeren händen" in text
    assert "diamantensack" in text


def test_es_gibt_eine_beschriftung_fuer_den_warten_button():
    assert story.BESCHRIFTUNG_WARTEN.strip()


# ───────────────────────────────────────────────────────────────────────────
# 6. Die Wortlaute stammen aus dem Konzept
# ───────────────────────────────────────────────────────────────────────────

def test_die_wortlaute_stehen_so_im_konzept():
    """Stichproben gegen dokumentation/Konzept_Spiel.md.

    Verglichen werden Kernaussagen, nicht ganze Absätze: Der Klartext der
    Funksprüche ist hier normalisiert und im Konzept normal geschrieben.
    """
    from pathlib import Path

    quelle = (
        Path(__file__).resolve().parent.parent
        / "dokumentation"
        / "Konzept_Spiel.md"
    ).read_text(encoding="utf-8")

    for satz in (
        "Das Wrack brennt.",
        "Der Feind nutzt genau die",
        "Verstanden,\nHilfe ist unterwegs.",
        "lebend, aber mit leeren\nHänden",
        "wir finden den Verräter",
    ):
        assert satz in quelle, f"{satz!r} steht so nicht im Konzept."


@pytest.mark.parametrize(
    "funkspruch, stichwoerter",
    [
        (story.FUNKSPRUCH_BOB_ERSTE_ANTWORT, ("WIR HOEREN DICH", "CAESAR", "HANDBUCH")),
        (story.FUNKSPRUCH_VERFOLGER, ("QUADRANT", "DURCHSUCHT", "VERRAETER")),
        (story.FUNKSPRUCH_BOB_ZWEITE_ANTWORT, ("VERSTANDEN", "HILFE", "UNTERWEGS")),
        (story.FUNKSPRUCH_ERSTER_RUF, ("HALLO", "HOERT", "JEMAND")),
        (story.FUNKSPRUCH_STANDORT, ("STANDORT", "WRACK")),
    ],
    ids=["bob 1", "verfolger", "bob 2", "erster ruf", "standort"],
)
def test_jeder_funkspruch_sagt_das_worum_es_geht(funkspruch, stichwoerter):
    for wort in stichwoerter:
        assert wort in funkspruch.klartext, (
            f"{funkspruch.kennung} enthält {wort!r} nicht mehr."
        )


# ───────────────────────────────────────────────────────────────────────────
# 7. Teilaufgabe und Weiterrechnen
# ───────────────────────────────────────────────────────────────────────────
#
# Lange Funksprüche werden nicht gekürzt, sondern nur zum Teil von Hand
# gelöst; den Rest löst ein Knopf auf. Die Begründung steht im Kopf von
# content/story.py. Diese Tests halten die Eigenschaften fest, auf die sich
# Phase 4 (Prüfung), 5 (Logging) und 6 (Anzeige) verlassen.

@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=FUNKSPRUCH_IDS)
def test_die_teilaufgabe_ist_der_anfang_der_nachricht(funkspruch):
    """Phase 4 schneidet den Rest als ``klartext[len(selbst_zu_loesen):]`` ab."""
    if not funkspruch.selbst_zu_loesen:
        return
    assert funkspruch.klartext.startswith(funkspruch.selbst_zu_loesen), (
        f"{funkspruch.kennung}: {funkspruch.selbst_zu_loesen!r} ist kein "
        "Anfang des Klartexts."
    )


@pytest.mark.parametrize("funkspruch", MIT_TEILAUFGABE, ids=[f.kennung for f in MIT_TEILAUFGABE])
def test_die_teilaufgabe_endet_an_einer_wortgrenze(funkspruch):
    """Ein halbes Wort zu entschlüsseln fühlt sich willkürlich an."""
    naechstes_zeichen = funkspruch.klartext[len(funkspruch.selbst_zu_loesen)]
    assert naechstes_zeichen == LEERZEICHEN, (
        f"{funkspruch.kennung}: Der Schnitt liegt mitten im Wort "
        f"(nächstes Zeichen {naechstes_zeichen!r})."
    )


@pytest.mark.parametrize("funkspruch", MIT_TEILAUFGABE, ids=[f.kennung for f in MIT_TEILAUFGABE])
def test_die_teilaufgabe_laesst_wirklich_etwas_uebrig(funkspruch):
    """Sonst wäre der Knopf sinnlos – dann gehört das Feld leer gelassen."""
    assert funkspruch.selbst_zu_loesen != funkspruch.klartext
    rest = funkspruch.klartext[len(funkspruch.selbst_zu_loesen):].strip()
    assert rest, f"{funkspruch.kennung} hat keinen Rest zum Weiterrechnen."


@pytest.mark.parametrize("funkspruch", MIT_TEILAUFGABE, ids=[f.kennung for f in MIT_TEILAUFGABE])
def test_keine_teilaufgabe_ueberschreitet_die_hoechstlaenge(funkspruch):
    """Der Schwellenwert steht an einer Stelle und wird nach dem Pilot angepasst."""
    buchstaben = len(funkspruch.selbst_zu_loesen.replace(LEERZEICHEN, ""))
    assert buchstaben <= story.HOECHSTLAENGE_TEILAUFGABE, (
        f"{funkspruch.kennung}: {buchstaben} Buchstaben von Hand – erlaubt "
        f"sind {story.HOECHSTLAENGE_TEILAUFGABE} "
        f"(story.HOECHSTLAENGE_TEILAUFGABE)."
    )


@pytest.mark.parametrize("funkspruch", OHNE_TEILAUFGABE, ids=[f.kennung for f in OHNE_TEILAUFGABE])
def test_keine_ganze_nachricht_ueberschreitet_ihre_hoechstlaenge(funkspruch):
    """Zweite Zahl für die Funksprüche ohne Teilaufgabe.

    Beide Grenzen getrennt zu halten ist der Punkt: Sonst wäre
    HOECHSTLAENGE_TEILAUFGABE nach unten durch die kürzeste vollständige
    Nachricht blockiert, und der Stellknopf für den Pilotdurchlauf liesse sich
    gar nicht mehr verstellen.
    """
    buchstaben = len(_fertiger_klartext(funkspruch).replace(LEERZEICHEN, ""))
    assert buchstaben <= story.HOECHSTLAENGE_GANZE_NACHRICHT, (
        f"{funkspruch.kennung}: {buchstaben} Buchstaben ganz von Hand – "
        f"erlaubt sind {story.HOECHSTLAENGE_GANZE_NACHRICHT}."
    )


@pytest.mark.parametrize("funkspruch", MIT_TEILAUFGABE, ids=[f.kennung for f in MIT_TEILAUFGABE])
def test_zu_jeder_teilaufgabe_gehoert_ein_weiterrechnen_text(funkspruch):
    """Ohne Erzähltext wirkt der Knopf wie eine Abkürzung statt wie Arbeit."""
    assert funkspruch.weiterrechnen.strip(), (
        f"{funkspruch.kennung} hat eine Teilaufgabe, aber keinen Übergangstext."
    )
    assert "{" not in funkspruch.weiterrechnen


@pytest.mark.parametrize("funkspruch", OHNE_TEILAUFGABE, ids=[f.kennung for f in OHNE_TEILAUFGABE])
def test_ohne_teilaufgabe_gibt_es_auch_keinen_uebergangstext(funkspruch):
    """Sonst stünde im Spiel ein Text zu einem Knopf, den es nicht gibt."""
    assert not funkspruch.weiterrechnen


def test_die_kurzen_funksprueche_werden_ganz_selbst_geloest():
    """Der erste Ruf und Bobs zweite Antwort bleiben vollständige Aufgaben.

    Bobs zweite Antwort ist der Schluss der Geschichte – den will man selbst
    entschlüsseln, nicht per Knopf aufgelöst bekommen.
    """
    kennungen = {f.kennung for f in OHNE_TEILAUFGABE}
    assert kennungen == {"erster_ruf", "bob_zweite_antwort"}


@pytest.mark.parametrize("funkspruch", MIT_TEILAUFGABE, ids=[f.kennung for f in MIT_TEILAUFGABE])
def test_die_teilaufgabe_ist_fuer_sich_verstaendlich(funkspruch):
    """Der geschnittene Anfang soll eine lesbare Aussage sein, kein Fragment."""
    assert len(funkspruch.selbst_zu_loesen.split()) >= 3, (
        f"{funkspruch.kennung}: {funkspruch.selbst_zu_loesen!r} ist zu kurz, "
        "um für sich zu stehen."
    )


@pytest.mark.parametrize("funkspruch", MIT_TEILAUFGABE, ids=[f.kennung for f in MIT_TEILAUFGABE])
def test_die_teilaufgabe_traegt_keine_initialen(funkspruch):
    """Die Unterschrift steht am Ende – sie darf nie in den Teil rutschen."""
    assert story.PLATZHALTER_INITIALEN not in funkspruch.selbst_zu_loesen


@pytest.mark.parametrize("funkspruch", MIT_TEILAUFGABE, ids=[f.kennung for f in MIT_TEILAUFGABE])
def test_der_geheimtext_der_teilaufgabe_ist_der_anfang_des_ganzen(funkspruch):
    """Der Rest muss sich hinten anfügen lassen, ohne dass der Anfang kippt.

    Beim Empfangen zeigt Phase 6 den ganzen Geheimtext und hebt den zu
    lösenden Anfang hervor; beim Senden wird nach dem Knopf der Geheimtext des
    Restes an den selbst getippten Anfang gehängt. Beides funktioniert nur,
    wenn der Geheimtext der Teilaufgabe wirklich der Anfang des vollständigen
    Geheimtexts ist. Bei Caesar und Substitution ist das selbstverständlich,
    bei Vigenère nicht: Dort hängt jeder Buchstabe von seiner Position im
    Schlüssel ab.

    (Beim Senden darf der vollständige Geheimtext nie angezeigt werden – er
    ist die Lösung. Siehe CLAUDE.md, Abschnitt "Lange Funksprüche".)
    """
    fertig = _fertiger_klartext(funkspruch)
    ganzer_geheimtext = VERFAHREN[funkspruch.verfahren](fertig)
    teil_geheimtext = VERFAHREN[funkspruch.verfahren](funkspruch.selbst_zu_loesen)
    assert ganzer_geheimtext.startswith(teil_geheimtext), (
        f"{funkspruch.kennung}: Der Geheimtext der Teilaufgabe ist nicht der "
        "Anfang des vollständigen Geheimtexts – die Anzeige aus Phase 6 "
        "würde zwei verschiedene Texte zeigen."
    )


def test_es_gibt_fuer_beide_richtungen_eine_knopfbeschriftung():
    assert set(story.BESCHRIFTUNG_REST) == {story.SENDEN, story.EMPFANGEN}
    for beschriftung in story.BESCHRIFTUNG_REST.values():
        assert beschriftung.strip()


def test_der_schwellenwert_bleibt_in_einem_sinnvollen_bereich():
    """Der Schwellenwert selbst braucht eine Grenze, sonst ist er zahnlos.

    ``test_keine_teilaufgabe_ueberschreitet_die_hoechstlaenge`` vergleicht die
    Teilaufgaben gegen ``HOECHSTLAENGE_TEILAUFGABE``. Wer die Konstante
    hochsetzt, macht damit auch diesen Test stumm – und hätte genau das
    Problem zurück, für das die Teilaufgabe gebaut wurde (78 Buchstaben von
    Hand im 15-Minuten-Fenster).

    Der Wert darf und soll nach dem Pilotdurchlauf angepasst werden, aber nur
    innerhalb dessen, was von Hand in einem Level zu schaffen ist. Wer ihn
    darüber hinaus braucht, sollte stattdessen die Teilaufgabe kürzen.
    """
    assert 10 <= story.HOECHSTLAENGE_GANZE_NACHRICHT <= 40
    assert 10 <= story.HOECHSTLAENGE_TEILAUFGABE <= 40, (
        f"HOECHSTLAENGE_TEILAUFGABE = {story.HOECHSTLAENGE_TEILAUFGABE}. "
        "Unter 10 Buchstaben ist die Aufgabe kein Beleg für das Verfahren, "
        "über 40 wird sie im Zeitfenster nicht mehr zu schaffen sein."
    )


# ───────────────────────────────────────────────────────────────────────────
# 8. Nachgereicht: Felder, die stillschweigend leer bleiben konnten
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=FUNKSPRUCH_IDS)
def test_jeder_funkspruch_hat_eine_einleitung(funkspruch):
    """Ohne sie steht die Nachricht unvermittelt auf dem Bildschirm.

    Eine Mutationsprobe hatte gezeigt, dass eine geleerte Einleitung von
    keinem Test bemerkt wurde.
    """
    assert funkspruch.einleitung.strip()
    assert "{" not in funkspruch.einleitung


@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=FUNKSPRUCH_IDS)
def test_der_schluessel_passt_zum_verfahren(funkspruch):
    """Caesar braucht eine Zahl, Vigenère ein Wort, die Substitution nichts."""
    if funkspruch.verfahren == story.CAESAR:
        assert isinstance(funkspruch.schluessel, int)
        assert 1 <= funkspruch.schluessel <= 25
    elif funkspruch.verfahren == story.VIGENERE:
        assert isinstance(funkspruch.schluessel, str) and funkspruch.schluessel
        assert normalisieren(funkspruch.schluessel) == funkspruch.schluessel
    else:
        assert funkspruch.schluessel is None, (
            "Bei der Substitution ist die Tabelle der Schlüssel."
        )


@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=FUNKSPRUCH_IDS)
def test_der_funkspruch_laesst_sich_mit_seinem_eigenen_schluessel_loesen(funkspruch):
    """Der Ernstfall: nicht irgendein Schlüssel, sondern der hinterlegte."""
    from crypto import caesar as _caesar, substitution as _sub, vigenere as _vig

    fertig = _fertiger_klartext(funkspruch)
    if funkspruch.verfahren == story.CAESAR:
        geheim = _caesar.verschluesseln(fertig, funkspruch.schluessel)
        assert _caesar.entschluesseln(geheim, funkspruch.schluessel) == fertig
    elif funkspruch.verfahren == story.VIGENERE:
        geheim = _vig.verschluesseln(fertig, funkspruch.schluessel)
        assert _vig.entschluesseln(geheim, funkspruch.schluessel) == fertig
    else:
        assert _sub.entschluesseln(_sub.verschluesseln(fertig)) == fertig


@pytest.mark.parametrize("funkspruch", story.FUNKSPRUECHE, ids=FUNKSPRUCH_IDS)
def test_die_absenderkennung_ist_aufloesbar(funkspruch):
    """Bob soll aus seinem Funkspruch heraus auffindbar sein."""
    from content import charaktere

    if funkspruch.absender_kennung == story.ABSENDER_SPIELFIGUR:
        assert funkspruch.richtung == story.SENDEN
    elif funkspruch.absender_kennung == story.ABSENDER_UNBEKANNT:
        assert funkspruch.absender == "unbekannt"
    else:
        assert funkspruch.absender_kennung == charaktere.BOB.kennung
        assert funkspruch.absender_kennung not in charaktere.CHARAKTER_NACH_KENNUNG


def test_bobs_beide_funksprueche_sind_ihm_zugeordnet():
    from content import charaktere

    von_bob = [f for f in story.FUNKSPRUECHE if f.absender_kennung == charaktere.BOB.kennung]
    assert [f.level for f in von_bob] == [1, 3]


def test_der_hinweis_und_die_reflexionsfrage_sind_da():
    """Arbeitsplan 7.2 und 7.3 verlangen beide Texte."""
    assert "Häufigkeitsanalyse" in " ".join(story.HINWEIS_HAEUFIGKEITSANALYSE.absaetze)
    assert "?" in " ".join(story.REFLEXIONSFRAGE_LEVEL_3.absaetze)
