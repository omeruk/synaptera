import os as _os; _ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # repo root
import sys; sys.path.insert(0, _ROOT)
import numpy as np, pandas as pd
from flight import groups as G
rid = G.load_root_ids(); r2i = G.root_to_index(rid); g = G.build_groups(rid)
R = dict(np.load(sys.argv[1]))
dn = pd.read_csv(G.PATH_DN); dn = dn[dn.root_id.isin(r2i)]; dn['idx'] = dn.root_id.map(r2i)
dn['type'] = dn.cell_type.str.replace(r'^(DNg02)_.*$', r'\1', regex=True); dn['s'] = dn.side.str[0].str.upper()
ann = pd.read_csv(G.PATH_ANN, sep='\t', low_memory=False).set_index('root_id').reindex(rid)
mn9 = [r2i[r] for r in ann.index[ann.cell_type.astype(str) == 'CB0701']]
cand = ['DNa01','DNa02','DNa03','DNb01','DNb06','DNg02','DNp01','DNp02','DNp04','DNp11','DNp07','DNp10','DNp15','DNp20','DNp22','DNp06','DNp09','DNg13','DNa08']
rows = {}
for k, c in R.items():
    r = {}
    for t in cand:
        for sd in 'LR':
            ii = dn.idx[(dn.type == t) & (dn.s == sd)].to_numpy()
            r[f'{t}{sd}'] = c[ii].sum() / max(len(ii), 1)
    r['MN9'] = '/'.join(str(int(c[m])) for m in mn9)
    r['allDN_L-R'] = int(c[g['dn_L']].sum() - c[g['dn_R']].sum())
    rows[k] = r
df = pd.DataFrame(rows).T
pd.set_option('display.width', 400); pd.set_option('display.max_columns', 60)
for part in (cand[:10], cand[10:]):
    cols = [f'{t}{s}' for t in part for s in 'LR']
    print(df[cols].to_string(float_format=lambda x: f'{x:.0f}'))
print(df[['MN9', 'allDN_L-R']].to_string())
# active population composition in F0 (undriven)
c = R['F0_bg']; act = c > 0
print('F0 active by super_class:', ann.super_class[act].value_counts().head(10).to_dict())
print('F0 KC active:', int((act & ann.cell_type.astype(str).str.startswith('KC').values).sum()), 'of', int(ann.cell_type.astype(str).str.startswith('KC').sum()))
if 'F0_bg_OFF' in R:
    off = R['F0_bg_OFF'] > 0
    print('DN active in F0:', int(act[dn.idx].sum()), ' persisting after OFF:', int(off[dn.idx].sum()), ' DN spikes F0 vs OFF(/s):', int(c[dn.idx].sum()), int(R['F0_bg_OFF'][dn.idx].sum() * 2))
