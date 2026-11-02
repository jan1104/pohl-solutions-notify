# Prüfprotokoll

Datum: 02.11.2026 · Softwarestand: 0.3.24

## Lokal erfolgreich

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

## Noch offen

- Vollständiger Laufzeittest in Home Assistant und Bestätigung unterstützter Versionen.
- Geräte-, Benachrichtigungs-, Neustart- und Wiederherstellungsprüfungen auf Zielhardware.
- Ausführung der GitHub-Actions-Prüfung nach einem späteren Push.
- YAML-Parserprüfung: lokal ist kein PyYAML installiert; die vorhandene Services-Datei
  wurde unverändert übernommen, Workflow und Vorlagen wurden manuell geprüft.

Es wurde keine Softwareversion veröffentlicht und nichts zu GitHub gepusht.
