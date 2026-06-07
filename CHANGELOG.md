# Changelog — camperfuchs-kontext

Der hier dokumentierte Stand ist die **eine Wahrheit** für beide Seiten. Die aktuell gültige
Versionsnummer steht in `plugins/camperfuchs-kontext/.claude-plugin/plugin.json` und muss mit
dem obersten Eintrag hier übereinstimmen. Wer eine neue Plugin-Version baut, schreibt hier einen
Eintrag dazu — sonst gilt die Version als nicht veröffentlicht.

Check „bin ich aktuell?": installierte Plugin-Version mit dem obersten Eintrag vergleichen.

---

## 0.3.0 — 07.06.2026

- Neuer Skill `camperfuchs-cache-purge`: gezielter Cloudflare-Edge-Purge für
  camperfuchs.de (Skript `scripts/cf_purge.sh` — einzelne URLs, mehrere, oder `--all`,
  automatische 30er-Blöcke). Löst das Edge-Layer-Propagationsproblem (APO `s-maxage` 1 Jahr).
- **Standing Rule** im Skill verankert: nach JEDEM selbst ausgelösten WP-API-Content-Edit
  die betroffene URL sofort purgen (nicht auf Nachfrage warten).
- Hinweis: Purge-fähig ist nur der BENUTZER-Token (liegt lokal in `.secrets`, NICHT im Plugin);
  Edge-Purge deckt nicht den SPC-Disk-Cache am Origin (separates Bahti-Thema). Alternativer
  Weg: SPC-REST `POST /wp-json/spc/v1/cache/purge`.

## 0.2.0 — 03.06.2026

- Serving-Kette korrigiert (per DO-API + curl verifiziert): Live-WP-Backend =
  139.59.155.118 (Droplet `www.camperfuchs.de-wordpress`, ID 34020513) hinter
  LB 157.245.21.250 → K8s. `209.38.194.145` = `wp.` (NICHT live). Auch im
  wp-502-Runbook korrigiert.
- Neu im Projektkontext: E-Mail-Infrastruktur (Mailgun rentanda.com, Spam-Thema
  Kai/Mailtrack), Automatisierung (Make.com, Team 345711), Preis-Positionierung.

## 0.1.0 — 03.06.2026

- Erste Version: Skill `camperfuchs-projekt` (Architektur, Hosting, Repo, Caching,
  SEO/Schema, Performance, Subdomains, Design-Tokens, Konventionen) + Skill
  `wp-502-debug` (Notfall-Runbook).
