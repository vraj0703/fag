import asyncio

from knowledge_base.knowledge_base import KnowledgeBase
from llm_apis.apis import llm_apis
from logger import logger


async def knowledge_base_test():
    """
    The main entry point for a command-line chatbot that uses this knowledge base built on RAG system.
    """
    logger.info("################################")
    logger.info("Initializing knowledge base...")
    logger.info("################################")

    """
    This single line will trigger the entire data population process:
    loading, splitting, embedding and storing documents, or loading from a saved index files.
    """
    kb = await KnowledgeBase.pre_heat()

    logger.info("Knowledge base initialization complete. The bot is ready to chat.")
    print("\nHello! I am a RAG-powered with configured knowledge base chat bot."
          "Ask me anything about the documents in your knowledge base.")

    print("Type 'exit' or 'quit' to end the session.")

    while True:
        try:
            query = input("\n> ")
            if query.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break

            # 1. Search the KnowledgeBase for relevant context
            logger.info(f"Searching for context related to: '{query}'")
            search_results = await kb.search(query, k=3)

            # 2. Build the prompt for the LLM
            final_prompt = f"You are a helpful AI assistant. Answer the user's question based on the following context.\n\n"

            if search_results:
                # We now access attributes with dot notation (doc.page_content)
                # and the metadata dictionary (doc.metadata['source']).
                context_str = "\n\n---\n\n".join(
                    [f"Source: {doc.metadata['source']}\n\nContent: {doc.page_content}" for doc in search_results]
                )
                final_prompt += f"CONTEXT:\n{context_str}\n\n---\n\nUSER QUESTION:\n{query}"
            else:
                logger.warning("No relevant context found in the KnowledgeBase.")
                final_prompt += f"USER QUESTION:\n{query}"

            # 3. Call the LLM to get a final answer
            logger.info("Sending prompt to LLM to generate a final answer...")
            # Note: You may need to adjust this method call depending on your llm_apis module.
            answer = await llm_apis.generate(final_prompt)

            # 4. Print the answer
            print(f"\n🤖 {answer}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred in the chat loop: {e}", exc_info=True)
            print("🤖 I'm sorry, an error occurred. Please try again.")


if __name__ == "__main__":
    asyncio.run(knowledge_base_test())
