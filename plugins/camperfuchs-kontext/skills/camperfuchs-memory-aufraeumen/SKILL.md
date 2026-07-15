---
name: camperfuchs-memory-aufraeumen
description: Memory-Hygiene für Björns Claude-Accounts — verwaiste Memory-Dateien (Orphans) triagieren und indexieren, MEMORY.md unter dem 200-Zeilen-Limit halten (SUBINDEX-Muster), tote Dateien sync-fest per _archiv-Rezept wegräumen. IMMER nutzen, wenn am Memory aufgeräumt wird — explizit („Memory aufräumen", „Orphans prüfen", „Dateien nicht im Index", „MEMORY.md zu lang", „Index kompaktieren", „Memory-Datei löschen", „Dublette im Memory", „Memory-Konsolidierung") wie implizit („gelöschte Memory-Datei kommt immer wieder", „Claude findet altes Wissen nicht", „der Speicher-Flow vergisst den Index"). Kern-Fakten — cf-shared-memory-sync (Windows-Task, alle 6h) gleicht 3 Memory-Spaces + Shared-Claude-Memory ab, stellt Gelöschtes wieder her, sieht KEINE Unterordner (kein -Recurse), MEMORY.md wird NIE gesynct. Enthält Orphan-Triage-Rezept, das erprobte _archiv-Rezept (alle 4 Orte, Referenz-Check vorher) und die Fallen (Stub-Überschreiben verteilt sich, $-Stripping → .ps1, Index-Formate je Account verschieden).
---

# Camperfuchs Memory aufräumen — Orphan-Triage, Index-Pflege, sync-festes Archivieren

Erprobt 15.07.2026 (271 Dateien, 125 Orphans → alle triagiert, 35 tote archiviert, Index von 181 auf ~135 Zeilen kompaktiert).

## System-Landkarte (zuerst verstehen, sonst arbeitet man gegen den Sync)

- **4 Sync-Orte:** drei Memory-Spaces (Pfade stehen in `05_Skills-Automation\sync-shared-memory.ps1` im Projektordner) plus `Shared-Claude-Memory\` im Projekt-Root.
- **Windows-Task `cf-shared-memory-sync`** (08:00, dann alle 6h): Zwei-Wege-Abgleich aller Root-`*.md`, neuere gewinnt, **kein Löschen** — eine im Space gelöschte Datei wird beim nächsten Lauf aus Shared restauriert.
- Der Sync nutzt `Get-ChildItem` **OHNE `-Recurse`** → Unterordner (z. B. `_archiv\`) sind für ihn unsichtbar.
- **`MEMORY.md` wird NIE gesynct** (Absicht: jeder Account hat ein eigenes Index-Format — hier `project_`/`feedback_`-Sektionen, Account 3 flache kebab-case-Liste). Folge: Inhaltsdateien wandern automatisch zwischen Accounts, aber jede Index-Zeile muss im eigenen MEMORY.md selbst ergänzt werden. Dubletten zwischen Accounts sind normal.
- Ein Hook mahnt ab ~160 Zeilen: MEMORY.md muss **unter 200 Zeilen** bleiben (Read-Limit).

## Rezept 1 — Orphan-Triage (Dateien, die im Index fehlen)

1. Listing per PowerShell (Desktop Commander, der Sandbox-Bash erreicht die Space-Pfade nicht): `Get-ChildItem <memory> -File | Sort LastWriteTime -Descending | Format-Table LastWriteTime, Length, Name` — **ohne `$`-Variablen** (Einzeiler-Stripping-Falle) oder gleich als `.ps1`.
2. Gegen MEMORY.md + alle `index_*.md`-Subindizes abgleichen → Orphan-Liste.
3. Grob-Sortierung nach Datum/Namen: (a) datierte Session-Handoffs und Massenexport-Dumps = wahrscheinlich tot; (b) `project_`/`feedback_`/`reference_`-Dateien jüngeren Datums = wahrscheinlich verlorenes Wissen.
4. Kategorie (b) **reinlesen** (Batches parallel), je Datei: Index-Zeile schreiben, kaputte Frontmatter fixen (`name` leer, fehlende description), Auto-Task-Chroniken auf Substanz eindampfen. Rolling-Logs mit 5+ Zwischenständen: nur Endstand + Fallen behalten.
5. Kategorie (a) → Rezept 3 (_archiv), aber NUR nach Referenz-Check.

## Rezept 2 — Index unter 200 Zeilen halten (SUBINDEX-Muster)

- Gotchas und Arbeitsregeln bleiben direkt in MEMORY.md; Status-/Setup-/erledigte-Feature-Zeilen wandern in Themen-Subindizes (`index_produkt_features_live.md`, `index_legacy_backend.md`, `index_zugaenge.md`, `index_seo_setup.md`, `index_verfuegbarkeits_automation.md` …).
- In MEMORY.md bleibt pro Subindex EINE Zeile: `[🚢 SUBINDEX …](index_x.md) — Stichwort-Hooks`.
- Subindex-Dateien bekommen normale Frontmatter (`type: reference`) und dieselbe Zeilen-Form wie MEMORY.md.

## Rezept 3 — Tote Dateien sync-fest archivieren (_archiv)

**Löschen bringt nichts, Überschreiben ist gefährlich** (ein Stub bekommt den neuesten Zeitstempel und wird in ALLE Spaces verteilt = Inhalts-Totalverlust). Stattdessen:

1. **Referenz-Check:** nur archivieren, was keine lebende Root-Memory per `[[name]]` oder `(name.md)` referenziert (Select-String über alle Nicht-Kandidaten).
2. **Verschieben nach `_archiv\` in ALLEN 4 Sync-Orten** — fehlt ein Ort, restauriert der nächste Sync-Lauf von dort.
3. Als `.ps1`-Datei ausführen (`powershell -NoProfile -ExecutionPolicy Bypass -File …`), NIE als `-Command`-Einzeiler ($-Stripping). Muster: Namensliste + Schleife über die 4 Orte, `Move-Item` in den jeweiligen `_archiv\`-Unterordner.
4. Nichts ist gelöscht — alles bleibt wiederherstellbar.

## Fallen

- **Einseitig löschen/archivieren** → Sync restauriert. Immer alle 4 Orte.
- **Datei-Timestamps lügen nach Sync:** Der Abgleich kopiert mit Original-Zeitstempel; eine „22.06."-Datei kann in einem anderen Space längst neuer sein → vor dem Archivieren LastWriteTime in ALLEN Orten prüfen (neuere Version = nicht tot).
- **PowerShell-Einzeiler verlieren `$`** → immer `.ps1`.
- **MEMORY.md-Formate der Accounts sind unvereinbar** — nie den Index eines anderen Space kopieren/überschreiben; Wissen aus dem anderen Account braucht eine eigene Index-Zeile im eigenen Format.
- **Parallel-Sessions editieren MEMORY.md gleichzeitig** — vor einem Voll-Rewrite frisch lesen; kleine Ergänzungen als gezielte Edits statt Write.

Verwandt: Memory `memory-loeschen-geht-nicht-einseitig.md`, `feedback_shared_memory_zwei_wege.md`.
