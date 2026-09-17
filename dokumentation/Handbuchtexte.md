# Bobs Verschlüsselungshandbuch

*Notfall-Ausgabe – lies das genau durch, bevor du irgendwas funkst.*

---

## Seite 1: Die Caesar-Verschlüsselung

### Was ist das?

Stell dir das Alphabet als einen Kreis vor, der sich drehen lässt – wie ein
Glücksrad mit 26 Feldern (A bis Z). Bei der Caesar-Verschlüsselung drehst du
das Rad um eine bestimmte Anzahl Stellen weiter. Diese Zahl nennt man den
**Schlüssel**.

Jeder Buchstabe deiner Nachricht wird um genau diese Anzahl Stellen im
Alphabet nach vorne verschoben. Kommst du am Ende des Alphabets an (bei Z),
geht es einfach wieder bei A weiter – wie bei einer Uhr, die nach 12 wieder
bei 1 anfängt.

### Beispiel: Schlüssel 3

Alphabet ohne Verschiebung:

`A B C D E F G H I J K L M N O P Q R S T U V W X Y Z`

Alphabet um 3 Stellen verschoben:

`D E F G H I J K L M N O P Q R S T U V W X Y Z A B C`

Das heißt: Aus $A$ wird $D$, aus $B$ wird $E$, aus $H$ wird $K$ und so weiter.

**Verschlüsseln des Wortes "HUND" mit Schlüssel 3:**

| Buchstabe       | H | U | N | D |
|-----------------|---|---|---|---|
| verschoben um 3 | K | X | Q | G |

Ergebnis: **HUND → KXQG**

**Entschlüsseln funktioniert genau umgekehrt:** Du gehst dieselbe Anzahl
Stellen im Alphabet zurück. Aus KXQG wird also wieder HUND.

### Merksatz

Verschlüsseln = im Alphabet **vorwärts** springen.
Entschlüsseln = im Alphabet **rückwärts** springen.
Am Rand des Alphabets (Z bzw. A) einfach am anderen Ende weitermachen.

---

## Seite 2: Die monoalphabetische Substitution

### Was ist das?

Bei Caesar hast du das ganze Alphabet um eine feste Zahl verschoben – das
Muster ist also leicht zu erkennen, sobald man es einmal weiß. Bei der
Substitution machst du es cleverer: Jeder Buchstabe bekommt einen **völlig
frei gewählten** Ersatzbuchstaben, nicht einfach "3 weiter". Es gibt kein
festes Verschiebungsmuster mehr.

**Ein Trick, um dir so eine Zuordnung leicht zu merken:** Nimm eine
Computertastatur. Lies die Buchstaben einfach der Reihe nach ab, Zeile für
Zeile:

Erste Zeile: `Q W E R T Z U I O P`
Zweite Zeile: `A S D F G H J K L`
Dritte Zeile: `Y X C V B N M`

Hintereinander ergibt das eine komplette neue Buchstaben-Reihenfolge mit 26
Zeichen. Ordnest du sie dem normalen Alphabet zu, bekommst du deine
Geheimtabelle:

| Original | A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P | Q | R | S | T | U | V | W | X | Y | Z |
|----------|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Geheim   | Q | W | E | R | T | Z | U | I | O | P | A | S | D | F | G | H | J | K | L | Y | X | C | V | B | N | M |

**Verschlüsseln des Wortes "HUND":**

| Buchstabe     | H | U | N | D |
|---------------|---|---|---|---|
| Geheimzeichen | I | X | F | R |

Ergebnis: **HUND → IXFR**

**Entschlüsseln:** Du suchst den Geheimbuchstaben in der unteren Zeile und
liest ab, welcher Originalbuchstabe darüber steht.

### Warum ist das schwerer zu knacken?

Bei Caesar gibt es nur 25 mögliche Schlüssel – die kann man in ein paar
Minuten alle durchprobieren. Bei der Substitution kann **jeder** Buchstabe zu
**jedem** anderen werden. Das ergibt Millionen und Millionen möglicher
Zuordnungen – zu viele zum Durchprobieren.

Trotzdem ist die Methode nicht unknackbar: In jeder Sprache kommen manche
Buchstaben viel häufiger vor als andere. Im Deutschen ist zum Beispiel das
"E" der häufigste Buchstabe. Wer einen langen Geheimtext hat, kann zählen,
welches Geheimzeichen am öftesten vorkommt – das ist dann sehr wahrscheinlich
das "E". So lässt sich die Zuordnung Stück für Stück knacken. Das nennt man
**Häufigkeitsanalyse**.

### Merksatz

Je länger der Text, desto leichter wird er über Häufigkeitsanalyse knackbar
– kurze Nachrichten sind sicherer als lange.

---

## Seite 3: Die Vigenère-Verschlüsselung (mit dem Vigenère-Quadrat)

> **Hinweis für die Umsetzung:** Hier stand ein Bild des Vigenère-Quadrats,
> das nicht mit ins Repository gewandert ist. Es wird auch nicht gebraucht:
> Das Quadrat wird von `crypto/vigenere_quadrat.py` aus der Formel erzeugt
> und in Phase 6.7 als 26×26-Raster angezeigt.

### Was ist das?

Bei Caesar hast du **immer** um dieselbe Zahl verschoben. Das Problem: Sobald jemand die eine Verschiebung errät, ist die ganze Nachricht offen. Die Vigenère-Verschlüsselung löst das clever: Du benutzt nicht nur eine Verschiebung, sondern ein ganzes **Schlüsselwort**. Jeder Buchstabe dieses Wortes sorgt für eine eigene, andere Verschiebung.

Das Schlüsselwort wird so oft wiederholt, bis es genauso lang ist wie deine Nachricht.

### Das Vigenère-Quadrat

Damit du nicht rechnen musst, gibt es eine fertige Tabelle: das **Vigenère-Quadrat**. Es sieht aus wie ein riesiges Kreuzworträtsel:

- Oben in der Kopfzeile stehen die Buchstaben deiner **Nachricht** (Klartext), A bis Z.
- Links in der ersten Spalte stehen die Buchstaben deines **Schlüsselworts**, A bis Z.
- In jedem Feld der Tabelle steht ein Buchstabe. Um zu verschlüsseln, gehst du einfach zur richtigen Zeile und Spalte und liest ab, was am Kreuzungspunkt steht.

### Verschlüsseln – Schritt für Schritt

**Beispiel: Nachricht "HUND", Schlüsselwort "ROT"**

Zuerst schreibst du das Schlüsselwort so oft untereinander, bis es genauso lang ist wie deine Nachricht:

| Nachricht | H | U | N | D |
|-----------|---|---|---|---|
| Schlüssel | R | O | T | R |

Jetzt gehst du Buchstabe für Buchstabe vor:

1. **H** (Nachricht) + **R** (Schlüssel): Suche im Quadrat die Zeile "R" und die Spalte "H". Am Kreuzungspunkt steht **Y**.
2. **U** + **O**: Zeile "O", Spalte "U" → **I**.
3. **N** + **T**: Zeile "T", Spalte "N" → **G**.
4. **D** + **R**: Zeile "R", Spalte "D" → **U**.

Ergebnis: **HUND → YIGU**

### Entschlüsseln – Schritt für Schritt

Jetzt hast du den Geheimtext **YIGU** und das Schlüsselwort **ROT** – und willst wissen, was ursprünglich dastand.

Diesmal machst du es andersherum: Du suchst zuerst die **Zeile** deines Schlüsselbuchstabens, und darin den Geheimbuchstaben. Die Spalte, in der du ihn findest, verrät dir den Original-Buchstaben.

1. Geheimbuchstabe **Y**, Schlüssel **R**: Gehe zur Zeile "R" und suche darin das "Y". Es steht in der Spalte **H**.
2. Geheimbuchstabe **I**, Schlüssel **O**: Zeile "O", suche "I" → Spalte **U**.
3. Geheimbuchstabe **G**, Schlüssel **T**: Zeile "T", suche "G" → Spalte **N**.
4. Geheimbuchstabe **U**, Schlüssel **R**: Zeile "R", suche "U" → Spalte **D**.

Ergebnis: **YIGU → HUND**

### Warum ist das noch sicherer?

Bei der einfachen Substitution steht jeder Buchstabe der Nachricht immer für dasselbe Geheimzeichen – deshalb funktioniert Häufigkeitsanalyse so gut. Bei Vigenère wird zum Beispiel das "N" aus HUND einmal zu "G", könnte an anderer Stelle aber zu einem ganz anderen Buchstaben werden – je nachdem, welcher Schlüsselbuchstabe gerade dran ist. Dadurch verschwimmt das Muster: Einfaches Zählen der häufigsten Zeichen hilft hier nicht mehr direkt weiter.

### Merksatz

**Verschlüsseln** = Nachrichtenbuchstabe (Spalte) und Schlüsselbuchstabe (Zeile) im Quadrat zusammenführen – der Kreuzpunkt ist der verschlüsselte Buchstabe.

**Entschlüsseln** = In der Zeile des Schlüsselbuchstabens den Geheimbuchstaben suchen – der Spaltenkopf darüber ist der entschlüsselte Buchstabe.

---

## Übungssätze für alle drei Seiten

Alle drei Seiten üben mit denselben zehn Sätzen. Sie sind ähnlich lang (10 bis
14 Buchstaben): Eine Übung zu Seite 3 soll nicht schon wegen eines längeren
Textes länger dauern als eine zu Seite 1 – schwerer wird es durch das
Verfahren, nicht durch die Länge. *(Nachträglich entschieden. Vorher hatte jede
Seite eine eigene Liste: Wörter mit 4–5 Buchstaben für Caesar, Sätze mit 7–18
für die Substitution und 12–18 für Vigenère. Übernommen sind die Sätze, die
schon 10 bis 14 Buchstaben lang waren.)*

### Übungssätze (10 Stück – einer wird zufällig ausgewählt)

 1. ICH BIN HIER
 2. KOMM SCHNELL
 3. BLEIB RUHIG
 4. WEG IST FREI
 5. ZEIT WIRD KNAPP
 6. PLAN WIRD NEU
 7. NAHE DEM WRACK
 8. RICHTUNG NORDEN
 9. KEIN WASSER MEHR
10. BIN NOCH AM LEBEN

Ein technischer Hinweis für die Umsetzung: Bei allen drei Seiten sollte pro Übungsaufgabe zusätzlich zufällig entschieden werden, ob das gewählte Wort/der Satz **ver-** oder **entschlüsselt** werden soll (bei Verschlüsseln zeigt ihr den Klartext, bei Entschlüsseln müsst ihr das Wort vorher selbst mit demselben Schlüssel verschlüsseln und als Aufgabe anzeigen). Auch bei Level 3 sollte der zufällig gewählte Schlüssel (Schlüsselwort) mit variieren, nicht immer "ROT" – sonst wird die Aufgabe nach ein paar Durchläufen vorhersehbar. Zwei, drei kurze Schlüsselwörter (z. B. ROT, WEG, TAG) als weitere Zufallsauswahl würden das lösen.