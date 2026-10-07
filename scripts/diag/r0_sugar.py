"""R0: Shiu et al. sugar GRN -> MN9 reproduction. Protocol = brain_model/model.py (create_model + poi, PoissonInput)."""
import os as _os; _ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # repo root
import sys, time, json
import numpy as np, pandas as pd
sys.path.insert(0, _ROOT + '/brain_model')
sys.path.insert(0, _ROOT)
from model import create_model, poi, default_params
from brian2 import Network, Hz, ms, defaultclock, seed as bseed, PoissonGroup, Synapses
BD = _ROOT + '/brain_model/'
SUG = [720575940624963786,720575940630233916,720575940637568838,720575940638202345,720575940617000768,720575940630797113,720575940632889389,720575940621754367,720575940621502051,720575940640649691,720575940639332736,720575940616885538,720575940639198653,720575940620900446,720575940617937543,720575940632425919,720575940633143833,720575940612670570,720575940628853239,720575940629176663,720575940611875570]
MN9 = {'630': [720575940660219265, 720575940645521262]}
ver, mode, freq, ntr = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
comp = BD + ('2023_03_23_completeness_630_final.csv' if ver == '630' else 'Completeness_783.csv')
con = BD + ('2023_03_23_connectivity_630_final.parquet' if ver == '630' else 'Connectivity_783.parquet')
ids = pd.read_csv(comp, index_col=0).index.to_numpy()
r2i = {int(r): i for i, r in enumerate(ids)}
ann = pd.read_csv(BD + 'flywire_annotations.tsv', sep='\t', low_memory=False)
mn9 = [int(r) for r in ann.loc[ann.cell_type == 'CB0701', 'root_id']] if ver == '783' else MN9['630']
exc = [r2i[s] for s in SUG if s in r2i]
if mode == 'sezgroup':   # our flight 'sez' input group (408)
    from flight import groups as G
    exc = list(G.build_groups(G.load_root_ids())['sez'])
p = dict(default_params); p['r_poi'] = freq * Hz
out = []
for tr in range(ntr):
    bseed(tr)
    t0 = time.time()
    neu, syn, mon = create_model(comp, con, p)
    if mode in ('shiu', 'sezgroup'):
        pois, neu = poi(neu, exc, [], p)
        net = Network(neu, syn, mon, *pois)
    else:   # 'flight': PoissonGroup -> Synapses v += w, delay 1.8 ms (flight/brain.py path)
        pg = PoissonGroup(len(exc), rates=freq * Hz)
        s = Synapses(pg, neu, 'w : volt', on_pre='v += w', delay=p['t_dly'])
        s.connect(i=np.arange(len(exc)), j=np.array(exc)); s.w = p['w_syn'] * p['f_poi']
        neu.rfc[np.array(exc)] = 0 * ms
        net = Network(neu, syn, mon, pg, s)
    net.run(1000 * ms)
    cnt = np.bincount(np.asarray(mon.i), minlength=len(ids))
    out.append(dict(mn9=[int(cnt[r2i[m]]) for m in mn9], n_active=int((cnt > 0).sum()), total=int(cnt.sum()),
                    exc_mean=float(cnt[exc].mean()), dt=time.time() - t0))
    print(tr, out[-1], flush=True)
mn = np.array([o['mn9'] for o in out])
print(json.dumps(dict(ver=ver, mode=mode, freq=freq, n_exc=len(exc), mn9_ids=mn9, mn9_mean=mn.mean(0).tolist(),
                      mn9_std=mn.std(0).tolist(), n_active=np.mean([o['n_active'] for o in out]))))
