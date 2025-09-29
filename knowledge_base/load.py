from logger import logger
import os
import subprocess
import tempfile

from config import config


def load_from_local_path(root_path, allowed_extensions=config["allowed_extensions"]):
    """Loads all files with allowed extensions from a local directory."""
    documents = []
    logger.info(f"Loading files from local path: {root_path}...")
    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in allowed_extensions):
                full_path = os.path.join(dirpath, filename)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        documents.append({"path": full_path, "content": content})
                except Exception as e:
                    logger.warning(f"Could not read file {full_path}: {e}")
    logger.info(f"Found {len(documents)} files in {root_path}.")
    return documents


def load_from_github(repo_url, allowed_extensions=config["allowed_extensions"]):
    """Clones a GitHub repo and loads files with allowed extensions."""
    logger.info(f"Cloning github repo: {repo_url}...")
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            subprocess.run(['git', 'clone', '--depth', '1', repo_url, temp_dir], check=True, capture_output=True)
            return load_from_local_path(temp_dir, allowed_extensions)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository {repo_url}. Error: {e.stderr.decode()}")
            return []
