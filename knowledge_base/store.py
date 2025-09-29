import numpy as np
from embed import generate_embedding

import faiss
from logger import logger


class StoreBase:
    def __init__(self):
        """
        A synchronous and lightweight initializer.
        It does NOT perform any I/O or slow operations.
        """
        self.documents = []
        self.dimension = None
        self.index: faiss.IndexFlatL2 | None = None
        logger.info("StoreBase instance created. Call 'await StoreBase.create()' to initialize.")

    async def _async_init(self):
        """
        A private async method to handle the slow initialization parts.
        """
        try:
            logger.info("Asynchronously initializing the vector store...")
            # Await the async call to generate a sample embedding
            sample_embedding = await generate_embedding("test")

            if sample_embedding is None:
                raise ValueError("Could not generate sample embedding.")

            self.dimension = len(sample_embedding)
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"Vector store initialized with dimension {self.dimension}.")
        except Exception as e:
            logger.error(
                f"FATAL: Could not initialize vector store. Is Ollama running and the model installed? Error: {e}")
            # Re-raise the exception to be handled by the caller
            raise

    async def add_document(self, doc_content, doc_path):
        """Generates embedding for a doc and adds it to the index."""
        embedding = await generate_embedding(doc_content)
        if embedding:
            vector = np.array([embedding]).astype('float32')
            self.index.add(vector)
            self.documents.append({"path": doc_path, "content": doc_content})

    async def search(self, query, k=5):
        """Searches for the k most similar documents to a query."""
        query_embedding = await generate_embedding(query)
        if query_embedding and self.index.ntotal > 0:
            vector = np.array([query_embedding]).astype('float32')
            # Ensure k is not greater than the number of items in the index
            k = min(k, self.index.ntotal)
            distances, indices = self.index.search(vector, k)
            return [self.documents[i] for i in indices[0]]
        return []

    @classmethod
    async def create(cls):
        """
        The async factory method. This is the new entry point for creating
        a fully initialized StoreBase object.
        """
        # 1. Create the instance synchronously
        instance = cls()
        # 2. Perform the async initialization
        await instance._async_init()
        # 3. Return the fully initialized instance
        return instance
