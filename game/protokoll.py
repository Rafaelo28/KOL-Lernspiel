"""Das CSV-Protokoll eines Durchlaufs (Arbeitsplan 5.5).

Pro Aufgabe eine Zeile. Aus diesen Dateien entsteht später die Auswertung –
sie sind das eigentliche Ergebnis des Experiments, nicht das Spiel.

Datenschutz (Projektregel 7)
────────────────────────────
In der Datei steht **kein Klarname**, nur die Pseudonym-ID aus dem
Spielstand. Welche Person dahintersteckt, führt die Lehrkraft getrennt.
Von der gewählten Spielfigur steht nur ihre Kennung drin (``vic_moreno``) –
sie sagt nichts über die Person aus, wird aber gebraucht: Die gesendeten
Funksprüche tragen die Initialen der Figur, ihr genauer Wortlaut hängt also
an ihr.

Der Ordner ``logs/`` ist in ``.gitignore``. Die Dateien dürfen nie ins
Repository.

Welche Übung jemand bekommen hat
────────────────────────────────
Aus ``seed`` und ``kennung`` einer Zeile baut
:func:`game.generator.uebung_nachbauen` die Übung wieder nach. Die Spalte
``aufgabennummer`` taugt dafür **nicht**: Sie zählt die Reihenfolge aller
Aufgaben im Level, Funksprüche eingeschlossen – der Zufallsstrom zählt nur
die Übungen.

Zeilen, bei denen Vorsicht geboten ist
──────────────────────────────────────
* ``abgebrochen = ja``: Das Level endete, während die Aufgabe noch lief. In
  ``sekunden`` steht dann die Zeit bis zum Levelwechsel, keine Rechenzeit.
  Für Zeitauswertungen herausfiltern.
* Für alles, was mit Tempo zu tun hat, ``gerechnete_buchstaben`` nehmen,
  nicht ``laenge_in_buchstaben``. Die beiden unterscheiden sich nur, wenn
  jemand bei einem Funkspruch mit Teilaufgabe von sich aus die ganze
  Nachricht gerechnet hat. ``vollstaendig_geloest`` allein zeigt das nicht
  an: Bei Übungen und bei Funksprüchen ohne Teilaufgabe steht es bei jeder
  gelösten Aufgabe auf ``ja`` – dort ist der Teil schon das Ganze.

Die Levelzeit
─────────────
``level_sekunden`` und ``levelende`` beschreiben das **Level**, nicht die
Aufgabe; sie stehen deshalb in jeder Zeile des Levels gleich. Solange das
Level läuft, ist ``levelende = laeuft`` und ``level_sekunden`` ein
Zwischenstand. Ein Level ohne eine einzige Aufgabe hat keine Zeile.

Warum der Seed in jeder Zeile steht
───────────────────────────────────
Der Arbeitsplan verlangt ihn "einmal pro Logdatei". Als Kommentarzeile über
der Tabelle wäre er zwar einmal da, aber jedes Tabellenprogramm und jedes
Auswertungsskript stolperte darüber. Als Spalte ist er redundant und stört
niemanden – und wenn jemand später mehrere Dateien zusammenkopiert, bleibt
die Zuordnung erhalten.

Warum ganze Sekunden
────────────────────
Die Spalte ``sekunden`` enthält ganze Zahlen. Mit Nachkommastellen käme das
Dezimaltrennzeichen ins Spiel: Ein "16.2" liest deutsches Excel nicht als
Zahl, ein "16,2" wiederum kollidiert mit dem Semikolon in naiven Lesern. Eine
Zehntelsekunde Genauigkeit sagt bei einer Aufgabe, die eine halbe Minute
dauert, ohnehin nichts – der Ärger wäre also umsonst.

Warum Semikolon und ``utf-8-sig``
─────────────────────────────────
Die Dateien werden auf einem deutschen Rechner in Excel oder LibreOffice
geöffnet. Dort ist das Semikolon das erwartete Trennzeichen; mit einem Komma
landet die ganze Zeile in einer einzigen Spalte. Das ``utf-8-sig`` sorgt
dafür, dass Umlaute in Excel richtig ankommen.

Für die Auswertung mit pandas::

    pandas.read_csv(datei, sep=";", encoding="utf-8-sig")

Wann geschrieben wird
─────────────────────
:meth:`Protokoll.schreiben` wird nach jeder abgeschlossenen Aufgabe und nach
jedem Levelwechsel aufgerufen, zuletzt am Spielende – sonst bleibt in
``levelende`` der Zwischenstand stehen. Die Datei wird jedes Mal vollständig
neu geschrieben; das ist bei zwanzig Zeilen kostenlos.

Geschrieben wird erst in eine Nebendatei, die dann in einem Schritt die alte
ersetzt. Bricht das Schreiben mittendrin ab – Absturz, zugeklappter Deckel,
Stromausfall –, bleibt die letzte vollständige Fassung stehen, statt einer
Datei, die nur noch die Kopfzeile enthält.
"""

import csv
import os
from datetime import datetime
from pathlib import Path

#: Wohin die Protokolle geschrieben werden. Der Inhalt steht in .gitignore.
STANDARDORDNER = "logs"

#: Trennzeichen und Kodierung – siehe Modulkopf.
TRENNZEICHEN = ";"
KODIERUNG = "utf-8-sig"

#: So viele Zeichen des Pseudonyms kommen höchstens in den Dateinamen. Die
#: Spalte ``pseudonym`` enthält es immer vollständig; im Dateinamen würde ein
#: sehr langes die Grenze des Dateisystems (255 Bytes) sprengen, und der
#: ganze Durchlauf bliebe ungespeichert.
HOECHSTLAENGE_PSEUDONYM_IM_DATEINAMEN = 40

#: Die Spalten in ihrer Reihenfolge. Pseudonym, Level, Aufgabennummer,
#: Richtung, Versuche, Lösung angezeigt, Sekunden und Zusatzaufgabe verlangt
#: der Arbeitsplan wörtlich; die übrigen kamen in den Phasen 4 und 5 dazu.
SPALTEN = (
    "pseudonym",
    "seed",
    "figur",
    "level",
    "levelende",
    "level_sekunden",
    "aufgabennummer",
    "kennung",
    "quelle",
    "verfahren",
    "richtung",
    "zusatzaufgabe",
    "laenge_in_buchstaben",
    "gerechnete_buchstaben",
    "sekunden",
    "versuche",
    "versuche_ohne_fortschritt",
    "loesung_angezeigt",
    "abgebrochen",
    "geloest",
    "vollstaendig_geloest",
)


def _ja_nein(wert):
    """Wahrheitswerte als "ja"/"nein" – lesbarer als True/False in Excel."""
    return "ja" if wert else "nein"


def zeile(spielstand, bearbeitung, aufgabennummer):
    """Baut die Logzeile zu einer erledigten Aufgabe.

    Rückgabe ist ein ``dict`` mit genau den Schlüsseln aus :data:`SPALTEN`.
    """
    aufgabe = bearbeitung.aufgabe
    return {
        "pseudonym": spielstand.pseudonym,
        "seed": spielstand.zufallsquelle.protokollwert,
        "figur": spielstand.figur.kennung,
        "level": aufgabe.level,
        "levelende": spielstand.levelende(aufgabe.level),
        "level_sekunden": round(spielstand.level_sekunden(aufgabe.level)),
        "aufgabennummer": aufgabennummer,
        "kennung": aufgabe.kennung,
        "quelle": aufgabe.quelle,
        "verfahren": aufgabe.verfahren,
        "richtung": aufgabe.richtung,
        "zusatzaufgabe": _ja_nein(aufgabe.zusatzaufgabe),
        "laenge_in_buchstaben": aufgabe.laenge_in_buchstaben,
        "gerechnete_buchstaben": bearbeitung.gerechnete_buchstaben,
        "sekunden": round(bearbeitung.benoetigte_sekunden),
        "versuche": bearbeitung.versuche,
        "versuche_ohne_fortschritt": bearbeitung.versuche_ohne_fortschritt,
        "loesung_angezeigt": _ja_nein(bearbeitung.loesung_angezeigt),
        "abgebrochen": _ja_nein(bearbeitung.abgebrochen),
        "geloest": _ja_nein(bearbeitung.geloest),
        "vollstaendig_geloest": _ja_nein(bearbeitung.vollstaendig_geloest),
    }


def zeilen(spielstand):
    """Alle Logzeilen eines Spielstands, in der Reihenfolge des Spiels.

    Die Aufgabennummer zählt **je Level** ab eins, Funksprüche eingeschlossen
    – sie gibt die Reihenfolge an. Welche Übung es war, steht in der Kennung
    (siehe Modulkopf und :func:`game.generator.uebung_nachbauen`).
    """
    nummer_je_level = {}
    gesammelt = []
    for bearbeitung in spielstand.erledigte_aufgaben:
        level = bearbeitung.aufgabe.level
        nummer_je_level[level] = nummer_je_level.get(level, 0) + 1
        gesammelt.append(zeile(spielstand, bearbeitung, nummer_je_level[level]))
    return gesammelt


def dateiname(spielstand, zeitpunkt=None):
    """Baut den Dateinamen: Pseudonym und Zeitstempel.

    Der Zeitstempel verhindert, dass ein zweiter Durchlauf denselben
    Pseudonyms den ersten überschreibt. Zeichen, die in Dateinamen Ärger
    machen, werden zu ``_``, und ein sehr langes Pseudonym wird gekürzt (siehe
    :data:`HOECHSTLAENGE_PSEUDONYM_IM_DATEINAMEN`).

    >>> from datetime import datetime
    >>> class Probe:
    ...     pseudonym = "P07"
    >>> dateiname(Probe(), datetime(2026, 9, 10, 14, 5, 30))
    'durchlauf_P07_2026-09-10_140530.csv'
    """
    zeitpunkt = zeitpunkt if zeitpunkt is not None else datetime.now()
    stempel = zeitpunkt.strftime("%Y-%m-%d_%H%M%S")
    sauber = "".join(
        zeichen if zeichen.isalnum() or zeichen in "-_" else "_"
        for zeichen in str(spielstand.pseudonym)
    )[:HOECHSTLAENGE_PSEUDONYM_IM_DATEINAMEN]
    return f"durchlauf_{sauber}_{stempel}.csv"


class Protokoll:
    """Schreibt das CSV eines Durchlaufs.

    Der Dateiname wird **einmal** beim Anlegen festgelegt. Sonst entstünde
    bei jedem Schreiben eine neue Datei, und am Ende lägen zwanzig
    Bruchstücke desselben Durchlaufs im Ordner.
    """

    def __init__(self, spielstand, ordner=None, zeitpunkt=None):
        self.spielstand = spielstand
        self.ordner = Path(ordner if ordner is not None else STANDARDORDNER)
        self.dateiname = dateiname(spielstand, zeitpunkt)

    @property
    def pfad(self):
        """Die Datei, in die geschrieben wird."""
        return self.ordner / self.dateiname

    @property
    def zwischendatei(self):
        """Die Nebendatei, in die zuerst geschrieben wird."""
        return self.pfad.with_name(self.pfad.name + ".tmp")

    def schreiben(self):
        """Schreibt alle bisher erledigten Aufgaben und gibt den Pfad zurück.

        Die Datei wird jedes Mal vollständig neu geschrieben – erst in die
        :attr:`zwischendatei`, die dann in einem Schritt die alte ersetzt. So
        ist nach einem Absturz alles bis zur letzten abgeschlossenen Aufgabe
        gesichert, auch wenn er mitten in diesem Aufruf kam.

        Klappt das Schreiben nicht, kommt der ``OSError`` durch – etwa wenn
        die Datei unter Windows gerade in Excel offen ist. Die alte Fassung
        bleibt dann unverändert. Die Oberfläche kann den Fehler melden und es
        nach der nächsten Aufgabe noch einmal versuchen; verloren geht dabei
        nichts, weil jedes Mal alles geschrieben wird.
        """
        inhalt = zeilen(self.spielstand)
        self.ordner.mkdir(parents=True, exist_ok=True)
        zwischendatei = self.zwischendatei
        try:
            with open(zwischendatei, "w", newline="", encoding=KODIERUNG) as datei:
                schreiber = csv.DictWriter(
                    datei, fieldnames=list(SPALTEN), delimiter=TRENNZEICHEN
                )
                schreiber.writeheader()
                schreiber.writerows(inhalt)
                # Erst wirklich auf der Platte, dann umbenennen – sonst kann
                # nach einem Stromausfall die neue Datei leer sein.
                datei.flush()
                os.fsync(datei.fileno())
            os.replace(zwischendatei, self.pfad)
        except BaseException:
            zwischendatei.unlink(missing_ok=True)
            raise
        return self.pfad
