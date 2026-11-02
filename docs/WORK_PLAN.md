# Arbeitsplan: Pohl Solutions Alarm Notify

Stand: 02.11.2026 · lokaler Entwicklungsstand 0.3.25 · kein Push / kein Deployment.
Arbeitsordner: `D:\depot\pohl-solutions-notify`.

## Auftrag und Arbeitsweise

Der Benutzer hat die Behebung der analysierten Probleme und automatische Weiterarbeit
alle sechs Stunden beauftragt. Die aktive chatgebundene Automation heißt
**Pohl Notify weiterentwickeln**, ID `pohl-notify-weiterentwickeln`.
Sie liest diesen Plan und bearbeitet den nächsten sinnvollen offenen Schritt.

Vor jedem Lauf `git status` und letzte Commits lesen; fremde Änderungen erhalten.
Nur belegte Fehler und klar beschriebene Folgeschritte bearbeiten. Aussagekräftige
Prüfungen ergänzen, Dokumentation aktualisieren und zusammenhängende lokale Commits
erstellen. Kein Push, Release, Deployment, Lizenzwechsel oder neue Produktfunktion
ohne gesonderten Auftrag. Keine Änderung nur zur Erzeugung vermeintlichen Fortschritts.

## Festgelegte Produktregeln für die Korrekturen

- „Ich komme“ betrifft ausschließlich das ausgewählte Ereignis.
- Priorität gilt je Gerät; auf einem gemeinsamen Gerät bleibt die bisherige
  Reihenfolge Einbruch vor Feuer erhalten. Weitere Ereignisse werden stumm gemeldet.
- Empfänger mit anderen Geräte-/Alarmartenzuordnungen werden unabhängig alarmiert.
- Deaktivierte normale Konten erhalten keine Alarmdaten. Aktive HA-Administratoren
  behalten Verwaltungsrechte. Der öffentliche HA-Sensor enthält nur die Alarmanzahl.
- Ursprüngliche Android-Einstellungen erst nach frisch gemeldeter Bestätigung löschen.
- Generierte Bilder sind privat, alarmartenbezogen zugriffsgeschützt und laufen ab.

## Abgeschlossen: erste Fehlerkorrektur

- [x] Globale Blockierung anderer Alarmempfänger entfernt.
- [x] Push-Ersatzmeldung bei ausstehender Wiederherstellung ergänzt.
- [x] Sensorbestätigung, Behalten ursprünglicher Werte und Wiederholungsdienst ergänzt.
- [x] Rückmeldungen auf das ausgewählte Ereignis begrenzt.
- [x] Lesefilterung für deaktivierte / unbekannte Konten korrigiert.
- [x] Detaildaten aus generischer HA-Entität entfernt.
- [x] Private Bildspeicherung, angemeldeter API-Zugriff und regelmäßige Bereinigung ergänzt.
- [x] Testsitzung für Gerätefreigabe verbindlich gemacht.
- [x] Version auf 0.3.25 erhöht; Anleitung und historische Analyse eingeordnet.
- [x] 39 lokale Verhaltenstests, Syntax- und Metadatenprüfungen erfolgreich.

## Nächste unabhängig ausführbare Schritte

1. Lade-/Entladepfade und WebSocket-Verwaltung mit einem gezielten Testgerüst prüfen:
   doppelte Registrierung, Integration nicht geladen, fehlende Nutzdaten, Import
   und Gerätefreigabe ohne Testsitzung. Keine echte HA-Kompatibilität daraus ableiten.
2. Wiederherstellung nach simuliertem Neustart, Abbruch von Hintergrundaufgaben und
   parallele Rückmeldungen / Prioritätswechsel gezielt prüfen. Fehler nur bei
   reproduzierbarem Fehlverhalten ändern.
3. Benachrichtigungs-/Browser-Mod-Anfragen gegen dokumentierte Schnittstellen prüfen;
   lokale Beispielkonfiguration und wiederholbares Installationspaket vorbereiten.
4. Lastverhalten bei vielen abgeschlossenen Ereignissen und Transporteinträgen messen.
   Erst anhand der Ergebnisse begrenzte Datenabfragen oder Speichermaßnahmen umsetzen.
5. Frontend zunächst lesbar formatieren und Logik-/Exporttests ergänzen; danach nur
   bei abgesicherter Gleichheit in überschaubare Bausteine zerlegen. Kein Designwechsel.

## Externe Validierung: derzeit nicht ausgeführt

- [ ] Tatsächliche HA-Version und Laden/Entladen auf Linux/HA feststellen.
- [ ] Android: Ton, TTS, Sensoraktualität, Offline-Fall und Rückkehr zu Originalwerten.
- [ ] iOS: kritische Hinweise, Aktionen und authentifizierte Bildanhänge.
- [ ] Browser Mod: Popup-Zuordnung und Wechsel zwischen parallelen Ereignissen.
- [ ] Geschützter Bildabruf mit tatsächlicher HA-HTTP-Anmeldung und Companion-App.
- [ ] Neustart während Alarm / Wiederherstellung, Import und Update auf Zielsystem.

Ablauf: [HA_TEST_PROTOCOL.md](HA_TEST_PROTOCOL.md). Diese Schritte brauchen eine
Testinstallation und echte Geräte. Wenn nur diese Schritte übrig sind, benötigte
Voraussetzungen konkret melden und keine unbelegten Erfolgsaussagen oder wiederholten
kosmetischen Änderungen erzeugen.

## Lokale Prüfungen in dieser Umgebung

Der normale Windows-`python`-Aufruf verweist hier auf den Store-Alias. Verwendet wurde:

```powershell
& 'C:\Users\jpohl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/validate.py
& 'C:\Users\jpohl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
node --check custom_components/alarm_system/frontend/panel.js
git diff --check
```

Die Importadapter in `tests/ha_test_support.py` ersetzen HA-/aiohttp-Grenzen.
Sie prüfen unseren Anwendungscode, nicht die tatsächliche HA- oder HTTP-Laufzeit.
Die Automation arbeitet lokal; der Rechner muss mit verfügbaren Projektdateien laufen
und die Desktop-App muss geöffnet sein. Zeitplanung ist keine Garantie für
ununterbrochene Arbeit bei ausgeschaltetem Rechner.
