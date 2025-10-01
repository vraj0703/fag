import ollama

from logger import logger
from config import config
from models.boolean_unit import BooleanUnit
from prompts.boolean_question import reasoning_prompt


class LLMApis:
    def __init__(self):
        self.embedding_model = config["models"]["embedding"]
        self.split_model = config["models"]["split"]
        self.generation_model = config["models"]["generation"]
        try:
            self.ollama_client = ollama.AsyncClient()
        except Exception as e:
            logger.fatal(f"Could not initialize Ollama client. Is Ollama running? Error: {e}")
            self.ollama_client = None

    async def split(self, prompt, file_content, format='json'):
        """Sends a prompt to the LLM for intelligent splitting."""
        if not self.ollama_client:
            logger.error("Ollama client not initialized. Cannot split file.")
            return None

        response = await self.ollama_client.chat(
            model=self.split_model,
            messages=[
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': file_content}
            ],
            # This is the key part: instruct Ollama to return JSON
            # based on the schema of our Pydantic model.
            format=format,
        )
        return response['message']['content']

    async def generate(self, prompt, format=''):
        """Sends a prompt to the LLM for intelligent splitting."""
        # This function is now async
        response = await self.ollama_client.chat(
            model=self.generation_model,
            messages=[
                {'role': 'user', 'content': prompt}
            ],
            # This is the key part: instruct Ollama to return JSON
            # based on the schema of our Pydantic model.
            format=format,
        )
        return response['message']['content']

    async def boolean_question(self, statement, question, format=BooleanUnit.model_json_schema()):
        """Ask the LLM the question about the statement.

       Args:
           statement: statement for the question. eg: "exit from the chat"
           question: question to be validated against the statement. eg: "Does user wanted to exit?"
           format: format in which llm returns always BooleanUnit.model_json_schema().

       Returns:
           True, False, None.

       Raises:
           any exception returns None
       """
        final_prompt = reasoning_prompt.format(statement=statement, question=question)
        logger.info(f"asking question: {question} about the statement: with prompt {final_prompt}")
        try:
            response = await self.ollama_client.chat(
                model=self.generation_model,
                messages=[
                    {'role': 'user', 'content': final_prompt}
                ],
                format=format,
            )

            response = BooleanUnit.model_validate_json(response)
            return response.answer()
        except Exception as e:
            logger.error(f"Failed to ask question: {question} about the statement: {statement} with error {e}")
            return None
