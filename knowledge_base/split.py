import logging
import json

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

File content as follows

```{file_content}```

"""


def split_file_into_logical_chunks(file_path):
    logging.info(f"Splitting file: {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()

        response_json = split_str_into_logical_chunks(file_content)
        logging.info(f"Successfully parsed analysis for {file_path}")
        return response_json

    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return None


def split_str_into_logical_chunks(string):
    logging.info(f"Splitting file: {string}...")
    try:
        final_prompt = PROMPT_TO_READ_DART_FILE.format(file_content=string)
        response = llm_apis.split(final_prompt)
        response.raise_for_status()
        response_json = json.loads(response.json()['response'])
        return response_json

    except Exception:
        logging.error(f"Exception: {string}")
        return None
