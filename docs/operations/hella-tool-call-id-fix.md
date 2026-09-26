# James: Tool-Ergebnisse trotz erfolgreichem MCP-Abruf unsichtbar

Stand: 26.09.2026. Betroffen: Hermes-Runtime, nicht YouTube-MCP.

## Ursache und Korrektur

Der Provider liefert für verschiedene Assistant-Turns wieder dieselbe ID
`call_0`. `sanitize_api_messages` entfernte alle späteren Calls und Ergebnisse
mit dieser ID. In der betroffenen Sitzung waren vor der Bereinigung 22
Tool-Ergebnisse (darunter vier Transkripte) vorhanden, danach nur sieben
(darunter kein Transkript). Mit dem Fix bleiben alle 22 Ergebnisse und alle
vier Transkripte erhalten.

Die API-Kopie bekommt deterministische, eindeutige IDs pro Aufruf samt
passendem Ergebnis. Echte doppelte Ergebnisse werden weiter entfernt. Der
persistierte Gesprächsverlauf wird nicht umgeschrieben. Neue Turns lassen die
bisherigen API-IDs stabil, auch wenn Provider-IDs mit erzeugten IDs kollidieren.

## Gezielter manueller Rollout

- Quelle ist der Hella-Fork auf Branch `hella`, Basis `3659ffab0`.
- Vor Veröffentlichung Regressionstests und bestehende Agent-Tests ausführen
  (`scripts/run_tests.sh`); keine Tests mit Produktionsschlüsseln.
- Bestehenden Workflow `hella-image.yml` manuell für den freigegebenen Commit
  aufrufen. Neues festes Image-Tag verwenden, das alte `hella-1.0` nicht ersetzen.
- James-Compose unter `/data/firmen/hella/compose/francisco/compose.yml` sichern.
  Nur dessen Image auf das neue Tag setzen und Service `hermes` neu erstellen.
- Agent-Daten/Verlauf erhalten; keine Änderung an Steffen oder Wilhelm.
- Nach Start den echten Modell-/Tool-Weg über eine isolierte API-Testsitzung
  prüfen: mindestens zwei aufeinanderfolgende Tool-Aufrufe, beide Ergebnisse
  in der abschließenden Antwort. Keine Telegram-Nachricht versenden.
- Fehlerfall: gesicherte Compose-Datei bzw. vorheriges Image wieder verwenden.

Zusätzlich wurde der Dateieigentümer von James' `cron/jobs.json` wieder auf
seinen Laufzeitnutzer korrigiert. Administrative Cron-Updates künftig als
Laufzeitnutzer ausführen; Lesbarkeit und Scheduler-Zugriff unter dieser UID
prüfen. Dies war ein separater Betriebsfehler, nicht die Ursache der verlorenen
MCP-Antworten.

## Prüfnachweis

Sechs Regressionstests plus 42 vorhandene Guardrail-/Session-Tests sowie Ruff
bestehen. Die neuen Regressionstests schlugen vor dem Fix fehl. Ein separater
Prozess mit den echten Runtime-Imports erhielt aus James' unveränderter Sitzung
nach dem Fix alle 22 Tool-Ergebnisse und vier Transkripte; IDs sind eindeutig
und Calls/Results vollständig gepaart.
Die breitere Datei `test_run_agent.py` ist lokal durch einen bereits im
unveränderten Basisstand reproduzierten Test-Isolationsfehler blockiert:
Logging greift beim Agent-Setup auf das echte `~/.hermes/logs/agent.log` zu,
was die Sandbox korrekt verweigert. Diese Testdatei wird nicht als bestanden
gewertet; der Fehler wird nicht durch Lockerung der Dateizugriffe umgangen.
