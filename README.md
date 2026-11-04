# Pohl Solutions Alarm Notify

Benachrichtigungen und Alarmverwaltung für **Home Assistant**, entwickelt unter
der Marke **Pohl Solutions**. Die Anwendung wird als Custom-Integration innerhalb
von Home Assistant betrieben; sie ist keine eigenständige Smartphone-App.

**Softwarestand:** 0.5.7 · **Integration-Domain:** `alarm_system`

## Funktionen

- Informationen (`INFO`) und Warnungen (`WARNING`) versenden.
- Feuer- und Einbruchereignisse (`FIRE`, `INTRUSION`) sowie bis zu 32 eigene Alarmarten mit mehreren Meldern verwalten.
- Eigene Namen, Empfängerzuordnung, Priorität, Ausgaben und Sprachtexte je Alarmart einstellen.
- HA-Benutzer, Alarmarten, Mobilgeräte und Browser zuordnen.
- Benachrichtigungen über die Home Assistant Companion App; Browser-Popups über Browser Mod.
- Rückmeldungen, Fehlalarm-Bestätigung, Melderbeendigung und Ereignisverlauf.
- Geräteprüfung, konfigurierbare Aufbewahrung, CSV-Verlauf und JSON-Konfigurationssicherung.

## Installation und Einrichtung

1. Den Ordner `custom_components/alarm_system` nach
   `<HA-Konfigurationsordner>/custom_components/alarm_system` kopieren.
2. Home Assistant neu starten.
3. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen**
   nach **Pohl Solutions Alarm Notify** suchen.
4. Eine Standortkennung vergeben und danach in der Seitenleiste **Alarme**
   Benutzer, Geräte und Melder einrichten.
5. Die Geräteprüfung für Feuer und Einbruch vollständig durchführen und abschließen.

Details, Voraussetzungen und Aktualisierung: [Installationsanleitung](docs/INSTALLATION.md).

## Dokumentation

- [Bedienung und Aktionen](docs/USAGE.md)
- [Schalter für Sprache, Ton, Push und Alarmfenster](docs/OUTPUT_SETTINGS.md)
- [Eigene Alarmarten und individuelle Einstellungen](docs/CUSTOM_ALARM_TYPES.md)
- [Architektur, Daten und Grenzen](docs/ARCHITECTURE.md)
- [Entwicklung und Prüfungen](CONTRIBUTING.md)
- [Vorbereitung für GitHub](docs/GITHUB.md)
- [Import und Herkunft](docs/IMPORT.md)
- [Prüfprotokoll](docs/VERIFICATION.md)
- [Projektanalyse des Ausgangsstands](docs/PROJECT_REVIEW.md)
- [Arbeitsplan und aktueller Status](docs/WORK_PLAN.md)
- [Detaillierte priorisierte Arbeitsliste](docs/DEVELOPMENT_BACKLOG.md)
- [Praktische HA- und Geräteprüfung](docs/HA_TEST_PROTOCOL.md)
- [Gesicherte Versionen und Rückkehr](docs/VERSIONS.md)
- [Änderungen](CHANGELOG.md)
- [Rechtehinweis](LICENSE)

## Entwicklungsstand

Der Ausgangsstand 0.3.24 stammt aus der bereitgestellten ZIP. Der lokale Stand 0.5.7
enthält Korrekturen für parallele Alarmzustellung, ereignisbezogene Rückmeldungen,
Android-Wiederherstellung sowie Konten- und Bildzugriffe. Zusätzlich werden
Startfehler aufgeräumt, Verwaltungskennungen geprüft und importierte Testsitzungen zurückgesetzt.
Fehler einzelner Listener beim Stoppen verhindern die weitere Bereinigung nicht mehr;
nach Stopbeginn eintreffende Ereignisse werden abgefangen. Vor Sprachansagen wird
die Gerätepriorität erneut geprüft; Aufräumfehler nach Startfehler verdecken nicht
mehr die ursprüngliche Ursache. Die lokalen Prüfungen
prüfen Syntax, Projektmetadaten, Alarmregeln, Engine-Abläufe und Bildzugriffe mit
ersetzten Home-Assistant-Grenzen. Eigene Alarmarten, Zuordnungen, Testrechte und Schema-2-Sicherungen sind lokal geprüft. Die Android-Sprachansage ist unabhängig vom
Alarmton schaltbar; der Einrichtungsablauf und die Schalter werden zusätzlich mit Node.js geprüft.
Ein vollständiger Test in einer laufenden Home-Assistant-Installation mit echten
Companion-Geräten und Browser Mod steht noch aus. Eine konkrete Mindestversion
von Home Assistant ist noch nicht durch einen solchen Test bestätigt.

## Rechte

Copyright (c) 2026 Pohl Solutions. Alle Rechte vorbehalten.
Es wird keine Open-Source-Lizenz erteilt. Siehe [LICENSE](LICENSE).

HACS-Installation und Hinweis zum Downloadfehler von `47f170b`: [HACS-Anleitung](docs/HACS.md).

Gezielte Ausgabetests und Empfängerübersicht: [Ausgaben testen und Wer bekommt was?](docs/OUTPUT_TESTS.md).
