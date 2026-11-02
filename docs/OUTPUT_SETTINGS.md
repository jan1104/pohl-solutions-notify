# Sprache, Alarmton, Push und Alarmfenster

Stand: 0.3.27. Einstellungen pro Gerät unter **Alarme → Geräte → Bearbeiten**;
im Schritt **Alarmansicht** das gewünschte Verhalten wählen und die Geräteprüfung abschließen.

| Schalter | Android | iPhone | Browser |
| --- | --- | --- | --- |
| Push-Nachrichten | Ein / aus | Ein / aus | Nicht verfügbar |
| Alarmton | Ein / aus | Ein / aus | Nicht verfügbar |
| Sprachansage | Ein / aus, unabhängig vom Alarmton | Nicht implementiert | Nicht implementiert |
| Alarmfenster | Ein / aus mit Browser Mod | Ein / aus mit Browser Mod | Ein / aus mit Browser Mod |

## Sprachansage und Ton unabhängig wählen

- **Nur Sprache:** Alarmton aus, Sprachansage ein.
- **Nur Alarmton:** Alarmton ein, Sprachansage aus.
- **Ton und Sprache:** Beide ein. Erst Alarmton, danach die Sprachansage.
- **Keine erzwungene Audioausgabe:** Beide aus. Push und Alarmfenster lassen sich weiter verwenden.
- Alle Ausgaben dürfen bewusst ausgeschaltet werden; für vollständige Stilllegung eines
  Geräts kann zusätzlich **Gerät aktiv** ausgeschaltet werden.

Die Sprache nennt Alarmart, Standort und zugeordnete Bereiche. Sie gilt für die
Feuer-/Einbruchalarmierung auf Android. Die konfigurierbare Sprachzeit steuert die
Wartezeit für die Ansage; sie ist kein Nachweis oder garantierter harter Schnitt
am Ende einer tatsächlich gesprochenen Nachricht.

Ohne Alarmton verlangt der Assistent keine Rufton-/Benachrichtigungslautstärkesensoren.
Sprachansagen verwenden den vorübergehenden `alarm_stream_max` der Companion-App;
die Integration ändert dafür keine Rufton- oder Benachrichtigungslautstärkewerte.
Ein eigener gespeicherter Sprachauftrag ermöglicht Stop-/Wiederholungsanforderungen
auch nach Unterbrechung. Echte Audioausgabe und Wiederherstellung des temporären
Companion-Audiostreams müssen auf dem Zielgerät geprüft werden.

## Was der Push-Schalter bedeutet

Push aus unterbindet normale Info-/Warnmeldungen und die reguläre stumme Alarmnachricht.
Ein eingeschalteter Alarmton benötigt unter Android jedoch weiterhin eine technische
Benachrichtigung und kann sie anzeigen. Der Push-Schalter bedeutet daher nicht,
dass bei gleichzeitig eingeschaltetem Alarmton jede Benachrichtigung unsichtbar ist.
Bei Problemen mit der Wiederherstellung bleibt die bisherige Ersatzmeldung für
aktivierte Alarmtöne erhalten.

Normale Info-/Warnmeldungen können entsprechend den Android-/iOS-Benachrichtigungseinstellungen
Töne haben, auch wenn der separate **Alarmton** für Feuer/Einbruch aus ist.
Für ausdrücklich stumme Android-Meldungen verwendet die Integration `Alarmstatus`
mit niedriger Wichtigkeit beim Anlegen. Bereits bestehende oder vom Benutzer geänderte
Android-Kanaleinstellungen werden dadurch nicht zuverlässig überschrieben.

## Update von 0.3.26

Vorher hatte Sprachansage ein bei ausgeschaltetem Alarmton keine Wirkung. Ab 0.3.27
wird diese Kombination als **nur Sprache** ausgeführt. Prüfe nach dem Update die
Geräteeinstellungen: Für ein stilles Gerät müssen Alarmton **und** Sprachansage aus sein.

Änderungen an den Ausgabeoptionen, Tönen oder Zeiten verlangen eine neue Geräteprüfung.
Die Plattformregeln gelten auch für direkte Verwaltungsaufrufe und JSON-Importe;
beispielsweise wird kein unbrauchbarer Sprachschalter für iOS gespeichert.

## Prüfstand

Automatisch geprüft: Ausgabe-Kombinationen, Sprachabbruch, fehlgeschlagener Stop,
Gerätefreigabe nach Änderungen, unterstützte Plattformschalter und Assistentenschritte.
Die Node.js-Prüfungen führen die tatsächlichen Oberflächenmethoden aus, ersetzen jedoch
die Browser-Grundobjekte. Es fand kein visueller oder physischer Gerätetest statt.
