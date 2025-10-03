from config import config
from knowledge_base.embed_store import StoreBase
from knowledge_base.load import load_from_github, load_from_local_path
from knowledge_base.split import split_str_into_logical_chunks

from logger import logger


class KnowledgeBase:
    def __init__(self):
        """A simple, synchronous initializer that does no I/O."""
        self.store: StoreBase | None = None

    async def _populate(self):
        """Asynchronously creates the store and populates it with structured data."""
        self.store = await StoreBase.create()

        # If the store was loaded from disk, it's already populated.
        if self.store.index is not None and len(self.store.index.docstore._dict) > 0:
            logger.info("KnowledgeBase is already populated from the saved index on disk.")
            return

        sources = config["knowledge_base"]["sources"]
        if not sources:
            logger.warning("No sources provided to populate the KnowledgeBase.")
            return

        logger.info("Populating KnowledgeBase from sources for the first time...")
        all_chunks_to_add = []  # Collect all chunks for efficient batch processing

        for source in sources:
            documents = await load_from_github(source) \
                if source.startswith("http") else await load_from_local_path(source)

            for doc in documents:
                logger.info(f"Performing structured split on file: {doc['path']}")
                # Use the new async, Pydantic-validated splitting function
                structured_analysis = await split_str_into_logical_chunks(doc['content'])

                if not structured_analysis:
                    logger.warning(f"Could not get structured analysis for: {doc['path']}. Adding whole file instead.")
                    if doc.get('content') and doc.get('path'):
                        all_chunks_to_add.append((doc['content'], doc['path']))
                    continue

                # Add the overall file purpose from the validated Pydantic model
                if 'file_purpose' in structured_analysis:
                    all_chunks_to_add.append((structured_analysis['file_purpose'], doc['path']))

                # Add each individual logical unit from the validated Pydantic model
                for unit in structured_analysis.get('logical_units', []):
                    # Create a detailed text chunk for embedding
                    chunk_content = (
                        f"Unit Name: {unit.get('name', 'N/A')}\n"
                        f"Type: {unit.get('type', 'N/A')}\n"
                        f"Purpose: {unit.get('purpose', 'N/A')}"
                    )
                    # Create a unique path for this chunk for later reference
                    chunk_path = f"{doc['path']}#{unit.get('name', 'unknown_unit')}"
                    all_chunks_to_add.append((chunk_content, chunk_path))

        # Add all collected chunks to the LangChain/FAISS store in a single, efficient batch operation
        if all_chunks_to_add:
            await self.store.add_documents(all_chunks_to_add)
            await self.store.save()  # Save the newly populated store to disk
            logger.info(f"KnowledgeBase populated and saved with {len(self.store.index.docstore._dict)} documents.")
        else:
            logger.warning("No document chunks were created from the sources.")

    async def search(self, query, k=5):
        """Searches for the k most similar documents to a query."""
        if not self.store:
            logger.error("Store is not initialized. Call pre_heat() first.")
            return []
        return await self.store.search(query, k)

    async def save(self):
        """Saves the knowledge base."""
        if not self.store:
            logger.error("Store is not initialized. Cannot save.")
            return
        return await self.store.save()

    @classmethod
    async def pre_heat(cls):
        """The async factory to create and return a fully populated instance."""
        instance = cls()
        await instance._populate()
        return instance
