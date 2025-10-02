import asyncio
from typing import List

from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from config import config


class _Command(BaseModel):
    """
    Pydantic model to structure the output from the AI.
    This ensures the AI returns the data in a predictable format.
    """
    command: str = Field(description="The primary command to be executed. For example: 'ls', 'git', 'docker'.")
    args: List[str] = Field(
        default_factory=list,
        description="A list of arguments and flags for the command. For example: ['-l', '-a', 'my_folder']."
    )
    is_dangerous: bool = Field(
        False,
        description="Set to true if the command could cause irreversible changes, like deleting files (e.g., 'rm -rf')."
    )


# 2. Setup Ollama with LangChain
model = ChatOllama(model=config["models"]["command_generation"])  # or codellama/mistral etc.

parser = PydanticOutputParser(pydantic_object=_Command)

prompt = PromptTemplate(
    template="""
You are an assistant that converts user instructions into a JSON object
that defines how to run a subprocess in Python.

User instruction:
{instruction}

Return only valid JSON matching this schema:
{format_instructions}
""",
    input_variables=["instruction"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


# 3. Async subprocess runner
async def run_subprocess(dto: _Command):
    print(f"\n[ Running Command ]: {dto.command}\n")
    full_command = f"{dto.command} {' '.join(dto.args)}"
    process = await asyncio.create_subprocess_shell(
        full_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if stdout:
        print(stdout.decode())
    if stderr:
        print(f"Error:\n{stderr.decode()}")


# 4. Main flow
async def execute_command(user_input):
    # Get structured response from Ollama
    chain = prompt | model | parser
    dto: _Command = await chain.ainvoke({"instruction": user_input})

    print(f"Parsed DTO: {dto}")
    await run_subprocess(dto)


if __name__ == "__main__":
    asyncio.run(execute_command("create a flutter project by the name `test_flutter`"))
