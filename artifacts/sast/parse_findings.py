import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = [
    'semgrep-owasp-top-ten-20260613T204704.json',
    'semgrep-javascript-20260613T204743.json',
]

seen = set()

for fname in FILES:
    fpath = os.path.join(BASE, fname)
    with open(fpath, encoding='utf-8') as f:
        d = json.load(f)
    results = d.get('results', [])
    print(f'\n=== {fname} ({len(results)} findings) ===')
    for i, r in enumerate(results):
        check_id = r.get('check_id', '')
        path = r.get('path', '')
        path = path.replace(os.sep, '/')
        start = r.get('start', {}).get('line', '?')
        end = r.get('end', {}).get('line', '?')
        sev = r.get('extra', {}).get('severity', '')
        msg = r.get('extra', {}).get('message', '')
        lines = r.get('extra', {}).get('lines', '').strip()
        cwe = r.get('extra', {}).get('metadata', {}).get('cwe', [])
        owasp_cat = r.get('extra', {}).get('metadata', {}).get('owasp', [])
        parts = path.split('/')
        short_path = '/'.join(parts[-3:]) if len(parts) >= 3 else path
        key = f'{check_id}@{short_path}:{start}'
        dup = ' (DUP)' if key in seen else ''
        seen.add(key)
        print(f'  [{i}]{dup} [{sev}] {check_id}')
        print(f'       File: {short_path} L{start}-{end}')
        if cwe:
            print(f'       CWE: {cwe}')
        if owasp_cat:
            print(f'       OWASP: {owasp_cat}')
        if lines:
            print(f'       Code: {lines[:120]}')
        print()
