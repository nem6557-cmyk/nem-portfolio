# Solver outputs excluded from this repository

The converged VTK field exports (internal.vtu, boundary *.vtp) and the
compressed meshes (*.msh.gz) for the three condenser-manifold cases total
roughly 210 MB and are excluded to keep the repository clonable. Every
case here is complete and reproducible: `Allrun` in each case directory
regenerates the mesh and fields, and the post-processing scripts rebuild
every figure. The exported fields are available on request.
