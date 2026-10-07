"""--nt-impute (MODEL VARIANT N1, SPEC_SENSORY_INPUTS §3.4b): sign imputation for neurons without a Codex nt_type.

Table rule recomputed independently from the parquet, root_id mapping, only empty neurons change, and DEV-subnet brain
builds (DEV only, never a result): flag off = parquet signs; N1 = |w| kept, only the imputed neurons' signs differ;
N2 = N1 then the literature rule (literature wins where both apply).
"""
import numpy as np
import pandas as pd
import pytest

from flight import groups as G

pytestmark = pytest.mark.skipif(not G.PATH_NT_IMPUTE.exists(),
                                reason=f"{G.PATH_NT_IMPUTE.name} missing (see scripts/make_nt_impute.py)")


@pytest.fixture(scope="module")
def root_ids():
    return G.load_root_ids()


@pytest.fixture(scope="module")
def tab():
    return pd.read_csv(G.PATH_NT_IMPUTE, keep_default_na=False)


@pytest.fixture(scope="module")
def parquet_sign(root_ids):
    con = pd.read_parquet(G.PATH_CON, columns=["Presynaptic_Index", "Excitatory"])
    s = np.zeros(len(root_ids), np.int64)
    s[con["Presynaptic_Index"].to_numpy()] = con["Excitatory"].to_numpy()
    return s


def test_table_is_the_empty_set(tab, root_ids, parquet_sign):
    sil = pd.read_csv(G.PATH_NT_SILENT)
    empty = set(sil.loc[sil["nt_type"] == "none", "root_id"])
    assert len(tab) == len(empty) == 19042 and set(tab["root_id"]) == empty
    r2i = G.root_to_index(root_ids)
    np.testing.assert_array_equal(tab["published_sign"].to_numpy(), parquet_sign[tab["root_id"].map(r2i).to_numpy()])
    assert set(tab["imputed_sign"]) <= {-1, 0, 1}
    assert (tab.loc[tab["published_sign"] == 0, "imputed_sign"] == 0).all()   # no outputs: nothing to change


def test_table_internal_rule(tab):
    t = tab
    np.testing.assert_array_equal(t["imputed_sign"].to_numpy(),
                                  np.where(t["published_sign"] == 0, 0, np.sign(t["peer_syn_pos"] - t["peer_syn_neg"])))
    assert (t.loc[t["cell_type"] == "", ["n_peers", "imputed_sign"]] == 0).all().all()   # no cell_type: published sign kept
    assert (t.loc[t["n_peers"] == 0, "imputed_sign"] == 0).all()                        # no predicted peer: published sign kept
    assert int(((t["imputed_sign"] != 0) & (t["imputed_sign"] != t["published_sign"])).sum()) > 0


def test_rule_recomputed_from_codex(tab):
    """Independent re-implementation (per-edge pandas groupby) from the Codex export; skipped without ~/Downloads/neurons.csv.gz."""
    import os
    f = os.path.expanduser("~/Downloads/neurons.csv.gz")
    if not os.path.exists(f):
        pytest.skip("Codex neurons.csv.gz not available")
    nt = pd.read_csv(f, usecols=["root_id", "nt_type"]).set_index("root_id")["nt_type"]
    sgn = nt.map({"ACH": 1, "DA": 1, "SER": 1, "OCT": 1, "GABA": -1, "GLUT": -1})
    con = pd.read_parquet(G.PATH_CON, columns=["Presynaptic_ID", "Connectivity"])
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type"]).drop_duplicates("root_id")
    ct = ann.set_index("root_id")["cell_type"]
    con["ct"] = con["Presynaptic_ID"].map(ct)
    con["vote"] = con["Connectivity"] * con["Presynaptic_ID"].map(sgn)          # NaN for empty neurons: no vote
    net = con[con["ct"].notna()].groupby("ct")["vote"].sum()
    t = tab.set_index("root_id")
    want = np.sign(t["cell_type"].map(net).fillna(0)).astype(np.int64)
    want[t["published_sign"] == 0] = 0
    np.testing.assert_array_equal(t["imputed_sign"].to_numpy(), want.to_numpy())


def test_indices(tab, root_ids):
    idx, sgn, typ = G.nt_impute_indices(root_ids)
    assert np.all(np.diff(idx) > 0) and len(idx) == len(sgn) == len(typ) == int((tab["imputed_sign"] != 0).sum())
    t = tab.set_index("root_id")
    np.testing.assert_array_equal(t.loc[root_ids[idx], "imputed_sign"].to_numpy(), sgn)


def test_dev_brain_signs(root_ids, parquet_sign):
    """DEV subnet (never a result)."""
    from flight.brain import FlightBrain
    off = FlightBrain(dev_subnet=True, seed=0, verbose=False, olfaction_full=True)
    n1 = FlightBrain(dev_subnet=True, seed=0, verbose=False, olfaction_full=True, nt_impute=True)
    n2 = FlightBrain(dev_subnet=True, seed=0, verbose=False, olfaction_full=True, nt_impute=True, nt_literature=True)
    lit = FlightBrain(dev_subnet=True, seed=0, verbose=False, olfaction_full=True, nt_literature=True)
    np.testing.assert_array_equal(off.l2g, n1.l2g)
    i = np.asarray(off.syn.i[:])
    w0, w1, w2, wl = (np.asarray(b.syn.w_[:]) for b in (off, n1, n2, lit))
    gpre = off.l2g[i]
    np.testing.assert_array_equal(np.sign(w0), parquet_sign[gpre])
    np.testing.assert_allclose(np.abs(w1), np.abs(w0))
    idx, sgn, _ = G.nt_impute_indices(root_ids)
    sign_of = np.zeros(len(root_ids), np.int64)
    sign_of[idx] = sgn
    m = sign_of[gpre] != 0
    assert m.any()
    np.testing.assert_array_equal(np.sign(w1[m]), sign_of[gpre[m]])
    np.testing.assert_array_equal(w1[~m], w0[~m])                      # nothing else changes
    assert n1.nt_imp_info["n_edges_changed"] == int((np.sign(w1) != np.sign(w0)).sum()) > 0
    assert off.nt_imp_info is None
    # N2: literature rule applied after the imputation, so wherever the literature table has a sign it wins
    lidx, lsgn, _ = G.nt_literature_indices(root_ids)
    lsign = np.zeros(len(root_ids), np.int64)
    lsign[lidx] = lsgn
    ml = lsign[gpre] != 0
    np.testing.assert_array_equal(w2[ml], wl[ml])
    np.testing.assert_array_equal(w2[~ml], w1[~ml])
    with pytest.raises(ValueError):
        FlightBrain(dev_subnet=True, seed=0, verbose=False, nt_impute=True, nt_silent="broad")


def test_shuffled_connectome(tmp_path):
    """Null control: edges keep presynaptic neuron, weight and sign; the postsynaptic column is a permutation; seed-reproducible."""
    from flight.brain import shuffled_connectome
    p1 = shuffled_connectome(tmp_path, 401)
    a = pd.read_parquet(G.PATH_CON)
    b = pd.read_parquet(p1)
    for c in ("Presynaptic_Index", "Presynaptic_ID", "Connectivity", "Excitatory", "Excitatory x Connectivity"):
        np.testing.assert_array_equal(a[c].to_numpy(), b[c].to_numpy())
    np.testing.assert_array_equal(np.sort(a["Postsynaptic_Index"].to_numpy()), np.sort(b["Postsynaptic_Index"].to_numpy()))
    assert (a["Postsynaptic_Index"].to_numpy() != b["Postsynaptic_Index"].to_numpy()).mean() > 0.9
    # the ID column moved together with the index column
    m = dict(zip(a["Postsynaptic_Index"].to_numpy()[:1000000], a["Postsynaptic_ID"].to_numpy()[:1000000]))
    assert all(m.get(i, j) == j for i, j in zip(b["Postsynaptic_Index"].to_numpy()[:200000], b["Postsynaptic_ID"].to_numpy()[:200000]))
