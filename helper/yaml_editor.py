import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from logger import logger


class YamlEditor:
    """An asynchronous utility class for safely editing YAML files."""

    async def add_item(self, file_path: str, key_path: str, value: any):
        """
        Asynchronously adds a single item to a list in a YAML file under a specified key.
        This operation is non-blocking.

        Args:
            file_path (str): Path to the YAML file.
            key_path (str): Dot-separated path to the key (e.g., 'flutter.assets').
            value: The item to add to the list.
        """
        try:
            await asyncio.to_thread(
                self._sync_add_item, file_path, key_path, value
            )
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Failed to add item to YAML file {file_path}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def _sync_add_item(self, file_path: str, key_path: str, value: any):
        """The synchronous, blocking portion of the single-item YAML editing logic."""
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.preserve_quotes = True
        path = Path(file_path)

        data = self._load_yaml_data(path, yaml)
        node = self._traverse_to_node(data, key_path)

        final_key = key_path.split('.')[-1]
        if final_key not in node or not isinstance(node[final_key], list):
            node[final_key] = []

        if isinstance(value, str):
            value = DoubleQuotedScalarString(value)

        if value not in node[final_key]:
            node[final_key].append(value)

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)

        logger.info(f'Added "{value}" to key "{key_path}" in {file_path}')

    async def add_asset_dirs_from_json(self, pubspec_path: str, json_path: str, key_path: str):
        """
        Asynchronously reads a folder structure JSON, generates asset directory paths,
        and adds them to a list in a YAML file (e.g., pubspec.yaml).

        Args:
            pubspec_path (str): Path to the target YAML file (e.g., 'pubspec.yaml').
            json_path (str): Path to the JSON file defining the folder structure.
            key_path (str): Dot-separated path to the key (e.g., 'flutter.assets').
        """
        try:
            await asyncio.to_thread(
                self._sync_add_asset_dirs, pubspec_path, json_path, key_path
            )
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Failed to add asset directories to YAML file {pubspec_path}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def _sync_add_asset_dirs(self, pubspec_path: str, json_path: str, key_path: str):
        """The synchronous logic for adding multiple asset directories from a JSON source."""
        # 1. Load the source JSON for the folder structure
        with open(json_path, 'r', encoding='utf-8') as f:
            structure = json.load(f)

        asset_root = structure.get("name")
        if not asset_root:
            raise ValueError("JSON structure must have a root 'name' key (e.g., 'assets').")

        # 2. Generate the list of directory paths, including the root and all subdirectories.
        asset_paths = [f"{asset_root}/"]  # Start with the root asset directory
        asset_paths.extend([f"{asset_root}/{child['name']}/" for child in structure.get("children", [])])
        logger.info(f"Generated {len(asset_paths)} asset paths from {json_path}")

        # 3. Load the target YAML file
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.preserve_quotes = True
        path = Path(pubspec_path)
        data = self._load_yaml_data(path, yaml)

        # 4. Traverse to the target node
        node = self._traverse_to_node(data, key_path)
        final_key = key_path.split('.')[-1]
        if final_key not in node or not isinstance(node[final_key], list):
            node[final_key] = []

        # 5. Add each generated path to the list if it doesn't already exist
        for asset_path in asset_paths:
            quoted_path = DoubleQuotedScalarString(asset_path)
            if quoted_path not in node[final_key]:
                node[final_key].append(quoted_path)

        # 6. Write the updated data back to the file
        with open(pubspec_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)

        logger.info(f"Updated assets in {pubspec_path}")

    def _load_yaml_data(self, path: Path, yaml: YAML) -> dict:
        """Helper to load YAML data from a file."""
        data = {}
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.load(f) or {}
        return data

    def _traverse_to_node(self, data: dict, key_path: str) -> dict:
        """Helper to traverse a dictionary using a dot-separated path."""
        keys = key_path.split(".")
        node = data
        for k in keys[:-1]:
            if k not in node or not isinstance(node[k], dict):
                node[k] = {}
            node = node[k]
        return node

    async def add_font_families_from_list(self, file_path: str, key_path: str, font_families_list: List[Dict[str, Any]]):
        """
        Asynchronously adds a list of font families to a YAML file, transforming
        the input structure to the required pubspec.yaml format.
        """
        try:
            await asyncio.to_thread(
                self._sync_add_font_families, file_path, key_path, font_families_list
            )
            return {'status': 'success'}
        except Exception as e:
            logger.error(f'Failed to add font families to YAML file {file_path}: {e}', exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def _sync_add_font_families(self, file_path: str, key_path: str, font_families_list: List[Dict[str, Any]]):
        """The synchronous logic for transforming and adding font families."""
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        path = Path(file_path)

        data = {}
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.load(f) or {}
        else:
            path.parent.mkdir(parents=True, exist_ok=True)

        keys = key_path.split('.')
        node = data
        for k in keys[:-1]:
            node = node.setdefault(k, {})

        final_key = keys[-1]
        font_list_in_yaml = node.setdefault(final_key, [])

        # Create a set of existing family names for quick lookup
        existing_families = {f['family'] for f in font_list_in_yaml if 'family' in f}

        for font_family in font_families_list:
            family_name = font_family.get('family')
            if not family_name or family_name in existing_families:
                logger.warning(f"Skipping duplicate or invalid font family: '{family_name}'")
                continue

            # Transform the 'fonts' list from simple strings to dictionaries with an 'asset' key
            transformed_fonts = [{'asset': path} for path in font_family.get('fonts', [])]

            new_font_entry = {
                'family': family_name,
                'fonts': transformed_fonts
            }

            font_list_in_yaml.append(new_font_entry)
            existing_families.add(family_name)
            logger.info(f"Prepared font family '{family_name}' for inclusion in {file_path}")

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
        logger.info(f'Successfully updated font families under key "{key_path}" in {file_path}')



if __name__ == "__main__":
    # Example usage
    yaml_file = "C:/Users/vraj0/IdeaProjects/fag_2/config/pubspec.yaml"
    editor = YamlEditor()
    editor.add_item(yaml_file, "flutter.assets", "images/a_dot_burr.jpeg")
