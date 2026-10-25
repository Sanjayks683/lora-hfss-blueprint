import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("layout433",ROOT/"scripts/export_ra02_433_layout.py")
layout=importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout)


def overlaps(a,b):
    _,x,y,w,h=a
    _,xx,yy,ww,hh=b
    return min(x+w,xx+ww)>max(x,xx) and min(y+h,yy+hh)>max(y,yy)


class Layout433Test(unittest.TestCase):
    def setUp(self):
        self.c={"feed_width_mm":3.1367,"ant_span_mm":95,"ant_end_mm":20,"L_nH":4.7,"C_pF":18}

    def test_copper_bounds_and_intentional_component_gaps(self):
        rects=layout.rectangles(self.c)
        for _,x,y,w,h in rects:
            self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
            self.assertLessEqual(x+w,120);self.assertLessEqual(y+h,65)
        # Neither component gap is shorted by generated copper.
        self.assertFalse(any(overlaps(a,b) for a in rects[:2] for b in rects[2:7]))
        self.assertFalse(any(overlaps(a,rects[7]) for a in rects[:7]))
        self.assertAlmostEqual(rects[2][2]-(rects[1][2]+rects[1][4]),.8)

    def test_rf_trace_continuity_and_keepout(self):
        r=layout.rectangles(self.c)
        self.assertTrue(overlaps(r[3],r[4]))
        self.assertTrue(overlaps(r[4],r[5]))
        self.assertTrue(overlaps(r[5],r[6]))
        self.assertGreaterEqual(r[6][2]-35,5)

    def test_manufacturing_units_and_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);layout.export(self.c,out)
            top=(out/"RA02_433.GTL").read_text()
            self.assertIn("%MOMM*%",top)
            self.assertIn("%FSLAX46Y46*%",top)
            self.assertEqual(top.count("G36*"),8)
            self.assertIn("X0120000000Y0065000000",(out/"RA02_433.GKO").read_text())
            self.assertIn("X7.300Y8.000",(out/"RA02_433_PTH.drl").read_text())
            self.assertIn("$INSUNITS\n70\n4",(out/"RA02_433.dxf").read_text())


if __name__=="__main__": unittest.main()
