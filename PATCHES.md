# PATCHES

Dieser Fork basiert auf dem eingefrorenen Upstream-Release **v2026.7.1**
(NousResearch/hermes-agent).

## Kern-Änderungen gegenüber Upstream
- 2026-09-26 · `agent/agent_runtime_helpers.py` · Wiederverwendete Tool-IDs (z. B. `call_0`) pro Assistant-Turn auf eindeutige IDs abbilden und das passende Ergebnis erhalten. Verhindert, dass erfolgreiche MCP-/Terminal-Antworten vor dem Modellaufruf verschwinden. Persistierten Verlauf unverändert lassen; IDs im API-Payload deterministisch. · Upstream-relevant: ja.

Jede künftige Änderung am Hermes-Kern wird hier gelistet:
Datum · Datei · Grund · Upstream-relevant? (ja/nein)

## Upstream-Merge-Historie
- 2026-07-06 · Freeze auf v2026.7.1
