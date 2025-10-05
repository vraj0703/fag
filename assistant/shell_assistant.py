import asyncio
import sys
import platform
from typing import List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from config import config
from logger import logger


# Suggestion: Rename _Command to something more descriptive and public
class ShellCommand(BaseModel):
    """A structured model for a shell command."""

    command: str = Field(
        description="The executable program to run (e.g., 'ls', 'git')."
    )
    args: List[str] = Field(
        default_factory=list, description="A list of arguments for the command."
    )
    is_dangerous: bool = Field(
        False,
        description="True if the command could cause irreversible changes (e.g., 'rm').",
    )


# Suggestion: A more detailed prompt that includes OS context
ASSISTANT_PROMPT_TEMPLATE = """
You are an expert assistant that converts a user's natural language instruction into a secure, executable shell command for a {operating_system} machine.

Analyze the user's instruction and provide the executable command and its arguments as a JSON object. If the command involves deleting files (rm), overwriting data, or other potentially irreversible actions, set 'is_dangerous' to true.

User instruction:
{instruction}

Return only a valid JSON object matching the schema below:
{format_instructions}
"""


class ShellAssistant:
    """A reusable class for converting natural language to shell commands."""

    def __init__(self):
        """Initializes the model, parser, and LangChain chain."""
        self.model = ChatOllama(model=config["models"]["command_generation"])
        self.parser = PydanticOutputParser(pydantic_object=ShellCommand)
        self.prompt = PromptTemplate(
            template=ASSISTANT_PROMPT_TEMPLATE,
            input_variables=["instruction", "operating_system"],
            partial_variables={
                "format_instructions": self.parser.get_format_instructions()
            },
        )
        self.chain = self.prompt | self.model | self.parser
        logger.info("ShellAssistant initialized.")

    async def generate_command(self, instruction: str) -> ShellCommand | None:
        """Generates a structured ShellCommand from a natural language instruction."""
        try:
            return await self.chain.ainvoke(
                {
                    "instruction": instruction,
                    "operating_system": platform.system(),  # e.g., "Linux", "Windows"
                }
            )
        except Exception as e:
            logger.error(f"Failed to get a valid command from the LLM: {e}")
            return None

    async def run_command(self, dto: ShellCommand):
        """Securely executes a shell command using create_subprocess_exec."""
        if not dto:
            return

        full_command_str = f"{dto.command} {' '.join(dto.args)}"
        print(f"\n🚀 Executing command: {full_command_str}\n")

        try:
            # CRITICAL FIX: Use create_subprocess_exec for security
            full_command = f"{dto.command} {' '.join(dto.args)}"
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            print("Command finished.")
            if stdout:
                print(f"\n--- STDOUT ---\n{stdout.decode().strip()}")
            if stderr:
                print(f"\n--- STDERR ---\n{stderr.decode().strip()}")

        except FileNotFoundError:
            print(
                f"Error: Command not found: '{dto.command}'. Please ensure it is installed and in your PATH."
            )
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


# Main flow
async def test_shell_assistant():
    if len(sys.argv) < 2:
        print("create a folder name `vishal`")
        return

    user_input = " ".join(sys.argv[1:])
    assistant = ShellAssistant()

    # 1. Get the structured command from the LLM
    command_dto = await assistant.generate_command(user_input)

    if command_dto:
        print(f"\nAI Suggestion: {command_dto.command} {' '.join(command_dto.args)}")

        # 2. SUGGESTION: Use the is_dangerous flag for a safety check
        if command_dto.is_dangerous:
            confirm = input(
                "⚠This command is flagged as potentially dangerous. Continue? (y/n): "
            ).lower()
            if confirm != "y":
                print("Execution cancelled.")
                return

        # 3. Securely run the command
        await assistant.run_command(command_dto)


if __name__ == "__main__":
    # Example: python your_script_name.py "create a flutter project called test_flutter"
    asyncio.run(test_shell_assistant())
