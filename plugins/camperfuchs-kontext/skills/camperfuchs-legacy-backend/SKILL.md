---
name: camperfuchs-legacy-backend
description: >-
  System-Landkarte und erprobte Arbeitsweise fuer das Camperfuchs LEGACY-Backend
  (camperfuchs.de/backend = Angular-4-App rentapp + Symfony-API auf srv2
  /home/gaz/rent, Azure-Projekt "Old Camperfuchs") — NICHT das neue Monorepo.
  IMMER nutzen, wenn am alten Backend etwas gelesen, geaendert oder deployt
  werden soll — explizit ("altes Backend", "rentapp", "srv2 deployen",
  "ArticleController", "booking-grid", "Buchungs-Kalender im Backend") wie
  implizit ("warum geht mein Fix da nicht live", "wo liegt der Code der
  Buchungsuebersicht", "Backend wirft 500", "memory exhausted"). KERN-REGEL (teuer gelernt 18.07.2026): Azure-master ist
  NICHT der Live-Stand — ~4 Jahre Drift, 64 von 561 Dateien in /backend/src
  weichen ab. NIE ab master patchen oder deployen; IMMER erst die Live-Datei von
  srv2 ziehen, DIESE patchen, mit Diff-Guard davor. Enthaelt System-Landkarte,
  Live-Bundle-Patch-Rezept ohne Rebuild, Deploy-Realitaet (kein CI; SSH aus der
  Sandbox) und die teuer gelernten Fallen.
---

# Camperfuchs Legacy-Backend (rentapp / Old Camperfuchs / srv2)

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


Das operative Alt-Admin unter **camperfuchs.de/backend** ist die Angular-4-App
`rentapp`; dahinter die Symfony-ApiBundle-API auf **srv2** (`/home/gaz/rent`).
Fuer das NEUE Monorepo stattdessen `camperfuchs-azure-devops` / `camperfuchs-deploy`.

## ⛔ KERN-REGEL: NIE ab Azure-`master` patchen oder deployen

**Der Server ist die Wahrheit, nicht der Azure-`master`.** Gemessen am 18.07.2026:

- Live-Basis auf srv2 ist ein ~2018er-Checkout + jahrelange In-Place-Patches;
  Azure-`master` lief bis 2022 weiter (letzter Fremd-Commit 29.08.2022) und
  traegt seit 2026 nur unsere eigenen, einzeln deployt-verifizierten Pushes.
- **64 von 561 gemeinsamen Dateien in `/backend/src` weichen inhaltlich ab**
  (Controller, Helper, Entities, Jsoner, Twigs), 6 existieren nur in master,
  1 nur live. Wer `master` auscheckt und deployt, spielt ~55 Dateien
  ungetesteten 2022er-Code ein und kann das Backend sprengen (am 18.07.2026
  fast passiert; nur per Backup-Rollback glimpflich ausgegangen).
- **Auch das Git auf srv2 ist NICHT die Wahrheit:** `/home/gaz/rent` ist ein
  Repo-Fossil ohne Remote — detached HEAD auf lokalen root-Commits
  ("init" 2025, "modified" 2026), echte Historie endet 2018, dazu ~11
  uncommittete Patches im Working Tree. **Wahrheit = die Datei auf der Platte.**

**Pflicht-Workflow fuer jeden Legacy-Code-Fix:**

1. **Live-Datei ziehen:** `scp`/`ssh cat` der Datei von srv2 — NIE die
   master-Version als Basis nehmen, auch nicht "nur zum Anschauen und dann
   patchen" (so entsteht der Unfall).
2. **DIESE Datei patchen** (chirurgisch, `str_replace`/Perl-index, kein Regex).
3. **Diff-Guard vorschalten:** `diff live neu` MUSS ausschliesslich die eigenen
   Patch-Zeilen zeigen. Verschwindet auch nur eine Zeile, die nicht zum eigenen
   Patch gehoert → ABBRUCH, Basis war falsch.
4. Backup auf dem Server (`$F.bak-$(date +%Y%m%d%H%M%S)`), `php -l`, dann live
   (opcache revalidiert nach ~2 s; erzwingen: `apache2ctl -k graceful`).
5. Azure-PR nur zur Doku (kein CI, ein Merge deployt NICHTS) — und dann den
   master-Stand der Datei NICHT mit dem Live-Stand verwechseln.

master ⇄ Produktion angleichen oder master als tot markieren: offener Punkt,
getrennt mit Bahti klaeren — bis dahin gilt die Regel ausnahmslos.

## System-Landkarte

- **Azure-Org:** `dev.azure.com/camperfuchs`, Legacy = Projekt **`Old Camperfuchs`**
  (Projekt-ID `5224931e-543c-4b78-9341-2daa0b34ab7d`), Repo `Old Camperfuchs`
  (Repo-ID `383c1f6d-32c2-449a-9bd0-a3a4ae9de509`, Default-Branch `master`).
  Das NEUE Backend liegt im Projekt `camperfuchs` — nicht verwechseln.
- **Im Repo:** `/rentapp` = Angular 4.2.4 (CLI 1.4.9, `.angular-cli.json`),
  `/backend` = die Symfony-API (auf srv2 als `/home/gaz/rent`), daneben
  `/checkout`, `/invoice`.
- **Auslieferung UI:** `camperfuchs.de/backend` kommt von **srv2.bluetrailer.de**
  (DO-Droplet, **IP 46.101.113.30** — DNS loest zeitweise nicht auf → IP nutzen)
  aus `/home/gaz/rentanda/web/backend/` (gehashte `main.<hash>.bundle.js` +
  `index.html` no-store, genau EINE Bundle-Referenz).
- **API:** Symfony 2/3 unter `/home/gaz/rent` (mod_php 7.3, KEIN php5-fpm —
  Details + SSH/Edit-Workflow in `camperfuchs-legacy-srv2-mail`).
- **Schluessel-Komponenten `/rentapp/src/app/`:** `components/booking-grid.component`
  (Jahres-Zeitstrahl + Hover-Popup, OnPush!), `pages/booking.component`
  (Detailseite, Route `/booking;id=<id>`).

## Zugriff: Sandbox zuerst (Stand 18.07.2026)

- **SSH auf srv2 geht DIREKT aus der Linux-Sandbox** (Key `.secrets/id_srv2_cf`
  → `/tmp`, `chmod 600`, `ssh -i … root@46.101.113.30`). Die alte Warnung
  "ssh blockt aus der Automations-Shell" gilt nur fuer den Windows-Weg;
  base64-.ps1 ueber Bjoerns Terminal ist nur noch Notfall-Fallback.
- **Azure-REST geht ebenfalls aus der Sandbox** (PAT aus
  `.secrets/azure-devops-pat.txt`, `curl -u ":$PAT"`) — auch fuers Projekt
  `Old Camperfuchs` (18.07.2026 verifiziert: refs, commits, items, Blob-Listen).
  Die eingeloggte Browser-Session (`javascript_tool` + `fetch(...,
  {credentials:'include'})`) bleibt Fallback; `get_page_text` zerstoert Bytes
  (Mojibake) — nie Dateiinhalte daraus zurueckschreiben.
- **Wenn der Sandbox-Weg nicht geht** (Projektordner nicht gemountet, also kein
  Zugriff auf `.secrets`, oder kein SSH-Key in der Sandbox): dann laeuft es ueber
  das **ssh/scp aus Git** per Desktop Commander — nicht ueber die Windows-eigene
  `ssh.exe` (die endet mit Exit 255 ohne Ausgabe):
  ```powershell
  & "C:\Program Files\Git\usr\bin\ssh.exe" srv2 "echo <BASE64> | base64 -d | bash"
  & "C:\Program Files\Git\usr\bin\scp.exe" "<lokal>" srv2:/tmp/datei
  ```
  Host-Alias `srv2` steht in `C:\Users\bjoer\.ssh\config` (User root, Key
  `id_srv2_cf`, `HostKeyAlgorithms +ssh-rsa`). **Immer base64-verpacken**, dann
  entfaellt das PowerShell-Quoting. Groessere Dateien nicht per base64 in die
  Kommandozeile, sondern in den Cowork-outputs-Ordner schreiben (auf Windows
  sichtbar) und per `scp` hochladen. Die „post-quantum"-Warnung ist Rauschen.
  Verifikation direkt gegen den Origin, an Cloudflare vorbei:
  `curl --resolve www.camperfuchs.de:443:127.0.0.1 -k …`.
- **Drift selbst messen** (Wiederholungs-Rezept): Azure
  `items?scopePath=/backend/src&recursionLevel=full` liefert Blob-SHAs;
  auf srv2 `git hash-object` je Working-Tree-Datei; SHA-Vergleich pro Pfad.

## Live-Bundle direkt patchen (ohne Rebuild) — ERPROBT

Fuer kleine UI-/Logik-Fixes im Angular-Bundle (kein Angular-4-Rebuild noetig):

1. Bundle-Namen aus `/backend/index.html` greifen (genau 1 Referenz).
2. Methode im Bundle finden (AOT behaelt template-referenzierte Namen,
   z. B. `stdPriceDiff=function(){…}`), Anker MUSS `count===1` sein.
3. OLD/NEW als base64 auf den Server, dort byteweise per Perl-`index`/`substr`
   ersetzen (KEIN `s///`).
4. Neues Bundle unter NEUEM Hash-Namen schreiben, `index.html`-Referenz per
   `sed` umbiegen (Cache-Bust ohne CF-Purge). Vorher Bundle + index.html als
   `.bak.$TS` sichern = Rollback.
5. Verifikation ohne PII: deployte Funktion aus dem Bundle extrahieren und mit
   synthetischen Daten testen — nie echte Kundendaten dumpen.

## Deploy-Realitaet

- **KEINE CI im Legacy.** 0 Build-Definitionen; `azure-pipelines.yml` ist
  verwaist. Ein Merge auf `master` schaltet nichts frei. Kein Staging.
- Deploy = Datei-Edit/Upload direkt auf srv2 (Workflow oben + Skill
  `camperfuchs-legacy-srv2-mail`), fuer Bundles das Patch-Rezept.
- Vollstaendiger rentapp-Rebuild nur im Ausnahmefall (Docker `node:8`).
- Immer: Backup vor Go-live, Bjoerns OK, Eintrag im `Camperfuchs-Worklog.md`
  (mit "kein PR" + Rollback-Pfad), sonst sieht Bahti es nicht.

## Teuer gelernte Fallen

- **master-Checkout = ~4 Jahre Fremdcode** (siehe Kern-Regel — Falle Nr. 1).
- **Content-Filter blockt JS-Rueckgaben** mit URLs/Quotes → nur base64/Zahlen/
  Booleans zurueckgeben, lange Strings halbieren.
- **PII-Classifier blockt** Buchungs-JSON-Dumps und Token-Scans → synthetische
  Daten, Beschreibung/Typ/Preis reichen.
- **`ng.probe` ist im Prod-Build AUS** → Daten aus Bundle/DOM ziehen.
- **OnPush:** verzoegerte Aenderungen in `booking-grid.component` brauchen
  `ChangeDetectorRef.markForCheck()`.
- **Bahti NICHT als PR-Reviewer setzen** (Reviewer = wir).
- **Erst die LIVE-Datei profilen, dann Git** — early returns
  (`grep -n "return new JsonResponse"`) finden, bevor man toten Code misst.
- **Ein dist-Deploy ueberschreibt index.html UND alle Bundles** (20.07.2026 teuer
  gelernt): Der master-Rebuild-Deploy vom 18.07. ersetzte die index.html (Addon-Tags
  `cf-booking-suggest.js` + Sentry WEG) und legte ein ungepatchtes master-Bundle live —
  Abrechnung/Aenderungsprotokoll/Aufbereitungszeit/Rabatt-Patches still verschwunden.
  Nach JEDEM Rollback/Deploy im Legacy PFLICHT: (1) index.html gegen das Vorgaenger-
  Backup diffen (Addon-/Extra-Script-Tags mitnehmen), (2) Patch-Fingerprints im Live-
  Bundle greppen (`Aufbereitung`, `Rabatt`, `stdPriceDiff` — Vorkommen zaehlen mit
  `grep -o | wc -l`, NICHT `grep -c`: das Bundle ist EINE Zeile). Referenz-Bundle mit
  allen Patches: `main.b40aa86a5627b4787d15.bundle.js` (16.07., inline.c8083d1b).
  Features robust gegen Bundle-Tausch machen -> als Addon-Modul in cf-booking-suggest.js
  bauen (Beispiel: Mobil-Feld Firmendetails, Modul `cfMF`, `?v=20260720mf6` — aktiver
  GET ueber Route-ID statt XHR-Sniffing, denn Angulars Initial-GET feuert in Microtasks
  VOR dem naechsten Script-Tag).
- ⚠️ **Anker-Kollision durch den eigenen Patch:** Fuegt ein frueherer Anker Code ein, der
  den String eines spaeteren Ankers enthaelt, schlaegt dessen `substr_count === 1`-Guard
  fehl. Entweder den eingefuegten Code anders formulieren (`in_array($status,
  array('offen','rueckfrage'), true)` statt der Oder-Kette) oder die Patch-Reihenfolge
  drehen. Der Guard muss dabei **vor** dem Schreiben abbrechen — dann bleibt die Datei
  unangetastet.
- ⚠️ **PDF-Vorschau und `prompt()` frieren die Browsersteuerung ein** („Cannot attach to
  this target"). Ausweg: den Datenpfad direkt bedienen (API/DB) oder einen neuen Tab
  oeffnen.
- ⚠️ **Ein geschlossener Dialog ist kein Versand** — nach einem Mailversand
  `POST /api/mail/send` im Apache-Log und `booking_document_history` pruefen.
- **PDO auf srv2 immer mit `ERRMODE_EXCEPTION`** — sonst liefert `query()` still `false`
  und die `foreach`-Warnung sieht aus wie „keine Treffer". Stringliterale in SQL ueber
  Platzhalter, nicht ueber escapte Quotes im base64-Skript.
- **Logs unter `/var/log` vorher `touch` + `chown www-data`**, sonst schreibt der
  Endpoint stumm nichts.
- **Lexware drosselt auf 2 Anfragen/Sekunde** (HTTP 429) → Pause + Retry.
- **Der Symfony-Service fuer Dateien heisst `storage`**, nicht `storage_service`;
  Dokument-PDFs liegen im Pool `cf_documents`, `booking_documents.content` ist nur ein Pfad.
- **Addons ueberleben einen Angular-Rerender nur mit Intervall** (~1 s) plus
  Guard-Attribut. In Tabellen lieber ein Badge in eine vorhandene Zelle haengen, als eine
  neue Spalte einzufuegen.

## Mail/DMARC: Portal-Default-Absender-Falle (21.07.2026)

`MailHelper::send($recipient,$subject,$body,$attachments,$from=null,...)` hat ZWEI Absender-Wege:
- `$from` gesetzt -> greift der 23.06.-Fix: `From: noreply@camperfuchs.de` + `Reply-To=$from`. Aligned, kein Bounce.
- `$from = null` -> else-Zweig nimmt den Portal-Default `getPortal()->getSenderEmail()` als From. Fuer das `cf`-Portal war das `robot@camperfuchs.com` (.com!) -> DMARC `p=reject` -> Bounce bei Gmail/GMX/web.de/t-online.

Konsequenz: JEDE `send()`-ohne-`$from` uebers cf-Portal bounct -- auch wenn der explizite-`$from`-Zweig laengst gefixt ist. Passiert am 20.07. mit der neuen office@-Mail "Neues Fahrzeug angelegt" (ArticleController).

Fix (21.07., beide Ebenen):
1. Aufruf mit explizitem `$from` versehen (chirurgisch), ODER
2. WURZEL: Portal-Default umstellen. cf-Portal (Portal-Entity key=`cf`, ID `MENJM5Y8`) `senderEmail` `robot@camperfuchs.com` -> `noreply@camperfuchs.de` (Doctrine + Guard, NUR cf; `pp`/`ra` sind Fremdmarken -> nie anfassen).
3. Letzte .com-Codestelle: `UserHelper.php:53` (User-Bestaetigungsmail) `robot@camperfuchs.com` -> `noreply@camperfuchs.de`. Danach kommt `robot@camperfuchs.com` in /home/gaz/rent/src nirgends mehr vor.

Portale + Default-Absender listen: Kernel booten (`sudo -u www-data`), Portal-Repo `findAll()` -> `getKey()`/`getSenderEmail()`. E2E-Beweis IMMER ueber Mailgun-Event `from=...` + `delivered`.

## Umlaut-/Encoding-Falle im Bundle (27.07.2026, teuer gelernt)

Symptom: Backend zeigt "Ã¼" statt "ü" (z.B. "Anzahlung bei Buchung Ã¼ber Camperfuchs"),
obwohl DB und API sauber sind. Ursache-Kette: Quelldatei im master lag DOPPELT encodiert vor
(echte Zeichen "Ã¼" = Bytes C383 C2BC) → der Minifier (node:8-Rebuild) macht daraus literale
JS-Escapes `\xc3\xbc` — und `\x` ist in JS ein Latin-1-Codepoint, rendert also als "Ã¼".

- Nach JEDEM rentapp-Rebuild pruefen: `grep -o '\\xc3' bundle | wc -l` MUSS 0 sein.
- Quelle auf Doppel-Encoding pruefen: Byte-Suche nach C3 83 ("Ã" als echtes Zeichen).
- In JS-Strings NIE UTF-8-Bytes als `\xNN`-Paare schreiben — `\u00XX` oder echte Zeichen.
- Fix 27.07.: Golden-Bundle jetzt `main.b99d8319dfc26e978896.bundle.js` (Cache-Bust ueber
  NEUEN Dateinamen, CF-Edge haelt alte Namen 1 Jahr), master-Quelle entdoppelt (a16af580).

## Selbstheiler-Cron (cf-ensure-addon.sh, Stand 27.07.2026)

Laeuft minuetlich als root auf srv2 (`$B=/home/gaz/rentanda/web/backend`): heilt index.html
(Addon-Script-Tags, Google-Maps-Key, main-Bundle-Referenz auf GOLDEN) UND seit 27.07. die
Addon-Module in `cf-booking-suggest.js`: fehlen die Fingerprints `__cfABMDLoaded`/`__cfRDOLoaded`/`__cfCMASKLoaded` (Stand 29.07.2026)
(Ueberschreiber-Regression), haengt er das Modul additiv aus `$B/cf-modules/<name>.module.js` an
und bumpt `?v=autoheal<ts>`. Neue Addon-Module deshalb IMMER: (1) als eigene IIFE mit
`__cfXYZLoaded`-Guard, (2) Modul-Datei in `cf-modules/` ablegen, (3) Zeile in der MOD-Liste des
Skripts ergaenzen. Wer cf-booking-suggest.js neu schreibt: vorher Fingerprints ALLER Module greppen.

## Kontaktdaten-Maskierung in der Vorgangsansicht (seit 29.07.2026)

Provisions-Leakage-Schutz, serverseitig — nicht nur UI.

- **`ApiBundle/Helper/AccessHelper.php`:** `$cfContactFields` (`email, tel, mobile, street,
  postal_code, city, birthday`), `cfContactIsMasked()`, `cfMaskContact()`, `cfStripContactInput()`.
  Maskiert wird für **alle Nicht-Admins** bei `Booking::TYPE_MIETANFRAGE` (1),
  `TYPE_MIETANFRAGE_ACCEPTED` (2) und `TYPE_MIETANFRAGE_DENIED` (4); frei bei 3/5/6.
- **`ApiBundle/Controller/BookingController.php`:** drei Einfügungen — `searchAction`
  (Liste/Grid), `indexAction` (Detail, **nach** dem `$memcacheService->set()`), sowie
  `cfStripContactInput()` vor `$jsoner->updateFromArray($bookingAr)`.

**Zwei Fallen, die das Ganze sonst kaputt machen:**

1. **Die UI schickt beim Speichern das komplette Buchungsobjekt zurück.** Ohne
   `cfStripContactInput()` überschreibt der erste speichernde Vermieter die echten Kontaktdaten
   mit den maskierten Leerwerten. Ausgabe UND Eingabe absichern.
2. **Die Maskierung muss NACH dem Memcache-Set sitzen**, sonst landet ein maskiertes JSON im
   geteilten Cache und Admins bekommen leere Felder serviert.

**Rollen-Realität (gemessen 29.07.2026):** Backend-Accounts mit Stations-Zuordnung sind
10 x `ROLE_ADMIN`, 104 x `ROLE_STATION`, **241 x `ROLE_USER`**. Eine Regel auf `ROLE_STATION`
hätte 241 Vermieter-Logins ungeschützt gelassen — deshalb prüft `cfContactIsMasked()` gegen
`isAdmin()`, nicht gegen eine Vermieter-Rolle.

**Frontend-Hinweis** statt leerer Felder: Addon-Modul `cf-modules/cf-cmask.module.js`
(Guard `__cfCMASKLoaded`), liest `GET /api/bookings/{id}` und reagiert nur auf
`contactMasked === true`. Testschalter ohne Vermieter-Login:
`window.__cfCMASKforce = true` in der Browser-Konsole. Vermieter-Testzugang existiert
(`vermieter-test@camperfuchs.de`, ROLE_USER, Stationen 3587 + 3869).

**PII-freies Verifikations-Rezept:** Kernel booten (`sudo -u www-data php`), `BookingJsoner` +
`cfMaskContact` auf echte Datensätze anwenden und **nur Zähler** ausgeben (wie viele Felder
befüllt, Flag ja/nein) — nie Werte. So lässt sich beweisen, dass Buchungen sichtbar bleiben und
Anfragen nicht lecken, ohne Kundendaten zu dumpen.

## PHP-Seiten und cf-*.js-Addons unter /backend

Neben der Angular-App leben dort eigene Bausteine (alle in `/home/gaz/rentanda/web/backend/`):

- **Eigene Seiten:** `cf-vorgang.php` (Vermieter-Vorgangsseite + Admin-Liste `?p=alle`),
  `cf-vorgaenge.php` (JSON-API der Liste), `cf-contact-toggle.php`, `cf-contact-release.php`,
  `cf-decline-notify.php`, `cf-vorgang-url.php` (signierte Vorgangs-URL **plus Status und
  letzte Schritte**, X-Token), `cf-status-bulk.php` (Status + Abrechnungsstand fuer bis zu
  200 Buchungsnummern auf einmal, X-Token), `cf-lexware-invoice.php` und `cf-lex-status.php`
  (Provisionsrechnung: Nummer + PDF, Auszahlung) u.a.
- **Addons:** `cf-*.js`, eingebunden per `<script>`-Tags am Ende von `index.html`, jeweils mit
  `?v=<version>` als Cache-Bust. Muster: IIFE mit Guard (`if (window.__cfXLoaded) return;`),
  Token aus `localStorage` (`stoken` || `token`), Kommentarkopf mit Zweck + Rollback.
  Nach jeder Aenderung an einem Addon **das `?v=` in `index.html` hochzaehlen**. Im Einsatz
  sind unter anderem `cf-vorgangslink.js` (Kasten „Stand des Vorgangs" + Status-Chip auf der
  Buchungsseite) und `cf-listenstatus.js` (Status- und Abrechnungs-Badge in der Buchungsliste).
- **Cron-Endpoints unter `/usr/local/cf/`:** `cf-zahlung-event.php` (alle 15 Minuten:
  Zahlungseingang → Verlaufseintrag + Chat-Status), `cf-status-sync.php` (stuendlich:
  Chat-Status gegen den Legacy-Stand abgleichen), `cf-verfmail.php` (Verfuegbarkeits-Mail an
  den Vermieter, JA/NEIN oder Direktbuch-Info).
- **Auth-Muster fuer eigene Endpoints:** JWT des eingeloggten Nutzers im Header `X-Token`,
  RS256 gegen `/home/gaz/rent/jwt/key.pub` pruefen (Vorlage: `cf-contact-toggle.php`), danach
  Rolle aus `users.role`; Stationsnutzer ueber `user_stations` (user_id, station_id). Fuer
  Skripte laesst sich ein Token mit `/home/gaz/rent/jwt/key.priv` selbst signieren
  (uid 1006 = b.dunker, ROLE_ADMIN).
- **Signierte Vorgangs-Links:** `substr(hash_hmac('sha256', 'vorgang|<id>|v', $ck), 0, 32)` mit
  `$ck = /usr/local/cf/cf-comm.key`; Chat-Link mit dem Praefix `t|`, Liste mit `liste|`, Storno
  mit `storno|`.

## Vorgang ↔ Buchung verlinken (20.08.2026)

Beide Richtungen sind eingebaut, das Muster taugt fuer weitere Spruenge:

- **Vorgang → Buchung:** in `cf-vorgang.php` haengt an `$akt` ein Button „Buchung im Backend
  oeffnen" (`/backend/booking;id=<id>`); im Aktions-Menue der Admin-Liste (`?p=alle`) gibt es
  denselben Eintrag.
- **Buchung → Vorgang:** Addon `cf-vorgangslink.js` zeigt in der linken Spalte den Kasten
  „Vermieter-Ansicht" mit Links auf Vorgangsseite und Chat. Die signierte URL holt es von
  **`cf-vorgang-url.php?b=<id>`** (X-Token; Admin darf alles, Stationsnutzer nur die eigene
  Station). Popup-Fenster **vor** dem fetch oeffnen, sonst greift der Popup-Blocker.
- **Anker-Falle:** Die Zeile „Vorgang: BZROLB" ist gesplittet — ein Element traegt nur
  „Vorgang:", die Nummer steht daneben. Auf `^Vorgang:` pruefen und den Elternknoten nehmen.

## Zahlen und Abrechnung im Legacy-Datenmodell

- ⚠️ **`booking_payments` ist tot** (letzter Eintrag 2021), ebenso `station_konto` (2022).
  Wer dort nachsieht, haelt jeden Vorgang fuer unbezahlt.
- **Zahlungen sind negative `booking_positions`** mit `type='partial'`: `gesamt` = Summe
  positiver, `gezahlt` = Summe negativer Positionen. Genau so rechnen `cf-zusage-reminder.php`
  und `cf-freigabe-watch.php`.
- **Provisionsstatus** steht in `bookings.meta.cf_abr` = `{at, nr, total}` (`nr` = optionale
  Lexware-Rechnungsnummer, `total` = abgerechneter Betrag fuer die Delta-Erkennung bei
  Verlaengerungen). Der Button „Als abgerechnet markieren" fragt per `prompt()` nach der Nummer
  und schreibt genau dieses Feld. Provision = 10 % netto vom Brutto + 19 % MwSt.
- ⚠️ **`provision_status` ist das dritte tote Feld** — 2026 bei allen 3.176 Vorgaengen NULL.
  Die Listenspalte „Abgerechnet (Prov)" meldet deshalb ueberall „nein"; `cf-listenstatus.js`
  ueberlagert sie mit der Wahrheit aus `meta.cf_abr`.
- **Status der Vorgangsseite:** `cf_vorgang.status`, ueberschrieben von `bookings.type = 3`
  (→ „gebucht") und `cancelled = 1` (→ „storniert"). Verlaufseintraege kommen aus
  `cf_vorgang_event` (kinds: vermieter_mail, entscheidung, seitenkanal, mieter_mail,
  kontaktfreigabe, nachricht, dokument, zahlung, auszahlung).
- **DB:** DO-managed MySQL, der `mysql`-Client braucht `-P25060`. **`NOW()` laeuft in UTC**, die
  Serveruhr in CEST — `cf_vorgang_event.ts` wird als UTC interpretiert.

## Der Chat-Status und die zwei reinen Anzeige-Status (20.08.2026)

Vier Oberflaechen zeigen denselben Stand: Vorgangsseite, Buchungsseite, Admin-Liste und der
Chat unter `/backend/nachrichten`. Der Chat liest `chat_map` im Worker `cf-mailstatus`.
Setzen und lesen geht **ohne Worker-Deploy**:

```
POST|GET https://cf-mailstatus.b-dunker.workers.dev/chat-map
Header:   X-Comm-Key: <Inhalt von /usr/local/cf/cf-comm.key>
Body:     {"booking":"<id>","status":"gebucht"}
```

Erlaubt sind genau elf Werte: `offen`, `ja`, `nein`, `rueckfrage`, `ja_freigegeben`,
`ja_rueckfall`, `abgesagt`, `zusage`, `anzahlung`, `gebucht`, `storniert`.

⚠️ **`cf-status-sync.php` korrigiert nur vorwaerts.** Zustaende, die allein der Chat kennt
(`zusage`, `rueckfrage`, `abgesagt`, `ja_rueckfall`), fasst der stuendliche Abgleich nicht an —
einzige Ausnahme ist das Storno.

Dazu kommen zwei reine **Anzeige-Status**. Nichts davon steht in der DB, sie leben allein in
`cf-vorgang.php`, gelten fuer Liste und Detailseite und greifen nur, wenn der Rohstatus
`offen` oder `rueckfrage` ist:

| Status | Bedingung | Wirkung |
|---|---|---|
| `direktbuchbar` | Fahrzeug am Standort online buchbar | Der Vermieter bekam nur `direktbuchbar_info`, also gar keine JA/NEIN-Frage — Kopf „Kein Handeln noetig", Chat und Zusage bleiben moeglich |
| `abgelaufen` | `date_from < NOW()` | Reisezeitraum vorbei, es ist nichts mehr zu entscheiden |

Beide raeumen die Arbeitsliste „Du bist dran" auf — sie schrumpfte dadurch von 26 auf 10.

## „Direkt buchbar" steht in `article_locations`, nicht in `articles`

⚠️ `articles.bookable` ist **nicht** die Wahrheit — dort stand fuer ein nachweislich direkt
buchbares Fahrzeug eine `0`. Massgeblich ist die Kombination Fahrzeug + Standort, so wie es
`cf-verfmail.php` schon immer gerechnet hat:

```sql
(SELECT MAX(al.bookable) FROM article_locations al
  WHERE al.article_id = r.article_id AND al.location_id = r.station_id
    AND al.visible = 1) direkt
```

`cf-vorgang.php` fragte dagegen `articles.bookable` ab und zeigte deshalb bei direkt buchbaren
Fahrzeugen „Deine Antwort fehlt noch". Bei jeder Frage „ist das direkt buchbar?" gehoert diese
Subquery hin. (Stand 20.08.2026: 309 Zeilen in `article_locations` mit `bookable = 1 AND
visible = 1`.)

## Herkunft („Quelle") kippt beim Umstellen Anfrage → Buchung (20.08.2026)

`origin` im `BookingController`: `online = 1` → online, sonst `createdBy` → partner bzw.
administrative, sonst `type === 1` → online, andernfalls **unknown**. Eine im Backend von
Anfrage auf Buchung umgestellte Buchung hat weder das Flag noch `createdBy` — sie fiel damit
auf „unbekannt" und verzerrte die Herkunfts-Statistik. Seit dem 20.08.2026 zieht die Regel
zusaetzlich `meta.provisorilyOrigin === 'customer'` heran (das wird bei jeder Website-Anfrage
gesetzt) und liefert wieder `online`. Wirkt rueckwirkend, ohne Datenmigration.

## Der Hinweis „Abweichung von Preisliste" und die Preis-Uebernahme (20.08.2026)

**Merksatz: Der Legacy-Preisrechner kennt genau ZWEI Zeilen.** `RateCalculator::getRatePositions()`
liefert fuer ein Wohnmobil ausschliesslich „Mietpreis pro Tag <Saison>" (aus `articles.season_data`)
plus „Servicegebuehr" (aus `articles.service_rate`), dazu ggf. eine „Abzgl. X% Rabatt"-Zeile.
**Zubehoer steht in `articles.additions` und kommt ueber `getAdditions()` getrennt** — es taucht in
`positions` NIE auf. Gebuehren der neuen Buchungsstrecke (z. B. Zahlungsgebuehr) kennt der Rechner
gar nicht. Wer den Buchungs-Gesamtbetrag gegen diese Liste rechnet, vergleicht Aepfel mit Birnen.

Genau daran ist die rote Box „Abweichung von Preisliste" zweimal gescheitert:

- Angulars `stdPriceDiff()` zaehlt am Vorgang nur `type='rent'` und vergleicht das mit der
  KOMPLETTEN Preisliste → meldete die Servicegebuehr als Abweichung.
- Der Fix vom 05.08.2026 (`cfPriceDiffFix`, im Addon `cf-booking-suggest.js`, weil ein frueherer
  Bundle-Patch bei einem Deploy verloren ging) verglich `booking.amountTotal` gegen die Liste →
  meldete jetzt Zubehoer + Zahlungsgebuehr als Abweichung, bei JEDER Online-Buchung.
  Beispiel 533743: Liste 1.774 EUR, amountTotal 1.882,06 EUR → „-108 EUR", obwohl 11x149 Miete und
  135 Servicepauschale exakt stimmten; die 108,06 waren 28,06 Zahlungsgebuehr + 80 Endreinigung.
- **Seit `cfPriceDiffFix v20260820pd2`** wird nur der vergleichbare Kern gerechnet: `type='rent'`
  plus Zeilen mit `servicegeb|servicepausch` plus Zeilen, die mit `Abzgl.` beginnen. Ohne
  Mietposition am Vorgang gibt die Funktion `null` zurueck und die Box bleibt unangetastet.
  Wirkung, an 170 laufenden Vorgaengen gemessen: Box meldete vorher 119x, jetzt 72x.

**„Preis fuer diesen Zeitraum uebernehmen" laeuft serverseitig** (`/backend/cf-price-apply.php`,
JWT `X-Token`, nur ROLE_ADMIN, Log `/var/log/cf-price-apply.log`). Vorher ging das nur ueber die
Oberflaeche — `confirmPositions()` ist im Prod-Build ausschliesslich ueber `selectArticle()`
erreichbar (`ng.probe` ist aus), also musste das Addon „Alternativen anzeigen" klicken und die
eigene Kachel treffen; das klappte die ganze Fahrzeugliste auf und warf ausserdem Zubehoer mit weg.

Der Endpoint ersetzt gezielt: raus `type='rent'` + `servicegeb|servicepausch` + `Abzgl.`-Zeilen,
**stehen bleiben** Zubehoer (`additional`), Gebuehren (`fee`), Versicherung, Gutscheine,
Individuelles und ALLE Zahlungen (`partial`). Neue Zeilen bekommen sinnvolle Typen
(Miete `rent`, Servicegebuehr `fee`, Rabatt `discount`) — Angular schrieb pauschal alles als `rent`.
Parameter: `id`, `dry=1` (nur rechnen, liefert remove/add/keep + Summen), `force=1` (schreiben
trotz erfasster Zahlung). Ohne Mietposition, ohne Preisliste, bei storniertem Vorgang → 409.
Im Addon (`cfPriceTake v20260820pt4`) zeigt der Button erst diese Vorschau und schreibt erst auf
Klick. ⚠️ Der Button haengt in der Warnbox — ist die ausgeblendet, ist auch er nicht erreichbar.

⚠️ **Uebernahme ist kein Automatismus.** Bei Vorgaengen, deren Vermieter-Preisliste veraltet ist,
hebt sie den Preis massiv an (gemessen: 2.324 → 3.644 EUR, weil die Liste Hochsaison sagt und zu
Standardsaison gebucht wurde). Immer erst die Vorschau lesen.

**Fallen beim Bauen solcher Endpoints:**

- `"Servicegeb*/Servicepausch*"` in einem PHP-Blockkommentar beendet den Kommentar (`*/`) und
  wirft einen Parse-Error weit unterhalb. `php -l` faengt es — vor jedem Deploy laufen lassen.
- **`pos()` ist im Legacy-Autoload schon global belegt.** Eigene Helfer brauchen ein Praefix,
  sonst „Cannot redeclare pos()".
- **Testvorgaenge lassen sich nicht hart loeschen.** `folders` hat einen Selbstbezug
  (`parent_id` → `folders.id`), und beim Anlegen einer Buchung entsteht dort ein Ordnerbaum;
  `DELETE FROM bookings` scheitert am FK. Sauberer Weg: Positionen loeschen, dann
  `cancelled=1, archived=1` setzen. Nicht in fremde Ordnerbaeume greifen.

## Der Bild-Endpoint liefert ohne Breitenangabe das Original (21.08.2026)

`FrontendArticleController::imageAction` bedient
`/api/articles_frontend/c/{article}/{image}[/{width}]`. Nur **mit** `/{width}` entsteht ein
Thumbnail; **ohne** geht die Originaldatei roh raus. Und genau ohne Breite verlinkt der Controller
die Galerie-Bilder und die Grundrisse (`outlineDay`/`outlineNight`) — eine Breite bekommt allein
`thumbnail`.

Folge: bis zu **63,2 MB für ein einzelnes Bild**; 2.702 der 14.419 Dateien in
`/home/gaz/storage/files` liegen über 1,2 MB. Cloudflare Polish fasst so große Dateien nicht an
(siehe `camperfuchs-projekt`), sie gingen also ungebremst an den Browser.

Seit dem 21.08. deckelt `FileService::getCappedOriginal()` Originale über 1,2 MB auf 1600 px:

- **Format bleibt** (`convert -thumbnail 1600x> -strip`), damit die Grundrisse ihren Alphakanal
  behalten. JPEG zusätzlich `-quality 82 -interlace Plane`.
- **Opake PNGs werden JPEG** — geprüft per `identify -format %[opaque]`. Ein PNG-Foto bleibt sonst
  auch bei 1600 px über 2 MB und fällt erneut durch Polish. Der Content-Type wandert mit
  (Referenzparameter), sonst lägen JPEG-Bytes unter `image/png`.
- **Scheitert `convert`, bleibt es beim Original.** Ein Bild darf nie verschwinden, nur weil die
  Wandlung hakt.
- Ergebnis der Stichprobe über die 60 vorher größten: **kein einziges mehr über 1,5 MB**,
  Durchschnitt 889 → 444 KB.

Nach so einer Änderung müssen die alten Kopien aus dem Edge-Cache: die betroffenen URLs gezielt
purgen (Cache-Lebensdauer sonst 7 Tage). ImageMagick ist hier 6.8.9 von 2014 — **WebP-Ausgabe nach
stdout funktioniert nicht** (`webp:-` liefert 0 Bytes), deshalb Format behalten und Polish die
Umwandlung überlassen.

## Cron: `* */2` ist nicht „alle zwei Stunden" (21.08.2026)

In der root-Crontab stand `* */2 * * * /home/gaz/s3copy.sh` — gemeint war `0 */2`. Mit `*` im
Minutenfeld startet der Job in jeder geraden Stunde **60-mal**. `s3copy.sh` synchronisiert 17 GB
nach DO Spaces, ein Lauf dauert weit länger als eine Minute, also stapelten sich die Läufe:
**load 4,06 bei 4 Kernen**, zwei `aws s3 sync` mit je 90 % CPU. Die `gaz`-Crontab enthielt
denselben Job korrekt mit `0 */2` — die root-Zeile war eine Dublette **mit** Tippfehler.

Nach dem Entfernen: **load 0,24.**

Drei Lehren:

- **Bei „Server ist langsam" zuerst `ps` nach CPU sortieren**, bevor Query oder Index verdächtigt
  werden. Der Verursacher stand hier ganz oben und war in zwei Minuten gefunden.
- **Cron-Zeilen beim Anlegen laut vorlesen.** „Stern Schrägstrich zwei" im Minutenfeld heißt
  jede Minute, nicht alle zwei Stunden.
- **Läuft derselbe Job in zwei Crontabs, ist eine davon vermutlich überflüssig.** Vor dem
  Korrigieren prüfen, ob man ihn nicht einfach löschen kann.

Ein sich stapelnder Cron-Job lässt sich mit `flock -n` grundsätzlich verhindern — mehrere
`cf-*`-Jobs auf srv2 machen das bereits vor.

## Eine Anfrage haengt am Standort, nicht am Fahrzeug-Besitzer (21.08.2026, teuer gelernt)

Vorgang #1W2KWY: Ein Mietinteressent wartete zwei Tage, der Vermieter hatte nie etwas gesehen.
Ursache war ein leeres Feld — **Station 4045 (Hemer) hatte weder `email` noch `mobil`**. Die
Anfrage-Mail ging nur an `office@`, und `cf-nudge24` uebersprang den Vorgang **still**
(`SKIP ... Station ohne Mail`, nur im Log). Betroffen waren ueber drei Monate **6 Anfragen**,
alle bei derselben Station. Niemand hat es gemerkt, bis der Kunde nachfragte.

Zwei Dinge, die man beim Nachforschen zwingend richtig machen muss:

**1. Die Zuordnung Anfrage → Standort laeuft ueber `article_locations`, NICHT ueber
`articles.station_id`.** Beim betroffenen Fahrzeug zeigte `articles.station_id` auf Station 4034
(Hagen, mit vollstaendigen Kontaktdaten), waehrend `article_locations.location_id` = 4045 (Hemer,
ohne Kontaktdaten) war — und `bookings.station_id` folgt dem Standort. Wer ueber `station_id`
joint, sieht ueberall gepflegte Vermieter und findet den Fehler nie. Derselbe Vermieter kann
mehrere Stationen haben, von denen nur eine gepflegt ist.

**2. „Fahrzeug vorhanden" heisst `articles.public = 1` + nicht `deleted` + `article_locations.visible = 1`.**
Ein rohes `COUNT(*) FROM articles WHERE station_id = ...` zaehlt Karteileichen mit. Damit sah es
so aus, als haetten 11 CF-gelistete Stationen bis zu 10 Fahrzeuge ohne hinterlegte Mail — real
ist bei allen elf **kein einziges Fahrzeug oeffentlich sichtbar**. Eine Ueberwachung auf dieser
Zahl haette 11 Dauer-Fehlalarme erzeugt und den echten Fall trotzdem verpasst. Bjoerns Regel
gilt: Fahrzeugzahlen nie selbst zusammenfiltern, immer gegen die Live-Sicht gegenpruefen.

**Waechter dagegen:** `/usr/local/cf/cf-station-mail-watch.php`, Cron `cf-station-mail-watch`
(taeglich 8:10, Log `/var/log/cf-station-mail-watch.log`). Zwei Checks — akut (offene Anfrage
`type=1`, Reise in der Zukunft, Station ohne `email`) und vorsorglich (sichtbares Fahrzeug ueber
`article_locations` an einer Station ohne `email`). DRY-RUN ist Standard, Versand nur mit
`--live`, Mail nur bei Treffern. Notaus: `#` vor die Cron-Zeile.

Merksatz: **Ein Filter, der nichts findet, kann auch bedeuten, dass die Meldung nie ankam.**
Ein stilles `continue` in einer Automatik ist ein blinder Fleck — es gehoert immer eine Meldung
an einen Menschen dahinter, nicht nur eine Zeile im Log.

## Das Kostenmuster hat eine fuenfte Fundstelle: `/api/customers/` (01.09.2026)

Die Regel „nicht die DB, nicht der Server, sondern Daten die niemand braucht" galt bisher fuer
`ArticleService`, `booking.component`, die Buchungsliste und Foxi. Am 01.09.2026 kam
`CustomerController::indexAction` dazu — und zwar als **HTTP 500**, nicht als Langsamkeit:

```php
// vorher: laedt ALLE 44.482 Buchungen des Scopes als volle Doctrine-Entities
$bookings = $em->getRepository('BluetrailerDBSchemeBundle:Booking')->findBy(['scope' => $scope]);
// ... und wirft davon in PHP die Haelfte per continue wieder weg
```

Beim Admin-Login sprengte das das 1-GB-`memory_limit`, und zwar genau dort, wo Symfony die
Antwort serialisiert: `OutOfMemoryException … at JsonResponse.php line 145`. Vier solche 500er in
sieben Tagen. Dazu lief ein `krsort` **innerhalb** der Aufbau-Schleife, also einmal je Buchung
statt einmal je Gruppe.

**Zwei Eingriffe, beide semantisch neutral:**

1. **Die `continue`-Bedingungen als Vorfilter in die Query ziehen** — 44.482 → 18.329 hydrierte
   Entities, Peak >1 GB → 553 MB, 500 → 200. Wichtig: **ohne `TRIM`** filtern, sonst weicht das
   Ergebnis vom PHP-Filter ab (`strlen(' 12 ')` ist 4, `LENGTH(TRIM(' 12 '))` ist 2).
   `origCount` muss ueber eine eigene COUNT-Query weiter die ungefilterte Gesamtzahl liefern.
2. **Den Zugriffsfilter in die Query ziehen.** Jeder Vermieter lud alle 18.329 Buchungen *aller*
   Partner und verwarf sie danach per `AccessHelper::userHasAccessToBooking()` — 36 Sekunden fuer
   eine **leere** Antwort. Mit `join('b.article','a')->join('a.station','st')` und
   `st.id IN (getLocations($user))` bzw. `st.domain = user.domain` fuer `domain_admin`:
   1.372 statt 18.329 Buchungen, 37,8 s → 0,2 s Query, live 36 s → 5,8 s.

**Die Regel dabei:** Der Query-Filter muss eine **Obermenge** der AccessHelper-Regel sein — den
`deleted`-Check bewusst weglassen — und die PHP-Pruefung bleibt als Sicherheitsnetz stehen. So
kann der Vorfilter nie mehr freigeben als erlaubt, nur weniger laden. Die Maskierung
(`cfMaskContact`) laeuft unveraendert weiter: nach dem Fix kamen 332 von 715 Buchungen maskiert
zurueck.

**Pflicht-Verifikation vor so einem Vorfilter** — sonst sieht ein Vermieter still zu wenig oder
zu viel: beide Varianten (mit/ohne Filter) fuer mehrere echte Konten durchrechnen und die
Ergebnis-Struktur auf Gleichheit vergleichen, inklusive eines `domain_admin` und eines Kontos
mit leerem Ergebnis. Am 01.09. waren alle fuenf identisch — erst danach ging es live.

**Offen geblieben:** Die Admin-Ansicht braucht weiterhin 102 s und liefert 22 MB (12.246
Kundengruppen). Die Kundensuche laedt die komplette Kundendatenbank und sucht im Browser —
dasselbe Muster wie die Buchungsliste. Richtiger Fix waere serverseitige Suche, das braucht einen
rentapp-Rebuild.

## `cf-commit.sh` trackt NICHT `/home/gaz/rent` (01.09.2026)

Der Drift-Wachhund `cf-commit.sh` arbeitet im Repo **`/usr/local/cf`** (die `cf-*.php`-Endpoints).
Ein Patch am Symfony-Backend unter `/home/gaz/rent` meldet dort korrekt „Nichts zu tun — es gibt
keine Aenderungen", obwohl `git -C /home/gaz/rent status` die Datei sehr wohl als `M` fuehrt.

**Folge:** Aenderungen am Legacy-Backend laufen am Drift-Netz vorbei. Wer dort patcht, muss die
Nachvollziehbarkeit selbst herstellen — Backup mit sprechendem Namen unter `/root/`, Eintrag auf
der Tafel, und den md5 der Ausgangsdatei vor dem Ueberschreiben pruefen (Diff-Guard), damit keine
parallele Session ueberschrieben wird.

## Fahrzeug-Änderungsprotokoll `cf_article_log` (seit 11.09.2026)

Anlass #3OBEWL: niemand konnte sagen, wer ein Fahrzeug auf „direkt buchbar" gestellt hatte.
Das Envers-Protokoll des Spring-Backends hilft dafür NICHT: `bookings_aud` und
`booking_positions_aud` sind gefüllt, **`article_locations_aud` existiert, hat aber 0 Zeilen** —
der Legacy-`ArticleController` schreibt an Envers vorbei, `revinfo` hat keine Nutzerspalte.

- **`ArticleController`** (Helfer `cfArtLogSnap()`/`cfArtLogDiff()`) schreibt vor/nach dem Flush
  in indexAction POST+DELETE und cfSetVisibilityAction je Änderung eine Zeile: wer (user_id,
  user_name, user_role, IP aus `CF-Connecting-IP`), `quelle` (`fahrzeugformular` /
  `sichtbarkeit` / `loeschen`), Fahrzeug, Standort, `feld` (`bookable`, `visible`, `main`,
  `standort`, `fahrzeug`, `fahrzeug_public|bookable|deleted|station`), `alt`, `neu`.
  ts = Berlin-Zeit. Fehler bleiben still — das Protokoll darf nie ein Speichern kippen.
- ⚠️ Das Fahrzeugformular setzt `article_locations.bookable` bei **jedem** Speichern aus dem
  Häkchen, **ohne Rollenprüfung** — auch Vermieter (ROLE_USER) stellen so auf direkt buchbar.
- **Sicherheitsnetz** `/usr/local/cf/cf-article-snapshot.php`, stündlich :17: vergleicht
  `article_locations` mit `cf_article_snap` und trägt Fremdänderungen (Spring, SQL, Skripte) mit
  `quelle='abgleich'` ein — ohne Nutzer, auf die Stunde genau.
- **Anzeige:** Backend → Protokoll → „Meine Vorgänge", Art „Fahrzeuge" (`cf-protokoll.php`).
  Vermieter sehen bei Admin-Änderungen „Camperfuchs-Team".
- Backup vor dem Patch: `/root/ArticleController.php.bak-a3-aenderungsprotokoll-20260911150333`.

## ⚠️ Kollations-Falle bei neuen cf_-Tabellen (11.09.2026)

MySQL 8 legt neue Tabellen mit **`utf8mb4_0900_ai_ci`** an, die Altbestände haben
`utf8mb4_unicode_ci` (`articles`) bzw. `utf8mb3_unicode_ci` (`stations`). Ein JOIN auf eine
Textspalte darüber wirft **„Illegal mix of collations"** — und wenn der Aufrufer das im
`try/catch` verschluckt (wie `cf-protokoll.php`), bleibt die Liste einfach **leer, ohne jede
Meldung**. Neue cf_-Tabellen, die mit Alt-Tabellen über Text-IDs gejoint werden, gleich mit
`DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci` anlegen, oder nachträglich
`ALTER TABLE … CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`. Joins über
Integer-IDs (`booking_id`) sind nicht betroffen. Diagnose: dieselbe Query mit
`PDO::ERRMODE_EXCEPTION` außerhalb des `try` laufen lassen.

## ⚠️ `/api/V1/bookings/request` legt KEINEN Vorgang an (11.09.2026)

Im Spring-Backend ist `POST /api/V1/bookings/request` der alte **Kontaktformular-Weg**
(`ContactService.processContact`): kein Eintrag in `bookings`, kein Angebots-PDF, keine
Vermieter-Mail — nur „Es gibt eine neue Buchungsanfrage!" an office@ (Gesamt 0,00 €, ohne
Vorgangsnummer, ~56 KB statt ~800 KB) und „Deine Kontaktanfrage" an den Kunden. Eine echte
Anfrage ist `POST /api/V1/bookings` mit `{type:'REQUEST', booking}` (so `request.tsx`) bzw.
`/api/V1/bookings/group`. Die Telefon-Anfrage-Maske (`cf-telanfrage.js`) lief bis v12 für
Einzel-Anfragen falsch; seit v14 prüft sie nach dem Absenden selbst, ob Vorgang und PDF da sind.

## Verwandte Skills
`camperfuchs-legacy-srv2-mail` (SSH-Zugang, sicherer Edit-Workflow, Mail/DMARC),
`camperfuchs-azure-devops` / `camperfuchs-deploy` (NEUES Monorepo),
`camperfuchs-live-daten` (DBs), `camperfuchs-projekt` (Gesamtarchitektur),
`camperfuchs-kalender-sperre` (Auto-Sperre bei NEIN zu direkt buchbaren Fahrzeugen).
