"""
66-tube coolant fluid domain, single-pass, SIMPLIFIED inlet/outlet (per direction:
keep it simple where the loft taper is fussy). Each manifold = a thin plenum across the
flush tube face, fed by a Ø5 hole entering AXIALLY on the centreline through the back
(pointing at the tubes). Single-pass: hole -> inlet plenum -> 66 tubes (Y) -> outlet plenum
-> hole. Tubes ID 1.6, OD 2.0, staggered.
"""
import json, numpy as np, gmsh
g=json.load(open("/home/claude/final/chamber_project/condenser_study/tube_positions.json"))["66-tube (OD2.0, L95)"]
pos=np.array(g["positions_mm"]); ID=g["ID_mm"]
X=pos[:,0]; Z=pos[:,1]-pos[:,1].mean()+7.0
rID=ID/2.0; Zc=float(np.mean([Z.min(),Z.max()]))
TY0,TY1=-47.0,47.0          # flush tube faces
plenY=4.0                    # plenum thickness across the tube face
RX=float(max(abs(X.min()),X.max()))+3.0
RZ0,RZ1=Z.min()-2.0, Z.max()+2.0
rport=2.5
HY0,HY1=-59.0,59.0          # Ø5 hole caps (inlet/outlet boundaries)

gmsh.initialize(); gmsh.option.setNumber("General.Terminal",0)
gmsh.model.add("t66"); occ=gmsh.model.occ
inP =occ.addBox(-RX,TY0-plenY,RZ0, 2*RX, plenY, RZ1-RZ0)      # inlet plenum (-Y)
outP=occ.addBox(-RX,TY1,      RZ0, 2*RX, plenY, RZ1-RZ0)      # outlet plenum (+Y)
inH =occ.addCylinder(0,HY0,Zc, 0,(TY0-plenY+1.0)-HY0,0, rport)  # axial centreline feed -> into inlet plenum
outH=occ.addCylinder(0,TY1+plenY-1.0,Zc, 0, HY1-(TY1+plenY-1.0),0, rport)
bores=[occ.addCylinder(xi,TY0-1.0,zi, 0,(TY1+1.0)-(TY0-1.0),0, rID) for (xi,zi) in zip(X,Z)]
allv=[(3,inP),(3,outP),(3,inH),(3,outH)]+[(3,b) for b in bores]
fused,_=occ.fuse([allv[0]],allv[1:]); occ.synchronize()
vols=gmsh.model.getEntities(3)
print(f"66 single-pass (simplified): fused solids={len(vols)} (want 1)")
b=gmsh.model.getBoundingBox(3,vols[0][1])
print(f"  bbox X[{b[0]:.0f},{b[3]:.0f}] Y[{b[1]:.0f},{b[4]:.0f}] Z[{b[2]:.0f},{b[5]:.0f}]")
print(f"  Ø5 axial feed on centreline (X=0,Z={Zc:.0f}) at Y=+-59 -> plenum across tube face X[+-{RX:.0f}] Z[{RZ0:.0f},{RZ1:.0f}]; 66 tubes ID{ID}")
def cap(yv,tol=0.6):
    out=[]
    for d,t in gmsh.model.getEntities(2):
        bb=gmsh.model.getBoundingBox(2,t); cy=(bb[1]+bb[4])/2; ext=bb[4]-bb[1]
        if abs(cy-yv)<tol and ext<tol: out.append(t)
    return out
inlet=cap(HY0); outlet=cap(HY1)
allf=[t for d,t in gmsh.model.getEntities(2)]
walls=[t for t in allf if t not in inlet and t not in outlet]
print(f"  tagged inlet={inlet} outlet={outlet} walls={len(walls)}")
gmsh.model.addPhysicalGroup(2,inlet,name="inlet")
gmsh.model.addPhysicalGroup(2,outlet,name="outlet")
gmsh.model.addPhysicalGroup(2,walls,name="walls")
gmsh.model.addPhysicalGroup(3,[vols[0][1]],name="fluid")
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature",12)
gmsh.option.setNumber("Mesh.MeshSizeMin",max(0.18,ID/8))
gmsh.option.setNumber("Mesh.MeshSizeMax",3.0)
gmsh.model.mesh.generate(3)
ntet=gmsh.model.mesh.getElementsByType(4)[0].size
print(f"  3D mesh: ~{ntet:,} tets")
gmsh.option.setNumber("Mesh.MshFileVersion",2.2)
gmsh.write("/home/claude/fluid_66_v3.msh"); gmsh.write("/home/claude/t66_v3_surface.stl")
print("  wrote fluid_66_v3.msh + surface stl")
gmsh.finalize()
