# Änderungen

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
