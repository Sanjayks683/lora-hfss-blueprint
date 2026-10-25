# Configuration and execution

## Runtime separation

`hfss_automation.py` uses **AEDT's native IronPython 2.7 engine** and `ScriptEnv`. Run it with **Tools > Run Script** in Electronics Desktop, or with `ansysedt.exe -ng -RunScriptAndExit`. Student uses `ansysedtsv.exe`. Do not run it with ordinary `python.exe`; do not install PyAEDT into IronPython. The microstrip estimator, tests and CSV plotting tool use **CPython 3.10+**. No remote-access software, mouse automation or external HFSS server is needed.

The API targets the classic native interface documented in AEDT 2024 R2/2025 R2. The installed Student 2025 R2 reports version **2025.2.4** and names its driven modal solver **HFSS Hybrid Modal Network**. The script accepts this and the older names. It also enables each design variable's Optimization flag before adding setup-level variable bounds; omitting that flag causes AEDT to discard the variable entries. Later or earlier releases may change optional setup/report properties. If a command is rejected, use **Tools > Record Script**, perform only that operation in a scratch project, stop recording, and compare the generated argument array. Preserve the solver type, port reference and physical intent when adapting a call.

## Demo mode

The default builds a 120 × 110 mm illustrative dielectric board, 1.6 mm dielectric thickness, 35 µm copper, 120 × 30 mm partial ground, and a straight printed radiator controlled by `ant_len`. The material Dk=4.3 and Df=0.018 are **example assumptions**. The radiator, feed and ground are not a reconstruction or recommended production antenna. It has no physical π components; use it to exercise setup, parameter coupling and post-processing before adapting the real model.

`Tools > Run Script > scripts/hfss_automation.py` creates and saves a new project. With the default flags it configures and validates; it does not solve or export results. After inspecting the generated geometry/port, solve `LoRa_Setup915` using the project tree. Solve nominal before enabling/running optimization. A new scripted generation requires a new `output_project` filename because existing files are protected from overwrite.

## Imported mode

1. Prepare an HFSS 3D Driven Modal copy with complete physical geometry, materials and conductor assignments, in **mm**. Remove existing ports and any air/open region/radiation/PML assignment from that copy. The new region encloses the complete physical model. An imported region left in place would distort its bounding box.
2. Create the covered port sheet at the intended launch and name it `PortSheet` (or configure its actual name). Determine the integration-line endpoints from CAD coordinates. The script cannot infer contact connectivity from the screenshot or validate it with a coordinate-only test.
3. Create a local design variable such as `ant_len` and bind it to a native radiator-end dimension, gap or lumped-element value. Vary it manually between min/max and verify that geometry/element value changes. Merely creating `ant_len` in the variables table is insufficient. Project variables `$name` are not supported by this package's variable preflight; use design variables.
4. Edit `config/hfss_config.json`:

```json
{
  "mode": "imported",
  "project_path": "C:/RF/Raven_prepared.aedt",
  "design_name": "Raven_868_915",
  "output_project": "build/Raven_configured.aedt",
  "solve_nominal": false,
  "run_optimization": false,
  "export_reports": false,
  "geometry_and_stackup_verified": true,
  "optimization_dependencies_verified": true,
  "no_existing_open_region_verified": true,
  "padding_reference_mhz": 800.0,
  "geometry_growth_allowance_mm": 20.0,
  "port_sheet": "PortSheet",
  "port_start_mm": [10.0, 5.0, 0.0],
  "port_end_mm": [10.0, 5.0, 1.6],
  "goal_ranges_mhz": [[863.0, 870.0], [902.0, 928.0]],
  "optimization_variables": [
    {"name": "ant_len", "min": "45mm", "max": "75mm", "min_step": "0.1mm", "max_step": "2mm"}
  ]
}
```

**The coordinates and bounds above are placeholders**, not Raven measurements. Replace them. Set confirmations true only after completing the corresponding engineering checks. Choose a geometry-growth allowance that encloses every allowed variation.

5. Run the script. It opens the source and saves to a different output before configuration; the source file is not overwritten. The output contains partial changes if an AEDT call fails, so inspect the error and regenerate from the preparation copy. Do not re-run onto a half-configured result.
6. Inspect `build/hfss_validation.log`, geometry, boundary assignments and Optimetrics Goals/Variables. A successful `ValidateDesign` is a prerequisite, not convergence evidence.
7. Solve nominal with the project-tree **Analysis > LoRa_Setup915 > Analyze**, examine convergence and ports, then run **Optimetrics > LoRa_MatchOptimization > Analyze**. After optimization, solve the nominal setup again to preserve final field solutions and reports. For unattended execution, set solve/optimization/export flags true after the nominal model has already passed manual engineering review.

## Local script launcher

From the repository root:

```powershell
.\scripts\run_hfss.ps1 -AedtExe 'C:\Program Files\ANSYS Inc\v252\AnsysEM\ansysedt.exe'
# Installation found on this system:
.\scripts\run_hfss.ps1 -AedtExe 'S:\ANSYS Inc\ANSYS Student\v252\AnsysEM\ansysedtsv.exe'
```

Use the actual installed executable path; the launcher does not auto-detect it. It starts a hidden **non-graphical** local AEDT process and waits. Pass `-Gui` only if graphically launched script execution is specifically needed. Licenses, scripting support and enough RAM/disk are required. AEDT can exit with code 0 even after a script error, so the launcher also requires a fresh `run_status.json` completion marker. Neither marker nor exit status alone certifies convergence or S11 performance. If the desktop is already in use, run from that desktop via Tools > Run Script to avoid unnecessary instances. Use a separate output path per run.

An alternate config can be passed with `-ConfigPath`. Directly in AEDT, the default config is located relative to the script; the optional environment variable `LORA_HFSS_CONFIG` overrides it. Output paths are relative to the repository root; input `project_path` should be absolute.

Use **separate output directories** for concurrent jobs because CSV, validation logs and the completion marker are placed beside each output project. `max_optimization_iterations` defaults to 50; set it to a small positive integer for an execution smoke test, and inspect termination reason before interpreting its result.

## What the script deliberately requires you to model

Geometry import/healing, a measured stackup, port-sheet creation for the real board, exact CAD parameterization, physical matching footprints, component parasitics, enclosure detail, local mesh operations and VNA calibration remain model-specific work. Automatic generic import or gap healing would be unreliable without the absent CAD files. The guide gives the procedure, while the script supplies the complete common solver/boundary/port/optimization setup.

## Generated reports

With `solve_nominal` and `export_reports` true, the script creates S11 dB, a 50 Ω Smith chart, an auxiliary real/imaginary S11 report, and a 915 MHz realized-gain 3D polar plot. It exports `s11_ri.csv` next to the output project. That export contains one nominal variation; avoid multiple variations in the offline plotter.

The current distribution and gain-overlay styling use the procedures in `VISUALIZATIONS.md`. These display properties vary by release and need the actual model's conductor faces. They are not fabricated by the automation.
