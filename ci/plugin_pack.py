#!/usr/bin/env python3
"""Baut und prueft das Paket camperfuchs-kontext.plugin aus dem Quellbaum.

Zweck: Am 15.07.2026 fiel eine Skill still aus dem ausgelieferten Paket, weil es aus einem
veralteten Baum gebaut wurde. Diese Pruefung laeuft jetzt bei jedem Push auf main.

  python3 ci/plugin_pack.py --check   nur pruefen, Exit 1 bei Abweichung
  python3 ci/plugin_pack.py --write   Paket neu bauen und in den Baum schreiben
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'plugins', 'camperfuchs-kontext')
PKG = os.path.join(ROOT, 'camperfuchs-kontext.plugin')
CHANGELOG = os.path.join(ROOT, 'CHANGELOG.md')

SECRET_PAT = re.compile(
    r'cfut_|dop_v1_|ghp_|github_pat_|sk-ant-|AIza|BEGIN [A-Z ]*PRIVATE KEY|\b[A-Za-z0-9]{52}\b')
# Diese Skill listet die Muster selbst auf, das ist der bekannte Fehlalarm.
SECRET_ALLOW = {'skills/camperfuchs-plugin-sync/SKILL.md'}

fehler = []


def frontmatter(text):
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if not m:
        return None
    out, key = {}, None
    for line in m.group(1).split('\n'):
        if re.match(r'^[a-zA-Z_]+:', line):
            key, _, rest = line.partition(':')
            out[key.strip()] = rest.strip()
        elif key:
            out[key] = (out.get(key, '') + ' ' + line.strip()).strip()
    return out


def sammle():
    rels = []
    for dp, _, fs in os.walk(SRC):
        for f in fs:
            rels.append(os.path.relpath(os.path.join(dp, f), SRC).replace(os.sep, '/'))
    return sorted(rels)


def pruefe(rels):
    skills = sorted({r.split('/')[1] for r in rels if r.startswith('skills/')})
    mit_md = sorted({r.split('/')[1] for r in rels if r.startswith('skills/') and r.endswith('SKILL.md')})
    if skills != mit_md:
        fehler.append('Skill-Ordner ohne SKILL.md: %s' % sorted(set(skills) - set(mit_md)))

    for rel in rels:
        roh = open(os.path.join(SRC, rel), 'rb').read()
        if rel.endswith('SKILL.md'):
            if roh[:3] == b'\xef\xbb\xbf':
                fehler.append('%s hat ein BOM' % rel)
                continue
            fm = frontmatter(roh.decode('utf-8'))
            if not fm:
                fehler.append('%s ohne Frontmatter' % rel)
                continue
            if not fm.get('name'):
                fehler.append('%s ohne name' % rel)
            d = ' '.join(fm.get('description', '').split()).lstrip('>-').strip()
            if not d:
                fehler.append('%s ohne description' % rel)
            elif len(d) > 1024:
                fehler.append('%s: description %d Zeichen (max 1024)' % (rel, len(d)))
        if rel in SECRET_ALLOW:
            continue
        try:
            txt = roh.decode('utf-8')
        except UnicodeDecodeError:
            continue
        t = SECRET_PAT.search(txt)
        if t:
            fehler.append('%s: moeglicher Secret-Treffer "%s"' % (rel, t.group()[:12]))

    version = json.load(open(os.path.join(SRC, '.claude-plugin', 'plugin.json'),
                             encoding='utf-8'))['version']
    oben = open(CHANGELOG, encoding='utf-8').read().split('## ')[1].split('\n')[0].strip()
    if not oben.startswith('v' + version):
        fehler.append('plugin.json ist %s, oberster CHANGELOG-Eintrag ist "%s"' % (version, oben))
    return version, len(mit_md)


def baue(rels):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in rels:
            info = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, open(os.path.join(SRC, rel), 'rb').read())
    return buf.getvalue()


def main():
    modus = '--write' if '--write' in sys.argv else '--check'
    rels = sammle()
    version, anzahl = pruefe(rels)
    neu = baue(rels)

    z = zipfile.ZipFile(io.BytesIO(neu))
    if z.testzip() is not None:
        fehler.append('gebautes Zip ist defekt')
    if any('\\' in n for n in z.namelist()):
        fehler.append('Backslash-Pfade im Zip')
    im_paket = len([n for n in z.namelist() if n.endswith('SKILL.md')])
    if im_paket != anzahl:
        fehler.append('Quellbaum hat %d Skills, Paket %d' % (anzahl, im_paket))

    if fehler:
        print('FEHLER:')
        for f in fehler:
            print('  -', f)
        return 1

    alt = open(PKG, 'rb').read() if os.path.exists(PKG) else b''
    gleich = hashlib.sha256(alt).hexdigest() == hashlib.sha256(neu).hexdigest()
    print('Version %s, %d Skills, %d Dateien, Paket %d Bytes' % (version, anzahl, len(rels), len(neu)))

    if gleich:
        print('Paket ist aktuell.')
        return 0
    if modus == '--write':
        open(PKG, 'wb').write(neu)
        print('Paket neu geschrieben.')
        return 0
    print('Paket weicht vom Quellbaum ab (bitte mit --write neu bauen).')
    return 1


if __name__ == '__main__':
    sys.exit(main())
