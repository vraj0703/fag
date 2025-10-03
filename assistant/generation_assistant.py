from typing import List

from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.docstore.document import Document

from config import config
from knowledge_base.knowledge_base import KnowledgeBase

from logger import logger

# A prompt template designed for high-quality, context-aware code generation
CODE_GENERATION_PROMPT_TEMPLATE = """
You are an expert Flutter/Dart developer and a helpful coding assistant. Your task is to write a new piece of code based on the user's request.

Use the following provided "Context" from the existing codebase to understand the project's conventions, style, and existing patterns. The new code you write MUST be consistent with this context.

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
    Uses a KnowledgeBase to generate context-aware code.
    """

    def __init__(self, knowledge_base: KnowledgeBase):
        """
        Initializes the assistant with a pre-populated KnowledgeBase.
        """
        self.knowledge_base = knowledge_base
        try:
            self.model = ChatOllama(model=config["models"]["generation"])

            self.prompt = PromptTemplate(
                template=CODE_GENERATION_PROMPT_TEMPLATE,
                input_variables=["context", "request"],
            )

            # This is the LangChain Expression Language (LCEL) chain.
            # It's a pipeline that defines the flow of data.
            self.chain = (
                {
                    "context": self._search_and_format_context,
                    "request": RunnablePassthrough(),
                }
                | self.prompt
                | self.model
                | StrOutputParser()
            )
            logger.info("CodeGenerationAssistant initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize CodeGenerationAssistant: {e}")
            self.chain = None

    async def _search_and_format_context(self, user_request: str) -> str:
        """
        A helper function that is part of the chain. It takes the user's request,
        searches the knowledge base, and formats the results into a string.
        """
        logger.info(
            f"Searching knowledge base for context related to: '{user_request}'"
        )
        search_results: List[Document] = await self.knowledge_base.store.search(
            user_request, k=4
        )

        if not search_results:
            logger.warning("No relevant context found in the knowledge base.")
            return "No relevant context found in the codebase."

        return "\n\n---\n\n".join(
            [
                f"Source File: {doc.metadata.get('source', 'N/A')}\n\n```dart\n{doc.page_content}\n```"
                for doc in search_results
            ]
        )

    async def generate(self, user_request: str) -> str | None:
        """
        Generates code by invoking the RAG chain.
        """
        if not self.chain:
            logger.error("Cannot generate code, the generation chain is not available.")
            return None

        try:
            logger.info("Invoking code generation chain...")
            response = await self.chain.ainvoke(user_request)
            return response
        except Exception as e:
            logger.error(f"An error occurred during code generation: {e}")
            return None
