# Konzept Spiel

## V1 ohne KI:

### Randgeschichte

- Am Anfang wählt man Charakter aus
- Geheimagent, hat gerade aus Antwerpen (der Stadt der Diamanten in Belgien) viele Diamanten im Wert von mehreren Milliarden Euro geklaut
- CIA, Interpool und die belgische Polizei sind auf der Suche nach dir
- Flugzeug abgestürtz über Wüste Afghanistans auf dem Weg nach Singapur
- Nun gestrandet

### Charaktere

- Bob der Admin
- Spieler (selbst wählbar aus) 
  - Charakter 1
  - Charakter 2
  - Charakter 3
  - Charakter 4
  - Charakter 5

### Geschichte

- Aufgabe: du musst nun zu deiner Basis Kontakt aufnehmen, ohne das deine Verfolger deine Nachricht bekommen
- Spieler muss nun Helikopter durchsuchen: findet dabei Handbuch über verchlüsselungen und ein Transmitter der die Signale übermittelt
- Spieler hat keine Ahnung über Verschlüsselungen weil er in der Ausbildung nicht aufgepasst hat
- Zuerst wird Ceasar Verschlüsselung beigebracht: Mit Handbuchseite wird es erklärt und dann im Buch einmal verschlüsseln und entschlüsseln als Übungsaufgabe. Übungswörter im Buch sind zufällig, sodass keiner abschauen kann
- Dann muss man in Realität die Nachricht: Hallo, Zentrale könnt ihr mich verstehen? \[mit Initialen des Charakters unterschreiben\]
- Zentrale antwortet in Ceasar: Ja wir können dich verstehen, benutze aber keine Ceasar Verschlüsselung, das kann man ganz einfach knacken. Die Botschaft muss entschlüsselt werden
- Spieler geht also zur nächsten Seite mit stärkerer Verschlüsselungstechnik und da kommt Transposition
- Nun wird Transposition erklärt und man macht einmal verschlüsseln und entschlüsseln im Buch als Übung mit Lösung
- Dann will Spieler nächste Nachricht versenden da hört er eine Nachricht von einer unbekannten Quelle auf seinem Transmitter: "Quadrant xy ist abgesucht wir fahren nun mit quadrant yx fort, wir finden den Idioten" (Nachricht ist auf Transposition muss entschlüsselt werden, das geht aber weil Bob hinten im Buch die Entschlüsselungalphabeten für den Feind hat)
- Spieler kann also kein Transposition verwenden --> muss auf nächstes umstellen --> Vigenére
- Spieler lernt Vigenére wieder mit Handbuch übt einmal ver- und entschlüsseln und muss dann seinen aktuellen Standort auf Vigenére versenden. Die Zentrale antwortet dann auch mit Vigenére und muss entschlüsselt werden
- Zentrale antwortet: mit wir schicken dir Hilfe. Nachdem das entschlüsselt wurde, kann man auf Warten tippen, dann kommt ein schöner Nachthimmel Bildschirm und dann kommt Hilfe und das Spiel ist durchgespielt
- Spiel ist vorbei man ist reich

## V2 mit Ergänzungen von KI:

# Rahmengeschichte: "**Der große Diamantenraub**"

## Prämisse

Der Raub ist geglückt: Deine Crew hat aus einem gesicherten Tresor in Antwerpen (der Diamantenstadt Belgiens.) Diamanten im Wert mehrerer Milliarden Euro erbeutet. Die Flucht per Charterflugzeug Richtung Singapur läuft zunächst glatt, bis CIA, Interpol und die belgische Polizei die Maschine auf dem Radar haben und Jäger aufsteigen lassen. Der Pilot muss ausweichen, verliert die Kontrolle – das Flugzeug stürzt über der afghanischen Wüste ab.

## Charaktere

**Spieler:in** – wählbar zu Beginn aus fünf Crewmitgliedern (Initialen werden
später zum Signieren der Funksprüche verwendet):

- Vic Moreno – Tresorknacker
- Elena Duarte – ehemalige Diamantenhändlerin
- Jonas Berg – Technik-Experte
- Amara Nwosu – Fluchtplanerin
- Théo Lambert – Fälscher und Tarnungsspezialist

**Bob** – dein alter Ausbilder, sitzt in der Crew-Zentrale in Singapur. Er ist
zu Beginn nicht erreichbar. Er meldet sich im gesamten Spiel nur **zweimal**
über Funk – jedes Mal ausschließlich in verschlüsselter Form, die der Spieler
selbst entschlüsseln muss. Er "plaudert" nie im Klartext dazwischen.

## Ausgangssituation

**Direkt nach dem Absturz** (Intro-Text, kein Kontakt, keine Wahlmöglichkeit):

> Das Wrack brennt. Du musst weg, bevor es jemand am Rauch findet. Der
> Diamantensack liegt griffbereit – aber er ist zu schwer, um ihn allein zu
> tragen und gleichzeitig schnell genug zu fliehen. Du lässt ihn zurück.

Im Vorbeigehen greifst du zwei Dinge aus dem Gepäckfach: ein
**Kurzwellen-Funkgerät** aus der Notausrüstung – kräftig genug, um über
Kontinente hinweg Signale zu senden, aber auch leicht von jedem mitzuhören,
der auf derselben Frequenz lauscht – und Bobs Verschlüsselungshandbuch,
Standardausrüstung, die du dir vor der Mission nie richtig angesehen hast.

Drei Kilometer weiter, an einer kleinen Oase, schlägst du dein Lager auf. Hier
bist du fürs Erste sicher – und auf dich allein gestellt: kein Funkkontakt, nur
das Handbuch. Deine Aufgabe: einen Weg finden, Kontakt zur Zentrale in Singapur
aufzunehmen, ohne dass die Verfolger – die dieselbe Frequenz absuchen – deine
Nachrichten mitlesen können.

*Nachträglich entschieden:* Der Unterschlupf ist eine **Oase**. In der Wüste
braucht man Wasser, und damit erklärt sich auch, warum das Lager nicht am Wrack
steht und die Diamanten dort zurückbleiben. Vor allem aber bekommt das
Verschlüsseln damit etwas Greifbares: In Level 2 liest man mit, wie die
Verfolger Quadrant für Quadrant absuchen – in Level 3 verschlüsselt man selbst
das Wort, das einen verraten würde, und am Ende landet der Hubschrauber genau
dort, weil nur die eigene Crew die Nachricht lesen konnte.

---

## Level 1 – Caesar-Verschlüsselung (ca. 15 Min)

**Einstieg (du bist allein, kein Bob):** Du schlägst das Handbuch auf. Seite 1:
"Grundlagen der Verschlüsselung – Caesar-Code."

**Handbuch-Erklärung:** Prinzip der festen Buchstabenverschiebung, inkl.
Sprung Z→A, mit animiertem Alphabetband. Das Buch erklärt sich selbst.

**Übung im Buch:** 2 Aufgaben (1× verschlüsseln, 1× entschlüsseln) mit
zufällig generierten Übungswörtern. Bei Fehler: sofortiger Hinweis, welche
Stelle nicht stimmt; nach 3 erfolglosen Versuchen wird die Lösung angeboten.

**Reale Anwendung – Senden:** Du verschlüsselst eine erste Funkmeldung, ohne
zu wissen, ob überhaupt jemand zuhört:
"Hallo, hört mich jemand? [Initialen]"
Eine falsch verschlüsselte Nachricht lässt sich nicht absenden – Meldung:
"Das stimmt noch nicht, versuch's nochmal."

**Reale Anwendung – Empfangen (erster Bob-Kontakt):** Kurz darauf trifft eine
Antwort ein, verschlüsselt in Caesar. Du musst sie selbst entschlüsseln, um
zu erfahren, was drinsteht:
"Ja, wir hören dich. Aber Caesar ist in Minuten zu knacken – nimm die
nächste Methode im Handbuch."

---

## Level 2 – Monoalphabetische Substitution (10 Min)

> *(Im Konzept standen hier 20 Minuten. Nach dem Pilotdurchlauf auf 10
> gekürzt – Begründung im Modulkopf von `game/zeitfenster.py`.)*

**Einstieg:** Kein Funkkontakt nötig – du weißt aus Bobs Nachricht bereits,
dass du weiterblättern musst. Seite: "Monoalphabetische Substitution."

**Handbuch-Erklärung:** freie Zuordnungstabelle statt fester Verschiebung.

**Übung im Buch:** mehrere Aufgaben mit steigender Textlänge (Wort → kurzer
Satz → längere Nachricht), zufällig generiert. Bei der letzten, längeren
Aufgabe der Hinweis: "Alle Zuordnungen durchprobieren würde ewig dauern –
hier hilft nur eine Häufigkeitsanalyse."

*Nachträglich entschieden:* Die Übungen werden nicht länger. Alle drei Level
üben mit denselben zehn, ähnlich langen Sätzen (10–14 Buchstaben) – schwerer
wird es durch das Verfahren, nicht durch die Länge, und die Bearbeitungszeiten
der Level bleiben vergleichbar. Der Hinweis auf die Häufigkeitsanalyse kommt
deshalb zum abgefangenen Funkspruch, der ja sichtbar lang ist.

**Reale Anwendung – nur Empfangen:** Bevor du weiterfunken kannst, rauscht es
im Gerät – ein fremder Funkspruch wird aufgefangen: "Quadrant 4 ist
durchsucht, wir gehen jetzt auf Quadrant 7 – wir finden den Verräter." Die
Nachricht ist mit derselben Substitutionsmethode verschlüsselt. Mithilfe von
Bobs erbeuteter Tabelle hinten im Handbuch kannst du sie entschlüsseln.

**Story-Übergang (ohne Bob-Dialog):** Erzähltext: "Der Feind nutzt genau die
Methode, die du gerade verwendest. Zeit für etwas Stärkeres." Du blätterst
selbst zur letzten Seite weiter – kein zusätzlicher Funkspruch nötig.

---

## Level 3 – Vigenère-Verschlüsselung (ca. 25 Min)

**Einstieg:** letzte Seite im Handbuch: "Vigenère-Verschlüsselung."

**Handbuch-Erklärung:** Schlüsselwort-Prinzip (3–4 Buchstaben), Schritt für
Schritt, mit geführtem Beispiel im Buch.

**Übung im Buch:** 2 Aufgaben (verschlüsseln/entschlüsseln) mit zufälligem
Schlüsselwort; danach kurze Reflexionsfrage: "Warum hilft
Häufigkeitsanalyse hier nicht mehr direkt?"

**Reale Anwendung – Senden:** Du verschlüsselst deinen aktuellen Standort und
sendest ihn: "Oase, drei Kilometer nordwestlich vom Wrack" – die Verfolger
dürfen nicht erfahren, wo die Oase liegt. Von Hand gerechnet wird "OASE DREI
KILOMETER", den Rest löst der Knopf auf.

**Reale Anwendung – Empfangen (zweiter und letzter Bob-Kontakt):** Antwort
trifft verschlüsselt in Vigenère ein. Entschlüsselt ergibt sich: "Verstanden,
Hilfe ist unterwegs."

**Abschluss:** Nach dem Entschlüsseln erscheint der Button "Warten". Ein
ruhiger Nachthimmel-Bildschirm blendet ein, dann Rettungsgeräusche – ein
Hubschrauber landet. Abschlusstext: "Du bist raus – lebend, aber mit leeren
Händen. Der Diamantensack liegt noch im Wrack in der Wüste. Manchmal ist das
Überleben der einzige Gewinn, den man mitnehmen kann."

*Nachträglich entschieden:* Der Knopf "Warten" steht schon im Nachtlager unter
dem Sternenhimmel. Danach fallen der Figur die Augen zu, die Nacht vergeht, und
am Morgen weckt sie das Geräusch der Rotorblätter. Weil die Crew von Polizei,
CIA und Interpol gejagt wird, zeigt der Hubschrauber groß den goldenen
Diamanten der Crew – so ist klar, dass Freunde kommen und keine Verfolger.

---

### Notiz für Entwicklung:

#### **Lange Funksprüche werden nur zum Teil von Hand gerechnet**

Nachträglich entschieden, nachdem die Längen ausgezählt waren: Bobs erste
Antwort hat 78 Buchstaben, der abgefangene Funkspruch 76. Die vollständig von
Hand zu entschlüsseln passt nicht in die festen Zeitfenster und ist vor allem
demotivierend.

Die Wortlaute oben bleiben deshalb inhaltlich unverändert – einzige Ausnahme:
Zahlen werden ausgeschrieben ("QUADRANT VIER" statt "QUADRANT 4"), weil die
Textkonvention Ziffern entfernt und der Funkspruch sonst seine Aussage
verlöre. Gelöst wird die Länge über eine Teilaufgabe: Die Spielenden rechnen den Anfang selbst (15–25 Buchstaben, immer
bis zu einer Wortgrenze), danach löst ein Knopf den Rest auf, begleitet von
einem kurzen Erzähltext. Der volle Geheimtext bleibt dabei sichtbar – sonst
ginge in Level 2 verloren, dass er lang ist, und genau darauf beruht der
Merksatz zur Häufigkeitsanalyse.

Die Aufteilung steht in `content/story.py`, die vollständige Begründung und
die Folgen für die Phasen 4, 5 und 6 in `CLAUDE.md`.


#### **Adaptive Zusatzaufgaben (Timer):**

- Zeit **pro Level/Aufgabe** messen, nicht die gesamte Spielöffnungsdauer (sonst verfälscht durch Pausen/Ablenkung).
- Zusatzaufgaben dürfen die festen Zeitfenster (im Konzept 15/20/25 Min, seit dem Pilotdurchlauf 15/10/25, siehe A4 und `game/zeitfenster.py`) nicht verlängern – sonst ist der Vergleich mit der Frontalunterrichts-Gruppe (60 bzw. jetzt 50 Min gesamt) nicht mehr sauber. Zeitfenster endet → weiter zum nächsten Level, egal wie viele Zusatzaufgaben offen sind.
- Schwellenwert ("zu schnell") vor dem eigentlichen Test mit einem kleinen Pilotdurchlauf kalibrieren, statt ihn zu schätzen.

**Fehlerhandling / Lösungsanzeige:**

- Falscheingabe wird blockiert, mit konkretem Hinweis, was falsch ist – identisch im Buch und bei echten Funksprüchen.
- Nach 3 erfolglosen Versuchen: Lösung anzeigen.
- "Fast richtig"-Erkennung ist ein sinnvolles Extra, aber Zusatzaufwand – realistisch einplanen.
- Wichtig: protokollieren, wie viele Versuche jemand brauchte und ob die Lösung angezeigt wurde – das ist für eure spätere Prozess-/Lernerfolgsauswertung (60 % Prozessnote) ein wertvoller Datenpunkt.

## Erklärungen für das Handbuch: