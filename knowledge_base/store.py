import faiss
import numpy as np
import logging
import sys

from embed import generate_embedding


class StoreBase:
    def __init__(self):
        self.documents = []
        try:
            logging.info("Initializing KnowledgeBase...")
            sample_embedding = generate_embedding("test")
            if sample_embedding is None:
                raise ValueError("Could not generate sample embedding.")
            self.dimension = len(sample_embedding)
            self.index = faiss.IndexFlatL2(self.dimension)
            logging.info(f"KnowledgeBase initialized with vector dimension {self.dimension}.")
        except Exception as e:
            logging.error(
                f"FATAL: Could not initialize KnowledgeBase. Is Ollama running and ai model installed? Error: {e}")
            sys.exit(1)

    def add_document(self, doc_content, doc_path):
        """Generates embedding for a doc and adds it to the index."""
        embedding = generate_embedding(doc_content)
        if embedding:
            vector = np.array([embedding]).astype('float32')
            self.index.add(vector)
            self.documents.append({"path": doc_path, "content": doc_content})

    def search(self, query, k=5):
        """Searches for the k most similar documents to a query."""
        query_embedding = generate_embedding(query)
        if query_embedding and self.index.ntotal > 0:
            vector = np.array([query_embedding]).astype('float32')
            # Ensure k is not greater than the number of items in the index
            k = min(k, self.index.ntotal)
            distances, indices = self.index.search(vector, k)
            return [self.documents[i] for i in indices[0]]
        return []
