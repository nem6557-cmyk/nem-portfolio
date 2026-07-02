# Changelog: split and consistency pass on `combined_paper.tex`

Source: `combined_paper.tex` (1855 lines). Output: two standalone, independently
compilable manuscripts. Both compile under `pdflatex` (Part I 31 pp., Part II 29 pp.)
with no LaTeX errors, no undefined references, and no undefined citations.

## 0. Structure

The combined file was **split into two standalone articles** (the primary directive;
no combined version was required):

- **`paper_part1.tex`** — the reduced-order-model paper (former Part I). Complete journal
  article: own preamble, **new standalone abstract**, introduction, body, and a 34-entry
  bibliography. `\part` and `\tableofcontents` removed (journal norm for a single article).
- **`paper_part2.tex`** — the CFD framework (former Part II), held as a separate manuscript.
  Own preamble, **new standalone abstract**, `\tableofcontents` **kept**, and a 5-entry
  bibliography.

Both files retain the original preamble verbatim, including
`\graphicspath{{./}{figs/}{figures/}{pub_figs/}{openfoam/doc_figs/}{openfoam/chamber42_3d/calibration/}}`,
so all existing figures resolve from the project directory. The split point was the
`\part{Three-Dimensional VOF Phase-Change Framework}` boundary; the two parts share no
cross-`\ref` (Part I labels are unprefixed, Part II labels carry the `of-` prefix), so the
split is clean.

**Bibliography de-duplication.** Each file now carries only the references it cites:
- Part I keeps its 34 cited entries unchanged.
- Part II keeps `shukla2024`, `of-weller1998`, `of-hirt1981`, `of-brackbill1992`, `of-lee1980`.
- Dropped the duplicate-keyed/uncited entries `of-shukla2024`, `of-cooke2012`,
  `of-kandlikar2001`, `of-mody2022`. The single remaining Part II `\cite{of-shukla2024}`
  was repointed to the canonical `shukla2024` (see P2.2).

## 1. Part I changes

- **P1.1a — 66-tube physics (sec:scope, "The 66-tube." paragraph).** Removed the incorrect
  attribution "large area and short tubes." Rewrote so the low coolant-side resistance is
  attributed to the **smaller bore (1.80 mm ID vs 3.14 mm)** raising the internal
  developing-laminar convective coefficient, **partly offset by the smaller external area
  (394 vs 469 cm²)**, and noted the tubes are the same 95 mm length as the 33-tube
  (per Table `tab:geom66`).
- **P1.1b — sec:pred66.** *No edit needed.* This subsection already attributes the advantage
  to "a lower condenser-side resistance"/"roughly half the condenser-side resistance"; it
  contains no "large area"/"short tubes" phrasing. Line 807 (sec:scope) was the only
  occurrence file-wide.
- **P1.2 — Measurement-uncertainty flux range (sec:uncertainty).** Replaced the erroneous
  "4.2 % at the peak logged flux (37 W/cm²)" passage. The section now states that the boiling
  curves are **logged continuously over the full nucleate range up to each configuration's
  CHF, reaching 174 W/cm² on the microchannel 33-tube** (Table `tab:rmse`), so the high-flux
  branch is **measured, not extrapolation**. The flux-dependent conduction correction is made
  explicit: it reaches **~22 K at 174 W/cm²**, so **U_Tsurf widens from ±0.2 K at low/moderate
  flux to ~±0.5 K at the CHF points**. The U_Tsat (±0.15 K), wall-superheat (±0.25 K),
  CHF (±4 %), and coolant-balance statements are retained. The model-structure argument now
  uses the worst-case ±0.5 K against the 4.4 K RMSE.
- **P1.3 — Number reconciliation to the source tables.**
  - **RMSE 4.3 → 4.4 K.** Fixed in the abstract (rewritten) and in sec:uncertainty
    (Table `tab:rmse` and Conclusions already read 4.4).
  - **Leave-one-coolant-out prose (sec:crossval) → Table `tab:crossval`.** 33-tube
    "3.8 → 5.0 K" corrected to **"3.7 → 4.9 K"**; 42-tube "4.9 → 9.0 K" corrected to
    **"4.8 → 9.1 K"**.
  - **Held-out saturation error (sec:gen42) → Table `tab:crossval`.** "13.6 versus 6.4 K"
    corrected to **"15.3 versus 7.4 K"**. (The "8.6 versus 4.1 K" saturation-*map* residual
    is a distinct in-sample quantity not in the table and was left unchanged; the 4.9/9.1 K
    surface-temperature values at lines 611–612 were already correct.)
  - **Conclusions LOCO values (cross-cutting consistency).** Conclusions item 5 "5.0 K …
    (9.0 K …)" corrected to **"4.9 K … (9.1 K …)"** to match the same quantity in
    Table `tab:crossval`.
- **P1.4 — Future-work hygiene (Next actions, item 4).** Rescoped the stale "Complete the
  measurement-uncertainty section" (that section now exists) to **"Add error bars to the data
  figures,"** referencing `sec:uncertainty`.

## 2. Part II changes

- **P2.1 — Next-steps item 1 (of-sec:next).** Rescoped from "Quantify the
  measurement-uncertainty band" (already reported in the companion ROM study) to
  **"Overlay the measurement-uncertainty bands"** on the reference figures
  (`of-fig:boil`, `of-fig:res`). The specific "surface temperature ±0.2 K" value was
  **dropped** to avoid contradicting Part I's flux-dependent ±0.2 → ±0.5 K. **Item number 1
  was kept** so the existing cross-reference ("Section `of-sec:next`, item 1") still resolves.
- **P2.2 — De-duplicate the opening (Overview, paragraph 1).** Replaced the duplicated
  immersion-cooling motivation / apparatus / two-surface-two-bundle characterization with a
  **single sentence** citing the apparatus origin (`shukla2024`) and the companion
  reduced-order study, and stating Part II's scope (the 3D VOF route for the same apparatus).
  This also performed the `of-shukla2024` → `shukla2024` repoint.
  - *Note:* **Paragraph 2 was preserved** (not merged). It carries the project integrity
    standard — the hard line between measured data, the reduced-order model, and the CFD, and
    the statement that the boiling-curve/resistance comparisons "are the CFD's target, not CFD
    output." Per the integrity constraint, this framing must not be softened or removed, which
    takes precedence over the literal "first two paragraphs" wording.
- **P2.3 — Scope shared sections to CFD-only content (of-sec:geom).**
  - Added a one-line pointer after the section heading: the full apparatus geometry is in the
    companion study; this section records only the detail needed to reproduce the CFD mesh.
  - **Evaporator surfaces** subsection trimmed: the verbatim 381/400/250 µm and A_r = 2.17
    restatement was replaced by a pointer to the companion study, **keeping the CFD-specific
    treatment** (plain = flat heated wall; microchannel = planned extension) and the figure.
  - The computational-domain subsection, its figures, and `of-tab:cond` were **kept** for
    standalone CFD-mesh reproducibility.
  - *Note:* The **governing-equations section (of-sec:equations) was left unchanged.** It is
    disjoint from Part I (VOF transport / momentum–surface-tension / energy–latent coupling /
    Lee closure vs Part I's Rohsenow/Hausen network); there is no shared physics to merge.
- **P2.4 — Integrity framing preserved (no edits).** The reserved field-contour slots
  ("Field contours (pending the converged run)"), the "no surrogate or unconverged fields are
  shown as results" statement, and the labeling of the single-phase conduction and
  hydrostatic-pressure fields as **verification references** ("These are verification
  references, not the VOF phase-change result"; "Neither is the VOF phase-change solution")
  were all left untouched.

## 3. Cross-cutting

- **Future-work de-overlap.** Part I "Next actions" (experimental/ROM steps) and Part II
  "Next steps" (CFD-campaign steps) no longer overlap. Part II **item 8** was rescoped from the
  experimental "resolve CHF mechanism from wall-temperature traces and reconcile the
  33/66-tube CHF" to a **CFD-only** task: verify the CHF turnover / vapor-blanket dryout in the
  converged solution (referencing the 2D demonstration, `of-sec:twod`), with the experimental
  burnout-versus-ceiling determination deferred to the companion ROM study (already Part I
  Next-actions item 2). The 33/66-tube reconciliation clause was dropped from Part II.
- **Added foundational CFD citations.** To avoid orphan bibitems while keeping the two genuine
  foundational references, `\cite{of-weller1998}` (OpenFOAM finite-volume framework) and
  `\cite{of-hirt1981}` (VOF method) were added at the solver/governing-equations introduction.
  These are not duplicates and are not on the drop list.

## Integrity / no-new-data confirmation

No new data, results, or claims were introduced. Every reported number now matches its source
table (`tab:rmse`, `tab:crossval`, `tab:geom`/`tab:geom66`). The hard separation between
measured data, the reduced-order model, and CFD output is preserved, and no reserved slot or
unconverged field is presented as a result. No `TODO` markers were required: every flagged
discrepancy resolved cleanly against a source table.
