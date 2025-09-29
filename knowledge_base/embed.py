from llm_apis.apis import llm_apis
from logger import logger


async def generate_embedding(text_chunk):
    """
    Generates an embedding for a given piece of text using Ollama.
    """
    try:
        return await llm_apis.embedding(text_chunk)
    except Exception as e:
        # Avoid flooding logs for very small chunks that might fail
        log_chunk = text_chunk[:70].replace('\n', ' ') + '...' if len(text_chunk) > 70 else text_chunk.replace('\n',
                                                                                                               ' ')
        logger.error(f"Failed to generate embedding for chunk: '{log_chunk}': {e}")
        return None