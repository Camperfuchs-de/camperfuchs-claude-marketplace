# Camperfuchs-Team Marketplace

Interner Claude-Marketplace für Camperfuchs/Rentanda. Eine zentrale Quelle, aus der Björn und
Bahti dieselben Plugins beziehen. Enthält aktuell:

- **camperfuchs-kontext** — geteilter technischer Projektkontext (Architektur, Infra, Repo,
  Caching, SEO, Konventionen) + WP-502-Notfall-Runbook.

Dieser Ordner enthält **keine Secrets** und ist genau so gedacht, um ihn in ein Git-Repo zu
pushen.

---

## Struktur

```
camperfuchs-marketplace/
├── .claude-plugin/marketplace.json     # Katalog (listet die Plugins)
├── plugins/
│   └── camperfuchs-kontext/            # das Plugin selbst (Quelle)
│       ├── .claude-plugin/plugin.json
│       ├── README.md
│       └── skills/...
└── camperfuchs-kontext.plugin          # fertig gepackt (für den Button-Weg in Cowork)
```

---

## A) Hosten — Status: erledigt

Das Repo ist angelegt und enthält bereits `README.md` + `camperfuchs-kontext.plugin`:
**https://dev.azure.com/camperfuchs/camperfuchs/_git/camperfuchs-claude-marketplace**

Bahti kann damit **sofort** installieren (siehe B, Weg 1).

**Noch offen — der Quellbaum** (`.claude-plugin/marketplace.json` + `plugins/...`) liegt noch
nicht im Repo, weil er sich über den Web-Editor nicht sauber anlegen lässt (Ordnerstruktur +
JSON). Sauber per einmaligem `git push` (Bahti oder Björn mit Azure-Login):
```bash
git clone https://dev.azure.com/camperfuchs/camperfuchs/_git/camperfuchs-claude-marketplace
cd camperfuchs-claude-marketplace
# Inhalt dieses Ordners (camperfuchs-marketplace/) reinkopieren, OHNE die schon vorhandene
# README.md/.plugin zu doppeln — also .claude-plugin/ und plugins/ kopieren:
cp -r "<Projektordner>/05_Skills-Automation/camperfuchs-marketplace/.claude-plugin" .
cp -r "<Projektordner>/05_Skills-Automation/camperfuchs-marketplace/plugins" .
git add . && git commit -m "Quellbaum camperfuchs-kontext v0.2.0" && git push
```
Für den reinen Cowork-`.plugin`-Weg ist der Quellbaum nicht nötig — nur für `/plugin marketplace
add` und zum Diffen/Ändern.

---

## B) Installieren (macht Bahti, einmalig)

Es gibt zwei Wege — Weg 1 ist in **Cowork** der sichere:

**Weg 1 — `.plugin`-Button (Cowork, garantiert):**
Bahti öffnet die Datei `camperfuchs-kontext.plugin` aus dem Repo in Cowork und klickt auf
Installieren. Fertig. Updates: neue `.plugin` aus dem Repo ziehen und erneut installieren.

**Weg 2 — Marketplace (Claude Code / wenn in Cowork verfügbar):**
```
/plugin marketplace add camperfuchs/camperfuchs-claude-marketplace
/plugin install camperfuchs-kontext@camperfuchs-team
```
(Bei Azure/GitLab statt dem owner/repo-Kürzel die volle Git-URL nehmen.)

> Hinweis: Der saubere „Pull"-Update-Weg (`/plugin marketplace update`) ist ein
> Claude-Code-Feature. In Cowork ist der `.plugin`-Button der erprobte Weg; das Repo bleibt aber
> in beiden Fällen die eine Wahrheit.

---

## C) Updaten (macht Björn, bei jeder Änderung)

1. Skill-Datei(en) unter `plugins/camperfuchs-kontext/skills/` ändern.
2. **Version hochzählen** in `plugins/camperfuchs-kontext/.claude-plugin/plugin.json`
   (z. B. `0.2.0` → `0.2.1`). Das ist der Auslöser, damit Bahti das Update bekommt.
3. `camperfuchs-kontext.plugin` neu packen:
   ```bash
   cd plugins/camperfuchs-kontext && zip -r ../../camperfuchs-kontext.plugin . -x "*.DS_Store"
   ```
4. Commit + push.

> Version nur in `plugin.json` pflegen, NICHT zusätzlich im marketplace-Eintrag — sonst
> maskiert die eine die andere.

---

## Was NICHT hier rein gehört

Keine Tokens, Passwörter, `.secrets`. Das Plugin nennt nur nicht-geheime IDs (IPs, Droplet-/
Zone-IDs), die ein Entwickler ohnehin braucht. Zugänge verwaltet jeder selbst.
