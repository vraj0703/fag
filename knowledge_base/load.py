import asyncio

import aiofiles

from logger import logger
import os
import subprocess
import tempfile

from config import config


async def load_from_local_path(root_path, allowed_extensions=None):
    """Asynchronously load all files with allowed extensions from a local directory."""
    if allowed_extensions is None:
        allowed_extensions = config["allowed_extensions"]

    documents = []
    logger.info(f"Loading files from local path: {root_path}...")

    tasks = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for filename in filenames:
            if any(filename.endswith(ext) for ext in allowed_extensions):
                full_path = os.path.join(dirpath, filename)

                async def read_file(path=full_path):  # default arg avoids late binding
                    try:
                        async with aiofiles.open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = await f.read()
                            return {"path": path, "content": content}
                    except Exception as e:
                        logger.warning(f"Could not read file {path}: {e}")
                        return None

                tasks.append(read_file())

    results = await asyncio.gather(*tasks, return_exceptions=False)
    documents = [doc for doc in results if doc]

    logger.info(f"Found {len(documents)} files in {root_path}.")
    return documents


async def load_from_github(repo_url, allowed_extensions=config["allowed_extensions"]):
    """Clones a GitHub repo and loads files with allowed extensions."""
    logger.info(f"Cloning github repo: {repo_url}...")
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            proc = await asyncio.create_subprocess_exec(
                'git', 'clone', '--depth', '1', repo_url, temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.error(f"Failed to clone repository {repo_url}. Error: {stderr.decode()}")
                return []
            return await load_from_local_path(temp_dir, allowed_extensions)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository {repo_url}. Error: {e.stderr.decode()}")
            return []


async def crawl_folder(root_path, allowed_extensions=config["allowed_extensions"]):
    string = ""
    documents = await load_from_local_path(root_path, allowed_extensions)
    for document in documents:
        string += "--------------------------------"
        string += f"{document["path"]}"
        string += "--------------------------------"
        string += document["content"]
        string += "--------------------------------"
    print(string)
    return string
