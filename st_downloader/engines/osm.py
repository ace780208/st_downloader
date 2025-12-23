import xml.etree.ElementTree as ET
import json
import logging
import os
import time
from typing import Dict, List, Any, Optional

from ..spatial import SpatialDownloader

logger = logging.getLogger(__name__)

class OSMEngine(SpatialDownloader):
    """
    OpenStreetMap (OSM) data acquisition and processing engine.
    
    Implements the Strategy Pattern to download raw OSM XML via the Overpass API
    and convert it into GeoJSON using an optimized, memory-efficient parser.
    """

    def download(self) -> str:
        """
        Downloads data using the direct OSM 'map' endpoint via a GET request.
        We manually construct the URL to prevent double-encoding of commas
        and to ensure urllib uses GET instead of POST.
        """
        if not self.bbox:
            raise ValueError("BBOX must be set. Use set_bbox().")

        # 1. Manually format the bbox string (West,South,East,North)
        # This ensures we get literal commas: "-117.215,32.868,..."
        bbox_str = (
            f"{self.bbox['west']},"
            f"{self.bbox['south']},"
            f"{self.bbox['east']},"
            f"{self.bbox['north']}"
        )
        
        # 2. Construct the FULL URL manually
        # This bypasses urllib's urlencode, ensuring the commas stay as commas.
        # We use the Overpass mirror which you verified works manually.
        base_url = "https://overpass-api.de/api/map"
        full_url = f"{base_url}?bbox={bbox_str}"
        
        filename = f"{self.dataset_name}.osm"
        
        # 3. Call execute WITHOUT params
        # Passing params=None (or ignoring it) ensures _execute_download 
        # does NOT attach a body, which forces urllib to send a GET request.
        return self._execute_download(full_url, filename)
    
    def osm_to_geojson(self, output_path: str, input_path: str) -> None:
        """
        Converts OpenStreetMap XML data to GeoJSON format using memory-efficient streaming.

        This function parses nodes, ways, and relations (multipolygon, boundary, route, 
        and restrictions). It uses ET.iterparse to handle large XML files by clearing 
        elements from memory after processing.

        Args:
            output_path (str): The file path where the resulting GeoJSON will be saved.
            input_path (str): The file path of the source .osm (XML) file.

        Returns:
            None
        """
        start_time = time.time()
        
        # Using iterparse for memory efficiency
        context = ET.iterparse(input_path, events=("start", "end"))
        
        nodes: Dict[str, List[float]] = {}
        ways: Dict[str, Dict[str, Any]] = {}
        features: List[Dict[str, Any]] = []
        
        # Temporary storage for child elements as we stream
        current_tags: Dict[str, str] = {}
        current_refs: List[str] = []
        current_members: List[Dict[str, str]] = []

        for event, elem in context:
            if event == "start":
                # Reset temporary storage when a new primary element begins
                if elem.tag in ["node", "way", "relation"]:
                    current_tags = {}
                    current_refs = []
                    current_members = []
                continue

            # Processing "end" events to ensure child tags are fully loaded
            if elem.tag == "tag":
                current_tags[elem.get("k")] = elem.get("v")
            
            elif elem.tag == "nd":
                current_refs.append(elem.get("ref"))
                
            elif elem.tag == "member":
                current_members.append({
                    "type": elem.get("type"),
                    "ref": elem.get("ref"),
                    "role": elem.get("role")
                })

            elif elem.tag == "node":
                n_id = elem.get("id")
                lon, lat = float(elem.get("lon")), float(elem.get("lat"))
                nodes[n_id] = [lon, lat]
                
                if current_tags:
                    features.append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {**current_tags, "osm_id": n_id}
                    })
                elem.clear() 

            elif elem.tag == "way":
                w_id = elem.get("id")
                coords = [nodes[r] for r in current_refs if r in nodes]
                ways[w_id] = {"coords": coords, "tags": current_tags.copy()}
                
                if current_tags:
                    # GeoJSON Polygon: first and last node must match
                    is_polygon = coords[0] == coords[-1] if len(coords) > 1 else False
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon" if is_polygon else "LineString",
                            "coordinates": [coords] if is_polygon else coords
                        },
                        "properties": {**current_tags, "osm_id": w_id}
                    })
                elem.clear()

            elif elem.tag == "relation":
                r_id = elem.get("id")
                rel_type = current_tags.get("type")

                if rel_type in ["multipolygon", "boundary"]:
                    outer = [ways[m["ref"]]["coords"] for m in current_members if m["role"] == "outer" and m["ref"] in ways]
                    inner = [ways[m["ref"]]["coords"] for m in current_members if m["role"] == "inner" and m["ref"] in ways]
                    if outer:
                        features.append({
                            "type": "Feature",
                            "geometry": {"type": "MultiPolygon", "coordinates": [outer + inner]},
                            "properties": {**current_tags, "osm_id": r_id}
                        })
                
                elif rel_type in ["route", "restriction"]:
                    for m in current_members:
                        props = {**current_tags, "rel_role": m["role"], "osm_id": r_id}
                        if m["type"] == "node" and m["ref"] in nodes:
                            features.append({
                                "type": "Feature",
                                "geometry": {"type": "Point", "coordinates": nodes[m["ref"]]},
                                "properties": props
                            })
                        elif m["type"] == "way" and m["ref"] in ways:
                            features.append({
                                "type": "Feature",
                                "geometry": {"type": "LineString", "coordinates": ways[m["ref"]]["coords"]},
                                "properties": props
                            })
                elem.clear()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)
            
        end_time = time.time()
        print(f"Conversion completed in {end_time - start_time:.4f} seconds.")

    def run(self) -> None:
        """High-level orchestrator: Downloads then converts."""
        raw_path = self.download()
        geojson_path = os.path.join(self.target_dir, f"{self.dataset_name}.geojson")
        self.osm_to_geojson(geojson_path, raw_path)