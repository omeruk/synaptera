"""Stage A2 smoke criteria (SPEC_SENSORY_INPUTS §3.2c): B-K1..B-K4 for each smoke HDF5, with exactly the
Stage A definitions (scripts/diag/sa_report.py criteria(); driven = orn_all or orn_food, vbnd, sugar), plus the
input-cut network rate per 5 steps and, for the --nt-literature runs, meta/nt_literature. Markdown to stdout.

    env -u PYTHONPATH python scripts/diag/sa2_report.py SMOKE_H5 [SMOKE_H5 ...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from flight import groups as G  # noqa: E402
from sa_report import RunA, criteria  # noqa: E402
from sb_report import DATA, neuron_sets  # noqa: E402


def main(paths):
    root_ids = G.load_root_ids()
    npz = np.load(DATA / "neuron_neuropil.npz")
    npl = np.where(npz["frac"] > 0, npz["neuropils"][npz["dominant"]], "(none)")
    sets = neuron_sets(root_ids)
    for p in paths:
        r = RunA(p)
        fl = r.meta["flags"]
        print(f"\n### `{r.path.name}`\n")
        print(f"olfaction_full {fl.get('olfaction_full')}, apl_graded {fl.get('apl_graded')}, "
              f"nt_literature {fl.get('nt_literature', False)}, seed {r.meta['seed']}, git {r.meta['git_hash']}; "
              f"driven {int(r.driven.sum()):,} neurons\n")
        nl = r.meta.get("nt_literature") or {}
        if nl:
            print(f"- nt_literature: {nl['n_types']} types, {nl['n_neurons']} neurons; sign changed in {nl['n_neurons_changed']} "
                  f"neurons / {nl['n_edges_changed']} edges ({nl['syn_exc_to_inh']:.0f} excitatory→inhibitory, "
                  f"{nl['syn_inh_to_exc']:.0f} inhibitory→excitatory synapses): {', '.join(nl['types_changed'])}")
        criteria(r, npl, sets, r.path.name, print)


if __name__ == "__main__":
    main(sys.argv[1:])
