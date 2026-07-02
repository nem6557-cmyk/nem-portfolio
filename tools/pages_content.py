"""Content for the generated pages. Imported by build_pages.py.

Sources for every number: Mustafa & Kandlikar, ASME J. Heat Mass
Transfer, in press, DOI 10.1115/1.4072138 (experimental page); the
chamber-model package summaries in research/chamber-model (model and
CFD pages); the LittleJourney codebase counts (software page).
"""


def fig(src, w, h, alt, cap):
    return (f'<figure><div class="figure"><img src="assets/{src}" width="{w}" '
            f'height="{h}" loading="lazy" decoding="async" alt="{alt}"></div>'
            f'<figcaption>{cap}</figcaption></figure>')


PAGES = {

# ======================================================================
"research.html": dict(
    title="PhD Research",
    desc="Doctoral research on subcooled pool boiling with submerged condensation for high-heat-flux electronics cooling: experiments to 195.3 W/cm2, a validated reduced-order thermal model, and an OpenFOAM phase-change CFD program.",
    eyebrow="PhD research &middot; RIT Thermal Analysis, Microfluidics and Fuel Cell Lab",
    h1="Cooling the chips that cool nothing else can",
    lede="My doctoral research at RIT, advised by Dr. Satish Kandlikar, asks how much heat a sealed, pump-free boiling chamber can remove from a processor-scale surface. The program runs on three legs that check each other: experiments on a patented 1U chamber, a validated reduced-order thermal model, and an OpenFOAM phase-change CFD framework. This page is the map; the three pages below are the territory.",
    tags=["Pool boiling", "Submerged condensation", "Subatmospheric", "Two-phase", "ASME JHMT", "OpenFOAM"],
    readout=[
        '<div class="cell real"><div class="val">195.3 W/cm&sup2;</div><div class="lbl">PEAK CHF, WATER AT 12 kPa</div></div>',
        '<div class="cell real"><div class="val">66 W/cm&sup2;</div><div class="lbl">HFE-7000 RECORD, &gt;1 cm&sup2;</div></div>',
        '<div class="cell"><div class="val">R&sup2; 0.938</div><div class="lbl">MODEL VS 261 DATA POINTS</div></div>',
        '<div class="cell"><div class="val">CoV 10%</div><div class="lbl">42-TUBE MANIFOLD FLOW</div></div>',
    ],
    back_href="index.html", back_label="Home",
    prev_href="index.html", prev_label="Home",
    next_href="research-chamber.html", next_label="Next: The experiments",
    colophon="Thermal Analysis, Microfluidics and Fuel Cell Laboratory &middot; RIT.",
    body=f"""
  <section class="doc-section">
    <h2>The problem</h2>
    <p>Current GPUs dissipate 500 to 1000 W per device at substrate heat fluxes of 50 to 100 W/cm&sup2;, and announced parts push past that. Air cannot carry it, cold plates need pumps, and spray cooling needs pressurized plumbing. Pool boiling removes comparable fluxes with no moving parts, and sealing the chamber with a submerged condenser turns it into a passive thermosiphon: vapor condenses on coolant-fed tubes above the surface and rains back down, with zero pumping power on the refrigerant side. The catch is the critical heat flux ceiling, and raising that ceiling on a real, processor-sized surface is the dissertation.</p>
    <p>The work runs on a compact chamber that fits a standard 1U server envelope, under 50.8 mm tall, whose design is protected by U.S. Patent 12,349,313 B2, assigned to RIT. My research characterizes, models, and extends that chamber: microchannel-enhanced copper substrates, a dual-taper microgap manifold, an enhanced finned-tube condenser, and operation at subatmospheric pressure so water boils at 49 &deg;C instead of 100.</p>
  </section>

  <section class="doc-section">
    <h2>Three legs, one program</h2>
    <p><strong>Experiments.</strong> Subcooled pool boiling of water at 12 kPa and Novec 7000 at 1 atm on identical 11.04 cm&sup2; microchannel substrates, four channel widths, with and without the taper manifold, across coolant temperatures. Peak results: 195.3 W/cm&sup2; with water and the highest CHF reported for HFE-7000 on any surface above 1 cm&sup2;. Published across four ASME journal papers with a fifth in press.</p>
    <p><a class="link-arrow" href="research-chamber.html">The experiments and what they found <span>&rarr;</span></a></p>
    <p><strong>Reduced-order model.</strong> A gray-box thermal network that predicts chip temperature from geometry, coolant condition, and heat flux, calibrated on part of the data and validated against 261 measured points spanning two chamber generations, two surface types, and four coolant temperatures: RMSE 4.34 K, R&sup2; 0.938.</p>
    <p><a class="link-arrow" href="research-model.html">The model and its validation <span>&rarr;</span></a></p>
    <p><strong>CFD.</strong> An OpenFOAM program with two arms: single-phase conjugate flow through three condenser manifold generations, which found that flow distribution is governed by feed geometry rather than tube count, and a calibrated 2D and 3D volume-of-fluid phase-change framework for the boiling chamber itself.</p>
    <p><a class="link-arrow" href="research-cfd.html">The OpenFOAM program <span>&rarr;</span></a></p>
    {fig("r-study-map.png", 2693, 1876, "Map of the numerical study showing how the experiments, reduced-order model, and CFD arms connect", "How the legs connect: measurements calibrate the model, the model scopes the CFD, and the CFD explains what the point measurements cannot see.")}
  </section>

  <section class="doc-section">
    <h2>Selected publications</h2>
    <ul>
      <li><strong>Mustafa, N. E., and Kandlikar, S. G.</strong> Comparative Evaluation of Subcooled Pool Boiling Performance Using Novec 7000 and Water in a Taper Microgap Boiling Chamber. <em>ASME J. Heat Mass Transfer</em>, in press. DOI 10.1115/1.4072138.</li>
      <li><strong>Mustafa, N. E., and Kandlikar, S. G.</strong> (2026). Performance Evaluation of Boiling Chamber With Enhanced Boiling and Condensing Surfaces for Efficient Warm Water Operation. <em>ASME J. Heat Transfer</em>, 148(4), 041605.</li>
      <li><strong>Mustafa, N. E., and Kandlikar, S. G.</strong> (2025). Performance Evaluation of Boiling Chamber With Microchannel Chip and Taper Microgap. <em>ASME J. Heat Transfer</em>, 147(12), 121604.</li>
      <li><strong>Mustafa, N. E., and Kandlikar, S. G.</strong> (2025). Novel Subcooled Boiling Chamber With Submerged Condensation for High Heat Flux Removal for Data Center Application. <em>ASME J. Heat Transfer</em>, 147(1), 012601.</li>
      <li><strong>Shukla, M. Y., Mustafa, N. E., and Kandlikar, S. G.</strong> (2026). Performance of a Novel 1.5U Boiling Chamber With Higher Coolant Temperatures for High Heat Flux Dissipation in Data Center Applications. <em>Proc. 24th IEEE ITherm</em>.</li>
      <li><strong>Mustafa, N.</strong> (2024). Impact of Coolant Temperature on Boiling Chamber Performance for Cooling Electronic Chips. M.S. thesis, Rochester Institute of Technology.</li>
    </ul>
    <p>Two manuscripts from the modeling program are hosted here as preprints, downloadable on their pages: Part I, the validated reduced-order model, and Part II, the CFD framework. Additional manuscripts are in review, including transient bioheat transfer modeling for cardiac radiofrequency ablation with Dr. Cristian Linte.</p>
  </section>
""",
),

# ======================================================================
"research-chamber.html": dict(
    title="Boiling Chamber Experiments",
    desc="Subcooled pool boiling experiments on a patented 1U chamber: water at 12 kPa to 195.3 W/cm2, the highest reported HFE-7000 CHF above 1 cm2, and the coolant-temperature coupling that governs both.",
    eyebrow="Research &middot; Experiments",
    h1="Two fluids, one chamber, and the ceiling of passive cooling",
    lede="The experimental core of the dissertation: de-ionized water at 12 kPa and 3M Novec 7000 at 1 atm, boiled on identical 11.04 cm&sup2; microchannel copper substrates inside a sealed 1U chamber with a submerged finned-tube condenser. Four channel widths, a dual-taper microgap manifold, four coolant temperatures, and a formal uncertainty analysis under every number. In press at the ASME Journal of Heat and Mass Transfer.",
    tags=["Water at 12 kPa", "Novec 7000", "Taper microgap", "CHF", "High-speed visualization", "Uncertainty analysis"],
    readout=[
        '<div class="cell real"><div class="val">195.3 W/cm&sup2;</div><div class="lbl">WATER CHF, 45 C COOLANT</div></div>',
        '<div class="cell real"><div class="val">66 W/cm&sup2;</div><div class="lbl">HFE-7000, HIGHEST &gt;1 cm&sup2;</div></div>',
        '<div class="cell"><div class="val">0.012 K/W</div><div class="lbl">MINIMUM TOTAL RESISTANCE</div></div>',
        '<div class="cell"><div class="val">3.6&ndash;5.0&times;</div><div class="lbl">WATER-TO-NOVEC CHF RATIO</div></div>',
    ],
    back_href="research.html", back_label="Research overview",
    prev_href="research.html", prev_label="Research overview",
    next_href="research-model.html", next_label="Next: The model",
    colophon="Experimental results in press, ASME J. Heat Mass Transfer, DOI 10.1115/1.4072138.",
    body=f"""
  <section class="doc-section">
    <h2>The apparatus</h2>
    <p>The chamber is a sealed 70 by 85 mm unit, under 50.8 mm tall with the lid bolted, that sits directly on the processor's heat spreader; its design is protected by U.S. Patent 12,349,313 B2, assigned to RIT. Inside, 28 finned condenser tubes provide 48,440 mm&sup2; of condensing area fed by facility coolant at 4.75 kg/min. The test substrates are copper 101, 55 by 55 by 1 mm with a 34.5 by 32 mm active boiling area, machined with parallel open microchannels at widths of 381, 500, 762, and 1000 &mu;m, all 400 &mu;m deep with 250 &mu;m fins. The dual-taper microgap manifold sits above the substrate at a 7 degree angle with a 2 mm inlet gap: bubbles nucleating at the narrow inlet get squeezed by the converging geometry toward the wider outlet, pumping fresh subcooled liquid across the surface with no external actuation.</p>
    <p>Heat flux comes from Fourier conduction across three calibrated thermocouples in the heater block, with a Taylor backward-difference gradient and a Kline&ndash;McClintock uncertainty propagation: heat flux to &plusmn;2.14 W/cm&sup2; and surface temperature to &plusmn;1.06 &deg;C, with every experiment repeated and agreeing within 5%. Water runs at 12 kPa, where it saturates near 49 &deg;C; Novec 7000 runs at 1 atm because its 12 kPa saturation temperature of roughly minus 12 &deg;C is useless for electronics.</p>
  </section>

  <section class="doc-section">
    <h2>What the taper does, and to whom</h2>
    <p>The taper was expected to help both fluids. It did not, and the asymmetry is the paper's most interesting result. For Novec 7000, the taper raised CHF on every channel width, 18 to 39%, peaking at 51.4 W/cm&sup2; on the 762 &mu;m substrate, because Novec's low surface tension makes small bubbles the taper can squeeze. For water, whose surface tension is 5.5 times higher, departure diameters outgrow the 2 mm gap; bubbles coalesce inside the taper into vapor slugs that choke liquid return, and CHF falls from 185.3 to 125.5 W/cm&sup2; on the 381 &mu;m substrate. Same geometry, opposite outcome, and the high-speed imaging shows both mechanisms directly.</p>
    {fig("r-chf-summary.png", 1440, 600, "Bar charts of CHF for water and Novec 7000 across four microchannel widths, with and without the taper manifold", "CHF at 20 &deg;C coolant across all configurations, from Table 7 of the paper. The taper helps the dielectric on every width and hurts water on every width; one manifold geometry cannot serve both fluids.")}
    <p>Channel width has its own physics. The optimum shifted from 762 &mu;m for Novec to 381 &mu;m for water, tracking the Bond number: water's larger bubbles want the stronger capillary confinement of narrow channels, while Novec's small bubbles escape narrow channels freely. The 500 &mu;m width underperformed for both fluids, sitting in the transitional regime where confinement is strong enough to trap vapor but too weak to drive capillary pumping.</p>
  </section>

  <section class="doc-section">
    <h2>The coolant-temperature coupling</h2>
    <p>In a sealed chamber, coolant temperature, pool subcooling, and internal pressure are one knob, not three. Raising the coolant from 20 to 45 &deg;C cut pool subcooling, let bubbles survive to the condenser instead of collapsing in the pool, raised internal pressure and with it vapor density, and shifted the bubble population toward smaller, more frequent departures. Water CHF climbed 56%, from 125.5 to 195.3 W/cm&sup2;. At 50 &deg;C the condenser ran out of driving temperature difference, vapor blanketed the tubes, and CHF fell back to 136.8. The same pressure-driven mechanism took Novec 7000 from 51.4 to approximately 66 W/cm&sup2; at 40 &deg;C coolant, the highest CHF reported for HFE-7000 on any surface above 1 cm&sup2;.</p>
    {fig("r-coolant-study.png", 1020, 600, "CHF versus coolant inlet temperature for water and Novec 7000, peaking at 45 C for water before condenser saturation", "The optimum sits near 45 &deg;C, inside the ASHRAE W4/W5 warm-water classes modern data centers already supply. Peak performance on facility water that already exists is the practical headline.")}
  </section>

  <section class="doc-section">
    <h2>What it means at system level</h2>
    <p>At 195.3 W/cm&sup2; on 11.04 cm&sup2;, the chamber dissipates roughly 2156 W from a single substrate, above the TDP of every current and announced GPU, including 1400 W Blackwell-class parts, while operating as a fully passive thermosiphon on the refrigerant side inside a 1U envelope. Surface temperatures at CHF stayed moderate, 49 &deg;C for Novec at 20 &deg;C coolant and 77.9 &deg;C for water at 45 &deg;C, both under the 85 to 105 &deg;C junction limits of current processors. And because the working fluid is hermetically sealed and the facility side can reject heat through a dry cooler, the design eliminates cooling-tower evaporation, roughly 790,000 liters of water per year for a 50 kW rack.</p>
    <div class="callout">
      <span class="tag-lbl">Honest scope</span>
      <p>The taper geometry used here was optimized for dielectric-scale bubbles; the water result makes clear a single taper cannot serve both fluids, and gap-height optimization for water is stated future work. Novec values above 51.4 W/cm&sup2; come from the 40 &deg;C coolant condition, and all comparisons are at the stated coolant temperatures, not a universal rating.</p>
    </div>
  </section>
""",
),

# ======================================================================
"research-model.html": dict(
    title="Reduced-Order Chamber Model",
    desc="A gray-box thermal model of the boiling chamber validated against 261 measured points across two chamber generations: RMSE 4.34 K, R2 0.938, with parity, residual, and per-configuration breakdowns.",
    eyebrow="Research &middot; Reduced-order model",
    h1="A model you can check: 261 points, 4.3 kelvin",
    lede="Experiments tell you what one chamber did; a validated model tells you what the next one will do. This is a gray-box thermal network of the sealed chamber, physics where the physics is known and calibrated closures where it is not, that predicts chip temperature from geometry, coolant condition, and heat flux. Its worth is measured the only way that counts: against 261 experimental points it must explain.",
    tags=["Gray-box modeling", "Thermal network", "Calibration", "Cross-validation", "Python", "Preprint"],
    readout=[
        '<div class="cell real"><div class="val">R&sup2; 0.938</div><div class="lbl">261 MEASURED POINTS</div></div>',
        '<div class="cell real"><div class="val">4.34 K</div><div class="lbl">RMSE, CHIP TEMPERATURE</div></div>',
        '<div class="cell"><div class="val">74%</div><div class="lbl">POINTS WITHIN 5 K</div></div>',
        '<div class="cell"><div class="val">+0.89 K</div><div class="lbl">OVERALL BIAS</div></div>',
    ],
    back_href="research.html", back_label="Research overview",
    prev_href="research-chamber.html", prev_label="The experiments",
    next_href="research-cfd.html", next_label="Next: The CFD program",
    colophon="Model code and data in research/chamber-model on GitHub &middot; preprint below.",
    body=f"""
  <section class="doc-section">
    <h2>The model</h2>
    <p>The chamber reduces to a thermal network from chip to facility coolant: conduction through the substrate, nucleate boiling at the enhanced surface through a calibrated Rohsenow-family closure with surface constants fit per surface type, saturation conditions set by the sealed-chamber pressure coupling, and condensation on the finned tube bundle to the coolant. The gray-box philosophy is strict about which parameters are physics and which are fit: fluid properties, geometry, and energy balances are physics; the handful of empirical constants are calibrated on a subset of the data and then frozen. The map below is the whole model on one page.</p>
    {fig("r-model-map.png", 2662, 1729, "Block map of the reduced-order chamber model showing physics blocks and calibrated closures", "The model map: white-box physics, calibrated closures, and where each measured quantity enters. Calibrated surface constants land close to handbook Rohsenow values, which is the sanity check a fit parameter owes you.")}
  </section>

  <section class="doc-section">
    <h2>Validation against everything measured</h2>
    <p>The test set is every steady-state point from two chamber generations and two surface types, 261 in all, spanning 33-tube and 42-tube condensers, plain and microchannel substrates, and coolant temperatures from 20 to 50 &deg;C. Overall: RMSE 4.34 K, MAE 3.48 K, R&sup2; 0.938, bias +0.89 K, with 74% of predictions within 5 K of measurement.</p>
    {fig("r-parity.png", 1125, 1125, "Parity plot of predicted versus measured chip temperature with a 5 K band", "Predicted versus measured chip temperature. The 33-tube configurations sit tightest; the 42-tube runs carry a +2 K bias the cross-validation had already flagged.")}
    <table class="data">
      <thead><tr><th>Configuration</th><th class="mono">N</th><th class="mono">RMSE (K)</th><th class="mono">Bias (K)</th><th class="mono">R&sup2;</th><th class="mono">Within 5 K</th></tr></thead>
      <tbody>
        <tr><td>33-tube, plain</td><td class="mono">87</td><td class="mono"><span class="t-real">3.14</span></td><td class="mono">-0.99</td><td class="mono">0.964</td><td class="mono">91%</td></tr>
        <tr><td>33-tube, microchannel</td><td class="mono">36</td><td class="mono">4.82</td><td class="mono">+0.88</td><td class="mono">0.867</td><td class="mono">67%</td></tr>
        <tr><td>42-tube, plain</td><td class="mono">64</td><td class="mono">4.42</td><td class="mono">+2.00</td><td class="mono">0.900</td><td class="mono">66%</td></tr>
        <tr><td>42-tube, microchannel</td><td class="mono">74</td><td class="mono">5.17</td><td class="mono">+2.16</td><td class="mono">0.927</td><td class="mono">65%</td></tr>
      </tbody>
    </table>
    {fig("r-boiling-mve.png", 2100, 1650, "Boiling curves, measured versus model, per configuration and coolant temperature", "Measured (filled) against model (open) boiling curves per configuration and coolant temperature. The model captures the coolant-temperature family structure, which is the behavior the experiments identified as the governing coupling.")}
    {fig("r-residuals.png", 2100, 750, "Residuals versus heat flux and residual distribution", "Residuals carry no trend with heat flux, and the distribution is centered with sigma 4.25 K. Warmer-coolant points fit best; the bias flips sign as coolant warms, which points at the condensation closure as the next refinement.")}
  </section>

  <section class="doc-section">
    <h2>Honest scope</h2>
    <p>These are in-sample statistics on the validated configurations; the model's 66-tube and HFE-7000 outputs are forecasts with no data behind them yet, and are labeled that way everywhere they appear. Leave-one-coolant-out cross-validation showed the 33-tube generation generalizes better than the 42-tube, which is written into the manuscript rather than smoothed over. The full write-up, Part I of the two-paper set, is hosted here as a preprint.</p>
    <p><a class="btn btn-ghost" href="assets/docs/mustafa_chamber_model_part1_preprint.pdf">Download Part I preprint (PDF, 27 pp.)</a></p>
  </section>
""",
),

# ======================================================================
"research-cfd.html": dict(
    title="OpenFOAM CFD Program",
    desc="The OpenFOAM arm of the dissertation: a three-generation condenser manifold flow study finding distribution is governed by feed geometry, and a calibrated 2D/3D VOF phase-change framework for the boiling chamber.",
    eyebrow="Research &middot; OpenFOAM",
    h1="CFD that admits what it has not yet earned",
    lede="Two OpenFOAM campaigns support the chamber work. The first asks a design question the experiments could not isolate: how evenly do three condenser manifold generations feed their tube bundles? The second builds a volume-of-fluid phase-change framework for the chamber itself, calibrated on measured boiling curves, and presented under a strict integrity standard: no unconverged field is ever shown as a result.",
    tags=["OpenFOAM", "simpleFoam", "VOF phase change", "Lee model", "snappyHexMesh", "ParaView"],
    readout=[
        '<div class="cell real"><div class="val">CoV 10%</div><div class="lbl">42-TUBE DISTRIBUTION</div></div>',
        '<div class="cell real"><div class="val">3</div><div class="lbl">MANIFOLD GENERATIONS</div></div>',
        '<div class="cell"><div class="val">2D + 3D</div><div class="lbl">VOF PHASE-CHANGE CASES</div></div>',
        '<div class="cell"><div class="val">28</div><div class="lbl">PARALLEL CONDENSER TUBES</div></div>',
    ],
    back_href="research.html", back_label="Research overview",
    prev_href="research-model.html", prev_label="The model",
    next_href="software.html", next_label="Next: Software",
    colophon="All cases reproducible from research/chamber-model/openfoam on GitHub.",
    body=f"""
  <section class="doc-section">
    <h2>The manifold question</h2>
    <p>A submerged condenser only works if coolant actually reaches all of its tubes. Three chamber generations used three feed designs, and single-phase conjugate simulations of each, meshed from the as-built geometry, answer how evenly each distributes flow across its bundle.</p>
    {fig("r-cfd-layouts.png", 2250, 780, "Tube bundle layouts for the 33, 42, and 66 tube condenser generations", "Three generations, three feed philosophies: a single centred axial port, top-fed vertical manifolds, and a centreline plenum.")}
    <table class="data">
      <thead><tr><th>Generation</th><th class="mono">Tube ID (mm)</th><th>Inlet model</th><th class="mono">Flow CoV</th><th>Distribution</th></tr></thead>
      <tbody>
        <tr><td class="mono">33-tube</td><td class="mono">3.14</td><td>single centred port, as built</td><td class="mono">131%</td><td>bullseye: one tube carries ~8&times; the mean</td></tr>
        <tr><td class="mono">42-tube</td><td class="mono">1.39</td><td>top-fed manifolds, as built</td><td class="mono"><span class="t-real">10%</span></td><td>uniform, validated geometry</td></tr>
        <tr><td class="mono">66-tube</td><td class="mono">1.60</td><td>simplified centreline feed</td><td class="mono">57%</td><td>centred jet favors middle tubes</td></tr>
      </tbody>
    </table>
    <p>The caveat travels with the table: the three cases use different inlet fidelities, so the CoV column is not a clean apparatus comparison. The 42-tube number is the meaningful one, a faithful as-built model of the validated geometry. The 66-tube figure is inflated by its simplified centreline-jet inlet; its real lofted diffuser would distribute far better. What does transfer cleanly is the mechanism: wide bores make a tube bundle hydraulically near-invisible, so distribution is governed by the manifold feed geometry, not by tube count. That lesson shaped the next design.</p>
    {fig("r-cfd-dist42.png", 2250, 825, "Per-tube flow distribution for the 42-tube manifold", "Per-tube flow in the validated 42-tube manifold: coefficient of variation 10%, with the top-centre tubes slightly favored.")}
    {fig("r-cfd-streamlines.png", 1500, 950, "Streamlines through the 33-tube condenser colored by velocity", "Streamlines through the 33-tube generation make its 131% CoV visible: the single centred port drives a bullseye pattern the later manifolds were designed to kill.")}
  </section>

  <section class="doc-section">
    <h2>The phase-change framework</h2>
    <p>The second campaign simulates the boiling chamber itself with a volume-of-fluid phase-change solver. A 2D case calibrates the Lee-model mass-transfer coefficients against measured boiling curves on the validated 42-tube plain configuration, and reproduces both regimes that matter: stable nucleate boiling at moderate superheat and the vapor-blanket collapse near CHF. The 3D case carries the calibrated closure onto the real chamber geometry, meshed with snappyHexMesh around the actual tube bundle STL.</p>
    {fig("r-cfd-convergence.png", 1120, 672, "Convergence history of the calibrated 2D phase-change case in the nucleate regime", "The calibrated 2D case converging in the nucleate regime at 65 &deg;C wall temperature. The companion case at 85 &deg;C reproduces the CHF-side collapse.")}
    <div class="callout">
      <span class="tag-lbl">The integrity standard</span>
      <p>The framework paper is written under one rule: no unconverged or surrogate field is shown as a result. The 2D calibration and regime studies are results; the 3D production run to stationarity is stated as the remaining work, defined by what it requires rather than dressed up as done. A CFD framework you can trust is one that tells you exactly where its evidence stops.</p>
    </div>
    <p><a class="btn btn-ghost" href="assets/docs/mustafa_chamber_cfd_part2_preprint.pdf">Download Part II preprint (PDF, 25 pp.)</a></p>
  </section>
""",
),

# ======================================================================
"software.html": dict(
    title="Software and Tools",
    desc="Software engineering beyond simulation: a production three-role daycare platform on React Native and Supabase, parametric OpenSCAD modeling, and the Python tooling behind this site.",
    eyebrow="Software &middot; Full-stack, CAD, and tooling",
    h1="The software habit that makes the research move",
    lede="Simulation work rides on software craft, and the craft gets exercised outside the lab too. The anchor here is LittleJourney, a production-grade three-role daycare platform I built end to end, alongside parametric CAD in OpenSCAD and the Python tooling that generates and themes this site.",
    tags=["React Native", "Supabase", "Stripe", "TypeScript", "OpenSCAD", "Python"],
    readout=[
        '<div class="cell real"><div class="val">24</div><div class="lbl">APP SCREENS, 3 ROLES</div></div>',
        '<div class="cell real"><div class="val">10</div><div class="lbl">SUPABASE EDGE FUNCTIONS</div></div>',
        '<div class="cell"><div class="val">100</div><div class="lbl">UNIT TESTS</div></div>',
        '<div class="cell"><div class="val">19.5k</div><div class="lbl">LINES TS + SQL</div></div>',
    ],
    back_href="index.html", back_label="Home",
    prev_href="research-cfd.html", prev_label="The CFD program",
    next_href="index.html", next_label="All sections",
    colophon="LittleJourney is presented as a case study; its source is private.",
    body=f"""
  <section class="doc-section">
    <h2>LittleJourney: a daycare platform, end to end</h2>
    <p>LittleJourney keeps parents connected to their child's day: a realtime timeline of meals, naps, activities and photos, end-of-day narrative reports, encrypted messaging with caregivers, and tuition invoicing paid through Stripe. Caregivers log activities and attendance from the same app; admins manage enrollment, staff, and subscription tiers. Three roles, one codebase: Expo 54 and React 19 on TypeScript 5.9, backed by Supabase for Postgres, auth, realtime, and storage.</p>
    {fig("sw-lj-architecture.png", 1470, 660, "Architecture diagram: React Native app, Supabase with row-level security, edge functions, and external services", "The architecture. Every table carries row-level security, and the ten edge functions re-verify role claims server-side before anything touches Stripe or user data.")}
    <p>The parts I am proudest of are the unglamorous ones. Authorization is enforced twice, once by Postgres row-level security on every table and again inside the edge functions, so a compromised client still cannot reach another family's data; the most recent work was precisely an authorization-hardening pass across those functions. Payments run through dedicated functions for checkout, invoices, saved payment methods, and the Stripe webhook, and two functions exist purely for user rights: full data export and account deletion. A hundred unit tests and CI keep the 19.5 thousand lines of TypeScript and SQL honest.</p>
    <p>The source is private, as the product carries live billing; this page and the architecture above are the case study.</p>
  </section>

  <section class="doc-section">
    <h2>Parametric CAD in OpenSCAD</h2>
    <p>For geometry that wants to be code, I model in OpenSCAD: fully parametric constructive solid geometry where every dimension is a named variable and an assembly is a function call. The piece below is an ABB IRB 760 palletizing robot modeled joint by joint, base, swing, parallel-linkage arm, and wrist, posable by setting joint angles. The same habit shows up in the research: the boiling chamber's CFD geometry lives as scripted, versioned CAD in the repository alongside the solver cases.</p>
    {fig("sw-abb-openscad.png", 1600, 1300, "OpenSCAD parametric model of an ABB IRB 760 palletizing robot in isometric view", "The IRB 760 assembly, posed in code. Parametric CAD means the model is a program: change a link length or a joint angle and the assembly follows.")}
  </section>

  <section class="doc-section">
    <h2>Tooling that built what you are reading</h2>
    <p>This site is itself a small software project, and its tooling lives in the repository. A hue-preserving dark-theme converter re-themes light matplotlib figures onto the site palette without touching a data pixel, which is how a decade's worth of research plots share one visual language here. A page generator renders these research and software pages from content modules through a single shared shell, so the design stays byte-consistent everywhere. And the publication-analysis scripts that produced the model-validation statistics ship in the research package, so every number on these pages traces to a script you can run.</p>
    <p><a class="link-arrow" href="https://github.com/nem6557-cmyk/nem-portfolio/tree/main/tools" target="_blank" rel="noopener">Browse the tooling on GitHub <span>&rarr;</span></a></p>
  </section>
""",
),
}
