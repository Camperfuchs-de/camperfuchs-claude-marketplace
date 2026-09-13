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
export CF_SESSION=A7                                # eigenes Tafel-Kürzel, landet im Protokoll
./cf_purge.sh /ihr-wohnmobil-ratgeber/faq/          # ein Pfad, www. wird ergänzt
./cf_purge.sh https://www.camperfuchs.de/a /b /c    # mehrere URLs (30er-Blöcke automatisch)
```

**`--all` ist keine Option für Inhaltsänderungen.** Das Skript verlangt seit dem 13.09.2026
zusätzlich `--wirklich` und erklärt beim Abbruch, warum. Details unten unter „Purge-Disziplin".

Jeder Purge schreibt eine Zeile nach `scripts/cf_purge.log` (Zeitpunkt, `CF_SESSION`,
Benutzer@Host, Modus, Anzahl). Cloudflare selbst protokolliert Purges **nicht** im Audit-Log —
am 13.09.2026 geprüft, deshalb das eigene Protokoll.

Das Skript sucht `.secrets` selbstständig aufwärts und nutzt den purge-fähigen Token. Erwartete Ausgabe pro Block: `OK`.

### Schritt 2 — Verifizieren

```bash
curl -sS -D - -o /dev/null "https://www.camperfuchs.de/<pfad>" | grep -i cf-cache-status
```

Direkt nach Purge `MISS`/`EXPIRED`, beim zweiten Abruf wieder `HIT` → Edge ist frisch.

### Schritt 3 — Ehrlicher Caveat

Wenn die Seite **trotz** erfolgreichem Purge weiter alt aussieht, sitzt die alte Fassung im **SPC-Disk-Cache am Origin** (WordPress, über mehrere K8s-Pods). Das löst kein Edge-Purge → ist die systemische Bahti-Baustelle (Auto-Purge über alle Pods bzw. `s-maxage` senken). Siehe Memory `project_camperfuchs_cache_propagation`.

## Sonderfall: Dateien LÖSCHEN (Mediathek/Uploads) — Löschen allein reicht NICHT

Wenn eine Datei nicht geändert, sondern **entfernt** werden soll (typisch: PDFs, die temporär über die WP-Mediathek verteilt wurden), ist das Löschen in WordPress nur der halbe Weg. `/wp-content/uploads/...` wird mit `cache-control: public, immutable, max-age=2592000` ausgeliefert und liegt danach **30 Tage** im Cloudflare-Edge — die Datei ist nach dem Löschen weiter öffentlich abrufbar.

Belegter Vorfall 27.07.2026 (Nürnberger-Briefversand, 27 Versicherungs-PDFs mit Namen, Kennzeichen, Beiträgen und Kontoinhaber-Daten): WP-Mediathek `?search=NBG-` lieferte bereits 0 Treffer, die URLs kamen trotzdem mit HTTP 200, `cf-cache-status: HIT`, `age 3039`. Erst der gezielte Purge machte daraus 404.

Pflicht-Reihenfolge beim Entfernen:

1. WP-Medien löschen (`DELETE /wp-json/wp/v2/media/<id>?force=true`), bis `?search=<präfix>` → 0 Treffer.
2. **Purgen** — alle betroffenen Datei-URLs, und zwar für **beide Hosts** (`https://www.camperfuchs.de/...` UND `https://camperfuchs.de/...`), sonst bleibt eine Variante im Cache stehen.
3. **Verifizieren mit dem Ziel HTTP 404** — hier zählt der Statuscode, nicht `cf-cache-status` wie bei Content-Edits. Nicht mit hoher Parallelität messen: ab ~10 gleichzeitigen curls liefert die Sandbox `000` (Verbindungsfehler), das sieht wie „weg" aus, ist aber gar keine Messung. Bewährt:

```bash
xargs -a urls.txt -P 3 -I{} sh -c 'echo "$(curl -s -o /dev/null -w %{http_code} --max-time 12 https://www.camperfuchs.de/wp-content/uploads/2026/07/{}) {}"'
```

Merksatz: **öffentlich hochgeladen = erst weg, wenn WP gelöscht UND gepurgt UND 404 verifiziert ist.**

## Token (wichtig)

- **Purge-fähig:** der Token in `.secrets/cloudflare-purge-token.txt` (identisch mit der historisch falsch benannten Datei `.secrets/Claude API BENUTZER API TOKEN.txt` — klingt nach Anthropic, ist Cloudflare) → `POST /zones/835b24…/purge_cache` = `success:true`.
- **NICHT purge-fähig:** der Token in `.secrets/cloudflare-api-token.txt` → Auth-Fehler 10000. Der ist nur fürs Lesen/Settings.
- Token liegt NUR lokal in `.secrets`, niemals in Memory/Chat/Repo im Klartext.

## Alternativer Purge-Weg

Gleichwertig: SPC-REST-Endpoint `POST /wp-json/spc/v1/cache/purge` (Auth = WP App-Password bjoerndunker, Body `{}`) → `{"success":true}`. Nützlich, wenn der CF-Token mal nicht greift.

## Purge-Disziplin — was ein Vollpurge wirklich kostet (gemessen 13.09.2026)

`purge_everything` wirft rund **9.700 Stadt-Landingpages** aus dem Edge. Danach gilt:

| Zustand | TTFB einer Stadt-LP |
|---|---|
| Edge-HIT | 0,04–0,3 s |
| Edge-MISS, Origin-Cache noch warm | ~0,5 s |
| komplett kalt | 1,5–1,9 s |
| kalt unter Crawler-/Warmer-Last | p50 2,5 s, p90 5 s, bis 11 s |

Der Warmer auf srv2 braucht für einen kompletten Durchlauf **rund 70 Minuten** (9.722 URLs,
6 parallel — schneller geht es nicht, der Origin schafft 2–3 Kalt-Renders/s; mehr Replicas
ändern daran nichts, am 13.09. gegengemessen). So lange ist der lange Schwanz kalt.

Am **12.09.2026** wurden zwischen 17:15 und 00:25 **acht** Vollpurges ausgelöst. Genau das ist
der Grund, warum Seobility 6.898 Seiten als „lange Antwortzeit" gemeldet hat.

**Regel:**

1. Inhaltsänderung → betroffene URLs nennen, nie `--all`. Auch 200 URLs sind kein Problem.
2. WordPress-Widget/Menü/Theme (wirkt auf alle Seiten) → trotzdem erst die tatsächlich
   betroffenen Seiten purgen, zusätzlich `POST /wp-json/spc/v1/cache/purge` gegen den
   Origin-Cache. Das ersetzt den Vollpurge.
3. `--all --wirklich` bleibt richtig nach einem prod-Deploy mit neuen Chunk-Hashes — dort
   macht die Pipeline es ohnehin selbst (`ci/deploy-prod-pipelines.yml`). Von Hand nur, wenn
   wirklich jede Seite betroffen ist.
4. Nach jedem Vollpurge den Warmer anstoßen, statt bis zu 5 Minuten auf den canary zu warten.
   Das Skript macht das selbst, wenn es SSH zu srv2 hat:
   `ssh srv2 'setsid nohup /usr/local/cf/cf-cache-warm.sh all >/dev/null 2>&1 &'`

## Grenzen

- Cloudflare: max. 30 URLs pro Purge-Request → das Skript teilt automatisch in 30er-Blöcke.
- **Der Edge hält nicht, was die TTL verspricht.** Selten abgerufene Seiten fliegen trotz
  7-Tage-Edge-TTL nach etwa einer Stunde wieder raus (LRU, am 13.09.2026 gemessen: gewärmte
  Seiten 30–90 min später wieder 0/20 HIT). Ein Purge ist deshalb teurer als er aussieht, und
  Wärmen ist kein Ersatz für einen sparsamen Umgang damit.
