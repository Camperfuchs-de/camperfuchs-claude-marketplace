---
name: camperfuchs-zahlungserinnerungen
description: >-
  Die zwei Zahlungserinnerungs-Jobs von Camperfuchs auf srv2, Trigger, Deploy und Debugging.
  cf-zusage-reminder.php (Zusage erteilt, Zahlungseingang 0, Tag 3 + Tag 7, live seit 31.07.2026, 9:35)
  und cf-payreminder.php (Restbetrag 40/30 Tage vor Reisebeginn, nur wo schon Geld ueber CF floss,
  Station-Opt-in, 9:20). IMMER nutzen bei "Kunde hat nicht gezahlt", "Erinnerung an Anzahlung/Restbetrag",
  "Zusage erteilt aber kein Geld", "warum bekam Mieter X (k)eine Erinnerung", Aendern von Stufen, Text,
  Betragslogik oder Guards, Tabellen cf_zusage_reminder / cf_payreminder / cf_payreminder_opt,
  Cron /etc/cron.d/cf-zusage-reminder bzw. cf-payreminder, Zusage-Marker bookings.meta.vermieterDecision, oder
  Antwort-Buttons der Mieter (cf-payanswer.php). NICHT fuer Vermieter-Follow-ups bei offenen Anfragen
  (-> camperfuchs-provisions-leakage), Mail-Bounces/DMARC (-> camperfuchs-legacy-srv2-mail),
  Zustell-Badges (-> camperfuchs-mailstatus) oder die JA/NEIN-Buttons selbst
  (-> camperfuchs-vermieter-verfuegbarkeit-buttons).
---

# Camperfuchs Zahlungserinnerungen (srv2)

Zwei Scripts, klare Arbeitsteilung. Nie das eine im anderen nachbauen.

| | `cf-zusage-reminder.php` | `cf-payreminder.php` |
|---|---|---|
| Fall | Zusage da, **Zahlungseingang 0** | **Restbetrag** offen, Anzahlung ist da |
| Zeitpunkt | Tag 3 und Tag 7 nach Zusage/Buchungsanlage | 40 und 30 Tage vor Reisebeginn |
| Steuerung Vermieter | **gar nicht** - Admin-only, siehe unten | Opt-IN `cf_payreminder_opt.enabled`, Default AUS |
| Cron | `35 9 * * *` | `20 9 * * *` |
| State | `cf_zusage_reminder` | `cf_payreminder` |
| Empfaenger | Mieter, BCC b.dunker + Vermieter | Mieter, BCC b.dunker + Vermieter |

Beide: `/usr/local/cf/<name>.php`, Aufruf `sudo -u www-data php … [--live] [--only=<stationId>] [--preview=<bookingId>]`,
**Default ist DRY-RUN**. Kein Azure-PR, das ist Legacy. Aenderungen in den Worklog eintragen.

## Trigger-Wahrheit (teuer erarbeitet)

- **Die Vermieter-Zusage steht in `bookings.meta`**: `vermieterDecision: "ja"` plus `vermieterDecisionAt`.
  **Erst seit 25.07.2026.** Aeltere Zusagen sind nur im Make-Datastore 131528 (`status="ja"`) belegt und
  werden vom Job nicht erfasst. Bei "warum kam da keine Mail" zuerst das pruefen.
- `bookings.type=2` (accepted) wird **nicht** benutzt. Die Anfrage bleibt `type=1`, bis daraus in-place eine
  Buchung `type=3` wird. Also: Zusage != Buchung.
- **Zahlungseingang = negative `booking_positions`** (`-SUM(quantity*unit_price)` ueber die negativen Zeilen),
  Toleranz 1 EUR. `amountPaid` sagt NICHT, wer das Geld hat (siehe camperfuchs-partner-abrechnung).
  Rabatte sind ebenfalls negativ und zaehlen damit als "bezahlt" — bewusst die sichere Richtung,
  lieber eine Mail zu wenig als eine falsche.
- Faelliger Betrag = **20 % Anzahlung**, bei Reisestart in unter 30 Tagen der **volle Betrag**. Identisch zur
  JA-Mail aus Make 6030776, damit die Zahlen zusammenpassen. Konto: Rentanda GmbH, KSK Limburg,
  DE78 5115 0018 0000 0542 54, HELADEF1LIM, Verwendungszweck Name + Vorgangsnummer.

## Guards in cf-zusage-reminder (nicht wegoptimieren)

1. `SINCE=2026-07-01` — sonst mailt der Job den Altbestand an.
2. Kappe 25 Mails/Lauf, Dedupe ueber `cf_zusage_reminder` (booking_id + kind, UNIQUE).
3. **Overlap-Check**: hat derselbe Mieter in einer ueberlappenden Buchung schon gezahlt, wird geschwiegen
   (er hat ein Alternativfahrzeug genommen). Gleiche Denkweise wie die Ghost-Selbstheilung im
   No-Response-Task.
4. Anfrage, die durch eine echte Buchung ersetzt wurde, faellt raus — dann greift Fall B.
5. Vermieter-Direktbuchungen (weder `online=1` noch Zusage ueber uns) bleiben aussen vor, das ist nicht unser Geld.
6. Teststation 3891 raus, ausser mit `--only=3891`.

## Arbeitsweg

1. **Zugang**: Windows-ssh.exe ist kaputt. Nur `C:\Program Files\Git\usr\bin\ssh.exe` bzw. `scp.exe` mit
   `-o StrictHostKeyChecking=no -o "HostKeyAlgorithms=+ssh-rsa" -o "PubkeyAcceptedAlgorithms=+ssh-rsa"`,
   Key `.secrets/id_srv2_cf`, ausgefuehrt ueber `mcp__remote-devices__Windows-MCP__PowerShell`.
   Die Cloud-Sandbox hat Port 22 zu, `device_bash` hat kein Netz. Lange Befehle als base64-Block
   (`echo <b64> | base64 -d | bash`), stderr mit `2>$null` schlucken.
2. **DB-Zugriff** vom Server aus, Creds nie anfassen:
   `g(){ grep -m1 "$1" app/config/parameters.yml | sed "s/.*: *//" | tr -d "'\""; }` in `/home/gaz/rent`,
   dann `mysql -h$H -P$P -u$U -p$W $D -e "…"`.
3. **Datei aendern**: lokal bauen, `php -l`, dann per `device_commit_files` in den Projektordner und von dort
   mit `scp.exe` nach `/usr/local/cf/`. Groesse auf beiden Seiten vergleichen (Mount-Truncation).
   Danach auf dem Server `php -l` und einen **Dry-Run**.
4. **Text pruefen** vor jedem Scharfschalten: `--preview=<bookingId>` schickt beide Stufen nur an
   b.dunker@camperfuchs.de, ohne die Buchung zu markieren. Ankunft per Gmail-Suche `subject:VORSCHAU` belegen.
5. **Scharf schalten**: Kommentarzeichen in `/etc/cron.d/cf-…` entfernen, vorher `cp` als `.bak-<ts>`.
   Rollback: Cron-Datei loeschen, Script loeschen, `DROP TABLE cf_zusage_reminder`.

## Antwort-Buttons der Mieter (seit 01.08.2026)

Zusage-Mail UND Erinnerung tragen drei Buttons: *Ich ueberweise in den naechsten Tagen* (10 Tage Ruhe),
*Ich habe noch eine Frage* (5 Tage Ruhe, Info an office@), *Ich buche doch nicht* (Schluss, Info an
office@ und an den Vermieter). Antworten landen in `cf_zusage_answer`, der Job liest sie vor jedem Versand.

- **Endpoint:** `/home/gaz/rentanda/web/backend/cf-payanswer.php` → `https://www.camperfuchs.de/backend/cf-payanswer.php`.
  PHP im Backend-Webroot wird dort ausgefuehrt und ist oeffentlich erreichbar (Vorbild: cf-payreminder-opt.php).
- **Zwei Stufen sind Pflicht.** Mail-Clients und Scanner laden Links im Hintergrund vor. Der Link aus der
  Mail zeigt nur eine Seite mit Bestaetigungs-Button, erst der POST schreibt. Getestet: GET schreibt nichts,
  POST schreibt genau einen Datensatz.
- **Zwei Schluessel:** `/usr/local/cf/cf-answer.key` signiert die Job-Mails, `/usr/local/cf/cf-answer-make.key`
  die Links aus Make (der steht im Blueprint, deshalb getrennt). Der Endpoint akzeptiert beide.
  Signatur = `substr(hash_hmac('sha256', "<aktion>|<bookingId>", key), 0, 16)`.
- **Make-Seite:** Szenario 6030776, Modul 22 (Gmail-Entwurf "Gute Nachricht"), Button-Block vor dem Satz
  "Bei Fragen sind wir natuerlich jederzeit fuer dich da". Die Buchungs-ID ist dort als `{{1.nr}}` verfuegbar.
  Make kann HMAC: `{{substring(sha256("zahle|" + 1.nr; "hex"; "<key>"); 0; 16)}}` — verifiziert, liefert
  bitgleich dasselbe wie PHP.
- **Wie man die Make-Seite testet, ohne einen Kunden anzufassen:** Modul 22 erzeugt nur einen ENTWURF.
  Webhook direkt aufrufen: `hook.eu1.make.com/tu2xumx8...?aktion=ja&confirm=1&nr=533179&vermieter=b.dunker@camperfuchs.de&betreff=TEST&mieter=b.dunker@camperfuchs.de&vorname=Test`.
  Ein Datastore-Record ist nicht noetig, `1.mieter` reicht fuer den Filter.
- **Gmail-Suche indiziert keine href-Attribute.** Ob der Block im Entwurf steht, prueft man ueber sichtbaren
  Text (`list_drafts` mit "Ein Klick genuegt uns"), nicht ueber die URL. Fuer den Beweis, dass eine Make-Formel
  wirklich rechnet, lohnt ein Wegwerf-Szenario (Webhook → WebhookRespond mit der Formel, danach loeschen).
- **Mailgun-Click-Tracking** schreibt die Button-Links auf `email.mg.camperfuchs.de` um. Der Redirect
  funktioniert und die Zwei-Stufen-Logik bleibt wirksam.

## Textregeln

Du-Form, kein Druck, keine Reservierungsversprechen ausser dem etablierten "sobald deine Anzahlung da ist,
blocken wir das Wohnmobil verbindlich fuer dich". Jede Mail bekommt eine Ausstiegszeile ("wenn du dich anders
entschieden hast, kurze Antwort genuegt") und den Satz, dass sich die Mail mit einer schon getaetigten Zahlung
ueberschnitten haben kann. Betreffzeilen mit echten Umlauten, im HTML-Body Entities.

## Schalter der Vermieter: Einstellungen -> Benachrichtigungen (seit 01.08.2026)

Beide Erinnerungen werden an EINER Stelle geschaltet: Backend, Menue Einstellungen, Eintrag
"Benachrichtigungen". Das Modal zeigt je Standort eine Zeile mit zwei Haken:

| Spalte | Bedeutung | Semantik | Sichtbar fuer | Tabelle | Endpoint |
|---|---|---|---|---|---|
| Anzahlung | 3/7 Tage nach Zusage | Opt-OUT, Default AN | **nur Admin** | `cf_zusage_opt.disabled` | `cf-zusageopt.php` |
| Restbetrag | 40/30 Tage vor Reise | Opt-IN, Default AUS | Admin + Vermieter | `cf_payreminder_opt.enabled` | `cf-payreminder-opt.php` |

### Wer welchen Schalter sehen darf (Bjoern, 20.08.2026)

**Die Anzahlung geht auf das Camperfuchs-Konto, der Restbetrag auf das des Vermieters.** Daraus
folgt die Sichtbarkeit, und das ist keine Kosmetik: vorher konnte jeder Vermieter uns unsere
eigene Anzahlungs-Erinnerung abdrehen.

- **Anzahlungs-Spalte nur fuer Admins** (`state.admin`, aus `/api/login` -> `user.role === 'admin'`;
  moegliche Werte `admin` / `station` / `user`). Der Admin-Text sagt explizit "Geht auf das
  Camperfuchs-Konto, deshalb nur hier schaltbar".
- **Restbetrag bleibt Opt-IN mit Default AUS.** Am 20.08.2026 stand die Umstellung auf Opt-out zur
  Debatte und wurde bewusst verworfen: es ist das Geld des Vermieters, also seine Entscheidung.
  Nicht erneut vorschlagen, ohne ihn zu fragen.
- **Ein Standort, kein Admin -> Solo-Ansicht.** Keine Tabelle, kein Standortname, kein Suchfeld,
  nur der eine Schalter mit Erklaertext. Der typische Vermieter hat genau einen Standort, alles
  andere ist Ballast (`var solo = !state.admin && state.stations.length === 1`).
- **Ohne gepflegte `stations.cf_iban` ist der Restbetrags-Haken gesperrt** statt wirkungslos:
  `cf-payreminder.php` ueberspringt Vorgaenge ohne CF-Bankdaten kommentarlos
  (`if (!$r['cf_iban']) { $skipped[] = ...; continue; }`). Der Endpoint liefert dafuer mit
  `?stations=1,2&bank=1` die Form `{"1":{"optIn":false,"bank":true}}`; ohne den Parameter bleibt
  es bei der alten `{"1":false}`-Form (rueckwaertskompatibel).
  ⚠️ Gesperrt wird nur das EINschalten (`ok || r`) - ein gesetzter Haken muss abwaehlbar bleiben,
  sonst sperrt sich aus, wer die Bankverbindung spaeter entfernt.
- Verifikation ohne Browser: `bn.js` mit **jsdom** laden, `fetch` stubben und die vier Faelle
  durchspielen (Vermieter mit/ohne Bank, Vermieter mit zwei Standorten, Admin). Prueft Spalten,
  Haken-Zustaende und Sperren in Sekunden.
- Datei-Stand 20.08.2026: `cf-benachrichtigungen.js` `?v=20260820bn4`, Backups
  `.bak-cfbank-*` / `.bak-cfsolo-*` im selben Ordner. Der Selbstheiler `cf-ensure-addon.sh` fasst
  diese Datei NICHT an, das `?v` in der `index.html` bleibt also stehen.

- UI: `cf-benachrichtigungen.js` haengt einen `a.item` in `management-menu .ui.dropdown.item > .menu`
  (gleiche Technik wie der Menuepunkt "€ Abrechnung"). Kein Bundle-Rebuild noetig, und genau deshalb
  auch **nicht** ins Angular-Bundle einbauen: der Azure-master hat gegenueber srv2 ~4 Jahre Drift.
- Die alte Kalender-Karte (`cf-zusageopt.js`, `#cf-pr-panel` der Nachbar-Session) wird nur ausgeblendet,
  fremde Dateien bleiben unangetastet. Rollback = Script-Tag zurueckstellen.
- Besitzpruefung im Endpoint: X-Token gegen `/api/login`, setzen nur fuer eigene Standorte (sonst 403).
  Der Login-Aufruf laeuft per `CURLOPT_RESOLVE` auf 127.0.0.1, weil srv2 ein CA-Bundle von 2019 hat.
- Admins sehen alle Standorte (bei Bjoern 340), deshalb Suchfeld ab 10 Eintraegen.

## Was als "bezahlt" gilt: PDF-Generator vs. Legacy (gemessen 20.08.2026)

Die beiden Systeme rechnen **absichtlich verschieden**. Wer sie angleicht, baut den Bug vom
05.08.2026 wieder ein.

- **Legacy** (`Booking::getAmountPaid()` und die Jobs hier): **jede negative Position** zaehlt als
  Zahlung, egal welcher Typ. Grob, aber fuer die Erinnerungs-Logik die sichere Richtung - lieber
  eine Mail zu wenig als eine falsche.
- **PDF-Generator** (`pdfgenerator/document.js`, `istZahlungsPosition`): nur `type` `payment` oder
  `partial`. Ein Rabatt/Gutschein ist ebenfalls negativ, senkt aber den PREIS und ist keine
  Zahlung. Genau daran stand am 05.08.2026 ein um 50 EUR zu hoher Gesamtpreis im Dokument.

Zahlenbild CF-Buchungen seit 01.01.2026 (598 negative Positionen): `partial` 337 (echte
Anzahlungen), `individual` 144, `rent` 106, `discount` 7, `coupon` 4 - also **261 Rabatte ueber
rund 35.000 EUR**, die im Dokument niemals als "bereits eingegangen" auftauchen duerfen.

Zwei Punkte, die den Unterschied entschaerfen:

1. **Der offene Betrag stimmt in beiden Faellen.** Wird eine Zahlung faelschlich als Rabatt
   behandelt, sinkt der Preis um genau den Betrag, um den die Zahlung fehlt. Nur der ausgewiesene
   Gesamtpreis waere zu niedrig.
2. **Fehltypisierungen sind selten**: in acht Monaten eine Position "Anzahlung" mit `individual`
   statt `partial` und drei Gutscheine als `partial`.

Fazit: nicht angleichen. Wenn ueberhaupt, ein Waechter, der negative Positionen meldet, deren Typ
nicht zur Beschreibung passt ("Anzahlung" ohne `partial`, "Gutschein" mit `partial`).

## Bekannte Fallen

- **Sticky-Kalenderkopf zeichnet sich durch Overlays.** Ein Modal mit `z-index:10000` wurde vom
  Belegungskalender durchbrochen, obwohl `elementFromPoint` das Modal meldete. Erst
  `z-index:2147483000` + `isolation:isolate` half. Overlays im Backend immer gegen einen Screenshot
  pruefen, nicht nur per DOM-Abfrage.

- **Parallel-Sessions**: `cf-payreminder.php` und `cf-zusage-reminder.php` wurden am selben Abend von zwei
  Accounts gebaut. Fremde Datei nie nebenbei mitaendern, lieber eine eigene Datei plus eigene Tabelle plus
  eigenen Cron. Vor dem Anfassen `ls -la /usr/local/cf/` und auf frische mtimes achten.
- `php -l` gibt auf srv2 eine `soap`-Warnung aus, die ist harmlos, mit `grep -v 'PHP Warning'` filtern.
- Der Cron laeuft als `www-data`, deshalb liegen die Scripts unter `/usr/local/cf/` und NICHT unter
  `/home/gaz` (dort kommt www-data nicht rein).
