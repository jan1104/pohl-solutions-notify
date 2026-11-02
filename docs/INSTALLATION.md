# Installation

## Voraussetzungen

- Eine Home-Assistant-Installation mit Zugriff auf den Konfigurationsordner
  und der Möglichkeit, Custom-Integrationen zu laden.
- Ein HA-Administratorkonto für die Einrichtung.
- Für mobile Benachrichtigungen: eingerichtete Home Assistant Companion App
  und ein vorhandener Dienst `notify.mobile_app_<geraet>`.
- Für Browser-Popups: Browser Mod und dort registrierte Browser.
- Für Verlaufsbilder: Recorder und ein numerischer Sensor mit aufgezeichnetem Verlauf.

Der Quellstand importiert `probatio` und verwendet aktuelle HA-Schnittstellen.
Die genaue unterstützte HA-Version muss noch in einer realen Testinstallation
bestätigt werden. Bei `ModuleNotFoundError: probatio` die HA-Version prüfen;
nicht wahllos Pakete in einer verwalteten HA-Installation nachinstallieren.
Die aktuelle [HA-Entwicklerdokumentation](https://contributors.home-assistant.io/core/development/input-validation/)
beschreibt diese Validierungsbibliothek.

## Dateien kopieren

Die fertige Verzeichnisstruktur in Home Assistant muss so aussehen:

```text
config/
  custom_components/
    alarm_system/
      __init__.py
      manifest.json
      config_flow.py
      frontend/
        panel.js
      ...
```

Nur den Integrationsordner kopieren; `.git`, Dokumentation, Tests und
`__pycache__` gehören nicht zur Installation. Danach Home Assistant neu starten.
Es wird kein Eintrag in `configuration.yaml` benötigt. HACS-Verteilung und
HACS-Validierung sind in diesem Projekt noch nicht eingerichtet.

## Ersteinrichtung

1. Integration über **Einstellungen → Geräte & Dienste** hinzufügen.
2. Eine eigene Standortkennung eintragen; `LW20` ist lediglich der mitgelieferte Standard.
3. In **Alarme** als Administrator vorhandene HA-Konten hinzufügen und Alarmarten zuweisen.
4. Geräte zuordnen, Companion-Notify-Dienst bzw. Browser auswählen und Kategorien einrichten.
5. Feuer- und Einbruchtest pro Gerät durchführen, beenden und bestätigen.
   Reguläre Empfänger werden nur berücksichtigt, wenn Gerät und Benutzer aktiviert,
   die Alarmart zugewiesen und das Gerät als getestet markiert sind.
6. Vorhandene `binary_sensor`-Entitäten als Melder zuordnen.

## Hinweise für das Update auf 0.3.25

Die Rückmeldung „Ich komme“ wirkt jetzt nur auf das ausgewählte Ereignis. Falls eigene
Automationen bisher die Attribute `site_id` oder `incidents` von
`sensor.alarm_system_active` verwenden, müssen sie angepasst werden: Diese Attribute
werden zur Begrenzung ungewollter Datenweitergabe nicht mehr bereitgestellt.
Der Sensorzustand (Anzahl aktiver Alarme) bleibt bestehen.

Verlaufsbilder liegen nicht mehr öffentlich unter `/local/`. Prüfe nach dem Update
den authentifizierten Bildabruf auf Android und iOS. Bei der ersten Einrichtung und
stündlich entfernt die Integration alte generierte UUID-PNGs aus ihrem bisherigen
öffentlichen Bildordner. Bereits extern gespeicherte Kopien lassen sich dadurch nicht zurückrufen.

## Aktualisieren und Entfernen

Vor einem Update eine vollständige HA-Sicherung erstellen. Danach den Integrationsordner
bei gestopptem Home Assistant ersetzen und HA neu starten. Bei veraltetem Frontend
Browser neu laden und gegebenenfalls den Cache leeren.

Zum Entfernen zuerst aktive Ereignisse beenden und die Wiederherstellung geänderter
Telefoneinstellungen abwarten. Danach die Integration über HA entfernen, HA stoppen
und den Integrationsordner löschen. Das Entfernen der Integration ist kein zugesicherter
Löschvorgang für alle gespeicherten Daten; siehe [Datenspeicherung](ARCHITECTURE.md).
