# Eigene Alarmarten ab 0.4.0

Ab 0.4.2: überarbeitete Sprachtexteingabe und zusätzliche Ausgaben für Informationen/Warnungen. Noch nicht auf echter HA-/Android-Installation geprüft.
Die vorhandenen Quell-Sicherungen 0.3.25 und 0.3.27 bleiben unverändert.

## Was sich einstellen lässt

Unter **Alarme → Alarmarten** können Administratoren bis zu 32 eigene Arten anlegen,
zum Beispiel **Hausalarm**, **Amokalarm**, **Wasseralarm** oder **Technikalarm**.
Es wird kein solcher Alarm automatisch ausgelöst und kein Empfänger automatisch hinzugefügt.

| Einstellung | Wirkung |
| --- | --- |
| Name | Anzeige im Panel, Versand, Verlauf und CSV |
| Empfänger | Je Benutzer wählbare Alarmarten; seine zugeordneten Geräte werden berücksichtigt |
| Priorität | Eigene Arten: ganze Zahl 1 bis 100, kleinere Zahl hat Vorrang auf demselben Gerät |
| Push | Normale/stumme Meldungen für diese Art aktivieren oder unterdrücken |
| Alarmton | Laute Alarmierung für diese Art aktivieren oder unterdrücken |
| Sprache | Android-Sprachansage unabhängig vom Alarmton aktivieren oder unterdrücken |
| Alarmfenster | Browser-Mod-Fenster für diese Art aktivieren oder unterdrücken |
| Tonphase | Eigene Arten: 1 bis 15 Sekunden für den Ablauf vor Sprach-/Wiederholungsphase |
| Sprachphase | Eigene Arten: 1 bis 12 Sekunden Wartezeit für die Sprachphase |
| Sprachtext | Optionaler eigener Satz, höchstens 240 Zeichen; deutsche Einfügeschaltflächen für Alarmname, Standort und Bereiche sowie Textvorschau |

Die vier bisherigen Arten bleiben erhalten: Information und Warnung sind normale
Meldungen; Feuer und Einbruch sind Ereignisse mit Rückmeldungen. Ihre Namen lassen
sich ändern. Ihre technischen IDs und Modi bleiben gleich. Einbruch behält Priorität
10 vor Feuer mit 20; diese vorhandenen Prioritäten werden nicht versehentlich verschoben.
Eine eigene Art startet mit 30. Wenn du einer eigenen Art ausdrücklich z. B. Priorität
5 gibst, bekommt sie auf gemeinsamen Geräten Vorrang auch vor Einbruch.

Bei Feuer/Einbruch bleiben die bestehenden Ton-/Sprachzeiten am Gerät eingestellt;
die eigenen Arten haben zusätzlich ihre eigenen Zeitwerte. Eine Tonphase begrenzt
nicht garantiert die tatsächliche Wiedergabelänge einer Tondatei. Empfang und
abgeschlossene Wiedergabe lassen sich aus den Wartezeiten nicht beweisen.

## Einrichtung Schritt für Schritt

1. **Alarmart hinzufügen:** Namen eingeben und gewünschte Ausgaben wählen.
2. **Vorrang festlegen:** Standard 30 lassen oder bewusst eine andere Priorität wählen.
3. **Sprachtext optional anpassen:** Einen normalen Satz schreiben, z. B. „Bitte zum Haupteingang kommen.“ Für veränderliche Angaben die beschrifteten Einfügeschaltflächen verwenden. Darunter zeigt eine Beispielvorschau den fertigen Text; sie spielt keinen Ton ab. Leer lassen verwendet die Standardansage.
4. **Empfänger zuordnen:** Unter **Benutzer → Bearbeiten → Meldungen wählen** die neue Art
   für jedes gewünschte vorhandene HA-Konto auswählen.
5. **Melder zuordnen:** Unter **Melder & Alarme** einen Binary-Sensor wählen und als
   Alarmart beispielsweise **Hausalarm** auswählen. Eine eindeutige Ereignisgruppe vergeben.
6. **Gerät prüfen:** Push/Ton/Sprache/Popup am jeweiligen Gerät kontrollieren. Der
   Assistent behält die Feuer-/Einbruch-Basisprüfung bei und bietet zusätzliche Tests
   der eigenen Alarmarten an. Neue Arten vor tatsächlichem Einsatz gezielt testen.
7. **Android-Ton wählen:** Nach Vorbereitung der Benachrichtigungskategorie den gewünschten
   Ton in Android für diese Kategorie einstellen. Das ist keine Audio-Dateiauswahl im Browser.

Die Alarmartenliste zeigt bereits zugeordnete aktive Benutzer an. Ein eigener Name
wird nicht als Empfängergruppe interpretiert: Die Kontozuordnung erfolgt ausdrücklich.

## Geräteschalter gelten zusätzlich

Ein Profil kann eine am Gerät ausgeschaltete Ausgabe nicht erzwingen. Beispiele:

- Hausalarm: Sprache ein, Ton aus; Gerät: Sprache ein → nur Sprache möglich.
- Hausalarm: Sprache ein; Gerät: Sprache aus → keine Sprachansage.
- Hausalarm: Popup ein; Gerät: Popup aus → kein Alarmfenster.
- Ton ein kann weiterhin eine technische Android-Benachrichtigung benötigen, auch
  wenn normale Push-Nachrichten aus sind. Sie bekommt beim Abschluss einen stummen Status.

Für nur Sprache/Push verlangt die Android-Vorbereitung keine Rufton-/Lautstärkesensoren,
wenn keine der zugeordneten Alarmarten einen Alarmton benötigt. Die bestehende
Benachrichtigungskonfiguration des Betriebssystems bleibt relevant.

## Namen, Kanäle und bestehende Verknüpfungen

Eine Alarmart hat eine feste ID. Umbenennen verändert diese ID und die Benutzer-/Melder-
Verknüpfungen nicht. Bei eigenen Arten wird die Android-Kategorie beim Anlegen aus
dem Namen gebildet und danach beibehalten. So gehen gewählte Android-Töne bei einer
Umbenennung nicht durch einen neuen Kanal verloren. Die tatsächliche Kategorie wird
im Editor angezeigt; sie kann deshalb nach einer Umbenennung den bisherigen Namen tragen.

Namen und Kategorien müssen eindeutig sein. Systemarten können nicht gelöscht werden.
Eine eigene Art kann nur gelöscht werden, solange sie weder Konten, Meldern, Ereignissen
noch Verlaufseinträgen zugeordnet ist. Vorhandener Verlauf bleibt damit verständlich.

Während aktiver Alarme, laufender Einrichtung oder ausstehender Wiederherstellung
werden Änderungen an Alarmarten gesperrt. Änderungen an bereits zugeordneten Arten
setzen betroffene Geräteprüfungen zurück; danach erneut prüfen und freigeben.

## Automationen und direkte Aktionen

In der Alarmartenliste steht unter **Für Automationen** die feste ID der Art.
Diese ID, nicht den frei bearbeitbaren Namen, als `type` angeben:

```yaml
- action: alarm_system.raise_alarm
  data:
    type: CUSTOM_0123456789AB  # Beispiel: durch die tatsächlich angelegte ID ersetzen
    alarm_key: house_alarm
    source_id: entrance
    source_name: Eingang
    area: Erdgeschoss
```

Eigene Arten erzeugen gespeicherte Ereignisse mit den bestehenden Rückmeldungen.
Eine Ereignisgruppe darf nicht verschiedene Alarmarten mischen. INFO/WARNING behalten
weiter ihre normale Nachrichtenfunktion mit optionalen einmaligen Ausgaben. Ein unbekannter Typ wird kontrolliert abgewiesen.

## Rechte und Gerätetests

Nur aktive HA-Administratoren verwalten die Arten. Normale Konten erhalten nur Profile
und Ereignisse ihrer zugewiesenen Arten. Während eines eigenen Gerätetests dürfen sie
auch den zu diesem Gerät gehörenden Basistest sehen und stoppen, selbst wenn Feuer/
Einbruch nicht zu ihren regulären Alarmarten gehören. Das gibt keine Rechte an echten
Feuer-/Einbruchereignissen oder an fremden Tests. Deaktivierte Konten bleiben gesperrt.

## Sicherung und Rückkehr

JSON-Konfigurationsexporte verwenden jetzt **Schema 2** und enthalten die Alarmarten.
Schema-1-Sicherungen werden weiter angenommen. Vorhandene Profile bleiben erhalten,
wenn ein unverändert beibehaltener Verlauf sie noch referenziert. Geräte werden nach
Import erneut geprüft. Ein ungültiger Import ändert den laufenden Stand nicht teilweise.

**Vor einem praktischen Update eine vollständige HA-Sicherung anlegen.** Ältere
Integrationsversionen verstehen eigene Alarmarten nicht. Zurücksetzen erfordert
gegebenenfalls die zur alten Version passende HA-Sicherung; nur die Python-Dateien
zurückzukopieren ist bei neu gespeicherten eigenen Alarmen keine sichere Datenmigration.
Keine internen Speicherdateien auf Verdacht löschen. Siehe auch [VERSIONS.md](VERSIONS.md).

## Noch praktisch zu prüfen

Echte HA-Konfigurationsschemas, Oberfläche im Browser, Android-Kategorien/Töne,
Sprachansagen, Browser-Mod-Popups, tatsächliche Benachrichtigungsaktionen und Import
auf der Testinstanz. Die lokalen Tests ersetzen diese Prüfungen nicht.

## Informationen und Warnungen ab 0.4.2

Auch beim Bearbeiten von **Information** und **Warnung** sind Push, Benachrichtigungston, Android-Sprache und Meldungsfenster sichtbar und unabhängig wählbar. Der Anzeigename ändert diese Möglichkeiten nicht. Bestehende Ausgaben bleiben bei einem Update unverändert; neue Schalter werden nicht automatisch eingeschaltet.

Ohne eigenen Sprachtext wird der konkrete **Benachrichtigungstext des Melders** einmal vorgelesen, z. B. „Das Garagentor ist noch offen.“ Ein eigener Satz in der Alarmart ersetzt diesen Text für ihre Ansagen. Dynamische Angaben lassen sich über deutsche Schaltflächen einfügen; intern bleiben vorhandene Vorlagen kompatibel. Die Vorschau enthält ausdrücklich Beispieldaten für Bereiche bzw. Nachrichtentext.

Diese Meldungen erzeugen keinen wiederholten, quittierungspflichtigen Alarm. Der Ton folgt den normalen Benachrichtigungseinstellungen; Sprache verwendet die normale Android-Medienlautstärke ohne erzwungene Änderung. Kein Ton-/Lautstärkesensor wird dafür zusätzlich verlangt. Bei **Stumm senden** entfallen Ton und Sprache. Bei laufenden Alarmen oder ausstehender Wiederherstellung auf dem Gerät entfallen zusätzliche Sprache, Ton und Fenster; ein erlaubter Push wird stumm angefordert. Meldungsfenster sind schließbar und setzen eine Browser-Mod-Zuordnung voraus.

Wie bei allen Alarmarten müssen die entsprechenden Ausgaben auch am Gerät aktiviert sein. Eine Änderung an einer zugeordneten Alarmart setzt dessen Geräteprüfung zurück; vor dem Einsatz erneut prüfen. Die Vorschau bestätigt keine tatsächliche Sprachausgabe oder Zustellung.

Bereits ans Handy übergebene Sprache lässt sich beim anschließenden Start eines Alarms nicht durch lokale Vorabprüfungen garantiert abbrechen; dieses Übergangsverhalten muss auf echtem Android geprüft werden.

## Standard-Sprachtext ab 0.4.3

Direkt unter dem Eingabefeld bleibt der **Standard-Sprachtext – wenn das Feld leer bleibt** immer sichtbar, auch wenn ein eigener Text eingetragen ist. Er übernimmt den aktuellen Alarmnamen und Standort. Bereiche sind als Beispieldaten erklärt. Bei Informationen ist der Beispieltext entsprechend gekennzeichnet; tatsächlich wird der Benachrichtigungstext des auslösenden Melders gesprochen. Die zusätzliche Vorschau darunter zeigt weiterhin die eigene Ansage.
