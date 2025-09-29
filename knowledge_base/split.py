from logger import logger
import json
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from llm_apis.apis import llm_apis

PROMPT_TO_READ_DART_FILE = """
You are a highly experienced Flutter engineer. Your task is to analyze a given Dart file and return a structured analysis of its contents in a specific JSON format.

Analysis Instructions:

Read the filename and directory path to infer context (e.g., user_repository.dart in /lib/data/ suggests user data logic).
Look for top-level documentation comments (///) to understand the file's primary role.
Identify the primary class or function, which often matches the filename.
For each logical unit (class, function, etc.), determine its purpose by examining its signature, documentation comments, and the code within its body.

Output Format:

Return the analysis strictly in the following JSON format. Do not include any other text, explanations, or markdown formatting in your response.

JSON

{
  "file_purpose": "A summary of the entire file's role.",
  "logical_units": [
    {
      "name": "unit_name",
      "type": "class | enum | interface | function | parameter",
      "purpose": "<A concise summary of the unit's purpose>",
      "dependencies": ["<dependency1>", "<dependency2>"],
      "returnType": "<The unit's return type or null>"
    }
  ]
}
"""


class LogicalUnit(BaseModel):
    """Defines the structure for a single logical code unit."""
    name: Optional[str] = Field(description="The name of the class, function, enum, etc.")
    type: Optional[Literal[
        'class', 'abstract class', 'enum', 'interface', 'function', 'parameter', 'method', 'library',
        'exception', 'extension method', 'private method', 'field', 'typedef']]
    purpose: Optional[str] = Field(..., description="A concise summary of the unit's purpose.")
    dependencies: List[str] = Field(default_factory=list,
                                    description="A list of other units or libraries this unit depends on.")
    returnType: Optional[str] = Field(None, description="The unit's return type, if applicable.")


class DartFileAnalysis(BaseModel):
    """The main schema for the entire file analysis."""
    file_purpose: str = Field(..., description="A high-level summary of the entire file's role and functionality.")
    logical_units: Optional[List[LogicalUnit]] = Field(...,
                                                       description="A list of all logical units found in the file.")


async def split_str_into_logical_chunks(file_content: str) -> Optional[dict]:
    try:
        content_preview = file_content[:120].replace('\n', ' ') + '...'
        logger.info(f"Sending content to LLM for structured analysis: '{content_preview}'")
        # The response content should be a JSON string that we can parse
        response_text = await llm_apis.split(PROMPT_TO_READ_DART_FILE, content_preview,
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
