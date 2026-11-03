# GitHub-Vorbereitung

- Repository: https://github.com/jan1104/pohl-solutions-notify
- Lokaler Arbeitsordner: `D:\depot\pohl-solutions-notify`
- Remote `origin`: `https://github.com/jan1104/pohl-solutions-notify.git`
- Gesicherter Ausgangsbranch: `main`; Weiterentwicklung: `develop`
- Lokale Versionstags: `v0.3.25` und `v0.3.27`
- Commit-Autor: `jan1104 <152987784+jan1104@users.noreply.github.com>`
- Rechte: Pohl Solutions, alle Rechte vorbehalten; keine Open-Source-Freigabe.

Das Remote wurde eingerichtet und lesend geprüft. Bei der Einrichtung lieferte es
keine Branches oder Tags, war also leer. Es wurde weder gepusht noch ein Release erstellt.
Die Sichtbarkeit des Repositories wird damit nicht geprüft oder geändert.

## Vor der ersten Übertragung

- In GitHub die gewünschte Sichtbarkeit prüfen; für nicht freigegebenen Quellcode **Private** verwenden.
- Rechte am übernommenen Code und geplante Nutzungsrechte für Endnutzer klären.
- Einrichtung und Versand in einer realen HA-Installation testen und getestete Versionen dokumentieren.
- Bei späterer Veröffentlichung im Manifest die Dokumentationsadresse durch die eigene
  Projektadresse ersetzen; derzeit verweist sie noch auf allgemeine HA-Dokumentation.
- Bei Bedarf echte GitHub-Benutzernamen als Codeowners ergänzen; derzeit ist die Liste leer.
- Änderungen prüfen und lokale Tests ausführen.

Ein späterer erster Push würde mit `git push -u origin main` erfolgen.
Dieser Befehl ist hier nur dokumentiert und wurde nicht ausgeführt.

## GitHub-Unterlagen

Issue-Vorlagen erfassen Fehler und Funktionswünsche ohne private HA-Daten.
Die Pull-Request-Vorlage hält Änderungen und Prüfungen fest. Die Actions-Datei
prüft Syntax, Metadaten und Modellregeln. HACS, Paketverteilung, automatische Releases
und Deployments sind noch nicht eingerichtet.
