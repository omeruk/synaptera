"""R1/R3: open-loop stimulation, full brain, model.py network. Readout per DN type x side, MN9, network stats."""
# SUPERSEDED: only resets v/g between conditions, so the self-sustained KC state (R1) carries over.
# Kept for the record; results in SPEC_BRAIN_CONTROL.md come from r3_open.py (net.restore per condition).
import os as _os; _ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # repo root
import sys, time, json
import numpy as np, pandas as pd
sys.path.insert(0, _ROOT + '/brain_model'); sys.path.insert(0, _ROOT)
from model import create_model, default_params
from flight import groups as G
from brian2 import Network, Hz, ms, mV, defaultclock, PoissonGroup, Synapses, seed as bseed
bseed(int(sys.argv[2]) if len(sys.argv) > 2 else 0)
defaultclock.dt = 0.1 * ms
rid = G.load_root_ids(); N = len(rid); r2i = G.root_to_index(rid); g = G.build_groups(rid)
ann = pd.read_csv(G.PATH_ANN, sep='\t', low_memory=False); ann = ann[ann.root_id.isin(r2i)]
ann['idx'] = ann.root_id.map(r2i); ct = ann.cell_type.astype(str); side = ann.side.astype(str)
def sel(pat, s): return np.sort(ann.loc[ct.str.match(pat) & (side == s), 'idx'].to_numpy())
SUG = [720575940624963786,720575940630233916,720575940637568838,720575940638202345,720575940617000768,720575940630797113,720575940632889389,720575940621754367,720575940621502051,720575940640649691,720575940639332736,720575940616885538,720575940639198653,720575940617937543,720575940632425919,720575940633143833,720575940612670570,720575940628853239,720575940629176663,720575940611875570]
S = {k: g[k] for k in ('ascending', 'olf_L', 'olf_R', 'olf_C', 'vis_L', 'vis_R', 'sez')}
for sd in ('left', 'right'):
    c = sd[0].upper()
    S[f'T45a_{c}'] = sel(r'^T[45]a$', sd); S[f'T45b_{c}'] = sel(r'^T[45]b$', sd)
    S[f'LPLC2_{c}'] = sel(r'^LPLC2$', sd); S[f'LC4_{c}'] = sel(r'^LC4$', sd)
S['sugar'] = np.array(sorted(r2i[s] for s in SUG))
p = dict(default_params)
neu, syn, mon = create_model(str(G.PATH_COMP), str(G.PATH_CON), p)
objs, PG = [], {}
for k, idx in S.items():
    pg = PoissonGroup(len(idx), rates=0 * Hz, name=f'pg_{k}')
    s = Synapses(pg, neu, 'w : volt', on_pre='v += w', delay=p['t_dly'], name=f'ps_{k}')
    s.connect(i=np.arange(len(idx)), j=idx); s.w = p['w_syn'] * p['f_poi']
    PG[k] = pg; objs += [pg, s]
net = Network(neu, syn, mon, *objs)
FLIGHT_BG = dict(ascending=22.5, olf_L=20, olf_R=20, olf_C=20, vis_L=20, vis_R=20, sez=10)
C = {
 'F0_bg': {}, 'F1_olfL150': dict(olf_L=150), 'F2_olfR150': dict(olf_R=150), 'F3_olfLR150': dict(olf_L=150, olf_R=150, olf_C=150),
 'F4_visL150': dict(vis_L=150), 'F5_visR150': dict(vis_R=150), 'F6_asc150': dict(ascending=150), 'F7_asc0': dict(ascending=0),
 'F8_yawR_optic': dict(T45a_L=50, T45b_R=50), 'F9_yawL_optic': dict(T45b_L=50, T45a_R=50),
 'F10_loomL': dict(LPLC2_L=100, LC4_L=100), 'F11_loomR': dict(LPLC2_R=100, LC4_R=100),
}
C = {k: {'bg': True, **v} for k, v in C.items()}
I = {
 'S0_none': {}, 'S1_ORN_L': dict(olf_L=100), 'S2_ORN_R': dict(olf_R=100), 'S3_ORN_LR': dict(olf_L=100, olf_R=100, olf_C=100),
 'S4_LAME_L': dict(vis_L=100), 'S5_LAME_R': dict(vis_R=100),
 'S6_yawR_optic': dict(T45a_L=50, T45b_R=50), 'S7_yawL_optic': dict(T45b_L=50, T45a_R=50),
 'S8_progressive': dict(T45a_L=50, T45a_R=50), 'S9_regressive': dict(T45b_L=50, T45b_R=50),
 'S10_loomL': dict(LPLC2_L=100, LC4_L=100), 'S11_loomR': dict(LPLC2_R=100, LC4_R=100),
 'S12_asc100': dict(ascending=100), 'S13_sugar100': dict(sugar=100), 'S14_allGRN100': dict(sez=100),
}
C.update({k: {'bg': False, **v} for k, v in I.items()})
only = sys.argv[1] if len(sys.argv) > 1 else 'all'
dn = pd.read_csv(G.PATH_DN); dn = dn[dn.root_id.isin(r2i)]; dn['idx'] = dn.root_id.map(r2i)
res = {}
T_SETTLE, T_MEAS = 50 * ms, 1000 * ms
for name, cond in C.items():
    if only != 'all' and not name.startswith(only): continue
    t0 = time.time()
    rates = dict(FLIGHT_BG) if cond['bg'] else {}
    rates.update({k: v for k, v in cond.items() if k != 'bg'})
    for k in PG: PG[k].rates = 0 * Hz
    net.run(20 * ms)                      # flush in-flight spikes (delay 1.8 ms)
    neu.v = p['v_0']; neu.g = 0 * mV; neu.rfc = p['t_rfc']
    for k, r in rates.items():
        PG[k].rates = r * Hz
        if r > 0: neu.rfc[S[k]] = 0 * ms
    net.run(T_SETTLE); n0 = int(mon.num_spikes); net.run(T_MEAS); n1 = int(mon.num_spikes)
    cnt = np.bincount(np.asarray(mon.i[n0:n1]), minlength=N).astype(np.int32)
    res[name] = cnt
    drv = np.zeros(N, bool)
    for k, r in rates.items():
        if r > 0: drv[S[k]] = True
    nd = ~drv
    print(f'{name:16s} rates={rates} net_mean={cnt.mean():.2f}Hz active={100*(cnt>0).mean():.1f}% undriven_active={100*(cnt[nd]>0).mean():.1f}% '
          f'dnL={cnt[g["dn_L"]].sum()} dnR={cnt[g["dn_R"]].sum()} dng02={cnt[np.r_[g["dng02_L"], g["dng02_R"]]].sum()} ({time.time()-t0:.0f}s)', flush=True)
np.savez_compressed(f'r3_counts_{only}_s{sys.argv[2] if len(sys.argv)>2 else 0}.npz', **res)
