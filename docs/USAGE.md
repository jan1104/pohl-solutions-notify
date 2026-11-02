# Bedienung und Aktionen

## Meldungen und Alarme

`INFO` und `WARNING` sind Nachrichten. `FIRE` und `INTRUSION` erzeugen gespeicherte
Ereignisse. Mehrere Melder derselben Ereignisgruppe (`alarm_key`) werden zusammengeführt.
Feuer und Einbruch müssen verschiedene Ereignisgruppen verwenden.

Im Panel **Alarme** verwalten Administratoren Benutzer, Geräte, Melder und Einstellungen.
Andere Benutzer erhalten eine nach Konto und Alarmart gefilterte Ansicht.
Die Rückmeldung **Ich komme** stoppt im übernommenen Modell die Tonwiederholung
aller derzeit aktiven regulären Ereignisse. Sie beendet die Ereignisse nicht.
Gerätetests werden dabei getrennt behandelt.

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

Die JSON-Sicherung enthält Einstellungen und Zuordnungen, keine Ereignisse und keinen
Alarmverlauf. Ein Import muss zum Standort passen, setzt vorhandene HA-Konten, Sensoren
und Notify-Dienste voraus und verlangt erneute Geräteprüfung. Während aktiver Ereignisse
oder ausstehender Wiederherstellung ist ein Import gesperrt.

Der CSV-Export enthält Verlaufsdaten. Beide Exporte können personenbezogene Namen,
Gerätekennungen oder Standortdaten enthalten und gehören nicht ins Git-Repository.
Die Aufbewahrung ist anfangs unbegrenzt und kann im Panel geändert werden.
