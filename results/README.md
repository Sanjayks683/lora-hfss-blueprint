# Full local HFSS run archive

For the current RA-02 **433 MHz** design, use [the dedicated design folder](../designs/ra02_433/README.md) and its solved-project archive. The archive below preserves the earlier 868/915 MHz demonstration runs.

`hfss_local_runs.zip` contains all generated native HFSS test projects, their `.aedtresults` solution folders (including saved fields), working S11 CSV/plot outputs, and execution logs from this session. `manifest.json` lists the archived files with byte sizes and SHA-256 hashes. Extract the ZIP while preserving directory names so each `.aedt` stays next to its corresponding `.aedtresults` folder.

The useful solved runs are:

- `build/native_test_04.aedt`: the nominal baseline demonstration, with solution cache.
- `build/native_optimization_smoke.aedt`: the bounded two-iteration optimization demonstration and final nominal re-solve, with solution cache.
- `build/final_api_check_02.aedt`: the final prepared model with corrected explicit optimization bounds/step fields, validation only.

Other numbered projects and failure logs document earlier setup/debugging attempts. They are included for completeness, not as accepted simulation results. Shared working logs/status files may reflect the last test rather than every individual project. Consult `docs/VALIDATION.md` and each native solution's convergence data.

All models are illustrative monopoles, **not the original Raven PCB**. The target-band match was not achieved by the baseline or the deliberately bounded optimization smoke test. Neither is a completed production design.

The archive includes the saved radiation/current field solutions and a realized-gain report in the solved projects. It does **not** contain a rendered 3D gain-overlay image or Jsurf animation: those exports were not generated. Follow `docs/VISUALIZATIONS.md` to create them from the saved solutions.
