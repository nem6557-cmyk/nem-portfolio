# Editable schematics + CSV data

Editable vector versions of the chamber schematics, plus the experimental data and
every paper table as CSV.

## Schematics

Seven schematics are provided, each as editable vector. They are clean redraws built
directly from the real geometry (tube coordinates in `data/cfd_tube_positions.json`) and
the dimensions in the manuscripts, not traced bitmaps.

| Figure | Built from |
|---|---|
| `bundle_xsec_33tube` | measured 33-tube coordinates, OD 4.76 / ID 3.14 mm |
| `bundle_xsec_42tube` | measured 42-tube CAD coordinates, OD 3.175 / ID 1.39 mm |
| `bundle_xsec_66tube` | 66-tube coordinates, OD 2.0 / ID 1.8 mm (forecast geometry) |
| `computational_domain_front` | chamber 80x80x42 mm, 40% fill, chip + bundle |
| `microchannel_section` | Cooke-Kandlikar surface, 381 / 400 / 250 um |
| `physics_model_map` | the gray-box reduced-order model flowchart (Part I) |
| `numerical_study_map` | the 3D VOF framework flowchart (Part II) |

### Which format to use

- **`chamber_schematics.pptx`** - a slide deck, one schematic per slide with a title and
  caption. Figures are high-resolution renders; use this for presenting or dropping slides
  into a talk.
- **`schematics/svg/`** - the fully editable source. Open in **Inkscape** (or any vector
  editor); text is real text, every shape is editable, rendering is exact. This is the
  primary format for editing a figure.
- **`schematics/pdf/`** - the same figures as vector PDF, for direct inclusion in LaTeX
  (`\includegraphics`) or printing.
- **`schematics/emf/`** - the five geometric schematics as EMF. In **PowerPoint**, Insert >
  Picture, then right-click > Group > Ungroup to turn the figure into editable PowerPoint
  shapes. (The two flowcharts are omitted here: they are wide enough that the SVG-to-EMF
  conversion clips them. Edit the flowcharts via the SVG or the generator below.)
- **`schematics/flowcharts_source_build_diagrams.py`** - the parametric Graphviz source for
  the two flowcharts. Edit the node text or colours and re-run (`python
  flowcharts_source_build_diagrams.py`, needs `graphviz`) to regenerate them. This is the
  easiest way to change flowchart content.

### Not reproduced as vector (intentionally)

Several manuscript figures are 3D renders or simulation output and cannot be turned into
editable line-art without redrawing from scratch. These remain raster in the papers:
the isometric domain and 3D microchannel views, the snappyHexMesh screenshots, and the
CFD field contour images (temperature, phase fraction). The data plots (boiling curves,
parity, residuals, resistance, cross-validation, sensitivity) are not schematics; they
regenerate from `master_chamber_model.py` and the CSVs here.

## Data (`data_csv/`)

**Raw measurements**
- `experimental_data_all_points.csv` - all 261 measured points (condenser, chip,
  coolant set point, q'', Q, T_surf, T_sat, T_liq, T_in, T_out, P, flow).
- `experimental_33_plain.csv`, `experimental_42_plain.csv`, `experimental_33_micro.csv`,
  `experimental_42_micro.csv` - the same rows split per configuration (87 / 64 / 36 / 74).

**Geometry**
- `tube_positions_33tube.csv`, `tube_positions_42tube.csv`, `tube_positions_66tube.csv` -
  per-tube (x, y) coordinates in mm, with OD and ID.

**Paper tables** (one CSV each, values matching the manuscripts)
- `table_geometry.csv`, `table_Csf_vs_handbook.csv`, `table_calibrated_constants.csv`,
  `table_prediction_error.csv`, `table_out_of_sample_validation.csv`,
  `table_resistance_nearCHF_mKW.csv`, `table_resistance_median_mKW.csv`,
  `table_predicted_66tube.csv`, `table_coolant_operating_conditions.csv`,
  `table_mesh_summary.csv`.

## Notes

- The 66-tube inner diameter is 1.6 mm in `cfd_tube_positions.json` (the CFD positions file)
  but 1.8 mm in the geometry table (0.1 mm wall on a 2.0 mm OD). The tube-position CSV and
  bundle cross-section export the value in the coordinates file as-is; the geometry table CSV
  uses the manuscript value. Reconcile before publication if the 66-tube is reported.
- The flowcharts were reconciled with the reframed Part II: the previous "HPC" labels now
  read "production run" / "production-resolution step", and the unconverged-status node is
  unchanged in meaning.
