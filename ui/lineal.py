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
"""

import math

from ui import stil

#: Tag aller Stücke des Lineals auf der Leinwand.
TAG = "lineal"


class Lineal:
    """Das Lineal über dem Quadrat auf einer Seite einer :class:`ui.buchleinwand.Buchleinwand`.

    ``quadrat`` ist das gesetzte Stück (:class:`ui.buchsatz.Quadrat`) auf der
    ``seite``. ``bei_benutzung()`` wird nach jedem Klick aufgerufen, der das
    Lineal bewegt – etwa, um ihn fürs Log zu zählen.
    """

    def __init__(self, leinwand, seite, quadrat, bei_benutzung=None):
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
