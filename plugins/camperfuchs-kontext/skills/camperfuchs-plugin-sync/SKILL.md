---
name: camperfuchs-plugin-sync
description: >-
  Lebenszyklus des geteilten Camperfuchs-Wissens-Plugins camperfuchs-kontext (Azure-Repo
  camperfuchs-claude-marketplace) — Stand-Check, neue Version bauen + veroeffentlichen, Bahtis
  Aenderungen einziehen. IMMER nutzen, wenn am geteilten Plugin gearbeitet wird — explizit
  („Plugin aktualisieren", „neue Plugin-Version bauen", „Skill ins Plugin aufnehmen",
  „Changelog-Eintrag", „Marketplace-Repo", „sind wir synchron", „hat Bahti was gepusht",
  „wie update ich das Plugin") wie implizit: wenn eine DAUERHAFTE Erkenntnis entsteht
  (Architektur-Korrektur, neuer Stack-Fakt, neue Konvention), proaktiv vorschlagen, sie ins
  Plugin zu nehmen. Der Weg ist browserlos per Azure-REST aus der Sandbox — kein Windows,
  kein F:, kein PowerShell, kein Desktop Commander noetig. Enthaelt das komplette Rezept, die
  Pflicht-Verifikation und die Fallen. NICHT fuer das private Archiv cf-wissen — das ist
  bewusst getrennt und gehoert NIE hierher.
---

# Camperfuchs-Plugin-Sync — geteiltes Wissen pflegen

Björn und Bahti teilen Projektwissen über das Plugin `camperfuchs-kontext`. Quelle der Wahrheit
ist das Azure-Repo. Veröffentlicht wird per Versionsnummer + Changelog.

**Bauen ja, pushen erst auf Björns Ja** (bzw. auf direkten Auftrag).

## Stammdaten

- **Repo (Wahrheit):** `camperfuchs-claude-marketplace`, Azure-Projekt `camperfuchs`,
  Repo-ID `eac81030-ec6b-4522-8012-47c887e5c0f2`, Default-Branch `main`.
- **Zugang:** PAT aus `.secrets/azure-devops-pat.txt`, `curl -u ":$PAT"`. Aus der Sandbox
  erreichbar. `dev.azure.com`, nie `portal.azure.com`.
- **Aufbau:** `.claude-plugin/marketplace.json` (Katalog `camperfuchs-team`),
  `plugins/camperfuchs-kontext/` (`.claude-plugin/plugin.json`, `skills/<name>/SKILL.md`),
  `CHANGELOG.md`, `camperfuchs-kontext.plugin`, `README.md`.
- **Versions-Konvention:** Version steht NUR in
  `plugins/camperfuchs-kontext/.claude-plugin/plugin.json`, nicht zusätzlich im
  marketplace.json-Eintrag. Oberster CHANGELOG-Eintrag MUSS dieselbe Nummer tragen, sonst gilt
  die Version als nicht veröffentlicht.
- **Lokale Kopie** (nur Lesen/Editieren, kein Repo):
  `…\Camperfuchs Tech & Produkt\05_Skills-Automation\camperfuchs-marketplace`.
  Nach dem Veröffentlichen nachziehen.
- **Bahti:** b.sultanov@camperfuchs.de, installiert per `.plugin`-Datei in Cowork.
- **Tabu:** Keine Tokens/Passwörter ins Plugin. `.secrets/` nie anfassen. `cf-wissen` (private
  Umsatz-/Partner-Interna) gehört NIE hierher.

## Workflow A — Stand-Check

```bash
PAT=$(tr -d ' \r\n' < .secrets/azure-devops-pat.txt)
B="https://dev.azure.com/camperfuchs/camperfuchs/_apis/git/repositories/eac81030-ec6b-4522-8012-47c887e5c0f2"
curl -s -u ":$PAT" "$B/commits?searchCriteria.\$top=5&api-version=7.0"
```
Version in `plugin.json` == oberster CHANGELOG-Eintrag? Alles von b.dunker → synchron melden,
eine Zeile. Fremde Commits → Workflow C.

## Workflow B — Neue Version veröffentlichen (browserlos, erprobt 15.07.2026)

1. **Baum ziehen.** `items?scopePath=/plugins/camperfuchs-kontext&recursionLevel=full` → Blob-Liste,
   jede Datei per `download=true&$format=octetStream` in einen Arbeitsordner **im Sandbox-Home**
   (`~/mp`), NICHT auf den Mount.
   ⚠️ **Soll-Ist der Dateizahl vergleichen.** `while read` verschluckt die letzte Zeile ohne
   Zeilenumbruch → `while IFS= read -r p || [ -n "$p" ]`. Fehlt eine Datei, löscht der Push die
   Skill still aus dem Plugin.
2. **Inhalt ändern.** Nur Dauerhaftes, keine Secrets, keine Tagesdetails.
3. **Version hoch** in `plugin.json` — **byte-genau per replace auf den Bytes**, nicht die Datei
   neu schreiben (sonst gehen Formatierung/Encoding kaputt):
   ```python
   b=open(p,'rb').read(); assert b.count(b'"version":  "0.14.0"')==1
   open(p,'wb').write(b.replace(b'"version":  "0.14.0"', b'"version":  "0.15.0"'))
   ```
4. **CHANGELOG-Eintrag oben** einfügen (vor dem ersten `## `), gleiche Nummer + Datum.
5. **ALLE Skills validieren, nicht nur die geänderten** — der Installer prüft jede und bricht
   beim ersten Fehler ab. Mit **echtem YAML-Parser** (`yaml.safe_load`), nicht per Regex:
   `name` gesetzt, `description` ≤ 1024 Zeichen, kein BOM (`raw[:3] != b'\xef\xbb\xbf'`).
6. **Secret-Scan** über den Baum: `cfut_|dop_v1_|ghp_|github_pat_|sk-ant-|AIza|BEGIN … PRIVATE KEY`
   plus 52-stellige Alnum. ⚠️ **Ein Treffer in `camperfuchs-plugin-sync/SKILL.md` ist ein
   Fehlalarm** — das ist genau diese Zeile, die die Muster auflistet. Fundstelle im Kontext
   ansehen, nicht blind Alarm schlagen.
7. **`.plugin` packen** mit Python-`zipfile` in der Sandbox, Pfade mit Forward-Slashes:
   `z.write(rel, rel.replace(os.sep,'/'))`.
8. **Zip verifizieren, nicht annehmen:** `testzip()` ok, **0 Backslash-Pfade**,
   `.claude-plugin/plugin.json` auf oberster Ebene, Version stimmt, Skill-Zahl stimmt,
   jede `SKILL.md` parst.
9. **Push in EINEM Commit** per `pushes`-API (`refUpdates.oldObjectId` = aktueller main-HEAD):
   SKILL.md als `rawtext`, die `.plugin` als `base64encoded`.
10. **Gegenprobe gegen das REPO**, nicht gegen die lokale Kopie: `.plugin`, `plugin.json` und
    `CHANGELOG.md` von `main` zurückladen und Schritt 8 wiederholen.
11. **Lokale Kopie** im Projektordner nachziehen.
12. **Björn Bescheid:** neue Version + die `.plugin` per `present_files` geben. Er installiert
    mit einem Klick (Einstellungen → Capabilities). Bewusst manuell = Sicherheitsgrenze.

## Workflow C — Bahti-Änderungen einziehen

Commits von b.sultanov prüfen (fachlich plausibel, keine Secrets), Björn in 1–2 Sätzen melden,
dann Workflow B ab Schritt 2 — außer Bahti hat Version+Changelog schon gepflegt, dann nur
`.plugin` neu packen + pushen.

## Fallen

- **`while read` + letzte Zeile ohne Zeilenumbruch** → Datei fehlt im Baum → Skill verschwindet
  still aus dem Plugin. Immer Soll-Ist der Dateizahl. (15.07. fast passiert mit `wp-502-debug`.)
- **Secret-Scan-Fehlalarm** in dieser Skill (siehe Schritt 6).
- **Nichts auf dem Mount bauen.** Dort schreibt `zip` kaputte Dateien, `du -h` lügt mit `0`, und
  der Mount liefert veraltete Stände. Arbeitsordner = Sandbox-Home.
- **git funktioniert NICHT auf dem gemounteten Projektordner** (`bad config line 1`,
  `unable to unlink '.git/config.lock'`). Ein Repo kann dort NIE liegen. Vorschläge à la „der
  Projektordner wird selbst der Klon" sind tot — nicht nochmal vorschlagen.
- **Account-Skills sind read-only** (Einstellungen → Capabilities). Was selbst gepflegt werden
  soll, MUSS ins Plugin. Liegt eine Skill doppelt (Account + Plugin), erscheint sie doppelt →
  die Account-Version einmalig löschen.

## Alt-Weg über Windows/`F:` (nur im Notfall)

Klon `F:\dev\cf-marketplace` ← `git@ssh.dev.azure.com:v3/camperfuchs/camperfuchs/camperfuchs-claude-marketplace`
(**SCP-Syntax**, `ssh://…:v3` scheitert; Push per SSH-Key, kein PAT). Dann gilt: packen **nur mit
`tar.exe -a -c -f`** (NICHT `Compress-Archive` / `ZipFile::CreateFromDirectory` — die schreiben
Backslash-Pfade); **`Set-Content -Encoding UTF8` schreibt ein BOM** und zerstört `plugin.json` →
`[System.IO.File]::WriteAllText($p,$txt,(New-Object System.Text.UTF8Encoding($false)))`;
PowerShell-Einzeiler verlieren `$`-Variablen → `.ps1` schreiben und mit
`powershell -NoProfile -ExecutionPolicy Bypass -File …` starten; `git add -A` erzeugt hunderte
CRLF-Warnungen → `core.autocrlf false`. Die SSH-Meldung „not using a post-quantum key exchange"
ist Rauschen. **Kein Python auf dem Rechner** (nur Store-Aliase), Node ist echt da.
Der REST-Weg oben umgeht diese Fallen alle — deshalb ist er der Standard.
