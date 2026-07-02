# 42-tube coolant manifold — STEP-faithful (v3)

Built from Heat_Exchanger_Design_3.step (the validated 42-tube condenser).
Real flow path: Ø5 TOP port over the inlet manifold -> DOWN the vertical inlet manifold
(X=-35) -> through the 42 tubes along X -> UP the vertical outlet manifold (X=+35) ->
Ø5 TOP port out. Both ports centred at Y=0. Tubes ID 1.39 in the Z-band [9,22];
manifolds are full-height vertical channels Z[0,28]. simpleFoam, laminar, water ~40 C, 4 L/min.

This corrects all earlier manifold models (centred axial stubs / side ports were wrong).

## Run (OpenFOAM v2512 sourced)
    ./Allrun                      # gmshToFoam -> scale -> checkMesh -> simpleFoam -> foamToVTK
Output in run42/. Converges to a mesh-limited plateau (tet mesh), field steady.
Then: zip run42/VTK and send it back for the figure set, or open run42/case.foam in ParaView.

## Regenerate the mesh (needs gmsh)
    python3 build_manifold_v3.py   # writes fluid_42_v3.msh

## Geometry (inferred from STEP, verified)
- 42 tubes, axis X, length ~62, ID 1.39, at real (Y,Z) positions, Z-band [9,22]
- vertical manifolds at X=+-35, Y[-34,34], Z[0,28]
- inlet  Ø5 top port at (X=-35, Y=0), flow enters downward
- outlet Ø5 top port at (X=+35, Y=0), flow exits upward
- BC: inlet flowRateInletVelocity 6.667e-5 m^3/s (4 L/min); outlet p=0; walls noSlip
