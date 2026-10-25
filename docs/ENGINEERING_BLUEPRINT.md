# Engineering blueprint

## 1. Define the model and reference plane

For this carrier, first establish whether RF travels on the host PCB or stays on the LoRa module and its antenna connector. A screenshot of SPI traces is not RF artwork. Obtain the actual `.PcbDoc` and schematic or a fabrication export with layer map and stackup. Confirm antenna type: PCB monopole/IFA, wire, external whip, or chip antenna. A bare carrier without its actual antenna cannot produce the antenna's far-field pattern.

Define one measurement/simulation reference plane: normally the compatible module's specified 50 Ω antenna interface, or a calibrated antenna connector. Model everything downstream of that plane, including the matching pads, feed, antenna, host ground, connector shield, mounting hardware and nearby metal that affects current. If starting at a bare RF IC pin, use the manufacturer's RF network and port impedance; a bare PA pin must not automatically be treated as 50 Ω.

Record these values before modeling:

| Required input | How to obtain it |
|---|---|
| Actual board outline, slots, antenna copper and ground clearance | CAD, not screenshot scaling |
| Copper order and thickness | Fabricator's final stackup; include plating |
| Feed height `h` | Dielectric distance to the actual reference ground, not total board thickness on a multilayer board |
| Dielectric Dk/Df near 900 MHz, solder-mask properties | Laminate and fabricator data; record tolerances |
| Via drill, barrel plating, pads, antipads, ground stitching | CAD/fabrication data |
| Antenna, connector, cable, shield, module and enclosure | Mechanical model + electrical structure |
| Target passband(s), deployment configuration | Product specification |

Use two distinct builds if the product has separate 868 and 915 MHz variants. For simultaneous coverage, impose both frequency intervals on the same design. Illustrative goals here are 863–870 and 902–928 MHz; they are engineering test intervals, not a statement of transmission permissions.

## 2. Export from Altium

**Preferred: EDB.** In the PCB editor, repour polygons (**Tools > Polygon Pours > Repour All**), resolve connectivity/DRC problems, and save a revision copy. Confirm physical board shape and layer stack before export. Install the **Ansys EDB Exporter** extension if absent, then use **File > Export > Ansys EDB**. Export metric units and retain the entire `.edb` folder containing `edb.def`. Validate component values after import: exporter fallbacks can substitute values when a source value is missing. Board cutouts also need special checking because the documented exporter has limitations. See [Altium EDB export](https://www.altium.com/documentation/altium-designer/design-tools-interfacing/ansys-edb-export?version=20).

**Alternative: ODB++.** Use **File > Fabrication Outputs > ODB++ Files** (or the equivalent fabrication output in an OutputJob). Include every relevant copper layer, outline, pads/vias and drill information. Use the same origin and units for all outputs. Prefer this route over Gerber when connectivity and stackup translation are available.

**Fallback: Gerber + drill.** Use **File > Fabrication Outputs > Gerber Files** or **Gerber X2 Files**, and **File > Fabrication Outputs > NC Drill Files**. Export top/bottom/internal copper, solder mask if modeled, a single unambiguous board profile and Excellon drill, with plated/nonplated holes distinguished. Include a layer map, stackup table, units, zero-suppression/coordinate format and, if available, an IPC-D-356 connectivity netlist. Use RS-274X/X2 so apertures are explicit. Do not substitute paste or silkscreen for copper. Gerber alone does not provide a reliable dielectric stackup or plated-via electrical model.

Do not use a generic component STEP export as the only RF model: a mechanically plausible board can omit electrical copper and via barrels entirely.

## 3. Import through HFSS 3D Layout, then create HFSS 3D solids

1. Open AEDT. Use **File > Import > EDB**, **ODB++**, or **Gerber**, as appropriate. These imports enter the **HFSS 3D Layout** editor. See the [supported Layout import formats](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/Subsystems/HFSS3DLayout/Content/3DLayout/ImportingFilesintotheLayoutEditor.htm). Do not attempt to run this package's 3D Modeler script on a Layout design.
2. Map layers explicitly. Check top/bottom orientation, polarity, copper order, dielectric thickness, outline and voids. Gerber dark/clear regions must preserve copper and antipads; a visually filled polygon can be an inverted void. Load drill files and build correctly plated barrels rather than solid metal rods for every hole.
3. Open **Layout > Layers** to inspect/edit the stackup (some releases label this **Edit Layers**). Confirm dimensional units by measuring a known pitch and the board outline. Never repair a 25.4× scaling error by eye. Confirm whether displayed thickness is copper-only, plated, or effective thickness.
4. Inspect the full ground and antenna first. Retain RF-related mounting holes, return planes, module ground/shield and nearby conductors. Do not crop away the antenna's counterpoise to save mesh. Use circuit cutouts only for a separately defined feed-network extraction.
5. In the project tree, right-click **Analysis > Add HFSS Solution Setup**. Right-click that **HFSS setup > Export > HFSS Model**, and save/open the resulting `.aedt`. The exporter produces the model seen by the HFSS solver, so curve approximation and export tolerances matter. Vendor confirmation of this route is available in the [Ansys Layout export discussion](https://innovationspace.ansys.com/forum/forums/topic/is-it-normal-that-dielectric-fill-is-invisible-in-layout-component-under-hfss/).
6. In the exported **HFSS 3D** design, confirm **HFSS > Solution Type > Modal** / **Driven Modal**. Remove obsolete imported excitation/open-region assignments from a preparation copy before using this script. Keep needed copper material/boundary assignments.
7. Save this preparation copy. An exported trace is usually an imported solid with no original routing parameters. Rebuild the tunable radiator end or feed gap as native geometry if geometric optimization is required.

### Geometry acceptance gate

- Compare board width/height, antenna end-to-end path, feed width, minimum gap, pad pitches, drill positions and layer Z positions against CAD. Set an explicit comparison tolerance appropriate to the design; e.g. ≤0.01 mm for critical small feed/matching gaps when the source precision supports it.
- Inspect top, bottom and sectional views. Verify all intended ground islands connect through plated vias. Preserve deliberately isolated RF nodes and antenna keepouts.
- Check sliver faces, duplicate overlapping sheets, self intersections, accidental copper bridges, missing voids, disconnected via barrels and ground planes at the wrong Z.
- Use **Modeler > Model Analysis** tools available in the release to inspect/heal imported bodies, then **HFSS > Validation Check**. Heal on a duplicate and keep tolerance much smaller than the narrowest intentional gap; never blanket-unite all copper or globally close small gaps.
- Confirm dielectric interiors and conductor contact at every transition. Use finite-conductivity copper for final loss results; PEC is useful for an initial diagnostic only. Avoid double-counting a copper sheet and an overlapping solid.
- Compare connectivity/net counts where import data supports it. Gerber-derived connectivity needs particular scrutiny. A green validation check does not prove electrical equivalence to the source PCB.

## 4. Feedline and matching layout

For an ordinary microstrip, place the signal above a continuous ground plane with dielectric height `h`, trace width `w`, and known Dk. Run a first estimate:

```powershell
python scripts\microstrip.py --h-mm 1.6 --er 4.3
python scripts\microstrip.py --h-mm 0.2 --er 4.3
```

Expect roughly 3.1 mm and 0.39 mm respectively for a zero-thickness 50 Ω estimate. This is not a prescription for the Raven board; its stackup is unknown. If top-side ground is close to the trace, use a **grounded coplanar waveguide** model including gap, side grounds and vias. Solder mask, thickness, copper roughness and the actual ground width alter impedance. Validate a uniform feed coupon with a field solver or a two-port HFSS model before optimizing the antenna.

Keep RF paths short, avoid reference-plane splits and narrow ground necks, and route digital lines away from the radiator/launch. Use smooth changes or suitable miters at bends. Place ground vias beside shunt pads and connector grounds with a short return path. A 2–3 mm stitching pitch is a useful initial layout scale near a 900 MHz feed, subject to geometry and fabrication limits; do not place these grounds into the radiator's required keepout. Follow the antenna manufacturer's all-layer keepout if using a chip antenna.

Reserve a **shunt–series–shunt π footprint** at the 50 Ω antenna interface:

```text
module 50 Ω RF ----o----[ series Zs ]----o---- feed/antenna
                  |                    |
              shunt Y1             shunt Y2
                  |                    |
              GND vias             GND vias
```

Use one selected footprint family, typically 0402 if assembly and tuning support it; pick real land patterns from the chosen components. Put each shunt ground via immediately adjacent to its ground pad, minimize pad-to-via loop, preserve clearance between series pads, and retain an accessible VNA connection strategy. Initially populate the series bridge with 0 Ω and leave both shunts DNP. DNP pads still have capacitance, and the 0 Ω part has parasitics. Do not use a physically open series gap as the baseline antenna feed.

For HFSS-only ideal matching, make separate covered sheets across each component gap and assign **HFSS > Boundaries > Assign > Lumped RLC** (some releases group this under circuit elements). Enable only the intended R/L/C terms. A shunt element must span RF node to actual ground, not float between unconnected pads. A series element bridges two RF nodes. Never overlap a lumped element with a copper short. For final matching, use vendor RF models/S-parameters with the pad/via EM model and avoid counting the same pads twice.

## 5. Port configuration

**Recommended internal launch: lumped port.** Cut away the upstream active radio network at the defined 50 Ω interface. Create a small covered sheet spanning the physical signal conductor and its true reference ground. For microstrip it is usually a vertical sheet at the input cross section; it must contact both conductors, contain the dielectric gap, and not bridge the antenna feed with metal. Rename it `PortSheet`. In face/sheet selection mode use **HFSS > Excitations > Assign > Port > Lumped Port**. Use one mode, 50 Ω, no deembedding initially, and an integration line from ground to signal entirely within the port sheet. Inspect endpoints/contact in section view. See the [native lumped-port API](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/Subsystems/Maxwell/Subsystems/Maxwell%20Scripting/Content/AssignLumpedPort.htm).

The script assigns this port by object name and uses the configured global coordinates in mm. It assumes a single-ended Driven Modal model. Its 50 Ω renormalization defines the S-parameter reference; it does not force the feed or antenna impedance to 50 Ω. Do not add a second excitation to the same sheet.

**Alternative: wave port.** Use a port on an exterior solution face, normal to a uniform feed extension. For microstrip include the signal, dielectric, ground and enough air/lateral width to contain fringing fields. Start with lateral span about 5–10 trace widths and several substrate heights of air, then increase the aperture to check impedance/S11 stability. These are starting dimensions, not universal port sizes. Use one quasi-TEM mode, inspect its E-field and modal impedance, and define ground-to-signal integration. Use **HFSS > Excitations > Assign > Port > Wave Port**. A wave port inside the air volume requires a valid backing/cap treatment; an arbitrary interior rectangle is not interchangeable with a lumped port. For coax, use the actual annulus between inner and outer conductors at the cable cross section.

If using a wave port, assign it manually/in a recorded release-specific script and adapt this package's port assignment/preflight rather than placing both kinds. For reference-plane shifts, deembed only through a uniform, characterized line. Retain the actual feed length if that is included in the VNA measurement.

## 6. Air region and solver acceptance

Free-space wavelength at 915 MHz is **327.6420 mm**, so λ0/4 is **81.9105 mm**. At 800 MHz the quarter-wave distance is **93.6851 mm**. Radiation boundaries generally need at least a quarter wavelength from radiating structure; see [Ansys radiation boundary guidance](https://ansyshelp.ansys.com/public/views/secured/electronics/v261/en/subsystems/hfss/Content/HFSS/RadiationBoundaries.htm).

The script encloses the complete pre-air geometry bounding box, pads all six sides by λ0/4 at the configured reference, and adds a separate geometry-growth allowance. The default 16 mm allowance accommodates the demo's maximum radiator extension. For imported models compute the largest motion of every optimized part and increase it if necessary. To enforce λ0/4 at the lowest sweep frequency for every variation, set `padding_reference_mhz` to **800**, keeping geometry allowance separate. Repeat with a larger region (or a validated PML) before accepting results. Do not apply radiation to the substrate, antenna, ground, or port sheet.

Mesh feed edges, narrow antenna gaps, matching pads and via contacts adequately. Start with local lengths around one third of a critical narrow gap/trace scale, then refine and test result stability; a universal global mesh length is inappropriate. Inspect actual tetrahedra rather than relying on a nominal setting. Require convergence before the pass limit, then tighten ΔS to 0.005 and compare resonance, complex input impedance, gain and efficiency. Check 868 and both band edges with independent adaptive setups when the 915 MHz mesh may be inadequate. A saved discrete field solve uses the existing mesh; it is not another adaptive-frequency validation.
