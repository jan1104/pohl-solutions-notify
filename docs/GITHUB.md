# GitHub-Vorbereitung

- Repository: https://github.com/jan1104/pohl-solutions-notify
- Lokaler Arbeitsordner: `D:\depot\pohl-solutions-notify`
- Remote `origin`: `https://github.com/jan1104/pohl-solutions-notify.git`
- Gesicherter Ausgangsbranch: `main`; Weiterentwicklung: `develop`
- Versionstags: `v0.3.25`, `v0.3.27` und neu lokal `v0.4.0`
- Commit-Autor: `jan1104 <152987784+jan1104@users.noreply.github.com>`
- Rechte: Pohl Solutions, alle Rechte vorbehalten; keine Open-Source-Freigabe.

Das Remote wurde eingerichtet und lesend geprüft. Bei der Einrichtung lieferte es
keine Branches oder Tags, war also leer. Bei der Ersteinrichtung wurde weder gepusht noch ein Release erstellt. Am 03.11.2026
wurden main, develop (damals 0.3.29) und die Tags 0.3.25/0.3.27 ausdrücklich vom
Benutzer zum Push freigegeben und erfolgreich übertragen. Der neue lokale Stand
0.4.0 wurde noch nicht gepusht; es wurde kein Release erstellt.
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

## HACS-Vorbereitung 0.4.1

HACS-Metadaten sind jetzt lokal ergänzt; Anleitung in [HACS.md](HACS.md). 0.4.1 einschließlich der eigenen Alarmarten ist noch nicht übertragen oder als Release veröffentlicht. Frühere Hinweise auf nicht eingerichtetes HACS beschreiben den Zustand vor diesem Fix.

## Veröffentlichung am 03.11.2026

Nach erneuter ausdrücklicher Benutzerfreigabe develop sowie die Tags v0.4.0/v0.4.1 gepusht und [Release v0.4.1](https://github.com/jan1104/pohl-solutions-notify/releases/tag/v0.4.1) veröffentlicht. HACS-Metadaten am Release-Tag remote geprüft. Repository ist öffentlich; Sichtbarkeit und Defaultbranch main wurden nicht geändert. Die API lieferte unmittelbar danach keine Workflow-Läufe für develop; deshalb keine erfolgreiche GitHub-CI behauptet. Lokale Prüfungen bestanden, echte HACS-/HA-/Android-Installation offen. Frühere Angaben zum rein lokalen Stand sind historisch.

## Update 0.4.2 am 03.11.2026

Mit fortgeltender Nutzerfreigabe develop und v0.4.2 gepusht, [Release v0.4.2](https://github.com/jan1104/pohl-solutions-notify/releases/tag/v0.4.2) veröffentlicht. Release und HACS-Datei remote geprüft; lokales Installations-ZIP gegen alle enthaltenen Git-Dateien geprüft. main und ältere Tags unverändert, kein HA-Deployment.

## Veröffentlichung 0.5.0 am 03.11.2026

Nach Nutzerauftrag und fortgeltender Push-Freigabe develop und v0.5.0 übertragen sowie GitHub-Release veröffentlicht. Release und HACS-Datei remote geprüft; ZIP-Inhalte byteweise gegen den Tag geprüft. Hauptbranch und frühere Tags unverändert. Kein HA-Deployment und keine native Geräteprüfung.
