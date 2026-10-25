"""Read HFSS discrete complex S11, check 433 MHz, and write numeric evidence."""
import argparse
import json
import math
from pathlib import Path
from postprocess_s11 import read_hfss_csv, db


def check(path):
    rows=read_hfss_csv(path)
    at433=[(f,g) for f,g in rows if abs(f-433)<1e-6]
    if len(at433)!=1: raise ValueError("Require exactly one directly solved 433 MHz sample")
    _,g=at433[0]
    z=50*(1+g)/(1-g)
    accepted=[f for f,v in rows if db(v)<=-10]
    return {"frequency_MHz":433,"reference_ohm":50,"S11_dB":db(g),
            "impedance_ohm":{"real":z.real,"imag":z.imag},
            "VSWR":(1+abs(g))/(1-abs(g)),"reflected_power_fraction":abs(g)**2,
            "mismatch_loss_dB":-10*math.log10(1-abs(g)**2),
            "requirement_dB":-10,"passes":db(g)<=-10,
            "source":"Native HFSS discrete sweep export","csv":str(path),
            "accepted_samples_MHz":accepted}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv",type=Path)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=check(args.csv)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["passes"] else 2)
