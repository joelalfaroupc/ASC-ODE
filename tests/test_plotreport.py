"""Standard-library regression tests for the documentation figure generator.

Run from ASC-ODE: python3 -B -m unittest discover -s tests -p 'test_plotreport.py'
"""
import math
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

# Import the demo without creating untracked __pycache__ files.
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "demos"))
import plotreport

SVG = "{http://www.w3.org/2000/svg}"


class NumericInputTests(unittest.TestCase):
    def read_csv(self, contents):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            path.write_text(contents, encoding="utf-8")
            return plotreport.read_numeric(path)

    def test_valid_csv_preserves_numeric_values_and_actual_step(self):
        rows = self.read_csv("t,value\n0,1\n0.125,0.8\n0.25,0.6\n")
        self.assertEqual(rows[1], {"t": 0.125, "value": 0.8})
        self.assertEqual(plotreport.step_size(rows), 0.125)

    def test_rejects_nonfinite_values(self):
        for value in ("nan", "inf", "-inf"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "non-finite"):
                    self.read_csv(f"t,value\n0,1\n0.1,{value}\n")

    def test_rejects_fewer_than_two_rows(self):
        for contents in ("t,value\n", "t,value\n0,1\n"):
            with self.subTest(contents=contents):
                with self.assertRaisesRegex(ValueError, "Missing"):
                    self.read_csv(contents)

    def test_rejects_invalid_time_grids(self):
        for times in ((0.1, 0.2), (0, 0), (0, -0.1)):
            with self.subTest(times=times):
                with self.assertRaisesRegex(ValueError, "time grid"):
                    self.read_csv(f"t,value\n{times[0]},1\n{times[1]},2\n")


class PlotMathTests(unittest.TestCase):
    def test_log_axes_reject_zero_and_negative_coordinates(self):
        for values in ([0, 1], [-1, 1]):
            with self.subTest(values=values):
                with self.assertRaisesRegex(ValueError, "positive"):
                    plotreport.axis_limits(values, True, None)

    def test_axes_reject_nonfinite_or_empty_coordinates(self):
        for values in ([], [1, math.nan], [1, math.inf]):
            with self.subTest(values=values):
                with self.assertRaisesRegex(ValueError, "finite and nonempty"):
                    plotreport.axis_limits(values, False, None)

    def test_log_limits_are_decade_coordinates(self):
        self.assertEqual(plotreport.axis_limits([0.001, 0.1], True, None), (-3, -1))
        self.assertEqual(plotreport.axis_limits([0.01, 0.1], True, (0.001, 1)), (-3, 0))

    def test_constant_series_gets_a_nonzero_axis_range(self):
        low, high = plotreport.axis_limits([1, 1], False, None)
        self.assertLess(low, 1)
        self.assertGreater(high, 1)

    def test_sampling_preserves_endpoints_and_coordinate_pairing(self):
        series = plotreport.Series("curve", list(range(1403)),
                                   [2*i for i in range(1403)], "#2366bd")
        sampled = plotreport.sample(series, limit=100)
        self.assertEqual(sampled[0], (0, 0))
        self.assertEqual(sampled[-1], (1402, 2804))
        self.assertLessEqual(len(sampled), 100)
        self.assertTrue(all(y == 2*x for x, y in sampled))

    def test_sampling_rejects_empty_or_mismatched_coordinates(self):
        for x, y in (([], []), ([0, 1], [0])):
            with self.subTest(x=x, y=y):
                with self.assertRaisesRegex(ValueError, "matching, nonempty"):
                    plotreport.sample(plotreport.Series("curve", x, y, "#2366bd"))

    def test_rc_reference_starts_at_zero_for_both_parameter_sets(self):
        for rc in (1.0, 0.0001):
            with self.subTest(rc=rc):
                self.assertEqual(plotreport.exact_rc([0], rc), [0])

    def test_rc_reference_matches_analytic_value_after_one_source_period(self):
        t = 0.02
        for rc in (1.0, 0.0001):
            with self.subTest(rc=rc):
                expected = (1-math.exp(-t/rc))/(1+(100*math.pi*rc)**2)
                self.assertAlmostEqual(plotreport.exact_rc([t], rc)[0], expected, places=14)


class SvgOutputTests(unittest.TestCase):
    def test_svg_preserves_escaped_labels_and_clips_curves(self):
        series = plotreport.Series("A < B & C", [0, 1], [0, 1], "#2366bd", markers=True)
        panels = [plotreport.Panel("Panel <one>", "x & time", "y < value", [series]),
                  plotreport.Panel("Panel two", "x", "y", [series])]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "figure.svg"
            plotreport.write_figure(path, "Title <test> & data", "Subtitle > 0", panels)
            root = ET.parse(path).getroot()
        self.assertEqual(root.tag, SVG + "svg")
        self.assertEqual(root.find(SVG + "title").text, "Title <test> & data")
        self.assertEqual(root.find(SVG + "desc").text, "Subtitle > 0")
        labels = [node.text for node in root.iter(SVG + "text")]
        self.assertIn("A < B & C", labels)
        self.assertIn("x & time", labels)
        clip_ids = {node.attrib["id"] for node in root.iter(SVG + "clipPath")}
        references = {node.attrib["clip-path"] for node in root.iter(SVG + "g")}
        self.assertEqual(clip_ids, {"panel-0", "panel-1"})
        self.assertEqual(references, {f"url(#{name})" for name in clip_ids})
        self.assertEqual(len(list(root.iter(SVG + "circle"))), 4)

    def test_phase_plot_can_use_equal_aspect_ratio(self):
        series = plotreport.Series("phase", [-1, 1], [-1, 1], "#2366bd")
        panel = plotreport.Panel("Phase", "x", "v", [series],
                                 xlim=(-2, 2), ylim=(-2, 2), equal=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "phase.svg"
            plotreport.write_figure(path, "Phase", "Equal scales", [panel])
            root = ET.parse(path).getroot()
        rectangle = root.find(f".//{SVG}clipPath/{SVG}rect")
        self.assertEqual(float(rectangle.attrib["width"]), float(rectangle.attrib["height"]))


class ReportIntegrationTests(unittest.TestCase):
    def test_existing_cpp_datasets_generate_all_nine_valid_figures(self):
        data = ROOT / "build"
        required = ([f"massspring_T{t}_h{h}.csv" for t in range(2) for h in range(3)]
                    + [f"rc_p{p}_h{h}.csv" for p in range(2) for h in range(4)]
                    + ["convergence.csv"])
        if not all((data / filename).is_file() for filename in required):
            self.skipTest("Run the C++ mass-spring, RC and convergence experiments first")
        expected = {
            "massspring_step_comparison.svg", "massspring_phase_comparison.svg",
            "massspring_long_time.svg", "massspring_energy.svg", "euler_convergence.svg",
            "rc_nonstiff_steps.svg", "rc_stiff_stability.svg", "rc_stiff_transient.svg",
            "rc_stiff_coarse_step.svg",
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            plotreport.generate(data, output)
            self.assertEqual({p.name for p in output.iterdir()}, expected)
            for path in output.iterdir():
                with self.subTest(figure=path.name):
                    root = ET.parse(path).getroot()
                    self.assertEqual(root.tag, SVG + "svg")
                    self.assertIsNotNone(root.find(SVG + "title"))
                    curves = list(root.iter(SVG + "polyline"))
                    self.assertTrue(curves)
                    for curve in curves:
                        coords = curve.attrib["points"].split()
                        self.assertGreaterEqual(len(coords), 2)
                        self.assertTrue(all(math.isfinite(float(value))
                                            for pair in coords for value in pair.split(",")))


if __name__ == "__main__":
    unittest.main()
