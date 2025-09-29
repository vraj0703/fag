import json

import ollama
import requests

from config import config
from logger import logger


class LLMApis:
    def split(self, prompt, model_name=config["models"]["split"]):
        try:
            return requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            )
        except requests.RequestException as e:
            logger.error(f"API request failed for prompt {prompt}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for prompt {prompt}: {e}")
            return None

    def embedding(self, text_chunk, model_name=config["models"]["embedding"]):
        try:
            response = ollama.embeddings(
                model=model_name,
                prompt=text_chunk
            )
            return response['embedding']
        except requests.RequestException as e:
            logger.error(f"Embed request failed for text_chunk {text_chunk}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Embed to parse JSON response for text_chunk {text_chunk}: {e}")
            return None
