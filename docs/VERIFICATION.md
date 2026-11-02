# Prüfprotokoll

## Lokaler Entwicklungsstand 0.3.25 – 02.11.2026

- 16 Python-Dateien auf Syntax geprüft; drei JSON-Dateien und Versionskonsistenz gültig.
- 39 Verhaltenstests erfolgreich: 12 Modell-/Kontofiltertests, 16 Engine-Regressionen
  und 11 Bildspeicher-/Zugriffstests.
- JavaScript-Syntax erfolgreich geprüft; Änderungen ohne Git-Whitespacefehler.
- Getestet werden der reale Projektcode und explizit ersetzte HA-/aiohttp-Grenzen.
  Keine Behauptung einer echten HA-Laufzeit, tatsächlicher HTTP-Middleware-Anmeldung
  oder Ton-/Bildzustellung auf echten Geräten.
- Aktive chatgebundene Automation für Weiterarbeit alle sechs Stunden eingerichtet
  und Status sowie gespeicherte Wiederholungsregel geprüft.

Die sechs Hauptbefunde aus der historischen Projektanalyse wurden im Anwendungscode
bearbeitet. Gerätefreigabe und Informationsumfang der allgemeinen Alarm-Entität wurden
zusätzlich eingeschränkt. Offene externe Validierung und nächste unabhängige Arbeiten
stehen in [WORK_PLAN.md](WORK_PLAN.md), der praktische Ablauf in
[HA_TEST_PROTOCOL.md](HA_TEST_PROTOCOL.md).

Nicht durchgeführt: Deployment, GitHub-Push, GitHub-Actions-Lauf, vollständiger
HA-Start auf Linux, echte Browseransicht und Companion-/Browser-Mod-Gerätetests.
Die private Bild-API muss insbesondere mit den tatsächlichen Companion-Versionen
geprüft werden. Der öffentliche Bildpfad wird dafür nicht wieder aktiviert.

## Historisches Import-Prüfprotokoll für 0.3.24

Datum: 02.11.2026 · Softwarestand: 0.3.24

### Beim Import lokal erfolgreich

- Python-Syntax aller Integrations-, Test- und Prüfskriptdateien geprüft (Python 3.12).
- Drei JSON-Dateien gelesen; Domain, Config-Flow und Versionskonsistenz geprüft.
- Deutsche Übersetzung mit Quelltext abgeglichen.
- Neun Verhaltenstests erfolgreich: Ereignisgruppen, Duplikate, Alarmarten,
  Normalsignal, Auslösesperre, Rückmeldung, Empfängerauswahl, Import-Standort,
  Benutzeransicht und Anzeigenamen.
- JavaScript-Syntax mit `node --check` erfolgreich geprüft.
- Alle 22 mitgelieferten ZIP-Dateien nach dem Verschieben bytegenau verglichen:
  unverändert; enthaltenen Bytecode von Git ausgeschlossen.
- Suche nach typischen GitHub-Tokenmustern und privaten Schlüsseln ohne Treffer.
  Dies ist kein vollständiges Sicherheitsgutachten.
- GitHub-Remote lesend erreichbar, beim Einrichten ohne Branches und Tags.

### Damals offene Prüfungen

- Vollständiger Laufzeittest in Home Assistant und Bestätigung unterstützter Versionen.
- Geräte-, Benachrichtigungs-, Neustart- und Wiederherstellungsprüfungen auf Zielhardware.
- Ausführung der GitHub-Actions-Prüfung nach einem späteren Push.
- YAML-Parserprüfung: lokal ist kein PyYAML installiert; die vorhandene Services-Datei
  wurde unverändert übernommen, Workflow und Vorlagen wurden manuell geprüft.

Es wurde keine Softwareversion veröffentlicht und nichts zu GitHub gepusht.
