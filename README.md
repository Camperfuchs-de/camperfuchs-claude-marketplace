# Camperfuchs-Team Marketplace

Geteilte Claude-Plugins fuer Camperfuchs / Rentanda (Bjoern + Bahti). Damit kennt eure Claude
unsere gemeinsamen Projekte, ohne Zugriff auf fremde Accounts oder Secrets.

## Schnell installieren (Bahti)

1. Die Datei **`camperfuchs-kontext.plugin`** aus diesem Repo herunterladen.
2. In Cowork oeffnen und auf **Installieren** klicken.

Danach kennt deine Claude: Architektur (WordPress + Next.js-App), Hosting/Serving-Kette,
Repo & Branch-Flow, Caching-Stack, SEO-Setup, Konventionen — plus das **WP-502-Notfall-Runbook**.

## Updaten

Neue `camperfuchs-kontext.plugin` aus dem Repo ziehen und erneut installieren. Bjoern legt bei
Aenderungen eine neue Version ab.

## Inhalt

- `camperfuchs-kontext.plugin` — fertiges Plugin zum Installieren (Cowork).
- `.claude-plugin/marketplace.json` + `plugins/camperfuchs-kontext/` — der Quellbaum (fuer den
  `/plugin marketplace add`-Weg und zum Nachvollziehen/Aendern). Wird per `git push` gepflegt.

## Keine Secrets

Dieses Repo enthaelt **keine** Tokens oder Passwoerter — nur nicht-geheime IDs (IPs, Droplet-/
Zone-IDs), die ein Entwickler ohnehin braucht.
