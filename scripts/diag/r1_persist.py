"""R1: does the model sustain activity without input (hysteresis)? fresh net, flight background ON then OFF."""
import os as _os; _ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # repo root
import sys; import numpy as np
sys.path.insert(0, _ROOT + '/brain_model'); sys.path.insert(0, _ROOT)
from flight.brain import FlightBrain
b = FlightBrain(seed=0, verbose=False, inputs='legacy')  # R1 was run with the Stage 4 inputs
def run(label, ms_):
    tot = np.zeros(b.n); n = int(ms_ / 25)
    for _ in range(n):
        _, c = b.step(); tot += c
    act = tot > 0
    drv = np.zeros(b.n, bool)
    for k in ('ascending','olf_L','olf_R','olf_C','vis_L','vis_R','sez'): drv[b.groups[k]] = True
    print(f'{label:28s} mean={tot.mean()/(ms_/1000):.2f}Hz active={100*act.mean():.1f}% undriven_active={100*act[~drv].mean():.2f}% dn={tot[np.r_[b.groups["dn_L"],b.groups["dn_R"]]].sum()/(ms_/1000):.0f}/s', flush=True)
    return tot
b.set_rates(ascending=0, olf_L=0, olf_R=0, olf_C=0, vis_L=0, vis_R=0, sez=0); run('fresh, no input', 250)
b.set_rates(ascending=22.5, olf_L=20, olf_R=20, olf_C=20, vis_L=20, vis_R=20, sez=10); run('flight bg ON', 500)
b.set_rates(ascending=0, olf_L=0, olf_R=0, olf_C=0, vis_L=0, vis_R=0, sez=0)
run('OFF 0-250ms', 250); run('OFF 250-500ms', 250); t = run('OFF 500-1000ms', 500); run('OFF 1000-2000ms', 1000)
import pandas as pd
from flight import groups as G
ann = pd.read_csv(G.PATH_ANN, sep='\t', low_memory=False).set_index('root_id').reindex(b.root_ids)
a = t > 0
print('persistent neurons by super_class:', ann.super_class[a].value_counts().head(8).to_dict())
print('persistent by cell_type top:', ann.cell_type[a].value_counts().head(15).to_dict())
np.save('r1_persist_mask.npy', a)
