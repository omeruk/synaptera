"""3D odor field: Dijkstra path distance around solid obstacles + trilinear lookup.

Same idea as the walking field (fly_brain_body_simulation.py: build_odor_field),
extended to 3D: odor "flows" around towers/platforms instead of through them,
so a point shadowed by a tower smells weaker than an open point at the same
Euclidean distance. This is a static geometric model (no advection/turbulence).

    d(x) = shortest 26-connected voxel path from the food, avoiding obstacles
    C(x) = 1 / (1 + (d/d0)^2)      (C = 1 at the food, ~ (d0/d)^2 far away)

Blocked and unreachable voxels have C = 0. Lookups outside the grid return 0
(no clamping to edge values). 26-connectivity over-estimates Euclidean distance
by at most ~8% in some directions; this is a known discretisation error.

The flight package imports this file (flight/odor_field_3d.py re-exports it).
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra


class OdorField3D:
    def __init__(self, bounds, res, food_pos, d0):
        self.res = float(res)
        self.origin = np.array([b[0] for b in bounds], dtype=np.float64)
        self.shape = tuple(int(round((b[1] - b[0]) / self.res)) + 1 for b in bounds)
        self.food_pos = np.asarray(food_pos, dtype=np.float64)
        self.d0 = float(d0)
        self.blocked = np.zeros(self.shape, dtype=bool)
        self.solids = []          # exact geometry, for sample points (inside_solid)
        self.dist = None
        self.conc = None

    # ── grid coordinates ────────────────────────────────────────────────────
    def axes(self):
        return [self.origin[a] + self.res * np.arange(self.shape[a]) for a in range(3)]

    def voxel_centers(self):
        return np.meshgrid(*self.axes(), indexing="ij")

    def world_to_index(self, pos):
        """Nearest voxel index (i, j, k) for a world position (no bounds check)."""
        return tuple(int(v) for v in np.round((np.asarray(pos) - self.origin) / self.res))

    # ── obstacles (voxel centre inside the solid, boundary inclusive) ───────
    def add_box(self, box):
        (x0, x1), (y0, y1), (z0, z1) = box
        self.solids.append(("box", tuple(map(float, (x0, x1, y0, y1, z0, z1)))))
        X, Y, Z = self.voxel_centers()
        self.blocked |= (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1) & (Z >= z0) & (Z <= z1)

    def add_cylinder(self, cx, cy, r, z_top, z_bottom=0.0):
        self.solids.append(("cyl", tuple(map(float, (cx, cy, r, z_top, z_bottom)))))
        X, Y, Z = self.voxel_centers()
        self.blocked |= ((X - cx) ** 2 + (Y - cy) ** 2 <= r * r) & (Z >= z_bottom) & (Z <= z_top)

    def inside_solid(self, pts):
        """True where point(s) (N, 3) lie inside an obstacle's exact geometry."""
        p = np.atleast_2d(np.asarray(pts, dtype=np.float64))
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        out = np.zeros(len(p), dtype=bool)
        for kind, g in self.solids:
            if kind == "box":
                x0, x1, y0, y1, z0, z1 = g
                out |= (x >= x0) & (x <= x1) & (y >= y0) & (y <= y1) & (z >= z0) & (z <= z1)
            else:
                cx, cy, r, zt, zb = g
                out |= ((x - cx) ** 2 + (y - cy) ** 2 <= r * r) & (z >= zb) & (z <= zt)
        return out

    def free_extent(self, pos, direction, lmax, n=41):
        """How far (<= lmax) one can go from pos along direction before entering
        a solid (resolution lmax/(n-1)). 0 if pos itself is inside."""
        t = np.linspace(0.0, lmax, n)
        hit = self.inside_solid(np.asarray(pos, float) + t[:, None] * np.asarray(direction, float))
        if not hit.any():
            return float(lmax)
        i = int(np.argmax(hit))
        return float(t[i - 1]) if i > 0 else 0.0

    # ── Dijkstra ────────────────────────────────────────────────────────────
    def build(self):
        nx, ny, nz = self.shape
        n = nx * ny * nz
        idx = np.arange(n, dtype=np.int32).reshape(self.shape)
        free = ~self.blocked

        def sl(d, size):  # (source slice, destination slice) along one axis
            return (slice(0, size - d), slice(d, size)) if d >= 0 else (slice(-d, size), slice(0, size + d))

        rows, cols, wts = [], [], []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    # each undirected edge once: first non-zero offset positive
                    off = (dx, dy, dz)
                    if off == (0, 0, 0) or next(v for v in off if v != 0) < 0:
                        continue
                    sa, sb = zip(*(sl(d, s) for d, s in zip(off, self.shape)))
                    m = free[sa] & free[sb]
                    rows.append(idx[sa][m])
                    cols.append(idx[sb][m])
                    wts.append(np.full(int(m.sum()), self.res * np.sqrt(dx * dx + dy * dy + dz * dz)))

        # Virtual source node n: joined to the free corners of the cell that
        # contains the food, with their exact Euclidean distances.
        u = (self.food_pos - self.origin) / self.res
        if np.any(u < 0) or np.any(u > np.array(self.shape) - 1):
            raise ValueError("food position outside the odor grid")
        base = np.minimum(np.floor(u).astype(int), np.array(self.shape) - 2)
        src_nodes, src_w = [], []
        for c in np.ndindex(2, 2, 2):
            ijk = tuple(base + np.array(c))
            if free[ijk]:
                p = self.origin + self.res * np.array(ijk)
                src_nodes.append(idx[ijk])
                src_w.append(max(np.linalg.norm(p - self.food_pos), 1e-9))  # 0 = "no edge" in csgraph
        if not src_nodes:
            raise ValueError("food cell is fully blocked")
        rows.append(np.full(len(src_nodes), n, dtype=np.int32))
        cols.append(np.array(src_nodes, dtype=np.int32))
        wts.append(np.array(src_w))

        g = coo_matrix((np.concatenate(wts), (np.concatenate(rows), np.concatenate(cols))),
                       shape=(n + 1, n + 1)).tocsr()
        d = dijkstra(g, directed=False, indices=n)[:n].reshape(self.shape)
        self.dist = d
        conc = np.where(np.isfinite(d), 1.0 / (1.0 + (d / self.d0) ** 2), 0.0)
        conc[self.blocked] = 0.0
        self.conc = conc.astype(np.float64)
        return self.conc

    # ── lookup ──────────────────────────────────────────────────────────────
    def lookup(self, pos):
        """Trilinear concentration at world point(s). pos: (3,) or (N, 3).

        Exact at voxel centres; 0 outside the grid.
        """
        p = np.atleast_2d(np.asarray(pos, dtype=np.float64))
        u = (p - self.origin) / self.res
        hi = np.array(self.shape) - 1
        inside = np.all((u >= -1e-9) & (u <= hi + 1e-9), axis=1)
        u = np.clip(u, 0, hi)
        i0 = np.minimum(np.floor(u).astype(int), hi - 1)
        f = u - i0
        num = np.zeros(len(p))
        den = np.zeros(len(p))
        c, free = self.conc, ~self.blocked
        for cx in (0, 1):
            wx = f[:, 0] if cx else 1 - f[:, 0]
            for cy in (0, 1):
                wy = f[:, 1] if cy else 1 - f[:, 1]
                for cz in (0, 1):
                    wz = f[:, 2] if cz else 1 - f[:, 2]
                    ii = (i0[:, 0] + cx, i0[:, 1] + cy, i0[:, 2] + cz)
                    w = wx * wy * wz * free[ii]
                    num += w * c[ii]
                    den += w
        # Blocked corners are left out and the weights renormalised; otherwise
        # their zeros would create a fake gradient pointing away from every
        # wall. Points whose free corners carry no weight (inside a solid) -> 0.
        ok = inside & (den > 1e-9)
        out = np.zeros(len(p))
        out[ok] = num[ok] / den[ok]
        return out if np.ndim(pos) == 2 else float(out[0])


def build_arena_odor_field(cfg=None):
    """Odor field for the flight arena in flight/config.py."""
    if cfg is None:
        from flight import config as cfg
    field = OdorField3D(cfg.ODOR_GRID_BOUNDS, cfg.ODOR_GRID_RES, cfg.FOOD_POS, cfg.ODOR_D0)
    for box in cfg.TOWERS:
        field.add_box(box)
    field.add_cylinder(*cfg.TAKEOFF_PEDESTAL)
    field.add_cylinder(*cfg.FOOD_PLATFORM)
    field.build()
    return field


def antenna_odor(field, pos, rot, half_sep):
    """Odor at the four antenna sample points.

    rot: 3x3 sampling frame -> world (columns = forward, left, up; FlyGym/MuJoCo
    convention). Returns dict with L, R, U, D, I_asym, I_grad and the sampling
    half-separations actually used (ell_LR, ell_UD).
    I_asym > 0: odor stronger on the right (same sign as walking: turn right).
    I_grad > 0: odor stronger above.

    Sample points never enter a solid: each pair (L/R, U/D) uses the same
    half-separation min(half_sep, free extent on either side). Without this, at
    l_eff = 10 mm a sample point inside a tower read C = 0 next to the wall and
    gave |I| = 1 (full turn) from the wall alone (Stage 4 v7 run).
    """
    pos = np.asarray(pos, dtype=np.float64)
    left, up = rot[:, 1], rot[:, 2]
    ell_lr = min(field.free_extent(pos, left, half_sep), field.free_extent(pos, -left, half_sep))
    ell_ud = min(field.free_extent(pos, up, half_sep), field.free_extent(pos, -up, half_sep))
    L, R, U, D = field.lookup(np.stack([pos + ell_lr * left, pos - ell_lr * left,
                                        pos + ell_ud * up, pos - ell_ud * up]))
    return dict(L=L, R=R, U=U, D=D,
                I_asym=(R - L) / (R + L + 1e-12),
                I_grad=(U - D) / (U + D + 1e-12),
                ell_LR=ell_lr, ell_UD=ell_ud)
