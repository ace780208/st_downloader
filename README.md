# st_downloader

A lightweight, **zero-dependency** Python package for downloading and processing spatial-temporal data.

## 🚀 Purpose
`st_downloader` provides a robust engine for fetching OpenStreetMap (OSM) data and converting it to GeoJSON using **only Python built-in libraries**. By avoiding third-party dependencies like `requests`, `GDAL`, or `Shapely`, this package ensures maximum portability and security for use in restricted environments, cloud functions, or lightweight containers.

## ✨ Key Features
* **Zero Dependencies:** Powered strictly by `urllib`, `xml.etree`, `shutil`, and `json`. No `pip install` required.
* **Strict BBOX Clipping:** Optimized for the Overpass API `/map` endpoint to ensure precise spatial filtering and small file sizes, preventing massive data downloads.
* **Memory Efficient:** Uses event-driven stream parsing (`ET.iterparse`) to process large XML files without high RAM consumption.
* **Rich Geometry Support:** * **Nodes:** Point features with associated tags.
    * **Ways:** Automatic detection and handling of `LineString` vs. `Polygon` (closed-loop detection).
    * **Relations:** Advanced processing for `multipolygon` (with holes), `boundary`, `route`, and `restriction` types.

---

## 📂 Project Structure
```text
st_downloader/
├── st_downloader/       # Core package
│   ├── base.py          # Built-in network logic (urllib)
│   ├── spatial.py       # Spatial base classes
│   └── engines/
│       └── osm.py       # OSM-specific logic and GeoJSON parser
├── tests/               # Unit tests (Mock-based)
│   └── test_osm.py
└── README.md
```
---
## 📖 Usage
This package is designed to be imported into your existing Python workflows. Below is the standard implementation for downloading and converting data:

<pre>
```Python

from st_downloader.engines.osm import OSMEngine

# 1. Initialize engine
engine = OSMEngine(dataset_name="my_area_data")

# 2. Set the bounding box (West, South, East, North)
# Example: UTC San Diego Area
engine.set_bbox(west=-117.215, south=32.868, east=-117.208, north=32.875)

# 3. Download .osm file using built-in streaming (urllib/shutil)
# This will save the file to ./downloads/my_area_data.osm
osm_path = engine.download()

# 4. Convert to GeoJSON
# This uses ET.iterparse to maintain a low memory footprint
engine.osm_to_geojson("output.geojson", osm_path)
```
</pre>
---
##🧪 Testing
The package includes a test suite that verifies the parsing logic and network triggers using mocks. No internet connection is required to run tests.

<pre>
```Bash

python -m unittest tests.test_osm
```
</pre>
---
## 🏗 Implementation Details
Streaming IO: Uses shutil.copyfileobj to pipe data from the web response directly to the disk, preventing memory crashes regardless of file size.

Event-Based Parsing: The osm_to_geojson function processes XML elements one by one, clearing them from memory immediately after they are used.

User-Agent Management: Includes a default header to ensure compatibility with Overpass API security policies.

## 📜 License
Available under the MIT License.