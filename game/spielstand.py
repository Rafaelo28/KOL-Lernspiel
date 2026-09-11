"""Der zentrale Spielzustand (Arbeitsplan 5.1).

Ein :class:`Spielstand` hält alles zusammen, was zu **einem Durchlauf** gehört:
die gewählte Figur, das laufende Level, die Aufgabe, an der gerade gearbeitet
wird, und die schon erledigten Aufgaben.

Warum das nicht in der Oberfläche steht
───────────────────────────────────────
Der Arbeitsplan sagt ausdrücklich "zentral, nicht über die UI verstreut". Der
Grund ist derselbe wie beim Versuchszähler: Verteilt man den Zustand über die
Screens, gibt es ihn mehrfach, und irgendein Screen vergisst irgendwann eine
Regel. Hier stehen die Übergänge einmal und lassen sich einmal testen.

Die Oberfläche fragt den Spielstand also, was gerade dran ist – sie führt nicht
selbst Buch.

Was hier **nicht** hineingehört
───────────────────────────────
* Der Aufgaben-Timer (5.3). Das **Level**-Zeitfenster (5.2) sitzt dagegen
  hier, weil sein Ablauf einen Zustandswechsel auslöst – siehe unten.
* Das CSV-Logging (Aufgabe 5.5). Der Spielstand sammelt die erledigten
  Bearbeitungen in :attr:`Spielstand.erledigte_aufgaben`; wie daraus eine
  Datei wird, entscheidet 5.5.
* Der Schwellenwert für Zusatzaufgaben (5.4). Der Spielstand fragt
  :mod:`game.zusatzaufgaben`, ob eine fällig ist, und setzt die Obergrenze
  je Level durch – die Zahlen selbst stehen dort.

Projektregel 1 steckt in :meth:`Spielstand.naechstes_level`
───────────────────────────────────────────────────────────
"Läuft die Zeit ab, wird sofort zum nächsten Level gewechselt – egal, wie
viele Aufgaben noch offen sind." Deshalb bricht der Levelwechsel eine offene
Aufgabe nicht ab, sondern **schliesst sie ordentlich ab**: Die Lösung wird
eingeblendet und die Bearbeitung wandert in die Liste der erledigten. Sonst
fehlte sie später im Log, und die Auswertung könnte nicht zwischen "nicht
bearbeitet" und "Zeit war um" unterscheiden.

Das Zeitfenster (Aufgabe 5.2)
─────────────────────────────
Mit jedem :meth:`starte_level` beginnt ein :class:`game.zeitfenster.Zeitfenster`
über 15, 20 oder 25 Minuten. Es hält nie an – auch nicht während einer
Zusatzaufgabe und nicht während des Weiterrechnen-Knopfes.

Ablaufen allein bewirkt nichts: Die Oberfläche muss regelmässig
:meth:`pruefe_zeitfenster` aufrufen (in Tkinter über ``after``). Das ist
Absicht – so gibt es keinen Nebenläufigkeitsfaden, der mitten in einer
Eingabe den Zustand umbaut, und der Wechsel geschieht immer an einer Stelle,
an der die Oberfläche darauf gefasst ist.

Zwischen dem Ablauf und dem nächsten Aufruf liegt also ein kurzer Moment. In
ihm wird keine neue Aufgabe mehr gestellt – :meth:`naechste_uebung` und
:meth:`stelle_funkspruch` werfen dann :class:`ZeitIstUm`, und die Oberfläche
schaltet weiter.

Wie lange jedes Level lief und ob es am Timer endete, hält der Spielstand
fest (:meth:`Spielstand.level_sekunden`, :meth:`Spielstand.levelende`) – die
Projektregeln verlangen die Zeitmessung pro Level **und** pro Aufgabe.

Was sich nur einmal tun lässt
─────────────────────────────
* :meth:`starte_level` – einmal je Durchlauf, danach nur noch
  :meth:`naechstes_level`. Sonst begänne ein Zeitfenster von vorn, oder ein
  Level fiele unbemerkt aus.
* Jeden Funkspruch stellen – sonst gäbe es drei frische Versuche und eine
  doppelte Zeile im Log.
* Zusatzaufgaben über die Obergrenze des Levels hinaus gibt es gar nicht.

Diese Sperren stehen hier und nicht in der Oberfläche: Ein Screen, der in
Phase 6 neu aufgebaut wird, soll die Messdaten nicht verfälschen können.

Datenschutz
───────────
:attr:`Spielstand.pseudonym` ist die ID, unter der ein Durchlauf im Log
auftaucht. Ein Klarname darf hier nie hinein (Projektregel 7); die Zuordnung
zu einer Person führt die Lehrkraft getrennt.
"""

from content import verfahren as _verfahren
from game.bearbeitung import Bearbeitung
from game.generator import Aufgabengenerator, aufgabe_aus_funkspruch
from game.zeitfenster import fuer_level as _zeitfenster_fuer_level
from game.zusatzaufgaben import (
    HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL,
    ist_faellig as _zusatzaufgabe_ist_faellig,
    obergrenze_erreicht as _obergrenze_erreicht,
)
from game.zufallsquelle import SEED_OBERGRENZE, Zufallsquelle

#: Die Level in ihrer Reihenfolge.
LEVEL = tuple(sorted(_verfahren.VERFAHREN_NACH_LEVEL))

#: So viele Ziffern hat der grösste Seed – das erzeugte Pseudonym braucht alle.
_SEED_STELLEN = len(str(SEED_OBERGRENZE - 1))

#: Wie ein Level endete – so steht es im Log.
LEVELENDE_ZEITABLAUF = "zeitablauf"
LEVELENDE_VORZEITIG = "vorzeitig"
LEVELENDE_LAEUFT = "laeuft"


class ZeitIstUm(ValueError):
    """Das Zeitfenster ist abgelaufen – eine neue Aufgabe gibt es nicht mehr.

    Die Oberfläche fängt genau diesen Fehler und ruft
    :meth:`Spielstand.pruefe_zeitfenster` auf. Er ist ein ``ValueError``,
    damit Code, der nur den allgemeinen Fall kennt, ihn trotzdem bemerkt.
    """


class Spielstand:
    """Der Zustand eines Durchlaufs.

    >>> from content import charaktere
    >>> stand = Spielstand(charaktere.VIC_MORENO, Zufallsquelle(4711), "P01")
    >>> stand.figur.name, stand.pseudonym
    ('Vic Moreno', 'P01')
    >>> stand.aktuelles_level is None
    True

    Ein Level starten, eine Übung stellen, sie lösen:

    >>> stand.starte_level(1)
    >>> aufgabe = stand.naechste_uebung()
    >>> ergebnis = stand.versuchen(aufgabe.loesung)
    >>> ergebnis.richtig
    True
    >>> stand.aufgabe_abschliessen()
    >>> len(stand.erledigte_aufgaben)
    1
    """

    def __init__(self, figur, zufallsquelle=None, pseudonym=None, zeitgeber=None):
        if figur is None:
            raise ValueError(
                "Ohne gewählte Figur geht es nicht: Ihre Initialen "
                "unterschreiben jeden gesendeten Funkspruch."
            )
        self.figur = figur
        self.zufallsquelle = zufallsquelle if zufallsquelle is not None else Zufallsquelle.neu()
        # Ein Pseudonym aus lauter Leerzeichen ist keins – im Log stünde eine
        # leere Zelle.
        pseudonym = str(pseudonym).strip() if pseudonym is not None else ""
        self.pseudonym = pseudonym or self._pseudonym_erzeugen()
        self._generator = Aufgabengenerator(self.zufallsquelle)
        self._zeitgeber = zeitgeber
        self._zeitfenster = None
        self._level = None
        self._gestartete_level = set()
        self._levelzeiten = {}
        self._gestellte_funksprueche = set()
        self._bearbeitung = None
        self._erledigt = []

    def _pseudonym_erzeugen(self):
        """Baut eine ID aus dem Seed – kein Klarname, aber wiederfindbar.

        Die Ziffern **sind** der Seed, mit Nullen aufgefüllt und nie gekürzt:
        Zwei Durchläufe mit verschiedenem Seed bekommen so nie dieselbe ID.
        """
        return f"P{self.zufallsquelle.seed:0{_SEED_STELLEN}d}"

    # ── Was gerade gilt ────────────────────────────────────────────────────

    @property
    def aktuelles_level(self):
        """Das laufende Level, oder ``None`` vor dem Start."""
        return self._level

    @property
    def aktuelles_verfahren(self):
        """Das Verfahren des laufenden Levels, oder ``None``."""
        if self._level is None:
            return None
        return _verfahren.VERFAHREN_NACH_LEVEL[self._level]

    @property
    def zeitfenster(self):
        """Das laufende Zeitfenster, oder ``None`` ausserhalb eines Levels."""
        return self._zeitfenster

    @property
    def restzeit_text(self):
        """Die Restzeit als "MM:SS" – leer ausserhalb eines Levels.

        Das Fenster zeigt das bewusst nicht an (Entscheidung nach 6.1: ein
        mitzählender Countdown erzeugt Zeitdruck-Stress). Das Feld bleibt für
        Tests und eine mögliche spätere Lehrkraft-Ansicht erhalten.
        """
        return self._zeitfenster.restzeit_text if self._zeitfenster else ""

    @property
    def verbleibende_sekunden(self):
        """Wie viel Zeit im Level noch bleibt – 0 ausserhalb eines Levels."""
        return self._zeitfenster.verbleibende_sekunden if self._zeitfenster else 0.0

    @property
    def zeit_ist_um(self):
        """Ist das Zeitfenster des laufenden Levels abgelaufen?"""
        return self._zeitfenster is not None and self._zeitfenster.ist_abgelaufen

    @property
    def aktuelle_bearbeitung(self):
        """Die Bearbeitung der laufenden Aufgabe, oder ``None``."""
        return self._bearbeitung

    @property
    def aktuelle_aufgabe(self):
        """Die laufende Aufgabe, oder ``None``."""
        return self._bearbeitung.aufgabe if self._bearbeitung else None

    @property
    def versuche(self):
        """Der Versuchszähler der laufenden Aufgabe – 0, wenn keine läuft."""
        return self._bearbeitung.versuche if self._bearbeitung else 0

    @property
    def erledigte_aufgaben(self):
        """Alle abgeschlossenen Bearbeitungen in der Reihenfolge des Spiels.

        Das ist die Grundlage für das CSV-Logging aus Aufgabe 5.5.
        """
        return tuple(self._erledigt)

    def erledigte_aufgaben_im_level(self, level):
        """Die abgeschlossenen Bearbeitungen eines Levels."""
        return tuple(b for b in self._erledigt if b.aufgabe.level == level)

    # ── Level ──────────────────────────────────────────────────────────────

    def starte_level(self, level):
        """Beginnt den Durchlauf mit diesem Level.

        Das geht **genau einmal**; danach werden die Level der Reihe nach über
        :meth:`naechstes_level` gespielt. Zwei Fehler schliesst das aus:

        * Ein zweiter Start desselben Levels liesse sein Zeitfenster von vorn
          beginnen – aus fünfzehn Minuten würden dreissig, ohne dass es
          jemandem auffiele. Genau so etwas passiert leicht, wenn in Phase 6
          ein Screen neu aufgebaut wird.
        * Ein Sprung nach vorn liesse ein Level ausfallen, und der Durchlauf
          gälte trotzdem als durchgespielt.

        Normalerweise beginnt ein Durchlauf mit Level 1. Ein anderes
        Startlevel ist für Tests und einen Wiedereinstieg nach einem Absturz
        gedacht; so ein Durchlauf gilt nie als :attr:`ist_durchgespielt`.
        """
        if level not in LEVEL:
            raise ValueError(f"Level {level!r} gibt es nicht; erlaubt sind {list(LEVEL)}.")
        if self._gestartete_level:
            raise ValueError(
                f"Der Durchlauf hat schon mit Level {min(self._gestartete_level)} "
                "begonnen. starte_level() gibt es nur einmal; danach werden die "
                "Level der Reihe nach über naechstes_level() gespielt. Ein "
                "zweiter Start liesse ein Zeitfenster von vorn beginnen oder ein "
                "Level ausfallen."
            )
        self._level = level
        self._gestartete_level.add(level)
        self._zeitfenster = _zeitfenster_fuer_level(level, self._zeitgeber)

    def naechstes_level(self):
        """Schaltet zum nächsten Level weiter, oder beendet das Spiel.

        Rückgabe ist das neue Level, oder ``None``, wenn Level 3 vorbei war.

        Projektregel 1: Das geschieht **unabhängig davon, was gerade offen
        ist**. Eine laufende Aufgabe wird nicht verworfen, sondern
        abgeschlossen – ihre Lösung wird eingeblendet und sie landet im Log.
        Sonst liesse sich später nicht unterscheiden, ob jemand eine Aufgabe
        gar nicht bekommen hat oder ob die Zeit um war.
        """
        if self._level is None:
            raise ValueError("Es läuft noch kein Level – zuerst starte_level().")
        if self._bearbeitung is not None:
            self.aufgabe_abschliessen()
        self._levelzeiten[self._level] = (
            self._zeitfenster.verstrichene_sekunden,
            LEVELENDE_ZEITABLAUF if self._zeitfenster.ist_abgelaufen else LEVELENDE_VORZEITIG,
        )
        naechstes = self._level + 1
        self._level = naechstes if naechstes in LEVEL else None
        if self._level is not None:
            self._gestartete_level.add(self._level)
        self._zeitfenster = (
            _zeitfenster_fuer_level(self._level, self._zeitgeber)
            if self._level is not None
            else None
        )
        return self._level

    def level_sekunden(self, level):
        """Wie lange ein Level lief – bei dem laufenden Level: bisher.

        ``None`` für ein Level, das in diesem Durchlauf nie begann. Endete das
        Level am Timer, steht hier die Dauer des Zeitfensters (plus die
        Bruchteile einer Sekunde, bis :meth:`pruefe_zeitfenster` es bemerkte).
        """
        if level in self._levelzeiten:
            return self._levelzeiten[level][0]
        if level == self._level:
            return self._zeitfenster.verstrichene_sekunden
        return None

    def levelende(self, level):
        """Wie ein Level endete: :data:`LEVELENDE_ZEITABLAUF`,
        :data:`LEVELENDE_VORZEITIG` oder – solange es läuft –
        :data:`LEVELENDE_LAEUFT`. ``None``, wenn es nie begann.

        Für die Auswertung entscheidend: Wer vorzeitig fertig war, hatte mehr
        Zeit, als er brauchte; wer am Timer endete, hätte mehr gebraucht.
        """
        if level in self._levelzeiten:
            return self._levelzeiten[level][1]
        if level == self._level:
            return LEVELENDE_LAEUFT
        return None

    def zusatzaufgaben_im_level(self, level=None):
        """Wie viele Zusatzaufgaben in diesem Level schon gestellt wurden."""
        level = level if level is not None else self._level
        return sum(
            1
            for b in self._erledigt
            if b.aufgabe.level == level and b.aufgabe.zusatzaufgabe
        )

    @property
    def zusatzaufgabe_faellig(self):
        """Soll nach der zuletzt erledigten Aufgabe eine Extraaufgabe kommen?

        Aufgabe 5.4: Wer eine Übung deutlich schneller gelöst hat als erwartet
        und noch genug Zeit im Level hat, bekommt eine weitere aus demselben
        Pool. Gefragt wird **nach** dem Abschliessen einer Aufgabe – solange
        schon die nächste läuft, ist nichts fällig.
        """
        if self._level is None or not self._erledigt or self._bearbeitung is not None:
            return False
        zuletzt = self._erledigt[-1]
        if zuletzt.aufgabe.level != self._level:
            return False
        return _zusatzaufgabe_ist_faellig(
            zuletzt, self.verbleibende_sekunden, self.zusatzaufgaben_im_level()
        )

    def pruefe_zeitfenster(self):
        """Schaltet weiter, wenn die Zeit des Levels um ist.

        Rückgabe ist ``True``, wenn dabei gewechselt wurde. Die Oberfläche
        ruft das regelmässig auf; solange Zeit bleibt, passiert nichts.

        Projektregel 1: Gewechselt wird **unabhängig davon, was gerade offen
        ist**. Eine laufende Aufgabe wird dabei abgeschlossen und nicht
        verworfen, damit sie im Log erhalten bleibt.
        """
        if not self.zeit_ist_um:
            return False
        self.naechstes_level()
        return True

    @property
    def ist_durchgespielt(self):
        """Wurden alle Level gespielt und ist das letzte vorbei?

        Gefragt wird, ob alle Level durch sind – nicht, ob dabei Aufgaben
        anfielen. Wer in jedem Level nur zusieht, bis die Zeit abläuft, hat
        das Spiel trotzdem durchlaufen. Wer dagegen erst bei Level 2
        eingestiegen ist, hat es nicht.
        """
        return self._level is None and self._gestartete_level >= set(LEVEL)

    # ── Aufgaben ───────────────────────────────────────────────────────────

    def naechste_uebung(self, zusatzaufgabe=False):
        """Stellt die nächste Handbuch-Übung des laufenden Levels.

        Die Uhr der Aufgabe beginnt hier. Aufrufen, wenn die Aufgabe auf dem
        Bildschirm erscheint – nicht schon, während davor noch ein Text
        gelesen wird.

        ``zusatzaufgabe=True`` markiert eine Extraaufgabe aus 5.4. Über die
        Obergrenze des Levels hinaus gibt es keine; die Grenze gilt hier und
        nicht erst in der Oberfläche.
        """
        self._verlange_level()
        self._verlange_freie_bahn()
        self._verlange_restzeit()
        if zusatzaufgabe and _obergrenze_erreicht(self.zusatzaufgaben_im_level()):
            raise ValueError(
                f"In Level {self._level} gab es schon "
                f"{HOECHSTZAHL_ZUSATZAUFGABEN_JE_LEVEL} Zusatzaufgaben – mehr "
                "gibt es nicht. Vorher zusatzaufgabe_faellig fragen."
            )
        aufgabe = self._generator.naechste_uebung(self._level, zusatzaufgabe=zusatzaufgabe)
        self._bearbeitung = Bearbeitung(aufgabe, self._zeitgeber)
        return aufgabe

    def stelle_funkspruch(self, funkspruch):
        """Stellt einen echten Funkspruch als Aufgabe.

        Er muss zum laufenden Level gehören – sonst käme Bobs Antwort mitten
        in Level 2 oder der Feind-Funkspruch schon in Level 1. Und jeder
        Funkspruch kommt nur einmal: Ein zweites Mal gäbe drei frische
        Versuche und im Log zwei Zeilen mit derselben Kennung.

        Wie bei :meth:`naechste_uebung` beginnt hier die Uhr der Aufgabe.
        """
        self._verlange_level()
        self._verlange_freie_bahn()
        self._verlange_restzeit()
        if funkspruch.level != self._level:
            raise ValueError(
                f"Der Funkspruch {funkspruch.kennung!r} gehört zu Level "
                f"{funkspruch.level}, gerade läuft Level {self._level}."
            )
        if funkspruch.kennung in self._gestellte_funksprueche:
            raise ValueError(
                f"Der Funkspruch {funkspruch.kennung!r} wurde in diesem "
                "Durchlauf schon gestellt. Jeder Funkspruch kommt nur einmal."
            )
        aufgabe = aufgabe_aus_funkspruch(funkspruch, self.figur.initialen)
        self._gestellte_funksprueche.add(funkspruch.kennung)
        self._bearbeitung = Bearbeitung(aufgabe, self._zeitgeber)
        return aufgabe

    def versuchen(self, eingabe):
        """Reicht eine Eingabe an die laufende Aufgabe weiter."""
        self._verlange_aufgabe()
        return self._bearbeitung.versuchen(eingabe)

    def weiterrechnen(self):
        """Drückt den Weiterrechnen-Knopf der laufenden Aufgabe."""
        self._verlange_aufgabe()
        return self._bearbeitung.weiterrechnen()

    def aufgabe_abschliessen(self):
        """Legt die laufende Aufgabe zu den erledigten.

        Ist sie noch nicht beendet – etwa weil das Zeitfenster ablief –, wird
        die Lösung vorher eingeblendet. So steht am Ende jede gestellte
        Aufgabe mit einem klaren Ergebnis im Log.
        """
        self._verlange_aufgabe()
        if not self._bearbeitung.ist_beendet:
            self._bearbeitung.aufgeben()
        self._erledigt.append(self._bearbeitung)
        self._bearbeitung = None

    # ── Innere Hilfen ──────────────────────────────────────────────────────

    def _verlange_level(self):
        if self._level is None:
            raise ValueError("Es läuft kein Level – zuerst starte_level().")

    def _verlange_restzeit(self):
        if self.zeit_ist_um:
            raise ZeitIstUm(
                f"Die Zeit für Level {self._level} ist um – hier wird keine "
                "Aufgabe mehr gestellt. pruefe_zeitfenster() schaltet weiter."
            )

    def _verlange_freie_bahn(self):
        if self._bearbeitung is not None:
            raise ValueError(
                f"Aufgabe {self._bearbeitung.aufgabe.kennung!r} läuft noch. "
                "Zuerst aufgabe_abschliessen() aufrufen – sonst fiele sie aus "
                "dem Log heraus."
            )

    def _verlange_aufgabe(self):
        if self._bearbeitung is None:
            raise ValueError(
                "Es läuft keine Aufgabe – zuerst naechste_uebung() oder "
                "stelle_funkspruch()."
            )

    def __repr__(self):
        laeuft = self.aktuelle_aufgabe.kennung if self.aktuelle_aufgabe else None
        return (
            f"Spielstand({self.pseudonym!r}, figur={self.figur.kennung!r}, "
            f"level={self._level}, aufgabe={laeuft!r}, "
            f"erledigt={len(self._erledigt)})"
        )
