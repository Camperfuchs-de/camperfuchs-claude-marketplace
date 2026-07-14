# Camperfuchs-Kontext (Plugin)

Geteilter technischer Projektkontext für die Zusammenarbeit an **Camperfuchs / Rentanda**.
Installiert man dieses Plugin, kennt die eigene Claude die gemeinsame Architektur, Infrastruktur,
das Repo, den Caching-Stack, das SEO-Setup und die Arbeitskonventionen — ohne Zugriff auf Björns
Account oder Secrets.

## Enthaltene Skills

| Skill | Zweck |
|---|---|
| `camperfuchs-projekt` | Technischer Projektkontext: Architektur (WP + Next.js-App), Hosting & Serving-Kette, Repo & Branch-Flow, Caching, Cloudflare, SEO/Schema, Konventionen. Triggert bei jedem Camperfuchs/Rentanda-Tech-Kontext. |
| `wp-502-debug` | Notfall-Runbook, wenn wp-admin 502 wirft. Schritt-für-Schritt-Diagnose (PHP-OOM, Plugin-Crash, Apache, Cloudflare). |

## Wichtig: keine Secrets

Dieses Plugin enthält **keine** API-Tokens, Passwörter oder Zugangsdaten. Es nennt nur
nicht-geheime Bezeichner (IPs, Droplet-IDs, Cloudflare-Zone-/Account-IDs), die ein Entwickler
für die Diagnose ohnehin braucht. Tokens liegen ausschließlich in Björns privatem `.secrets`-Store.
Wer eigene Aktionen ausführen will, nutzt seine eigenen Zugänge.

## Installation

In Cowork: das `.plugin`-File öffnen und über den Button installieren. Danach sind beide Skills
automatisch aktiv und triggern, sobald es um Camperfuchs/Rentanda geht.

## Pflege

Wenn sich Architektur, IPs oder Hosting ändern: in `skills/camperfuchs-projekt/SKILL.md`
aktualisieren, Version in `.claude-plugin/plugin.json` hochzählen, neu packen und verteilen.
