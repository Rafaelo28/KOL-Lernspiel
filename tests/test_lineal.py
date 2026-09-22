"""Tests für das Lineal im Vigenère-Quadrat (Arbeitsplan 6.7): ui/lineal.py.

Geprüft wird, dass ein Klick an den Rand des Quadrats Zeile oder Spalte
markiert, ein Klick ins Quadrat beide, ein zweiter Klick auf denselben Kopf
das Lineal wieder abnimmt – und vor allem, dass das Lineal nur markiert: Es
schreibt keinen einzigen Buchstaben hin. Abgelesen wird weiter selbst.

Wie es in der Übung ankommt (nur in Level 3, gezählt fürs Log), prüft
``tests/test_uebung_screen.py``.

Braucht eine Bildschirmanzeige, sonst übersprungen.
"""

import pytest

tk = pytest.importorskip("tkinter")

from content import handbuch as buch  # noqa: E402
from crypto.normalize import ALPHABET  # noqa: E402
from crypto.vigenere_quadrat import erzeuge_quadrat  # noqa: E402
from ui import buchsatz, stil  # noqa: E402
from ui.buchleinwand import Buchleinwand  # noqa: E402
from ui.lineal import Lineal  # noqa: E402


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
def benutzt():
    """Eine leere Liste, in der jede Bewegung des Lineals landet."""
    return []


@pytest.fixture
def lineal(wurzel, massstab, benutzt):
    """Ein Buch mit dem Quadrat auf der linken Seite – wie neben einer Vigenère-Übung."""
    def px(wert):
        """Rechnet eine Pixelangabe auf den Maßstab um – wie ``Screen.px``, nur ohne Screen."""
        return stil.skaliert(wert, massstab)

    leinwand = Buchleinwand(wurzel, massstab, px)
    x0, y0, x1, y1 = leinwand.flaeche("links")
    seite = buchsatz.einzelseite([buch.WERKZEUG_NACH_LEVEL[3]], leinwand.schriften, x1 - x0, y1 - y0, px)
    leinwand.seite_zeichnen("links", seite.stuecke)
    (quadrat,) = [stueck for stueck in seite.stuecke if isinstance(stueck, buchsatz.Quadrat)]
    return Lineal(leinwand, "links", quadrat, bei_benutzung=lambda: benutzt.append(1))


def _mitte(lineal, zeile, spalte):
    """Die Mitte eines Feldes auf der Leinwand – Zeile und Spalte -1 sind die Köpfe."""
    x0, y0, _, _ = lineal.leinwand.flaeche(lineal.seite)
    feld = lineal.quadrat.feld
    return (x0 + lineal.quadrat.x + (spalte + 1.5) * feld, y0 + lineal.quadrat.y + (zeile + 1.5) * feld)


def _texte_in(leinwand, rechteck, waagrecht=False):
    """Die Buchstaben, deren Mitte im Rechteck liegt – von oben nach unten oder von links nach rechts."""
    x0, y0, x1, y1 = rechteck
    gefunden = []
    for element in leinwand.find_withtag("links"):
        if leinwand.type(element) != "text":
            continue
        a, b, c, d = leinwand.bbox(element)
        x, y = (a + c) / 2, (b + d) / 2
        if x0 <= x <= x1 and y0 <= y <= y1:
            gefunden.append(((x, y) if waagrecht else (y, x), leinwand.itemcget(element, "text")))
    return [text for _, text in sorted(gefunden)]


def _rechteck(lineal, tag):
    """Die Ecken des markierten Rechtecks auf der linken Seite: (x0, y0, x1, y1)."""
    (element,) = lineal.leinwand.find_withtag(f"{tag}&&links")
    return lineal.leinwand.coords(element)


# ── Wohin geklickt wurde ───────────────────────────────────────────────────

@pytest.mark.parametrize("massstab", [1, 1.5])
def test_das_lineal_weiss_wohin_geklickt_wurde(lineal):
    assert lineal.ziel(*_mitte(lineal, 17, -1)) == ("zeile", 17)
    assert lineal.ziel(*_mitte(lineal, -1, 7)) == ("spalte", 7)
    assert lineal.ziel(*_mitte(lineal, 17, 7)) == ("feld", 17, 7)
    assert lineal.ziel(*_mitte(lineal, 0, 0)) == ("feld", 0, 0)
    assert lineal.ziel(*_mitte(lineal, 25, 25)) == ("feld", 25, 25)
    assert lineal.ziel(*_mitte(lineal, -1, -1)) is None                  # die leere Ecke
    assert lineal.ziel(*_mitte(lineal, 26, 3)) is None                   # unter dem Quadrat
    assert lineal.ziel(*_mitte(lineal, 3, 26)) is None                   # rechts daneben
    assert lineal.ziel(*_mitte(lineal, -2, 3)) is None                   # darüber


# ── Was markiert wird ──────────────────────────────────────────────────────

@pytest.mark.parametrize("massstab", [1, 1.5])
def test_ein_klick_links_legt_das_lineal_an_die_ganze_zeile(lineal, benutzt):
    assert lineal.klicken(*_mitte(lineal, ALPHABET.index("R"), -1)) is True
    zeile = _rechteck(lineal, "linealzeile")
    assert _texte_in(lineal.leinwand, zeile, waagrecht=True) == ["R"] + list(erzeuge_quadrat()[ALPHABET.index("R")])
    assert not lineal.leinwand.find_withtag("linealspalte") and not lineal.leinwand.find_withtag("linealkreuzung")
    assert benutzt == [1]


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_ein_klick_oben_legt_das_lineal_an_die_ganze_spalte(lineal):
    lineal.klicken(*_mitte(lineal, -1, ALPHABET.index("H")))
    spalte = _rechteck(lineal, "linealspalte")
    quadrat = erzeuge_quadrat()
    assert _texte_in(lineal.leinwand, spalte) == ["H"] + [reihe[ALPHABET.index("H")] for reihe in quadrat]


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_wo_sich_zeile_und_spalte_kreuzen_liegt_der_marker_dunkler(lineal):
    """Das Feld selbst bleibt, wie es ist – den Buchstaben liest man ab."""
    lineal.klicken(*_mitte(lineal, ALPHABET.index("R"), -1))
    lineal.klicken(*_mitte(lineal, -1, ALPHABET.index("H")))
    kreuzung = _rechteck(lineal, "linealkreuzung")
    assert _texte_in(lineal.leinwand, kreuzung) == ["Y"]                  # HUND + ROT → Y…
    (element,) = lineal.leinwand.find_withtag("linealkreuzung")
    assert lineal.leinwand.itemcget(element, "fill") == stil.FARBE_KREUZUNG
    feld = lineal.quadrat.feld
    assert kreuzung[2] - kreuzung[0] == kreuzung[3] - kreuzung[1] == feld


@pytest.mark.parametrize("massstab", [1, 1.5])
def test_das_lineal_schreibt_keinen_buchstaben_hin(lineal):
    """Es markiert nur. Einen Buchstaben auszugeben wäre ein Rechner – das Ablesen ist, was geübt wird."""
    leinwand = lineal.leinwand
    vorher = [(e, leinwand.itemcget(e, "text")) for e in leinwand.find_all() if leinwand.type(e) == "text"]
    for zeile, spalte in ((17, -1), (-1, 7), (3, 9), (3, -1)):
        lineal.klicken(*_mitte(lineal, zeile, spalte))
    nachher = [(e, leinwand.itemcget(e, "text")) for e in leinwand.find_all() if leinwand.type(e) == "text"]
    assert nachher == vorher
    assert {leinwand.type(e) for e in leinwand.find_withtag("lineal")} == {"rectangle"}


def test_ein_klick_auf_ein_feld_legt_das_lineal_an_zeile_und_spalte(lineal):
    """Beim Entschlüsseln: den Geheimbuchstaben in der Zeile gefunden – das Lineal zeigt hinauf zum Spaltenkopf."""
    lineal.klicken(*_mitte(lineal, ALPHABET.index("R"), ALPHABET.index("H")))
    assert (lineal.zeile, lineal.spalte) == (ALPHABET.index("R"), ALPHABET.index("H"))
    assert _texte_in(lineal.leinwand, _rechteck(lineal, "linealspalte"))[0] == "H"
    lineal.klicken(*_mitte(lineal, 2, 3))
    assert (lineal.zeile, lineal.spalte) == (2, 3)
    assert len(lineal.leinwand.find_withtag("lineal")) == 3


def test_ein_zweiter_klick_auf_denselben_kopf_nimmt_das_lineal_ab(lineal, benutzt):
    lineal.klicken(*_mitte(lineal, 4, -1))
    lineal.klicken(*_mitte(lineal, -1, 9))
    lineal.klicken(*_mitte(lineal, 4, -1))
    assert lineal.zeile is None and lineal.spalte == 9
    assert not lineal.leinwand.find_withtag("linealzeile") and not lineal.leinwand.find_withtag("linealkreuzung")
    lineal.klicken(*_mitte(lineal, -1, 9))
    assert lineal.spalte is None and not lineal.leinwand.find_withtag("lineal")
    assert benutzt == [1, 1, 1, 1]


def test_ein_klick_neben_das_quadrat_tut_nichts(lineal, benutzt):
    lineal.klicken(*_mitte(lineal, 4, 4))
    assert lineal.klicken(*_mitte(lineal, -1, -1)) is False
    assert lineal.klicken(5, 5) is False
    assert (lineal.zeile, lineal.spalte) == (4, 4)
    assert benutzt == [1]


def test_der_marker_liegt_ueber_dem_grund_der_koepfe_und_unter_den_buchstaben(lineal):
    lineal.klicken(*_mitte(lineal, 4, 9))
    leinwand = lineal.leinwand
    stapel = leinwand.find_all()
    marker = [stapel.index(e) for e in leinwand.find_withtag("lineal")]
    buchstaben = [stapel.index(e) for e in leinwand.find_withtag("(kopfzeile||kopfspalte||feld)&&links")]
    kopfgrund = [stapel.index(e) for e in leinwand.find_withtag("links") if leinwand.type(e) == "rectangle"
                 and leinwand.itemcget(e, "fill") == stil.FARBE_PAPIER_DUNKEL]
    assert kopfgrund and max(kopfgrund) < min(marker) and max(marker) < min(buchstaben)
