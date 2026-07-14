# Changelog â€” camperfuchs-kontext

Der hier dokumentierte Stand ist die **eine Wahrheit** fÃ¼r beide Seiten. Die aktuell gÃ¼ltige
Versionsnummer steht in `plugins/camperfuchs-kontext/.claude-plugin/plugin.json` und muss mit
dem obersten Eintrag hier Ã¼bereinstimmen. Wer eine neue Plugin-Version baut, schreibt hier einen
Eintrag dazu â€” sonst gilt die Version als nicht verÃ¶ffentlicht.

Check â€žbin ich aktuell?": installierte Plugin-Version mit dem obersten Eintrag vergleichen.

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
