# Entwicklung

Arbeitsordner: `D:\depot\pohl-solutions-notify`. Standardbranch: `main`.
Dieses Repository ist proprietär; diese Anleitung erteilt keine Nutzungsrechte.

## Lokal prüfen

Python 3.12 oder neuer und Node.js bereitstellen. Die Prüfungen benötigen keine
zusätzlichen Python-Pakete und installieren kein Home Assistant:

```powershell
python scripts/validate.py
python -m unittest discover -s tests -v
node --check custom_components/alarm_system/frontend/panel.js
```

`validate.py` prüft Python-Syntax, JSON, Domain und Versionskonsistenz.
Die Verhaltenstests prüfen HA-unabhängige Module und die vollständigen Engine-/Chart-
Module mit schmalen Importadaptern für HA und aiohttp. Ersetzt werden externe Grenzen,
nicht die zu prüfenden Projektmethoden. Geprüft werden unter anderem Melder-Normalisierung,
Auslösesperren, Empfängerberechtigung, Alarmparallelität, Wiederherstellung und Bildzugriffe.
Einstiegshandler werden zusätzlich mit ersetzten HA-/probatio-Dekoratoren und
Schemaobjekten geprüft; diese Adapter validieren keine echten HA-Schemas. Das
ersetzt weder einen echten HTTP-Server noch HA-Laufzeit- und Mobilgerätetests.
Die GitHub-Actions-Konfiguration führt dieselben Prüfungen nach einem späteren Push aus.
Sie enthält weder Deployment noch Veröffentlichung.

## Änderungen und Commits

1. Änderungen auf einem passenden Arbeitsbranch durchführen.
2. Betroffene Dokumentation und `CHANGELOG.md` aktualisieren.
3. Prüfungen ausführen und Änderungen mit `git diff` prüfen.
4. Zusammenhängende Änderungen getrennt committen, beispielsweise mit
   `fix:`, `feat:`, `docs:` oder `chore:`.

Bei einer Softwareversionserhöhung Manifest, `const.py` und Versionsangaben im
Frontend einschließlich Konfigurationsexport sowie README konsistent ändern.
Der reine Repository-Import behielt 0.3.24; die erste funktionale Korrektur trägt 0.3.25.

Keine HA-Sicherungen, persönlichen Exporte, Zugangsdaten oder Laufzeitdateien committen.
Vor Veröffentlichung zusätzlich die Prüfungen in [GITHUB.md](docs/GITHUB.md) abschließen.
