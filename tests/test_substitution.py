"""Tests für die monoalphabetische Substitution (Arbeitsplan 1.6).

Alle Erwartungswerte in dieser Datei sind von Hand aus
``dokumentation/Handbuchtexte.md`` (Seite 2) und aus der Textkonvention in
``crypto/normalize.py`` hergeleitet – nicht aus ``crypto/substitution.py``
abgeschrieben. Die Tabelle steht im Handbuch ausgeschrieben:

    Original  A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
    Geheim    Q W E R T Z U I O P A S D F G H J K L Y X C V B N M

Damit ist "HUND" → "IXFR" (H→I, U→X, N→F, D→R) der Prüfwert des Handbuchs.
"""

import pytest

from crypto import substitution
from crypto.normalize import ALPHABET, normalisieren
from crypto.substitution import (
    TASTATUR_REIHEN,
    entschluesseln,
    erzeuge_tastatur_tabelle,
    umkehren,
    verschluesseln,
)

# ───────────────────────────────────────────────────────────────────────────
# Von Hand aus dem Handbuch abgetippte Referenzdaten
# ───────────────────────────────────────────────────────────────────────────

#: Die drei Tastaturzeilen aus dem Merk-Trick des Handbuchs.
HANDBUCH_REIHEN = ("QWERTZUIOP", "ASDFGHJKL", "YXCVBNM")

#: Die untere Zeile der Handbuch-Tabelle, Zeichen für Zeichen abgetippt.
HANDBUCH_GEHEIMALPHABET = "QWERTZUIOPASDFGHJKLYXCVBNM"

#: Die Handbuch-Tabelle, ausgeschrieben statt berechnet.
HANDBUCH_TABELLE = {
    "A": "Q", "B": "W", "C": "E", "D": "R", "E": "T", "F": "Z",
    "G": "U", "H": "I", "I": "O", "J": "P", "K": "A", "L": "S",
    "M": "D", "N": "F", "O": "G", "P": "H", "Q": "J", "R": "K",
    "S": "L", "T": "Y", "U": "X", "V": "C", "W": "V", "X": "B",
    "Y": "N", "Z": "M",
}

#: Die zehn Übungssätze von Handbuchseite 2, jeweils von Hand verschlüsselt.
#: Beispielrechnung für Satz 1: A→Q, L→S, L→S, E→T, S→L | O→G, K→A.
UEBUNGSSAETZE_LEVEL_2 = [
    ("ALLES OK", "QSSTL GA"),
    ("ICH BIN HIER", "OEI WOF IOTK"),
    ("KOMM SCHNELL", "AGDD LEIFTSS"),
    ("WO BIST DU", "VG WOLY RX"),
    ("BLEIB RUHIG", "WSTOW KXIOU"),
    ("WEG IST FREI", "VTU OLY ZKTO"),
    ("GEFAHR NAH", "UTZQIK FQI"),
    ("ZEIT WIRD KNAPP", "MTOY VOKR AFQHH"),
    ("PLAN WIRD NEU", "HSQF VOKR FTX"),
    ("HILFE WIRD GEBRAUCHT", "IOSZT VOKR UTWKQXEIY"),
]

#: Übungswörter von Handbuchseite 1 und Übungssätze von Seite 3 – reichen
#: für den Rundlauf, auch wenn sie zu anderen Leveln gehören.
WEITERE_UEBUNGSTEXTE = [
    "HUND", "KATZE", "MAUS", "BURG", "FELS",
    "WALD", "STERN", "MOND", "SAND", "TURM",
    "ICH BIN IN SICHERHEIT",
    "STANDORT UNBEKANNT",
    "NAHE DEM WRACK",
    "RICHTUNG NORDEN",
    "KEIN WASSER MEHR",
    "VERFOLGER SIND NAH",
    "BRAUCHE SOFORT HILFE",
    "BIN NOCH AM LEBEN",
    "WARTE AUF RETTUNG",
    "SIGNAL WIRD SCHWACH",
]

#: Atbash-Tabelle (A→Z, B→Y, …, Z→A) als zweite, unabhängige Zuordnung.
#: Von Hand gebildet, indem das Alphabet rückwärts darunter geschrieben wird.
ATBASH_TABELLE = {
    buchstabe: ALPHABET[::-1][nummer] for nummer, buchstabe in enumerate(ALPHABET)
}

#: Identitätstabelle A→A … Z→Z – gültig, ändert aber nichts am Text.
IDENTITAETS_TABELLE = {buchstabe: buchstabe for buchstabe in ALPHABET}


def _tabelle_mit_aenderung(**aenderungen):
    """Liefert eine Kopie der Handbuch-Tabelle mit gezielten Änderungen."""
    tabelle = dict(HANDBUCH_TABELLE)
    tabelle.update(aenderungen)
    return tabelle


# ───────────────────────────────────────────────────────────────────────────
# 1. Die Tastatur-Tabelle selbst
# ───────────────────────────────────────────────────────────────────────────


def test_tastatur_reihen_entsprechen_dem_handbuch():
    """TASTATUR_REIHEN enthält genau die drei Zeilen aus dem Merk-Trick."""
    assert TASTATUR_REIHEN == HANDBUCH_REIHEN


def test_tastatur_reihen_ergeben_26_verschiedene_buchstaben():
    """Zusammengesetzt sind die drei Reihen ein vollständiges Alphabet."""
    zusammen = "".join(TASTATUR_REIHEN)
    assert len(zusammen) == 26
    assert set(zusammen) == set(ALPHABET)
    assert zusammen == HANDBUCH_GEHEIMALPHABET


def test_erzeuge_tastatur_tabelle_entspricht_der_handbuch_tabelle():
    """Die erzeugte Tabelle ist Zeichen für Zeichen die aus dem Handbuch."""
    assert erzeuge_tastatur_tabelle() == HANDBUCH_TABELLE


def test_tabelle_hat_26_eintraege_in_alphabetischer_reihenfolge():
    """Die UI zeigt die Tabelle an – deshalb ist A..Z die Reihenfolge."""
    tabelle = erzeuge_tastatur_tabelle()
    assert len(tabelle) == 26
    assert list(tabelle.keys()) == list(ALPHABET)


@pytest.mark.parametrize(
    "original, geheim",
    [("A", "Q"), ("B", "W"), ("H", "I"), ("U", "X"),
     ("N", "F"), ("D", "R"), ("Z", "M")],
)
def test_stichproben_aus_der_handkontrolle(original, geheim):
    """Die im Arbeitsplan von Hand kontrollierten Einzelzuordnungen."""
    assert erzeuge_tastatur_tabelle()[original] == geheim


def test_tabelle_ist_eine_bijektion():
    """26 Schlüssel, 26 verschiedene Werte – sonst wäre sie nicht umkehrbar."""
    tabelle = erzeuge_tastatur_tabelle()
    assert sorted(tabelle.values()) == list(ALPHABET)


def test_kein_buchstabe_bleibt_auf_sich_selbst():
    """Merkmal dieser Tabelle: keine Zuordnung bildet auf sich selbst ab."""
    tabelle = erzeuge_tastatur_tabelle()
    assert not [b for b in ALPHABET if tabelle[b] == b]


def test_tabelle_ist_keine_caesar_verschiebung():
    """Kernlernziel Level 2: Substitution ist kein festes Verschiebemuster."""
    tabelle = erzeuge_tastatur_tabelle()
    abstaende = {
        (ALPHABET.index(tabelle[b]) - ALPHABET.index(b)) % 26 for b in ALPHABET
    }
    assert len(abstaende) > 1


def test_erzeuge_tastatur_tabelle_liefert_jedesmal_ein_neues_dict():
    """Kein globaler Zustand: Änderungen am Ergebnis dürfen nicht bleiben."""
    erste = erzeuge_tastatur_tabelle()
    erste["A"] = "X"
    zweite = erzeuge_tastatur_tabelle()
    assert zweite["A"] == "Q"


def test_zu_wenige_buchstaben_in_den_reihen_werden_gemeldet(monkeypatch):
    """Fehlt ein Buchstabe in den Reihen, muss der Code das selbst merken."""
    monkeypatch.setattr(
        substitution, "TASTATUR_REIHEN", ("QWERTZUIOP", "ASDFGHJKL", "YXCVBN")
    )
    with pytest.raises(ValueError):
        substitution.erzeuge_tastatur_tabelle()


def test_doppelter_buchstabe_in_den_reihen_wird_gemeldet(monkeypatch):
    """26 Zeichen, aber nicht 26 verschiedene – muss ebenfalls auffallen."""
    monkeypatch.setattr(
        substitution, "TASTATUR_REIHEN", ("QWERTZUIOP", "ASDFGHJKL", "YXCVBNQ")
    )
    with pytest.raises(ValueError):
        substitution.erzeuge_tastatur_tabelle()


# ───────────────────────────────────────────────────────────────────────────
# 2. umkehren()
# ───────────────────────────────────────────────────────────────────────────


def test_umkehren_liefert_die_geheim_nach_original_zuordnung():
    """Aus A→Q wird beim Entschlüsseln Q→A."""
    umgekehrt = umkehren(erzeuge_tastatur_tabelle())
    erwartet = {geheim: original for original, geheim in HANDBUCH_TABELLE.items()}
    assert umgekehrt == erwartet


@pytest.mark.parametrize(
    "geheim, original",
    [("Q", "A"), ("W", "B"), ("I", "H"), ("X", "U"),
     ("F", "N"), ("R", "D"), ("M", "Z")],
)
def test_umkehren_stichproben(geheim, original):
    """Gegenprobe zu den handkontrollierten Zuordnungen."""
    assert umkehren(erzeuge_tastatur_tabelle())[geheim] == original


def test_umkehren_hat_26_eintraege():
    """Auch die Rücktabelle ist vollständig."""
    umgekehrt = umkehren(erzeuge_tastatur_tabelle())
    assert len(umgekehrt) == 26
    assert sorted(umgekehrt) == list(ALPHABET)


def test_umkehren_zweimal_ergibt_die_ausgangstabelle():
    """Zweimal umgekehrt ist wieder die Original-Zuordnung."""
    tabelle = erzeuge_tastatur_tabelle()
    assert umkehren(umkehren(tabelle)) == tabelle


def test_umkehren_veraendert_die_uebergebene_tabelle_nicht():
    """Die Eingabetabelle bleibt unangetastet (reine Funktion)."""
    tabelle = erzeuge_tastatur_tabelle()
    umkehren(tabelle)
    assert tabelle == HANDBUCH_TABELLE


def test_umkehren_der_atbash_tabelle_ergibt_sich_selbst():
    """Atbash ist selbstinvers – A→Z und Z→A."""
    assert umkehren(ATBASH_TABELLE) == ATBASH_TABELLE


# ───────────────────────────────────────────────────────────────────────────
# 3. Referenzwert aus dem Handbuch
# ───────────────────────────────────────────────────────────────────────────


def test_handbuch_beispiel_hund_wird_zu_ixfr():
    """Der Pflicht-Referenzwert von Handbuchseite 2."""
    assert verschluesseln("HUND") == "IXFR"


def test_handbuch_beispiel_ixfr_wird_wieder_hund():
    """Die Gegenrichtung desselben Beispiels."""
    assert entschluesseln("IXFR") == "HUND"


def test_tabelle_none_ist_die_tastatur_tabelle():
    """tabelle=None bedeutet ausdrücklich: Tastatur-Tabelle benutzen."""
    assert verschluesseln("HUND", None) == verschluesseln("HUND")
    assert verschluesseln("HUND", tabelle=HANDBUCH_TABELLE) == "IXFR"
    assert entschluesseln("IXFR", tabelle=HANDBUCH_TABELLE) == "HUND"


# ───────────────────────────────────────────────────────────────────────────
# 4. Die zehn Übungssätze, von Hand durchgerechnet
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("klartext, geheimtext", UEBUNGSSAETZE_LEVEL_2)
def test_uebungssaetze_werden_richtig_verschluesselt(klartext, geheimtext):
    """Jeder Übungssatz aus dem Handbuch, Buchstabe für Buchstabe geprüft."""
    assert verschluesseln(klartext) == geheimtext


@pytest.mark.parametrize("klartext, geheimtext", UEBUNGSSAETZE_LEVEL_2)
def test_uebungssaetze_werden_richtig_entschluesselt(klartext, geheimtext):
    """Dieselben Sätze in der Gegenrichtung."""
    assert entschluesseln(geheimtext) == klartext


@pytest.mark.parametrize(
    "text", [satz for satz, _ in UEBUNGSSAETZE_LEVEL_2] + WEITERE_UEBUNGSTEXTE
)
def test_rundlauf_mit_uebungstexten(text):
    """entschluesseln(verschluesseln(x)) muss x zurückgeben."""
    assert entschluesseln(verschluesseln(text)) == text


@pytest.mark.parametrize(
    "text", [satz for satz, _ in UEBUNGSSAETZE_LEVEL_2] + WEITERE_UEBUNGSTEXTE
)
def test_rundlauf_in_der_gegenrichtung(text):
    """Auch verschluesseln(entschluesseln(x)) muss x zurückgeben."""
    assert verschluesseln(entschluesseln(text)) == text


@pytest.mark.parametrize("text", WEITERE_UEBUNGSTEXTE[:6])
def test_rundlauf_mit_eigener_tabelle(text):
    """Der Rundlauf gilt auch für eine frei übergebene Tabelle."""
    assert entschluesseln(verschluesseln(text, ATBASH_TABELLE), ATBASH_TABELLE) == text


# ───────────────────────────────────────────────────────────────────────────
# 5. Fremde Tabellen
# ───────────────────────────────────────────────────────────────────────────


def test_atbash_tabelle_verschluesselt_hund_zu_sfmw():
    """Von Hand: H→S, U→F, N→M, D→W."""
    assert verschluesseln("HUND", ATBASH_TABELLE) == "SFMW"


def test_atbash_tabelle_verschluesselt_einen_satz():
    """ALLES OK wird mit Atbash zu ZOOVH LP."""
    assert verschluesseln("ALLES OK", ATBASH_TABELLE) == "ZOOVH LP"


def test_atbash_entschluesselt_zurueck():
    """Gegenrichtung derselben Handrechnung."""
    assert entschluesseln("SFMW", ATBASH_TABELLE) == "HUND"


def test_identitaetstabelle_laesst_den_text_unveraendert():
    """A→A … Z→Z ist gültig und darf nichts verändern."""
    assert verschluesseln("ZEIT WIRD KNAPP", IDENTITAETS_TABELLE) == "ZEIT WIRD KNAPP"
    assert entschluesseln("ZEIT WIRD KNAPP", IDENTITAETS_TABELLE) == "ZEIT WIRD KNAPP"


def test_uebergebene_tabelle_wird_nicht_veraendert():
    """Reine Funktion: die Tabelle des Aufrufers bleibt unangetastet."""
    tabelle = dict(ATBASH_TABELLE)
    verschluesseln("ICH BIN HIER", tabelle)
    entschluesseln("ICH BIN HIER", tabelle)
    assert tabelle == ATBASH_TABELLE


# ───────────────────────────────────────────────────────────────────────────
# 6. Textkonvention: Leerzeichen, Umlaute, Satzzeichen
# ───────────────────────────────────────────────────────────────────────────


def test_leerzeichen_bleiben_an_denselben_stellen(
):
    """Regel 3: Wortgrenzen bleiben im Geheimtext sichtbar."""
    klartext = "HILFE WIRD GEBRAUCHT"
    geheimtext = verschluesseln(klartext)
    positionen_klar = [i for i, z in enumerate(klartext) if z == " "]
    positionen_geheim = [i for i, z in enumerate(geheimtext) if z == " "]
    assert positionen_klar == positionen_geheim
    assert len(geheimtext) == len(klartext)


@pytest.mark.parametrize("klartext, geheimtext", UEBUNGSSAETZE_LEVEL_2)
def test_leerzeichen_zahl_bleibt_gleich(klartext, geheimtext):
    """In jedem Übungssatz stehen vorher und nachher gleich viele Lücken."""
    assert verschluesseln(klartext).count(" ") == klartext.count(" ")
    assert entschluesseln(geheimtext).count(" ") == geheimtext.count(" ")


def test_leerzeichen_wird_nicht_ersetzt():
    """Das Leerzeichen ist kein Buchstabe und bekommt kein Geheimzeichen."""
    assert verschluesseln("A A") == "Q Q"
    assert entschluesseln("Q Q") == "A A"


def test_leerer_text_bleibt_leer():
    """Randfall: nichts rein, nichts raus."""
    assert verschluesseln("") == ""
    assert entschluesseln("") == ""


def test_nur_leerzeichen_ergibt_leeren_text():
    """Randfall: Der Text besteht nur aus Weißraum (Regel 6 der Konvention)."""
    assert verschluesseln("   ") == ""
    assert entschluesseln("   ") == ""


def test_mehrfache_leerzeichen_werden_zusammengefasst():
    """Die Normalisierung räumt doppelte Lücken vorher auf."""
    assert verschluesseln("  ALLES   OK  ") == "QSSTL GA"


def test_kleinbuchstaben_werden_wie_grossbuchstaben_behandelt():
    """Regel 1: intern wird alles zu Großbuchstaben."""
    assert verschluesseln("hund") == "IXFR"
    assert entschluesseln("ixfr") == "HUND"


def test_umlaute_werden_ersetzt():
    """Regel 5: Ü→UE, also GRUESSE → U K X T L L T."""
    assert verschluesseln("Grüße") == "UKXTLLT"


def test_umlaute_im_ganzen_satz():
    """VERRÄTER → VERRAETER → C T K K Q T Y T K."""
    assert verschluesseln("Verräter") == "CTKKQTYTK"


def test_satzzeichen_und_ziffern_fallen_weg():
    """Regel 6: aus dem abgefangenen Funkspruch bleibt nur A–Z plus Lücken."""
    assert verschluesseln("Quadrant 4!") == "JXQRKQFY"


def test_funkspruch_mit_satzzeichen_wird_wie_der_klartext_behandelt():
    """Der Aufgabentext wird normalisiert angezeigt – das muss passen."""
    roh = "Quadrant 4 ist durchsucht, wir gehen jetzt auf Quadrant 7."
    assert verschluesseln(roh) == verschluesseln(normalisieren(roh))
    assert entschluesseln(verschluesseln(roh)) == normalisieren(roh)


def test_rundlauf_mit_umlauten_ergibt_den_normalisierten_text():
    """Nach dem Rundlauf steht die Ersatzform da, nicht mehr der Umlaut."""
    assert entschluesseln(verschluesseln("Hallo, hört mich jemand?")) == (
        "HALLO HOERT MICH JEMAND"
    )


# ───────────────────────────────────────────────────────────────────────────
# 7. Struktur- und Längenverhalten
# ───────────────────────────────────────────────────────────────────────────


def test_jeder_buchstabe_wird_immer_gleich_ersetzt():
    """Monoalphabetisch: gleiche Buchstaben ergeben gleiche Geheimzeichen."""
    geheimtext = verschluesseln("HILFE WIRD GEBRAUCHT")
    klartext = "HILFE WIRD GEBRAUCHT"
    zuordnung = {}
    for klar, geheim in zip(klartext, geheimtext):
        zuordnung.setdefault(klar, geheim)
        assert zuordnung[klar] == geheim


def test_sehr_langer_text_bleibt_korrekt():
    """Randfall Länge: 50 aneinandergehängte Übungssätze."""
    klartext = " ".join(satz for satz, _ in UEBUNGSSAETZE_LEVEL_2) * 50
    klartext = normalisieren(klartext)
    geheimtext = verschluesseln(klartext)
    assert len(geheimtext) == len(klartext)
    assert entschluesseln(geheimtext) == klartext


def test_langer_text_stueckweise_gleich_dem_ganzen():
    """Positionsunabhängigkeit: Wort für Wort ergibt dasselbe wie am Stück."""
    saetze = [satz for satz, _ in UEBUNGSSAETZE_LEVEL_2]
    einzeln = " ".join(verschluesseln(satz) for satz in saetze)
    am_stueck = verschluesseln(" ".join(saetze))
    assert einzeln == am_stueck


def test_ganzes_alphabet_wird_auf_das_geheimalphabet_abgebildet():
    """A..Z ergibt genau die untere Zeile der Handbuch-Tabelle."""
    assert verschluesseln(ALPHABET) == HANDBUCH_GEHEIMALPHABET
    assert entschluesseln(HANDBUCH_GEHEIMALPHABET) == ALPHABET


def test_verschluesseln_und_entschluesseln_sind_nicht_dasselbe():
    """Anders als Atbash ist die Tastatur-Tabelle nicht selbstinvers."""
    assert verschluesseln("HUND") != entschluesseln("HUND")


# ───────────────────────────────────────────────────────────────────────────
# 8. Ungültige Eingaben
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("funktion", [verschluesseln, entschluesseln])
def test_zu_kurze_tabelle_wirft_valueerror(funktion):
    """25 statt 26 Einträge – der Buchstabe A fehlt."""
    unvollstaendig = dict(HANDBUCH_TABELLE)
    del unvollstaendig["A"]
    with pytest.raises(ValueError):
        funktion("HUND", unvollstaendig)


@pytest.mark.parametrize("funktion", [verschluesseln, entschluesseln])
def test_leere_tabelle_wirft_valueerror(funktion):
    """Eine leere Tabelle ist etwas anderes als None (= Tastatur-Tabelle)."""
    with pytest.raises(ValueError):
        funktion("HUND", {})


@pytest.mark.parametrize("funktion", [verschluesseln, entschluesseln])
def test_doppelt_vergebener_buchstabe_wirft_valueerror(funktion):
    """B→Q wäre doppelt: Q ist schon für A vergeben, W fehlt dafür."""
    with pytest.raises(ValueError):
        funktion("HUND", _tabelle_mit_aenderung(B="Q"))


def test_fehlermeldung_nennt_den_doppelten_buchstaben():
    """Die Meldung soll sagen, was konkret nicht stimmt (Fehlerhandling)."""
    with pytest.raises(ValueError) as fehler:
        verschluesseln("HUND", _tabelle_mit_aenderung(B="Q"))
    assert "Q" in str(fehler.value)


@pytest.mark.parametrize("funktion", [verschluesseln, entschluesseln])
def test_wert_ausserhalb_von_a_bis_z_wirft_valueerror(funktion):
    """Ziffern sind keine gültigen Geheimzeichen."""
    with pytest.raises(ValueError):
        funktion("HUND", _tabelle_mit_aenderung(A="1"))


@pytest.mark.parametrize("funktion", [verschluesseln, entschluesseln])
def test_wert_mit_zwei_zeichen_wirft_valueerror(funktion):
    """Ein Geheimzeichen ist genau ein Buchstabe, nicht zwei."""
    with pytest.raises(ValueError):
        funktion("HUND", _tabelle_mit_aenderung(A="QQ"))


@pytest.mark.parametrize("funktion", [verschluesseln, entschluesseln])
def test_schluessel_ausserhalb_von_a_bis_z_wirft_valueerror(funktion):
    """Umlaute kommen in der Tabelle nicht vor (Regel 2 der Konvention)."""
    kaputt = dict(HANDBUCH_TABELLE)
    kaputt["Ä"] = kaputt.pop("A")
    with pytest.raises(ValueError):
        funktion("HUND", kaputt)


@pytest.mark.parametrize("funktion", [verschluesseln, entschluesseln])
def test_leerzeichen_als_tabellenschluessel_wirft_valueerror(funktion):
    """Das Leerzeichen wird nie ersetzt und gehört nicht in die Tabelle."""
    kaputt = dict(HANDBUCH_TABELLE)
    kaputt[" "] = "X"
    with pytest.raises(ValueError):
        funktion("HUND", kaputt)


@pytest.mark.parametrize("funktion", [verschluesseln, entschluesseln])
@pytest.mark.parametrize("keine_tabelle", ["QWERTZUIOPASDFGHJKLYXCVBNM", 26, ["A", "Q"]])
def test_tabelle_muss_ein_dict_sein(funktion, keine_tabelle):
    """Ein String oder eine Liste ist keine Zuordnungstabelle."""
    with pytest.raises((TypeError, ValueError)):
        funktion("HUND", keine_tabelle)


@pytest.mark.parametrize("funktion", [verschluesseln, entschluesseln])
@pytest.mark.parametrize("kein_text", [None, 42, ["H", "U"]])
def test_nicht_text_wirft_typeerror(funktion, kein_text):
    """Text rein, Text raus – alles andere ist ein Programmierfehler."""
    with pytest.raises(TypeError):
        funktion(kein_text)


def test_fehlermeldungen_sind_deutsch():
    """Alle Meldungen des Spiels sind auf Deutsch."""
    with pytest.raises(ValueError) as fehler:
        verschluesseln("HUND", {})
    meldung = str(fehler.value)
    assert meldung.strip()
    assert not any(
        wort in meldung.lower()
        for wort in ("table", "must", "invalid", "expected", "letter")
    )
