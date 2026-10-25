# Sources and assumptions

Reviewed 2026-10-25. Use your installed AEDT Help and recorded scripts as the release-specific authority. Menu examples refer to HFSS 3D unless explicitly labeled Layout.

| Source | Used for |
|---|---|
| [Original folder at inspected commit](https://github.com/Stavyansh/PCB-Design/tree/1a9fc4166bf9c25f6e9df71fcfc9cf6936299828/lora_module_v1) | Available assets; README module/band and approximate board size |
| [Ai-Thinker RA-02](https://docs.ai-thinker.com/en/Ra-02/) | 410–525 MHz module specification |
| [TI 433 to 930 MHz BOM-tunable PCB antenna](https://www.ti.com/lit/an/swra730/swra730.pdf) | Printed monopole and external matching engineering context; the coupon geometry here is independently modeled |
| [Ansys antenna parameter selection](https://ansyshelp.ansys.com/public/views/secured/electronics/v252/en/subsystems/hfss/Content/ReportsandPostProc/SelectingAntennaParameterstoPlot.htm) | Correct native report type `Antenna Parameters` and efficiency/power quantities |
| [Semtech SX1278](https://www.semtech.com/products/wireless-rf/lora-connect/sx1278) | Device identification and frequency-range limitation |
| [Altium EDB exporter](https://www.altium.com/documentation/altium-designer/design-tools-interfacing/ansys-edb-export?version=20) | File > Export > Ansys EDB; exported layers/components; cutout/value caveats |
| [Altium CAM imports/exports](https://www.altium.com/documentation/altium-designer/preparing-for-manufacture/cam/imports-exports) | Fabrication data and format considerations |
| [Ansys Layout import formats, 2025 R1](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/Subsystems/HFSS3DLayout/Content/3DLayout/ImportingFilesintotheLayoutEditor.htm) | EDB, ODB++, Gerber route into Layout |
| [Ansys Layout export confirmation](https://innovationspace.ansys.com/forum/forums/topic/is-it-normal-that-dielectric-fill-is-invisible-in-layout-component-under-hfss/) | HFSS setup > Export > HFSS Model |
| [Native solution setup, 2024 R2](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v242/en/Subsystems/HFSS/Subsystems/HFSS%20Scripting/Content/InsertSetup.htm) | HfssDriven setup API |
| [Native sweep API, 2025 R1](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/Subsystems/HFSS/Subsystems/HFSS%20Scripting/Content/InsertFrequencySweep.htm) | Interpolating/discrete sweeps and field-saving flags |
| [Native optimization API, 2025 R2](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v252/en/Subsystems/HFSS/Subsystems/HFSS%20Scripting/Content/InsertSetupOptimization.htm) | Variables, bounds, goals and optimizer structure |
| [Ansys PyAEDT Optimetrics source](https://github.com/ansys/pyaedt/blob/main/src/ansys/aedt/core/modules/design_xploration.py) | Current native variable-array fields and range/discrete goal syntax; this package calls AEDT directly |
| [Variable optimization flags](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v242/en/Subsystems/HFSS/Subsystems/HFSS%20Scripting/Content/ChangePropertyForHFSSandMaxwell.htm) | Enabling design-variable Optimization before creating the setup |
| [Native lumped-port API, 2025 R1](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/Subsystems/Maxwell/Subsystems/Maxwell%20Scripting/Content/AssignLumpedPort.htm) | Port-mode, integration-line, impedance structure; shared AEDT help page |
| [Native radiation-boundary API](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/Subsystems/HFSS/Subsystems/HFSS%20Scripting/Content/AssignRadiation.htm) | AssignRadiation |
| [Native infinite sphere API](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v242/en/Subsystems/HFSS3DLayout/Subsystems/HFSS3DLayout%20Scripting/Content/InsertInfiniteSphereSetup.htm) | Sphere angular sampling |
| [Radiation-boundary principles](https://ansyshelp.ansys.com/public/views/secured/electronics/v261/en/subsystems/hfss/Content/HFSS/RadiationBoundaries.htm) | Quarter-wave separation and PML distinction |
| [Smith chart procedure](https://ansyshelp.ansys.com/public/views/secured/electronics/v261/en/subsystems/HFSS/Content/ReportsandPostProc/CreatingSmithCharts.htm) | Quantity and report menus |
| [Overlaying 3D polar plots](https://ansyshelp.ansys.com/public/views/secured/electronics/v252/en/Subsystems/HFSS/Content/ReportsandPostProc/Overlaying3DPolarPlotsofNearorFarFieldsonModels.htm) | Overlay menu, Phi/Theta eligibility, visibility/scale/transparency |
| [Derived field quantities](https://ansyshelp.ansys.com/public/views/secured/electronics/v251/en/subsystems/hfss/Content/ReportsandPostProc/CalculatingDerivedFieldQuantities.htm) | Phase-dependent Mag_Jsurf definition |
| [Ansys Bandpass Filter tutorial](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/PDFs/HFSS%20Bandpass%20Filter.pdf) | Plot-context phase animation workflow |

Board dimensions in the original README are approximate, not verified metrology. Demo material, geometry, component footprint size suggestions, mesh starting scales and acceptance tolerances are engineering assumptions/examples explicitly identified in the guide. The microstrip estimator uses common quasi-static zero-thickness closed-form approximations; it is a starting estimate, not a substitute for a stackup-specific field solution. No antenna simulation output is supplied as if it were measured or solved.
