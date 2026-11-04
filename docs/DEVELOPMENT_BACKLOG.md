# Detaillierte Arbeitsliste: Pohl Solutions Alarm Notify

Stand: 03.11.2026. Planungsbasis: App 0.3.27, Entwicklungszweig `develop`,
Planungs-Ausgangspunkt `fc8abcb`. Feste Tags `v0.3.27` und `v0.3.25` bleiben unverändert.

## Ziel und Grenzen

Ein nachvollziehbares Android-Alarmsystem innerhalb von Home Assistant: schnell
bedienbar, verständliche Zustände und kontrolliertes Verhalten auch bei Ausfällen.
Mehr Funktionen allein sind kein Qualitätsnachweis. Vor neuer Oberfläche zuerst
Unterbrechungen, Datenhaltung und reale Gerätegrenzen absichern.

Planungsbasis: 79 Python-Tests und sieben Tests der Frontendlogik.
Aktueller Fortschritt: 0.3.29 mit 92 Python- und sieben Frontendtests; siehe WORK_PLAN.md. Diese arbeiten
mit ersetzten HA-/HTTP-/Browsergrenzen und sind keine Prüfung echter Geräte.
0.3.25 wurde vom Benutzer als bereits gelaufen gemeldet; 0.3.27 ist als lokaler Code
fest gesichert. Eine vollständige Hardware-/HA-Freigabe für 0.3.27 liegt nicht vor.

Dieser Auftrag erstellt den Plan. Die bestehenden Fehler-/Testarbeiten können im
bereits beauftragten Rahmen weiterlaufen. Neue Produktfunktionen und geänderte
Alarmregeln sind nachfolgend als Vorschläge gekennzeichnet und werden durch ihre
Aufnahme in diese Liste nicht automatisch eingebaut. Kein Push, Deployment oder
Lizenzwechsel gehört zu diesem Planungsauftrag.

## Feste Regeln

- Einbruch vor Feuer **auf demselben Gerät**; getrennte Empfänger bleiben unabhängig.
- „Ich komme“ bestätigt nur das ausgewählte Ereignis, nicht alle Alarme.
- Android-Sprache, Alarmton, Push und Popup haben die dokumentierten getrennten Wirkungen.
- Keine frei erfundenen Empfangs-/Wiedergabebestätigungen oder grünen Zustände aus
  einem lediglich angenommenen Serviceaufruf.
- Originale Handyeinstellungen und noch notwendige Wiederherstellungsdaten erhalten.
- Normale Konten sehen nur ihre berechtigten Daten; Administratorzugriff bleibt gesondert.
- Bestehende Versionsmarken nicht verändern, fremde Arbeit nicht überschreiben.

## Priorität, Aufwand und Abhängigkeiten

**P0:** vor einem belastbaren praktischen Update erforderlich.
**P1:** wichtigste nächste Bedienungs-/Qualitätsverbesserung.
**P2:** Wartung, Komfort und nach Messung begründete Optimierung.
**P3:** spätere Erweiterung, solange der Kern noch nicht ausreichend validiert ist.

Aufwand **S/M/L** ist relativ: klein und isoliert / mehrere Abläufe / umfangreich oder
mit realer Umgebung. Das sind keine festen Zeit- oder Kostenzusagen. Geplante
Tests sind Prüfaufträge; sie behaupten keine bislang unbestätigten Fehler.

| Paket | Inhalt | Priorität | Voraussetzung | Ergebnis |
| --- | --- | --- | --- | --- |
| A | Gesicherte Ausgangslage und Testumgebung | P0 | Projektzugriff; für Geräteprüfung Nutzerumgebung | Reproduzierbarer Teststand |
| B | Wiederherstellung, Unterbrechungen, Parallelität | P0 | A1–A2 | Nachgewiesene Fehlerabläufe |
| C | Daten, Rechte, Diagnose | P0/P1 | A; teilweise B | Geschützte, nachvollziehbare Daten |
| D | Geräteübersicht und gezielte Tests | P1, Vorschläge | B–C | Verständliche Bereitschaft und Einrichtung |
| E | Alarmansicht und Bedienung unter Stress | P1, Vorschläge | B; bewahrte Alarmregeln | Schnelle und fehlersichere Rückmeldung |
| F | Android-Sprache, Ton und Zustellung | P0/P1 | A3–A4 und B | Geprüfte Gerätewirkung |
| G | Code, Leistung und Versionspflege | P1/P2 | Messungen/Tests je Aufgabe | Wartbare und messbare Entwicklung |
| H | Erweiterungen über den Kern hinaus | P2/P3, Vorschläge | Kernprüfung und Produktentscheidung | Bewusst gewählter Mehrwert |

## A – Ausgangslage und reale Testfähigkeit

### A1 [P0, S] Gesicherte Quellen unverändert halten

- [ ] Vor jedem Arbeitsschritt Branch und Arbeitsstand prüfen; nur auf `develop` ändern.
- [ ] Versionstags, Manifestversion, Quellcommit und Paket-Prüfsumme zusammen dokumentieren.
- [ ] Neue funktionale Änderungen separat versionieren; 0.3.27 nicht nachträglich umetikettieren.

**Fertig, wenn:** ein Quellpaket aus dem Tag unabhängig vom aktuellen Arbeitsordner
wieder erzeugt und geprüft werden kann. Vorhandene Pakettests und Hashdatei verwenden.

### A2 [P0, M] Rückkehr tatsächlich proben

- [ ] Git-Bundle testweise in ein leeres temporäres Repository klonen und beide Tags prüfen.
- [ ] Pakete in temporäre Ordner entpacken und Struktur/Version gegen den Tag prüfen.
- [ ] Zuordnung von HA-Sicherung und Integrationsversion festhalten.
- [ ] Downgrade mit ausstehenden neueren Sprachaufträgen als unzulässigen Zustand erkennen;
  keine automatische Löschung interner HA-Daten als Abkürzung vorsehen.

**Fertig, wenn:** Quellen aus einer unabhängigen Kopie wiederherstellbar sind und die
praktische HA-Rückkehr anhand einer zugehörigen Sicherung dokumentiert ist.
Die Git-Probe kann lokal erfolgen; die HA-Probe braucht eine Testinstanz.

### A3 [P0, S/M] Umgebung eindeutig erfassen

- [ ] Android-Modell/-Version, Companion-Version, HA-Version und Installationsart erfassen.
- [ ] Browser-Mod-Version und registrierte Browser nur dann erfassen, wenn tatsächlich genutzt.
- [ ] Testkonten/-geräte festlegen; keine Produktionskonten oder kompletten privaten Exporte einchecken.
- [ ] Unterstützte Versionen erst nach Test als bestätigt eintragen.

**Fertig, wenn:** jeder praktische Test einem konkreten Versionsstand und Gerät zugeordnet ist.
Fehlende Angaben sind als unbekannt markiert, nicht durch Annahmen ersetzt.

### A4 [P0, L] Echte HA-Grenzen prüfen

- [ ] Laden, Entladen und erneutes Laden in einer getrennten HA-Umgebung prüfen.
- [ ] Reale Konfigurationsschemas und WebSocket-Fehlermeldungen testen.
- [ ] Geschützten HTTP-Bildabruf mit echten Benutzeranmeldungen prüfen.
- [ ] 0.3.27-Paket installieren und die Testmatrix aus `HA_TEST_PROTOCOL.md` protokollieren.

**Fertig, wenn:** Ergebnisse mit HA-Protokollen/Versionen vorliegen. Lokal ersetzte
Importadapter dürfen dieses Häkchen nicht erfüllen. Keine Installation auf dem
produktiven HA ohne entsprechenden Nutzerauftrag.

## B – Alarmabläufe und Wiederherstellung

### B1 [P0, M] Neustart an kritischen Stellen simulieren

- [ ] Vor/nach Speichern der ursprünglichen Lautstärke unterbrechen.
- [ ] Während Alarmton, TTS, nur Sprache und Wiederherstellung unterbrechen.
- [ ] Beim Neustart bestehende reguläre Alarme, abgebrochene Tests und gespeicherte
  Sprach-/Wiederherstellungsaufträge getrennt prüfen.

**Fertig, wenn:** keine Originalwerte verloren gehen, keine verwaisten Aufgaben
zurückbleiben und ein Test nicht unbemerkt als regulärer Alarm fortgesetzt wird.

### B2 [P0, M] Parallelität und Prioritätswechsel prüfen

**Teilfortschritt 0.3.29:** Wechsel von Feuer zu Einbruch während der Tonwartezeit
nachgestellt und erneute Prioritätsprüfung vor TTS ergänzt. Getrennte Geräte sowie
Schutz neuerer Playback-Leases durch Regressionstests geprüft. Weitere parallele
Rückmeldungen und reale Audio-/Transportzeiten bleiben offen.

- [ ] Feuer → Einbruch und Einbruch → Feuer auf gemeinsamem sowie getrennten Geräten testen.
- [ ] Prioritätswechsel während TTS und während einer noch laufenden Tonwartezeit prüfen.
- [ ] Rückmeldung gleichzeitig mit neuem Melder, weiterer Rückmeldung oder Geräteänderung testen.
- [ ] Ausgabevarianten auch für zusätzliche Status-/Abschlussmeldungen kombinieren:
  Push aus + Ton ein, nur Popup, nur Sprache, deaktiviertes Gerät und deaktiviertes Konto.
- [ ] Sicherstellen, dass ein alter Hintergrundauftrag keinen neueren Auftrag stoppt
  oder dessen Wiederherstellungsdaten entfernt.

**Fertig, wenn:** Einbruch-Vorrang eingehalten wird, andere Empfänger weiter versorgt
werden und die gewollte ereignisbezogene Rückmeldung erhalten bleibt.

### B3 [P0, M] Fehler beim Stoppen und Speichern behandeln

**Teilfortschritt 0.3.28:** Einzelner Listener-Abmeldefehler verhindert übriges
Aufräumen/Gerätewiederherstellung nicht mehr; nach Stopbeginn eintreffende Ereignisse
werden abgefangen. In 0.3.29 wurden zusätzlich einzelne Fehler beim Aufräumen nach
Startfehler abgefangen, ohne den ursprünglichen Startfehler zu verdecken. Weitere
Speicher-/Abbruchgrenzen bleiben offen.

- [ ] Fehler einzelner Abmeldefunktionen, Speicherung und Transport an definierten Punkten injizieren.
- [ ] Prüfen, ob weitere Aufräumschritte auch nach dem ersten Fehler durchgeführt werden.
- [ ] Reguläres Entladen bei ausstehender Wiederherstellung prüfen.
- [ ] Wiederholungsabstände und Zahl gleichzeitig laufender Wiederherstellungsaufgaben prüfen.
- [ ] Entfernen von Gerät/Konto bei laufender Einrichtung, Alarm oder vorhandenen
  Wiederherstellungsdaten prüfen. Die vorhandene `ensure_device_idle`-Sperre muss
  bestehen bleiben; keine nicht mehr zuordenbaren Wiederherstellungsaufträge erzeugen.

**Fertig, wenn:** Fehler nachvollziehbar bleiben, ursprüngliche Daten erhalten werden
und erneute Versuche ohne parallele unkontrollierte Aufgaben möglich sind.

### B4 [P0, M] Ausfall eines Handys isolieren

- [ ] Nicht erreichbares, langsam reagierendes oder fehlerhaft zugeordnetes Gerät simulieren.
- [ ] Prüfen, ob die gemeinsame Transportsteuerung andere Geräte unzulässig lange blockiert.
- [ ] Zeitgrenzen nur mit begründeten Werten und passender Fehlerbehandlung einführen.

**Fertig, wenn:** ein defektes Gerät gesunde Empfänger nicht dauerhaft blockiert.
Konkrete Zeitgrenzen erst anhand der Schnittstelle und gemessenen Abläufe festlegen.

### B5 [P0/P1, M] Sensorzustände und Melderflattern prüfen

- [ ] `off`, `on`, `unknown`, `unavailable`, entfernte Entität und Wiederkehr systematisch testen.
- [ ] Sehr häufige Wechsel und wiederholte gleiche Meldungen testen.
- [ ] Alarmunterdrückung nach Beenden und Entsperrung durch Normalzustand nachvollziehen.

**Fertig, wenn:** keine unbeabsichtigte automatische Alarmbeendigung entsteht und
jedes definierte Zustandsmuster nachvollziehbar dokumentiert ist. Neue Regeln für
Auslösung beim Wiederverbinden nicht stillschweigend ändern.

### B6 [P1, S/M] Rückmeldungen und Bestätigungstoken begrenzen

**Teilfortschritt 0.5.1, nur lokal:** Fremd zugeordnete Abbruch-/Bestätigungsversuche
verbrauchen gültige Kennungen nicht mehr. Abgelaufene offene und abgeschlossene
Kennungen werden bei Rückmeldungen und im Tick bereinigt; Ablaufgrenzen und
wiederholte gültige Bestätigungen mit acht Regressionstests geprüft. Veraltete
andere Benachrichtigungsaktionen bleiben ein gesonderter Prüfauftrag.

- [ ] Abgelaufene Fehlalarm-Bestätigung, erneuten Versuch und doppelte Aktionen testen.
- [ ] Wiederholte abgelaufene Anfragen auf anwachsende Tokenbestände prüfen.
- [ ] Veraltete Benachrichtigungsaktionen für bereits beendete Ereignisse abweisen oder
  als bereits erledigt beantworten, ohne neue Nebenwirkungen.

**Fertig, wenn:** identische Wiederholungen keine doppelten Zustandswechsel auslösen
und kurzlebige Bestätigungen nicht unbegrenzt im Speicher verbleiben.

## C – Daten, Rechte und Diagnose

### C1 [P0, M] Gemeinsame Rechte-Matrix testen

- [ ] Admin, normaler Empfänger, falsche Alarmart, deaktiviertes/entferntes/unbekanntes Konto prüfen.
- [ ] Panel, WebSockets, HA-Aktionen, Bild-API und allgemeine HA-Entität gegenüberstellen.
- [ ] Prüfen, ob bereits offene Browseransichten nach Rechteänderung Daten weiter behalten.

**Fertig, wenn:** erlaubte und verweigerte Zugriffe überall denselben fachlichen Regeln
folgen. Ein generischer Alarmzähler darf nicht wieder versehentlich Detaildaten erhalten.

### C2 [P1, M, Funktionsvorschlag] Datenschutz am Sperrbildschirm

Der Code verwendet aktuell für Android-Alarme `visibility="public"`. Das ist eine
konkrete Implementierungsentscheidung, kein Nachweis über die tatsächliche Darstellung
jedes Handys.

- [ ] Als Option „Details auf Sperrbildschirm verbergen“ entwerfen.
- [ ] Titel, Standort, Bereich, Kamera-/Bildanhang und Rückmeldeaktion einzeln bewerten.
- [ ] Sicherstellen, dass geschützte Details nicht durch eine zweite Statusmeldung wieder erscheinen.

**Fertig, wenn:** die gewählte Einstellung auf einem gesperrten Zielgerät geprüft ist.
Eine Änderung des bestehenden Standardverhaltens ausdrücklich festlegen.

### C3 [P0/P1, M] Import und Datensicherung weiter absichern

**Teilfortschritt 0.5.2, nur lokal:** Aktivierungs- und Stummschalter akzeptieren
beim Import nur echte JSON-Booleans. Zuvor aktivierte z. B. der Text "false"
Benutzer/Melder oder machte sie stumm. Sechs Regressionstests prüfen beide
Schemas, mehrdeutige Werte, atomare Ablehnung und unveränderte Legacy-Vorgaben.
Weitere verschachtelte Importtypen bleiben ein gesonderter Prüfauftrag.

- [ ] Verschachtelte Datentypen, Zahlen, doppelte IDs und fremde/alte Gerätesitzungen testen.
- [ ] Änderungen zunächst vollständig prüfen und erst danach den Zustand austauschen.
- [ ] Nicht unterstützte Sicherungsversionen verständlich abweisen.
- [ ] Bei künftigen Datenformatänderungen Vorwärts-/Rückwärtsgrenzen dokumentieren.

**Fertig, wenn:** ungültiger Import bestehende Einrichtung und Wiederherstellungsdaten
nicht verändert. Konfigurationsexport ausdrücklich von vollständiger HA-Sicherung unterscheiden.

### C4 [P1, M, Funktionsvorschlag] Bereinigte Diagnose anbieten

- [ ] Versionsnummern, Einrichtungsvollständigkeit, letzte Anforderung, Empfangsbestätigung,
  tatsächliche Ansicht und Wiederherstellungsstatus getrennt anzeigen.
- [ ] Export vorab auf Namen, Standort, Geräte-/Benutzerkennungen, URLs und Tokens prüfen.
- [ ] Nur nach bewusster Auslösung durch den Benutzer exportieren; keine Hintergrundübertragung.

**Fertig, wenn:** ein Fehlerbericht ohne kompletten privaten HA-Datenbestand möglich ist.
„Angefordert“ darf nicht als „angekommen“ oder „abgespielt“ umbenannt werden.

### C5 [P1/P2, M] Verlauf und Bilder begrenzen

- [ ] Tatsächliche Aufbewahrung für Journal, Ereignisse, Bilder und Sicherungen gegenüberstellen.
- [ ] Bildablauf vor und nach Neustart sowie Bereinigung ohne neue Bilder testen.
- [ ] Gleichzeitiges Erzeugen, Lesen und Bereinigen sowie fehlende/kaputte Metadaten testen.
- [ ] Rechteänderungen während eines Bildabrufs und die genaue Ablaufgrenze prüfen.
- [ ] Gegenlast durch viele Bilder/Verlaufseinträge messen, bevor neue Limits eingeführt werden.

**Fertig, wenn:** Aufbewahrungsangaben der realen Speicherwirkung entsprechen.
Bestehende unbefristete Aufbewahrung nicht ungefragt durch Löschung ersetzen.

## D – Geräteübersicht und Einrichtung

### D1 [P1, M, Funktionsvorschlag] Kompakte Geräteübersicht

- [ ] Je Gerät Kontozuordnung, Aktivierung und Push/Ton/Sprache/Popup sichtbar machen.
- [ ] „Absichtlich ausgeschaltet“ von „Einrichtung fehlt“ unterscheiden.
- [ ] Ausstehende Wiederherstellung und letzte erfolgreiche Geräteprüfung anzeigen.

**Fertig, wenn:** die tatsächlichen Einstellungen ohne Öffnen jedes Assistenten erkennbar
sind. Nicht erreichbare Geräte ohne Nachweis weder pauschal rot noch grün markieren.

### D2 [P1, M, Funktionsvorschlag] Einzelne Ausgaben gezielt testen

- [ ] Push, Ton, Sprache und Alarmfenster separat auslösen können.
- [ ] Vor hörbaren Tests klar ankündigen, auf welchem Gerät sie stattfinden.
- [ ] Eindeutigen Teststatus und Stop-Knopf anbieten; reale Alarme haben Vorrang.
- [ ] Einzeltest nicht automatisch als vollständige Feuer-/Einbruchgeräteprüfung zählen.

**Fertig, wenn:** ein Fehler gezielt eingegrenzt werden kann, ohne unbeabsichtigt die
vollständige Gerätefreigabe zu umgehen. Nutzt zuerst die abgesicherte Auftragssteuerung aus B.

### D3 [P1, M, Funktionsvorschlag] Verständlicher Bereitschaftsstatus

- [ ] Zustände wie „Einrichtung offen“, „Test bestätigt“, „Sensorwerte fehlen“ und
  „Wiederherstellung ausstehend“ mit konkretem nächsten Schritt versehen.
- [ ] Alter von Sensorwerten/Bestätigungen berücksichtigen, soweit tatsächlich verfügbar.
- [ ] „Nicht nachgewiesen“ als eigenen Zustand zulassen.

**Fertig, wenn:** ein Test von gestern nicht als garantierte Erreichbarkeit heute erscheint.

### D4 [P1/P2, M] Assistent und gespeicherte Einstellungen prüfen

- [ ] Mobilgeräteauswahl, Kontoänderung, Plattformwechsel und verlorene Browserzuordnung testen.
- [ ] Texteingaben und Fokus bei Hintergrundaktualisierungen erhalten.
- [ ] Änderungen vor dem Speichern zusammenfassen; notwendige Wiederholungstests erklären.

**Fertig, wenn:** UI und gespeicherte Einstellungen übereinstimmen und Einstellungen
nicht durch Aktualisieren, Zurück oder Abbrechen unbemerkt verändert werden.

## E – Alarmansicht, Aussehen und Bedienung

### E1 [P1, M, Funktionsvorschlag] Gleichzeitige Alarme deutlich sichtbar machen

- [ ] Hauptalarm mit unmissverständlicher Alarmart, Bereich und Beginn darstellen.
- [ ] Weitere aktive Alarme dauerhaft sichtbar halten, auch bei priorisiertem Einbruch.
- [ ] Jede Aktion eindeutig mit ihrem Ereignis verbinden.

**Fertig, wenn:** bei Einbruch + Feuer niemand annehmen muss, dass eine Rückmeldung
beide erledigt. Farbliche Hervorhebung allein reicht als Kennzeichnung nicht.

### E2 [P1, M, Funktionsvorschlag] Rückmeldung unter Stress vereinfachen

- [ ] Große, voneinander getrennte Schaltflächen für „Ich komme“, „Fehlalarm“ und Beenden.
- [ ] Laufende Aktion sichtbar machen; doppelte Bedienung und veraltete Daten berücksichtigen.
- [ ] Fehlalarm-Bestätigung verständlich, aber weiterhin bewusst zweistufig halten.
- [ ] Netzverlust während eines Klicks klar von erfolgreicher Rückmeldung unterscheiden.

**Fertig, wenn:** der sichtbare Erfolg erst nach bestätigter Zustandsänderung erscheint
und ein wiederholter Klick kein zweites Ereignis auslöst.

### E3 [P1/P2, M] Lesbarkeit und Zugänglichkeit prüfen

- [ ] Kleine Displays, Querformat, vergrößerte Schrift und Hell-/Dunkeldarstellung prüfen.
- [ ] Zustände mit Text und Symbol zusätzlich zu Farbe darstellen.
- [ ] Tastatur, Fokus, Screenreader-Beschriftungen und Kameradialog prüfen.

**Fertig, wenn:** die wichtigsten Aktionen ohne horizontales Suchen erreichbar bleiben
und Benachrichtigungen keine Eingaben oder Fokuspositionen unerwartet verdrängen.
Kein visuelles „bestanden“ ohne echte Browserprüfung.

### E4 [P2, M, Funktionsvorschlag] Verlauf gezielt nutzbar machen

- [ ] Filter nach Alarmart, Zeitraum, Melder und Status entwerfen.
- [ ] Ereignisaktionen von reinen Transportmeldungen verständlich unterscheiden.
- [ ] Filter für Anzeige und CSV nachvollziehbar aufeinander abstimmen.
- [ ] Unabhängig von neuen Filtern den bestehenden CSV-Export mit Formelanfängen,
  Anführungszeichen, Zeilenumbrüchen und Umlauten prüfen; aktive Ereignisse müssen
  bei Aufbewahrungsbereinigung erhalten bleiben.

**Fertig, wenn:** Nutzer ein konkretes Ereignis wiederfinden und aus „angefordert“
keinen Zustellnachweis ableiten müssen. Abhängigkeit zu G3 für große Datenbestände.

## F – Android-Ausgabe und Zustellung

### F1 [P0, L] Vollständige Ausgabematrix auf Zielgerät prüfen

- [ ] Alle Kombinationen von Sprache/Ton prüfen, dazu Push und Popup ein/aus.
- [ ] DND, Stumm/Vibration, gesperrtes Display, App im Hintergrund und fehlende Berechtigungen prüfen.
- [ ] Bereits bestehende Android-Kanaleinstellungen mit neuer Installation vergleichen.
- [ ] Unbekannte oder veraltete Sensorwerte und reale Offline-/Wiederkehrfälle prüfen.

**Fertig, wenn:** jede zugesicherte Schalterwirkung mit einer Gerätekonfiguration
nachgewiesen ist. Besonderheiten werden dokumentiert, nicht mit pauschalen Garantien überdeckt.

### F2 [P1, M/L] Lange Sprachansagen und Stop-Verhalten prüfen

- [ ] Lange Standort-/Bereichsnamen, mehrere Melder und wiederholte Ansagen testen.
- [ ] Prüfen, ob die konfigurierte Wartezeit zu Überlappung oder abgeschnittener Sprache führt.
- [ ] Fehlgeschlagenen Sprachstop und Neustart mit reinem Sprachauftrag testen.

**Fertig, wenn:** die Bedeutung der Sprachzeit eindeutig ist und kein bloßer Timer
als Beweis für abgeschlossene Wiedergabe behandelt wird.

### F3 [P2, M, Funktionsvorschlag] Ansagetext mit Vorschau

- [ ] Begrenzte Platzhalter für Alarmart, Standort und Bereich erlauben.
- [ ] Lesbare Textvorschau vor einer hörbaren Testansage anbieten.
- [ ] Leere, überlange oder unerwartete Inhalte begrenzen und Standardtext beibehalten.

**Fertig, wenn:** Texte ohne kaputte Platzhalter verständlich bleiben. Erst nach F2
umsetzen, damit individuell längere Texte kein ungeprüftes Wiederholungsproblem schaffen.

### F4 [P1/P2, M] Benachrichtigungsaktionen und veraltete Nachrichten prüfen

- [ ] Direktlinks, bereits beendete Ereignisse, Neustart und Kontowechsel testen.
- [ ] Bildabruf samt Anmeldung, Ablauf und falscher Alarmberechtigung prüfen.
- [ ] Ablaufzeiten verspäteter Nachrichten festlegen, ohne einen lokalen Versandauftrag
  fälschlich als bestätigte Zustellung zu behandeln.

**Fertig, wenn:** ein alter Hinweis keine falsche neue Alarmaktion auslöst und ein
ungeladenes Bild nicht durch einen öffentlichen Ersatzpfad umgangen wird.

## G – Programmierung, Messung und Versionspflege

### G1 [P1, M] Tests über kritische Grenzen erweitern

- [ ] Fake-Adapter, tatsächliche HA-Tests, Browserlogik und reale Geräte getrennt ausweisen.
- [ ] Jede gefundene Regression zuerst reproduzieren, dann gezielt korrigieren.
- [ ] Export-/Verlaufsmethoden in die bestehenden Node.js-Tests aufnehmen.

**Fertig, wenn:** die Tests fachlich beobachtbares Verhalten absichern und nicht nur
interne Funktionsnamen oder Implementierungsdetails nachbauen.

### G2 [P2, M] Oberfläche und Engine schrittweise aufteilen

- [ ] Zuerst lesbar formatieren und Verhaltenstests vervollständigen.
- [ ] Danach Geräteassistent, Alarmansicht, Export und Kamera getrennt betrachten.
- [ ] Engine-Verantwortlichkeiten für Zustellung, Wiederherstellung und Zustand trennen,
  ohne in einem Schritt die ganze Anwendung neu zu schreiben.

**Fertig, wenn:** Verhalten, Paketinhalt und statisches Laden weiter geprüft sind.
Keine neue Buildkette nur aus Gewohnheit einführen.

### G3 [P1/P2, M] Langzeitlast messen

- [ ] Datenbestände z. B. mit 100, 1.000 und 10.000 Ereignissen als Testgrößen erzeugen.
- [ ] Speicherzeit, Antwortgröße, Frontend-Aktualisierung und wachsende Logs messen.
- [ ] Meldersturm mit vielen gleichzeitigen Empfängern zusätzlich betrachten.
- [ ] Erst danach entscheiden, ob Pagination, begrenzte Antworten oder gebündelte Speicherung nötig sind.

**Fertig, wenn:** Messbedingungen und Werte reproduzierbar vorliegen. Keine festen
Leistungsversprechen ohne Zielhardwaremessung; keine historischen Daten ungefragt löschen.

### G4 [P1/P2, M] Neue Version vollständig nachvollziehbar machen

- [ ] Neue Funktion und Korrektur klein committen; passende Versionsangaben gemeinsam ändern.
- [ ] Änderungsnotizen, Paket-Prüfsumme und Teststand zum neuen Tag dokumentieren.
- [ ] Neue Paketversion erstellen, vorhandene ZIPs und Tags nicht überschreiben.
- [ ] Spätere Veröffentlichung gesondert behandeln: Repo-Sichtbarkeit, Lizenzhinweis,
  konkrete Projektlinks und unterstützte Versionen prüfen.

**Fertig, wenn:** jede ausgelieferte Datei zu einem festen Quellstand gehört und eine
verständliche Rückkehranleitung existiert. Ein Tag ist keine automatisch getestete HA-Freigabe.

## H – Über den bisherigen Funktionsumfang hinaus

### H1 [P2, M/L, Vorschlag] Empfangs- und Reaktionsübersicht

Getrennt zeigen: Versand angefordert, Empfang bestätigt, Ansicht sichtbar, Person
kommt. Keine Spalte „Ton sicher gehört“, solange es dafür keinen verlässlichen Nachweis gibt.

**Prüfkriterium:** Zustände beruhen jeweils auf dem dazugehörigen Signal und bleiben
bei offline befindlichen Geräten als unbekannt erkennbar.

### H2 [P2/P3, L, Entscheidung] Eskalation ohne Rückmeldung

Möglicher Ablauf: Nach konfigurierbarer Zeit an weitere festgelegte Empfänger melden.
Vorher klären: welche Alarmarten, welche Zeit, wer darf stoppen, maximale Wiederholungen
und Verhalten nach Neustart. Keine automatische Änderung der bestehenden Empfängerregeln.

**Prüfkriterium:** Eskalation ist begrenzt, protokolliert und beeinflusst keine fremden
Ereignisse. Erst nach B, F und einer ausdrücklichen Produktentscheidung umsetzen.

### H3 [P2/P3, M/L, Entscheidung] Zeitweises Abschalten mit Ablauf

Optionaler Wartungsmodus für einzelne Geräte/Melder, mit Grund und sichtbarem Endzeitpunkt.
Kein stilles globales Abschalten aller Alarme; Neustart und Ablauf müssen definiert sein.

**Prüfkriterium:** eine Wartung kann nicht unbemerkt unbegrenzt fortbestehen.
Die genaue Wirkung auf Feuer/Einbruch nicht ohne Entscheidung festlegen.

### H4 [P3, L, Architekturentscheidung] Ausfall der ganzen HA-Instanz erkennen

Ein in HA laufendes System kann seinen eigenen vollständigen Ausfall nicht über
seinen ausgefallenen Versandweg melden. Falls das zum gewünschten Produkt gehört,
einen unabhängig laufenden Zustandsprüfer als gesondertes Vorhaben entwerfen.

**Prüfkriterium:** eigener Fehler-/Strom-/Netzpfad und klare Grenzen; kein neues Konto,
Cloudabo oder zusätzlicher Dienst automatisch einrichten. Die App bleibt ohne
entsprechende Nachweise keine zugesicherte unabhängige Alarmanlage.

### H5 [P2/P3, M/L, Vorschlag] Wiederkehrende Geräteprüfung

Optional an eine erneute bewusste Geräteprüfung erinnern, beispielsweise nach relevanter
Konfigurationsänderung oder längerer Zeit. Nie eine historische Prüfung als heutige
Erreichbarkeitsgarantie anzeigen und keinen lauten Test ohne bewusste Auslösung starten.

**Prüfkriterium:** Erinnerung und tatsächlicher Test sind klar getrennt; keine unnötigen
wiederholten Nachrichten oder automatisch abgespielten Alarmtöne.

## Bewusst nicht als Erstes umsetzen

- Kein Komplettneubau der Oberfläche vor der Absicherung der Alarmabläufe.
- Keine Cloud, Zusatz-App, automatische Anrufe/SMS oder Mehrstandortverwaltung als Nebenprodukt.
- Kein öffentlicher Bildpfad als Behelf für fehlende Companion-Unterstützung.
- Keine automatische Prioritätsänderung: Einbruch vor Feuer bleibt festgehalten.
- Keine behauptete Betriebsbereitschaft allein wegen hoher Testanzahl.
- Keine neuen Funktionen im Sechs-Stunden-Lauf allein deshalb, weil sie hier als Idee stehen.

## Konkrete Reihenfolge der nächsten Arbeitspakete

1. **B1 + B3:** Neustart, Abbruch, Fehler im Aufräumen und Speicherung prüfen.
2. **B2 + B4:** Parallelität, Prioritätswechsel und langsames/ausgefallenes Gerät prüfen.
3. **B6 + C3:** abgelaufene Aktionen und robuste Imports prüfen.
4. **A2 + A3 + A4:** Rückkehrprobe vervollständigen und echte Testumgebung vorbereiten.
   Lokale Schritte parallel zu 1–3; externe Schritte erst mit verfügbarer Umgebung.
5. **F1 + F2:** Android-Ausgabematrix und lange/abgebrochene Ansagen praktisch prüfen.
6. **D1 + D2 + E1:** als erste vorgeschlagene Produktverbesserung kompakte Geräteübersicht,
   gezielte Einzeltests und deutlichere parallele Alarme spezifizieren.
7. **G3, dann G2:** messen, anschließend gezielt vereinfachen.
8. Weitere Ideen aus H nach nachgewiesenem Nutzen und festgelegten Regeln auswählen.

Keine starre Zusage „0.3.28 enthält alles“. Der nächste Versionsumfang ergibt sich aus
einem kleinen abgeschlossenen Paket; weitere Pakete folgen mit eigenen Rücksprungpunkten.

## Arbeitsweise mit Subagenten und automatischer Fortsetzung

- Hauptagent bestimmt Ziel und Dateigrenzen, prüft fachliche Regeln und integriert.
- Kleinerer Subagent: isolierter Testfall, Hilfswerkzeug, beschränkte UI-Logik oder
  gezielte technische Gegenprüfung; keine selbstständigen Branchwechsel/Commits.
- Unabhängige Aufgaben dürfen parallel laufen, dieselben Dateien nicht.
- Ergebnis zusammen prüfen: Tests, Dokumentation, Git-Diff und tatsächlich behobenes Verhalten.
- Jeder automatische Lauf liest zunächst `WORK_PLAN.md`, diesen Plan und den aktuellen Git-Stand.
- Bei unveränderter, nicht bearbeitbarer externer Voraussetzung keinen künstlichen
  Fortschritt durch wiederholte Dokumentänderungen erzeugen.

## Fertig-Kriterium pro Änderung

1. Auslöser und gewünschtes Verhalten sind klar.
2. Bei Fehlern ist das alte Fehlverhalten reproduziert.
3. Kleine Änderung mit passender Prüfung; relevante bisherige Tests bestehen.
4. Rechte, parallele Ereignisse, Abbruch und gespeicherte Daten wurden mitbedacht.
5. Bedienung, Versionshinweis und gegebenenfalls Rückkehrgrenze sind dokumentiert.
6. Lokaler Commit mit verständlicher Beschreibung; keine fremden Änderungen enthalten.
7. Hardware-/HA-Prüfungen werden ehrlich als bestanden, fehlgeschlagen oder offen geführt.

## Punkte für spätere Nutzerentscheidungen

Jetzt muss nichts davon sofort beantwortet werden. Für die jeweiligen Pakete werden
gezielt benötigt: konkretes Android-Modell und Versionsstände (A3), gewünschte
Sperrbildschirmdetails (C2), Verhalten bei manueller Lautstärkeänderung während eines
Alarms (B/F), gewünschter Ansagetext (F3), Eskalationsempfänger/-zeiten (H2) und Umfang
eines Wartungsmodus (H3). Bereits beantwortet: Android, 0.3.25 lief schon,
Einbruch hat auf demselben Gerät Vorrang vor Feuer.

## Zweite technische Gegenprüfung

Der Hauptagent und ein Subagent haben die Planung auf fehlende Randfälle geprüft.
Zusätzlich berücksichtigt sind Entfernen bei vorhandenen Wiederherstellungsaufträgen,
Ausgabeschalter in Status-/Abschlussmeldungen, CSV-Sonderfälle, Bilddateirennen und
unabhängige Wiederherstellungsproben. Eine anfängliche Vermutung zur Geräteentfernung
wurde anhand der vorhandenen `ensure_device_idle`-Sperre nicht als bestätigter Fehler
übernommen; daraus bleibt ein sinnvoller Regressionstest. Die bestehende Aufnahme
von `retention_mode` in Konfigurationssicherungen bleibt erhalten.

Es wurde in diesem Planungsdurchgang kein neuer App-Fehler als praktisch reproduziert
behauptet und keine Funktion geändert. Jeder spätere Fehlerfix braucht die im Plan
beschriebene gezielte Reproduktion und Prüfung.
