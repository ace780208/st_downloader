import unittest
import os
import json
import shutil
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from st_downloader.engines.osm import OSMEngine

class TestOSMEngine(unittest.TestCase):
    """
    Unit tests for OSMEngine using Westfield UTC (San Diego) boundaries.
    """

    def setUp(self) -> None:
        """Set up test environment with Westfield UTC coordinates."""
        self.dataset_name: str = "test_utc_unit"
        self.test_dir: str = "./test_downloads"
        self.engine: OSMEngine = OSMEngine(self.dataset_name)
        self.engine.set_target_directory(self.test_dir)
        # Westfield UTC BBox
        self.engine.set_bbox(32.8680, -117.2150, 32.8750, -117.2080)

    def tearDown(self) -> None:
        """Clean up the temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_osm_to_geojson(self) -> None:
        """
        Comprehensive test for UTC features: Node, Way, Multipolygon, 
        Boundary, Route, and Restriction.
        """
        osm_content: str = """<?xml version="1.0" encoding="UTF-8"?>
        <osm version="0.6" generator="Overpass API 0.7.62.8 e802775f">
        <note>The data included in this document is from www.openstreetmap.org. The data is made available under ODbL.</note>
        <meta osm_base="2025-12-21T23:30:31Z"/>
        <bounds minlat="32.8680000" minlon="-117.2150000" maxlat="32.8750000" maxlon="-117.2080000"/>

        <node id="1" lat="32.8715" lon="-117.2110" version="1" timestamp="2025-01-01T00:00:00Z">
            <tag k="name" v="UTC Transit Center"/>
        </node>
        <node id="2" lat="32.8720" lon="-117.2120" version="1"/>
        <node id="3" lat="32.8730" lon="-117.2120" version="1"/>
        <node id="4" lat="32.8730" lon="-117.2110" version="1"/>
        <node id="5" lat="32.8725" lon="-117.2115" version="1"/>

        <way id="10" version="1">
            <nd ref="2"/>
            <nd ref="3"/>
            <tag k="highway" v="primary"/>
            <tag k="name" v="Genesee Ave"/>
        </way>

        <way id="11" version="1">
            <nd ref="1"/>
            <nd ref="2"/>
            <nd ref="3"/>
            <nd ref="4"/>
            <nd ref="1"/>
            <tag k="building" v="retail"/>
        </way>

        <way id="12" version="1">
            <nd ref="5"/>
            <nd ref="2"/>
            <nd ref="3"/>
            <nd ref="5"/>
        </way>

        <relation id="100" version="1">
            <member type="way" ref="11" role="outer"/>
            <member type="way" ref="12" role="inner"/>
            <tag k="type" v="multipolygon"/>
            <tag k="amenity" v="marketplace"/>
        </relation>

        <relation id="200" version="1">
            <member type="way" ref="11" role="outer"/>
            <tag k="type" v="boundary"/>
            <tag k="boundary" v="parking"/>
            <tag k="name" v="UTC Parking South"/>
        </relation>

        <relation id="300" version="1">
            <member type="way" ref="10" role="track"/>
            <member type="node" ref="1" role="stop"/>
            <tag k="type" v="route"/>
            <tag k="route" v="bus"/>
            <tag k="ref" v="201"/>
        </relation>

        <relation id="400" version="1">
            <member type="way" ref="10" role="from"/>
            <member type="node" ref="5" role="via"/>
            <tag k="type" v="restriction"/>
            <tag k="restriction" v="no_left_turn"/>
        </relation>
        </osm>"""
        input_path = os.path.join(self.test_dir, "utc_full.osm")
        output_path = os.path.join(self.test_dir, "utc_full.geojson")
        
        with open(input_path, "w", encoding="utf-8") as f:
            f.write(osm_content)

        self.engine.osm_to_geojson(output_path, input_path)

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        features = data["features"]

        # Assertions to confirm all logic paths were executed
        # 1. Multipolygon logic check
        print("Found properties:", [f["properties"] for f in features])
        mall = next(f for f in features if f["properties"].get("amenity") == "marketplace")
        self.assertEqual(len(mall["geometry"]["coordinates"][0]), 2) 

        # 2. Route member tag check
        bus_stop = next(f for f in features if f["properties"].get("rel_role") == "stop")
        self.assertEqual(bus_stop["properties"]["ref"], "201")

        # 3. Restriction check
        # Find the restriction members specifically by their roles
        restriction_features = [f for f in features if f["properties"].get("restriction") == "no_left_turn"]
        
        # Get the "via" point
        no_left_via = next(f for f in restriction_features if f["properties"].get("rel_role") == "via")
        self.assertEqual(no_left_via["geometry"]["type"], "Point")
        self.assertEqual(no_left_via["properties"]["osm_id"], "400")

        # Get the "from" line
        no_left_from = next(f for f in restriction_features if f["properties"].get("rel_role") == "from")
        self.assertEqual(no_left_from["geometry"]["type"], "LineString")

    @patch('urllib.request.urlopen')
    def test_download_trigger(self, mock_urlopen: MagicMock) -> None:
        """Verifies the engine builds the specific Overpass map URL using built-ins."""
        # 1. Setup the mock response for urllib
        # urllib returns a context manager that has a read/stream interface
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        # To simulate data for shutil.copyfileobj, we need a 'read' method
        mock_response.read.side_effect = [b"<osm></osm>", b""] 
        mock_urlopen.return_value = mock_response

        # 2. Run the download
        self.engine.download()
        
        # 3. Verify the call
        # urllib.request.urlopen(req) is called with a Request object
        args, _ = mock_urlopen.call_args
        request_obj = args[0]
        
        # Extract the URL from the Request object
        actual_url = request_obj.full_url if hasattr(request_obj, 'full_url') else request_obj
        
        self.assertIn("overpass-api.de/api/map", actual_url)
        self.assertIn("bbox=-117.215", actual_url)

if __name__ == '__main__':
    unittest.main()