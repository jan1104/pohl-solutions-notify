# Ausgaben testen und Empfänger prüfen – ab 0.5.0

## Wer bekommt was?

Bei der Melderzuordnung zeigt die Übersicht die gewählte Alarmart, Melder und Bereich, zugeordnete Benutzer und deren Geräte. Unter **Alarmarten → Wer bekommt was?** steht dieselbe Übersicht für die gespeicherte Art.

Eine Ausgabe ist nur geplant, wenn sie sowohl an der Alarmart als auch am Gerät eingeschaltet und auf dessen Plattform eingerichtet ist. Sprache ist Android vorbehalten; Fenster brauchen eine Browser-Zuordnung. Stumme Informationen/Warnungen verwenden weder Ton noch Sprache. Deaktivierte Zuordnungen und offene Geräteprüfungen werden kenntlich gemacht. Die Vorschau bestätigt keine aktuelle Erreichbarkeit, Zustellung oder Wiedergabe. Laufende Alarme und Wiederherstellungen können die Ausgabe zusätzlich einschränken.

Die Ansagevorschau nutzt den konkreten Meldertext und Bereich, soweit vorhanden. Bei zusammengefassten Alarmen können später weitere Bereiche hinzukommen.

## Einzelne Ausgabe prüfen

Ab 0.5.7 geht es auch direkt unter **Melder & Alarme → Testen** in der gewünschten Zeile. Der Melder mit seinem Bereich und Text ist dann schon gewählt. Anschließend Gerät und einzelne Ausgabe wählen. Dies ist dieselbe Ausgabenprobe, kein Umschalten des Binary-Sensors und kein vollständiger quittierungspflichtiger Alarm.

1. Als Administrator **Alarmarten → Ausgaben testen** öffnen.
2. Ein zugeordnetes aktives Gerät wählen. Ein noch nicht vollständig freigegebenes Gerät kann geprüft werden; die Probe erteilt keine Gerätefreigabe.
3. Optional einen echten Melder derselben Art auswählen. Die Probe nutzt dessen Text und Bereich ohne Sensoränderung. Ohne Auswahl werden ausdrücklich Beispieldaten verwendet.
4. **Push**, **Ton**, **Sprache** oder **Fenster testen** drücken. Jede Schaltfläche fordert genau eine Ausgabe an. Nicht erlaubte Ausgaben bleiben gesperrt.
5. Das Ergebnis am Gerät prüfen und gegebenenfalls **Test stoppen** wählen. Eigene Tests werden beim Schließen zur Beendigung angefordert. Ein in einem anderen Tab gestarteter, wiedergefundener Test wird nur durch ausdrücklichen Stopp beendet.

Proben sind als **TEST** markiert; Sprache beginnt mit „Test.“. Push ist stumm. Die Tonprobe verwendet den normalen Benachrichtigungston ohne erzwungene Lautstärkeänderung; Sprache verwendet die normale Android-Medienlautstärke. Das prüft keine maximale Alarm-Lautstärke und ersetzt keinen vollständigen Geräte-/Alarmtest.

## Vorrang und Grenzen

Während aktiver Alarme, Einrichtung oder Wiederherstellung sind neue Einzeltests gesperrt. Pro Gerät ist nur eine Probe offen. Normale Informationsansagen übernehmen das Gerät während einer Probe nicht. Echte Alarme behalten Vorrang; eine Testbereinigung darf deren Audio oder Fenster nicht stoppen.

Der lokale Testtransport wartet insgesamt höchstens fünf Sekunden auf seine Ausgaben und prüft währenddessen auf einen neuen Alarm. Bei Alarmstart oder Zeitüberschreitung wird das lokale Warten abgebrochen und die Transportsteuerung freigegeben. Ein nicht bestätigter Abbruch bleibt zur Bereinigung gespeichert; weitere Tests auf diesem Gerät bleiben gesperrt, solange der alte Vorgang noch läuft. Bereits extern angenommene Befehle können dadurch nicht zurückgeholt werden. Eine allgemeine Lösung für Speicherausfälle ist damit nicht verbunden.

Nach ungefähr 30 Sekunden wird eine Bereinigung angefordert; das Testfenster hat zusätzlich ein Browser-Mod-Zeitlimit. Stoppen entfernt nur die markierte Testbenachrichtigung, fordert das Ende der Testansage an oder schließt das zugehörige Fenster. Das bestätigt nicht die Umsetzung am Endgerät und garantiert nicht die Länge einer schon gestarteten Tondatei.

Bei laufendem Alarm oder Wiederherstellung wird die Bereinigung zurückgestellt. Danach den offenen Test erneut stoppen. Transportfehler behalten ihre Testkennung für einen neuen Stoppversuch. Geräteänderungen, Import und vollständige Geräteprüfung erst nach Ende der Probe fortsetzen. Nach einem HA-Neustart sind die nur im Arbeitsspeicher gehaltenen Testkennungen nicht wiederherstellbar; echte Alarm-/Wiederherstellungsdaten sind davon getrennt.

Bereits ans Handy übergebene Sprache lässt sich beim späteren Alarmstart nicht durch lokale Vorabprüfungen garantiert abbrechen. Dieser Übergang, Stoppen, Tonkanal und Fensterwirkung müssen auf echtem Android/Browser Mod geprüft werden. Die lokalen Adaptertests ersetzen dies nicht.

Die vollständige Geräteprüfung für Feuer und Einbruch bleibt bestehen. Einzeltests erzeugen weder quittierungspflichtige Ereignisse noch erfolgreiche Basistest-Einträge.

Fenster verwenden eine eigene Markierung und gezieltes Schließen über `tag`, keine globale Schließaktion. Parameter und Zeitlimit wurden gegen das [offizielle Browser-Mod-Dienstschema](https://github.com/thomasloven/hass-browser_mod/blob/master/custom_components/browser_mod/services.yaml) geprüft; die echte Browser-Mod-Prüfung steht aus.
