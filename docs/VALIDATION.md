# Validation record

Date: **2026-10-25**. All desktop interaction was through local scripts and log/file inspection. No remote desktop or UI automation was used.

## Local HFSS runtime

- Installation: `S:/ANSYS Inc/ANSYS Student/v252/AnsysEM/ansysedtsv.exe`.
- Reported version: **2025.2.4**.
- Execution: `-ng -RunScriptAndExit` with a local script and `-LogFile`.
- Native IronPython execution and `ScriptEnv` initialization: passed.
- Demo geometry, material, 50 Ω lumped excitation and air/radiation assignment: created and model validation passed.
- 915 MHz adaptive setup, interpolating sweep and discrete field sweeps: completed normally.
- Adaptive convergence: 14 passes, 14,014 solved elements, final max ΔS **0.0072788148**, two consecutive passes below 0.01.
- Interpolating sweep: reported converged.
- S11 dB, Smith, real/imaginary S11 and 915 MHz realized-gain 3D polar report objects: created. CSV exported and read successfully by the offline plotter.
- Optimetrics execution: a bounded **two-iteration smoke test** ran the nominal `ant_len=60mm` and perturbed `ant_len=60.771805mm` variations, then stopped at the intentionally low iteration limit and re-solved/exported the final nominal state. This verifies geometry coupling and optimizer execution; it does not establish achievement of the −10 dB goal.
- Final setup-only native validation passed again after completing the current-release variable-array fields. Native project serialization retained `ant_len` setup bounds **45–75 mm**, minimum step **0.1 mm** and maximum step **2 mm**. The prepared model is included in `examples/lora_demo_prepared.aedt`. The bounded optimization smoke test preceded this step-size refinement; no full optimization success is claimed.
- Actual demonstration baseline results and convergence evidence: [examples](../examples/README.md). The baseline fails the target 902–928 MHz match.

Runtime checks revealed and corrected two compatibility details: the installed solver name is `HFSS Hybrid Modal Network`, and design variables must be enabled for Optimization before the native setup can use them. They also confirmed that AEDT can return process code 0 after a script error; the launcher checks a fresh script completion marker in addition to the process exit code.

Use a separate output directory for concurrent jobs so validation logs, report CSV and completion markers do not collide. Use `max_optimization_iterations` to bound a smoke test; the shipped default remains 50 for a tuning run.

## Offline checks

- Seven `unittest` tests passed: configuration/import guards, quarter-wave arithmetic/growth allowance, native-array contract recording, missing-variable preflight, microstrip scaling, sampled acceptance, CSV units/duplicate rejection.
- CPython compilation passed for scripts and tests.
- PowerShell launcher parsed successfully.
- Matplotlib PNG/SVG rendering tested first with a synthetic fixture kept outside deliverables, then with the **actual HFSS-exported** demonstration CSV. Final baseline image was visually inspected.
- The baseline acceptance check correctly returned a sampled **FAIL**, including exact band edges.

These offline tests do not emulate the electromagnetic solver. API recording mocks check argument construction only; the separate local HFSS run provides the native execution evidence.

## Remaining engineering verification

The linked source does not include editable PCB geometry, stackup or antenna CAD. Therefore no simulation of the actual Raven carrier/antenna, production matching values, airbox sensitivity, final discrete passband verification, enclosure/tolerance study, measured VNA correlation, radiation efficiency acceptance, or actual-board gain/current animation is claimed.

The report objects and saved-field solutions were created in HFSS. Interactive 3D overlay appearance and current-animation export must be checked using the supplied menu procedures on the intended production model. The package does not substitute the demo for that model.
