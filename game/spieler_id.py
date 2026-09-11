"""Die ID, unter der ein Durchlauf im Log steht (Projektregel 7).

Die Lehrkraft verteilt die IDs selbst, auf Papier, in der Form ``X-XX``:
Die erste Ziffer ist die Klasse, die beiden anderen die Nummer des Kindes –
``1-12`` bekommt das zwölfte Kind der 7/1. Wer hinter einer ID steckt, weiss
nur die Lehrkraft; das Spiel sieht nie einen Namen.

Warum so streng
───────────────
Das Spiel nimmt **nur** IDs in genau dieser Form an. Im Eingabefeld auf dem
Startbildschirm lassen sich deshalb nur Ziffern und der Strich an seiner
Stelle tippen (:func:`ist_anfang`) – einen Namen einzutragen ist gar nicht
möglich, auch nicht aus Versehen.

Wer nach der Klasse gleich die Nummer tippt, bekommt den Strich geschenkt
(:func:`strich_fehlt`): Aus "1", "1", "2" wird "1-12". Fehlt am Ende noch
etwas, sagt :func:`fehler` genau, was – nicht nur "ungültig".

Die ID im Log
─────────────
In der CSV-Datei steht vor der ID ein "ID " (siehe
:func:`game.protokoll.pseudonym_fuer_tabelle`): Excel machte aus ``1-12``
beim Öffnen sonst den 1. Dezember.
"""

import re

#: So sieht eine ID aus: Klasse (eine Ziffer), Strich, Nummer (zwei Ziffern).
#: Bewusst [0-9] statt \d – \d liesse auch arabische und andere Ziffern zu.
MUSTER = re.compile(r"[0-9]-[0-9]{2}")

#: Alle Anfänge einer ID: "", "1", "1-", "1-1" und die ganze ID.
_ANFANG = re.compile(r"([0-9](-[0-9]{0,2})?)?")

#: Das Beispiel in Hinweisen und Fehlermeldungen.
BEISPIEL = "1-12"


def ist_gueltig(text):
    """Ist ``text`` eine vollständige ID wie ``1-12``?

    >>> ist_gueltig("1-12"), ist_gueltig("1-2"), ist_gueltig("Max")
    (True, False, False)
    """
    return MUSTER.fullmatch(text) is not None


def ist_anfang(text):
    """Kann aus ``text`` durch Weitertippen noch eine ID werden?

    Das Eingabefeld lässt nur Eingaben zu, nach denen das gilt – so kommen
    keine Buchstaben hinein.

    >>> [ist_anfang(t) for t in ("", "1", "1-", "1-1", "1-12")]
    [True, True, True, True, True]
    >>> [ist_anfang(t) for t in ("a", "-", "11", "1-123", "1 ")]
    [False, False, False, False, False]
    """
    return _ANFANG.fullmatch(text) is not None


def strich_fehlt(bisher, zeichen):
    """Tippt jemand nach der Klasse gleich eine Ziffer, fehlt der Strich davor.

    >>> strich_fehlt("1", "2"), strich_fehlt("1", "-"), strich_fehlt("", "1")
    (True, False, False)
    """
    return re.fullmatch(r"[0-9]", bisher) is not None and re.fullmatch(r"[0-9]", zeichen) is not None


def fehler(text):
    """Was an ``text`` noch nicht stimmt – als Satz für die Spielenden.

    Leer, wenn ``text`` eine gültige ID ist. Sonst ein konkreter Hinweis, was
    fehlt (Projektregel 6: nie nur "falsch").

    >>> fehler("1-12")
    ''
    >>> fehler("1-2")
    'Deine Nummer hat zwei Ziffern. Bei einer einstelligen kommt eine 0 davor: 1-02.'
    """
    if ist_gueltig(text):
        return ""
    if text == "":
        return f"Trag zuerst deine ID ein. Du bekommst sie von deiner Lehrkraft, zum Beispiel {BEISPIEL}."
    if re.fullmatch(r"[0-9]", text):
        return f"Nach der Klasse fehlen noch der Strich und deine Nummer, zum Beispiel {text}-12."
    if re.fullmatch(r"[0-9]-", text):
        return f"Nach dem Strich fehlt noch deine Nummer – zwei Ziffern, zum Beispiel {text}12."
    einstellig = re.fullmatch(r"([0-9])-([0-9])", text)
    if einstellig:
        klasse, nummer = einstellig.groups()
        return f"Deine Nummer hat zwei Ziffern. Bei einer einstelligen kommt eine 0 davor: {klasse}-0{nummer}."
    ohne_strich = re.fullmatch(r"([0-9])([0-9]{2})", text)
    if ohne_strich:
        return f"Zwischen Klasse und Nummer gehört ein Strich: {ohne_strich[1]}-{ohne_strich[2]}."
    if re.fullmatch(r"-[0-9]*", text):
        return f"Vor dem Strich fehlt noch deine Klasse, zum Beispiel {BEISPIEL}."
    return f"Die ID hat die Form Klasse, Strich, Nummer – zum Beispiel {BEISPIEL}."
