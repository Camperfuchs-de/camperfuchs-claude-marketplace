---
name: camperfuchs-projekt
description: >
  Technischer Projektkontext fuer Camperfuchs / Rentanda — was die Plattform ist, wie sie
  aufgebaut ist (WordPress-Marketing-Seite + eigenstaendige Next.js-Inventar-App), wie sie
  gehostet und ausgeliefert wird (Cloudflare -> DO-Load-Balancer -> Kubernetes -> WP-Backend),
  wie das Repo und der Branch-Flow funktionieren, wie der Caching-Stack tickt, wie E-Mail und
  Automatisierung laufen, und welche Konventionen im Team gelten. IMMER zuerst beachten, sobald
  es um irgendetwas Technisches bei Camperfuchs / Rentanda / Campercare geht — Architektur,
  Hosting, Deployment, Repo, Caching, "warum verhaelt sich die Seite so", Performance, SEO-Setup,
  Schema, E-Mail/Spam, Make.com. Auch bei impliziten Faellen wie "die Aenderung ist nicht
  sichtbar", "die Seite ist langsam", "wo liegt der Code", "auf welchem Server laeuft das".
  Enthaelt KEINE Tokens oder Passwoerter — nur nicht-geheime Bezeichner.
metadata:
  type: skill
  scope: camperfuchs-rentanda
---

# Camperfuchs — Technischer Projektkontext

Grundwissen ueber die Camperfuchs-Plattform fuer alle Tech-Aufgaben. Diese Skill liefert das
"Wie ist es aufgebaut" — nicht die Tagesaufgabe. Vor jeder Diagnose oder Code-Aenderung hier
nachsehen, statt zu raten. **Keine Secrets in dieser Skill**: Tokens/Passwoerter liegen in
einem privaten Store, nicht hier.

## Was ist Camperfuchs

- **Rentanda GmbH** betreibt die Marken **Camperfuchs** (Wohnmobil-Vermietung, `camperfuchs.de`),
  **Campercare** (`campercare.net`) und **blueTrailer**.
- Geschaeftsmodell: hochpreisige Wohnmobil-/Camper-Vermietung. Im Content/SEO daher Wert-Framing
  statt nackter Preiszahl (siehe Preis-Positionierung unten).
- Geschaeftsfuehrer: **Björn Dunker**. Programmierer: **Bahti** (Bakhtiyor Sultanov, Minijob,
  wenig Zeit) — zustaendig fuer App-Code, Origin/Kubernetes.

## Architektur (Hybrid)

`camperfuchs.de` ist **kein** reines WordPress. Mehrere Systeme unter einer Domain, vom
Kubernetes-Ingress nach Pfad verteilt:

1. **WordPress** = Marketing-Seite (Startseite, Stadt-Landingpages, Blog, Lead-Formulare).
   - Page-Builder: **WPBakery** (Hauptseiten, 33+ Seiten) **und** **Elementor** (Lead-Seiten:
     "Angebot anfordern", "Wohnmobil mieten/vermieten"). Beide bleiben aktiv — vor dem Editieren
     pruefen, mit welchem Builder die jeweilige Seite gebaut ist.
   - SEO: **Rank Math PRO** ist der einzige aktive SEO-Player. AIOSEO + dessen Tochter-Plugins
     sind bewusst deaktiviert (seit 25.05.2026). Schema-Org-Daten kommen aus Rank Math.
2. **Next.js / Nuxt-Inventar- & Landingpage-Stack** = eigenstaendige App fuer Fahrzeuge & Buchung
   sowie Teile der Landingpages. Laeuft im Kubernetes-Cluster, **nicht** in WordPress. Setzt
   **eigene** Cache-Header und liefert **eigenes** JSON-LD aus (Schema kommt hier NICHT aus
   Rank Math).

Faustregel: Marketing/Texte/SEO → WordPress. Fahrzeuge/Buchung/App-Logik → App-Repo.

## Repo & Deployment

- **Azure DevOps Mono-Repo**: `dev.azure.com/camperfuchs/camperfuchs`.
  Direkt diese Project-URL nutzen — **nicht** ueber `portal.azure.com` (anderer Auth-Flow,
  friert ein).
- Struktur: `frontend/` (die App) + `landing-pages/`. UI-/Seiten-Texte liegen in
  `frontend/i18n/de/` — kleine Textaenderungen gehen dort direkt, ohne Bahti.
- **Branch-Flow** (Branch-Schutz wird erzwungen): `feature → main → staging → prod`.
- `staging.camperfuchs.de` = Testumgebung (darf **nicht** von Google indexiert werden).
- App-Code, Origin und Kubernetes liegen bei Bahti; reine Text-/Content-Changes kann Björn
  selbst machen.

## Datenbank-Migrationen (Flyway) — Versionsnummer kollidiert = Backend tot

Das Spring-Backend faehrt Flyway-Migrationen aus `backend/src/main/resources/db/migration`
(`V<major>.<minor>.<patch>__<name>.sql`). **Zwei Dateien mit derselben Versionsnummer sind ein
harter Startfehler**, kein Warnhinweis:

```
Found more than one migration with version 2.1.15
```

Jeder neue Backend-Pod crasht dann beim Start — die komplette Umgebung antwortet mit **503**,
nicht nur das neue Feature. Am 27./28.07.2026 hat genau das staging lahmgelegt: zwei parallel
entwickelte Branches vergaben beide `V2.1.15` (`booking_meta_utf8mb4` und
`station_request_days_off`). Gemerkt haben wir es erst nach dem Merge nach main, weil ein
einzelner Branch fuer sich immer gruen baut.

**Regel vor jedem Merge einer Migration:**

1. Versionsnummer gegen die **zuletzt vergebene Nummer auf `main`** pruefen, nicht gegen den
   eigenen Branchpunkt. Bei parallelen Sessions/Entwicklern ist der Branchpunkt veraltet.
2. Kollidiert sie, die eigene Datei **umbenennen** (Inhalt bleibt) und neu pushen — die naechste
   freie Nummer nehmen, nicht die fremde verschieben.
3. Migrationen **idempotent** schreiben (`ADD COLUMN IF NOT EXISTS` o. ae.). Spalten werden bei
   dringenden Faellen vorab manuell auf der prod-DB angelegt; eine nicht-idempotente Migration
   scheitert dann beim Deploy.
4. staging und prod haben **getrennte Datenbanken** — ein Fix auf einer Seite heilt die andere
   nicht.

**Verwandter Fehlerfall:** `FlywayValidateException` / „Validate failed" bei einer Migration, die
inhaltlich laengst angewendet ist (Pod-Kill mitten im langen `ALTER` → Zeile blieb auf
`success=0`). Dann NICHT die Migration neu laufen lassen, sondern erst den Ist-Zustand der DDL
pruefen und danach die History-Zeile reparieren
(`UPDATE flyway_schema_history SET success=1 WHERE version='…'`) — in **beiden** Datenbanken.

## Hosting & Serving-Kette

Hosting: **DigitalOcean** (VPS-Droplets + Managed Kubernetes). Kein Managed-WP-Hoster.
`www.camperfuchs.de` wird **nicht** direkt von einer WordPress-Droplet bedient, sondern ueber
diese Kette (verifiziert 03.06.2026 per DO-API + `curl --resolve`):

```
Besucher → Cloudflare (Zone 835b24…) → DO Load Balancer 157.245.21.250 (LB-ID a0e0382b…)
        → Kubernetes-Cluster "camperfuchs" (Namespace camperfuchs-prod),
          Nodes 138.197.176.10 + 161.35.208.128 → ingress-nginx (proxy_pass)
```

Der nginx-Ingress faechert nach Pfad auf:

- `/`, `/wp-admin/` und alle WP-/Marketing-Pfade → **139.59.155.118** = Droplet
  `www.camperfuchs.de-wordpress` (ID 34020513) = **der echte Live-WordPress-Backend**.
- Nuxt-Landingpages (`/de/*`, `*_nuxt*`, `/wohnmobil-mieten-guenstig/*`) → landing-pages-App;
  `/api/V1` → backend; `/backend`, `/api` → 46.101.113.30 (srv2.bluetrailer).

**WP-Backend-Stack (auf 139.59.155.118): Apache + mod_php** (NICHT PHP-FPM!):

- `memory_limit` in `/etc/php/8.0/apache2/php.ini`.
- Neustart mit `systemctl restart apache2` — **nicht** `reload` (reload zieht ini-Aenderungen
  nicht).
- Stack ist alt: WP 6.4.1 + PHP 8.0 (Update im Backlog, kein Notfall).

**Wichtigster 502-Fall (verifiziert 29.05.2026):** `/wp-admin` warf 502 nur fuer eingeloggte
Browser (mit Cookies), `curl` bekam 302. Ursache war **nicht** PHP-OOM, sondern der
**Ingress `proxy_buffer_size` zu klein** fuer die grossen Response-Header, die WordPress (139)
bei eingeloggten Requests sendet. Fix in den 139-`proxy_pass`-Locations:
`proxy_buffer_size 64k; proxy_buffers 8 64k; proxy_busy_buffers_size 128k;`.
**Caveat:** der Ingress ist **Helm-managed** (`camperfuchs-prod`) → ein ad-hoc-Patch wird beim
naechsten `helm upgrade` ueberschrieben. Permanenter Fix muss in die Helm-Chart/Values =
Aufgabe Bahti.

**Droplet-Landkarte (Stand 03.06.2026, DO-API):**

| Rolle | Droplet (DO-Name) | ID | IP |
|---|---|---|---|
| Live-WP-Backend (hinter K8s) | `www.camperfuchs.de-wordpress` | 34020513 | 139.59.155.118 |
| K8s-Node | `camperfuchs-default-pool-33vc8h` | 572253690 | 138.197.176.10 |
| K8s-Node | `camperfuchs-default-pool-33vceb` | 572254461 | 161.35.208.128 |
| DO Load Balancer (vor K8s) | LB `a0e0382b…` | — | 157.245.21.250 |
| `wp.camperfuchs.de` (verworfen, NICHT live) | `camperfuchs.de` | 402882700 | 209.38.194.145 |
| Relaunch `new.camperfuchs.de` | `new-wordpress-camperfuchs` | 528117386 | 167.172.160.66 |
| Support/Help | `help-camperfuchs` | 527006892 | 64.226.80.165 |
| blueTrailer | `srv2.bluetrailer.de` | 9319374 | 46.101.113.30 |

Verwechslungsgefahr: **209.38.194.145 ist NICHT Live-www** — das ist `wp.` (verworfener Relaunch).
Vor jedem Eingriff kurz per `curl --resolve www.camperfuchs.de:443:<IP>` gegenpruefen. Bei hartem
Down: Power Cycle ueber `cloud.digitalocean.com/droplets` (volle Diagnose im `wp-502-debug`-Runbook).

## Caching-Stack (wichtig fuer "Aenderung nicht sichtbar")

Zwei Cache-Schichten, die sich **ergaenzen** (kein Konflikt):

1. **Cloudflare APO** (Automatic Platform Optimization) = Edge-Cache, sehr lange TTL
   (HTML s-maxage ~1 Jahr).
2. **Super Page Cache** (WP-Plugin) = **Disk-only**. Der Cloudflare-Toggle im Plugin ist
   **bewusst AUS**.

**Propagations-Falle** (kommt oft): Ein Content-Edit ist am Origin sofort frisch
(pruefbar mit `?cb=<timestamp>` an der URL), aber Besucher sehen weiter die alte Version, weil
Edge (APO, ~1J) + Super-Page-Cache-Disk die alte HTML liefern. Zusatzproblem: Multi-Pod-Disk →
ein Admin-"Purge" greift nicht zuverlaessig ueber alle Pods. → Wenn "die Aenderung ist nicht
sichtbar": fast immer Cache, nicht der Edit. Erst Origin per `?cb=` gegenpruefen, dann ueber den
Cache nachdenken.

- **Cloudflare**: Pro Plan. Cache-Hit-Rate nur ~44 % (trotz APO+SPC). Super Bot Fight Mode,
  Page Shield und OWASP-Ruleset sind AUS.
- **Cloudflare-Bezeichner** (keine Secrets, nur IDs):
  - Account `1f19594872b7aa8df85c24f19a34e621` = b.dunker@-Account (camperfuchs.de + .com +
    blueTrailer + campercare).
  - Account `1cc531159e1e37083ee8ea1003f95a0e` = "Domains"-Account.
  - Zone `camperfuchs.de` = `835b24e58f5c7a050c30286992c6be11`.

## SEO & Schema

- **Rank Math PRO** = einziger SEO-Player auf WordPress (siehe oben).
- **Schema-Strategie**: Vermietung wird als **`Product` mit `businessFunction = LeaseOut`**
  ausgezeichnet — das ist korrekt fuer Vermietung. `Vehicle`/Fahrzeug-Schema waere fuer **Verkauf**
  und ist hier falsch. Camperfuchs ist beim Schema bereits gleichauf mit der Konkurrenz.
- Die App liefert ihr JSON-LD selbst (nicht ueber Rank Math).

## Performance (Baseline)

- **Speculative Loading** aktiv (Prerender + "Moderate").
- **bfcache** ist in der App blockiert (Hebel fuers Zurueck-Navigieren).
- LCP-Baseline (CrUX, 27.05.2026): ~3,7 s. Stadt-Landingpages deutlich schlechter (~6,2 s) —
  groesster Performance-Hebel sind die Stadt-LPs (Edge-Cache + leichtere Hero).

## Stand-Updates seit 03.06.2026

- **Origin-TLS** renewt seit 14.06.2026 automatisch per **DNS-01/Cloudflare** (cert-manager ClusterIssuer `letsencrypt-prod` + Cloudflare-API-Token-Secret in ns `cert-manager`); Cert war zuvor 2 Jahre abgelaufen (HTTP-01 ging nie wegen NGINX-Master/Minion-Merge). Cloudflare-SSL-Modus danach auf **Full (strict)** gehoben. ClusterIssuer = Cluster-Infra, NICHT im Mono-Repo.
- **Backend-Header-Limit (#816, 16.06.2026):** Tomcat lehnte `/api/V1/articles` mit **HTTP 400** ab, wenn die Header zu gross wurden (Cookie-Jar ~3,8KB + Sentry `baggage`/`sentry-trace` + lange URL) -> Symptom "Suche nicht geladen" TROTZ freier Fahrzeuge (NICHT die Slot-Logik). Fix: `max-http-header-size` auf 64KB. Anderer Fall als der WP-502-`proxy_buffer_size`-Header oben.
- **Consent vereinheitlicht (11.06.2026):** WP-Bruecke (Code-Snippet id=29) spiegelt `cf_consent` <-> WPConsent, Consent-Mode-Default-Deny vor GTM. **Super Page Cache purgt zuverlaessig per REST:** `POST /wp-json/spc/v1/cache/purge`. Der fruehere Hinweis "Admin-Purge greift nicht zuverlaessig" gilt nur fuer den Admin-Button; der REST-Weg funktioniert (Achtung: es gibt ZWEI Cloudflare-Tokens — `cloudflare-api-token.txt` kann NICHT purgen, `cloudflare-purge-token.txt` schon; siehe Skill camperfuchs-cache-purge).
- **Cache Reserve** ist als **3. Cache-Ebene** aktiv (seit 11/2025, ~5$/Mon, separate Nutzungs-Rechnung) — ergaenzt APO + Super Page Cache, kein Konflikt.
- **prod-Gate = min. 1 Approver:** Björn kann den prod-Deploy allein freigeben. Deploy-Kette unveraendert `feature -> main -> staging -> prod`; Azure DevOps auch browserlos per PAT-REST steuerbar.
- **new.camperfuchs.de** ist die **neue Homepage im Aufbau** (eigenstaendiges WordPress, Theme **Kadence**, Inhalte als Kadence-Bloecke, per WP-REST baubar/editierbar) — nicht mehr nur ein "Relaunch-Droplet".
- **/de-Routing-Backlog #533-545 live (08.06.2026):** /de-Redirects, lowercase-301, JSON-LD/Cover-LCP/Cache-Control-Serie, Next-`/de/sitemap.xml` (lowercase). Restproblem: Sitemap-Generator listet z.T. noch MixedCase-Slugs, die auf lowercase 301en -> Grossstadt-LPs werden nicht indexiert (Fix offen, Backend/Bahti).
- **Image-Tags sind seit 14.07.2026 pro Umgebung getrennt (PR #1365) â€” WICHTIG beim Deploy:** `skaffold build -t $(Build.SourceVersion)-staging` bzw. `-prod`, Helm setzt `*.imageConfig.tag` passend. Vorher pushten BEIDE Pipelines den Tag `<repo>:<SHA>` â€” und da **staging und prod im SELBEN Cluster mit geteilten Nodes** laufen, ueberschrieb der spaetere Build das Image des frueheren; Nodes mit gecachtem Image zogen wegen `IfNotPresent` nicht neu. Folge: prod-Pods liefen auf zwei verschiedenen Images unter einem Tag, die Next-`buildId` flippte, Chunks unter `/_next/static/<buildId>/` liefen sporadisch ins 404 (07.07. + 14.07. je einmal passiert). `SENTRY_RELEASE` bleibt der reine SHA. **Azure nimmt die `ci/*.yml` immer aus dem Branch, der gebaut wird** â€” Pipeline-Aenderungen wirken erst, wenn sie im jeweiligen Branch liegen.
- **Deploy-Diagnose-Tell:** Bei "Deploy gruen, aber alte/wechselnde Version + 404 beim Navigieren" zuerst die `buildId` messen (`curl` ~20x auf `/wohnmobil-mieten`, `"buildId"` zaehlen) â€” zwei Werte = zwei Images live. Pod-Drift zeigt sich nur an `.status.containerStatuses[0].imageID` (Digest), NICHT an `.specâ€¦image` (Tag). `kubectl rollout restart` behebt das **nicht** (Nodes cachen den Tag); nur ein Digest-Pin konvergiert. Betroffen waeren nur die Next-Apps + `sharp`; `backend`/`pdfgenerator` bauen deterministisch.
- **frontend/backend haben eine HPA** (min 2, max 4, Ziel 80% CPU). `replicaCount` in `chart/values.*.yaml` ist nur der Startwert â€” wer Replicas "von Hand" korrigiert, arbeitet gegen die HPA. Nach Deploys skaliert sie kurz hoch; passt der zusaetzliche Pod nicht auf die 2 Nodes, steht er `Pending` und verschwindet beim Scale-Down von selbst. Das ist **kein** Defekt.
- **Lokale Dev-Umgebung** steht: `F:\dev\camperfuchs` (Mono-Repo lokal, `yarn dev` -> localhost:3000); kleine Frontend-/Text-Aenderungen lokal testbar, PRs per Browser.

## Make.com - Szenario deaktiviert (Fehler / Gift-Bundle)

Ein instant-Webhook-Szenario, das mit einem Modul-Fehler stoppt (z. B. `BundleValidationError: Validation failed for 1 parameter(s)`, typisch eine ungueltige E-Mail an ein Gmail-`to`-Feld), schaltet sich beim Reaktivieren SOFORT wieder ab, solange in der Webhook-Queue das ausloesende Bundle liegt. Diagnose: `executions?status=error` (welches Modul / welcher Parameter), dann `hooks_get` (`queueCount`). Die Webhook-Queue laesst sich NICHT ueber die Make-API/MCP leeren, nur im UI (Szenario oeffnen, "Show queue", Item, Detail, Delete). Danach die Ursache fixen (Filter/Guard VOR dem strengen Modul; `text:pattern` ist ein gueltiger Regex-Filter-Operator) und reaktivieren. Immer auch das client-seitige Formular haerten (echte E-Mail-Regex, nicht nur `type=email` bei Button+fetch ohne <form>), sonst liefert der naechste Tippfehler dasselbe Gift.

**Zweiter, anders gelagerter Fall derselben Meldung:** `Validation failed for 1 parameter(s). Missing value of required parameter 'followAllRedirects'` (bzw. `followRedirect`, `parseResponse`) kommt NICHT von einem Gift-Bundle, sondern von einem HTTP-Modul (`http:ActionSendData`), das per Make-API/Blueprint angelegt oder geklont wurde. Ueber die Make-UI setzt Make die Defaults dieser Booleans automatisch, ueber die API NICHT — sie muessen alle explizit im `mapper` stehen (`serializeUrl`, `method`, `headers`, `qs`, `bodyType`, `parseResponse`, `authUser`, `authPass`, `timeout`, `shareCookies`, `ca`, `rejectUnauthorized`, `followRedirect`, `followAllRedirects`, `gzip`, `useMtls`, `useQuerystring`). Das Szenario stoppt dabei NICHT — es laeuft weiter und schickt nur Fehler-Alert-Mails, faellt also leicht durch. Beim Klonen eines bestehenden Szenarios den Mapper des Quell-HTTP-Moduls 1:1 mitkopieren, nie "nur url setzen". Wegwerf-Testszenarien `ZZ <Zweck>-Test` nennen und nach dem Test loeschen statt deaktivieren; Alert-Mails koennen dem Loeschen nachlaufen, daher bei einer Make-Fehlermail zuerst `scenarios_list` pruefen — steht das Szenario nicht mehr drin, ist nichts zu tun.

## Windows/PowerShell — JSON- und Config-Dateien schreiben (BOM-Falle)

Windows PowerShell 5 schreibt mit `Set-Content`, `Out-File` und `>` UTF-8 **mit BOM**. Ein BOM macht eine
JSON-Datei fuer viele Parser ungueltig (`Unexpected token '', "{ …" is not valid JSON`) — betrifft
`plugin.json` im Marketplace-Repo genauso wie App-Configs, `.env`-artige Dateien und alles, was ein
Programm spaeter parst. Immer so schreiben:

```powershell
[System.IO.File]::WriteAllText($pfad, $text, (New-Object System.Text.UTF8Encoding($false)))
```

Der eigentliche Schaden entsteht meist erst danach: Ein Programm, das seine Config nicht parsen kann,
schreibt sie beim naechsten Start haeufig mit **Defaults neu** — dann sind die Einstellungen weg, ohne
dass jemand etwas geloescht hat (am 20.08.2026 genau so mit der Claude-Desktop-Config passiert). Deshalb
gilt: vor dem Schreiben Backup, nach dem Schreiben verifizieren (`ConvertFrom-Json` **und** die ersten
Bytes gegen `EF BB BF` pruefen), und laufende Programme vorher beenden — viele schreiben ihre Config beim
Beenden aus dem Speicher zurueck und ueberschreiben die Reparatur sonst wieder.

Zweite Falle im selben Umfeld: PowerShell-**Einzeiler**, die ueber ein Tool/MCP durchgereicht werden,
verlieren `$`-Variablen (`$_`, `$b` …) und scheitern mit Parser-Fehlern. Solche Aufgaben in eine `.ps1`
schreiben und mit `powershell -NoProfile -ExecutionPolicy Bypass -File …` starten.

## Subdomains

- `www.` = Live.
- `