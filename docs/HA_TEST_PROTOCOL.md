# Praktische Home-Assistant- und Geräteprüfung für 0.4.0

Status: noch nicht durchgeführt. Nicht als Produktionsfreigabe verwenden.
Eine getrennte Testinstanz mit Sicherung, Testkonten und kontrollierten Sensoren
verwenden. Kein automatisches Deployment auf ein bewohntes oder produktives System.

## Umgebung protokollieren

Datum, HA-Core-Version, Installationsart, Python-Version der HA-Umgebung,
Companion-Version und Betriebssystem pro Gerät sowie Browser-Mod-Version festhalten.
Nur bereinigte Protokolle speichern; keine Zugangsdaten oder personenbezogenen Exporte.

## Aufbau

1. Integration installieren, HA neu starten und einmalig konfigurieren.
2. Zwei Konten und Geräte einrichten: Konto A nur Feuer, Konto B nur Einbruch.
3. Ein weiteres Gerät mit beiden Alarmarten und eindeutig zugeordnetem Browser vorsehen.
4. Kategorien vorbereiten, Feuer-/Einbruchtests abschließen und Geräte bestätigen.
5. Zwei unabhängige Test-Binary-Sensoren bzw. manuelle Aktionen mit getrennten
   Ereignisgruppen bereitstellen.

## Parallele Alarme und Rückmeldungen

1. Einbruch auslösen, danach Feuer. Beide getrennten Geräte müssen ihren zugewiesenen
   Alarm erhalten. Das gemeinsame Gerät erhält den priorisierten Alarm und eine
   stumme Nachricht für das weitere Ereignis.
2. Bei Feuer „Ich komme“ drücken: Nur Feuer wird `claimed`; Einbruch bleibt offen.
3. Priorisierten Alarm bestätigen/beenden: Der nächste offene Alarm muss am gemeinsamen
   Gerät wieder verarbeitet werden. Auch umgekehrte Auslösereihenfolge prüfen.
4. Feuer mit Ton und Sprache auslösen; während der Tonwartezeit Einbruch an dasselbe
   Gerät auslösen. Die folgende Sprachstufe darf nicht mehr den nachrangigen Feueralarm ansagen.
   Mit Einbruch an einem anderen Gerät wiederholen: Feueransage bleibt dort unabhängig.
5. Alarm ohne passende Empfänger anlegen: Andere Empfänger dürfen nicht blockiert werden.
6. Fehlalarm bestätigen/abbrechen, Token ablaufen lassen und doppelte Klicks prüfen.

## Android-Wiederherstellung

1. Ursprünglichen Ruftonmodus und Lautstärke notieren. Alarm mit Ton/TTS auslösen.
2. Rückmeldung geben und aktuelle Companion-Sensorwerte beobachten. Originalwerte
   müssen zurückkehren; erst danach darf die Wiederherstellungsanzeige verschwinden.
3. Handy offline nehmen, Alarm beenden und später wieder verbinden. Gespeicherte
   Originalwerte müssen erhalten bleiben und erneut angefordert werden.
4. Verzögerte Sensorberichte simulieren: Alte gleiche Werte dürfen keine neue
   Bestätigung vortäuschen. Beide Werte müssen nach dem Anforderungszeitpunkt gemeldet sein.
5. Neuer Alarm bei ausstehender Wiederherstellung: Stumme Push-Nachricht weiter
   anfordern; keine unbekannten Originalwerte durch neue Werte überschreiben.
6. HA während Wiedergabe und während Wiederherstellung neu starten. Testereignisse
   werden abgebrochen; reguläre Ereignisse und Originalwerte bleiben nachvollziehbar.

## Zugriffsprüfung und Bilder

1. Normales Konto deaktivieren: Panel, WebSocket-Daten und Bild-API dürfen ihm keine
   Alarmdaten mehr geben. Aktiver Administrator behält Verwaltungszugriff.
2. `sensor.alarm_system_active` darf keine Alarmtitel, IDs oder Standortdetails enthalten.
3. INFO/WARNING mit numerischem Recorder-Verlauf senden. Bild muss auf Android/iOS
   geladen werden, ohne es öffentlich unter `/local/` abzulegen.
4. API-Bildpfad ohne Anmeldung, mit falscher Alarmart, deaktiviertem Konto und
   abgelaufenem Bild prüfen: kein Bildinhalt. Richtiger Empfänger erhält PNG.
5. Ablauf nach 24 Stunden und stündliche Bereinigung prüfen. Frühere generierte
   UUID-PNGs dürfen nach Start nicht mehr im alten öffentlichen Bildordner liegen.
6. Keine geschützten Bildpfade durch öffentliche Ersatzpfade umgehen, falls eine
   Companion-Version den authentifizierten Abruf nicht unterstützt; Ursache prüfen.

## Ausgabeoptionen ab 0.3.27

Auf Android die Kombinationen nur Sprache, nur Ton, beide ein sowie beide aus prüfen.
Nur Sprache ohne Rufton-/Benachrichtigungslautstärkesensoren vollständig einrichten.
Bei nur Sprache die unveränderten Rufton-/Benachrichtigungseinstellungen sowie Stop,
Abbruch, Offline-Wiederholung und HA-Neustart prüfen. Für INFO/WARNING Push aus testen.
Android-Kanal `Alarmstatus` mit vorhandenen persönlichen Einstellungen auf tatsächlich
stummes Verhalten prüfen. iPhone und Browser dürfen keinen Sprachschalter anzeigen.

## Eigene Alarmarten ab 0.4.0

Hausalarm und Amokalarm auf der Testinstanz anlegen, getrennte Konten zuordnen und
Binary-Sensoren verbinden. Je Profil Push/Ton/Sprache/Popup unabhängig prüfen;
Geräte-Aus darf vom Profil nicht überschrieben werden. Individuelle Kategorien,
Tonwahl und Sprachvorlagen am Android-Gerät testen. Prioritäten 30 und bewusst 5
gegen Einbruch 10/Feuer 20 auf gemeinsamen und getrennten Geräten prüfen.

Nur einem eigenen Typ zugeordnetes normales Konto muss seinen Basistest sehen/
stoppen können, aber keinen echten unzugewiesenen Feueralarm oder fremden Test.
Umbenennen muss ID und gewählten Android-Kanal erhalten. Schema-2-Export auf derselben
Testinstanz wieder importieren; anschließend Geräte neu prüfen. Alte Schema-1-Sicherung
weiter einlesen; vorhandene Historie mit eigenen Typen erhalten. Gebrauchte Arten
nicht löschen können. Rückkehr nur mit passender vollständiger HA-Sicherung proben.

## Abschluss

Laden/Entladen, erneutes Laden, normale INFO/WARNING, Kameras, Import/Export und
CSV-Verlauf prüfen. Ergebnis pro Schritt als bestanden, fehlgeschlagen oder nicht
getestet protokollieren. Erst nach tatsächlichen Ergebnissen unterstützte Versionsmatrix
und Freigabestatus aktualisieren.
