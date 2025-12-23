from .base import DataDownloader
from typing import Optional, Dict

class SpatialDownloader(DataDownloader):
    """
    Interface for spatial data engines. Adds Bounding Box (BBOX) support.
    """
    def __init__(self, dataset_name: str):
        super().__init__(dataset_name)
        self.bbox: Optional[Dict[str, float]] = None

    def set_bbox(self, south: float, west: float, north: float, east: float) -> None:
        """Sets the geographic extent (Decimal Degrees)."""
        self.bbox = {
            'south': south,
            'west': west,
            'north': north,
            'east': east
        }

    def download(self) -> str:
        """Abstract method to be implemented by specific API strategies."""
        raise NotImplementedError("Subclasses must implement download()")