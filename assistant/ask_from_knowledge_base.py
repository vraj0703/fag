import asyncio
import sys
from typing import List

from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.docstore.document import Document

from config import config
from knowledge_base.knowledge_base import KnowledgeBase
from logger import logger

# 1. Define the prompt template that will be used to instruct the LLM.
#    It takes the retrieved context and the user's request as input.
CODE_GENERATION_PROMPT = """
You are an expert Flutter/Dart developer and a helpful coding assistant. Your primary task is to generate a block of code based on the user's request.

To ensure the generated code is accurate and consistent with the existing project, use the following context from the codebase. This context provides relevant examples, architectural patterns, and conventions that you should adhere to.

### Context from Knowledge Base:
{context}

---

### User's Request:
{user_prompt}

---

### Generated Code:
"""


class CodeGenerationAssistant:
    """
    An assistant that uses a KnowledgeBase (RAG) to generate context-aware code.
    """

    def __init__(self, knowledge_base: KnowledgeBase):
        """
        Initializes the assistant with a pre-built KnowledgeBase.
        """
        self.knowledge_base = knowledge_base

        # Initialize the LangChain components for the generation chain
        self.model = ChatOllama(model=config["models"]["generation"])
        self.prompt = PromptTemplate(
            template=CODE_GENERATION_PROMPT,
            input_variables=["context", "user_prompt"],
        )
        # The chain combines the prompt, model, and a simple string output parser
        self.chain = self.prompt | self.model | StrOutputParser()
        logger.info("CodeGenerationAssistant initialized successfully.")

    async def generate(self, user_prompt: str, k: int = 5) -> str | None:
        """
        Generates code by first retrieving relevant context from the KnowledgeBase.

        Args:
            user_prompt (str): The user's natural language request for code.
            k (int): The number of relevant documents to retrieve.

        Returns:
            A string containing the generated code, or None if an error occurs.
        """
        try:
            # 1. Retrieve relevant documents from the KnowledgeBase
            logger.info(
                f"Searching knowledge base for context related to: '{user_prompt}'"
            )
            context_docs: List[Document] = await self.knowledge_base.search(
                user_prompt, k=k
            )

            # 2. Format the retrieved documents into a string for the prompt
            if context_docs:
                context_str = "\n\n---\n\n".join(
                    [
                        f"Source: {doc.metadata['source']}\n\n```dart\n{doc.page_content}\n```"
                        for doc in context_docs
                    ]
                )
                logger.info(f"Found {len(context_docs)} relevant context documents.")
            else:
                context_str = "No relevant context found in the knowledge base."
                logger.warning("Could not find relevant context for the prompt.")

            # 3. Invoke the LangChain chain with the user's prompt and the retrieved context
            logger.info("Invoking LLM to generate code...")
            generated_code = await self.chain.ainvoke(
                {"user_prompt": user_prompt, "context": context_str}
            )

            return generated_code.strip()

        except Exception as e:
            logger.error(
                f"An error occurred during code generation: {e}", exc_info=True
            )
            return None


# --- Example Usage ---
async def main():
    """
    Main function to initialize the system and run the assistant.
    """
    # 1. Initialize and populate the KnowledgeBase (this will load from disk if already built)
    logger.info("Initializing KnowledgeBase...")
    kb = await KnowledgeBase.pre_heat()
    logger.info("KnowledgeBase is ready.")

    # 2. Create an instance of our assistant, passing the knowledge base to it
    assistant = CodeGenerationAssistant(knowledge_base=kb)

    # 3. Get the user's request from command-line arguments
    if len(sys.argv) < 2:
        print('\nUsage: python code_generation_assistant.py "<your code request>"')
        print(
            'Example: python code_generation_assistant.py "create a Flutter stateless widget for a blue login button with rounded corners"'
        )
        return

    user_request = " ".join(sys.argv[1:])
    print(f"\n🔹 Your request: '{user_request}'")

    # 4. Run the generation process
    generated_code = await assistant.generate(user_request)

    # 5. Print the result
    if generated_code:
        print("\n✅ AI Generated Code:")
        print("---")
        print(generated_code)
        print("---")
    else:
        print("\n❌ Sorry, I was unable to generate the code for your request.")


if __name__ == "__main__":
    asyncio.run(main())
