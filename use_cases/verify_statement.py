import asyncio
from typing import Optional, Literal

from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel

from config import config


class BooleanUnit(BaseModel):
    boolean: Optional[Literal['true', 'false', 'none']]

    def answer(self):
        if self.boolean in ["true", "yes", "y", "1"]:
            return True
        elif self.boolean in ["false", "no", "n", "0"]:
            return False
        else:
            return None


# 2. Setup Ollama with LangChain
model = ChatOllama(model=config["models"]["command_generation"])  # or codellama/mistral etc.

parser = PydanticOutputParser(pydantic_object=BooleanUnit)

prompt = PromptTemplate(
    template="""
        You are an honest and strict reasoning assistant. Answer the following question strictly in JSON:
        
        Statement: ```{statement}```
        
        Question: ```{question}```
        
        Respond only in JSON format as follows:
        ```{format_instructions}```
        
        Use:
        - true  → if the statement is correct
        - false → if the statement is incorrect
        - null  → if it's uncertain, ambiguous, or cannot be determined
    """,
    input_variables=["statement", "question"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


async def verify_statement_against_question(statement, question):
    # Get structured response from Ollama
    chain = prompt | model | parser
    dto: BooleanUnit = await  chain.ainvoke({"statement": statement, "question": question})

    print(f"Parsed DTO: {dto}")
    return dto.answer()


if __name__ == "__main__":
    asyncio.run(verify_statement_against_question("exist from the chat", "does user want to exist?"))
