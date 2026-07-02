# 66-tube coolant manifold — single-pass, axial centreline feed (v3)

Built from Full_Assembly_V1_2mm_OD_66_Tubes.step (next-gen 66-tube condenser, forecast).
Flow path (single-pass, one side straight to the other, NO loop):
Ø5 feed hole on the CENTRELINE entering AXIALLY through the back of the inlet plenum
(pointing at the tubes) -> across the flush tube face -> through 66 tubes along Y ->
out the axial centreline hole at the far end. Tubes ID 1.6, OD 2.0, staggered (rows
13/4/16/4/13/16). simpleFoam, laminar, water ~40 C, 4 L/min.

## Manifold modelling note
The real manifolds are LOFTED tapers (diffuser from the Ø5 hole opening out to the flush
tube face). Per direction, the inlet/outlet here are SIMPLIFIED to a thin plenum across the
tube face fed by the axial centreline Ø5 hole - this captures the correct feed direction
(axial, centreline, through the back, at the tubes) without the exact loft profile. If the
lofted diffuser is needed later, the plenum is the swap point. FORECAST geometry (no 66-tube
validation data) - exploratory.

## Run (OpenFOAM v2512 sourced)
    ./Allrun                      # gmshToFoam -> scale -> checkMesh -> simpleFoam -> foamToVTK
Output in run66/ (~944k cells). Then zip run66/VTK and send back, or open run66/case.foam.

## Regenerate the mesh (needs gmsh)
    python3 build_manifold_v3_66.py   # writes fluid_66_v3.msh

## Geometry
- 66 tubes, axis Y, length ~94, ID 1.6, real (X,Z) positions, Z-band [3,11]
- inlet/outlet: thin plenum across tube face + Ø5 axial centreline feed (X=0, Z=7) at Y=+-59
- single-pass: inlet -Y, outlet +Y
- BC: inlet flowRateInletVelocity 6.667e-5 m^3/s (4 L/min); outlet p=0; walls noSlip
