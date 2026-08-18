#!/usr/bin/env python3
"""Rebuild model_ai.cpp: keep pure-virtual hand stubs + insert generated non-pure stubs."""
import io

cpp = io.open(r'D:\vcmi_model_ai\model_ai.cpp', encoding='utf-8').read()
stubs = io.open(r'D:\vcmi_model_ai\stubs_gen.txt', encoding='utf-8').read().strip().split('\n')

# hand-written overrides to keep (pure virtuals + battle pure virtuals)
hand = [
    'showBlockingDialog', 'showGarrisonDialog', 'showTeleportDialog',
    'showMapObjectSelectDialog', 'makeSurrenderRetreatDecision',
    'heroGotLevel', 'commanderGotLevel', 'activeStack', 'yourTacticPhase',
]

# extract function names from generated stubs
def fname(stub):
    return stub.strip().split('(')[0].split()[-1]

# filter out stubs that collide with hand-written ones
gen_keep = [s for s in stubs if fname(s) not in hand]

# remove existing non-pure overrides from the class (initGameInterface / yourTurn hand-written)
import re
# remove lines matching hand-written non-pure overrides
cpp = re.sub(r'\tvoid initGameInterface\([^)]*\)[^}]*}\n', '', cpp)
cpp = re.sub(r'\tvoid yourTurn\(QueryID\)[^}]*}\n', '', cpp)

# insert generated stubs before the closing brace of class ModelAI
marker = '};\n\nextern "C"'
insert = '\n'.join('    ' + s for s in gen_keep) + '\n'
cpp = cpp.replace(marker, insert + marker)

io.open(r'D:\vcmi_model_ai\model_ai.cpp', 'w', encoding='utf-8', newline='\n').write(cpp)
print('inserted', len(gen_keep), 'stubs (kept', len(hand), 'hand pure-virtual stubs)')
