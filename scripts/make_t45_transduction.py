"""Write data/t45_transduction.json (FlyVis T4/T5 a0, a_ref; flight.visual_input.calibrate_transduction).
Run once before any closed-loop run; the constants are then fixed.

    env -u PYTHONPATH python scripts/make_t45_transduction.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from flight import visual_input as V  # noqa: E402

d = V.calibrate_transduction()
with open(V.PATH_TRANSDUCTION, "w") as f:
    json.dump(d, f, indent=1)
for t in d["a0"]:
    a0 = d["a0"][t]
    print(f"{t}: a0 mean {sum(a0) / len(a0):+.4f} (min {min(a0):+.4f}, max {max(a0):+.4f})  a_ref {d['a_ref'][t]:.4f}")
