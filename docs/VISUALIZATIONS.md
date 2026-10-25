# Polished HFSS visualizations

Menu paths below follow the classic HFSS 3D interface documented around AEDT 2024 R2–2025 R2. Ribbon labels can differ by release; project-tree context menus are the most consistent route. Always label the **frequency, variation, quantity and normalization**. Export from genuine solved results.

## S11 magnitude plot

1. Right-click **Results > Create Modal Solution Data Report > Rectangular Plot** (also **HFSS > Results > Create Modal Solution Data Report > Rectangular Plot**).
2. Select solution `LoRa_Setup915 : LoRa_Sweep800_1000`. On **Trace**, use Primary Sweep `Freq`, Category `S Parameter`, Quantity `S(LoRa_Port,LoRa_Port)`, Function `dB`. Restrict **Families** to the intended nominal/best variation. Click **New Report**.
3. Double-click an axis to edit its scale: X 800–1000 MHz, major spacing 25 or 50 MHz; Y approximately −40 to 0 dB, adjusted so no genuine minimum is hidden. Use white background, restrained light grid, a 2–3 px dark teal trace, and legible 11–14 pt labels.
4. Add a horizontal −10 dB limit line using the report's limit-line context command if available, or add a constant `−10` expression as another trace. Add markers at 868 and 915 MHz and at the relevant edges; show marker values. A negative S11 dB trace is distinct from positive return loss.
5. Right-click the report in **Results > Export > To File** (in some builds **Export > Data**) for CSV. For portable plotting, export **re(S11)** and **im(S11)** against frequency. The script creates `LoRa_S11_RI` for this purpose. Use the real/imag report's **Export > To File** for CSV if exporting manually.
6. Run `python scripts/postprocess_s11.py build/s11_ri.csv --bands 902:928`. This writes `build/plots/s11_smith_50ohm.png` at 300 dpi and a vector SVG. The offline figure includes a −10 dB line, passband shading, exact center-frequency markers when present, and a Smith grid.

For final evidence repeat using the final **discrete** sweep export, and state that context in the figure caption. Keep identical axes when comparing variants; do not smooth away mismatch peaks.

## Smith chart centered on 50 Ω

1. Confirm the port is referenced/renormalized to **50 Ω**; a chart center is only 50 Ω when the associated reference is 50 Ω.
2. Right-click **Results > Create Modal Solution Data Report > Smith Chart**. Select the same solution and nominal variation as above. Choose `S(LoRa_Port,LoRa_Port)` and **Function = None**. Do not plot `dB(S11)` on a Smith chart. The standard path is documented in [Ansys Creating Smith Charts](https://ansyshelp.ansys.com/public/views/secured/electronics/v261/en/subsystems/HFSS/Content/ReportsandPostProc/CreatingSmithCharts.htm).
3. Show the impedance grid, full 800–1000 MHz trace and markers at 868/915 MHz. Label the center `50 + j0 Ω`. Grid values are normalized: `r=1` corresponds to 50 Ω and `x=1` to +j50 Ω.
4. Report actual `Zin = 50*(1+Γ)/(1−Γ)` at the markers. A marker on the real axis away from center is resonant but mismatched. Keep the chart circular and use a thin grid with a stronger trace.

## 3D realized-gain pattern overlaid on the PCB

1. Confirm an open boundary and solved radiation fields exist. The package supplies separate saved-field solutions at 868 and 915 MHz. Use the one matching your figure; an interpolated S sweep is not sufficient field data.
2. Right-click **Radiation > Insert Far Field Setup > Infinite Sphere**. Use Theta 0–180°, Phi −180–180°, 2° steps, Global coordinates; the script already creates `LoRa_InfiniteSphere`.
3. Right-click **Results > Create Far Fields Report > 3D Polar Plot**. Select `LoRa_Setup915 : LoRa_Fields915`, Geometry/Context `LoRa_InfiniteSphere`, Freq `915MHz`, and the correct variation. Use **Phi as the primary sweep and Theta as secondary**, both All. Choose `RealizedGainTotal`, Function `dB`. Click **New Report**. Repeat for 868 MHz with `LoRa_Fields868`.
4. Return to the 3D model window. Use **HFSS > Fields > Plot Fields > Radiation Field...**, or right-click **Field Overlays > Plot Fields > Radiation Field...**. Select the existing 3D polar report, check **Visible**, and click **Apply**. Adjust **Transparency** to about 0.35–0.55 and **Scale** until the PCB is visible inside the pattern. These are visual settings, not changes to computed gain. See [Ansys 3D polar overlay instructions](https://ansyshelp.ansys.com/public/views/secured/electronics/v252/en/Subsystems/HFSS/Content/ReportsandPostProc/Overlaying3DPolarPlotsofNearorFarFieldsonModels.htm).
5. Hide the airbox visually while keeping it in the model and solution. Use a neutral PCB rendering, copper in a muted metallic color, an isometric camera with the antenna unobscured, axes visible, and a readable `Realized Gain (dBi)` legend. Keep a consistent absolute scale/legend when comparing frequency or design variants.
6. Use the model window's right-click **Copy Image** command and save from an image editor, or the release's **Export Image** command where present. Use a large viewport (e.g. 2400 × 1600) and retain a caption with peak gain, frequency and variation.

Use **GainTotal** if you specifically want gain relative to accepted input power, or **RealizedGainTotal** to include mismatch at the driven port. Do not label directivity as gain. The rendered lobe radius is a display scale, not a physical field boundary or propagation distance.

## Animated antenna and ground surface currents

1. Use the solved `LoRa_Fields915` or `LoRa_Fields868` sweep. Confirm full fields were saved for the selected frequency and final variation; re-solve final nominal after optimization if needed.
2. In face selection mode, select antenna/trace copper faces and relevant ground faces. Include inner ground faces/returns where physically useful; hide dielectric or change transparency only for viewing. Do not select the airbox as a substitute for conductor faces.
3. Right-click **Field Overlays > Plot Fields > J > Mag_Jsurf** (equivalently **HFSS > Fields > Plot Fields > J > Mag_Jsurf**). Select solution, frequency and phase `0deg`. Click **Done**. Add a separate **Vector_Jsurf** overlay if arrows help reveal return paths.
4. Double-click the legend/plot to set a clear color scale, units **A/m**, suitable linear/log scale, and a fixed global min/max. Use the same range for every animation frame; independent autoscaling can exaggerate motion and obscure relative amplitude.
5. Right-click **Field Overlays > Jsurf > your current plot > Animate...**. In **Create Animation Setup**, select intrinsic variable **Phase**, Start `0deg`, Stop `360deg`, Step `10deg` (or 36 frames, depending on release). Click **OK**, then **Animate**. Use 24–36 frames for an uncluttered phase cycle; omit the duplicate 360° frame when looping if exporting frames.
6. Use **Export** in the Animation controls to save AVI or the available frame/image format in your installed release. For a GIF deliverable, export PNG frames and encode them locally. Avoid screen recording when a native export is available. Keep the camera, color limits, excitation amplitude and frequency fixed.

**Use a phase-dependent quantity.** HFSS defines `Mag_Jsurf` using the field at the selected phase; `ComplexMag_Jsurf` is a phasor magnitude and does not animate with phase. See [Ansys named field expressions](https://ansyshelp.ansys.com/public/views/secured/electronics/v251/en/subsystems/hfss/Content/ReportsandPostProc/CalculatingDerivedFieldQuantities.htm). For custom expressions, form `Mag(AtPhase(Jsurf,Phase))` (with the appropriate vector/smoothing operators), or animate the real vector at phase. The [Ansys phase-animation example](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/PDFs/HFSS%20Bandpass%20Filter.pdf) documents the plot-context **Animate** workflow.

A phase cycle at one frequency shows steady-state sinusoidal current evolution; it is not a packet/transient simulation. At 915 MHz its physical period is approximately 1.093 ns. Record the excitation normalization used; arbitrary 1 W results should not be labeled as currents at the actual transmitter power without proper scaling.
