# Changelog — camperfuchs-kontext

Der hier dokumentierte Stand ist die **eine Wahrheit** für beide Seiten. Die aktuell gültige
Versionsnummer steht in `plugins/camperfuchs-kontext/.claude-plugin/plugin.json` und muss mit
dem obersten Eintrag hier übereinstimmen. Wer eine neue Plugin-Version baut, schreibt hier einen
Eintrag dazu — sonst gilt die Version als nicht veröffentlicht.

Check „bin ich aktuell?": installierte Plugin-Version mit dem obersten Eintrag vergleichen.

---

## 0.67.0 - 13.09.2026

**camperfuchs-cache-purge - Purge-Disziplin, mit Zahlen belegt**

Anlass: Seobility meldete 6.898 Seiten mit langer Antwortzeit. Ursache war nicht der Server,
sondern acht Vollpurges an einem einzigen Abend (12.09., 17:15-00:25).

- `cf_purge.sh --all` verlangt jetzt zusaetzlich `--wirklich` und erklaert beim Abbruch den
  gezielten Weg. Ein Vollpurge kostet rund 70 Minuten kalten Edge fuer ~9.700 Stadtseiten.
- Nach einem bestaetigten Vollpurge stoesst das Skript den Warmer auf srv2 selbst an, statt bis
  zu 5 Minuten auf den canary zu warten.
- Jeder Purge schreibt eine Zeile nach `scripts/cf_purge.log` (Zeitpunkt, `CF_SESSION`,
  Benutzer@Host, Modus, Anzahl). Cloudflare protokolliert Purges nicht im Audit-Log - am
  13.09.2026 geprueft.
- SKILL.md: neuer Abschnitt "Purge-Disziplin" mit den gemessenen TTFB-Werten (Edge-HIT
  0,04-0,3 s, komplett kalt 1,5-1,9 s, unter Last bis 11 s) und dem teuer gelernten Befund,
  dass der Edge selten abgerufene Seiten trotz 7-Tage-TTL nach etwa einer Stunde wieder
  auswirft (LRU). Mehr LP-Replicas helfen dagegen nicht - am 13.09. gegengemessen.

## v0.66.0 (2026-09-13)

- `camperfuchs-plugin-sync`: **Cowork ersetzt eine Installation nicht, es legt die neue daneben.**
  Nach dem Einspielen von v0.65.0 lagen `camperfuchs-kontext` (0.64.0) und
  `camperfuchs-kontext~g2` (0.65.0) gleichzeitig da, beide mit 17 Skills. Im Skill-Verzeichnis
  erscheint nur ein Eintrag, und welche Fassung ihn liefert, ist nicht vorhersehbar — eine Session
  kann mit veraltetem Wissen arbeiten, ohne dass etwas nach einem Fehler aussieht. Neuer Abschnitt
  mit der Regel (alte Version in Einstellungen → Capabilities löschen), dem Zähl-Befehl zur
  Gegenprobe und dem Hinweis, dass das `~g2`-Suffix im Ordnernamen harmlos ist. Schritt 12 von
  Workflow B verweist jetzt darauf.

## v0.65.0 (2026-09-13)

- `camperfuchs-plugin-sync`: **Bahti macht erstmal nichts** — festgehalten in den Stammdaten und
  als Ruhevermerk über Workflow C. Von ihm sind vorerst keine Commits zu erwarten, er braucht
  keinen Zugang zum GitHub-Spiegel, und niemand soll auf seine Änderungen warten oder ihm
  vorsorglich Zugänge einrichten. Erst wieder einplanen, wenn Björn es ausdrücklich sagt.
- `camperfuchs-plugin-sync`: Neuer Abschnitt zum **GitHub-Spiegel**, der seit dem 13.09.2026 wirklich
  läuft. Enthält die beiden `/plugin`-Befehle für Claude Code, den Ablauftermin des Tokens
  (13.09.2027) und die teuer gelernte Falle: der Spiegel-Schritt wird ohne die Pipeline-Variable
  `GITHUB_TOKEN` stillschweigend übersprungen — die Pipeline bleibt grün, obwohl bei GitHub nichts
  ankommt. Prüfen heißt deshalb: bei GitHub nachsehen, nicht auf die Pipeline-Farbe schauen.

## v0.64.0 (2026-09-11)

**Legacy-Backend: Fahrzeug-Änderungsprotokoll, Kollations-Falle, Kontaktformular-Endpunkt.
Verfügbarkeits-Flow: Alternative auf der „doch belegt"-Seite.**

- `camperfuchs-legacy-backend`: neues Kapitel `cf_article_log` — wer stellt ein Fahrzeug auf
  direkt buchbar/online (ArticleController + stündlicher Abgleich, Anzeige im Protokoll).
  `article_locations_aud` bleibt leer, weil der Legacy-Controller an Envers vorbei schreibt.
- `camperfuchs-legacy-backend`: MySQL-8-Kollation neuer Tabellen (`utf8mb4_0900_ai_ci`) gegen
  Altbestand (`utf8mb4_unicode_ci`) — JOIN wirft, im try/catch wird daraus eine stille leere
  Liste.
- `camperfuchs-legacy-backend`: `/api/V1/bookings/request` ist der Kontaktformular-Weg ohne
  Vorgang; echte Anfrage = `POST /api/V1/bookings` bzw. `/group`.
- `camperfuchs-verfuegbarkeits-flow`: `cf-notfree.php` (direkt buchbar, „doch belegt") bietet
  jetzt „Hast du stattdessen etwas frei?" an — anderer Zeitraum mit Kalender-Vorschlag oder
  anderes eigenes Fahrzeug; landet als „Der Vermieter bietet dir an" in der Absage.

## v0.63.0 (2026-09-11)

**Deploy-Tore per REST, und warum Fahrzeugseiten aus der Suche langsam waren.**

`camperfuchs-frontend-feature-shippen`:
- Tor-Freigabe per PAT (`PATCH …/pipelines/approvals`, Body als Array) plus Tor-Wächter-Skript,
  das genau einmal freigibt (ein Lauf, richtiger Branch, richtiger Commit). Erprobt an der
  prod-Runde 1995+2001+1999+2002 (Lauf 5326).
- Beschreibung korrigiert: PRs gehen wieder per PAT-REST, nicht mehr „nur per Browser".
- Stand zum Self-Approval-Filter: am 11.09. nachmittags liefen Approve und Tor-Freigabe mit
  Björns Go durch. Blockiert er doch: nicht umgehen.
- landing-pages-Chunks liegen unter `/de/_next/`.
- Neue Fallen: Query-Parameter an internen Links machen jede Fahrzeugseite zum Cache-MISS
  (47 % der Aufrufe, LCP p75 3,1 s statt 1,5 s) → Nur-Browser-Werte in den Hash; ein stilles
  `router.replace` zählt als `$pageview`; vor jedem Tempo-Fix `lcp_detail` (TTFB vs. Bild) ansehen.

`camperfuchs-projekt`: Caching-Abschnitt um Fahrzeugseiten + Query-Parameter ergänzt.

## v0.62.0 (2026-09-11)

**Kalender-Sperre: bei direkt buchbaren Fahrzeugen sperrt ein NEIN jetzt automatisch.**

`camperfuchs-kalender-sperre` kennt jetzt zwei Regeln. Anfrage-Fahrzeuge bleiben beim
freiwilligen Klick auf der NEIN-Seite. Bei direkt buchbaren Fahrzeugen sperrt
`cf-nein-sperre.php` (srv2, alle 10 Minuten) den Zeitraum selbst — Björns Entscheidung nach
#3OBEWL: Feith hatte einen Zeitraum im Juli abgesagt, aber nie gesperrt; ein Kunde bekam
„direkt buchbar" und 14 Minuten später „leider belegt".

- Nur `article_locations.bookable = 1` am Standort der Anfrage, nur NEINs ab 11.09.2026 14:00,
  nur Zukunft, jede Anfrage einmal (Merker `neinsperre`), jede Sperre als Mail an Björn.
- Rezept, um offene NEIN-Zeiträume ohne Sperre zu finden.
- Hinweis auf die Warnung in der Telefon-Anfrage-Maske („Vermieter hat hier schon abgelehnt").
- Neu unter „Offen": Änderungen an „direkt buchbar" werden nirgends protokolliert
  (`article_locations_aud` bleibt leer, der Legacy-ArticleController schreibt an Envers vorbei).

## v0.61.0 (2026-09-11)

**Freigabe-Tore: Doppel-Läufe erkennen, nie ein altes Tor freigeben.**

`camperfuchs-frontend-feature-shippen` hat einen neuen Abschnitt. Anlass: Am 11.09.2026
standen fünf Deploy-Läufe (5184, 5189, 5213, 5217, 5223) bis zu 32 h am Freigabe-Tor. Alle
waren Doppel-Läufe von Commits, die ein zweiter Lauf längst ausgerollt hatte. Ein Klick auf
eines dieser Tore hätte staging bzw. prod um ein bis zwei Tage zurückgesetzt.

- Check vor jedem Approve am Tor: wartet dort der aktuelle HEAD des Ziel-Branches, gibt es
  schon einen neueren erfolgreichen Lauf? Sonst abbrechen statt freigeben.
- Vor manuellem Queue/Rerun prüfen, ob auf dem Commit schon ein Lauf wartet.
- Nach jedem Release muss die Liste offener Freigaben leer sein.
- Cowork blockiert Self-Approval eigener PRs und das Abbrechen von Pipelines: Björn bekommt
  die fertigen Links plus den Namen des Knopfs.
- Schritt 6 (prod-Gate) verweist auf den Check.

## v0.60.0 (2026-09-11)

**Die Cloud-Sandbox hat kein Egress mehr — alle Rezepte laufen über den PC.**

Seit dem 11.09.2026 lehnt der Egress-Proxy der Claude-Cloud-Sandbox `dev.azure.com`,
`www.camperfuchs.de`, `tafel.camperfuchs.de`, `api.eu.mailgun.net`, `api.cloudflare.com`
und `eu1.make.com` ab (`connect_rejected`). Erlaubt bleiben npm, pypi, github.com und
api.anthropic.com. Die Ablehnung liest sich wie ein Serverfehler und wurde schon einmal
als solcher fehlgedeutet.

Sechs Skills beschrieben einen Weg, den es so nicht mehr gibt. Sie tragen jetzt oben einen
Warnblock mit dem Ersatzweg (Desktop Commander, `.ps1` per `-File`, `Invoke-RestMethod` /
`Invoke-WebRequest` / Git-ssh):

- camperfuchs-frontend-feature-shippen
- camperfuchs-kalender-sperre
- camperfuchs-legacy-backend
- camperfuchs-plugin-sync (dessen eigener Standardweg „browserlos aus der Sandbox" ist betroffen)
- camperfuchs-verfuegbarkeits-flow
- camperfuchs-wp-droplet-ops

Dazu die Falle, die beim Bauen dieser Version selbst zugeschlagen hat: **PowerShell 5.1 liest
eine .ps1 ohne BOM als Windows-1252.** Längere Texte mit Umlauten oder Sonderzeichen gehören
deshalb nicht als Literal ins Skript, sondern in eine eigene Datei, die per
`[System.IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)` eingelesen wird. Der erste Anlauf
hat genau so sechs Skills mit doppelt kodierten Zeichen beschrieben und wurde verworfen.

Inhaltlich sonst unverändert. Details im Projekt-Doc `claude/sandbox-ohne-egress.md`.
Ob die Sperre bleibt, ist eine Einstellung auf Anthropic-Seite (Admin settings → Capabilities)
und noch offen — bis dahin ist der PC-Weg der Normalfall.

## v0.59.0 (2026-09-10)

### camperfuchs-frontend-feature-shippen
- **Zwei neue goldene Regeln aus dem Filter-Chip-Vorfall vom 09.09.** (1) `deploy-kette`
  wird schon VOR dem main-PR gesperrt, nicht erst beim Promote — ein Zwischenstand in
  `main` wird sonst von der naechsten b.dunker-Session nach prod mitgenommen, und
  „WIR = b.dunker, bewusst mit-deployen" schuetzt genau davor nicht. An dem Tag ging ein
  gerade abgelehnter Knopf live und musste per Korrektur-Kette (1966→1967→1968) von prod
  zurueckgeholt werden. (2) Ein Feature, das Bjoern noch nicht gesehen hat, ist kein
  prod-Kandidat: seine Rueckmeldung gehoert VOR den Promote, weil die Kette schneller
  laeuft als die Einarbeitung.

## v0.58.0 (2026-09-09)

### camperfuchs-plugin-sync
- **„Die Pipeline hat nicht ausgeloest" ist fast immer eine Fehldiagnose.** Definition 29 teilt
  sich den EINEN Build-Agent mit allen Deploys; am 09.09. lagen 3,5 Minuten zwischen Push und
  Build-Start, weil ein prod-Deploy lief. Zusammen mit dem bekannten Lag von
  `builds?definitions=29` hat das an einem Tag zwei Sessions dazu gebracht, das Paket unnoetig
  von Hand zu bauen. Neue Regel im Kapitel zur Pipeline: ungefilterte Build-Liste plus
  Agent-Warteschlange pruefen, 10 Minuten Geduld, und den Commit ehrlich betiteln.

## v0.57.0 (2026-09-09)

### camperfuchs-kontaktfreigabe
- **Waechter Block B fragt jetzt `/evt-peek`, nicht mehr `/status`.** `/status` liest `mail_rec`,
  und das fasst gleichartige Ereignisse derselben Adresse binnen 15 Minuten (`DEDUPE_S`) zu einem
  zusammen. Beim Buchungsabschluss gehen Zahlungs- und Kontaktdaten-Mail in derselben Sekunde
  raus — eine der beiden fehlte dort immer. Am 08.09. meldete der Waechter Vorgang 1V0RGT als
  "nicht zugestellt", obwohl Mailgun `250 OK delivered` hatte. `/evt-peek` liest `mail_evt` und
  haelt jedes Ereignis einzeln; dafuer nimmt es seit 09.09. auch `rec=` + `since=`.
- **Kontaktdaten-Mail traegt `cf_b`**, damit `mail_evt.cfb` die Vorgangs-ID fuehrt und die
  Zuordnung nicht mehr nur ueber die Empfaengeradresse laeuft.
- **Erstfreigabe-Zeitpunkt bleibt stehen.** Ein zweiter Endpoint-Aufruf setzt `cfContactReleased`
  nicht mehr neu (sonst verschiebt jeder Nachversand die Pruefbasis des Waechters), sondern
  vermerkt `cfContactReleasedAgainAt` / `...AgainBy`.

## v0.56.0 (2026-09-09)

### camperfuchs-alternativ-angebot
- **Nach Anbieter streuen.** Fahrzeuge derselben Station teilen sich exakt dieselben Koordinaten;
  eine Stations-ID gibt die oeffentliche Suche nicht her. Ohne Streuung stammen die Vorschlaege
  regelmaessig alle von einem Anbieter - Stichprobe ueber sechs Orte: in fuenf Faellen drei
  Vorschlaege vom selben Vermieter, in Berlin dreimal book-a-camper (sechs Fahrzeuge mit
  Stadtteilnamen, alle Station 3981). Sagt der ab, ist die ganze Auswahl weg.
- Neue Grundregel plus Rezept in Schritt 3b. Die automatische Absage-Mail
  (`suchAlternativen()` in `cf-decmail.php`) streut seit dem 09.09.2026 selbst.

## v0.55.0 (2026-09-03)

- **camperfuchs-legacy-backend**: Wissen aus der doppelt gefuehrten Konto-Fassung uebernommen —
  die reinen Anzeige-Status `direktbuchbar` und `abgelaufen` (20.08.), die Korrektur dass
  `articles.bookable` nicht die Wahrheit ist (maszgeblich ist `MAX(al.bookable)` aus
  `article_locations`), `provision_status` als drittes totes Feld, die Herkunfts-Ableitung ueber
  `meta.provisorilyOrigin`, der chat-map-Endpoint samt der 11 Statuswerte, die fehlenden
  Endpoints und Crons (`cf-status-bulk.php`, `cf-listenstatus.js`, `cf-vorgangslink.js`,
  `cf-lexware-invoice.php`, `cf-lex-status.php`, `cf-zahlung-event.php`, `cf-status-sync.php`,
  `cf-verfmail.php`) sowie acht teuer gelernte Fallen (Anker-Kollision, PDF-Vorschau friert die
  Browsersteuerung ein, geschlossener Dialog ist kein Versand, PDO `ERRMODE_EXCEPTION`,
  Log-Rechte, Lexware-Drosselung, Service heiszt `storage`, Addon-Intervall).
- **camperfuchs-frontend-feature-shippen**: Sofort-Abbruch-Check des Waechters ergaenzt
  (`git merge-base --is-ancestor <sha> origin/prod` als erster Schritt jedes Laufs, Task
  deaktivieren statt neu planen) plus Querverweis auf `camperfuchs-release-waechter`.
- **camperfuchs-plugin-sync**: Azure-Weboberflaeche als allerletzter Ausweg dokumentiert
  (Web-Upload nur flach ohne Ordnerstruktur, Monaco-Editor nicht skriptbar).

Hintergrund: Diese drei Skills lagen doppelt vor — einmal als Konto-Skill, einmal hier. Bei
`wp-502-debug` nannte die Konto-Fassung eine falsche Live-Origin-IP; im Stoerfall war es Zufall,
welche Fassung geladen wurde. Die Konto-Fassungen von `wp-502-debug`,
`camperfuchs-alternativ-angebot` und `camperfuchs-verfuegbarkeits-flow` sind am 03.09.2026 zu
Verweis-Stubs geworden; die drei hier genannten folgen, sobald diese Version steht.

## v0.54.0 (2026-09-02)

- `camperfuchs-wp-droplet-ops`: neuer Abschnitt **WPCode-Snippets aendern**. Die Shortcodes auf
  edition. (z.B. `[cf_haendlerverzeichnis]`, Post 2472) liegen als WPCode-Snippets vor. Zwei
  Fallen, die am 02.09. je eine Runde gekostet haben, sind jetzt dokumentiert: `wp post update`
  ohne `--user=1` strippt den PHP-Code still per KSES und meldet nur "Inhalt ist leer"; und WPCode
  liefert aus dem Array-Cache in der Option `wpcode_snippets` aus, nicht aus dem Post - wer nur
  den Post aendert, sieht im Frontend nie etwas. Inklusive PHP-Rezept zum Patchen der Option.

## v0.53.0 (2026-09-02)

**Das Kostenmuster hat eine fuenfte Fundstelle — und sie warf 500er.**
`CustomerController::indexAction` im Legacy-Backend holte mit `findBy(['scope' => …])` alle
44.482 Buchungen als volle Doctrine-Entities und verwarf davon die Haelfte erst in PHP. Das
sprengte beim Admin-Login das 1-GB-`memory_limit` in `JsonResponse.php` — vier HTTP 500 in
sieben Tagen. Ergaenzt in `camperfuchs-legacy-backend`:

- **Vorfilter in die Query statt `continue` in PHP** — 44.482 → 18.329 Entities, Peak >1 GB →
  553 MB, 500 → 200. Falle: **ohne `TRIM`** filtern, sonst weicht das Ergebnis vom PHP-Filter
  ab; `origCount` braucht eine eigene COUNT-Query.
- **Zugriffsfilter in die Query ziehen.** Jeder Vermieter lud alle 18.329 Buchungen *aller*
  Partner und verwarf sie per `AccessHelper` — 36 s fuer eine leere Antwort. Mit Join auf
  `article`/`station` und `st.id IN getLocations($user)`: 37,8 s → 0,2 s Query, live 5,8 s.
- **Die Regel dazu:** Der Query-Vorfilter muss eine *Obermenge* der AccessHelper-Regel sein und
  die PHP-Pruefung bleibt als Netz stehen — so kann er nie mehr freigeben, nur weniger laden.
  Vor dem Live-Schalten beide Varianten fuer mehrere echte Konten auf Ergebnis-Gleichheit
  pruefen, inklusive `domain_admin` und einem Konto mit leerem Ergebnis.
- **`cf-commit.sh` trackt nur `/usr/local/cf`, NICHT `/home/gaz/rent`.** Patches am Symfony-
  Backend laufen am Drift-Netz vorbei und brauchen Backup, Tafel-Eintrag und md5-Diff-Guard.

---

## cf-tafel 0.1.0 — 23.08.2026

**Neues, zweites Plugin im Marketplace:** `cf-tafel` — die Pflicht-Arbeitsweise fuer parallele
Claude-Sessions ueber die zentrale Tafel https://tafel.camperfuchs.de (anmelden, sperren,
Warteschlange "braucht Bjoern", Lagebild, Fingerabdruck-Register). Eine Skill mit den
curl-Rezepten; der Zugriffsschluessel liegt bewusst NICHT im Plugin, sondern in Bjoerns
.secrets-Ordner. Ersetzt das manuelle Skill-Kopieren in die Accounts B und C.

## v0.52.0 (2026-08-21)

**Warum eine Anfrage zwei Tage liegenblieb — und was man beim Nachforschen falsch machen kann.**

- `camperfuchs-legacy-backend`: **Eine Anfrage haengt am Standort, nicht am Fahrzeug-Besitzer.**
  Vorgang #1W2KWY lief ins Leere, weil Station 4045 (Hemer) weder `email` noch `mobil` hatte;
  `cf-nudge24` uebersprang ihn still (nur Log-Zeile), ueber drei Monate waren 6 Anfragen betroffen.
  Neu dokumentiert: Die Zuordnung Anfrage → Standort laeuft ueber `article_locations`, NICHT ueber
  `articles.station_id` (beim Fall zeigte `station_id` auf die gepflegte Schwester-Station, die
  Anfrage ging an die ungepflegte). Und „Fahrzeug vorhanden" heisst `public=1` + nicht `deleted` +
  `visible=1` — ein rohes `COUNT(*)` auf `articles` zaehlt Karteileichen und haette 11
  Dauer-Fehlalarme erzeugt, waehrend der echte Fall durchgerutscht waere. Dazu der neue Waechter
  `cf-station-mail-watch` (Cron taeglich 8:10, DRY-RUN Standard, Mail nur bei Treffern).
  Merksatz: Ein stilles `continue` in einer Automatik ist ein blinder Fleck — dahinter gehoert
  eine Meldung an einen Menschen, nicht nur eine Zeile im Log.

## v0.51.0 (2026-08-21)

**Was am 21.08. auf srv2 gelernt wurde — drei Fallen, die zusammen die halbe Grundlast der Box ausmachten.**

- `camperfuchs-relay-chat`: **Die Listenansicht fragt gesammelt, nicht je Zeile.** `chatList` rief
  für jede der bis zu 40 Zeilen einzeln `/api/bookings/<id>` auf — 112 Anfragen je Minute rund um
  die Uhr. Neuer Endpoint `/backend/cf-chatbulk.php` beantwortet alle IDs in einem Aufruf, nutzt
  dieselben `AccessHelper`-Methoden wie der Einzelabruf und liefert nur Flags, keine Kontaktdaten.
  Danach 8 Anfragen je Minute. Fällt je Zeile auf den alten Weg zurück, wenn er nicht antwortet.
- `camperfuchs-relay-chat`: **Ein Cache, dessen Fehler niemand sieht, ist kein Cache.** Der
  bestehende `caches.default`-Cache in `bkFetch` hat seit Mitte August nie gegriffen — Schlüssel
  auf einer fremden Domain, und der Hauptaufrufer läuft über workers.dev, wo die Cache-API
  wirkungslos ist. Alle Fehler landeten in leeren `catch`-Blöcken. Regel: nach dem Einbau messen,
  ob der Cache greift.
- `camperfuchs-projekt`: **Bilder ohne `Accept`-Header zu messen misst das Falsche.** Cloudflare
  variiert nach `Accept`; ohne Browser-Header bekommt man PNG statt WebP. Und Polish überspringt
  Dateien ab etwa 2 MB komplett — erkennbar am fehlenden `cf-polished`-Header.
- `camperfuchs-legacy-backend`: **Der Bild-Endpoint liefert ohne Breitenangabe das Original** —
  gefunden: 63,2 MB für ein Bild. Neuer Deckel auf 1600 px inklusive der Feinheiten (Format
  behalten wegen der Grundriss-Transparenz, opake PNGs zu JPEG, Rückfall aufs Original wenn
  `convert` scheitert).
- `camperfuchs-legacy-backend`: **`* */2` im Cron heißt jede Minute, nicht alle zwei Stunden.**
  Ein 17-GB-Sync startete dadurch 60-mal pro Stunde und stapelte sich; load 4,06 → 0,24. Bei
  „Server langsam" zuerst `ps` nach CPU sortieren, bevor Query oder Index verdächtigt werden.

## v0.50.0 (2026-08-20)

`camperfuchs-legacy-backend` — der Hinweis „Abweichung von Preisliste" und die Preis-Uebernahme.

- **Merksatz aufgenommen:** `getRatePositions()` liefert nur Miete + Servicegebuehr (+ Rabattzeile).
  Zubehoer steht in `articles.additions` und kommt getrennt; Gebuehren der neuen Buchungsstrecke
  kennt der Rechner gar nicht. Buchungs-Gesamtbetrag nie gegen diese Liste rechnen.
- Warum die Box zweimal falsch lag (Angular `stdPriceDiff()` und der Fix vom 05.08.), wie
  `cfPriceDiffFix v20260820pd2` es loest und was das an echten Vorgaengen gebracht hat (119 → 72).
- **Neuer Endpoint `/backend/cf-price-apply.php`** dokumentiert: uebernimmt die Preisliste
  serverseitig, laesst Zubehoer/Gebuehren/Versicherung/Zahlungen stehen, `dry=1` fuer die Vorschau,
  `force=1` bei bereits erfasster Zahlung. Ersetzt den alten Weg ueber die Fahrzeug-Kacheln.
- Drei Fallen: `*/` in PHP-Blockkommentaren, `pos()` ist im Legacy-Autoload belegt, und
  Testvorgaenge lassen sich wegen des `folders`-Selbstbezugs nicht hart loeschen (stornieren +
  archivieren statt DELETE).

---

## v0.49.0 (2026-08-20)

Konto-Wissen eingezogen und drei ueberholte Aussagen korrigiert (Abgleich der doppelt gefuehrten
Skills Konto vs. Plugin):

- `camperfuchs-verfuegbarkeits-flow`: neues Kapitel **„Wer verschickt welche Mail"** ganz oben.
  Am 20.08.2026 gegen den Live-Blueprint geprueft: 6030776 hat **59 Module**, **M22/M24/M10
  existieren nicht mehr**, im ganzen Szenario gibt es **kein `ActionCreateDraft`**. Die
  Zusage-/Absage-Mail an den Mietinteressenten schickt `cf-decmail.php` auf srv2 (Cron, Mailgun),
  nicht Make. Die alte System-Landkarte ist als historischer Stand gekennzeichnet. Restposten
  notiert: die NEIN-Info-Mail M5 verspricht im Text noch einen Gmail-Entwurf, den es nicht gibt.
- `camperfuchs-frontend-feature-shippen`: **Lint-Vorcheck vor dem Push** (ESLint laeuft im
  pr-build mit; `prefer-regexp-exec` liess Build 3813 durchfallen — spart eine 15-Minuten-Runde).
  Ausserdem die pauschale Aussage „PAT ist abgelaufen, kein REST mehr" ersetzt durch „PAT vorher
  testen" — der REST-Weg laeuft wieder, git-ueber-SSH ist der dritte Weg.
- `camperfuchs-legacy-backend`: PHP-Seiten-/`cf-*.js`-Addon-Architektur unter `/backend`
  (Auth per `X-Token`, `?v=`-Cache-Bust, signierte Vorgangslinks), **Vorgang ↔ Buchung**-
  Verlinkung inkl. Popup- und Anker-Falle, sowie das **Zahlungs-/Abrechnungs-Datenmodell**
  (`booking_payments` ist tot, Zahlungen sind negative `booking_positions` type=partial,
  `bookings.meta.cf_abr`, Provision 10 % netto, MySQL `-P25060`, `NOW()` in UTC). Beim Zugriff
  ergaenzt, was zu tun ist, wenn der Sandbox-Weg mangels `.secrets`/Key nicht geht (ssh/scp aus
  Git per Desktop Commander, base64-verpackt).
- `camperfuchs-plugin-sync`: Scheduled Task `camperfuchs-plugin-stand-check` (taeglich 8:30)
  beim Stand-Check vermerkt.

## v0.48.0 (2026-08-20)

- `camperfuchs-projekt`: neues Kapitel **Windows/PowerShell — JSON- und Config-Dateien schreiben
  (BOM-Falle)**. `Set-Content`/`Out-File`/`>` schreiben UTF-8 mit BOM und machen JSON damit
  unparsbar; Programme schreiben ihre Config danach oft mit Defaults neu, wodurch Einstellungen
  lautlos verschwinden. Richtiger Weg (`WriteAllText` + `UTF8Encoding($false)`), Backup- und
  Verifikations-Pflicht sowie der Hinweis, laufende Programme vorher zu beenden. Enthaelt ausserdem
  die `$`-Stripping-Falle bei durchgereichten PowerShell-Einzeilern (`.ps1` statt Einzeiler).

## v0.47.0 (2026-08-20)

- `camperfuchs-zahlungserinnerungen`: Wer welchen Erinnerungs-Schalter sehen darf. Die Anzahlung
  geht auf das Camperfuchs-Konto, deshalb ist ihre Spalte jetzt Admin-only; vorher konnte jeder
  Vermieter uns die eigene Anzahlungs-Erinnerung abdrehen. Der Restbetrag bleibt bewusst Opt-in
  mit Default aus (Bjoern, 20.08.2026). Dazu die Solo-Ansicht fuer Vermieter mit einem Standort,
  die Sperre des Hakens ohne gepflegte `cf_iban` (nur das Einschalten sperren!), das
  `?bank=1`-Antwortformat des Endpoints und das jsdom-Rezept zur browserlosen Verifikation.
- `camperfuchs-zahlungserinnerungen`: Neuer Abschnitt, warum PDF-Generator und Legacy-Backend
  "bezahlt" absichtlich verschieden rechnen (nur `payment`/`partial` vs. jede negative Position),
  inklusive Zahlenbild 2026: von 598 negativen Positionen sind 261 Rabatte ueber rund 35.000 EUR.
  Angleichen wuerde den Gesamtpreis-Bug vom 05.08.2026 zurueckbringen.

## v0.46.0 (2026-08-11)

**Neu: Skill `camperfuchs-relay-chat`** — Landkarte des maskierten Chats zwischen Vermieter und
Mietinteressent (Worker cf-mailstatus, Aliasse chat+/partner+/antwort+, D1 chat_map/chat_partner,
Seite /backend/nachrichten) plus die Fehlersuch-Reihenfolge.

Kern der Aufnahme ist eine teuer bezahlte Lehre vom 11.08.2026: Die Mailgun-Routen matchten nur
numerische Vorgangsschlüssel, der Reply-To trug aber die Buchungsnummer. Damit griff keine Route,
der catch_all schluckte die Mail still, und **jede** Kundenantwort ging verloren — ohne eine
einzige Fehlermeldung. Daraus die verallgemeinerte Regel: ein stiller Fallback ist gefährlicher
als ein lauter Fehler; wo weitergereicht wird, muss „passt zu nichts" eine Meldung erzeugen.

Ebenfalls dokumentiert: Anhänge laufen jetzt in beide Richtungen durch (Mail wie Web-Chat),
die numerische Buchungs-ID ist der einzig gültige Vorgangsschlüssel, und ein abweichender Preis
im Chat ist meist ein ungepflegter Saison-Zeitraum, kein Betrug.

## v0.45.0 (2026-08-11)

- camperfuchs-projekt (Make.com-Abschnitt): zweiter Fall der Meldung `Validation failed for
  1 parameter(s)` ergänzt — `Missing value of required parameter 'followAllRedirects'` kommt
  von einem per API/Blueprint gebauten HTTP-Modul, nicht von einem Gift-Bundle. Make setzt die
  Defaults nur in der UI, über die API müssen alle Mapper-Booleans explizit gesetzt sein; das
  Szenario stoppt dabei nicht, sondern schickt nur Alert-Mails. Dazu die Konvention für
  Wegwerf-Testszenarien (`ZZ <Zweck>-Test`, nach dem Test löschen) und der Hinweis, dass
  Alert-Mails dem Löschen nachlaufen → bei Fehlermail zuerst `scenarios_list` prüfen.

## v0.44.0 (2026-08-10)

- camperfuchs-kalender-sperre: Titel-Match läuft jetzt SERVERSEITIG fuzzy — neuer key-gated
  Endpoint srv2 `GET /api/automation/articles-by-landlord?email=&title=` (normalisiert,
  Tiers exact/contains/Orts-Suffix-Cut, gegen short_name UND articles.title). Make 6578305
  prüft nur noch `4.data.match.count` und sperrt mit `match.id`. Auslöser: "First Line" vs
  "FirstLine" (womo-winkler) lief in den Fallback. Repo Old Camperfuchs PR #1801.
  Außerdem: Hook per curl aus der Sandbox aufrufbar (alte Chrome-Pflicht-Note überholt).

## v0.43.0 (2026-08-07)
- **`camperfuchs-frontend-feature-shippen` erweitert: Stale-Branch-Falle bei alten PRs.**
  `mergeStatus: succeeded` heisst nur „textuell mergebar", nicht „semantisch richtig".
  Ein PR von altem main kann beim Merge neuere main-Aenderungen stillschweigend
  zurueckdrehen — genau daran starb PR 1732 zweimal im pr-build (`CustomerBookingControllerSpec`,
  `TooManyInvocationsError` auf `checkBookingPlausibility`, weil der Branch die 5-arg-Fassung
  ohne `preDayPickup` mitbrachte und `normalizeLegacyStationId()` mitgerissen haette).
  Neu im Skill: der Pflicht-Check (Branch-Tip gegen AKTUELLES main diffen, nicht gegen die
  Merge-Basis), die Regel „nicht rebasen, sondern auf aktuellem main neu aufsetzen"
  inkl. Schritt-fuer-Schritt-Rezept, die 40-Zeichen-Objekt-ID-Falle der Items-API, und
  wann ein Policy-Requeue ueberhaupt hilft (nur bei Flake/veraltetem Target) plus wo der
  brauchbare Build-Log haengt (am `Task`-Record, nicht am `Stage`-Record).
  Praxis: 1732 -> 1774 und 1537 -> 1776 nach diesem Muster ersetzt.

## v0.42.0 (2026-08-03)
- **Neu im Plugin: `camperfuchs-wp-droplet-ops`** — bisher nur Account-Skill (und dort read-only),
  jetzt hier gepflegt. Deckt die WP-Droplet 167.172.160.66 mit new.camperfuchs.de und
  edition.camperfuchs.de ab: SSH-Zugang, Klon-Runbook für neue Subdomains, Memory-Balance.
- **Neues Performance-Kapitel** aus dem Fall vom 03.08.2026 („edition extrem langsam", TTFB 9–11 s →
  0,44–0,55 s). Die Ursache war der **zu 100 % volle PHP-OPcache**: zwei komplette WooCommerce-Installs
  mit zusammen ~59.000 PHP-Dateien teilen sich einen 128M-Cache, hit_rate 20 %, dadurch ~2 s
  PHP-Bootstrap pro Seitenaufruf auf 2 Kernen. Fix: `99-cf-opcache.ini` mit 512M/64M/65407.
  Dazu die drei Folgeschritte — WP Super Cache im PHP-Modus auf beiden Sites (warmer Treffer 7–11 ms,
  Checkout/Warenkorb/wp-json ausgenommen, kein Cache für Eingeloggte), `DISABLE_WP_CRON` plus
  `/etc/cron.d/cf-wp-cron` (`HOME=/tmp` ist Pflicht), und ein Memory-Limit von 512M **nur** für
  `/wp-admin/`, `/wp-json/` und `admin-ajax.php` statt global — sonst kehrt die alte MySQL-OOM-Historie
  zurück.
- Aufgenommen: **wie man auf dieser Droplet überhaupt richtig misst** (`curl --resolve` statt
  Host-Header, warm/kalt trennen, parallele Requests), das OPcache-Status-Snippet, und die Falle, die
  in derselben Session zuschlug: **PowerShell expandiert `$Variablen` in SSH-Einzeilern** und hat damit
  die `wp-cache-config.php` auf beiden Sites zerschossen — immer der base64-Weg, immer vorher `cp -a`.
## v0.41.0 (2026-08-01)
- `camperfuchs-kontaktfreigabe`: neuer Abschnitt zum **Waechter `cf-freigabe-watch.php`** (Cron 9:45,
  DRY-RUN als Standard). Block A meldet Vorgaenge mit Vermieter-Zusage UND Zahlungseingang, bei denen
  die Kontaktdaten nicht freigegeben sind, mit Freigabe-Button auf den Make-Hook (kein Schluessel in
  der Mail). Block B meldet Freigaben, deren Kontaktdaten-Mail laut Worker `cf-mailstatus` nicht
  zugestellt wurde. Dazu die Falle, die im ersten Anlauf zuschlug: Block B muss gegen den neuen
  meta-Vermerk `cfContactMailTo` pruefen, nicht gegen `stations.email` - sonst meldet er Testversande
  und `nomail=1`-Freigaben als Zustellfehler. Und die Notiz, warum das Zustell-Badge aus der
  Dokumentenliste hier nicht greift (die Kontaktdaten-Mail ist kein Dokument).

## v0.40.0 (2026-08-01)
- `camperfuchs-frontend-feature-shippen`: neuer **Schritt 2b — Encoding-Guard**. Vor jedem Push
  auf UTF-8-Doppelkodierung prüfen (`grep -c -P 'Ã|…'`), am Bundle gegenprüfen
  (`\xc3\xa4` / `\xe2\x82\xac` = Mojibake, `\xe4` = korrekt), Ursache Windows-PowerShell
  `Invoke-RestMethod` (dekodiert ohne charset als ISO-8859-1), Reparatur-Rezept und die Warnung,
  absichtliche Mojibake-Beispiele nicht mitzureparieren.
  Anlass: PR 1645 vom 01.08.2026 hatte `QueryResultCard.tsx` doppelt kodiert, die Suchseite zeigte
  live `ab 169 â‚¬ / Nacht`. Fix per PR 1654/1655/1656.
- `CHANGELOG.md`: Zeichenkodierung repariert (war selbst doppelt kodiert, cp1252-Variante).

## v0.39.0 (2026-08-01)
- **camperfuchs-kontaktfreigabe** aktualisiert: die Kontaktdaten-Mail an den Vermieter verschickt
  seit heute der srv2-Endpoint `cf-contact-release.php` selbst ueber **Mailgun** (From noreply@,
  Reply-To office@), nicht mehr das Gmail-Modul in Make 6752917. Neuer Fallback `mieter=` +
  `vermieter=`: ohne Datastore-Datensatz sucht der Endpoint den Vorgang in der DB (Vorrang hat
  der mit `meta.vermieterDecision = "ja"`). Beide Router-Routen in 6752917 rufen jetzt nur noch
  den Endpoint, die Warnmail an b.dunker gibt es nur noch im Fehlerfall. Dazu neu in der Skill:
  Endpoint-Parameter (`nomail`, `to`, `undo`, `by`), Log-Felder (`via`, `cand`, `mail`, `to`),
  Test-Rezepte fuer beide Routen und die Falle, dass die alte Version 400/404 gar nicht loggte.

## v0.38.0 (2026-08-01)
- **Neu: Skill `camperfuchs-kontaktfreigabe`** - die komplette Kette, wann der Vermieter die
  Kontaktdaten des Mietinteressenten bekommt und wann das Backend den Vorgang demaskiert:
  Maskierungsregel im AccessHelper (inkl. der neuen Ausnahme `meta.cfContactReleased`), die vier
  Bausteine (Make 5482694 Datastore-Felder `vorgang`/`link`, 6030776 Freigabe-Button,
  6752917 Router mit Vermieter-Mail bzw. Warnmail, srv2-Endpoint `cf-contact-release.php`),
  das Verifikations-Rezept mit selbst signiertem JWT und die Cloudflare-Cache-Falle bei eigenen
  GET-Endpoints. Keine Schluessel im Text, nur Pfade.

## v0.37.0 (2026-08-01)

**Mail-Schalter liegen jetzt unter Einstellungen -> Benachrichtigungen (`camperfuchs-zahlungserinnerungen`)**

- Beide Erinnerungen (Anzahlung nach Zusage, Restbetrag vor Reisebeginn) werden an einer Stelle
  geschaltet: ein Modal mit einer Zeile je Standort und zwei Haken, Suchfeld ab 10 Standorten.
  Die Karte im Belegungskalender entfaellt.
- `cf-benachrichtigungen.js` haengt den Menuepunkt per DOM ins Einstellungen-Dropdown, wie es der
  Eintrag "€ Abrechnung" vormacht. Bewusst KEIN Bundle-Rebuild: der Azure-master hat gegenueber
  srv2 rund vier Jahre Drift, das Ergebnis waere identisch, das Risiko deutlich hoeher.
- Neue Falle: der Sticky-Kopf des Belegungskalenders zeichnet sich durch Overlays mit z-index 10000,
  obwohl elementFromPoint das Overlay meldet. Erst 2147483000 + isolation:isolate half.

---

## v0.36.0 (2026-08-01)

**Vermieter koennen die Anzahlungs-Erinnerung abschalten (`camperfuchs-zahlungserinnerungen`)**

- Neues **Opt-OUT** je Standort (`cf_zusage_opt.disabled`, Default AN, Schalter im Backend-Kalender
  ueber `cf-zusageopt.php` + `cf-zusageopt.js`). Bewusst anders als beim Restbetrag-Job, der ein
  Opt-IN hat: bei der Anzahlung geht das Geld an uns.
- Eigene Dateien statt Eingriff in die Nachbar-Skripte, die Karte wird per appendChild angedockt.
- Besitzpruefung ueber X-Token gegen /api/login (Loopback per CURLOPT_RESOLVE wegen des alten
  CA-Bundles auf srv2), setzen nur fuer eigene Standorte.
- Falle dokumentiert: die Script-Tags in der Backend-index.html tragen `type="text/javascript"` —
  ein Anker ohne das Attribut findet nichts und der Patch bricht ab.
- Ausserdem: der Job filtert Anhaenger ueber `articles.portals` aus.

---

## v0.35.0 (2026-08-01)

**Antwort-Buttons fuer Mieter (`camperfuchs-zahlungserinnerungen`)**

- Zusage-Mail (Make 6030776, Modul 22) und Zahlungserinnerung tragen jetzt drei Buttons:
  "Ich ueberweise in den naechsten Tagen" (10 Tage Ruhe), "Ich habe noch eine Frage" (5 Tage Ruhe),
  "Ich buche doch nicht" (Schluss, Info an office@ und Vermieter). Neuer Endpoint
  `cf-payanswer.php` im Backend-Webroot, Antworten in `cf_zusage_answer`.
- **Zwei Stufen sind Pflicht**, weil Mail-Clients Links vorladen: der Link zeigt nur eine Seite mit
  Bestaetigungs-Button, erst der POST schreibt.
- Zwei getrennte Signatur-Schluessel (Job und Make), damit der Blueprint-Schluessel nicht der Job-Schluessel ist.
- **Make kann HMAC:** `substring(sha256("zahle|" + 1.nr; "hex"; "<key>"); 0; 16)` liefert bitgleich dasselbe
  wie PHPs `hash_hmac` — in einem Wegwerf-Szenario verifiziert.
- Test-Rezepte ergaenzt: Modul 22 erzeugt nur einen Entwurf, laesst sich also per Webhook-Aufruf gefahrlos
  pruefen; Gmail-Suche indiziert keine href-Attribute, deshalb ueber sichtbaren Text pruefen.
- Ausserdem: der Job filtert jetzt auf `articles.portals` mit "cf", blueTrailer-Anhaenger fallen raus.

---

## v0.34.0 (2026-07-31)

**Neue Skill `camperfuchs-zahlungserinnerungen` — die zwei Zahlungserinnerungs-Jobs auf srv2**

- `cf-zusage-reminder.php` (neu, live seit 31.07., Cron 9:35): erinnert den Mieter, wenn eine
  Vermieter-Zusage vorliegt, aber **kein Zahlungseingang** verbucht ist. Stufen Tag 3 und Tag 7,
  Betrag 20 % Anzahlung bzw. voller Betrag unter 30 Tagen bis Reisebeginn.
- `cf-payreminder.php` (Cron 9:20): Restbetrag 40/30 Tage vor Reisebeginn, nur wo schon Geld ueber
  Camperfuchs floss, mit Station-Opt-in. Die Skill grenzt beide sauber gegeneinander ab.
- **Trigger-Wahrheit dokumentiert:** die Zusage steht seit 25.07.2026 in `bookings.meta` als
  `vermieterDecision: "ja"` plus `vermieterDecisionAt`; `type=2` (accepted) wird nicht benutzt;
  Zahlungseingang sind die negativen `booking_positions`, nicht `amountPaid`.
- Enthaelt Guards (Altbestands-Sperre, Overlap-Check, Dedupe-Tabellen), den srv2-Arbeitsweg
  (Git-ssh statt kaputtem Windows-ssh, base64-Block, scp, `php -l`, Dry-Run, `--preview`),
  die Textregeln fuer Kundenmails und die Parallel-Session-Falle.

---

## v0.33.0 (2026-07-30)

**Deploy-Stage bricht ab: Helm-Installer faellt still auf 3.1.2 zurueck (`camperfuchs-frontend-feature-shippen`)**

- Neuer Abschnitt zum am 30.07.2026 aufgetretenen Fehlschlag: Build-Stage gruen, Deploy-Stage
  sofort tot mit `Error: unknown flag: --dependency-update`. Ursache ist `HelmInstaller@1` ohne
  feste Version — der GitHub-API-Lookup schlaegt fehl und der Task faellt still auf seine
  Default-Version Helm 3.1.2 zurueck, die das Flag nicht kennt.
- Dauerhafter Fix ist im Monorepo: `helmVersionToInstall: '4.2.3'` in
  `ci/deploy-prod-pipelines.yml` und `ci/deploy-staging-pipelines.yml`. Nie auf `latest`
  zuruecksetzen; der Pin wirkt erst, wenn er bis in den jeweiligen Deploy-Branch gemergt ist.
- Rezept zum Neustart eines gescheiterten Deploys: Stage-Retry per REST antwortet 204, startet
  aber nichts — stattdessen die Deploy-Definition frisch queuen.
- Zwei Zeit-Fallen ergaenzt: der Deploy-Auto-Trigger kommt 1–3 Minuten verzoegert (nicht doppelt
  queuen), und die Approval-ID erscheint erst, wenn die Deploy-Stage wirklich wartet.

## v0.32.0 (2026-07-29)

**Übergabepunkt verschoben — Kontaktdaten erst nach Freigabe (`camperfuchs-verfuegbarkeits-flow`)**

- M60 ist aus der JA-Route von 6030776 **entfernt**. Ein JA ist nur eine Verfügbarkeitszusage;
  die Kontaktdaten gehen jetzt erst nach einem bewussten Klick raus.
- Neu: Freigabe-Szenario **6752917** (Hook 3469287, zweistufig gegen Scanner) und
  48h-Rückfall **6752962** (alle 3 h, „Zeitraum wieder frei" an den Vermieter statt Kontaktdaten).
- Status-Maschine in DS 131528: `ja` → `ja_freigegeben` / `ja_rueckfall`; Cutoff gegen Alt-Bestand.
- Warum keine Automatik auf „bezahlt": Anfrage-Fahrzeuge werden per Überweisung bezahlt — kein
  Systemereignis. Dokumentiert, damit es nicht nochmal vorgeschlagen wird.
- Datenstruktur 444568 war unvollständig: `telefon`, `ort`, `personen` wurden seit jeher still
  verworfen (Kontaktdaten-Mail ohne Telefonnummer, Personenfilter im Alt-Picker leer).
- Neue Make-Fallen: `SearchRecord` liefert `{{N.data.feld}}`; `date:`-Operatoren greifen nicht;
  `notexist` funktioniert nicht; Scheduling-`type`-Werte; `pg[limit]` max 100; keine
  Regex-Ersetzungen mit `\b` auf rohem Blueprint-JSON.
- Bemerkungs-Freitext wird in M2+M26 beim Rendern gefiltert (Rufnummern/E-Mails), Reisedaten
  bleiben stehen.

**Maskierung Phase 2b geschlossen (`camperfuchs-legacy-backend`)**

- Vorgangsansicht maskiert Kontaktdaten serverseitig für alle Nicht-Admins bei Anfrage-Typen
  (1/2/4); Buchungen bleiben unverändert sichtbar.
- Zwei Fallen dokumentiert: Schreibrichtung absichern (die UI schickt das ganze Objekt zurück)
  und Maskierung NACH dem Memcache-Set.
- Rollen-Realität: 241 Vermieter-Logins sind `ROLE_USER`, nicht `ROLE_STATION` — Regel gegen
  `isAdmin()` statt gegen eine Vermieter-Rolle.
- Frontend-Hinweis als Addon-Modul `cf-cmask` (cron-fest), inkl. Testschalter.

## v0.31.0 (2026-07-28)

- **`camperfuchs-projekt`: neuer Abschnitt „Datenbank-Migrationen (Flyway)".** Zwei Migrationen
  mit derselben Versionsnummer sind ein harter Startfehler („Found more than one migration with
  version X") — jeder neue Backend-Pod crasht, die ganze Umgebung antwortet 503, nicht nur das
  neue Feature. Am 27./28.07.2026 hat das staging lahmgelegt: zwei parallel entwickelte Branches
  vergaben beide `V2.1.15` (`booking_meta_utf8mb4` von Bahti und `station_request_days_off`).
  Ein einzelner Branch baut fuer sich immer gruen — auffallen kann es erst nach dem Merge.
  Aufgenommen sind die Regel (Nummer gegen den aktuellen `main`-Stand pruefen, nicht gegen den
  eigenen Branchpunkt), das Vorgehen bei Kollision (eigene Datei umbenennen), die Pflicht zur
  Idempotenz und der verwandte Fall `FlywayValidateException` bei `success=0`-Zeilen (History-Zeile
  reparieren statt Migration neu laufen lassen — in BEIDEN Datenbanken, staging und prod sind
  getrennt).

## v0.30.0 (2026-07-27)

- camperfuchs-legacy-backend: Umlaut-/Encoding-Falle dokumentiert (Doppel-Encoding in der
  master-Quelle wird vom Minifier zu literalen `\xc3`-Escapes = "ü" im UI; Pruef-Rezept,
  Golden-Bundle jetzt main.b99d8319) + Selbstheiler-Cron-Abschnitt (heilt jetzt auch
  cf-booking-suggest.js-Module cfABMD/cfRDO additiv, Konvention fuer neue Addon-Module).
- camperfuchs-kalender-sperre: Wochentags-Ausschluss-Button (rdo=1) auf der NEIN-Danke-Seite
  + restaurierter Kalender-Sperre-Button, neuer Endpoint /api/automation/request-days-off,
  Fallen: by-landlord braucht &size=500 (Vermieter >50 Fahrzeuge), DS-fahrzeug = Shortname.

## v0.29.0 — 2026-07-27

- **camperfuchs-cache-purge:** neuer Abschnitt „Dateien LÖSCHEN (Mediathek/Uploads)". Gelöschte
  WP-Uploads bleiben bis zu 30 Tage über den Cloudflare-Edge öffentlich abrufbar
  (`immutable, max-age=2592000`) — Löschen allein reicht nicht. Belegter Vorfall 27.07.2026:
  Mediathek leer, PDFs trotzdem HTTP 200 mit `cf-cache-status: HIT`. Enthält die Pflicht-Reihenfolge
  (löschen → purgen für beide Hosts → auf HTTP 404 verifizieren) und die Mess-Falle, dass zu viele
  parallele curls `000` liefern und wie „weg" aussehen.

## v0.28.0 — 2026-07-27

- `camperfuchs-verfuegbarkeits-flow`: M22-JA-Entwurf-Fix dokumentiert (get(map(ifempty(…; emptyarray))) wirft nicht mehr bei Fahrzeugen außerhalb by-landlord; M24-Fallback mit 21.mieter), Modulzahl 36→38, NEU: Abschnitt "Phase-4 decision-Call M99 entkoppelt" (M99 als eigene Router-3-Route — nie zurück in die lineare Kette, Filter/Ignore killen dort die ganze Nachverarbeitung), Test-Fallen ergänzt (131793-Record zwischen Läufen löschen, Ops-Zahlen als Diagnose, Make-REST-PATCH braucht Browser-UA).

## v0.27.0 -- 2026-07-22
- **projekt:** Falschaussage korrigiert — es gibt **ZWEI** Cloudflare-Tokens: `cloudflare-api-token.txt` (Zonen lesen + Snippets schreiben, **kein** Purge) und `cloudflare-purge-token.txt` (**kann purgen**, verifiziert `success:true`). Der bisherige Satz "Cloudflare-API-Token kann weiterhin NICHT purgen" galt nur fuer den ersten Token und hat wiederholt zu unnoetigen Workarounds gefuehrt.
- **cache-purge:** Purge-Token jetzt unter dem sprechenden Namen `.secrets/cloudflare-purge-token.txt` referenziert (historisch lag er als `Claude API BENUTZER API TOKEN.txt` vor, klingt nach Anthropic, ist aber Cloudflare).
- **Hinweis:** v0.26.0 war im Changelog, aber nie in `plugin.json` (dort stand weiterhin 0.25.0). Mit dieser Version sind Changelog und plugin.json wieder deckungsgleich.

## v0.26.0 -- 2026-07-21
- **frontend-feature-shippen:** Prod-Promote-Quelle explizit — Prod-PRs MÜSSEN von `staging` kommen (Policy `prod-check-source-branch-pipeline`/Def 14 verlangt SOURCE==staging), main→prod fällt durch.
- **projekt:** Backend-Konvention ergänzt — neue Spring-Endpoints setzen Statuscodes NICHT per `@ResponseStatus` (ControllerAdvisor-Catch-all übersteuert auf 500); gemappte Exceptions nutzen (ElementNotFoundException→404, BadRequestException→400, neue ForbiddenException→403 + Advisor-Handler).

## v0.25.0 -- 2026-07-21
- **legacy-backend:** Mail/DMARC Portal-Default-Absender-Falle ergaenzt. `MailHelper::send()` ohne `$from` nimmt den Portal-`senderEmail` als From; cf-Portal-Default `robot@camperfuchs.com` (.com) -> DMARC-Bounce. Wurzel-Fix: cf-Portal `senderEmail` -> `noreply@camperfuchs.de`; letzte .com-Codestelle in `UserHelper.php` bereinigt.

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
## 0.12.1 — 14.07.2026

- **BOM- und Validierungs-Fallen in `camperfuchs-plugin-sync` dokumentiert** — beide haben die
  Installation von 0.12.0 real scheitern lassen: PowerShells `Set-Content -Encoding UTF8` schreibt
  ein BOM (macht `plugin.json` ungueltig und die erste `.gitignore`-Regel unwirksam), und der
  Installer prueft ALLE Skills, nicht nur die geaenderten (hier kippte eine 1262-Zeichen-
  description von `nein-alternativen-anfragen`).
- **Neuer Pflichtschritt 4b:** vor dem Veroeffentlichen jede SKILL.md mit einem echten YAML-Parser
  pruefen (Laenge, Frontmatter, BOM) — nicht per Regex; eigene Regex-Checks lieferten Fehlalarme.
- **Mount-Cache-Falle ergaenzt:** die Sandbox kann eine veraltete Datei zeigen, waehrend Windows
  die korrekte hat. Windows ist massgeblich; frischer Dateiname umgeht den Cache.

---
## 0.12.0 — 14.07.2026

- **`camperfuchs-plugin-sync` ins Plugin migriert und geradegezogen.** Er beschrieb noch den
  obsoleten Browser-Upload-Weg („Upload file(s)"), nannte eine falsche lokale Kopie und kannte
  2 von inzwischen 9 Skills. Jetzt: git-Klon `F:\dev\cf-marketplace` + SSH-Push als echter Loop.
- **Packen jetzt nativ mit `tar.exe`** (verifiziert: 0 Backslash-Pfade, `plugin.json` oben).
  Die alte Regel „nur in der Sandbox zippen" ist überholt — sie galt nur gegen
  `Compress-Archive` / .NET `ZipFile`, die die ZIP-Spec verletzen.
- **Neue Sperrvermerke:** git läuft NICHT auf dem gemounteten Projektordner (`config.lock:
  Operation not permitted`) → ein Repo kann dort nie liegen; Zip auf dem Mount wird kaputt und
  `du -h` meldet dort fälschlich 0; kein Python auf dem Rechner (nur Store-Aliase);
  PowerShell-Einzeiler über DC verlieren `# Changelog — camperfuchs-kontext

Der hier dokumentierte Stand ist die **eine Wahrheit** für beide Seiten. Die aktuell gültige
Versionsnummer steht in `plugins/camperfuchs-kontext/.claude-plugin/plugin.json` und muss mit
dem obersten Eintrag hier übereinstimmen. Wer eine neue Plugin-Version baut, schreibt hier einen
Eintrag dazu — sonst gilt die Version als nicht veröffentlicht.

Check „bin ich aktuell?": installierte Plugin-Version mit dem obersten Eintrag vergleichen.

-Variablen → `.ps1` nutzen.
- Abgrenzung ergänzt: das private Archiv `cf-wissen` gehört **nie** in dieses geteilte Repo.

---
## 0.11.0 — 14.07.2026

- **Neue Skill `camperfuchs-sammelanfrage`** ins Plugin aufgenommen: System-Landkarte der
  Sammelanfrage + des Merkzettels (MerkzettelContext/localStorage `cf_merkzettel_v1`,
  `sammelanfrage.tsx`, `BookingCalculator` mit `merkMode`, Detailseite `?merk=1&merkLoc=`,
  Backend `fare` + `bookings/group`), Datenmodell, Endpoints und der „Weg 2"-Flow (eigener
  Reisezeitraum + Zubehoer JE Fahrzeug, live prod seit 08.07.2026, Merge `672680b5`).
- **Teuer gelernte Fallen dokumentiert:** `update()` ist auf `article`+`articleLocation` gekeyt —
  ein falsches/erfundenes `merkLoc` schreibt still nichts zurueck und sieht aus wie „Rueckweg
  kaputt"; `extras` speichert Zubehoer-**Namen**, die Checkboxen nutzen `index` (beide Seiten
  anfassen); `/sammelanfrage` per Direkt-URL haengt/404t (separate, vorbestehende Routing-Luecke,
  nicht Weg 2 — in-app navigieren); zwei `BookingCalculator`-Instanzen (Desktop + Mobile).
- **Browser-Verifikations-Fallen ergaenzt:** Screenshots timen auf den Fahrzeug-Detailseiten aus
  (CDP 30 s) → `get_page_text` nutzen; `read_page filter:interactive` verschluckt Elemente, die im
  Seitentext stehen; Sticky-Sidebar braucht `scroll_to {ref}`; Mobile-Optik ist nicht simulierbar
  (`resize_window` aendert `innerWidth` nicht).

---

## 0.10.0 — 09.07.2026

- **Neue Skill `camperfuchs-frontend-feature-shippen`** ins Plugin aufgenommen (Idee → live:
  richtige Komponente finden, Worktree off `origin/main`, PR-/Deploy-Kette, Verifikation).
- **Schritt 5 korrigiert (teuer gelernt 09.07.):** Der Live-Beleg per JS-Bundle-Fingerprint muss
  die Chunks über `/_next/static/<buildId>/_buildManifest.js` enumerieren. Seit PR #1303
  (`perf/code-split-datepicker`) werden Datepicker/BookingCalculator lazy nachgeladen und stehen
  NICHT im initialen HTML — wer nur das HTML scannt, schließt fälschlich „Fix nicht live".
  Ergänzt: i18n-Keys sind kein Komponenten-Marker, taugliche vs. untaugliche Fingerprints,
  „Quelle schlägt Bundle", PowerShell-Fallen (`$`-Stripping, `-LiteralPath`, abgeschnittene Ausgabe).
- **Repo-Struktur repariert:** Der vollständige Quellbaum (`plugins/`, `.claude-plugin/`) liegt jetzt
  im Azure-Repo. Vorher lagen dort nur flache Dateien (Browser-Upload konnte keine Unterordner) —
  dadurch waren die Versionen **0.7.0–0.9.0 nie veröffentlicht**; mit diesem Stand nachgezogen.
- **Pflege künftig per `git push` (SSH)** statt Browser-Upload → `quellbaum.zip`-Krücke entfällt.

## 0.9.0 — 23.06.2026

- `camperfuchs-verfuegbarkeits-flow`: **Rückfrage hat jetzt ein Freitext-Formular** (Modul 30, live 23.06.). Klickt der Vermieter „Rückfrage", kommt statt der reinen Bestätigungsseite eine Formularseite (CF-Palette) mit Textfeld „Deine Frage oder Anmerkung" → neuer Webhook-Param `frage`; Modul 7 (Björn-Info-Mail) zeigt den Text im Beige-Block. Router 11 jetzt VIER Routen (Modul 12 nur noch JA via Zusatz-Filter `aktion notequal rueckfrage`; Modul 30 = `aktion equal rueckfrage`). JA/NEIN unverändert. Doku: neue Sektion „Rückfrage-Formular: Modul 30", Params- und Aufgaben-Liste ergänzt.

## 0.8.0 — 16.06.2026

- `camperfuchs-projekt`: Stand-Updates seit 03.06. nachgezogen — Origin-TLS jetzt DNS-01/Cloudflare-renewt + CF-SSL "Full (strict)" (14.06.); Backend `max-http-header-size` 64KB gegen `/api/V1/articles` HTTP-400 "Suche nicht geladen" (#816, 16.06.); Consent vereinheitlicht (11.06.) + funktionierender SPC-Cache-Purge per REST `POST /wp-json/spc/v1/cache/purge`; Cache Reserve als 3. Ebene; prod-Gate min=1 (Björn allein freigabefähig); new.camperfuchs.de = neue Homepage (WP/Kadence); /de-Routing-Backlog #533-545 live + Sitemap-lowercase-Restproblem; lokale Dev-Umgebung F:\dev\camperfuchs.

## 0.7.0 — 15.06.2026

- `camperfuchs-verfuegbarkeits-flow`: NEIN-**Modul 20 ist jetzt ein Fahrzeug-Picker** (Variante B
  LIVE) — lädt die freien Fahrzeuge des Vermieters per `GET /api/V1/articles/by-landlord?email=`
  als antippbare Radio-Liste (inkl. Kennzeichen hinter dem Namen). Die frühere Notiz „Variante B
  nicht möglich / nur Freitext" wurde entfernt.
- Neues **Backend-Muster** dokumentiert: ein vermieter-eigenes Zusatzfeld NUR in `by-landlord`
  ausliefern — Feld in `ArticleOverviewVM` mit field-level `@JsonInclude(NON_NULL)`, NICHT in
  `from()` setzen, nur in `findArticlesByLandlordEmail` anreichern (`enrichWithLicensePlate`) →
  öffentliche `/api/V1/articles`-Suche bleibt ohne das Feld. Inkl. Kennzeichen-Beispiel (PR #788),
  Spaltennamen-Falle (`licensePlateNumber`→`number_plate`, `deactivated`→`deleted`) und
  Datenschutz-Hinweis (by-landlord ist öffentlich/ohne Login → Feld per E-Mail abfragbar).

## 0.6.0 — 15.06.2026

- `camperfuchs-verfuegbarkeits-flow`: **NEIN-Pfad bietet jetzt optional Alternativ-Zeitraum +
  Alternativ-Fahrzeug an.** Router 11 in 6030776 hat DREI Routen — neue Modul-20-Formular-Seite
  bei `aktion=nein` (zwei optionale Freitextfelder → `alt_zeitraum`/`alt_fahrzeug` per
  GET-Formular zurück an den Hook), Modul 12 (Button-Seite) auf `aktion≠nein` verengt.
  Mieter-Entwurf (M10) baut die Alternative über zwei `if()`-Fragmente ein (leerer String =
  falsy → kein hängender Satz), bleibt Entwurf; Björn-Info (M5) zeigt die Alternative. Variante B
  (Vermieter wählt eigene Fahrzeuge) bewusst verworfen — `/api/V1/articles` kennt keinen
  Vermieter, bräuchte Backend-Endpoint.
- Gelernt + dokumentiert: der Make-**Hook** ist aus der Sandbox per `curl` testbar (Test-Rezept
  headless ohne Chrome); `scenarios_run`-`data` mappt NICHT auf Webhook-Felder; riesige
  Mapper-Strings (M10-Signatur) nie von Hand neu tippen → Python-Edit auf Rohtext + Token-Reread.

## 0.5.0 — 08.06.2026

- Neuer Skill `camperfuchs-verfuegbarkeits-flow`: Betrieb/Änderung/Troubleshooting des
  Vermieter-Verfügbarkeits-Flows (Make 5482694 + 6030776) — System-Landkarte (alle IDs),
  zweistufiger Scanner-Schutz, Antwort-Tracking (Datastore 131528), Mieter-Entwurf bei NEIN,
  Test-Rezepte und Gotchas.
- Neu darin: **Fahrzeug-Link + Telefon als Info-Buttons** in der Verfügbarkeits-Mail (M2).
  Fahrzeug-URL wird OHNE Regex-Änderung im Mapper aus `{{7.fahrzeug}}` (Format „Name [URL]")
  gezogen (`split/first/trim` + `if/contains/replace/last`, Fallback Homepage) → kein
  Parser-Risiko. Plus Schema-Falle dokumentiert: `validate_blueprint_schema` lehnt top-level
  `scheduling`/`interface` ab → vor validate/update strippen (Blueprint = name/flow/metadata).

## 0.4.0 — 07.06.2026

- Neuer Skill `camperfuchs-agent-readiness`: prüft die KI-/Agenten-Auffindbarkeit von
  camperfuchs.de (Markdown for Agents, Link-Header→llms.txt, llms.txt) per curl und
  triagiert die Agent-Discovery-Standards (OAuth/OIDC, MCP-Server-Card, ACP, x402,
  DNS-AID, WebMCP, API-Catalog) nach ECHTEM Nutzen — statt blind isitagentready-Haken zu jagen.
- Merksatz verankert: Stubs ohne echtes Backend sind schädlich (Agent versucht→scheitert→Seite
  wirkt kaputt); isitagentready-„operation was aborted" = Checker-Timeout, kein echtes Loch.

## 0.3.0 — 07.06.2026

- Neuer Skill `camperfuchs-cache-purge`: gezielter Cloudflare-Edge-Purge für
  camperfuchs.de (Skript `scripts/cf_purge.sh` — einzelne URLs, mehrere, oder `--all`,
  automatische 30er-Blöcke). Löst das Edge-Layer-Propagationsproblem (APO `s-maxage` 1 Jahr).
- **Standing Rule** im Skill verankert: nach JEDEM selbst ausgelösten WP-API-Content-Edit
  die betroffene URL sofort
