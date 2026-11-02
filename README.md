# Pohl Solutions Alarm Notify

Benachrichtigungen und Alarmverwaltung für **Home Assistant**, entwickelt unter
der Marke **Pohl Solutions**. Die Anwendung wird als Custom-Integration innerhalb
von Home Assistant betrieben; sie ist keine eigenständige Smartphone-App.

**Softwarestand:** 0.3.24 · **Integration-Domain:** `alarm_system`

## Funktionen

- Informationen (`INFO`) und Warnungen (`WARNING`) versenden.
- Feuer- und Einbruchereignisse (`FIRE`, `INTRUSION`) mit mehreren Meldern verwalten.
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
- [Architektur, Daten und Grenzen](docs/ARCHITECTURE.md)
- [Entwicklung und Prüfungen](CONTRIBUTING.md)
- [Vorbereitung für GitHub](docs/GITHUB.md)
- [Import und Herkunft](docs/IMPORT.md)
- [Prüfprotokoll](docs/VERIFICATION.md)
- [Änderungen](CHANGELOG.md)
- [Rechtehinweis](LICENSE)

## Entwicklungsstand

Der Quellstand wurde aus der bereitgestellten ZIP übernommen. Die lokalen Prüfungen
prüfen Syntax, Projektmetadaten und ausgewählte Regeln der Alarmverwaltung.
Ein vollständiger Test in einer laufenden Home-Assistant-Installation mit echten
Companion-Geräten und Browser Mod steht noch aus. Eine konkrete Mindestversion
von Home Assistant ist noch nicht durch einen solchen Test bestätigt.

## Rechte

Copyright (c) 2026 Pohl Solutions. Alle Rechte vorbehalten.
Es wird keine Open-Source-Lizenz erteilt. Siehe [LICENSE](LICENSE).
