"""Offline tests only; recording calls is NOT an AEDT runtime test."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hfss = load("hfss_automation")
strip = load("microstrip")
post = load("postprocess_s11")


class Recorder:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args):
            self.calls.append((name, args))
        return record


class FakeEditor(Recorder):
    def GetModelUnits(self):
        return "mm"

    def GetObjectsInGroup(self, group):
        return ["Feed", "Substrate", "Ground"] if group == "Solids" else ["PortSheet"]

    def GetModelBoundingBox(self):
        return ["0", "0", "-0.035", "120", "110", "1.635"]


class FakeDesign:
    def __init__(self):
        self.modules = {name: Recorder() for name in ("AnalysisSetup", "BoundarySetup", "RadField", "Optimetrics")}
        self.modules["AnalysisSetup"].GetSetups = lambda: []
        self.modules["BoundarySetup"].GetExcitations = lambda: []

    def GetDesignType(self):
        return "HFSS"

    def GetSolutionType(self):
        return "HFSS Hybrid Modal Network"

    def GetVariables(self):
        return ["ant_len"]

    def GetVariableValue(self, name):
        return "60mm"

    def ChangeProperty(self, args):
        self.variable_change = args

    def GetModule(self, name):
        return self.modules[name]


class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((ROOT / "config/hfss_config.json").read_text())

    def test_config_and_import_guard(self):
        hfss.validate_config(self.cfg)
        c = copy.deepcopy(self.cfg)
        c["mode"] = "imported"
        with self.assertRaises(ValueError):
            hfss.validate_config(c)
        c = copy.deepcopy(self.cfg)
        c["goal_ranges_mhz"] = [[750, 900]]
        with self.assertRaises(ValueError):
            hfss.validate_config(c)

    def test_geometry_allowance(self):
        self.assertAlmostEqual(hfss.quarter_wave_mm(915), 81.91050765, places=6)
        self.assertAlmostEqual(hfss.quarter_wave_mm(800), 93.685143125, places=8)
        # ant_len increases by <=15 mm; default allowance is 16 mm per side.
        self.assertGreaterEqual(self.cfg["geometry_growth_allowance_mm"], 75 - 60)

    def test_native_array_contract(self):
        d, e = FakeDesign(), FakeEditor()
        hfss.configure(d, e, self.cfg)
        analysis = d.modules["AnalysisSetup"].calls
        self.assertEqual(sum(n == "InsertFrequencySweep" for n, _ in analysis), 3)
        setup = analysis[0][1][1]
        self.assertEqual(setup[setup.index("Frequency:=") + 1], "915MHz")
        opt = d.modules["Optimetrics"].calls[0]
        self.assertEqual(opt[1][0], "OptiOptimization")
        self.assertIn("NAME:LocalVariableTab", d.variable_change[1])
        variable_array = next(v for v in opt[1][1] if isinstance(v, list) and v[0] == "NAME:Variables")
        self.assertEqual(variable_array[2][variable_array[2].index("MinStep:=") + 1], "0.1mm")
        self.assertIn("MinFocus:=", variable_array[2])
        goals = [v for v in opt[1][1] if isinstance(v, list) and v[0] == "NAME:Goals"][0]
        goal = goals[1]
        self.assertEqual(goal[goal.index("Condition:=") + 1], "<=")
        self.assertIn("dB(S(LoRa_Port,LoRa_Port))", goal)
        box_call = next(args for name, args in e.calls if name == "CreateBox")
        self.assertAlmostEqual(float(box_call[0][box_call[0].index("XPosition:=") + 1][:-2]),
                               -hfss.quarter_wave_mm(915) - 16, places=6)

    def test_missing_variable_stops_before_air_creation(self):
        d, e = FakeDesign(), FakeEditor()
        d.GetVariables = lambda: []
        with self.assertRaises(ValueError):
            hfss.configure(d, e, self.cfg)
        self.assertFalse(e.calls)

    def test_microstrip_scaling(self):
        width = strip.width_for_z0(1.6, 4.3)
        self.assertTrue(2.9 < width < 3.3)
        self.assertAlmostEqual(strip.width_for_z0(0.2, 4.3), width / 8, places=8)
        self.assertGreater(strip.impedance(1, 1.6, 4.3), strip.impedance(3, 1.6, 4.3))

    def test_db_and_sampled_acceptance(self):
        edge = 10 ** (-10 / 20)
        self.assertAlmostEqual(post.db(complex(edge, 0)), -10)
        data = [(902, 0.1j), (903, 0.2j), (904, 0.1j)]
        self.assertTrue(post.assess(data, [(902, 904)])[0][-1])
        self.assertFalse(post.assess([(902, 0.5j), (903, 0.1j)], [(902, 903)])[0][-1])
        with self.assertRaises(ValueError):
            post.assess(data, [(901, 904)])
        with self.assertRaises(ValueError):
            post.assess([(902, 0.1j), (904, 0.1j)], [(902, 904)])

    def test_csv_units_and_duplicate_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.csv"
            path.write_text('Freq [GHz],"re(S(LoRa_Port,LoRa_Port)) []","im(S(LoRa_Port,LoRa_Port)) []"\n0.902,0.1,-0.2\n0.903,0.2,-0.1\n')
            data = post.read_hfss_csv(path)
            self.assertAlmostEqual(data[0][0], 902)
            self.assertEqual(data[0][1], 0.1 - 0.2j)
            path.write_text(path.read_text() + "0.903,0.2,-0.1\n")
            with self.assertRaises(ValueError):
                post.read_hfss_csv(path)


if __name__ == "__main__":
    unittest.main()
