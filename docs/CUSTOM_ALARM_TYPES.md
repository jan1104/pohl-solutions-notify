# Eigene Alarmarten ab 0.4.0

Lokaler Entwicklungsstand, noch nicht auf echter HA-/Android-Installation geprüft.
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
| Sprachtext | Bis zu 240 Zeichen mit {name}, {site} und {areas}; leer verwendet den Standardtext |

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
3. **Sprachtext optional anpassen:** Beispiel: `Achtung, {name}. Bereich {areas}. Standort {site}.`
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
weiter ihre normale Nachrichtenfunktion. Ein unbekannter Typ wird kontrolliert abgewiesen.

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
