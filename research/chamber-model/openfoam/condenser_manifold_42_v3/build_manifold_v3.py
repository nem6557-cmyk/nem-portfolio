"""
42-tube coolant fluid domain, STEP-faithful (Heat_Exchanger_Design_3.step).
Flow path: Ø5 top port -> DOWN inlet manifold (X=-35) -> through 42 tubes (along X)
-> UP outlet manifold (X=+35) -> Ø5 top port out. Both ports centred at Y=0.
Tubes: axis X, ID 1.39, in a Z-band; manifolds are tall vertical channels.
"""
import sys, json, numpy as np, gmsh
g=json.load(open("/home/claude/final/chamber_project/condenser_study/tube_positions.json"))["42-tube (OD3.175, L62.6)"]
pos=np.array(g["positions_mm"]); ID=g["ID_mm"]; OD=g["OD_mm"]
# JSON axis1->Y, axis2->Z (+offset to real band Z[9,22])
Y=pos[:,0]; Z=pos[:,1]-pos[:,1].mean()+15.5
rID=ID/2.0
TX0,TX1=-31.0,31.0            # tube X extent (length ~62)
MZ0,MZ1=0.0,28.0             # manifold height (vertical channel)
MY0,MY1=-34.0,34.0          # manifold Y span
mw=10.0                      # manifold thickness in X
rport=2.5; Zport_top=40.0    # Ø5 top ports, up to Z=40

gmsh.initialize(); gmsh.option.setNumber("General.Terminal",0)
gmsh.model.add("hx"); occ=gmsh.model.occ
inMan = occ.addBox(TX0-mw, MY0,MZ0, mw, MY1-MY0, MZ1-MZ0)   # inlet manifold (X<-31)
outMan= occ.addBox(TX1,    MY0,MZ0, mw, MY1-MY0, MZ1-MZ0)   # outlet manifold (X>31)
bores=[occ.addCylinder(TX0,yi,zi, (TX1-TX0),0,0, rID) for (yi,zi) in zip(Y,Z)]
inPort = occ.addCylinder(-35.0,0.0,MZ1, 0,0,Zport_top-MZ1, rport)   # top port over inlet manifold
outPort= occ.addCylinder( 35.0,0.0,MZ1, 0,0,Zport_top-MZ1, rport)
allv=[(3,inMan),(3,outMan),(3,inPort),(3,outPort)]+[(3,b) for b in bores]
fused,_=occ.fuse([allv[0]],allv[1:]); occ.synchronize()
vols=gmsh.model.getEntities(3)
print(f"42-tube v3: fused solids={len(vols)} (want 1)")
xb=gmsh.model.getBoundingBox(3,vols[0][1])
print(f"  bbox X[{xb[0]:.0f},{xb[3]:.0f}] Y[{xb[1]:.0f},{xb[4]:.0f}] Z[{xb[2]:.0f},{xb[5]:.0f}] mm")
print(f"  42 tubes axis X, Z-band [{Z.min():.0f},{Z.max():.0f}], manifolds Z[0,28], ports Ø5 at (X=+-35,Y=0,Z=28..40)")
# tag inlet/outlet = the port top caps (Z=40)
def faces_near(axis,val,tol=0.4):
    out=[]
    for d,t in gmsh.model.getEntities(2):
        bb=gmsh.model.getBoundingBox(2,t); c=[(bb[0]+bb[3])/2,(bb[1]+bb[4])/2,(bb[2]+bb[5])/2]
        ext=[bb[3]-bb[0],bb[4]-bb[1],bb[5]-bb[2]]
        if abs(c[axis]-val)<tol and ext[axis]<tol: out.append(t)
    return out
top=faces_near(2,Zport_top)
# inlet = the one near X=-35, outlet near X=+35
inlet=[t for t in top if gmsh.model.getBoundingBox(2,t)[0]<0]
outlet=[t for t in top if gmsh.model.getBoundingBox(2,t)[0]>0]
allf=[t for d,t in gmsh.model.getEntities(2)]
walls=[t for t in allf if t not in inlet and t not in outlet]
print(f"  tagged inlet={inlet} outlet={outlet} walls={len(walls)}")
gmsh.model.addPhysicalGroup(2,inlet,name="inlet")
gmsh.model.addPhysicalGroup(2,outlet,name="outlet")
gmsh.model.addPhysicalGroup(2,walls,name="walls")
gmsh.model.addPhysicalGroup(3,[vols[0][1]],name="fluid")
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature",14)
gmsh.option.setNumber("Mesh.MeshSizeMin",max(0.15,ID/8))
gmsh.option.setNumber("Mesh.MeshSizeMax",3.0)
gmsh.option.setNumber("Mesh.Optimize",1); gmsh.option.setNumber("Mesh.OptimizeNetgen",1)
gmsh.model.mesh.generate(3)
ntet=gmsh.model.mesh.getElementsByType(4)[0].size
print(f"  3D mesh: ~{ntet:,} tets")
gmsh.option.setNumber("Mesh.MshFileVersion",2.2)
gmsh.write("/home/claude/fluid_42_v3.msh")
gmsh.write("/home/claude/hx42_v3_surface.stl")
print("  wrote fluid_42_v3.msh (gmshToFoam-ready) + surface stl")
gmsh.finalize()
