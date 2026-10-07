"""Stage 1: 3D odor field (Dijkstra around obstacles + trilinear lookup).

Run with -s to see the I_asym report at the take-off point.
"""
import numpy as np
import pytest

from flight import config as cfg
from flight.odor_field_3d import OdorField3D, antenna_odor, build_arena_odor_field


@pytest.fixture(scope="module")
def field():
    return build_arena_odor_field()


def yaw_rot(yaw):
    c, s = np.cos(yaw), np.sin(yaw)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def test_grid_shape_and_obstacles_present(field):
    assert field.shape == (113, 105, 61)
    X, Y, Z = field.voxel_centers()
    for (x0, x1), (y0, y1), (z0, z1) in cfg.TOWERS:
        inside = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1) & (Z >= z0) & (Z <= z1)
        assert inside.sum() > 0 and field.blocked[inside].all()
    cx, cy, r, zt = cfg.FOOD_PLATFORM
    plat = ((X - cx) ** 2 + (Y - cy) ** 2 <= r * r) & (Z <= zt)
    assert plat.sum() > 0 and field.blocked[plat].all()


def test_obstacle_voxels_zero(field):
    assert np.all(field.conc[field.blocked] == 0.0)
    # lookups at solid interiors are 0 too
    pts = np.array([[180.0, 30.0, 100.0], [300.0, 180.0, 150.0], [440.0, 80.0, 100.0],
                    [165.0, -95.0, 5.0], [0.0, 0.0, 10.0]])
    assert np.all(field.lookup(pts) == 0.0)


def test_free_space_reachable(field):
    free = ~field.blocked
    assert np.all(np.isfinite(field.dist[free]))
    assert np.all(field.conc[free] > 0.0)


def test_maximum_at_food_voxel(field):
    imax = np.unravel_index(np.argmax(field.conc), field.shape)
    assert imax == field.world_to_index(cfg.FOOD_POS)
    assert field.lookup(cfg.FOOD_POS) == pytest.approx(1.0)
    # strictly unique maximum
    assert np.sum(field.conc == field.conc.max()) == 1


def test_shadowed_point_weaker_than_open_point(field):
    food = cfg.FOOD_POS
    behind = np.array([250.0, 150.0, 100.0])          # straight line to food crosses tower 2
    r = np.linalg.norm(behind - food)
    open_pt = food + np.array([0.0, -r, 0.0])        # same Euclidean distance, clear line (x = 440)
    assert np.linalg.norm(open_pt - food) == pytest.approx(r)
    # line of sight check: segment behind->food passes through tower 2
    (x0, x1), (y0, y1), (z0, z1) = cfg.TOWER2
    seg = behind + np.linspace(0, 1, 200)[:, None] * (food - behind)
    assert np.any((seg[:, 0] >= x0) & (seg[:, 0] <= x1) & (seg[:, 1] >= y0) & (seg[:, 1] <= y1)
                  & (seg[:, 2] >= z0) & (seg[:, 2] <= z1))
    c_b, c_o = field.lookup(behind), field.lookup(open_pt)
    assert c_b < c_o
    # path distance behind the tower is clearly longer than Euclidean
    assert field.dist[field.world_to_index(behind)] > 1.1 * r


def test_trilinear_exact_at_grid_points(field):
    rng = np.random.default_rng(0)
    free_idx = np.argwhere(~field.blocked)
    # random free voxels + every free voxel face-adjacent to a solid
    pick = free_idx[rng.choice(len(free_idx), 2000, replace=False)]
    b = field.blocked
    near = np.zeros_like(b)
    for ax in range(3):
        near |= np.roll(b, 1, ax) | np.roll(b, -1, ax)
    near_idx = np.argwhere(near & ~b)
    idx = np.concatenate([pick, near_idx])
    pts = field.origin + field.res * idx
    np.testing.assert_allclose(field.lookup(pts), field.conc[tuple(idx.T)], rtol=1e-12, atol=0)
    # corners of the grid (upper boundary included)
    corners = np.array([[b_[0] for b_ in cfg.ODOR_GRID_BOUNDS], [b_[1] for b_ in cfg.ODOR_GRID_BOUNDS]])
    np.testing.assert_allclose(field.lookup(corners), [field.conc[0, 0, 0], field.conc[-1, -1, -1]])


def test_trilinear_is_linear_between_free_voxels(field):
    p0 = np.array([100.0, -50.0, 250.0])  # all corners free, far from solids
    p1 = p0 + field.res * np.array([1.0, 0.0, 0.0])
    mid = 0.5 * (p0 + p1)
    assert field.lookup(mid) == pytest.approx(0.5 * (field.lookup(p0) + field.lookup(p1)))


def test_outside_grid_zero(field):
    (xa, xb), (ya, yb), (za, zb) = cfg.ODOR_GRID_BOUNDS
    pts = np.array([[xa - 0.1, 0, 50], [xb + 0.1, 0, 50], [0, ya - 1, 50], [0, yb + 1, 50],
                    [0, 0, za - 0.01], [0, 0, zb + 5], [1e4, 1e4, 1e4]])
    assert np.all(field.lookup(pts) == 0.0)
    assert field.lookup([xb + 0.1, 0, 50]) == 0.0


def test_no_fake_gradient_next_to_solids(field):
    # Just above the platform top the field must not be pulled to 0 by the solid
    # voxels below (they are excluded and weights renormalised).
    cx, cy, _, zt = cfg.FOOD_PLATFORM
    above = field.lookup([cx + 5.0, cy, zt + 0.5])
    assert above > 0.5 * field.lookup([cx + 5.0, cy, zt + field.res])


def test_food_outside_grid_rejected():
    f = OdorField3D(((0, 10), (0, 10), (0, 10)), 1.0, (20, 5, 5), 2.0)
    with pytest.raises(ValueError):
        f.build()


def test_iasym_sign_convention():
    # odor source to the right of a fly heading +x -> I_asym > 0 (turn right, as in walking)
    f = OdorField3D(((-50, 50), (-50, 50), (0, 50)), 1.0, (20.0, -20.0, 20.0), 5.0)
    f.build()
    a = antenna_odor(f, [0.0, 0.0, 20.0], yaw_rot(0.0), 0.5)
    assert a["I_asym"] > 0
    a = antenna_odor(f, [0.0, 0.0, 20.0], yaw_rot(np.pi), 0.5)  # facing -x: source on the left
    assert a["I_asym"] < 0
    # source above -> I_grad > 0
    f2 = OdorField3D(((-20, 20), (-20, 20), (0, 60)), 1.0, (0.0, 0.0, 50.0), 5.0)
    f2.build()
    assert antenna_odor(f2, [0.0, 0.0, 20.0], yaw_rot(0.3), 0.5)["I_grad"] > 0


def test_iasym_report_at_takeoff(field):
    """Report |I_asym| at the take-off point (x20 arena). Not a pass/fail threshold;
    the l_eff decision goes to the user (SPEC Stage 1)."""
    p = cfg.START_POS + np.array([0.0, 0.0, 1.0])  # 1 mm above the thorax rest height
    e = 0.5
    g = np.array([(field.lookup(p + e * np.eye(3)[a]) - field.lookup(p - e * np.eye(3)[a])) / (2 * e)
                  for a in range(3)])
    g_yaw = np.arctan2(g[1], g[0])
    print(f"\n[I_asym report] take-off {p}, C={field.lookup(p):.4g}, "
          f"path d={field.dist[field.world_to_index(cfg.START_POS)]:.0f} mm, "
          f"horizontal gradient yaw={np.degrees(g_yaw):.1f} deg")
    for ell in (cfg.ANTENNA_HALF_SEP_REAL, cfg.ANTENNA_HALF_SEP_EFF):
        for off in (30, 90):
            a = antenna_odor(field, p, yaw_rot(g_yaw + np.radians(off)), ell)  # gradient on the right
            print(f"  l={ell:4.1f} mm, gradient {off:2d} deg right: I_asym={a['I_asym']:+.4f}, "
                  f"walking turn term 2*tanh(20*I)={2 * np.tanh(20 * a['I_asym']):+.3f}")
            assert a["I_asym"] > 0


def test_antenna_never_samples_inside_solids(field):
    """Stage 4 v7: 2 mm from tower 1's west face, the l_eff = 10 mm left sample
    point lay inside the tower (C = 0) -> I_asym = +1, full turn from the wall
    alone. Samples are now kept outside solids (same l for both sides of a pair)."""
    x0 = cfg.TOWER1[0][0]
    worst = 0.0
    for clr in (0.3, 1.0, 2.0, 5.0, 9.0):
        for hd in np.radians(np.arange(-180, 180, 15)):
            p = np.array([x0 - clr, 50.0, 118.0])
            a = antenna_odor(field, p, yaw_rot(hd), cfg.ANTENNA_HALF_SEP_EFF)
            for q in (p + a["ell_LR"] * yaw_rot(hd)[:, 1], p - a["ell_LR"] * yaw_rot(hd)[:, 1]):
                assert not field.inside_solid(q[None])[0]
            assert a["ell_LR"] <= cfg.ANTENNA_HALF_SEP_EFF
            worst = max(worst, abs(a["I_asym"]))
    # heading along the wall with the wall on the left: the old sampling read 0 on the left
    p = np.array([x0 - 2.0, 50.0, 118.0])
    a = antenna_odor(field, p, yaw_rot(-np.pi / 2), cfg.ANTENNA_HALF_SEP_EFF)
    assert a["ell_LR"] == pytest.approx(2.0, abs=0.3)
    assert a["L"] > 0 and a["R"] > 0
    print(f"\n[wall] max |I_asym| within 9 mm of tower 1 west face: {worst:.3f} (was 1.000)")
    assert worst < 0.2


def test_platform_does_not_zero_the_lower_antenna(field):
    """Just above the food platform, the D sample (-10 mm) used to fall inside the
    platform cylinder -> I_grad = +1 (climb)."""
    cx, cy, r, zt = cfg.FOOD_PLATFORM
    p = np.array([cx - r + 2.0, cy, zt + 1.0])
    a = antenna_odor(field, p, yaw_rot(0.0), cfg.ANTENNA_HALF_SEP_EFF)
    assert a["ell_UD"] < 1.5 and a["D"] > 0
    assert abs(a["I_grad"]) < 0.5
