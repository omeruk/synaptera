"""pytest configuration.

The 25 walking scripts in this directory are standalone simulations, not pytest
tests: they have no ``test_`` functions and run full FlyGym episodes (and write
files) at import time. Collecting them would run for hours, so they are excluded
here by name. They are unchanged and still run as ``python tests/<name>.py``.

Real pytest tests live in ``tests/flight/``. Tests that build the full 138,639-
neuron connectome are marked ``slow`` and only run with ``--runslow``.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# repo root on sys.path so tests can `import flight` regardless of how pytest is invoked
sys.path.insert(0, str(ROOT))
# Input data that the public snapshot does not ship (rebuilt by scripts/fetch_data.py)
DATA_DIRS = (ROOT / "brain_model", ROOT / "data")
MODEL_PY = ROOT / "brain_model" / "model.py"   # Shiu et al. model, imported by flight/brain.py

collect_ignore = [
    "test_back_camera.py",
    "test_fly_body_height.py",
    "test_flyvis_reflex_integration.py",
    "test_flyvis_stateful_timing.py",
    "test_light_source.py",
    "test_looming_integration.py",
    "test_optic_flow_reflex.py",
    "test_poisson_rate_update.py",
    "test_pole_on_path.py",
    "test_shadow_pole.py",
    "test_shadow_pole_v2.py",
    "test_shadow_pole_v3.py",
    "test_solid_wall_navigation.py",
    "test_solid_wall_stability.py",
    "test_vision_sensor.py",
    "test_visual_looming_reflex.py",
    "test_wall_base_sweep.py",
    "test_wall_before_food.py",
    "test_wall_heading04.py",
    "test_wall_heading0588.py",
    "test_wall_spawn_south.py",
    "test_wall_v40_config.py",
    "test_wall_wider.py",
    "test_wall_zigzag.py",
    "test_wall_zigzag_channeled.py",
]


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False,
                     help="run slow tests (full-brain build, long physics)")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: full-brain or long-running test (needs --runslow)")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return
    skip_slow = pytest.mark.skip(reason="slow test; use --runslow")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def _missing_data_file(excinfo):
    """Path of a missing input file under brain_model/ or data/ that caused excinfo, else None."""
    err = excinfo.value
    while err is not None:
        if isinstance(err, ModuleNotFoundError) and err.name == "model" and not MODEL_PY.exists():
            return MODEL_PY
        if isinstance(err, FileNotFoundError) and err.filename:
            p = Path(str(err.filename)).resolve()
            if not p.exists() and any(d in p.parents for d in DATA_DIRS):
                return p
        err = err.__cause__ or err.__context__
    return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """A test that fails only because an input data file is absent (e.g. a fresh public snapshot before
    scripts/fetch_data.py) is reported as skipped, with the file name, instead of failed."""
    outcome = yield
    rep = outcome.get_result()
    if rep.failed and call.excinfo is not None:
        p = _missing_data_file(call.excinfo)
        if p is not None:
            rep.outcome = "skipped"
            rep.longrepr = (str(item.path), item.location[1] or 0,
                            f"Skipped: missing data file {p.relative_to(ROOT)} (run scripts/fetch_data.py)")


class _DataAwareModule(pytest.Module):
    """A test module that cannot be imported only because brain_model/model.py is absent is reported as
    skipped instead of a collection error."""

    def _getobj(self):
        try:
            return super()._getobj()
        except self.CollectError as e:
            if not MODEL_PY.exists() and "No module named 'model'" in str(e):
                pytest.skip("missing brain_model/model.py (run scripts/fetch_data.py)", allow_module_level=True)
            raise


def pytest_pycollect_makemodule(module_path, parent):
    if module_path.name.startswith("test_"):
        return _DataAwareModule.from_parent(parent, path=module_path)
    return None
