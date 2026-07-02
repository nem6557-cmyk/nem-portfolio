# Condenser coolant manifold, 33-tube, AXIAL centred-port — FINISHED CASE

Complete, self-contained OpenFOAM case for the single-phase coolant side of the 33-tube
condenser. Straight-through header: Ø5 ports centred on the tube-axis centreline of each
plenum, aligned, flow along +Z. simpleFoam, laminar, water ~40 C, 4 L/min.

This folder is FINISHED two ways:
1. It already contains the SOLVED field (VTK/) — open it in ParaView right now, no run needed.
2. It contains everything to re-run from scratch in one command (./Allrun).

## Just want to look at the result (recommended)
Open in ParaView:
- VTK/manifold_33.vtm.series          (the solved field, time 500)
- or case.foam                         (after ./Allrun, native OpenFOAM reader)
Pre-rendered views are in figures/ (top_view, centreplane_slice, per_tube_distribution,
midtube_crossplane, streamlines, pressure).

IMPORTANT for WSL users: ParaView's GUI crashes under WSL on many setups (a known WSL/OpenGL
driver bug, not a case problem). Use NATIVE WINDOWS ParaView instead: install ParaView for
Windows, then File > Open and paste this path:
  \\wsl$\Ubuntu\home\<you>\...\condenser_manifold_33_FINISHED\VTK\manifold_33.vtm.series
It uses your real GPU and will not crash. (If you must use WSL ParaView, launch with
LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe paraview &  and open via File menu.)

## Re-run from scratch (needs OpenFOAM v2512 sourced)
    ./Allrun        # gmshToFoam -> scale mm->m -> checkMesh -> simpleFoam -> foamToVTK
    ./Allclean      # remove results, keep the setup
Converges to a mesh-limited residual plateau (~1e-3 on this tet mesh), field steady.

## Result summary
Central "bullseye" maldistribution: the centred jet over-feeds the single on-axis tube to
~989 mL/min (~8x the 125 mL/min mean); the rest of the bundle is starved (20-210). Distribution
is left-right and top-bottom symmetric (the physical check that the geometry is correct).
Mass conserved to 3% (4116 vs 4000 mL/min). CoV ~131%, driven by the one central tube. Pressure drop inlet->outlet = 10.45 kPa, and it is dominated almost entirely by the Ø5 OUTLET PORT contraction: the tube bundle itself contributes only ~25 Pa over its 95 mm, the plenums and tubes sit at a near-uniform ~9.7 kPa, and the full drop occurs across the exit into the small port. Implication: coolant pumping power is set by port sizing, not the tubes. See figures/pressure_along_length.png.
Honest scope: laminar (Re ~1200), single centred port (no diffuser), Path-B idealised plenum
walls. A diffuser / distributor plate / multi-port inlet would spread the jet and reduce the
spike — the natural next case.

## Contents
0/                 U (flowRateInletVelocity 6.667e-5 m^3/s), p (outlet 0)
constant/          transportProperties (water nu 6.58e-7), turbulenceProperties (laminar)
system/            controlDict, fvSchemes (upwind), fvSolution (SIMPLE, p 0.3 / U 0.5, non-ortho 3)
fluid_33_AXIAL.msh gmsh tet mesh, axial centred ports (390k cells)
VTK/               SOLVED field (time 500): internal + inlet/outlet/walls
figures/           pre-rendered plots:
                   - full3D_velocity_volume.png   (full 3D VOLUME render, whole domain, jet glows)
                   - full3D_pressure_volume.png   (full 3D VOLUME render, ΔP = 10.45 kPa)
                   - iso_velocity.png        (isometric 3D, centre-plane + mid-tube slices)
                   - iso_pressure_drop.png   (isometric 3D pressure, ΔP = 10.45 kPa inlet->outlet)
                   - top_view.png            (down the tube axis at mid-tube)
                   - centreplane_slice.png   (jet column on y=0)
                   - per_tube_distribution.png, midtube_crossplane.png, streamlines.png, pressure.png
Allrun, Allclean   build + clean scripts
case.foam          ParaView entry point
