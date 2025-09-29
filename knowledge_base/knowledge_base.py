from config import config
from split import split_str_into_logical_chunks
from store import StoreBase
from load import load_from_github, load_from_local_path
from logger import logger


class KnowledgeBase:
    def __init__(self):
        """A simple, synchronous initializer that does no I/O."""
        self.store: StoreBase | None = None

    async def _populate(self):
        """Asynchronously creates the store and populates it with data."""
        self.store = await StoreBase.create()

        sources = config["knowledge_base"]["sources"]
        if not sources:
            logger.warning("No sources provided to populate the KnowledgeBase.")
            return

        logger.info("Populating KnowledgeBase from sources...")
        for source in sources:
            documents = load_from_github(source) if source.startswith("http") else load_from_local_path(source)

            # --- Use intelligent splitting ---
            for doc in documents:
                logger.info(f"Splitting file: {doc['path']}")
                logical_chunks = await split_str_into_logical_chunks(doc['content'])

                if not logical_chunks:
                    logger.warning(
                        f"Could not split file into chunks: {doc['path']}. Adding whole file content instead.")
                    if doc.get('content') and doc.get('path'):
                        await self.store.add_document(doc['content'], doc['path'])
                    continue

                # Add the overall file purpose to the knowledge base
                if 'file_purpose' in logical_chunks:
                    await self.store.add_document(logical_chunks['file_purpose'], doc['path'])

                # Add each individual logical unit (class, function, etc.)
                for unit in logical_chunks.get('logical_units', []):
                    # Create a detailed text chunk for embedding
                    chunk_content = (
                        f"Unit Name: {unit.get('name', 'N/A')}\n"
                        f"Type: {unit.get('type', 'N/A')}\n"
                        f"Purpose: {unit.get('purpose', 'N/A')}"
                    )
                    # Create a unique path for this chunk for later reference
                    chunk_path = f"{doc['path']}#{unit.get('name', 'unknown_unit')}"
                    await self.store.add_document(chunk_content, chunk_path)

            logger.info(f"KnowledgeBase populated with {self.store.index.ntotal} documents.")
        else:
            logger.warning("No sources provided to populate the KnowledgeBase.")

    async def search(self, query, k=5):
        """Searches for the k most similar documents to a query."""
        return await self.store.search(query, k)

    @classmethod
    async def pre_heat(cls):
        """The async factory to create and return a fully populated instance."""
        kb = cls()
        await kb._populate()
        return kb
