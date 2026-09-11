"""Tests für ui/animation.py und die gerenderten Animationen in content/animationen.

Die Abspiel-Tests bauen sich eine kleine Animation selbst: jedes Einzelbild
in einer eigenen Farbe, von Tkinter als PNG geschrieben. So lässt sich
nachprüfen, dass das Blatt richtig zerschnitten wird und die Bilder in der
richtigen Reihenfolge kommen.

Die Tests zu den echten Animationen prüfen ohne Bildschirm, dass die Dateien
zueinander und zu ihrer SVG-Quelle passen – sonst zeigte das Spiel verrutschte
oder abgeschnittene Bilder.
"""

import importlib.util
import json
import struct
from pathlib import Path

import pytest

PROJEKT = Path(__file__).resolve().parent.parent
ANIMATIONEN = PROJEKT / "content" / "animationen"
_spec = importlib.util.spec_from_file_location("rendern", PROJEKT / "grafik" / "rendern.py")
rendern = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rendern)


def _png_groesse(datei):
    kopf = Path(datei).read_bytes()[:24]
    assert kopf[:8] == b"\x89PNG\r\n\x1a\n", f"{datei} ist kein PNG"
    return struct.unpack(">II", kopf[16:24])


# ───────────────────────────────────────────────────────────────────────────
# 1. Die echten Animationen passen zu ihren Quellen (ohne Bildschirm)
# ───────────────────────────────────────────────────────────────────────────

ECHTE = sorted(p for p in ANIMATIONEN.iterdir() if p.is_dir()) if ANIMATIONEN.exists() else []


def test_es_gibt_die_wrack_animation():
    assert (ANIMATIONEN / "wrack" / "animation.json").exists()


@pytest.mark.parametrize("ordner", ECHTE, ids=lambda p: p.name)
def test_die_dateien_einer_animation_passen_zusammen(ordner):
    beschreibung = json.loads((ordner / "animation.json").read_text(encoding="utf-8"))
    assert _png_groesse(ordner / beschreibung["hintergrund"]) == (beschreibung["breite"], beschreibung["hoehe"])
    assert beschreibung["bereiche"], "Eine Animation ohne bewegten Ausschnitt ist ein Standbild."
    for bereich in beschreibung["bereiche"]:
        zeilen = -(-beschreibung["bilder"] // bereich["spalten"])
        assert _png_groesse(ordner / bereich["datei"]) == (
            bereich["spalten"] * bereich["breite"], zeilen * bereich["hoehe"])
        assert 0 <= bereich["x"] and bereich["x"] + bereich["breite"] <= beschreibung["breite"]
        assert 0 <= bereich["y"] and bereich["y"] + bereich["hoehe"] <= beschreibung["hoehe"]


@pytest.mark.parametrize("ordner", ECHTE, ids=lambda p: p.name)
def test_eine_animation_passt_zu_ihrer_svg_quelle(ordner):
    """Wer die SVG ändert und das Rendern vergisst, merkt es hier."""
    beschreibung = json.loads((ordner / "animation.json").read_text(encoding="utf-8"))
    quelle = PROJEKT / beschreibung["quelle"]
    assert quelle.exists(), f"Die Quelle {beschreibung['quelle']} fehlt."
    e = rendern.einstellungen_lesen(quelle.read_text(encoding="utf-8"), ordner.name)
    assert (e.breite, e.hoehe, e.bilder, e.takt_ms) == (
        beschreibung["breite"], beschreibung["hoehe"], beschreibung["bilder"], beschreibung["takt_ms"])
    assert [tuple(b) for b in e.bereiche] == [
        (b["x"], b["y"], b["breite"], b["hoehe"]) for b in beschreibung["bereiche"]]


@pytest.mark.parametrize("ordner", ECHTE, ids=lambda p: p.name)
def test_eine_animation_bleibt_klein_genug_fuer_schulrechner(ordner):
    """Grober Deckel: im Arbeitsspeicher unter 40 MB, auf der Platte unter 8 MB."""
    beschreibung = json.loads((ordner / "animation.json").read_text(encoding="utf-8"))
    speicher = beschreibung["breite"] * beschreibung["hoehe"] * 4 + sum(
        b["breite"] * b["hoehe"] * 4 * beschreibung["bilder"] for b in beschreibung["bereiche"])
    assert speicher < 40 * 2**20
    assert sum(p.stat().st_size for p in ordner.iterdir()) < 8 * 2**20


# ───────────────────────────────────────────────────────────────────────────
# 2. Abspielen (braucht einen Bildschirm)
# ───────────────────────────────────────────────────────────────────────────

tk = pytest.importorskip("tkinter")
from ui.animation import Animation, Buehne  # noqa: E402

FARBEN = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#00ffff"]


@pytest.fixture
def wurzel():
    try:
        wurzel = tk.Tk()
    except tk.TclError as fehler:
        pytest.skip(f"Keine Bildschirmanzeige: {fehler}")
    wurzel.withdraw()
    yield wurzel
    wurzel.destroy()


def _probeanimation(wurzel, ordner, spalten=2, bilder=5, blatt_zu_klein=False):
    """Hintergrund 40×30 grau, ein Ausschnitt 10×8 an (12, 6), Bild i in FARBEN[i]."""
    ziel = ordner / "probe"
    ziel.mkdir(parents=True)
    hintergrund = tk.PhotoImage(master=wurzel, width=40, height=30)
    hintergrund.put("#777777", to=(0, 0, 40, 30))
    hintergrund.write(str(ziel / "hintergrund.png"), format="png")
    zeilen = -(-bilder // spalten) - (1 if blatt_zu_klein else 0)
    blatt = tk.PhotoImage(master=wurzel, width=10 * spalten, height=8 * zeilen)
    for nr in range(bilder):
        x, y = (nr % spalten) * 10, (nr // spalten) * 8
        if y < 8 * zeilen:
            blatt.put(FARBEN[nr], to=(x, y, x + 10, y + 8))
    blatt.write(str(ziel / "bereich_1.png"), format="png")
    (ziel / "animation.json").write_text(json.dumps({
        "quelle": "probe.svg", "breite": 40, "hoehe": 30, "bilder": bilder, "takt_ms": 50,
        "hintergrund": "hintergrund.png",
        "bereiche": [{"datei": "bereich_1.png", "x": 12, "y": 6, "breite": 10, "hoehe": 8, "spalten": spalten}],
    }), encoding="utf-8")
    return Animation("probe", ordner)


def _farbe(bild):
    return "#%02x%02x%02x" % tuple(bild.get(5, 4))


def test_die_beschreibung_wird_gelesen(wurzel, tmp_path):
    animation = _probeanimation(wurzel, tmp_path)
    assert (animation.breite, animation.hoehe, animation.bilder, animation.takt_ms) == (40, 30, 5, 50)
    assert animation.dauer_ms == 250
    assert animation.ausschnitte[0].x == 12


def test_eine_fehlende_animation_sagt_wie_man_sie_rendert(tmp_path):
    with pytest.raises(FileNotFoundError) as fehler:
        Animation("gibts_nicht", tmp_path)
    assert "grafik/rendern.py grafik/gibts_nicht.svg" in str(fehler.value)


def test_eine_kaputte_beschreibung_wird_verstaendlich_abgewiesen(tmp_path):
    (tmp_path / "kaputt").mkdir()
    (tmp_path / "kaputt" / "animation.json").write_text('{"breite": 10}', encoding="utf-8")
    with pytest.raises(ValueError) as fehler:
        Animation("kaputt", tmp_path)
    assert "unvollständig" in str(fehler.value)


def test_das_blatt_wird_der_reihe_nach_zerschnitten(wurzel, tmp_path):
    buehne = Buehne(wurzel, _probeanimation(wurzel, tmp_path))
    assert [_farbe(bild) for bild in buehne._folgen[0]] == FARBEN


def test_die_buehne_hat_die_groesse_der_animation(wurzel, tmp_path):
    buehne = Buehne(wurzel, _probeanimation(wurzel, tmp_path))
    assert (int(buehne.cget("width")), int(buehne.cget("height"))) == (40, 30)


def test_zeige_bild_laeuft_im_kreis(wurzel, tmp_path):
    buehne = Buehne(wurzel, _probeanimation(wurzel, tmp_path))
    buehne.zeige_bild(7)
    assert buehne.bild_nr == 2
    element = buehne._elemente[0]
    assert buehne.itemcget(element, "image") == str(buehne._folgen[0][2])


def test_abspielen_blaettert_im_takt_weiter(wurzel, tmp_path):
    buehne = Buehne(wurzel, _probeanimation(wurzel, tmp_path))
    assert not buehne.laeuft
    buehne.starten()
    buehne.starten()                      # ein zweiter Aufruf startet keinen zweiten Takt
    assert buehne.laeuft
    angemeldet = wurzel.tk.splitlist(wurzel.tk.call("after", "info"))
    assert len(angemeldet) == 1
    for erwartet in (1, 2, 3, 4, 0):
        buehne._weiter()
        assert buehne.bild_nr == erwartet


def test_anhalten_meldet_den_takt_ab(wurzel, tmp_path):
    buehne = Buehne(wurzel, _probeanimation(wurzel, tmp_path))
    buehne.starten()
    buehne.anhalten()
    assert not buehne.laeuft
    assert wurzel.tk.call("after", "info") == ""


def test_beim_abriss_haelt_die_buehne_selbst_an(wurzel, tmp_path):
    """Der Screen muss daran nicht denken – sonst liefe ein after() ins Leere."""
    rahmen = tk.Frame(wurzel)
    buehne = Buehne(rahmen, _probeanimation(wurzel, tmp_path))
    buehne.starten()
    rahmen.destroy()
    assert wurzel.tk.call("after", "info") == ""


def test_ein_blatt_in_falscher_groesse_wird_abgewiesen(wurzel, tmp_path):
    """Etwa nach einem Rendern mit anderen Einstellungen, ohne die Beschreibung."""
    animation = _probeanimation(wurzel, tmp_path, blatt_zu_klein=True)
    with pytest.raises(ValueError) as fehler:
        Buehne(wurzel, animation)
    assert "neu rendern" in str(fehler.value)
    # Keine halb gebaute Leinwand bleibt im Fenster zurück.
    assert not [kind for kind in wurzel.winfo_children() if isinstance(kind, Buehne)]


def test_die_echte_wrack_animation_laedt(wurzel):
    buehne = Buehne(wurzel, Animation("wrack"))
    assert (int(buehne.cget("width")), int(buehne.cget("height"))) == (960, 540)
    assert len(buehne._folgen[0]) == buehne.animation.bilder
