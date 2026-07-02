import ezdxf, numpy as np
from collections import Counter
doc = ezdxf.readfile("/mnt/user-data/uploads/Middle_Container_66_tubes_2_mm_OD_v1_Sheet1.dxf")
msp = doc.modelspace()

# collect circles from modelspace + inside block INSERTs
circles=[]
def grab(container):
    for e in container:
        if e.dxftype()=="CIRCLE":
            circles.append((e.dxf.center.x, e.dxf.center.y, e.dxf.radius))
grab(msp)
for ins in msp.query("INSERT"):
    try:
        for e in ins.virtual_entities():
            if e.dxftype()=="CIRCLE":
                c=e.dxf.center; circles.append((c.x,c.y,e.dxf.radius))
    except Exception: pass
circles=np.array(circles)
print(f"total circles found: {len(circles)}")
if len(circles):
    radii=np.round(circles[:,2],3)
    print("circle radius counts (drawn units):")
    for r,c in sorted(Counter(radii).items()):
        print(f"   r={r:.3f}  (d={2*r:.3f}) : {c}")

# dimensions (measured values)
dims=[]
for d in msp.query("DIMENSION"):
    try: dims.append(round(d.get_measurement(),3))
    except Exception: pass
print(f"\ndimension entities: {len(dims)}")
vals=sorted(set(dims))
print("unique measured dimension values:", [v for v in vals if v>0][:40])

# text annotations
txt=[]
for t in msp.query("TEXT MTEXT"):
    s = t.dxf.text if t.dxftype()=="TEXT" else t.text
    s=s.strip()
    if s: txt.append(s)
print(f"\ntext entities: {len(txt)}")
print("sample text:", txt[:30])
