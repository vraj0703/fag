import asyncio
import os
import sys

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

from config import config
from logger import logger

class StoreBase:
    def __init__(self):
        """
        A synchronous and lightweight initializer. It prepares the configuration
        but does not perform any blocking I/O or API calls.
        """
        self.folder_path = "faiss_index"
        self.index: FAISS | None = None

        try:
            model_name = config["models"]["embedding"]
            self.embeddings = OllamaEmbeddings(model=model_name)
        except Exception as e:
            logger.error(f"FATAL: Could not initialize OllamaEmbeddings. Is Ollama running? Error: {e}")
            sys.exit(1)

        logger.info("StoreBase instance created. Call 'await StoreBase.create()' to initialize.")

    async def _async_init(self):
        """
        A private async method to handle the slow, I/O-bound parts of initialization.
        It loads the vector store from disk if it exists.
        """
        if os.path.exists(self.folder_path):
            try:
                logger.info(f"Loading existing vector store from {self.folder_path}...")
                # FAISS.load_local is a synchronous I/O operation, so we run it in a thread
                # to avoid blocking the asyncio event loop.
                self.index = await asyncio.to_thread(
                    FAISS.load_local,
                    folder_path=self.folder_path,
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"VectorStore loaded successfully. Contains {len(self.index.docstore._dict)} documents.")
            except Exception as e:
                logger.error(f"Failed to load existing store, a new one will be created. Error: {e}")
                self.index = None

    async def add_documents(self, documents: list[tuple[str, str]]):
        """
        Converts (content, path) tuples to LangChain Documents and adds them to the store.

        Args:
            documents (list): A list of tuples, where each tuple is (doc_content, doc_path).
        """
        if not documents:
            return

        logger.info(f"Adding {len(documents)} document chunks to the vector store...")
        # Convert raw tuples to LangChain Document objects
        langchain_docs = [
            Document(page_content=content, metadata={'source': path})
            for content, path in documents
        ]

        if self.index is None:
            # If the index doesn't exist, create it from the new documents.
            # This is a CPU/IO-bound operation, so we run it in a thread.
            self.index = await asyncio.to_thread(
                FAISS.from_documents,
                documents=langchain_docs,
                embedding=self.embeddings
            )
            logger.info("New vector store created from documents.")
        else:
            # If it exists, add the new documents to it using the async method.
            await self.index.aadd_documents(langchain_docs)
            logger.info("New documents added to existing vector store.")

    async def search(self, query: str, k: int = 5) -> list[Document]:
        """Searches the vector store for the k most similar documents."""
        if not self.index:
            logger.warning("Search attempted on an empty or uninitialized vector store.")
            return []

        logger.info(f"Performing similarity search for query: '{query[:50]}...'")
        # Use LangChain's built-in async method for searching
        results = await self.index.asimilarity_search(query, k=k)
        return results

    async def save(self):
        """Saves the Faiss index and document list to disk."""
        if self.index:
            logger.info(f"Saving vector store to {self.folder_path}...")
            # save_local is a synchronous I/O operation, so run it in a thread.
            await asyncio.to_thread(self.index.save_local, self.folder_path)
            logger.info("Save complete.")
        else:
            logger.warning("Vector store is not initialized. Nothing to save.")

    @classmethod
    async def create(cls):
        """
        The async factory method. Creates and returns a fully initialized StoreBase object.
        """
        instance = cls()
        await instance._async_init()
        return instance