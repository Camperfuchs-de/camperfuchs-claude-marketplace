---
name: camperfuchs-plugin-sync
description: >
  Lebenszyklus des geteilten Camperfuchs-Wissens-Plugins camperfuchs-kontext (Repo
  camperfuchs-claude-marketplace) — Stand-Check, neue Version bauen + veroeffentlichen, Bahtis
  Aenderungen einziehen. IMMER nutzen, wenn am geteilten Plugin gearbeitet wird — explizit
  („Plugin aktualisieren", „neue Plugin-Version bauen", „Skill ins Plugin aufnehmen",
  „Changelog-Eintrag", „Marketplace-Repo", „sind wir synchron", „hat Bahti was gepusht",
  „Quellbaum") wie implizit: wenn eine DAUERHAFTE Erkenntnis entsteht (Architektur-Korrektur,
  neuer Stack-Fakt, neue Konvention), proaktiv vorschlagen, sie ins Plugin zu nehmen. Enthaelt
  Stammdaten (git-Klon F:\dev\cf-marketplace, SSH-Push), Versions-Konvention, den erprobten Loop
  und die teuer gelernten Fallen: packen mit tar.exe (NICHT Compress-Archive), git laeuft NICHT
  auf dem gemounteten Projektordner, kein Python auf dem Rechner, PowerShell-Einzeiler verlieren
  $-Variablen. NICHT fuer das private Archiv cf-wissen — das ist bewusst getrennt.
metadata:
  type: skill
  scope: camperfuchs-rentanda
---

# Camperfuchs-Plugin-Sync — geteiltes Wissen pflegen

Björn und Bahti teilen Projektwissen über das Plugin `camperfuchs-kontext`. Quelle der Wahrheit
ist das Azure-Repo; veröffentlicht wird per Versionsnummer + Changelog. Bauen ja — **committen
erst auf Björns Ja** (bzw. auf direkten Auftrag).

## Stammdaten

- **Repo (Wahrheit):** `camperfuchs-claude-marketplace` im Azure-Projekt `camperfuchs`.
- **git-Klon (hier wird gearbeitet):** `F:\dev\cf-marketplace`
  ← `git@ssh.dev.azure.com:v3/camperfuchs/camperfuchs/camperfuchs-claude-marketplace`
  **SCP-Syntax!** `ssh://…:v3` scheitert mit „Could not resolve hostname". Push per SSH-Key,
  **kein PAT nötig**.
- **Lokale Kopie** (Projektordner): `…\Camperfuchs Tech & Produkt\05_Skills-Automation\camperfuchs-marketplace`
  — nur Lese-/Editier-Kopie für die Sandbox, **nicht** das Repo (git geht dort nicht, s.u.).
  Nach dem Bauen mit dem Klon synchron halten.
- **Aufbau:** `.claude-plugin/marketplace.json` (Katalog `camperfuchs-team`),
  `plugins/camperfuchs-kontext/` (`.claude-plugin/plugin.json`, `skills/<name>/SKILL.md`),
  `CHANGELOG.md`, `camperfuchs-kontext.plugin`, `README.md`.
- **Versions-Konvention:** Version steht NUR in
  `plugins/camperfuchs-kontext/.claude-plugin/plugin.json` (nicht zusätzlich im
  marketplace.json-Eintrag — maskiert sich sonst gegenseitig). Oberster CHANGELOG-Eintrag MUSS
  dieselbe Nummer tragen, sonst gilt die Version als nicht veröffentlicht.
- **Skills im Plugin (Stand 0.12.0):** agent-readiness, cache-purge, frontend-feature-shippen,
  nein-alternativen-anfragen, plugin-sync, projekt, sammelanfrage, verfuegbarkeits-flow,
  wp-502-debug.
- **Wächter:** Scheduled Task `camperfuchs-plugin-stand-check` (8:30) macht Workflow A.
- **Bahti:** b.sultanov@camperfuchs.de, installiert per `.plugin`-Button in Cowork; pusht eigene
  Änderungen per git in den Quellbaum.
- **Tabu:** Keine Tokens/Passwörter ins Plugin oder Repo. `.secrets/` nie anfassen.
  **Das private Archiv `cf-wissen` gehört NIE hierher** (Umsatzzahlen/Partner-Interna).

## Workflow A — Stand-Check („sind wir synchron?")

1. Im Klon: `git fetch origin; git status -sb; git log --oneline -3`.
2. Oberste Version in `CHANGELOG.md` == `version` in `plugin.json`? Sonst nicht sauber veröffentlicht.
3. Bewerten: fremde Commits (nicht b.dunker) → Workflow C. Klon hinter origin → `git pull`.
   Alles gleich → eine Zeile: „Plugin-Stand synchron (vX.Y.Z)."

## Workflow B — Neue Version bauen + veröffentlichen

Läuft **komplett per Desktop Commander auf `F:`**. Die Sandbox erreicht F: nicht — braucht sie
aber auch nicht mehr (siehe tar-Falle).

1. **Inhalt ändern:** `F:\dev\cf-marketplace\plugins\camperfuchs-kontext\skills\<name>\SKILL.md`.
   Nur Dauerhaftes, keine Secrets, keine Tagesdetails. `description` **max 1024 Zeichen**.
2. **Version hoch** in `plugin.json` + **CHANGELOG-Eintrag oben** (gleiche Nummer, Datum, Stichpunkte).
3. **Packen mit `tar.exe`** (verifiziert 14.07., spec-konform):
   ```powershell
   cd F:\dev\cf-marketplace\plugins\camperfuchs-kontext
   tar.exe -a -c -f F:\dev\_ck.zip *
   Move-Item F:\dev\_ck.zip F:\dev\cf-marketplace\camperfuchs-kontext.plugin -Force
   ```
4. **Zip verifizieren** (nicht annehmen): Integrität ok, **0 Backslash-Pfade**,
   `.claude-plugin/plugin.json` auf oberster Ebene, Version + Skill-Zahl stimmen.
5. **Secret-Scan** über den Baum: `cfut_`, `dop_v1_`, `ghp_`, `github_pat_`, `sk-ant-`, `AIza`,
   `BEGIN … PRIVATE KEY`, 52-stellige Alnum → muss leer sein.
6. **Commit + Push:** `git add …; git commit -m "vX.Y.Z: …"; git push origin main`.
   Die SSH-Meldung „WARNING: connection is not using a post-quantum key exchange algorithm" ist
   **Rauschen**, kein Fehler (PowerShell stuft sie nur als NativeCommandError ein).
7. **Lokale Kopie** im Projektordner nachziehen (damit die Sandbox denselben Stand liest).
8. Björn Bescheid: neue Version + „einmal Plugin updaten" (1 Klick, bewusst manuell = Sicherheitsgrenze).

## Workflow C — Bahti-Änderungen einziehen

1. `git fetch origin; git log --oneline origin/main -5` → fremde Commits ansehen.
2. Diff reviewen (fachlich plausibel? keine Secrets?), Björn in 1–2 Sätzen melden.
3. `git pull`, dann Workflow B ab Schritt 2 — außer Bahti hat Version+Changelog schon gepflegt,
   dann nur `.plugin` neu packen + pushen.

## Fallen (teuer gelernt, nicht erneut ausprobieren)

- **git funktioniert NICHT auf dem gemounteten Projektordner** (14.07. getestet): `git init`
  scheitert mit `bad config line 1` + `unable to unlink '.git/config.lock': Operation not
  permitted`; `rm -rf` wird dort ebenfalls verweigert. Ein Repo kann NIE im Projektordner liegen.
  Vorschläge à la „der Projektordner wird selbst der Klon, dann pusht die Sandbox autonom" sind
  tot — nicht nochmal vorschlagen.
- **Zip nicht auf dem Mount bauen:** `zip` schreibt dort eine kaputte Datei
  („End-of-central-directory signature not found"), und ein blindes `cp` überschreibt die noch
  gute `.plugin` mit Schrott. Außerdem meldet `du -h` auf dem Mount fälschlich `0` — mit
  `ls -la`/`stat`/`wc -c` gegenchecken.
- **`tar.exe` ist der Weg**, NICHT `Compress-Archive` (PS 5.1) und NICHT
  `[IO.Compression.ZipFile]::CreateFromDirectory` — die schreiben **Backslash-Pfade** und
  verletzen die ZIP-Spec. Das `*`-Glob nimmt `.claude-plugin` mit (kein Dot-Folder-Problem).
- **Kein Python auf dem Rechner:** `python`/`python3` sind nur Microsoft-Store-Aliase
  („Python wurde nicht gefunden"), `py` fehlt. Node ist echt da. Für Zip braucht es kein Python
  → nicht installieren.
- **PowerShell-Einzeiler über DC verlieren `$`-Variablen** und scheitern an escapten Quotes
  („Die Zeichenfolge hat kein Abschlusszeichen", „Nach foreach fehlt ein Variablenname").
  → `.ps1` in den outputs-Ordner schreiben und mit
  `powershell -NoProfile -ExecutionPolicy Bypass -File …` starten.
- **`git add -A` erzeugt hunderte CRLF-Warnzeilen** und sprengt den Tool-Output; mit
  `$ErrorActionPreference='Stop'` bricht das Skript sogar ab. → im Repo `core.autocrlf false` +
  vor den git-Aufrufen auf `Continue` schalten, Ausgabe nach `Out-Null`.
- **Account-Skills sind read-only** (Settings → Capabilities). Was selbst gepflegt werden soll,
  MUSS ins Plugin. Liegt eine Skill doppelt (Account + Plugin), erscheint sie doppelt → die
  Account-Version einmalig löschen.
- **Der alte Browser-Upload-Weg ist obsolet** (konnte nur flache Dateien, keine Unterordner).
  Nicht wiederbeleben. `dev.azure.com` direkt, nie `portal.azure.com`.
