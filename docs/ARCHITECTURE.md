# Architektur und Daten

## Aufbau

| Datei | Aufgabe |
| --- | --- |
| `__init__.py` | Einrichtung, HA-Aktionen, WebSocket-Schnittstellen und Panel |
| `config_flow.py` | Einzelne lokale Integration mit Standortkennung |
| `model.py` | Ereignisse, Quellen, Berechtigungsregeln und Aufbewahrung ohne HA-Importe |
| `engine.py` | Persistenz, Versand, Tonzyklen, Rückmeldungen und Wiederherstellung |
| `configuration.py` | Validierung von Sicherungen und Filterung der Benutzeransicht |
| `discovery.py` | Zuordnung tatsächlicher Companion- und Browser-Mod-Geräte |
| `identity.py` | Anzeigenamen statt interner Konto-UUIDs |
| `charts.py` | PNG-Verlaufsbilder aus Recorder-Daten |
| `chart_storage.py` | Private Bilddateien, Ablaufzeit und Bereinigung ohne HA-Abhängigkeit |
| `chart_view.py` | Angemeldeter Bildabruf mit Alarmartenprüfung |
| `frontend/panel.js` | Oberfläche und Einrichtung ohne zusätzliche Frontend-Bibliothek |

Die technischen Namen `alarm_system`, `alarm-system` und bestehende Aktionsnamen bleiben
zur Kompatibilität erhalten. Produktname ist **Pohl Solutions Alarm Notify**.

## Ablauf

Ein Meldersignal oder eine HA-Aktion erreicht die Engine. Das Modell verwaltet den
Ereigniszustand, die Engine speichert ihn und verteilt Nachrichten an passende Empfänger.
Die Oberfläche liest Daten über `alarm_system/get`; Verwaltung erfolgt über
`alarm_system/manage`, Rückmeldungen über `alarm_system/respond`.

## Datenspeicherung

Die Integration verwendet den HA-Store mit dem Schlüssel `alarm_system.registry_and_events`
unter `.storage`. Er enthält Konfiguration, Benutzer-/Gerätezuordnungen, Ereignisse,
Journal und Wiederherstellungszustände für Geräte. Bestätigungstoken werden nur im
Arbeitsspeicher gehalten. Konfigurations-JSON ersetzt keine vollständige HA-Sicherung.

Seit 0.3.25 liegen Verlaufsbilder privat unter `.storage/alarm_system_charts`.
Eine Metadatendatei speichert Alarmart und Ablaufzeit. Der API-Endpunkt
`/api/alarm_system/charts/<datei>.png` verlangt eine HA-Anmeldung sowie einen aktiven
Administrator oder ein aktives zugeordnetes Konto mit passender Alarmart.
Antworten verwenden `Cache-Control: no-store`. Abgelaufene Bilder werden sofort
abgewiesen; die Dateibereinigung läuft beim Start und stündlich. Frühere öffentliche
Bilder mit dem vom Projekt erzeugten UUID-Dateinamensmuster werden aus dem alten
`www/alarm_system_charts`-Verzeichnis entfernt. Fremde Dateinamen bleiben erhalten.

Die Alarmpriorität gilt pro Gerät. Bereits vorhandene Priorität auf einem gemeinsamen
Gerät (Einbruch vor Feuer) bleibt erhalten. Andere Geräte bleiben davon unabhängig.
Rückmeldungen verändern nur das ausgewählte Ereignis. Für Android behalten Leases
ursprüngliche Werte und einen Wiederholungszeitpunkt, bis frisch gemeldete Sensorwerte
die Wiederherstellung bestätigen. Laufende Tonwiedergaben werden vom Wiederholungsdienst
nicht eigenständig beendet.

## Prüfgrenzen

Die lokale Testserie ersetzt keine Laufzeitprüfung der HA-Anbindung. Insbesondere
Android-Lautstärke/Rufton-Wiederherstellung, iOS-Benachrichtigungen, Browser-Mod-Popups,
Neustart während eines Alarms und Recorder-Bilder müssen auf den tatsächlichen
Zielgeräten geprüft werden. Die Software ist bisher nicht als zertifiziertes
Brand- oder Einbruchmeldesystem bewertet.
