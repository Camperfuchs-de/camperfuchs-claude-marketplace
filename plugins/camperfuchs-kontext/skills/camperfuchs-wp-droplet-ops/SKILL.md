---
name: camperfuchs-wp-droplet-ops
description: >-
  Betrieb der WP-Droplet 167.172.160.66 (new-wordpress-camperfuchs) mit new.camperfuchs.de UND edition.camperfuchs.de - SSH-Zugang, Klon-Rezept, OOM/500-Debugging und Performance. IMMER nutzen bei: "new./edition. ist langsam/down/500/Database Error", "edition laedt ewig", TTFB-/Ladezeit-Klagen zu diesen Subdomains, "komme nicht in wp-admin (new./edition.)", Memory-Fatals im wp-admin-Dashboard, neue Subdomain-Kopie anlegen, vHost/SSL/certbot auf dieser Droplet, oder wenn per SSH auf die Droplet gearbeitet werden soll. Enthaelt: SSH-Rezept (Git-ssh + base64), Klon-Runbook (DNS bis certbot/noindex), das Performance-Kapitel (OPcache 512M, WP Super Cache, System-Cron, Admin-Memory nur fuer /wp-admin/ und /wp-json/), die Memory-Balance und die Fallen (Login-500 nach 302, 421-SNI, PowerShell frisst $Variablen, doppelte "stop editing"-Zeile). NICHT fuer www/K8s, srv2 (-> camperfuchs-legacy-srv2-mail) oder Kadence-Content per REST.
---

# Camperfuchs WP-Droplet-Ops (new. + edition.)

## Die Maschine

| Was | Wert |
|---|---|
| Droplet | `new-wordpress-camperfuchs`, DO-ID **528117386**, FRA1, 7,8 GB RAM, **nur 2 CPU-Kerne** |
| IP | **167.172.160.66** |
| Sites | `new.camperfuchs.de` -> `/var/www/html`, DB `wordpress` * `edition.camperfuchs.de` -> `/var/www/edition`, DB `edition` |
| Stack | Ubuntu 22, Apache mpm_prefork + mod_php 8.3, MySQL lokal, wp-cli, certbot, UFW (nur 22/80/443) |
| DB-User | `wordpress`@localhost (beide DBs), Root-PW-Datei `/root/.digitalocean_password` |
| WP-Login | Beide Sites identisch (edition = DB-Klon): User `b.dunker`, App-PW `.secrets/new-camperfuchs-wordpress-app-password.txt` |
| DNS | CF-Zone camperfuchs.de, new. + edition. = A-Records **DNS-only** (nicht proxied!) - also **kein Cloudflare-Edge-Cache** wie bei www |

Beide Sites sind site-weit **noindex** (blog_public=0). Vor Indexierbar-Schalten an Duplicate-Content denken (new. vs. edition. vs. www).

## SSH-Zugang

Aus der Sandbox ist Port 22 der Droplet **nicht erreichbar** - der Weg fuehrt ueber Bjoerns PC:
Windows-MCP-PowerShell + **Git-ssh** (`C:\Program Files\Git\usr\bin\ssh.exe`), weil `windows-ssh.exe` kaputt ist.

```powershell
$k = Join-Path $env:TEMP "id_new_cf"
Copy-Item "...\Camperfuchs Tech & Produkt\.secrets\id_new_cf" $k -Force
icacls $k /inheritance:r /grant:r "$($env:USERNAME):(R)" | Out-Null
& "C:\Program Files\Git\usr\bin\ssh.exe" -i $k -o StrictHostKeyChecking=no -o BatchMode=yes root@167.172.160.66 "<befehl>"
```

**Befehle IMMER als base64-Block schicken**, nie als Inline-String (siehe Fallen). Skript lokal in der
Sandbox schreiben, `base64 -w0`, dann:
`echo $b | base64 -d > /tmp/x.sh; bash /tmp/x.sh 2>&1`

Zum Aufraeumen braucht der Temp-Key erst wieder Vollzugriff: `icacls $p /grant:r "$($env:USERNAME):(F)"`, dann `Remove-Item`.

Falls der Key je nicht mehr geht: DO-Web-Konsole direkt als Tab oeffnen
(`https://cloud.digitalocean.com/droplets/528117386/terminal/ui/`, root, ohne Passwort) - der Button
oeffnet sonst ein Popup ausserhalb der MCP-Tab-Gruppe. Login bei DO muss Bjoern machen.

## Richtig messen (sonst misst man Unsinn)

- Von aussen: `curl -s -o /dev/null -w "ttfb=%{time_starttransfer} total=%{time_total}\n" https://edition.camperfuchs.de/`
- Auf dem Server: **immer** `curl -k --resolve <host>:443:127.0.0.1 https://<host>/`.
  `curl -H "Host: ..." http://127.0.0.1/` liefert nur den 301, und ueber HTTPS mit Host-Header
  kommt 421 (SNI-Mismatch) - beides sagt nichts ueber die Seite aus.
- Warm/kalt trennen: ersten Request nach einem Reload wegwerfen, erst ab dem zweiten messen.
- Gleichzeitigkeit testen, nicht nur einzeln: 6-10 parallele Requests. Auf 2 Kernen zeigt sich
  das Problem erst dort.

## Performance-Runbook (Stand 03.08.2026)

Damals gemeldet: "edition extrem langsam", extern **TTFB 9-11 s**. Danach **0,44-0,55 s extern,
7-11 ms serverseitig**. Die vier Stellschrauben, in der Reihenfolge ihrer Wirkung:

### 1. OPcache - der haeufigste Grund, und er ist unsichtbar

Auf der Droplet liegen **zwei komplette WooCommerce-Installs** (~59.000 PHP-Dateien zusammen), die
sich **einen** OPcache teilen. Mit dem Debian-Default (128M) laeuft er permanent ueber: gemessen waren
`used=128M / free=0M`, interned strings ebenfalls voll, **hit_rate 20 %** (633k Hits gegen 2,49 Mio.
Misses). Folge: fast jede Datei wird bei jedem Request neu kompiliert, ~2 s PHP-Bootstrap pro
Seitenaufruf - und bei der kleinsten Gleichzeitigkeit staut es auf 10 s.

Status auslesen (Wegwerf-Datei, danach loeschen):

```php
<?php $s=opcache_get_status(false); $c=opcache_get_configuration();
echo $s['opcache_statistics']['num_cached_scripts'], " von ", $c['directives']['opcache.max_accelerated_files'], "\n";
echo "hit_rate=", round($s['opcache_statistics']['opcache_hit_rate'],2), "\n";
echo "mem_free_MB=", round($s['memory_usage']['free_memory']/1048576,1), "\n";
echo "interned_free_MB=", round($s['interned_strings_usage']['free_memory']/1048576,1), "\n";
```

`free_memory` nahe 0 oder hit_rate unter ~90 % = Befund. Fix in
`/etc/php/8.3/apache2/conf.d/99-cf-opcache.ini` (99- gewinnt gegen 10-opcache.ini):

```
opcache.memory_consumption=512
opcache.interned_strings_buffer=64
opcache.max_accelerated_files=65407
```

Danach `apache2ctl configtest && systemctl reload apache2`, dann 5-6 Requests zum Warmlaufen, erst
dann messen. **Das kollidiert NICHT mit der Memory-Balance weiter unten** - OPcache-SHM wird einmal
global belegt, nicht pro Apache-Worker.

### 2. Page-Cache (WP Super Cache) - seit 03.08.2026 auf beiden Sites aktiv

Vorher gab es gar keinen, und weil die Subdomains DNS-only laufen, auch keinen Edge-Cache. Konfiguration
steht in `wp-content/wp-cache-config.php`:

- `$cache_enabled = true; $super_cache_enabled = true; $wp_cache_mod_rewrite = 0;` (PHP-Modus, kein .htaccess-Gefummel)
- `$cache_max_time = 1800;` - zusaetzlich purged WP bei jedem Speichern
- `$wp_cache_not_logged_in = 2;` - eingeloggte Nutzer bekommen NIE eine Cache-Seite
- `$cache_rejected_uri` enthaelt `/cart`, `/checkout`, `/my-account`, `/warenkorb`, `/kasse`, `/mein-konto`, `wp-json`
- `wp-content/cache` gehoert www-data

Warmer Treffer liegt bei 7-11 ms. Verifizieren: zweiter Request enthaelt den Kommentar
`Cached page generated by WP-Super-Cache`; `/checkout/` darf ihn NICHT enthalten; ein Request mit
`wordpress_logged_in_*`-Cookie auch nicht; die Cache-Datei darf kein `admin-bar` enthalten.
Purge testen: `wp --allow-root eval 'wp_cache_clear_cache();'` und einmal `wp post update <id>`.

`wp super-cache enable` gibt es als wp-cli-Befehl **nicht** - direkt die Config-Datei setzen.

### 3. WP-Cron als echter System-Cron

`DISABLE_WP_CRON` war auf beiden Sites nicht gesetzt, der WooCommerce Action Scheduler lief jede
Minute ueber Besucher-Requests. Jetzt: `define( 'DISABLE_WP_CRON', true );` in beiden wp-config.php
plus `/etc/cron.d/cf-wp-cron`:

```
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOME=/tmp
* * * * * www-data /usr/bin/wp --path=/var/www/html cron event run --due-now >/dev/null 2>&1
* * * * * www-data /usr/bin/wp --path=/var/www/edition cron event run --due-now >/dev/null 2>&1
```

`HOME=/tmp` ist Pflicht, sonst bricht wp-cli als www-data ab. Kontrolle: `wp cron event list` muss
`wp_cache_gc` und `action_scheduler_run_queue` zeigen.

### 4. Memory-Limit nur fuer Admin/REST

Symptom: `Allowed memory size of 268435456 bytes exhausted` im `<sub>-error.log`, ausgeloest von
Dashboard-Widgets (SimplePie-Feed, `class-wp-rest-server.php`, `kadence-blocks/.../Shutdown_Collection.php`).
Grund: `WP_MAX_MEMORY_LIMIT=512M` greift nur ueber `wp_raise_memory_limit('admin')` im klassischen
Admin - die `/wp-json/`-Aufrufe des Dashboards bleiben bei den 256M der php.ini.

Fix in beiden wp-config.php, vor der **letzten** "stop editing"-Zeile:

```php
if ( ! empty( $_SERVER['REQUEST_URI'] ) && preg_match( '#/wp-admin/|/wp-json/|admin-ajax\.php#', $_SERVER['REQUEST_URI'] ) ) {
	@ini_set( 'memory_limit', '512M' );
}
```

Bewusst **nicht** global in der php.ini - das Frontend bleibt bei 256M, sonst kommt die OOM-Historie
zurueck. Verifizieren mit einer Wegwerf-Datei im Webroot, die `wp-load.php` einbindet und
`ini_get('memory_limit')` ausgibt: ohne `/wp-json/` in der URL 256M, mit 512M.

### Erst danach an anderes denken

Bot-Traffic, MySQL und RAM waren am 03.08. **nicht** die Ursache (10-100 Requests/min, 3,5 von 7,8 GB
belegt, Swap unberuehrt). Reihenfolge beim Suchen: `uptime` + `free -h` + `ps aux --sort=-%cpu`,
dann OPcache-Status, dann `awk` ueber `<sub>-access.log` fuer Requests pro Minute und Top-IPs.
Ein `load` von 3+ bei zweistelligen Requests pro Minute heisst: pro Request wird zu viel CPU verbrannt,
nicht zu viel Traffic.

## Runbook: WP auf neue Subdomain klonen

Erprobt am 09.07.2026 (edition.). Reihenfolge einhalten, jeder Schritt ~1 SSH-Call:

1. **DNS:** CF-API (Token `.secrets/cloudflare-api-token.txt`): A-Record `<sub>` -> 167.172.160.66, **proxied=false**.
2. **DB:** `mysql -e "CREATE DATABASE <sub>; GRANT ALL ON <sub>.* TO 'wordpress'@'localhost'"`, dann `mysqldump --single-transaction wordpress | mysql <sub>`.
3. **Dateien:** `rsync -a --delete /var/www/html/ /var/www/<sub>/`, in `wp-config.php` DB_NAME umstellen.
4. **URLs:** `cd /var/www/<sub> && wp --allow-root search-replace 'new.camperfuchs.de' '<sub>.camperfuchs.de' --all-tables` (erwischt auch guid/siteurl/home).
5. **noindex sicherstellen:** `wp --allow-root option get blog_public` (0 = noindex).
6. **vHost:** `/etc/apache2/sites-available/<sub>.conf` (Muster: edition.conf), `a2ensite` + `apache2ctl configtest` + reload.
7. **SSL:** `certbot --apache -d <sub>.camperfuchs.de -n`. DNS muss schon aufloesen.
8. **Verifizieren von aussen:** Startseite 200, robots-Meta `noindex`, `grep -c new.camperfuchs.de` im HTML = 0, HTTP->HTTPS 301, neue Site UND new. testen.
9. **Neu seit 03.08.:** Der Klon erbt Page-Cache und wp-config-Bloecke mit. Danach `wp-content/cache`
   auf www-data setzen und die Zeile fuer den Klon in `/etc/cron.d/cf-wp-cron` ergaenzen.

## Memory-Balance (NICHT blind hochdrehen!)

Historie: MySQL wurde **87x** vom OOM-Killer gekillt. Ursache: MaxRequestWorkers 150 x 200-300 MB/Worker
weit ueber dem RAM. Ein globaler memory_limit-Bump auf 512M hat es verschaerft. Stabile Konfiguration:

- `/etc/php/8.3/apache2/php.ini`: `memory_limit = 256M` (global bleibt es dabei!)
- beide `wp-config.php`: `WP_MEMORY_LIMIT=256M`, `WP_MAX_MEMORY_LIMIT=512M` + der REST-Block von oben
- `/etc/apache2/mods-enabled/mpm_prefork.conf`: `MaxRequestWorkers 25`, `MaxConnectionsPerChild 1000`
- 2G Swapfile `/swapfile` (in fstab)

Bei 500 / "Error establishing a database connection": erst `journalctl -u mysql --since '15 min ago'`
+ `free -h` + `ps aux --sort=-rss | head` - fast immer OOM, nicht die DB selbst. MySQL restartet selbst.

## WPCode-Snippets aendern (Shortcodes wie das Haendlerverzeichnis)

Die Shortcodes auf edition. (z.B. `[cf_haendlerverzeichnis]`) leben NICHT in einem Plugin oder in
`functions.php`, sondern als WPCode-Snippets: Plugin `insert-headers-and-footers`, Post-Type
`wpcode`. Das Haendlerverzeichnis ist Post **2472** (~113 KB PHP+CSS+JS). Zwei Fallen kosten sonst
garantiert eine Stunde (beide am 02.09.2026 erlebt):

- **`wp post update` ohne `--user=1` verschluckt den PHP-Code still.** Ohne User-Kontext greift
  KSES und strippt alles; wp-cli meldet dann nur `Warning: Inhalt, Titel und Textauszug sind leer`
  und der Post bleibt unveraendert. Kein Fehler, kein Exit-Code. **Immer `--user=1` anhaengen**,
  dann greift `unfiltered_html`. Fallback, falls es weiter klemmt: per SQL an WordPress vorbei.
- **WPCode liefert aus einem Array-Cache aus, nicht aus dem Post.** Die Option `wpcode_snippets`
  (~116 KB, serialisiertes Array) haelt eine Kopie des Codes. Wer nur den Post 2472 aendert,
  sieht im Frontend **nie** eine Aenderung - auch nach jedem Cache-Purge nicht. Die Option muss
  mitgepatcht werden, und zwar per PHP (nicht per SQL-String-Replace, sonst zerreisst die
  Serialisierung an den Laengenangaben):

```bash
cat > /tmp/p.php <<'PHP'
<?php
$o = get_option('wpcode_snippets'); $n=0;
$walk = function(&$v) use (&$walk,&$n) {
  if (is_array($v)) { foreach ($v as &$x) { $walk($x); } return; }
  if (is_string($v) && strpos($v,'<ANKER>')!==false) { $v=str_replace('<ALT>','<NEU>',$v); $n++; }
};
$walk($o);
if ($n) { update_option('wpcode_snippets',$o); }
echo "ersetzt: $n
";
PHP
wp --allow-root eval-file /tmp/p.php   # danach wp cache flush + Supercache-Verzeichnis leeren
```

Reihenfolge, die funktioniert: Post 2472 patchen (mit `--user=1`) **und** die Option patchen,
dann `wp cache flush` + `rm -rf wp-content/cache/supercache/<host>/*`. Erst dann live pruefen.
Zum Wiederfinden: `wp db query "SELECT ID,post_title FROM wp_posts WHERE post_type='wpcode'"`.

## Fallen

- **PowerShell frisst `$Variablen` in SSH-Einzeilern.** `sed -i 's/^$cache_enabled.../'` wurde zu
  `sed -i 's/^ .../'` und hat am 03.08. die `wp-cache-config.php` auf beiden Sites mit Parse-Error
  zerschossen. Immer der base64-Weg, und **vor jedem sed ein `cp -a <datei> <datei>.bak_<datum>`**.
- **"Komme nicht in wp-admin"** heisst oft NICHT falsches Passwort: access.log zeigt POST wp-login
  **302 (= Login OK)**, danach GET /wp-admin **500** (Memory-Fatal). Immer
  `/var/log/apache2/<sub>-error.log` lesen, bevor an Creds gedreht wird.
- **curl ueber 127.0.0.1 mit Host-Header gegen HTTPS liefert 421** (SNI-Mismatch) - kein Fehler der Site.
- **wp-config hat ZWEI "stop editing"-Zeilen** (DO-One-Click: Zeile ~93 "Add any custom values",
  Zeile ~100 die echte). Beim Einfuegen `tail -1` nehmen, nicht `head -1`, sonst landet der Block
  an der falschen Stelle oder doppelt.
- **Klon teilt Plugins/Cron/Mail:** wpsmtp und Cron laufen auf dem Klon mit und koennen echte Mails
  senden; bei Bedarf dort deaktivieren.
- **fail2ban-Jails** `wordpress-hard/-soft` + `sshd` aktiv - nach vielen Fehl-Logins IP-Ban pruefen
  (`fail2ban-client status wordpress-hard`).
- **WPCode-Snippet geaendert, aber nichts passiert?** Post allein reicht nicht, die Option
  `wpcode_snippets` haelt eine Kopie -> eigener Abschnitt oben.
- Kadence-/REST-Content-Mechanik (Seiten bauen, Meta-Fallen) steht NICHT hier -> Memory
  `project_new_camperfuchs_de` (gilt 1:1 auch fuer edition).
