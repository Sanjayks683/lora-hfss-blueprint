# -*- coding: utf-8 -*-
"""Native IronPython: export solved 433 MHz reports, gain and current frames."""
import os,sys,json,traceback
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(ROOT,"scripts"))
SOURCE=os.environ.get("RA433_FINAL_SOURCE",os.path.join(ROOT,"build","ra02_433","verified","RA02_433_verified.aedt"))
OUT=os.path.join(ROOT,"designs","ra02_433","hfss_exports")
LOG=[]


def property_change(module,report,tab,server,props):
    module.ChangeProperty(["NAME:AllTabs",["NAME:"+tab,["NAME:PropServers",report+":"+server],
                           ["NAME:ChangedProps"]+props]])


def attempt(name,fn):
    try:
        value=fn(); LOG.append({"operation":name,"status":"ok"}); return value
    except Exception:
        LOG.append({"operation":name,"status":"error","detail":traceback.format_exc()})
    finally:
        with open(os.path.join(OUT,"export_log.json"),"w") as stream: json.dump(LOG,stream,indent=2)


def current_args(phase,faces):
    return ["NAME:Current433","SolutionName:=","RA02_433 : Fields433","QuantityName:=","Mag_Jsurf",
        "PlotFolder:=","Jsurf433","FieldType:=","Fields","UserSpecifyName:=",1,"UserSpecifyFolder:=",1,
        "IntrinsicVar:=","Freq='433MHz' Phase='%ddeg'"%phase,
        "PlotGeomInfo:=",[1,"Surface","FacesList",len(faces)]+faces,"FilterBoxes:=",[0],
        ["NAME:PlotOnSurfaceSettings","Filled:=",True,"IsoValType:=","Fringe","SmoothShade:=",True,
         "AddGrid:=",False,"MapTransparency:=",False,"Transparency:=",0,"ArrowUniform:=",True,
         "ArrowSpacing:=",0.1,"GridColor:=",[255,255,255]]]


def main():
    if not os.path.isdir(OUT): os.makedirs(OUT)
    import ScriptEnv
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
    desktop=globals()["oDesktop"]; desktop.OpenProject(SOURCE)
    p=desktop.GetActiveProject(); d=p.SetActiveDesign("RA02_433_FR4_Trace")
    ed=d.SetActiveEditor("3D Modeler"); r=d.GetModule("ReportSetup"); fields=d.GetModule("FieldsReporter")
    fam=["Freq:=",["All"]]
    for name in d.GetVariables(): fam += [name+":=",["Nominal"]]
    for name in ("S11_RI","S11_dB","Discrete_S11_RI","Discrete_S11_dB"):
        attempt(name+"_csv",lambda n=name:r.ExportToFile(n,os.path.join(OUT,n+".csv"),False))
    for name in ("S11_dB","Discrete_S11_dB","Smith50"):
        if "dB" in name:
            low,high=(420,446) if "Discrete" in name else (350,550)
            attempt(name+"_axis",lambda n=name,lo=low,hi=high:property_change(r,n,"Scaling","AxisX",
                [["NAME:Min","Value:=","%dMHz"%lo],["NAME:Max","Value:=","%dMHz"%hi],
                 ["NAME:Auto Units","Value:=",False],["NAME:Units","Value:=","MHz"]]))
            attempt(name+"_grid",lambda n=name:property_change(r,n,"Grid","Grid",
                [["NAME:Show minor X grid","Value:=",False],["NAME:Show minor Y grid","Value:=",False],
                 ["NAME:Major grid line color","R:=",220,"G:=",225,"B:=",230]]))
            attempt(name+"_limit",lambda n=name,lo=low,hi=high:r.AddCartesianLimitLine(n,
                ["NAME:CartesianLimitLine",["NAME:XValues",lo*1e6,hi*1e6],"XUnits:=","MHz",
                 ["NAME:YValues",-10,-10],"YUnits:=","","YAxis:=","Y1"]))
            attempt(name+"_limit_style",lambda n=name:property_change(r,n,"Limit Line","LimitLine1",
                [["NAME:Violation Emphasis","Value:=",False],["NAME:Hatch Pixels","Value:=","0"],
                 ["NAME:Line Width","Value:=","2"],["NAME:Color","R:=",40,"G:=",95,"B:=",160]]))
            attempt(name+"_433_marker",lambda n=name:r.AddCartesianXMarker(n,"433 MHz",433e6))
        attempt(name+"_native_image",lambda n=name:r.ExportImageToFile(n,os.path.join(OUT,n+"_native.jpg"),2000,1300))
    r.CreateReport("Zin433","Modal Solution Data","Rectangular Plot","RA02_433 : Discrete420_446",
        ["Domain:=","Sweep"],fam,["X Component:=","Freq","Y Component:=",["re(Z(RF50,RF50))","im(Z(RF50,RF50))"]])
    attempt("zin_csv",lambda:r.ExportToFile("Zin433",os.path.join(OUT,"Zin433.csv"),False))
    attempt("zin_image",lambda:r.ExportImageToFile("Zin433",os.path.join(OUT,"Zin433_native.jpg"),2000,1300))
    ffam=["Freq:=",["433MHz"],"Phi:=",["All"],"Theta:=",["All"]]
    for name in d.GetVariables(): ffam += [name+":=",["Nominal"]]
    r.CreateReport("RealizedGain433","Far Fields","3D Polar Plot","RA02_433 : Fields433",
        ["Context:=","Sphere433"],ffam,["Phi Component:=","Phi","Theta Component:=","Theta","Mag Component:=",["dB(RealizedGainTotal)"]])
    attempt("gain_native_image",lambda:r.ExportImageToFile("RealizedGain433",os.path.join(OUT,"gain433_native.jpg"),1700,1500))
    attempt("gain_csv",lambda:r.ExportToFile("RealizedGain433",os.path.join(OUT,"gain433.csv"),False))
    categories=attempt("antenna_categories",lambda:list(r.GetAllCategories("Antenna Parameters","Data Table","RA02_433 : Fields433",["Context:=","Sphere433"])))
    if categories:
        quantities=[]
        for category in categories:
            vals=attempt("antenna_quantities_"+category,lambda c=category:list(r.GetAllQuantities("Antenna Parameters","Data Table","RA02_433 : Fields433",["Context:=","Sphere433"],c)))
            if vals: quantities.extend(vals)
        wanted=[q for q in quantities if q in ("RadiationEfficiency","TotalEfficiency","PeakRealizedGain","PeakGain","RadiatedPower","AcceptedPower")]
        if wanted:
            fam1=["Freq:=",["433MHz"]]
            for name in d.GetVariables(): fam1 += [name+":=",["Nominal"]]
            attempt("antenna_metrics_report",lambda:r.CreateReport("AntennaMetrics433","Antenna Parameters","Data Table","RA02_433 : Fields433",
                ["Context:=","Sphere433"],fam1,["X Component:=","Freq","Y Component:=",wanted]))
            attempt("antenna_metrics_csv",lambda:r.ExportToFile("AntennaMetrics433",os.path.join(OUT,"antenna_metrics433.csv"),False))
    def picture(path,plot="none",orientation="isometric",w=1800,h=1300):
        ed.ExportModelImageToFile(path,w,h,["NAME:SaveImageParams","ShowAxis:=","False","ShowGrid:=","False",
            "ShowRuler:=","False","ShowRegion:=","False","Selections:=",["FR4","Feed","FeedTail","Ground"],
            "FieldPlotSelections:=",plot,"Orientation:=",orientation])
    attempt("model_image",lambda:picture(os.path.join(OUT,"model433_native.jpg")))
    faces=[str(x) for obj in ("Feed","FeedTail","Ground") for x in ed.GetFaceIDs(obj)]
    fields.CreateFieldPlot(current_args(0,faces),"Field"); fields.UpdateAllFieldsPlots()
    fields.SetPlotFolderSettings("Jsurf433",["NAME:FieldsPlotSettings","Real time mode:=",True,
        ["NAME:ColorMapSettings","ColorMapType:=","Spectrum","SpectrumType:=","Rainbow","UniformColor:=",[127,255,255],"RampColor:=",[255,127,127]],
        ["NAME:Scale3DSettings","m_nLevels:=",21,"m_autoScale:=",False,"minvalue:=",0.0,"maxvalue:=",500.0,"log:=",False,"IntrinsicMin:=",0.0,"IntrinsicMax:=",500.0],
        ["NAME:Marker3DSettings","MarkerType:=",0,"MarkerMapSize:=",False,"MarkerMapColor:=",False,"MarkerSize:=",0.25],
        ["NAME:Arrow3DSettings","ArrowType:=",1,"ArrowMapSize:=",True,"ArrowMapColor:=",True,"ShowArrowTail:=",True,"ArrowSize:=",0.25]])
    attempt("current_static",lambda:picture(os.path.join(OUT,"jsurf433_native.jpg"),"Current433"))
    attempt("current_field_data",lambda:fields.ExportFieldPlot("Current433","false",os.path.join(OUT,"jsurf433.aedtplt")))
    frames=os.path.join(OUT,"current_frames")
    if not os.path.isdir(frames): os.makedirs(frames)
    for phase in range(0,360,10):
        fields.ModifyFieldPlot("Current433",current_args(phase,faces)); fields.UpdateQuantityFieldsPlots("Jsurf433")
        attempt("phase_%03d"%phase,lambda ph=phase:picture(os.path.join(frames,"phase_%03d.jpg"%ph),"Current433","top",1000,900))
    fields.ModifyFieldPlot("Current433",current_args(0,faces))
    d.ExportConvergence("RA02_433","",os.path.join(OUT,"convergence.conv"))
    p.Save()
    with open(os.path.join(OUT,"provenance.json"),"w") as stream:
        json.dump({"project":SOURCE,"design":"RA02_433_FR4_Trace","frequency_MHz":433,"reference_ohm":50,
            "C_match":str(d.GetVariableValue("C_match")),"L_match":str(d.GetVariableValue("L_match")),
            "excitation":"1 W, 0 degrees","images":"Native HFSS exports","current_scale_A_per_m":[0,500],
            "errors":sum(e["status"]=="error" for e in LOG)},stream,indent=2)


if __name__=="__main__":
    try: main()
    except Exception:
        if not os.path.isdir(OUT): os.makedirs(OUT)
        with open(os.path.join(OUT,"failure.txt"),"w") as stream: stream.write(traceback.format_exc())
        raise
