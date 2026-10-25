# Matching and optimization workflow

## 1. Establish a trustworthy baseline

Verify radio/antenna compatibility, source geometry, stackup, reference plane and port first. Put the π network in its baseline state: series 0 Ω or an explicit connected bridge, shunts DNP with pads present. Save initial complex S11 and `Zin = 50*(1+S11)/(1-S11)`. A real-valued 50 Ω input is the Smith-chart center; an S11 notch alone does not prove efficient radiation.

Simulate the complete intended installed environment. The host ground, cable shield, mounting posts, battery and enclosure can participate in the antenna current. For the source's roughly 120 × 65 mm carrier, do not assume the ground is electrically negligible around 900 MHz.

## 2. Tune the radiator before adding matching reactance

Sweep a physically meaningful length or gap across a safe range. A longer monopole generally lowers resonance; use `L_new ≈ L_old*f_res/f_target` only as a small-change first estimate. Strong coupling, meanders, IFA shorts and ground discontinuities can break that simple relationship.

Parameterize the shortest sensible set: radiator end length, feed/short gap or location, and perhaps one matching value. Preserve actual manufacturing clearances. For imported geometry, replacing only the tunable antenna section with native HFSS geometry is often more reliable than trying to stretch a faceted imported solid.

The supplied Optimetrics setup uses **Quasi Newton** and the native `InsertSetup("OptiOptimization", ...)` interface. Official parameter definitions are in [Ansys optimization scripting](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v252/en/Subsystems/HFSS/Subsystems/HFSS%20Scripting/Content/InsertSetupOptimization.htm). It evaluates `dB(S(LoRa_Port,LoRa_Port)) <= -10` over each configured range using the interpolating sweep. The default goal is 902–928 MHz. For both bands, configure `[[863,870],[902,928]]`. For only the two center frequencies, configure `[[868,868],[915,915]]`, recognizing this gives no passband guarantee.

Review the generated setup in **Optimetrics > LoRa_MatchOptimization > Properties**. Confirm the solution points to `LoRa_Setup915 : LoRa_Sweep800_1000`, goals have `<=` with `−10`, and Variables includes dimensions that visibly affect the model. Native range specifications use `rd` for range/discrete selection. Use a small coarse parametric study before a local optimizer so it starts near a viable basin. An Optimetrics goal is a request to the solver, not proof it was reached.

## 3. Synthesize and realize the π network

At the chosen reference plane, inspect complex impedance at the intended center and edges. The sign of reactance and resistance relative to 50 Ω determines which network topology is useful. Do not select capacitor/inductor values from an S11 dB-only plot.

Two valid approaches:

- **HFSS ideal elements:** create actual component-gap sheets and assign parameterized lumped RLC values. Add those existing local variables to `optimization_variables` with explicit units (`pF`, `nH`, `ohm`). The geometry includes pads/vias; the ideal elements represent only component impedance. A DNP shunt is an open circuit, so omit/disable its element. Do not approximate DNP with a zero-ohm shunt. Use separate model variants for capacitor-vs-inductor topology rather than forcing a component through zero with an unphysical bound.
- **EM/circuit co-simulation:** export an EM multiport model with reference planes at the appropriate RF nodes, then connect RF vendor component models in AEDT Circuit. Internal component ports plus the external reference plane must form a consistent multiport; a one-port antenna-only file cannot represent arbitrary distributed coupling between all matching pads. Deembed only if the same pad/reference structure is not also included in the component model. Optimize standard component candidates and recheck the assembled EM/circuit solution.

Include finite Q, ESR, self-resonance and ground-via inductance. Once a continuous ideal solution is found, enumerate neighboring available component values using the chosen supplier/model. Re-run with realistic tolerance corners. A resistive network can produce attractive S11 by dissipating power; track realized gain and radiation/total efficiency alongside match.

## 4. Final numerical verification

1. Re-solve the winning physical variation as a clean nominal design. Inspect final geometry and exported manufacturing dimensions. Check the optimizer's final values rather than assuming its last iterate was best.
2. Right-click **Analysis > setup > Add Frequency Sweep**, choose **Discrete**, and solve the specified band(s) on a dense grid. Start with 0.25 MHz spacing near edges/notches and make it finer if narrow features appear. Include exact edges and centers. Compare with the interpolating result; 1 MHz output spacing is not the same as 1 MHz independent solves.
3. Confirm adaptive convergence at 915 MHz and use independent adaptive setups at 868 MHz / relevant extremes. Tighten ΔS from 0.01 to 0.005 and refine critical local mesh. Suggested project acceptance checks are resonance shift <1 MHz and gain change <0.2 dB; choose tighter tolerances if required by the product. Near a very deep notch compare complex S11 rather than unstable dB differences.
4. Increase air padding by 25–50% and compare. If the result changes materially, fix the boundary/mesh configuration before tuning further. For the wide sweep, use the 800 MHz reference padding to retain at least λ0/4 at all frequencies and variations.
5. Evaluate Dk, substrate thickness, etch width, antenna gap, solder mask, component tolerance, enclosure/hand/cable placement and assembly corners using fabrication data. Design nominal margin, e.g. a −12 to −15 dB target where feasible, so −10 dB is not met only at the nominal point. Margin is not a guarantee of tolerance yield.
6. Save real/imag S11 CSV for the final discrete solution. The offline checker reports the worst **exported sample** per band; it requires edges and limits maximum sample gaps. Use `--max-gap-mhz 0.251` for a 0.25 MHz validation grid. It does not prove the continuous-frequency maximum between samples.

## 5. VNA correlation

Use a calibrated VNA at the same 50 Ω reference plane, with the radio disconnected/unpowered as appropriate to the fixture. Calibrate/deembed the actual cable and launch, stabilize cable routing, and measure the fully assembled antenna environment. A coax shield attached to a small PCB can alter the ground current; document and control that arrangement. Measure S11, then correlate efficiency/gain using an appropriate radiation measurement. If measurement disagrees, inspect stackup, connector/reference plane, antenna dimensions and nearby metal before fitting extra matching elements.

## Troubleshooting map

| Symptom | First checks |
|---|---|
| No meaningful radiator in model | Antenna may attach to RA-02 I-PEX; add actual antenna/connector/cable |
| Excellent S11, poor range/gain | Lossy dielectric/components, resistive match, ground/cable current, efficiency |
| Optimizer changes variable but trace is identical | Variable unbound to geometry/element; cached/incorrect solution context |
| Oscillatory or implausibly sharp S11 | Port contact, tiny sliver/short, sweep interpolation, insufficient adaptation |
| Current ends at pad or via | Missing contact/barrel, incorrect Z, unbridged series gap |
| Gain changes with airbox | Radiation boundary too close, insufficient mesh, wrong outer-face assignment |
| Animation is static | Complex magnitude selected, missing saved fields, wrong frequency/variation |
| 868 MHz match is poor while 915 MHz is good | Single-band radiator; goal omitted 868; insufficient bandwidth; wrong mesh context |
