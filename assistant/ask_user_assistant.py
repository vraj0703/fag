import asyncio
from typing import List, Dict, Any, Literal, Optional

from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from config import config
from logger import logger


# 1. Define the Pydantic model for the AI's structured response for EACH question.
class AnalysisResult(BaseModel):
    """A model to hold the AI's detailed analysis of a user's response."""
    status: Literal["VALID", "INVALID", "NEEDS_CONFIRMATION"] = Field(description="The status of the user's input.")
    value: Any | None = Field(None,
                              description="The final, extracted value if the status is VALID or NEEDS_CONFIRMATION.")
    reasoning: Optional[str] = Field(None,
                                     description="A brief explanation of the AI's decision, especially if the status is not VALID.")
    clarification_question: Optional[str] | None = Field(None,
                                                         description="A helpful follow-up question to ask the user if their input was INVALID or vague.")


# 2. Define the prompt template for the AI.
# This prompt instructs the AI to act as a data validation layer.
ASSISTANT_PROMPT_TEMPLATE = """
You are an intelligent data gathering assistant. Your goal is to have a short conversation with a user to get a specific piece of information.

Analyze the user's response to the question they were asked. Your task is to determine if their response is VALID, INVALID, or NEEDS_CONFIRMATION.

- Use VALID if the user provides a clear, unambiguous answer that either matches the data type or can be converted.
- **CRITICAL RULE:** If the user's input already perfectly matches the requested format (e.g., they provide 'my_project' for 'snake_case'), the status MUST be VALID.
- Use NEEDS_CONFIRMATION if the user provides a conceptual answer that you can convert, but you want to be sure (e.g., user says "sky blue" for a hex code).
- Use INVALID if the user's response is vague or doesn't answer the question. If you use INVALID, you MUST provide a helpful `clarification_question`.

The user was asked: "{question}"
The expected data type is: "{data_type}"
The user responded with: "{user_response}"

Return ONLY a valid JSON object matching the schema below. Do not add any other text.
{format_instructions}
"""


class AskUserAssistant:
    """A class to have an intelligent, multi-turn conversation to gather information."""

    def __init__(self):
        try:
            self.model = ChatOllama(model=config["models"]["generation"], format="json")
            self.parser = PydanticOutputParser(pydantic_object=AnalysisResult)
            self.prompt = PromptTemplate(
                template=ASSISTANT_PROMPT_TEMPLATE,
                input_variables=["question", "data_type", "user_response"],
                partial_variables={"format_instructions": self.parser.get_format_instructions()},
            )
            self.chain = self.prompt | self.model | self.parser
            logger.info("ConversationalCollector initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ConversationalCollector: {e}")
            self.chain = None

    async def collect_parameter(self, param: Dict[str, str]) -> Any:
        """Manages the conversational loop for gathering a single parameter."""
        param_name, param_type, ask_prompt = param['name'], param['type'], param['prompt']

        # Start the conversation for this parameter
        user_response = input(f"🤖 {ask_prompt} > ")

        while True:
            logger.info(f"Analyzing user response: '{user_response}' for parameter '{param_name}'")
            analysis: AnalysisResult = await self.chain.ainvoke({
                "question": ask_prompt,
                "data_type": param_type,
                "user_response": user_response
            })

            if analysis.status == "VALID":
                logger.info(f"Value validated and accepted: {analysis.value}")
                return analysis.value

            elif analysis.status == "NEEDS_CONFIRMATION":
                confirm_prompt = f"I interpreted that as '{analysis.value}'. Is that correct? (yes/no) > "
                confirmation = input(f"🤖 {confirm_prompt}").lower()
                if confirmation in ['y', 'yes']:
                    logger.info(f"User confirmed value: {analysis.value}")
                    return analysis.value
                else:
                    user_response = input("My mistake. Please tell me again. > ")
                    continue  # Re-analyze the new response

            elif analysis.status == "INVALID":
                guidance = analysis.clarification_question or "Please provide a more specific answer."
                user_response = input(f"🤖 {guidance} > ")
                continue  # Re-analyze the new response

    async def gather_info(self, parameters: List[Dict[str, str]]) -> Dict[str, Any]:
        """Orchestrates the collection of multiple parameters."""
        if not self.chain:
            logger.error("Cannot gather info, the chain is not available.")
            return {}

        collected_data = {}
        for param in parameters:
            collected_data[param['name']] = await self.collect_parameter(param)

        return collected_data

    async def gather_list(self, item_name: str, parameters: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Interactively gathers a list of complex objects from the user.
        Args:
            item_name (str): The name of the item being collected (e.g., 'font family').
            parameters (list): The list of parameters that define a single item.
        Returns:
            A list of dictionaries, where each dictionary is a collected item.
        """
        collected_items = []
        while True:
            add_another_response = input(f"🤖 Would you like to add a {item_name}? (yes/no) > ").lower()
            if add_another_response not in ['y', 'yes']:
                break

            logger.info(f"Collecting details for a new {item_name}...")
            # Use the existing gather_info to collect one full item
            item_data = await self.gather_info(parameters)
            collected_items.append(item_data)
            logger.info(f"Added {item_name}: {item_data}")

        logger.info(f"Finished collecting {len(collected_items)} {item_name}(s).")
        return collected_items


# --- Example Usage ---
async def test_conversational_collector():
    params_to_get = [
        {"name": "project_name", "type": "string (snake_case)", "prompt": "What should we name the new project?"},
        {"name": "primary_color", "type": "color hex code", "prompt": "What is the primary color for the app's theme?"}
    ]

    assistant = AskUserAssistant()

    print("--- Starting Conversational Information Gathering ---")
    final_results = await assistant.gather_info(params_to_get)
    print("--- Information Gathering Complete ---")

    print("\nHere is the final structured data:")
    print(final_results)


if __name__ == "__main__":
    asyncio.run(test_conversational_collector())
