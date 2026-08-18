#!/usr/bin/env python3
"""Auto-answer all QueryID-carrying dialog stubs in model_ai.cpp (selectionMade(0, qid))."""
import io, re

p = r'D:\vcmi_model_ai\model_ai.cpp'
src = io.open(p, encoding='utf-8').read()

# find generated stub lines (indented, ending with 'override {}') that mention QueryID
lines = src.split('\n')
changed = 0
for i, ln in enumerate(lines):
    if 'override {}' not in ln or 'QueryID' not in ln:
        continue
    # add parameter name to bare QueryID occurrences inside the parameter list
    # pattern: 'QueryID' followed by ',' or ')' (no name) -> 'QueryID qid'
    # only inside the parens part (before '('? after '(')
    if '(' not in ln:
        continue
    head, rest = ln.split('(', 1)
    params, tail = rest.rsplit(')', 1)
    newparams = re.sub(r'QueryID(?=[,\)])', 'QueryID qid', params)
    # if there are multiple QueryID params, rename first one only (they are askID-style)
    if newparams.count('QueryID qid') > 1:
        # keep only first named; subsequent stay bare (not referenced)
        seen = 0
        out = []
        for tok in re.split(r'(QueryID(?:\s+qid)?)', newparams):
            if tok.startswith('QueryID') and 'qid' in tok:
                seen += 1
                out.append('QueryID qid' if seen == 1 else 'QueryID')
            else:
                out.append(tok)
        newparams = ''.join(out)
    if newparams != params:
        lines[i] = head + '(' + newparams + ')' + tail
        changed += 1
    # replace body with auto-answer
    if 'qid' in newparams:
        lines[i] = lines[i].replace('override {}',
            'override { if(qid != QueryID(-1)) cc->selectionMade(0, qid); }')

io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
print('stubs auto-answered:', changed)
