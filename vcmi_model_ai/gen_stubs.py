#!/usr/bin/env python3
"""Extract all non-pure virtuals from the three interface headers and emit stub overrides."""
import re, io

headers = [
    r'D:\vcmi-1.7.5\lib\callback\IGameEventsReceiver.h',
    r'D:\vcmi-1.7.5\lib\callback\CGameInterface.h',
    r'D:\vcmi-1.7.5\lib\callback\CBattleGameInterface.h',
]

stubs = []
seen = set()
for h in headers:
    with io.open(h, encoding='utf-8', errors='replace') as f:
        src = f.read()
    # remove comments
    src = re.sub(r'//.*?(\n|$)', '\n', src)
    src = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
    # find virtual declarations ending with {} or ; (non-pure)
    for m in re.finditer(r'virtual\s+([^;{}]+?)\s*\(\s*([^)]*)\)\s*(?:const)?\s*(?:override)?\s*(\{\s*\}|;)', src, re.S):
        decl = m.group(0)
        if '= 0' in decl or '=0' in decl:
            continue
        ret_and_name = m.group(1).strip()
        params = m.group(2).strip()
        body = m.group(3)
        # strip default args and param names? keep types only
        # split params on commas not inside <> or ()
        parts = []
        depth = 0
        cur = ''
        for ch in params + ',':
            if ch in '<(':
                depth += 1
            elif ch in '>)':
                depth -= 1
            if ch == ',' and depth == 0:
                parts.append(cur.strip())
                cur = ''
            else:
                cur += ch
        types = []
        for p in parts:
            if not p:
                continue
            # remove default value
            p = re.sub(r'\s*=\s*[^,]+$', '', p.strip())
            if p in ('void',):
                continue
            # keep full decl (type + name) — need name? no; use type only
            # handle 'const X & name' -> strip trailing identifier
            m2 = re.match(r'^(.*?)(\s+\w+)$', p)
            types.append(m2.group(1).strip() if m2 else p)
        sig = '%s(%s)' % (ret_and_name, ', '.join(types)) if types else '%s()' % ret_and_name
        # add const qualifier if present
        if 'const' in m.group(0).split(')')[1][:40] and re.search(r'\)\s*const', m.group(0)):
            sig = sig.replace(')', ') const')
        key = ret_and_name + '(' + ', '.join(types) + ')'
        if key in seen:
            continue
        seen.add(key)
        stubs.append('    ' + sig + ' override {}')

with io.open(r'D:\vcmi_model_ai\stubs_gen.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(stubs))
print('generated', len(stubs), 'stubs')
