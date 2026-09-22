"""Tests für den Satz des Handbuchs (Arbeitsplan 6.4): ui/buchsatz.py.

Geprüft werden die Regeln, nach denen der Text auf die Buchseiten kommt –
Überschriften nie allein unten, Absätze nur mit je zwei Zeilen geteilt,
Tabellen in Teilen, die auf die Seite passen, das Quadrat auf einer Seite
für sich, Beispiele links mit ihrem Werkzeug rechts daneben.

Gemessen wird hier mit einer ausgedachten Schrift: Jedes Zeichen ist 10
Pixel breit, jede Zeile 20 hoch. So lässt sich genau ausrechnen, was wohin
gehört – und die Tests brauchen keinen Bildschirm. Ob das echte Buch mit
den echten Schriften auf seine Seiten passt, prüft
``tests/test_handbuch_screen.py``.
"""

import pytest

from content import handbuch as buch
from ui import buchsatz
from ui.buchsatz import Karte, Quadrat, Raster, Schrittmarke, Stempel, Verzierung, Zeile

ZEICHEN = 10
ZEILE = 20


class Schrift:
    """Eine ausgedachte Schrift: 10 Pixel je Zeichen, 20 je Zeile."""

    def measure(self, text):
        """Wie breit dieser Text wäre: zehn Pixel je Zeichen."""
        return ZEICHEN * len(text)

    def metrics(self, was):
        """Zeilenhöhe und Oberlänge dieser ausgedachten Schrift."""
        return {"linespace": ZEILE, "ascent": 15}[was]


SCHRIFTEN = buchsatz.Schriften(*(Schrift() for _ in buchsatz.Schriften._fields))


def px(wert):
    """Im Test wird nicht skaliert – ein Pixel bleibt ein Pixel."""
    return wert


def _seite(*abschnitte, titel="K"):
    """Eine Handbuchseite aus den übergebenen Abschnitten, sonst mit festen Angaben."""
    return buch.Handbuchseite(level=1, titel=titel, verfahren="caesar", abschnitte=abschnitte)


def _absatz(zeilen):
    """Ein Absatz, der bei 200 Pixeln Breite genau so viele Zeilen hat: je vier Wörter "wort"."""
    return buch.Absatz(" ".join(["wort"] * (4 * zeilen)))


def _setzen(seite, breite=200, hoehe=200, stempel=None):
    """Setzt eine Seite mit der ausgedachten Schrift auf ein Blatt von 200 × 200 Pixeln."""
    return buchsatz.setzen(seite, SCHRIFTEN, breite, hoehe, px, stempel=stempel)


def _zeilen(buchseite, *arten):
    """Alle Textzeilen einer gesetzten Seite – auf Wunsch nur die von bestimmter Art."""
    return [s for s in buchseite.stuecke if isinstance(s, Zeile) and (not arten or s.art in arten)]


def _inhalt(buchseite):
    """Was auf einer Inhaltsseite steht, ohne die Seitenzahl."""
    return [s for s in buchseite.stuecke if not (isinstance(s, Zeile) and s.art == "seitenzahl")]


# ── Umbrechen ──────────────────────────────────────────────────────────────

def test_umbrechen_fuellt_die_zeilen_so_weit_es_geht():
    assert buchsatz.umbrechen("aaa bbb ccc ddd", Schrift(), 70) == ["aaa bbb", "ccc ddd"]


def test_ein_zu_langes_wort_bekommt_eine_zeile_fuer_sich():
    assert buchsatz.umbrechen("a Verschlüsselungshandbuch b", Schrift(), 100) == [
        "a", "Verschlüsselungshandbuch", "b"]


def test_umbrechen_ohne_text_gibt_keine_zeilen():
    assert buchsatz.umbrechen("   ", Schrift(), 100) == []


# ── Verteilen auf Seiten ───────────────────────────────────────────────────

def _kiste(hoehe, trennbar=True, vorher=0, neue_seite=False, name=""):
    """Eine Kiste mit dieser Höhe; ``name`` steckt als einziges Stück darin, damit man sie wiedererkennt."""
    return buchsatz._Kiste(hoehe, (name,), vorher, trennbar, neue_seite)


def _namen(seiten):
    """Die Namen der Kisten, Seite für Seite – so lässt sich die Verteilung ablesen."""
    return [[kiste.stuecke[0] for kiste, _ in seite] for seite in seiten]


def test_kisten_fuellen_eine_seite_nach_der_anderen():
    kisten = [_kiste(80, name=n) for n in "abcde"]
    assert _namen(buchsatz.seiten_verteilen(kisten, 200)) == [["a", "b"], ["c", "d"], ["e"]]


def test_der_abstand_davor_faellt_oben_auf_einer_seite_weg():
    kisten = [_kiste(100, name="a"), _kiste(100, vorher=30, name="b")]
    seiten = buchsatz.seiten_verteilen(kisten, 200)
    assert _namen(seiten) == [["a"], ["b"]]
    assert seiten[1][0][1] == 0


def test_was_nicht_getrennt_werden_darf_wandert_zusammen_auf_die_naechste_seite():
    kisten = [_kiste(120, name="a"), _kiste(40, name="b"), _kiste(60, trennbar=False, name="c")]
    assert _namen(buchsatz.seiten_verteilen(kisten, 200)) == [["a"], ["b", "c"]]


def test_gibt_es_keine_erlaubte_trennstelle_wird_eben_vor_der_letzten_kiste_getrennt():
    """Lieber eine Regel gebrochen als eine Seite, die überläuft – oder eine, die leer bleibt."""
    kisten = [_kiste(120, name="a"), _kiste(60, trennbar=False, name="b"), _kiste(60, trennbar=False, name="c")]
    assert _namen(buchsatz.seiten_verteilen(kisten, 200)) == [["a", "b"], ["c"]]


def test_neue_seite_heisst_neue_seite():
    kisten = [_kiste(20, name="a"), _kiste(20, neue_seite=True, name="b"), _kiste(20, name="c")]
    assert _namen(buchsatz.seiten_verteilen(kisten, 200)) == [["a"], ["b", "c"]]


def test_eine_kiste_groesser_als_die_seite_steht_allein():
    kisten = [_kiste(20, name="a"), _kiste(300, name="b"), _kiste(20, name="c")]
    assert _namen(buchsatz.seiten_verteilen(kisten, 200)) == [["a"], ["b"], ["c"]]


# ── Buchregeln ─────────────────────────────────────────────────────────────

def test_eine_ueberschrift_steht_nie_allein_unten_auf_der_seite():
    # Titel 20, Überschrift 14 + 20, Absatz 6 + 100 = 160; die zweite
    # Überschrift passte noch (174 + 20), ihr Absatz aber nicht mehr.
    seite = _seite(buch.Abschnitt("Eins", (_absatz(5),)), buch.Abschnitt("Zwei", (_absatz(3),)))
    satz = _setzen(seite)
    erste, zweite = satz.seiten[1], satz.seiten[2]
    assert [z.text for z in _zeilen(erste, "abschnitt")] == ["Eins"]
    assert _zeilen(zweite)[0].text == "Zwei"


@pytest.mark.parametrize("platz_in_zeilen, oben", [(1, 0), (2, 2), (3, 2)])
def test_ein_absatz_laesst_unten_und_oben_je_zwei_zeilen(platz_in_zeilen, oben):
    """Keine einzelne Zeile unten (Schusterjunge) und keine allein oben (Hurenkind)."""
    # Titel 20, Überschrift 14 + 20, dann ein Absatz, der den Platz bis auf
    # ``platz_in_zeilen`` Zeilen füllt, dann ein Absatz mit vier Zeilen.
    fuellung = (200 - 54 - 6 - 6 - platz_in_zeilen * ZEILE) // ZEILE
    seite = _seite(buch.Abschnitt("Eins", (_absatz(fuellung), _absatz(4))))
    satz = _setzen(seite)
    auf_der_ersten = len(_zeilen(satz.seiten[1], "absatz")) - fuellung
    assert auf_der_ersten == oben
    assert len(_zeilen(satz.seiten[2], "absatz")) == 4 - oben


def test_eine_kurze_aufzaehlung_wird_nicht_geteilt():
    fuellung = (200 - 54 - 6 - 6 - 2 * ZEILE - 3) // ZEILE        # Platz für zwei Punkte, nicht drei
    punkte = buch.Aufzaehlung(punkte=("eins", "zwei", "drei"))
    satz = _setzen(_seite(buch.Abschnitt("Eins", (_absatz(fuellung), punkte))))
    assert [z.text for z in _zeilen(satz.seiten[2], "punkt")] == ["eins", "zwei", "drei"]


def test_ein_absatz_mit_doppelpunkt_bleibt_bei_dem_was_er_ankuendigt():
    tabelle = buch.Tabelle(zeilen=(("x", "A", "B"), ("y", "C", "D")))
    fuellung = (200 - 54 - 6 - 6 - ZEILE - 8 - 2) // ZEILE        # Platz für die Ankündigung, nicht die Tabelle
    ankuendigung = buch.Absatz("so geht es:")
    satz = _setzen(_seite(buch.Abschnitt("Eins", (_absatz(fuellung), ankuendigung, tabelle))))
    zweite = satz.seiten[2]
    assert _zeilen(zweite)[0].text == "so geht es:"
    assert any(isinstance(s, Raster) for s in zweite.stuecke)


def test_eine_randnotiz_bleibt_bei_dem_worauf_sie_sich_bezieht():
    fuellung = (200 - 54 - 6) // ZEILE                            # die Seite ist voll
    notiz = buch.Randnotiz("Merk dir das!", bezug="wort")
    satz = _setzen(_seite(buch.Abschnitt("Eins", (_absatz(fuellung), notiz))))
    zweite = satz.seiten[2]
    notizen = _zeilen(zweite, "notiz")
    assert notizen and notizen[0].winkel == buchsatz.NOTIZWINKEL
    # Mit ihr sind die letzten Zeilen des Absatzes umgezogen – mindestens zwei.
    assert len(_zeilen(zweite, "absatz")) >= 2


# ── Tabellen, Quadrat, Merksatz ────────────────────────────────────────────

def _raster(satz):
    """Alle Tabellen eines gesetzten Kapitels, über alle Seiten hinweg."""
    return [s for seite in satz.seiten for s in seite.stuecke if isinstance(s, Raster)]


def test_eine_breite_tabelle_wird_in_teile_zerlegt_die_auf_die_seite_passen():
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    tabelle = buch.Tabelle(zeilen=(("oben", *alphabet), ("unten", *alphabet.lower())))
    satz = _setzen(_seite(buch.Abschnitt("Eins", (tabelle,))), breite=300, hoehe=400)
    teile = _raster(satz)
    assert len(teile) > 1
    for teil in teile:
        assert teil.x >= 0 and teil.x + teil.breite <= 300
        assert [zeile[0] for zeile in teil.zeilen] == ["oben", "unten"]    # jeder Teil ist beschriftet
    assert "".join(c for teil in teile for c in teil.zeilen[0][1:]) == alphabet
    assert "".join(c for teil in teile for c in teil.zeilen[1][1:]) == alphabet.lower()


def test_so_wenige_teile_wie_moeglich():
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    tabelle = buch.Tabelle(zeilen=(("o", *alphabet), ("u", *alphabet)))
    # Zellen je 16 Pixel (10 + 2 × 3 Rand): 13 passen neben die Beschriftung, 26 nicht.
    satz = _setzen(_seite(buch.Abschnitt("Eins", (tabelle,))), breite=260, hoehe=400)
    assert [len(teil.zeilen[0]) - 1 for teil in _raster(satz)] == [13, 13]


def test_eine_schmale_tabelle_bleibt_ganz():
    tabelle = buch.Tabelle(zeilen=(("Buchstabe", "H", "U", "N", "D"), ("verschoben", "K", "X", "Q", "G")))
    (teil,) = _raster(_setzen(_seite(buch.Abschnitt("Eins", (tabelle,))), breite=300))
    assert teil.zeilen == (("Buchstabe", "H", "U", "N", "D"), ("verschoben", "K", "X", "Q", "G"))


def test_eine_zu_lange_beschriftung_wird_in_ihrer_spalte_umbrochen():
    alphabet = "ABCDEFGHIJKLM"
    tabelle = buch.Tabelle(zeilen=(("ohne Verschiebung", *alphabet), ("mit", *alphabet)))
    (teil,) = _raster(_setzen(_seite(buch.Abschnitt("Eins", (tabelle,))), breite=340, hoehe=400))
    assert teil.zeilen[0][0] == "ohne\nVerschiebung"
    assert teil.zeilenhoehen[0] > teil.zeilenhoehen[1]           # die Zeile wächst mit
    assert teil.oben(1) == teil.zeilenhoehen[0]
    assert teil.hoehe == sum(teil.zeilenhoehen)


def test_das_quadrat_bekommt_eine_seite_fuer_sich():
    seite = _seite(buch.Abschnitt("Eins", (_absatz(2), buch.VigenereQuadrat("Das Quadrat"), _absatz(2))))
    satz = _setzen(seite, breite=300, hoehe=400)
    (quadratseite,) = [s for s in satz.seiten if any(isinstance(t, Quadrat) for t in s.stuecke)]
    assert [z.text for z in _zeilen(quadratseite) if z.art != "seitenzahl"] == ["Das Quadrat"]
    nummer = satz.seiten.index(quadratseite)
    assert _zeilen(satz.seiten[nummer + 1], "absatz")                  # danach geht es auf einer neuen weiter
    (quadrat,) = [t for t in quadratseite.stuecke if isinstance(t, Quadrat)]
    assert quadrat.kante <= 300 and quadrat.y + quadrat.kante <= 400
    assert quadrat.feld == min(300, 400 - ZEILE - 6) // 27         # so gross, wie die Seite es erlaubt


def test_vor_dem_quadrat_beginnt_eine_neue_seite():
    """Auch wenn davor noch Platz wäre: Das Quadrat steht nie unter einem Absatz."""
    # Breite 200, Höhe 400: Das Quadrat ist 7 Pixel je Feld gross und liesse
    # oben Platz für den Absatz – trotzdem gehört er auf die Seite davor.
    seite = _seite(buch.Abschnitt("Eins", (_absatz(1), buch.VigenereQuadrat("Das Quadrat"))))
    satz = _setzen(seite, breite=200, hoehe=400)
    (quadratseite,) = [s for s in satz.seiten if any(isinstance(t, Quadrat) for t in s.stuecke)]
    (quadrat,) = [t for t in quadratseite.stuecke if isinstance(t, Quadrat)]
    assert quadrat.y + quadrat.kante < 400 - ZEILE              # es wäre Platz gewesen
    assert not _zeilen(quadratseite, "absatz")
    assert _zeilen(satz.seiten[satz.seiten.index(quadratseite) - 1], "absatz")


def test_der_merksatz_steht_auf_einer_karte():
    merksatz = buch.Abschnitt("Merksatz", (buch.Absatz("vorwärts"), buch.Absatz("rückwärts")), hervorgehoben=True)
    satz = _setzen(_seite(buch.Abschnitt("Eins", (_absatz(1),)), merksatz))
    (seite,) = [s for s in satz.seiten if any(isinstance(t, Karte) for t in s.stuecke)]
    (karte,) = [t for t in seite.stuecke if isinstance(t, Karte)]
    texte = _zeilen(seite, "merksatz_titel", "merksatz")
    assert [z.text for z in texte] == ["Merksatz", "vorwärts", "rückwärts"]
    for zeile in texte:
        assert karte.x < zeile.x and karte.y < zeile.y and zeile.y + ZEILE < karte.y + karte.hoehe


# ── Beispiele mit dem Werkzeug gegenüber ───────────────────────────────────

WERKZEUG = buch.Tabelle(titel="Werkzeug", zeilen=(("o", "A", "B"), ("u", "C", "D")))
SCHRITTE = (buch.Schritt(spalte="A", kreuzung="C"), buch.Schritt(spalte="B", kreuzung="D"))


def _werkzeug(seite):
    """Die Tabellen auf einer Seite – das Werkzeug steht auf der rechten."""
    return [s for s in seite.stuecke if isinstance(s, Raster)]


def _ist_werkzeugseite(seite, werkzeug=WERKZEUG):
    """Auf der Seite steht das Werkzeug – und sonst nichts ausser Titel und Seitenzahl."""
    return (seite.werkzeug == werkzeug
            and [r.zeilen for r in _werkzeug(seite)] == [werkzeug.zeilen]
            and {z.art for z in _zeilen(seite)} <= {"tabellentitel", "seitenzahl"})


def _abschnitte_auf(seite):
    """Die Überschriften, die auf dieser Seite stehen."""
    return [z.text for z in _zeilen(seite, "abschnitt")]


def test_neben_jeder_seite_eines_abschnitts_mit_werkzeug_liegt_das_werkzeug():
    seite = _seite(buch.Abschnitt("Eins", (_absatz(2),)),
                   buch.Abschnitt("Zwei", (_absatz(15),), gegenueber=WERKZEUG))
    satz = _setzen(seite)
    # Titelseite | Eins – Zwei | Werkzeug – Zwei (Rest) | Werkzeug
    assert len(satz.seiten) == 6
    assert _abschnitte_auf(satz.seiten[1]) == ["Eins"] and satz.seiten[1].werkzeug is None
    assert _abschnitte_auf(satz.seiten[2]) == ["Zwei"] and satz.seiten[2].werkzeug is None
    assert _zeilen(satz.seiten[4], "absatz")                              # der Rest von "Zwei"
    for nummer in (3, 5):
        assert _ist_werkzeugseite(satz.seiten[nummer])
    assert [s.nummer for s in satz.seiten[1:]] == [1, 2, 3, 4, 5]
    assert satz.inhalt == (("Eins", 1), ("Zwei", 2))


def test_wuerde_das_werkzeug_links_liegen_bleibt_eine_seite_leer():
    seite = _seite(buch.Abschnitt("Eins", (_absatz(12),)),
                   buch.Abschnitt("Zwei", (_absatz(1),), gegenueber=WERKZEUG))
    satz = _setzen(seite)
    # Titelseite | Eins – Eins (Rest) | leer – Zwei | Werkzeug
    assert _zeilen(satz.seiten[2], "absatz")
    leer = satz.seiten[3]
    assert leer.nummer == 3 and not _zeilen(leer)                       # auch ohne Seitenzahl
    assert [type(s) for s in leer.stuecke] == [Verzierung]
    assert _abschnitte_auf(satz.seiten[4]) == ["Zwei"]
    assert _ist_werkzeugseite(satz.seiten[5])
    assert dict(satz.inhalt)["Zwei"] == 4


def test_beginnt_das_kapitel_mit_werkzeug_bleibt_die_seite_neben_der_titelseite_leer():
    satz = _setzen(_seite(buch.Abschnitt("Eins", (_absatz(1),), gegenueber=WERKZEUG), titel="Kapitel"))
    assert [type(s) for s in satz.seiten[1].stuecke] == [Verzierung]
    assert [z.text for z in _zeilen(satz.seiten[2], "kapitel")] == ["Kapitel"]
    assert _ist_werkzeugseite(satz.seiten[3])


def test_abschnitte_mit_demselben_werkzeug_laufen_ineinander():
    seite = _seite(buch.Abschnitt("Eins", (_absatz(1),), gegenueber=WERKZEUG),
                   buch.Abschnitt("Zwei", (_absatz(1),), gegenueber=WERKZEUG))
    satz = _setzen(seite)
    assert _abschnitte_auf(satz.seiten[2]) == ["Eins", "Zwei"]
    assert _ist_werkzeugseite(satz.seiten[3])
    assert len(satz.seiten) == 4


def test_ein_anderes_werkzeug_beginnt_eine_neue_doppelseite():
    anderes = buch.Tabelle(zeilen=(("x", "Q"), ("y", "R")))
    seite = _seite(buch.Abschnitt("Eins", (_absatz(1),), gegenueber=WERKZEUG),
                   buch.Abschnitt("Zwei", (_absatz(1),), gegenueber=anderes))
    satz = _setzen(seite)
    assert _abschnitte_auf(satz.seiten[2]) == ["Eins"] and _ist_werkzeugseite(satz.seiten[3])
    assert _abschnitte_auf(satz.seiten[4]) == ["Zwei"] and _ist_werkzeugseite(satz.seiten[5], anderes)


def test_nach_dem_werkzeug_geht_es_auf_einer_neuen_seite_weiter():
    """Auch wenn neben dem Beispiel noch Platz wäre – daneben läge sonst ein Werkzeug, das nicht dazugehört."""
    seite = _seite(buch.Abschnitt("Eins", (_absatz(1),), gegenueber=WERKZEUG),
                   buch.Abschnitt("Zwei", (_absatz(1),)),
                   buch.Abschnitt("Drei", (_absatz(1),)))
    satz = _setzen(seite)
    assert _abschnitte_auf(satz.seiten[2]) == ["Eins"] and _ist_werkzeugseite(satz.seiten[3])
    assert _abschnitte_auf(satz.seiten[4]) == ["Zwei", "Drei"] and satz.seiten[4].werkzeug is None
    assert len(satz.seiten) == 5


def test_das_quadrat_als_werkzeug_steht_auf_jeder_seite_daneben():
    seite = _seite(buch.Abschnitt("Eins", (_absatz(24),), gegenueber=buch.VigenereQuadrat("Q")))
    satz = _setzen(seite, breite=200, hoehe=400)
    quadratseiten = [s for s in satz.seiten if any(isinstance(t, Quadrat) for t in s.stuecke)]
    assert [satz.seiten.index(s) for s in quadratseiten] == [3, 5]
    assert all(s.werkzeug == buch.VigenereQuadrat("Q") for s in quadratseiten)


def _beispiel(*bloecke, schritte=SCHRITTE, ueberschrift="Beispiel"):
    """Ein Abschnitt mit Werkzeug und Schritten – die Form, um die es beim Umbruch von Beispielen geht."""
    return buch.Abschnitt(ueberschrift, bloecke, gegenueber=WERKZEUG, schritte=schritte)


def test_die_schritte_einer_aufzaehlung_tragen_ihre_marke():
    punkte = buch.Aufzaehlung(punkte=("erster " * 4, "zweiter"), nummeriert=True)     # zwei Zeilen, eine
    satz = _setzen(_seite(buch.Abschnitt("Vorher", (_absatz(1),)), _beispiel(buch.Absatz("so:"), punkte)))
    seite = satz.seiten[2]
    marken = [Schrittmarke(1, nr, schritt) for nr, schritt in enumerate(SCHRITTE)]
    assert seite.schritte == tuple(marken)
    zeilen = [z for z in _zeilen(seite) if z.schritt is not None]
    assert [(z.art, z.schritt.nummer) for z in zeilen] == [("zeichen", 0), ("punkt", 0), ("punkt", 0),
                                                         ("zeichen", 1), ("punkt", 1)]
    assert all(z.schritt == marken[z.schritt.nummer] for z in zeilen)
    assert not [z for z in _zeilen(seite, "absatz", "abschnitt") if z.schritt is not None]
    assert satz.seiten[3].schritte == ()


def test_in_einer_beispieltabelle_sind_die_spalten_die_schritte():
    """Ohne nummerierte Punkte tragen die Spalten der letzten Tabelle die Schritte – nicht Stichpunkte davor."""
    stichpunkte = buch.Aufzaehlung(punkte=("so", "geht"))
    beispiel = buch.Tabelle(zeilen=(("rein", "A", "B"), ("raus", "C", "D")))
    satz = _setzen(_seite(_beispiel(stichpunkte, buch.Tabelle(zeilen=(("x", "Q"), ("y", "R"))), beispiel)), hoehe=400)
    raster = [r for r in _werkzeug(satz.seiten[2])]
    assert [r.schritte for r in raster] == [(), (Schrittmarke(0, 0, SCHRITTE[0]), Schrittmarke(0, 1, SCHRITTE[1]))]
    assert satz.seiten[2].schritte == raster[1].schritte
    assert all(z.schritt is None for z in _zeilen(satz.seiten[2]))


def test_die_marken_einer_geteilten_beispieltabelle_gehoeren_zu_ihren_spalten():
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    schritte = tuple(buch.Schritt(spalte=b, kreuzung=b.lower()) for b in alphabet)
    beispiel = buch.Tabelle(zeilen=(("o", *alphabet), ("u", *alphabet.lower())))
    satz = _setzen(_seite(_beispiel(beispiel, schritte=schritte)), breite=260, hoehe=400)
    teile = _werkzeug(satz.seiten[2])
    assert len(teile) == 2
    for teil in teile:
        assert [marke.schritt.spalte for marke in teil.schritte] == list(teil.zeilen[0][1:])


def test_passen_schritte_und_beispiel_nicht_zusammen_faellt_das_auf():
    punkte = buch.Aufzaehlung(punkte=("eins", "zwei", "drei"), nummeriert=True)
    with pytest.raises(ValueError):
        _setzen(_seite(_beispiel(punkte)))


def test_ohne_schritte_traegt_nichts_eine_marke():
    punkte = buch.Aufzaehlung(punkte=("eins", "zwei"), nummeriert=True)
    satz = _setzen(_seite(buch.Abschnitt("Eins", (punkte,), gegenueber=WERKZEUG)))
    assert satz.seiten[2].schritte == ()
    assert all(z.schritt is None for z in _zeilen(satz.seiten[2]))


def test_ein_beispiel_das_auf_eine_seite_passt_beginnt_lieber_auf_einer_neuen():
    """Die Regeln für Absätze erlaubten eine Trennung – aber wer rechnet, soll nicht umblättern."""
    # Titel 20; "Erklärung" 14 + 20, Absatz 6 + 60 = 120. Das Beispiel ist
    # 20 + 6 + 80 + 6 + 20 + 3 + 20 = 155 hoch: Es passt nicht mehr darunter,
    # aber auf eine Seite. Nach den Regeln für Absätze dürfte die Seite nach
    # der Überschrift und zwei Zeilen seines Absatzes enden.
    punkte = buch.Aufzaehlung(punkte=("eins", "zwei"), nummeriert=True)
    seite = _seite(buch.Abschnitt("Erklärung", (_absatz(3),), gegenueber=WERKZEUG),
                   _beispiel(_absatz(4), punkte))
    satz = _setzen(seite)
    assert _abschnitte_auf(satz.seiten[2]) == ["Erklärung"]
    assert len(_zeilen(satz.seiten[2], "absatz")) == 3
    assert _abschnitte_auf(satz.seiten[4]) == ["Beispiel"]
    assert len(_zeilen(satz.seiten[4], "absatz")) == 4 and len(_zeilen(satz.seiten[4], "punkt")) == 2


def test_bei_einem_langen_beispiel_bleiben_die_schritte_beisammen_und_das_ergebnis_bei_ihnen():
    # Das Beispiel ist höher als eine Seite; geteilt wird vor den Schritten, nicht zwischen ihnen.
    punkte = buch.Aufzaehlung(punkte=("wort " * 8, "zwei", "wort " * 8), nummeriert=True)   # 3 + 1 + 3 Zeilen
    ergebnis = buch.Absatz("Ergebnis", betont=True)
    seite = _seite(_beispiel(_absatz(5), punkte, ergebnis, _absatz(1),
                             schritte=SCHRITTE + (buch.Schritt(spalte="A", kreuzung="C"),)))
    satz = _setzen(seite)
    erste, zweite = satz.seiten[2], satz.seiten[4]
    assert not _zeilen(erste, "punkt")
    assert len(_zeilen(zweite, "punkt")) == 7 and _zeilen(zweite, "betont")
    assert _ist_werkzeugseite(satz.seiten[3]) and _ist_werkzeugseite(satz.seiten[5])
    assert erste.schritte == () and len(zweite.schritte) == 3


def test_ein_langer_schritt_wird_nicht_zwischen_seinen_zeilen_geteilt():
    """Ein Absatz dürfte nach zwei Zeilen umbrechen – ein Schritt nicht."""
    # Titel 20, Überschrift 14 + 20, Absatz 6 + 80 = 140. Vom ersten Schritt
    # (vier Zeilen) passten noch zwei darunter. Das Beispiel ist höher als eine Seite.
    punkte = buch.Aufzaehlung(punkte=(" ".join(["wort"] * 12), "zwei"), nummeriert=True)
    seite = _seite(_beispiel(_absatz(4), punkte, buch.Absatz("Ergebnis", betont=True), _absatz(4)))
    satz = _setzen(seite)
    assert not _zeilen(satz.seiten[2], "punkt")
    assert len(_zeilen(satz.seiten[4], "punkt")) == 5


def test_schritte_werden_auch_nach_dem_zweiten_nicht_geteilt():
    """Stichpunkte dürften nach zweien umbrechen – Schritte nicht."""
    # Wie oben, aber vier einzeilige Schritte: zwei passten noch darunter.
    punkte = buch.Aufzaehlung(punkte=("eins", "zwei", "drei", "vier"), nummeriert=True)
    schritte = SCHRITTE + SCHRITTE
    seite = _seite(_beispiel(_absatz(4), punkte, buch.Absatz("Ergebnis", betont=True), _absatz(4),
                             schritte=schritte))
    satz = _setzen(seite)
    assert not _zeilen(satz.seiten[2], "punkt")
    assert [z.text for z in _zeilen(satz.seiten[4], "punkt")] == ["eins", "zwei", "drei", "vier"]


def test_das_ergebnis_wandert_nicht_allein_auf_die_naechste_seite():
    # "Vorher" steht auf Seite 1, das Beispiel beginnt oben auf Seite 2:
    # Überschrift 20, Absatz 6 + 100, zwei Schritte 6 + 20 + 3 + 20 = 175 –
    # für das Ergebnis (6 + 20) ist kein Platz mehr.
    punkte = buch.Aufzaehlung(punkte=("eins", "zwei"), nummeriert=True)
    seite = _seite(buch.Abschnitt("Vorher", (_absatz(1),)),
                   _beispiel(_absatz(5), punkte, buch.Absatz("Ergebnis", betont=True), _absatz(4)))
    satz = _setzen(seite)
    assert not _zeilen(satz.seiten[2], "punkt", "betont")
    assert [z.text for z in _zeilen(satz.seiten[4], "punkt", "betont")] == ["eins", "zwei", "Ergebnis"]


def test_endet_ein_beispiel_mit_seinen_schritten_haengt_der_naechste_abschnitt_nicht_daran():
    # Das Beispiel (20 + 86 + 49 = 155) passt auf Seite 2, die Überschrift
    # des nächsten Abschnitts noch darunter, ihre erste Zeile nicht mehr –
    # also beginnt er auf der nächsten Seite, und das Beispiel bleibt, wo es ist.
    punkte = buch.Aufzaehlung(punkte=("eins", "zwei"), nummeriert=True)
    seite = _seite(buch.Abschnitt("Vorher", (_absatz(1),)),
                   _beispiel(_absatz(4), punkte),
                   buch.Abschnitt("Danach", (_absatz(2),), gegenueber=WERKZEUG))
    satz = _setzen(seite)
    assert _abschnitte_auf(satz.seiten[2]) == ["Beispiel"]
    assert [z.text for z in _zeilen(satz.seiten[2], "punkt")] == ["eins", "zwei"]
    assert _abschnitte_auf(satz.seiten[4]) == ["Danach"]


def test_die_leere_seite_hat_nur_eine_verzierung():
    (verzierung,) = buchsatz.leerseite(300, 400, px, nummer=7).stuecke
    assert buchsatz.leerseite(300, 400, px, nummer=7).nummer == 7
    assert verzierung == Verzierung(90, 200, 120)


# ── Das ganze Kapitel ──────────────────────────────────────────────────────

def test_zuerst_kommt_die_titelseite_ohne_seitenzahl():
    satz = _setzen(_seite(buch.Abschnitt("Eins", (_absatz(2),))), breite=300, hoehe=300)
    titel = satz.seiten[0]
    assert titel.nummer is None
    assert not _zeilen(titel, "seitenzahl")
    assert [s.nummer for s in satz.seiten[1:]] == list(range(1, len(satz.seiten)))


def test_jede_inhaltsseite_hat_ihre_seitenzahl_unter_der_textflaeche():
    satz = _setzen(_seite(buch.Abschnitt("Eins", (_absatz(12),))))
    for seite in satz.seiten[1:]:
        (zahl,) = _zeilen(seite, "seitenzahl")
        assert zahl.text == f"– {seite.nummer} –" and zahl.y >= 200


def test_das_inhaltsverzeichnis_nennt_die_seite_jeder_ueberschrift():
    seite = _seite(buch.Abschnitt("Eins", (_absatz(6),)), buch.Abschnitt("Zwei", (_absatz(6),)),
                   buch.Abschnitt("Merksatz", (buch.Absatz("m"),), hervorgehoben=True))
    satz = _setzen(seite, breite=400, hoehe=300)
    for ueberschrift, nummer in satz.inhalt:
        auf_der_seite = [z.text for z in _zeilen(satz.seiten[nummer], "abschnitt", "merksatz_titel")]
        assert ueberschrift in auf_der_seite
    assert [u for u, _ in satz.inhalt] == ["Eins", "Zwei", "Merksatz"]
    verzeichnis = _zeilen(satz.seiten[0], "inhalt")
    assert [z.text for z in verzeichnis] == ["Eins", "Zwei", "Merksatz"]
    zahlen = _zeilen(satz.seiten[0], "inhalt_seite")
    assert [z.text for z in zahlen] == [str(n) for _, n in satz.inhalt]


def test_eine_zu_lange_ueberschrift_wird_im_verzeichnis_gekuerzt():
    lang = "Ein Trick, um dir die Zuordnung zu merken"
    satz = _setzen(_seite(buch.Abschnitt(lang, (_absatz(1),))), breite=300, hoehe=300)
    (eintrag,) = _zeilen(satz.seiten[0], "inhalt")
    assert eintrag.text.endswith(" …") and lang.startswith(eintrag.text[:-2])
    assert eintrag.x + ZEICHEN * len(eintrag.text) <= 300


def test_der_stempel_steht_unten_auf_der_titelseite():
    satz = _setzen(_seite(buch.Abschnitt("Eins", (_absatz(1),))), breite=300, hoehe=400, stempel=(120, 50))
    (stempel,) = [s for s in satz.seiten[0].stuecke if isinstance(s, Stempel)]
    assert stempel.y + stempel.hoehe == 400
    assert stempel.x == (300 - 120) // 2
    assert max(z.y + ZEILE for z in _zeilen(satz.seiten[0])) <= stempel.y   # kein Text darunter


@pytest.mark.parametrize("seite", buch.SEITEN, ids=lambda s: f"Level {s.level}")
def test_keine_zeile_des_echten_handbuchs_ist_zu_breit(seite):
    """Mit der ausgedachten Schrift: Jede Zeile passt – ausser einem Wort, das allein zu lang ist."""
    satz = _setzen(seite, breite=366, hoehe=385)
    for buchseite in satz.seiten:
        for zeile in _zeilen(buchseite):
            for text in zeile.text.split("\n"):
                if zeile.anker == "nw" and " " in text:
                    assert zeile.x + ZEICHEN * len(text) <= 366, text


def test_unbekannte_bloecke_fallen_auf():
    with pytest.raises(TypeError):
        _setzen(_seite(buch.Abschnitt("Eins", ("kein Block",))))
