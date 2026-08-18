#!/usr/bin/env python3
"""Generate import library for VCMI_lib.dll from its export table (no full build needed)."""
import pefile, os, subprocess, sys

DLL = r'D:\Program Files\VCMI\VCMI_lib.dll'
OUT = r'D:\vcmi_model_ai'
os.makedirs(OUT, exist_ok=True)

pe = pefile.PE(DLL)
if not hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
    print('NO EXPORT TABLE')
    sys.exit(1)

lines = ['LIBRARY VCMI_lib', 'EXPORTS']
named = 0
for e in pe.DIRECTORY_ENTRY_EXPORT.symbols:
    if e.name:
        lines.append('    ' + e.name.decode())
        named += 1
    else:
        lines.append('    NONAME_%d' % e.ordinal)  # placeholders not usable; count only named

print('named exports:', named)
DEF = os.path.join(OUT, 'VCMI_lib.def')
with open(DEF, 'w', newline='\r\n') as f:
    f.write('\n'.join(lines) + '\n')
print('def written:', DEF)

# find lib.exe
import glob
cands = glob.glob(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\*\bin\Hostx64\x64\lib.exe')
if not cands:
    print('lib.exe not found')
    sys.exit(1)
libexe = cands[0]
print('lib.exe:', libexe)

r = subprocess.run([libexe, '/def:%s' % DEF, '/out:%s' % os.path.join(OUT, 'VCMI_lib.lib'),
                    '/machine:x64'], capture_output=True, text=True, timeout=300)
print('lib.exe rc:', r.returncode)
print(r.stdout[-500:] if r.stdout else '')
print(r.stderr[-500:] if r.stderr else '')
lib = os.path.join(OUT, 'VCMI_lib.lib')
if os.path.exists(lib):
    print('IMPORT LIB OK:', os.path.getsize(lib), 'bytes')
