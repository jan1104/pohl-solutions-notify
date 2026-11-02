# Projektanalyse: Pohl Solutions Alarm Notify

Stand: 02.11.2026 · Softwareversion 0.3.24 · geprüfter Ausgangscommit `68f227a`

## Einschätzung

Das Projekt enthält eine bereits umfangreiche Home-Assistant-Custom-Integration
mit eigener Oberfläche, Alarmmodell, Geräteeinrichtung und mehreren Versandwegen.
Die Trennung zwischen Modell und Home-Assistant-Anbindung ist hilfreich. Der Stand
ist als Entwicklungsbasis brauchbar, aber die Prüfung zeigt konkrete Lücken bei
parallelen Alarmen, Rückmeldungen und Gerätewiederherstellung. Eine verlässliche
Freigabe für den Produktivbetrieb lässt sich daraus noch nicht ableiten.

Die Analyse umfasst alle 14 gelieferten Quell- und Metadatendateien sowie
Dokumentation, Tests und Workflow. Keine funktionalen Änderungen wurden vorgenommen.
Quelltext und einzelne Abläufe wurden geprüft; Home Assistant, Companion-Geräte
und Browser Mod standen nicht als laufende Testumgebung zur Verfügung. Aussagen
über tatsächliche Tonwiedergabe oder das sichtbare Layout auf Geräten wären deshalb
nicht belegt.

## Was die Software ist

Pohl Solutions Alarm Notify läuft innerhalb einer Home-Assistant-Instanz. Sie ist
keine eigenständige mobile App und enthält keinen eigenen Cloudserver. Die Oberfläche
wird von HA geladen. Mobile Nachrichten werden an vorhandene Companion-Notify-Dienste
übergeben; Browser-Mod-Dienste öffnen Alarmfenster. Ob mobile Nachrichten lokal oder
über externe Pushdienste transportiert werden, hängt von der Companion-/HA-Konfiguration ab.

Node-RED wird in der Oberfläche als Signalquelle genannt, ist aber technisch nicht
zwingend: Der Code verarbeitet passende HA-Binary-Sensoren und direkte HA-Aktionen.
Komplexe Auslösebedingungen gehören in die vorgeschaltete Automation.

## Aufbau

| Baustein | Datei | Aufgabe |
| --- | --- | --- |
| HA-Einstieg | `custom_components/alarm_system/__init__.py` | Einrichtung, Aktionen, WebSockets, Rechteprüfung für Verwaltung |
| Ersteinrichtung | `config_flow.py` | Eine Integration mit Standortkennung |
| Ereignismodell | `model.py` | Zustände, Meldergruppen, Empfänger, Journal, Aufbewahrung |
| Ablaufsteuerung | `engine.py` | Speicherung, Versand, Wiederholungen, Ton/TTS, Wiederherstellung, Browserfenster |
| Sicherung und Ansicht | `configuration.py` | Importprüfung, Gerätestest-Auswertung, Kontofilterung |
| Geräteerkennung | `discovery.py` | Companion-/Browser-Mod-Zuordnung und Sensorauswahl |
| Anzeigenamen | `identity.py` | Interne Konto-UUIDs als Anzeigenamen vermeiden |
| Diagramme | `charts.py` | Recorder-Abfrage und PNG-Erzeugung |
| Oberfläche | `frontend/panel.js` | Alarmansicht, Verlauf, Kameras, Assistenten, Export |
| Metadaten | `manifest.json`, `const.py`, `services.yaml`, Übersetzungen | Integration, Version, Aktionen und Texte |

Die Engine umfasst 917 Zeilen. Das Frontend umfasst rund 86 KB in 227 sehr dichten
Zeilen; die längste Zeile enthält 6.505 Zeichen. Damit sind viele Funktionen vorhanden,
Änderungen und Reviews aber unnötig schwer. Es gibt keinen Frontend-Buildschritt.

## Ablauf eines Ereignisses

1. Ein Binary-Sensor wechselt auf `on`, oder eine Automation ruft `raise_alarm` auf.
2. `INFO` und `WARNING` werden als Nachrichten verarbeitet. `FIRE` und `INTRUSION`
   erzeugen ein gespeichertes Ereignis mit einer oder mehreren Melderzeilen.
3. Gleiche `alarm_key`-Werte fassen Melder zu einem Ereignis zusammen. Feuer und
   Einbruch dürfen dieselbe Gruppe nicht gleichzeitig verwenden.
4. Die Engine speichert den Zustand und wählt aktivierte, getestete Geräte
   aktivierter Benutzer mit passender Alarmart aus.
5. Je nach Gerät folgen Push, Browserfenster, Alarmton und Android-Sprachansage.
6. Eine Rückmeldung setzt Ereignisse auf `claimed`; einzelne Melder oder ein
   bestätigter Fehlalarm können das Ereignis beenden.
7. Ein `off`-Signal beendet einen Alarm ausdrücklich nicht. Es hebt die Sperre
   gegen erneutes Auslösen eines bereits beendeten, zuvor aktiven Melders auf.

Zustände: `open` → `claimed` → `ended`; zusätzlich `false_alarm` als Abschluss.
Ein Alarm kann auch direkt aus `open` beendet werden.

## Bereits sinnvoll gelöst

- Das Modell kann ohne Home Assistant geprüft werden.
- Verwaltungsaktionen verlangen einen aktiven HA-Administrator.
- Rückmeldungen verwenden das angemeldete Konto statt einer frei wählbaren Benutzer-ID.
- Fehlalarm-Bestätigung ist an Konto und Ereignis gebunden und läuft nach 60 Sekunden ab.
- Geräteeinstellungen werden vor Änderungen als Wiederherstellungsdaten gespeichert.
- Unbekannte Android-Lautstärke/Ruftonwerte werden nicht blind überschrieben.
- Import wird zunächst validiert, muss zum Standort passen und ist während aktiver
  Alarme oder vorhandener Wiederherstellungsdaten gesperrt.
- HTML-Texte werden an vielen Stellen escaped; CSV-Zellen berücksichtigen typische
  Formelanfänge. Das ist hilfreich, ersetzt aber keinen vollständigen Sicherheitstest.
- Die Oberfläche unterscheidet angeforderte Übertragung von bewiesenem Empfang.

## Wesentliche Befunde

### 1. Hohe Priorität: Globale Alarmpriorität blockiert andere Empfänger

Fundstellen: `engine.py:473`, `engine.py:476`, besonders die Auswahl bei Zeile 486.

`primary()` bevorzugt Einbruch vor Feuer. `cycle()` lässt ausschließlich das erste
offene Ereignis seinen regulären Gerätezyklus ausführen. Diese Entscheidung erfolgt
für die gesamte Instanz und berücksichtigt keine unterschiedlichen Empfängergruppen.

Beispiel: Einbruch ist offen und hat Empfänger A; anschließend wird Feuer mit
Empfänger B ausgelöst. Der Feuerzyklus kehrt vor der Empfängerauswahl zurück.
Der Einbruchzyklus kann eine stumme Zusatzstatusmeldung an Feuerempfänger schicken,
aber deren regulärer Feuer-Alarmzyklus läuft nicht. Auch ein Ereignis ohne geeignete
Empfänger kann dadurch ein anderes Ereignis blockieren.

Nachgestellt durch Ausführung der unveränderten Methoden `primary()` und `cycle()`
in einem isolierten Prüfobjekt: Der Feuerzyklus endet vor jedem Zustellversuch.

Empfehlung: Priorität je Gerät bzw. Empfänger bestimmen. Jeder berechtigte Empfänger
muss weiterhin einen für ihn relevanten Alarm erhalten. Die gewünschte Priorität
zwischen Feuer und Einbruch ausdrücklich festlegen.

### 2. Hohe Priorität: Fehlgeschlagene Wiederherstellung überspringt Push

Fundstelle: `engine.py:532` bis `engine.py:536`.

Wenn alte Android-Wiederherstellungsdaten existieren und `restore_device()` sie nicht
lösen kann, meldet `play_device()` nur `audio_skipped` und beendet sich. Der spätere
Aufruf von `notify()` wird ebenfalls übersprungen, obwohl Push aktiviert ist.
Damit verhindert ein Fehler im Ton-/Wiederherstellungspfad auch die Ersatzmeldung.

Mit der unveränderten Methode und einer absichtlich erfolglosen Wiederherstellung
nachgestellt: protokolliert wird `audio_skipped`; `notify()` wird nicht aufgerufen.

Empfehlung: Die laute Ausgabe aussetzen, aber eine normale Push-Nachricht senden;
Wiederherstellung separat und begrenzt wiederholen.

### 3. Hohe Priorität: Wiederherstellungsdaten werden vor Gerätebestätigung gelöscht

Fundstelle: `engine.py:687` bis `engine.py:699`.

Bei der Kategorien-Einrichtung werden zurückgemeldete Sensorwerte geprüft. Bei einer
Alarmwiedergabe reicht dagegen die erfolgreiche Annahme dreier HA-Serviceaufrufe,
um die gespeicherten ursprünglichen Rufton-/Lautstärkewerte zu löschen. Das beweist
nicht, dass ein offline befindliches oder verzögert reagierendes Handy sie übernommen hat.

Mit angenommenen Serviceaufrufen und weiterhin abweichenden Sensorwerten nachgestellt:
Der ursprüngliche Zustand wird aus `leases` entfernt. Das bestätigt das Speicherverhalten,
nicht die tatsächliche Reaktion eines realen Handys.

Zusätzlich gibt es in `tick()` keinen allgemeinen Wiederholungsdienst für fehlgeschlagene
Alarm-Wiederherstellungen nach Abschluss eines Ereignisses. Ein Neustart versucht
Wiederherstellung; die automatische Kategorien-Einrichtung behandelt nur Setup-Leases.

Empfehlung: Wiederherstellung erst nach bestätigten Werten abschließen, mit Zeitgrenze,
Wiederholungsplan und sichtbarem Status. Ursprüngliche Werte bis dahin erhalten.

### 4. Fachlich zu entscheiden: Eine Antwort wirkt über Alarmberechtigungen hinweg

Fundstellen: `model.py:189`, insbesondere Zeile 195; `engine.py:168`.

Das ist eine bereits eingebaute Regel: Eine normale Antwort „Ich komme“ setzt alle
offenen Ereignisse auf `claimed`. Die Berechtigung wird nur für das angeklickte Ereignis
geprüft. Ein ausschließlich für Feuer berechtigtes Konto kann deshalb durch seine
Feuer-Rückmeldung auch die Einbruchalarmierung anderer Empfänger stillsetzen.

Nachgestellt: `authorized(user, intrusion)` ist falsch; nach `come(fire, user)` ist
der Einbruch trotzdem `claimed`. Der bisherige Test prüft gerade das globale Verhalten
und bewertet es als erfolgreich.

Das ist keine offene Frage der Implementierung, sondern eine Produktentscheidung:
Soll jede Rückmeldung wirklich die gesamte Anlage stummschalten? Falls ja, muss dieses
weitreichende Recht ausdrücklich vorgesehen und in der Oberfläche erklärt werden.
Andernfalls nur das betreffende oder weitere ausdrücklich berechtigte Ereignisse ändern.

### 5. Mittlere Priorität: Deaktivierung sperrt keinen Lesezugriff

Fundstelle: `configuration.py:70` bis `configuration.py:84`.

`user_view()` filtert nach Alarmarten, prüft aber nicht `enabled`. Ein in der Integration
deaktiviertes, weiterhin bei HA angemeldetes Konto erhält noch seine zugewiesenen
Alarmereignisse, Melder und Verlaufseinträge. Nachgestellt mit einem deaktivierten
Feuerkonto und einem Feuerereignis: Das Ereignis bleibt in der Rückgabe sichtbar.

Die deaktivierten Konten werden beim regulären Versand und bei Rückmeldungen anders
behandelt. Die gewünschte Bedeutung von „deaktiviert“ sollte daher ausdrücklich
festgelegt werden. Falls es auch Zugriff entziehen soll, muss die Lesefilterung folgen.

Zusätzlich veröffentlicht `publish()` in `sensor.alarm_system_active` die Titel,
Typen und Zustände sämtlicher aktiver Ereignisse. Diese Entität verwendet nicht die
eigene alarmartenbezogene Kontofilterung. Die tatsächlichen Zugriffsrechte auf diese
Entität müssen in HA gesondert geprüft werden.

### 6. Mittlere Priorität: Verlaufsbilder umgehen die Kontofilterung

Fundstelle: `charts.py:81` bis `charts.py:88`.

Verlaufsbilder werden in `www/alarm_system_charts` gespeichert und über `/local/`
ausgeliefert. HA dokumentiert ausdrücklich, dass Dateien aus `www` nicht durch die
HA-Anmeldung geschützt sind. Kennt jemand die URL und kann die HA-Instanz erreichen,
kann die eigene Benutzer-/Alarmartenfilterung den Bildabruf nicht verhindern.
Zufällige Dateinamen erschweren das Erraten, ersetzen aber keine Zugriffskontrolle.

Die 24-Stunden-Bereinigung läuft ausschließlich beim Erzeugen weiterer Bilder;
wenn keine weiteren Bilder entstehen, können ältere Dateien liegen bleiben.

Empfehlung: Zugriffsgeschützte Auslieferung oder ausdrücklich freigegebene Bildinhalte;
Aufräumen zeitgesteuert durchführen.

Quelle: https://www.home-assistant.io/integrations/http/#hosting-files

## Weitere Verbesserungen

- **Gerätetest auf Serverseite:** `__init__.py:268` verlangt die beiden Tests nur,
  wenn bereits eine `test_session` existiert. Ein Administrator kann ein frisch
  angelegtes Gerät direkt per `device_confirm` freigeben. Die Oberfläche erzwingt
  den Ablauf strenger. Das ist keine Rechteausweitung für normale Konten, aber die
  behauptete Testpflicht ist serverseitig nicht durchgehend abgesichert.
- **Wachsende Datenmenge:** Aufbewahrung ist standardmäßig unbegrenzt. Modellzustand,
  Journal und Ereignisse werden tief kopiert und gemeinsam gespeichert. WebSocket-
  Abfragen übertragen den vollständigen sichtbaren Bestand; die Begrenzung auf
  50 abgeschlossene Ereignisse erfolgt erst in der Darstellung. Keine Messung einer
  konkreten Leistungsgrenze; bei längerer Nutzung ist ein Lasttest erforderlich.
- **Wartbarkeit:** `engine.py` bündelt zu viele Verantwortlichkeiten. `panel.js`
  verbindet CSS, Dialoge, Kamera, Export, Zustand und Kommunikation in einer Datei.
  Lesbar formatieren und danach in zusammenhängende Bausteine aufteilen.
- **Metadaten:** Dokumentationslink verweist auf allgemeine HA-Dokumentation;
  Codeowners fehlen. Unterstützte HA-/Companion-/Browser-Mod-Versionen sind unbestätigt.
- **Produktfluss:** Node-RED ist sprachlich fest verankert, obwohl andere HA-Signalquellen
  möglich sind. Generische Begriffe und ein Node-RED-Beispiel würden den Einsatz erleichtern.
- **Lebenszyklus und Nebenläufigkeit:** Laden, Entladen, HA-Neustart, abgebrochene
  Aufgaben und parallele Geräteantworten benötigen Integrationstests. Hier wird
  ohne Laufzeitnachweis kein zusätzlicher konkreter Fehler behauptet.

## Prüfstand

Erfolgreich erneut ausgeführt:

- Prüfung von elf Python-Dateien und drei JSON-Dateien samt Versionskonsistenz.
- Neun vorhandene Verhaltenstests.
- JavaScript-Syntaxprüfung mit Node.js.
- Fünf gezielte isolierte Ablaufprüfungen für Lesen deaktivierter Konten, globale
  Rückmeldung, Alarmpriorität, Löschen von Wiederherstellungsdaten und Push-Ausfall
  bei fehlgeschlagener Wiederherstellung.

Die isolierten Ablaufprüfungen zeigen bestehendes Verhalten und sind keine
vollständigen HA-Integrationstests. Die vorhandene GitHub-Prüfung importiert weder
Home Assistant noch die vollständige Engine, führt keinen Browser aus und prüft
keine realen Mobilgeräte. Erfolgreiche CI allein belegt daher keine betriebsbereite App.

## Empfohlene Reihenfolge

1. Gewünschte Regeln für parallele Alarme und globale Rückmeldung festlegen.
2. Zustellung pro Empfänger sicherstellen und Push vom Tonfehlerpfad entkoppeln.
3. Wiederherstellung mit Bestätigung und wiederholbaren Versuchen absichern.
4. Deaktivierung und Zugriffe über Panel, HA-Entitäten und Bilder vereinheitlichen.
5. Die gefundenen Fälle als Regressionstests ergänzen; HA-Laufzeittests aufbauen.
6. Frontend und Engine schrittweise aufteilen, getestete Versionsmatrix dokumentieren.
7. Erst danach eine getestete neue Softwareversion und Veröffentlichung vorbereiten.

Alle Befunde beziehen sich auf den unveränderten importierten Stand. Die Analyse
selbst veröffentlicht nichts und behebt keine der genannten Stellen automatisch.
