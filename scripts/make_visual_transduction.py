"""Write data/visual_transduction.json: FlyVis a0 (every node) and a_ref (every FlyVis type) for
--vision-boundary (flight.vision_boundary.calibrate). Run once; constants are then fixed.

    env -u PYTHONPATH python scripts/make_visual_transduction.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from flight import vision_boundary as VB  # noqa: E402

d = VB.calibrate()
with open(VB.PATH_TRANSDUCTION, "w") as f:
    json.dump(d, f)
for t, v in d["a_ref"].items():
    print(f"{t:10s} a_ref {v:.4f} ({d['a_ref_stimulus'][t]})")
