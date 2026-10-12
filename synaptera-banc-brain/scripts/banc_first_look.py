"""First look at the FlyWire Codex BANC export (neurons-banc.csv.gz, connections_princeton-banc.csv.gz): coverage, key
cell types for flight and feeding, motor neurons and the left/right input balance. Analysis only (prints a report).

    env -u PYTHONPATH python synaptera-banc-brain/scripts/banc_first_look.py <directory with the two .csv.gz files>

Reading: synaptera-banc-brain/03_BANC_OPPORTUNITIES.md, appendix A.
"""
import glob
import sys

import numpy as np
import pandas as pd

d = sys.argv[1]
NEURONS = glob.glob(f"{d}/*neurons-banc.csv.gz")[0]
CONNECTIONS = glob.glob(f"{d}/*connections_princeton-banc.csv.gz")[0]

# ── coverage ──
n=pd.read_csv(NEURONS, low_memory=False)
c=pd.read_csv(CONNECTIONS, low_memory=False)
print("NEURONS", n.shape); print(n.columns.tolist())
for col in ["Flow","Super Class","Body Part","Soma side","Predicted NT type","Function"]:
    print("--",col); print(n[col].value_counts(dropna=False).head(15).to_string())
print("typed (Primary Cell Type notna):", n["Primary Cell Type"].notna().mean())
print("CONN", c.shape, "syn total", c.syn_count.sum(), "min syn", c.syn_count.min(), "median", c.syn_count.median())
print("nt_type", c.nt_type.value_counts(dropna=False).head(10).to_string())
pairs=c.groupby(["pre_root_id","post_root_id"]).syn_count.sum()
print("unique pairs", len(pairs), "syn", pairs.sum())
ids=set(n["Root ID"])
print("conn ids not in neurons: pre", (~c.pre_root_id.isin(ids)).mean(), "post", (~c.post_root_id.isin(ids)).mean())
print("top neuropils", c.groupby("neuropil").syn_count.sum().sort_values(ascending=False).head(25).to_string())

# ── key types, motor neurons, left/right ──
n=pd.read_csv(NEURONS, low_memory=False).set_index("Root ID")
c=pd.read_csv(CONNECTIONS, usecols=["pre_root_id","post_root_id","syn_count"])
pt=n["Primary Cell Type"].astype(str); alt=n["Alternative Cell Type(s)"].astype(str)
insyn=c.groupby("post_root_id").syn_count.sum().reindex(n.index).fillna(0)
outsyn=c.groupby("pre_root_id").syn_count.sum().reindex(n.index).fillna(0)
print("mean in-syn/neuron", insyn.mean(), "mean in-edges", c.groupby('post_root_id').size().reindex(n.index).fillna(0).mean())
side=n["Soma side"]
for sc in ["optic_lobe_intrinsic","central_brain_intrinsic","visual_projection","descending","ascending","motor","ventral_nerve_cord_intrinsic"]:
    m=n["Super Class"]==sc
    L=insyn[m&(side=="left")].sum(); R=insyn[m&(side=="right")].sum()
    print(f"{sc}: n L/R {(m&(side=='left')).sum()}/{(m&(side=='right')).sum()}  in-syn R/L {R/max(L,1):.3f}")
def show(pat, col=pt):
    m=col.str.contains(pat, regex=True, na=False)
    sub=n[m|alt.str.contains(pat,regex=True,na=False)]
    return sub
for t in [r"^DNg02",r"^DNp15$",r"^DNa02$",r"^DNa01$",r"^DNp01$",r"^DNp07$",r"^DNp10$",r"^DNp03$",r"MN9",r"CB0701",r"^LB3",r"^TTMn|TTM",r"^HS[NES]?$|^HS",r"^H2$",r"^LPLC2$",r"^LC4$"]:
    s=show(t)
    out=[]
    for rid,row in s.iterrows():
        out.append(f"{row['Primary Cell Type']}/{row['Soma side'][0]}:{int(insyn[rid])}")
    print(t, len(s), " ".join(out[:14]))
mot=n[n["Super Class"]=="motor"]
print("motor by Body Part:", mot["Body Part"].value_counts(dropna=False).to_string())
print("motor by Class:", mot["Class"].value_counts(dropna=False).head(15).to_string())
print("motor Sub Class:", mot["Sub Class"].value_counts(dropna=False).head(25).to_string())
w=mot[mot["Body Part"].astype(str).str.contains("wing|haltere|thorax",na=False)|mot["Class"].astype(str).str.contains("wing|haltere|flight",na=False)|mot["Sub Class"].astype(str).str.contains("wing|haltere|flight",na=False)]
print("wing/haltere/thorax MN types:", w["Primary Cell Type"].value_counts().head(60).to_dict())
dn=n[n["Super Class"]=="descending"]
g=pd.DataFrame(dict(t=dn["Primary Cell Type"],s=dn["Soma side"],i=insyn[dn.index]))
p=g.groupby(["t","s"]).agg(k=("i","size"),i=("i","sum")).unstack("s").dropna()
p=p[(p[("k","left")]==1)&(p[("k","right")]==1)]
r=np.log2(p[("i","right")]/p[("i","left")].clip(lower=1))
print("paired DN types",len(p),"median|log2|",round(r.abs().median(),3),"frac>0.5",round((r.abs()>0.5).mean(),3),"frac>1",round((r.abs()>1).mean(),3),"median signed",round(r.median(),3))
for t in ["DNp15","DNa02","DNa01","DNp01","DNp07","DNp10","DNg02_a"]:
    if t in p.index: print(" ",t, int(p.loc[t,("i","left")]), int(p.loc[t,("i","right")]), round(2**r[t],2))
