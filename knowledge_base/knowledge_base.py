from config import config
from store import StoreBase
from split import split_file_into_logical_chunks
from load import load_from_github, load_from_local_path
from logger import logger

class KnowledgeBase:
    def __init__(self):
        self.store = StoreBase()
        # --- KnowledgeBase Population ---
        sources = config["knowledge_base"]["sources"]
        if sources:
            logger.info("Populating KnowledgeBase from sources...")
            for source in sources:
                documents = load_from_github(source) if source.startswith("http") else load_from_local_path(source)

                # --- Use intelligent splitting ---
                for doc in documents:
                    logger.info(f"Splitting file: {doc['path']}")
                    logical_chunks = split_file_into_logical_chunks(doc['path'])

                    if not logical_chunks:
                        logger.warning(
                            f"Could not split file into chunks: {doc['path']}. Adding whole file content instead.")
                        if doc.get('content') and doc.get('path'):
                            self.store.add_document(doc['content'], doc['path'])
                        continue

                    # Add the overall file purpose to the knowledge base
                    if 'file_purpose' in logical_chunks:
                        self.store.add_document(logical_chunks['file_purpose'], doc['path'])

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
                        self.store.add_document(chunk_content, chunk_path)

            logger.info(f"KnowledgeBase populated with {self.store.index.ntotal} documents.")
        else:
            logger.warning("No sources provided to populate the KnowledgeBase.")

    def search(self, query, k=5):
        """Searches for the k most similar documents to a query."""
        return self.store.search(query, k)
