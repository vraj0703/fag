import ollama

from logger import logger
from config import config


class LLMApis:
    def __init__(self):
        self.embedding_model = config["models"]["embedding"]
        self.split_model = config["models"]["split"]
        self.generation_model = config["models"]["generation"]
        try:
            self.ollama_client = ollama.AsyncClient()
        except Exception as e:
            logger.fatal(f"Could not initialize Ollama client. Is Ollama running? Error: {e}")
            self.ollama_client = None

    async def embedding(self, text_chunk):
        """Generates an embedding for a given piece of text."""
        # This function is now async
        response = await self.ollama_client.embed(
            model=self.embedding_model,
            input=text_chunk
        )
        return response.embeddings

    async def split(self, prompt, file_content, format='json'):
        """Sends a prompt to the LLM for intelligent splitting."""
        if not self.ollama_client:
            logger.error("Ollama client not initialized. Cannot split file.")
            return None

        response = await self.ollama_client.chat(
            model=self.split_model,
            messages=[
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': file_content}
            ],
            # This is the key part: instruct Ollama to return JSON
            # based on the schema of our Pydantic model.
            format=format,
        )
        return response['message']['content']

    async def generate(self, prompt, format):
        """Sends a prompt to the LLM for intelligent splitting."""
        # This function is now async
        response = await self.ollama_client.chat(
            model=self.generation_model,
            messages=[
                {'role': 'user', 'content': prompt}
            ],
            # This is the key part: instruct Ollama to return JSON
            # based on the schema of our Pydantic model.
            format=format,
        )
        return response
