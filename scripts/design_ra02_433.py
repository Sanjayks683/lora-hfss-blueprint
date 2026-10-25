# -*- coding: utf-8 -*-
"""Native AEDT IronPython: 433 MHz FR4 bent-trace monopole, full-wave model.

Use RA433_OUTPUT to choose a fresh .aedt path. Default geometry is an initial
candidate; simulation results, not its nominal dimensions, determine acceptance.
RA433_END_MM and RA433_SPAN_MM control the open-end arm and horizontal span.
"""
from __future__ import print_function
import os, sys, json, traceback, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import hfss_automation as common

TARGET = 433
SETUP = "RA02_433"
SWEEP = "Sweep350_550"
PORT = "RF50"
OUT = os.environ.get("RA433_OUTPUT", os.path.join(ROOT,"build","ra02_433","candidate.aedt"))
ARM = float(os.environ.get("RA433_END_MM", "20"))
SPAN = float(os.environ.get("RA433_SPAN_MM", "95"))
MATCH = os.environ.get("RA433_MATCH", "1") == "1"
L_NH = float(os.environ.get("RA433_L_NH", "4.3"))
C_PF = float(os.environ.get("RA433_C_PF", "20"))


def sheet(ed, name, points):
    pts=["NAME:PolylinePoints"]
    for x,y,z in points+[points[0]]:
        pts.append(["NAME:PLPoint","X:=",common.mm(x),"Y:=",common.mm(y),"Z:=",common.mm(z)])
    segments=["NAME:PolylineSegments"]
    for i in range(len(points)):
        segments.append(["NAME:PLSegment","SegmentType:=","Line","StartIndex:=",i,"NoOfPoints:=",2])
    ed.CreatePolyline(["NAME:PolylineParameters","IsPolylineCovered:=",True,"IsPolylineClosed:=",True,
        pts,segments,["NAME:PolylineXSection","XSectionType:=","None"]],
        ["NAME:Attributes","Name:=",name,"PartCoordinateSystem:=","Global"])


def main():
    folder=os.path.dirname(OUT)
    if not os.path.isdir(folder): os.makedirs(folder)
    if os.path.exists(OUT): raise ValueError("Refusing to overwrite existing project")
    import ScriptEnv
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
    desktop=globals()["oDesktop"]
    project=desktop.NewProject()
    project.InsertDesign("HFSS","RA02_433_FR4_Trace","DrivenModal","")
    design=project.SetActiveDesign("RA02_433_FR4_Trace")
    ed=design.SetActiveEditor("3D Modeler")
    ed.SetModelUnits(["NAME:Units Parameter","Units:=","mm","Rescale:=",False])
    props=["NAME:NewProps"]
    for name,value in (("ant_end",common.mm(ARM)),("ant_span",common.mm(SPAN)),
                       ("L_match","%gnH"%L_NH),("C_match","%gpF"%C_PF)):
        props.append(["NAME:"+name,"PropType:=","VariableProp","UserDef:=",True,"Value:=",value])
    design.ChangeProperty(["NAME:AllTabs",["NAME:LocalVariableTab",["NAME:PropServers","LocalVariables"],props]])
    project.GetDefinitionManager().AddMaterial(["NAME:RA433_FR4","CoordinateSystemType:=","Cartesian",
        "BulkOrSurfaceType:=",1,["NAME:PhysicsTypes","set:=",["Electromagnetic"]],
        "permittivity:=","4.3","dielectric_loss_tangent:=","0.018"])
    common.box(ed,"FR4",["0mm","0mm","0mm"],["120mm","65mm","1.6mm"],"RA433_FR4",True)
    common.box(ed,"Ground",["0mm","0mm","-0.035mm"],["120mm","35mm","0.035mm"],"copper",False)
    # 50-ohm zero-thickness microstrip estimate; final launch is included in EM.
    feed_w=3.1367
    if MATCH:
        common.box(ed,"Feed",[common.mm(10-feed_w/2),"5mm","1.6mm"],
            [common.mm(feed_w),"3.5mm","0.035mm"],"copper",False)
        common.box(ed,"InputPad",["9.5mm","8.5mm","1.6mm"],["1mm","1.5mm","0.035mm"],"copper",False)
        ed.Unite(["NAME:Selections","Selections:=","Feed,InputPad"],["NAME:UniteParameters","KeepOriginals:=",False])
        common.box(ed,"FeedTail",[common.mm(10-feed_w/2),"12.3mm","1.6mm"],
            [common.mm(feed_w),"22.7mm","0.035mm"],"copper",False)
        common.box(ed,"OutputPad",["9.5mm","10.8mm","1.6mm"],["1mm","1.5mm","0.035mm"],"copper",False)
        ed.Unite(["NAME:Selections","Selections:=","FeedTail,OutputPad"],["NAME:UniteParameters","KeepOriginals:=",False])
    else:
        common.box(ed,"Feed",[common.mm(10-feed_w/2),"5mm","1.6mm"],
            [common.mm(feed_w),"30mm","0.035mm"],"copper",False)
    # U-bent monopole: start (10,35), rise to y60, span right, return down.
    common.box(ed,"AntRise",["9mm","34mm","1.6mm"],["2mm","27mm","0.035mm"],"copper",False)
    common.box(ed,"AntTop",["9mm","59mm","1.6mm"],["ant_span+2mm","2mm","0.035mm"],"copper",False)
    common.box(ed,"AntEnd",["9mm+ant_span","60mm-ant_end","1.6mm"],
        ["2mm","ant_end+1mm","0.035mm"],"copper",False)
    ed.Unite(["NAME:Selections","Selections:=",("FeedTail" if MATCH else "Feed")+",AntRise,AntTop,AntEnd"],
        ["NAME:UniteParameters","KeepOriginals:=",False])
    sheet(ed,"PortSheet",[(10-feed_w/2,5,0),(10+feed_w/2,5,0),
        (10+feed_w/2,5,1.6),(10-feed_w/2,5,1.6)])
    boundary=design.GetModule("BoundarySetup")
    if MATCH:
        common.box(ed,"CapGroundPad",["6.9mm","7.4mm","1.6mm"],["0.8mm","1.2mm","0.035mm"],"copper",False)
        for name,radius,material,inside in (("ViaCu","0.175mm","copper",False),("ViaDrill","0.15mm","air",True)):
            ed.CreateCylinder(["NAME:CylinderParameters","XCenter:=","7.3mm","YCenter:=","8mm",
                "ZCenter:=","-0.035mm","Radius:=",radius,"Height:=","1.67mm","WhichAxis:=","Z","NumSides:=","0"],
                ["NAME:Attributes","Name:=",name,"PartCoordinateSystem:=","Global","MaterialValue:=",'"'+material+'"',"SolveInside:=",inside])
        ed.Subtract(["NAME:Selections","Blank Parts:=","ViaCu,FR4,Ground,CapGroundPad","Tool Parts:=","ViaDrill"],
            ["NAME:SubtractParameters","KeepOriginals:=",False])
        ed.Subtract(["NAME:Selections","Blank Parts:=","FR4","Tool Parts:=","ViaCu"],
            ["NAME:SubtractParameters","KeepOriginals:=",True])
        ed.Unite(["NAME:Selections","Selections:=","Ground,CapGroundPad,ViaCu"],
            ["NAME:UniteParameters","KeepOriginals:=",False])
        sheet(ed,"L_Sheet",[(9.5,10,1.635),(10.5,10,1.635),(10.5,10.8,1.635),(9.5,10.8,1.635)])
        boundary.AssignLumpedRLC(["NAME:SeriesL","Objects:=",["L_Sheet"],
            ["NAME:CurrentLine","Start:=",["10mm","10mm","1.635mm"],"End:=",["10mm","10.8mm","1.635mm"]],
            "RLC Type:=","Serial","UseResist:=",True,"Resistance:=","0.25ohm",
            "UseInduct:=",True,"Inductance:=","L_match","UseCap:=",False])
        edge=10-feed_w/2
        sheet(ed,"C_Sheet",[(7.7,7.5,1.635),(edge,7.5,1.635),(edge,8.5,1.635),(7.7,8.5,1.635)])
        boundary.AssignLumpedRLC(["NAME:ShuntC","Objects:=",["C_Sheet"],
            ["NAME:CurrentLine","Start:=",[common.mm(edge),"8mm","1.635mm"],"End:=",["7.7mm","8mm","1.635mm"]],
            "RLC Type:=","Serial","UseResist:=",True,"Resistance:=","0.08ohm",
            "UseInduct:=",True,"Inductance:=","0.3nH","UseCap:=",True,"Capacitance:=","C_match"])
    boundary.AssignLumpedPort(["NAME:"+PORT,"Objects:=",["PortSheet"],"RenormalizeAllTerminals:=",True,
        "DoDeembed:=",False,["NAME:Modes",["NAME:Mode1","ModeNum:=",1,"UseIntLine:=",True,
        ["NAME:IntLine","Coordinate System:=","Global","Start:=",["10mm","5mm","0mm"],
        "End:=",["10mm","5mm","1.6mm"]],"AlignmentGroup:=",0,"CharImp:=","Zpi","RenormImp:=","50ohm"]],
        "ShowReporterFilter:=",False,"ReporterFilter:=",[True],"Impedance:=","50ohm"])
    common.box(ed,"Air",["-220mm","-220mm","-220.035mm"],
        ["560mm","505mm","441.67mm"],"air",True)
    boundary.AssignRadiation(["NAME:Radiation","Objects:=",["Air"],"IsFssReference:=",False,"IsForPML:=",False])
    display_objects=[("Air",1.0,(255,255,255)),("FR4",0.75,(35,105,80)),
                     ("Feed",0.0,(190,115,45)),("Ground",0.0,(190,115,45))]
    if MATCH: display_objects.append(("FeedTail",0.0,(190,115,45)))
    for obj,trans,color in display_objects:
        ed.ChangeProperty(["NAME:AllTabs",["NAME:Geometry3DAttributeTab",["NAME:PropServers",obj],
            ["NAME:ChangedProps",["NAME:Transparent","Value:=",trans],
             ["NAME:Color","R:=",color[0],"G:=",color[1],"B:=",color[2]]]]])
    analysis=design.GetModule("AnalysisSetup")
    analysis.InsertSetup("HfssDriven",["NAME:"+SETUP,"Frequency:=","433MHz","MaxDeltaS:=",0.01,
        "MaximumPasses:=",24,"MinimumPasses:=",3,"MinimumConvergedPasses:=",2,
        "PercentRefinement:=",10,"IsEnabled:=",True,"BasisOrder:=",1,"DoLambdaRefine:=",True,
        "DoMaterialLambda:=",True,"SaveAnyFields:=",True,"SaveRadFieldsOnly:=",False])
    analysis.InsertFrequencySweep(SETUP,["NAME:"+SWEEP,"IsEnabled:=",True,"RangeType:=","LinearStep",
        "RangeStart:=","350MHz","RangeEnd:=","550MHz","RangeStep:=","1MHz","Type:=","Interpolating",
        "SaveFields:=",False,"SaveRadFields:=",False,"InterpTolerance:=",0.1,"InterpMaxSolns:=",200,
        "InterpMinSolns:=",0,"InterpMinSubranges:=",1,"InterpUseS:=",True,
        "InterpUsePortImped:=",False,"InterpUsePropConst:=",True,"ExtrapToDC:=",False])
    analysis.InsertFrequencySweep(SETUP,["NAME:Fields433","IsEnabled:=",True,"RangeType:=","LinearCount",
        "RangeStart:=","433MHz","RangeEnd:=","433MHz","RangeCount:=",1,"Type:=","Discrete",
        "SaveFields:=",True,"SaveRadFields:=",False,"ExtrapToDC:=",False])
    design.GetModule("RadField").InsertInfiniteSphereSetup(["NAME:Sphere433","UseCustomRadiationSurface:=",False,
        "CSDefinition:=","Theta-Phi","Polarization:=","Linear","ThetaStart:=","0deg","ThetaStop:=","180deg",
        "ThetaStep:=","2deg","PhiStart:=","-180deg","PhiStop:=","180deg","PhiStep:=","2deg","UseLocalCS:=",False])
    project.SaveAs(OUT,True)
    if design.ValidateDesign(os.path.join(folder,"validation.log"))!=1: raise RuntimeError("Validation failed")
    design.Analyze(SETUP)
    reports=design.GetModule("ReportSetup")
    fam=["Freq:=",["All"]]
    for var in ("ant_end","ant_span","L_match","C_match"): fam += [var+":=",["Nominal"]]
    for name,quant in (("S11_dB",["dB(S(RF50,RF50))"]),("S11_RI",["re(S(RF50,RF50))","im(S(RF50,RF50))"])):
        reports.CreateReport(name,"Modal Solution Data","Rectangular Plot",SETUP+" : "+SWEEP,
            ["Domain:=","Sweep"],fam,["X Component:=","Freq","Y Component:=",quant])
        reports.ExportToFile(name,os.path.join(folder,name+".csv"),False)
    reports.CreateReport("Smith50","Modal Solution Data","Smith Chart",SETUP+" : "+SWEEP,
        ["Domain:=","Sweep"],fam,["Polar Component:=",["S(RF50,RF50)"]])
    design.ExportConvergence(SETUP,"",os.path.join(folder,"convergence.conv"))
    project.Save()
    with open(os.path.join(folder,"candidate.json"),"w") as stream:
        json.dump({"ant_end_mm":ARM,"ant_span_mm":SPAN,"feed_width_mm":feed_w,"board_mm":[120,65],
            "dielectric_mm":1.6,"copper_mm":0.035,"Dk":4.3,"Df":0.018,"frequency_MHz":433,
            "ground_y_max_mm":35,"air_padding_mm":220,"matching_enabled":MATCH,"L_nH":L_NH,"C_pF":C_PF,
            "aedt_version":str(desktop.GetVersion())},stream,indent=2)


if __name__=="__main__":
    try: main()
    except Exception:
        folder=os.path.dirname(OUT)
        if not os.path.isdir(folder): os.makedirs(folder)
        with open(os.path.join(folder,"failure.txt"),"w") as stream: stream.write(traceback.format_exc())
        raise
