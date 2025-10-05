from typing import List, Optional

from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.docstore.document import Document

from config import config
from knowledge_base.knowledge_base import KnowledgeBase
from logger import logger

CODE_GENERATION_PROMPT_TEMPLATE = """
You are an expert Flutter/Dart developer and a helpful coding assistant. Your primary task is to write a new piece of code based on the user's request.

Use the following provided "Context" to inform your response. This context includes relevant examples from the existing codebase and any specific data provided for this task. The new code you write MUST be consistent with this context.

### Context:
{context}

---

### User Request:
{request}

---

### Your Code:
"""


class CodeGenerationAssistant:
    """
    Uses a KnowledgeBase (RAG) and optional explicit context to generate code.
    """

    def __init__(self, knowledge_base: KnowledgeBase):
        """
        Initializes the assistant with a pre-built KnowledgeBase.
        """
        self.knowledge_base = knowledge_base
        try:
            self.model = ChatOllama(model=config["models"]["generation"])
            self.prompt = PromptTemplate(
                template=CODE_GENERATION_PROMPT_TEMPLATE,
                input_variables=["context", "request"],
            )
            # The chain combines the prompt, model, and a simple string output parser
            self.chain = self.prompt | self.model | StrOutputParser()
            logger.info("CodeGenerationAssistant initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize CodeGenerationAssistant: {e}")
            self.chain = None

    async def _search_and_format_context(self, user_request: str) -> str:
        """
        Searches the knowledge base for relevant documents and formats them into a string.
        """
        logger.info(
            f"Searching knowledge base for context related to: '{user_request}'"
        )
        search_results: List[Document] = await self.knowledge_base.search(
            user_request, k=4
        )

        if not search_results:
            logger.warning("No relevant context found in the knowledge base.")
            return "No relevant context was found in the codebase."

        return "\n\n---\n\n".join(
            [
                f"Source File: {doc.metadata.get('source', 'N/A')}\n\n```dart\n{doc.page_content}\n```"
                for doc in search_results
            ]
        )

    async def generate(self, user_request: str, extra_context: Optional[str] = None) -> str | None:
        """
        Generates code by invoking the RAG chain, optionally prepending extra context.

        Args:
            user_request (str): The user's natural language request for code.
            extra_context (str, optional): A string of extra, high-priority context
                                           to provide to the LLM. Defaults to None.

        Returns:
            A string containing the generated code, or None if an error occurs.
        """
        if not self.chain:
            logger.error("Cannot generate code, the generation chain is not available.")
            return None

        try:
            # 1. Get the base context from the KnowledgeBase via RAG search.
            rag_context = await self._search_and_format_context(user_request)

            # 2. Combine the explicit context with the RAG context.
            final_context = rag_context
            if extra_context:
                logger.info("Prepending extra context to the prompt.")
                final_context = f"**High-Priority Context for this task:**\n{extra_context}\n\n---\n\n**General Codebase Context:**\n{rag_context}"

            # 3. Invoke the LangChain chain with the combined context.
            logger.info("Invoking LLM to generate code...")
            generated_code = await self.chain.ainvoke(
                {"request": user_request, "context": final_context}
            )

            return generated_code.strip()

        except Exception as e:
            logger.error(f"An error occurred during code generation: {e}", exc_info=True)
            return None
