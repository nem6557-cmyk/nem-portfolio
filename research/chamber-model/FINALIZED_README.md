# Finalized manuscripts

This project was split from the single combined manuscript into two standalone,
independently compilable papers, with a consistency pass that reconciled every reported
number against its source table.

## Deliverables (at this project root)

| File | What it is |
|---|---|
| `paper_part1.pdf` | Part I, compiled (27 pp.): the validated reduced-order predictive thermal model. |
| `paper_part1.tex` | Part I source. |
| `paper_part2.pdf` | Part II, compiled (25 pp.): the 3D VOF phase-change simulation framework. |
| `paper_part2.tex` | Part II source. |
| `CHANGELOG_split.md` | Every edit and structural decision in the split/consistency pass. |

The original combined manuscript is preserved unchanged at
`paper/extended_52page/combined_paper.tex`.

## Recompiling

Both `.tex` files use a project-root-relative graphics path
(`\graphicspath{{./}{figs/}{figures/}{pub_figs/}{openfoam/doc_figs/}{openfoam/chamber42_3d/calibration/}}`),
so compile them **from this directory (the project root)**, not from a subfolder:

```
pdflatex paper_part1.tex && pdflatex paper_part1.tex && pdflatex paper_part1.tex
pdflatex paper_part2.tex && pdflatex paper_part2.tex && pdflatex paper_part2.tex
```

Three passes resolve cross-references, the bibliography, and (Part II) the table of contents.
Both compile with no errors and no undefined references. Each carries its own
`thebibliography` block, so no `bibtex`/`biber` run is required.

## Notes

- **Part I** is the mature, near-submittable manuscript. Open items before submission:
  add measurement-uncertainty error bars to the data figures, and ideally a third
  (66-tube) dataset to convert the cross-geometry generalization claim from two chambers
  to a true leave-one-chamber-out.
- **Part II** is a complete, reproducible specification of the CFD framework, presented under
  the project integrity standard: no unconverged or surrogate field is shown as a result. The
  converged production run (calibration, run to stationarity, field contours, and
  CFD-to-experiment overlay) is the remaining work. The forward work is framed by what it
  requires (production mesh resolution, calibration, a run to stationarity), not by any
  specific computing platform.
- **Companion cross-reference:** Part II refers to Part I narratively as "the companion
  reduced-order study" rather than as a formal citation, because there is no bibliography entry
  for Part I yet. Add a real citation (preprint or venue identifier) before either is submitted.
- The `[Author list]` placeholder in both title blocks needs to be filled in.

## Editable schematics + CSV data

`editable_schematics_and_csv/` contains editable vector versions of the chamber schematics
and all data as CSV. See its own `README.md` for details. In short:

- `chamber_schematics.pptx` - one schematic per slide (presentation deck).
- `schematics/svg/` - 7 schematics as editable SVG (Inkscape); `schematics/pdf/` - vector PDF;
  `schematics/emf/` - the 5 geometric schematics as EMF (ungroup in PowerPoint to edit);
  `schematics/flowcharts_source_build_diagrams.py` - Graphviz source for the 2 flowcharts.
- `data_csv/` - the 261 measured points (all and per-config), the 33/42/66-tube coordinates,
  and every paper table as CSV.

The 3D renders, mesh screenshots, and CFD field images are raster output and are not
reproduced as vector; the data plots regenerate from `master_chamber_model.py` and these CSVs.
