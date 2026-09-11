---
name: camperfuchs-frontend-feature-shippen
description: >-
  Kleine Frontend-Änderung (Text, Hinweis, Button, Icon-/CSS-Größe, bedingtes UI-Element) in
  den Camperfuchs-Next-Apps umsetzen UND live schalten. IMMER nutzen, wenn Björn eine
  UI-/Text-/Style-Optimierung in der App will oder sagt „mach das live", „X größer",
  „Feature einbauen und ausrollen", „bring das live", „kannst du direkt live schalten" —
  auch implizit („kannst du das in der App machen", „das fehlt noch im Frontend", „warum
  nicht auf allen Seiten"). Liefert den erprobten Pfad: richtige Komponente per sichtbarem
  String greppen (Suchleiste 3×: SearchingBar/SearchWidget/SearchHeader), Edit im Worktree
  von F:\dev\camperfuchs, Push via SSH, PR nach main/staging/prod NUR per Browser (PAT
  abgelaufen; Azure-Freeze → neuer Tab), Approve + Auto-Complete erst nach Create
  (main=Squash, staging/prod=Rebase), staging-Verifikation, prod-Gate freigeben, Live-Check
  per JS oder CSS-Bundle-Fingerprint, optional automatisch per Wächter. Ergänzt
  camperfuchs-azure-devops/-deploy/-lokale-dev-umgebung/-suchfilter/-basis.
---

# Camperfuchs: Frontend-Feature shippen (Idee → live)

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


Verkettet das Wissen aus camperfuchs-lokale-dev-umgebung, -azure-devops und
-deploy zu EINEM erprobten Pfad: von „ich will X in der App" bis „X ist live auf
www verifiziert". Erprobt am Ort-Hinweis (WI #252, 08.06.), am Such-Leerzustand-Fix
(#732) und am Mobil-Filter-X (#739, 14.06.2026).

## Goldene Regeln (aus camperfuchs-basis)
- **Selbst lösen vor Bahti-Ticket.** Frontend-Text/UI/CSS = immer selbst per
  Feature-Branch + PR. Bahti nur, wenn Origin/K8s/Deploy-Infra nötig.
- **Reviewer = WIR, nicht Bahti.** Bahti NICHT manuell als Reviewer setzen. Die
  Branch-Policy addet ohnehin automatisch.
- **Claude darf live schalten — mit Bedingungen:** staging autonom; vor dem
  prod-Go-live IMMER auf staging verifizieren, dass es WIRKLICH funktioniert,
  UND Björn nochmal fragen + OK abwarten. Sagt Björn „direkt live schalten" =
  prod-Go liegt vor (im Wächter-Prompt dokumentieren).
- **Live-Status + ETA**, Hänger sofort melden.
- **WIR = b.dunker.** PRs/Promotes unter b.dunker sind unsere eigenen — bewusst
  mit-deployen. Nur ein fremder b.sultanov(Bahti)-Commit im staging→prod-Diff ist
  vor prod zu klären. (Im Commits-Tab des Promote-PRs prüfen.)
- **`deploy-kette` SCHON vor dem main-PR sperren, nicht erst beim Promote** (09.09.2026
  teuer gelernt). Solange ein eigener Zwischenstand in `main` liegt und die Kette offen
  ist, nimmt die naechste b.dunker-Session ihn beim naechsten staging→prod mit — die
  Regel eine Zeile hoeher gilt aus DEREN Sicht und ist deshalb kein Schutz. An dem Tag
  ging ein Knopf live, den Bjoern eine Minute vorher abgelehnt hatte, und musste per
  Korrektur-Kette (PR 1966→1967→1968) wieder von prod genommen werden. Also: Lock auf
  `deploy-kette` setzen, BEVOR der main-PR aufgeht, und erst nach dem prod-Check
  freigeben. Ist die Kette belegt: eigenen Stand auf der Tafel ansagen („liegt in main,
  noch NICHT fuer prod freigegeben") und die haltende Session bitten, main→staging
  mitzunehmen — sonst promotet sie an deinem Zwischenstand vorbei.
- **Ein Feature, das Bjoern noch nicht gesehen hat, ist kein prod-Kandidat.** Steht es
  auf staging und kommt seine Rueckmeldung („den Knopf brauchen wir nicht"), gehoert die
  Korrektur VOR den prod-Promote — nicht hinterher. Die Kette laeuft schneller, als eine
  Rueckmeldung eingearbeitet ist.

## Schritt 0 — Die richtige Komponente finden (häufigste Falle!)
Nicht raten, wo ein Element lebt. Per sichtbarem Text/Placeholder greppen:
```
DC start_search  path=F:\dev\camperfuchs\frontend  searchType=content
                 pattern="<sichtbarer String|Placeholder>"  filePattern=*.tsx
```
Wichtige Doppelgänger (die Suchleiste gibt es DREImal):
- `frontend/app/components/Sections/SearchingBar.tsx` — Hero-Such-Formular,
  navigiert per `router.push` nach `/wohnmobil-mieten`.
- `frontend/widgets/SearchWidget.tsx` — das in WordPress eingebettete
  Startseiten-Widget (eigener Bundle).
- `frontend/pages/wohnmobil-mieten/SearchHeader.tsx` — die echte Such-/
  Filterleiste auf der Ergebnisseite (mit „Meist Genutzt", „Typ"). Hier lebt auch
  das Mobil-Filter-Sheet `styles.smartphoneFilterLayout` (nur <1200px sichtbar)
  inkl. Schließen-X (`<div className={styles.closure}>`), und der Leer-/
  Fehlerzustand der Ergebnisliste in `SearchMainContent.tsx`.
Ein WI, das „in der Suche" sagt, meint oft nur eine davon → prüfen, ob das
Feature auf ALLEN gewünschten Flächen sitzt.

## Schritt 1 — Lokal umsetzen (F:\dev\camperfuchs, per Desktop Commander)
Native Read/Grep erreichen F: NICHT → IMMER Desktop Commander (läuft auf Windows).
**Björn hat fast immer einen WIP-Branch ausgecheckt** → NICHT stören: isoliert per
Worktree off origin/main bauen.
```
DC start_process  cd /d F:\dev\camperfuchs & git fetch origin --quiet & git rev-parse --short origin/main
DC start_process  git worktree add -b fix/<kurz> F:\dev\cf-wt-<kurz> origin/main
DC read_file / edit_block   <Komponente im Worktree>   # minimaler, offensichtlicher Edit
DC start_process  git --no-pager diff
```
Vor dem Push benutzte Variablen/Props im Scope prüfen (spart eine Build-Runde).
TSX-Syntaxcheck ohne vollen Build: `npx --yes esbuild <datei>.tsx --loader:.tsx=tsx
--outfile=NUL`. (SCSS-only-Änderungen: esbuild greift nicht → der staging-Build
ist das Gate.) Worktrees nach Merge aufräumen (`git worktree remove`).

### Lint-Vorcheck vor dem Push (spart eine ganze Build-Runde auf dem langsamen Pool)

Der `pr-build` laesst **ESLint** mitlaufen; ein einziger Verstoss killt Build 1, und du wartest
15+ Minuten auf Build 2 (teuer gelernt 24.07.2026: `@typescript-eslint/prefer-regexp-exec` liess
Build 3813 durchfallen). Deshalb VOR dem Commit den geaenderten Code pruefen:

```
cd F:\dev\cf-wt-<kurz> && npx eslint <geaenderte Datei>
```

Schnell zuschlagende Regeln in diesem Repo:
- **`prefer-regexp-exec`**: NIE `str.match(re)` fuer einen einfachen Match — Pattern vorab
  definieren und `re.exec(str)` benutzen.
- **`no-unused-vars`** / ungenutzte Imports (bleiben nach einem Edit oft uebrig).
- Fehlende React-Hook-Dependencies (`react-hooks/exhaustive-deps`).

Laeuft `eslint` im Worktree nicht sauber (Setup fehlt), mindestens den Diff manuell gegen diese
Regeln durchsehen, bevor gepusht wird.

## Schritt 2 — Commit + Push (SSH, nicht PAT)
```
DC start_process  git add <datei> & git -c user.name="Bjoern Dunker" -c user.email="b.dunker@camperfuchs.de" commit -q -m "<typ>(scope): …"
DC start_process  git push -u origin fix/<kurz>
```
Push läuft über den SSH-Key (ssh.dev.azure.com), unabhängig vom PAT. Die
„post-quantum"-Warnung ist harmlos (mit findstr rausfiltern).

## Schritt 2b — Encoding-Guard (Pflicht, kostet 10 Sekunden)

Vor JEDEM Push, der eine Datei mit deutschen Texten anfasst (.tsx/.ts/.json/.md), pruefen, ob
Umlaute, `€`, Gedankenstriche oder Emoji doppelt kodiert wurden. Der Build meckert NICHT — es
sind syntaktisch gueltige Strings, sie gehen bis prod durch.

```bash
grep -c -P 'Ã|â‚¬|â€|ðŸ|Â·' <datei>        # 0 erwartet, alles andere = STOPP
```

Am ausgelieferten Bundle gegenpruefen (nach dem Deploy):

```bash
grep -o -a -h -P '\\x(c2|c3|e2|f0)\\x[0-9a-f]{2}' chunks/*.js   # 0 Treffer erwartet
```
Merke: Umlaute stehen im Bundle korrekt als `\xe4` — `\xc3\xa4`, `\xe2\x82\xac`,
`\xf0\x9f\x8f\xb7` sind Mojibake.

**Ursache Nr. 1: Windows-PowerShell.** `Invoke-RestMethod` auf `…/items?…&$format=text`
dekodiert Antworten ohne `charset`-Header als ISO-8859-1. Wer so eine Datei holt, aendert und
zurueckschreibt, kodiert die GANZE Datei doppelt — auch die Stellen, die er gar nicht angefasst
hat. Genau so ging am 01.08.2026 PR 1645 (Bild-Karussell) live und die Suchseite zeigte
stundenlang `ab 169 â‚¬ / Nacht`, kaputte Karussell-Pfeile und `NÃ¤chte`.

→ **Read-Modify-Write von Repo-Dateien NUR aus der Sandbox** (`curl` + Python, explizit UTF-8).
PowerShell darf Status abfragen, PRs anlegen, approven — aber nie Dateiinhalte transportieren.

⚠️ **Nicht blind reparieren.** Ein paar Stellen dokumentieren Mojibake ABSICHTLICH (z.B. `camperfuchs-legacy-backend` zeigt, wie das Backend falsche Zeichen rendert). Vor dem Ersetzen den Treffer im Kontext ansehen. Und: die Fehl-Dekodierung ist mal ISO-8859-1, mal cp1252 — bei cp1252 landen die Bytes 0x80-0x9F auf Zeichen wie „€“ oder „—“, ein reiner latin-1-Rundlauf lässt die dann stehen.

**Reparatur, wenn es doch passiert ist:**

```python
fixed = kaputt.encode('latin-1').decode('utf-8')   # laeuft es durch, war es genau diese Doppelkodierung
```
Dann als normalen Fix-PR main → staging → prod durchziehen (Diff enthaelt NUR die Zeichen,
keine Logik). Beispiel: PR 1654/1655/1656 am 01.08.2026.

## Schritt 3 — PR → main (Browser oder REST — PAT vorher testen)
⚠️ **Der PAT-Status schwankt.** Am 14.06.2026 war er abgelaufen (`curl -u ":$PAT" …/_apis/…`
lieferte `{"code":"rest_not_logged_in"}`, HTTP 401) — daher stand hier lange „nur Browser".
Inzwischen laeuft der REST-Weg wieder (`camperfuchs-plugin-sync` und `camperfuchs-legacy-backend`
setzen ihn voraus, zuletzt im August 2026 genutzt). **Regel: PAT einmal mit einem harmlosen
GET testen** — antwortet er, ist der REST-Ship-Loop der schnellere Weg; kommt 401, alle
Azure-Aktionen ueber den eingeloggten Browser (Claude in Chrome) fahren. Ein dritter Weg, wenn
weder PAT noch Browser ziehen: **git ueber SSH** (Push/Commit gehen unabhaengig vom PAT).
(Oeffentliche API-/Live-Checks gegen www/staging brauchen ohnehin keinen PAT.)

⚠️ **Azure-SPA-Freeze (teuer gelernt 14.06.):** Create-/Diff-Seiten erreichen
manchmal nie „document_idle" → `screenshot`/`read_page`/`find` scheitern mit
„Page still loading / waited 45000ms". Besonders der **schwere staging→prod-Diff**.
**Fix: einen NEUEN Tab anlegen (`tabs_create_mcp`) und dort frisch navigieren** —
das löst den Hänger zuverlässig. Reloads/Waits im selben wedged Tab helfen nicht.

PR-Create-Direktlink:
```
https://dev.azure.com/camperfuchs/camperfuchs/_git/camperfuchs/pullrequestcreate?sourceRef=<feature-branch>&targetRef=main
```
- Titel/Beschreibung füllt Azure aus dem Commit vor.
- Reviewer NICHT manuell setzen (b.dunker + b.sultanov sind optional/auto).
- ⚠️ **Auto-Complete-Reihenfolge (teuer gelernt):** Den „Set auto-complete"-Haken
  VOR dem Anlegen anzuhaken wirft oft „Failed to set auto-complete: Merge strategy
  is not allowed by policy". → Stattdessen: **erst „Create"** → dann **„Approve"**
  (als b.dunker erfüllt das „mind. 1 Reviewer muss approven") → dann **„Set
  auto-complete"** über den Dropdown-Pfeil → im Dialog die **erlaubte Merge-
  Strategie** wählen: **main = Squash commit**, **staging/prod = Rebase and
  fast-forward** (Delete source branch für Feature-Branches an, für main/staging
  aus). Mergt automatisch, sobald die Checks grün sind.

## Schritt 4 — main → staging (Deploy auf staging)
staging ist geschützt (Direkt-Push = `TF402455`). Promote-PR:
```
https://dev.azure.com/camperfuchs/camperfuchs/_git/camperfuchs/pullrequestcreate?sourceRef=main&targetRef=staging
```
Approve + Auto-Complete **Rebase**. Häufig steht main schon == staging (CI/andere
Session hat promotet) → die Create-Seite sagt „There are no changes to merge" →
dann ist nichts zu tun. Sonst triggert der Merge Pipeline 12
`staging-build-and-deploy`; ggf. wartet ein Env-Gate „staging" → freigeben (NUR
staging). Was mitfährt vorher nennen: `git --no-pager log --oneline
origin/staging..origin/main`.

## Schritt 5 — Auf staging verifizieren (Pflicht vor prod)
Warten bis `staging-build-and-deploy` durch ist, dann prüfen. ⚠️ **~5 Min
Pod-Tausch-Lag** nach „Deploy succeeded" — kurz nach Finish antworten teils noch
alte Pods. Tripwire für „neue Pods live": ein neu hinzugekommener Response-Key
(z.B. ein primitives `boolean`, das nicht null sein kann) ist erst bei neuen Pods
gesetzt.
- **Sichtbarer Text / bedingtes Element:** Chrome `navigate
  https://staging.camperfuchs.de/<pfad>?cb=1` (Basic-Auth camperfuchs/camperfuchs),
  dann `document.body.innerText.includes('<String>')`; Toggle beidseitig testen.
- **Backend-Verhalten:** öffentliche API mit Cache-Buster gegen staging curl'en
  (Basic-Auth) und die Treffer/Felder prüfen.
- ⚠️ **Mobile-only Änderung ist headless NICHT visuell prüfbar** (innerWidth lässt
  sich nicht <1200px zwingen; das Sheet ist ≥1200px `display:none`). Stattdessen
  über den **CSS-Bundle-Fingerprint** belegen, dass die Änderung deployed ist:
  ```
  BASE=https://camperfuchs:camperfuchs@staging.camperfuchs.de
  curl -s "$BASE/wohnmobil-mieten" | grep -oE '/_next/static/css/[^"]+\.css'   # Chunk-Links
  curl -s "$BASE/_next/static/css/<chunk>.css" | grep -o 'box-sizing:content-box'  # bzw. dein Rule-Fingerprint
  ```
  (Klassennamen sind in CSS-Modulen gehasht → nach dem eindeutigen Eigenschafts-
  Fingerprint greppen, z.B. `font-size:1.75rem;padding:.5rem`.) Visuelle Endabnahme
  macht Björn am Handy auf staging.

### ⚠️ JS-Bundle-Fingerprint: Chunks über `_buildManifest.js` enumerieren (teuer gelernt 09.07.)
Für Änderungen, die als **Inline-Style/JSX** im JS landen (nicht im CSS-Modul), gilt:
**Nur die im HTML referenzierten Chunks zu greppen REICHT NICHT.** Seit PR #1303
(`perf/code-split-datepicker`) werden Datepicker/BookingCalculator **lazy** nachgeladen —
ihr Chunk steht NICHT im initialen HTML. Wer nur das HTML scannt, zieht den Fehlschluss
„Fix ist nicht live / wurde revertet", obwohl er live ist (konkret 09.07.: 23 JS aus dem
HTML vs. **60** inkl. Manifest; der Treffer lag in `chunks/6030-*.js`, nur im Manifest).

Richtiger Weg:
```
buildId aus dem HTML ziehen:      "buildId":"<id>"
Manifest holen:                   /_next/static/<buildId>/_buildManifest.js
ALLE static/**.js aus HTML + Manifest vereinigen  → dann erst nach dem Fingerprint greppen
```
Weitere Fallen dabei:
- **i18n-Keys sind KEIN Komponenten-Marker.** `rangeOverlapsBooked`, `genericError`,
  `requestHint` liegen im Übersetzungs-Bundle (`chunks/pages/_app-*.js`) → führt zum
  falschen Chunk. Marker mit echtem Komponenten-Literal wählen (z.B. `Kurzfristig buchbar`,
  `cf-day-with-price`).
- **Taugliche Fingerprints:** Hex-Farben/Literal-Strings aus Inline-Styles (`fff4d6`,
  `2px solid #f0b400`), className-Literale. **Untauglich:** lokale Variablennamen
  (wegminifiziert) und reactstrap-Klassen wie `alert-warning` (wird dynamisch als
  `alert-${color}` gebaut, steht nie literal drin).
- **Quelle schlägt Bundle:** bei Zweifel zuerst `git show origin/prod:<pfad>` prüfen —
  das ist die belastbare Aussage, ob die Änderung noch im Code ist.

Windows/PowerShell beim Prüfen: `$`-Variablen werden in `powershell -Command` gestrippt →
längere Checks als `.ps1` schreiben und mit `-File` starten. Pfade mit `[Klammern]`
brauchen `Get-Content -LiteralPath`. `Select-String`-Ausgabe wird im DC-Output oft
ABGESCHNITTEN → nicht als „kein Treffer" fehldeuten.

## Schritt 6 — prod-Gate → staging → prod
ERST Björn fragen + OK abwarten (was alles mit live geht). „Direkt live schalten"
= OK liegt vor. Dann (NEUER Tab gegen Freeze):
```
https://dev.azure.com/camperfuchs/camperfuchs/_git/camperfuchs/pullrequestcreate?sourceRef=staging&targetRef=prod
```
- ⚠️ **Commits-Tab prüfen:** Es fahren ALLE Commits mit, die staging prod voraus
  ist — nur b.dunker erwartet; taucht ein fremder b.sultanov(Bahti)-Commit auf →
  NICHT promoten, mit Björn klären.
- prod = `b.dunker must approve` (Required) → als b.dunker approven.
- „Set auto-complete" → **Rebase and fast-forward** (hält prod == staging),
  Delete source aus.
- Merge triggert Pipeline 13 `prod-build-and-deploy`. **Env-Gate „prod" freigeben**
  (Pipelines → Runs → den Run am prod-Commit → Stage „Deploy to Prod" → Approve).
  Im skaffold-Log das geänderte Image prüfen: `succeeded` ODER `Found Remotely` am
  prod-SHA (kein `canceled`).
- Live-Beleg auf `https://www.camperfuchs.de/<pfad>?cb=<n>` (ohne Auth): per JS
  auf sichtbaren Text bzw. per CSS-Bundle-Fingerprint (wie Schritt 5).

## Autonom live schalten per Wächter (Scheduled Task) — empfohlen bei langen Builds
pr-build + je Deploy dauern ~15–18 Min → nicht in der Session abpollen (verbrennt
Tokens, blockiert Björn). Stattdessen einen **One-Shot Scheduled Task** anlegen,
der die Kette eigenständig zu Ende führt (Mechanik + Sofort-Abbruch-Check → Skill
`camperfuchs-release-waechter`):
- Prompt selbst-enthaltend: PR-Nr, Branch, geänderte Datei + Rule-Fingerprint,
  „PAT abgelaufen → Browser", „Freeze → neuer Tab", Merge-Strategien je Branch,
  prod-OK-Status, prod-TABU falls kein OK.
- **Erster Schritt jedes Laufs: Sofort-Abbruch-Check** — ist der Commit schon von
  prod-HEAD erreichbar (`git merge-base --is-ancestor <sha> origin/prod`), ist er
  live → melden + Task deaktivieren, NICHT erneut planen. Bereits erledigte Stufen
  (main/staging) überspringen.
- Ablauf pro Lauf: Status der aktuellen Stufe prüfen → wenn fertig, nächste Stufe
  (Promote/Approve/Verify); **wenn noch am Bauen/Deployen, sich selbst ~12 Min
  später neu planen** (`create_scheduled_task` neuer fireAt) und mit Kurzstatus
  enden. Env-Gates nur für die jeweils richtige Umgebung freigeben.
- Am Ende: Worklog-Eintrag + ehrlicher Bericht an Björn (live ja/nein, Beleg),
  bei Mobile zusätzlich Bitte um Handy-Check.
Erprobt 14.06.: `leerzustand-fix-staging`, `leerzustand-prod-rollout`,
`mobil-filter-x-staging` (bis prod).

## Build-/Deploy-Fakten (Geduld einplanen)
- Builds laufen inzwischen oft auf einem Linux-Agent (bjoern-linux-OptiPlex/
  ubuntu), stabiler als der alte ArschBook-Mac. Bei Hang/`notStarted` (Agent
  offline) bzw. `canceled` (Registry-Timeout): neuen Build der Merge-Ref queuen.
- Fortschritt browserlos: `git fetch origin; git --no-pager log --oneline -2
  origin/<branch>` — sobald der „Merged PR …"-Commit auf dem Zielbranch erscheint,
  ist gemergt. (Merge-Status selbst braucht aber Azure/Browser.)
- Hashed Next-Chunks → kein Cloudflare-Purge nötig.

## Deploy-Stage bricht ab: Helm-Installer faellt still auf Helm 3.1.2 zurueck

Symptom (30.07.2026, prod-Build 4162): Build-Stage **gruen**, die Deploy-Stage bricht
sofort ab mit

```
[command] .../helm/3.1.2/x64/linux-amd64/helm upgrade ... --dependency-update ...
Error: unknown flag: --dependency-update
```

Ursache: `HelmInstaller@1` ohne feste Version fragt die GitHub-Releases-API nach der
neuesten Helm-Version. Schlaegt der Call fehl (TLS-/Netzfehler auf dem self-hosted
Agent), faellt der Task **still** auf seine Default-Version **Helm 3.1.2** zurueck —
die kennt `--dependency-update` (gibt es ab Helm 3.7) nicht. Beleg im Log des Tasks
„Install Helm": `... Using default Helm version v3.1.2.` statt
`Found tool in cache: helm 4.2.3 x64`.

**Dauerhafter Fix liegt seit 30.07.2026 im Repo** (`ci/deploy-prod-pipelines.yml` und
`ci/deploy-staging-pipelines.yml`):

```yaml
- task: HelmInstaller@1
  displayName: 'Install Helm'
  inputs:
    helmVersionToInstall: '4.2.3'
```

Feste Version = kein API-Lookup und Cache-Hit auf dem Agent. **Nie auf `latest`
zuruecksetzen.** Taucht der Fehler trotzdem auf: pruefen, ob der Deploy-Branch die
gepinnte YAML schon hat — die Deploy-Pipeline liest ihre YAML aus dem jeweiligen
Branch, der Pin wirkt also erst, wenn er bis `staging` bzw. `prod` durchgereicht ist.

### Gescheiterten Deploy neu anstossen

`PATCH /build/builds/{id}/stages/{stageName}` mit `{"state":"retry"}` antwortet zwar
**204**, startet die Stage aber **nicht** neu (Timeline bleibt auf `attempt 1 / failed`).
Verlaesslich ist ein frischer Lauf der Deploy-Definition:

```
POST /build/builds?api-version=7.1   {"definition":{"id":13},"sourceBranch":"refs/heads/prod"}
# staging analog: {"id":12} + refs/heads/staging
```

Der neue Lauf baut nochmal und laeuft wieder ins Environment-Approval-Gate → dort freigeben.

### Zwei Zeit-Fallen drumherum
- **Auto-Trigger kommt verzoegert:** nach dem Merge startet `*-build-and-deploy` teils
  erst 1–3 Minuten spaeter. Nicht sofort nachqueuen, sonst laufen zwei Deploys parallel
  (den ueberfluessigen per `PATCH /build/builds/{id}` `{"status":"cancelling"}` stoppen).
- **Das Approval erscheint spaet:** `GET /pipelines/approvals?state=pending` liefert
  waehrend der Build-Stage noch nichts. Erst wenn die Deploy-Stage wartet, gibt es eine
  Approval-ID — weiter pollen statt anzunehmen, es gebe kein Gate.

## Alte PRs: Stale-Branch-Falle (teuer gelernt 07.08.2026)

**`mergeStatus: succeeded` heisst nur „textuell mergebar", NICHT „semantisch richtig".**
Bei jedem PR, der aelter als ein paar Tage ist, VOR dem Scharfstellen von Auto-Complete
pruefen, ob der Branch neuere main-Aenderungen zurueckdrehen wuerde.

Der Fall: PR 1732 („Auth-Gate vor DB-Zugriff") war zweimal rot (pr-build 4503 und der
Requeue 4609), beide Male `CustomerBookingControllerSpec` mit
`TooManyInvocationsError` / `TooFewInvocationsError` auf `checkBookingPlausibility`.
Kein Flake: Der Branch stammte von altem main und trug eine ALTE Fassung von
`CustomerBookingController.java`. Der Merge haette zwei neuere main-Aenderungen
stillschweigend rueckgaengig gemacht — `normalizeLegacyStationId()` (Legacy-Stations-IDs
aus alten Angebots-PDFs) und den `preDayPickup`-Parameter (5-arg statt 6-arg → genau
daran starben die Specs).

**Pflicht-Check vor Auto-Complete bei alten PRs:**
```bash
# 1) Welche Dateien fasst der PR an?
LAST=$(curl -s -H "Authorization: Basic $AUTH" \
  "$B/pullrequests/$PR/iterations?api-version=7.0" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['value'][-1]['id'])")
curl -s -H "Authorization: Basic $AUTH" \
  "$B/pullrequests/$PR/iterations/$LAST/changes?api-version=7.0"

# 2) Branch-Tip gegen AKTUELLES main diffen (nicht gegen die Merge-Basis!).
#    Zeigt der Diff Zeilen, die in main NEUER sind und im Branch FEHLEN → Stale-Branch.
curl -s -H "Authorization: Basic $AUTH" -H "Accept: text/plain" \
  "$B/items?path=$FILE&versionDescriptor.version=main&versionDescriptor.versionType=branch&includeContent=true&api-version=7.0" > /tmp/main.txt
curl -s -H "Authorization: Basic $AUTH" -H "Accept: text/plain" \
  "$B/items?path=$FILE&versionDescriptor.version=$BRANCH&versionDescriptor.versionType=branch&includeContent=true&api-version=7.0" > /tmp/branch.txt
diff -u /tmp/main.txt /tmp/branch.txt
```

**Konsequenz: NICHT rebasen, sondern neu aufsetzen.** Billiger und sicherer, als
Konflikte in einer Datei aufzuloesen, die sich wochenlang weiterentwickelt hat:

1. Die *Absicht* des alten PR aus seinem Commit-Diff gegen die eigene Basis herausziehen
   (`commits?searchCriteria.itemVersion.version=main&searchCriteria.compareVersion.version=<branch>`,
   dann Datei-Inhalte auf Basis-Commit vs. Branch-Tip diffen). Objekt-IDs muessen **40 Zeichen**
   lang sein, sonst antwortet die API mit `ArgumentException`.
2. Aktuelle main-Fassung der betroffenen Dateien ziehen, die Aenderung frisch anwenden,
   Anker vorher per `grep -c` verifizieren (existiert der Ankertext noch? ist die Aenderung
   evtl. schon drin?).
3. Neuen Branch `<alt>-v2` per Push-API anlegen, neuen PR, Self-Approve + Auto-Complete.
4. Alten PR mit Begruendungs-Kommentar `abandoned` — nur bei EIGENEN PRs (b.dunker),
   nie bei fremden.

So gemacht bei 1732 → **1774** (gruen, gemergt) und 1537 → **1776**.

**Nebenbefund:** Ein Requeue der Build-Policy (`PATCH policy/evaluations/{id}`) hilft nur
bei echten Flakes und bei Builds gegen ein veraltetes Target. Bleibt der Build nach dem
Requeue rot, ist es ein echter Fehler — dann Log ziehen und die Ursache lesen, nicht
nochmal requeuen:
```bash
# failed record + Log-ID holen, dann gezielt den Task-Log grepppen
curl -s -H "Authorization: Basic $AUTH" \
  "https://dev.azure.com/camperfuchs/camperfuchs/_apis/build/builds/$ID/timeline?api-version=7.0"
curl -s -H "Authorization: Basic $AUTH" \
  "https://dev.azure.com/camperfuchs/camperfuchs/_apis/build/builds/$ID/logs/$LOGID?api-version=7.0" \
  | grep -nE "Tests run:.*Failures: [1-9]|TooManyInvocations|TooFewInvocations|Failed tests"
```
Der Log am `Stage`-Record ist meist leer — der brauchbare haengt am **`Task`**-Record.

## PR-Build-Pipeline reparieren (wenn `pr-build-pipeline` dauerhaft rot bleibt)

Die CI-Prüfung auf PRs läuft aus Branch `azure-pipelines`, Datei
`ci/pr-build-pipeline.yml`. Wenn ALLE PRs scheitern, muss dieses YAML per
eigenem PR auf den Branch `azure-pipelines` gefixt werden (Direct-Push = gesperrt).

**Agent-Pool-Fakten (Stand 15.06.2026):**
| Pool | Status |
|---|---|
| `macos` (ArschBook) | offline/kalt → kein Build |
| `ubuntu` (poolId=11, `camperfuchs-hostinger-agent`) | online, stabil → nutzen |
| `vmImage: ubuntu-latest` | Microsoft-hosted → in dieser Org **nicht autorisiert** |

Fix: alle drei `name: 'macos'` im YAML auf `name: 'ubuntu'` ändern.

**Maven auf ubuntu — `Maven@4` vermeiden:**
`Maven@4` setzt eine `maven`-Demand, die der ubuntu-Agent nicht erfüllt → Agent
bleibt bei „No agents found". Stattdessen plain `script:`-Step:
```yaml
variables:
  MAVEN_CACHE_FOLDER: $(Pipeline.Workspace)/.m2/repository
  MAVEN_OPTS: '-Dmaven.repo.local=$(MAVEN_CACHE_FOLDER)'

# im Backend-Stage:
- script: |
    if ! command -v mvn &> /dev/null; then
      sudo apt-get update -q && sudo apt-get install -y maven
    fi
    cd backend
    mvn -Dmaven.repo.local=$(MAVEN_CACHE_FOLDER) clean compile test
  displayName: 'Maven Build and Test'
```
Exit 127 (`mvn: command not found`) = Maven fehlt im PATH → conditional install hilft.

**YAML im Azure-Browser-Editor (Monaco API):**
```javascript
// RICHTIG:
monaco.editor.getModels()[0].setValue('<neuer YAML-Inhalt>')
// FALSCH (existiert nicht):
monaco.editor.getEditors()   // → TypeError
```
Alternativ: lokaler Worktree → Edit → `git push origin azure-pipelines`.

**`main-check-source-branch-pipeline` deaktivieren falls nötig:**
Project Settings → Repos → camperfuchs → Branch Policies → main →
Build Validation → Toggle für `main-check-source-branch-pipeline` AUS
(damit PRs auf `azure-pipelines` ohne den main-CI-Check durchkommen).

## Querverweise
- Repo-/PR-Mechanik im Detail: **camperfuchs-azure-devops** (PAT-Stand dort pflegen)
- Deploy-Kette, Approval-Gates, Hotfix/Revert, Agent-Hänger: **camperfuchs-deploy**
- Lokales Setup / Worktrees / Terminal-Loop: **camperfuchs-lokale-dev-umgebung**
- Such-/Filter-Spezifika (SearchHeader, Mobil-Sheet, Leerzustand): **camperfuchs-suchfilter**
- Arbeitsstil/Identität: **camperfuchs-basis** · Wächter-Mechanik: **camperfuchs-release-waechter** · **schedule**
- Tracking statt UI: **camperfuchs-posthog-event** · Fehler nach Deploy: **camperfuchs-sentry-incident**
