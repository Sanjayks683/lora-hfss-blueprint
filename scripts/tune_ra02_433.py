# -*- coding: utf-8 -*-
"""Native IronPython: tune the physically modeled 433 MHz L/C matching network.
Uses a fresh project copy; re-solves with explicit adaptive convergence and checks
an independent discrete frequency grid. Exported CSV is the acceptance evidence.
"""
import os,sys,json,traceback
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE=os.environ.get("RA433_TUNE_SOURCE",os.path.join(ROOT,"build","ra02_433","candidate.aedt"))
TARGET=os.environ.get("RA433_TUNE_OUTPUT",os.path.join(ROOT,"build","ra02_433","verified","RA02_433_verified.aedt"))
CAP=os.environ.get("RA433_TUNE_C","20pF")
IND=os.environ.get("RA433_TUNE_L","4.3nH")
DELTA=float(os.environ.get("RA433_DELTA_S","0.01"))


def main():
    folder=os.path.dirname(TARGET)
    if not os.path.isdir(folder): os.makedirs(folder)
    if os.path.exists(TARGET): raise ValueError("Choose a fresh output project")
    import ScriptEnv
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
    desktop=globals()["oDesktop"]
    desktop.OpenProject(SOURCE)
    p=desktop.GetActiveProject(); d=p.SetActiveDesign("RA02_433_FR4_Trace")
    p.SaveAs(TARGET,True)
    d.SetVariableValue("C_match",CAP); d.SetVariableValue("L_match",IND)
    a=d.GetModule("AnalysisSetup")
    a.EditSetup("RA02_433",["NAME:RA02_433","Frequency:=","433MHz","MaxDeltaS:=",DELTA,
        "MaximumPasses:=",24,"MinimumPasses:=",3,"MinimumConvergedPasses:=",2,
        "PercentRefinement:=",10,"IsEnabled:=",True,"BasisOrder:=",1,"DoLambdaRefine:=",True,
        "DoMaterialLambda:=",True,"SaveAnyFields:=",True,"SaveRadFieldsOnly:=",False])
    a.InsertFrequencySweep("RA02_433",["NAME:Discrete420_446","IsEnabled:=",True,"RangeType:=","LinearStep",
        "RangeStart:=","420MHz","RangeEnd:=","446MHz","RangeStep:=","0.5MHz","Type:=","Discrete",
        "SaveFields:=",False,"SaveRadFields:=",False,"ExtrapToDC:=",False])
    if d.ValidateDesign(os.path.join(folder,"validation.log"))!=1: raise RuntimeError("HFSS validation failed")
    d.Analyze("RA02_433")
    r=d.GetModule("ReportSetup")
    fam=["Freq:=",["All"]]
    for name in d.GetVariables(): fam += [name+":=",["Nominal"]]
    r.CreateReport("Discrete_S11_RI","Modal Solution Data","Rectangular Plot","RA02_433 : Discrete420_446",
        ["Domain:=","Sweep"],fam,["X Component:=","Freq","Y Component:=",["re(S(RF50,RF50))","im(S(RF50,RF50))"]])
    r.CreateReport("Discrete_S11_dB","Modal Solution Data","Rectangular Plot","RA02_433 : Discrete420_446",
        ["Domain:=","Sweep"],fam,["X Component:=","Freq","Y Component:=",["dB(S(RF50,RF50))"]])
    for name in ("S11_RI","S11_dB","Discrete_S11_RI","Discrete_S11_dB"):
        r.ExportToFile(name,os.path.join(folder,name+".csv"),False)
    d.ExportConvergence("RA02_433","",os.path.join(folder,"convergence.conv"))
    p.Save()
    with open(os.path.join(folder,"tuned_parameters.json"),"w") as stream:
        json.dump({"L_match":str(d.GetVariableValue("L_match")),"C_match":str(d.GetVariableValue("C_match")),
                   "ant_end":str(d.GetVariableValue("ant_end")),"ant_span":str(d.GetVariableValue("ant_span")),
                   "aedt_version":str(desktop.GetVersion()),"adaptive_delta_s":DELTA},stream,indent=2)


if __name__=="__main__":
    try: main()
    except Exception:
        folder=os.path.dirname(TARGET)
        if not os.path.isdir(folder): os.makedirs(folder)
        with open(os.path.join(folder,"failure.txt"),"w") as stream: stream.write(traceback.format_exc())
        raise
