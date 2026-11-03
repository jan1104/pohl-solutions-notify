# Prüfprotokoll

## Versionssicherung – 03.11.2026

- Vor Beginn sauberer Arbeitsstand auf `main`, HEAD `47f170b`; keine fremden Änderungen.
- `v0.3.27` auf `47f170b`, `v0.3.25` auf `c76c70f` annotiert und auf Manifestversion geprüft.
- `develop` für die weitere Arbeit angelegt; App-Dateien gegenüber `v0.3.27` unverändert.
- Installationspakete ausschließlich aus verfolgten Integrationsdateien beider Tags erzeugt,
  alle ZIP-Dateien gegen Git-Blobs abgeglichen und ZIP-Integrität geprüft. SHA-256-Werte
  in `dist/snapshots.json` dokumentiert. Keine Caches oder privaten HA-Laufzeitdaten enthalten.
- Ein kleinerer Subagent implementierte das Verpackungswerkzeug; der Hauptagent prüfte
  Ergebnis, Fehlerbehandlung und die integrierte Testserie.
- 79 Python-Tests und sieben Node.js-Frontendtests bestanden. 19 Python-Dateien,
  drei JSON-Dateien und Versionskonsistenz geprüft; Git-Whitespaceprüfung erfolgreich.
- Zusätzliche lokale Sicherung aller Git-Referenzen als Bundle; keine externe Kopie,
  kein Push, kein Deployment und kein neuer HA-/Handytest.


## Lokaler Entwicklungsstand 0.3.27 – 02.11.2026

- Ausgabeoptionen erneut geprüft: unabhängige Android-Sprache, nur Ton, nur Push,
  alle Ausgaben aus, abbrechbare Sprache, Stop-Wiederholung und Freigabe nach Änderung.
- Sensorlose Auswahl von nur Sprache/Push im tatsächlichen Frontend-Assistenten geprüft.
- 75 Python-Tests sowie sieben Node.js-Tests der unveränderten Frontendmethoden bestanden.
- 17 Python-Dateien und drei JSON-Dateien samt Version geprüft; JavaScript-Syntax gültig.
- HA/aiohttp-Grenzen und Browser-Grundobjekte bleiben ersetzt. Keine echte Tonwiedergabe,
  visueller Browserprüfung oder tatsächlicher Companion-/HA-Start behauptet.
- Kein Push, kein Deployment. Update-Hinweis und Schaltertabelle: [OUTPUT_SETTINGS.md](OUTPUT_SETTINGS.md).


## Lokaler Entwicklungsstand 0.3.26 – 02.11.2026, automatischer Abendlauf

- Ausgangsstand war sauber: keine fremden/uncommitteten Änderungen, HEAD `c76c70f`.
- Vor den Korrekturen zeigten die neuen Einstiegstests doppelte Engine-Ersetzung,
  zurückbleibende Engine bei Startfehlern sowie interne KeyErrors bei entladener
  Integration und fehlenden Kennungen. Zusätzliche Importprüfung zeigte die Übernahme
  alter Testsitzungen und flüchtiger Warte-/Wiederherstellungsfelder.
- Nach Korrektur: 57 Tests bestanden (12 Modell-/Kontofilter-, 17 Engine-, 11 Bild-
  und 17 Einstieg-/Verwaltungstests). Insbesondere Startfehler, Startabbruch,
  Registrierung beim Neuladen, fehlende Kennungen, Importvorschau und Gerätefreigabe geprüft.
- 17 Python-Dateien, drei JSON-Dateien und Versionskonsistenz erfolgreich geprüft;
  JavaScript-Syntax und Git-Whitespaceprüfung erfolgreich.
- Die Einstiegstests führen den Projektcode aus, ersetzen aber HA, aiohttp und
  probatio-Dekoratoren/Schemaobjekte. Sie beweisen keine echte HA-Kompatibilität
  oder tatsächliche Schema-/Transport-/Gerätefunktion.
- Kein Push, keine Veröffentlichung, kein Deployment und kein Gerätezugriff.


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
