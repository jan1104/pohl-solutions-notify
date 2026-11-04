# Prüfprotokoll

## Importschalter 0.5.2 – 04.11.2026, automatischer Morgenlauf

- Vorher realen Import mit enabled="false" für Benutzer/Gerät/Melder und silent="false" ausgeführt: alle Werte waren anschließend wahr bzw. wahr ausgewertet.
- Separater Testagent reproduzierte 56 fehlschlagende Unterfälle: vier Schalter, sieben mehrdeutige Datentypwerte, zwei Sicherungsschemas.
- Nach Korrektur bestehen alle sechs neuen Testmethoden einschließlich echter Booleans, fehlender älterer Felder und Unveränderlichkeit von Eingabedokument/laufender Konfiguration.
- Keine native HA-/Android-Prüfung; kein Push, Release oder Deployment.

## Bestätigungskennungen 0.5.1 – 04.11.2026, automatischer Lauf

- Vor der Änderung reproduziert: Abbruch mit falschem Benutzer entfernt fremde gültige Kennung; abgelaufene Kennung bleibt nach neuer Anfrage vorhanden. Unabhängiger Testagent reproduzierte zusätzliche falsche Ereigniszuordnung und Ablaufgrenzen.
- Acht neue Tests verwenden die echten respond-/tick-Methoden mit ersetzten Konto-, Speicher- und Transportgrenzen. Nach Korrektur bestehen Benutzer-/Ereignisbindung, Ablaufbereinigung, Wiederverwendung aktueller Anfragen sowie idempotente bestätigte Wiederholungen.
- Keine native HA-/Android-Prüfung; kein Push und kein Deployment.

## Einzeltests und Empfängerübersicht 0.5.0 – 03.11.2026

- 185 Python- und 41 Frontendtests erfolgreich; Syntax, Versionen und Metadaten konsistent.
- Testgrenzen: Adminrechte und verschachtelte Kennungen, Profil-/Geräteschalter, Plattform, echte Meldertexte, Stummschaltung, deaktivierte Zuordnungen und keine Gerätefreigabe.
- Lebenszyklus: gezielter Stopp mit aktueller Kennung, abgelaufene/ersetzte Tests, Fehler und erneute Bereinigung, Ablauf, Entladen und verspätete Dialogantworten.
- Unabhängige Gegenprüfung fand unbeschränkt wartende Testtransporte. Behoben und mit hängendem Transport, neuem Alarm, Zeitüberschreitung, unbestätigtem Abbruch und Popup-Sperrübernahme geprüft. Speicherung hält die Transportsperre nicht mehr.
- Vorschau und Bedienelemente prüfen Empfänger, Plattformen, effektive Ausgaben, offene Freigaben und Wiederherstellung; keine aktuelle Erreichbarkeit behauptet.
- Modell/Engine/Frontend laufen in lokalen Adaptern. Keine echte HA-, Browser-, Android- oder Browser-Mod-Prüfung. Bereits extern angenommene Befehle bleiben eine native Prüfgrenze.

## Sprachtexteingabe und Informationsausgabe 0.4.2 – 03.11.2026

- 146 Python- und 24 Frontendtests erfolgreich, Syntax/Metadaten konsistent.
- Neue Regressionen: unabhängige Meldungsschalter und Persistenz, Sprache ohne Push, Geräte-/Plattformgrenzen, normale Ton-/Stummregeln, eigene Texte, schließbares Fenster mit escaped Inhalt, deaktivierte Empfänger sowie Alarmstart während Push-Transport.
- Frontend prüft Standardtext ohne rohes Muster, deutsche Einfügeschaltflächen mit Cursorposition/Längenbegrenzung, sichere Live-Textvorschau und erhaltene Schalter auch beim Umbenennen.
- Kein echter Home-Assistant-, Android-, Browser- oder Browser-Mod-Test. Vorschau ist Text mit Beispieldaten, kein Wiedergabetest.

## HACS-Korrektur 0.4.1 – 03.11.2026

- Fehlende Root-hacs.json im unveränderten Commit 47f170b als konkrete Ursache identifiziert, mit offiziellem HACS-Downloadcode abgeglichen.
- 134 Python- und 21 Frontendtests bestanden; Syntax-, Metadaten- und Whitespaceprüfung erfolgreich.
- Regressionen prüfen fehlendes/ungültiges HACS-Manifest, falsches Root-/ZIP-Layout, fehlenden Issue-Tracker und mehrere Integrationen.
- Kein echter HACS-/HA-/Android-Test. Kein Push, Release oder Deployment.

## Lokaler Entwicklungsstand 0.4.0 – 03.11.2026

- Ausgangsstand sauber auf `develop`, HEAD `037b832`.
- 132 Python-Tests und 21 Node.js-Tests erfolgreich; 25 Python-Dateien, drei JSON-
  Dateien und Versionskonsistenz geprüft. Frontend-Syntax gültig, Git-Whitespaceprüfung sauber.
- Neue Prüfungen: Migration/Profilvalidierung, eigene Ereignisse/Melder/Priorität,
  Caps am Gerät, individuelle TTS/Zeiten/Kanäle, Admin-Verwaltung, erneute Geräteprüfung,
  Schema 1/2, Erhalt historischer Referenzen, dynamische Auswahl und Namens-Escaping.
- Eigene Basistests für ausschließlich eigenen Alarmarten zugeordnete Konten waren
  zunächst nicht sichtbar/bedienbar; gezielt nachgestellt und korrigiert. Tests sichern
  weiterhin Ablehnung fremder Tests, echter nicht zugewiesener Alarme und deaktivierter Konten ab.
- Zwei Subagenten bearbeiteten Modell und Frontend; Hauptagent prüfte und integrierte
  reale Projektmethoden mit ersetzten HA-/HTTP-/Browsergrenzen.
- Keine echte HA-, Browser- oder Android-Prüfung, kein Deployment und kein neuer Push.
- Feste Ausgangstags und `main` unverändert; Anleitung und Sicherungsgrenzen in CUSTOM_ALARM_TYPES.md.


## Lokaler Entwicklungsstand 0.3.29 – 03.11.2026, automatischer Nachmittagslauf

- Sauberer Ausgangsstand auf `develop`, HEAD `b9e4527`.
- Ein neuer Prioritätswechseltest schlug vor der Korrektur fehl: Nach Feuer-Tonwartezeit
  wurde TTS trotz neuem Einbruch auf demselben Gerät angefordert. Zwei Kontrolltests
  sichern unabhängige Geräte und die Erhaltung einer neueren Lease ab.
- Zwei neue Einstiegstests schlugen vor der Korrektur fehl: Ein Fehler beim Aufräumen
  verdeckte die eigentliche Startursache und übersprang weitere Aufräumschritte.
- Nach den gezielten Korrekturen: 92 Python- und sieben Node.js-Tests erfolgreich;
  22 Python-Dateien, drei JSON-Dateien und Version 0.3.29 geprüft.
- Frontend-Syntax und Git-Whitespaceprüfung bestanden. Externe Grenzen bleiben
  ersetzt; kein echter HA-Start, Transportzeitnachweis oder physischer Audiotest.
- `main` und gespeicherte Versionstags unverändert; kein Push, Deployment oder Release.


## Lokaler Entwicklungsstand 0.3.28 – 03.11.2026, automatischer Morgenlauf

- Sauberer Ausgangsstand auf `develop`, HEAD `b439db1`.
- Fünf neue Shutdown-Tests schlugen vor der Korrektur fehl: zwei durch abgebrochene
  Aufräumarbeiten bei Listenerfehler, drei durch weitere Verarbeitung später Ereignisse.
- Nach minimaler Korrektur bestehen diese Tests und drei zusätzliche Recovery-Tests
  eines Subagenten; insgesamt 87 Python- sowie sieben Node.js-Tests erfolgreich.
- 21 Python-Dateien und drei JSON-Dateien auf Syntax/Metadaten geprüft,
  Version 0.3.28 konsistent, Frontend-Syntax und Git-Whitespaceprüfung bestanden.
- Geprüft: weitere Bereinigung trotz fehlgeschlagener Abmeldung, Beginn der
  Gerätewiederherstellung, späte Events nach Stop, Testabbruch beim Wiederanlauf,
  Originalwerte bei fehlgeschlagener Wiederherstellung und Recovery-Flag bei Fehlern.
- Keine echte HA-/Handyprüfung, keine reale Prozessabschaltung und kein Beweis
  für HA-Speicheratomicität. Keine Veröffentlichung, kein Push, kein Deployment.


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

## Veröffentlichungsprüfung 0.4.1 – 03.11.2026

- Nach Nutzerfreigabe develop und neue Tags erfolgreich gepusht, GitHub-Release v0.4.1 erstellt.
- Über GitHub-API veröffentlichten Release-Status und hacs.json am Tag geprüft. Defaultbranch main unverändert.
- API lieferte unmittelbar danach keine Workflow-Läufe für develop; keine GitHub-CI-Bestätigung. Kein HA-Deployment oder echter HACS-/Android-Test.

## Standardvorschau 0.4.3 – 03.11.2026

24 Frontendtests erfolgreich, bestehende Tests um immer sichtbaren Standard neben eigenem Text sowie Live-Namensänderung und sichere Textausgabe erweitert. Frontend-Syntax und Versions-/Metadatenprüfung erfolgreich. Python-Verhaltenscode unverändert, dessen letzte Gesamtprüfung war 146 Tests in 0.4.2. Keine native HA-/Android-/Browser-Prüfung.

## Vereinfachte Melderzuordnung 0.4.4 – 03.11.2026

- 156 Python- und 26 Frontendtests erfolgreich. Syntax, Metadaten/Versionen und Whitespace geprüft.
- Modellregressionen für gleiche/unterschiedliche Alarmarten, stabile Gruppe bei Umbenennung, alte gespeicherte Gruppen, unveränderte aktive Ereignisse und Signalnormalisierung, Fehlalarm-Sperre bis AUS, direkte Service-Gruppen.
- Engine-/Importfälle für mehrere Bereiche im selben Ereignis, getrennte Typen, atomaren Altimport und weiter einmalige INFO-Meldungen.
- Frontend prüft einzelne Dropdown-Auswahl, dynamische Namen, Wegfall manueller Felder/Validierung, keine veralteten Gruppenschlüssel beim Speichern, Informationseinstellungen weiter verfügbar.
- Zwei Subagenten bearbeiteten Modell und Frontend getrennt; Hauptagent prüfte Migration und integrierte Engine-/Importtests. Keine native Prüfung behauptet.

## Kompakter Verlauf 0.4.5 – 03.11.2026

29 Frontendtests erfolgreich. Neue Prüfungen für standardmäßig geschlossene Details mit vollständiger Kurzzeile, sichere Namen/Texte, erhaltenen Detailinhalt, stabilen Aufklappzustand anhand Ereignis-ID und unverändert offen dargestellte aktive Alarme mit Bedienaktionen. Informationseinträge unterscheiden Auslösung von Empfang. Syntax/Versionsmetadaten geprüft; unabhängiger Subagent fand keine blockierenden Befunde. Python-Verhaltenscode unverändert, dessen letzte Gesamtprüfung war 156 Tests in 0.4.4. Keine native Browser-/HA-/Android-Prüfung.

Prüfstand dieses Laufs: 193 Python- und 41 Frontendtests bestanden; Syntax, Versionsmetadaten und Whitespace sauber.

Prüfstand Morgenlauf: 199 Python- und 41 Frontendtests bestanden; Syntax/Metadaten/Versionen und Whitespace sauber.
