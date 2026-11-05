# Arbeitsplan: Pohl Solutions Alarm Notify

Stand: 05.11.2026 · lokaler Entwicklungsstand 0.5.8 · letztes veröffentlichtes Release 0.5.7 / kein HA-Deployment.
Arbeitsordner: `D:\depot\pohl-solutions-notify`. Weiterentwicklung auf **develop**.
Feste Rücksprungpunkte: **v0.3.27** (gesicherter Ausgangsstand) und **v0.3.25** (vom Benutzer
als gelaufen gemeldete Versionsnummer). `main` bleibt auf dem 0.3.27-Ausgangsstand.
Siehe [VERSIONS.md](VERSIONS.md); Tags nicht verschieben oder überschreiben.

## Detaillierte Arbeitsliste

[DEVELOPMENT_BACKLOG.md](DEVELOPMENT_BACKLOG.md) enthält 36 priorisierte Arbeitspakete
mit Abhängigkeiten und Fertig-Kriterien. Für automatische Fehler-/Testarbeit zunächst
B1/B3, danach B2/B4 und B6/C3 bearbeiten. Neue Funktionsvorschläge aus D/E/H sind
Planungsoptionen; ihre Aufnahme ist keine automatische Freigabe zum Einbauen.
Gesicherte Tags und App 0.3.27 wurden bei der Planung nicht verändert.

## Auftrag und Arbeitsweise

Der Benutzer hat die Behebung der analysierten Probleme und automatische Weiterarbeit
alle sechs Stunden beauftragt. Die aktive chatgebundene Automation heißt
**Pohl Notify weiterentwickeln**, ID `pohl-notify-weiterentwickeln`.
Sie liest diesen Plan und bearbeitet den nächsten sinnvollen offenen Schritt.

Vor jedem Lauf `git status`, aktuellen Branch und letzte Commits lesen; fremde Änderungen erhalten.
Auf `develop` weiterarbeiten. Wenn ein anderer Branch mit fremder Arbeit aktiv ist,
nicht ungefragt wechseln oder dessen Änderungen übernehmen. Geeignete abgegrenzte
Programmieraufgaben an Subagenten geben; der Hauptagent prüft und integriert.
Kleinere Modelle für Routineaufgaben verwenden, soweit verfügbar und geeignet.
Nur belegte Fehler und klar beschriebene Folgeschritte bearbeiten. Aussagekräftige
Prüfungen ergänzen, Dokumentation aktualisieren und zusammenhängende lokale Commits
erstellen. Kein Push, Release, Deployment, Lizenzwechsel oder neue Produktfunktion
ohne gesonderten Auftrag. Keine Änderung nur zur Erzeugung vermeintlichen Fortschritts.

## Versionssicherung am 03.11.2026

- Aktueller unveränderter App-Stand 0.3.27 und älterer lokaler Stand 0.3.25 mit Tags gesichert.
- Weiterentwicklung von der bisherigen Version auf eigenem Branch getrennt.
- Lokales Verpackungswerkzeug mit vier Tests, geprüfte Installations-ZIPs aus beiden Tags
  und zusätzliche Git-Historiensicherung erstellt. 79 Python- und sieben Frontendtests bestanden.
- Rückkehr zum Quellstand und Grenzen gegenüber HA-Laufzeitdaten dokumentiert.
- Benutzer bestätigt Android und Priorität **Einbruch vor Feuer** auf gemeinsamen Geräten.

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

## Abgeschlossen: Teil von B1/B3 in 0.3.28

Automatischer Lauf am 03.11.2026, morgens (Europe/Berlin), Ausgangscommit `b439db1`.

- [x] Fehler eines einzelnen Abmelde-Callbacks reproduziert: bisher blieben weitere
  Aufräumarbeiten und Gerätewiederherstellung aus. Fehler wird jetzt protokolliert,
  die übrige Bereinigung läuft weiter.
- [x] Nach Stopbeginn eintreffende Sensorereignisse, Empfangsbestätigungen und
  Handyantworten dürfen keine weitere Verarbeitung anstoßen; entsprechend abgesichert.
- [x] Neustartverhalten regulärer Alarme und Abbruch von Gerätetests lokal geprüft.
- [x] Originale Lease-Werte bei fehlgeschlagenen Wiederherstellungsbefehlen bleiben erhalten;
  Recovery-Flag wird auch bei Transport-/Speicherfehlern zurückgesetzt.
- [x] Acht neue Tests; insgesamt 87 Python- und sieben Frontendtests bestanden.

Kleinerer Subagent bearbeitete die isolierten Recovery-Tests, Hauptagent die
Aufräumkorrektur und Integration. Keine reale Prozessabschaltung, HA-Store-Atomicity
oder Gerätezustellung nachgewiesen. B1/B3 bleiben für weitere Unterbrechungs- und
Speichergrenzen teilweise offen; vorhandene Tags und `main` wurden nicht verändert.

## Abgeschlossen: Teil von B2/B3 in 0.3.29

Automatischer Lauf am 03.11.2026, nachmittags (Europe/Berlin), Ausgangscommit `b9e4527`.

- [x] Prioritätswechsel während einer Tonwartezeit nachgestellt: Feuer-TTS wurde bisher
  trotz zwischenzeitlich priorisiertem Einbruch auf demselben Gerät gesendet.
  Aktuelle Gerätepriorität wird vor der Sprachstufe jetzt erneut geprüft.
- [x] Kontrolle: Einbruch auf anderem Gerät unterdrückt Feueransage nicht;
  ein alter Worker entfernt keine neuere Playback-Lease.
- [x] Fehler einzelner Service-/Panel-Aufräumschritte nach Startfehler nachgestellt.
  Alle übrigen Aufräumversuche laufen weiter, der ursprüngliche Fehler bleibt erhalten.
- [x] Fünf neue Regressionstests; 92 Python- und sieben Frontendtests erfolgreich.

Subagent erstellte isolierte Prioritätswechseltests; Hauptagent prüfte die Reproduktion,
implementierte die kleine Prioritätskorrektur und die Start-Aufräumkorrektur.
Keine HA-/Handytests oder neue Produktregel; Einbruch-Vorrang pro Gerät bleibt bestehen.
Weitere Speicher-/Transportgrenzen und echte Zeit-/Wiedergabewirkung bleiben offen.

## Eigene Alarmarten: ausdrücklicher Folgeauftrag in 0.4.0

Benutzer wünscht frei benannte Arten (z. B. Hausalarm/Amokalarm) und hat ausdrücklich
Empfänger sowie Ton/Sprache/Push/Popup/Priorität je Art bestätigt.

- [x] Persistente Profile, sichere Migration und eindeutige IDs mit bis zu 32 eigenen Arten.
- [x] Verwaltung, Empfänger-/Melderauswahl, Profilpriorität und Ausgabeverknüpfung umgesetzt.
- [x] Android-Kategorien bei Umbenennung stabil; Zeiten und sichere Sprachvorlagen ergänzt.
- [x] Schema-2-Export/Import mit Schema-1-Kompatibilität und Erhaltung historischer Verweise.
- [x] Eigene Gerätetests bei eingeschränkter Alarmzuordnung ohne Öffnung fremder Rechte.
- [x] 132 Python- und 21 Frontendtests bestanden; Bedienung und Rückkehrgrenzen dokumentiert.

Modell und Frontend wurden in getrennten Subagenten bearbeitet; Hauptagent integrierte
Transport, Verwaltung, Import und zusätzliche Tests. Keine neuen Arten oder Empfänger
in der tatsächlichen HA-Instanz angelegt. Bedienung: [CUSTOM_ALARM_TYPES.md](CUSTOM_ALARM_TYPES.md).
Prioritäten: Einbruch 10 vor Feuer 20 bleibt fest; eigene Arten starten mit 30 und
können durch ausdrücklich konfigurierte Werte 1–100 vor-/nachgeordnet werden.
Die neue Profilfunktion ist beauftragt; übrige neue D/E/H-Vorschläge bleiben Planungsoptionen.

## Nächste unabhängig ausführbare Schritte

1. Weitere Speicher-/Transportfehler, fehlgeschlagenes reguläres Entladen sowie
   parallele Rückmeldungen und laufende/abgebrochene Aufträge gezielt prüfen. Fehler nur bei
   reproduzierbarem Fehlverhalten ändern. Fehler in Aufräumfunktionen selbst und
   fehlgeschlagenes reguläres Entladen gezielt mitprüfen. Der einzelne Listenerfehler
   und erst nach Stopbeginn eintreffende Ereignisse sind bereits in 0.3.28 abgesichert.
2. Benachrichtigungs-/Browser-Mod-Anfragen gegen dokumentierte Schnittstellen prüfen;
   lokale Beispielkonfiguration ergänzen. Das Installationspaket aus Tags ist bereits umgesetzt.
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
node --test tests/frontend_outputs.test.cjs tests/frontend_alarm_types.test.cjs
git diff --check
```

Die Importadapter in `tests/ha_test_support.py` ersetzen HA-/aiohttp-Grenzen.
Sie prüfen unseren Anwendungscode, nicht die tatsächliche HA- oder HTTP-Laufzeit.
Die Automation arbeitet lokal; der Rechner muss mit verfügbaren Projektdateien laufen
und die Desktop-App muss geöffnet sein. Zeitplanung ist keine Garantie für
ununterbrochene Arbeit bei ausgeschaltetem Rechner.

## HACS-Downloadfehler am 03.11.2026

- Nutzer meldet Ablehnung von Commit `47f170b`; dort fehlt Root-`hacs.json`.
- In 0.4.1 HACS-Quelldownload konfiguriert, Manifest vervollständigt und CI-Regressionsprüfung ergänzt.
- Nach ausdrücklicher Freigabe am 03.11.2026 develop und Tags 0.4.0/0.4.1 übertragen; GitHub-Release v0.4.1 veröffentlicht und HACS-Datei am Release-Tag remote geprüft. Defaultbranch main bleibt unverändert; in HACS v0.4.1 auswählen.
- Alten Commit/Tags nicht umschreiben. Kein weiterer lokaler Codeumbau behebt die Auswahl des alten Commits.
- Anleitung und Quellen: [HACS.md](HACS.md). Echte Installation weiterhin offen.

## Nutzerkorrektur 0.4.2: Sprachtext und Informationsausgaben

- Ausdrücklicher Auftrag: technische Platzhalter verständlich machen, spätere Sprache auch bei Information ermöglichen.
- Optionaler normaler Sprachtext, deutsche Einfügeschaltflächen und konkrete Beispielvorschau; vorhandene Vorlagen erhalten.
- INFO/WARNING unterstützen unabhängige Push-/Ton-/Sprach-/Fenster-Ausgaben; Defaults erhalten, einmalig und ohne erzwungene Lautstärke. Ereignis-/Quittierungsmodus unverändert.
- Reale Alarme haben auf dem jeweiligen Gerät Vorrang, Stummschalter unterdrückt auch Sprache. Rechte und Geräteschalter bleiben wirksam.
- 146 Python-/24 Frontendtests erfolgreich; HA-/Android-/Browser-Mod-Tests offen. Benutzer hat selbstständiges Pushen am 03.11.2026 erlaubt.

- Veröffentlichung 0.4.2 abgeschlossen: develop und Tag übertragen, GitHub-Release erstellt, hacs.json am Release remote sowie ZIP-Inhalte gegen den Tag geprüft.

## Nutzerwunsch 0.4.3: Standardansage immer anzeigen

- Unter dem Sprachtextfeld automatisch die Standardansage anzeigen, unabhängig von einem eigenen Text. Name wird live aktualisiert; Beispieldaten eindeutig kennzeichnen.
- 24 Frontendtests, Syntax und Versionsprüfung erfolgreich. Keine Backend-Logik geändert, keine erneute native Prüfung behauptet.

- 0.4.3 mit fortgeltender Nutzerfreigabe gepusht und veröffentlicht; Release und hacs.json am Tag remote geprüft.

## Ausdrückliche Produktentscheidung 0.4.4: eine Auswahl pro Melder

- Nutzer bestätigt: Art der Meldung wählt angelegte Alarmarten; alle Melder derselben Alarmart bilden automatisch einen gemeinsamen Alarm.
- Zusätzliches Freitextfeld und manuelle Ereignisgruppe aus dem Melderassistenten entfernen. Interne Gruppierung an stabile Typen-ID binden; reine Umbenennung darf keine neue Gruppe erzeugen.
- Laufende/Historienereignisse nicht zusammenführen oder umschreiben; alte Signal-/Fehlalarm-Sperren bis AUS erhalten und danach auf neue Gruppierung übergehen.
- Direkte Service-Aufrufe mit explizitem alarm_key bleiben kompatibel. Info/Warnung bleiben einzelne Meldungen.
- Regressionen auf Modell-, Import-, Engine- und Frontendebene; echte HA-/Android-/Browser-Prüfung weiterhin offen.

- Umgesetzt und lokal geprüft: 156 Python-/26 Frontendtests; Stand für HACS-Veröffentlichung vorbereitet.

- 0.4.4 mit fortgeltender Nutzerfreigabe gepusht und als GitHub-Release veröffentlicht; Release/HACS-Datei remote und ZIP-Inhalte gegen den Git-Tag geprüft.

## Nutzerwunsch 0.4.5: Verlauf standardmäßig kompakt

- Abgeschlossene Ereignisse und Meldungen einzeln zuklappen; Kurzzeile mit Datum/Uhrzeit, Status, Alarmart und beteiligten Meldern.
- Details beim Aufklappen, stabiler Zustand bei Aktualisierung, aktive Alarme weiter unmittelbar sichtbar.
- 29 Frontendtests sowie Syntax und Versionen geprüft. Letzte Python-Verhaltensprüfung: 156 Tests in 0.4.4; keine Änderung der Python-Alarmregeln.

- 0.5.0 gepusht und als GitHub-Release veröffentlicht; Release/HACS-Datei remote sowie ZIP-Inhalte gegen Git-Tag geprüft.

## Beauftragte Verbesserungen 0.5.0: Einzeltests und Empfängerübersicht

- Nutzer beauftragt die vorgeschlagenen nächsten Schritte: einzelne Ausgaben pro Alarmart/Gerät testen und wirksame Empfänger vorab anzeigen.
- Administratorrechte, reale oder ausdrücklich beispielhafte Melderdaten, TEST-Kennzeichnung, keine Sensoränderungen oder Gerätefreigabe. Normale Tonprobe statt erzwungener Lautstärke.
- Ein Test pro Gerät mit Kennung, gezielter Stopp und automatische Bereinigung; Alarme/Leases/Einrichtung schützen, Fehlerzustände für erneuten Stopp erhalten.
- Vorschau zeigt Profil-/Geräteschalter, Plattform, deaktivierte Zuordnungen, offene Geräteprüfungen und vorübergehende Einschränkungen ohne Empfangsbestätigung.
- Gegenprüfung fand unbeschränkt wartenden Testtransport unter gemeinsamer Sperre. Vor Veröffentlichung durch begrenzten, bei Alarm abbrechbaren Transport absichern.
- Korrigiert: gemeinsame Fünf-Sekunden-Grenze, laufende Alarmprüfung und begrenztes Abbruchwarten; Speicherung außerhalb der Transportsperre. Regressionen bestätigen Freigabe bei hängender Probe und eintreffendem Alarm sowie korrekte Popup-Sperren.
- Gesamtprüfung: 185 Python- und 41 Frontendtests, Syntax/Metadaten/Versionen und Whitespace erfolgreich. Unabhängige Gegenprüfung abgeschlossen; native HA-/Android-/Browser-Mod-Prüfung offen.
- Anleitung und Grenzen: [OUTPUT_TESTS.md](OUTPUT_TESTS.md). Nur diese zwei Vorschläge beauftragt; weitere Ideen bleiben Optionen.

- 0.5.0 mit fortgeltender Nutzerfreigabe gepusht und veröffentlicht. Release/HACS-Datei remote und ZIP-Inhalte gegen Git-Tag geprüft; kein HA-Deployment.

## Automatischer Lauf 04.11.2026: B6 Bestätigungskennungen

- Ausgangsstand sauber auf develop bei 671b0a4. Konkrete Fehler lokal nachgestellt: fremd zugeordnete Anfragen verbrauchen gültige Bestätigungen; abgelaufene Kennungen bleiben ohne weitere Bereinigung im Speicher.
- Erst Benutzer-/Ereigniszuordnung prüfen, danach gültige Kennung verbrauchen. Offene und abgeschlossene Kennungen beim Rückmelden und regelmäßigen Tick zeitgerecht bereinigen.
- Acht Regressionen für falsche Benutzer/Ereignisse, gültige Wiederholungen, Ablaufgrenze und Bereinigung. Keine geänderte Alarmregel, keine neue Produktfunktion.
- 0.5.1 wird als lokaler Checkpoint gesichert. Kein Push, Release, Deployment oder Lizenzwechsel in diesem automatischen Lauf. Native HA-/Android-Prüfungen bleiben offen.

Prüfstand dieses Laufs: 193 Python- und 41 Frontendtests bestanden; Syntax, Versionsmetadaten und Whitespace sauber.

## Automatischer Morgenlauf 04.11.2026: C3 Importschalter

- Ausgangsstand sauber auf develop bei 947a089, lokaler Checkpoint 0.5.1 bleibt erhalten.
- Konkret nachgestellt: Benutzer/Melder mit enabled="false" wurden aktiviert, silent="false" stellte Meldungen stumm, und device.enabled blieb als wahrer Text erhalten.
- Import prüft Aktivierungs- und Stummschalter strikt auf echte JSON-Booleans. Keine Änderung gültiger Konfigurationen oder der bisherigen Vorgaben bei fehlenden Legacy-Feldern.
- Ungültige Sicherung bleibt atomar abgewiesen; Originaldokument und laufende Konfiguration unverändert. Beide Sicherungsschemas mit sechs Regressionstests geprüft.
- Nur lokaler Stand 0.5.2; kein Push, Release, Deployment oder Lizenzwechsel. Keine echte HA-/Android-Prüfung.

Prüfstand Morgenlauf: 199 Python- und 41 Frontendtests bestanden; Syntax/Metadaten/Versionen und Whitespace sauber.

## Automatischer Nachmittagslauf 04.11.2026: B3 reguläres Entladen

- Ausgangsstand sauber auf develop bei 4956c62, lokale Checkpoints 0.5.1/0.5.2 erhalten.
- Konkret nachgestellt: Dienstentfernungsfehler verhindert verbleibende Dienste, Panel-, JavaScript- und Sensorbereinigung. Engine wurde vorzeitig entfernt, sodass ein erneuter Versuch fälschlich Erfolg meldete.
- Ressourcenbereinigung versucht alle Schritte; erster Fehler bleibt erhalten. Gestoppte Engine bis zur vollständigen Entfernung behalten, damit ein erneutes Entladen wirklich aufräumt.
- Scheitert bereits der Engine-Stopp, bleiben Engine und Ressourcen wie bisher für Wiederherstellungs-/Speicherwiederholung erhalten. Keine Alarmregel geändert.
- Start- und Entladebereinigung verwenden denselben Ressourcenhelfer. Kein Push, Release, Deployment oder Lizenzwechsel; echte HA-Prüfung offen.

Prüfstand Nachmittagslauf: 205 Python- und 41 Frontendtests bestanden; sechs neue Entlade-Regressionsfälle. Syntax/Versionen/Metadaten und Whitespace sauber.

## Freigabe und Veröffentlichung 04.11.2026

Auf ausdrücklichen Nutzerauftrag develop und Tags 0.5.1/0.5.2/0.5.3 gepusht sowie GitHub-Release v0.5.3 veröffentlicht. HACS-Datei und Manifestversion am Release-Tag remote geprüft. Benutzer beginnt jetzt eigene Gerätetests; deren Ergebnisse noch offen. Kein HA-Deployment durch den Agenten. Frühere Angaben zum lokalen Stand dokumentieren den Zustand vor dieser Freigabe.

## Nutzerkorrektur 0.5.4: Zeiten zur Alarmart verschieben

- Ton-/Sprachzeiten bei Alarmarten führen, im Geräteassistenten nur Ausgabeschalter belassen. Feuer/Einbruch akzeptieren zentrale Werte, Prioritäten bleiben unverändert.
- Vorhandene unterschiedliche Gerätewerte ohne ungefragte Vereinheitlichung bewahren. Leere Systemprofilfelder verwenden bisherige Zeiten, deren Übersicht steht bei der Alarmart.
- Ausgelassene Gerätezeitfelder beim Speichern erhalten; Schema-2-Import unterstützt neue Profilwerte. Rücksprunggrenze älterer Validatoren dokumentiert.
- 210 Python- und 44 Frontendtests erfolgreich. Nutzertext zeigte noch Frontend 0.4.5; tatsächliche installierte HA-Version unbekannt. Nach Update HACS-Version, HA-Neustart und vollständiges Neuladen des Panels prüfen. Keine native Geräteprüfung behauptet.

- 0.5.4 gepusht und veröffentlicht; HACS-Datei/Manifest remote sowie ZIP-Dateien gegen den Tag geprüft. Nutzer muss nach Update das Panel vollständig neu laden und die angezeigte Version prüfen. Kein HA-Deployment durch den Agenten.

## Nutzerbefund 0.5.5: kurzer Ton, Pause und unlesbarer Detailverlauf

- Nutzer berichtet vom Jan S22: Ton etwa eine Sekunde, danach Pause bis Sprache; Protokoll enthält Empfangstimeout nach zehn Sekunden und „Ich komme“ zeitgleich. Das Protokoll allein belegt keine TTS-Ausgabe nach dieser Rückmeldung.
- Code wartete seriell auf Empfang (bis zehn Sekunden) und danach die Tonphase. Empfangsdiagnose läuft nun parallel; vorhandene Abbruch-/Prioritäts-/Playback-Prüfungen bleiben erhalten.
- Die Länge eines Android-Benachrichtigungsklangs bleibt eine Endgeräte-/Tondateieigenschaft. Keine erfundene Dauersteuerung oder Push-Flut eingebaut; längeren Klang wählen bzw. Phase anpassen und neu testen.
- Deutsche Verlaufseinträge mit Melder-/Gerätenamen, Zusammenfassung gleicher Anforderungen und separaten technischen Rohdaten.
- 216 Python-/47 Frontendtests bestanden. Externe Grundlage: offizielle Companion-Dokumentation zu Notification Received und Benachrichtigungsklängen; keine erneute native Geräteprüfung durch den Agenten.

- 0.5.5 gepusht und veröffentlicht; HACS-Datei remote und ZIP-Inhalte gegen den Tag geprüft. S22-Tonlänge und neue Sprachabfolge vom Benutzer erneut praktisch prüfen lassen. Kein HA-Deployment durch den Agenten.

## Nutzerkorrektur 0.5.6: weniger Text bei Alarmart bearbeiten

- Erklärungstexte kürzen und unter Weitere Hinweise einklappen. Standard-Sprachtext weiterhin direkt anzeigen; zusätzliche eigene Vorschau nur bei eigenem Text.
- 47 Frontendtests sowie Syntax-/Metadatenprüfung erfolgreich. Python-Verhalten unverändert; letzte Gesamtprüfung 216 Tests in 0.5.5.
- Nutzeransicht zeigt weiterhin 0.4.5. Tatsächlicher Installations-/Cachezustand unbekannt; nach HACS-Update, HA-Neustart und vollständigem Neuladen die angezeigte Version prüfen. Keine native Browserprüfung behauptet.

- 0.5.6 gepusht und veröffentlicht; HACS-Datei remote und ZIP-Dateien gegen Tag geprüft. Kein HA-Deployment durch den Agenten.

## Nutzerwunsch 0.5.7: beim Melder testen

- Testen-Button pro Melder in der Liste Melder & Alarme. Öffnet die vorhandene Ausgabenprobe mit dem tatsächlichen Melder vorausgewählt; Gerätewahl und Ausgabe folgen im Dialog.
- Keine echten Sensorwechsel, keine zusätzliche Alarmregel oder Basistestfreigabe. Deaktivierte/falsche Zuordnungen sowie laufende Alarme weiterhin abweisen.
- 50 Frontendtests erfolgreich, drei zusätzliche Fälle für Feuer/Info/Warnung, echte Melderkennung im Testauftrag und ungültige Vorauswahl. Python-Transport unverändert; letzte Gesamtprüfung 216 Tests in 0.5.5. Keine native Geräteprüfung behauptet.

- Vor dem automatischen Lauf bereits begonnener Nutzerauftrag abgeschlossen: Melder-Testeinstieg 0.5.7 veröffentlicht; HACS-Datei remote und ZIP-Dateien gegen Tag geprüft. Keine weitere Produktänderung oder Veröffentlichung aus dem automatischen Prüfauftrag. Dokumentation dieses Abschlusses lokal committet; Gerätetests beim Benutzer weiterhin offen.

## Automatischer Nachtlauf 05.11.2026: B6 veraltete Rückmeldungen

- Ausgangsstand auf develop bei 82dc06f sauber; vorhandenen lokalen Dokumentationscommit erhalten. Keine Änderung am veröffentlichten Gerätesteststand 0.5.7.
- Nachgestellt: Fehlalarm-Anfrage für beendetes Ereignis erzeugt neue Kennung; „Ich komme“ liefert ungefangenen Modellfehler; abgewiesene Bestätigung verbraucht trotzdem Kennung und trägt sie als erfolgreich abgeschlossen ein.
- Abschlussprüfung vor neuen Token-/Journaländerungen; kontrollierte Fehlermeldung „Dieses Ereignis ist bereits beendet“. Bereits legitime Wiederholungen bleiben idempotent: gesehen, bestehendes „Ich komme“, bereits beendeter Melder und gültig wiederholte Fehlalarm-Bestätigung.
- Sechs neue Regressionen einschließlich ended/false_alarm und noch offener Kennungen. 222 Python-/50 Frontendtests, Syntax/Metadaten/Versionen und Whitespace erfolgreich.
- Lokaler Checkpoint 0.5.8; kein Push, Release, Deployment oder Lizenzwechsel. Echte Geräte-/HA-Prüfungen weiterhin offen.
