# -*- coding: utf-8 -*-
"""Run inside AEDT's IronPython 2.7 engine: Tools > Run Script.

Default: build an explicitly illustrative printed monopole, no solve.
Imported mode: work on a COPY of a prepared HFSS Driven Modal model.
No PyAEDT, numpy, UI automation, or network access is used here.
"""
from __future__ import print_function
import json
import os
import sys
import traceback
import datetime

SETUP = "LoRa_Setup915"
SWEEP = "LoRa_Sweep800_1000"
OPT = "LoRa_MatchOptimization"
AIR = "LoRa_Air"
SPHERE = "LoRa_InfiniteSphere"
PORT = "LoRa_Port"


def mm(value):
    return "%.12gmm" % float(value)


def quarter_wave_mm(freq_mhz):
    return 299792458.0 / (float(freq_mhz) * 1e6) * 1000.0 / 4.0


def validate_config(c):
    if c["mode"] not in ("demo", "imported"):
        raise ValueError("mode must be demo or imported")
    if not 0 < float(c["padding_reference_mhz"]) <= 915:
        raise ValueError("Padding reference must be >0 and <=915 MHz")
    if float(c["geometry_growth_allowance_mm"]) < 0:
        raise ValueError("Negative geometry allowance")
    if not c["goal_ranges_mhz"]:
        raise ValueError("At least one optimization interval is required")
    for lo, hi in c["goal_ranges_mhz"]:
        if not 800 <= lo <= hi <= 1000:
            raise ValueError("Goals must lie inside the 800-1000 MHz sweep")
    for key in ("port_start_mm", "port_end_mm"):
        if len(c[key]) != 3:
            raise ValueError("Port coordinates must contain x,y,z")
        for value in c[key]:
            float(value)
    if c["port_start_mm"] == c["port_end_mm"]:
        raise ValueError("Zero-length integration line")
    if not c["optimization_variables"]:
        raise ValueError("Define at least one physically connected variable")
    names = [v["name"] for v in c["optimization_variables"]]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate optimization variables")
    if c["run_optimization"] and not c["solve_nominal"]:
        raise ValueError("Solve and inspect the nominal model before optimization")
    if int(c.get("max_optimization_iterations", 50)) < 1:
        raise ValueError("Optimization requires at least one iteration")
    if c["export_reports"] and not c["solve_nominal"]:
        raise ValueError("Report export needs a solved model")
    if c["mode"] == "imported":
        if not all(c[k] for k in ("geometry_and_stackup_verified",
                                  "optimization_dependencies_verified",
                                  "no_existing_open_region_verified")):
            raise ValueError("Complete the imported-model checklist and confirmations")
        if not c["project_path"] or not c["design_name"]:
            raise ValueError("Imported mode needs project_path and design_name")


def box(ed, name, origin, size, material, solve_inside):
    ed.CreateBox(["NAME:BoxParameters", "XPosition:=", origin[0],
                  "YPosition:=", origin[1], "ZPosition:=", origin[2],
                  "XSize:=", size[0], "YSize:=", size[1], "ZSize:=", size[2]],
                 ["NAME:Attributes", "Name:=", name, "Flags:=", "",
                  "Color:=", "(120 170 150)", "Transparency:=", 0.3,
                  "PartCoordinateSystem:=", "Global", "MaterialValue:=",
                  '"%s"' % material, "SolveInside:=", solve_inside])


def port_sheet(ed):
    # Explicit covered polyline avoids rectangle-axis ambiguity.
    points = [(58.5, 5, 0), (61.5, 5, 0), (61.5, 5, 1.6),
              (58.5, 5, 1.6), (58.5, 5, 0)]
    p = ["NAME:PolylinePoints"]
    for x, y, z in points:
        p.append(["NAME:PLPoint", "X:=", mm(x), "Y:=", mm(y), "Z:=", mm(z)])
    seg = ["NAME:PolylineSegments"]
    for i in range(4):
        seg.append(["NAME:PLSegment", "SegmentType:=", "Line",
                    "StartIndex:=", i, "NoOfPoints:=", 2])
    ed.CreatePolyline(["NAME:PolylineParameters", "IsPolylineCovered:=", True,
                       "IsPolylineClosed:=", True, p, seg,
                       ["NAME:PolylineXSection", "XSectionType:=", "None"]],
                      ["NAME:Attributes", "Name:=", "PortSheet",
                       "PartCoordinateSystem:=", "Global"])


def build_demo(design, project):
    """120x110 mm EXAMPLE, deliberately not the repository PCB."""
    design.ChangeProperty(["NAME:AllTabs", ["NAME:LocalVariableTab",
        ["NAME:PropServers", "LocalVariables"], ["NAME:NewProps",
        ["NAME:ant_len", "PropType:=", "VariableProp", "UserDef:=", True,
         "Value:=", "60mm"]]]])
    materials = project.GetDefinitionManager()
    materials.AddMaterial(["NAME:LoRa_Demo_FR4", "CoordinateSystemType:=", "Cartesian",
        "BulkOrSurfaceType:=", 1, ["NAME:PhysicsTypes", "set:=", ["Electromagnetic"]],
        "permittivity:=", "4.3", "dielectric_loss_tangent:=", "0.018"])
    ed = design.SetActiveEditor("3D Modeler")
    ed.SetModelUnits(["NAME:Units Parameter", "Units:=", "mm", "Rescale:=", False])
    box(ed, "Substrate", ["0mm", "0mm", "0mm"],
        ["120mm", "110mm", "1.6mm"], "LoRa_Demo_FR4", True)
    box(ed, "Ground", ["0mm", "0mm", "-0.035mm"],
        ["120mm", "30mm", "0.035mm"], "copper", False)
    box(ed, "Feed", ["58.5mm", "5mm", "1.6mm"],
        ["3mm", "25mm", "0.035mm"], "copper", False)
    box(ed, "Antenna", ["58.5mm", "30mm", "1.6mm"],
        ["3mm", "ant_len", "0.035mm"], "copper", False)
    ed.Unite(["NAME:Selections", "Selections:=", "Feed,Antenna"],
             ["NAME:UniteParameters", "KeepOriginals:=", False])
    port_sheet(ed)
    return ed


def goal(name, lo, hi):
    return ["NAME:" + name, "ReportType:=", "Modal Solution Data",
            "Solution:=", SETUP + " : " + SWEEP,
            "Calculation:=", "dB(S(%s,%s))" % (PORT, PORT),
            "Name:=", name, "Context:=", ["Domain:=", "Sweep"],
            ["NAME:Ranges", "Range:=", ["Var:=", "Freq", "Type:=", "rd",
             "Start:=", "%gMHz" % lo, "Stop:=", "%gMHz" % hi,
             "DiscreteValues:=", ""]], "Condition:=", "<=",
            ["NAME:GoalValue", "GoalValueType:=", "Independent",
             "Format:=", "Real/Imag", "bG:=", ["v:=", "[-10]"]],
            "Weight:=", "[1]"]


def configure(design, ed, c):
    solution_type = str(design.GetSolutionType())
    if design.GetDesignType() != "HFSS" or solution_type not in (
            "DrivenModal", "HFSS Modal Network", "HFSS Hybrid Modal Network"):
        raise ValueError("Requires HFSS 3D Modal Network; got " + solution_type)
    if ed.GetModelUnits() != "mm":
        raise ValueError("Model must already be in mm; do not rescale imported geometry blindly")
    objects = list(ed.GetObjectsInGroup("Solids")) + list(ed.GetObjectsInGroup("Sheets"))
    if c["port_sheet"] not in objects:
        raise ValueError("Missing configured port sheet")
    if AIR in objects:
        raise ValueError("Reserved air object already exists: start from a clean copy")
    analysis = design.GetModule("AnalysisSetup")
    if SETUP in list(analysis.GetSetups()):
        raise ValueError("Reserved setup exists: do not run twice on generated project")
    bounds = design.GetModule("BoundarySetup")
    if list(bounds.GetExcitations()):
        raise ValueError("Remove old ports from the prepared COPY; script assigns one 50-ohm port")
    variables = list(design.GetVariables())
    opt_vars = ["NAME:Variables"]
    starting = ["NAME:StartingPoint"]
    changed = ["NAME:ChangedProps"]
    for v in c["optimization_variables"]:
        if v["name"] not in variables:
            raise ValueError("Missing design variable: " + v["name"])
        starting += [v["name"] + ":=", design.GetVariableValue(v["name"])]
        changed.append(["NAME:" + v["name"], "Value:=", design.GetVariableValue(v["name"]),
                        ["NAME:Optimization", "Included:=", True,
                         "Min:=", v["min"], "Max:=", v["max"]]])
        opt_vars += [v["name"] + ":=", ["i:=", True, "int:=", False, "Min:=", v["min"],
                     "Max:=", v["max"], "MinStep:=", v["min_step"],
                     "MaxStep:=", v["max_step"], "MinFocus:=", v["min"],
                     "MaxFocus:=", v["max"], "UseManufacturableValues:=", False]]
    # Native AEDT ignores setup-level variable entries unless the design
    # variable itself is enabled for optimization first.
    design.ChangeProperty(["NAME:AllTabs", ["NAME:LocalVariableTab",
                           ["NAME:PropServers", "LocalVariables"], changed]])
    # Bounding box is captured before creating air. Extra allowance must bound
    # ALL geometry motion over optimization; importer must verify this manually.
    bb = [float(x) for x in ed.GetModelBoundingBox()]
    pad = quarter_wave_mm(c["padding_reference_mhz"]) + c["geometry_growth_allowance_mm"]
    origin = [mm(bb[i] - pad) for i in range(3)]
    size = [mm(bb[i + 3] - bb[i] + 2 * pad) for i in range(3)]
    box(ed, AIR, origin, size, "air", True)
    bounds.AssignRadiation(["NAME:LoRa_Radiation", "Objects:=", [AIR],
                            "IsFssReference:=", False, "IsForPML:=", False])
    bounds.AssignLumpedPort(["NAME:" + PORT, "Objects:=", [c["port_sheet"]],
        "RenormalizeAllTerminals:=", True, "DoDeembed:=", False,
        ["NAME:Modes", ["NAME:Mode1", "ModeNum:=", 1, "UseIntLine:=", True,
         ["NAME:IntLine", "Coordinate System:=", "Global",
          "Start:=", [mm(x) for x in c["port_start_mm"]],
          "End:=", [mm(x) for x in c["port_end_mm"]]],
         "AlignmentGroup:=", 0, "CharImp:=", "Zpi", "RenormImp:=", "50ohm"]],
        "ShowReporterFilter:=", False, "ReporterFilter:=", [True], "Impedance:=", "50ohm"])
    analysis.InsertSetup("HfssDriven", ["NAME:" + SETUP, "Frequency:=", "915MHz",
        "MaxDeltaS:=", 0.01, "MaximumPasses:=", 20, "MinimumPasses:=", 3,
        "MinimumConvergedPasses:=", 2, "PercentRefinement:=", 25,
        "IsEnabled:=", True, "BasisOrder:=", 1, "DoLambdaRefine:=", True,
        "DoMaterialLambda:=", True, "SaveAnyFields:=", True,
        "SaveRadFieldsOnly:=", False])
    analysis.InsertFrequencySweep(SETUP, ["NAME:" + SWEEP, "IsEnabled:=", True,
        "RangeType:=", "LinearStep", "RangeStart:=", "800MHz",
        "RangeEnd:=", "1000MHz", "RangeStep:=", "1MHz", "Type:=", "Interpolating",
        "SaveFields:=", False, "SaveRadFields:=", False, "InterpTolerance:=", 0.2,
        "InterpMaxSolns:=", 250, "InterpMinSolns:=", 0, "InterpMinSubranges:=", 1,
        "InterpUseS:=", True, "InterpUsePortImped:=", False,
        "InterpUsePropConst:=", True, "ExtrapToDC:=", False])
    # Independent solved frequencies for current and gain plots, not interpolated fields.
    for freq in (868, 915):
        analysis.InsertFrequencySweep(SETUP, ["NAME:LoRa_Fields%d" % freq,
            "IsEnabled:=", True, "RangeType:=", "LinearCount",
            "RangeStart:=", "%dMHz" % freq, "RangeEnd:=", "%dMHz" % freq,
            "RangeCount:=", 1, "Type:=", "Discrete", "SaveFields:=", True,
            "SaveRadFields:=", False, "ExtrapToDC:=", False])
    design.GetModule("RadField").InsertInfiniteSphereSetup(["NAME:" + SPHERE,
        "UseCustomRadiationSurface:=", False, "CSDefinition:=", "Theta-Phi",
        "Polarization:=", "Linear", "ThetaStart:=", "0deg", "ThetaStop:=", "180deg",
        "ThetaStep:=", "2deg", "PhiStart:=", "-180deg", "PhiStop:=", "180deg",
        "PhiStep:=", "2deg", "UseLocalCS:=", False])
    goals = ["NAME:Goals"]
    for i, interval in enumerate(c["goal_ranges_mhz"]):
        # Child name is Goal for the native Optimetrics array format.
        item = goal("Goal", interval[0], interval[1])
        item[item.index("Name:=") + 1] = "S11_band_%d" % i
        goals.append(item)
    design.GetModule("Optimetrics").InsertSetup("OptiOptimization", ["NAME:" + OPT,
        "IsEnabled:=", True, "SaveFields:=", False, starting,
        "Optimizer:=", "Quasi Newton", "MaxIterations:=", int(c.get("max_optimization_iterations", 50)),
        "PriorPSetup:=", "", "PreSolvePSetup:=", False, opt_vars, ["NAME:LCS"], goals,
        "Acceptable_Cost:=", 0.0, "Noise:=", 0.0001, "UpdateDesignWhenDone:=", True])


def reports(design, out_dir):
    r = design.GetModule("ReportSetup")
    s = "S(%s,%s)" % (PORT, PORT)
    solution = SETUP + " : " + SWEEP
    # Explicit nominal values also support parameterized imported models.
    families = ["Freq:=", ["All"]]
    for name in design.GetVariables():
        if not name.startswith("_"):
            families += [name + ":=", ["Nominal"]]
    r.CreateReport("LoRa_S11_dB", "Modal Solution Data", "Rectangular Plot", solution,
        ["Domain:=", "Sweep"], families, ["X Component:=", "Freq", "Y Component:=", ["dB(" + s + ")"]])
    r.CreateReport("LoRa_Smith50", "Modal Solution Data", "Smith Chart", solution,
        ["Domain:=", "Sweep"], families, ["Polar Component:=", [s]])
    # Portable real/imag CSV feeds the offline plotting and acceptance checker.
    r.CreateReport("LoRa_S11_RI", "Modal Solution Data", "Rectangular Plot", solution,
        ["Domain:=", "Sweep"], families,
        ["X Component:=", "Freq", "Y Component:=", ["re(" + s + ")", "im(" + s + ")"]])
    r.ExportToFile("LoRa_S11_RI", os.path.join(out_dir, "s11_ri.csv"), False)
    ff_families = ["Phi:=", ["All"], "Theta:=", ["All"], "Freq:=", ["915MHz"]]
    for name in design.GetVariables():
        if not name.startswith("_"):
            ff_families += [name + ":=", ["Nominal"]]
    r.CreateReport("LoRa_RealizedGain915", "Far Fields", "3D Polar Plot",
        SETUP + " : LoRa_Fields915", ["Context:=", SPHERE], ff_families,
        ["Phi Component:=", "Phi", "Theta Component:=", "Theta",
         "Mag Component:=", ["dB(RealizedGainTotal)"]])


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.environ.get("LORA_HFSS_CONFIG", os.path.join(root, "config", "hfss_config.json"))
    with open(cfg_path, "r") as stream:
        c = json.load(stream)
    validate_config(c)
    out = c["output_project"]
    if not os.path.isabs(out):
        out = os.path.join(root, out)
    out = os.path.abspath(out)
    if os.path.exists(out):
        raise ValueError("Refusing to overwrite existing output project: " + out)
    folder = os.path.dirname(out)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    import ScriptEnv
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
    desktop = globals()["oDesktop"]
    if c["mode"] == "demo":
        project = desktop.NewProject()
        project.InsertDesign("HFSS", "LoRa_Demo_Not_Raven", "DrivenModal", "")
        design = project.SetActiveDesign("LoRa_Demo_Not_Raven")
        ed = build_demo(design, project)
    else:
        source = os.path.abspath(c["project_path"])
        if os.path.normcase(source) == os.path.normcase(out):
            raise ValueError("Output must differ from imported source")
        desktop.OpenProject(source)
        project = desktop.GetActiveProject()
        design = project.SetActiveDesign(c["design_name"])
        ed = design.SetActiveEditor("3D Modeler")
    project.SaveAs(out, True)
    configure(design, ed, c)
    project.Save()
    log = os.path.join(folder, "hfss_validation.log")
    status = design.ValidateDesign(log)
    if status != 1:
        raise RuntimeError("HFSS validation failed; inspect " + log)
    if c["solve_nominal"]:
        design.Analyze(SETUP)
    if c["run_optimization"]:
        design.GetModule("Optimetrics").SolveSetup(OPT)
        # Re-solve final nominal state to retain current/gain fields after optimization.
        design.Analyze(SETUP)
    if c["export_reports"]:
        reports(design, folder)
    project.Save()
    with open(os.path.join(folder, "run_status.json"), "w") as stream:
        json.dump({"aedt_version": str(desktop.GetVersion()), "mode": c["mode"],
                   "validation_passed": status == 1,
                   "solve_requested": c["solve_nominal"],
                   "optimization_requested": c["run_optimization"],
                   "reports_requested": c["export_reports"],
                   "utc": datetime.datetime.utcnow().isoformat() + "Z"}, stream, indent=2)
    desktop.AddMessage(project.GetName(), design.GetName(), 0,
        "LoRa preparation complete. Inspect mesh convergence before accepting results.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        failure_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build")
        if not os.path.isdir(failure_path):
            os.makedirs(failure_path)
        with open(os.path.join(failure_path, "script_failure.log"), "w") as stream:
            stream.write(traceback.format_exc())
        raise
