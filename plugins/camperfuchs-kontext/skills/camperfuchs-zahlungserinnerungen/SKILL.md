---
name: camperfuchs-zahlungserinnerungen
description: >-
  Die zwei Zahlungserinnerungs-Jobs von Camperfuchs auf srv2, Trigger, Deploy und Debugging.
  cf-zusage-reminder.php (Zusage erteilt, Zahlungseingang 0, Tag 3 + Tag 7, live seit 31.07.2026, 9:35)
  und cf-payreminder.php (Restbetrag 40/30 Tage vor Reisebeginn, nur wo schon Geld ueber CF floss,
  Station-Opt-in, 9:20). IMMER nutzen bei "Kunde hat nicht gezahlt", "Erinnerung an Anzahlung/Restbetrag",
  "Zusage erteilt aber kein Geld", "warum bekam Mieter X (k)eine Erinnerung", Aendern von Stufen, Text,
  Betragslogik oder Guards, Tabellen cf_zusage_reminder / cf_payreminder / cf_payreminder_opt,
  Cron /etc/cron.d/cf-zusage-reminder bzw. cf-payreminder, oder Fragen zum Zusage-Marker
  bookings.meta.vermieterDecision. NICHT fuer Vermieter-Follow-ups bei offenen Anfragen
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
| Opt-in | keins (unser Geld) | `cf_payreminder_opt.enabled=1` je Station, Default AUS |
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

## Textregeln

Du-Form, kein Druck, keine Reservierungsversprechen ausser dem etablierten "sobald deine Anzahlung da ist,
blocken wir das Wohnmobil verbindlich fuer dich". Jede Mail bekommt eine Ausstiegszeile ("wenn du dich anders
entschieden hast, kurze Antwort genuegt") und den Satz, dass sich die Mail mit einer schon getaetigten Zahlung
ueberschnitten haben kann. Betreffzeilen mit echten Umlauten, im HTML-Body Entities.

## Bekannte Fallen

- **Parallel-Sessions**: `cf-payreminder.php` und `cf-zusage-reminder.php` wurden am selben Abend von zwei
  Accounts gebaut. Fremde Datei nie nebenbei mitaendern, lieber eine eigene Datei plus eigene Tabelle plus
  eigenen Cron. Vor dem Anfassen `ls -la /usr/local/cf/` und auf frische mtimes achten.
- `php -l` gibt auf srv2 eine `soap`-Warnung aus, die ist harmlos, mit `grep -v 'PHP Warning'` filtern.
- Der Cron laeuft als `www-data`, deshalb liegen die Scripts unter `/usr/local/cf/` und NICHT unter
  `/home/gaz` (dort kommt www-data nicht rein).
