"""R1/R2 extra anatomy (was run inline during diagnosis):
  dng02   DNg02 presynaptic inputs by class/type (signed) and per-neuron exc/inh synapse totals
  kc      recurrent excitation inside the self-sustained set (needs r1_persist_mask.npy from r1_persist.py)
  excprop excitatory-only, in-degree-normalised propagation from sensory sources to DNg02 (k = 1..5)
Usage: python r2_extra.py {dng02|kc|excprop}   (run from the output directory)"""
import os as _os; _ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # repo root
import sys; sys.path.insert(0, _ROOT)
import numpy as np, pandas as pd, scipy.sparse as sp
from flight import groups as G

rid = G.load_root_ids(); N = len(rid); g = G.build_groups(rid)
ann = pd.read_csv(G.PATH_ANN, sep='\t', low_memory=False).set_index('root_id').reindex(rid)
ct = ann.cell_type.astype(str); cc = ann.cell_class.astype(str); sc = ann.super_class.astype(str)
con = pd.read_parquet(G.PATH_CON, columns=['Presynaptic_Index', 'Postsynaptic_Index', 'Connectivity', 'Excitatory'])
dng = np.r_[g['dng02_L'], g['dng02_R']]
what = sys.argv[1] if len(sys.argv) > 1 else 'dng02'

if what == 'dng02':
    c = con[con.Postsynaptic_Index.isin(dng)].copy()
    c['w'] = c.Connectivity * c.Excitatory
    pi = c.Presynaptic_Index.values
    c['ptype'] = ct.values[pi]; c['pnt'] = ann.top_nt.astype(str).values[pi]
    c['pclass'] = sc.values[pi] + '/' + cc.values[pi]
    print('by class'); print(c.groupby('pclass').w.agg(['sum', 'count']).sort_values('sum').to_string())
    t = c.groupby(['ptype', 'pnt']).w.sum().sort_values()
    print('most inhibitory types'); print(t.head(15).to_string())
    print('most excitatory types'); print(t.tail(20).to_string())
    e = c[c.w > 0].groupby('Postsynaptic_Index').w.sum(); i = c[c.w < 0].groupby('Postsynaptic_Index').w.sum()
    print('per-DNg02 exc syn median', e.median(), 'inh', i.median())

elif what == 'kc':
    a = np.load('r1_persist_mask.npy')
    c = con[a[con.Presynaptic_Index.values] & a[con.Postsynaptic_Index.values]]
    c = c.assign(w=c.Connectivity * c.Excitatory, pre=ct.values[c.Presynaptic_Index.values], post=ct.values[c.Postsynaptic_Index.values])
    kc = lambda s: s.str.startswith('KC')
    m = kc(c.pre) & kc(c.post)
    print('within-persistent synapses', len(c), 'signed sum', c.w.sum())
    print('KC->KC signed syn', c[m].w.sum(), ' per KC (post) mean', c[m].groupby('Postsynaptic_Index').w.sum().mean())
    print('top pre->post type pairs (signed):'); print(c.groupby(['pre', 'post']).w.sum().sort_values().tail(12).to_string())

elif what == 'excprop':
    pre, post, n, s = [con[k].to_numpy() for k in con.columns]
    indeg = np.bincount(post, weights=n, minlength=N); indeg[indeg == 0] = 1
    e = s > 0
    Ae = sp.csr_matrix((n[e] / indeg[post[e]], (post[e], pre[e])), shape=(N, N))
    src = {'ORN': np.r_[g['olf_L'], g['olf_R'], g['olf_C']], 'LA>ME': np.r_[g['vis_L'], g['vis_R']], 'ASC': g['ascending'],
           'GRN': g['sez'], 'T4/T5': np.flatnonzero(ct.str.match(r'^T[45][abcd]$').values),
           'LPLC2+LC4': np.flatnonzero(ct.str.match(r'^(LPLC2|LC4)$').values),
           'HS/VS': np.flatnonzero(ct.str.match(r'^(HS[ENS]|VS\d)$').values), 'ocellar': np.flatnonzero((cc == 'ocellar').values),
           'mechanosens': np.flatnonzero((cc == 'mechanosensory').values),
           'visual_projection(all)': np.flatnonzero((sc == 'visual_projection').values),
           'photorec(visual)': np.flatnonzero((cc == 'visual').values)}
    for k, idx in src.items():
        x = np.zeros(N); x[idx] = 1; out = []
        for _ in range(5):
            x = Ae @ x; out.append(x[dng].mean())
        print(f'{k:24s} n={len(idx):6d}  exc-only influence on DNg02, k=1..5: ' + ' '.join(f'{v:.1e}' for v in out))
