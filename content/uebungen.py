"""Die Übungstexte aus dem Handbuch (Arbeitsplan 2.2).

Quelle ist ``dokumentation/Handbuchtexte.md``. Es gibt **einen** Pool mit
vierundfünfzig Sätzen für alle drei Level. Aus ihm zieht der Aufgaben-Generator (Phase 3) –
dadurch bekommen nicht alle dieselbe Aufgabe, und es lässt sich nicht abschauen.

Diese Datei ist die **einzige** Stelle im Code, an der die Übungstexte stehen.
Vorher lagen sie in fünf Testdateien parallel; ``tests/test_uebungen.py``
vergleicht sie jetzt zusätzlich Zeile für Zeile mit dem Markdown der Quelle.
Läuft eines von beidem auseinander, wird ein Test rot – sonst würde im Spiel
ein Satz auftauchen, der im Handbuch gar nicht steht.

Warum die Texte schon in Großbuchstaben stehen
──────────────────────────────────────────────
Sie sind bereits in der Form der Textkonvention (siehe
:mod:`crypto.normalize`): nur A–Z und einfache Leerzeichen. Damit stimmen
Aufgabentext und Lösung von vornherein überein – die UI muss nichts umformen,
und in der Anzeige taucht kein Komma auf, das in der Lösung fehlt.

Warum alle drei Level aus demselben Pool ziehen
───────────────────────────────────────────────
Zuerst hatte jede Handbuchseite ihre eigene Liste: Wörter mit vier, fünf
Buchstaben für Caesar, Sätze mit 7 bis 18 Buchstaben für die Substitution und
Sätze mit 12 bis 18 für Vigenère. Eine Übung in Level 3 hätte dann schon wegen
ihres Textes länger gedauert als eine in Level 1, und in den Messdaten liesse
sich nicht trennen, was am Verfahren liegt und was an der Länge. Schwerer
werden die Level durch das Verfahren, nicht durch längere Texte.

Nachträglich entschieden: Alle drei Level üben mit denselben Sätzen, und die
sind ähnlich lang – 10 bis 14 Buchstaben. Die ersten zehn sind genau die Sätze
der früheren Listen, die in diesem Bereich lagen. Jeder hat Wortgrenzen, damit
die Regeln 3 und 7 der Textkonvention im Spiel sichtbar werden.

Der Pool ist zweimal gewachsen, und beide Male aus demselben Grund: Es gingen
die Texte aus, bevor die Zeit um war. Seit die Zusatzaufgaben nach der
Restzeit kommen und nicht mehr nach dem Tempo (:mod:`game.zusatzaufgaben`),
übt man in einem Level so lange, wie sein Zeitfenster trägt. Mit zehn Texten
bekam ein Level nur drei bis vier eigene, mit achtzehn genau sechs – und sechs
Übungen plus die Funksprüche sind im geschätzten Tempo nach gut einem Drittel
des Fensters erledigt. Danach endete das Level "vorzeitig", während die
Kontrollgruppe weiterarbeitete; gemessen worden wäre dann nicht die Methode,
sondern wie schnell dem Spiel die Aufgaben ausgehen.

Jetzt sind es vierundfünfzig, also **achtzehn je Level**: zwei Pflichtübungen
und bis zu sechzehn Zusatzaufgaben, alle verschieden. Im geschätzten Tempo
trägt das bis ans Ende des Zeitfensters (ein bis fünf Prozent bleiben
ungenutzt), bei langsamerem erst recht. Wer deutlich schneller rechnet als
geschätzt, hat seinen Abschnitt trotzdem vor der Zeit durch – bei doppelter
Geschwindigkeit bleiben in Level 3 rund zwölf Minuten. Ob das vorkommt, sagt
der Pilotdurchlauf (Arbeitsplan 8.2): Dort wird die Schätzgerade selbst
nachgemessen, und danach entscheidet sich, ob der Pool noch einmal wächst
oder die Zeitfenster kürzer werden.

Weil derselbe Satz so in mehreren Leveln vorkommen kann, verteilt der
Generator den Pool auf die Level (siehe :mod:`game.generator`): Wer einen Satz
in Level 1 verschlüsselt hat, soll ihn in Level 2 nicht aus dem Gedächtnis
"entschlüsseln" können.
"""

# ───────────────────────────────────────────────────────────────────────────
# Die Übungstexte – für alle drei Level
# ───────────────────────────────────────────────────────────────────────────

UEBUNGSTEXTE = (
    "ICH BIN HIER",
    "KOMM SCHNELL",
    "BLEIB RUHIG",
    "WEG IST FREI",
    "ZEIT WIRD KNAPP",
    "PLAN WIRD NEU",
    "NAHE DEM WRACK",
    "RICHTUNG NORDEN",
    "KEIN WASSER MEHR",
    "BIN NOCH AM LEBEN",
    "OASE IST NAH",
    "SAND UEBERALL",
    "FEUER IST AUS",
    "WARTE AUF UNS",
    "FUNK IST STARK",
    "NIMM DIE KARTE",
    "SPUREN IM SAND",
    "HALT DICH BEREIT",
    "LAGER IST SICHER",
    "WIR SIND ZU ZWEIT",
    "HIMMEL IST KLAR",
    "MOTOR IST HIN",
    "SUCHE DEN WEG",
    "BRING DAS SEIL",
    "MOND STEHT HOCH",
    "KEIN SIGNAL HIER",
    "WIND WIRD STARK",
    "NACHT IST LANG",
    "WASSER IST KNAPP",
    "FOLGE DEN SPUREN",
    "FUNK BLEIBT AN",
    "WIR HABEN GLUECK",
    "STEINE AM WEG",
    "DAS ZELT STEHT",
    "KARTE IST ALT",
    "ZWEI TAGE ZEIT",
    "HITZE IST HART",
    "BRAUCHEN HILFE",
    "DER WEG IST WEIT",
    "BOB MELDET SICH",
    "NIEMAND FOLGT",
    "TREFFEN AM WRACK",
    "LICHT IM NORDEN",
    "WIR GEHEN LOS",
    "DAS FUNKGERAET",
    "SCHATTEN AM FELS",
    "DIESE NACHT NOCH",
    "RUHIG UND LEISE",
    "ALLES GUT HIER",
    "DER TANK IST LEER",
    "KOMM ZUM LAGER",
    "WIR WARTEN HIER",
    "SONNE GEHT AUF",
    "PASS GUT AUF DICH",
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
