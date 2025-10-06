import asyncio
import json
import os
import aiofiles
from logger import logger


class FolderArchitect:
    """A utility class for asynchronously creating a directory structure from a JSON definition."""

    async def _create_directories_recursive(self, node, parent_path):
        """Recursively create folders from a JSON node."""
        # The placeholder <feature_name> should ideally be replaced before this step,
        # but we can safely ignore it for folder creation.
        current_path = os.path.join(parent_path, node["name"].replace("<feature_name>", "feature"))

        # Run the synchronous os.makedirs call in a separate thread
        await asyncio.to_thread(os.makedirs, current_path, exist_ok=True)
        logger.info(f"Directory ensured at: {current_path}")

        if "children" in node:
            tasks = [self._create_directories_recursive(child, current_path) for child in node["children"]]
            await asyncio.gather(*tasks)

    async def architect_folder(self, json_file: str, base_path: str = "."):
        """
        Asynchronously reads a JSON file and creates the defined folder structure
        starting from a given base path.

        Args:
            json_file (str): The path to the JSON file defining the folder structure.
            base_path (str): The root directory where the structure should be created.
                             Defaults to the current directory.
        """
        logger.info(f"Architecting folders from '{json_file}' into base path '{base_path}'...")
        try:
            async with aiofiles.open(json_file, "r", encoding="utf-8") as f:
                content = await f.read()
                structure = json.loads(content)

            # Create the root directory of the structure (e.g., 'lib' or 'assets')
            # inside the base_path.
            root_path = os.path.join(base_path, structure["name"])
            await asyncio.to_thread(os.makedirs, root_path, exist_ok=True)
            logger.info(f"Directory ensured at: {root_path}")

            # Create all children inside the new root path
            if "children" in structure:
                tasks = [self._create_directories_recursive(child, root_path) for child in structure["children"]]
                await asyncio.gather(*tasks)

            return {"status": "success"}

        except FileNotFoundError:
            logger.error(f"Architecture JSON file not found at: {json_file}")
            return {"status": "error", "message": "JSON file not found"}
        except Exception as e:
            logger.error(f"Failed to architect folders: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
