# HACS-Download ab 0.4.1

## Ursache der gemeldeten Ablehnung

Der vom Nutzer gewählte Commit `47f170b` enthält keine `hacs.json` im Repository-Hauptverzeichnis. HACS liest diese Datei für die gewählte Revision; kann es sie nicht laden, entsteht die gemeldete Ablehnung. Der Hash selbst ist keine ungültige Versionsnummer.

0.4.1 ergänzt die Datei und die Metadaten `documentation`, `issue_tracker`, `codeowners`. HACS verwendet die Quellen unter `custom_components/alarm_system`, keine Release-ZIP-Anlage. Die vorhandenen Installations-ZIPs behalten ihren bisherigen Aufbau.

## Veröffentlichung und Auswahl

Am 03.11.2026 hat der Benutzer Push und Veröffentlichung freigegeben. `develop`, `v0.4.0` und `v0.4.1` wurden übertragen. Das [GitHub-Release v0.4.1](https://github.com/jan1104/pohl-solutions-notify/releases/tag/v0.4.1) ist veröffentlicht; `hacs.json` ist unter diesem Tag über die GitHub-API abrufbar. `main` und die alten Tags bleiben erhalten. Der Defaultbranch bleibt `main`; in HACS ausdrücklich das neue Release auswählen.

Nach Veröffentlichung: Repository in HACS aktualisieren, im Downloaddialog die neue Version auswählen, herunterladen und Home Assistant neu starten. Wenn dort weiterhin `47f170b` erscheint, ist die Auswahl noch alt. Bleibt der Fehler trotz neuer Auswahl, HA-/HACS-Version und den zugehörigen HACS-Logauszug prüfen; darin keine Tokens oder privaten Daten weitergeben.

Vor einem praktischen Update vollständige HA-Sicherung erstellen; Hinweise zu eigenen Alarmarten und Rückkehr in [VERSIONS.md](VERSIONS.md) beachten. Es wurde keine echte HACS-Installation getestet.

## Offizielle Quellen

- [HACS-Allgemeine Anforderungen und Releases](https://www.hacs.xyz/docs/publish/start/)
- [HACS-Integrationslayout und Manifest](https://www.hacs.xyz/docs/publish/integration/)
- [HACS-Downloadprüfung `_ensure_download_capabilities`](https://github.com/hacs/integration/blob/main/custom_components/hacs/repositories/base.py)

## Aktuelles Update 0.4.2

Am 03.11.2026 wurde zusätzlich [v0.4.2](https://github.com/jan1104/pohl-solutions-notify/releases/tag/v0.4.2) veröffentlicht. Für die verständliche Sprachtexteingabe und Informationssprache dieses Release auswählen. Ältere Angaben zu v0.4.1 erklären die ursprüngliche HACS-Korrektur.

## Melderzuordnung 0.4.4

[Release v0.4.4](https://github.com/jan1104/pohl-solutions-notify/releases/tag/v0.4.4) enthält die einzelne Meldungsart-Auswahl und automatische Gruppierung. Dieses Release in HACS wählen. Übergang alter laufender Gruppen und Fehlalarm-Sperren siehe [CUSTOM_ALARM_TYPES.md](CUSTOM_ALARM_TYPES.md).

## Ausgabetests und Empfängerübersicht 0.5.0

[Release v0.5.0](https://github.com/jan1104/pohl-solutions-notify/releases/tag/v0.5.0) ergänzt Einzeltests und die Vorschau wirksamer Ausgaben. Dieses Release in HACS auswählen, nach Installation HA neu starten. Anleitung: [OUTPUT_TESTS.md](OUTPUT_TESTS.md).
