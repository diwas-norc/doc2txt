import logging
import tempfile
from pathlib import Path
from typing import List, Generator
import shutil

logger = logging.getLogger(__name__)

class TempStorageClient:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "doc2txt_storage"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using temporary directory at: {self.temp_dir}")

    def _get_file_path(self, file_name: str) -> Path:
        return self.temp_dir / file_name

    def upload_file(self, file_name: str, data: bytes, overwrite: bool = True) -> str:
        file_path = self._get_file_path(file_name)
        
        if file_path.exists() and not overwrite:
            raise FileExistsError(f"File {file_name} already exists")

        # Ensure the parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the data to the file
        with open(file_path, 'wb') as f:
            f.write(data)
        
        return str(file_path)

    def download_file(self, file_name: str) -> bytes:
        file_path = self._get_file_path(file_name)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_name} not found")

        with open(file_path, 'rb') as f:
            return f.read()

    def delete_file(self, file_name: str):
        file_path = self._get_file_path(file_name)
        
        if file_path.exists():
            file_path.unlink()
        
        # If the parent directory is empty, remove it too
        parent_dir = file_path.parent
        if parent_dir != self.temp_dir and not any(parent_dir.iterdir()):
            parent_dir.rmdir()

    def list_files(self, prefix: str = None) -> Generator[str, None, None]:
        if prefix:
            search_path = self.temp_dir / prefix
            search_dir = search_path.parent
        else:
            search_dir = self.temp_dir

        if search_dir.exists():
            for file_path in search_dir.rglob('*'):
                if file_path.is_file():
                    yield str(file_path.relative_to(self.temp_dir))

    def get_file_path(self, file_name: str) -> str:
        """Returns the full path to the file in the temporary directory"""
        return str(self._get_file_path(file_name))

    def cleanup(self):
        """Cleans up all temporary files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir) 