from ruamel.yaml import YAML
from pathlib import Path

from ruamel.yaml.scalarstring import DoubleQuotedScalarString


class YamlEditor:
    def add_item(self, file_path: str, key_path: str, value):
        """
        Add an item to a list in a YAML file under the specified key.

        Args:
            file_path (str): Path to the YAML file.
            key_path (str): Key under which the list exists or should be created.
            value: Item to add to the list (can be str, int, dict, etc.).
        """

        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.preserve_quotes = True

        path = Path(file_path)

        # Ensure file exists
        data = {}
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.load(f) or {}

        # Traverse or create nested dicts
        keys = key_path.split(".")
        node = data
        for k in keys[:-1]:
            if k not in node or not isinstance(node[k], dict):
                node[k] = {}
            node = node[k]

        final_key = keys[-1]
        if final_key not in node or not isinstance(node[final_key], list):
            node[final_key] = []

        # Ensure string is double-quoted
        if isinstance(value, str):
            value = DoubleQuotedScalarString(value)

        if value not in node[final_key]:
            node[final_key].append(value)

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)

        print(f'✅ Added "{value}" to key "{key_path}" in {file_path}')


if __name__ == "__main__":
    # Example usage
    yaml_file = "C:/Users/vraj0/IdeaProjects/fag_2/config/pubspec.yaml"
    editor = YamlEditor()
    editor.add_item(yaml_file, "flutter.assets", "images/a_dot_burr.jpeg")
