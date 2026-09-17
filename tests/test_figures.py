import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from render_results import build_outputs


class FigureTests(unittest.TestCase):
    def test_overview_bar_percentages_have_consistent_outside_spacing(self):
        root = ET.parse(Path(__file__).resolve().parents[1] / "assets" / "analytics-overview.svg").getroot()
        ns = {"svg": "http://www.w3.org/2000/svg"}
        bars = [bar for bar in root.findall(".//svg:rect", ns)
                if bar.get("x") == "155" and bar.get("height") == "26"]
        self.assertEqual(len(bars), 4)
        for bar in bars:
            labels = [label for label in root.findall(".//svg:text", ns)
                      if float(label.get("y")) == float(bar.get("y")) + 19
                      and (label.text or "").endswith("%")]
            self.assertEqual(len(labels), 1)
            gap = float(labels[0].get("x")) - float(bar.get("x")) - float(bar.get("width"))
            self.assertEqual(gap, 11, f"{labels[0].text} should sit 11px beyond its bar")

    def test_source_generated_figures_have_accessible_structure(self):
        output = build_outputs()
        self.assertEqual(output, build_outputs())
        for name, text in output.items():
            if name.endswith(".svg"):
                root = ET.fromstring(text)
                self.assertEqual(root.attrib["role"], "img")
                self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}title"))
                self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}desc"))
