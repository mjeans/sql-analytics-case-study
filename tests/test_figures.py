import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from render_results import build_outputs


class FigureTests(unittest.TestCase):
    def test_source_generated_figures_have_accessible_structure(self):
        output = build_outputs()
        self.assertEqual(output, build_outputs())
        for name, text in output.items():
            if name.endswith(".svg"):
                root = ET.fromstring(text)
                self.assertEqual(root.attrib["role"], "img")
                self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}title"))
                self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}desc"))
