"""Tests für den Aufgaben-Screen (Arbeitsplan 6.5): ui/uebung.py.

Geprüft wird, dass die Übung im Buch steht (Auftrag, Text, Schreibfeld), dass
links das richtige Werkzeug liegt, dass die Rückmeldung der Spiellogik
ankommt – Fehlermeldung, Fortschritt, Versuche, Lösung – und dass man mitten
in der Aufgabe nachschlagen und zu genau dieser Aufgabe zurückkehren kann.

Die Regeln selbst prüft die Spiellogik (``tests/test_bearbeitung.py``,
``tests/test_rueckmeldung.py``); hier geht es darum, dass der Screen sie
weiterreicht, statt eigene zu erfinden.

Braucht eine Bildschirmanzeige, sonst übersprungen.
"""

import pytest

tk = pytest.importorskip("tkinter")

from content import charaktere, story  # noqa: E402
from content import handbuch as buch  # noqa: E402
from content import verfahren  # noqa: E402
from crypto.normalize import ALPHABET  # noqa: E402
from game.aufgabe import VERSCHLUESSELN, Aufgabe, anwenden  # noqa: E402
from game.bearbeitung import HINWEIS_FORTSCHRITT  # noqa: E402
from game.rueckmeldung import rueckmeldung  # noqa: E402
from game.zeitfenster import DAUER_JE_LEVEL_SEKUNDEN  # noqa: E402
from ui import ablauf, funk, handbuch, stil, uebung  # noqa: E402
from ui.lineal import HINWEIS as LINEAL_HINWEIS  # noqa: E402

LEVEL = (1, 2, 3)


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


def _zur_uebung(fenster, level=1):
    """Spielt vom Startbildschirm bis zur ersten Übung des Levels.

    Seit Phase 7 überspringt kein Knopf mehr ein Level: Der Weg dorthin führt
    über die Aufgaben der Level davor, also werden sie gelöst.
    """
    fenster.aktueller_screen._feld.insert(0, "1-12")
    fenster.aktueller_screen.starten()
    fenster.aktueller_screen.waehle(charaktere.JONAS_BERG)
    fenster.aktueller_screen.bestaetigen()
    for _ in story.INTRO.absaetze:
        fenster.aktueller_screen.weiter()
    for _ in range(300):
        screen = fenster.aktueller_screen
        if isinstance(screen, uebung.Uebung) and screen.aufgabe.level == level:
            return screen
        _einen_schritt_weiter(fenster)
    raise AssertionError(f"Die erste Übung von Level {level} kam nie.")


def _nachlese_durchklicken(fenster):
    """Klickt die Funksprüche weg, die nach einem Zeitablauf zum Mitlesen dastehen (ui/ablauf.py)."""
    while isinstance(fenster.aktueller_screen, funk.Funk) and fenster.aktueller_screen.nur_lesen:
        fenster.aktueller_screen.weiter()
    return fenster.aktueller_screen


def _einen_schritt_weiter(fenster):
    """Löst die Aufgabe des Screens – oder klickt weiter, wenn keine dasteht."""
    screen = fenster.aktueller_screen
    aufgabe = getattr(screen, "aufgabe", None)
    if aufgabe is None:
        screen.weiter()
        return
    if hasattr(screen, "anzeige_vervollstaendigen"):
        screen.anzeige_vervollstaendigen()        # den Schreibmaschinen-Takt überspringen
    screen._feld.delete(0, "end")
    screen._feld.insert(0, aufgabe.loesung)
    screen.pruefen()
    if getattr(screen, "restknopf_sichtbar", False):
        screen.rest_freigeben()
    screen.weiter()


def _eine_zeile(texte):
    """Texte zu einer Zeile zusammengezogen – egal, wo umbrochen wurde."""
    return " ".join(" ".join(texte).split())


def _tippen(screen, text):
    """Schreibt ``text`` in das Schreibfeld – wie von Hand eingetippt."""
    screen._feld.delete(0, "end")
    screen._feld.insert(0, text)


def _mit_fehler(loesung, anzahl=1):
    """Die Lösung mit ``anzahl`` falschen Buchstaben, von vorne weg."""
    zeichen = list(loesung)
    falsch = 0
    for nr, buchstabe in enumerate(zeichen):
        if buchstabe == " " or falsch >= anzahl:
            continue
        zeichen[nr] = "A" if buchstabe != "A" else "B"
        falsch += 1
    return "".join(zeichen)


def _letzter_falsch(loesung):
    """Die Lösung mit falschem letztem Buchstaben – und dessen Stelle im Text."""
    zeichen = list(loesung)
    stelle = max(nr for nr, b in enumerate(zeichen) if b != " ")
    zeichen[stelle] = "A" if zeichen[stelle] != "A" else "B"
    return "".join(zeichen), stelle


# ── Was auf der Doppelseite steht ──────────────────────────────────────────

@pytest.mark.parametrize("level", LEVEL)
def test_die_uebung_steht_auf_der_rechten_buchseite(fenster, level):
    screen = _zur_uebung(fenster, level)
    rechts = _eine_zeile(screen.texte("rechts"))
    assert "Übung 1" in rechts
    assert screen.auftrag(screen.aufgabe) in rechts
    assert screen.aufgabe.anzeigetext in rechts
    assert uebung.BESCHRIFTUNG_ANTWORT in rechts
    assert screen.aufgabe.loesung not in rechts        # die Lösung steht nirgends


@pytest.mark.parametrize("level, angabe", [(1, "Schlüssel"), (2, "deine Geheimtabelle"),
                                           (3, "Schlüsselwort")])
def test_der_auftrag_nennt_richtung_und_schluessel(fenster, level, angabe):
    screen = _zur_uebung(fenster, level)
    auftrag = screen.auftrag(screen.aufgabe)
    assert auftrag.startswith(("VERSCHLÜSSELN", "ENTSCHLÜSSELN"))
    assert angabe in auftrag
    if level != 2:                                     # die Substitution hat keinen Schlüssel
        assert str(screen.aufgabe.schluessel) in auftrag


@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("level", LEVEL)
def test_das_richtungswort_steht_in_rotstift_neben_der_schluesselangabe(fenster, level):
    """"Verschlüssele" und "Entschlüssele" sehen im Augenwinkel gleich aus.

    Eine Pilotperson hat deshalb einen Geheimtext ein zweites Mal
    verschlüsselt. Großbuchstaben und Rotstift sind zwei Unterscheidungen
    statt einer – und beides bleibt auf der Zeile, auf der vorher der ganze
    Satz stand.
    """
    screen = _zur_uebung(fenster, level)
    wort, rest = sorted(screen.buch.find_withtag("auftrag&&rechts"))
    assert screen.buch.itemcget(wort, "text") == uebung.RICHTUNGSWORT[screen.aufgabe.richtung]
    assert screen.buch.itemcget(wort, "fill") == stil.FARBE_ROTSTIFT
    assert screen.buch.itemcget(rest, "fill") == stil.FARBE_TINTE
    links, oben, rechts_kante, unten = screen.buch.bbox(wort)
    assert screen.buch.bbox(rest)[0] >= rechts_kante, "die Angabe steht daneben"
    assert screen.buch.bbox(rest)[1] == oben, "und auf derselben Zeile"


def test_die_uebungen_eines_levels_werden_gezaehlt(fenster):
    screen = _zur_uebung(fenster)
    _tippen(screen, screen.aufgabe.loesung)
    screen.pruefen()
    screen.weiter()
    assert "Übung 2" in _eine_zeile(fenster.aktueller_screen.texte("rechts"))


def test_bei_caesar_liegt_nur_das_blanke_alphabet_daneben(fenster):
    """Eine verschobene Zeile wäre für den Schlüssel der Aufgabe die halbe Lösung."""
    screen = _zur_uebung(fenster, 1)
    zellen = [screen.buch.itemcget(e, "text") for e in screen.buch.find_withtag("zelle&&links")]
    assert "".join(zellen) == ALPHABET


def test_bei_der_substitution_liegt_die_geheimtabelle_daneben(fenster):
    screen = _zur_uebung(fenster, 2)
    zellen = [screen.buch.itemcget(e, "text") for e in screen.buch.find_withtag("zelle&&links")]
    erwartet = [zelle for zeile in buch.GEHEIMTABELLE.zeilen for zelle in zeile[1:]]
    assert sorted(zellen) == sorted(erwartet)


def test_bei_vigenere_liegt_das_quadrat_daneben(fenster):
    screen = _zur_uebung(fenster, 3)
    assert screen.buch.quadratfeld("R", "H") == "Y"
    assert len(screen.buch.find_withtag("feld&&links")) == 26 * 26


@pytest.mark.parametrize("level", (1, 2))
def test_die_merkkarte_des_levels_liegt_mit_daneben(fenster, level):
    """Sie sagt mit den Sätzen des Handbuchs, wie man mit dem Werkzeug rechnet – ohne Blättern."""
    screen = _zur_uebung(fenster, level)
    karte = buch.MERKKARTE_NACH_LEVEL[level]
    links = _eine_zeile(screen.texte("links"))
    assert karte.ueberschrift in links
    for satz in karte.saetze:
        assert _eine_zeile([satz.text]) in links
    assert screen.buch.find_withtag("karte&&links")
    assert "Häufigkeitsanalyse" not in links


def test_neben_dem_quadrat_ist_fuer_eine_karte_kein_platz(fenster):
    screen = _zur_uebung(fenster, 3)
    assert not screen.buch.find_withtag("karte&&links")


def _quadratmitte(screen, zeile, spalte):
    """Die Mitte eines Feldes im Quadrat links – Zeile und Spalte -1 sind die Köpfe."""
    lineal = screen.lineal
    x0, y0, _, _ = screen.buch.flaeche("links")
    feld = lineal.quadrat.feld
    return (round(x0 + lineal.quadrat.x + (spalte + 1.5) * feld), round(y0 + lineal.quadrat.y + (zeile + 1.5) * feld))


def test_bei_vigenere_liegt_ein_lineal_am_quadrat(fenster, ausloesen):
    screen = _zur_uebung(fenster, 3)
    assert screen.lineal is not None and screen.lineal.seite == "links"
    assert _eine_zeile([LINEAL_HINWEIS]) in _eine_zeile(screen.texte("rechts"))
    bearbeitung = fenster.durchlauf.spielstand.aktuelle_bearbeitung
    for zeile, spalte in ((17, -1), (-1, 7)):
        x, y = _quadratmitte(screen, zeile, spalte)
        ausloesen(screen.buch, "<Button-1>", x=x, y=y)
    assert (screen.lineal.zeile, screen.lineal.spalte) == (17, 7)
    assert screen.buch.find_withtag("linealkreuzung")
    assert bearbeitung.lineal_klicks == 2
    ausloesen(screen.buch, "<Motion>", x=x, y=y)
    assert screen.buch.cget("cursor") == "hand2"
    ausloesen(screen.buch, "<Motion>", x=5, y=5)
    assert screen.buch.cget("cursor") == ""


@pytest.mark.parametrize("level", (1, 2))
def test_vor_level_3_gibt_es_kein_lineal(fenster, level):
    """Ohne Quadrat braucht es keins."""
    screen = _zur_uebung(fenster, level)
    assert screen.lineal is None
    assert not screen.buch.bind("<Button-1>")
    assert LINEAL_HINWEIS.split()[0] not in " ".join(screen.texte("rechts"))


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_der_hinweis_aufs_lineal_steht_zwischen_aufgabe_und_schreibfeld(fenster):
    """Vorher stand er am unteren Seitenrand – dort hat ihn die erste Testperson übersehen.

    Jetzt liegt er im Blickweg: unter dem Aufgabentext, über dem Feld, in das
    die Antwort kommt. Die Rückmeldung bleibt unter dem Feld und deckt ihn
    auch nach drei Fehlversuchen nicht zu.
    """
    screen = _zur_uebung(fenster, 3)
    stuecke = screen.buch.find_withtag("linealhinweis")
    assert stuecke
    oben = min(screen.buch.bbox(e)[1] for e in stuecke)
    unten = max(screen.buch.bbox(e)[3] for e in stuecke)
    text_unten = max(screen.buch.bbox(e)[3] for e in screen.buch.find_withtag("aufgabentext"))
    feld_oben = screen._ursprung[1] + screen._feldkasten[1]
    assert text_unten <= oben, "unter dem Aufgabentext"
    assert unten <= feld_oben, "und über dem Schreibfeld"

    falsch = _mit_fehler(screen.aufgabe.loesung, 99)
    for _ in range(3):
        _tippen(screen, falsch)
        screen.pruefen()
    assert screen.ist_beendet
    rueckmeldung_oben = min(screen.buch.bbox(e)[1] for e in screen.buch.find_withtag("rueckmeldung"))
    assert unten <= rueckmeldung_oben, "die Rückmeldung steht darunter, nicht darüber"
    assert screen.buch.find_withtag("linealhinweis"), "und der Hinweis steht noch da"


def test_der_hinweis_aufs_lineal_ist_mit_rotstift_dazugeschrieben(fenster):
    """Gedruckte Kleinschrift am Rand liest niemand – Handschrift in Rot fällt auf."""
    screen = _zur_uebung(fenster, 3)
    (stueck,) = screen.buch.find_withtag("linealhinweis")
    assert screen.buch.itemcget(stueck, "fill") == stil.FARBE_ROTSTIFT
    assert screen.buch.itemcget(stueck, "font") == str(screen.buch.schriften.notiz)
    assert float(screen.buch.itemcget(stueck, "angle")) > 0, "schief wie hingekritzelt"


def test_bei_der_ersten_uebung_zeigt_sich_das_lineal_von_selbst(fenster):
    """Zeigen statt schreiben: Man sieht die Bänder und den Kreuzungspunkt sofort."""
    screen = _zur_uebung(fenster, 3)
    assert (screen.lineal.zeile, screen.lineal.spalte) != (None, None)
    assert screen.buch.find_withtag("linealkreuzung")
    bearbeitung = fenster.durchlauf.spielstand.aktuelle_bearbeitung
    assert bearbeitung.lineal_klicks == 0, "vorgezeigt ist nicht selbst geklickt"


def test_das_vorgezeigte_lineal_liegt_nicht_auf_dem_ersten_schritt(fenster):
    """Sonst wäre die erste Zeile im Quadrat schon markiert – die halbe Arbeit."""
    screen = _zur_uebung(fenster, 3)
    schluessel, text = screen.aufgabe.schluessel, screen.aufgabe.anzeigetext
    erster = (ALPHABET.index(schluessel[0]), ALPHABET.index(text.replace(" ", "")[0]))
    assert screen.lineal.zeile != erster[0] and screen.lineal.spalte != erster[1]


def test_bei_der_zweiten_uebung_zeigt_sich_das_lineal_nicht_mehr(fenster):
    """Wer eine Aufgabe hinter sich hat, weiss davon – und ein fremd liegendes Lineal wäre im Weg."""
    screen = _zur_uebung(fenster, 3)
    _tippen(screen, screen.aufgabe.loesung)
    screen.pruefen()
    screen.weiter()
    zweite = fenster.aktueller_screen
    assert isinstance(zweite, uebung.Uebung) and zweite.aufgabe is not None
    assert (zweite.lineal.zeile, zweite.lineal.spalte) == (None, None)


def test_geschrieben_wird_in_handschrift(fenster):
    screen = _zur_uebung(fenster)
    assert screen._feld.cget("font") == str(screen.buch.schriften.notiz)
    assert screen._feld.cget("fg") == stil.FARBE_BLEISTIFT


# ── Prüfen ─────────────────────────────────────────────────────────────────

def test_die_richtige_antwort_wird_gelobt_und_gestempelt(fenster):
    screen = _zur_uebung(fenster)
    _tippen(screen, screen.aufgabe.loesung)
    screen.pruefen()
    assert uebung.LOB in _eine_zeile(screen.rueckmeldung())
    assert screen.buch.find_withtag("stempel")
    assert screen.ist_beendet and screen.knopftext == uebung.KNOPF_WEITER
    assert fenster.durchlauf.spielstand.aktuelle_bearbeitung.geloest


def test_kleingeschrieben_ist_auch_richtig(fenster):
    """Textkonvention Regel 1: Kleinschreibung ist erlaubt und nie ein Fehler."""
    screen = _zur_uebung(fenster)
    _tippen(screen, screen.aufgabe.loesung.lower())
    screen.pruefen()
    assert screen.ist_beendet


def test_eine_falsche_antwort_nennt_die_stelle_und_kostet_einen_versuch(fenster):
    screen = _zur_uebung(fenster)
    falsch = _mit_fehler(screen.aufgabe.loesung)
    _tippen(screen, falsch)
    screen.pruefen()
    gezeigt = _eine_zeile(screen.rueckmeldung())
    assert rueckmeldung(screen.aufgabe, falsch) in gezeigt
    assert uebung.VERSUCHE_UEBRIG.format(anzahl=2) in gezeigt
    assert not screen.ist_beendet
    assert fenster.durchlauf.spielstand.aktuelle_bearbeitung.versuche == 1
    assert screen.eingabe == falsch                    # bleibt stehen zum Ausbessern


def test_die_fehlerstelle_wird_im_aufgabentext_unterringelt(fenster):
    """Dieselbe Auskunft wie in der Meldung – nur gleich an der richtigen Stelle."""
    screen = _zur_uebung(fenster, 1)                   # Level 1: ein Wort, eine Zeile
    falsch, stelle = _letzter_falsch(screen.aufgabe.loesung)
    _tippen(screen, falsch)
    screen.pruefen()
    (markierung,) = screen.buch.find_withtag("fehlerstelle")
    links, _, rechts, _ = screen.buch.bbox(markierung)
    schrift = screen.buch.schriften.kapitel
    text = screen.aufgabe.anzeigetext
    x0 = screen.buch.flaeche("rechts")[0]
    assert abs(links - (x0 + schrift.measure(text[:stelle]))) <= 5
    assert abs(rechts - (x0 + schrift.measure(text[:stelle + 1]))) <= 5


def test_bei_mehrzeiligem_aufgabentext_sitzt_die_markierung_in_der_richtigen_zeile(fenster, monkeypatch):
    """Die Übungstexte passen heute in eine Zeile – der lange Funkspruch in 6.6 nicht mehr."""
    lang = " ".join(("HUND KATZE MAUS BURG FELS", "NEBEL WASSER STURM WOLKE", "BERG TAL FLUSS SEE"))
    aufgabe = Aufgabe("probe", 1, verfahren.CAESAR, VERSCHLUESSELN, 5, lang,
                      anwenden(verfahren.CAESAR, VERSCHLUESSELN, lang, 5))
    fenster.aktueller_screen._feld.insert(0, "1-12")
    fenster.aktueller_screen.starten()
    fenster.aktueller_screen.waehle(charaktere.JONAS_BERG)
    fenster.aktueller_screen.bestaetigen()
    for _ in story.INTRO.absaetze:
        fenster.aktueller_screen.weiter()
    generator = fenster.durchlauf.spielstand._generator
    monkeypatch.setattr(generator, "naechste_uebung", lambda level, zusatzaufgabe=False: aufgabe)
    fenster.aktueller_screen.weiter()                  # Handbuch → Übung
    screen = fenster.aktueller_screen

    assert len(screen._textzeilen) >= 2, "Der Text sollte umbrochen werden."
    # Ein Fehler genau beim ersten Buchstaben der zweiten Zeile
    stelle = len(screen._textzeilen[0]) + 1
    falsch = list(aufgabe.loesung)
    falsch[stelle] = "A" if falsch[stelle] != "A" else "B"
    _tippen(screen, "".join(falsch))
    screen.pruefen()

    (markierung,) = screen.buch.find_withtag("fehlerstelle")
    links, oben, _, unten = screen.buch.bbox(markierung)
    x0, y0 = screen.buch.flaeche("rechts")[:2]
    schrift = screen.buch.schriften.kapitel
    assert abs(links - x0) <= 5                        # Zeilenanfang, nicht mitten im Text
    zweite_zeile = y0 + screen._text_oben + schrift.metrics("linespace")
    assert zweite_zeile <= oben and unten <= zweite_zeile + schrift.metrics("linespace") + 6


def test_ohne_abweichung_wird_nichts_markiert(fenster):
    """Eine zu kurze Antwort hat keine Stelle, an der es kippt – nur eine Länge."""
    screen = _zur_uebung(fenster)
    _tippen(screen, screen.aufgabe.loesung[:2])
    screen.pruefen()
    assert not screen.buch.find_withtag("fehlerstelle")
    assert "zu kurz" in _eine_zeile(screen.rueckmeldung())


def test_eine_leere_eingabe_kostet_keinen_versuch(fenster):
    screen = _zur_uebung(fenster)
    screen.pruefen()
    assert "noch nichts eingegeben" in _eine_zeile(screen.rueckmeldung())
    assert fenster.durchlauf.spielstand.aktuelle_bearbeitung.versuche == 0
    assert not screen.ist_beendet


def test_wer_naeher_drankommt_verliert_keinen_versuch(fenster):
    screen = _zur_uebung(fenster)
    loesung = screen.aufgabe.loesung
    for eingabe in (_mit_fehler(loesung, 3), _mit_fehler(loesung, 2)):
        _tippen(screen, eingabe)
        screen.pruefen()
    assert HINWEIS_FORTSCHRITT in _eine_zeile(screen.rueckmeldung())
    assert fenster.durchlauf.spielstand.aktuelle_bearbeitung.verbleibende_versuche == 3


def test_vor_dem_letzten_versuch_steht_es_deutlich_da(fenster):
    screen = _zur_uebung(fenster)
    falsch = _mit_fehler(screen.aufgabe.loesung)
    for _ in range(2):
        _tippen(screen, falsch)
        screen.pruefen()
    assert uebung.LETZTER_VERSUCH in _eine_zeile(screen.rueckmeldung())


def test_nach_drei_versuchen_ohne_fortschritt_steht_die_loesung_da(fenster):
    """Projektregel 2 – ohne sie bliebe das Spiel an einer Aufgabe hängen."""
    screen = _zur_uebung(fenster)
    falsch = _mit_fehler(screen.aufgabe.loesung)
    for _ in range(3):
        _tippen(screen, falsch)
        screen.pruefen()
    gezeigt = _eine_zeile(screen.rueckmeldung())
    assert uebung.LOESUNGSZEILE.format(loesung=screen.aufgabe.loesung) in gezeigt
    assert screen.ist_beendet and screen.knopftext == uebung.KNOPF_WEITER
    assert not screen.buch.find_withtag("stempel")     # aufgelöst ist nicht gelöst


def test_am_ende_steht_die_antwort_als_handschrift_im_buch(fenster):
    """Das Eingabefeld weicht dem, was darin stand – sonst läge es über dem Stempel."""
    screen = _zur_uebung(fenster)
    geschrieben = screen.aufgabe.loesung.lower()
    _tippen(screen, geschrieben)
    screen.pruefen()
    (antwort,) = screen.buch.find_withtag("antwort")
    assert screen.buch.itemcget(antwort, "text") == geschrieben
    assert screen.buch.itemcget(antwort, "font") == str(screen.buch.schriften.notiz)
    assert not screen.buch.find_withtag("eingabe")
    assert screen.eingabe == geschrieben


# ── Weiter und Nachschlagen ────────────────────────────────────────────────

def test_weiter_schliesst_die_aufgabe_ab_und_stellt_die_naechste(fenster):
    screen = _zur_uebung(fenster)
    erste = screen.aufgabe
    _tippen(screen, erste.loesung)
    screen.pruefen()
    screen.pruefen()                                   # der Knopf heisst jetzt "Weiter"
    naechste = fenster.aktueller_screen
    assert isinstance(naechste, uebung.Uebung) and naechste is not screen
    assert naechste.aufgabe is not erste
    (erledigt,) = fenster.durchlauf.spielstand.erledigte_aufgaben
    assert erledigt.aufgabe is erste and erledigt.geloest


def test_mitten_in_der_uebung_laesst_sich_nachschlagen_und_zurueckkehren(fenster, uhr):
    """Dieselbe Aufgabe, dasselbe Geschriebene, dieselben Versuche – und die Uhr lief weiter."""
    screen = _zur_uebung(fenster)
    aufgabe = screen.aufgabe
    _tippen(screen, _mit_fehler(aufgabe.loesung))
    screen.pruefen()
    _tippen(screen, "MON")
    screen._nachschlagen()

    nachgeschlagen = fenster.aktueller_screen
    assert isinstance(nachgeschlagen, handbuch.Handbuch)
    assert nachgeschlagen.knopftext == handbuch.KNOPF_ZURUECK
    assert fenster.durchlauf.spielstand.aktuelle_aufgabe is aufgabe
    uhr.jetzt += 20
    nachgeschlagen.weiter()

    zurueck = fenster.aktueller_screen
    assert isinstance(zurueck, uebung.Uebung)
    assert zurueck.aufgabe is aufgabe
    assert zurueck.eingabe == "MON"
    assert uebung.VERSUCHE_UEBRIG.format(anzahl=2) in _eine_zeile(zurueck.rueckmeldung())
    assert fenster.durchlauf.spielstand.aktuelle_bearbeitung.versuche == 1

    _tippen(zurueck, aufgabe.loesung)
    zurueck.pruefen()
    zurueck.weiter()
    (erledigt,) = fenster.durchlauf.spielstand.erledigte_aufgaben
    assert round(erledigt.benoetigte_sekunden) == 20    # Nachschlagen gehört zum Lösen


def test_beim_fortsetzen_steht_auch_eine_aufgeloeste_aufgabe_wieder_da(fenster):
    screen = _zur_uebung(fenster)
    falsch = _mit_fehler(screen.aufgabe.loesung)
    for _ in range(3):
        _tippen(screen, falsch)
        screen.pruefen()
    screen._nachschlagen()
    fenster.aktueller_screen.weiter()
    zurueck = fenster.aktueller_screen
    assert zurueck.ist_beendet and zurueck.knopftext == uebung.KNOPF_WEITER
    assert uebung.LOESUNGSZEILE.format(loesung=zurueck.aufgabe.loesung) in _eine_zeile(zurueck.rueckmeldung())


def test_laeuft_die_zeit_ab_wird_die_uebung_abgebrochen(fenster, uhr):
    """Projektregel 1: Das Level wechselt, egal was offen ist."""
    screen = _zur_uebung(fenster)
    uhr.jetzt += DAUER_JE_LEVEL_SEKUNDEN[1]
    fenster._takt()
    assert isinstance(_nachlese_durchklicken(fenster), handbuch.Handbuch)
    (erledigt,) = fenster.durchlauf.spielstand.erledigte_aufgaben
    assert erledigt.aufgabe is screen.aufgabe and erledigt.abgebrochen


def test_nach_dem_zeitablauf_wird_keine_uebung_mehr_gestellt(fenster, uhr):
    """Der Screen fragt beim Anzeigen – ist die Zeit um, hat der Levelwechsel schon umgeschaltet."""
    screen = _zur_uebung(fenster)
    _tippen(screen, screen.aufgabe.loesung)
    screen.pruefen()
    uhr.jetzt += DAUER_JE_LEVEL_SEKUNDEN[1]
    screen.weiter()                                    # stellt die nächste Übung – zu spät
    assert isinstance(_nachlese_durchklicken(fenster), handbuch.Handbuch)
    assert fenster.aktueller_screen.seite is buch.SEITE_SUBSTITUTION


# ── Platz auf dem Bildschirm ───────────────────────────────────────────────

@pytest.mark.parametrize("massstab", [1, 1.5])
@pytest.mark.parametrize("level", LEVEL)
def test_nichts_ragt_ueber_die_buchseiten_hinaus(fenster, level):
    """Auch nicht die längste Rückmeldung: dreimal alles falsch, dann die Lösung."""
    screen = _zur_uebung(fenster, level)
    falsch = _mit_fehler(screen.aufgabe.loesung, 99)
    for _ in range(3):
        _tippen(screen, falsch)
        screen.pruefen()
    luft = 2
    for seite in ("links", "rechts"):
        x0, y0, x1, y1 = screen.buch.flaeche(seite)
        for element in screen.buch.find_withtag(seite):
            a, b, c, d = screen.buch.bbox(element)
            assert x0 - luft <= a and c <= x1 + luft and y0 - luft <= b and d <= y1 + luft, (
                f"{screen.buch.gettags(element)} liegt bei {(a, b, c, d)}, "
                f"die Textfläche ist {(x0, y0, x1, y1)}")


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_der_screen_passt_ins_fenster(fenster, wurzel, platz):
    _zur_uebung(fenster)
    wurzel.update_idletasks()
    assert wurzel.winfo_reqwidth() <= platz[0]
    assert wurzel.winfo_reqheight() <= platz[1]


def test_die_kopfzeile_nennt_das_level(fenster):
    assert _zur_uebung(fenster).titel == "Übung – Level 1"
