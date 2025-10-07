import json
from typing import Dict

import aiofiles
import os
import asyncio
from logger import logger


class FileHelper:
    """A utility class for asynchronous file and directory operations."""

    async def _create_directory(self, path: str):
        """Asynchronously creates a directory if it doesn't exist, in a non-blocking way."""
        try:
            # os.makedirs is a blocking call, so run it in a thread
            await asyncio.to_thread(os.makedirs, path, exist_ok=True)
            logger.info(f"Directory ensured at: {path}")
            return True
        except OSError as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False

    async def write_file(self, file_path: str, content: str) -> bool:
        """Asynchronously writes content to a file, creating parent directories if needed."""
        try:
            content_to_write = content
            if isinstance(content, (dict, list)):
                # Use json.dumps for proper JSON formatting (double quotes)
                content_to_write = json.dumps(content, indent=2)

            parent_dir = os.path.dirname(file_path)
            if not os.path.exists(parent_dir):
                await self._create_directory(parent_dir)

            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content_to_write)
            logger.info(f"Successfully wrote content to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write to file {file_path}: {e}")
            return False

    async def read_file(self, file_path: str) -> str | None:
        """Asynchronously reads the content of a file."""
        logger.info(f"Reading file: {file_path}")
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None

    async def copy_file(self, source_path: str, destination_path: str) -> bool:
        """
        Asynchronously copies the content of a source file to a destination file.
        It will create the destination file and any necessary parent directories.
        """
        logger.info(f"Copying content from '{source_path}' to '{destination_path}'...")
        # 1. Read the content from the source file.
        content = await self.read_file(source_path)

        if content is None:
            logger.error(f"Copy failed because source file could not be read: {source_path}")
            return False

        # 2. Write the retrieved content to the destination file.
        #    The write_file method handles the creation of the file and directories.
        return await self.write_file(destination_path, content)

    async def copy_multiple_files(self, files_map: Dict[str, str]) -> Dict:
        # ... (implementation remains the same)
        logger.info(f'Starting to copy {len(files_map)} files...')
        tasks = [self.copy_file(source, dest) for source, dest in files_map.items()]
        results = await asyncio.gather(*tasks)
        failed_files = [source for (source, _), success in zip(files_map.items(), results) if not success]
        if failed_files:
            logger.error(f'Failed to copy the following files: {failed_files}')
            return {'status': 'error', 'message': 'Some files failed to copy.', 'failed_files': failed_files}
        logger.info('All files copied successfully.')
        return {'status': 'success'}

    async def copy_directory_contents(self, source_dir: str, destination_dir: str) -> Dict:
        """
        Asynchronously copies all files from a source directory to a destination directory.

        Args:
            source_dir (str): The directory to copy files from.
            destination_dir (str): The directory to copy files to.
        """
        logger.info(f"Preparing to copy contents from '{source_dir}' to '{destination_dir}'...")
        if not os.path.isdir(source_dir):
            message = f"Source '{source_dir}' is not a valid directory."
            logger.error(message)
            return {'status': 'error', 'message': message}

        files_map = {}
        for root, _, files in os.walk(source_dir):
            for filename in files:
                source_path = os.path.join(root, filename)
                # Create a relative path to maintain the folder structure
                relative_path = os.path.relpath(source_path, source_dir)
                destination_path = os.path.join(destination_dir, relative_path)
                files_map[source_path] = destination_path

        if not files_map:
            logger.warning(f"No files found to copy in '{source_dir}'.")
            return {'status': 'success', 'message': 'No files found to copy.'}

        # Reuse the existing copy_multiple_files method
        return await self.copy_multiple_files(files_map)
