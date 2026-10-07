"""R2: anatomical source -> DN map. Hops (BFS) + signed in-degree-normalised propagation."""
import os as _os; _ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # repo root
import sys, json
import numpy as np, pandas as pd, scipy.sparse as sp
sys.path.insert(0, _ROOT)
from flight import groups as G
rid = G.load_root_ids(); N = len(rid); r2i = G.root_to_index(rid); g = G.build_groups(rid)
ann = pd.read_csv(G.PATH_ANN, sep='\t', low_memory=False); ann = ann[ann.root_id.isin(r2i)]
ann['idx'] = ann.root_id.map(r2i); ct = ann.cell_type.astype(str); side = ann.side.astype(str)
def sel(mask): return np.sort(ann.loc[mask, 'idx'].to_numpy())
SUG = [720575940624963786,720575940630233916,720575940637568838,720575940638202345,720575940617000768,720575940630797113,720575940632889389,720575940621754367,720575940621502051,720575940640649691,720575940639332736,720575940616885538,720575940639198653,720575940617937543,720575940632425919,720575940633143833,720575940612670570,720575940628853239,720575940629176663,720575940611875570]
src = {'ORN_L': g['olf_L'], 'ORN_R': g['olf_R'], 'LAME_L': g['vis_L'], 'LAME_R': g['vis_R']}
for nm, pat in [('T4', r'^T4[abcd]$'), ('T5', r'^T5[abcd]$'), ('T4T5ab', r'^T[45][ab]$'), ('LPLC2', r'^LPLC2$'), ('LC4', r'^LC4$'),
                ('HSVS', r'^(HSE|HSN|HSS|VS\d|H2)$')]:
    for s in ('left', 'right'):
        src[f'{nm}_{s[0].upper()}'] = sel(ct.str.match(pat) & (side == s))
asc = ann[ann.idx.isin(g['ascending'])]
src['ASC_L'] = np.sort(asc.loc[asc.side == 'left', 'idx'].to_numpy()); src['ASC_R'] = np.sort(asc.loc[asc.side == 'right', 'idx'].to_numpy())
src['ASC_all'] = g['ascending']
gr = ann[ann.idx.isin(g['sez'])]
src['GRN_L'] = np.sort(gr.loc[gr.side == 'left', 'idx'].to_numpy()); src['GRN_R'] = np.sort(gr.loc[gr.side == 'right', 'idx'].to_numpy())
src['SUGAR_L'] = np.array(sorted(r2i[s] for s in SUG))
print({k: len(v) for k, v in src.items()})

con = pd.read_parquet(G.PATH_CON, columns=['Presynaptic_Index', 'Postsynaptic_Index', 'Connectivity', 'Excitatory'])
pre = con.Presynaptic_Index.to_numpy(); post = con.Postsynaptic_Index.to_numpy()
n = con.Connectivity.to_numpy().astype(np.float64); sgn = con.Excitatory.to_numpy().astype(np.float64); del con
indeg = np.bincount(post, weights=n, minlength=N); indeg[indeg == 0] = 1
A = sp.csr_matrix((sgn * n / indeg[post], (post, pre)), shape=(N, N))          # signed, post-normalised
exc5 = (sgn > 0) & (n >= 5)
Ex = sp.csr_matrix((np.ones(exc5.sum()), (post[exc5], pre[exc5])), shape=(N, N))  # excitatory >=5 syn
Any5 = sp.csr_matrix((np.ones((n >= 5).sum()), (post[n >= 5], pre[n >= 5])), shape=(N, N))

def hops(M, s, kmax=8):
    d = np.full(N, 99, np.int16); d[s] = 0; fr = np.zeros(N); fr[s] = 1
    for k in range(1, kmax + 1):
        fr = (M @ fr > 0) & (d == 99); d[fr] = k; fr = fr.astype(float)
    return d

dn = pd.read_csv(G.PATH_DN); dn = dn[dn.root_id.isin(r2i)]; dn['idx'] = dn.root_id.map(r2i)
dn['type'] = dn.cell_type.str.replace(r'^(DNg02)_.*$', r'\1', regex=True)   # pool DNg02_a..h
dn['s'] = dn.side.str[0].str.upper()
rows = []
K = 4
for sn, s in src.items():
    he = hops(Ex, s); ha = hops(Any5, s)
    x = np.zeros(N); x[s] = 1.0; cum = np.zeros(N); per = []
    for k in range(K):
        x = A @ x; cum += x; per.append(x.copy())
    for (t, sd), grp in dn.groupby(['type', 's']):
        ii = grp.idx.to_numpy()
        rows.append(dict(src=sn, type=t, side=sd, n=len(ii), hop_exc=int(he[ii].min()), hop_any=int(ha[ii].min()),
                         cum=float(cum[ii].mean()), k1=float(per[0][ii].mean()), k2=float(per[1][ii].mean()),
                         k3=float(per[2][ii].mean()), k4=float(per[3][ii].mean())))
    dnall = dn.idx.to_numpy()
    print(sn, 'DN reached exc-hops<=k:', [int((he[dnall] <= k).sum()) for k in range(1, 7)], 'any:', [int((ha[dnall] <= k).sum()) for k in range(1, 5)], flush=True)
df = pd.DataFrame(rows); df.to_csv('r2_src_dn.csv', index=False)
