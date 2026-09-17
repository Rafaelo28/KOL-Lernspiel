"""Der Abschluss (Arbeitsplan 6.8): Warten, Einschlafen, die Rettung.

Nach Bobs letzter Antwort ("Verstanden, Hilfe ist unterwegs") liegt man im
**Nachtlager** in den Dünen: Feuer, Rucksack, das ausgeschaltete Funkgerät,
darüber der Sternenhimmel (``grafik/nachtlager.svg``). Oben links steht, dass
man wartet – und unten rechts der Knopf "Warten".

Dann fallen die Augen zu. Zwei Lider schieben sich über das Bild, öffnen sich
noch zweimal halb, wie wenn man gegen den Schlaf ankämpft, und schließen sich.
Auf Schwarz steht "Die Nacht vergeht." Wenn sie sich wieder öffnen, liegt
dieselbe Stelle im **Morgengrauen** da (``grafik/morgen.svg``), das Feuer ist
aus – und ein Geräusch kommt näher. Der **Hubschrauber**
(``grafik/hubschrauber.svg``) fliegt von rechts ein und landet auf dem Sand
neben dem Lager. Nach "Weiter" folgt der Schlusstext aus dem Konzept: lebend,
aber mit leeren Händen – die Diamanten bleiben in der Wüste.

Freunde, keine Verfolger
────────────────────────
Gejagt wird die Crew von Polizei, CIA und Interpol. Ein Hubschrauber am Ende
könnte deshalb erst einmal wie eine Festnahme aussehen. Damit das nicht
passiert, sagen es Bild und Text: Der Hubschrauber ist dunkelgrün mit
Goldstreifen statt in Polizeifarben, auf seiner Seite glänzt groß ein goldener
Diamant – das Zeichen der Crew –, ein grünes Licht blinkt, jemand winkt aus
der offenen Tür, und der Text beginnt mit "Das ist nicht die Polizei".

Wie der Ablauf gebaut ist
─────────────────────────
Alles nach dem Warten-Knopf hängt an einer Uhr in Millisekunden (Konstanten
unten): wie weit die Augen zu sind, wann die Szene wechselt, wo der
Hubschrauber gerade ist. :meth:`Abschluss.zu_zeit` stellt jeden Moment her,
auch mit einem Sprung dorthin; der Takt liest nur die Uhr ab. Auf einem
langsamen Schulrechner werden so Bilder übersprungen, aber die Rettung dauert
nicht länger – und im Test lässt sich jeder Augenblick direkt ansteuern.

Die Augenlider zeichnet das Spiel selbst: zwei Flächen mit gebogener Kante,
zusammen eine Öffnung wie ein Auge. Das kostet nichts und braucht keine
Bilder. Der Text liegt über den Lidern – er erzählt, was gerade passiert, und
muss auch mit halb geschlossenen Augen lesbar bleiben.

Die Messdaten
─────────────
Beim Wechsel ins Spielende ist der Durchlauf schon gespeichert. Am Ende steht
unten links klein, wo die Datei liegt – für die Lehrkraft, die sie einsammelt
(Arbeitsplan 8.4). Passt der Pfad nicht in die Zeile, wird er vorn gekürzt:
Ordner und Dateiname am Ende sind das, was man sucht.
"""

import time
import tkinter as tk
import tkinter.font as tkfont

from content import story
from ui import stil
from ui.animation import Animation, Buehne, Figur
from ui.screen import Screen

#: Die beiden Szenen und der Hubschrauber (content/animationen/).
ABEND, MORGEN, HUBSCHRAUBER = "nachtlager", "morgen", "hubschrauber"

#: Wo der Erzähltext steht: im Himmel oben links – rechts fliegt der
#: Hubschrauber ein. Pixel im Maßstab 1, wie alle festen Grössen (ui/stil.py).
TEXT_X, TEXT_Y, TEXT_BREITE = 24, 20, 400

#: Aufschriften der Knöpfe.
KNOPF_WARTEN = story.BESCHRIFTUNG_WARTEN
KNOPF_WEITER = "Weiter"
KNOPF_BEENDEN = "Spiel beenden"

#: Unten links, wenn Level 3 am Timer endete.
HINWEIS_ZEITABLAUF = "Die Zeit für Level 3 ist abgelaufen."
#: Unten links am Ende – für die Lehrkraft.
HINWEIS_MESSDATEN = "Die Messdaten sind gespeichert: {pfad}"

#: Wie weit die Augen zu sind (0 offen, 1 geschlossen) – zu welcher Zeit nach
#: dem Warten-Knopf, in Millisekunden. Zweimal kämpft man noch dagegen an,
#: beim Aufwachen blinzelt man einmal.
LIDER = ((0, 0.0), (1200, 0.55), (1900, 0.3), (3000, 0.8), (3800, 0.5), (5500, 1.0),
         (8500, 1.0), (9400, 0.6), (10000, 0.85), (11500, 0.0))
#: Die Augen sind zu: Auf Schwarz steht, dass die Nacht vergeht.
NACHT = 5500
#: Hinter den geschlossenen Augen wird es Morgen.
MORGEN_BEGINNT = 8000
#: Das Geräusch, das weckt.
GERAEUSCH = 8500
#: Der Flug des Hubschraubers: die linke obere Ecke seines Bilds (Pixel im
#: Maßstab 1) zu diesen Zeiten – von rechts außerhalb herein, dann senkrecht
#: hinunter auf den Sand.
FLUG = ((10000, (980, 50)), (13000, (470, 104)), (15000, (470, 340)))
#: So tief unter der Oberkante seines Bilds stehen die Kufen (Pixel im Maßstab 1).
KUFEN = 136
#: Erst unter dieser Höhe über dem Boden wirft er einen Schatten auf den Sand
#: neben dem Lager – im Sinkflug (Pixel im Maßstab 1).
SCHATTEN_AB = 230
#: Gelandet – der Text zur Rettung und der Knopf "Weiter".
GELANDET = FLUG[-1][0]
#: Takt, in dem die Uhr abgelesen wird, in Millisekunden.
TAKT_MS = 30

#: Die Farbe der Augenlider – fast schwarz.
FARBE_LID = "#050508"
#: Der Schatten des Hubschraubers auf dem Morgensand.
FARBE_BODENSCHATTEN = "#b98263"
#: Aus so vielen Strecken besteht die Kante eines Lids.
KANTENSTUECKE = 48


def zwischenwert(stuetzstellen, zeit):
    """Der Wert zwischen zwei Stützstellen ``(zeit, wert)`` – weich angefahren und abgebremst.

    Werte sind Zahlen oder Paare. Vor der ersten und nach der letzten
    Stützstelle gilt deren Wert. Zwischen (0, 0.0) und (100, 1.0) liegt bei 50
    also 0.5, bei 25 aber nur 0.15625 – es geht langsam los.
    """
    if zeit <= stuetzstellen[0][0]:
        return stuetzstellen[0][1]
    for (t0, w0), (t1, w1) in zip(stuetzstellen, stuetzstellen[1:]):
        if zeit <= t1:
            f = (zeit - t0) / (t1 - t0)
            f = f * f * (3 - 2 * f)
            if isinstance(w0, tuple):
                return tuple(a + (b - a) * f for a, b in zip(w0, w1))
            return w0 + (w1 - w0) * f
    return stuetzstellen[-1][1]


def vorne_kuerzen(text, passt):
    """Kürzt ``text`` von vorn, bis ``passt(text)`` zustimmt – das Ende bleibt stehen.

    Für einen Dateipfad ist das Ende das Wichtigste: Ordner und Dateiname. Aus
    "C:/Spiel/logs/datei.csv" wird bei höchstens zwölf Zeichen "…s/datei.csv".
    """
    if passt(text):
        return text
    for anfang in range(1, len(text) - 1):
        gekuerzt = "…" + text[anfang:]
        if passt(gekuerzt):
            return gekuerzt
    return "…" + text[-1:]


class Abschluss(Screen):
    """Das Ende des Spiels. ``durch_zeitablauf`` sagt, ob Level 3 am Timer endete."""

    titel = "Die Rettung"

    def __init__(self, fenster, durch_zeitablauf=False, zeitgeber=time.monotonic):
        super().__init__(fenster)
        self.configure(bg=stil.FARBE_NACHT)
        self._zeitgeber = zeitgeber
        #: "abend" (vor dem Warten), "nacht" (die Uhr läuft), "gerettet", "ende".
        self.phase = "abend"
        self.zeit_ms = None
        self._beginn = None
        self._erledigt = set()
        self.hubschrauber = None

        # Von unten nach oben: Szene, Schatten des Hubschraubers (er selbst
        # kommt später darüber), Lider, Erzähltext, "Die Nacht vergeht."
        self.buehne = Buehne(self, Animation(ABEND, massstab=self.massstab), bg=stil.FARBE_NACHT)
        self.buehne.pack()
        breite, hoehe = self.buehne.animation.breite, self.buehne.animation.hoehe
        self._bodenschatten = self.buehne.create_oval(0, 0, 0, 0, fill=FARBE_BODENSCHATTEN, outline="",
                                                      state="hidden")
        self._lid_oben = self.buehne.create_polygon(0, 0, 0, 0, 0, 0, fill=FARBE_LID, outline="")
        self._lid_unten = self.buehne.create_polygon(0, 0, 0, 0, 0, 0, fill=FARBE_LID, outline="")
        x, y, versatz = self.px(TEXT_X), self.px(TEXT_Y), self.px(2)
        schrift = dict(anchor="nw", width=self.px(TEXT_BREITE), font=stil.SCHRIFT_ERZAEHLUNG)
        self._schatten = self.buehne.create_text(x + versatz, y + versatz, fill=stil.FARBE_SCHATTEN, **schrift)
        self._text = self.buehne.create_text(x, y, fill=stil.FARBE_SAND, **schrift)
        self._nachttext = self.buehne.create_text(breite // 2, hoehe // 2, anchor="center", state="hidden",
                                                  font=stil.SCHRIFT_ERZAEHLUNG, fill=stil.FARBE_SAND,
                                                  text=story.EINSCHLAFEN.absaetze[1])
        self.lider(0.0)
        self._text_setzen(story.NACHTHIMMEL.absaetze)

        leiste = tk.Frame(self, bg=stil.FARBE_NACHT)
        leiste.pack(fill="x", pady=(self.px(stil.ABSTAND // 2), 0))
        # Der Knopf zuerst: Er bekommt seinen Platz, der Hinweis den Rest.
        self._knopf = tk.Button(leiste, text=KNOPF_WARTEN, command=self.warten,
                                highlightbackground=stil.FARBE_NACHT)
        self._knopf.pack(side="right")
        self._knopf.bind("<Return>", lambda _ereignis: self._knopf.invoke())
        self._hinweis = tk.Label(leiste, bg=stil.FARBE_NACHT, fg=stil.FARBE_DUENE, anchor="w",
                                 text=HINWEIS_ZEITABLAUF if durch_zeitablauf else "")
        self._hinweis.pack(side="left", fill="x", expand=True)

    # ── Was dasteht ────────────────────────────────────────────────────────

    @property
    def text(self):
        """Der Erzähltext über der Szene."""
        return self.buehne.itemcget(self._text, "text")

    @property
    def knopftext(self):
        return self._knopf.cget("text")

    @property
    def knopf_bereit(self):
        return self._knopf.cget("state") != "disabled"

    @property
    def hinweis(self):
        """Die kleine Zeile unten links."""
        return self._hinweis.cget("text")

    @property
    def nachttext_sichtbar(self):
        return self.buehne.itemcget(self._nachttext, "state") != "hidden"

    @property
    def bodenschatten(self):
        """Der Schatten des Hubschraubers als (links, oben, rechts, unten) – ``None``, solange keiner fällt."""
        if self.buehne.itemcget(self._bodenschatten, "state") == "hidden":
            return None
        return tuple(self.buehne.coords(self._bodenschatten))

    def lidkanten(self):
        """Die Unterkante des oberen und die Oberkante des unteren Lids – je als Punkte (x, y) von links nach rechts."""
        def kante(element):
            werte = self.buehne.coords(element)[2:-2]
            return list(zip(werte[::2], werte[1::2]))
        return kante(self._lid_oben), kante(self._lid_unten)

    # ── Zeichnen ───────────────────────────────────────────────────────────

    def _text_setzen(self, absaetze):
        text = "\n\n".join(absaetze)
        self.buehne.itemconfigure(self._schatten, text=text)
        self.buehne.itemconfigure(self._text, text=text)

    def lider(self, zu):
        """Legt die Augenlider über die Szene – ``zu`` von 0 (offen) bis 1 (geschlossen).

        Die Kanten sind Parabelbögen, zusammen eine Öffnung wie ein Auge. Die
        Öffnung ist breiter als das Bild, damit offen auch die Ecken frei sind;
        geschlossen liegen beide Kanten in der Mitte und überlappen um ein
        Pixel, damit keine Lichtritze bleibt.
        """
        breite, hoehe = self.buehne.animation.breite, self.buehne.animation.hoehe
        rand = self.px(20)
        halbachse = breite * 0.75
        mitte = hoehe / 2
        # So weit, dass die Kante offen auch über den Bildecken liegt.
        weit = (hoehe / 2) / (1 - (breite / 2 / halbachse) ** 2) * 1.1
        offen = (1 - min(1.0, max(0.0, zu))) * weit
        oben, unten = [(-rand, -rand)], [(-rand, hoehe + rand)]
        for i in range(KANTENSTUECKE + 1):
            x = -rand + (breite + 2 * rand) * i / KANTENSTUECKE
            u = (x - breite / 2) / halbachse
            bogen = offen * max(0.0, 1 - u * u)
            oben.append((x, mitte - bogen + 1))
            unten.append((x, mitte + bogen - 1))
        oben.append((breite + rand, -rand))
        unten.append((breite + rand, hoehe + rand))
        self.buehne.coords(self._lid_oben, *[wert for punkt in oben for wert in punkt])
        self.buehne.coords(self._lid_unten, *[wert for punkt in unten for wert in punkt])

    # ── Der Ablauf ─────────────────────────────────────────────────────────

    def beim_anzeigen(self):
        self.buehne.starten()
        self._knopf.focus_set()

    def warten(self):
        """Der Knopf "Warten": Die Augen fallen zu, die Uhr beginnt."""
        if self.phase != "abend":
            return
        self.phase = "nacht"
        self._knopf.configure(state="disabled")
        self._beginn = self._zeitgeber()
        self.zu_zeit(0)
        self.spaeter(TAKT_MS, self._takt)

    def _takt(self):
        # Läuft weiter, solange der Screen steht – der Rotor dreht sich auch nach der Landung.
        self.zu_zeit(round((self._zeitgeber() - self._beginn) * 1000))
        self.spaeter(TAKT_MS, self._takt)

    def zu_zeit(self, ms):
        """Stellt den Moment ``ms`` nach dem Warten-Knopf her – auch mit einem Sprung dorthin."""
        self.zeit_ms = ms
        self.lider(zwischenwert(LIDER, ms))
        if self._einmal("einschlafen", ms, 0):
            self._text_setzen(story.EINSCHLAFEN.absaetze[:1])
        if self._einmal("nacht", ms, NACHT):
            self._text_setzen(())
            self.buehne.itemconfigure(self._nachttext, state="normal")
        if self._einmal("morgen", ms, MORGEN_BEGINNT):
            self.buehne.itemconfigure(self._nachttext, state="hidden")
            self.buehne.wechseln(Animation(MORGEN, massstab=self.massstab))
        if self._einmal("geraeusch", ms, GERAEUSCH):
            self._text_setzen(story.AUFWACHEN.absaetze)
        if ms >= FLUG[0][0]:
            self._hubschrauber_bewegen(ms)
        if self._einmal("gelandet", ms, GELANDET):
            self.phase = "gerettet"
            self._text_setzen(story.RETTUNG.absaetze)
            self._knopf.configure(text=KNOPF_WEITER, state="normal", command=self.weiter)
            self._knopf.focus_set()

    def _einmal(self, name, ms, ab):
        """Ist ``ms`` so weit, dass ``name`` passiert – und ist es noch nicht passiert?"""
        if ms < ab or name in self._erledigt:
            return False
        self._erledigt.add(name)
        return True

    def _hubschrauber_bewegen(self, ms):
        flug = tuple((t, (self.px(links), self.px(oben))) for t, (links, oben) in FLUG)
        x, y = (round(wert) for wert in zwischenwert(flug, ms))
        if self.hubschrauber is None:
            self.hubschrauber = Figur(self.buehne, Animation(HUBSCHRAUBER, massstab=self.massstab), x, y)
            for element in self.hubschrauber.elemente:
                self.buehne.tag_lower(element, self._lid_oben)
        self.hubschrauber.verschieben(x, y)
        self.hubschrauber.zeige_bild(ms // self.hubschrauber.animation.takt_ms)
        self._bodenschatten_setzen(x, y)

    def _bodenschatten_setzen(self, x, y):
        """Unter dem Hubschrauber ein flacher Schatten auf dem Sand – je tiefer er kommt, desto grösser."""
        boden = self.px(FLUG[-1][1][1] + KUFEN)
        naehe = 1 - (boden - (y + self.px(KUFEN))) / self.px(SCHATTEN_AB)
        if naehe <= 0:
            self.buehne.itemconfigure(self._bodenschatten, state="hidden")
            return
        mitte = x + self.hubschrauber.animation.breite / 2
        halb_breit, halb_hoch = self.px(150) * naehe, self.px(7) * naehe
        self.buehne.coords(self._bodenschatten, mitte - halb_breit, boden - halb_hoch,
                           mitte + halb_breit, boden + halb_hoch)
        self.buehne.itemconfigure(self._bodenschatten, state="normal")

    def weiter(self):
        """Nach der Landung: der Schlusstext – und wo die Messdaten liegen."""
        if self.phase != "gerettet":
            return
        self.phase = "ende"
        self._text_setzen(story.ABSCHLUSS.absaetze)
        self._knopf.configure(text=KNOPF_BEENDEN, command=self.fenster.schliessen)
        self._knopf.focus_set()
        schrift = tkfont.Font(root=self, font=self._hinweis.cget("font"))
        platz = self.buehne.animation.breite - self._knopf.winfo_reqwidth() - self.px(stil.ABSTAND)
        pfad = vorne_kuerzen(str(self.durchlauf.protokoll.pfad),
                             lambda p: schrift.measure(HINWEIS_MESSDATEN.format(pfad=p)) <= platz)
        self._hinweis.configure(text=HINWEIS_MESSDATEN.format(pfad=pfad))
