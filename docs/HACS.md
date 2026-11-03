# HACS-Download ab 0.4.1

## Ursache der gemeldeten Ablehnung

Der vom Nutzer gewählte Commit `47f170b` enthält keine `hacs.json` im Repository-Hauptverzeichnis. HACS liest diese Datei für die gewählte Revision; kann es sie nicht laden, entsteht die gemeldete Ablehnung. Der Hash selbst ist keine ungültige Versionsnummer.

0.4.1 ergänzt die Datei und die Metadaten `documentation`, `issue_tracker`, `codeowners`. HACS verwendet die Quellen unter `custom_components/alarm_system`, keine Release-ZIP-Anlage. Die vorhandenen Installations-ZIPs behalten ihren bisherigen Aufbau.

## Was noch nötig ist

Die Korrektur ist zunächst lokal. HACS lädt weiterhin den alten Commit, solange keine korrigierte Revision auf GitHub angeboten und ausgewählt wird. Ein Push ausschließlich auf `develop` ändert den unveränderten Defaultbranch `main` nicht.

Vorgesehene Veröffentlichung nach ausdrücklichem Auftrag: `develop` und den neuen Tag `v0.4.1` übertragen und ein GitHub-Release zu diesem Tag erstellen. Dabei `main` und bisherige Tags erhalten. Der Release-Text muss auf neue Alarmarten und die noch offene echte HA-/Android-Prüfung hinweisen. Ein bloßer Git-Tag ist keine GitHub-Release-Auswahl in HACS.

Nach Veröffentlichung: Repository in HACS aktualisieren, im Downloaddialog die neue Version auswählen, herunterladen und Home Assistant neu starten. Wenn dort weiterhin `47f170b` erscheint, ist die Auswahl noch alt. Bleibt der Fehler trotz neuer Auswahl, HA-/HACS-Version und den zugehörigen HACS-Logauszug prüfen; darin keine Tokens oder privaten Daten weitergeben.

Vor einem praktischen Update vollständige HA-Sicherung erstellen; Hinweise zu eigenen Alarmarten und Rückkehr in [VERSIONS.md](VERSIONS.md) beachten. Es wurde keine echte HACS-Installation getestet.

## Offizielle Quellen

- [HACS-Allgemeine Anforderungen und Releases](https://www.hacs.xyz/docs/publish/start/)
- [HACS-Integrationslayout und Manifest](https://www.hacs.xyz/docs/publish/integration/)
- [HACS-Downloadprüfung `_ensure_download_capabilities`](https://github.com/hacs/integration/blob/main/custom_components/hacs/repositories/base.py)
