'''
import os
import logging
import requests
import shutil
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DataDownloader:
    """
    Base class for all data acquisition. Handles file I/O and HTTP streaming.
    
    Attributes:
        dataset_name (str): The unique identifier for the dataset.
        target_dir (str): The local directory where files will be saved.
    """
    def __init__(self, dataset_name: str):
        self.dataset_name: str = dataset_name
        self.target_dir: str = "./downloads"
        
    def set_target_directory(self, path: str) -> None:
        """Sets and creates the output directory."""
        self.target_dir = path
        os.makedirs(self.target_dir, exist_ok=True)

    def _execute_download(self, url: str, filename: str) -> str:
        """
        Executes a GET request using the requests library.
        """
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)

        out_path = os.path.join(self.target_dir, filename)

        # Using stream=True to handle the file download efficiently without loading it all into RAM
        with requests.get(url, stream=True) as r:
            # Check if the API returned an error (like Area Too Large)
            r.raise_for_status()
            
            with open(out_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        return out_path
'''    
    
import os
import urllib.request
import shutil
from typing import Optional

class DataDownloader:
    def __init__(self, dataset_name: str):
        self.dataset_name = dataset_name
        self.target_dir = "./downloads"
        
    def set_target_directory(self, path: str) -> None:
        """Sets and creates the output directory."""
        self.target_dir = path
        os.makedirs(self.target_dir, exist_ok=True)

    def _execute_download(self, url: str, filename: str) -> str:
        """
        Executes a GET request using only Python built-in libraries.
        Uses streaming to prevent memory exhaustion from large files.
        """
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)

        out_path = os.path.join(self.target_dir, filename)

        # OSM servers require a User-Agent to identify the script
        headers = {
            'User-Agent': 'ST-Downloader/1.0 (Built-in Only)'
        }
        
        req = urllib.request.Request(url, headers=headers)
        print(req)

        try:
            # urlopen() starts the connection without downloading the whole body
            with urllib.request.urlopen(req) as response:
                # Open the local file for binary writing
                with open(out_path, 'wb') as out_file:
                    # copyfileobj streams data in chunks (default 16kb)
                    # This is safe even if the file is 10GB
                    shutil.copyfileobj(response, out_file)
        except Exception as e:
            print(f"Error during download: {e}")
            raise

        return out_path