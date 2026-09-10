"""Versuchszähler und Lösungsanzeige (Arbeitsplan 4.3).

Eine :class:`Bearbeitung` begleitet **eine** Aufgabe von der ersten Eingabe bis
zum Ende. Sie zählt die Fehlversuche, blendet nach dreien die Lösung ein und
weiss, wann der Weiterrechnen-Knopf erscheinen darf.

Warum das ein eigenes Objekt ist
────────────────────────────────
Der Versuchszähler ist die Stelle, an der das Spiel blockieren kann. Läge er
in der Oberfläche, gäbe es ihn dreimal – einmal je Screen – und an einer der
drei Stellen würde die Regel früher oder später fehlen. Genau davor warnt
Projektregel 2: Ohne die Lösungsanzeige hängt das Spiel an Bobs zwei
Funksprüchen fest, und die sind story-tragend.

Die Regeln
──────────
* **Drei Fehlversuche ohne Fortschritt, dann die Lösung.**
  :data:`HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT` steht an genau einer Stelle.

  Entscheidend ist das "ohne Fortschritt". Wer bei einem langen Funkspruch
  vier Buchstaben verzählt hat und sie einen nach dem anderen ausbessert,
  braucht vier Versuche – mit einem harten Limit von drei bekäme ausgerechnet
  diese Person die Lösung vorgesetzt, obwohl sie die Methode verstanden hat
  und nur langsam war. In den Messdaten sähe das aus wie "nicht gekonnt".

  Deshalb: Eine Eingabe, die **weniger Fehler** hat als die beste bisher,
  kostet keinen Versuch. Die Strähne beginnt bei jedem Fortschritt von vorn.
  Wer dreimal hintereinander nicht weiterkommt, bekommt die Lösung.

  Das läuft nicht endlos: Jeder Fortschritt senkt die Fehlerzahl um
  mindestens eins, und mehr Fehler als Buchstaben kann eine Antwort nicht
  haben. Nach oben begrenzt ist die Sache also von selbst – und zusätzlich
  durch das feste Zeitfenster des Levels (Projektregel 1).
* **Gilt für alles.** Handbuch-Übungen und echte Funksprüche, Bobs beide
  Nachrichten eingeschlossen. Ein Test spielt alle fünf Funksprüche mit lauter
  Fehleingaben durch und prüft, dass keiner blockiert.
* **Eine leere Eingabe zählt nicht.** Wer auf "Prüfen" drückt, ohne etwas
  einzugeben, hat es nicht versucht (siehe :mod:`game.pruefung`). Sonst wären
  nach drei Fehlklicks die Versuche verbraucht.
* **Nach dem Ende zählt nichts mehr.** Ist die Aufgabe gelöst oder die Lösung
  angezeigt, ändern weitere Eingaben den Zähler nicht mehr. Das Log soll
  festhalten, wie viele Versuche bis zur Entscheidung nötig waren, nicht wie
  oft danach noch getippt wurde.

Der Weiterrechnen-Knopf (Arbeitsplan 4.4)
─────────────────────────────────────────
Bei den drei langen Funksprüchen erscheint er, sobald der geprüfte Anfang
richtig ist **oder** die Lösung angezeigt wurde. Nur bei richtiger Lösung
würde das Spiel an denselben Stellen wieder festhängen, an denen die
3-Versuche-Regel es gerade freigemacht hat.

:meth:`Bearbeitung.weiterrechnen` ist der Druck auf diesen Knopf. Er liefert
den Erzähltext ("Zwanzig Minuten später …") und gibt die vollständige
Nachricht frei. Die Erzählzeit darin ist reine Fiktion – der Level-Timer aus
Aufgabe 5.2 läuft unverändert weiter, dieses Modul rührt ihn nicht an.

Erst danach ist die Aufgabe wirklich fertig. Dafür gibt es zwei getrennte
Merkmale: :attr:`ist_beendet` heisst "die Prüfung ist vorbei",
:attr:`ist_abgeschlossen` heisst "auch der Rest liegt vor". Bei Aufgaben ohne
Teilaufgabe fallen beide zusammen.

Was für das Log herausfällt (Arbeitsplan 5.5)
─────────────────────────────────────────────
:attr:`Bearbeitung.versuche` (alle falschen Eingaben),
:attr:`Bearbeitung.versuche_ohne_fortschritt` (davon die, die gegen das
Kontingent zählten), :attr:`Bearbeitung.loesung_angezeigt` und
:attr:`game.aufgabe.Aufgabe.laenge_in_buchstaben`.

Beide Zahlen zu haben lohnt sich für die Auswertung: "acht Versuche, davon
keiner ohne Fortschritt" ist etwas ganz anderes als "drei Versuche, alle ohne
Fortschritt", auch wenn beide am Ende gelöst haben.
"""

from typing import NamedTuple

from game.pruefung import pruefe
from game.rueckmeldung import fehlerzahl_der_aufgabe, rueckmeldung

#: Nach so vielen Fehlversuchen **ohne Fortschritt** wird die Lösung
#: eingeblendet (Projektregel 2). Die Zahl steht bewusst an genau einer
#: Stelle im Projekt und wird nach dem Pilotdurchlauf gegebenenfalls
#: angepasst.
HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT = 3

#: Satz, der erscheint, wenn eine Eingabe zwar falsch war, aber besser als
#: alles bisher. Er macht sichtbar, dass dieser Versuch nichts gekostet hat.
HINWEIS_FORTSCHRITT = (
    "Du bist näher dran als vorher – dieser Versuch zählt nicht mit."
)


class Weiterrechnen(NamedTuple):
    """Was nach dem Druck auf den Weiterrechnen-Knopf angezeigt wird.

    ``erzaehltext``           die Figur rechnet zu Ende ("Zwanzig Minuten später …")
    ``vollstaendige_nachricht`` die ganze Lösung, jetzt sichtbar
    ``rest``                  nur der Teil, der eben dazugekommen ist
    """

    erzaehltext: str
    vollstaendige_nachricht: str
    rest: str


class Versuchsergebnis(NamedTuple):
    """Was nach einer Eingabe gilt – anzeigefertig für die Oberfläche.

    ``richtig``              Die Aufgabe ist gelöst.
    ``meldung``              Der Satz aus :mod:`game.rueckmeldung`, leer bei
                             richtiger Lösung.
    ``zaehlte_als_versuch``  Hat diese Eingabe einen Versuch gekostet?
    ``fortschritt``          War sie besser als alles bisher?
    ``hinweis_fortschritt``  Satz dazu, sonst leer.
    ``fehlerzahl``           Wie viele Buchstaben noch nicht stimmen.
    ``versuche``             Wie viele falsche Eingaben es bisher gab.
    ``verbleibende_versuche``Wie viele Versuche ohne Fortschritt noch bleiben.
    ``loesung_angezeigt``    Die Lösung steht jetzt auf dem Bildschirm.
    ``angezeigte_loesung``   Sie selbst, sonst leer.
    ``darf_abgeschickt_werden`` Regel 4.1.
    ``darf_weiterrechnen``   Der Knopf für den Rest der Nachricht ist da.
    ``ist_beendet``          Die Aufgabe ist erledigt – gelöst oder aufgelöst.
    """

    richtig: bool
    meldung: str
    zaehlte_als_versuch: bool
    fortschritt: bool
    hinweis_fortschritt: str
    fehlerzahl: int
    versuche: int
    verbleibende_versuche: int
    loesung_angezeigt: bool
    angezeigte_loesung: str
    darf_abgeschickt_werden: bool
    darf_weiterrechnen: bool
    ist_beendet: bool


class Bearbeitung:
    """Der Verlauf einer einzelnen Aufgabe.

    >>> from game.aufgabe import Aufgabe, VERSCHLUESSELN
    >>> a = Aufgabe("probe", 1, "caesar", VERSCHLUESSELN, 3, "HUND", "KXQG")
    >>> lauf = Bearbeitung(a)
    >>> lauf.versuche, lauf.verbleibende_versuche
    (0, 3)

    Eine leere Eingabe kostet nichts:

    >>> lauf.versuchen("").zaehlte_als_versuch
    False
    >>> lauf.versuche
    0

    Drei Fehlversuche ohne Fortschritt, dann steht die Lösung da:

    >>> [lauf.versuchen(falsch).versuche for falsch in ("KXQA", "KXQB", "KXQC")]
    [1, 2, 3]
    >>> lauf.loesung_angezeigt, lauf.angezeigte_loesung
    (True, 'KXQG')

    Wer sich dagegen verbessert, behält seine Versuche:

    >>> b = Aufgabe("probe", 2, "substitution", VERSCHLUESSELN, None,
    ...             "ZEIT WIRD KNAPP", "MTOY VOKR AFQHH")
    >>> lauf = Bearbeitung(b)
    >>> for eingabe in ("AAAA AAAA AAAAA", "MTOY AAAA AAAAA", "MTOY VOKR AAAAA"):
    ...     _ = lauf.versuchen(eingabe)
    >>> lauf.versuche, lauf.versuche_ohne_fortschritt, lauf.loesung_angezeigt
    (3, 0, False)
    """

    def __init__(self, aufgabe):
        self.aufgabe = aufgabe
        self._versuche = 0
        self._geloest = False
        self._loesung_angezeigt = False
        self._vollstaendig_geloest = False
        self._rest_freigegeben = False
        self._ohne_fortschritt = 0
        self._beste_fehlerzahl = None

    # ── Zustand ────────────────────────────────────────────────────────────

    @property
    def versuche(self):
        """Alle falschen, nicht leeren Eingaben – die Zahl fürs Log."""
        return self._versuche

    @property
    def versuche_ohne_fortschritt(self):
        """Wie viele Versuche hintereinander nichts gebracht haben.

        Diese Zahl entscheidet über die Lösungsanzeige, nicht
        :attr:`versuche`. Jeder Fortschritt setzt sie auf null zurück.
        """
        return self._ohne_fortschritt

    @property
    def beste_fehlerzahl(self):
        """Die wenigsten Fehler, die bisher erreicht wurden.

        ``None``, solange noch nichts eingegeben wurde.
        """
        return self._beste_fehlerzahl

    @property
    def verbleibende_versuche(self):
        """Wie viele Versuche ohne Fortschritt noch bleiben.

        Ist die Aufgabe beendet, sind es keine mehr – auch wenn sie über
        :meth:`aufgeben` beendet wurde und der Zähler nie hochgelaufen ist.
        Sonst stünde auf einer erledigten Aufgabe "noch 3 Versuche".
        """
        if self.ist_beendet:
            return 0
        return max(0, HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT - self._ohne_fortschritt)

    @property
    def geloest(self):
        return self._geloest

    @property
    def vollstaendig_geloest(self):
        """Wurde die ganze Nachricht gerechnet, nicht nur die Teilaufgabe?"""
        return self._vollstaendig_geloest

    @property
    def loesung_angezeigt(self):
        return self._loesung_angezeigt

    @property
    def angezeigte_loesung(self):
        """Die Lösung, solange sie eingeblendet ist – sonst leer.

        Gezeigt wird bei einer Teilaufgabe nur deren Anfang. Der Rest kommt
        über den Weiterrechnen-Knopf, genau wie beim richtigen Lösen.
        """
        return self.aufgabe.loesung if self._loesung_angezeigt else ""

    @property
    def ist_beendet(self):
        """Die Aufgabe ist erledigt – gelöst oder aufgelöst.

        Diese Eigenschaft ist die Zusicherung gegen das Blockieren: Sie wird
        für **jede** Aufgabe wahr, spätestens nach drei Versuchen **ohne
        Fortschritt**. Weil jeder Fortschritt die Fehlerzahl um mindestens
        eins senkt und eine Antwort nicht mehr Fehler haben kann als
        Buchstaben, ist auch das nach oben begrenzt.
        """
        return self._geloest or self._loesung_angezeigt

    @property
    def rest_freigegeben(self):
        """Wurde der Weiterrechnen-Knopf schon gedrückt?"""
        return self._rest_freigegeben

    @property
    def ist_abgeschlossen(self):
        """Die Aufgabe ist ganz fertig – bei Teilaufgaben inklusive Rest.

        Unterschied zu :attr:`ist_beendet`: Dort ist nur die *Prüfung* vorbei.
        Solange der Rest der Nachricht noch hinter dem Knopf steckt, ist die
        Geschichte nicht weitergegangen.
        """
        if not self.ist_beendet:
            return False
        return self._rest_freigegeben or not self.aufgabe.hat_teilaufgabe

    @property
    def sichtbare_nachricht(self):
        """Was von der Nachricht zu sehen ist.

        Vor dem Knopf nur die Teilaufgabe (und auch die erst, wenn sie gelöst
        oder aufgelöst wurde), danach die ganze Nachricht.
        """
        if self._rest_freigegeben:
            return self.aufgabe.vollstaendige_loesung
        if self.ist_beendet:
            return self.aufgabe.loesung
        return ""

    @property
    def knopf_beschriftung(self):
        """Die Aufschrift des Knopfes – leer, solange er nicht da ist."""
        return self.aufgabe.knopf_beschriftung if self.darf_weiterrechnen else ""

    @property
    def darf_weiterrechnen(self):
        """Erscheint der Knopf für den Rest der Nachricht?

        Nur bei Aufgaben mit Teilaufgabe, und dort sobald sie erledigt ist –
        richtig gelöst **oder** aufgelöst. Ohne das zweite würde das Spiel an
        denselben Stellen wieder festhängen.

        Nach dem Druck ist er weg: Es gibt nichts mehr aufzulösen.
        """
        return (
            self.aufgabe.hat_teilaufgabe
            and self.ist_beendet
            and not self._rest_freigegeben
        )

    # ── Eingabe ────────────────────────────────────────────────────────────

    def versuchen(self, eingabe):
        """Nimmt eine Eingabe entgegen und gibt das Ergebnis zurück."""
        ergebnis = pruefe(self.aufgabe, eingabe)
        zaehlt = ergebnis.zaehlt_als_versuch and not self.ist_beendet
        fehler = fehlerzahl_der_aufgabe(self.aufgabe, eingabe)
        fortschritt = False

        if zaehlt:
            self._versuche += 1
            # Fortschritt heisst: weniger Fehler als je zuvor. Der Vergleich
            # geht gegen das bisherige Beste, nicht gegen den letzten Versuch –
            # sonst liesse sich die Strähne durch Hin- und Herändern beliebig
            # zurücksetzen, ohne wirklich voranzukommen.
            fortschritt = (
                self._beste_fehlerzahl is not None and fehler < self._beste_fehlerzahl
            )
            if self._beste_fehlerzahl is None or fehler < self._beste_fehlerzahl:
                self._beste_fehlerzahl = fehler
            if fortschritt:
                self._ohne_fortschritt = 0
            else:
                self._ohne_fortschritt += 1
                if self._ohne_fortschritt >= HOECHSTZAHL_VERSUCHE_OHNE_FORTSCHRITT:
                    self._loesung_angezeigt = True

        if ergebnis.richtig and not self.ist_beendet:
            self._geloest = True
            self._vollstaendig_geloest = ergebnis.vollstaendig_geloest
        elif ergebnis.richtig:
            # Nach dem Auflösen darf man die Lösung natürlich noch eintippen.
            self._geloest = True

        return Versuchsergebnis(
            richtig=ergebnis.richtig,
            meldung=rueckmeldung(self.aufgabe, eingabe),
            zaehlte_als_versuch=zaehlt,
            fortschritt=fortschritt,
            hinweis_fortschritt=HINWEIS_FORTSCHRITT if fortschritt else "",
            fehlerzahl=fehler,
            versuche=self._versuche,
            verbleibende_versuche=self.verbleibende_versuche,
            loesung_angezeigt=self._loesung_angezeigt,
            angezeigte_loesung=self.angezeigte_loesung,
            darf_abgeschickt_werden=ergebnis.darf_abgeschickt_werden,
            darf_weiterrechnen=self.darf_weiterrechnen,
            ist_beendet=self.ist_beendet,
        )

    def weiterrechnen(self):
        """Der Druck auf den Weiterrechnen-Knopf (Arbeitsplan 4.4).

        Gibt den Rest der Nachricht frei und liefert den Erzähltext dazu.
        Zweimal drücken geht nicht – der Knopf verschwindet danach.

        Der Level-Timer wird dabei **nicht** angehalten oder verlängert. Die
        "zwanzig Minuten" im Erzähltext sind Geschichte, keine Spielzeit
        (Projektregel 1: die Zeitfenster sind fix).
        """
        if not self.darf_weiterrechnen:
            raise ValueError(
                f"Aufgabe {self.aufgabe.kennung!r}: Es gibt hier nichts "
                "weiterzurechnen. Der Knopf erscheint erst, wenn die "
                "Teilaufgabe gelöst oder aufgelöst ist, und nur einmal."
            )
        self._rest_freigegeben = True
        return Weiterrechnen(
            erzaehltext=self.aufgabe.weiterrechnen_text,
            vollstaendige_nachricht=self.aufgabe.vollstaendige_loesung,
            rest=self.aufgabe.rest_der_loesung,
        )

    def aufgeben(self):
        """Blendet die Lösung sofort ein, ohne weitere Versuche.

        Gebraucht, wenn das Zeitfenster eines Levels abläuft (Projektregel 1):
        Dann wird weitergeschaltet, egal was offen ist – die Aufgabe darf dann
        nicht als "noch offen" im Log stehen bleiben.
        """
        self._loesung_angezeigt = True

    def __repr__(self):
        return (
            f"Bearbeitung({self.aufgabe.kennung!r}, versuche={self._versuche}, "
            f"geloest={self._geloest}, loesung_angezeigt={self._loesung_angezeigt}, "
            f"rest_freigegeben={self._rest_freigegeben})"
        )
