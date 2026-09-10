"""Die drei Verschlüsselungsverfahren als gemeinsame Kennungen.

Warum eine eigene Datei
───────────────────────
``content/handbuch.py`` und ``content/story.py`` müssen sich darauf einigen,
wie ein Verfahren heisst – sonst lässt sich in Phase 7 eine Handbuchseite
nicht ihren Funksprüchen zuordnen. Vorher hatten beide ein Feld ``verfahren``,
meinten damit aber Verschiedenes: die Seite den Anzeigenamen
("Caesar-Verschlüsselung"), der Funkspruch die Kennung ("caesar"). Genau so
etwas fällt erst auf, wenn jemand die beiden gegeneinander hält.

Die Kennungen sind schlichte Zeichenketten. ``content/`` importiert nichts aus
``crypto/``; welches Modul zu welcher Kennung gehört, entscheidet Phase 7.
"""

CAESAR = "caesar"
SUBSTITUTION = "substitution"
VIGENERE = "vigenere"

#: Alle drei in der Reihenfolge der Level.
ALLE = (CAESAR, SUBSTITUTION, VIGENERE)

#: Welches Verfahren gehört zu welchem Level?
VERFAHREN_NACH_LEVEL = {1: CAESAR, 2: SUBSTITUTION, 3: VIGENERE}

#: Ausgeschriebene Namen für die Anzeige.
BEZEICHNUNG = {
    CAESAR: "Caesar-Verschlüsselung",
    SUBSTITUTION: "monoalphabetische Substitution",
    VIGENERE: "Vigenère-Verschlüsselung",
}
