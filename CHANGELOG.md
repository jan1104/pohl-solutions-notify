# Änderungen

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
