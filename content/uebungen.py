"""Die Übungswörter und -sätze aus dem Handbuch (Arbeitsplan 2.2).

Quelle ist ``dokumentation/Handbuchtexte.md``. Pro Level gibt es zehn Texte,
aus denen der Aufgaben-Generator (Phase 3) zufällig einen auswählt – dadurch
bekommen nicht alle dieselbe Aufgabe und es lässt sich nicht abschauen.

Diese Datei ist die **einzige** Stelle im Code, an der die Übungstexte stehen.
Vorher lagen sie in fünf Testdateien parallel; ``tests/test_uebungen.py``
vergleicht sie jetzt zusätzlich Zeile für Zeile mit dem Markdown der Quelle.
Läuft eines von beidem auseinander, wird ein Test rot – sonst würde im Spiel
ein Wort auftauchen, das im Handbuch gar nicht steht.

Warum die Texte schon in Großbuchstaben stehen
──────────────────────────────────────────────
Sie sind bereits in der Form der Textkonvention (siehe
:mod:`crypto.normalize`): nur A–Z und einfache Leerzeichen. Damit stimmen
Aufgabentext und Lösung von vornherein überein – die UI muss nichts umformen,
und in der Anzeige taucht kein Komma auf, das in der Lösung fehlt.

Zum Schwierigkeitsverlauf
─────────────────────────
Die Level-2-Sätze sind bewusst unterschiedlich lang: von "ALLES OK" (7
Buchstaben) bis "HILFE WIRD GEBRAUCHT" (18). Das Konzept sieht für Level 2
einen Anstieg vor, damit am Ende der Hinweis auf die Häufigkeitsanalyse trägt.
Als *erste* Stufe nennt das Konzept ein einzelnes Wort – die dafür passenden
Texte stehen im Pool von Level 1, den der Generator mitbenutzen darf. Welche
Reihenfolge er daraus baut, entscheidet Aufgabe 3.2; hier steht nur das
Material.
"""

# ───────────────────────────────────────────────────────────────────────────
# Level 1 – Caesar (Handbuchseite 1)
# ───────────────────────────────────────────────────────────────────────────

UEBUNGSWOERTER_LEVEL_1 = (
    "HUND",
    "KATZE",
    "MAUS",
    "BURG",
    "FELS",
    "WALD",
    "STERN",
    "MOND",
    "SAND",
    "TURM",
)


# ───────────────────────────────────────────────────────────────────────────
# Level 2 – Monoalphabetische Substitution (Handbuchseite 2)
# ───────────────────────────────────────────────────────────────────────────

UEBUNGSSAETZE_LEVEL_2 = (
    "ALLES OK",
    "ICH BIN HIER",
    "KOMM SCHNELL",
    "WO BIST DU",
    "BLEIB RUHIG",
    "WEG IST FREI",
    "GEFAHR NAH",
    "ZEIT WIRD KNAPP",
    "PLAN WIRD NEU",
    "HILFE WIRD GEBRAUCHT",
)


# ───────────────────────────────────────────────────────────────────────────
# Level 3 – Vigenère (Handbuchseite 3)
# ───────────────────────────────────────────────────────────────────────────

UEBUNGSSAETZE_LEVEL_3 = (
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
)


# Schlüsselwörter für Level 3. Das Handbuch rechnet sein Beispiel mit ROT
# durch; für die Übungsaufgaben muss der Schlüssel aber wechseln, sonst ist
# die Aufgabe nach zwei Durchläufen vorhersehbar (siehe Zusammenfassung,
# Punkt 5). Weitere Wörter können hier einfach ergänzt werden – erlaubt ist
# alles aus A–Z ohne Leerzeichen; kurz sollte es bleiben, damit die Schleife
# im Handbuch-Quadrat von Hand nachvollziehbar bleibt.
VIGENERE_SCHLUESSELWOERTER = ("ROT", "WEG", "TAG")

# Schlüssel für Level 1. Das Handbuch sagt: "Schlüssel wird vorgegeben" – die
# Übungsaufgabe nennt ihn also, geknackt werden muss er nicht.
#
# Enthalten sind alle Verschiebungen von 1 bis 25. Nicht enthalten sind:
# * 0 und 26, weil sie den Text unverändert lassen und damit keine Aufgabe sind;
# * 13, weil Ver- und Entschlüsseln dort dasselbe Ergebnis liefern. Genau das
#   soll in Level 1 aber unterschieden werden ("vorwärts" gegen "rückwärts"
#   springen, siehe Merksatz auf Handbuchseite 1), und ein Schlüssel, bei dem
#   beide Richtungen gleich aussehen, verwischt den Unterschied.
CAESAR_SCHLUESSEL = tuple(k for k in range(1, 26) if k != 13)

#: Der Schlüssel, mit dem Handbuchseite 1 ihr Beispiel durchrechnet
#: (HUND wird zu KXQG). Die echten Funksprüche von Level 1 benutzen ihn
#: ebenfalls, damit die Spielenden dem Beispiel Schritt für Schritt folgen
#: können – der Ernstfall soll das Verfahren üben, nicht eine neue Zahl.
CAESAR_SCHLUESSEL_HANDBUCH = 3


# ───────────────────────────────────────────────────────────────────────────
# Sichten für den Aufgaben-Generator und die Tests
# ───────────────────────────────────────────────────────────────────────────

# Welcher Pool gehört zu welchem Level? Bewusst ein Dict und keine Funktion –
# content/ enthält nur Daten.
UEBUNGSTEXTE_NACH_LEVEL = {
    1: UEBUNGSWOERTER_LEVEL_1,
    2: UEBUNGSSAETZE_LEVEL_2,
    3: UEBUNGSSAETZE_LEVEL_3,
}

# Alle 30 Texte am Stück, in Level-Reihenfolge. Praktisch für Tests, die jedes
# Verfahren gegen das gesamte Material laufen lassen.
ALLE_UEBUNGSTEXTE = (
    UEBUNGSWOERTER_LEVEL_1 + UEBUNGSSAETZE_LEVEL_2 + UEBUNGSSAETZE_LEVEL_3
)
