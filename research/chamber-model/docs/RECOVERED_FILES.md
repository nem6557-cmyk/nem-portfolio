# Recovered from chamber_project_complete_1_.zip

Files that existed in the older `chamber_project` archive but were dropped from
`chamber_model_final`. Restored here for completeness and reproducibility.
Generators are placed next to the outputs they produce; relative imports may
need adjustment to the reorganized layout.

| Restored file | Original path | Produces |
|---|---|---|
| data/c33.npy | data/c33.npy | cached 33-tube condenser array |
| data/c42.npy | data/c42.npy | cached 42-tube condenser array |
| docs/build_diagrams.py | diagrams/build_diagrams.py | docs/physics_model_map.*, docs/numerical_study_map.* |
| pub_figs/publication_analysis.py | analysis/publication_analysis.py | pub_figs/fig_*.{png,pdf}, predictions.csv, results_table.tex |
| openfoam/postprocess_3d.py | openfoam/postprocess_3d.py | the 3D VOF PyVista renders |

NOT restored: report/report.tex and report/report.pdf, superseded by paper/.
