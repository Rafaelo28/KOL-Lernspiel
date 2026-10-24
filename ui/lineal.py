"""Das Lineal im Vigenère-Quadrat (Arbeitsplan 6.7).

Wer von Hand im Quadrat nachschlägt, legt einen Finger oder ein Lineal an die
Zeile und fährt die Spalte hinunter – sonst verrutscht man in 26 × 26 Feldern
leicht um eins. Das Lineal tut dasselbe auf dem Bildschirm:

* Ein Klick links auf einen Buchstaben der Kopfspalte legt es an dessen
  **Zeile** (der Schlüsselbuchstabe), ein Klick oben in der Kopfzeile an die
  **Spalte** (der Buchstabe der Nachricht). Wo sich beide kreuzen, liegt das
  Feld etwas dunkler – wie zwei Textmarker übereinander.
* Ein Klick auf ein Feld legt beide an dieses Feld. So findet man beim
  Entschlüsseln vom gefundenen Geheimbuchstaben den Weg hinauf zum Spaltenkopf.
* Ein zweiter Klick auf denselben Kopf nimmt das Lineal dort wieder weg.

Warum es markiert und nicht abliest
───────────────────────────────────
Das Lineal gibt den Buchstaben am Kreuzungspunkt nicht aus. Das Ablesen im
Quadrat ist genau, was Level 3 übt und misst; die Kontrollgruppe rechnet auf
Papier und darf dort Finger und Lineal benutzen – mehr nicht. Ein Werkzeug,
das den Buchstaben nennt, wäre ein Rechner, und die Messdaten verglichen nicht
mehr Lernspiel und Unterricht, sondern Rechnen mit und ohne Hilfe. Wie oft es
benutzt wurde, steht im Log (``lineal_klicks``).

Das Lineal gibt es nur, wo das Quadrat liegt – in Level 3, von der ersten
Übung an. Das Quadrat selbst zeichnet :mod:`ui.buchleinwand`; das Lineal legt
sich nur darüber.

Dass es das Lineal gibt, muss auffallen
───────────────────────────────────────
Die erste Testperson des Pilotdurchlaufs hat es nicht bemerkt. Deshalb zweierlei:

* :data:`HINWEIS` steht auf beiden Bildschirmen mit Quadrat – auf der
  Übungsseite als rote Notiz über dem Schreibfeld, am Funkgerät in der
  Knopfleiste. Vorher stand der Satz nur klein am unteren Seitenrand, unter
  dem Schreibfeld und unter aller Rückmeldung.
* Bei der **ersten** Aufgabe eines Levels legt sich das Lineal von selbst an
  (:meth:`Lineal.vorzeigen`): Man sieht die beiden Bänder und den dunkleren
  Kreuzungspunkt, ohne etwas gelesen zu haben. Der erste eigene Klick legt es
  um. Gezählt wird das Vorzeigen nicht – ``lineal_klicks`` im Log soll sagen,
  wie oft jemand **selbst** geklickt hat.
"""

import math

from crypto.normalize import ALPHABET
from ui import buchsatz, stil

#: Tag aller Stücke des Lineals auf der Leinwand.
TAG = "lineal"

#: Der Satz, der sagt, dass es das Lineal gibt. Er steht hier und nicht in den
#: Screens: :mod:`ui.uebung` und :mod:`ui.funk` zeigen denselben.
HINWEIS = "Tipp: Klick im Quadrat links auf Zeile und Spalte – dann liegt dein Lineal an!"

#: So weit liegt das vorgezeigte Lineal vom ersten Schritt der Aufgabe weg:
#: dreizehn Felder, also genau gegenüber im Alphabet.
ABSTAND_VORZEIGEN = 13


class Lineal:
    """Das Lineal über dem Quadrat auf einer Seite einer :class:`ui.buchleinwand.Buchleinwand`.

    ``quadrat`` ist das gesetzte Stück (:class:`ui.buchsatz.Quadrat`) auf der
    ``seite``. ``bei_benutzung()`` wird nach jedem Klick aufgerufen, der das
    Lineal bewegt – etwa, um ihn fürs Log zu zählen.
    """

    def __init__(self, leinwand, seite, quadrat, bei_benutzung=None):
        """Merkt sich, über welchem Quadrat das Lineal liegt; gezeichnet ist noch nichts.

        Angelegt wird es erst durch einen Klick (:meth:`klicken`), der
        :attr:`zeile` und :attr:`spalte` setzt.
        """
        self.leinwand = leinwand
        self.seite = seite
        self.quadrat = quadrat
        self._bei_benutzung = bei_benutzung
        #: Die markierte Zeile und Spalte (0 = A) – oder ``None``.
        self.zeile = None
        self.spalte = None

    # ── Wo geklickt wurde ──────────────────────────────────────────────────

    def ziel(self, x, y):
        """Was an dieser Stelle der Leinwand liegt.

        ``("zeile", k)`` in der Kopfspalte, ``("spalte", m)`` in der Kopfzeile,
        ``("feld", k, m)`` im Quadrat – sonst ``None``, auch in der leeren Ecke
        oben links.
        """
        x0, y0, _, _ = self.leinwand.flaeche(self.seite)
        feld = self.quadrat.feld
        spalte = math.floor((x - x0 - self.quadrat.x) / feld) - 1
        zeile = math.floor((y - y0 - self.quadrat.y) / feld) - 1
        if not (-1 <= zeile < 26 and -1 <= spalte < 26) or zeile == spalte == -1:
            return None
        if zeile == -1:
            return ("spalte", spalte)
        if spalte == -1:
            return ("zeile", zeile)
        return ("feld", zeile, spalte)

    def klicken(self, x, y):
        """Ein Klick auf die Leinwand. ``True``, wenn er das Lineal bewegt hat."""
        ziel = self.ziel(x, y)
        if ziel is None:
            return False
        if ziel[0] == "zeile":
            self.zeile = None if self.zeile == ziel[1] else ziel[1]
        elif ziel[0] == "spalte":
            self.spalte = None if self.spalte == ziel[1] else ziel[1]
        else:
            self.zeile, self.spalte = ziel[1], ziel[2]
        self.zeichnen()
        if self._bei_benutzung is not None:
            self._bei_benutzung()
        return True

    def vorzeigen(self, feld):
        """Legt das Lineal von selbst an ``feld`` – damit zu sehen ist, dass es das gibt.

        Gedacht für die erste Aufgabe eines Levels (siehe Modulkopf). Anders
        als :meth:`klicken` ruft das **nicht** ``bei_benutzung()``: Im Log
        soll stehen, wie oft jemand selbst geklickt hat, nicht, wie oft das
        Spiel etwas vorgemacht hat.
        """
        self.zeile, self.spalte = feld
        self.zeichnen()

    # ── Zeichnen ───────────────────────────────────────────────────────────

    def zeichnen(self):
        """Legt das Lineal neu an: Zeile und Spalte über das ganze Quadrat, der Kreuzungspunkt dunkler."""
        leinwand = self.leinwand
        leinwand.delete(f"{TAG}&&{self.seite}")
        x0, y0, _, _ = leinwand.flaeche(self.seite)
        feld, kante = self.quadrat.feld, self.quadrat.kante
        links, oben = x0 + self.quadrat.x, y0 + self.quadrat.y
        marken = (self.seite, TAG)
        elemente = []
        if self.zeile is not None:
            y = oben + (self.zeile + 1) * feld
            elemente.append(leinwand.create_rectangle(links, y, links + kante, y + feld, width=0,
                                                      fill=stil.FARBE_MARKIERUNG, tags=marken + ("linealzeile",)))
        if self.spalte is not None:
            x = links + (self.spalte + 1) * feld
            elemente.append(leinwand.create_rectangle(x, oben, x + feld, oben + kante, width=0,
                                                      fill=stil.FARBE_MARKIERUNG, tags=marken + ("linealspalte",)))
        if self.zeile is not None and self.spalte is not None:
            x, y = links + (self.spalte + 1) * feld, oben + (self.zeile + 1) * feld
            elemente.append(leinwand.create_rectangle(x, y, x + feld, y + feld, width=0,
                                                      fill=stil.FARBE_KREUZUNG, tags=marken + ("linealkreuzung",)))
        # Über den dunkleren Grund von Kopfzeile und Kopfspalte, unter die Buchstaben.
        leinwand.unterlegen(self.seite, "kopfzeile", elemente)


def anlegen(leinwand, seite, stuecke, bei_benutzung=None):
    """Legt ein Lineal an, wenn unter den ``stuecke`` der Seite das Quadrat ist – sonst ``None``.

    Klicks auf die Leinwand bewegen es, und über dem Quadrat zeigt der
    Mauszeiger eine Hand.
    """
    quadrate = [stueck for stueck in stuecke if isinstance(stueck, buchsatz.Quadrat)]
    if not quadrate:
        return None
    lineal = Lineal(leinwand, seite, quadrate[0], bei_benutzung=bei_benutzung)
    leinwand.bind("<Button-1>", lambda ereignis: lineal.klicken(ereignis.x, ereignis.y))
    leinwand.bind("<Motion>", lambda ereignis: leinwand.configure(
        cursor="hand2" if lineal.ziel(ereignis.x, ereignis.y) else ""))
    return lineal


def erster_schritt(aufgabe):
    """Zeile und Spalte, mit denen eine Vigenère-Aufgabe im Quadrat anfängt.

    Die Zeile ist der erste Buchstabe des Schlüsselworts, die Spalte der erste
    Buchstabe der angezeigten Nachricht. ``None``, wenn sich das nicht sagen
    lässt – ohne Aufgabe (ein Funkspruch zum Mitlesen) oder in einem Level,
    dessen Schlüssel kein Wort ist.
    """
    if aufgabe is None:
        return None
    schluessel = str(aufgabe.schluessel or "").strip()
    text = (aufgabe.anzeigetext or "").replace(" ", "")
    if not schluessel or not text:
        return None
    if schluessel[0] not in ALPHABET or text[0] not in ALPHABET:
        return None
    return (ALPHABET.index(schluessel[0]), ALPHABET.index(text[0]))


def vorzeigefeld(erster_schritt_der_aufgabe=None):
    """Wo das Lineal liegt, wenn es sich selbst vorstellt.

    Ohne Aufgabe links oben (A/A). Sonst dreizehn Zeilen und dreizehn Spalten
    weiter, also genau gegenüber im Alphabet: Das Lineal soll zeigen, *dass*
    es sich anlegen lässt, und nicht den ersten Nachschlageschritt
    verschenken. Eine schon markierte Zeile wäre die halbe Arbeit – und
    gerechnet werden soll von Hand (siehe Modulkopf).

    >>> vorzeigefeld()
    (0, 0)
    >>> vorzeigefeld((0, 0))
    (13, 13)
    >>> vorzeigefeld((17, 7))
    (4, 20)
    """
    if erster_schritt_der_aufgabe is None:
        return (0, 0)
    zeile, spalte = erster_schritt_der_aufgabe
    return ((zeile + ABSTAND_VORZEIGEN) % len(ALPHABET), (spalte + ABSTAND_VORZEIGEN) % len(ALPHABET))
