#!/usr/bin/env python3
"""Generate tbb12.lib import library from installed tbb12.dll."""
import pefile, os, subprocess

DLL = r'D:\GAMES\VCMI\tbb12.dll'
OUT = r'D:\vcmi_model_ai'

pe = pefile.PE(DLL)
lines = ['LIBRARY tbb12', 'EXPORTS']
for e in pe.DIRECTORY_ENTRY_EXPORT.symbols:
    if e.name:
        lines.append('    ' + e.name.decode())

def_path = os.path.join(OUT, 'tbb12.def')
with open(def_path, 'w', newline='\r\n') as f:
    f.write('\n'.join(lines) + '\n')

import glob
libexe = glob.glob(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\*\bin\Hostx64\x64\lib.exe')[0]
r = subprocess.run([libexe, '/def:%s' % def_path, '/out:%s' % os.path.join(OUT, 'tbb12.lib'),
                    '/machine:x64'], capture_output=True, text=True, timeout=120)
print('lib.exe rc:', r.returncode)
lib = os.path.join(OUT, 'tbb12.lib')
print('tbb12.lib:', os.path.getsize(lib), 'bytes' if os.path.exists(lib) else 'MISSING')
