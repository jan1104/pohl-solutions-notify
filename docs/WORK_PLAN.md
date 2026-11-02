# Arbeitsplan: Pohl Solutions Alarm Notify

Stand: 02.11.2026 · lokaler Entwicklungsstand 0.3.27 · kein Push / kein Deployment.
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
- Android-Sprachansage ist unabhängig vom Alarmton ein-/ausschaltbar. Ohne Alarmton
  keine erzwungene Rufton-/Benachrichtigungslautstärkeänderung und keine dafür nötigen
  Sensoren. iOS/Browser bieten keinen nicht implementierten Sprachschalter an.
- Push aus unterbindet Info/Warnung und reguläre stumme Meldungen; Alarmtöne dürfen
  weiterhin ihre erforderlichen technischen Benachrichtigungen verwenden.

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

## Abgeschlossen: Einstieg und Verwaltung in 0.3.26

Automatischer Lauf am 02.11.2026, abends (Europe/Berlin).

- [x] Reale Einstiegshandler über schmale Importadapter prüfbar gemacht.
- [x] Fehler bei erneutem / abgebrochenem Start nachgestellt und bereinigt:
  Engine, Listener, Hintergrundaufgaben und bereits angelegte Oberfläche entfernen;
  kein regulärer Stop-/Speicherpfad mit nur teilweise geladenem Modell.
- [x] Doppelte Einrichtung ersetzt keine bereits laufende Engine mehr.
- [x] WebSocket-Zugriffe auf entladene / stoppende Integration geben kontrollierte Fehler.
- [x] Fehlende, falsch typisierte oder unbekannte Gerätekennungen vor Journal-/Speicheränderungen abweisen.
- [x] Importvorschau, ungültigen Import und Gerätefreigabe mit/ohne Testsitzung über
  die tatsächlichen Verwaltungshandler prüfen.
- [x] Importierte alte Testsitzung und flüchtige Wiederherstellungs-/Wartezustände
  entfernen, damit die verlangte erneute Geräteprüfung nicht auf alte Sitzungen zurückgreift.
- [x] 57 Tests erfolgreich; Python-/JSON-/Versions- und JavaScript-Prüfung bestanden.

Die Schema-/Decorator-Adapter validieren keine HA- oder probatio-Schnittstellen.
Die Tests ersetzen deshalb weiterhin keine echte HA-Installation.

## Abgeschlossen: Ausgabeoptionen in 0.3.27

Fortsetzung auf Benutzerauftrag: Sprache und weitere Schalter prüfen und verbessern.

- [x] Ursache nachgestellt: Sprache war an den Alarmton gekoppelt; separate Auswahl umgesetzt.
- [x] Sprache-only besitzt stoppbaren, persistenten Auftrag ohne Rufton-/Lautstärkebaseline.
- [x] Sensor-/Kategorienvorbereitung nur für Android-Alarmton verlangen; Assistent lässt
  Nutzer erst die Ausgabeoptionen wählen, bevor er diese Sensoren voraussetzt.
- [x] Plattformgrenzen und echte boolesche Schalter auch beim Speichern/Import anwenden.
- [x] Änderungen von Sprache, Push, Popup und Audiozeiten verlangen erneut Geräteprüfung.
- [x] Stumme Android-Statuskanäle mit niedriger Wichtigkeit anfordern; bestehende
  Android-Kanaleinstellungen nicht als überschrieben darstellen.
- [x] 75 Python- und sieben Node.js-Tests erfolgreich; lokale Version 0.3.27.

Bedienung und wichtiger Hinweis beim Update von 0.3.26: [OUTPUT_SETTINGS.md](OUTPUT_SETTINGS.md).

## Nächste unabhängig ausführbare Schritte

1. Wiederherstellung nach simuliertem Neustart, Abbruch von Hintergrundaufgaben und
   parallele Rückmeldungen / Prioritätswechsel gezielt prüfen. Fehler nur bei
   reproduzierbarem Fehlverhalten ändern. Fehler in Aufräumfunktionen selbst und
   fehlgeschlagenes reguläres Entladen gezielt mitprüfen.
2. Benachrichtigungs-/Browser-Mod-Anfragen gegen dokumentierte Schnittstellen prüfen;
   lokale Beispielkonfiguration und wiederholbares Installationspaket vorbereiten.
3. Lastverhalten bei vielen abgeschlossenen Ereignissen und Transporteinträgen messen.
   Erst anhand der Ergebnisse begrenzte Datenabfragen oder Speichermaßnahmen umsetzen.
4. Die bereits ergänzten Schalter-/Assistententests um Export-/Verlaufstests erweitern.
   Frontend zunächst lesbar formatieren; danach nur
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
node --test tests/frontend_outputs.test.cjs
git diff --check
```

Die Importadapter in `tests/ha_test_support.py` ersetzen HA-/aiohttp-Grenzen.
Sie prüfen unseren Anwendungscode, nicht die tatsächliche HA- oder HTTP-Laufzeit.
Die Automation arbeitet lokal; der Rechner muss mit verfügbaren Projektdateien laufen
und die Desktop-App muss geöffnet sein. Zeitplanung ist keine Garantie für
ununterbrochene Arbeit bei ausgeschaltetem Rechner.
