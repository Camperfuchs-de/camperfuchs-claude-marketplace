---
name: camperfuchs-cache-purge
description: "Cloudflare-Edge-Cache von camperfuchs.de gezielt leeren, damit Content-Änderungen sofort bei Besuchern ankommen statt hinter der 1-Jahr-s-maxage-Kopie zu hängen. Diese Skill IMMER nutzen, wenn nach einer Inhaltsänderung die neue Version live gezogen werden soll — explizit ('Cache leeren', 'purgen', 'Seite ist noch alt', 'Edit kommt nicht an', 'Änderung nicht sichtbar', 'Cloudflare purge', 'frisch ziehen', 'Cache propagiert nicht') ebenso wie implizit: IMMER automatisch nach jedem WordPress-/WP-API-Content-Edit die betroffene(n) URL(s) purgen, ohne dass Björn extra danach fragt. Liefert: gezielten Edge-Purge per Skript (einzelne URLs, mehrere, oder alles), Verifikation des Cache-Status, und den ehrlichen Hinweis, wenn das Problem am Origin/SPC-Disk-Cache (Bahti) statt am Edge liegt."
---

# Camperfuchs Cache-Purge

Gezielter Cloudflare-Edge-Purge für camperfuchs.de. Löst das bekannte Propagations-Problem: Content-Edits liegen frisch am Origin, aber der Edge (APO, `s-maxage=31536000` = 1 Jahr) liefert weiter die alte Version.

## Wann nutzen

1. **Standing Rule (automatisch):** Nach JEDEM Content-Edit über die WP-REST-API (oder einer Inhaltsänderung, die ich selbst ausgelöst habe) sofort die betroffene(n) URL(s) purgen. Nicht auf Nachfrage warten — das gehört fest zum Edit-Workflow.
2. **Auf Zuruf:** „Cache leeren", „Seite ist noch alt", „purge mal /xyz", „Änderung kommt nicht an".

## Workflow

### Schritt 1 — Purgen

```bash
cd 05_Skills-Automation/camperfuchs-cache-purge/scripts
./cf_purge.sh /ihr-wohnmobil-ratgeber/faq/          # ein Pfad, www. wird ergänzt
./cf_purge.sh https://www.camperfuchs.de/a /b /c    # mehrere URLs
./cf_purge.sh --all                                 # ganzer Edge (nur wenn nötig)
```

Das Skript sucht `.secrets` selbstständig aufwärts und nutzt den purge-fähigen Token. Erwartete Ausgabe pro Block: `OK`.

### Schritt 2 — Verifizieren

```bash
curl -sS -D - -o /dev/null "https://www.camperfuchs.de/<pfad>" | grep -i cf-cache-status
```

Direkt nach Purge `MISS`/`EXPIRED`, beim zweiten Abruf wieder `HIT` → Edge ist frisch.

### Schritt 3 — Ehrlicher Caveat

Wenn die Seite **trotz** erfolgreichem Purge weiter alt aussieht, sitzt die alte Fassung im **SPC-Disk-Cache am Origin** (WordPress, über mehrere K8s-Pods). Das löst kein Edge-Purge → ist die systemische Bahti-Baustelle (Auto-Purge über alle Pods bzw. `s-maxage` senken). Siehe Memory `project_camperfuchs_cache_propagation`.

## Token (wichtig)

- **Purge-fähig:** der Token in `.secrets/cloudflare-purge-token.txt` (identisch mit der historisch falsch benannten Datei `.secrets/Claude API BENUTZER API TOKEN.txt` — klingt nach Anthropic, ist Cloudflare) → `POST /zones/835b24…/purge_cache` = `success:true`.
- **NICHT purge-fähig:** der Token in `.secrets/cloudflare-api-token.txt` → Auth-Fehler 10000. Der ist nur fürs Lesen/Settings.
- Token liegt NUR lokal in `.secrets`, niemals in Memory/Chat/Repo im Klartext.

## Alternativer Purge-Weg

Gleichwertig: SPC-REST-Endpoint `POST /wp-json/spc/v1/cache/purge` (Auth = WP App-Password bjoerndunker, Body `{}`) → `{"success":true}`. Nützlich, wenn der CF-Token mal nicht greift.

## Grenzen

- Cloudflare: max. 30 URLs pro Purge-Request → das Skript teilt automatisch in 30er-Blöcke.
- `--all` (purge_everything) sparsam einsetzen — kühlt den ganzen Edge aus, kurzzeitig langsamere TTFB bis re-warm.
