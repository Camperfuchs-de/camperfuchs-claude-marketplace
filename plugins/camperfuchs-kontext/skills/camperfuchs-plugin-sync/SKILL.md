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

> ⚠️ **Seit 11.09.2026 hat die Cloud-Sandbox kein Egress mehr.** `dev.azure.com`,
> `www.camperfuchs.de`, `tafel.camperfuchs.de`, `api.eu.mailgun.net`, `api.cloudflare.com`
> und `eu1.make.com` antworten dort mit `connect_rejected` — das liest sich wie ein
> Serverfehler, ist aber die Egress-Policy. Erlaubt sind nur noch npm, pypi, github.com und
> api.anthropic.com. **Jedes curl-/SSH-/REST-Rezept unten läuft deshalb über den PC:**
> Desktop Commander, Skript in eine `.ps1` schreiben und per
> `powershell -NoProfile -ExecutionPolicy Bypass -File …` starten
> (`Invoke-RestMethod` / `Invoke-WebRequest` / das Git-ssh unter
> `C:\Program Files\Git\usr\bin\ssh.exe`).
>
> ⚠️ **Und die .ps1-Datei braucht ein BOM oder reines ASCII** — PowerShell 5.1 liest eine
> UTF-8-Datei ohne BOM als Windows-1252, dabei werden Umlaute und Sonderzeichen doppelt
> kodiert. Längere Texte mit Sonderzeichen deshalb nicht als Literal ins Skript schreiben,
> sondern in eine eigene Datei legen und mit
> `[System.IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)` einlesen. Außerdem frisst
> PowerShell `$`-Variablen in `-Command`-Einzeilern und bricht bei
> `$ErrorActionPreference='Stop'` schon an stderr-Rauschen ab.


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
  ⚠️ **Stand 13.09.2026: Bahti macht erstmal nichts.** Von ihm sind vorerst keine Commits zu
  erwarten, er braucht auch keinen Zugang zum GitHub-Spiegel. Das Plugin wird allein aus Björns
  Sessions gepflegt, Workflow C ruht. Ihn erst wieder einplanen, wenn Björn es ausdrücklich sagt —
  nicht von selbst „zur Sicherheit" Zugänge einrichten oder auf seine Änderungen warten.
- **Tabu:** Keine Tokens/Passwörter ins Plugin. `.secrets/` nie anfassen. `cf-wissen` (private
  Umsatz-/Partner-Interna) gehört NIE hierher.

## Workflow A — Stand-Check

Laeuft auch automatisch: Scheduled Task **`camperfuchs-plugin-stand-check`** (taeglich 8:30) —
er vergleicht die installierte Version mit dem obersten CHANGELOG-Eintrag und meldet sich nur,
wenn etwas auseinanderlaeuft.

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

## Workflow C — Bahti-Änderungen einziehen (ruht seit 13.09.2026)

> Bahti macht erstmal nichts (siehe Stammdaten). Dieser Workflow ist bis auf Weiteres
> gegenstandslos. Taucht trotzdem ein fremder Commit auf, ist das ein Grund bei Björn
> nachzufragen — nicht ihn stillschweigend einzuziehen.

Commits von b.sultanov prüfen (fachlich plausibel, keine Secrets), Björn in 1–2 Sätzen melden,
dann Workflow B ab Schritt 2 — außer Bahti hat Version+Changelog schon gepflegt, dann nur
`.plugin` neu packen + pushen.

## Verwandt: Auto-Memory-Sync (Björns Seite, gleiche Denkfalle)

Björns Auto-Memory-Dateien gleicht der Windows-Task `cf-shared-memory-sync` alle 6h zwischen drei
Spaces und `Shared-Claude-Memory\` ab (`05_Skills-Automation\sync-shared-memory.ps1`), bewusst
**ohne Löschen**. Daraus folgt (15.07.2026 verifiziert):

- **Eine Memory-Datei zu löschen bringt nichts** — sie kommt beim nächsten Lauf zurück, mit
  Original-Zeitstempel.
- **Sie mit einem Stub zu überschreiben ist schädlich** — der Stub bekommt den neuesten
  Zeitstempel, der Sync verteilt ihn in die anderen Spaces und zerstört dort den Inhalt.
- **Aufräumen läuft über den Index, nicht über die Dateien.** `MEMORY.md` wird nie synchronisiert.
  Nicht mehr Gebrauchtes kommt aus dem Index raus, die Datei bleibt liegen. Zu viel Gutes für den
  Index → thematische `index_*.md`-Subindexe.

Merksatz für beide Systeme: **die Wahrheit liegt im Quellbaum bzw. im Index, nicht in der lokalen
Kopie.** Wer die Kopie anfasst, um aufzuräumen, macht es meistens kaputt.

## Parallele Sessions — Versionsnummer VOR dem Bauen prüfen

Björn lässt mehrere Sessions gleichzeitig laufen, alle committen als `b.dunker`. Am 15.07.2026 ist
deshalb zweimal dieselbe Nummer vergeben worden (zwei verschiedene v0.14.0, dann zwei v0.15.0), und
einmal ist es richtig teuer geworden: Session B baute das `.plugin` aus einem Baum ohne die frisch
gepushte Skill `camperfuchs-alternativ-angebot` und überschrieb den Changelog-Eintrag von Session A.
Ergebnis: Quellbaum 11 Skills, ausgeliefertes Paket 10. Die Skill war still weg, ohne Fehler.

Pflicht vor jedem Bauen:

1. **Lock setzen** (siehe unten). Wer den Lock nicht bekommt, baut nicht.
2. `git fetch` + `git log HEAD..origin/main` — liegt dort schon eine neuere Version, erst einziehen.
3. Version IMMER erst nach dem Einziehen bestimmen, nie vorher festlegen.
4. **Soll-Ist der Skill-Zahl vergleichen**: Ordner im Quellbaum vs. `skills/*/SKILL.md` im gebauten
   `.plugin`. Weichen sie ab, ist etwas rausgefallen. Nie ungeprüft pushen.
5. Fremden Changelog-Eintrag mit gleicher Nummer nicht überschreiben, sondern eigenen Eintrag mit
   der nächsten Nummer anlegen.
6. **Lock freigeben**, sobald der Push durch ist — auch wenn abgebrochen wurde.

### Das Lock-Rezept (`PLUGIN-LOCK.md` im Repo-Wurzelverzeichnis)

Der Trick: **git push ist atomar.** Zwei Sessions können nicht beide dieselbe Lock-Datei anlegen und
pushen — die zweite wird abgelehnt. Damit gewinnt genau eine, ohne dass jemand koordinieren muss.

**Lock nehmen:**

```bash
git fetch origin && git merge --ff-only origin/main
# Liegt PLUGIN-LOCK.md schon da und ist der Zeitstempel < 30 min alt?
#   -> STOPP. Nicht bauen. Björn melden: "Andere Session pflegt gerade das Plugin, seit HH:MM."
#   -> Ist er älter als 30 min, ist es eine Leiche: übernehmen und im Commit vermerken.
printf 'gehalten seit: %s\nzweck: <was gebaut wird>\n' "$(date -Iseconds)" > PLUGIN-LOCK.md
git add PLUGIN-LOCK.md && git commit -m "lock: Plugin-Pflege" && git push origin main
# Push abgelehnt = eine andere Session war schneller -> git reset --hard origin/main, STOPP.
```

**Lock freigeben** (im selben Commit wie die neue Version, spart eine Runde):

```bash
git rm PLUGIN-LOCK.md
git add ... && git commit -m "vX.Y.Z: ..." && git push origin main
```

Der Lock ist eine Höflichkeitsbremse gegen die eigenen Parallel-Sessions, kein Sicherheitsmechanismus.
Er kostet 20 Sekunden und hat am 15.07.2026 gefehlt, als eine Skill still aus dem Paket fiel.

## Das Paket baut jetzt die Pipeline (seit 01.08.2026)

`marketplace-plugin-build` (Definition 29, YAML `ci/plugin-build.yml`, Pool `macos`) laeuft bei jedem
Push auf `main`, der `plugins/*`, `CHANGELOG.md` oder das Script anfasst. Sie prueft ALLE Skills
(Frontmatter, name, description <= 1024, kein BOM), scannt auf Secrets, vergleicht Skill-Zahl
Quellbaum gegen Paket, baut `camperfuchs-kontext.plugin` **deterministisch** (feste Zeitstempel, damit
gleicher Inhalt gleiche Bytes ergibt) und committet es zurueck, falls es abweicht. Der eigene Commit
traegt `[skip ci]`.

Damit kann Schritt 7/8 aus Workflow B nicht mehr vergessen werden: eine gepushte Skill landet
automatisch im ausgelieferten Paket. Von Hand bleibt genau das, was Urteil braucht: Inhalt,
Versionsnummer, Changelog-Eintrag und Bjoerns Installations-Klick.

Lokal dasselbe pruefen: `python3 ci/plugin_pack.py --check` (Exit 1 bei Abweichung) bzw. `--write`.

### GitHub-Spiegel für den Claude-Marktplatz (seit 13.09.2026 scharf)

Dieselbe Pipeline spiegelt `main` zusätzlich nach **`Camperfuchs-de/camperfuchs-claude-marketplace`**
auf GitHub (privates Repo). Damit lässt sich das Plugin in Claude Code direkt als Marktplatz
einbinden, statt die `.plugin`-Datei von Hand zu installieren:

```
/plugin marketplace add Camperfuchs-de/camperfuchs-claude-marketplace
/plugin install camperfuchs-kontext@camperfuchs-team
```

Der Spiegel-Schritt läuft nur, wenn die Pipeline-Variable **`GITHUB_TOKEN`** gesetzt ist — fehlt
sie, wird er stillschweigend übersprungen und die Pipeline bleibt trotzdem grün. Das sah monatelang
nach „läuft" aus, obwohl nichts bei GitHub ankam. **Wer prüfen will, ob der Spiegel wirklich
arbeitet, schaut bei GitHub nach, nicht auf die Pipeline-Farbe.**

Der hinterlegte Token (fine-grained, Konto `camperfuchs`, Rechte Contents + Pull requests auf genau
dieses Repo) **läuft am 13.09.2027 ab**. Danach schlägt der Push fehl; dann neuen Token erzeugen und
die Pipeline-Variable überschreiben. Die Variable selbst bleibt dauerhaft bestehen. Kopie des Tokens
liegt unter `.secrets/github-marketplace-token.txt`.

### ⚠️ „Die Pipeline hat nicht ausgeloest" ist fast immer eine Fehldiagnose (09.09.2026, zweimal)

Definition 29 laeuft im **Agent-Pool 10 mit genau EINEM online Agent**, der auch alle
staging-/prod-Deploys und PR-Builds faehrt. Laeuft gerade ein Deploy, wartet der Plugin-Build
in der Warteschlange — am 09.09. lagen zwischen Push und Build-Start **3,5 Minuten**
(gequeued 16:27:27, gestartet 16:30:56, fertig 16:31:16), weil `prod-build-and-deploy` den
Agent hielt. Dazu kommt: **`builds?definitions=29` laggt** und zeigt einen frischen Build oft
noch gar nicht.

Beides zusammen hat an einem Tag ZWEI Sessions (A4 bei v0.56.0, A9 bei v0.57.0) zu dem Schluss
gebracht, die Pipeline sei ausgefallen — beide haben das Paket von Hand gebaut und mit einem
irrefuehrenden Commit-Kommentar gepusht. Schaden entsteht dabei keiner (der Bau ist
deterministisch, die Bytes sind identisch), aber die Historie wird unwahr und es kostet Zeit.

**Regel vor dem Schluss „Pipeline laeuft nicht":**

```bash
# ungefilterte Liste nehmen, NICHT definitions=29
curl -s -u ":$PAT" "https://dev.azure.com/camperfuchs/camperfuchs/_apis/build/builds?\$top=12&api-version=7.0"
# und sehen, ob der Agent gerade belegt ist
curl -s -u ":$PAT" "https://dev.azure.com/camperfuchs/_apis/distributedtask/pools/10/jobrequests?api-version=7.0"
```

Erst wenn nach **10 Minuten** kein Build mit dem eigenen `sourceVersion` auftaucht und der Agent
frei ist, von Hand bauen — und den Commit dann ehrlich betiteln
(„Paket manuell gebaut, Pipeline-Build blieb aus"), nicht „Pipeline hat nicht ausgeloest".
Details zum Agent-Stau: Skill `camperfuchs-build-agent-stau`.

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

### Azure-Weboberfläche (allerletzter Ausweg, wenn auch git nicht geht)

- **Der Web-Upload nimmt zwar mehrere Dateien, legt sie aber NUR flach in den aktuellen Ordner**
  (`webkitdirectory=false`) — Ordnerstruktur geht damit nicht. Verschachtelte Quellbaum-Dateien
  kommen so nie sauber ins Repo; dafür bleibt nur der git-Push oder ein hochgeladenes
  `quellbaum.zip`, das jemand anschließend entpackt und pusht.
- **Der Web-Editor (Monaco) ist nicht skriptbar:** `window.monaco` ist von außen nicht erreichbar,
  und Tipp-Eingaben zerschießen JSON/Markdown durch die Auto-Klammern. Deshalb nie Datei-Inhalte
  über den Web-Editor anlegen oder ändern — nur `file_upload` mit den exakten Bytes.
