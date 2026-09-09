"""Tkinter-Oberfläche: Fenstergerüst und die einzelnen Screens.

Hier werden als einziger Stelle Bedienelemente gebaut. Tkinter selbst wird
ausserdem von ``main.py`` importiert – der Einstiegspunkt öffnet das
Hauptfenster und fängt die beiden Startfehler ab (Tkinter fehlt, keine
Bildschirmanzeige). ``crypto/``, ``game/`` und ``content/`` dürfen Tkinter
dagegen nie anfassen; ``tests/test_zusammenspiel.py`` prüft das.
"""
