"""Generate exact rectangular copper artwork for the simulated 433 MHz coupon.
Input: JSON final_parameters.json. Output: Gerber RS-274X, drill, DXF and SVG.
No schematic or full RA-02 carrier is inferred from the original screenshots.
"""
import argparse
import csv
import json
from pathlib import Path


def rectangles(c):
    w=c["feed_width_mm"]
    x=10-w/2
    return [("RF input",x,5,w,3.5),("L1 input pad",9.5,8.5,1,1.5),
            ("L1 output pad",9.5,10.8,1,1.5),("Feed",x,12.3,w,22.7),
            ("Antenna rise",9,34,2,27),("Antenna top",9,59,c["ant_span_mm"]+2,2),
            ("Antenna open end",9+c["ant_span_mm"],60-c["ant_end_mm"],2,c["ant_end_mm"]+1),
            ("C1 ground pad",6.9,7.4,.8,1.2)]


def gerber(path, rects):
    def coord(x,y): return "X%010dY%010d"%(round(x*1e6),round(y*1e6))
    lines=["G04 433 MHz RA02 antenna coupon - units mm*","%FSLAX46Y46*%","%MOMM*%",
           "%ADD10C,0.010000*%","%LPD*%","D10*"]
    for name,x,y,w,h in rects:
        lines += ["G04 "+name+"*","G36*",coord(x,y)+"D02*",coord(x+w,y)+"D01*",
                  coord(x+w,y+h)+"D01*",coord(x,y+h)+"D01*",coord(x,y)+"D01*","G37*"]
    lines.append("M02*")
    path.write_text("\n".join(lines)+"\n",encoding="ascii")


def export(c,out):
    out.mkdir(parents=True,exist_ok=True)
    top=rectangles(c)
    gerber(out/"RA02_433.GTL",top)
    gerber(out/"RA02_433.GBL",[("Ground plane",0,0,120,35)])
    # The simulation has no soldermask. These openings intentionally expose all copper.
    for ext in ("GTS","GBS"):
        gerber(out/("RA02_433."+ext),[("No soldermask on coupon",0,0,120,65)])
    outline=["G04 Board profile 120 x 65 mm*","%FSLAX46Y46*%","%MOMM*%","%ADD10C,0.050000*%",
             "D10*","X0000000000Y0000000000D02*","X0120000000Y0000000000D01*",
             "X0120000000Y0065000000D01*","X0000000000Y0065000000D01*","X0000000000Y0000000000D01*","M02*"]
    (out/"RA02_433.GKO").write_text("\n".join(outline)+"\n")
    (out/"RA02_433_PTH.drl").write_text("M48\n; Finished plated hole 0.300 mm; 25 um radial plating\nMETRIC,TZ\nT01C0.300\n%\nG90\nT01\nX7.300Y8.000\nM30\n")
    # DXF closed polylines on named copper/profile layers; all coordinates in mm.
    dxf=["0","SECTION","2","HEADER","9","$INSUNITS","70","4","0","ENDSEC","0","SECTION","2","ENTITIES"]
    for layer,rs in (("TOP_COPPER",top),("BOTTOM_COPPER",[("Ground",0,0,120,35)]),
                     ("BOARD_OUTLINE",[("Board",0,0,120,65)])):
        for _,x,y,w,h in rs:
            dxf += ["0","LWPOLYLINE","100","AcDbEntity","8",layer,"100","AcDbPolyline","90","4","70","1"]
            for xx,yy in ((x,y),(x+w,y),(x+w,y+h),(x,y+h)):
                dxf += ["10",str(xx),"20",str(yy)]
    dxf += ["0","CIRCLE","8","PTH_DRILL","10","7.3","20","8.0","30","0","40","0.15",
            "0","ENDSEC","0","EOF"]
    (out/"RA02_433.dxf").write_text("\n".join(dxf)+"\n")
    # Dimensions and coordinates follow HFSS lower-left origin; SVG inverts Y.
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="-8 -12 138 88">',
         '<rect x="-8" y="-12" width="138" height="88" fill="#f5f7fa"/>',
         '<text x="0" y="-7" font-family="sans-serif" font-size="3.5" font-weight="bold">RA-02 | 433 MHz FR4 antenna + L/C match</text>',
         '<rect x="0" y="0" width="120" height="65" fill="#e0ebe3" stroke="#243a36" stroke-width="0.25"/>',
         '<rect x="0" y="0" width="120" height="30" fill="#fff2d0"/>',
         '<line x1="0" y1="30" x2="120" y2="30" stroke="#c25338" stroke-dasharray="1,1" stroke-width="0.25"/>',
         '<text x="30" y="12" font-family="sans-serif" font-size="2.7">RADIATOR: no bottom copper, components or metal here</text>',
         '<text x="36" y="50" font-family="sans-serif" font-size="2.7">Bottom ground: 120 × 35 mm</text>']
    for _,x,y,w,h in top:
        svg.append('<rect x="%g" y="%g" width="%g" height="%g" fill="#b76b2b"/>'%(x,65-y-h,w,h))
    svg += ['<circle cx="7.3" cy="57" r="0.15" fill="white" stroke="black" stroke-width="0.1"/>',
            '<line x1="7.7" y1="57" x2="8.43165" y2="57" stroke="#255eab" stroke-width="0.6"/>',
            '<line x1="10" y1="54.2" x2="10" y2="55" stroke="#255eab" stroke-width="0.6"/>',
            '<text x="14" y="57" font-family="sans-serif" font-size="2.4">L1 = %g nH (series); C1 = %g pF (shunt)</text>'%(c["L_nH"],c["C_pF"]),
            '<text x="14" y="62" font-family="sans-serif" font-size="2.4">RF input at (10, 5) mm; 50 Ω reference</text>',
            '<text x="0" y="71" font-family="sans-serif" font-size="2.5">120 × 65 mm | FR4 dielectric 1.6 mm | copper 35 µm | all dimensions in mm</text>',
            '<text x="0" y="75" font-family="sans-serif" font-size="2.3">Coupon artwork, not a complete RA-02 carrier. Match must be measured after integration.</text>','</svg>']
    (out/"RA02_433_layout.svg").write_text("\n".join(svg)+"\n",encoding="utf-8")
    with (out/"BOM.csv").open("w",newline="",encoding="utf-8") as stream:
        writer=csv.writer(stream)
        writer.writerow(["Reference","Value","Role","Model"])
        writer.writerow(["L1","%g nH"%c["L_nH"],"Series RF inductor, 0603","Series resistance 0.25 ohm; vendor RF model must be checked"])
        writer.writerow(["C1","%g pF"%c["C_pF"],"Shunt C0G/NP0 capacitor, 0603","ESR 0.08 ohm + ESL 0.3 nH; ground via modeled in EM"])
    (out/"geometry_rectangles.json").write_text(json.dumps(top,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("parameters",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    export(json.loads(args.parameters.read_text()),args.output)
