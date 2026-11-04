# Bedienung und Aktionen

## Meldungen und Alarme

`INFO` und `WARNING` sind Nachrichten. `FIRE` und `INTRUSION` erzeugen gespeicherte
Ereignisse. Im Panel angebundene Melder derselben Alarmart werden ab 0.4.4 automatisch zusammengeführt. Dafür genügt die Auswahl **Art der Meldung**. Direkte Aktionsaufrufe verwenden weiterhin ihre ausdrücklich angegebene Ereignisgruppe (`alarm_key`).
Feuer und Einbruch müssen verschiedene Ereignisgruppen verwenden.

Im Panel **Alarme** verwalten Administratoren Benutzer, Geräte, Melder und Einstellungen.
Andere Benutzer erhalten eine nach Konto und Alarmart gefilterte Ansicht.
Seit Version 0.3.25 stoppt **Ich komme** nur die Tonwiederholung des ausgewählten
Ereignisses. Andere Ereignisse laufen weiter. Die Rückmeldung beendet das Ereignis nicht.
Die Priorität wird pro Gerät bestimmt: Auf einem gemeinsam verwendeten Gerät bleibt
Einbruch vor Feuer priorisiert; weitere Ereignisse erhalten eine stumme Nachricht.
Geräte mit anderen Empfängerzuordnungen führen ihren eigenen Alarmzyklus aus.
Nach einer Rückmeldung wird die Bearbeitung weiterer offener Ereignisse wieder angestoßen.

Deaktivierte Benutzer erhalten außerhalb administrativer HA-Konten keine Alarmansicht,
Melderlisten, Geräte oder Verlaufseinträge mehr. HA-Administratoren behalten ihren
Verwaltungszugriff. Die allgemeine HA-Entität zeigt nur noch die Anzahl aktiver Alarme.

Ein wieder normales Sensorsignal beendet keinen Alarm automatisch. Nach Beenden eines
noch aktiven Melders wird die erneute Auslösung bis zum Normalsignal unterdrückt.
Fehlalarm erfordert den Bestätigungsablauf mit kurzlebigem Token.

## Nachricht aus einer Automation

Beispiel für eine HA-Aktionssequenz; Titel, Nachricht und Gerätezuordnung anpassen:

```yaml
- action: alarm_system.raise_alarm
  data:
    type: INFO
    title: Pohl Solutions
    message: Die Waschmaschine ist fertig.
    silent: true
```

## Feuerereignis auslösen

```yaml
- action: alarm_system.raise_alarm
  data:
    type: FIRE
    alarm_key: fire_house
    source_id: smoke_kitchen
    source_name: Rauchmelder Küche
    area: Erdgeschoss
    detection: Rauch
```

Nach Rückkehr des Melders zum Normalzustand bei manueller Ansteuerung melden:

```yaml
- action: alarm_system.source_normal
  data:
    alarm_key: fire_house
    source_id: smoke_kitchen
```

Bei im Panel registrierten Binary-Sensoren übernimmt die Integration die Signalbeobachtung.
Die Erkennungslogik muss bereits einen fertigen `on`-/`off`-Zustand liefern, z. B. aus Node-RED.

## Aktionsübersicht

| Aktion | Zweck |
| --- | --- |
| `alarm_system.raise_alarm` | Nachricht senden oder Ereignis auslösen |
| `alarm_system.source_normal` | Normalzustand melden und Auslösesperre lösen |
| `alarm_system.respond` | Rückmeldung mit angemeldetem HA-Konto |
| `alarm_system.confirm_false_alarm` | Bestätigung im zugeordneten Browser |

Felder sind in `custom_components/alarm_system/services.yaml` beschrieben. Für Rückmeldungen
vorzugsweise die Oberfläche verwenden: Kontoprüfung und Bestätigungstoken gehören zum Ablauf.
Eine frei angegebene Benutzer-ID ersetzt keine Anmeldung.

## Sicherung und Verlauf

Ab lokalem Stand 0.5.2 müssen Aktivierungs- und Stummschalter in importierten JSON-Sicherungen echte Werte `true` oder `false` sein. Texte wie `"false"` und Zahlen werden mit einem Fehler abgewiesen, bevor Einstellungen ersetzt werden. Reguläre JSON-Exporte enthalten diese Schalter bereits im richtigen Format.

Die JSON-Sicherung enthält Einstellungen und Zuordnungen, keine Ereignisse und keinen
Alarmverlauf. Ein Import muss zum Standort passen, setzt vorhandene HA-Konten, Sensoren
und Notify-Dienste voraus und verlangt erneute Geräteprüfung. Seit 0.3.26 werden dafür auch importierte
alte Testsitzungen und flüchtige Warte-/Wiederherstellungsfelder verworfen. Während aktiver Ereignisse
oder ausstehender Wiederherstellung ist ein Import gesperrt.

Der CSV-Export enthält Verlaufsdaten. Beide Exporte können personenbezogene Namen,
Gerätekennungen oder Standortdaten enthalten und gehören nicht ins Git-Repository.
Die Aufbewahrung ist anfangs unbegrenzt und kann im Panel geändert werden.

## Wiederherstellung und Verlaufsbilder ab 0.3.25

Ursprüngliche Android-Einstellungen bleiben gespeichert, bis die Sensoren sowohl
Ruftonmodus als auch Lautstärke nach der Anforderung aktuell zurückmelden.
Bei fehlender Bestätigung folgt nach frühestens 30 Sekunden ein neuer Versuch.
Der Geräteeintrag zeigt eine ausstehende Wiederherstellung an. Eine stumme
Alarmnachricht bleibt möglich, während die erneute laute Ausgabe ausgesetzt wird.
Ein Gerät kann während ausstehender Wiederherstellung nicht erneut freigegeben werden.

Verlaufsbilder benötigen die HA-Anmeldung und die Berechtigung für die zugehörige
Alarmart. Sie sind höchstens 24 Stunden abrufbar und werden regelmäßig bereinigt.
Der Abruf über die Companion-App muss auf den Zielgeräten noch praktisch getestet werden.

## Ausgabeoptionen ab 0.3.27

Sprachansage und Alarmton sind auf Android unabhängig schaltbar. Die genaue
Schalterwirkung, Plattformgrenzen und Update-Hinweise stehen in [OUTPUT_SETTINGS.md](OUTPUT_SETTINGS.md).

## Eigene Alarmarten ab 0.4.0

Alarmarten mit eigenen Namen, Empfängern und Ausgaben unter **Alarmarten** einrichten.
Die vollständige Anleitung einschließlich Sprachtexten und Schema-2-Sicherung steht
in [CUSTOM_ALARM_TYPES.md](CUSTOM_ALARM_TYPES.md).

Die Umstellung vorhandener Melder sowie laufender alter Gruppen ist in [CUSTOM_ALARM_TYPES.md](CUSTOM_ALARM_TYPES.md) beschrieben.

## Kompakter Verlauf ab 0.4.5

Jeder abgeschlossene Alarm steht zunächst zugeklappt im Verlauf. Datum/Uhrzeit, Status, Alarmart und beteiligte Melder sind sofort sichtbar. Ein Klick oder die Tastatur öffnet Bereiche, Rückmeldungen, Zeitpunkte sowie Verlauf/Transport. Der Aufklappzustand bleibt während automatischer Aktualisierungen erhalten; beim erneuten Öffnen der Seite beginnen die Einträge wieder geschlossen. Aktive Alarme bleiben vollständig sichtbar. Informationen/Warnungen zeigen als Status **Gemeldet**; das ist keine Bestätigung des tatsächlichen Empfangs.

Ab 0.5.0: Unter **Alarmarten → Ausgaben testen** einzelne Ausgaben prüfen. Die Melderzuordnung zeigt **Wer bekommt was?** einschließlich Geräteschaltern und offenen Prüfungen. Siehe [OUTPUT_TESTS.md](OUTPUT_TESTS.md).
