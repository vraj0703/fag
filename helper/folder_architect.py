import json
import os
from pathlib import Path


class FolderArchitect:
    def create_directories(self, node, parent_path=""):
        """Recursively create only folders from JSON structure."""
        current_path = os.path.join(parent_path, node["name"])
        os.makedirs(current_path, exist_ok=True)
        print(f"Created folder: {current_path}")

        if "children" in node:
            for child in node["children"]:
                self.create_directories(child, current_path)

    def architect_folder(self, json_file):
        # Load JSON from local file
        with open(json_file, "r", encoding="utf-8") as f:
            structure = json.load(f)

        # Base directory = where the command is run
        base_dir = os.getcwd()

        # Iterate through the list at root
        for node in structure["children"]:
            self.create_directories(node, base_dir)


if __name__ == "__main__":
    FolderArchitect().architect_folder(Path(__file__).parent.parent / "json" / "app_folder_structure.json")
