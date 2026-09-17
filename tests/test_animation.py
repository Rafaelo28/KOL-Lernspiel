"""Tests für ui/animation.py und die gerenderten Animationen in content/animationen.

Die Abspiel-Tests bauen sich eine kleine Animation selbst: jedes Einzelbild
in einer eigenen Farbe, von Tkinter als PNG geschrieben. So lässt sich
nachprüfen, dass das Blatt richtig zerschnitten wird und die Bilder in der
richtigen Reihenfolge kommen.

Die Tests zu den echten Animationen prüfen ohne Bildschirm, dass die Dateien
zueinander und zu ihrer SVG-Quelle passen – sonst zeigte das Spiel verrutschte
oder abgeschnittene Bilder. Das gilt für jeden Maßstab: Auf einem
1080p-Schulmonitor lädt das Spiel den grossen Satz aus ``<name>/1.5x/``.
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

ECHTE_ANIMATIONEN = sorted(p for p in ANIMATIONEN.iterdir() if p.is_dir()) if ANIMATIONEN.exists() else []

#: Jeder Bildsatz: der Ordner der Animation im Maßstab 1, die anderen im Unterordner.
ECHTE = [(ordner / rendern.unterordner(massstab), massstab)
         for ordner in ECHTE_ANIMATIONEN for massstab in rendern.MASSSTAEBE]


def _satz_id(satz):
    ordner, massstab = satz
    return ordner.name if massstab == 1 else f"{ordner.parent.name}@{massstab:g}"


def test_es_gibt_die_wrack_animation():
    assert (ANIMATIONEN / "wrack" / "animation.json").exists()


@pytest.mark.parametrize("ordner", ECHTE_ANIMATIONEN, ids=lambda p: p.name)
def test_jede_animation_gibt_es_in_jedem_massstab(ordner):
    """Sonst stürzte das Spiel erst auf dem Schulmonitor ab – dort gilt der grosse."""
    for massstab in rendern.MASSSTAEBE:
        assert (ordner / rendern.unterordner(massstab) / "animation.json").exists(), (
            f"{ordner.name} fehlt im Maßstab {massstab:g}: python3 grafik/rendern.py grafik/{ordner.name}.svg")


@pytest.mark.parametrize("satz", ECHTE, ids=_satz_id)
def test_die_dateien_einer_animation_passen_zusammen(satz):
    ordner, _ = satz
    beschreibung = json.loads((ordner / "animation.json").read_text(encoding="utf-8"))
    if beschreibung["hintergrund"] is None:
        # Ein durchsichtiger einmaliger Ablauf wird über etwas gelegt – ohne eigenen Hintergrund.
        assert beschreibung.get("durchsichtig") and beschreibung.get("einmalig")
    else:
        assert _png_groesse(ordner / beschreibung["hintergrund"]) == (beschreibung["breite"], beschreibung["hoehe"])
    if beschreibung.get("standbild"):
        assert beschreibung["bereiche"] == [], "Ein Standbild hat keine bewegten Ausschnitte."
    else:
        assert beschreibung["bereiche"], "Eine Animation ohne bewegten Ausschnitt ist ein Standbild."
    for bereich in beschreibung["bereiche"]:
        zeilen = -(-beschreibung["bilder"] // bereich["spalten"])
        assert _png_groesse(ordner / bereich["datei"]) == (
            bereich["spalten"] * bereich["breite"], zeilen * bereich["hoehe"])
        assert 0 <= bereich["x"] and bereich["x"] + bereich["breite"] <= beschreibung["breite"]
        assert 0 <= bereich["y"] and bereich["y"] + bereich["hoehe"] <= beschreibung["hoehe"]


@pytest.mark.parametrize("satz", ECHTE, ids=_satz_id)
def test_eine_animation_passt_zu_ihrer_svg_quelle(satz):
    """Wer die SVG ändert und das Rendern vergisst, merkt es hier – in jedem Maßstab."""
    ordner, massstab = satz
    beschreibung = json.loads((ordner / "animation.json").read_text(encoding="utf-8"))
    quelle = PROJEKT / beschreibung["quelle"]
    assert quelle.exists(), f"Die Quelle {beschreibung['quelle']} fehlt."
    e = rendern.einstellungen_lesen(quelle.read_text(encoding="utf-8"), quelle.stem, massstab)
    assert (e.breite, e.hoehe, e.bilder, e.takt_ms) == (
        beschreibung["breite"], beschreibung["hoehe"], beschreibung["bilder"], beschreibung["takt_ms"])
    assert [tuple(b) for b in e.bereiche] == [
        (b["x"], b["y"], b["breite"], b["hoehe"]) for b in beschreibung["bereiche"]]


@pytest.mark.parametrize("satz", ECHTE, ids=_satz_id)
def test_eine_animation_bleibt_klein_genug_fuer_schulrechner(satz):
    """Grober Deckel: im Arbeitsspeicher unter 40 MB, auf der Platte unter 8 MB.

    Im grossen Maßstab hat jedes Bild 1,5 × 1,5 = 2,25-mal so viele Pixel; der
    Deckel wächst entsprechend mit.
    """
    ordner, massstab = satz
    flaeche = massstab ** 2
    beschreibung = json.loads((ordner / "animation.json").read_text(encoding="utf-8"))
    speicher = beschreibung["breite"] * beschreibung["hoehe"] * 4 + sum(
        b["breite"] * b["hoehe"] * 4 * beschreibung["bilder"] for b in beschreibung["bereiche"])
    assert speicher < 40 * 2**20 * flaeche
    assert sum(p.stat().st_size for p in ordner.iterdir() if p.is_file()) < 8 * 2**20 * flaeche


def test_spiel_und_werkzeug_kennen_dieselben_massstaebe():
    """Das Spiel wählt einen Maßstab, das Werkzeug rendert die Bilder dazu – beide Listen müssen passen."""
    from ui import animation, stil

    assert stil.MASSSTAEBE == rendern.MASSSTAEBE
    for massstab in stil.MASSSTAEBE:
        assert animation.unterordner(massstab) == rendern.unterordner(massstab)


# ───────────────────────────────────────────────────────────────────────────
# 2. Abspielen (braucht einen Bildschirm)
# ───────────────────────────────────────────────────────────────────────────

tk = pytest.importorskip("tkinter")
from ui.animation import Ablauf, Animation, Buehne, Figur  # noqa: E402

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


def _probe_ablauf(wurzel, ordner, bilder=4):
    """Ein durchsichtiger einmaliger Ablauf ohne Hintergrund: 10×8 Pixel an (5, 3),
    Bild i in FARBEN[i] – mit einem durchsichtigen Pixel in der Ecke."""
    ziel = ordner / "blaettern"
    ziel.mkdir(parents=True)
    zeilen = []
    for y in range(8):
        zeile = bytearray()
        for nr in range(bilder):
            farbe = bytes.fromhex(FARBEN[nr][1:])
            for x in range(10):
                zeile += bytes(4) if (x, y) == (0, 0) else farbe + b"\xff"
        zeilen.append(bytes(zeile))
    (ziel / "bereich_1.png").write_bytes(rendern.png_schreiben(10 * bilder, 8, zeilen, kanaele=4))
    (ziel / "animation.json").write_text(json.dumps({
        "quelle": "blaettern.svg", "breite": 40, "hoehe": 30, "bilder": bilder, "takt_ms": 20,
        "hintergrund": None, "durchsichtig": True, "einmalig": True,
        "bereiche": [{"datei": "bereich_1.png", "x": 5, "y": 3, "breite": 10, "hoehe": 8, "spalten": bilder}],
    }), encoding="utf-8")
    return Animation("blaettern", ordner)


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


@pytest.mark.parametrize("massstab, groesse", [(1, (960, 540)), (1.5, (1440, 810))])
def test_die_echte_wrack_animation_laedt(wurzel, massstab, groesse):
    buehne = Buehne(wurzel, Animation("wrack", massstab=massstab))
    assert (int(buehne.cget("width")), int(buehne.cget("height"))) == groesse
    assert len(buehne._folgen[0]) == buehne.animation.bilder


def test_ein_fehlender_grosser_satz_nennt_den_massstab(tmp_path):
    (tmp_path / "nur_klein").mkdir()
    (tmp_path / "nur_klein" / "animation.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileNotFoundError) as fehler:
        Animation("nur_klein", tmp_path, massstab=1.5)
    assert "Maßstab 1.5" in str(fehler.value)
    assert "grafik/rendern.py grafik/nur_klein.svg" in str(fehler.value)


def test_beim_abriss_gibt_die_buehne_ihre_bilder_frei(wurzel, tmp_path):
    """Im grossen Maßstab belegt eine Szene um die 50 MB – die sollen nicht bis zum nächsten Aufräumen liegen."""
    buehne = Buehne(wurzel, _probeanimation(wurzel, tmp_path))
    bilder = [str(bild) for bild in buehne._folgen[0]]
    assert all(name in wurzel.image_names() for name in bilder)
    buehne.destroy()
    assert not any(name in wurzel.image_names() for name in bilder)


# ───────────────────────────────────────────────────────────────────────────
# 3. Standbilder und einmalige Abläufe
# ───────────────────────────────────────────────────────────────────────────

def test_ein_standbild_hat_nichts_abzuspielen(wurzel, tmp_path):
    ziel = tmp_path / "bild"
    ziel.mkdir()
    grund = tk.PhotoImage(master=wurzel, width=20, height=10)
    grund.put("#335577", to=(0, 0, 20, 10))
    grund.write(str(ziel / "hintergrund.png"), format="png")
    (ziel / "animation.json").write_text(json.dumps({
        "quelle": "bild.svg", "breite": 20, "hoehe": 10, "bilder": 1, "takt_ms": 1,
        "hintergrund": "hintergrund.png", "bereiche": [], "standbild": True}), encoding="utf-8")
    animation = Animation("bild", tmp_path)
    assert animation.standbild and not animation.einmalig
    buehne = Buehne(wurzel, animation)
    buehne.starten()
    assert not buehne.laeuft
    assert wurzel.tk.call("after", "info") == ""


def test_ein_ablauf_ohne_hintergrund_wird_gelesen(wurzel, tmp_path):
    animation = _probe_ablauf(wurzel, tmp_path)
    assert animation.hintergrund is None
    assert animation.durchsichtig and animation.einmalig


def _farbe_von(leinwand, element):
    bild = leinwand.itemcget(element, "image")
    return "#%02x%02x%02x" % tuple(leinwand.tk.call(bild, "get", 5, 4))


def test_ein_ablauf_zeigt_seine_bilder_der_reihe_nach_und_raeumt_dann_auf(wurzel, tmp_path):
    import time

    leinwand = tk.Canvas(wurzel, width=40, height=30)
    ablauf = Ablauf(leinwand, _probe_ablauf(wurzel, tmp_path), x=2, y=1)
    gesehen, fertig = [], []

    def bei_bild(nr, anzahl):
        (element,) = leinwand.find_withtag(Ablauf.TAG)
        gesehen.append((_farbe_von(leinwand, element), nr, anzahl))

    assert ablauf.abspielen(bei_bild=bei_bild, danach=lambda: fertig.append(True))
    assert leinwand.coords(leinwand.find_withtag(Ablauf.TAG)[0]) == [7.0, 4.0]   # 2 + 5, 1 + 3
    ende = time.monotonic() + 2
    while not fertig and time.monotonic() < ende:
        wurzel.update()
        time.sleep(0.005)
    assert gesehen == [(farbe, nr, 4) for nr, farbe in enumerate(FARBEN[:4])]
    assert fertig == [True]
    assert leinwand.find_withtag(Ablauf.TAG) == ()
    assert not ablauf.laeuft


def test_ein_ablauf_laeuft_rueckwaerts_und_nicht_doppelt(wurzel, tmp_path):
    leinwand = tk.Canvas(wurzel, width=40, height=30)
    ablauf = Ablauf(leinwand, _probe_ablauf(wurzel, tmp_path))
    farben = []
    ablauf.abspielen(rueckwaerts=True,
                     bei_bild=lambda nr, anzahl: farben.append(_farbe_von(leinwand, leinwand.find_withtag(Ablauf.TAG)[0])))
    assert not ablauf.abspielen()                          # läuft schon – kein zweiter darüber
    assert farben == [FARBEN[3]]
    ablauf.abbrechen()
    assert leinwand.find_withtag(Ablauf.TAG) == () and not ablauf.laeuft
    assert wurzel.tk.call("after", "info") == ""


def test_die_durchsichtigkeit_bleibt_beim_zerschneiden_erhalten(wurzel, tmp_path):
    """Sonst läge beim Umblättern ein Rechteck über dem Text."""
    leinwand = tk.Canvas(wurzel, width=40, height=30)
    ablauf = Ablauf(leinwand, _probe_ablauf(wurzel, tmp_path))
    (_, folge), = ablauf._folgen
    assert folge[0].transparency_get(0, 0)
    assert not folge[0].transparency_get(5, 4)


# ───────────────────────────────────────────────────────────────────────────
# 4. Szenenwechsel und bewegte Figuren (für den Abschluss, 6.8)
# ───────────────────────────────────────────────────────────────────────────

def test_wechseln_tauscht_die_szene_und_laesst_liegen_was_darueber_liegt(wurzel, tmp_path):
    buehne = Buehne(wurzel, _probeanimation(wurzel, tmp_path / "abend"))
    alte_elemente = set(buehne.find_all())
    alte_bilder = [str(bild) for bild in buehne._folgen[0]]
    text = buehne.create_text(3, 3, text="Die Nacht vergeht.")
    buehne.starten()
    buehne.zeige_bild(3)

    morgen = _probeanimation(wurzel, tmp_path / "morgen", spalten=3, bilder=3)
    morgen.breite, morgen.hoehe = 60, 45
    buehne.wechseln(morgen)

    assert buehne.animation is morgen
    assert (int(buehne.cget("width")), int(buehne.cget("height"))) == (60, 45)
    assert [_farbe(bild) for bild in buehne._folgen[0]] == FARBEN[:3]
    stapel = buehne.find_all()
    assert not alte_elemente & set(stapel)
    assert stapel == (buehne._hintergrund_element, buehne._elemente[0], text)
    assert buehne.bild_nr == 0
    assert buehne.laeuft
    assert len(wurzel.tk.splitlist(wurzel.tk.call("after", "info"))) == 1
    assert not any(name in wurzel.image_names() for name in alte_bilder)


def test_eine_angehaltene_buehne_bleibt_beim_wechseln_stehen(wurzel, tmp_path):
    buehne = Buehne(wurzel, _probeanimation(wurzel, tmp_path / "abend"))
    buehne.wechseln(_probeanimation(wurzel, tmp_path / "morgen"))
    assert not buehne.laeuft
    assert wurzel.tk.call("after", "info") == ""


def test_eine_szene_ohne_hintergrund_laesst_sich_einwechseln(wurzel, tmp_path):
    buehne = Buehne(wurzel, _probeanimation(wurzel, tmp_path / "abend"))
    buehne.wechseln(_probe_ablauf(wurzel, tmp_path / "ohne"))
    assert buehne._hintergrund_element is None
    assert buehne.find_all() == tuple(buehne._elemente)


def test_eine_figur_zeigt_nur_ihre_ausschnitte_dort_wo_sie_steht(wurzel, tmp_path):
    leinwand = tk.Canvas(wurzel, width=400, height=300)
    figur = Figur(leinwand, _probeanimation(wurzel, tmp_path), x=100, y=50)
    (element,) = figur.elemente
    assert leinwand.find_all() == (element,), "Der Hintergrund käme doppelt über die Szene."
    assert leinwand.coords(element) == [112.0, 56.0]            # 100 + 12, 50 + 6
    assert leinwand.find_withtag(Figur.TAG) == (element,)
    assert (figur.x, figur.y, figur.bild_nr) == (100, 50, 0)
    assert _farbe_von(leinwand, element) == FARBEN[0]

    figur.verschieben(-30, 7)
    assert leinwand.coords(element) == [-18.0, 13.0]
    assert (figur.x, figur.y) == (-30, 7)


def test_eine_figur_blaettert_nur_wenn_man_sie_laesst(wurzel, tmp_path):
    """Kein eigener Takt: Flug und Rotor bleiben im Takt dessen, der sie bewegt."""
    leinwand = tk.Canvas(wurzel, width=400, height=300)
    figur = Figur(leinwand, _probeanimation(wurzel, tmp_path))
    assert wurzel.tk.call("after", "info") == ""
    figur.zeige_bild(7)
    assert figur.bild_nr == 2
    assert _farbe_von(leinwand, figur.elemente[0]) == FARBEN[2]


def test_eine_figur_raeumt_hinter_sich_auf(wurzel, tmp_path):
    leinwand = tk.Canvas(wurzel, width=400, height=300)
    anderes = leinwand.create_rectangle(0, 0, 5, 5)
    figur = Figur(leinwand, _probeanimation(wurzel, tmp_path))
    bilder = [str(bild) for _, folge in figur._folgen for bild in folge]
    figur.entfernen()
    assert leinwand.find_all() == (anderes,)
    assert figur.elemente == ()
    assert not any(name in wurzel.image_names() for name in bilder)


def test_die_durchsichtigkeit_der_figur_bleibt_erhalten(wurzel, tmp_path):
    """Der Hubschrauber ist kein Rechteck vor dem Morgenhimmel."""
    leinwand = tk.Canvas(wurzel, width=400, height=300)
    figur = Figur(leinwand, _probe_ablauf(wurzel, tmp_path))
    (_, folge), = figur._folgen
    assert folge[0].transparency_get(0, 0)
    assert not folge[0].transparency_get(5, 4)
