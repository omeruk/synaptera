"""R3b: can DNg02 fire at all? drive vertical motion, ocelli, VS, and DNg02's own top excitatory presynaptic types."""
import os as _os; _ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # repo root
import sys, time
import numpy as np, pandas as pd
sys.path.insert(0, _ROOT + '/brain_model'); sys.path.insert(0, _ROOT)
from model import create_model, default_params
from flight import groups as G
from brian2 import Network, Hz, ms, defaultclock, PoissonGroup, Synapses, seed as bseed
bseed(0); defaultclock.dt = 0.1 * ms
rid = G.load_root_ids(); N = len(rid); r2i = G.root_to_index(rid); g = G.build_groups(rid)
ann = pd.read_csv(G.PATH_ANN, sep='\t', low_memory=False); ann = ann[ann.root_id.isin(r2i)]
ann['idx'] = ann.root_id.map(r2i); ct = ann.cell_type.astype(str)
dng = np.r_[g['dng02_L'], g['dng02_R']]
con = pd.read_parquet(G.PATH_CON, columns=['Presynaptic_Index', 'Postsynaptic_Index', 'Connectivity', 'Excitatory'])
c = con[con.Postsynaptic_Index.isin(dng) & (con.Excitatory > 0)]
pre_exc = c.groupby('Presynaptic_Index').Connectivity.sum().sort_values(ascending=False)
del con
S = {
 'T45c': np.sort(ann.loc[ct.str.match(r'^T[45]c$'), 'idx'].to_numpy()),
 'T45d': np.sort(ann.loc[ct.str.match(r'^T[45]d$'), 'idx'].to_numpy()),
 'VS': np.sort(ann.loc[ct.str.match(r'^VS\d$'), 'idx'].to_numpy()),
 'ocellar': np.sort(ann.loc[ann.cell_class.astype(str) == 'ocellar', 'idx'].to_numpy()),
 'exc_pre_top50': np.sort(pre_exc.index[:50].to_numpy()),
 'exc_pre_all': np.sort(pre_exc.index.to_numpy()),
}
print({k: len(v) for k, v in S.items()}, 'exc presyn of DNg02:', len(pre_exc))
p = dict(default_params)
neu, syn, mon = create_model(str(G.PATH_COMP), str(G.PATH_CON), p)
objs, PG = [], {}
for k, idx in S.items():
    pg = PoissonGroup(len(idx), rates=0 * Hz, name=f'pg_{k}')
    s = Synapses(pg, neu, 'w : volt', on_pre='v += w', delay=p['t_dly'], name=f'ps_{k}')
    s.connect(i=np.arange(len(idx)), j=idx); s.w = p['w_syn'] * p['f_poi']; PG[k] = pg; objs += [pg, s]
net = Network(neu, syn, mon, *objs); net.store('fresh')
dn = pd.read_csv(G.PATH_DN); dn = dn[dn.root_id.isin(r2i)]
for name, rates in [('T45c100', dict(T45c=100)), ('T45d100', dict(T45d=100)), ('VS100', dict(VS=100)), ('ocellar100', dict(ocellar=100)),
                    ('excpre_top50_50', dict(exc_pre_top50=50)), ('excpre_top50_100', dict(exc_pre_top50=100)),
                    ('excpre_all_50', dict(exc_pre_all=50)), ('excpre_all_100', dict(exc_pre_all=100))]:
    net.restore('fresh'); neu.rfc = p['t_rfc']
    for k, r in rates.items():
        PG[k].rates = r * Hz; neu.rfc[S[k]] = 0 * ms
    net.run(50 * ms); n0 = int(mon.num_spikes); net.run(1000 * ms)
    cnt = np.bincount(np.asarray(mon.i[n0:int(mon.num_spikes)]), minlength=N)
    per = cnt[dng]
    print(f'{name:18s} DNg02 per-neuron Hz: mean={per.mean():.1f} max={per.max()} n_firing={int((per>0).sum())}/25  L={cnt[g["dng02_L"]].mean():.1f} R={cnt[g["dng02_R"]].mean():.1f}  net_active={100*(cnt>0).mean():.1f}%', flush=True)
