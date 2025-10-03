import asyncio
from typing import Optional, Literal

from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel

from config import config
from logger import logger


# To align with your project, this could be in 'models/boolean_unit.py'
class BooleanUnit(BaseModel):
    boolean: Optional[Literal["true", "false", "none"]]

    def answer(self) -> bool | None:
        if self.boolean == "true":
            return True
        elif self.boolean == "false":
            return False
        else:
            return None


# To align with your project, this template could be in 'prompts/boolean_question.py'
REASONING_PROMPT_TEMPLATE = """
You are an honest and strict reasoning assistant. Answer the following question strictly in JSON.

Statement: ```{statement}```
Question: ```{question}```

Respond only in the JSON format specified below:
```{format_instructions}```

Use:
- true  → if the statement clearly and directly implies the answer to the question is yes.
- false → if the statement clearly and directly implies the answer to the question is no.
- null  → if it is uncertain, ambiguous, or cannot be determined from the statement alone.
"""


class ReasoningAssistant:
    """A reusable class for structured boolean reasoning."""

    def __init__(self):
        """Initializes the model, parser, and LangChain chain once."""
        try:
            # 1. Initialize the components
            self.model = ChatOllama(model=config["models"]["command_generation"])
            self.parser = PydanticOutputParser(pydantic_object=BooleanUnit)

            # 2. Create the prompt template
            self.prompt = PromptTemplate(
                template=REASONING_PROMPT_TEMPLATE,
                input_variables=["statement", "question"],
                partial_variables={
                    "format_instructions": self.parser.get_format_instructions()
                },
            )

            # 3. Build the chain for reuse
            self.chain = self.prompt | self.model | self.parser
            logger.info("ReasoningAssistant initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize ReasoningAssistant: {e}")
            self.chain = None

    async def verify(self, statement: str, question: str) -> bool | None:
        """
        Verifies a statement against a question using the pre-built chain.
        Includes robust error handling.
        """
        if not self.chain:
            logger.error("Cannot verify, the reasoning chain is not available.")
            return None

        try:
            # 4. Invoke the chain and get a structured response
            dto: BooleanUnit = await self.chain.ainvoke(
                {"statement": statement, "question": question}
            )
            logger.info(f"LLM verification result: {dto.boolean}")
            return dto.answer()
        except Exception as e:
            logger.error(f"An error occurred during verification: {e}")
            return None


# --- Example Usage ---
async def main():
    assistant = ReasoningAssistant()

    # Test Case 1 (Should be True)
    result1 = await assistant.verify(
        statement="The user said: 'okay, let's exit from the chat now'.",
        question="Does the user want to exit?",
    )
    print(f"Test 1: Does user want to exit? --> {result1}")

    # Test Case 2 (Should be False)
    result2 = await assistant.verify(
        statement="The user is asking to create a new file.",
        question="Does the user want to exit?",
    )
    print(f"Test 2: Does user want to exit? --> {result2}")

    # Test Case 3 (Should be None)
    result3 = await assistant.verify(
        statement="The user said: 'maybe later'.",
        question="Does the user want to exit?",
    )
    print(f"Test 3: Does user want to exit? --> {result3}")


if __name__ == "__main__":
    asyncio.run(main())
