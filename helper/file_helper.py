import aiofiles
import os
from logger import logger


class FileHelper:
    """A utility class for asynchronous file and directory operations."""

    async def create_directory(self, path: str):
        """Asynchronously creates a directory if it doesn't exist."""
        try:
            os.makedirs(path, exist_ok=True)
            logger.info(f"Directory ensured at: {path}")
            return True
        except OSError as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False

    async def write_file(self, file_path: str, content: str):
        """Asynchronously writes content to a file, creating parent directories if needed."""
        try:
            parent_dir = os.path.dirname(file_path)
            if not os.path.exists(parent_dir):
                await self.create_directory(parent_dir)

            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            logger.info(f"Successfully wrote content to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write to file {file_path}: {e}")
            return False
