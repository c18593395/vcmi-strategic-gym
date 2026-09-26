# -*- coding: utf-8 -*-
"""M1.5: settings.json 切 adventureEnemyAI=Nullkiller2 (备份先行, 幂等)。"""
import json
import shutil

P = r'C:\Users\Administrator\Documents\My Games\vcmi\config\settings.json'
BAK = P + '.bak_pre_nk2_0927'

if not __import__('os').path.exists(BAK):
    shutil.copyfile(P, BAK)
    print('backup ->', BAK)
else:
    print('backup exists:', BAK)

data = json.load(open(P, encoding='utf-8'))
old = data['ai']['adventureEnemyAI']
data['ai']['adventureEnemyAI'] = 'Nullkiller2'
json.dump(data, open(P, 'w', encoding='utf-8'), indent='\t', ensure_ascii=False)
print(f'adventureEnemyAI: {old} -> Nullkiller2')
print(f'adventureAlliedAI (untouched): {data["ai"]["adventureAlliedAI"]}')
