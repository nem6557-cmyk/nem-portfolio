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
      <li><strong>Mustafa, N. E., Abou Assali, M., Tawil, K., and Kandlikar, S. G.</strong> (2026). Photographic Insights into Bubble Dynamics and Two-Phase Flow Field in a Taper Microgap in a Boiling Chamber. <em>Thermal Science and Engineering Progress</em>, 73.</li>
      <li><strong>Shukla, M. Y., Mustafa, N. E., and Kandlikar, S. G.</strong> (2025). Performance of a Novel 1.5U Boiling Chamber With Higher Coolant Temperatures for High Heat Flux Dissipation in Data Center Applications. <em>Proc. 24th IEEE ITherm</em>.</li>
      <li><strong>Mustafa, N.</strong> (2024). Impact of Coolant Temperature on Boiling Chamber Performance for Cooling Electronic Chips. M.S. thesis, Rochester Institute of Technology.</li>
    </ul>
    <p>I also presented the boiling chamber thermal-network work first-author at IEEE ITherm 2026 in Orlando. Two manuscripts from the modeling program are hosted here as preprints, downloadable on their pages: Part I, the validated reduced-order model, and Part II, the CFD framework. Additional manuscripts are in review.</p>
  </section>

  <section class="doc-section">
    <h2>A second thread: bioheat for cardiac ablation</h2>
    <p>Alongside the chamber program, I collaborate with Dr. Cristian Linte on NSF-funded transient bioheat transfer modeling for cardiac radiofrequency ablation: tissue-scale thermal models validated against thermocouple measurements at millimeter depths, with the agreement quantified the way medical work demands, down to Bland-Altman limits.</p>
    <p><a class="link-arrow" href="research-bioheat.html">The bioheat validation <span>&rarr;</span></a></p>
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
  </section>

  <section class="doc-section">
    <h2>What perfusion does to the field</h2>
    <p>Perfusion is the clinical wildcard. Flowing blood carries heat out of the treatment zone as a distributed sink, so the same delivered power produces a smaller, cooler lesion near vessels than in still tissue, which is exactly where ablation either succeeds or leaves surviving tissue behind. The analytical arm isolates that effect across probe temperatures: the perfused response curves sit systematically below their non-perfused counterparts, and the gap widens with drive temperature.</p>
    {fig("rb-perfusion.png", 1200, 800, "Perfusion effect on tissue thermal response", "The perfusion effect at the lower probe temperature: perfused tissue plateaus cooler because blood flow removes heat continuously.")}
    {fig("rb-perfusion-hot.png", 1200, 800, "Perfusion effect at elevated probe temperature", "At the higher probe temperature the perfusion gap grows: more heat is delivered, so more is available for blood to carry away, and the separation between the two curves widens.")}
  </section>

  <section class="doc-section">
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
    next_href="research-bioheat.html", next_label="Next: Bioheat",
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
    {fig("rcfd-pressure-generations.png", 1440, 360, "Mid-plane kinematic pressure for the 33, 42, and 66 tube manifolds", "The same three generations in pressure. The 33-tube manifold spends its head in a single central plume; the 42-tube spreads the drop across the header; the 66-tube reflects its simplified centreline inlet. Scales are per case because the absolute levels differ by design.")}
    {fig("rcfd-axial-42.png", 1440, 460, "Axial speed slices through the 42-tube manifold at three heights", "Why the 42-tube manifold earns its 10% CoV: axial speed slices at 18%, 50%, and 82% of the bundle height stay comparable on a shared scale, so the header feeds the tubes evenly from bottom to top instead of dumping into the nearest few.")}
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
    prev_href="labs.html", prev_label="The labs",
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


def lab(title, num, story, figsrc, figw, figh, alt, cap, results, path):
    return f"""
  <section class="doc-section">
    <h2>{num} &middot; {title}</h2>
    <p>{story}</p>
    {fig(figsrc, figw, figh, alt, cap)}
    <div class="callout"><span class="tag-lbl">Verified output</span>
    <p class="mono" style="font-size:13px">{results}</p></div>
    <p><a class="link-arrow" href="https://github.com/nem6557-cmyk/nem-portfolio/tree/main/labs/{path}" target="_blank" rel="noopener">Code and run log <span>&rarr;</span></a></p>
  </section>"""


PAGES.update({

"labs.html": dict(
    title="The Labs",
    desc="Fifteen compact, fully verified builds across circuit simulation, scientific visualization, machine learning, AI evaluation methodology, and pure curiosity. Every number ran here.",
    eyebrow="Labs &middot; Fifteen builds, five disciplines",
    h1="Small builds, real numbers",
    lede="The projects pages hold the deep work; the labs hold the range. Fifteen compact builds across five disciplines, held to the same rule as everything else on this site: every number below was produced by code in this repository, on this machine, and each lab ships its run log. Where a first attempt was wrong, the fix and the lesson stayed in.",
    tags=["ngspice", "ParaView / VTK", "Machine learning", "AI evaluation", "Side quests"],
    readout=[
        '<div class="cell real"><div class="val">15</div><div class="lbl">LABS, ALL VERIFIED</div></div>',
        '<div class="cell"><div class="val">5</div><div class="lbl">DISCIPLINES</div></div>',
        '<div class="cell"><div class="val">4</div><div class="lbl">USE REAL RESEARCH DATA</div></div>',
        '<div class="cell"><div class="val">2</div><div class="lbl">KEPT-IN LESSONS</div></div>',
    ],
    back_href="index.html", back_label="Home",
    prev_href="index.html", prev_label="Home",
    next_href="labs-ngspice.html", next_label="Circuits first",
    colophon="Every lab: one script, one RESULTS.txt, one figure.",
    body="""
  <section class="doc-section">
    <h2>Five benches</h2>
    <p><strong>Circuits (ngspice).</strong> The motor thermal network from project 2 solved as a SPICE circuit and agreeing to millikelvins, a Sallen-Key filter with a 300-build Monte Carlo, and a buck converter whose first wrong measurement became the lab's lesson.</p>
    <p><a class="link-arrow" href="labs-ngspice.html">ngspice bench <span>&rarr;</span></a></p>
    <p><strong>Scientific visualization (ParaView / VTK).</strong> The dissertation's real CFD fields rendered headlessly: the 33-tube manifold's bullseye made visible, two generations compared on matched scales, and structural mode shapes treated as a vis problem.</p>
    <p><a class="link-arrow" href="labs-paraview.html">visualization bench <span>&rarr;</span></a></p>
    <p><strong>Machine learning.</strong> A Gaussian-process surrogate cross-validated on the real 261-point chamber dataset, a PINN benchmarked honestly against Crank-Nicolson, and a feature-importance study whose accidental CV pitfall became the point.</p>
    <p><a class="link-arrow" href="labs-ml.html">ML bench <span>&rarr;</span></a></p>
    <p><strong>AI evaluation.</strong> Mutation-testing the project 6 checkers, sweeping the tolerance like the classifier threshold it is, and item-response analysis of which graded fields carry signal.</p>
    <p><a class="link-arrow" href="labs-ai-eval.html">evaluation bench <span>&rarr;</span></a></p>
    <p><strong>Side quests.</strong> Prayer times derived from solar geometry and self-checked to the arcminute, a double pendulum with its chaos measured, and generative art advected through a physically honest plume field.</p>
    <p><a class="link-arrow" href="labs-fun.html">side quests <span>&rarr;</span></a></p>
  </section>
""",
),

"labs-ngspice.html": dict(
    title="ngspice Bench",
    desc="Three verified circuit-simulation labs: an electro-thermal analogy cross-checked to millikelvins, a Sallen-Key Monte Carlo yield study, and a buck converter with its measurement lesson kept in.",
    eyebrow="Labs &middot; Circuit simulation",
    h1="ngspice: three circuits, three cross-checks",
    lede="Circuit simulation with the same discipline as the research: every lab pairs the simulator against an independent reference, an analytic result, another solver, or a design equation, and reports the gap.",
    tags=["ngspice 42", "Electro-thermal analogy", "Monte Carlo", "Power electronics"],
    readout=[
        '<div class="cell real"><div class="val">4.5 mK</div><div class="lbl">SPICE VS RK4, MAX GAP</div></div>',
        '<div class="cell real"><div class="val">0.000%</div><div class="lbl">RATING VS CLOSED FORM</div></div>',
        '<div class="cell"><div class="val">99.3%</div><div class="lbl">MC YIELD, 300 BUILDS</div></div>',
        '<div class="cell"><div class="val">1%</div><div class="lbl">RIPPLE VS PREDICTION GAP</div></div>',
    ],
    back_href="labs.html", back_label="All labs",
    prev_href="labs.html", prev_label="All labs",
    next_href="labs-paraview.html", next_label="Next: Visualization",
    colophon="ngspice 42 in batch mode; every figure regenerable from labs/ngspice.",
    body=(
lab("The motor's thermal circuit", "NG-1",
    "The electro-thermal analogy makes project 2's two-node motor network a two-RC circuit: temperature is voltage, heat flow is current, ngspice is the thermal solver. Two cross-checks anchor it. On a 300-second open-loop transient, SPICE and the project's RK4 integrator agree to 4.5 millikelvin on the winding and 0.05 on the case. And a DC sweep of dissipated power recovers the continuous torque rating at 2.765 N m, matching the closed-form value to the last digit.",
    "ng1-transient.png", 1110, 630,
    "Winding and case temperatures from ngspice overlaid on the Python RK4 solution",
    "Two solvers, one network. The dashed SPICE traces sit on the RK4 curves; the derating threshold from project 2 is marked.",
    "transient max |SPICE - RK4|: winding 4.53 mK, case 0.05 mK; continuous rating 2.765 N m from the DC sweep vs 2.765 closed form (0.000%)",
    "ngspice/01-electrothermal") +
lab("A filter and its factory yield", "NG-2",
    "A unity-gain Sallen-Key Butterworth low-pass designed for 1 kHz: the nominal AC sweep lands the cutoff at 1000.3 Hz against a 1000.4 Hz design value with a clean minus 40 dB per decade rolloff. Then the engineering question: with 5% resistors and 10% capacitors, 300 Monte Carlo builds put 99.3% of units inside a plus or minus 10% cutoff window, with a 35 Hz standard deviation.",
    "ng2-sallenkey.png", 1530, 600,
    "Bode magnitude of the Sallen-Key filter and Monte Carlo histogram of cutoff frequencies",
    "Left: the nominal response with cutoff and slope annotated. Right: where 300 toleranced builds actually land.",
    "nominal fc 1000.3 Hz (design 1000.4), rolloff -40.0 dB/dec, MC yield 99.3% inside +/-10%, sigma 35 Hz",
    "ngspice/02-sallen-key") +
lab("The buck converter that taught a lesson", "NG-3",
    "A 12-to-5 V buck at 100 kHz. The first run of this lab reported 110 mV of 'ripple' that disagreed with the small-ripple analysis by 30 times, and the waveform showed why: the output LC is underdamped and its startup transient rings for about 12 milliseconds, four times longer than the original measurement window. The corrected lab runs 25 ms, adds realistic capacitor ESR, and lands: inductor ripple within 1% of the volt-second prediction, output ripple 9.2 mVpp against a 13.1 mVpp in-phase upper bound whose quadrature estimate sits at 10. The wrong first cut stays documented in the script.",
    "ng3-buck.png", 1530, 600,
    "Buck converter startup showing the underdamped ring-down and the steady-state ripple zoom",
    "Left: the ring-down that fooled the first measurement. Right: the actual switching ripple, measured after the transient has died.",
    "settled mean 4.641 V (async diode drop), ripple 9.17 mVpp vs 13.12 two-term bound, inductor ripple 0.306 A vs 0.309 predicted",
    "ngspice/03-buck")),
),

"labs-paraview.html": dict(
    title="Visualization Bench",
    desc="Three scientific-visualization labs on real data through the VTK pipeline: the 33-tube manifold bullseye, a two-generation comparison on matched scales, and structural mode shapes.",
    eyebrow="Labs &middot; ParaView / VTK",
    h1="Visualization: making the numbers visible",
    lede="The dissertation's CoV numbers live in tables; these labs make them visible. All three render headlessly through the VTK pipeline that ParaView is built on, from the actual converged solver fields, and each ships a pvpython twin where it applies. A figure here is a claim, so the data is real or the lab does not ship.",
    tags=["VTK / PyVista", "pvpython", "Streamlines", "Mode shapes", "Real CFD fields"],
    readout=[
        '<div class="cell real"><div class="val">389,517</div><div class="lbl">CELLS, 33-TUBE FIELD</div></div>',
        '<div class="cell real"><div class="val">1.71M</div><div class="lbl">CELLS COMPARED IN PV-2</div></div>',
        '<div class="cell"><div class="val">0.934 s</div><div class="lbl">T1, MATCHES PROJECT 5</div></div>',
        '<div class="cell"><div class="val">3</div><div class="lbl">MODES RENDERED LIVE</div></div>',
    ],
    back_href="labs.html", back_label="All labs",
    prev_href="labs-ngspice.html", prev_label="Circuits",
    next_href="labs-ml.html", next_label="Next: Machine learning",
    colophon="Rendered headless via VTK; pvpython twins included for ParaView proper.",
    body=(
lab("Anatomy of a bad manifold", "PV-1",
    "The 33-tube condenser's flow CoV measured 131% in the research CFD, and this render shows what that number looks like: streamlines seeded from the actual inlet patch dive straight through the bundle center as a jet while the flanks sit stagnant, and the mid-plane speed slice confirms a single hot column. The 389,517-cell converged field is the real one from the dissertation package.",
    "pv1-manifold-anatomy.png", 1500, 1650,
    "Streamlines and speed slice through the 33-tube manifold showing the central jet",
    "The bullseye, visible: a single centred port overfeeds the middle tubes while the edges starve.",
    "389,517 cells; inlet-patch seeded streamlines; peak interpolated speed 4.18 m/s",
    "paraview/01-manifold-anatomy") +
lab("Two generations, matched scales", "PV-2",
    "The craft lab: 42-tube and 66-tube manifold fields, 1.71 million cells combined, rendered as mid-plane speed and pressure slices with matched cameras and matched color ranges per row, so the eye compares physics instead of colormap artifacts. The 42-tube's even feed and the 66-tube's simplified centreline jet read instantly, caveat included.",
    "pv2-generation-compare.png", 1760, 920,
    "Four-panel comparison of speed and pressure slices for the 42 and 66 tube manifolds",
    "Matched scales per row. The 66-tube panel inherits the simplified-inlet caveat from the research CFD page; the comparison is about rendering discipline as much as flow.",
    "42-tube: 769,447 cells, speed max 4.28 m/s; 66-tube: 944,081 cells, speed max 3.98 m/s; shared clim per row",
    "paraview/02-generation-compare") +
lab("Mode shapes as a vis problem", "PV-3",
    "Project 5's three-story frame rebuilt in OpenSees, eigensolved live, and its first three lateral modes rendered as warped, displacement-colored tubes over the ghosted undeformed frame. The first period lands at 0.934 seconds, identical to project 5's reported value because it is the same model solved again, and modes two and three come out at 0.260 and 0.132 seconds.",
    "pv3-structural-modes.png", 1740, 760,
    "Three warped mode shapes of the steel frame colored by displacement",
    "Classic shear-frame signatures: monotonic sway, S-reversal, double zigzag. The eigensolve runs inside the lab script.",
    "T1 = 0.934 s (matches project 5), T2 = 0.260 s, T3 = 0.132 s; unbraced frame, live eigensolve",
    "paraview/03-structural-modes")),
),

"labs-ml.html": dict(
    title="Machine Learning Bench",
    desc="Three ML labs with honest evaluation: a GP surrogate cross-validated on 261 real chamber points, a PINN benchmarked against Crank-Nicolson, and a CV-pitfall study on what drives chip temperature.",
    eyebrow="Labs &middot; Machine learning",
    h1="ML that shows its validation",
    lede="Three studies on the theme this whole site keeps returning to: a model is worth exactly its evaluation. Two of the three run on the real 261-point experimental dataset from the boiling chamber; the third pits a PINN against sixty-year-old numerics and reports who won.",
    tags=["Gaussian processes", "PINN / PyTorch", "Cross-validation", "Real research data"],
    readout=[
        '<div class="cell real"><div class="val">1.46 K</div><div class="lbl">GP CV RMSE, 261 POINTS</div></div>',
        '<div class="cell"><div class="val">92.7%</div><div class="lbl">95% INTERVAL COVERAGE</div></div>',
        '<div class="cell real"><div class="val">360&times;</div><div class="lbl">CN BEATS PINN ON ERROR</div></div>',
        '<div class="cell"><div class="val">&minus;0.10</div><div class="lbl">LEAVE-CONFIG-OUT R&sup2;</div></div>',
    ],
    back_href="labs.html", back_label="All labs",
    prev_href="labs-paraview.html", prev_label="Visualization",
    next_href="labs-ai-eval.html", next_label="Next: AI evaluation",
    colophon="Datasets: research/chamber-model (real); all metrics out-of-fold where stated.",
    body=(
lab("A surrogate with calibrated doubt", "ML-1",
    "A Gaussian process trained on the real 261-point dataset, heat flux, coolant setpoint, condenser generation, surface type, predicting chip temperature, and evaluated entirely out-of-fold: 5-fold CV RMSE of 1.46 K with R-squared 0.993. That beats the gray-box physics model's 4.34 K, and the page says why that comparison is unfair in both directions: the GP interpolates a fixed apparatus brilliantly and extrapolates nowhere, while the physics model explains and transfers. The second panel asks whether the GP's error bars mean anything: a claimed 95% interval covers 92.7% empirically, slightly overconfident and reported as such.",
    "ml1-gp-surrogate.png", 1560, 660,
    "GP parity plot with uncertainty bars and the calibration curve",
    "Out-of-fold parity with 95% bars, and the calibration curve that grades the bars themselves.",
    "5-fold CV: RMSE 1.46 K, MAE 0.87 K, R2 0.993; empirical coverage of 95% intervals: 92.7%",
    "ml/01-gp-surrogate") +
lab("The PINN loses, and that is the result", "ML-2",
    "One-dimensional transient conduction with the effective diffusivity tuned in the cardiac bioheat validation, solved three ways: exact Fourier series, Crank-Nicolson, and a physics-informed neural network trained on the PDE residual with hard-encoded boundary conditions. The verdict is unambiguous: CN reaches 2.4e-5 max error in 0.1 seconds; the PINN reaches 8.6e-3 after 77 seconds of training. For a clean forward problem on a rectangle, classical numerics wins by more than two orders of magnitude, and the lab says so, because PINNs earn their keep on inverse problems and irregular domains, not here.",
    "ml2-pinn.png", 1560, 630,
    "Temperature profiles from exact, PINN, and Crank-Nicolson solvers with an error comparison",
    "All three solvers overlaid at three snapshots, and the error bars that settle the contest.",
    "PINN worst max-error 8.6e-3 (77 s train, CPU); Crank-Nicolson 2.4e-5 (0.1 s); alpha = 1.447e-7 m2/s from the bioheat validation",
    "ml/02-pinn-conduction") +
lab("What drives the chamber, and a CV trap", "ML-3",
    "A random forest on the same 261 points, interrogated with permutation importance and partial dependence: heat flux dominates, coolant setpoint second, condenser generation third, surface type fourth, exactly the physics ordering. The kept-in lesson: the first run used unshuffled folds on a configuration-ordered CSV and scored R-squared of zero. The final lab reports both numbers on purpose: shuffled CV 0.930 for interpolation, leave-one-configuration-out negative 0.10 for extrapolation. Interpolation is easy; a new configuration is not, which is precisely why the physics model exists.",
    "ml3-drivers.png", 1890, 600,
    "Permutation importance and partial dependence plots for the chamber dataset",
    "The forest agrees with the physics on ordering, and the two CV numbers frame what data-driven models can and cannot do here.",
    "shuffled 5-fold R2 0.930 +/- 0.013; leave-config-out R2 -0.10 +/- 0.45; importance: q'' 1.15, coolant 0.55, generation 0.39, surface 0.17",
    "ml/03-what-drives-the-chamber")),
),

"labs-ai-eval.html": dict(
    title="AI Evaluation Bench",
    desc="Three evaluation-methodology labs: mutation-testing the project 6 checkers to 100% sensitivity, sweeping tolerance as a classifier threshold, and item-response analysis of graded fields.",
    eyebrow="Labs &middot; AI evaluation",
    h1="Evaluating the evaluators",
    lede="Project 6 built machine-gradable tasks; these labs turn the instruments on themselves. The discipline is measurement: a checker has a sensitivity and a specificity, a tolerance is a threshold with error rates on both sides, and a graded field carries a measurable amount of information about ability.",
    tags=["Mutation testing", "ROC thinking", "Item response", "Grader QA"],
    readout=[
        '<div class="cell real"><div class="val">79/79</div><div class="lbl">MUTANTS CAUGHT</div></div>',
        '<div class="cell real"><div class="val">97.5%</div><div class="lbl">BENIGN VARIANTS PASSED</div></div>',
        '<div class="cell"><div class="val">0.5&ndash;2%</div><div class="lbl">TOLERANCE OPERATING BAND</div></div>',
        '<div class="cell"><div class="val">0.61</div><div class="lbl">TOP FIELD DISCRIMINATION</div></div>',
    ],
    back_href="labs.html", back_label="All labs",
    prev_href="labs-ml.html", prev_label="Machine learning",
    next_href="labs-fun.html", next_label="Next: Side quests",
    colophon="Targets: the project 6 task pack; populations synthetic where stated.",
    body=(
lab("Who checks the checkers", "AE-1",
    "Mutation testing, applied to graders. Each golden answer from the three project 6 tasks gets attacked with a battery of mutants: just-outside-tolerance scaling, unit slips both directions, sign flips, type corruption, missing fields, boolean flips, 79 mutants in all, plus 120 benign variants jittered well inside tolerance that a fair checker must pass. The checkers caught all 79 mutants and passed 97.5% of the benign population. The detection matrix shows the coverage by mutation class, and by construction the only survivors would be errors inside the tolerance band, which is what the next lab is about.",
    "ae1-mutation.png", 1290, 510,
    "Heatmap of mutation detection rates by task and mutation class",
    "Every cell at 100%: each mutation class, caught on every task. Sensitivity means nothing without the benign pass rate beside it.",
    "79/79 mutants caught (sensitivity 100%); 117/120 benign in-tolerance variants passed (specificity 97.5%)",
    "ai-eval/01-mutation-testing") +
lab("The tolerance is a threshold", "AE-2",
    "A numeric tolerance is a classifier decision boundary, so it deserves a threshold sweep. Two synthetic populations face T1's governing field: legitimate solutions with 0.3% numerical scatter, and wrong-method answers built from the checker's own documented traps, phi omitted entirely at plus 11.1%, the compression-controlled phi of 0.65 at minus 27.8%, plus smaller illustrative slips. Sweeping tolerance from 0.05% to 15% traces false-fail against false-pass: the pack's chosen 1% sits inside the 0.5-to-2% operating band, failing 0.05% of honest work and passing zero wrong methods.",
    "ae2-tolerance.png", 1140, 660,
    "False-fail and false-pass rates versus tolerance width with the 1% choice marked",
    "Below the band, noise fails honest solutions; above it, small method slips start passing. The choice was a measurement, not a habit.",
    "at 1% tolerance: false-fail 0.05% of 4000 legit draws, false-pass 0/4 wrong methods; smallest 2% slip first passes at 2.0%",
    "ai-eval/02-tolerance-tradeoff") +
lab("Which fields carry signal", "AE-3",
    "Classical test theory on the pack's scoring structure. A simulated population of 600 solvers with Beta-distributed ability attempts each task as a chain of steps where errors propagate downstream, mirroring how a_mm being wrong drags eps_t and phiMn with it. Per field, the lab computes difficulty and point-biserial discrimination. The structural finding: chain heads are hard and informative, terminal fields are hardest but partially redundant because they inherit upstream failures, and the sharpest single item is T3's drift field at r = 0.61. Labeled a simulation under a stated error model, because it is one.",
    "ae3-discrimination.png", 1260, 750,
    "Difficulty versus discrimination scatter for all fifteen graded fields",
    "Fifteen fields, three tasks, one map of where the pack's information actually lives.",
    "N=600 simulated solvers; difficulty 0.13 to 0.38; top discrimination T3:drift r_pb = 0.61; propagation makes terminal fields partially redundant",
    "ai-eval/03-item-discrimination")),
),

"labs-fun.html": dict(
    title="Side Quests",
    desc="Three curiosity builds held to the same standard: prayer times from solar geometry self-checked to the arcminute, a double pendulum with measured chaos, and generative art from a physically honest plume field.",
    eyebrow="Labs &middot; Side quests",
    h1="Curiosity, same standards",
    lede="No client, no deadline, no citation, and the same rule anyway: every number verified, every claim checked. Three builds that exist because the questions would not leave me alone.",
    tags=["Solar geometry", "Chaos", "Generative art", "NumPy"],
    readout=[
        '<div class="cell real"><div class="val">&minus;0.833&deg;</div><div class="lbl">MAGHRIB ALTITUDE CHECK</div></div>',
        '<div class="cell real"><div class="val">1.20 /s</div><div class="lbl">LYAPUNOV EXPONENT</div></div>',
        '<div class="cell"><div class="val">1.75e-7</div><div class="lbl">ENERGY DRIFT, 40 s RK4</div></div>',
        '<div class="cell"><div class="val">30k</div><div class="lbl">PARTICLES PER PIECE</div></div>',
    ],
    back_href="labs.html", back_label="All labs",
    prev_href="labs-ai-eval.html", prev_label="AI evaluation",
    next_href="software.html", next_label="Next: Software",
    colophon="labs/fun in the repository; every figure regenerable.",
    body=(
lab("Salah times from the sky", "FUN-1",
    "Prayer times are astronomy: Dhuhr is solar transit, Asr is a shadow ratio, Maghrib is sunset, Fajr and Isha are solar depression angles. This lab computes all five for Rochester from NOAA's solar position equations under the ISNA convention, and self-validates two ways: computed Dhuhr equals the equation-of-time solar noon identically, and an independent altitude evaluation at the computed Maghrib returns exactly the minus 0.833 degree refraction-corrected horizon. For July 2, 2026 it gives Maghrib at 20:54, which matches the published Rochester sunset to the minute. The year chart shows the seasons breathing, daylight-saving steps included.",
    "f1-salah.png", 1380, 750,
    "All five prayer times across the year 2026 for Rochester with dawn and dusk bands shaded",
    "A year of Rochester's sky under the ISNA 15/15 convention. The vertical steps are daylight saving, not astronomy.",
    "Jul 2 2026: fajr 03:47, sunrise 05:35, dhuhr 13:14, asr 17:19, maghrib 20:54, isha 22:41; both self-checks exact",
    "fun/01-salah-solar") +
lab("Chaos, measured", "FUN-2",
    "The double pendulum everyone has seen, plus the numbers most demos skip. A Benettin twin-trajectory measurement over 80 renormalizations puts the largest Lyapunov exponent at 1.20 per second, a 0.58 second doubling time for any uncertainty, which is why two starts one nanoradian apart disagree completely within eleven seconds. A vectorized RK4 sweep of 14,641 initial conditions maps time-to-first-flip across the angle plane, and the integrator earns trust the boring way: measured relative energy drift of 1.75e-7 over the 40 second reference run.",
    "f2-pendulum.png", 1710, 690,
    "Twin-trajectory divergence with exponential fit and the fractal flip-time map",
    "Left: one nanoradian becoming everything. Right: which initial angles somersault, and how soon; the interleaved structure is the chaos.",
    "lambda = 1.20 /s (doubling 0.58 s); 76% of the 121x121 grid flips within 25 s; energy drift 1.75e-7 relative",
    "fun/02-double-pendulum") +
lab("Plume art", "FUN-3",
    "Generative art with a defensible velocity field: three buoyant plumes, Gaussian updraft cores with entrainment inflow at their flanks, superposed with a divergence-free curl-noise background. Thirty thousand particles advect through it for 340 steps, their trails accumulating on the canvas and colored from deep teal in the cold far field to orange in the rising cores. Two seeds, two pieces. It is art, but the field would pass a code review, which felt like the only acceptable way for this site to make art.",
    "f3-plume-art.png", 1920, 770,
    "Two generative art pieces of particle trails through thermal plume fields",
    "rise i and rise ii: same code, different seeds. The physics is decorative and correct.",
    "30,000 particles, 340 advection steps, three plumes + curl noise; seeds 12 and 47",
    "fun/03-plume-art")),
),

"research-bioheat.html": dict(
    title="Bioheat Modeling for Cardiac Ablation",
    desc="Transient bioheat transfer modeling for cardiac radiofrequency ablation with sub-0.12 C RMSE validation against thermocouple measurements, including Bland-Altman agreement analysis.",
    eyebrow="Research &middot; Bioheat, with Dr. Cristian Linte",
    h1="Tissue-scale heat, validated to a tenth of a degree",
    lede="The second research thread: NSF-funded transient bioheat modeling for cardiac radiofrequency ablation, in collaboration with Dr. Cristian Linte. Radiofrequency ablation treats arrhythmia by heating tissue through a catheter tip, and the safety question is thermal: what does the temperature field do at depth, over time, with and without blood perfusion carrying heat away. The models here answer with tuned effective properties and validation at the standard medical bar.",
    tags=["Bioheat transfer", "Cardiac RF ablation", "Perfusion", "Bland-Altman", "NSF collaboration"],
    readout=[
        '<div class="cell real"><div class="val">0.117 &deg;C</div><div class="lbl">RMSE AT 3 mm DEPTH</div></div>',
        '<div class="cell real"><div class="val">R&sup2; 0.972</div><div class="lbl">TM1, 324 K NON-PERFUSED</div></div>',
        '<div class="cell"><div class="val">7.2%</div><div class="lbl">MAPE VS 15% CRITERION</div></div>',
        '<div class="cell"><div class="val">4</div><div class="lbl">VALIDATION CASES, ALL PASS</div></div>',
    ],
    back_href="research.html", back_label="Research overview",
    prev_href="research-cfd.html", prev_label="The CFD program",
    next_href="software.html", next_label="Next: Software",
    colophon="Bioheat collaboration with Dr. C. Linte, RIT &middot; manuscript in review.",
    body=f"""
  <section class="doc-section">
    <h2>Two arms, one question</h2>
    <p>The analytical arm fits empirical thermal-response models to measured tissue heating across probe temperatures, extracting effective properties and quantifying how perfusion reshapes the field: flowing blood is a distributed heat sink, and the difference between perfused and non-perfused tissue is the difference between a lesion that stays put and one that grows. The numerical arm solves the transient bioheat equation with those effective properties and faces thermocouple measurements at two depths, 3 and 7 millimeters, across four cases: probe temperatures of 324 K and 362 K, each with and without perfusion.</p>
    {fig("rb-analytical.png", 1500, 900, "Global fit of the empirical thermal response models across cases", "The analytical arm's global fit across probe temperatures. Effective properties come out of this stage and feed the numerical model.")}
  </section>

  <section class="doc-section">
    <h2>Validation at the medical bar</h2>
    <p>For the 324 K non-perfused case, the tuned model, effective conductivity 0.55 W/m-K, specific heat 3800 J/kg-K, interface coefficient 3800 W/m&sup2;-K, tracks the 3 mm thermocouple with an RMSE of 0.117 &deg;C and R&sup2; of 0.972, and the 7 mm probe at 0.114 &deg;C. Agreement is quantified the way medical instrumentation demands: mean absolute percentage error against explicit pass criteria, 7.2% at TM1 against a 15% bar and 9.2% at TM2 against 20%, plus Bland-Altman bias and limits of agreement, with biases of hundredths of a degree. All four cases pass their criteria.</p>
    {fig("rb-validation.png", 1500, 850, "Numerical model temperature histories overlaid on thermocouple measurements", "Model against thermocouples at both depths for the 324 K non-perfused case. The disagreement lives in the second decimal place.")}
    {fig("rb-validation-perf.png", 1500, 850, "Perfused-case model and thermocouple temperature histories", "The perfused counterpart at the same probe temperature. Blood flow bleeds heat out of the tissue, so the whole field sits cooler and the steady plateau arrives lower; the model tracks that shift too.")}
  </section>

  <section class="doc-section">
    <h2>What perfusion does to the field</h2>
    <p>Perfusion is the clinical wildcard. Flowing blood carries heat out of the treatment zone as a distributed sink, so the same delivered power produces a smaller, cooler lesion near vessels than in still tissue, which is exactly where ablation either succeeds or leaves surviving tissue behind. The analytical arm isolates that effect across probe temperatures: the perfused response curves sit systematically below their non-perfused counterparts, and the gap widens with drive temperature.</p>
    {fig("rb-perfusion.png", 1200, 800, "Perfusion effect on tissue thermal response", "The perfusion effect at the lower probe temperature: perfused tissue plateaus cooler because blood flow removes heat continuously.")}
    {fig("rb-perfusion-hot.png", 1200, 800, "Perfusion effect at elevated probe temperature", "At the higher probe temperature the perfusion gap grows: more heat is delivered, so more is available for blood to carry away, and the separation between the two curves widens.")}
  </section>

  <section class="doc-section">
    <div class="callout">
      <span class="tag-lbl">Honest scope</span>
      <p>These are effective-property models tuned per protocol and validated against benchtop thermocouple data; they are decision-support physics, not patient-specific prediction. The tuned parameters are reported with the fits so the calibration is inspectable rather than buried.</p>
    </div>
  </section>
""",
),
})
