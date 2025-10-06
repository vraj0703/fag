from logger import logger
import json
from typing import Optional
from llm_apis.apis import llm_apis
from models.file_analysis import DartFileAnalysis
from prompts.read_code_to_analysis import PROMPT_TO_READ_DART_FILE


async def split_str_into_logical_chunks(file_content: str) -> Optional[dict]:
    try:
        logger.info(f"Sending content to LLM for structured analysis: '{file_content}'")
        # The response content should be a JSON string that we can parse
        response_text = await llm_apis.split(PROMPT_TO_READ_DART_FILE, file_content,
                                             DartFileAnalysis.model_json_schema())

        # Validate the response against our Pydantic model
        analysis_result = DartFileAnalysis.model_validate_json(response_text)

        # Convert the Pydantic model back to a dictionary for consistent output
        return analysis_result.model_dump()

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from LLM response. Error: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during structured splitting. Error: {e}")
        return None
