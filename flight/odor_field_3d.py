"""Re-export of simulation_data/odor_field_3d.py (the implementation lives there)."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parent.parent / "simulation_data" / "odor_field_3d.py"
_spec = importlib.util.spec_from_file_location("_neurofly_odor_field_3d", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

OdorField3D = _mod.OdorField3D
build_arena_odor_field = _mod.build_arena_odor_field
antenna_odor = _mod.antenna_odor

__all__ = ["OdorField3D", "build_arena_odor_field", "antenna_odor"]
