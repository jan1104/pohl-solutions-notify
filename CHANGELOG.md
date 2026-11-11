# Änderungen

## 0.5.17 – geprüfter Stand für die praktische Geräteprüfung

- Fasst die Korrekturen seit 0.5.7 für Alarmfenster, Rückmeldungen, Sensorverfügbarkeit, Imports und Entladen zusammen.
- Ergänzt Wiederherstellungsprüfungen und aktualisiert die Versions- und Installationsangaben. Die praktische HA-/Android-/Browser-Mod-Prüfung steht aus.

## 0.5.16 – Wartende Rückmeldungen beim Entladen absichern

- Wartende Rückmeldungen werden abgewiesen, wenn das Entladen vor der Verarbeitung beginnt. Eine bereits gespeicherte Rückmeldung bleibt erhalten. Die alte Instanz startet dafür keinen Statusversand mehr.

## 0.5.15 – Wartende Melderereignisse beim Entladen anhalten

- Ein bereits wartendes Melderereignis prüft den Stoppzustand, sobald es die Modellsperre erhält. Ist die Auslösung schon gespeichert, übernimmt die nächste Instanz den Alarm. Die alte Instanz startet nach dem Speichern keinen neuen Versandauftrag.

## 0.5.14 – Laufende Timer beim Entladen anhalten

- Der Timer prüft nach dem Warten auf die Sperre, das Speichern und die Bildbereinigung, ob die Integration gerade entladen wird. So kann ein bereits laufender Timer nach Beginn des Entladens keine neuen Alarm- oder Wiederherstellungsaufträge starten.

## 0.5.13 – Vorrang beim Öffnen eines wartenden Alarmfensters prüfen

- Nach der Wartezeit prüft die Engine, welcher Alarm am jeweiligen Gerät Vorrang hat. Ein überholter Feuerauftrag öffnet am gemeinsamen Browser kein Fenster, wenn Einbruch inzwischen Vorrang hat.

## 0.5.12 – neueres Alarmfenster beim Beenden eines älteren Alarms erhalten

- Die Integration prüft vor dem Schließen, welches Ereignis das Fenster am Browser belegt. Ein Fenster für einen anderen Alarm bleibt offen.
- Öffnen und Schließen verwenden dieselbe Sperre. Eine verzögerte Schließanfrage kann dadurch innerhalb der Integration kein gleichzeitig angefordertes neueres Fenster schließen.

## 0.5.11 – ungültige Sensorzuordnungen beim Import abweisen, nur lokal

- Klingelmodus-, Lautstärke- und Browser-Sichtbarkeitssensoren in Sicherungen dürfen keine Listen, Objekte oder Zahlen sein. Solche Werte konnten später Ton- oder Popup-Verarbeitung mit einem Typfehler abbrechen.
- Import wird vor dem Zustandsaustausch verständlich abgewiesen. Fehlende, leere, null und vorübergehend nicht verfügbare Sensorzuordnungen bleiben kompatibel; Geräte müssen weiterhin neu getestet werden.
- Vier zusätzliche Regressionen; 236 Python- und 52 Frontendtests erfolgreich. Nur lokaler Checkpoint; kein Push, Release oder Deployment.

## 0.5.10 – Sensorverfügbarkeit korrekt protokollieren, nur lokal

- Wiederholtes unknown/unavailable nicht mehr als wiederholten Zustandswechsel speichern. Übergänge nennen den zuletzt beobachteten Zustand statt der letzten gültigen Ein-/Aus-Flanke.
- Beobachtungen nur im Arbeitsspeicher; Alarmflanken und Unterdrückung bleiben unverändert. Verfügbarkeit allein beendet oder entsperrt keinen Alarm.
- Fünf neue Regressionen; 229 Python- und 50 Frontendtests erfolgreich. Nur lokaler Checkpoint; kein Push, Release oder Deployment.

## 0.5.9 – ungültige importierte Zeitwerte abweisen, nur lokal

- Gerätezeiten in Sicherungen akzeptieren keine JSON-Booleans mehr: true wurde bisher still zu einer Sekunde. Ungültige Typen, nicht endliche Werte und Werte außerhalb der bisherigen Grenzen werden kontrolliert abgewiesen.
- Bestehende Zahlen, numerische Legacy-Texte und Standardwerte bleiben kompatibel; abgewiesene Importe ändern weder Sicherung noch aktuelle Einrichtung.
- 224 Python- und 50 Frontendtests erfolgreich. Nur lokaler Checkpoint; kein Push, Release oder Deployment.

## 0.5.8 – veraltete Rückmeldungen abweisen, nur lokal

- Fehler nachgestellt: Für bereits beendete Ereignisse ließen sich neue Fehlalarm-Bestätigungen erzeugen. Spätere Bestätigung konnte die Kennung verbrauchen und als abgeschlossen vormerken, bevor das Modell den Vorgang ablehnte.
- Neue Rückmeldungen an abgeschlossene Ereignisse vor Protokoll-/Tokenänderungen kontrolliert abweisen. Gültige wiederholte Rückmeldungen bleiben ohne weitere Nebenwirkung.
- 222 Python- und 50 Frontendtests erfolgreich. Nur lokaler Checkpoint; kein Push, Release oder Deployment.

## 0.5.7 – Ausgaben direkt beim Melder testen

- Jeder Melder erhält unter Melder & Alarme einen Testen-Button. Die bestehende Ausgabenprobe öffnet mit genau diesem Melder vorausgewählt.
- Geräteauswahl und getrennte Push-/Ton-/Sprach-/Fensterprobe wie bei Alarmarten; keine Sensorumschaltung und keine Gerätefreigabe.
- Deaktivierte/falsche Melder und laufende Alarme bleiben gesperrt. 50 Frontendtests und Syntax-/Versionsprüfung erfolgreich.

## 0.5.6 – kürzerer Alarmarten-Dialog

- Lange Erklärungstexte unter Weitere Hinweise einklappen, Beschriftungen und Zeit-Hinweise kürzen.
- Standard-Sprachtext bleibt immer sichtbar. Zusätzliche eigene Vorschau nur bei einem eingegebenen eigenen Text anzeigen; Einfügeschaltflächen bleiben vorhanden.
- Einstellungen, Validierung und Alarmablauf unverändert. 47 Frontendtests sowie Syntax-/Versionsprüfung erfolgreich; keine native Browserprüfung.

## 0.5.5 – keine zusätzliche Empfangspause, verständlicher Detailverlauf

- Reproduzierbaren Ablauf korrigiert: Empfangsbestätigung wird parallel beobachtet. Vor Sprache wird nur die konfigurierte Tonphase abgewartet, nicht zusätzlich bis zu zehn Sekunden auf eine Bestätigung.
- Abbruch, „Ich komme“, Geräte-/Prioritätswechsel und neuere Wiedergabeaufträge behalten ihre Schutzprüfungen. Empfang bleibt vom tatsächlichen Abspielen unterschieden.
- Detailverlauf mit deutschen Ereignisnamen, Melder-/Gerätenamen und getrennten Abschnitten für Ereignisse sowie Geräte/Zustellung. Nahe identische Versandanforderungen zusammenfassen; Rohdaten unter Technische Details.
- Die tatsächliche Länge eines Android-Benachrichtigungsklangs wird dadurch nicht verlängert. Keine zusätzlichen Push-Wiederholungen innerhalb der Tonphase.
- 216 Python- und 47 Frontendtests erfolgreich. Erneute echte Android-Prüfung erforderlich.

## 0.5.4 – Ton- und Sprachzeiten bei der Alarmart

- Im Geräteassistenten entfallen Feuer-/Einbruch-/Sprachzeitfelder. Geräte behalten ihre Schalter für erlaubte Ausgaben; Zeiten werden unter Alarmarten bearbeitet.
- Feuer und Einbruch unterstützen wie eigene Alarmarten zentrale Tonphasen- und Sprachzeiten. Die vorhandenen Prioritäten bleiben fest.
- Bestehende individuelle Gerätezeiten bleiben erhalten, solange kein zentraler Wert gewählt wird; bei der Alarmart einsehbar. Ein leerer Systemalarm-Zeitwert verwendet diese bisherigen Gerätezeiten.
- Vereinfachtes Speichern eines Geräts setzt ausgelassene bisherige Zeiten nicht zurück. Neue Profilzeiten bleiben über Schema-2-Sicherungen erhalten.
- 210 Python- und 44 Frontendtests erfolgreich; echte HA-/Android-Prüfung offen.

## 0.5.3 – Entladen nach Aufräumfehlern wiederholbar, nur lokal

- Reproduziert: Ein Fehler beim Entfernen eines Dienstes brach alle weiteren Aufräumschritte ab; die Engine war bereits entfernt und ein erneuter Entladeversuch meldete fälschlich Erfolg.
- Nach erfolgreichem Stoppen alle Ressourcenentfernungen versuchen und den ersten Fehler erhalten. Bei einem Fehler die gestoppte Engine für einen erneuten Versuch behalten; erst nach vollständigem Aufräumen entfernen.
- Fehlgeschlagener Engine-Stopp bewahrt weiterhin Engine und Wiederherstellungsdaten. Bestehende Startfehlerbehandlung verwendet dieselbe Ressourcenbereinigung, ohne ihren ursprünglichen Fehler zu verdecken.
- Nur lokal vorbereitet, kein Push, Release oder Deployment. Echte HA-Prüfung weiterhin offen.

## 0.5.2 – Importschalter eindeutig prüfen, nur lokal

- Fehler reproduziert: Der JSON-Text "false" wurde bei Benutzer-/Melderaktivierung und Stummschaltung als wahr ausgewertet; ein Geräteaktivierungsschalter konnte als wahrer Text stehenbleiben.
- Import akzeptiert für diese Schalter nur echte JSON-Werte true/false. Mehrdeutige Texte, Zahlen und Container werden vor dem Austausch der Einstellungen abgewiesen.
- Fehlende ältere Schalter behalten ihr bisheriges Verhalten; ein fehlender Geräteaktivierungsschalter wird nicht automatisch eingeschaltet. Eingabedokument und laufende Einstellungen bleiben bei Fehlern unverändert.
- Sechs neue Regressionstests mit beiden unterstützten Sicherungsschemas. Kein Push, Release oder Deployment.

## 0.5.1 – Fehlalarm-Bestätigungen abgesichert, nur lokal

- Fehler nachgestellt: Eine falsch zugeordnete Abbruch-/Bestätigungsanfrage verbrauchte zuvor eine noch gültige fremde Bestätigungskennung. Kennungen erst nach passender Benutzer-/Ereignisprüfung entfernen.
- Abgelaufene offene und bereits verwendete Bestätigungen werden bei Rückmeldungen sowie im regelmäßigen Lauf aus dem Arbeitsspeicher entfernt; Ablaufgrenze konsequent beachten.
- Gültige Wiederholungen bleiben innerhalb ihres Zeitfensters ohne weitere Zustandsänderung. Keine Änderung der Alarmprioritäten oder Ausgaben.
- Acht neue Regressionstests; echte HA-/Android-Prüfung weiterhin offen. Nicht gepusht oder veröffentlicht.

## 0.5.0 – gezielte Ausgabetests und Empfängerübersicht

- Unter Alarmarten einzelne Push-, Ton-, Sprach- oder Fensterproben für ein zugeordnetes Gerät anfordern; optional echte Melderdaten statt Beispielen verwenden.
- TEST-Kennzeichnung, gezielter Stopp, automatische Bereinigung und erneuter Stopp nach Transportfehlern. Keine Sensoränderung, Alarmereignisse oder Gerätefreigabe.
- Tests beachten Profil-/Geräteschalter, Plattform und Empfängerrechte; während Alarmen, Einrichtung und Wiederherstellung gesperrt. Tonprobe verwendet normale Benachrichtigungseinstellungen.
- Neue Übersicht „Wer bekommt was?“ bei Melderzuordnung und Alarmarten zeigt wirksame Ausgaben, fehlende Zuordnungen und offene Geräteprüfungen ohne Zustellversprechen.
- Zeitlich begrenzte Testtransporte geben beim Alarmstart die Transportsteuerung frei; nicht bestätigte Abbrüche bleiben zur Bereinigung gesperrt. Speicherung außerhalb der Transportsperre.
- 185 Python- und 41 Frontendtests erfolgreich. Echte HA-/Android-/Browser-Mod-Prüfung offen; Anleitung in docs/OUTPUT_TESTS.md.

## 0.4.5 – kompakter Alarmverlauf

- Abgeschlossene Alarme sind einzeln standardmäßig zugeklappt. Die Kurzzeile zeigt Datum/Uhrzeit, Status, Alarmart und alle beteiligten Melder.
- Aufklappen zeigt die vorhandenen Details einschließlich Bereiche, Rückmeldungen und Verlauf/Transport. Geöffnete Einträge bleiben bei automatischer Aktualisierung geöffnet.
- Informationen/Warnungen erhalten ebenfalls kompakte aufklappbare Verlaufseinträge. „Gemeldet“ bestätigt keine tatsächliche Zustellung.
- Aktive Alarmansichten bleiben direkt sichtbar. 29 Frontendtests sowie Syntax-/Versionsprüfung erfolgreich; keine echte Browser-/HA-/Android-Prüfung.

## 0.4.4 – eine Meldungsart und automatische Meldergruppen

- Im Melderassistenten nur noch eine Auswahlliste **Art der Meldung** mit den angelegten Alarmarten; zusätzlicher Freitext und manuelle Ereignisgruppe entfallen.
- Angebundene Melder derselben Alarmart werden automatisch zu einem gemeinsamen Alarm zusammengefasst; stabile Typen-ID erhält die Zuordnung auch beim Umbenennen.
- Laufende alte Gruppen und Titel bleiben unverändert; vorhandene Fehlalarm-Sperren bis zum echten AUS erhalten. Alte Beschreibungen und Historie bleiben gespeichert.
- Direkte HA-Aktionen behalten ihre expliziten Gruppen; Informationen/Warnungen bleiben einzelne Meldungen.
- 156 Python- und 26 Frontendtests erfolgreich. Echte HA-/Android-/Browser-Prüfung weiterhin offen.

## 0.4.3 – Standard-Sprachtext immer sichtbar

- Unter dem Eingabefeld steht zusätzlich immer der automatische Standard-Sprachtext als verständliche Vorschau, auch bei einem eigenen Text.
- Der Standard folgt beim Bearbeiten dem Alarmnamen. Standort wird übernommen, Bereiche sind ausdrücklich Beispieldaten; bei Informationen wird der tatsächliche Meldertext erst beim Auslösen bestimmt.
- 24 Frontendtests einschließlich Standardvorschau und Namensänderung erfolgreich; Syntax und Versionskonsistenz geprüft. Keine echte Browser-/HA-/Android-Prüfung.

## 0.4.2 – verständliche Ansagen und flexible Informationsausgabe

- Sprachtext ist optional und zeigt bei der Standardansage kein technisches Vorlagenmuster mehr. Deutsche Einfügeschaltflächen und eine laufend aktualisierte Textvorschau erklären die dynamischen Angaben.
- Information/Warnung behalten alle vier Ausgabeschalter. Benachrichtigungston, Android-Sprachansage und Meldungsfenster sind unabhängig vom Push wählbar.
- Ohne eigenen Sprachtext lesen normale Meldungen ihren Benachrichtigungstext einmal vor. Geräteschalter und Empfängerrechte gelten weiterhin.
- Normale Meldungen erzwingen keine Handy-Lautstärke, erzeugen keinen quittierungspflichtigen Alarm und verdrängen laufende Alarme nicht. Stumm senden unterdrückt Ton und Sprache.
- 146 Python- und 24 Frontendtests bestanden; echte HA-/Android-Prüfung offen.

## 0.4.1 – HACS-Downloadmetadaten, lokal vorbereitet

- Fehlende `hacs.json` im Repository-Hauptverzeichnis ergänzt; Ursache der Meldung beim Download von `47f170b`.
- Projektlinks, Fehleradresse und Codeowner im Integrationsmanifest vervollständigt.
- HACS-Quelllayout in der bestehenden CI prüfen; Regressionen für fehlende/ungültige Metadaten und falsche Downloadlayouts.
- Alte Tags und `main` bleiben unverändert. GitHub-Übertragung und Release stehen aus.

## 0.4.0 – eigene Alarmarten, lokal vorbereitet

- Bis zu 32 frei benannte eigene Alarmarten; dynamische Auswahl bei Benutzern,
  Meldern, Gerätetests und Automationsaktionen.
- Name, Empfängerzuordnung, Priorität, Push, Ton, Sprache, Popup, Ablaufzeiten und
  Sprachvorlage individuell konfigurieren; Geräteschalter gelten zusätzlich.
- Vorhandene vier Arten automatisch übernehmen; Einbruch-/Feuerprioritäten beibehalten.
- Persistente eindeutige Typen-IDs und stabile Android-Kategorien bei Umbenennung.
- Neuer Alarmarten-Editor, Empfängerübersicht und IDs für Automationen; Namen auch
  in Versand, Verlauf und CSV dynamisch anzeigen.
- Konfigurationssicherung Schema 2 einschließlich Profilen, Schema 1 weiter lesbar.
- Eigene Geräte-Basistests unabhängig von regulärer Alarmzuordnung erlauben; fremde
  Tests und nicht zugewiesene echte Alarme bleiben gesperrt.
- Verwendete Arten nicht löschen und Änderungen bei laufender Alarmierung/Wiederherstellung sperren.
- 132 Python- und 21 Frontendtests erfolgreich. Reale HA-/Android-Prüfung steht aus.


## 0.3.29 – lokal vorbereitet, nicht veröffentlicht

- Vor dem Übergang vom Android-Alarmton zur Sprachansage wird die aktuelle Priorität
  für dieses Gerät erneut geprüft. Ein inzwischen eingegangener Einbruchalarm
  verhindert damit die nachträgliche Feueransage auf demselben Gerät.
- Getrennte Empfänger behalten ihre Ansage; alte Aufträge entfernen keine neueren Playback-Leases.
- Fehler bei einem Aufräumschritt nach fehlgeschlagenem Start verhindern die übrigen
  Aufräumversuche nicht mehr und verdecken nicht den ursprünglichen Startfehler.
- Fünf Regressionstests ergänzt; 92 Python- und sieben Frontendtests bestanden.


## 0.3.28 – lokal vorbereitet, nicht veröffentlicht

- Fehler beim Abmelden eines einzelnen Ereignislisteners werden protokolliert;
  übrige Listener, Hintergrundaufgaben und anschließende Gerätewiederherstellung
  werden trotzdem bearbeitet.
- Nach Beginn des Stopps eingehende Sensorereignisse, Empfangsbestätigungen und
  mobile Rückmeldungen werden ignoriert, damit verbliebene Listener keine neue Verarbeitung anstoßen.
- Acht Regressionstests für Aufräumfehler, späte Ereignisse und Wiederanlauf ergänzt.
- 87 Python- und sieben Frontendtests erfolgreich; bestehende Versionstags unverändert.


## Entwicklungsplanung – 03.11.2026

- Detaillierte Arbeitsliste mit 36 Paketen, Prioritäten, Abhängigkeiten und Fertig-Kriterien erstellt.
- Technische Gegenprüfung und zusätzliche Randfälle dokumentiert; neue Produktideen
  von laufender Fehler-/Testarbeit getrennt. App-Code und Versionstags unverändert.


## Versionssicherung – 03.11.2026

- Quellstände 0.3.27 und 0.3.25 mit festen lokalen Tags markiert; keine Änderung am App-Code.
- Weitere Entwicklung auf `develop`, bisheriger `main` bleibt als Ausgangsstand erhalten.
- Installationspakete aus Tags, lokale Git-Historiensicherung und Rückkehranleitung ergänzt.
- Gewünschte Nutzung von Subagenten für geeignete Programmieraufgaben dokumentiert.


## 0.3.27 – lokal vorbereitet, nicht veröffentlicht

- Android-Sprachansage funktioniert unabhängig vom Alarmton; eigene stoppbare
  Sprachaufträge ohne Änderungen an Rufton- oder Benachrichtigungslautstärke.
- Android-Geräte ohne Alarmton benötigen keine dafür vorgesehenen Sensoren oder
  stumme Kategorienvorbereitung. Sensorauswahl erst nach Wahl der Ausgabeoptionen verlangen.
- Ausgabeoptionen serverseitig typisieren und an Plattformen anpassen; Änderungen
  an Sprache, Push, Popup und Audiozeiten erfordern neue Geräteprüfung.
- Wirkung von Push und Sprachschalter verständlicher erklären. Android-Statusmeldungen
  mit niedriger Wichtigkeit anfordern, ohne bestehende Kanaleinstellungen zu überschreiben.
- 75 Python-Tests und sieben zusätzliche Frontend-Logiktests in der GitHub-Prüfung.
- Wichtig beim Update: Sprachansage ein bei Alarmton aus bedeutet jetzt tatsächlich
  nur Sprache. Für ein stilles Gerät beide ausschalten.


## 0.3.26 – lokal vorbereitet, nicht veröffentlicht

- Fehlgeschlagene/abgebrochene Einrichtung räumt eigene Laufzeitressourcen auf,
  ohne einen regulären Stop-/Speicherpfad mit teilweise geladenem Modell auszuführen.
- Doppelte Einrichtung ersetzt keine bestehende Engine; Neuladen verwendet statische
  Ressourcen und Bildroute weiter. Wiederholtes Entladen einer fehlenden Instanz ist unschädlich.
- WebSocket-Zugriffe bei entladener/stoppender Integration melden einen kontrollierten Fehler.
- Verschachtelte Verwaltungskennungen werden vor Journal- oder Speicheränderungen geprüft;
  fehlende/ungültige IDs und nicht vorhandene Testgeräte erzeugen keine internen KeyErrors mehr.
- Import entfernt alte Testsitzungen und flüchtige Wiederherstellungs-/Wartefelder zusätzlich
  zum bisherigen Zurücksetzen des Gerätestatus.
- 18 Regressionstests ergänzt, insgesamt 57 lokale Verhaltenstests erfolgreich.


## 0.3.25 – lokal vorbereitet, nicht veröffentlicht

- Alarmpriorität pro Gerät statt globaler Blockierung anderer Empfänger.
- Zusätzliche Alarme auf gemeinsamem Gerät erhalten eine stumme Nachricht.
- „Ich komme“ bestätigt ausschließlich das ausgewählte Ereignis.
- Push bleibt bei fehlgeschlagener vorheriger Wiederherstellung möglich.
- Android-Wiederherstellung benötigt frische bestätigte Sensorwerte; ursprüngliche
  Werte bleiben bis dahin gespeichert und fehlgeschlagene Versuche werden wiederholt.
- Ausstehende Wiederherstellung wird angezeigt und blockiert neue Gerätefreigabe.
- Deaktivierte Konten erhalten keine Alarmdaten mehr; unbekannte Konten keine Kontenliste.
- Generische aktive-Alarm-Entität enthält keine Ereignis- oder Standortdetails mehr.
- Private Verlaufsbilder mit angemeldetem, berechtigungsgeprüftem API-Abruf und
  Ablaufzeit; Start-/Stundenbereinigung einschließlich alter generierter öffentlicher Bilder.
- Gerätefreigabe verlangt serverseitig eine aktuelle Testsitzung mit beiden abgeschlossenen Alarmtests.
- 39 Verhaltenstests sowie Arbeitsplan für die automatische Weiterarbeit ergänzt.

## Repository-Vorbereitung für 0.3.24

- Vollständige Projektanalyse mit isoliert nachgestellten Befunden und priorisierten nächsten Schritten dokumentiert.

- Projekt als lokales Git-Repository für Pohl Solutions vorbereitet.
- Home-Assistant-Verzeichnisstruktur `custom_components/alarm_system` angelegt.
- Installations-, Bedienungs-, Architektur- und Entwicklungsdokumentation ergänzt.
- Proprietären Rechtehinweis ergänzt.
- Lokale Prüfungen, Verhaltenstests und GitHub-Actions-Prüfung ergänzt.
- GitHub-Vorlagen und Verbindung zum Repository eingerichtet; kein Push.

## 0.3.24 – importierter Ausgangsstand

Am 02.11.2026 aus `alarm_system.zip` übernommen. Diese Versionsnummer war bereits
im Quellstand enthalten. Eine frühere Änderungshistorie oder ein ursprüngliches
Veröffentlichungsdatum wurde nicht mitgeliefert. Quelldateien blieben beim Import unverändert.
