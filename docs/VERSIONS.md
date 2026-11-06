# Gesicherte Versionen und Rückkehr

Stand: 03.11.2026. Neuer Stand 0.5.7 veröffentlicht; kein Deployment.
Die älteren Branches und Tags wurden am 03.11.2026 auf ausdrücklichen Nutzerauftrag zu GitHub gepusht; 0.4.0 noch nicht.

| Stand | Fester Git-Tag | Quellcommit | Einordnung |
| --- | --- | --- | --- |
| 0.5.11 | `v0.5.11` | über Tag auflösbar | Ungültige importierte Sensorreferenzen vor Ton-/Popup-Fehlern abweisen; nur lokal, kein HACS-Release |
| 0.5.10 | `v0.5.10` | über Tag auflösbar | Sensorverfügbarkeit ohne doppelte Verlaufseinträge/Speicherungen; nur lokal, kein HACS-Release |
| 0.5.9 | `v0.5.9` | über Tag auflösbar | Ungültige importierte Gerätezeiten kontrolliert abgewiesen; nur lokal, kein HACS-Release |
| 0.5.8 | `v0.5.8` | über Tag auflösbar | Veraltete Rückmeldungen kontrolliert abgewiesen; nur lokal, kein HACS-Release |
| 0.5.7 | `v0.5.7` | über Tag auflösbar | Ausgabenprobe direkt bei jedem Melder; HACS-Release veröffentlicht |
| 0.5.6 | `v0.5.6` | über Tag auflösbar | Kompakter Alarmarten-Dialog; HACS-Release veröffentlicht |
| 0.5.5 | `v0.5.5` | über Tag auflösbar | Parallele Empfangsdiagnose und lesbarer Detailverlauf; HACS-Release veröffentlicht |
| 0.5.4 | `v0.5.4` | über Tag auflösbar | Zeiten bei Alarmarten, bisherige Gerätewerte erhalten; HACS-Release veröffentlicht |
| 0.5.3 | `v0.5.3` | über Tag auflösbar | Entladebereinigung nach Fehlern wiederholbar; HACS-Release veröffentlicht |
| 0.5.2 | `v0.5.2` | über Tag auflösbar | Mehrdeutige Importschalter abgewiesen; nur lokal, kein HACS-Release |
| 0.5.1 | `v0.5.1` | über Tag auflösbar | Bestätigungskennungen korrigiert; nur lokaler Checkpoint, kein HACS-Release |
| 0.5.0 | `v0.5.0` | über Tag auflösbar | Einzeltests und Empfängerübersicht; HACS-Release veröffentlicht |
| 0.4.5 | `v0.4.5` | über Tag auflösbar | Kompakter zugeklappter Alarmverlauf; HACS-Release veröffentlicht |
| 0.4.4 | `v0.4.4` | über Tag auflösbar | Eine Meldungsart pro Melder, automatische Gruppen; HACS-Release veröffentlicht |
| 0.4.3 | `v0.4.3` | über Tag auflösbar | Standard-Sprachtext immer sichtbar, HACS-Release veröffentlicht |
| 0.4.2 | `v0.4.2` | über Tag auflösbar | Sprachtext mit Vorschau; unabhängige Ausgaben auch für Information/Warnung |
| 0.4.1 | `v0.4.1` | über Tag auflösbar | HACS-Metadaten korrigiert; lokal geprüft, GitHub-Release offen |
| 0.4.0 | `v0.4.0` | über Tag auflösbar | Eigene Alarmarten, lokal geprüft; echte HA-/Android-Prüfung offen |
| 0.3.27 | `v0.3.27` | `47f170b` | Aktueller eingefrorener Quellstand; 75 Python- und sieben Frontendtests bestanden |
| 0.3.25 | `v0.3.25` | `c76c70f` | Lokaler Stand zur vom Benutzer als bereits gelaufen gemeldeten Versionsnummer |

Der auf dem Handy tatsächlich installierte Quellinhalt wurde nicht aus HA ausgelesen.
Deshalb ist die Zuordnung von 0.3.25 zur Nutzerangabe keine zusätzliche technische
Prüfung der Installation. 0.3.27 wurde noch nicht auf echten Geräten bestätigt.

## Weitere Entwicklung

`main` bleibt auf `47f170b`. Die weitere Arbeit einschließlich Verpackungswerkzeug
und dieser Dokumentation erfolgt auf `develop`. Die Tags halten exakt den damaligen
Inhalt fest, unabhängig von späteren Änderungen. Keine dieser Marken automatisch
verschieben oder durch ein erzwungenes Update ersetzen.

Der Benutzer hat Subagenten für geeignete Programmieraufgaben gewünscht. Kleine,
abgrenzbare Aufgaben können kleinere Modelle bearbeiten; der Hauptagent prüft und
integriert das Ergebnis. So werden parallele Änderungen an denselben Dateien vermieden.

## Installation aus einer gesicherten Version

Das lokale Werkzeug erstellt Installations-ZIPs ausschließlich aus Git-Tags:

```powershell
python scripts/package_snapshot.py --ref v0.4.0
python scripts/package_snapshot.py --ref v0.3.27
python scripts/package_snapshot.py --ref v0.3.25
```

Die neue Datei liegt unter `dist/alarm_system-0.4.0.zip`; die älteren Dateien unter
`dist/alarm_system-0.3.27.zip` und
`dist/alarm_system-0.3.25.zip`. Sie enthalten nur die verfolgten Integrationsdateien
unter `custom_components/alarm_system`, keine Caches, Dokumentation oder privaten
HA-Daten. Bereits vorhandene Pakete werden nicht überschrieben. Weitere Kopien in
anderen Zielordnern lassen sich mit `--output-dir` erstellen.

Die aktuelle Windows-Python-Umgebung ist in [WORK_PLAN.md](WORK_PLAN.md) angegeben.
Die ursprünglichen SHA-256-Werte und Quellcommits stehen in `dist/snapshots.json`;
für 0.4.0 in `dist/snapshot-0.4.0.json`. Eine zusätzliche Historienkopie zu diesem
Stand ist `dist/pohl-solutions-notify-history-0.4.0.bundle`.
Ein zusätzliches Git-Bundle unter `dist/pohl-solutions-notify-history.bundle`
sichert die lokale Versionshistorie einschließlich Tags und Entwicklungszweig zum
Zeitpunkt seiner Erstellung. Spätere Commits sind darin erst nach einer erneuten,
separaten Sicherung enthalten. `dist` wird nicht in Git aufgenommen.

## Eigene Alarmarten ab 0.4.0

0.4.0 ergänzt persistente Alarmprofile und Konfigurationssicherungen mit Schema 2.
Vor einem praktischen Update eine vollständige Sicherung der bisherigen HA-Instanz
anlegen. Ältere Versionen verstehen selbst definierte Alarmarten in den Laufzeitdaten
nicht. Bei einem Downgrade gegebenenfalls die zur alten Version passende vollständige
HA-Sicherung verwenden. Die alten Quell-Tags und ZIPs werden nicht überschrieben.

## Sicher zurückkehren

**Quellcode:** Die Tags können unabhängig vom Entwicklungszweig als ZIP ausgepackt
oder in einem separaten Verzeichnis betrachtet werden. Kein `git reset --hard` und
keine uncommitteten Änderungen für einen Rücksprung löschen. Ein separater Checkout
lässt sich bei Bedarf beispielsweise so anlegen:

```powershell
git worktree add --detach ..\pohl-solutions-notify-0.3.27 v0.3.27
```

Das neue Verzeichnis muss noch frei sein. Im eigentlichen Arbeitsordner bleibt
`develop` unverändert.

**Home Assistant:** Ein Quellcode-Tag sichert weder HA-Einstellungen noch Ereignisse
oder ursprüngliche Handyeinstellungen. Vor jedem praktischen Update eine vollständige
HA-Sicherung erstellen und ihr die Integrationsversion zuordnen. Vor einem Downgrade
aktive Alarme und Gerätetests beenden, die Wiederherstellung am Handy abwarten und
dann HA stoppen. Anschließend den Integrationsordner durch das gewählte Paket ersetzen
und wieder starten. Bei Problemen mit Laufzeitdaten die zur Version passende vollständige
HA-Sicherung verwenden, statt interne Speicherdateien willkürlich zu bearbeiten.

Insbesondere kennt 0.3.25 die später eingeführten reinen Sprachaufträge nicht. Nicht
mit ausstehenden Sprach-/Wiederherstellungsaufträgen auf diese Version zurückgehen.
Lokale Git-Snapshots ermöglichen die exakte Rückkehr zum Code; sie garantieren keine
verlustfreie Rückwärtsmigration fremder HA-Laufzeitdaten.

## Unabhängige Sicherung

ZIPs und Bundle auf demselben Rechner schützen vor versehentlichen Codeänderungen,
aber nicht vor Ausfall dieses Rechners. Für eine unabhängige Kopie diese Dateien auf
ein anderes Laufwerk oder ein vorhandenes Sicherungsziel kopieren. Es wurde dafür
kein neues externes Konto oder Cloudspeicher eingerichtet.

Am 04.11.2026 zusätzlich v0.5.1 nur lokal für die Bestätigungsfehlerkorrektur gesichert; letztes veröffentlichtes HACS-Release bleibt v0.5.0.

Am 04.11.2026 nach Nutzerauftrag develop und Tags v0.5.1–v0.5.3 gepusht und Release v0.5.3 erstellt. v0.5.1/v0.5.2 sind darin enthalten, haben keine separaten GitHub-Releases. Frühere lokale Einordnungen sind historisch.
