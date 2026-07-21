# Changelog â€” camperfuchs-kontext

Der hier dokumentierte Stand ist die **eine Wahrheit** fÃ¼r beide Seiten. Die aktuell gÃ¼ltige
Versionsnummer steht in `plugins/camperfuchs-kontext/.claude-plugin/plugin.json` und muss mit
dem obersten Eintrag hier Ã¼bereinstimmen. Wer eine neue Plugin-Version baut, schreibt hier einen
Eintrag dazu â€” sonst gilt die Version als nicht verÃ¶ffentlicht.

Check â€žbin ich aktuell?": installierte Plugin-Version mit dem obersten Eintrag vergleichen.

---

## v0.24.0 — 2026-07-20

- `camperfuchs-legacy-backend`: Neue Pflicht-Falle „dist-Deploy ueberschreibt index.html UND alle Bundles" — nach jedem Legacy-Rollback/Deploy index.html-Diff gegen Vorgaenger-Backup + Patch-Fingerprint-Grep im Live-Bundle (Aufbereitung/Rabatt/stdPriceDiff, grep -o statt -c); Referenz-Bundle b40aa86a (16.07.); Empfehlung: bundle-feste Features als cf-booking-suggest-Addon (Beispiel cfMF Mobil-Feld inkl. Microtask-Falle beim XHR-Sniffing).

## 0.23.0 (2026-07-20)

- `camperfuchs-verfuegbarkeits-flow` auf Stand 20.07.2026: 6030776-Landkarte komplett (36 Module, Router 3 mit drei Routen NEIN/JA/RUECKFRAGE inkl. M40/M42/M44-Vorkette, M5-Picker-Hook, JA-Kundenentwurf M22 mit Zahlungsdaten + M24-Fallback, Kontaktdaten-Mail M60/M61, WhatsApp-Rueckfrage M50-M53); neue Sektion Stale-Base-Schutz (19./20.07. still geloeschte Module); Querverweise auf nein-alternativen-anfragen (6559455) und kalender-sperre; description erweitert.

## 0.22.0 - 2026-07-18

- `camperfuchs-projekt`: Runbook-Nugget "Make.com - Szenario deaktiviert (Fehler / Gift-Bundle)" ergaenzt. Ein instant-Webhook-Szenario, das an einem Modul-Fehler stoppt (BundleValidationError), schaltet sich beim Reaktivieren sofort wieder ab, solange das ausloesende Bundle in der Webhook-Queue liegt; die Queue ist NUR im UI leerbar (Show queue -> Delete), nicht ueber die Make-API. Fix: Filter/Guard vor dem strengen Modul (`text:pattern` gueltiger Regex-Operator) + client-seitiges Formular haerten. Hintergrund 18.07.2026: Newsletter-DOI 6439308 lag an `ronnymeier@gmail.com.` (Endpunkt), 50-Euro-Popup in WP-Snippet #32.

## 0.21.0 — 2026-07-18

- NEU: Skill `camperfuchs-legacy-backend` ins Plugin aufgenommen (Migration aus Account-Skill) — mit korrigierter KERN-REGEL: NIE ab Azure-`master` patchen/deployen; immer erst die Live-Datei von srv2 ziehen und mit Diff-Guard patchen. Hintergrund: gemessener Drift 18.07.2026 — 64/561 Dateien in `/backend/src` weichen zwischen master (Stand 2022) und srv2-Live (2018er-Basis + In-Place-Patches) ab; srv2-Git ist ein Remote-loses Fossil, Wahrheit = Datei auf der Platte. Zudem korrigiert: SSH auf srv2 und Azure-REST (auch Projekt `Old Camperfuchs`) gehen direkt aus der Sandbox.

## 0.20.0 — 2026-07-16

- `camperfuchs-verfuegbarkeits-flow`: Kontaktdaten-Maskierung bei Anfrage-Fahrzeugen dokumentiert (LIVE 15.07., prod-verifiziert) — Spring office-Routing (PR #1367, Marker-Zeilen), 5482694 Parser M25 + Router M27/Route B (M26 ohne Telefon/Buttons/mieter-Param, Trigger -subject:"TEST SYSTEM"), 6030776 Datastore-Fallback fuer mieter (M5/M10/M22/M60) + neue Kontaktdaten-Mail M60 nach JA. Inkl. K8s-Pending-Rollout-Falle ("Deploy gruen != neuer Code live") und Test-Rezept.

## 0.19.0 --- 15.07.2026

- **WhatsApp-Freitext von Vermietern wird klassifiziert und geroutet** (Szenario 6277699, Route 2),
  dokumentiert in `camperfuchs-verfuegbarkeits-flow`: Haiku entscheidet ja / nein / alternative /
  rueckfrage / auto_antwort / unklar. ja und nein laufen automatisch in den bestehenden
  confirm-Webhook, der Rest landet als Mail bei Bjoern, Auto-Antworten werden geschluckt.
  Vorher fielen Freitext-Antworten still auf den Boden (Fall ginbie: 9 Tage).
- Neue Fallen: `toJSON` existiert in Make NICHT (Escaping nur ueber `json:CreateJSON` +
  Datenstruktur), String-Zahlen im CreateJSON-Mapper geben Anthropic-400, der WhatsApp-Hook ist
  `web-shared` und hat keine URL (nur mit echter Nachricht testbar).
- `camperfuchs-kalender-sperre`: Stufe B ist nicht mehr offen, Verweis gesetzt.

## 0.18.0 --- 15.07.2026

- **`camperfuchs-plugin-sync`: Lock-Rezept gegen Parallel-Sessions.** Vor dem Bauen wird
  `PLUGIN-LOCK.md` im Repo-Wurzelverzeichnis angelegt und gepusht. Weil `git push` atomar ist,
  gewinnt genau eine Session; die andere bekommt eine Ablehnung und stoppt, statt blind
  weiterzubauen. Lock juenger als 30 min = andere Session arbeitet, STOPP. Aelter = Leiche,
  uebernehmen. Freigabe passiert im selben Commit wie die Version (`git rm PLUGIN-LOCK.md`).
  Dieses Rezept wurde beim Bauen von 0.18.0 selbst benutzt.
- Hintergrund: am 15.07. gab es an einem Abend zweimal 0.14.0 und zweimal 0.15.0, und einmal ist
  eine fertige Skill still aus dem ausgelieferten Paket gefallen. Die Soll-Ist-Pruefung aus 0.16.0
  faengt den Schaden, der Lock verhindert ihn.

## 0.17.0 (2026-07-15)

- Neue Skill `camperfuchs-memory-aufraeumen`: Orphan-Triage, MEMORY.md-Kompaktierung (SUBINDEX-Muster) und sync-festes _archiv-Rezept fuer die Memory-Spaces (cf-shared-memory-sync stellt Geloeschtes wieder her, sieht aber keine Unterordner).

## 0.16.0 --- 15.07.2026

- ⚠️ **Reparatur: `camperfuchs-alternativ-angebot` war im 0.15.0-Paket gar nicht enthalten.** Die
  Skill wurde in einer parallelen Session gebaut und gepusht (Commit 228e6fc, Quellbaum ok), eine
  zweite Session baute danach das `.plugin` aus einem Baum ohne sie und überschrieb gleichzeitig
  deren Changelog-Eintrag. Quellbaum 11 Skills, Paket 10, kein Fehler, keine Warnung. Ab jetzt im
  Paket. Wer 0.15.0 installiert hat: bitte auf 0.16.0 aktualisieren.
- **`camperfuchs-plugin-sync`: neue Pflichtregel „Parallele Sessions".** Vor jedem Bauen `git fetch`
  + `git log HEAD..origin/main`, Version erst DANACH bestimmen, und Soll-Ist der Skill-Zahl
  vergleichen (Ordner im Quellbaum vs. `skills/*/SKILL.md` im gebauten `.plugin`). Fremden
  Changelog-Eintrag gleicher Nummer nie überschreiben, sondern die nächste Nummer nehmen.
  Björn lässt mehrere Sessions parallel laufen, alle committen als `b.dunker` — heute gab es
  deshalb zweimal 0.14.0 und zweimal 0.15.0.
- **`camperfuchs-plugin-sync`: Auto-Memory-Sync ergänzt.** `cf-shared-memory-sync` gleicht Björns
  Memory-Dateien alle 6h über drei Spaces ab, bewusst ohne Löschen. Eine Memory-Datei zu löschen
  bringt daher nichts (kommt zurück), sie mit einem Stub zu überschreiben zerstört den Inhalt in
  den anderen Spaces. Aufräumen läuft über den Index, nicht über die Dateien.

## 0.15.0 (15.07.2026)

- **`camperfuchs-plugin-sync` auf den REST-Weg umgeschrieben.** Veroeffentlichen laeuft jetzt
  komplett browserlos aus der Sandbox per Azure-REST: kein Windows, kein `F:`, kein PowerShell,
  kein Desktop Commander. Damit entfallen die halbe Fallensammlung (BOM durch
  `Set-Content`, Backslash-Pfade durch `Compress-Archive`, `$`-Verlust in PS-Einzeilern,
  CRLF-Flut bei `git add -A`, veraltete Mount-Staende) — sie stehen nur noch als Notfall-Anhang
  drin, falls doch jemand ueber den Klon arbeitet.
- Neue Falle dokumentiert: `while read` verschluckt die letzte Zeile ohne Zeilenumbruch. Beim
  Ziehen des Plugin-Baums fehlte dadurch fast `wp-502-debug/SKILL.md` — ein Push haette die
  Skill still aus dem Plugin geloescht. Deshalb Pflicht: Soll-Ist der Dateizahl vergleichen.
- Ebenfalls dokumentiert: der Secret-Scan schlaegt immer in dieser Skill an, weil sie die
  Suchmuster selbst auflistet. Fehlalarm, nicht blind Alarm schlagen.

## 0.14.0 (15.07.2026)

- **Neu: `camperfuchs-kalender-sperre`.** Sagt ein Vermieter auf eine Mietanfrage NEIN, kann er
  den Zeitraum jetzt auf der Danke-Seite per Klick selbst im Kalender sperren
  (Make 6578305 -> key-gated `/api/automation/block` auf srv2). Bewusst mit Klick statt
  Automatik, weil ein NEIN nicht zwingend "belegt" heisst.
- Enthaelt die Legacy-Fakten, die uns Stunden gekostet haben: `domainAdmin` ist fuer Camperfuchs
  eine Sackgasse (`stations.domain` ist bei 3.553 Stationen NULL), `articles.id` ist varchar und
  identisch mit den IDs der neuen Such-API, Sperre = Buchung mit `type = 6`.
- Make-Fallen: `builtin:Ignore` als onerror beendet die ganze Route (auch den `WebhookRespond`),
  Router-Fallback-Routen brauchen einen eigenen Filter, und Fahrzeug-Titel per
  `split(...; " [https")` schneiden statt per Regex.

## 0.13.0 --- 14.07.2026

- **`camperfuchs-projekt`: Image-Tags sind jetzt pro Umgebung getrennt (PR #1365).** staging und
  prod pushten bis dahin BEIDE den Tag `<repo>:<SHA>` in denselben Cluster -> der spaetere Build
  ueberschrieb das Image des frueheren, Nodes mit gecachtem Image zogen nicht neu -> prod lief auf
  zwei Images unter einem Tag, die Next-`buildId` flippte, Chunks gingen sporadisch ins 404.
  Passiert am 07.07. und erneut am 14.07. Jetzt: `-staging` / `-prod`-Suffix, verifiziert ueber
  zwei aufeinanderfolgende Deploys (buildId stabil ohne Eingriff).
- **Zwei teuer bezahlte Fehldiagnosen dokumentiert:** (1) "zwei Builds desselben Commits sind die
  Ursache" -- nein, es flippte auch bei nur EINEM prod-Build. (2) `kubectl rollout restart`
  konvergiert -- nein, die Nodes cachen den Tag; nur ein Digest-Pin half.
- **Deploy-Diagnose-Tell ergaenzt:** buildId zaehlen statt Code verdaechtigen; Pod-Drift zeigt sich
  nur an `imageID` (Digest), nicht am Tag. Ausserdem: Azure nimmt die `ci/*.yml` aus dem Branch,
  der gebaut wird -- Pipeline-Fixes wirken erst, wenn sie im jeweiligen Branch liegen.
- **HPA-Fakt ergaenzt:** frontend/backend haben eine HPA (min 2, max 4, Ziel 80% CPU).
  `replicaCount` im Chart ist nur der Startwert; ein nach dem Deploy kurz haengender
  `Pending`-Pod ist Scale-Up-Nachwehen, kein Defekt.

---
## 0.12.1 â€” 14.07.2026

- **BOM- und Validierungs-Fallen in `camperfuchs-plugin-sync` dokumentiert** â€” beide haben die
  Installation von 0.12.0 real scheitern lassen: PowerShells `Set-Content -Encoding UTF8` schreibt
  ein BOM (macht `plugin.json` ungueltig und die erste `.gitignore`-Regel unwirksam), und der
  Installer prueft ALLE Skills, nicht nur die geaenderten (hier kippte eine 1262-Zeichen-
  description von `nein-alternativen-anfragen`).
- **Neuer Pflichtschritt 4b:** vor dem Veroeffentlichen jede SKILL.md mit einem echten YAML-Parser
  pruefen (Laenge, Frontmatter, BOM) â€” nicht per Regex; eigene Regex-Checks lieferten Fehlalarme.
- **Mount-Cache-Falle ergaenzt:** die Sandbox kann eine veraltete Datei zeigen, waehrend Windows
  die korrekte hat. Windows ist massgeblich; frischer Dateiname umgeht den Cache.

---
## 0.12.0 â€” 14.07.2026

- **`camperfuchs-plugin-sync` ins Plugin migriert und geradegezogen.** Er beschrieb noch den
  obsoleten Browser-Upload-Weg (â€žUpload file(s)"), nannte eine falsche lokale Kopie und kannte
  2 von inzwischen 9 Skills. Jetzt: git-Klon `F:\dev\cf-marketplace` + SSH-Push als echter Loop.
- **Packen jetzt nativ mit `tar.exe`** (verifiziert: 0 Backslash-Pfade, `plugin.json` oben).
  Die alte Regel â€žnur in der Sandbox zippen" ist Ã¼berholt â€” sie galt nur gegen
  `Compress-Archive` / .NET `ZipFile`, die die ZIP-Spec verletzen.
- **Neue Sperrvermerke:** git lÃ¤uft NICHT auf dem gemounteten Projektordner (`config.lock:
  Operation not permitted`) â†’ ein Repo kann dort nie liegen; Zip auf dem Mount wird kaputt und
  `du -h` meldet dort fÃ¤lschlich 0; kein Python auf dem Rechner (nur Store-Aliase);
  PowerShell-Einzeiler Ã¼ber DC verlieren `# Changelog â€” camperfuchs-kontext

Der hier dokumentierte Stand ist die **eine Wahrheit** fÃ¼r beide Seiten. Die aktuell gÃ¼ltige
Versionsnummer steht in `plugins/camperfuchs-kontext/.claude-plugin/plugin.json` und muss mit
dem obersten Eintrag hier Ã¼bereinstimmen. Wer eine neue Plugin-Version baut, schreibt hier einen
Eintrag dazu â€” sonst gilt die Version als nicht verÃ¶ffentlicht.

Check â€žbin ich aktuell?": installierte Plugin-Version mit dem obersten Eintrag vergleichen.

-Variablen â†’ `.ps1` nutzen.
- Abgrenzung ergÃ¤nzt: das private Archiv `cf-wissen` gehÃ¶rt **nie** in dieses geteilte Repo.

---
## 0.11.0 â€” 14.07.2026

- **Neue Skill `camperfuchs-sammelanfrage`** ins Plugin aufgenommen: System-Landkarte der
  Sammelanfrage + des Merkzettels (MerkzettelContext/localStorage `cf_merkzettel_v1`,
  `sammelanfrage.tsx`, `BookingCalculator` mit `merkMode`, Detailseite `?merk=1&merkLoc=`,
  Backend `fare` + `bookings/group`), Datenmodell, Endpoints und der â€žWeg 2"-Flow (eigener
  Reisezeitraum + Zubehoer JE Fahrzeug, live prod seit 08.07.2026, Merge `672680b5`).
- **Teuer gelernte Fallen dokumentiert:** `update()` ist auf `article`+`articleLocation` gekeyt â€”
  ein falsches/erfundenes `merkLoc` schreibt still nichts zurueck und sieht aus wie â€žRueckweg
  kaputt"; `extras` speichert Zubehoer-**Namen**, die Checkboxen nutzen `index` (beide Seiten
  anfassen); `/sammelanfrage` per Direkt-URL haengt/404t (separate, vorbestehende Routing-Luecke,
  nicht Weg 2 â€” in-app navigieren); zwei `BookingCalculator`-Instanzen (Desktop + Mobile).
- **Browser-Verifikations-Fallen ergaenzt:** Screenshots timen auf den Fahrzeug-Detailseiten aus
  (CDP 30 s) â†’ `get_page_text` nutzen; `read_page filter:interactive` verschluckt Elemente, die im
  Seitentext stehen; Sticky-Sidebar braucht `scroll_to {ref}`; Mobile-Optik ist nicht simulierbar
  (`resize_window` aendert `innerWidth` nicht).

---

## 0.10.0 â€” 09.07.2026

- **Neue Skill `camperfuchs-frontend-feature-shippen`** ins Plugin aufgenommen (Idee â†’ live:
  richtige Komponente finden, Worktree off `origin/main`, PR-/Deploy-Kette, Verifikation).
- **Schritt 5 korrigiert (teuer gelernt 09.07.):** Der Live-Beleg per JS-Bundle-Fingerprint muss
  die Chunks Ã¼ber `/_next/static/<buildId>/_buildManifest.js` enumerieren. Seit PR #1303
  (`perf/code-split-datepicker`) werden Datepicker/BookingCalculator lazy nachgeladen und stehen
  NICHT im initialen HTML â€” wer nur das HTML scannt, schlieÃŸt fÃ¤lschlich â€žFix nicht live".
  ErgÃ¤nzt: i18n-Keys sind kein Komponenten-Marker, taugliche vs. untaugliche Fingerprints,
  â€žQuelle schlÃ¤gt Bundle", PowerShell-Fallen (`$`-Stripping, `-LiteralPath`, abgeschnittene Ausgabe).
- **Repo-Struktur repariert:** Der vollstÃ¤ndige Quellbaum (`plugins/`, `.claude-plugin/`) liegt jetzt
  im Azure-Repo. Vorher lagen dort nur flache Dateien (Browser-Upload konnte keine Unterordner) â€”
  dadurch waren die Versionen **0.7.0â€“0.9.0 nie verÃ¶ffentlicht**; mit diesem Stand nachgezogen.
- **Pflege kÃ¼nftig per `git push` (SSH)** statt Browser-Upload â†’ `quellbaum.zip`-KrÃ¼cke entfÃ¤llt.

## 0.9.0 â€” 23.06.2026

- `camperfuchs-verfuegbarkeits-flow`: **RÃ¼ckfrage hat jetzt ein Freitext-Formular** (Modul 30, live 23.06.). Klickt der Vermieter â€žRÃ¼ckfrage", kommt statt der reinen BestÃ¤tigungsseite eine Formularseite (CF-Palette) mit Textfeld â€žDeine Frage oder Anmerkung" â†’ neuer Webhook-Param `frage`; Modul 7 (BjÃ¶rn-Info-Mail) zeigt den Text im Beige-Block. Router 11 jetzt VIER Routen (Modul 12 nur noch JA via Zusatz-Filter `aktion notequal rueckfrage`; Modul 30 = `aktion equal rueckfrage`). JA/NEIN unverÃ¤ndert. Doku: neue Sektion â€žRÃ¼ckfrage-Formular: Modul 30", Params- und Aufgaben-Liste ergÃ¤nzt.

## 0.8.0 â€” 16.06.2026

- `camperfuchs-projekt`: Stand-Updates seit 03.06. nachgezogen â€” Origin-TLS jetzt DNS-01/Cloudflare-renewt + CF-SSL "Full (strict)" (14.06.); Backend `max-http-header-size` 64KB gegen `/api/V1/articles` HTTP-400 "Suche nicht geladen" (#816, 16.06.); Consent vereinheitlicht (11.06.) + funktionierender SPC-Cache-Purge per REST `POST /wp-json/spc/v1/cache/purge`; Cache Reserve als 3. Ebene; prod-Gate min=1 (BjÃ¶rn allein freigabefÃ¤hig); new.camperfuchs.de = neue Homepage (WP/Kadence); /de-Routing-Backlog #533-545 live + Sitemap-lowercase-Restproblem; lokale Dev-Umgebung F:\dev\camperfuchs.

## 0.7.0 â€” 15.06.2026

- `camperfuchs-verfuegbarkeits-flow`: NEIN-**Modul 20 ist jetzt ein Fahrzeug-Picker** (Variante B
  LIVE) â€” lÃ¤dt die freien Fahrzeuge des Vermieters per `GET /api/V1/articles/by-landlord?email=`
  als antippbare Radio-Liste (inkl. Kennzeichen hinter dem Namen). Die frÃ¼here Notiz â€žVariante B
  nicht mÃ¶glich / nur Freitext" wurde entfernt.
- Neues **Backend-Muster** dokumentiert: ein vermieter-eigenes Zusatzfeld NUR in `by-landlord`
  ausliefern â€” Feld in `ArticleOverviewVM` mit field-level `@JsonInclude(NON_NULL)`, NICHT in
  `from()` setzen, nur in `findArticlesByLandlordEmail` anreichern (`enrichWithLicensePlate`) â†’
  Ã¶ffentliche `/api/V1/articles`-Suche bleibt ohne das Feld. Inkl. Kennzeichen-Beispiel (PR #788),
  Spaltennamen-Falle (`licensePlateNumber`â†’`number_plate`, `deactivated`â†’`deleted`) und
  Datenschutz-Hinweis (by-landlord ist Ã¶ffentlich/ohne Login â†’ Feld per E-Mail abfragbar).

## 0.6.0 â€” 15.06.2026

- `camperfuchs-verfuegbarkeits-flow`: **NEIN-Pfad bietet jetzt optional Alternativ-Zeitraum +
  Alternativ-Fahrzeug an.** Router 11 in 6030776 hat DREI Routen â€” neue Modul-20-Formular-Seite
  bei `aktion=nein` (zwei optionale Freitextfelder â†’ `alt_zeitraum`/`alt_fahrzeug` per
  GET-Formular zurÃ¼ck an den Hook), Modul 12 (Button-Seite) auf `aktionâ‰ nein` verengt.
  Mieter-Entwurf (M10) baut die Alternative Ã¼ber zwei `if()`-Fragmente ein (leerer String =
  falsy â†’ kein hÃ¤ngender Satz), bleibt Entwurf; BjÃ¶rn-Info (M5) zeigt die Alternative. Variante B
  (Vermieter wÃ¤hlt eigene Fahrzeuge) bewusst verworfen â€” `/api/V1/articles` kennt keinen
  Vermieter, brÃ¤uchte Backend-Endpoint.
- Gelernt + dokumentiert: der Make-**Hook** ist aus der Sandbox per `curl` testbar (Test-Rezept
  headless ohne Chrome); `scenarios_run`-`data` mappt NICHT auf Webhook-Felder; riesige
  Mapper-Strings (M10-Signatur) nie von Hand neu tippen â†’ Python-Edit auf Rohtext + Token-Reread.

## 0.5.0 â€” 08.06.2026

- Neuer Skill `camperfuchs-verfuegbarkeits-flow`: Betrieb/Ã„nderung/Troubleshooting des
  Vermieter-VerfÃ¼gbarkeits-Flows (Make 5482694 + 6030776) â€” System-Landkarte (alle IDs),
  zweistufiger Scanner-Schutz, Antwort-Tracking (Datastore 131528), Mieter-Entwurf bei NEIN,
  Test-Rezepte und Gotchas.
- Neu darin: **Fahrzeug-Link + Telefon als Info-Buttons** in der VerfÃ¼gbarkeits-Mail (M2).
  Fahrzeug-URL wird OHNE Regex-Ã„nderung im Mapper aus `{{7.fahrzeug}}` (Format â€žName [URL]")
  gezogen (`split/first/trim` + `if/contains/replace/last`, Fallback Homepage) â†’ kein
  Parser-Risiko. Plus Schema-Falle dokumentiert: `validate_blueprint_schema` lehnt top-level
  `scheduling`/`interface` ab â†’ vor validate/update strippen (Blueprint = name/flow/metadata).

## 0.4.0 â€” 07.06.2026

- Neuer Skill `camperfuchs-agent-readiness`: prÃ¼ft die KI-/Agenten-Auffindbarkeit von
  camperfuchs.de (Markdown for Agents, Link-Headerâ†’llms.txt, llms.txt) per curl und
  triagiert die Agent-Discovery-Standards (OAuth/OIDC, MCP-Server-Card, ACP, x402,
  DNS-AID, WebMCP, API-Catalog) nach ECHTEM Nutzen â€” statt blind isitagentready-Haken zu jagen.
- Merksatz verankert: Stubs ohne echtes Backend sind schÃ¤dlich (Agent versuchtâ†’scheitertâ†’Seite
  wirkt kaputt); isitagentready-â€žoperation was aborted" = Checker-Timeout, kein echtes Loch.

## 0.3.0 â€” 07.06.2026

- Neuer Skill `camperfuchs-cache-purge`: gezielter Cloudflare-Edge-Purge fÃ¼r
  camperfuchs.de (Skript `scripts/cf_purge.sh` â€” einzelne URLs, mehrere, oder `--all`,
  automatische 30er-BlÃ¶cke). LÃ¶st das Edge-Layer-Propagationsproblem (APO `s-maxage` 1 Jahr).
- **Standing Rule** im Skill verankert: nach JEDEM selbst ausgelÃ¶sten WP-API-Content-Edit
  die betroffene URL sofort
